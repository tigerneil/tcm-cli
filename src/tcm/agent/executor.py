"""
Plan executor: iterates plan steps, calls tools, handles errors/retries.
"""

import json
import logging
import time
from rich.console import Console
from rich.panel import Panel

from tcm.agent.session import Session
from tcm.tools import registry, ensure_loaded

logger = logging.getLogger("tcm.agent.executor")
console = Console()


def execute_plan(session: Session, plan: dict, verbose: bool = False) -> list[dict]:
    """Execute a research plan step by step.

    Args:
        session: Active session with LLM and config.
        plan: Plan dict with 'steps' list.
        verbose: Whether to print step details.

    Returns:
        List of step results.
    """
    ensure_loaded()
    steps = plan.get("steps", [])
    results = []

    if not steps:
        # No tool steps — this was a direct LLM response
        return [{"step": 0, "tool": "llm_direct", "result": plan.get("reasoning", ""), "status": "success"}]

    max_retries = int(session.config.get("agent.executor_max_retries", 2))

    for step in steps:
        step_num = step.get("step", len(results) + 1)
        tool_name = step.get("tool", "")
        parameters = step.get("parameters", {})
        purpose = step.get("purpose", "")

        if verbose:
            console.print(f"  [cyan]Step {step_num}[/cyan]: {tool_name} — {purpose}")

        tool = registry.get_tool(tool_name)
        if not tool:
            result = {
                "step": step_num,
                "tool": tool_name,
                "status": "error",
                "error": f"Tool '{tool_name}' not found.",
            }
            results.append(result)
            continue

        # Substitute references to previous results
        resolved_params = _resolve_params(parameters, results)

        # Execute with retry
        result = _execute_with_retry(session, tool, resolved_params, max_retries)
        result["step"] = step_num
        result["tool"] = tool_name
        result["purpose"] = purpose

        if verbose:
            status_icon = "✓" if result["status"] == "success" else "✗"
            color = "green" if result["status"] == "success" else "red"
            console.print(f"    [{color}]{status_icon}[/{color}] {result['status']}")

        results.append(result)

    return results


def _execute_with_retry(session: Session, tool, parameters: dict, max_retries: int) -> dict:
    """Execute a tool with retry logic."""
    for attempt in range(1, max_retries + 1):
        try:
            output = tool.run(**parameters)
            session.record_tool_success(tool.name)
            return {"status": "success", "output": output}
        except Exception as e:
            error_text = str(e)
            logger.warning("Tool %s failed (attempt %d): %s", tool.name, attempt, error_text)
            session.record_tool_failure(tool.name, error_text)

            if attempt >= max_retries:
                return {"status": "error", "error": error_text}
            time.sleep(1)

    return {"status": "error", "error": "Max retries exceeded"}


def _resolve_params(parameters: dict, previous_results: list) -> dict:
    """Resolve parameter references like '$step1.output.targets' to actual values."""
    resolved = {}
    for key, value in parameters.items():
        if isinstance(value, str) and value.startswith("$step"):
            try:
                # Parse reference like "$step1.output.targets"
                parts = value[1:].split(".")
                step_ref = int(parts[0].replace("step", "")) - 1
                if 0 <= step_ref < len(previous_results):
                    result = previous_results[step_ref]
                    obj = result
                    for part in parts[1:]:
                        if isinstance(obj, dict):
                            obj = obj.get(part, value)
                        else:
                            obj = value
                            break
                    resolved[key] = obj
                else:
                    resolved[key] = value
            except (ValueError, IndexError):
                resolved[key] = value
        else:
            resolved[key] = value
    return resolved
