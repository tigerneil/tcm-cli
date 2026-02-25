"""
Synthesizer: takes tool results → produces structured research answer.
"""

import json
import logging
from tcm.agent.session import Session

logger = logging.getLogger("tcm.agent.synthesizer")

BASE_SYNTHESIS_SYSTEM = """You are an expert Traditional Chinese Medicine (TCM) research assistant.
You are given a user's question and the results from executing a research plan.

Your task: synthesize these results into a clear, well-structured answer.

GUIDELINES:
1. Be specific and cite data from tool results.
2. Structure your response with clear headings when appropriate.
3. Include dosage information when relevant.
4. Note any safety concerns or contraindications.
5. If results are incomplete, acknowledge limitations.
6. End with 2-3 suggested follow-up questions.
"""


def _lang_instructions(lang: str) -> str:
    lang = (lang or "en").lower()
    if lang == "zh":
        return (
            "OUTPUT LANGUAGE:\n"
            "- 仅用中文回答，不要包含英文。\n"
            "- 标题与结构使用中文（例如：'## 关键信息'、'## 建议的下一步'）。\n"
            "- 术语应包含中医术语并在必要时给出现代医学对照。\n"
        )
    if lang == "bi":
        return (
            "OUTPUT LANGUAGE:\n"
            "- 提供中英双语内容。先中文段落，再对应的英文段落。\n"
            "- 对每个主要标题使用并列标题，例如：'## 关键信息 | Key Findings'、'## 建议的下一步 | Suggested Next Steps'。\n"
            "- 在要点层面尽量对齐中英文内容。\n"
        )
    # default en
    return (
        "OUTPUT LANGUAGE:\n"
        "- Answer in English only (no Chinese characters unless quoted from sources).\n"
        "- Use English headings such as '## Key Findings' and '## Suggested Next Steps'.\n"
        "- Include pinyin in parentheses when helpful (e.g., Ren Shen (ginseng)).\n"
    )


def _build_synthesis_system(lang: str) -> str:
    return BASE_SYNTHESIS_SYSTEM + "\n" + _lang_instructions(lang)


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
    lang = session.config.get("ui.language", "en")

    # Use streaming for synthesis
    chunks = []
    for chunk in llm.stream(
        system=_build_synthesis_system(lang),
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
    lang = session.config.get("ui.language", "en")

    for chunk in llm.stream(
        system=_build_synthesis_system(lang),
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
