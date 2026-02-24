"""
Research planner: takes user query → calls LLM with tool catalog → returns ordered plan.
"""

import json
import logging
from tcm.agent.session import Session
from tcm.tools import registry, ensure_loaded

logger = logging.getLogger("tcm.agent.planner")

PLANNER_SYSTEM = """You are an expert Traditional Chinese Medicine (TCM) research assistant.
You have access to a set of computational tools for TCM research.

Given a user's research question, create a step-by-step execution plan.

RULES:
1. Select only the tools needed to answer the question.
2. Order steps logically — later steps can depend on earlier results.
3. Each step must specify exactly one tool and its parameters.
4. Be conservative — only include steps that directly help answer the question.
5. If the question is simple and can be answered with 1-2 tools, keep the plan short.

OUTPUT FORMAT (strict JSON):
{
  "reasoning": "Brief explanation of your approach",
  "steps": [
    {
      "step": 1,
      "tool": "category.tool_name",
      "parameters": {"param1": "value1"},
      "purpose": "Why this step is needed"
    }
  ]
}

AVAILABLE TOOLS:
"""


def create_plan(session: Session, query: str, mention_context: str = "") -> dict:
    """Create a research plan for the given query.

    Returns:
        dict with 'reasoning' and 'steps' keys.
    """
    ensure_loaded()

    # Build tool catalog for the planner
    suppressed = session.tool_health_suppressed_tools()
    tool_catalog = registry.tool_descriptions_for_llm(
        exclude_tools=suppressed,
    )

    system_prompt = PLANNER_SYSTEM + tool_catalog

    if mention_context:
        system_prompt += f"\n\nUSER CONTEXT:\n{mention_context}"

    messages = [{"role": "user", "content": query}]

    llm = session.get_llm()
    response = llm.chat(
        system=system_prompt,
        messages=messages,
        temperature=0.1,
        max_tokens=2048,
    )

    # Parse the plan from LLM response
    try:
        # Try to extract JSON from the response
        content = response.content.strip()
        # Handle markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        plan = json.loads(content)
        if "steps" not in plan:
            plan = {"reasoning": "Direct response", "steps": []}
        return plan
    except (json.JSONDecodeError, IndexError):
        logger.warning("Failed to parse plan JSON, returning raw response")
        return {
            "reasoning": response.content,
            "steps": [],
            "raw_response": True,
        }
