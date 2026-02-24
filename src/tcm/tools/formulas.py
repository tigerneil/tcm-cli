"""
Formula tools: classical formula search, composition analysis, modification.

Covers 方剂 (formulas/prescriptions) — search by name, analyze composition
using 君臣佐使 (sovereign-minister-assistant-envoy) framework.
"""

import logging
from tcm.tools import registry

logger = logging.getLogger("tcm.tools.formulas")


FORMULA_DB = {
    "四君子汤": {
        "pinyin": "Sì Jūn Zǐ Tāng",
        "english": "Four Gentlemen Decoction",
        "source": "《太平惠民和剂局方》(Taiping Huimin Heji Ju Fang)",
        "category": "补益剂-补气 (Tonifying - Qi-Supplementing)",
        "composition": {
            "君 (Sovereign)": [{"herb": "人参", "dosage": "9g", "role": "Greatly tonifies original Qi"}],
            "臣 (Minister)": [{"herb": "白术", "dosage": "9g", "role": "Strengthens Spleen, dries dampness"}],
            "佐 (Assistant)": [{"herb": "茯苓", "dosage": "9g", "role": "Drains dampness, assists Spleen"}],
            "使 (Envoy)": [{"herb": "甘草", "dosage": "6g", "role": "Harmonizes formula, tonifies Qi"}],
        },
        "functions": "益气健脾 (Augments Qi and strengthens Spleen)",
        "indications": "Spleen Qi deficiency: pale complexion, soft voice, reduced appetite, loose stools, fatigue",
        "modifications": {
            "加陈皮 → 异功散": "Add Chenpi for Qi stagnation with dampness",
            "加陈皮半夏 → 六君子汤": "Add Chenpi + Banxia for phlegm-dampness",
            "加木香砂仁 → 香砂六君子汤": "Add Muxiang + Sharen for severe Qi stagnation",
        },
    },
    "小柴胡汤": {
        "pinyin": "Xiǎo Chái Hú Tāng",
        "english": "Minor Bupleurum Decoction",
        "source": "《伤寒论》(Shanghan Lun)",
        "category": "和解剂 (Harmonizing)",
        "composition": {
            "君 (Sovereign)": [{"herb": "柴胡", "dosage": "24g", "role": "Harmonizes Shaoyang, relieves exterior"}],
            "臣 (Minister)": [{"herb": "黄芩", "dosage": "9g", "role": "Clears Shaoyang heat"}],
            "佐 (Assistant)": [
                {"herb": "半夏", "dosage": "9g", "role": "Harmonizes Stomach, descends rebellious Qi"},
                {"herb": "人参", "dosage": "9g", "role": "Supports healthy Qi"},
                {"herb": "生姜", "dosage": "9g", "role": "Assists in harmonizing Stomach"},
                {"herb": "大枣", "dosage": "4 pieces", "role": "Nourishes Qi and Blood"},
            ],
            "使 (Envoy)": [{"herb": "甘草", "dosage": "9g", "role": "Harmonizes all herbs"}],
        },
        "functions": "和解少阳 (Harmonizes Shaoyang)",
        "indications": "Shaoyang syndrome: alternating chills and fever, bitter taste, dry throat, dizziness, chest fullness",
        "modifications": {
            "去参枣加桂枝 → 柴胡桂枝汤": "For concurrent Taiyang symptoms",
            "加芒硝 → 大柴胡汤": "For concurrent Yangming symptoms",
        },
    },
    "补中益气汤": {
        "pinyin": "Bǔ Zhōng Yì Qì Tāng",
        "english": "Tonify the Middle and Augment Qi Decoction",
        "source": "《脾胃论》(Pi Wei Lun)",
        "category": "补益剂-补气 (Tonifying - Qi-Supplementing)",
        "composition": {
            "君 (Sovereign)": [{"herb": "黄芪", "dosage": "15-20g", "role": "Tonifies Qi, raises Yang"}],
            "臣 (Minister)": [
                {"herb": "人参", "dosage": "9g", "role": "Tonifies Spleen Qi"},
                {"herb": "白术", "dosage": "9g", "role": "Strengthens Spleen"},
            ],
            "佐 (Assistant)": [
                {"herb": "当归", "dosage": "6g", "role": "Nourishes Blood"},
                {"herb": "陈皮", "dosage": "6g", "role": "Regulates Qi"},
                {"herb": "升麻", "dosage": "3g", "role": "Raises Yang Qi"},
                {"herb": "柴胡", "dosage": "3g", "role": "Raises Yang Qi"},
            ],
            "使 (Envoy)": [{"herb": "甘草", "dosage": "6g", "role": "Harmonizes formula"}],
        },
        "functions": "补中益气，升阳举陷 (Tonifies the middle, augments Qi, raises Yang, lifts sinking)",
        "indications": "Spleen Qi sinking: organ prolapse, chronic diarrhea, fatigue, shortness of breath, spontaneous sweating",
        "modifications": {},
    },
    "六味地黄丸": {
        "pinyin": "Liù Wèi Dì Huáng Wán",
        "english": "Six-Ingredient Rehmannia Pill",
        "source": "《小儿药证直诀》(Xiao Er Yao Zheng Zhi Jue)",
        "category": "补益剂-补阴 (Tonifying - Yin-Supplementing)",
        "composition": {
            "君 (Sovereign)": [{"herb": "熟地黄", "dosage": "24g", "role": "Nourishes Kidney Yin, fills essence"}],
            "臣 (Minister)": [
                {"herb": "山茱萸", "dosage": "12g", "role": "Nourishes Liver and Kidney"},
                {"herb": "山药", "dosage": "12g", "role": "Tonifies Spleen and Kidney"},
            ],
            "佐 (Assistant)": [
                {"herb": "泽泻", "dosage": "9g", "role": "Drains Kidney fire, prevents stagnation"},
                {"herb": "牡丹皮", "dosage": "9g", "role": "Clears Liver fire"},
                {"herb": "茯苓", "dosage": "9g", "role": "Drains dampness, strengthens Spleen"},
            ],
        },
        "functions": "滋补肝肾 (Nourishes and tonifies Liver and Kidney)",
        "indications": "Kidney Yin deficiency: soreness of lower back and knees, dizziness, tinnitus, night sweats, heat in palms and soles",
        "modifications": {
            "加知母黄柏 → 知柏地黄丸": "For Yin deficiency with fire",
            "加枸杞菊花 → 杞菊地黄丸": "For Liver/Kidney Yin deficiency affecting eyes",
            "加麦冬五味子 → 麦味地黄丸": "For Lung-Kidney Yin deficiency",
        },
    },
}


@registry.register(
    name="formulas.search",
    description="Search for a classical TCM formula by name (Chinese, pinyin, or English). Returns full composition, functions, and indications.",
    category="formulas",
    parameters={"query": "Formula name to search for"},
    usage_guide="When user asks about a specific classical formula or prescription.",
)
def formulas_search(query: str) -> dict:
    """Search for a formula by name."""
    query_lower = query.lower().strip()
    for chinese_name, data in FORMULA_DB.items():
        if (
            query_lower == chinese_name.lower()
            or query_lower == data["pinyin"].lower()
            or query_lower == data["english"].lower()
        ):
            return {"status": "found", "formula": {"chinese_name": chinese_name, **data}}
    return {"status": "not_found", "message": f"Formula '{query}' not found in local database."}


@registry.register(
    name="formulas.composition",
    description="Analyze a formula's composition using the 君臣佐使 (Sovereign-Minister-Assistant-Envoy) framework.",
    category="formulas",
    parameters={"formula_name": "Formula name"},
    usage_guide="When analyzing the role of each herb in a formula.",
)
def formulas_composition(formula_name: str) -> dict:
    """Analyze formula composition."""
    query_lower = formula_name.lower().strip()
    for chinese_name, data in FORMULA_DB.items():
        if query_lower in (chinese_name.lower(), data["pinyin"].lower(), data["english"].lower()):
            return {
                "status": "found",
                "formula": chinese_name,
                "composition": data["composition"],
                "functions": data["functions"],
            }
    return {"status": "not_found", "message": f"Formula '{formula_name}' not found."}


@registry.register(
    name="formulas.modifications",
    description="List classical modifications/variations of a formula.",
    category="formulas",
    parameters={"formula_name": "Formula name"},
    usage_guide="When exploring formula variants or modifications for specific conditions.",
)
def formulas_modifications(formula_name: str) -> dict:
    """List formula modifications."""
    query_lower = formula_name.lower().strip()
    for chinese_name, data in FORMULA_DB.items():
        if query_lower in (chinese_name.lower(), data["pinyin"].lower(), data["english"].lower()):
            return {
                "status": "found",
                "formula": chinese_name,
                "modifications": data.get("modifications", {}),
            }
    return {"status": "not_found", "message": f"Formula '{formula_name}' not found."}


@registry.register(
    name="formulas.by_category",
    description="List formulas in a specific category (e.g., 补益剂, 和解剂, 清热剂).",
    category="formulas",
    parameters={"category": "Formula category name"},
    usage_guide="When browsing formulas by therapeutic category.",
)
def formulas_by_category(category: str) -> dict:
    """List formulas by category."""
    category_lower = category.lower()
    matches = []
    for chinese_name, data in FORMULA_DB.items():
        if category_lower in data["category"].lower():
            matches.append({
                "chinese_name": chinese_name,
                "pinyin": data["pinyin"],
                "english": data["english"],
                "category": data["category"],
                "functions": data["functions"],
            })
    if matches:
        return {"status": "found", "count": len(matches), "formulas": matches}
    return {"status": "not_found", "message": f"No formulas found in category '{category}'."}
