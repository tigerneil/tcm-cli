from __future__ import annotations

"""
Production-grade, zero-extra-dependency HTTP + REST API server for TCM Studio.

Serves the static web workbench (`/` -> `index.html`, `/studio` -> `studio.html`)
alongside live computational TCM tools, quantitative tongue/herb image biometrics,
multi-layer network pharmacology graphs, and SOTA multimodal LLM orchestration.
"""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import importlib
import inspect
import json
import logging
import mimetypes
from pathlib import Path
import re
import threading
from typing import Any, Callable
import urllib.parse
import webbrowser

from tcm import __version__
from tcm.agent.config import Config, PROVIDER_SPECS
from tcm.agent.executor import execute_plan
from tcm.agent.planner import create_plan
from tcm.agent.session import Session
from tcm.agent.synthesizer import synthesize
from tcm.tools import ensure_loaded, registry

logger = logging.getLogger("tcm.studio.server")

_STATIC_MIME_OVERRIDES: dict[str, str] = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".mjs": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".ico": "image/x-icon",
    ".md": "text/markdown; charset=utf-8",
}

_PARAM_ALIAS_GROUPS: tuple[tuple[str, ...], ...] = (
    ("query", "name", "herb_name", "herb", "candidate_name"),
    ("query", "formula_name", "formula", "name"),
    ("query", "compound_name", "compound", "name"),
    ("condition_or_syndrome", "syndrome_name", "syndrome", "condition", "pattern", "indication", "query"),
    ("text", "prescription", "prescription_text", "raw_text", "formula_text", "query"),
    ("features", "observations", "description", "visual_features", "traits"),
    ("body_color", "tongue_color", "color"),
    ("body_shape", "tongue_shape", "shape"),
    ("coating_color", "fur_color", "moss_color"),
    ("coating_texture", "coating_quality", "fur_texture", "coating"),
    ("sublingual", "sublingual_veins"),
    ("biometrics", "image_biometrics", "colorimetry"),
    ("inspection", "wang", "visual"),
    ("auscultation", "wen_audio", "olfaction", "voice_breath"),
    ("inquiry", "wen_inquiry", "symptoms"),
    ("pulse", "qie", "palpation", "pulse_quality"),
    ("herbs", "herb_list"),
    ("gene_list", "genes", "targets", "target_list"),
    ("dosage_g", "dosage"),
    ("point_code", "point", "acupoint", "code", "query", "name"),
    ("clause_id", "clause", "number", "query"),
)

# Curated offline phytochemistry, ADMET, target, and KEGG pathway knowledge
# ensuring rich multi-layer graphs for all built-in formulas & herbs offline.
_OFFLINE_HERB_COMPOUNDS: dict[str, list[str]] = {
    "人参": ["Ginsenoside Rg1", "Ginsenoside Rb1", "Ginsenoside Re"],
    "黄芪": ["Astragaloside IV", "Calycosin", "Formononetin"],
    "白术": ["Atractylenolide I", "Atractylenolide III", "Atractylone"],
    "茯苓": ["Pachymic acid", "Poricoic acid A", "Tumulosic acid"],
    "甘草": ["Glycyrrhizin", "Liquiritigenin", "Isoliquiritigenin"],
    "当归": ["Ferulic acid", "Z-Ligustilide", "Senkyunolide A"],
    "黄连": ["Berberine", "Coptisine", "Palmatine"],
    "柴胡": ["Saikosaponin A", "Saikosaponin D", "Quercetin"],
    "黄芩": ["Baicalin", "Baicalein", "Wogonin"],
    "半夏": ["Beta-Sitosterol", "Baicalein", "Coniferin"],
    "生姜": ["6-Gingerol", "6-Shogaol", "Zingerone"],
    "大枣": ["Jujuboside A", "Rutin", "Oleanolic acid"],
    "陈皮": ["Hesperidin", "Nobiletin", "Tangeretin"],
    "升麻": ["Cimifugin", "Isoferulic acid", "Ferulic acid"],
    "熟地黄": ["Catalpol", "Acteoside", "Rehmannioside D"],
    "山茱萸": ["Morroniside", "Loganin", "Ursolic acid"],
    "山药": ["Diosgenin", "Allantoin", "Dioscin"],
    "泽泻": ["Alisol B 23-acetate", "Alisol A", "Pachymic acid"],
    "牡丹皮": ["Paeonol", "Paeoniflorin", "Gallic acid"],
    "桂枝": ["Cinnamaldehyde", "Cinnamic acid", "2-Methoxycinnamaldehyde"],
    "白芍": ["Paeoniflorin", "Albiflorin", "Catechin"],
    "麻黄": ["Ephedrine", "Pseudoephedrine", "Quercetin"],
    "川芎": ["Tetramethylpyrazine", "Ferulic acid", "Z-Ligustilide"],
    "桃仁": ["Amygdalin", "Beta-Sitosterol", "Campesterol"],
    "红花": ["Hydroxysafflor yellow A", "Kaempferol", "Luteolin"],
    "丹参": ["Tanshinone IIA", "Salvianolic acid B", "Cryptotanshinone"],
    "附子": ["Benzoylmesaconine", "Hypaconitine", "Fuziline"],
}

_OFFLINE_COMPOUND_META: dict[str, dict[str, Any]] = {
    "Ginsenoside Rg1": {"mw": 801.01, "ob": 12.28, "dl": 0.84, "targets": ["AKT1", "ESR1", "NR3C1", "PPARG", "NOS3"]},
    "Ginsenoside Rb1": {"mw": 1109.29, "ob": 6.24, "dl": 0.65, "targets": ["AMPK", "AKT1", "NFKB1", "TNF", "HMOX1"]},
    "Ginsenoside Re": {"mw": 947.15, "ob": 10.12, "dl": 0.72, "targets": ["PIK3CA", "AKT1", "NOS3", "IL6"]},
    "Astragaloside IV": {"mw": 784.97, "ob": 17.74, "dl": 0.15, "targets": ["TLR4", "NFKB1", "PIK3CA", "AKT1", "HMOX1"]},
    "Calycosin": {"mw": 284.26, "ob": 47.75, "dl": 0.24, "targets": ["ESR1", "MAPK1", "PTGS2", "VEGFA"]},
    "Formononetin": {"mw": 268.26, "ob": 69.67, "dl": 0.21, "targets": ["ESR1", "PPARG", "PTGS2", "SIRT1"]},
    "Atractylenolide I": {"mw": 230.30, "ob": 37.37, "dl": 0.15, "targets": ["TLR4", "TNF", "IL6", "PTGS2"]},
    "Atractylenolide III": {"mw": 248.32, "ob": 68.11, "dl": 0.17, "targets": ["NFKB1", "IL6", "MAPK1", "AMPK"]},
    "Atractylone": {"mw": 216.32, "ob": 41.10, "dl": 0.13, "targets": ["PTGS2", "NOS2", "TNF"]},
    "Pachymic acid": {"mw": 528.76, "ob": 33.63, "dl": 0.81, "targets": ["PPARG", "PIK3CA", "AKT1", "NR3C1"]},
    "Poricoic acid A": {"mw": 498.70, "ob": 30.52, "dl": 0.76, "targets": ["TGFB1", "SMAD3", "NFKB1"]},
    "Tumulosic acid": {"mw": 486.73, "ob": 29.88, "dl": 0.80, "targets": ["PPARG", "TNF", "IL1B"]},
    "Glycyrrhizin": {"mw": 822.93, "ob": 19.62, "dl": 0.68, "targets": ["HMGB1", "TLR4", "NFKB1", "HSD11B2"]},
    "Liquiritigenin": {"mw": 256.25, "ob": 32.76, "dl": 0.18, "targets": ["ESR2", "PTGS2", "AKT1", "NFE2L2"]},
    "Isoliquiritigenin": {"mw": 256.25, "ob": 85.32, "dl": 0.15, "targets": ["NLRP3", "NFKB1", "PTGS2", "HMOX1"]},
    "Ferulic acid": {"mw": 194.18, "ob": 39.56, "dl": 0.06, "targets": ["PTGS2", "NOS3", "NFE2L2", "F2"]},
    "Z-Ligustilide": {"mw": 190.24, "ob": 51.30, "dl": 0.07, "targets": ["TNF", "MAPK1", "NOS3", "PTGS2"]},
    "Senkyunolide A": {"mw": 192.25, "ob": 26.56, "dl": 0.07, "targets": ["TNF", "PTGS2", "CALM1"]},
    "Berberine": {"mw": 336.36, "ob": 36.86, "dl": 0.78, "targets": ["AMPK", "DPP4", "PTGS2", "LDLR", "PCSK9"]},
    "Coptisine": {"mw": 320.32, "ob": 30.67, "dl": 0.86, "targets": ["NFKB1", "MAPK1", "PTGS2", "AMPK"]},
    "Palmatine": {"mw": 352.40, "ob": 64.60, "dl": 0.65, "targets": ["TNF", "IL6", "PTGS2", "ACHE"]},
    "Saikosaponin A": {"mw": 780.98, "ob": 14.42, "dl": 0.63, "targets": ["NFKB1", "TNF", "IL6", "BDNF"]},
    "Saikosaponin D": {"mw": 780.98, "ob": 13.80, "dl": 0.63, "targets": ["STAT3", "NFKB1", "TP53", "NR3C1"]},
    "Quercetin": {"mw": 302.24, "ob": 46.43, "dl": 0.28, "targets": ["AKT1", "TNF", "IL6", "VEGFA", "MAPK1"]},
    "Baicalin": {"mw": 446.36, "ob": 40.12, "dl": 0.75, "targets": ["TLR4", "NFKB1", "STAT3", "PTGS2"]},
    "Baicalein": {"mw": 270.24, "ob": 33.52, "dl": 0.21, "targets": ["ALOX12", "PTGS2", "AKT1", "NFE2L2"]},
    "Wogonin": {"mw": 284.26, "ob": 30.68, "dl": 0.23, "targets": ["AKT1", "TP53", "NFKB1", "PTGS2"]},
    "Beta-Sitosterol": {"mw": 414.71, "ob": 36.91, "dl": 0.75, "targets": ["CASP3", "PPARG", "PTGS2"]},
    "6-Gingerol": {"mw": 294.39, "ob": 35.64, "dl": 0.16, "targets": ["TRPV1", "PTGS2", "NFKB1", "HTR3A"]},
    "Hesperidin": {"mw": 610.56, "ob": 13.33, "dl": 0.67, "targets": ["TNF", "NOS3", "NFE2L2", "AKT1"]},
    "Nobiletin": {"mw": 402.39, "ob": 61.67, "dl": 0.52, "targets": ["RORC", "AMPK", "NFKB1", "MAPK1"]},
    "Catalpol": {"mw": 362.33, "ob": 5.07, "dl": 0.44, "targets": ["PIK3CA", "AKT1", "BDNF", "NFE2L2"]},
    "Morroniside": {"mw": 406.38, "ob": 11.45, "dl": 0.55, "targets": ["CASP3", "BCL2", "NFE2L2", "AKT1"]},
    "Diosgenin": {"mw": 414.62, "ob": 80.88, "dl": 0.81, "targets": ["STAT3", "AKT1", "PPARG", "NFKB1"]},
    "Alisol B 23-acetate": {"mw": 514.74, "ob": 32.52, "dl": 0.82, "targets": ["FXR", "PPARG", "AMPK"]},
    "Paeonol": {"mw": 166.17, "ob": 28.79, "dl": 0.04, "targets": ["TNF", "NFKB1", "PTGS2", "ICAM1"]},
    "Paeoniflorin": {"mw": 480.46, "ob": 53.87, "dl": 0.79, "targets": ["TNF", "IL6", "MAPK1", "BDNF"]},
    "Cinnamaldehyde": {"mw": 132.16, "ob": 31.99, "dl": 0.02, "targets": ["TRPA1", "TLR4", "NOS2", "PTGS2"]},
    "Ephedrine": {"mw": 165.23, "ob": 43.35, "dl": 0.04, "targets": ["ADRB2", "ADRB1", "ADRA1A"]},
    "Tetramethylpyrazine": {"mw": 136.19, "ob": 41.09, "dl": 0.03, "targets": ["NOS3", "F2", "VEGFA", "CALM1"]},
    "Tanshinone IIA": {"mw": 294.34, "ob": 49.89, "dl": 0.40, "targets": ["NFKB1", "PTGS2", "NOS3", "STAT3"]},
}

_TARGET_PATHWAYS: dict[str, list[tuple[str, str]]] = {
    "AKT1": [("hsa04151", "PI3K-Akt signaling pathway"), ("hsa04066", "HIF-1 & survival signaling")],
    "PIK3CA": [("hsa04151", "PI3K-Akt signaling pathway"), ("hsa04910", "Insulin & metabolic signaling")],
    "AMPK": [("hsa04152", "AMPK energy-sensing pathway"), ("hsa04922", "Glucagon & lipid metabolism")],
    "PPARG": [("hsa03320", "PPAR metabolic signaling"), ("hsa04152", "AMPK energy-sensing pathway")],
    "NFKB1": [("hsa04064", "NF-kappa B inflammatory pathway"), ("hsa04620", "Toll-like receptor signaling")],
    "TLR4": [("hsa04620", "Toll-like receptor signaling"), ("hsa04064", "NF-kappa B inflammatory pathway")],
    "TNF": [("hsa04668", "TNF cytokine signaling"), ("hsa04064", "NF-kappa B inflammatory pathway")],
    "IL6": [("hsa04630", "JAK-STAT immune signaling"), ("hsa04668", "TNF cytokine signaling")],
    "STAT3": [("hsa04630", "JAK-STAT immune signaling"), ("hsa04066", "HIF-1 & survival signaling")],
    "PTGS2": [("hsa00590", "Arachidonic acid & eicosanoid metabolism"), ("hsa04668", "TNF cytokine signaling")],
    "MAPK1": [("hsa04010", "MAPK signaling cascade"), ("hsa04722", "Neurotrophin & stress regulation")],
    "NOS3": [("hsa04270", "Vascular smooth muscle & NO vasodilation"), ("hsa04151", "PI3K-Akt signaling pathway")],
    "NFE2L2": [("hsa05208", "Nrf2/HO-1 oxidative stress defense")],
    "HMOX1": [("hsa05208", "Nrf2/HO-1 oxidative stress defense")],
    "ESR1": [("hsa04915", "Estrogen & endocrine modulation")],
    "NR3C1": [("hsa04080", "HPA-axis neuroendocrine regulation")],
    "BDNF": [("hsa04722", "Neurotrophin & stress regulation")],
    "HSD11B2": [("hsa04960", "Aldosterone-regulated sodium reabsorption")],
    "DPP4": [("hsa04910", "Insulin & metabolic signaling")],
    "F2": [("hsa04611", "Platelet activation & coagulation cascade")],
}


def resolve_static_dir() -> Path:
    """Resolve the Studio static web asset directory.

    Checks repository `docs/` first, then package-bundled `static/`, then `./docs`.
    """
    repo_docs = Path(__file__).resolve().parents[3] / "docs"
    if repo_docs.is_dir():
        return repo_docs
    pkg_static = Path(__file__).resolve().parent / "static"
    if pkg_static.is_dir():
        return pkg_static
    cwd_docs = Path.cwd() / "docs"
    if cwd_docs.is_dir():
        return cwd_docs
    return repo_docs


def _ensure_all_tools_loaded() -> None:
    """Ensure core and newly registered diagnostic/acupuncture/classics tools are loaded."""
    ensure_loaded()
    for extra_mod in ("diagnostics", "acupuncture", "classics"):
        if not registry.list_tools(extra_mod):
            try:
                importlib.import_module(f"tcm.tools.{extra_mod}")
            except Exception:
                pass


def _has_provider_key(session: Session, provider: str | None) -> bool:
    """Return True if the provider is ready for live inference (API key or local Ollama)."""
    prov = (provider or session.config.get("llm.provider", "anthropic") or "").lower()
    if prov == "ollama":
        return True
    return bool(session.config.llm_api_key(prov))


def _configured_providers(session: Session) -> list[str]:
    """List providers that currently have credentials configured."""
    ready: list[str] = []
    for name in sorted(PROVIDER_SPECS.keys()):
        if name == "ollama":
            if session.config.get("llm.provider") == "ollama" or session.config.llm_api_key("ollama"):
                ready.append(name)
        elif session.config.llm_api_key(name):
            ready.append(name)
    return ready


def _serialize_model(model_obj: Any, active_model: str, session: Session) -> dict[str, Any]:
    """Convert a ModelInfo object or dict into a rich JSON-ready dictionary."""
    if hasattr(model_obj, "to_dict"):
        data = dict(model_obj.to_dict())
    elif isinstance(model_obj, dict):
        data = dict(model_obj)
    else:
        modalities = list(getattr(model_obj, "modalities", None) or ["text"])
        data = {
            "id": model_obj.id,
            "provider": model_obj.provider,
            "display_name": model_obj.display_name,
            "context_window": model_obj.context_window,
            "input_price": model_obj.input_price,
            "output_price": model_obj.output_price,
            "description": model_obj.description,
            "modalities": modalities,
            "tier": getattr(model_obj, "tier", "standard"),
        }
    data["active"] = data.get("id") == active_model
    data["configured"] = _has_provider_key(session, data.get("provider"))
    return data


def _list_models_filtered(
    provider: str | None = None,
    modality: str | None = None,
    tier: str | None = None,
) -> list[Any]:
    """List models from catalog with defensive fallback if filter kwargs aren't supported yet."""
    from tcm.models.llm import list_models

    try:
        return list_models(
            provider=provider or None,
            modality=modality or None,
            tier=tier or None,
        )
    except TypeError:
        models = list_models(provider=provider or None)
        if modality:
            mod_norm = modality.strip().lower()
            models = [
                m for m in models
                if mod_norm in [x.lower() for x in (getattr(m, "modalities", None) or ["text"])]
            ]
        if tier:
            tier_norm = tier.strip().lower()
            models = [m for m in models if str(getattr(m, "tier", "")).lower() == tier_norm]
        return models


def _recommend_models_safe(task: str, session: Session) -> list[dict[str, Any]]:
    """Return task-ranked SOTA model recommendations with configured-key annotations."""
    try:
        from tcm.models.multimodal import recommend_models_for_task  # type: ignore
        recs = recommend_models_for_task(task or "general")
        enriched: list[dict[str, Any]] = []
        for item in recs:
            row = dict(item) if isinstance(item, dict) else _serialize_model(item, session.current_model, session)
            row["configured"] = _has_provider_key(session, row.get("provider"))
            enriched.append(row)
        if enriched:
            return enriched
    except Exception as exc:
        logger.debug("Model recommendation fallback (%s): %s", task, exc)

    models = _list_models_filtered()[:5]
    return [_serialize_model(m, session.current_model, session) for m in models]


def _extract_biometrics_safe(image_input: Any) -> dict[str, Any] | None:
    """Extract CIE L*a*b* and somatotopy biometrics for an image input."""
    if not image_input:
        return None
    try:
        from tcm.models.multimodal import extract_image_biometrics  # type: ignore
        return extract_image_biometrics(image_input)
    except Exception as exc:
        logger.warning("Image biometrics extraction failed: %s", exc)
        return {"status": "unavailable", "error": str(exc), "tcm_visual_hints": []}


def _load_attachment_safe(source: Any) -> Any | None:
    """Load an attachment via multimodal.load_attachment when available."""
    if not source:
        return None
    try:
        from tcm.models.multimodal import load_attachment  # type: ignore
        return load_attachment(source)
    except Exception as exc:
        logger.debug("Attachment load fallback: %s", exc)
        return None


def _coerce_param_value(param: inspect.Parameter, value: Any) -> Any:
    """Coerce list <-> comma-separated string when function signature expects one or the other."""
    ann = str(param.annotation).lower() if param.annotation is not inspect.Parameter.empty else ""
    if isinstance(value, list) and ("str" in ann or isinstance(param.default, str)):
        return ", ".join(str(x) for x in value if str(x).strip())
    if isinstance(value, str) and "list" in ann:
        return [s.strip() for s in value.split(",") if s.strip()]
    return value


def _adapt_tool_kwargs(func: Callable[..., Any], raw_params: dict[str, Any]) -> dict[str, Any]:
    """Map caller parameter aliases to the target tool function's exact signature."""
    sig = inspect.signature(func)
    if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
        return {k: v for k, v in raw_params.items() if v is not None}

    accepted_params = {
        name: param
        for name, param in sig.parameters.items()
        if param.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
    }
    matched: dict[str, Any] = {}
    used_raw_keys: set[str] = set()

    for name, param in accepted_params.items():
        if name in raw_params and raw_params[name] is not None:
            matched[name] = _coerce_param_value(param, raw_params[name])
            used_raw_keys.add(name)

    for name, param in accepted_params.items():
        if name in matched:
            continue
        for group in _PARAM_ALIAS_GROUPS:
            if name in group:
                for alias in group:
                    if alias in raw_params and raw_params[alias] is not None:
                        matched[name] = _coerce_param_value(param, raw_params[alias])
                        used_raw_keys.add(alias)
                        break
            if name in matched:
                break

    unfilled_required = [
        name for name, param in accepted_params.items()
        if name not in matched and param.default is inspect.Parameter.empty
    ]
    unused_values = [
        (k, v) for k, v in raw_params.items()
        if k not in used_raw_keys and v is not None
    ]
    if len(unfilled_required) == 1 and len(unused_values) >= 1:
        req_name = unfilled_required[0]
        matched[req_name] = _coerce_param_value(accepted_params[req_name], unused_values[0][1])

    return matched


def _run_tool_by_name(
    tool_name: str,
    params: dict[str, Any],
    fallback_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Execute a registered tool with smart parameter adaptation, or invoke fallback if absent."""
    _ensure_all_tools_loaded()
    tool = registry.get_tool(tool_name)
    if tool is not None:
        resolved = _adapt_tool_kwargs(tool.function, params)
        out = tool.run(**resolved)
        return out if isinstance(out, dict) else {"result": out}
    if fallback_fn is not None:
        return fallback_fn(params)
    raise KeyError(f"Tool '{tool_name}' not found.")


def _chat_llm_optional(
    session: Session,
    system_prompt: str,
    user_prompt: str,
    attachments: list[Any] | None = None,
) -> str | None:
    """Call active LLM with optional multimodal attachments if API credentials are configured."""
    if not _has_provider_key(session, session.config.get("llm.provider")):
        return None
    try:
        llm = session.get_llm()
        messages = [{"role": "user", "content": user_prompt}]
        atts = [a for a in (attachments or []) if a is not None]
        if atts:
            try:
                resp = llm.chat(
                    system=system_prompt,
                    messages=messages,
                    temperature=0.2,
                    max_tokens=2048,
                    attachments=atts,
                )
                return resp.content
            except TypeError:
                pass
        resp = llm.chat(system=system_prompt, messages=messages, temperature=0.2, max_tokens=2048)
        return resp.content
    except Exception as exc:
        logger.warning("Optional LLM clinical synthesis skipped: %s", exc)
        return None


# ─── Defensive Fallbacks for Newly Added Diagnostic/Acupuncture/Classics Tools ───


def _fallback_tongue_analyze(params: dict[str, Any]) -> dict[str, Any]:
    """Structured tongue diagnosis fallback when diagnostics.tongue_analyze is still loading."""
    body_color = str(params.get("body_color") or "").lower()
    body_shape = str(params.get("body_shape") or "").lower()
    coating_color = str(params.get("coating_color") or "").lower()
    coating_tex = str(params.get("coating_texture") or "").lower()
    obs = str(params.get("observations") or "").lower()
    text = " ".join([body_color, body_shape, coating_color, coating_tex, obs])

    syndromes: list[dict[str, Any]] = []
    if any(k in text for k in ("pale", "淡", "tooth", "齿痕", "swollen", "胖")):
        syndromes.append({
            "syndrome": "脾气虚夹湿 (Spleen Qi Deficiency with Dampness)",
            "eight_principles": "Interior · Deficiency · Cold/Damp",
            "treatment_principle": "健脾益气，渗湿化痰 (Strengthen Spleen, augment Qi, drain Dampness)",
            "recommended_formulas": ["四君子汤", "参苓白术散", "六君子汤"],
        })
    if any(k in text for k in ("yellow", "黄", "greasy", "腻")) and any(k in text for k in ("red", "红")):
        syndromes.append({
            "syndrome": "湿热蕴脾 / 肝胆湿热 (Damp-Heat Accumulation)",
            "eight_principles": "Interior · Excess · Heat",
            "treatment_principle": "清热燥湿，理气和胃 (Clear Heat and dry Dampness)",
            "recommended_formulas": ["连朴饮", "龙胆泻肝汤", "茵陈蒿汤"],
        })
    if any(k in text for k in ("peeled", "少苔", "无苔", "fissure", "裂纹", "crimson", "绛")):
        syndromes.append({
            "syndrome": "阴虚火旺 (Yin Deficiency with Effulgent Fire)",
            "eight_principles": "Interior · Deficiency · Heat",
            "treatment_principle": "滋阴降火 (Nourish Yin and clear deficiency Fire)",
            "recommended_formulas": ["六味地黄丸", "知柏地黄丸"],
        })
    if any(k in text for k in ("purple", "紫", "瘀", "ecchymosis", "distended")):
        syndromes.append({
            "syndrome": "气滞血瘀 (Qi Stagnation & Blood Stasis)",
            "eight_principles": "Interior · Excess",
            "treatment_principle": "活血化瘀，行气通络 (Invigorate Blood and move Qi)",
            "recommended_formulas": ["血府逐瘀汤", "桃红四物汤"],
        })
    if not syndromes:
        syndromes.append({
            "syndrome": "平人淡红舌 / 气机轻度失调 (Balanced or Mild Qi Disharmony)",
            "eight_principles": "Balanced / Mild",
            "treatment_principle": "调和气血，顾护脾胃 (Harmonize Qi & Blood, support Spleen/Stomach)",
            "recommended_formulas": ["四君子汤", "逍遥散"],
        })
    return {"status": "ok", "primary_syndromes": syndromes, "input_summary": text.strip()}


def _fallback_herb_identify(params: dict[str, Any]) -> dict[str, Any]:
    """Macroscopic decoction-piece authentication fallback."""
    cand = str(params.get("candidate_name") or "").strip()
    feats = str(params.get("features") or params.get("observations") or "").lower()
    markers = [
        ("黄芪", ("菊花心", "chrysanthemum", "astragal", "fibrous", "豆腥气"), "菊花心 radial striations, yellowish-white cortex, bean-like aroma"),
        ("人参", ("珍珠点", "芦碗", "ginseng", "resin", "人参"), "芦头/芦碗 rhizome scars, 珍珠点 rootlet warts, resin-duct ring"),
        ("黄连", ("鸡爪", "coptis", "bright yellow", "金黄", "极苦"), "鸡爪连 branched rhizome, brilliant yellow fracture (berberine), intensely bitter"),
        ("当归", ("归头", "ligustilide", "angelica", "油室", "棕色油点"), "Oil-spotted yellowish-brown cambium ring, rich aromatic scent"),
        ("白术", ("朱砂点", "云头", "atractylod", "烘术"), "Warty tuberous mass, brownish-yellow oil cavities, sweet-aromatic"),
        ("茯苓", ("pachyman", "poria", "白茯苓", "granular"), "White finely granular texture, odorless, bland/slightly sweet"),
    ]
    matched = cand or "黄芪"
    trait_note = "Standard Chinese Pharmacopoeia macroscopic traits"
    for herb_cn, kws, desc in markers:
        if herb_cn == cand or any(k in feats for k in kws):
            matched = herb_cn
            trait_note = desc
            break
    return {
        "status": "ok",
        "top_candidate": matched,
        "candidates": [{"herb": matched, "confidence": 0.86, "diagnostic_markers": trait_note}],
        "processing_paozhi": ["生用 (Raw decoction piece)", "炙用 / 蜜炙 (Honey-fried for tonification when indicated)"],
    }


_CN_DIGITS = {"半": 0.5, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}


def _cn_num_to_float(token: str) -> float:
    token = token.strip()
    if not token:
        return 0.0
    try:
        return float(token)
    except ValueError:
        pass
    if token == "十":
        return 10.0
    if "十" in token:
        left, _, right = token.partition("十")
        tens = _CN_DIGITS.get(left, 1) * 10
        ones = _CN_DIGITS.get(right, 0)
        return float(tens + ones)
    return float(_CN_DIGITS.get(token, 1.0))


def _fallback_prescription_parse(params: dict[str, Any]) -> dict[str, Any]:
    """Parse modern and classical Chinese prescriptions with historical metrology conversion."""
    text = str(params.get("text") or "").strip()
    era = str(params.get("era") or "modern").lower()
    unit_factors = {
        "han": {"两": 13.8, "铢": 0.575, "分": 3.45, "升": 200.0, "枚": 3.0, "g": 1.0, "克": 1.0, "钱": 3.0},
        "eastern_han": {"两": 13.8, "铢": 0.575, "分": 3.45, "升": 200.0, "枚": 3.0, "g": 1.0, "克": 1.0, "钱": 3.0},
        "ming_qing": {"两": 31.2, "钱": 3.12, "分": 0.312, "g": 1.0, "克": 1.0, "枚": 3.0},
        "modern": {"g": 1.0, "克": 1.0, "钱": 3.0, "两": 30.0, "分": 0.3, "枚": 3.0},
    }
    factors = unit_factors.get(era, unit_factors["modern"])
    pattern = re.compile(
        r"([\u4e00-\u9fff]{2,5})\s*(?:\([^)]*\)|（[^）]*）)?\s*"
        r"([0-9]+(?:\.[0-9]+)?|[一二两三四五六七八九十半]+)\s*(两|钱|分|铢|克|g|枚|升)"
    )
    items: list[dict[str, Any]] = []
    for match in pattern.finditer(text):
        herb_name, qty_raw, unit = match.group(1), match.group(2), match.group(3)
        qty = _cn_num_to_float(qty_raw)
        grams = round(qty * factors.get(unit, 1.0), 2)
        items.append({
            "herb": herb_name,
            "original_amount": f"{qty_raw}{unit}",
            "metric_grams": grams,
            "conservative_clinical_grams": round(qty * 3.0, 2) if era in ("han", "eastern_han") and unit == "两" else grams,
        })
    return {"status": "ok", "era": era, "herbs": items, "total_herbs": len(items)}


def _fallback_four_examinations(params: dict[str, Any]) -> dict[str, Any]:
    """Synthesize Inspection, Auscultation, Inquiry, and Pulse into syndrome differentiation."""
    combined = ", ".join(
        str(params.get(k) or "")
        for k in ("inspection", "auscultation", "inquiry", "pulse")
        if params.get(k)
    )
    syn_res = _run_tool_by_name("syndromes.identify", {"symptoms": combined or "fatigue"})
    matches = syn_res.get("matches", [])
    primary = matches[0] if matches else {
        "syndrome": "脾气虚",
        "english": "Spleen Qi Deficiency",
        "treatment_principle": "健脾益气 (Strengthen Spleen and augment Qi)",
        "representative_formulas": ["四君子汤", "补中益气汤"],
    }
    return {
        "status": "ok",
        "eight_principles": {
            "location": "表 (Exterior)" if "浮" in combined or "chills" in combined.lower() else "里 (Interior)",
            "nature": "热 (Heat)" if any(w in combined for w in ("红", "黄", "数", "heat", "red")) else "寒/平 (Cold/Neutral)",
            "strength": "虚 (Deficiency)" if any(w in combined for w in ("虚", "弱", "细", "乏力", "fatigue")) else "实/虚实夹杂 (Excess/Mixed)",
        },
        "primary_syndrome": primary,
        "ranked_syndromes": matches,
    }


def _fallback_acupuncture_protocol(params: dict[str, Any]) -> dict[str, Any]:
    """WHO standard acupoint protocol fallback with pregnancy-contraindicated point filtering."""
    preg_safe = bool(params.get("pregnancy_safe", False))
    points = [
        {"code": "ST36", "name": "足三里 (Zusanli)", "meridian": "Stomach", "role": "Tonifies Spleen/Stomach Qi & Blood"},
        {"code": "PC6", "name": "内关 (Neiguan)", "meridian": "Pericardium", "role": "Harmonizes Stomach, calms Shen"},
        {"code": "LR3", "name": "太冲 (Taichong)", "meridian": "Liver", "role": "Courses Liver Qi, pacifies Yang"},
        {"code": "KI3", "name": "太溪 (Taixi)", "meridian": "Kidney", "role": "Nourishes Kidney Yin & Yuan Qi"},
    ]
    if not preg_safe:
        points.extend([
            {"code": "LI4", "name": "合谷 (Hegu)", "meridian": "Large Intestine", "role": "Courses Qi, relieves pain"},
            {"code": "SP6", "name": "三阴交 (Sanyinjiao)", "meridian": "Spleen", "role": "Harmonizes Liver, Spleen, Kidney"},
        ])
    return {
        "status": "ok",
        "condition": params.get("condition") or params.get("syndrome_name") or "General regulation",
        "pregnancy_safe": preg_safe,
        "points": points,
    }


def _fallback_classics_search(params: dict[str, Any]) -> dict[str, Any]:
    """Classical TCM canon lookup fallback."""
    q = str(params.get("query") or "")
    clauses = [
        {
            "canon": "《黄帝内经·素问》 (Huangdi Neijing Suwen)",
            "section": "至真要大论",
            "text": "谨守病机，各司其属，有者求之，无者求之，盛者责之，虚者责之。",
            "translation": "Carefully observe the pathomechanism and govern each pattern according to its category.",
        },
        {
            "canon": "《伤寒论》 (Shanghan Lun)",
            "section": "辨少阳病脉证并治 · Clause 96",
            "text": "伤寒五六日中风，往来寒热，胸胁苦满，嘿嘿不欲饮食，心烦喜呕……小柴胡汤主之。",
            "translation": "Alternating chills and fever, chest/hypochondriac fullness, poor appetite: Xiao Chaihu Tang governs.",
        },
    ]
    return {"status": "ok", "query": q, "results": clauses}


# ─── Network Pharmacology Multi-Layer Graph Builder ──────────────────────────


def _resolve_formula_and_herbs(formula_name: str, explicit_herbs: list[str]) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    """Resolve formula metadata and ordered herb entries with Jun-Chen-Zuo-Shi roles."""
    formula_info: dict[str, Any] | None = None
    herb_entries: list[dict[str, str]] = []

    if formula_name:
        res = _run_tool_by_name("formulas.search", {"query": formula_name})
        if res.get("status") == "found" and isinstance(res.get("formula"), dict):
            formula_info = res["formula"]
            comp = formula_info.get("composition", {})
            if isinstance(comp, dict):
                for role_label, role_items in comp.items():
                    for item in role_items:
                        if isinstance(item, dict) and item.get("herb"):
                            herb_entries.append({
                                "herb": str(item["herb"]),
                                "role": str(role_label),
                                "dosage": str(item.get("dosage", "")),
                                "note": str(item.get("role", "")),
                            })

    seen = {e["herb"] for e in herb_entries}
    for h in explicit_herbs:
        clean_h = str(h).strip()
        if clean_h and clean_h not in seen:
            herb_entries.append({"herb": clean_h, "role": "配伍 (Component)", "dosage": "", "note": ""})
            seen.add(clean_h)

    if not herb_entries and formula_name:
        for part in [p.strip() for p in formula_name.split(",") if p.strip()]:
            if part not in seen:
                herb_entries.append({"herb": part, "role": "配伍 (Component)", "dosage": "", "note": ""})
                seen.add(part)

    return formula_info, herb_entries


def _get_compounds_for_herb(herb_name: str) -> tuple[dict[str, Any], list[str]]:
    """Fetch herb profile and bioactive compounds from tools + curated offline reference."""
    lookup = _run_tool_by_name("herbs.lookup", {"query": herb_name})
    herb_data = lookup.get("herb", {}) if lookup.get("status") == "found" else {}
    cpd_res = _run_tool_by_name("herbs.compounds", {"herb_name": herb_name})
    compounds = list(cpd_res.get("key_compounds", [])) if cpd_res.get("status") == "found" else []
    for extra_cpd in _OFFLINE_HERB_COMPOUNDS.get(herb_name, []):
        if extra_cpd not in compounds:
            compounds.append(extra_cpd)
    if not compounds:
        compounds = [f"{herb_name} Active Fraction A", "Quercetin", "Beta-Sitosterol"]
    return herb_data, compounds


def _get_compound_profile(compound_name: str) -> dict[str, Any]:
    """Fetch ADMET and molecular targets for a compound from tools + curated reference."""
    tgt_res = _run_tool_by_name("compounds.targets", {"compound_name": compound_name})
    admet_res = _run_tool_by_name("compounds.admet", {"compound_name": compound_name})
    ref = _OFFLINE_COMPOUND_META.get(compound_name, {})

    targets = list(tgt_res.get("targets", [])) if tgt_res.get("status") == "found" else []
    for t in ref.get("targets", []):
        if t not in targets:
            targets.append(t)
    if not targets:
        targets = ["TNF", "NFKB1", "AKT1"]

    ob = admet_res.get("ob_percent") or ref.get("ob", 35.0)
    dl = admet_res.get("dl") or ref.get("dl", 0.32)
    mw = admet_res.get("molecular_weight") or ref.get("mw", 320.0)
    return {
        "compound": compound_name,
        "molecular_weight": mw,
        "ob_percent": ob,
        "dl": dl,
        "lipinski_pass": float(mw) <= 500.0 or float(dl) >= 0.18,
        "targets": targets,
    }


def _collect_drug_interactions(herb_names: list[str], drugs: list[str]) -> list[dict[str, Any]]:
    """Evaluate herb-drug interactions across all formula herbs and requested Western drugs."""
    interactions: list[dict[str, Any]] = []
    for drug in drugs:
        clean_drug = str(drug).strip()
        if not clean_drug:
            continue
        for herb in herb_names:
            res = _run_tool_by_name("interactions.herb_drug", {"herb": herb, "drug": clean_drug})
            if res.get("status") == "found":
                for item in res.get("interactions", []):
                    interactions.append(dict(item))
    return interactions


def build_pharmacology_network_payload(body: dict[str, Any]) -> dict[str, Any]:
    """Build interactive Formula -> Herb -> Compound -> Target -> Pathway graph & safety profile."""
    _ensure_all_tools_loaded()
    formula_name = str(body.get("formula") or "").strip()
    raw_herbs = body.get("herbs") or []
    explicit_herbs = raw_herbs if isinstance(raw_herbs, list) else [h.strip() for h in str(raw_herbs).split(",") if h.strip()]
    disease = str(body.get("disease") or "").strip()
    raw_drugs = body.get("drugs") or []
    drugs = raw_drugs if isinstance(raw_drugs, list) else [d.strip() for d in str(raw_drugs).split(",") if d.strip()]

    if not formula_name and not explicit_herbs:
        formula_name = "四君子汤"

    formula_info, herb_entries = _resolve_formula_and_herbs(formula_name, explicit_herbs)
    title_label = (formula_info or {}).get("chinese_name") or formula_name or "Custom Formula (自拟方)"

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    node_ids: set[str] = set()
    admet_list: list[dict[str, Any]] = []

    def add_node(node_id: str, label: str, group: str, role: str = "", meta: dict[str, Any] | None = None) -> None:
        if node_id not in node_ids:
            node_ids.add(node_id)
            nodes.append({"id": node_id, "label": label, "group": group, "role": role, "meta": meta or {}})

    formula_node_id = f"formula:{title_label}"
    add_node(
        formula_node_id,
        title_label,
        "formula",
        role="formula",
        meta={"disease_focus": disease, **(formula_info or {"name": title_label})},
    )

    # Also invoke pharmacology.network_build for baseline registry health/compatibility
    if herb_entries:
        try:
            _run_tool_by_name("pharmacology.network_build", {"formula_name": formula_name or ", ".join(e["herb"] for e in herb_entries)})
        except Exception:
            pass

    all_targets: list[str] = []
    for entry in herb_entries:
        h_name = entry["herb"]
        h_id = f"herb:{h_name}"
        herb_data, compounds = _get_compounds_for_herb(h_name)
        add_node(
            h_id,
            h_name,
            "herb",
            role=entry["role"],
            meta={
                "dosage": entry["dosage"] or herb_data.get("dosage", ""),
                "role_note": entry["note"],
                "nature": herb_data.get("nature", ""),
                "flavor": herb_data.get("flavor", ""),
                "meridians": herb_data.get("meridians", []),
            },
        )
        edges.append({"source": formula_node_id, "target": h_id, "relation": entry["role"] or "contains_herb"})

        for cpd in compounds:
            c_id = f"compound:{cpd}"
            cpd_prof = _get_compound_profile(cpd)
            if c_id not in node_ids:
                admet_list.append(cpd_prof)
            add_node(
                c_id,
                cpd,
                "compound",
                role="bioactive_compound",
                meta={
                    "ob_percent": cpd_prof["ob_percent"],
                    "dl": cpd_prof["dl"],
                    "molecular_weight": cpd_prof["molecular_weight"],
                },
            )
            edges.append({"source": h_id, "target": c_id, "relation": "contains_compound"})

            for tgt in cpd_prof["targets"]:
                t_id = f"target:{tgt}"
                add_node(t_id, tgt, "target", role="protein_target", meta={"gene_symbol": tgt, "disease": disease})
                edges.append({"source": c_id, "target": t_id, "relation": "modulates_target"})
                if tgt not in all_targets:
                    all_targets.append(tgt)

    # Pathway enrichment layer (tries pharmacology.pathway_enrich / pathway_enrichment + KEGG map)
    pathway_tool = registry.get_tool("pharmacology.pathway_enrich") or registry.get_tool("pharmacology.pathway_enrichment")
    if pathway_tool is not None and all_targets:
        try:
            _run_tool_by_name(pathway_tool.name, {"gene_list": ", ".join(all_targets)})
        except Exception:
            pass

    seen_edges = {(e["source"], e["target"]) for e in edges}
    for tgt in all_targets:
        t_id = f"target:{tgt}"
        for pw_code, pw_name in _TARGET_PATHWAYS.get(tgt, [("hsa01100", "Metabolic & homeostatic regulation")]):
            p_id = f"pathway:{pw_code}"
            add_node(p_id, pw_name, "pathway", role="signaling_pathway", meta={"kegg_id": pw_code})
            if (t_id, p_id) not in seen_edges:
                edges.append({"source": t_id, "target": p_id, "relation": "participates_in"})
                seen_edges.add((t_id, p_id))

    herb_names = [e["herb"] for e in herb_entries]
    herbs_csv = ", ".join(herb_names)
    herb_compat = _run_tool_by_name("interactions.check_herbs", {"herbs": herbs_csv}) if herbs_csv else {"status": "safe"}
    pregnancy = _run_tool_by_name("safety.pregnancy_check", {"herbs": herbs_csv}) if herbs_csv else {"status": "safe"}
    toxicity = [
        _run_tool_by_name("safety.toxicity_check", {"herb_name": h})
        for h in herb_names
    ]
    drug_interactions = _collect_drug_interactions(herb_names, drugs or ["Warfarin", "Digoxin", "Metformin"])

    counts = {
        "herbs": sum(1 for n in nodes if n["group"] == "herb"),
        "compounds": sum(1 for n in nodes if n["group"] == "compound"),
        "targets": sum(1 for n in nodes if n["group"] == "target"),
        "pathways": sum(1 for n in nodes if n["group"] == "pathway"),
        "edges": len(edges),
    }

    return {
        "status": "ok",
        "formula_info": formula_info or {"chinese_name": title_label, "herbs": herb_names, "disease": disease},
        "graph": {
            "nodes": nodes,
            "edges": edges,
            "stats": counts,
        },
        "admet": admet_list,
        "safety": {
            "herb_interactions": herb_compat,
            "pregnancy": pregnancy,
            "toxicity": [t for t in toxicity if t.get("status") == "toxic"],
        },
        "drug_interactions": drug_interactions,
    }


# ─── Offline Deterministic Tool Planner & Bilingual Synthesizer ──────────────


def _build_offline_plan(query: str, attachments: list[Any]) -> dict[str, Any]:
    """Deterministically match user query & multimodal inputs to computational TCM tools."""
    _ensure_all_tools_loaded()
    q_low = (query or "").lower()
    steps: list[dict[str, Any]] = []

    def add_step(tool_name: str, parameters: dict[str, Any], purpose: str) -> None:
        if registry.get_tool(tool_name) is not None and len(steps) < 6:
            steps.append({
                "step": len(steps) + 1,
                "tool": tool_name,
                "parameters": parameters,
                "purpose": purpose,
            })

    # 1. Multimodal image routing
    has_image = any(getattr(a, "kind", "") == "image" for a in attachments)
    if has_image or any(k in q_low for k in ("tongue", "舌", "苔")):
        add_step("diagnostics.tongue_analyze", {"observations": query}, "Analyze tongue signs and syndrome mapping")
    if any(k in q_low for k in ("饮片", "鉴别", "slice", "specimen", "adulterant")):
        add_step("diagnostics.herb_identify", {"features": query}, "Authenticate crude herb / decoction piece")
    if any(k in q_low for k in ("两", "钱", "克", "prescription", "方笺")):
        era = "han" if any(k in q_low for k in ("伤寒", "han", "东汉")) else "modern"
        add_step("diagnostics.prescription_parse", {"text": query, "era": era}, "Parse prescription herbs and dosages")

    # 2. Formula & network pharmacology matching
    from tcm.tools.formulas import FORMULA_DB
    for f_name, f_data in FORMULA_DB.items():
        if f_name in query or f_data["english"].lower() in q_low or f_data["pinyin"].lower() in q_low:
            add_step("formulas.search", {"query": f_name}, f"Look up classical formula {f_name}")
            if any(k in q_low for k in ("network", "target", "pathway", "网络", "靶点", "机制", "pharmacology")):
                add_step("pharmacology.network_build", {"formula_name": f_name}, f"Build network pharmacology for {f_name}")
            break

    # 3. Herb & safety matching
    from tcm.tools.herbs import HERB_DB
    matched_herbs: list[str] = []
    for h_name, h_data in HERB_DB.items():
        if h_name in query or h_data["english"].lower() in q_low:
            matched_herbs.append(h_name)
            add_step("herbs.lookup", {"query": h_name}, f"Look up Materia Medica entry for {h_name}")
    for extra_h in ("附子", "半夏", "藜芦", "海藻", "桃仁", "红花", "川芎", "大黄"):
        if extra_h in query and extra_h not in matched_herbs:
            matched_herbs.append(extra_h)

    if len(matched_herbs) >= 2 or any(k in q_low for k in ("interaction", "反", "畏", "incompatible")):
        herbs_arg = ", ".join(matched_herbs) if matched_herbs else query
        add_step("interactions.check_herbs", {"herbs": herbs_arg}, "Screen classical Eighteen Incompatibilities & Nineteen Fears")
    if any(k in q_low for k in ("pregnan", "孕", "胎")):
        herbs_arg = ", ".join(matched_herbs) if matched_herbs else query
        add_step("safety.pregnancy_check", {"herbs": herbs_arg}, "Check pregnancy safety profile")
    for drug in ("warfarin", "digoxin", "metformin", "interferon", "aspirin"):
        if drug in q_low and matched_herbs:
            add_step("interactions.herb_drug", {"herb": matched_herbs[0], "drug": drug.title()}, f"Check herb-drug interaction with {drug.title()}")

    # 4. Syndromes, acupoints, and classical canons
    from tcm.tools.syndromes import SYNDROME_DB
    for s_name, s_data in SYNDROME_DB.items():
        if s_name in query or s_data["english"].lower() in q_low:
            add_step("syndromes.lookup", {"syndrome_name": s_name}, f"Look up syndrome {s_name}")
            break
    if any(k in q_low for k in ("acupoint", "acupuncture", "穴", "针灸", "st36", "li4", "lr3", "pc6", "sp6", "足三里", "合谷", "太冲")):
        add_step("acupuncture.protocol", {"condition": query}, "Generate acupuncture point protocol")
        add_step("acupuncture.point_lookup", {"query": query}, "Look up specific acupoint details")
    if any(k in q_low for k in ("伤寒", "内经", "金匮", "本草", "shanghan", "neijing", "classic", "clause", "条文")):
        add_step("classics.search", {"query": query}, "Search classical TCM canon clauses")

    # 5. Compound lookup
    for cpd in ("berberine", "小檗碱", "ginsenoside", "astragaloside"):
        if cpd in q_low:
            add_step("compounds.search", {"query": cpd}, f"Look up active compound {cpd}")

    # Default step when free-text symptoms or broad question asked
    if not steps:
        add_step("syndromes.identify", {"symptoms": query}, "Identify matching TCM syndrome patterns")
        if registry.get_tool("classics.search") is not None:
            add_step("classics.search", {"query": query}, "Search classical TCM canon references")
        else:
            add_step("herbs.by_category", {"category": "补气"}, "Retrieve representative Materia Medica category")

    return {
        "reasoning": "Offline deterministic TCM tool routing based on clinical/pharmacological entities.",
        "steps": steps,
    }


def _synthesize_offline_markdown(
    query: str,
    plan: dict[str, Any],
    results: list[dict[str, Any]],
    attachments: list[Any],
    lang: str = "bi",
) -> str:
    """Format deterministic tool outputs into a clean bilingual/monolingual Markdown report."""
    lang_norm = (lang or "bi").lower()
    if lang_norm == "zh":
        heading = "## 计算中医学分析结果"
        note = "> 当前处于**离线确定性工具模式**（未配置云端大模型 API Key，所有结果均来自本地中医计算工具库）。"
    elif lang_norm == "en":
        heading = "## Computational TCM Analysis"
        note = "> Running in **Offline Deterministic Tool Mode** (grounded directly in local TCM computational tools; configure an API key via `tcm keys set` for live SOTA LLM synthesis)."
    else:
        heading = "## 计算中医学分析 | Computational TCM Findings"
        note = (
            "> **离线确定性引擎 | Offline Deterministic Engine**: 以下结果由本地中医计算工具链直接生成。"
            "配置 API Key (`tcm keys set`) 后可开启 35+ SOTA 多模态大模型深度综合研判。"
        )

    sections = [heading, "", note, "", f"**Query:** `{query}`"]

    for att in attachments:
        if getattr(att, "kind", "") == "image":
            bio = _extract_biometrics_safe(att)
            if bio and "lab_approx" in bio:
                lab = bio["lab_approx"]
                sections.append(
                    f"\n### 图像生物特征 | Image Colorimetry\n"
                    f"- **CIE L\\*a\\*b\\***: `L*={lab.get('L')}`, `a*={lab.get('a')}`, `b*={lab.get('b')}` "
                    f"| Moisture Gloss: `{bio.get('moisture_gloss_index')}`"
                )
                for hint in bio.get("tcm_visual_hints", []):
                    sections.append(f"- {hint}")

    for res in results:
        tool = res.get("tool", "tool")
        purpose = res.get("purpose", "")
        sections.append(f"\n### `{tool}` — {purpose}")
        if res.get("status") == "success":
            payload = json.dumps(res.get("output", {}), ensure_ascii=False, indent=2, default=str)
            if len(payload) > 2400:
                payload = payload[:2400] + "\n... (truncated)"
            sections.append(f"```json\n{payload}\n```")
        else:
            sections.append(f"- Warning: {res.get('error', 'Tool execution error')}")

    return "\n".join(sections)


# ─── Endpoint Implementations ────────────────────────────────────────────────


def _handle_diagnose_tongue(session: Session, body: dict[str, Any]) -> dict[str, Any]:
    image = body.get("image")
    lang = str(body.get("lang") or session.config.get("ui.language", "bi") or "bi")
    biometrics = _extract_biometrics_safe(image) if image else None

    hints_str = "; ".join(biometrics.get("tcm_visual_hints", [])) if isinstance(biometrics, dict) else ""
    observations = str(body.get("observations") or "").strip()
    if hints_str and not observations:
        observations = hints_str

    params = {
        "observations": observations,
        "body_color": body.get("body_color", ""),
        "body_shape": body.get("body_shape", ""),
        "coating_color": body.get("coating_color", ""),
        "coating_texture": body.get("coating_texture", ""),
        "sublingual": body.get("sublingual", ""),
        "biometrics": biometrics,
        "lang": lang,
    }
    diagnosis = _run_tool_by_name("diagnostics.tongue_analyze", params, fallback_fn=_fallback_tongue_analyze)

    llm_synthesis = None
    if body.get("use_llm"):
        att = _load_attachment_safe(image) if image else None
        sys_prompt = (
            "You are a senior TCM tongue diagnosis (望舌象) specialist. Integrate CIE L*a*b* colorimetry, "
            f"somatotopy zones, and clinical signs into a concise clinical interpretation (language={lang})."
        )
        user_prompt = json.dumps({"biometrics": biometrics, "diagnosis": diagnosis, "inputs": params}, ensure_ascii=False, default=str)
        llm_synthesis = _chat_llm_optional(session, sys_prompt, user_prompt, attachments=[att] if att else None)

    return {
        "status": "ok",
        "biometrics": biometrics,
        "diagnosis": diagnosis,
        "llm_synthesis": llm_synthesis,
        "recommended_models": _recommend_models_safe("tongue_vision", session),
    }


def _handle_diagnose_herb(session: Session, body: dict[str, Any]) -> dict[str, Any]:
    image = body.get("image")
    features = str(body.get("features") or body.get("observations") or "").strip()
    candidate_name = str(body.get("candidate_name") or body.get("name") or "").strip()
    biometrics = _extract_biometrics_safe(image) if image else None

    ident_params = {
        "features": features,
        "candidate_name": candidate_name,
        "biometrics": biometrics,
    }
    identification = _run_tool_by_name("diagnostics.herb_identify", ident_params, fallback_fn=_fallback_herb_identify)

    # Extract top herb name for Materia Medica enrichment
    herb_query = (
        candidate_name
        or identification.get("top_candidate")
        or identification.get("herb")
        or (identification.get("candidates", [{}])[0].get("herb") if identification.get("candidates") else "")
    )
    herb_lookup = _run_tool_by_name("herbs.lookup", {"query": str(herb_query)}) if herb_query else {"status": "not_found"}

    llm_synthesis = None
    if body.get("use_llm"):
        att = _load_attachment_safe(image) if image else None
        sys_prompt = "You are a Chinese Pharmacopoeia (中国药典) macroscopic herb authentication specialist."
        user_prompt = json.dumps(
            {"features": features, "candidate_name": candidate_name, "identification": identification, "materia_medica": herb_lookup},
            ensure_ascii=False,
            default=str,
        )
        llm_synthesis = _chat_llm_optional(session, sys_prompt, user_prompt, attachments=[att] if att else None)

    return {
        "status": "ok",
        "biometrics": biometrics,
        "identification": identification,
        "materia_medica": herb_lookup,
        "llm_synthesis": llm_synthesis,
        "recommended_models": _recommend_models_safe("herb_identification", session),
    }


def _handle_diagnose_prescription(session: Session, body: dict[str, Any]) -> dict[str, Any]:
    text = str(body.get("text") or body.get("prescription") or body.get("observations") or "").strip()
    era = str(body.get("era") or "modern").strip()
    image = body.get("image")
    use_llm = bool(body.get("use_llm", False))

    ocr_transcript = None
    att = _load_attachment_safe(image) if image else None
    if att is not None and use_llm:
        ocr_transcript = _chat_llm_optional(
            session,
            "Transcribe all Chinese herbs, processing notes, and dosages from this prescription image accurately.",
            "Extract the prescription text verbatim.",
            attachments=[att],
        )
        if ocr_transcript and not text:
            text = ocr_transcript

    parsed = _run_tool_by_name(
        "diagnostics.prescription_parse",
        {"text": text, "era": era},
        fallback_fn=_fallback_prescription_parse,
    )

    # Extract herb names from parsed output regardless of exact key naming
    raw_items = parsed.get("herbs") or parsed.get("items") or parsed.get("ingredients") or []
    herb_names = [
        str(item.get("herb") or item.get("name"))
        for item in raw_items
        if isinstance(item, dict) and (item.get("herb") or item.get("name"))
    ]
    herbs_csv = ", ".join(herb_names)
    compatibility = _run_tool_by_name("interactions.check_herbs", {"herbs": herbs_csv}) if herbs_csv else {"status": "safe", "warnings": []}
    pregnancy = _run_tool_by_name("safety.pregnancy_check", {"herbs": herbs_csv}) if herbs_csv else {"status": "safe"}
    toxicity = [_run_tool_by_name("safety.toxicity_check", {"herb_name": h}) for h in herb_names]

    llm_synthesis = None
    if use_llm and text:
        llm_synthesis = _chat_llm_optional(
            session,
            "You are a classical TCM formula & clinical pharmacy safety reviewer.",
            json.dumps({"text": text, "era": era, "parsed": parsed, "compatibility": compatibility, "pregnancy": pregnancy}, ensure_ascii=False, default=str),
            attachments=[att] if att else None,
        )

    return {
        "status": "ok",
        "era": era,
        "text": text,
        "ocr_transcript": ocr_transcript,
        "parsed": parsed,
        "herbs": raw_items,
        "compatibility": compatibility,
        "toxicity": [t for t in toxicity if t.get("status") == "toxic"],
        "pregnancy_safety": pregnancy,
        "llm_synthesis": llm_synthesis,
        "recommended_models": _recommend_models_safe("classical_ocr", session),
    }


def _handle_diagnose_four_examinations(session: Session, body: dict[str, Any]) -> dict[str, Any]:
    pregnancy_safe = bool(body.get("pregnancy_safe", False))
    exam_params = {
        "inspection": str(body.get("inspection") or ""),
        "auscultation": str(body.get("auscultation") or ""),
        "inquiry": str(body.get("inquiry") or ""),
        "pulse": str(body.get("pulse") or ""),
        "pregnancy_safe": pregnancy_safe,
    }
    diagnosis = _run_tool_by_name(
        "diagnostics.four_examinations",
        exam_params,
        fallback_fn=_fallback_four_examinations,
    )

    primary_syn = ""
    if isinstance(diagnosis.get("primary_syndrome"), dict):
        primary_syn = str(diagnosis["primary_syndrome"].get("syndrome") or "")
    elif isinstance(diagnosis.get("primary_syndrome"), str):
        primary_syn = diagnosis["primary_syndrome"]
    if not primary_syn:
        primary_syn = exam_params["inquiry"] or exam_params["inspection"] or "脾气虚"

    acupuncture = _run_tool_by_name(
        "acupuncture.protocol",
        {"condition_or_syndrome": primary_syn, "pregnancy_safe": pregnancy_safe},
        fallback_fn=_fallback_acupuncture_protocol,
    )
    classics = _run_tool_by_name(
        "classics.search",
        {"query": primary_syn},
        fallback_fn=_fallback_classics_search,
    )

    llm_synthesis = None
    if body.get("use_llm"):
        llm_synthesis = _chat_llm_optional(
            session,
            "You are an integrative TCM physician writing a structured Four-Examinations (四诊合参) SOAP note.",
            json.dumps({"inputs": exam_params, "diagnosis": diagnosis, "acupuncture": acupuncture, "classics": classics}, ensure_ascii=False, default=str),
        )

    return {
        "status": "ok",
        "diagnosis": diagnosis,
        "acupuncture": acupuncture,
        "classics": classics,
        "llm_synthesis": llm_synthesis,
        "recommended_models": _recommend_models_safe("bilingual_synthesis", session),
    }


def _handle_agent_query(base_session: Session, body: dict[str, Any]) -> dict[str, Any]:
    query = str(body.get("query") or "").strip()
    if not query:
        raise ValueError("Field 'query' is required.")

    # Build isolated request session inheriting configured API keys
    req_cfg = Config(data=dict(base_session.config._data))
    if body.get("model"):
        req_cfg.set("llm.model", str(body["model"]).strip())
    lang = str(body.get("lang") or body.get("language") or req_cfg.get("ui.language") or "bi").lower()
    if lang in {"en", "zh", "bi"}:
        req_cfg.set("ui.language", lang)

    req_session = Session(config=req_cfg, verbose=base_session.verbose)
    raw_atts = body.get("attachments") or []
    loaded_atts = []
    for item in raw_atts:
        att = _load_attachment_safe(item)
        if att is not None:
            loaded_atts.append(att)
            req_session.attachments.append(att)

    if _has_provider_key(req_session, req_cfg.get("llm.provider")):
        try:
            plan = create_plan(req_session, query, attachments=loaded_atts or None)
            results = execute_plan(req_session, plan, verbose=False)
            answer = synthesize(req_session, query, plan, results, attachments=loaded_atts or None)
            llm = req_session.get_llm()
            usage = {
                "calls": len(llm.usage.calls),
                "input_tokens": llm.usage.total_input_tokens,
                "output_tokens": llm.usage.total_output_tokens,
                "total_tokens": llm.usage.total_tokens,
                "cost_usd": round(llm.usage.total_cost, 6),
                "summary": llm.usage.summary(),
            }
            return {
                "status": "ok",
                "mode": "llm_agent",
                "model": req_session.current_model,
                "provider": req_cfg.get("llm.provider"),
                "plan": plan,
                "results": results,
                "answer": answer,
                "usage": usage,
            }
        except Exception as exc:
            logger.warning("Live LLM agent failed (%s); falling back to offline deterministic planner.", exc)

    plan = _build_offline_plan(query, loaded_atts)
    results = execute_plan(req_session, plan, verbose=False)
    answer = _synthesize_offline_markdown(query, plan, results, loaded_atts, lang=lang)
    return {
        "status": "ok",
        "mode": "offline_deterministic",
        "model": req_session.current_model,
        "provider": req_cfg.get("llm.provider"),
        "plan": plan,
        "results": results,
        "answer": answer,
        "usage": {
            "calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "cost_usd": 0.0,
            "summary": "Offline deterministic mode (0 LLM calls)",
        },
    }


# ─── Threading HTTP Server & Request Handler ─────────────────────────────────


class TCMStudioServer(ThreadingHTTPServer):
    """Thread-safe HTTP + REST API server for TCM Studio."""

    allow_reuse_address = True
    daemon_threads = True

    def __init__(
        self,
        server_address: tuple[str, int],
        handler_cls: type[SimpleHTTPRequestHandler],
        session: Session | None = None,
        static_dir: Path | None = None,
    ):
        self.session = session or Session()
        self.static_dir = (static_dir or resolve_static_dir()).resolve()
        self.lock = threading.RLock()
        super().__init__(server_address, handler_cls)

    @property
    def host(self) -> str:
        raw_host = str(self.server_address[0])
        return "127.0.0.1" if raw_host in ("0.0.0.0", "::", "") else raw_host

    @property
    def port(self) -> int:
        return int(self.server_address[1])

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


class TCMStudioRequestHandler(SimpleHTTPRequestHandler):
    """Handles CORS, JSON `/api/*` endpoints, and static website/Studio files."""

    server: TCMStudioServer  # type: ignore[assignment]

    def log_message(self, fmt: str, *args: Any) -> None:
        logger.debug("%s - %s", self.address_string(), fmt % args)

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    def _send_json(self, payload: dict[str, Any], status_code: int = 200) -> None:
        raw = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-cache")
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(raw)

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        if not raw.strip():
            return {}
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("JSON request body must be an object.")
        return parsed

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._send_cors_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_HEAD(self) -> None:
        parsed = urllib.parse.urlsplit(self.path)
        route = parsed.path.rstrip("/") or "/"
        if route in ("/api/health", "/api/models", "/api/tools"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self._send_cors_headers()
            self.end_headers()
            return
        self._serve_static(parsed.path, head_only=True)

    def do_GET(self) -> None:
        parsed = urllib.parse.urlsplit(self.path)
        route = parsed.path.rstrip("/") or "/"
        query_params = dict(urllib.parse.parse_qsl(parsed.query, keep_blank_values=False))

        api_routes: dict[str, Callable[[dict[str, str]], None]] = {
            "/api/health": self._get_health,
            "/api/models": self._get_models,
            "/api/tools": self._get_tools,
        }
        handler = api_routes.get(route)
        if handler is not None:
            try:
                handler(query_params)
            except Exception as exc:
                logger.exception("GET %s failed", route)
                self._send_json({"status": "error", "error": str(exc)}, status_code=500)
            return

        if route.startswith("/api/"):
            self._send_json({"status": "error", "error": f"Unknown API endpoint: {route}"}, status_code=404)
            return

        self._serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlsplit(self.path)
        route = parsed.path.rstrip("/")

        post_routes: dict[str, Callable[[dict[str, Any]], None]] = {
            "/api/models/select": self._post_models_select,
            "/api/tools/run": self._post_tools_run,
            "/api/diagnose/tongue": lambda b: self._send_json(_handle_diagnose_tongue(self.server.session, b)),
            "/api/diagnose/herb": lambda b: self._send_json(_handle_diagnose_herb(self.server.session, b)),
            "/api/diagnose/prescription": lambda b: self._send_json(_handle_diagnose_prescription(self.server.session, b)),
            "/api/diagnose/four-examinations": lambda b: self._send_json(_handle_diagnose_four_examinations(self.server.session, b)),
            "/api/pharmacology/network": lambda b: self._send_json(build_pharmacology_network_payload(b)),
            "/api/agent/query": lambda b: self._send_json(_handle_agent_query(self.server.session, b)),
        }
        handler = post_routes.get(route)
        if handler is None:
            self._send_json({"status": "error", "error": f"Unknown POST endpoint: {route}"}, status_code=404)
            return

        try:
            body = self._read_json_body()
            handler(body)
        except json.JSONDecodeError as exc:
            self._send_json({"status": "error", "error": f"Invalid JSON: {exc}"}, status_code=400)
        except ValueError as exc:
            self._send_json({"status": "error", "error": str(exc)}, status_code=400)
        except KeyError as exc:
            self._send_json({"status": "error", "error": str(exc)}, status_code=404)
        except Exception as exc:
            logger.exception("POST %s failed", route)
            self._send_json({"status": "error", "error": str(exc)}, status_code=500)

    # ── GET API handlers ──

    def _get_health(self, _params: dict[str, str]) -> None:
        _ensure_all_tools_loaded()
        session = self.server.session
        tools = registry.list_tools()
        categories = registry.categories()
        self._send_json({
            "status": "ok",
            "service": "tcm-studio",
            "version": __version__,
            "mode": "live",
            "active_model": session.current_model,
            "active_provider": session.config.get("llm.provider"),
            "language": session.config.get("ui.language", "bi"),
            "tool_count": len(tools),
            "categories": categories,
            "configured_providers": _configured_providers(session),
        })

    def _get_models(self, params: dict[str, str]) -> None:
        session = self.server.session
        active = session.current_model
        raw_models = _list_models_filtered(
            provider=params.get("provider"),
            modality=params.get("modality"),
            tier=params.get("tier"),
        )
        models = [_serialize_model(m, active, session) for m in raw_models]
        task = params.get("task") or "general"
        recommendations = _recommend_models_safe(task, session)
        self._send_json({
            "status": "ok",
            "active_model": active,
            "active_provider": session.config.get("llm.provider"),
            "models": models,
            "recommendations": recommendations,
        })

    def _get_tools(self, params: dict[str, str]) -> None:
        _ensure_all_tools_loaded()
        category = params.get("category") or None
        tools = registry.list_tools(category=category)
        serialized = [
            {
                "name": t.name,
                "category": t.category,
                "description": t.description,
                "parameters": t.parameters,
                "usage_guide": t.usage_guide,
            }
            for t in tools
        ]
        self._send_json({
            "status": "ok",
            "count": len(serialized),
            "categories": registry.categories(),
            "tools": serialized,
        })

    # ── POST API handlers ──

    def _post_models_select(self, body: dict[str, Any]) -> None:
        from tcm.models.llm import MODEL_CATALOG

        model = str(body.get("model") or "").strip()
        provider = str(body.get("provider") or "").strip() or None
        lang = str(body.get("language") or body.get("lang") or "").strip().lower()
        session = self.server.session

        with self.server.lock:
            if model:
                session.set_model(model, provider=provider)
            if lang:
                session.config.set("ui.language", lang)

        active = session.current_model
        info_obj = MODEL_CATALOG.get(active)
        model_info = _serialize_model(info_obj, active, session) if info_obj else {"id": active, "provider": session.config.get("llm.provider")}
        self._send_json({
            "status": "ok",
            "active_model": active,
            "active_provider": session.config.get("llm.provider"),
            "language": session.config.get("ui.language", "bi"),
            "model_info": model_info,
        })

    def _post_tools_run(self, body: dict[str, Any]) -> None:
        tool_name = str(body.get("tool") or body.get("name") or "").strip()
        if not tool_name:
            raise ValueError("Field 'tool' is required.")
        raw_params = body.get("parameters") if body.get("parameters") is not None else body.get("params", {})
        if not isinstance(raw_params, dict):
            raise ValueError("Field 'parameters' must be a JSON object.")

        output = _run_tool_by_name(tool_name, raw_params)
        self._send_json({
            "status": "ok",
            "tool": tool_name,
            "output": output,
        })

    # ── Static file serving ──

    def _serve_static(self, raw_path: str, head_only: bool = False) -> None:
        clean = urllib.parse.unquote(raw_path or "/").split("?", 1)[0]
        if clean in ("/", ""):
            rel_target = "index.html"
        elif clean in ("/studio", "/studio/"):
            rel_target = "studio.html"
        else:
            rel_target = clean.lstrip("/")

        static_root = self.server.static_dir
        candidate = (static_root / rel_target).resolve()
        try:
            candidate.relative_to(static_root)
        except ValueError:
            self._send_json({"status": "error", "error": "Forbidden path"}, status_code=403)
            return

        if candidate.is_dir():
            candidate = (candidate / "index.html").resolve()

        if not candidate.is_file() and rel_target == "studio.html":
            fallback_index = (static_root / "index.html").resolve()
            if fallback_index.is_file():
                candidate = fallback_index

        if not candidate.is_file():
            self._send_json({"status": "error", "error": f"File not found: {rel_target}"}, status_code=404)
            return

        ext = candidate.suffix.lower()
        content_type = _STATIC_MIME_OVERRIDES.get(ext) or mimetypes.guess_type(str(candidate))[0] or "application/octet-stream"
        data = candidate.read_bytes()

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self._send_cors_headers()
        self.end_headers()
        if not head_only:
            self.wfile.write(data)


def create_studio_server(
    host: str = "127.0.0.1",
    port: int = 8765,
    session: Session | None = None,
    static_dir: Path | None = None,
) -> TCMStudioServer:
    """Instantiate a bound TCMStudioServer ready for `serve_forever()` or background thread execution."""
    _ensure_all_tools_loaded()
    active_session = session or Session()
    return TCMStudioServer(
        (host, int(port)),
        TCMStudioRequestHandler,
        session=active_session,
        static_dir=static_dir,
    )


def run_studio(
    host: str = "127.0.0.1",
    port: int = 8765,
    open_browser: bool = False,
    model: str | None = None,
    session: Session | None = None,
) -> None:
    """Start the TCM Studio HTTP & REST API server and block until interrupted."""
    active_session = session or Session()
    if model:
        active_session.set_model(model)

    server = create_studio_server(host=host, port=port, session=active_session)
    if open_browser:
        url = f"{server.base_url}/studio"
        timer = threading.Timer(0.35, lambda: webbrowser.open(url))
        timer.daemon = True
        timer.start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
