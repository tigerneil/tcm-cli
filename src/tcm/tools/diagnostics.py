"""
Multimodal TCM diagnostic tools covering the Four Examinations (四诊合参: 望闻问切),
pharmacognostic decoction piece authentication (中药饮片性状鉴别), and classical/modern
prescription metrology & safety parsing (处方解析与剂量折算).
"""
from __future__ import annotations

import logging
import re

from tcm.tools import registry
from tcm.tools.formulas import FORMULA_DB
from tcm.tools.herbs import _search_herb
from tcm.tools.interactions import check_herbs
from tcm.tools.safety import pregnancy_check, toxicity_check

logger = logging.getLogger("tcm.tools.diagnostics")


# ─── 1. Canonical Tongue Patterns (中医舌诊图谱与辨证库) ─────────────────────────

TONGUE_PATTERNS: list[dict] = [
    {
        "id": "TP01",
        "pattern_name": "淡红舌薄白苔",
        "english_name": "Pale-Red Body, Thin-White Coating",
        "syndrome": "平人常象 / 外感风寒表证初起 (Normal Constitution or Mild Exterior Wind)",
        "eight_principles": {
            "interior_exterior": "表/平 (Normal or Mild Exterior)",
            "heat_cold": "平/微寒 (Neutral or Mild Cold)",
            "excess_deficiency": "不虚不实 (Balanced Zheng Qi)",
            "yin_yang": "阴阳平和 (Yin-Yang Harmonious)",
        },
        "scores": {"exterior": 1, "interior": 0, "heat": 0, "cold": 1, "deficiency": 0, "excess": 0},
        "keywords": [
            "淡红", "薄白", "正常", "润", "pale-red", "pale red", "pink",
            "thin white", "thin-white", "normal tongue",
        ],
        "zone_focus": "全舌调匀 (Uniform across all zones)",
        "pathomechanism": "胃气充盛，气血调和，津液润泽；若伴恶寒发热则为外邪初袭肌表，尚未伤及里气。",
        "treatment_principle": "无病勿药；若兼表证则辛温或辛凉轻宣解表 (Harmonize Nutritive-Defensive Qi if exterior signs present)",
        "recommended_formulas": ["桂枝汤", "银翘散"],
        "followup_questions": [
            "有无近期恶风寒、微热、鼻塞或咽痒等初起外感症状？",
            "平素饮食、二便及睡眠是否如常？",
        ],
    },
    {
        "id": "TP02",
        "pattern_name": "淡白胖大齿痕舌・白滑苔",
        "english_name": "Pale Swollen Scalloped Tongue, Wet Slippery White Coating",
        "syndrome": "脾肾阳虚 / 气虚湿盛证 (Spleen & Kidney Yang / Qi Deficiency with Dampness)",
        "eight_principles": {
            "interior_exterior": "里证 (Interior)",
            "heat_cold": "寒证 (Cold)",
            "excess_deficiency": "虚中夹湿 (Deficiency with Damp Accumulation)",
            "yin_yang": "阳虚 (Yang / Qi Deficiency)",
        },
        "scores": {"exterior": 0, "interior": 3, "heat": 0, "cold": 3, "deficiency": 3, "excess": 1},
        "keywords": [
            "淡白", "胖大", "齿痕", "白滑", "水滑", "舌胖", "舌淡", "pale", "swollen",
            "scalloped", "teeth-mark", "tooth-mark", "teeth mark", "wet white", "slippery white",
        ],
        "zone_focus": "舌中脾胃与舌根肾区水湿内停，舌边齿痕明显",
        "pathomechanism": "脾气亏虚或命门火衰，运化水湿无权，水饮痰湿内停泛溢于舌体，舌体胖嫩受齿缘压迫而成齿痕。",
        "treatment_principle": "温补脾肾，益气健脾，温阳化湿利水 (Warm Spleen-Kidney Yang, augment Qi, transform dampness)",
        "recommended_formulas": ["四君子汤", "理中汤", "实脾饮", "真武汤"],
        "followup_questions": [
            "是否伴见畏寒肢冷、神疲乏力、食少腹胀或大便溏薄？",
            "晨起颜面或下肢有无浮肿，小便是否清长或不利？",
        ],
    },
    {
        "id": "TP03",
        "pattern_name": "红舌黄腻苔",
        "english_name": "Red Body, Yellow Greasy Coating",
        "syndrome": "脾胃湿热 / 肝胆湿热 / 痰热内蕴证 (Damp-Heat in Spleen-Stomach or Liver-Gallbladder)",
        "eight_principles": {
            "interior_exterior": "里证 (Interior)",
            "heat_cold": "热证 (Heat)",
            "excess_deficiency": "实证 (Excess)",
            "yin_yang": "阳盛湿热 (Yang Heat with Turbid Dampness)",
        },
        "scores": {"exterior": 0, "interior": 3, "heat": 3, "cold": 0, "deficiency": 0, "excess": 3},
        "keywords": [
            "红舌", "舌红", "黄腻", "黄厚腻", "浊腻", "red body", "red tongue",
            "yellow greasy", "yellow-greasy", "sticky yellow", "slimy yellow",
        ],
        "zone_focus": "舌中厚黄腻主脾胃湿热；兼舌边红赤主肝胆湿热熏蒸",
        "pathomechanism": "湿邪与热邪交蒸中焦或肝胆，湿遏热伏，熏蒸胃浊上泛于舌面，故舌质红而苔黄厚粘腻。",
        "treatment_principle": "清热化湿，理气和胃，或清利肝胆湿热 (Clear heat, resolve dampness, regulate middle/rib-side Qi)",
        "recommended_formulas": ["连朴饮", "龙胆泻肝汤", "黄连温胆汤", "茵陈蒿汤"],
        "followup_questions": [
            "是否口苦口粘、渴不多饮、脘腹痞满或胁肋胀痛？",
            "大便是否粘滞不爽臭秽，小便是否短赤？",
        ],
    },
    {
        "id": "TP04",
        "pattern_name": "红绛少苔/剥苔/裂纹舌",
        "english_name": "Crimson/Red Body, Scanty or Peeled Coating with Fissures",
        "syndrome": "肝肾阴虚火旺 / 胃阴枯竭证 (Liver-Kidney Yin Deficiency with Empty Fire)",
        "eight_principles": {
            "interior_exterior": "里证 (Interior)",
            "heat_cold": "虚热证 (Deficiency Heat)",
            "excess_deficiency": "虚证 (Yin Deficiency)",
            "yin_yang": "阴虚阳亢 (Yin Exhaustion with Empty Fire)",
        },
        "scores": {"exterior": 0, "interior": 3, "heat": 3, "cold": 0, "deficiency": 3, "excess": 0},
        "keywords": [
            "红绛", "绛舌", "少苔", "无苔", "剥苔", "地图舌", "镜面舌", "裂纹", "光红",
            "crimson", "scarlet", "scanty coating", "peeled", "geographic", "mirror",
            "fissure", "fissured", "cracked",
        ],
        "zone_focus": "舌中剥落主胃阴大伤；舌根少苔裂纹主肾阴亏虚",
        "pathomechanism": "久病或温病后期肝肾真阴亏耗、胃津不足，虚火内炽灼伤血络则舌红绛，胃气胃阴不能上蒸则少苔剥落，精血不荣舌体则生裂纹。",
        "treatment_principle": "滋补肝肾，养阴生津，清降虚火 (Nourish Liver-Kidney & Stomach Yin, clear deficiency fire)",
        "recommended_formulas": ["六味地黄丸", "知柏地黄丸", "沙参麦冬汤", "大补阴丸"],
        "followup_questions": [
            "有无五心烦热、潮热盗汗、口燥咽干、夜间尤甚？",
            "是否伴腰膝酸软、头晕耳鸣或失眠多梦？",
        ],
    },
    {
        "id": "TP05",
        "pattern_name": "青紫舌或瘀点瘀斑・舌下络脉迂曲怒张",
        "english_name": "Cyanotic/Violaceous Body or Petechiae, Engorged Sublingual Veins",
        "syndrome": "血瘀证 (气滞血瘀 / 寒凝血瘀 / 心脉瘀阻 Blood Stasis Syndrome)",
        "eight_principles": {
            "interior_exterior": "里证 (Interior)",
            "heat_cold": "寒热皆可见 (Cold Congealing or Heat Stasis)",
            "excess_deficiency": "实证或本虚标实 (Excess Stasis or Qi-Deficiency Stasis)",
            "yin_yang": "营血郁滞 (Yin-Blood Stagnation)",
        },
        "scores": {"exterior": 0, "interior": 3, "heat": 0, "cold": 1, "deficiency": 1, "excess": 3},
        "keywords": [
            "青紫", "紫暗", "暗紫", "瘀点", "瘀斑", "舌下络脉", "迂曲", "怒张", "粗胀",
            "cyanotic", "purple", "violaceous", "bluish", "petechiae", "ecchymosis",
            "sublingual", "engorged", "tortuous", "distended veins",
        ],
        "zone_focus": "舌尖边瘀点常见心肝血瘀；舌下金津玉液络脉粗胀青紫为全身血瘀早期指征",
        "pathomechanism": "气机郁滞、寒邪凝滞或气虚鼓动无力，致血行不畅乃至瘀阻脉络，舌体血络瘀滞故见紫暗、瘀斑及舌下静脉曲张。",
        "treatment_principle": "活血化瘀，行气通络 (Invigorate Blood, dispel stasis, course Qi & unblock collaterals)",
        "recommended_formulas": ["血府逐瘀汤", "桃红四物汤", "少腹逐瘀汤", "补阳还五汤"],
        "followup_questions": [
            "身体固定部位有无刺痛、夜间痛甚或拒按？",
            "面色唇甲是否晦暗，女性患者经色是否紫暗夹有血块？",
        ],
    },
    {
        "id": "TP06",
        "pattern_name": "舌尖红赤起刺",
        "english_name": "Red Prickly/Thorny Tongue Tip",
        "syndrome": "心火亢盛 / 上焦肺卫郁热证 (Heart/Lung Fire Blazing)",
        "eight_principles": {
            "interior_exterior": "里证/上焦 (Upper Jiao Interior)",
            "heat_cold": "实热证 (Excess Fire)",
            "excess_deficiency": "实证 (Excess)",
            "yin_yang": "阳热亢盛 (Blazing Yang Fire)",
        },
        "scores": {"exterior": 0, "interior": 2, "heat": 3, "cold": 0, "deficiency": 0, "excess": 3},
        "keywords": [
            "舌尖红", "尖红", "起刺", "芒刺", "点刺", "草莓舌", "red tip",
            "tip red", "prickly", "thorny", "strawberry tip", "red papillae",
        ],
        "zone_focus": "舌尖属心肺（上焦），蕈状乳头充血隆起成红刺",
        "pathomechanism": "情志化火或温邪上受，致心经实火炽盛或上焦风热郁闭，火热循经上炎于舌尖，灼伤血络而红赤起芒刺。",
        "treatment_principle": "清心泻火，导热下行 (Clear Heart fire, drain heat via Small Intestine)",
        "recommended_formulas": ["导赤散", "泻心汤", "清营汤"],
        "followup_questions": [
            "近期是否心烦失眠、口舌生疮或口渴喜冷饮？",
            "小便是否短赤灼热或涩痛？",
        ],
    },
    {
        "id": "TP07",
        "pattern_name": "舌边红赤苔薄黄",
        "english_name": "Red Tongue Edges, Thin Yellow Coating",
        "syndrome": "肝郁化火 / 肝火上炎证 (Liver Qi Stagnation Transforming into Fire)",
        "eight_principles": {
            "interior_exterior": "里证 (Interior)",
            "heat_cold": "热证 (Heat from Stagnation)",
            "excess_deficiency": "实证 (Excess)",
            "yin_yang": "木火刑金/肝阳偏亢 (Yang Hyperactivity in Wood)",
        },
        "scores": {"exterior": 0, "interior": 2, "heat": 2, "cold": 0, "deficiency": 0, "excess": 2},
        "keywords": [
            "舌边红", "边红", "两侧红", "薄黄", "red edges", "edges red",
            "red sides", "lateral red", "thin yellow",
        ],
        "zone_focus": "舌两侧分候肝胆，边红显著提示肝胆郁火偏旺",
        "pathomechanism": "情志不遂、肝气郁结日久化火，肝胆木火循经上冲，反映于舌体两侧边缘红赤、苔色转黄。",
        "treatment_principle": "疏肝解郁，清肝泻火 (Course Liver Qi, clear stagnant Liver-Gallbladder fire)",
        "recommended_formulas": ["丹栀逍遥散", "龙胆泻肝汤", "柴胡疏肝散"],
        "followup_questions": [
            "近期是否急躁易怒、胸胁胀满疼痛、口苦咽干或目赤头痛？",
            "睡眠是否多梦易醒，女性是否经行乳房胀痛或经期提前？",
        ],
    },
    {
        "id": "TP08",
        "pattern_name": "淡白瘦薄舌少苔",
        "english_name": "Pale Thin Small Tongue, Scanty Dry Coating",
        "syndrome": "气血两虚 / 心脾两虚证 (Qi & Blood Dual Deficiency)",
        "eight_principles": {
            "interior_exterior": "里证 (Interior)",
            "heat_cold": "虚寒或平 (Mild Deficiency Cold / Neutral)",
            "excess_deficiency": "虚证 (Deficiency)",
            "yin_yang": "气血俱不足 (Qi and Blood Depletion)",
        },
        "scores": {"exterior": 0, "interior": 3, "heat": 0, "cold": 1, "deficiency": 4, "excess": 0},
        "keywords": [
            "瘦薄", "瘦小", "干瘪", "淡白少苔", "舌淡瘦", "pale thin",
            "thin tongue", "small pale", "withered", "pale scanty",
        ],
        "zone_focus": "全舌形体瘦小失充，舌色浅淡无华",
        "pathomechanism": "久病耗伤、脾胃生化乏源或慢性失血，致气血双亏，不能上荣充养舌肌，故舌色淡白、舌体瘦薄、苔少乏津。",
        "treatment_principle": "益气养血，健脾养心 (Augment Qi, nourish Blood, fortify Spleen & Heart)",
        "recommended_formulas": ["八珍汤", "归脾汤", "人参养荣汤", "当归补血汤"],
        "followup_questions": [
            "是否面色苍白或萎黄、头晕眼花、心悸怔忡、倦怠乏力？",
            "是否有慢性失血、月经过多或长期饮食减少史？",
        ],
    },
    {
        "id": "TP09",
        "pattern_name": "白厚腻浊苔",
        "english_name": "Thick Turbid Greasy White Coating",
        "syndrome": "痰湿困脾 / 寒湿中阻 / 食积内停证 (Phlegm-Turbidity or Cold-Damp Encumbering Spleen)",
        "eight_principles": {
            "interior_exterior": "里证 (Interior)",
            "heat_cold": "寒证/湿证 (Cold-Damp)",
            "excess_deficiency": "实证或本虚标实 (Turbid Excess)",
            "yin_yang": "阴湿困遏清阳 (Turbid Yin Encumbering Clear Yang)",
        },
        "scores": {"exterior": 0, "interior": 3, "heat": 0, "cold": 2, "deficiency": 1, "excess": 3},
        "keywords": [
            "白厚腻", "白腻", "厚腻", "浊腻", "腐腻", "白腐", "thick white",
            "greasy white", "white greasy", "turbid white", "curdy",
        ],
        "zone_focus": "舌中及舌根苔厚白粘腻如涂猪脂或豆腐渣",
        "pathomechanism": "外感寒湿或恣食生冷肥甘，损伤脾阳，湿聚成饮化痰，或宿食停滞中焦，寒湿浊邪上泛聚于舌面而成白厚腻苔。",
        "treatment_principle": "燥湿化痰，温中散寒，理气消食 (Dry dampness, resolve phlegm, warm middle, move Qi)",
        "recommended_formulas": ["二陈汤", "平胃散", "藿香正气散", "保和丸"],
        "followup_questions": [
            "是否胸脘痞闷、头重如裹、口淡不渴或泛吐痰涎？",
            "近期有无进食油腻生冷后嗳腐吞酸、腹胀便溏？",
        ],
    },
    {
        "id": "TP10",
        "pattern_name": "灰黑燥苔或滑苔",
        "english_name": "Gray-Black Dry Cracked or Wet Slippery Coating",
        "syndrome": "极热伤阴（灰黑燥裂苔）或阳虚寒极（灰黑水滑苔）(Extreme Heat Consuming Yin or Extreme Cold-Yang Collapse)",
        "eight_principles": {
            "interior_exterior": "深重里证 (Deep Critical Interior)",
            "heat_cold": "燥裂主极热 / 滑润主极寒 (Dry=Extreme Heat; Wet=Extreme Cold)",
            "excess_deficiency": "实热劫津或真阳衰微 (Fulminant Excess Heat or Yang Exhaustion)",
            "yin_yang": "阴阳偏极危候 (Critical Yin or Yang Extremity — differentiate moisture!)",
        },
        "scores": {"exterior": 0, "interior": 4, "heat": 2, "cold": 2, "deficiency": 2, "excess": 2},
        "keywords": [
            "灰黑", "黑苔", "灰苔", "焦黑", "黑燥", "黑滑", "gray-black",
            "grey-black", "black coating", "gray coating", "charred coating",
        ],
        "zone_focus": "全舌或舌中舌根染灰黑色（须先排除乌梅、铁剂、咖啡、桑椹等染苔！）",
        "pathomechanism": "苔之润燥为灰黑苔辨寒热之铁则：若舌红绛而苔焦黑燥裂起刺，乃热极津枯；若舌淡白胖嫩而苔灰黑水滑，乃阳虚寒极、浊阴上泛。",
        "treatment_principle": "燥苔急下存阴（增液承气）；滑苔回阳救逆（四逆温阳）— 先排除饮食药物染苔！",
        "recommended_formulas": ["增液承气汤", "大承气汤", "四逆汤", "附子理中汤"],
        "followup_questions": [
            "【关键鉴别】近期是否食用乌梅、桑椹、黑芝麻、咖啡或服用铁剂、铋剂（排除假性染苔）？",
            "舌面是干涩燥裂伴高热烦渴便秘（极热），还是湿润多津伴畏寒肢厥下利清谷（极寒）？",
        ],
    },
    {
        "id": "TP11",
        "pattern_name": "红舌黄燥苔或老黄苔",
        "english_name": "Red Firm Body, Dry Rough Yellow Coating",
        "syndrome": "阳明气分大热 / 阳明腑实证 (Yangming Interior Excess Heat)",
        "eight_principles": {
            "interior_exterior": "里证 (Interior Yangming)",
            "heat_cold": "实热证 (Blazing Excess Heat)",
            "excess_deficiency": "实证 (Excess)",
            "yin_yang": "阳盛伤津 (Yang Excess Consuming Fluids)",
        },
        "scores": {"exterior": 0, "interior": 3, "heat": 4, "cold": 0, "deficiency": 0, "excess": 4},
        "keywords": [
            "黄燥", "老黄", "焦黄", "燥裂", "糙苔", "dry yellow",
            "rough yellow", "burnt yellow",
        ],
        "zone_focus": "舌中老黄燥裂，提示胃肠燥热结聚",
        "pathomechanism": "邪热入里传至阳明，气分大热或燥屎内结肠腑，邪热蒸腾胃浊并灼伤津液，故舌红苍老而苔黄干涩粗糙。",
        "treatment_principle": "辛寒清气或通腑泄热存阴 (Clear Qi-level heat or purge Yangming腑实)",
        "recommended_formulas": ["白虎汤", "调胃承气汤", "大承气汤"],
        "followup_questions": [
            "是否有壮热大汗、大烦大渴喜冷饮、脉洪大？",
            "大便是否秘结不通、腹满硬痛拒按？",
        ],
    },
]


def _extract_biometric_clues(biometrics: dict | None) -> tuple[list[str], dict]:
    """Translate quantitative vision biometrics into TCM tongue clues and summary."""
    if not biometrics or not isinstance(biometrics, dict):
        return [], {}

    derived_clues: list[str] = []
    interpretation: dict = {}

    lab = biometrics.get("lab_approx") or biometrics.get("lab") or {}
    if isinstance(lab, dict) and lab:
        l_val = lab.get("L", lab.get("L_mean", lab.get("l")))
        a_val = lab.get("a", lab.get("a_mean"))
        b_val = lab.get("b", lab.get("b_mean"))
        interpretation["cie_lab"] = {"L": l_val, "a": a_val, "b": b_val}

        if isinstance(a_val, (int, float)):
            if a_val >= 26:
                derived_clues.extend(["红绛", "舌红", "crimson"])
                interpretation["erythema_index"] = "High a* (>=26): crimson/deep-red body suggesting heat or Yin fire"
            elif a_val >= 19:
                derived_clues.extend(["舌红", "red body"])
                interpretation["erythema_index"] = "Elevated a* (19-25): reddish tongue body"
            elif a_val <= 11:
                derived_clues.extend(["淡白", "pale"])
                interpretation["erythema_index"] = "Low a* (<=11): pale blood-depleted or Yang-deficient body"
            else:
                derived_clues.append("淡红")
                interpretation["erythema_index"] = "Moderate a* (12-18): normal pale-red range"

        if isinstance(b_val, (int, float)):
            if b_val >= 18:
                derived_clues.extend(["黄腻", "薄黄", "dry yellow"])
                interpretation["yellowness_index"] = "High b* (>=18): yellow coating chromophore shift"
            elif b_val <= 2:
                derived_clues.extend(["青紫", "purple"])
                interpretation["yellowness_index"] = "Low/negative b* (<=2): bluish-purple stasis shift"

        if isinstance(l_val, (int, float)):
            if l_val <= 42:
                derived_clues.extend(["灰黑", "紫暗"])
                interpretation["luminance_note"] = "Low L* (<=42): dark/violaceous or gray-black surface"
            elif l_val >= 70 and isinstance(a_val, (int, float)) and a_val < 14:
                derived_clues.extend(["淡白", "白厚腻"])
                interpretation["luminance_note"] = "High L* (>=70) with low redness: pale body or thick white coat"

    hints = biometrics.get("tcm_visual_hints")
    if isinstance(hints, list):
        derived_clues.extend(str(h) for h in hints)
        interpretation["visual_hints"] = hints
    elif isinstance(hints, dict):
        derived_clues.extend(f"{k}:{v}" for k, v in hints.items())
        derived_clues.extend(str(v) for v in hints.values())
        interpretation["visual_hints"] = hints
    elif isinstance(hints, str) and hints.strip():
        derived_clues.append(hints.strip())
        interpretation["visual_hints"] = [hints.strip()]

    zones = biometrics.get("zones")
    if isinstance(zones, dict) and zones:
        interpretation["zone_biometrics"] = zones
        tip_info = str(zones.get("tip") or zones.get("舌尖") or "").lower()
        edge_info = str(zones.get("sides") or zones.get("edges") or zones.get("舌边") or "").lower()
        center_info = str(zones.get("center") or zones.get("middle") or zones.get("舌中") or "").lower()
        if "red" in tip_info or "红" in tip_info:
            derived_clues.append("舌尖红")
        if "red" in edge_info or "红" in edge_info:
            derived_clues.append("舌边红")
        if "yellow" in center_info or "黄" in center_info:
            derived_clues.append("黄腻")

    return derived_clues, interpretation


def _build_tongue_somatotopy(combined_text: str, biometrics: dict | None) -> dict:
    """Map tongue observations onto the Four Somatotopic Organ Zones (舌面脏腑分候)."""
    zones_in = (biometrics or {}).get("zones", {}) if isinstance(biometrics, dict) else {}
    text_low = combined_text.lower()

    tip_notes = []
    if any(k in text_low for k in ("舌尖红", "尖红", "起刺", "芒刺", "red tip", "tip red", "prickly")):
        tip_notes.append("舌尖红赤/点刺 → 心火亢盛或上焦肺卫郁热 (Heart/Lung heat)")
    if zones_in.get("tip") or zones_in.get("舌尖"):
        tip_notes.append(f"Image zone: {zones_in.get('tip') or zones_in.get('舌尖')}")

    center_notes = []
    if any(k in text_low for k in ("黄腻", "yellow greasy")):
        center_notes.append("舌中苔黄腻 → 脾胃湿热或痰热中阻 (Middle-Jiao damp-heat)")
    elif any(k in text_low for k in ("白腻", "白厚", "白滑", "greasy white", "wet white", "thick white")):
        center_notes.append("舌中白腻/水滑 → 寒湿痰饮困脾 (Spleen encumbered by cold-damp/phlegm)")
    elif any(k in text_low for k in ("剥苔", "少苔", "裂纹", "peeled", "fissur", "scanty")):
        center_notes.append("舌中少苔/剥落/裂纹 → 胃阴不足，气阴两伤 (Stomach Yin depletion)")
    if zones_in.get("center") or zones_in.get("middle") or zones_in.get("舌中"):
        center_notes.append(
            f"Image zone: {zones_in.get('center') or zones_in.get('middle') or zones_in.get('舌中')}"
        )

    edge_notes = []
    if any(k in text_low for k in ("舌边红", "边红", "red edges", "edges red", "red sides")):
        edge_notes.append("舌边红赤 → 肝郁化火或肝胆火旺 (Liver-Gallbladder fire)")
    if any(k in text_low for k in ("齿痕", "scalloped", "teeth-mark", "tooth-mark", "teeth mark")):
        edge_notes.append("舌边齿痕 → 脾虚湿盛，舌体胖嫩受齿挤压 (Spleen Qi/Yang deficiency with dampness)")
    if any(k in text_low for k in ("瘀斑", "瘀点", "petechiae")):
        edge_notes.append("舌边瘀点瘀斑 → 肝经气滞血瘀 (Liver channel Blood stasis)")
    if zones_in.get("sides") or zones_in.get("edges") or zones_in.get("舌边"):
        edge_notes.append(
            f"Image zone: {zones_in.get('sides') or zones_in.get('edges') or zones_in.get('舌边')}"
        )

    root_notes = []
    if any(k in text_low for k in ("舌根厚", "根腻", "灰黑", "black coating", "gray-black")):
        root_notes.append("舌根苔厚或灰黑 → 下焦湿浊或肾司二便失常 (Lower-Jiao turbidity / Kidney)")
    elif any(k in text_low for k in ("红绛", "少苔", "crimson")):
        root_notes.append("舌根红绛少津 → 肾阴亏虚，相火妄动 (Kidney Yin deficiency)")
    if zones_in.get("root") or zones_in.get("base") or zones_in.get("舌根"):
        root_notes.append(f"Image zone: {zones_in.get('root') or zones_in.get('base') or zones_in.get('舌根')}")

    return {
        "舌尖心肺 (Tip - Heart & Lung / Upper Jiao)": tip_notes or ["未见明显局部异常 (Unremarkable)"],
        "舌中脾胃 (Center - Spleen & Stomach / Middle Jiao)": center_notes or ["胃气尚可 (Unremarkable)"],
        "舌边肝胆 (Edges - Liver & Gallbladder)": edge_notes or ["未见明显郁火或齿痕 (Unremarkable)"],
        "舌根肾与下焦 (Root - Kidney & Lower Jiao)": root_notes or ["下焦未见明显异常 (Unremarkable)"],
    }


def _score_tongue_patterns(combined_text: str) -> list[dict]:
    """Score all canonical tongue patterns against combined text + biometric tokens."""
    text_low = combined_text.lower()
    scored: list[dict] = []

    for pat in TONGUE_PATTERNS:
        matched = [kw for kw in pat["keywords"] if kw.lower() in text_low]
        if not matched:
            continue
        raw_hits = len(matched)
        conf = min(0.98, round(0.42 + 0.14 * raw_hits, 2))
        # Refine gray-black dry vs slippery sub-differentiation
        pat_syndrome = pat["syndrome"]
        if pat["id"] == "TP10":
            if any(w in text_low for w in ("燥", "裂", "干", "dry", "cracked", "rough")):
                pat_syndrome = "热极伤阴证（灰黑燥裂苔 — Extreme Interior Heat Exhausting Yin）"
                conf = min(0.98, round(conf + 0.12, 2))
            elif any(w in text_low for w in ("滑", "润", "湿", "淡白", "slippery", "wet", "moist", "pale")):
                pat_syndrome = "阳虚寒极证（灰黑水滑苔 — Extreme Interior Cold / Yang Collapse）"
                conf = min(0.98, round(conf + 0.12, 2))

        scored.append({
            "pattern_id": pat["id"],
            "pattern_name": pat["pattern_name"],
            "english_name": pat["english_name"],
            "syndrome": pat_syndrome,
            "confidence": conf,
            "matched_clues": matched,
            "eight_principles": pat["eight_principles"],
            "pathomechanism": pat["pathomechanism"],
            "treatment_principle": pat["treatment_principle"],
            "recommended_formulas": pat["recommended_formulas"],
            "_scores": pat["scores"],
            "_followup": pat["followup_questions"],
        })

    scored.sort(key=lambda item: item["confidence"], reverse=True)
    return scored


@registry.register(
    name="diagnostics.tongue_analyze",
    description=(
        "Analyze TCM tongue inspection findings (望舌: tongue body color/shape, coating color/texture, "
        "sublingual veins, and optional quantitative image biometrics) into Eight Principles, "
        "somatotopy organ zones, ranked syndromes, and classical formulas."
    ),
    category="diagnostics",
    parameters={
        "observations": "Free-text tongue description (Chinese or English)",
        "body_color": "Tongue body color (舌色: e.g., 淡白, 淡红, 红, 红绛, 青紫)",
        "body_shape": "Tongue body shape/features (舌形: e.g., 胖大, 齿痕, 瘦薄, 裂纹, 点刺)",
        "coating_color": "Coating color (苔色: e.g., 白, 黄, 灰黑)",
        "coating_texture": "Coating texture (苔质: e.g., 薄, 厚, 腻, 滑, 燥, 少苔, 剥苔)",
        "sublingual": "Sublingual vein findings (舌下络脉: e.g., 迂曲怒张, 紫暗)",
        "biometrics": "Optional quantitative image analysis dict (lab_approx, zones, tcm_visual_hints)",
    },
    usage_guide="When analyzing tongue photos/biometrics or clinical tongue examination descriptions.",
)
def tongue_analyze(
    observations: str = "",
    body_color: str = "",
    body_shape: str = "",
    coating_color: str = "",
    coating_texture: str = "",
    sublingual: str = "",
    biometrics: dict | None = None,
) -> dict:
    """Perform multimodal TCM tongue pattern differentiation (舌诊辨证)."""
    bio_clues, bio_interp = _extract_biometric_clues(biometrics)
    parts = [
        observations, body_color, body_shape, coating_color, coating_texture, sublingual,
        " ".join(bio_clues),
    ]
    combined = " ".join(p.strip() for p in parts if p and str(p).strip())

    if not combined:
        return {
            "status": "insufficient_input",
            "message": (
                "Please provide tongue observations (e.g., '舌淡胖有齿痕，苔白滑' or "
                "body_color='red', coating_color='yellow', coating_texture='greasy') or image biometrics."
            ),
            "supported_patterns_count": len(TONGUE_PATTERNS),
        }

    scored = _score_tongue_patterns(combined)
    somatotopy = _build_tongue_somatotopy(combined, biometrics)

    if not scored:
        # Fallback baseline when general tokens don't hit specific canonical phrases
        fallback = TONGUE_PATTERNS[0]
        return {
            "status": "complete",
            "input_summary": combined,
            "primary_syndrome": {
                "pattern_id": fallback["id"],
                "pattern_name": fallback["pattern_name"],
                "english_name": fallback["english_name"],
                "syndrome": fallback["syndrome"],
                "confidence": 0.35,
                "matched_clues": [],
                "treatment_principle": fallback["treatment_principle"],
                "recommended_formulas": fallback["recommended_formulas"],
            },
            "differential_syndromes": [],
            "eight_principles": fallback["eight_principles"],
            "somatotopy_zones": somatotopy,
            "recommended_formulas": fallback["recommended_formulas"],
            "biometric_interpretation": bio_interp,
            "clinical_followup_questions": fallback["followup_questions"],
        }

    top = scored[0]
    followups: list[str] = []
    formula_refs: list[dict] = []
    seen_formulas: set[str] = set()

    for item in scored[:3]:
        for q in item["_followup"]:
            if q not in followups:
                followups.append(q)
        for fname in item["recommended_formulas"]:
            if fname not in seen_formulas:
                seen_formulas.add(fname)
                fdb = FORMULA_DB.get(fname)
                formula_refs.append({
                    "formula": fname,
                    "english": fdb["english"] if fdb else "",
                    "functions": fdb["functions"] if fdb else "Classical formula for matched tongue pattern",
                    "in_local_formula_db": fdb is not None,
                })

    clean_candidates = [
        {k: v for k, v in c.items() if not k.startswith("_")}
        for c in scored
    ]

    return {
        "status": "complete",
        "input_summary": combined,
        "primary_syndrome": clean_candidates[0],
        "primary_syndromes": clean_candidates[:3],
        "differential_syndromes": clean_candidates[1:4],
        "candidate_patterns": clean_candidates[:5],
        "eight_principles": {
            **top["eight_principles"],
            "dimension_scores": top["_scores"],
        },
        "somatotopy_zones": somatotopy,
        "recommended_formulas": formula_refs,
        "biometric_interpretation": bio_interp,
        "clinical_followup_questions": followups[:5],
    }


# ─── 2. Macroscopic Herb Authentication (中药饮片性状鉴别库) ──────────────────────

DECOCTION_PIECE_DB: dict[str, dict] = {
    "黄芪": {
        "pinyin": "Huáng Qí",
        "latin": "Radix Astragali (Astragalus membranaceus)",
        "english": "Astragalus Root",
        "hallmark_mnemonic": "金井玉栏菊花心，豆腥气味甘微温",
        "macroscopic_features": [
            "横切或斜切厚片，皮部黄白色，木部淡黄色，习称『金井玉栏』(pale cortex & yellow xylem)",
            "木质部具放射状纹理及裂隙，习称『菊花心』(chrysanthemum-heart radial striations)",
            "质硬而韧，断面强纤维性并显粉性 (tough fibrous & starchy fracture)",
            "气微，嚼之微甜而有特异『豆腥气』(characteristic raw bean-like aroma & sweet taste)",
        ],
        "keywords": [
            "菊花心", "豆腥气", "豆腥", "金井玉栏", "chrysanthemum", "bean", "bean-like",
            "radial striation", "pale yellow cortex", "astragal", "黄芪", "炙黄芪", "生黄芪",
        ],
        "processing_specs": {
            "生黄芪 (Raw Astragalus)": "表皮淡棕黄，长于固表止汗、托毒生肌、利水消肿",
            "炙黄芪 (Honey-fried Astragalus)": "蜜炙后表面深黄微亮、略带粘性及蜜香，长于补中益气升阳",
        },
        "adulterants_and_lookalikes": [
            "红芪 (Radix Hedysari): 外皮红棕色，无豆腥气，化学主含红芪多糖而非黄芪甲苷",
            "锦鸡儿/蓝花棘豆根 (Caragana / Oxytropis伪品): 木部偏硬无菊花心裂隙，味淡微苦涩，具潜在神经毒性",
            "蜀葵根/圆叶锦葵根: 断面黏液质重，无豆腥气",
        ],
        "chemical_markers": ["Astragaloside IV (黄芪甲苷 >=0.080%)", "Calycosin-7-O-beta-D-glucoside (毛蕊异黄酮葡萄糖苷)"],
    },
    "人参": {
        "pinyin": "Rén Shēn",
        "latin": "Radix et Rhizoma Ginseng (Panax ginseng)",
        "english": "Asian Ginseng",
        "hallmark_mnemonic": "芦碗铁线珍珠点，皮部黄棕树脂道",
        "macroscopic_features": [
            "顶端具根茎习称『芦头』，上具凹窝状茎痕习称『芦碗』(bowl-shaped rhizome stem scars)",
            "主根上部具细密深陷横环纹习称『铁线纹』，须根具不明显疣状突起习称『珍珠点』(pearl warts)",
            "断面淡黄白色，形成层环明显，皮部散有黄棕色点状『树脂道』(brownish resin canal dots)",
            "香气特异，味微苦而回甘 (specific fragrance, bittersweet aftertaste)",
        ],
        "keywords": [
            "芦头", "芦碗", "珍珠点", "铁线纹", "树脂道", "rhizome scar", "pearl wart",
            "resin canal", "ginseng", "人参", "红参", "生晒参",
        ],
        "processing_specs": {
            "生晒参 (Sun-dried Ginseng)": "性微温偏平，大补元气、生津养阴安神",
            "红参 (Steamed Red Ginseng)": "蒸制后棕红半透明角质样，性温力峻，长于温补回阳固脱",
        },
        "adulterants_and_lookalikes": [
            "西洋参 (Panax quinquefolius): 无芦碗或较小，横环纹细密，性凉清火生津，味苦重回甘",
            "党参 (Codonopsis Radix): 根头具多数疣状茎痕习称『狮子盘头』，皮部无树脂道，味甜无苦味",
            "【有毒伪品】商陆 (Phytolaccae Radix): 断面具同心性罗盘纹，嚼之麻舌有毒，严禁混用！",
        ],
        "chemical_markers": ["Ginsenoside Rg1 (人参皂苷Rg1)", "Ginsenoside Re", "Ginsenoside Rb1"],
    },
    "党参": {
        "pinyin": "Dǎng Shēn",
        "latin": "Radix Codonopsis (Codonopsis pilosula)",
        "english": "Codonopsis Root",
        "hallmark_mnemonic": "狮子盘头菊花心，气香味甜无树脂道",
        "macroscopic_features": [
            "根头部有多数疣状突起的茎痕及芽，习称『狮子盘头』(lion's-head warty crown)",
            "根头下有致密环状横纹，断面皮部淡黄白至棕黄，木部黄色具放射纹理，裂隙多",
            "有特殊浓郁果糖甜香，味甜，嚼之无渣 (sweet mucilaginous taste, no resin canals)",
        ],
        "keywords": ["狮子盘头", "lion head crown", "codonopsis", "党参"],
        "processing_specs": {
            "生党参": "健脾益肺，养血生津",
            "米炒党参": "增强健脾止泻之力",
        },
        "adulterants_and_lookalikes": [
            "银柴胡: 根头『珍珠盘』（密集白棕色疣状芽痕），味淡不甜，清虚热药",
            "人参: 具芦碗与黄棕色树脂道点，味微苦回甘",
        ],
        "chemical_markers": ["Lobetyolin (党参炔苷)", "Codonopsis polysaccharides"],
    },
    "黄连": {
        "pinyin": "Huáng Lián",
        "latin": "Rhizoma Coptidis (Coptis chinensis)",
        "english": "Coptis Rhizome",
        "hallmark_mnemonic": "鸡爪味连过桥杆，断面鲜黄紫外金光",
        "macroscopic_features": [
            "味连多分枝集聚成簇，弯曲如鸡爪，习称『鸡爪连』(chicken-claw clustered rhizomes)",
            "中段有光滑细长节间，习称『过桥』(smooth internode bridge)",
            "断面不整齐，皮部橙红色或暗棕色，木部鲜黄色或橙黄色，髓部有时中空",
            "365nm紫外灯下木质部显金黄色强烈荧光 (brilliant golden-yellow berberine UV fluorescence)；味极苦",
        ],
        "keywords": [
            "鸡爪连", "鸡爪", "过桥", "鲜黄", "紫外", "金黄荧光", "味极苦", "chicken-claw",
            "chicken claw", "internode", "fluorescence", "uv", "berberine", "golden-yellow",
            "coptis", "黄连", "雅连", "云连",
        ],
        "processing_specs": {
            "生黄连": "苦寒直折，清心胃实火、燥湿解毒",
            "酒黄连 (Wine-fried)": "引药上行，善清头目上焦之火",
            "姜黄连 (Ginger-juice fried)": "缓其苦寒，善清胃热、和胃止呕",
            "萸黄连 (Evodia-processed)": "舒肝和胃止呕，专治肝火犯胃胁痛吞酸（如左金丸）",
        },
        "adulterants_and_lookalikes": [
            "雅连 (Coptis deltoidea): 单枝多，『过桥』较长；云连 (Coptis teeta): 细小弯曲如钩",
            "胡黄连 (Picrorhizae Rhizoma): 断面灰黑色或棕黑色，具4-10个白色点状维管束环，主清虚热疳热",
            "十大功劳茎/小檗根: 形粗大无鸡爪过桥特征",
        ],
        "chemical_markers": ["Berberine (小檗碱 >=5.5%)", "Epiberberine (表小檗碱)", "Coptisine (黄连碱)", "Palmatine (巴马汀)"],
    },
    "当归": {
        "pinyin": "Dāng Guī",
        "latin": "Radix Angelicae Sinensis (Angelica sinensis)",
        "english": "Chinese Angelica Root",
        "hallmark_mnemonic": "归头归身与归尾，皮部棕油气清香",
        "macroscopic_features": [
            "全根分三部：根头膨大具环纹为『归头』，主根粗短为『归身』，支根上粗下细多扭曲为『归尾』",
            "外皮黄棕色至棕褐色，质柔韧，断面黄白色或淡黄棕色",
            "皮部厚，有裂隙及多数棕色点状分泌腔（挥发油室油环 brown oil rings/dots）",
            "香气浓郁特异（藁本内酯芳香气 intense ligustilide aroma），味甘、辛、微苦",
        ],
        "keywords": [
            "归头", "归身", "归尾", "油室", "棕色油点", "油环", "藁本内酯", "气清香浓郁",
            "ligustilide", "oil ring", "oil dots", "angelica", "当归", "酒当归",
        ],
        "processing_specs": {
            "全当归": "既补血又活血，和血调经",
            "当归头 / 当归身 / 当归尾": "归头偏止血上行，归身专补血守中，归尾偏破血通经下行",
            "酒当归 (Wine-fried)": "活血通经祛瘀之力大增",
            "土炒当归": "既能补血又不致滑肠，宜于血虚便溏者",
        },
        "adulterants_and_lookalikes": [
            "欧当归 (Levisticum officinale): 气浊如芹菜陈腐气，根头常中空，具光敏毒性差异",
            "东当归 (Angelica acutiloba): 支根细多，香气较弱而味辛麻",
            "独活 (Radix Angelicae Pubescentis): 根头粗大有横纹，气浊香，味苦辛而麻舌",
        ],
        "chemical_markers": ["Z-Ligustilide (藁本内酯)", "Ferulic acid (阿魏酸 >=0.050%)"],
    },
    "白术": {
        "pinyin": "Bái Zhú",
        "latin": "Rhizoma Atractylodis Macrocephalae",
        "english": "White Atractylodes Rhizome",
        "hallmark_mnemonic": "云头鸡腿朱砂点，麸炒焦香健脾良",
        "macroscopic_features": [
            "不规则肥厚团块，上端膨大如云头、下端渐细弯曲如鸡腿，习称『云头鸡腿』或『鹤形』",
            "表面灰黄色或灰棕色，具瘤状突起及断续纵皱纹",
            "断面黄白色至淡棕色，散生棕黄或棕红色油点（『朱砂点』cinnabar oil cavities）；烘术断面角质样有裂隙",
            "气清香，味甘微辛，嚼之略带粘液性 (sweet-acrid, slightly mucilaginous)",
        ],
        "keywords": [
            "云头鸡腿", "鹤形", "朱砂点", "烘术", "麸炒白术", "cloud-head", "chicken-leg",
            "cinnabar", "atractylod", "白术", "生白术",
        ],
        "processing_specs": {
            "生白术 (Raw)": "长于燥湿利水、运脾通便（大剂量30-60g治脾虚便秘）",
            "麸炒白术 (Bran-fried)": "表面深黄偶带焦斑、具麦麸焦香，缓其燥性，专长健脾益气、安胎",
            "土炒白术 (Earth-fried)": "灶心土或赤石脂炒，专长补脾止泻",
        },
        "adulterants_and_lookalikes": [
            "苍术 (Rhizoma Atractylodis): 呈连珠状或结节圆柱形，断面朱砂点极密且暴露久置可析出白毛状结晶『起霜』，辛燥气极浓烈",
            "白芷片: 形成层环近方形，灰棕色油点排成环状，香气浓烈无粘牙感",
        ],
        "chemical_markers": ["Atractylenolide I & III (白术内酯I、III)", "Atractylone (苍术酮)"],
    },
    "茯苓": {
        "pinyin": "Fú Líng",
        "latin": "Poria (Poria cocos / Wolfiporia extensa)",
        "english": "Poria Sclerotium",
        "hallmark_mnemonic": "雪白细腻嚼粘牙，抱松根心号茯神",
        "macroscopic_features": [
            "去皮切制为白色立方块『茯苓块』或薄片『白茯苓片』，颜色雪白或淡粉白，质地致密细腻粉性",
            "中间抱有松根者切制后习称『茯神』(pine-root core inside sclerotium)",
            "气微，味淡，嚼之粘牙 (odorless, bland, sticks to teeth when chewed)",
            "理化特征：真品主含β-茯苓聚糖，加碘试液不显深蓝色，水煮不糊化崩解",
        ],
        "keywords": [
            "雪白细腻", "茯苓块", "茯神", "嚼之粘牙", "粘牙", "松根", "poria",
            "granular white", "pine root", "茯苓", "赤茯苓", "茯苓皮",
        ],
        "processing_specs": {
            "白茯苓": "健脾渗湿，实脾止泻",
            "赤茯苓 (Pink outer layer)": "偏于清利下焦湿热",
            "茯苓皮 (Outer dark skin)": "专于行皮肤水湿、利水消肿",
            "茯神 / 朱茯神": "专入心经，宁心安神定惊",
        },
        "adulterants_and_lookalikes": [
            "米粉/淀粉/石膏压制伪品: 遇碘液立即显深蓝紫色，入沸水即糊化散碎，嚼之不粘牙或有砂砾感",
            "猪苓 (Polyporus): 外皮乌黑薄皱，断面洁白或淡黄但质轻体松如软木塞，嚼之不粘牙",
        ],
        "chemical_markers": ["Pachymic acid (茯苓酸)", "Beta-pachyman (茯苓聚糖)"],
    },
    "川贝母": {
        "pinyin": "Chuān Bèi Mǔ",
        "latin": "Bulbus Fritillariae Cirrhosae",
        "english": "Tendrilleaf Fritillary Bulb",
        "hallmark_mnemonic": "松贝怀中抱月坐，青贝观音合掌开",
        "macroscopic_features": [
            "松贝呈类圆锥形或近球形小珠（高0.3-0.8cm），外层两瓣鳞叶大小悬殊，大瓣紧抱小瓣，未抱部分呈新月形，习称『怀中抱月』；顶端闭合，底部平可直立",
            "青贝外层两鳞叶大小相近，相对抱合而顶端开裂，习称『观音合掌』",
            "炉贝呈长圆锥形如马牙，表面常有棕黄色斑块习称『虎皮斑』",
            "表面类白色，富粉性，气微，味微苦 (ivory-white starchy bulb, mildly bitter)",
        ],
        "keywords": [
            "怀中抱月", "观音合掌", "虎皮斑", "松贝", "青贝", "炉贝", "holding the moon",
            "guanyin", "fritillaria", "川贝", "川贝母",
        ],
        "processing_specs": {
            "生川贝母（研粉冲服）": "性微寒味甘苦，润肺化痰、清热散结，贵重药材多研细粉1-2g冲服或炖梨",
        },
        "adulterants_and_lookalikes": [
            "浙贝母 (Fritillaria thunbergii): 鳞叶肥大呈新月形大片（大贝直径2-3.5cm），味苦重，偏于清肺化痰散结（治风热痰火实证），价廉不可冒充川贝",
            "平贝母 (Fritillaria ussuriensis): 呈扁球形如算盘珠，顶端微凹",
            "【剧毒伪品】光慈姑/丽江山慈姑 (Iphigenia indica): 呈圆锥形一侧有纵沟，断面角质样半透明，含剧毒秋水仙碱 (Colchicine)，误服可致死！",
        ],
        "chemical_markers": ["Imperialine / Sipeimine (西贝母碱)", "Peimisine (贝母辛)"],
    },
    "三七": {
        "pinyin": "Sān Qī",
        "latin": "Radix et Rhizoma Notoginseng (Panax notoginseng)",
        "english": "Notoginseng Root",
        "hallmark_mnemonic": "铜皮铁骨狮子头，断面蜡绿苦回甘",
        "macroscopic_features": [
            "主根类圆锥或圆柱形，表面灰褐色或灰黄色带断续纵皱，习称『铜皮』(bronze skin)",
            "质地坚实沉重如铁，击碎时皮部与木部常微分离，习称『铁骨』(iron bone)",
            "顶端茎痕周围有瘤状突起习称『狮子头』(lion-head knobbed crown)",
            "断面灰绿色、黄绿色或灰褐色，具蜡样光泽（角质样 olive-green waxy luster）及放射状菊花心；味苦而后微甜（苦后回甘）",
        ],
        "keywords": [
            "铜皮铁骨", "狮子头", "铜皮", "铁骨", "蜡样光泽", "灰绿", "苦后回甘",
            "bronze skin", "iron bone", "lion head", "olive-green", "waxy",
            "notoginseng", "三七", "田七",
        ],
        "processing_specs": {
            "生三七粉 (Raw powder, 1-3g冲服)": "『生打』——散瘀止血、消肿定痛，止血而不留瘀",
            "熟三七 (Steamed / Oil-processed)": "『熟补』——长于补血养血、扶正培元",
        },
        "adulterants_and_lookalikes": [
            "【致命肝毒伪品】菊三七/土三七 (Gynura japonica): 断面黄色纤维性无蜡光，味苦酸无回甘，含吡咯里西啶生物碱 (Pyrrolizidine alkaloids)，可致不可逆肝窦阻塞综合征 (HSOS/VOD)！",
            "莪术/姜黄雕刻伪品: 表面可见刀削痕，具浓烈姜樟辛辣气，遇碘显蓝紫色",
        ],
        "chemical_markers": ["Notoginsenoside R1 (三七皂苷R1)", "Ginsenoside Rg1", "Ginsenoside Rb1", "Dencichine (田七氨酸)"],
    },
    "柴胡": {
        "pinyin": "Chái Hú",
        "latin": "Radix Bupleuri (Bupleurum chinense / B. scorzonerifolium)",
        "english": "Bupleurum Root",
        "hallmark_mnemonic": "北柴胡硬片状纤，南柴胡软败油气",
        "macroscopic_features": [
            "北柴胡呈圆锥形常有分枝，根头膨大，顶端残留多数纤维状叶基（毛刷状 fibrous leaf-base tuft），质硬而韧，断面显片状纤维性 (laminated shaly fracture)",
            "南柴胡（红柴胡）较细不分支，表面红棕色，质稍软易折断，断面平坦不显纤维性，具微弱『败油气』(rancid oil odor)",
        ],
        "keywords": [
            "片状纤维", "败油气", "叶基纤维", "北柴胡", "南柴胡", "醋柴胡",
            "shaly fracture", "bupleur", "柴胡",
        ],
        "processing_specs": {
            "生柴胡": "升散力强，主和解少阳、退热疏邪（如小柴胡汤）",
            "醋柴胡 (Vinegar-fried)": "缓其升散，引药入肝经，增强疏肝止痛之力（如柴胡疏肝散）",
            "鳖血柴胡": "抑制劫肝阴之弊，用于阴虚骨蒸劳热",
        },
        "adulterants_and_lookalikes": [
            "【剧毒禁用】大叶柴胡 (Bupleurum longiradiatum): 根茎细长具密生环节且中空，含剧毒大叶柴胡毒素 (Bupleurotoxin)，致惊厥呼吸麻痹，药典严禁入药！",
            "柴胡地上茎叶混充: 髓部中空或疏松，皂苷含量极低",
        ],
        "chemical_markers": ["Saikosaponin A (柴胡皂苷a)", "Saikosaponin D (柴胡皂苷d)"],
    },
    "甘草": {
        "pinyin": "Gān Cǎo",
        "latin": "Radix et Rhizoma Glycyrrhizae (Glycyrrhiza uralensis)",
        "english": "Licorice Root",
        "hallmark_mnemonic": "红皮黄心菊花纹，折断粉尘味甘甜",
        "macroscopic_features": [
            "外皮红棕色或暗棕色具纵皱纹（红皮甘草），切面略显纤维性，黄白色至鲜黄色",
            "形成层环明显，射线放射状有裂隙习称『菊花心』；根茎中心有髓，根无髓",
            "折断时有粉尘飞扬 (starch dust puff on snapping)，气微，味甜而特殊 (intensely sweet)",
        ],
        "keywords": [
            "红皮", "粉尘飞扬", "味甜而特殊", "甘甜", "glycyrrhiz", "licorice",
            "sweet taste", "甘草", "炙甘草", "生甘草",
        ],
        "processing_specs": {
            "生甘草 (Raw Licorice)": "性平偏凉，长于清热解毒、利咽祛痰、缓急调和诸药",
            "炙甘草 (Honey-fried Licorice)": "蜜炙表面红棕微亮，性温，专长补脾和胃、益气复脉（如炙甘草汤）",
        },
        "adulterants_and_lookalikes": [
            "刺果甘草 (Glycyrrhiza pallidiflora): 木化程度高，味苦涩不甜，不含甘草甜素",
            "苦参片: 皮部黄白薄，味极苦，切勿与甘草饮片混装！",
        ],
        "chemical_markers": ["Glycyrrhizic acid / Glycyrrhizin (甘草酸 >=2.0%)", "Liquiritin (甘草苷 >=0.50%)"],
    },
    "附子": {
        "pinyin": "Fù Zǐ",
        "latin": "Radix Aconiti Lateralis Praeparata (Aconitum carmichaelii)",
        "english": "Prepared Lateral Aconite Root",
        "hallmark_mnemonic": "黑顺茶棕角质亮，多角形成必先煎",
        "macroscopic_features": [
            "黑顺片为纵切片，上宽下窄，外皮黑褐色，切面暗黄色或茶棕色，半透明角质样并具油润光泽，可见纵向导管束脉纹",
            "白附片剥去外皮，全体黄白色、半透明角质样；横切面可见『多角形形成层环』(polygonal cambium ring)",
            "盐附子表面灰黑色被白色盐霜；合格炮制品气微、口尝味淡而『无麻舌感』！",
        ],
        "keywords": [
            "黑顺片", "白附片", "盐附子", "多角形形成层", "乌头碱", "麻舌", "先煎",
            "aconit", "black slice", "horny translucent", "附子", "制附子", "炮附子",
        ],
        "processing_specs": {
            "黑顺片 / 白附片 / 炮附片": (
                "【安全铁律】生附子含剧毒双酯型生物碱（乌头碱 Aconitine，口服0.2mg即可中毒，2-4mg致死）！"
                "临床必须使用炮制品，且汤剂须『先煎 30-60 分钟』至口尝绝无麻舌感，使双酯型水解为低毒单酯型苯甲酰乌头原碱；严禁与半夏、瓜蒌、贝母、白蔹、白及同用（十八反）！"
            ),
        },
        "adulterants_and_lookalikes": [
            "【同名异物警示】白附子（禹白附 Typhonium giganteum）: 为天南星科植物块茎，祛风痰逐寒湿药，与毛茛科『白附片（附子）』基原功效截然不同，切勿混淆！",
            "生川乌/生草乌饮片: 未完全炮制者尝之麻辣刺痛，严禁直接内服",
        ],
        "chemical_markers": [
            "Monoester alkaloids: Benzoylaconine, Benzoylmesaconine, Benzoylhypaconine",
            "Toxic diester limit: Aconitine + Mesaconitine + Hypaconitine strictly <=0.020%",
        ],
    },
    "陈皮": {
        "pinyin": "Chén Pí",
        "latin": "Pericarpium Citri Reticulatae (Citrus reticulata)",
        "english": "Aged Tangerine Peel",
        "hallmark_mnemonic": "广陈三瓣相连剥，对光油室透而明",
        "macroscopic_features": [
            "广陈皮（新会陈皮）常剥成数瓣，基部相连，标准为规整『三瓣相连』(three connected lobes)",
            "外表面橙红色或红棕色（久贮呈深褐色），有无数大而凹入的油室，对光照视『透明清晰』(translucent oil dots against light)",
            "内表面浅黄白色海绵状『橘白』，附黄白色筋络（橘络维管束）；气香醇厚，味辛、苦，以陈久者良",
        ],
        "keywords": [
            "三瓣", "广陈皮", "新会陈皮", "油室", "对光透明", "橘白", "陈久者良",
            "three lobes", "translucent oil", "tangerine peel", "citri", "陈皮",
        ],
        "processing_specs": {
            "陈皮（自然陈化3年以上）": "挥发油燥烈之性减退而多甲氧基黄酮富集，理气健脾、燥湿化痰而不伤津",
            "炒陈皮 / 麸炒陈皮": "温中健脾之力更佳",
        },
        "adulterants_and_lookalikes": [
            "普通橘皮（陈皮通货）: 多为不规则碎片，油室细小不透光，味苦涩偏燥",
            "青皮 (Pericarpium Citri Reticulatae Viride): 幼果或未成熟果皮，外皮灰绿至黑绿，专于疏肝破气消积",
            "化橘红: 外被密柔毛（毛橘红），偏于燥湿化寒痰",
        ],
        "chemical_markers": ["Hesperidin (橙皮苷 >=3.5%)", "Nobiletin (川陈皮素)", "Tangeretin (橘皮素)"],
    },
    "半夏": {
        "pinyin": "Bàn Xià",
        "latin": "Rhizoma Pinelliae (Pinellia ternata)",
        "english": "Pinellia Tuber",
        "hallmark_mnemonic": "圆球凹顶麻点密，生品戟喉制后安",
        "macroscopic_features": [
            "类球形或扁球形，直径0.8-1.5cm，顶端有凹陷茎痕习称『肚脐眼』，周围密布麻点状根痕",
            "表面白色或浅黄色，断面洁白、富粉性；生半夏尝之极度麻辣刺喉（草酸钙针晶刺激黏膜）",
        ],
        "keywords": [
            "肚脐眼", "麻点根痕", "戟人咽喉", "清半夏", "姜半夏", "法半夏",
            "pinellia", "半夏",
        ],
        "processing_specs": {
            "清半夏 (Alum-processed)": "白矾制，长于燥湿化痰",
            "姜半夏 (Ginger + Alum)": "断面淡棕半透明角质样，专长温中止呕",
            "法半夏 (Licorice + Lime)": "断面黄色粉性，长于燥湿且调和脾胃",
        },
        "adulterants_and_lookalikes": [
            "水半夏 (Typhonium flagelliforme): 呈圆锥形或椭圆形，上端无凹陷肚脐眼，根痕仅在顶端附近，止呕力弱不可代半夏",
            "天南星: 扁球形更大（直径1.5-3cm），周围有小侧芽如虎掌",
        ],
        "chemical_markers": ["Succinic acid (琥珀酸)", "Total organic acids", "Calcium oxalate raphides (reduced by炮制)"],
    },
}


@registry.register(
    name="diagnostics.herb_identify",
    description=(
        "Authenticate Chinese herbal decoction pieces (中药饮片性状鉴别) from macroscopic features "
        "(cross-section, aroma, taste, UV fluorescence, shape hallmarks) and optional image biometrics. "
        "Returns matched specimens, processing specs (炮制), adulterant warnings, and active markers."
    ),
    category="diagnostics",
    parameters={
        "features": "Macroscopic description (e.g., '菊花心, 豆腥气, pale yellow cortex' or '怀中抱月')",
        "candidate_name": "Optional suspected herb name to verify or refute",
        "biometrics": "Optional image biometrics dict (lab_approx, tcm_visual_hints)",
    },
    usage_guide="When identifying raw herbs/decoction pieces from photos or macroscopic pharmacognosy traits.",
)
def herb_identify(
    features: str,
    candidate_name: str = "",
    biometrics: dict | None = None,
) -> dict:
    """Identify TCM decoction pieces via classical pharmacognosy hallmarks (性状鉴别)."""
    bio_clues, bio_interp = _extract_biometric_clues(biometrics)
    query_blob = f"{features} {candidate_name} {' '.join(bio_clues)}".strip()
    if not query_blob:
        return {
            "status": "not_found",
            "message": "Please provide macroscopic traits (e.g., '菊花心, 豆腥气' or '鸡爪连, golden-yellow UV').",
        }

    q_low = query_blob.lower()
    matches: list[dict] = []

    for herb_name, spec in DECOCTION_PIECE_DB.items():
        matched_kws = [kw for kw in spec["keywords"] if kw.lower() in q_low]
        # Also match phrases inside macroscopic_features or mnemonic
        if (
            herb_name in query_blob
            or spec["english"].lower() in q_low
            or spec["pinyin"].lower() in q_low
        ) and herb_name not in matched_kws:
            matched_kws.append(herb_name)
        for feat_line in spec["macroscopic_features"]:
            for token in ("菊花心", "豆腥气", "芦碗", "珍珠点", "鸡爪", "过桥", "怀中抱月", "观音合掌", "铜皮铁骨", "狮子头", "狮子盘头", "云头鸡腿", "朱砂点", "茯神", "三瓣"):
                if token in feat_line and token in query_blob and token not in matched_kws:
                    matched_kws.append(token)

        if not matched_kws:
            continue

        conf = min(0.98, round(0.45 + 0.15 * len(matched_kws), 2))
        herb_profile = _search_herb(herb_name)
        tox_profile = toxicity_check(herb_name)

        matches.append({
            "herb": herb_name,
            "pinyin": spec["pinyin"],
            "latin": spec["latin"],
            "english": spec["english"],
            "confidence": conf,
            "matched_hallmarks": matched_kws,
            "hallmark_mnemonic": spec["hallmark_mnemonic"],
            "macroscopic_features": spec["macroscopic_features"],
            "processing_specifications": spec["processing_specs"],
            "adulterants_and_lookalikes": spec["adulterants_and_lookalikes"],
            "active_chemical_markers": spec["chemical_markers"],
            "safety_profile": tox_profile,
            "linked_herb_profile": herb_profile,
        })

    matches.sort(key=lambda m: m["confidence"], reverse=True)

    candidate_check = None
    if candidate_name.strip():
        cand = candidate_name.strip()
        confirmed = any(
            cand.lower() in (m["herb"].lower(), m["english"].lower(), m["pinyin"].lower())
            for m in matches
        )
        candidate_check = {
            "candidate_name": cand,
            "verified": confirmed,
            "assessment": (
                f"Macroscopic traits are consistent with {cand}."
                if confirmed
                else f"Provided traits do NOT strongly match {cand}; inspect top differential matches and adulterant notes."
            ),
        }

    if not matches:
        return {
            "status": "not_found",
            "message": f"No canonical decoction piece matched '{features}'.",
            "candidate_verification": candidate_check,
            "supported_specimens": list(DECOCTION_PIECE_DB.keys()),
        }

    return {
        "status": "found",
        "count": len(matches),
        "top_candidate": matches[0]["herb"],
        "top_match": matches[0],
        "candidates": matches[:5],
        "matches": matches[:5],
        "processing_paozhi": [
            f"{k}: {v}" for k, v in matches[0]["processing_specifications"].items()
        ],
        "candidate_verification": candidate_check,
        "biometric_interpretation": bio_interp,
    }


# ─── 3. Classical & Modern Prescription Parser (处方解析与古今衡制折算) ────────────

ERA_METROLOGY: dict[str, dict] = {
    "han": {
        "label": "东汉伤寒论衡制 (Eastern Han Shanghan Lun Archaeological Standard: 1两 ≈ 13.8g; conservative clinical 1两 ≈ 3.0g)",
        "units_g": {
            "斤": 220.8,
            "两": 13.8,
            "分": 3.45,     # 汉代 1两 = 4分
            "铢": 0.575,    # 汉代 1两 = 24铢
            "升": 40.0,     # 半夏/麦冬等饮片折算约40g/半升~90g/升均值
            "合": 4.0,
            "枚": 3.0,      # 大枣/栀子等均值约3g/枚
            "方寸匕": 2.0,
            "钱匕": 1.5,
            "尺": 15.0,
            "把": 12.0,
            "g": 1.0,
            "克": 1.0,
        },
        "conservative_liang_g": 3.0,
    },
    "ming_qing": {
        "label": "明清十六两库平制 (Ming-Qing 16-Liang Standard: 1两 = 31.2g, 1钱 = 3.12g, 1分 = 0.31g)",
        "units_g": {
            "斤": 500.0,
            "两": 31.2,
            "钱": 3.12,
            "分": 0.31,
            "厘": 0.031,
            "枚": 3.0,
            "g": 1.0,
            "克": 1.0,
        },
    },
    "modern": {
        "label": "现代中国药典与临床衡制 (Modern PRC Pharmacopoeia: g/克, 1钱 = 3.0g, 1两 = 30.0g)",
        "units_g": {
            "kg": 1000.0,
            "g": 1.0,
            "克": 1.0,
            "mg": 0.001,
            "毫克": 0.001,
            "两": 30.0,
            "钱": 3.0,
            "分": 0.3,
            "枚": 3.0,
            "片": 1.5,
        },
    },
}

_CN_DIGITS = {
    "零": 0, "〇": 0, "一": 1, "壹": 1, "二": 2, "贰": 2, "两": 2,
    "三": 3, "叁": 3, "四": 4, "肆": 4, "五": 5, "伍": 5,
    "六": 6, "陆": 6, "七": 7, "柒": 7, "八": 8, "捌": 8,
    "九": 9, "玖": 9,
}

PROCESSING_KEYWORDS = (
    "先煎", "后下", "包煎", "绵裹", "烊化", "冲服", "另煎", "另炖", "泡服",
    "麸炒", "土炒", "酒炒", "醋炒", "盐炙", "蜜炙", "姜炙",
    "去皮", "去节", "去心", "去核", "破八片", "炙", "炮", "切", "擘", "碎", "洗", "煅",
)

HERB_CANONICAL_ALIASES: dict[str, tuple[str, str]] = {
    "炙甘草": ("甘草", "蜜炙 (Honey-fried)"),
    "生甘草": ("甘草", "生用 (Raw)"),
    "炙黄芪": ("黄芪", "蜜炙 (Honey-fried)"),
    "生黄芪": ("黄芪", "生用 (Raw)"),
    "炙麻黄": ("麻黄", "蜜炙 (Honey-fried)"),
    "生麻黄": ("麻黄", "生用 (Raw)"),
    "制附子": ("附子", "炮制 (Processed — decoct first 先煎)"),
    "炮附子": ("附子", "炮制 (Processed — decoct first 先煎)"),
    "黑顺片": ("附子", "黑顺片 (Processed — decoct first 先煎)"),
    "白附片": ("附子", "白附片 (Processed — decoct first 先煎)"),
    "熟附子": ("附子", "炮制 (Processed — decoct first 先煎)"),
    "制半夏": ("半夏", "制用 (Processed)"),
    "法半夏": ("半夏", "法制 (Licorice-lime processed)"),
    "姜半夏": ("半夏", "姜矾制 (Ginger-processed)"),
    "清半夏": ("半夏", "白矾制 (Alum-processed)"),
    "生半夏": ("半夏", "生用【有毒】 (Raw — toxic!)"),
    "麸炒白术": ("白术", "麸炒 (Bran-fried)"),
    "炒白术": ("白术", "炒用 (Stir-fried)"),
    "生白术": ("白术", "生用 (Raw)"),
    "醋柴胡": ("柴胡", "醋炙 (Vinegar-fried)"),
    "酒当归": ("当归", "酒炙 (Wine-fried)"),
    "当归身": ("当归", "归身 (Main root)"),
    "当归尾": ("当归", "归尾 (Lateral root)"),
    "生石膏": ("石膏", "生用先煎 (Raw — decoct first)"),
    "生大黄": ("大黄", "生用后下 (Raw — add near end for purgation)"),
    "酒大黄": ("大黄", "酒制 (Wine-processed)"),
    "熟大黄": ("大黄", "熟制 (Steamed)"),
    "三七粉": ("三七", "研粉冲服 (Powder — infuse)"),
    "北沙参": ("沙参", ""),
    "南沙参": ("沙参", ""),
    "白芍": ("芍药", "白芍"),
    "赤芍": ("芍药", "赤芍"),
    "肥知母": ("知母", ""),
    "绵茵陈": ("茵陈", ""),
}

CLASSICAL_BASE_FORMULAS: dict[str, dict] = {
    "四君子汤": {"herbs": {"人参", "白术", "茯苓", "甘草"}, "source": "《太平惠民和剂局方》", "actions": "益气健脾"},
    "六君子汤": {"herbs": {"人参", "白术", "茯苓", "甘草", "陈皮", "半夏"}, "source": "《医学正传》", "actions": "益气健脾，燥湿化痰"},
    "桂枝汤": {"herbs": {"桂枝", "芍药", "甘草", "生姜", "大枣"}, "source": "《伤寒论》第12条", "actions": "解肌发表，调和营卫"},
    "麻黄汤": {"herbs": {"麻黄", "桂枝", "杏仁", "甘草"}, "source": "《伤寒论》第35条", "actions": "发汗解表，宣肺平喘"},
    "小柴胡汤": {"herbs": {"柴胡", "黄芩", "半夏", "人参", "甘草", "生姜", "大枣"}, "source": "《伤寒论》第96条", "actions": "和解少阳"},
    "四逆散": {"herbs": {"柴胡", "芍药", "枳实", "甘草"}, "source": "《伤寒论》第318条", "actions": "透邪解郁，疏肝理脾"},
    "四逆汤": {"herbs": {"附子", "干姜", "甘草"}, "source": "《伤寒论》第323条", "actions": "回阳救逆"},
    "理中汤": {"herbs": {"人参", "干姜", "白术", "甘草"}, "source": "《伤寒论》第386条", "actions": "温中祛寒，补气健脾"},
    "炙甘草汤": {"herbs": {"甘草", "生姜", "桂枝", "人参", "生地黄", "阿胶", "麦冬", "麻仁", "大枣"}, "source": "《伤寒论》第177条", "actions": "益气滋阴，通阳复脉"},
    "大黄黄连泻心汤": {"herbs": {"大黄", "黄连"}, "source": "《伤寒论》第154条", "actions": "泄热消痞"},
    "六味地黄丸": {"herbs": {"熟地黄", "山茱萸", "山药", "泽泻", "牡丹皮", "茯苓"}, "source": "《小儿药证直诀》", "actions": "滋补肝肾"},
    "肾气丸": {"herbs": {"干地黄", "山药", "山茱萸", "泽泻", "茯苓", "牡丹皮", "桂枝", "附子"}, "source": "《金匮要略》", "actions": "补肾助阳"},
    "补中益气汤": {"herbs": {"黄芪", "人参", "白术", "甘草", "当归", "陈皮", "升麻", "柴胡"}, "source": "《脾胃论》", "actions": "补中益气，升阳举陷"},
    "逍遥散": {"herbs": {"柴胡", "当归", "芍药", "白术", "茯苓", "甘草"}, "source": "《太平惠民和剂局方》", "actions": "疏肝健脾，养血调经"},
    "四物汤": {"herbs": {"当归", "川芎", "芍药", "熟地黄"}, "source": "《仙授理伤续断秘方》", "actions": "补血和血"},
    "桃红四物汤": {"herbs": {"当归", "川芎", "芍药", "熟地黄", "桃仁", "红花"}, "source": "《医宗金鉴》", "actions": "养血活血逐瘀"},
    "二陈汤": {"herbs": {"半夏", "陈皮", "茯苓", "甘草"}, "source": "《太平惠民和剂局方》", "actions": "燥湿化痰，理气和中"},
    "平胃散": {"herbs": {"苍术", "厚朴", "陈皮", "甘草"}, "source": "《太平惠民和剂局方》", "actions": "燥湿运脾，行气和胃"},
    "半夏厚朴汤": {"herbs": {"半夏", "厚朴", "茯苓", "生姜", "紫苏叶"}, "source": "《金匮要略》", "actions": "行气散结，降逆化痰"},
    "酸枣仁汤": {"herbs": {"酸枣仁", "甘草", "知母", "茯苓", "川芎"}, "source": "《金匮要略》", "actions": "养血安神，清热除烦"},
    "银翘散": {"herbs": {"金银花", "连翘", "桔梗", "薄荷", "淡竹叶", "甘草", "荆芥", "淡豆豉", "牛蒡子"}, "source": "《温病条辨》", "actions": "辛凉透表，清热解毒"},
}


def parse_chinese_number(num_str: str) -> float | None:
    """Convert Arabic or Chinese numeral string (including 半, 十, 百, 一两半 style) to float."""
    s = num_str.strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        pass

    if s == "半":
        return 0.5

    has_half = s.endswith("半") and len(s) > 1
    if has_half:
        s = s[:-1]

    total = 0.0
    current = 0
    for ch in s:
        if ch in _CN_DIGITS:
            current = _CN_DIGITS[ch]
        elif ch in ("十", "拾"):
            total += (current if current > 0 else 1) * 10
            current = 0
        elif ch in ("百", "佰"):
            total += (current if current > 0 else 1) * 100
            current = 0
        else:
            return None
    total += current
    if has_half:
        total += 0.5
    return total if total > 0 else None


_QTY_ONLY_RE = re.compile(
    r"^(\d+(?:\.\d+)?|[零〇一壹二贰两三叁四肆五伍六陆七柒八捌九玖十拾百佰半]+)\s*"
    r"(方寸匕|钱匕|毫克|kg|mg|g|克|斤|两|钱|分|厘|铢|升|合|枚|片|尺|把)(半)?([一-龥]*)$"
)

_PROC_ONLY_RE = re.compile(
    r"^[\(（]?(" + "|".join(PROCESSING_KEYWORDS) + r")[\)）]?$"
)

_ITEM_REGEX = re.compile(
    r"^(三七粉|三七|田七|[一-龥A-Za-z]{1,8}?)\s*"
    r"(?:[\(（]([^\)）]*)[\)）]\s*)?"
    r"(\d+(?:\.\d+)?|[零〇一壹二贰两三叁四肆五伍六陆七柒八捌九玖十拾百佰半]+)\s*"
    r"(方寸匕|钱匕|毫克|kg|mg|g|克|斤|两|钱|分|厘|铢|升|合|枚|片|尺|把)"
    r"(半)?\s*"
    r"(?:[\(（]([^\)）]*)[\)）]|([一-龥，、\s]*))?$"
)


def _normalize_herb_and_notes(raw_herb: str, extra_notes: list[str]) -> tuple[str, list[str]]:
    """Resolve canonical herb name and collect processing/decoction notes."""
    notes = [n.strip() for n in extra_notes if n and n.strip()]
    clean = raw_herb.strip()

    if clean in HERB_CANONICAL_ALIASES:
        canon, proc = HERB_CANONICAL_ALIASES[clean]
        if proc:
            notes.insert(0, proc)
        return canon, notes

    if len(clean) >= 3 and clean[0] in ("炙", "炒", "煅", "炮"):
        notes.insert(0, f"{clean[0]}制")
        return clean[1:], notes

    return clean, notes


def _parse_single_token(token: str, era_cfg: dict, era_key: str) -> dict | None:
    """Parse one herb-dosage clause from modern or classical prescription text."""
    tok = token.strip().strip("。；;，,、:")
    if not tok:
        return None

    m = _ITEM_REGEX.match(tok)
    if not m:
        return None

    raw_herb, pre_paren, qty_raw, unit, trailing_half, post_paren, suffix_txt = m.groups()
    qty = parse_chinese_number(qty_raw)
    if qty is None:
        return None
    if trailing_half:
        qty += 0.5

    units_map = era_cfg["units_g"]
    unit_factor = units_map.get(unit, 1.0)
    metric_g = round(qty * unit_factor, 2)

    raw_notes = []
    for chunk in (pre_paren, post_paren, suffix_txt):
        if chunk:
            matched_procs = [pk for pk in PROCESSING_KEYWORDS if pk in chunk]
            raw_notes.extend(matched_procs if matched_procs else [chunk.strip()])

    canonical_herb, notes = _normalize_herb_and_notes(raw_herb, raw_notes)

    orig_dose_str = f"{qty_raw}{unit}{'半' if trailing_half else ''}"
    entry: dict = {
        "raw_text": tok,
        "raw_herb": raw_herb,
        "herb": canonical_herb,
        "original_dose": orig_dose_str,
        "original_amount": orig_dose_str,
        "quantity": qty,
        "unit": unit,
        "metric_g": metric_g,
        "metric_grams": metric_g,
        "processing_notes": notes,
    }
    if era_key == "han" and unit in ("两", "斤"):
        cons_factor = era_cfg["conservative_liang_g"] * (16 if unit == "斤" else 1)
        cons_g = round(qty * cons_factor, 2)
        entry["clinical_conservative_g"] = cons_g
        entry["conservative_clinical_grams"] = cons_g
    return entry


def _match_classical_formulas(herb_set: set[str]) -> list[dict]:
    """Identify classical base formulas present (exact or modified) in extracted herb set."""
    if not herb_set:
        return []
    expanded = set(herb_set)
    if "白芍" in expanded or "赤芍" in expanded:
        expanded.add("芍药")
    if "生地黄" in expanded or "熟地黄" in expanded:
        expanded.add("干地黄")

    matches: list[dict] = []
    for fname, fdata in CLASSICAL_BASE_FORMULAS.items():
        base_herbs = fdata["herbs"]
        overlap = base_herbs & expanded
        coverage = len(overlap) / len(base_herbs)
        if coverage < 0.60 or len(overlap) < 2:
            continue
        added = sorted(herb_set - base_herbs - {"白芍", "赤芍"})
        omitted = sorted(base_herbs - expanded)
        match_type = (
            "exact_base_formula"
            if coverage == 1.0 and not added
            else ("modified_addition (加味)" if coverage == 1.0 else "partial_or_modified (化裁加减)")
        )
        matches.append({
            "formula": fname,
            "source": fdata["source"],
            "actions": fdata["actions"],
            "coverage_ratio": round(coverage, 2),
            "match_type": match_type,
            "matched_herbs": sorted(overlap),
            "added_herbs": added,
            "omitted_herbs": omitted,
            "in_local_formula_db": fname in FORMULA_DB,
        })

    matches.sort(key=lambda x: (x["coverage_ratio"], len(x["matched_herbs"])), reverse=True)
    return matches[:5]


_UNSPACED_BOUNDARY_RE = re.compile(
    r"((?:\d+(?:\.\d+)?|[零〇一壹二贰三叁四肆五伍六陆七柒八捌九玖十拾百佰半]+)"
    r"(?:方寸匕|钱匕|毫克|kg|mg|g|克|斤|两|钱|分|厘|铢|升|合|枚|片)(?:半)?"
    r"(?:[\(（][^\)）]*[\)）]|先煎|后下|包煎|绵裹|烊化|冲服|去皮|去节|炙|切|擘|碎|炮)?)"
    r"(?=[一-龥]{1,5}(?:\d|[一二三四五六七八九十半]))"
)


def _tokenize_prescription(text: str) -> list[str]:
    """Split prescription text into individual herb+dose segments across formats."""
    normalized = _UNSPACED_BOUNDARY_RE.sub(r"\1, ", text.strip())
    raw_chunks = re.split(r"[,，;；。\n\r\t]+|\s+", normalized)
    merged: list[str] = []
    for chunk in raw_chunks:
        c = chunk.strip()
        if not c:
            continue
        if merged and (
            (_QTY_ONLY_RE.match(c) and not _ITEM_REGEX.match(merged[-1]))
            or _PROC_ONLY_RE.match(c)
        ):
            merged[-1] = f"{merged[-1]} {c}"
        elif (
            merged
            and c in ("g", "克", "mg", "kg", "两", "钱", "分", "枚", "升")
            and re.search(r"(\d|[零〇一二三四五六七八九十半])$", merged[-1])
        ):
            merged[-1] = f"{merged[-1]}{c}"
        else:
            merged.append(c)
    return merged


@registry.register(
    name="diagnostics.prescription_parse",
    description=(
        "Parse modern clinical prescriptions or classical TCM prescriptions (e.g., Shanghan Lun / "
        "Ming-Qing texts or OCR output). Converts historical weights (斤/两/钱/分/铢/枚) to metric grams, "
        "extracts processing notes (炙/先煎/后下/包煎/烊化/冲服), runs 十八反/十九畏, toxicity, and "
        "pregnancy safety checks, and identifies matching classical base formulas."
    ),
    category="diagnostics",
    parameters={
        "text": "Prescription string (e.g., '桂枝三两 芍药三两 甘草二两炙 生姜三两切 大枣十二枚擘' or '人参 9g, 白术 12g, 茯苓 12g, 炙甘草 6g')",
        "era": "Metrology standard: 'modern' (default), 'han' (Eastern Han 1两=13.8g & 3g conservative), or 'ming_qing' (1两=31.2g, 1钱=3.12g)",
    },
    usage_guide="When parsing herbal prescriptions, OCR prescription text, or converting classical dosages.",
)
def prescription_parse(text: str, era: str = "modern") -> dict:
    """Parse herbal prescription, convert metrology, check safety, and match base formulas."""
    era_key = era.lower().strip()
    if era_key == "eastern_han":
        era_key = "han"
    if era_key not in ERA_METROLOGY:
        return {
            "status": "error",
            "message": f"Unsupported era '{era}'. Choose from: {list(ERA_METROLOGY.keys())}.",
        }

    era_cfg = ERA_METROLOGY[era_key]
    merged_tokens = _tokenize_prescription(text)

    items: list[dict] = []
    unparsed: list[str] = []
    for tok in merged_tokens:
        parsed = _parse_single_token(tok, era_cfg, era_key)
        if parsed:
            items.append(parsed)
        else:
            unparsed.append(tok)

    if not items:
        return {
            "status": "not_found",
            "message": "Could not extract herb-dosage items from input text.",
            "unparsed_segments": unparsed,
        }

    # Build herb list for interactions + pregnancy + toxicity checks
    herb_names_for_safety: list[str] = []
    toxic_alerts: list[dict] = []
    for it in items:
        h = it["herb"]
        if h not in herb_names_for_safety:
            herb_names_for_safety.append(h)
        # Map 附子/川乌/草乌 to 乌头 as well so interactions.check_herbs catches 乌头反半夏/瓜蒌/贝母!
        if h in ("附子", "川乌", "草乌") and "乌头" not in herb_names_for_safety:
            herb_names_for_safety.append("乌头")
        tox = toxicity_check(h)
        if tox.get("status") == "toxic":
            toxic_alerts.append(tox)

    herb_csv = ", ".join(herb_names_for_safety)
    interaction_report = check_herbs(herb_csv)
    # Remove synthetic '乌头' from safe list in pregnancy report if added only for 十八反
    preg_csv = ", ".join(dict.fromkeys(it["herb"] for it in items))
    pregnancy_report = pregnancy_check(preg_csv)

    total_g = round(sum(it["metric_g"] for it in items), 2)
    formula_matches = _match_classical_formulas({it["herb"] for it in items})

    summary: dict = {
        "status": "complete",
        "era": era_key,
        "metrology_standard": era_cfg["label"],
        "herb_count": len(items),
        "total_herbs": len(items),
        "total_metric_weight_g": total_g,
        "items": items,
        "herbs": items,
        "classical_formula_matches": formula_matches,
        "safety_audit": {
            "herb_interactions": interaction_report,
            "toxicity_alerts": toxic_alerts,
            "pregnancy_safety": pregnancy_report,
        },
    }
    if era_key == "han":
        summary["total_clinical_conservative_g"] = round(
            sum(it.get("clinical_conservative_g", it["metric_g"]) for it in items), 2
        )
    if unparsed:
        summary["unparsed_notes"] = unparsed
    return summary


# ─── 4. Four Examinations & 28 Classical Pulses (四诊合参与二十八脉库) ──────────────

TWENTY_EIGHT_PULSES: dict[str, dict] = {
    "浮": {
        "pinyin": "Fú", "english": "Floating",
        "classic_feel": "举之有余，按之不足 (Distinct on light touch, weakens on heavy pressure)",
        "hemodynamic_correlate": "Peripheral vasodilation & superficial arterial filling during acute immune/febrile response",
        "indications": "表证（浮紧风寒、浮数风热），亦见虚阳浮越（浮大无根）",
        "eight_principles": {"exterior": 3, "yang": 1},
    },
    "沉": {
        "pinyin": "Chén", "english": "Deep",
        "classic_feel": "轻取不应，重按始得 (Imperceptible superficially, felt near bone on heavy pressure)",
        "hemodynamic_correlate": "Increased peripheral vascular resistance or reduced stroke volume",
        "indications": "里证（沉实有力为里实，沉弱无力为里虚）",
        "eight_principles": {"interior": 3, "yin": 1},
    },
    "迟": {
        "pinyin": "Chí", "english": "Slow",
        "classic_feel": "一息不足四至 (<4 beats/breath, <60 bpm)",
        "hemodynamic_correlate": "Heightened vagal parasympathetic tone / sinus bradycardia",
        "indications": "寒证（迟而有力为冷积实寒，迟而无力为虚寒阳衰）",
        "eight_principles": {"cold": 3, "yin": 2},
    },
    "数": {
        "pinyin": "Shuò", "english": "Rapid",
        "classic_feel": "一息五至以上 (5-6 beats/breath, 90-120 bpm)",
        "hemodynamic_correlate": "Sympathetic activation / sinus tachycardia / hypermetabolic state",
        "indications": "热证（洪数为实热，细数为阴虚内热；亦见气血虚极躁动）",
        "eight_principles": {"heat": 3, "yang": 2},
    },
    "滑": {
        "pinyin": "Huá", "english": "Slippery",
        "classic_feel": "往来流利，应指圆滑，如盘走珠 (Rolling smoothly like pearls on a jade plate)",
        "hemodynamic_correlate": "High arterial compliance, rapid systolic upstroke, dicrotic wave prominence",
        "indications": "痰饮、食积、实热，以及青壮年平脉或妇人妊娠喜脉",
        "eight_principles": {"excess": 2, "heat": 1},
    },
    "涩": {
        "pinyin": "Sè", "english": "Choppy",
        "classic_feel": "形细而行迟，往来艰涩不畅，如轻刀刮竹 (Hesitant and rough like scraping bamboo)",
        "hemodynamic_correlate": "Elevated blood viscosity, impaired microvascular perfusion, or slow systolic rise",
        "indications": "气滞血瘀（涩而有力）、精伤血少津亏（涩而无力）",
        "eight_principles": {"interior": 2, "deficiency": 1, "excess": 1},
    },
    "弦": {
        "pinyin": "Xián", "english": "Wiry",
        "classic_feel": "端直以长，如按琴弦 (Taut, straight, and long like pressing a zither string)",
        "hemodynamic_correlate": "Increased arterial wall stiffness, smooth muscle spasm, or elevated blood pressure",
        "indications": "肝胆病、诸痛证、痰饮、疟疾",
        "eight_principles": {"interior": 2, "excess": 2},
    },
    "紧": {
        "pinyin": "Jǐn", "english": "Tight",
        "classic_feel": "绷急弹指，状如转索 (Tense, vibrating like a twisted rope)",
        "hemodynamic_correlate": "Intense cold-induced or pain-driven alpha-adrenergic vasoconstriction",
        "indications": "实寒证（表寒浮紧、里寒沉紧）、剧痛、宿食",
        "eight_principles": {"cold": 3, "excess": 3},
    },
    "细": {
        "pinyin": "Xì", "english": "Thready",
        "classic_feel": "脉细如线，但应指明显 (Fine as a silk thread yet distinct)",
        "hemodynamic_correlate": "Reduced stroke volume / mild hypovolemia with intact vascular tone",
        "indications": "气血两虚、阴精亏损、湿邪阻压脉道",
        "eight_principles": {"interior": 2, "deficiency": 3, "yin": 1},
    },
    "洪": {
        "pinyin": "Hóng", "english": "Surging",
        "classic_feel": "脉体阔大，充实有力，来盛去衰，状若波涛汹涌 (Arrives like surging waves, recedes slackly)",
        "hemodynamic_correlate": "Wide pulse pressure, high cardiac output + marked peripheral vasodilation",
        "indications": "阳明气分热盛、壮热烦渴",
        "eight_principles": {"heat": 4, "excess": 3, "yang": 3},
    },
    "微": {
        "pinyin": "Wēi", "english": "Faint",
        "classic_feel": "极细极软，按之欲绝，若有若无 (Extremely fine and soft, barely perceptible)",
        "hemodynamic_correlate": "Severe hypotension, low cardiac output, impending circulatory shock",
        "indications": "阴阳气血诸虚，尤主阳气衰微欲脱（少阴亡阳）",
        "eight_principles": {"interior": 3, "cold": 2, "deficiency": 4, "yin": 3},
    },
    "濡": {
        "pinyin": "Rú", "english": "Soggy",
        "classic_feel": "浮而细软，如帛在水中 (Superficial, thin, and soft like silk floating on water)",
        "hemodynamic_correlate": "Low arterial tension accompanied by interstitial fluid retention",
        "indications": "诸虚（气血虚）、湿困脾胃",
        "eight_principles": {"deficiency": 2, "interior": 1},
    },
    "弱": {
        "pinyin": "Ruò", "english": "Weak",
        "classic_feel": "沉而细软，轻取不显 (Deep, fine, and soft)",
        "hemodynamic_correlate": "Diminished cardiac output and low peripheral vascular tone",
        "indications": "阳气虚衰、气血俱虚",
        "eight_principles": {"interior": 3, "deficiency": 3, "cold": 1, "yin": 2},
    },
    "缓": {
        "pinyin": "Huǎn", "english": "Moderate",
        "classic_feel": "一息四至，来去怠缓 (4 beats/breath, relaxed or slack)",
        "hemodynamic_correlate": "Balanced autonomic vagal-sympathetic tone or mild smooth-muscle hypotonia",
        "indications": "湿病、脾胃虚弱；若从容和缓有力则为有胃气之平脉",
        "eight_principles": {"deficiency": 1},
    },
    "促": {
        "pinyin": "Cù", "english": "Abrupt",
        "classic_feel": "脉来急数而时一止，止无定数 (Rapid with irregular missed beats)",
        "hemodynamic_correlate": "Tachycardia with premature ectopic contractions or rapid atrial fibrillation",
        "indications": "阳盛实热、气血痰饮宿食郁滞，亦见脏气乖违心阳虚衰",
        "eight_principles": {"heat": 3, "excess": 2, "yang": 2},
    },
    "结": {
        "pinyin": "Jié", "english": "Knotted",
        "classic_feel": "脉来缓而时一止，止无定数 (Slow/moderate with irregular missed beats)",
        "hemodynamic_correlate": "Premature beats or sinus pause under high vagal tone / myocardial ischemia",
        "indications": "阴盛气结、寒痰血瘀、癥瘕积聚",
        "eight_principles": {"cold": 2, "excess": 2, "yin": 2},
    },
    "代": {
        "pinyin": "Dài", "english": "Intermittent",
        "classic_feel": "脉来一止，止有定数，良久方还 (Regularly recurring missed beats at fixed intervals)",
        "hemodynamic_correlate": "Second-degree AV conduction block or ventricular bigeminy/trigeminy",
        "indications": "脏气衰微（心气心阳亏损）、跌打重创、惊恐痛极",
        "eight_principles": {"interior": 3, "deficiency": 4, "yin": 2},
    },
    "芤": {
        "pinyin": "Kōu", "english": "Hollow",
        "classic_feel": "浮大中空，如按葱管 (Superficial, large, with hollow center like a scallion stalk)",
        "hemodynamic_correlate": "Acute hypovolemia/hemorrhage with low diastolic pressure and reflex vasodilation",
        "indications": "大失血、伤阴亡津之际",
        "eight_principles": {"deficiency": 4},
    },
    "革": {
        "pinyin": "Gé", "english": "Tympanic",
        "classic_feel": "浮而搏指，中空外坚，如按鼓皮 (Hard taut exterior with empty center like a drumskin)",
        "hemodynamic_correlate": "Arteriosclerotic vessel wall rigidity combined with severe anemia/hypovolemia",
        "indications": "亡血、失精、半产、崩漏（精血虚寒）",
        "eight_principles": {"deficiency": 4, "cold": 2},
    },
    "牢": {
        "pinyin": "Láo", "english": "Firm",
        "classic_feel": "沉按实大弦长，坚牢不移 (Deep, replete, large, wiry, and long)",
        "hemodynamic_correlate": "Sustained severe hypertension and deep arterial stiffness",
        "indications": "阴寒内实、疝气、癥瘕积聚",
        "eight_principles": {"interior": 3, "cold": 2, "excess": 4},
    },
    "伏": {
        "pinyin": "Fú (Hidden)", "english": "Hidden",
        "classic_feel": "重按推筋着骨始得 (Buried deep against bone, requiring heavy pressure)",
        "hemodynamic_correlate": "Profound vasoconstriction during syncope, severe pain, or shock",
        "indications": "邪闭、厥证、痛极、阳衰",
        "eight_principles": {"interior": 4, "excess": 2},
    },
    "动": {
        "pinyin": "Dòng", "english": "Moving",
        "classic_feel": "脉形如豆，厥厥动摇，滑数有力 (Short, slippery, rapid, throbbing like a spinning bean at Guan)",
        "hemodynamic_correlate": "Acute sympathetic catecholamine surge elevating heart rate and contractility",
        "indications": "痛证、惊恐（阴阳相搏）",
        "eight_principles": {"excess": 2, "yang": 2},
    },
    "散": {
        "pinyin": "Sàn", "english": "Scattered",
        "classic_feel": "浮散无根，至数不齐，按之消失 (Diffuse, irregular, rootless, vanishes on pressure)",
        "hemodynamic_correlate": "Decompensated heart failure / terminal arrhythmia",
        "indications": "元气离散，脏腑精气将绝危候",
        "eight_principles": {"deficiency": 5},
    },
    "实": {
        "pinyin": "Shí", "english": "Replete",
        "classic_feel": "三部脉举按皆充实有力 (Forceful and full across all depths and positions)",
        "hemodynamic_correlate": "High stroke volume with robust arterial pressure",
        "indications": "实证（邪气亢盛而正气未虚）",
        "eight_principles": {"excess": 4, "yang": 2},
    },
    "虚": {
        "pinyin": "Xū", "english": "Vacuous",
        "classic_feel": "三部脉举之无力，按之空豁 (Forceless and empty across all depths)",
        "hemodynamic_correlate": "Low cardiac output and diminished vascular tone",
        "indications": "虚证（气血两虚，尤以气虚为主）",
        "eight_principles": {"deficiency": 4, "yin": 1},
    },
    "长": {
        "pinyin": "Cháng", "english": "Long",
        "classic_feel": "首尾端直，超过本位 (Extends straight beyond Cun and Chi positions)",
        "hemodynamic_correlate": "Strong arterial pulse wave propagation (healthy elasticity if gentle; hypertension if wiry)",
        "indications": "阳气有余、阳盛内热（长而和缓为气血充盛平脉）",
        "eight_principles": {"excess": 2, "yang": 2},
    },
    "短": {
        "pinyin": "Duǎn", "english": "Short",
        "classic_feel": "首尾俱短，不及本位 (Fails to fill Cun and Chi positions, felt mainly at Guan)",
        "hemodynamic_correlate": "Impaired stroke volume or obstructed peripheral pulse wave transmission",
        "indications": "短而有力为气郁血瘀，短而无力为心肺气损",
        "eight_principles": {"deficiency": 2},
    },
    "疾": {
        "pinyin": "Jí", "english": "Racing",
        "classic_feel": "脉来急疾，一息七八至 (>140 bpm)",
        "hemodynamic_correlate": "Supraventricular tachycardia or extreme febrile hypermetabolism",
        "indications": "阳极阴竭，元气欲脱，或热极急证",
        "eight_principles": {"heat": 4, "deficiency": 3, "yang": 3},
    },
}

FOUR_EXAM_SYNDROMES: list[dict] = [
    {
        "syndrome": "脾气虚证 (Spleen Qi Deficiency)",
        "eight_principles": "里虚寒/平证 (Interior Deficiency)",
        "modality_clues": {
            "inspection": ["面色萎黄", "淡白", "齿痕", "胖大", "少神", "sallow", "pale", "scalloped"],
            "auscultation": ["少气懒言", "语声低微", "气短", "low voice", "weak voice", "shortness of breath"],
            "inquiry": ["食少", "纳呆", "腹胀", "便溏", "乏力", "倦怠", "poor appetite", "loose stool", "fatigue", "bloating"],
            "pulse": ["缓", "弱", "虚", "细", "濡", "weak", "moderate", "thready", "soggy"],
        },
        "treatment_principle": "健脾益气，助运化湿 (Fortify Spleen, augment Qi, aid transformation)",
        "formulas": ["四君子汤", "参苓白术散", "补中益气汤"],
        "modifications": "兼腹胀气滞加陈皮、木香（香砂六君子汤）；久泻中气下陷重用炙黄芪配升麻、柴胡。",
        "acupoints": ["ST36 (足三里)", "SP6 (三阴交)", "BL20 (脾俞)", "CV12 (中脘)", "CV6 (气海)"],
        "lifestyle": "忌生冷寒凉及油腻甜食；宜山药、薏苡仁、莲子、大枣温热粥饮，劳逸结合避免思虑伤脾。",
    },
    {
        "syndrome": "脾肾阳虚证 (Spleen & Kidney Yang Deficiency)",
        "eight_principles": "里虚寒证 (Interior Deficiency Cold)",
        "modality_clues": {
            "inspection": ["面色晄白", "畏寒蜷卧", "淡白胖", "白滑", "浮肿", "pale swollen", "edema", "wet white"],
            "auscultation": ["气息微弱", "肠鸣", "low breath", "borborygmi"],
            "inquiry": ["畏寒肢冷", "五更泄泻", "腰膝冷痛", "夜尿频多", "完谷不化", "cold limbs", "chill", "dawn diarrhea", "nocturia"],
            "pulse": ["沉", "迟", "微", "弱", "deep", "slow", "faint", "weak"],
        },
        "treatment_principle": "温补脾肾，化气行水，涩肠止泻 (Warm Spleen & Kidney Yang, transform Qi & water)",
        "formulas": ["附子理中汤", "真武汤", "四神丸", "金匮肾气丸"],
        "modifications": "水肿明显加茯苓皮、泽泻、车前子；五更泻加补骨脂、肉豆蔻、吴茱萸。",
        "acupoints": ["CV4 (关元 - 艾灸)", "BL23 (肾俞)", "BL20 (脾俞)", "ST36 (足三里)", "KI3 (太溪)"],
        "lifestyle": "注意腰腹及足底保暖（睡前温水泡脚按涌泉），宜食生姜、羊肉、核桃、芡实，忌生冷瓜果冷饮。",
    },
    {
        "syndrome": "肝郁气滞 / 肝郁脾虚证 (Liver Qi Stagnation Invading Spleen)",
        "eight_principles": "里实/虚实夹杂证 (Interior Qi Stagnation with Spleen Deficiency)",
        "modality_clues": {
            "inspection": ["忧郁", "舌边红", "薄白", "郁闷", "depressed", "red edges"],
            "auscultation": ["善太息", "叹气", "嗳气", "sighing", "sigh", "belching"],
            "inquiry": ["胸胁胀痛", "情志抑郁", "急躁", "乳房胀痛", "月经不调", "腹痛即泻", "梅核气", "hypochondriac", "stress", "irritable", "pms", "lump in throat"],
            "pulse": ["弦", "弦细", "弦缓", "wiry"],
        },
        "treatment_principle": "疏肝解郁，理气健脾养血 (Course Liver Qi, resolve depression, fortify Spleen)",
        "formulas": ["逍遥散", "柴胡疏肝散", "四逆散", "痛泻要方"],
        "modifications": "郁久化火见口苦目赤加牡丹皮、栀子（丹栀逍遥散）；咽中如有炙脔合半夏厚朴汤。",
        "acupoints": ["LR3 (太冲)", "LI4 (合谷 - 四关穴)", "PC6 (内关)", "GB34 (阳陵泉)", "ST36 (足三里)"],
        "lifestyle": "调畅情志，规律户外疏导运动（八段锦/散步），可饮玫瑰花陈皮佛手茶，忌郁怒熬夜。",
    },
    {
        "syndrome": "肝肾阴虚火旺证 (Liver-Kidney Yin Deficiency with Empty Fire)",
        "eight_principles": "里虚热证 (Interior Yin Deficiency with Empty Heat)",
        "modality_clues": {
            "inspection": ["颧红", "红绛", "少苔", "剥苔", "裂纹", "消瘦", "malar flush", "crimson", "scanty", "peeled", "fissured"],
            "auscultation": ["干咳少痰", "声音嘶哑", "dry cough", "hoarse"],
            "inquiry": ["腰膝酸软", "五心烦热", "盗汗", "潮热", "头晕耳鸣", "口干咽燥", "失眠多梦", "night sweat", "tinnitus", "dizziness", "hot flashes", "insomnia", "dry throat"],
            "pulse": ["细", "数", "细数", "thready", "rapid"],
        },
        "treatment_principle": "滋补肝肾，育阴潜阳，清降虚火 (Nourish Liver-Kidney Yin, clear empty fire)",
        "formulas": ["六味地黄丸", "知柏地黄丸", "杞菊地黄丸", "一贯煎"],
        "modifications": "虚火旺盛骨蒸潮热加知母、黄柏、地骨皮；失眠心烦合酸枣仁汤或天王补心丹；目干视物昏花加枸杞子、菊花。",
        "acupoints": ["KI3 (太溪)", "SP6 (三阴交)", "BL23 (肾俞)", "HT7 (神门)", "LR3 (太冲)"],
        "lifestyle": "亥时（21-23点）前安睡养阴，忌辛辣煎炸烟酒咖啡，宜食黑芝麻、桑椹、枸杞、百合、银耳。",
    },
    {
        "syndrome": "脾胃湿热 / 肝胆湿热证 (Damp-Heat in Middle Jiao or Liver-Gallbladder)",
        "eight_principles": "里实热证 (Interior Excess Damp-Heat)",
        "modality_clues": {
            "inspection": ["面垢油光", "身目发黄", "红舌", "黄腻", "yellow greasy", "red tongue", "oily face", "jaundice"],
            "auscultation": ["口气臭秽", "大便腥臭", "halitosis", "foul breath"],
            "inquiry": ["口苦口粘", "脘腹痞满", "恶心厌油", "大便粘滞", "小便短赤", "身重困倦", "阴囊潮湿", "bitter taste", "sticky mouth", "scant dark urine", "heavy body", "sticky stool"],
            "pulse": ["滑", "数", "濡", "弦数", "slippery", "rapid", "soggy"],
        },
        "treatment_principle": "清热化湿，理气和胃 / 清利肝胆 (Clear heat, drain dampness, harmonize middle or gallbladder)",
        "formulas": ["连朴饮", "三仁汤", "龙胆泻肝汤", "茵陈蒿汤"],
        "modifications": "湿重于热用三仁汤宣畅三焦；热重于湿或伴黄疸合茵陈蒿汤；痰热心烦失眠用黄连温胆汤。",
        "acupoints": ["SP9 (阴陵泉)", "LI11 (曲池)", "ST40 (丰隆)", "GB34 (阳陵泉)", "CV12 (中脘)"],
        "lifestyle": "严格戒酒、肥甘厚味、烧烤辛辣及甜腻奶茶；宜食赤小豆、薏苡仁、冬瓜、绿豆清淡饮食。",
    },
    {
        "syndrome": "气滞血瘀证 (Qi Stagnation & Blood Stasis)",
        "eight_principles": "里实证 (Interior Blood Stasis)",
        "modality_clues": {
            "inspection": ["面色晦暗", "唇甲青紫", "青紫", "瘀点", "瘀斑", "舌下络脉迂曲", "cyanotic", "purple", "petechiae", "engorged"],
            "auscultation": ["太息", "痛吟"],
            "inquiry": ["刺痛", "痛有定处", "夜间痛甚", "拒按", "血块", "痛经", "胸痛", "stabbing pain", "fixed pain", "worse at night", "clots", "dysmenorrhea"],
            "pulse": ["涩", "弦", "结", "choppy", "wiry", "knotted"],
        },
        "treatment_principle": "活血化瘀，行气止痛 (Invigorate Blood, dispel stasis, move Qi to stop pain)",
        "formulas": ["血府逐瘀汤", "桃红四物汤", "膈下逐瘀汤", "少腹逐瘀汤"],
        "modifications": "气虚血瘀半身不遂改用补阳还五汤重用生黄芪；寒凝血瘀痛经加肉桂、小茴香、吴茱萸。",
        "acupoints": ["SP6 (三阴交)", "LI4 (合谷)", "LR3 (太冲)", "BL17/BL40 (委中)", "PC6 (内关)"],
        "lifestyle": "保持气血温通，避免久坐不动及寒凉刺激，孕妇慎用活血峻品。",
    },
    {
        "syndrome": "风寒束表证 (Exterior Wind-Cold)",
        "eight_principles": "表实寒证 (Exterior Excess Cold)",
        "modality_clues": {
            "inspection": ["薄白", "清涕", "thin white", "clear nasal"],
            "auscultation": ["喷嚏", "咳嗽声重", "鼻塞声重", "sneezing", "nasal voice"],
            "inquiry": ["恶寒重发热轻", "无汗", "头项强痛", "肢体酸痛", "口不渴", "severe chills", "no sweat", "body ache", "headache", "stiff neck"],
            "pulse": ["浮", "紧", "浮紧", "floating", "tight"],
        },
        "treatment_principle": "辛温解表，宣肺散寒 (Release exterior with acrid-warm herbs, diffuse Lung Qi)",
        "formulas": ["麻黄汤", "桂枝汤", "荆防败毒散", "葛根汤"],
        "modifications": "表虚有汗恶风用桂枝汤调和营卫；项背强几几加葛根（葛根汤）；内兼寒饮喘咳用小青龙汤。",
        "acupoints": ["LU7 (列缺)", "LI4 (合谷)", "GB20 (风池)", "BL13 (肺俞)", "TE5 (外关)"],
        "lifestyle": "温覆取微似汗（不可大汗淋漓亡阳），啜热稀粥助药力，避风寒、忌生冷酸涩敛邪。",
    },
    {
        "syndrome": "风热犯肺 / 卫分温病证 (Exterior Wind-Heat)",
        "eight_principles": "表实热证 (Exterior Heat)",
        "modality_clues": {
            "inspection": ["咽红肿", "舌尖边红", "薄黄", "黄痰", "red throat", "red tip", "yellow phlegm"],
            "auscultation": ["咳嗽气粗", "声嘶", "loud cough"],
            "inquiry": ["发热重恶寒轻", "咽喉肿痛", "口微渴", "有汗", "sore throat", "high fever", "mild chills", "thirst"],
            "pulse": ["浮", "数", "浮数", "floating", "rapid"],
        },
        "treatment_principle": "辛凉透表，清热宣肺利咽 (Release exterior with acrid-cool herbs, clear Lung heat)",
        "formulas": ["银翘散", "桑菊饮"],
        "modifications": "咽痛甚加玄参、马勃、板蓝根；咳甚痰黄加瓜蒌皮、浙贝母、黄芩。",
        "acupoints": ["LI4 (合谷)", "LI11 (曲池)", "LU7 (列缺)", "TE5 (外关)", "GV14/GB20 (风池)"],
        "lifestyle": "多饮温开水或芦根菊花桑叶饮，室内通风保湿，忌辛辣温补发物。",
    },
    {
        "syndrome": "少阳枢机不利证 (Shaoyang Half-Exterior Half-Interior)",
        "eight_principles": "半表半里热郁证 (Shaoyang Pivot Disharmony)",
        "modality_clues": {
            "inspection": ["薄白或薄黄", "默默"],
            "auscultation": ["喜呕", "嗳气"],
            "inquiry": ["往来寒热", "胸胁苦满", "口苦", "咽干", "目眩", "不欲饮食", "心烦喜呕", "alternating chills and fever", "bitter taste", "dry throat", "dizziness"],
            "pulse": ["弦", "弦细", "wiry"],
        },
        "treatment_principle": "和解少阳，枢转气机 (Harmonize and release Shaoyang pivot)",
        "formulas": ["小柴胡汤", "大柴胡汤", "柴胡桂枝汤"],
        "modifications": "兼阳明大便秘结腹满痛改用大柴胡汤；兼太阳表证未解用柴胡桂枝汤。",
        "acupoints": ["TE5 (外关)", "GB34 (阳陵泉)", "GB20 (风池)", "PC6 (内关)"],
        "lifestyle": "饮食清淡易消化，保持情绪平和，慎勿妄用汗吐下三法伤正。",
    },
    {
        "syndrome": "痰湿阻滞证 (Phlegm-Dampness Obstruction)",
        "eight_principles": "里实夹虚证 (Interior Phlegm-Dampness)",
        "modality_clues": {
            "inspection": ["形体肥胖", "白厚腻", "白腻", "痰多", "thick white", "greasy white", "overweight"],
            "auscultation": ["喉中痰鸣", "咳吐白痰", "phlegm rattle", "copious sputum"],
            "inquiry": ["胸脘痞闷", "头重如裹", "眩晕", "嗜睡", "呕恶痰涎", "口淡不渴", "heavy head", "chest oppression", "drowsy", "phlegm"],
            "pulse": ["滑", "缓", "濡", "弦滑", "slippery", "soggy"],
        },
        "treatment_principle": "燥湿化痰，理气和中 (Dry dampness, transform phlegm, regulate middle Qi)",
        "formulas": ["二陈汤", "半夏白术天麻汤", "温胆汤", "平胃散"],
        "modifications": "风痰眩晕头痛合半夏白术天麻汤；痰热惊悸失眠用温胆汤加黄连。",
        "acupoints": ["ST40 (丰隆)", "SP9 (阴陵泉)", "CV12 (中脘)", "PC6 (内关)", "ST36 (足三里)"],
        "lifestyle": "控制甜食冷饮与乳制品摄入，坚持有氧发汗运动助阳化饮，宜陈皮普洱茶。",
    },
]


def _analyze_pulse_text(pulse_str: str) -> tuple[list[dict], dict[str, int]]:
    """Match pulse descriptions against all 28 Classical Pulses and aggregate 8-principle weights."""
    matched: list[dict] = []
    ep_totals = {"exterior": 0, "interior": 0, "cold": 0, "heat": 0, "deficiency": 0, "excess": 0, "yin": 0, "yang": 0}
    if not pulse_str.strip():
        return matched, ep_totals

    p_low = pulse_str.lower()
    for p_cn, p_data in TWENTY_EIGHT_PULSES.items():
        if p_cn in pulse_str or p_data["english"].lower() in p_low or p_data["pinyin"].lower() in p_low:
            matched.append({"pulse": p_cn, **p_data})
            for dim, val in p_data["eight_principles"].items():
                ep_totals[dim] = ep_totals.get(dim, 0) + val

    if any(w in p_low for w in ("无力", "forceless", "feeble")):
        ep_totals["deficiency"] += 2
    if any(w in p_low for w in ("有力", "forceful", "strong")):
        ep_totals["excess"] += 2
    return matched, ep_totals


def _summarize_eight_principles(ep: dict[str, int]) -> dict:
    """Format quantitative Eight-Principle scores into clinical polarity labels."""
    loc = (
        "表里同病 (Combined Exterior-Interior)"
        if ep["exterior"] >= 2 and ep["interior"] >= 2
        else ("表证 (Exterior)" if ep["exterior"] > ep["interior"] else "里证 (Interior)")
    )
    therm = (
        "寒热错杂 (Mixed Cold-Heat)"
        if ep["cold"] >= 2 and ep["heat"] >= 2
        else ("热证 (Heat)" if ep["heat"] > ep["cold"] else ("寒证 (Cold)" if ep["cold"] > ep["heat"] else "平/寒热不显 (Neutral)"))
    )
    strength = (
        "本虚标实 / 虚实夹杂 (Mixed Deficiency-Excess)"
        if ep["deficiency"] >= 2 and ep["excess"] >= 2
        else ("虚证 (Deficiency)" if ep["deficiency"] > ep["excess"] else ("实证 (Excess)" if ep["excess"] > ep["deficiency"] else "中和 (Balanced)"))
    )
    yin_score = ep["yin"] + ep["interior"] + ep["cold"] + ep["deficiency"]
    yang_score = ep["yang"] + ep["exterior"] + ep["heat"] + ep["excess"]
    overall = "阴证偏重 (Predominantly Yin)" if yin_score > yang_score else "阳证偏重 (Predominantly Yang)"
    return {
        "location": loc,
        "nature": therm,
        "strength": strength,
        "yin_yang": overall,
        "location_表里": loc,
        "nature_寒热": therm,
        "strength_虚实": strength,
        "overarching_阴阳": overall,
        "scores": ep,
    }


@registry.register(
    name="diagnostics.four_examinations",
    description=(
        "Synthesize all Four TCM Examinations (四诊合参: 望 inspection/tongue, 闻 auscultation/olfaction, "
        "问 inquiry/symptoms, 切 28 classical pulses 二十八脉) into an Eight-Principle profile (八纲辨证), "
        "ranked Zang-Fu syndromes with modality concordance, classical formulas, acupoints, and lifestyle advice."
    ),
    category="diagnostics",
    parameters={
        "inspection": "望诊: complexion, spirit, tongue appearance, body build",
        "auscultation": "闻诊: voice strength, cough, wheezing, sighing, breath/stool odor",
        "inquiry": "问诊: chills/fever, sweat, pain, appetite, thirst, stool/urine, sleep, menses",
        "pulse": "切诊: pulse qualities from the 28 Classical Pulses (e.g., '脉弦细数', '沉迟无力', 'wiry rapid')",
    },
    usage_guide="When performing holistic TCM syndrome differentiation across multiple clinical modalities.",
)
def four_examinations(
    inspection: str = "",
    auscultation: str = "",
    inquiry: str = "",
    pulse: str = "",
) -> dict:
    """Perform holistic Four-Examinations synthesis (四诊合参・八纲脏腑辨证)."""
    modalities = {
        "inspection": inspection.strip(),
        "auscultation": auscultation.strip(),
        "inquiry": inquiry.strip(),
        "pulse": pulse.strip(),
    }
    if not any(modalities.values()):
        return {
            "status": "insufficient_input",
            "message": "Provide at least one modality among inspection (望), auscultation (闻), inquiry (问), or pulse (切).",
            "supported_pulses_count": len(TWENTY_EIGHT_PULSES),
        }

    matched_pulses, ep_scores = _analyze_pulse_text(modalities["pulse"])

    # Incorporate tongue Eight-Principle clues if inspection mentions tongue traits
    tongue_sub = None
    if modalities["inspection"]:
        t_res = tongue_analyze(observations=modalities["inspection"])
        if t_res.get("status") == "complete":
            tongue_sub = t_res["primary_syndrome"]
            dim_s = t_res["eight_principles"].get("dimension_scores", {})
            for k, v in dim_s.items():
                ep_scores[k] = ep_scores.get(k, 0) + v

    all_text_low = " ".join(modalities.values()).lower()
    if any(w in all_text_low for w in ("恶寒", "畏寒", "肢冷", "喜温", "chills", "cold limbs")):
        ep_scores["cold"] += 2
    if any(w in all_text_low for w in ("发热", "烦热", "口苦", "黄痰", "短赤", "fever", "hot", "thirst")):
        ep_scores["heat"] += 2
    if any(w in all_text_low for w in ("乏力", "懒言", "自汗", "盗汗", "酸软", "fatigue", "weak")):
        ep_scores["deficiency"] += 2
    if any(w in all_text_low for w in ("胀痛", "刺痛", "拒按", "黄腻", "秘结", "distension", "stabbing")):
        ep_scores["excess"] += 2

    ranked_syndromes: list[dict] = []
    for syn in FOUR_EXAM_SYNDROMES:
        evidence: dict[str, list[str]] = {}
        total_hits = 0
        for mod_key, clue_list in syn["modality_clues"].items():
            # Allow cross-modality pickup if user pasted all symptoms into inquiry/inspection
            mod_text = modalities[mod_key].lower()
            broad_text = all_text_low if not mod_text else mod_text
            hits = [c for c in clue_list if c.lower() in broad_text]
            if hits:
                evidence[mod_key] = hits
                total_hits += len(hits)

        if total_hits == 0:
            continue
        concordance = len(evidence)
        confidence = min(0.98, round(0.32 + 0.10 * total_hits + 0.08 * concordance, 2))
        ranked_syndromes.append({
            "syndrome": syn["syndrome"],
            "confidence": confidence,
            "modality_concordance_count": concordance,
            "evidence_by_modality": evidence,
            "eight_principles_pattern": syn["eight_principles"],
            "treatment_principle": syn["treatment_principle"],
            "representative_formulas": syn["formulas"],
            "herb_modifications": syn["modifications"],
            "recommended_acupoints": syn["acupoints"],
            "dietary_and_lifestyle_advice": syn["lifestyle"],
        })

    ranked_syndromes.sort(
        key=lambda s: (s["confidence"], s["modality_concordance_count"]),
        reverse=True,
    )

    eight_principles_summary = _summarize_eight_principles(ep_scores)

    return {
        "status": "complete",
        "modalities_provided": [k for k, v in modalities.items() if v],
        "eight_principles": eight_principles_summary,
        "eight_principles_profile": eight_principles_summary,
        "pulse_analysis": {
            "matched_pulses": matched_pulses,
            "total_classical_pulses_in_db": len(TWENTY_EIGHT_PULSES),
        },
        "tongue_subanalysis": tongue_sub,
        "primary_syndrome": ranked_syndromes[0] if ranked_syndromes else None,
        "ranked_syndromes": ranked_syndromes[:5],
    }
