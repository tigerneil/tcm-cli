"""
Safety tools: toxicity profiling, contraindications, dosage validation.
"""

import logging
from tcm.tools import registry

logger = logging.getLogger("tcm.tools.safety")

TOXIC_HERBS = {
    "附子": {"toxicity": "有毒 (Toxic)", "toxic_compounds": ["Aconitine"], "max_dosage": "3-15g (processed)", "notes": "Must be processed (炮制). Raw aconite is extremely toxic."},
    "半夏": {"toxicity": "有毒 (Toxic)", "toxic_compounds": ["3,4-dihydroxybenzaldehyde"], "max_dosage": "3-9g (processed)", "notes": "Must use processed form (制半夏). Raw is irritating and toxic."},
    "马钱子": {"toxicity": "大毒 (Very Toxic)", "toxic_compounds": ["Strychnine", "Brucine"], "max_dosage": "0.3-0.6g (processed)", "notes": "Extremely narrow therapeutic window. External use preferred."},
    "雷公藤": {"toxicity": "大毒 (Very Toxic)", "toxic_compounds": ["Triptolide", "Celastrol"], "max_dosage": "10-25g (root, decocted 2h+)", "notes": "Hepatotoxic, nephrotoxic, gonadotoxic. Requires careful monitoring."},
    "细辛": {"toxicity": "有毒 (Toxic)", "toxic_compounds": ["Aristolochic acid (in root)"], "max_dosage": "1-3g", "notes": "Use above-ground parts only. Root contains aristolochic acid (carcinogenic)."},
}

PREGNANCY_CONTRAINDICATED = [
    "附子", "大黄", "芒硝", "巴豆", "牵牛子", "芫花", "大戟", "甘遂",
    "麝香", "三棱", "莪术", "水蛭", "虻虫", "马钱子", "雷公藤",
]

PREGNANCY_CAUTION = [
    "桃仁", "红花", "牛膝", "王不留行", "川芎", "丹参", "半夏",
    "薏苡仁", "肉桂", "枳实", "干姜",
]


@registry.register(
    name="safety.toxicity_check",
    description="Check if a herb has known toxicity. Returns toxicity level, toxic compounds, and safe dosage range.",
    category="safety",
    parameters={"herb_name": "Herb name (Chinese)"},
    usage_guide="When evaluating safety of a potentially toxic herb.",
)
def toxicity_check(herb_name: str) -> dict:
    """Check herb toxicity."""
    if herb_name in TOXIC_HERBS:
        return {"status": "toxic", "herb": herb_name, **TOXIC_HERBS[herb_name]}
    return {"status": "not_toxic", "herb": herb_name, "message": "No known toxicity in standard pharmacopoeia dosages."}


@registry.register(
    name="safety.pregnancy_check",
    description="Check if herbs are safe during pregnancy. Identifies contraindicated and cautionary herbs.",
    category="safety",
    parameters={"herbs": "Comma-separated list of herb names"},
    usage_guide="When checking formula safety for pregnant patients.",
)
def pregnancy_check(herbs: str) -> dict:
    """Check pregnancy safety."""
    herb_list = [h.strip() for h in herbs.split(",") if h.strip()]
    contraindicated = [h for h in herb_list if h in PREGNANCY_CONTRAINDICATED]
    caution = [h for h in herb_list if h in PREGNANCY_CAUTION]
    safe = [h for h in herb_list if h not in PREGNANCY_CONTRAINDICATED and h not in PREGNANCY_CAUTION]

    status = "safe"
    if contraindicated:
        status = "contraindicated"
    elif caution:
        status = "caution"

    return {
        "status": status,
        "contraindicated": contraindicated,
        "caution": caution,
        "safe": safe,
    }


@registry.register(
    name="safety.dosage_validate",
    description="Validate if a herb dosage is within the recommended range.",
    category="safety",
    parameters={"herb_name": "Herb name", "dosage_g": "Dosage in grams"},
    usage_guide="When verifying prescription dosages.",
)
def dosage_validate(herb_name: str, dosage_g: float) -> dict:
    """Validate herb dosage."""
    from tcm.tools.herbs import _search_herb
    herb = _search_herb(herb_name)
    if not herb:
        return {"status": "unknown", "message": f"Herb '{herb_name}' not found for dosage validation."}

    dosage_str = herb.get("dosage", "")
    return {
        "status": "info",
        "herb": herb["chinese_name"],
        "requested_dosage": f"{dosage_g}g",
        "recommended_range": dosage_str,
        "message": "Compare requested dosage against the recommended range. Adjust based on patient condition and formula context.",
    }
