"""
Herb tools: lookup, property classification, efficacy grouping.

Covers 中药 (Chinese Materia Medica) queries — search by pinyin, Chinese name,
Latin name, or English name. Returns properties (性味归经), efficacy, dosage.
"""
from __future__ import annotations

import httpx
import logging

from tcm.tools import registry

logger = logging.getLogger("tcm.tools.herbs")


# ─── Built-in herb knowledge base (subset for offline use) ────────

HERB_DB = {
    "人参": {
        "pinyin": "Rén Shēn",
        "latin": "Radix et Rhizoma Ginseng",
        "english": "Ginseng",
        "nature": "微温 (Slightly Warm)",
        "flavor": "甘、微苦 (Sweet, Slightly Bitter)",
        "meridians": ["脾 (Spleen)", "肺 (Lung)", "心 (Heart)", "肾 (Kidney)"],
        "category": "补气药 (Qi-Tonifying)",
        "functions": [
            "大补元气 (Greatly tonifies original Qi)",
            "复脉固脱 (Restores pulse and prevents collapse)",
            "补脾益肺 (Tonifies Spleen and benefits Lung)",
            "生津养血 (Generates fluids and nourishes Blood)",
            "安神益智 (Calms spirit and benefits intelligence)",
        ],
        "dosage": "3-9g; 15-30g for rescue from collapse",
        "contraindications": "Not for excess heat or Qi stagnation. Incompatible with 藜芦 (Veratrum).",
        "key_compounds": ["Ginsenoside Rg1", "Ginsenoside Rb1", "Ginsenoside Re"],
    },
    "黄芪": {
        "pinyin": "Huáng Qí",
        "latin": "Radix Astragali",
        "english": "Astragalus",
        "nature": "微温 (Slightly Warm)",
        "flavor": "甘 (Sweet)",
        "meridians": ["脾 (Spleen)", "肺 (Lung)"],
        "category": "补气药 (Qi-Tonifying)",
        "functions": [
            "补气升阳 (Tonifies Qi and raises Yang)",
            "固表止汗 (Consolidates exterior and stops sweating)",
            "利水消肿 (Promotes urination and reduces edema)",
            "生津养血 (Generates fluids and nourishes Blood)",
            "托毒排脓 (Expels toxins and drains pus)",
        ],
        "dosage": "9-30g",
        "contraindications": "Not for excess exterior or Qi stagnation with food retention.",
        "key_compounds": ["Astragaloside IV", "Cycloastragenol", "Calycosin"],
    },
    "当归": {
        "pinyin": "Dāng Guī",
        "latin": "Radix Angelicae Sinensis",
        "english": "Chinese Angelica",
        "nature": "温 (Warm)",
        "flavor": "甘、辛 (Sweet, Acrid)",
        "meridians": ["肝 (Liver)", "心 (Heart)", "脾 (Spleen)"],
        "category": "补血药 (Blood-Tonifying)",
        "functions": [
            "补血活血 (Tonifies and activates Blood)",
            "调经止痛 (Regulates menstruation and relieves pain)",
            "润肠通便 (Moistens intestines and unblocks bowels)",
        ],
        "dosage": "6-12g",
        "contraindications": "Not for diarrhea due to dampness or abdominal fullness.",
        "key_compounds": ["Ligustilide", "Ferulic acid", "Angelica polysaccharides"],
    },
    "甘草": {
        "pinyin": "Gān Cǎo",
        "latin": "Radix et Rhizoma Glycyrrhizae",
        "english": "Licorice",
        "nature": "平 (Neutral)",
        "flavor": "甘 (Sweet)",
        "meridians": ["心 (Heart)", "肺 (Lung)", "脾 (Spleen)", "胃 (Stomach)"],
        "category": "补气药 (Qi-Tonifying)",
        "functions": [
            "补脾益气 (Tonifies Spleen and benefits Qi)",
            "清热解毒 (Clears heat and resolves toxins)",
            "祛痰止咳 (Expels phlegm and stops coughing)",
            "缓急止痛 (Relaxes urgency and relieves pain)",
            "调和诸药 (Harmonizes other herbs)",
        ],
        "dosage": "2-10g",
        "contraindications": "Prolonged high-dose use may cause edema and hypertension.",
        "key_compounds": ["Glycyrrhizin", "Liquiritin", "Isoliquiritigenin"],
    },
    "黄连": {
        "pinyin": "Huáng Lián",
        "latin": "Rhizoma Coptidis",
        "english": "Coptis",
        "nature": "寒 (Cold)",
        "flavor": "苦 (Bitter)",
        "meridians": ["心 (Heart)", "脾 (Spleen)", "胃 (Stomach)", "肝 (Liver)", "胆 (Gallbladder)", "大肠 (Large Intestine)"],
        "category": "清热燥湿药 (Heat-Clearing, Dampness-Drying)",
        "functions": [
            "清热燥湿 (Clears heat and dries dampness)",
            "泻火解毒 (Drains fire and resolves toxins)",
        ],
        "dosage": "2-5g",
        "contraindications": "Not for Spleen and Stomach deficiency cold.",
        "key_compounds": ["Berberine", "Coptisine", "Palmatine"],
    },
    "柴胡": {
        "pinyin": "Chái Hú",
        "latin": "Radix Bupleuri",
        "english": "Bupleurum",
        "nature": "微寒 (Slightly Cold)",
        "flavor": "辛、苦 (Acrid, Bitter)",
        "meridians": ["肝 (Liver)", "胆 (Gallbladder)", "肺 (Lung)"],
        "category": "解表药 (Exterior-Releasing)",
        "functions": [
            "和解表里 (Harmonizes exterior and interior)",
            "疏肝升阳 (Courses Liver and raises Yang)",
            "退热 (Reduces fever)",
        ],
        "dosage": "3-10g",
        "contraindications": "Not for Liver-Wind-moving or Yin deficiency with fire.",
        "key_compounds": ["Saikosaponin A", "Saikosaponin D", "Bupleurumol"],
    },
    "白术": {
        "pinyin": "Bái Zhú",
        "latin": "Rhizoma Atractylodis Macrocephalae",
        "english": "White Atractylodes",
        "nature": "温 (Warm)",
        "flavor": "甘、苦 (Sweet, Bitter)",
        "meridians": ["脾 (Spleen)", "胃 (Stomach)"],
        "category": "补气药 (Qi-Tonifying)",
        "functions": [
            "健脾益气 (Strengthens Spleen and benefits Qi)",
            "燥湿利水 (Dries dampness and promotes urination)",
            "止汗 (Stops sweating)",
            "安胎 (Calms fetus)",
        ],
        "dosage": "6-12g",
        "contraindications": "Not for Yin deficiency with internal heat.",
        "key_compounds": ["Atractylenolide I", "Atractylenolide III", "Atractylone"],
    },
    "茯苓": {
        "pinyin": "Fú Líng",
        "latin": "Poria",
        "english": "Poria",
        "nature": "平 (Neutral)",
        "flavor": "甘、淡 (Sweet, Bland)",
        "meridians": ["心 (Heart)", "肺 (Lung)", "脾 (Spleen)", "肾 (Kidney)"],
        "category": "利水渗湿药 (Dampness-Draining)",
        "functions": [
            "利水渗湿 (Promotes urination and drains dampness)",
            "健脾 (Strengthens Spleen)",
            "宁心安神 (Calms heart and tranquilizes spirit)",
        ],
        "dosage": "10-15g",
        "contraindications": "Not for frequent urination due to deficiency cold.",
        "key_compounds": ["Pachymic acid", "Poricoic acid", "Beta-pachyman"],
    },
}


def _search_herb(query: str) -> dict | None:
    """Search herb by Chinese name, pinyin, English name, or Latin name."""
    query_lower = query.lower().strip()
    for chinese_name, data in HERB_DB.items():
        if (
            query_lower == chinese_name.lower()
            or query_lower == data["pinyin"].lower()
            or query_lower == data["english"].lower()
            or query_lower in data["latin"].lower()
        ):
            return {"chinese_name": chinese_name, **data}
    return None


@registry.register(
    name="herbs.lookup",
    description="Look up a Chinese herb by name (Chinese, pinyin, English, or Latin). Returns properties, functions, dosage, and key compounds.",
    category="herbs",
    parameters={"query": "Herb name to search for"},
    usage_guide="When user asks about a specific herb's properties, dosage, or classification.",
)
def herbs_lookup(query: str) -> dict:
    """Look up herb information."""
    result = _search_herb(query)
    if result:
        return {"status": "found", "herb": result}
    return {"status": "not_found", "message": f"Herb '{query}' not found in local database. Try using data_api.tcmsp_search for online lookup."}


@registry.register(
    name="herbs.properties",
    description="Classify herb by its Four Natures (四气) and Five Flavors (五味). Returns nature, flavor, and meridian tropism.",
    category="herbs",
    parameters={"herb_name": "Herb name (Chinese or English)"},
    usage_guide="When analyzing herb properties for formula design or syndrome matching.",
)
def herbs_properties(herb_name: str) -> dict:
    """Get herb property classification."""
    result = _search_herb(herb_name)
    if not result:
        return {"status": "not_found", "message": f"Herb '{herb_name}' not found."}
    return {
        "status": "found",
        "herb": result["chinese_name"],
        "nature": result["nature"],
        "flavor": result["flavor"],
        "meridians": result["meridians"],
        "category": result["category"],
    }


@registry.register(
    name="herbs.by_category",
    description="List herbs in a specific therapeutic category (e.g., 补气药, 清热药, 活血化瘀药).",
    category="herbs",
    parameters={"category": "Therapeutic category name (Chinese or English)"},
    usage_guide="When looking for herbs within a specific therapeutic group.",
)
def herbs_by_category(category: str) -> dict:
    """List herbs by therapeutic category."""
    category_lower = category.lower()
    matches = []
    for chinese_name, data in HERB_DB.items():
        if category_lower in data["category"].lower():
            matches.append({
                "chinese_name": chinese_name,
                "pinyin": data["pinyin"],
                "english": data["english"],
                "category": data["category"],
            })
    if matches:
        return {"status": "found", "count": len(matches), "herbs": matches}
    return {"status": "not_found", "message": f"No herbs found in category '{category}'."}


@registry.register(
    name="herbs.by_meridian",
    description="Find herbs that enter a specific meridian/channel (e.g., 肝经, 心经, Liver, Heart).",
    category="herbs",
    parameters={"meridian": "Meridian name (Chinese or English)"},
    usage_guide="When searching for herbs that target a specific organ/meridian system.",
)
def herbs_by_meridian(meridian: str) -> dict:
    """Find herbs by meridian tropism."""
    meridian_lower = meridian.lower()
    matches = []
    for chinese_name, data in HERB_DB.items():
        for m in data["meridians"]:
            if meridian_lower in m.lower():
                matches.append({
                    "chinese_name": chinese_name,
                    "pinyin": data["pinyin"],
                    "english": data["english"],
                    "meridians": data["meridians"],
                })
                break
    if matches:
        return {"status": "found", "count": len(matches), "herbs": matches}
    return {"status": "not_found", "message": f"No herbs found for meridian '{meridian}'."}


@registry.register(
    name="herbs.compounds",
    description="List key active compounds for a given herb.",
    category="herbs",
    parameters={"herb_name": "Herb name"},
    usage_guide="When investigating the phytochemistry of a specific herb.",
)
def herbs_compounds(herb_name: str) -> dict:
    """Get key compounds for a herb."""
    result = _search_herb(herb_name)
    if not result:
        return {"status": "not_found", "message": f"Herb '{herb_name}' not found."}
    return {
        "status": "found",
        "herb": result["chinese_name"],
        "english": result["english"],
        "key_compounds": result.get("key_compounds", []),
    }
