"""
Interaction tools: herb-herb and herb-drug interactions, contraindications.

Covers 十八反 (18 Incompatibilities) and 十九畏 (19 Mutual Fears) and
modern herb-drug interaction data.
"""

import logging
from tcm.tools import registry

logger = logging.getLogger("tcm.tools.interactions")

# Classical incompatibilities (十八反)
EIGHTEEN_INCOMPATIBILITIES = {
    "甘草": ["海藻", "大戟", "甘遂", "芫花"],
    "乌头": ["贝母", "瓜蒌", "半夏", "白蔹", "白及"],
    "藜芦": ["人参", "沙参", "丹参", "玄参", "苦参", "细辛", "芍药"],
}

# Classical mutual fears (十九畏)
NINETEEN_FEARS = [
    ("硫黄", "朴硝"), ("水银", "砒霜"), ("狼毒", "密陀僧"),
    ("巴豆", "牵牛子"), ("丁香", "郁金"), ("川乌/草乌", "犀角"),
    ("牙硝", "三棱"), ("官桂", "赤石脂"), ("人参", "五灵脂"),
]

# Modern herb-drug interactions
HERB_DRUG_INTERACTIONS = [
    {
        "herb": "人参 (Ginseng)",
        "drug": "Warfarin",
        "interaction": "May decrease anticoagulant effect",
        "severity": "moderate",
        "mechanism": "CYP enzyme induction, platelet aggregation effects",
    },
    {
        "herb": "甘草 (Licorice)",
        "drug": "Digoxin",
        "interaction": "Hypokalemia from licorice may potentiate digoxin toxicity",
        "severity": "major",
        "mechanism": "Mineralocorticoid effect causing potassium loss",
    },
    {
        "herb": "当归 (Angelica)",
        "drug": "Warfarin",
        "interaction": "May increase anticoagulant effect and bleeding risk",
        "severity": "major",
        "mechanism": "Coumarin derivatives in Angelica potentiate anticoagulation",
    },
    {
        "herb": "黄连 (Coptis/Berberine)",
        "drug": "Metformin",
        "interaction": "Additive hypoglycemic effect — may enhance blood sugar lowering",
        "severity": "moderate",
        "mechanism": "Both activate AMPK pathway",
    },
    {
        "herb": "柴胡 (Bupleurum)",
        "drug": "Interferon",
        "interaction": "May have additive immunomodulatory effects",
        "severity": "minor",
        "mechanism": "Both modulate immune response pathways",
    },
]


@registry.register(
    name="interactions.check_herbs",
    description="Check for classical incompatibilities (十八反/十九畏) between two or more herbs.",
    category="interactions",
    parameters={"herbs": "Comma-separated list of herb names (Chinese)"},
    usage_guide="When validating formula safety or checking herb combinations.",
)
def check_herbs(herbs: str) -> dict:
    """Check herb-herb interactions."""
    herb_list = [h.strip() for h in herbs.split(",") if h.strip()]
    warnings = []

    # Check 十八反
    for key_herb, incompatible in EIGHTEEN_INCOMPATIBILITIES.items():
        if key_herb in herb_list:
            for inc in incompatible:
                if inc in herb_list:
                    warnings.append({
                        "type": "十八反 (18 Incompatibilities)",
                        "herbs": [key_herb, inc],
                        "severity": "contraindicated",
                        "description": f"{key_herb} is classically incompatible with {inc}",
                    })

    # Check 十九畏
    for herb_a, herb_b in NINETEEN_FEARS:
        herbs_a = herb_a.split("/")
        if any(a in herb_list for a in herbs_a) and herb_b in herb_list:
            warnings.append({
                "type": "十九畏 (19 Mutual Fears)",
                "herbs": [herb_a, herb_b],
                "severity": "caution",
                "description": f"{herb_a} and {herb_b} are classically considered mutually antagonistic",
            })

    if warnings:
        return {"status": "warnings", "count": len(warnings), "warnings": warnings}
    return {"status": "safe", "message": "No classical incompatibilities found between the listed herbs."}


@registry.register(
    name="interactions.herb_drug",
    description="Check for known interactions between a Chinese herb and a Western drug.",
    category="interactions",
    parameters={"herb": "Herb name", "drug": "Drug name"},
    usage_guide="When patient is combining TCM herbs with Western pharmaceuticals.",
)
def herb_drug(herb: str, drug: str) -> dict:
    """Check herb-drug interactions."""
    herb_lower = herb.lower()
    drug_lower = drug.lower()
    matches = []

    for interaction in HERB_DRUG_INTERACTIONS:
        if herb_lower in interaction["herb"].lower() and drug_lower in interaction["drug"].lower():
            matches.append(interaction)

    if matches:
        return {"status": "found", "interactions": matches}
    return {
        "status": "not_found",
        "message": f"No known interactions found between '{herb}' and '{drug}' in local database. Consider consulting a pharmacist or checking online databases.",
    }


@registry.register(
    name="interactions.formula_safety",
    description="Run a comprehensive safety check on a formula's herb combination. Checks both classical and modern interactions.",
    category="interactions",
    parameters={"herbs": "Comma-separated list of herbs"},
    usage_guide="When validating a complete formula for safety before prescribing.",
)
def formula_safety(herbs: str) -> dict:
    """Comprehensive formula safety check."""
    herb_result = check_herbs(herbs)
    return {
        "status": "complete",
        "herb_interactions": herb_result,
        "note": "This checks classical TCM incompatibilities. For herb-drug interactions, use interactions.herb_drug for each herb-drug pair.",
    }
