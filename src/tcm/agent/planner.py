from __future__ import annotations

"""
Research planner: takes user query → calls LLM with tool catalog → returns ordered plan.
"""

import json
import logging
from pathlib import Path
from typing import Any
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
6. When multimodal inputs (tongue photos, crude herb slices, prescription images/PDFs, audio) are attached, invoke the appropriate `diagnostics.*` tools (`diagnostics.tongue_analyze`, `diagnostics.herb_identify`, `diagnostics.prescription_parse`, `diagnostics.four_examinations`) alongside supporting Materia Medica, safety, acupuncture, or classical canon tools.

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


def _normalize_attachments(raw_attachments: list[Any]) -> list[Any]:
    """Normalize raw attachment items via tcm.models.multimodal.load_attachment when available."""
    normalized: list[Any] = []
    load_fn = None
    try:
        from tcm.models.multimodal import load_attachment  # type: ignore
        load_fn = load_attachment
    except ImportError:
        pass

    for item in raw_attachments:
        if item is None:
            continue
        if load_fn is not None and isinstance(item, (str, Path, dict)):
            try:
                normalized.append(load_fn(item))
                continue
            except Exception as exc:
                logger.debug("Attachment normalization fallback for %r: %s", item, exc)
        normalized.append(item)
    return normalized


def _extract_attachment_biometrics(att: Any) -> dict[str, Any] | None:
    """Safely extract quantitative image biometrics for an image attachment."""
    try:
        from tcm.models.multimodal import extract_image_biometrics  # type: ignore
    except ImportError:
        return None

    candidates = [att]
    for attr in ("source", "path", "data_uri"):
        val = getattr(att, attr, None)
        if val:
            candidates.append(val)
    if isinstance(att, dict):
        for key in ("data_uri", "data", "source", "path"):
            if att.get(key):
                candidates.append(att[key])

    for candidate in candidates:
        try:
            bio = extract_image_biometrics(candidate)
            if isinstance(bio, dict):
                return bio
        except Exception:
            continue
    return None


def _build_multimodal_prompt_section(attachments: list[Any]) -> str:
    """Build an ATTACHED MULTIMODAL INPUTS summary section for the planner system prompt."""
    lines = ["\n\nATTACHED MULTIMODAL INPUTS:"]
    for idx, att in enumerate(attachments, 1):
        if isinstance(att, dict):
            name = att.get("name") or att.get("source") or f"attachment_{idx}"
            mime = att.get("mime_type") or "application/octet-stream"
            modality = att.get("modality") or att.get("kind") or ("image" if str(mime).startswith("image/") else "file")
        else:
            name = getattr(att, "name", None) or getattr(att, "filename", None) or getattr(att, "source", f"attachment_{idx}")
            mime = getattr(att, "mime_type", None) or "application/octet-stream"
            modality = (
                getattr(att, "modality", None)
                or getattr(att, "kind", None)
                or ("image" if str(mime).startswith("image/") else "file")
            )

        lines.append(f"- Attachment #{idx}: name={name}, modality={modality}, mime_type={mime}")
        if str(modality).lower() == "image" or str(mime).lower().startswith("image/"):
            bio = _extract_attachment_biometrics(att)
            if bio:
                bio_compact = json.dumps(bio, ensure_ascii=False, default=str)
                if len(bio_compact) > 1200:
                    bio_compact = bio_compact[:1200] + "...(truncated)"
                lines.append(f"  Image Biometrics: {bio_compact}")

    lines.append(
        "MULTIMODAL TOOL ROUTING:\n"
        "- Tongue inspection / tongue image -> include `diagnostics.tongue_analyze` (pass color/coating hints from biometrics or user query).\n"
        "- Crude herb / decoction piece photo -> include `diagnostics.herb_identify` and `herbs.lookup`.\n"
        "- Prescription photo / PDF / classical formula text -> include `diagnostics.prescription_parse` and safety checks.\n"
        "- Combined clinical signs / voice / pulse -> include `diagnostics.four_examinations`, `acupuncture.protocol`, or `classics.search` as relevant."
    )
    return "\n".join(lines)


def create_plan(
    session: Session,
    query: str,
    mention_context: str = "",
    attachments: list | None = None,
) -> dict:
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

    raw_atts = attachments if attachments is not None else getattr(session, "attachments", None)
    active_atts = _normalize_attachments(list(raw_atts)) if raw_atts else []
    if active_atts:
        system_prompt += _build_multimodal_prompt_section(active_atts)

    messages = [{"role": "user", "content": query}]

    llm = session.get_llm()
    if active_atts:
        try:
            response = llm.chat(
                system=system_prompt,
                messages=messages,
                temperature=0.1,
                max_tokens=2048,
                attachments=active_atts,
            )
        except TypeError:
            response = llm.chat(
                system=system_prompt,
                messages=messages,
                temperature=0.1,
                max_tokens=2048,
            )
    else:
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
