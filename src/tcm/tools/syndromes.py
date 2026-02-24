"""
Syndrome tools: TCM pattern differentiation (辨证论治).

Maps symptoms to TCM syndromes and suggests treatment principles and formulas.
"""

import logging
from tcm.tools import registry

logger = logging.getLogger("tcm.tools.syndromes")

SYNDROME_DB = {
    "脾气虚": {
        "pinyin": "Pí Qì Xū",
        "english": "Spleen Qi Deficiency",
        "category": "脏腑辨证 (Organ Pattern)",
        "symptoms": [
            "食少纳呆 (poor appetite)", "腹胀 (abdominal distension)",
            "便溏 (loose stools)", "面色萎黄 (sallow complexion)",
            "神疲乏力 (fatigue)", "少气懒言 (shortness of breath, reluctance to speak)",
            "舌淡苔白 (pale tongue, white coating)", "脉缓弱 (slow, weak pulse)",
        ],
        "treatment_principle": "健脾益气 (Strengthen Spleen and augment Qi)",
        "representative_formulas": ["四君子汤", "补中益气汤"],
        "key_herbs": ["人参", "黄芪", "白术", "茯苓", "甘草"],
    },
    "肝气郁结": {
        "pinyin": "Gān Qì Yù Jié",
        "english": "Liver Qi Stagnation",
        "category": "脏腑辨证 (Organ Pattern)",
        "symptoms": [
            "胸胁胀痛 (distending pain in chest and hypochondria)",
            "情志抑郁 (emotional depression)", "善太息 (frequent sighing)",
            "咽中如有物梗阻 (sensation of a lump in throat)",
            "月经不调 (irregular menstruation)", "乳房胀痛 (breast distension)",
            "脉弦 (wiry pulse)",
        ],
        "treatment_principle": "疏肝理气 (Course Liver and regulate Qi)",
        "representative_formulas": ["逍遥散", "柴胡疏肝散"],
        "key_herbs": ["柴胡", "白芍", "香附", "川芎", "枳壳"],
    },
    "肾阴虚": {
        "pinyin": "Shèn Yīn Xū",
        "english": "Kidney Yin Deficiency",
        "category": "脏腑辨证 (Organ Pattern)",
        "symptoms": [
            "腰膝酸软 (soreness of lower back and knees)",
            "头晕耳鸣 (dizziness and tinnitus)",
            "失眠多梦 (insomnia with many dreams)",
            "五心烦热 (heat in palms, soles, and chest)",
            "盗汗 (night sweats)", "口干咽燥 (dry mouth and throat)",
            "舌红少苔 (red tongue with little coating)",
            "脉细数 (thin, rapid pulse)",
        ],
        "treatment_principle": "滋补肾阴 (Nourish and supplement Kidney Yin)",
        "representative_formulas": ["六味地黄丸", "左归丸"],
        "key_herbs": ["熟地黄", "山茱萸", "山药", "枸杞子", "女贞子"],
    },
    "风寒表证": {
        "pinyin": "Fēng Hán Biǎo Zhèng",
        "english": "Wind-Cold Exterior Pattern",
        "category": "六经辨证 (Six-Channel Pattern)",
        "symptoms": [
            "恶寒重发热轻 (severe chills, mild fever)",
            "无汗 (no sweating)", "头身疼痛 (headache and body aches)",
            "鼻塞流清涕 (nasal congestion, clear discharge)",
            "咳嗽 (cough)", "舌苔薄白 (thin white tongue coating)",
            "脉浮紧 (floating, tight pulse)",
        ],
        "treatment_principle": "辛温解表 (Release exterior with warm, acrid herbs)",
        "representative_formulas": ["麻黄汤", "桂枝汤"],
        "key_herbs": ["麻黄", "桂枝", "紫苏叶", "生姜", "防风"],
    },
    "湿热蕴脾": {
        "pinyin": "Shī Rè Yùn Pí",
        "english": "Damp-Heat in Spleen",
        "category": "脏腑辨证 (Organ Pattern)",
        "symptoms": [
            "脘腹胀满 (epigastric and abdominal fullness)",
            "恶心呕吐 (nausea and vomiting)",
            "口苦口粘 (bitter taste, sticky sensation in mouth)",
            "大便溏臭 (loose, foul-smelling stools)",
            "小便短黄 (scant, yellow urine)",
            "身重困倦 (heavy body, fatigue)",
            "舌红苔黄腻 (red tongue, yellow greasy coating)",
            "脉濡数 (soggy, rapid pulse)",
        ],
        "treatment_principle": "清热化湿 (Clear heat and resolve dampness)",
        "representative_formulas": ["茵陈蒿汤", "三仁汤"],
        "key_herbs": ["黄连", "黄芩", "茵陈", "薏苡仁", "藿香"],
    },
}


@registry.register(
    name="syndromes.identify",
    description="Given a list of symptoms, identify matching TCM syndromes/patterns. Returns syndrome name, treatment principle, and recommended formulas.",
    category="syndromes",
    parameters={"symptoms": "Comma-separated list of symptoms"},
    usage_guide="When user describes symptoms and wants TCM pattern differentiation.",
)
def syndromes_identify(symptoms: str) -> dict:
    """Identify syndromes from symptoms."""
    symptom_list = [s.strip().lower() for s in symptoms.split(",")]
    matches = []
    for syndrome_name, data in SYNDROME_DB.items():
        syndrome_symptoms = [s.lower() for s in data["symptoms"]]
        score = 0
        for user_symptom in symptom_list:
            for syn_symptom in syndrome_symptoms:
                if user_symptom in syn_symptom or syn_symptom in user_symptom:
                    score += 1
                    break
        if score > 0:
            matches.append({
                "syndrome": syndrome_name,
                "english": data["english"],
                "match_score": score,
                "total_symptoms": len(data["symptoms"]),
                "treatment_principle": data["treatment_principle"],
                "representative_formulas": data["representative_formulas"],
            })
    matches.sort(key=lambda x: x["match_score"], reverse=True)
    if matches:
        return {"status": "found", "matches": matches}
    return {"status": "no_match", "message": "No matching syndromes found for the given symptoms."}


@registry.register(
    name="syndromes.lookup",
    description="Look up a specific TCM syndrome/pattern by name. Returns symptoms, treatment principle, and formulas.",
    category="syndromes",
    parameters={"syndrome_name": "Syndrome name (Chinese or English)"},
    usage_guide="When user asks about a specific TCM syndrome or pattern.",
)
def syndromes_lookup(syndrome_name: str) -> dict:
    """Look up a syndrome by name."""
    query_lower = syndrome_name.lower().strip()
    for name, data in SYNDROME_DB.items():
        if query_lower == name.lower() or query_lower == data["english"].lower():
            return {"status": "found", "syndrome": {"name": name, **data}}
    return {"status": "not_found", "message": f"Syndrome '{syndrome_name}' not found."}


@registry.register(
    name="syndromes.treatment",
    description="Get the treatment principle and recommended herbs/formulas for a TCM syndrome.",
    category="syndromes",
    parameters={"syndrome_name": "Syndrome name"},
    usage_guide="When determining treatment strategy for a diagnosed syndrome.",
)
def syndromes_treatment(syndrome_name: str) -> dict:
    """Get treatment for a syndrome."""
    query_lower = syndrome_name.lower().strip()
    for name, data in SYNDROME_DB.items():
        if query_lower == name.lower() or query_lower == data["english"].lower():
            return {
                "status": "found",
                "syndrome": name,
                "treatment_principle": data["treatment_principle"],
                "representative_formulas": data["representative_formulas"],
                "key_herbs": data["key_herbs"],
            }
    return {"status": "not_found", "message": f"Syndrome '{syndrome_name}' not found."}
