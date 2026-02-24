"""
Synthesizer: takes tool results → produces structured research answer.
"""

import json
import logging
from tcm.agent.session import Session

logger = logging.getLogger("tcm.agent.synthesizer")

SYNTHESIS_SYSTEM = """You are an expert Traditional Chinese Medicine (TCM) research assistant.
You are given a user's question and the results from executing a research plan.

Your task: synthesize these results into a clear, well-structured answer.

GUIDELINES:
1. Be specific and cite data from tool results.
2. Use both Chinese and English terminology (e.g., 补气 Qi-tonifying).
3. Structure your response with clear headings when appropriate.
4. Include dosage information when relevant.
5. Note any safety concerns or contraindications.
6. If results are incomplete, acknowledge limitations.
7. End with 2-3 suggested follow-up questions.

FORMAT:
- Use Markdown formatting.
- Include a "## Key Findings" section.
- Include a "## Suggested Next Steps" section with follow-up research questions.
"""


def synthesize(session: Session, query: str, plan: dict, results: list[dict]) -> str:
    """Synthesize tool results into a final answer.

    Args:
        session: Active session.
        query: Original user query.
        plan: The execution plan.
        results: List of step results from executor.

    Returns:
        Synthesized answer as markdown string.
    """
    # Check for direct LLM response (no tool steps)
    if len(results) == 1 and results[0].get("tool") == "llm_direct":
        return results[0].get("result", "")

    # Build context from results
    results_summary = _format_results(results)

    user_message = f"""**User Question:** {query}

**Plan Reasoning:** {plan.get('reasoning', 'N/A')}

**Tool Results:**
{results_summary}

Please synthesize these results into a comprehensive answer."""

    llm = session.get_llm()
    max_tokens = int(session.config.get("agent.synthesis_max_tokens", 8192))

    # Use streaming for synthesis
    chunks = []
    for chunk in llm.stream(
        system=SYNTHESIS_SYSTEM,
        messages=[{"role": "user", "content": user_message}],
        temperature=0.2,
        max_tokens=max_tokens,
    ):
        chunks.append(chunk)

    return "".join(chunks)


def synthesize_streaming(session: Session, query: str, plan: dict, results: list[dict]):
    """Synthesize with streaming — yields text chunks.

    Usage:
        for chunk in synthesize_streaming(session, query, plan, results):
            print(chunk, end="", flush=True)
    """
    if len(results) == 1 and results[0].get("tool") == "llm_direct":
        yield results[0].get("result", "")
        return

    results_summary = _format_results(results)

    user_message = f"""**User Question:** {query}

**Plan Reasoning:** {plan.get('reasoning', 'N/A')}

**Tool Results:**
{results_summary}

Please synthesize these results into a comprehensive answer."""

    llm = session.get_llm()
    max_tokens = int(session.config.get("agent.synthesis_max_tokens", 8192))

    for chunk in llm.stream(
        system=SYNTHESIS_SYSTEM,
        messages=[{"role": "user", "content": user_message}],
        temperature=0.2,
        max_tokens=max_tokens,
    ):
        yield chunk


def _format_results(results: list[dict]) -> str:
    """Format tool results for the synthesizer prompt."""
    parts = []
    for r in results:
        step = r.get("step", "?")
        tool = r.get("tool", "unknown")
        status = r.get("status", "unknown")
        purpose = r.get("purpose", "")

        if status == "success":
            output = r.get("output", {})
            output_str = json.dumps(output, ensure_ascii=False, indent=2, default=str)
            # Truncate very long outputs
            if len(output_str) > 3000:
                output_str = output_str[:3000] + "\n... (truncated)"
            parts.append(f"### Step {step}: {tool}\n**Purpose:** {purpose}\n**Status:** ✓ Success\n```json\n{output_str}\n```\n")
        else:
            error = r.get("error", "Unknown error")
            parts.append(f"### Step {step}: {tool}\n**Purpose:** {purpose}\n**Status:** ✗ Error: {error}\n")

    return "\n".join(parts)
