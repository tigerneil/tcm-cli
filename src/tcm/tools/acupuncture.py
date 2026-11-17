"""
Acupuncture & Moxibustion tools (针灸学工具): WHO standard acupoint lookup across all
14 channels (十二正经与任督二脉), channel point listing, and clinical point-prescription
protocols (处方配穴与妊娠禁针安全过滤).
"""
from __future__ import annotations

import logging
import re

from tcm.tools import registry
from tcm.tools.meridians import MERIDIAN_DB

logger = logging.getLogger("tcm.tools.acupuncture")


# ─── Channel Metadata across All 14 Channels (十四经脉索引) ──────────────────────

CHANNEL_INDEX: dict[str, dict] = {
    "LU": {"chinese": "手太阴肺经", "short_cn": "肺经", "english": "Lung Meridian", "aliases": ["lu", "lung", "肺", "肺经", "手太阴"]},
    "LI": {"chinese": "手阳明大肠经", "short_cn": "大肠经", "english": "Large Intestine Meridian", "aliases": ["li", "large intestine", "大肠", "大肠经", "手阳明"]},
    "ST": {"chinese": "足阳明胃经", "short_cn": "胃经", "english": "Stomach Meridian", "aliases": ["st", "stomach", "胃", "胃经", "足阳明"]},
    "SP": {"chinese": "足太阴脾经", "short_cn": "脾经", "english": "Spleen Meridian", "aliases": ["sp", "spleen", "脾", "脾经", "足太阴"]},
    "HT": {"chinese": "手少阴心经", "short_cn": "心经", "english": "Heart Meridian", "aliases": ["ht", "he", "heart", "心", "心经", "手少阴"]},
    "SI": {"chinese": "手太阳小肠经", "short_cn": "小肠经", "english": "Small Intestine Meridian", "aliases": ["si", "small intestine", "小肠", "小肠经", "手太阳"]},
    "BL": {"chinese": "足太阳膀胱经", "short_cn": "膀胱经", "english": "Bladder Meridian", "aliases": ["bl", "ub", "bladder", "urinary bladder", "膀胱", "膀胱经", "足太阳"]},
    "KI": {"chinese": "足少阴肾经", "short_cn": "肾经", "english": "Kidney Meridian", "aliases": ["ki", "kd", "kidney", "肾", "肾经", "足少阴"]},
    "PC": {"chinese": "手厥阴心包经", "short_cn": "心包经", "english": "Pericardium Meridian", "aliases": ["pc", "p", "pericardium", "心包", "心包经", "手厥阴"]},
    "TE": {"chinese": "手少阳三焦经", "short_cn": "三焦经", "english": "Triple Energizer Meridian", "aliases": ["te", "sj", "tb", "triple burner", "triple energizer", "sanjiao", "三焦", "三焦经", "手少阳"]},
    "GB": {"chinese": "足少阳胆经", "short_cn": "胆经", "english": "Gallbladder Meridian", "aliases": ["gb", "gallbladder", "胆", "胆经", "足少阳"]},
    "LR": {"chinese": "足厥阴肝经", "short_cn": "肝经", "english": "Liver Meridian", "aliases": ["lr", "lv", "liv", "liver", "肝", "肝经", "足厥阴"]},
    "GV": {"chinese": "督脉", "short_cn": "督脉", "english": "Governor Vessel (Du Mai)", "aliases": ["gv", "du", "du mai", "governor vessel", "督", "督脉"]},
    "CV": {"chinese": "任脉", "short_cn": "任脉", "english": "Conception Vessel (Ren Mai)", "aliases": ["cv", "rn", "ren", "ren mai", "conception vessel", "任", "任脉"]},
}

# Classical pregnancy-forbidden / contraindicated points (妊娠禁针与小腹禁针穴)
PREGNANCY_FORBIDDEN_POINTS: dict[str, str] = {
    "LI4": "合谷宣泄气机力峻，易催产下胎，古今列为妊娠禁针首穴 (Strongly moves Qi & promotes labor)",
    "SP6": "三阴交调血通经行气，与合谷同用可引产，妊娠严禁针刺 (Strongly activates Blood & uterine contractions)",
    "BL60": "昆仑通经催产力强，滞产可用而妊娠安胎绝对禁针 (Promotes labor descent; forbidden during pregnancy)",
    "BL67": "至阴矫正胎位仅限特定孕周遵医嘱艾灸，常规妊娠禁针 (Uterine-active point; forbidden for routine needling)",
    "CV4": "关元位于小腹正中子宫上方，妊娠禁深刺及重灸小腹 (Lower abdominal point directly overlying gravid uterus)",
    "CV6": "气海位于下腹脐下1.5寸，妊娠期间禁针小腹穴位 (Lower abdominal point; forbidden in pregnancy)",
    "ST25": "天枢位于脐旁2寸腹部，孕期禁针腹部穴位 (Abdominal point adjacent to uterus)",
    "CV12": "中脘位于上腹，妊娠中晚期子宫增大严禁深刺腹部 (Abdominal point; avoid in mid-to-late pregnancy)",
}


# ─── 28 Curated Clinical Acupoints Across All 14 Channels (临床核心腧穴库) ───────

ACUPOINT_DB: dict[str, dict] = {
    "LU7": {
        "code": "LU7", "aliases": [],
        "chinese_name": "列缺", "pinyin": "Liè Quē", "pinyin_plain": "lieque",
        "english_name": "Broken Sequence",
        "channel_code": "LU", "meridian": "手太阴肺经 (Lung Meridian)",
        "special_categories": ["络穴 (Luo-Connecting)", "八脉交会穴通任脉 (Confluent of Ren Mai)", "四总穴『头项寻列缺』"],
        "location": "前臂桡侧缘，桡骨茎突上方，腕横纹上1.5寸，当肱桡肌与拇长展肌腱之间 (1.5 cun proximal to wrist crease above radial styloid)",
        "needling": "向上或向下斜刺 0.3-0.5 寸 (Oblique insertion 0.3-0.5 cun); 可灸",
        "actions": ["宣肺解表 (Diffuses Lung & releases exterior)", "通经活络利头项 (Unblocks channels & benefits head/neck)", "通调任脉 (Regulates Ren Mai)"],
        "indications": ["外感咳嗽气喘", "偏正头痛、项强", "咽喉肿痛", "口眼歪斜"],
        "pregnancy_safety": "safe",
        "safety_notes": "避开桡动脉分支及头静脉浅支。",
    },
    "LU9": {
        "code": "LU9", "aliases": [],
        "chinese_name": "太渊", "pinyin": "Tài Yuān", "pinyin_plain": "taiyuan",
        "english_name": "Supreme Abyss",
        "channel_code": "LU", "meridian": "手太阴肺经 (Lung Meridian)",
        "special_categories": ["输穴 (Shu-Stream)", "原穴 (Yuan-Source)", "八会穴之脉会『脉会太渊』"],
        "location": "腕掌侧横纹桡侧，桡动脉搏动处 (At radial end of palmar wrist crease, lateral to radial artery pulsation)",
        "needling": "避开桡动脉，直刺 0.3-0.5 寸 (Perpendicular 0.3-0.5 cun avoiding radial artery); 慎瘢痕灸",
        "actions": ["补肺益气 (Tonifies Lung Qi)", "止咳化痰 (Stops cough & transforms phlegm)", "通调血脉 (Harmonizes vessels)"],
        "indications": ["久咳虚喘", "无脉症、脉管炎", "腕臂痛"],
        "pregnancy_safety": "safe",
        "safety_notes": "紧邻桡动脉，进针前务必指切押手避开动脉搏动处。",
    },
    "LI4": {
        "code": "LI4", "aliases": [],
        "chinese_name": "合谷", "pinyin": "Hé Gǔ", "pinyin_plain": "hegu",
        "english_name": "Joining Valley",
        "channel_code": "LI", "meridian": "手阳明大肠经 (Large Intestine Meridian)",
        "special_categories": ["原穴 (Yuan-Source)", "四总穴『面口合谷收』", "四关穴之一 (with LR3)"],
        "location": "手背第1、2掌骨间，当第二掌骨桡侧的中点处 (Dorsum of hand, between 1st & 2nd metacarpals at midpoint of 2nd metacarpal)",
        "needling": "直刺 0.5-1.0 寸 (Perpendicular 0.5-1.0 cun); 可灸",
        "actions": ["疏风解表 (Disperses wind & releases exterior)", "行气活血镇痛 (Moves Qi, invigorates Blood, stops pain)", "通经清热开窍 (Clears heat & benefits face/mouth)"],
        "indications": ["发热恶寒无汗或多汗", "头痛、牙痛、咽喉肿痛、面瘫", "痛经、闭经、滞产", "腹痛便秘"],
        "pregnancy_safety": "contraindicated",
        "safety_notes": "【妊娠禁针】孕妇严禁针刺合谷，防动胎气致流产早产。",
    },
    "LI11": {
        "code": "LI11", "aliases": [],
        "chinese_name": "曲池", "pinyin": "Qū Chí", "pinyin_plain": "quchi",
        "english_name": "Pool at the Crook",
        "channel_code": "LI", "meridian": "手阳明大肠经 (Large Intestine Meridian)",
        "special_categories": ["合穴 (He-Sea — Earth point)"],
        "location": "屈肘成直角，肘横纹外侧端与肱骨外上髁连线中点 (Midpoint between lateral end of cubital crease and lateral epicondyle)",
        "needling": "直刺 1.0-1.5 寸 (Perpendicular 1.0-1.5 cun); 可灸",
        "actions": ["清热解表凉血 (Clears heat, cools Blood, releases exterior)", "祛风湿止痒 (Expels wind-damp & relieves itching)", "调和气血降压 (Harmonizes Qi-Blood & lowers Yang hypertension)"],
        "indications": ["热病高热", "瘾疹湿疹瘙痒", "高血压眩晕", "上肢不遂、肘臂痛", "腹痛吐泻"],
        "pregnancy_safety": "safe",
        "safety_notes": "常规安全要穴。",
    },
    "ST25": {
        "code": "ST25", "aliases": [],
        "chinese_name": "天枢", "pinyin": "Tiān Shū", "pinyin_plain": "tianshu",
        "english_name": "Celestial Pivot",
        "channel_code": "ST", "meridian": "足阳明胃经 (Stomach Meridian)",
        "special_categories": ["大肠募穴 (Front-Mu of Large Intestine)"],
        "location": "腹中部，距脐中旁开 2 寸 (2 cun lateral to center of umbilicus CV8)",
        "needling": "直刺 1.0-1.5 寸 (Perpendicular 1.0-1.5 cun); 可灸",
        "actions": ["调中和胃理气 (Regulates middle Qi)", "通调大肠双向调节便泄 (Bi-directionally regulates constipation & diarrhea)"],
        "indications": ["腹胀肠鸣、便秘、泄泻、痢疾", "绕脐痛", "月经不调、痛经"],
        "pregnancy_safety": "contraindicated",
        "safety_notes": "【妊娠禁针】腹部腧穴，孕妇禁针；肠梗阻腹膜炎患者慎勿穿透腹膜。",
    },
    "ST36": {
        "code": "ST36", "aliases": [],
        "chinese_name": "足三里", "pinyin": "Zú Sān Lǐ", "pinyin_plain": "zusanli",
        "english_name": "Leg Three Miles",
        "channel_code": "ST", "meridian": "足阳明胃经 (Stomach Meridian)",
        "special_categories": ["合穴 (He-Sea)", "胃下合穴 (Lower He-Sea of Stomach)", "四总穴『肚腹三里留』", "强壮保健第一要穴"],
        "location": "小腿前外侧，犊鼻（外膝眼）下 3 寸，距胫骨前缘一横指（中指）(3 cun below Dubi ST35, one finger-breadth lateral to anterior crest of tibia)",
        "needling": "直刺 1.0-2.0 寸 (Perpendicular 1.0-2.0 cun); 极宜艾灸保健",
        "actions": ["健脾和胃化湿 (Fortifies Spleen, harmonizes Stomach, resolves dampness)", "扶正培元补益气血 (Tonifies Zheng Qi & Blood)", "通经活络升降气机 (Unblocks channels & regulates Qi ascent/descent)"],
        "indications": ["胃痛、呕吐、腹胀、泄泻、便秘", "虚劳羸瘦、免疫力低下", "下肢痿痹", "头晕心悸"],
        "pregnancy_safety": "safe",
        "safety_notes": "孕期可温和轻刺或艾灸调理脾胃，忌强刺激泻法。",
    },
    "ST40": {
        "code": "ST40", "aliases": [],
        "chinese_name": "丰隆", "pinyin": "Fēng Lóng", "pinyin_plain": "fenglong",
        "english_name": "Abundant Bulge",
        "channel_code": "ST", "meridian": "足阳明胃经 (Stomach Meridian)",
        "special_categories": ["络穴 (Luo-Connecting)", "治痰第一要穴 (Master Point for Phlegm)"],
        "location": "小腿前外侧，外踝尖上 8 寸，条口外侧，距胫骨前缘二横指 (8 cun superior to lateral malleolus, two finger-breadths lateral to anterior tibial crest)",
        "needling": "直刺 1.0-1.5 寸 (Perpendicular 1.0-1.5 cun); 可灸",
        "actions": ["燥湿化痰（有形无形之痰皆治）(Transforms both visible & invisible phlegm)", "和胃降逆开窍定眩 (Harmonizes Stomach & calms phlegm dizziness)"],
        "indications": ["咳嗽痰多哮喘", "痰饮眩晕头痛", "梅核气、癫狂", "高脂血症、痰湿肥胖"],
        "pregnancy_safety": "safe",
        "safety_notes": "常规安全。",
    },
    "SP6": {
        "code": "SP6", "aliases": [],
        "chinese_name": "三阴交", "pinyin": "Sān Yīn Jiāo", "pinyin_plain": "sanyinjiao",
        "english_name": "Three Yin Intersection",
        "channel_code": "SP", "meridian": "足太阴脾经 (Spleen Meridian)",
        "special_categories": ["足太阴脾、足厥阴肝、足少阴肾三阴经交会穴 (Intersection of SP, LR, KI)"],
        "location": "小腿内侧，内踝尖上 3 寸，胫骨内侧缘后际 (3 cun directly above tip of medial malleolus, posterior to medial border of tibia)",
        "needling": "直刺 1.0-1.5 寸 (Perpendicular 1.0-1.5 cun); 可灸",
        "actions": ["健脾化湿 (Fortifies Spleen & resolves dampness)", "调补肝肾养血调经 (Nourishes Liver-Kidney Yin & regulates menstruation)", "安神利尿 (Calms Shen & promotes urination)"],
        "indications": ["月经不调、痛经、带下、崩漏、不孕", "脾胃虚弱肠鸣便溏", "失眠心悸", "遗精遗尿水肿"],
        "pregnancy_safety": "contraindicated",
        "safety_notes": "【妊娠禁针】孕妇严禁针刺三阴交，尤忌配伍合谷（可诱发宫缩流产）。",
    },
    "SP9": {
        "code": "SP9", "aliases": [],
        "chinese_name": "阴陵泉", "pinyin": "Yīn Líng Quán", "pinyin_plain": "yinlingquan",
        "english_name": "Yin Mound Spring",
        "channel_code": "SP", "meridian": "足太阴脾经 (Spleen Meridian)",
        "special_categories": ["合穴 (He-Sea — Water point)", "祛湿第一要穴 (Master Point for Dampness)"],
        "location": "小腿内侧，胫骨内侧髁下缘与胫骨内侧缘之间的凹陷中 (In depression between inferior border of medial condyle of tibia and medial border of tibia)",
        "needling": "直刺 1.0-2.0 寸 (Perpendicular 1.0-2.0 cun); 可灸",
        "actions": ["健脾利水渗湿 (Fortifies Spleen, drains dampness, promotes urination)", "通利三焦膝关 (Unblocks water passages & benefits knee)"],
        "indications": ["腹胀、水肿、泄泻、黄疸", "小便不利或失禁", "膝痛痹证"],
        "pregnancy_safety": "safe",
        "safety_notes": "常规安全。",
    },
    "HT7": {
        "code": "HT7", "aliases": ["HE7"],
        "chinese_name": "神门", "pinyin": "Shén Mén", "pinyin_plain": "shenmen",
        "english_name": "Spirit Gate",
        "channel_code": "HT", "meridian": "手少阴心经 (Heart Meridian)",
        "special_categories": ["输穴 (Shu-Stream)", "原穴 (Yuan-Source)", "养心安神第一要穴"],
        "location": "腕前区，腕掌侧远端横纹尺侧端，尺侧腕屈肌腱的桡侧凹陷处 (At ulnar end of distal wrist crease, radial to flexor carpi ulnaris tendon)",
        "needling": "直刺 0.3-0.5 寸 (Perpendicular 0.3-0.5 cun); 可灸",
        "actions": ["宁心安神定志 (Calms Heart & tranquilizes Spirit)", "清心通络定悸 (Clears Heart heat & regulates palpitations)"],
        "indications": ["失眠多梦、健忘、惊悸怔忡", "心痛、烦躁焦虑", "癫狂痫"],
        "pregnancy_safety": "safe",
        "safety_notes": "尺侧紧邻尺神经及尺动静脉，忌粗针深刺乱捣。",
    },
    "SI3": {
        "code": "SI3", "aliases": [],
        "chinese_name": "后溪", "pinyin": "Hòu Xī", "pinyin_plain": "houxi",
        "english_name": "Back Stream",
        "channel_code": "SI", "meridian": "手太阳小肠经 (Small Intestine Meridian)",
        "special_categories": ["输穴 (Shu-Stream)", "八脉交会穴通督脉 (Confluent of Du Mai)"],
        "location": "微握拳，第5掌指关节尺侧近端赤白肉际凹陷中 (Ulnar border of hand, proximal to 5th MCP joint at end of transverse palmar crease)",
        "needling": "直刺 0.5-1.0 寸（治急性腰扭伤或落枕可向合谷方向透刺并嘱患者活动腰颈）; 可灸",
        "actions": ["通督脉利腰颈 (Unblocks Du Mai & relaxes cervical/lumbar spine)", "清心安神截疟祛风 (Clears heat & expels wind)"],
        "indications": ["头项强痛、落枕、急性腰扭伤", "耳聋耳鸣", "盗汗、疟疾、癫狂"],
        "pregnancy_safety": "safe",
        "safety_notes": "常规安全。",
    },
    "BL13": {
        "code": "BL13", "aliases": ["UB13"],
        "chinese_name": "肺俞", "pinyin": "Fèi Shù", "pinyin_plain": "feishu",
        "english_name": "Lung Shu",
        "channel_code": "BL", "meridian": "足太阳膀胱经 (Bladder Meridian)",
        "special_categories": ["肺之背俞穴 (Back-Shu of Lung)"],
        "location": "脊柱区，第3胸椎棘突下，后正中线旁开 1.5 寸 (1.5 cun lateral to lower border of T3 spinous process)",
        "needling": "向脊柱方向斜刺 0.5-0.8 寸 (Oblique medial insertion 0.5-0.8 cun); 宜艾灸或拔罐、三伏贴",
        "actions": ["调补肺气宣肺止咳 (Tonifies & diffuses Lung Qi, stops cough/asthma)", "清肺虚热固表 (Clears Lung deficiency heat & consolidates exterior)"],
        "indications": ["咳嗽、气喘、哮喘、感冒鼻炎", "骨蒸潮热盗汗", "皮肤瘾疹瘙痒"],
        "pregnancy_safety": "safe",
        "safety_notes": "【解剖警示】深部为胸膜腔及肺脏，严禁直刺深刺，谨防气胸 (Pneumothorax risk)！",
    },
    "BL20": {
        "code": "BL20", "aliases": ["UB20"],
        "chinese_name": "脾俞", "pinyin": "Pí Shù", "pinyin_plain": "pishu",
        "english_name": "Spleen Shu",
        "channel_code": "BL", "meridian": "足太阳膀胱经 (Bladder Meridian)",
        "special_categories": ["脾之背俞穴 (Back-Shu of Spleen)"],
        "location": "脊柱区，第11胸椎棘突下，后正中线旁开 1.5 寸 (1.5 cun lateral to lower border of T11 spinous process)",
        "needling": "斜刺 0.5-0.8 寸 (Oblique medial insertion 0.5-0.8 cun); 宜灸",
        "actions": ["健脾益气和胃 (Fortifies Spleen Qi & harmonizes Stomach)", "运化水湿统血 (Transforms dampness & holds Blood)"],
        "indications": ["腹胀、纳呆、呕吐、泄泻、水肿", "便血、崩漏等脾不统血证", "背痛乏力"],
        "pregnancy_safety": "safe",
        "safety_notes": "不可直刺过深，以防伤及胸膜下界及内脏。",
    },
    "BL23": {
        "code": "BL23", "aliases": ["UB23"],
        "chinese_name": "肾俞", "pinyin": "Shèn Shù", "pinyin_plain": "shenshu",
        "english_name": "Kidney Shu",
        "channel_code": "BL", "meridian": "足太阳膀胱经 (Bladder Meridian)",
        "special_categories": ["肾之背俞穴 (Back-Shu of Kidney)"],
        "location": "腰区，第2腰椎棘突下，后正中线旁开 1.5 寸 (1.5 cun lateral to lower border of L2 spinous process)",
        "needling": "直刺 0.5-1.0 寸 (Perpendicular 0.5-1.0 cun); 宜温灸",
        "actions": ["培补肾元益精壮骨 (Tonifies Kidney Yin/Yang, essence, and lumbar bones)", "纳气利水聪耳 (Aids Kidney Qi grasping & water metabolism)"],
        "indications": ["腰膝酸痛、慢性腰痛", "头晕耳鸣耳聋", "遗精阳痿、月经不调、不孕", "久喘、水肿、夜尿频"],
        "pregnancy_safety": "caution",
        "safety_notes": "深部紧邻肾脏下极，严禁大幅度提插深刺；孕妇腰骶部慎强刺激。",
    },
    "BL40": {
        "code": "BL40", "aliases": ["UB40"],
        "chinese_name": "委中", "pinyin": "Wěi Zhōng", "pinyin_plain": "weizhong",
        "english_name": "Middle of the Crook",
        "channel_code": "BL", "meridian": "足太阳膀胱经 (Bladder Meridian)",
        "special_categories": ["合穴 (He-Sea)", "膀胱下合穴", "四总穴『腰背委中求』", "血郄"],
        "location": "膝后区，腘横纹中点，当股二头肌腱与半腱肌肌腱的中间 (Midpoint of transverse crease of popliteal fossa)",
        "needling": "直刺 1.0-1.5 寸，或三棱针点刺腘静脉浮络放血 (Perpendicular 1.0-1.5 cun or prick superficial venule); 禁瘢痕灸",
        "actions": ["舒筋通络利腰膝 (Relaxes sinews & unblocks lumbar spine/knee)", "清暑泄热凉血解毒 (Clears summerheat & cools Blood)"],
        "indications": ["急性或慢性腰背痛、坐骨神经痛、下肢痿痹", "急性吐泻中暑", "丹毒疔疮"],
        "pregnancy_safety": "caution",
        "safety_notes": "深层有腘动静脉和胫神经；孕妇禁刺络放血及强刺激。",
    },
    "BL60": {
        "code": "BL60", "aliases": ["UB60"],
        "chinese_name": "昆仑", "pinyin": "Kūn Lún", "pinyin_plain": "kunlun",
        "english_name": "Kunlun Mountains",
        "channel_code": "BL", "meridian": "足太阳膀胱经 (Bladder Meridian)",
        "special_categories": ["经穴 (Jing-River — Fire point)"],
        "location": "踝区，外踝尖与跟腱之间的凹陷中 (In depression midway between tip of lateral malleolus and Achilles tendon)",
        "needling": "直刺 0.5-0.8 寸 (Perpendicular 0.5-0.8 cun); 可灸",
        "actions": ["通经活络止痛 (Unblocks Taiyang channel & stops pain)", "散风清热催产 (Clears head-wind & promotes labor)"],
        "indications": ["后头痛、项强、腰骶痛、足踝肿痛", "滞产、胞衣不下"],
        "pregnancy_safety": "contraindicated",
        "safety_notes": "【妊娠禁针】具明显催产下胎作用，孕妇禁针。",
    },
    "BL67": {
        "code": "BL67", "aliases": ["UB67"],
        "chinese_name": "至阴", "pinyin": "Zhì Yīn", "pinyin_plain": "zhiyin",
        "english_name": "Reaching Yin",
        "channel_code": "BL", "meridian": "足太阳膀胱经 (Bladder Meridian)",
        "special_categories": ["井穴 (Jing-Well — Metal point)"],
        "location": "足小趾末节外侧，趾甲根角侧后方 0.1 寸 (Lateral side of 5th toe, 0.1 cun proximal to corner of nail)",
        "needling": "浅刺 0.1 寸；胎位不正专用艾条温和灸 15-20 分钟",
        "actions": ["正胎催产 (Corrects malposition of fetus & expedites delivery)", "清头明目散风 (Clears vertex/occipital headache)"],
        "indications": ["胎位不正（艾灸）、滞产", "巅顶及后头痛、目痛鼻塞"],
        "pregnancy_safety": "contraindicated",
        "safety_notes": "【妊娠禁针】除产科医生指导下特定孕周艾灸矫正胎位外，妊娠期严禁针刺。",
    },
    "KI1": {
        "code": "KI1", "aliases": ["KD1"],
        "chinese_name": "涌泉", "pinyin": "Yǒng Quán", "pinyin_plain": "yongquan",
        "english_name": "Gushing Spring",
        "channel_code": "KI", "meridian": "足少阴肾经 (Kidney Meridian)",
        "special_categories": ["井穴 (Jing-Well — Wood point)", "引火归元要穴"],
        "location": "足底，卷足时足前部凹陷处，约当第2、3趾趾缝纹头端与足跟连线的前1/3与后2/3交点上 (On sole in depression at junction of anterior 1/3 and posterior 2/3)",
        "needling": "直刺 0.5-1.0 寸（痛感较强，临床常采用艾灸、吴茱萸敷贴或按摩导引）",
        "actions": ["苏厥开窍救急 (Revives consciousness)", "滋肾清热、引火归元 (Nourishes Kidney & conducts upper fire downward)"],
        "indications": ["昏厥、中暑、小儿惊风", "虚火上炎之失眠、口腔溃疡、头晕头痛、高血压", "足心烦热"],
        "pregnancy_safety": "caution",
        "safety_notes": "足底针刺痛感剧烈，孕妇忌针刺涌泉防痛厥动胎（温水泡脚轻揉可）。",
    },
    "KI3": {
        "code": "KI3", "aliases": ["KD3"],
        "chinese_name": "太溪", "pinyin": "Tài Xī", "pinyin_plain": "taixi",
        "english_name": "Supreme Stream",
        "channel_code": "KI", "meridian": "足少阴肾经 (Kidney Meridian)",
        "special_categories": ["输穴 (Shu-Stream)", "原穴 (Yuan-Source)", "补肾育阴第一要穴"],
        "location": "踝区，内踝尖与跟腱之间的凹陷中 (In depression midway between tip of medial malleolus and Achilles tendon)",
        "needling": "直刺 0.5-1.0 寸 (Perpendicular 0.5-1.0 cun); 可灸",
        "actions": ["滋肾阴、温肾阳 (Nourishes Kidney Yin & warms Kidney Yang)", "壮腰膝清虚热纳气 (Strengthens lower back & clears empty heat)"],
        "indications": ["腰膝酸软、头晕耳鸣、失眠健忘", "盗汗潮热、消渴咽干", "遗精阳痿、月经不调", "虚喘咳血"],
        "pregnancy_safety": "safe",
        "safety_notes": "前方有胫后动静脉，进针时避开血管搏动。",
    },
    "PC6": {
        "code": "PC6", "aliases": ["P6"],
        "chinese_name": "内关", "pinyin": "Nèi Guān", "pinyin_plain": "neiguan",
        "english_name": "Inner Pass",
        "channel_code": "PC", "meridian": "手厥阴心包经 (Pericardium Meridian)",
        "special_categories": ["络穴 (Luo-Connecting)", "八脉交会穴通阴维脉 (Confluent of Yinwei Mai)", "四总穴延伸『内关心胸胃』"],
        "location": "前臂前区，腕掌侧远端横纹上 2 寸，掌长肌腱与桡侧腕屈肌腱之间 (2 cun proximal to distal wrist crease, between palmaris longus and flexor carpi radialis tendons)",
        "needling": "直刺 0.5-1.0 寸 (Perpendicular 0.5-1.0 cun); 可灸或指压止呕",
        "actions": ["宁心安神宽胸理气 (Calms Heart Spirit & unbinds chest)", "和胃降逆止呕（妊娠恶阻首选安全穴）(Harmonizes Stomach & stops nausea/vomiting)"],
        "indications": ["心痛、心悸、胸闷、心律失常", "胃痛、恶心呕吐、呃逆、妊娠恶阻、晕车", "失眠郁证"],
        "pregnancy_safety": "safe",
        "safety_notes": "深部正对正中神经干，不宜深刺重提插以防触电样神经损伤；妊娠止呕安全首选。",
    },
    "TE5": {
        "code": "TE5", "aliases": ["SJ5", "TB5"],
        "chinese_name": "外关", "pinyin": "Wài Guān", "pinyin_plain": "waiguan",
        "english_name": "Outer Pass",
        "channel_code": "TE", "meridian": "手少阳三焦经 (Triple Energizer Meridian)",
        "special_categories": ["络穴 (Luo-Connecting)", "八脉交会穴通阳维脉 (Confluent of Yangwei Mai)"],
        "location": "前臂后区，腕背侧远端横纹上 2 寸，尺骨与桡骨间隙中点 (2 cun proximal to dorsal wrist crease, between radius and ulna)",
        "needling": "直刺 0.5-1.0 寸 (Perpendicular 0.5-1.0 cun); 可灸",
        "actions": ["疏风清热解表和解少阳 (Releases exterior wind-heat & harmonizes Shaoyang)", "通经活络聪耳利胁 (Benefits ear & hypochondrium)"],
        "indications": ["外感热病、往来寒热", "偏头痛、耳鸣耳聋", "胁肋痛、上肢痿痹落枕"],
        "pregnancy_safety": "safe",
        "safety_notes": "常规安全。",
    },
    "GB20": {
        "code": "GB20", "aliases": [],
        "chinese_name": "风池", "pinyin": "Fēng Chí", "pinyin_plain": "fengchi",
        "english_name": "Wind Pool",
        "channel_code": "GB", "meridian": "足少阳胆经 (Gallbladder Meridian)",
        "special_categories": ["足少阳胆经与阳维脉交会穴", "治内风外风第一要穴"],
        "location": "项部，枕骨之下，胸锁乳突肌上端与斜方肌上端之间的凹陷中 (Below occiput in depression between upper origins of sternocleidomastoid and trapezius)",
        "needling": "针尖微下，向鼻尖方向斜刺 0.8-1.2 寸 (Oblique insertion 0.8-1.2 cun directed toward tip of nose)",
        "actions": ["祛风解表、平肝熄风潜阳 (Expels exterior wind & extinguishes interior Liver wind)", "清头明目利官窍 (Clears head, eyes, and ears)"],
        "indications": ["头痛、眩晕、高血压、中风", "感冒发热、颈项强痛", "目赤肿痛、耳鸣、失眠"],
        "pregnancy_safety": "safe",
        "safety_notes": "【解剖铁律】深部正对延髓及椎动脉，严禁向对侧眼眶内上方深刺，以免误伤延髓危及生命！",
    },
    "GB34": {
        "code": "GB34", "aliases": [],
        "chinese_name": "阳陵泉", "pinyin": "Yáng Líng Quán", "pinyin_plain": "yanglingquan",
        "english_name": "Yang Mound Spring",
        "channel_code": "GB", "meridian": "足少阳胆经 (Gallbladder Meridian)",
        "special_categories": ["合穴 (He-Sea)", "胆下合穴", "八会穴之筋会『筋会阳陵泉』"],
        "location": "小腿外侧，腓骨头前下方凹陷处 (In depression anterior and inferior to head of fibula)",
        "needling": "直刺 1.0-1.5 寸 (Perpendicular 1.0-1.5 cun); 可灸",
        "actions": ["疏肝利胆清湿热 (Courses Liver, benefits Gallbladder, clears damp-heat)", "舒筋活络强健筋骨 (Relaxes sinews & unblocks channels)"],
        "indications": ["黄疸、口苦、呕吐、胁肋痛、胆囊炎", "半身不遂、下肢痿痹、膝肿痛、抽筋"],
        "pregnancy_safety": "safe",
        "safety_notes": "腓骨颈附近有腓总神经经过，勿粗暴乱捣以防足下垂。",
    },
    "LR3": {
        "code": "LR3", "aliases": ["LV3", "LIV3"],
        "chinese_name": "太冲", "pinyin": "Tài Chōng", "pinyin_plain": "taichong",
        "english_name": "Supreme Rush",
        "channel_code": "LR", "meridian": "足厥阴肝经 (Liver Meridian)",
        "special_categories": ["输穴 (Shu-Stream)", "原穴 (Yuan-Source)", "四关穴之一 (with LI4)"],
        "location": "足背，第1、2跖骨间，跖骨底结合部前方凹陷中，或触及动脉搏动处 (Dorsum of foot, in depression distal to junction of 1st and 2nd metatarsal bones)",
        "needling": "直刺 0.5-0.8 寸 (Perpendicular 0.5-0.8 cun); 可灸",
        "actions": ["疏肝理气解郁 (Courses Liver Qi & resolves stagnation)", "平肝熄风潜阳清火 (Calms Liver Yang, extinguishes wind, clears Liver fire)", "调经活血止痛 (Regulates menstruation & stops pain)"],
        "indications": ["头痛眩晕、急躁易怒、高血压、失眠", "胸胁胀痛、郁证", "月经不调、痛经", "目赤肿痛"],
        "pregnancy_safety": "caution",
        "safety_notes": "避开足背动脉深支；孕妇慎用重泻强刺激。",
    },
    "GV20": {
        "code": "GV20", "aliases": ["DU20"],
        "chinese_name": "百会", "pinyin": "Bǎi Huì", "pinyin_plain": "baihui",
        "english_name": "Hundred Convergences",
        "channel_code": "GV", "meridian": "督脉 (Governor Vessel)",
        "special_categories": ["督脉与足太阳、手足少阳、足厥阴诸阳之会 (Sea of Yang Meeting)"],
        "location": "头部，当前发际正中直上 5 寸，或两耳尖连线的中点处 (At vertex on midline, 5 cun posterior to anterior hairline, midpoint of line connecting ear apices)",
        "needling": "平刺 0.5-0.8 寸 (Subcutaneous transverse insertion 0.5-0.8 cun); 宜艾条温和灸升阳",
        "actions": ["升阳举陷益气固脱 (Raises sunken Yang Qi & lifts prolapse)", "醒脑开窍安神定眩 (Awakens brain, calms Shen, relieves dizziness)", "平肝熄风 (Pacifies wind)"],
        "indications": ["头痛、眩晕、中风失语、痴呆健忘、失眠", "胃下垂、子宫脱垂、脱肛、久泻（艾灸）"],
        "pregnancy_safety": "safe",
        "safety_notes": "小儿囟门未合者禁针。",
    },
    "CV4": {
        "code": "CV4", "aliases": ["RN4", "REN4"],
        "chinese_name": "关元", "pinyin": "Guān Yuán", "pinyin_plain": "guanyuan",
        "english_name": "Origin Pass",
        "channel_code": "CV", "meridian": "任脉 (Conception Vessel)",
        "special_categories": ["小肠募穴 (Front-Mu of Small Intestine)", "任脉与足三阴经交会穴", "培元固本第一要穴"],
        "location": "下腹部，前正中线上，当脐中下 3 寸 (On anterior midline, 3 cun inferior to umbilicus)",
        "needling": "排空膀胱后直刺 1.0-1.5 寸；极宜温灸/隔姜灸/隔附子饼灸",
        "actions": ["培补元气、温肾壮阳回阳固脱 (Tonifies Yuan Qi, warms Kidney Yang, rescues collapse)", "调经暖宫固精止带 (Warms uterus & consolidates essence)"],
        "indications": ["元气虚损、畏寒肢冷、五更泄泻", "遗精阳痿早泄、尿频遗尿", "痛经闭经、宫寒不孕"],
        "pregnancy_safety": "contraindicated",
        "safety_notes": "【妊娠禁针灸】位于小腹子宫正上方，孕妇绝对禁针；针前必须嘱患者排空小便以防刺伤充盈膀胱！",
    },
    "CV6": {
        "code": "CV6", "aliases": ["RN6", "REN6"],
        "chinese_name": "气海", "pinyin": "Qì Hǎi", "pinyin_plain": "qihai",
        "english_name": "Sea of Qi",
        "channel_code": "CV", "meridian": "任脉 (Conception Vessel)",
        "special_categories": ["肓之原穴 (Yuan-Source of Membranes / Sea of Qi — 生气之海)"],
        "location": "下腹部，前正中线上，当脐中下 1.5 寸 (On anterior midline, 1.5 cun inferior to umbilicus)",
        "needling": "直刺 1.0-1.5 寸；宜艾灸温补气机",
        "actions": ["益气助阳、升阳举陷 (Tonifies & raises Qi, warms Yang)", "调理气机行气散滞 (Regulates lower-jiao Qi dynamics)"],
        "indications": ["气虚乏力、少气懒言、脏器下垂", "腹胀腹痛、肠鸣泄泻、便秘", "月经不调、痛经崩漏"],
        "pregnancy_safety": "contraindicated",
        "safety_notes": "【妊娠禁针灸】小腹腧穴，孕妇严禁针刺。",
    },
    "CV12": {
        "code": "CV12", "aliases": ["RN12", "REN12"],
        "chinese_name": "中脘", "pinyin": "Zhōng Wǎn", "pinyin_plain": "zhongwan",
        "english_name": "Middle Cavity",
        "channel_code": "CV", "meridian": "任脉 (Conception Vessel)",
        "special_categories": ["胃之募穴 (Front-Mu of Stomach)", "八会穴之腑会『腑会中脘』"],
        "location": "上腹部，前正中线上，当脐中上 4 寸（胸剑联合与脐中连线中点）(On anterior midline, 4 cun superior to umbilicus)",
        "needling": "直刺 1.0-1.5 寸 (Perpendicular 1.0-1.5 cun); 宜温灸",
        "actions": ["和胃健脾消食导滞 (Harmonizes Stomach, strengthens Spleen, reduces food stagnation)", "降逆利水化痰 (Descends rebellious Stomach Qi & resolves phlegm)"],
        "indications": ["胃痛、腹胀、反酸、呕吐、呃逆、消化不良", "泄泻、黄疸、痰饮内停"],
        "pregnancy_safety": "contraindicated",
        "safety_notes": "【解剖与妊娠警示】深部为胃幽门部、胰腺及肝左叶，勿深刺过猛；妊娠期禁针腹部穴位。",
    },
}


# ─── Clinical Acupuncture Protocols (临床辨证针灸处方库) ─────────────────────────

CLINICAL_PROTOCOLS: list[dict] = [
    {
        "name": "肝气郁结 / 情志郁证与痛证 (Liver Qi Stagnation, Stress & Tension Pain)",
        "keywords": ["肝气郁结", "肝郁", "郁证", "压力", "焦虑", "胁痛", "情绪", "四关", "stress", "liver qi", "anxiety", "depression", "tension"],
        "primary_points": ["LI4", "LR3", "PC6"],
        "supplemental_points": ["GB34", "CV12", "ST36"],
        "safe_pregnancy_substitutes": ["TE5", "GB34", "HT7"],
        "technique": "毫针平补平泻或轻泻法（提插捻转得气后留针 20-30 分钟，每 10 分钟行针一次），忌艾灸燥热助火。",
        "pairing_rationale": (
            "【四关穴配伍：合谷 LI4 + 太冲 LR3】源于《标幽赋》『寒热痛痹，开四关而已之』——合谷属阳明主气，太冲属厥阴主血，"
            "一阳一阴、一气一血、一升一降，相配大开周身气血关隘，疏肝解郁镇痛；辅以内关 PC6 宽胸宁神、阳陵泉 GB34 疏利少阳枢机。"
        ),
    },
    {
        "name": "不寐 / 心肾不交与心脾两虚失眠 (Insomnia — Shen Disturbance)",
        "keywords": ["失眠", "不寐", "多梦", "心悸", "心肾不交", "安神", "insomnia", "sleep", "palpitation"],
        "primary_points": ["HT7", "SP6", "PC6", "GV20"],
        "supplemental_points": ["KI3", "KI1", "BL23"],
        "safe_pregnancy_substitutes": ["KI3", "ST36"],
        "technique": "神门、内关平补平泻；太溪、三阴交行捻转补法；若心肾不交虚火上炎，睡前温灸或吴茱萸贴敷涌泉 KI1 引火归元，留针 30 分钟。",
        "pairing_rationale": (
            "神门 HT7（心原穴）配内关 PC6（心包络穴）双宁心神；三阴交 SP6 统调脾肝肾三阴养血育阴；"
            "太溪 KI3 滋水制火，合百会 GV20 上下相应以交通心肾、镇静安眠。"
        ),
    },
    {
        "name": "头痛 / 偏头痛与肝阳上亢眩晕 (Headache, Migraine & Liver Yang Rising)",
        "keywords": ["头痛", "偏头痛", "眩晕", "高血压", "肝阳上亢", "头风", "headache", "migraine", "dizziness", "vertigo", "hypertension"],
        "primary_points": ["GB20", "LR3", "LI4", "GV20"],
        "supplemental_points": ["TE5", "LU7", "KI3", "ST40"],
        "safe_pregnancy_substitutes": ["LU7", "TE5", "KI3"],
        "technique": "风池向鼻尖斜刺泻法，太冲、合谷行捻转泻法平肝潜阳；若夹痰浊配丰隆 ST40，肾阴不足补太溪 KI3，留针 25-30 分钟。",
        "pairing_rationale": (
            "风池 GB20 乃祛内外风要穴，配太冲 LR3 平肝潜阳清火上冲；少阳偏头痛配外关 TE5，阳明前额痛配合谷 LI4，太阳头项痛配列缺 LU7（分经论治）。"
        ),
    },
    {
        "name": "胃痛呕吐 / 脾胃虚弱与妊娠恶阻 (Epigastric Pain, Nausea, Dyspepsia & Morning Sickness)",
        "keywords": ["胃痛", "呕吐", "恶心", "腹胀", "消化不良", "脾气虚", "脾胃", "恶阻", "stomach", "nausea", "vomiting", "dyspepsia", "bloating", "spleen qi"],
        "primary_points": ["ST36", "PC6", "CV12"],
        "supplemental_points": ["BL20", "SP6", "SP9"],
        "safe_pregnancy_substitutes": ["BL20"],
        "technique": "足三里、中脘行提插捻转补法或温针灸健脾温中；内关直刺导气上行降逆止呕，留针 20-30 分钟。",
        "pairing_rationale": (
            "【合募俞配穴：足三里 ST36 + 中脘 CV12 + 脾俞 BL20】胃之下合穴配胃募穴与脾背俞穴，前后相应共奏健脾和胃升清降浊之功；"
            "配『内关心胸胃』PC6 宽中降逆止呕（若系妊娠恶阻则专取内关 PC6 + 足三里 ST36 轻刺，去中脘、三阴交）。"
        ),
    },
    {
        "name": "外感感冒 / 风寒风热咳嗽 (Common Cold, Exterior Wind & Cough)",
        "keywords": ["感冒", "咳嗽", "外感", "风寒", "风热", "发热", "鼻塞", "哮喘", "cold", "cough", "flu", "fever", "asthma"],
        "primary_points": ["LU7", "LI4", "BL13", "GB20"],
        "supplemental_points": ["LI11", "TE5", "LU9", "ST40"],
        "safe_pregnancy_substitutes": ["LU9", "TE5"],
        "technique": "浅刺疾出或提插泻法宣散表邪；风寒可于肺俞 BL13 拔火罐或艾灸，风热加曲池 LI11、外关 TE5 泻热，留针 15-20 分钟。",
        "pairing_rationale": (
            "【原络配穴：合谷 LI4 + 列缺 LU7】手阳明原穴配手太阴络穴，表里双解宣肺疏风；"
            "配肺俞 BL13 宣降肺气，风池 GB20 疏散风邪。"
        ),
    },
    {
        "name": "腰痛 / 肾虚劳损与坐骨神经痛 (Low Back Pain, Sciatica & Kidney Deficiency)",
        "keywords": ["腰痛", "腰膝酸软", "坐骨神经", "肾虚", "落枕", "颈肩痛", "back pain", "low back", "sciatica", "lumbar", "kidney"],
        "primary_points": ["BL40", "BL23", "KI3"],
        "supplemental_points": ["SI3", "BL60", "GB34", "CV4"],
        "safe_pregnancy_substitutes": ["SI3", "GB34"],
        "technique": "急性腰痛取委中 BL40 泻法或后溪 SI3 透刺行运动针法；慢性肾虚腰痛取肾俞 BL23、太溪 KI3、关元 CV4 补法加温针灸。",
        "pairing_rationale": (
            "谨守《四总穴歌》『腰背委中求』（BL40 疏通足太阳经气），配肾俞 BL23 + 太溪 KI3 俞原相配培补肾本，阳陵泉 GB34（筋会）舒筋利节。"
        ),
    },
    {
        "name": "痰湿内盛 / 水肿泄泻与代谢调理 (Phlegm-Dampness, Edema & Diarrhea)",
        "keywords": ["痰湿", "湿热", "水肿", "肥胖", "泄泻", "腹泻", "高血脂", "dampness", "phlegm", "edema", "diarrhea", "obesity"],
        "primary_points": ["ST40", "SP9", "ST36", "ST25"],
        "supplemental_points": ["CV12", "CV6", "BL20"],
        "safe_pregnancy_substitutes": ["BL20"],
        "technique": "丰隆、阴陵泉平补平泻或泻法健脾利湿化痰；足三里、脾俞补法培土制水，留针 30 分钟。",
        "pairing_rationale": (
            "【化痰祛湿双璧：丰隆 ST40 + 阴陵泉 SP9】丰隆化有形无形之痰，阴陵泉健脾渗水湿，辅以足三里 ST36 与天枢 ST25 分清别浊。"
        ),
    },
    {
        "name": "痛经 / 月经不调与宫寒血瘀 (Dysmenorrhea & Menstrual Disorders)",
        "keywords": ["痛经", "月经", "闭经", "妇科", "宫寒", "血瘀", "dysmenorrhea", "menstrual", "period pain", "pms"],
        "primary_points": ["SP6", "CV4", "CV6", "LR3"],
        "supplemental_points": ["LI4", "ST36", "KI3"],
        "safe_pregnancy_substitutes": ["ST36", "PC6", "KI3"],
        "technique": "寒凝痛经于关元 CV4、气海 CV6 施重灸温经散寒；气滞血瘀取三阴交 SP6、太冲 LR3、合谷 LI4 泻法行气活血止痛。",
        "pairing_rationale": (
            "任脉关元 CV4、气海 CV6 温养冲任胞宫，配足三阴交会穴三阴交 SP6 及肝原太冲 LR3 调理冲任气血。"
        ),
    },
]


def _normalize_code(raw: str) -> str:
    """Normalize acupoint codes like 'st-36', 'st 36', 'rn4' -> 'ST36', 'RN4'."""
    return re.sub(r"[\s\-_]+", "", raw.strip()).upper()


def _find_acupoint(query: str) -> dict | None:
    """Search acupoint by WHO code, alias code, Chinese name, pinyin, or English name."""
    q = query.strip()
    if not q:
        return None
    norm_code = _normalize_code(q)
    q_low = q.lower()
    q_plain = re.sub(r"[\s\-_']+", "", q_low)

    for code, data in ACUPOINT_DB.items():
        if norm_code == code or norm_code in data["aliases"]:
            return data
        if (
            q == data["chinese_name"]
            or q_plain == data["pinyin_plain"]
            or q_low == data["pinyin"].lower()
            or q_low == data["english_name"].lower()
            or data["chinese_name"] in q
        ):
            return data
    return None


@registry.register(
    name="acupuncture.point_lookup",
    description=(
        "Look up a TCM acupoint by WHO standard code (e.g., ST36, LI4, GV20, CV4), "
        "Chinese name (足三里), pinyin (zusanli), or English name. Returns anatomical location, "
        "special point categories, needling depth/method, indications, and pregnancy/anatomical safety."
    ),
    category="acupuncture",
    parameters={"point": "Acupoint identifier (WHO code, Chinese, pinyin, or English)"},
    usage_guide="When user asks for location, needling technique, or functions of a specific acupoint.",
)
def point_lookup(point: str) -> dict:
    """Look up a single clinical acupoint."""
    found = _find_acupoint(point)
    if found:
        return {"status": "found", "acupoint": found}
    return {
        "status": "not_found",
        "message": f"Acupoint '{point}' not found in curated database ({len(ACUPOINT_DB)} core clinical points).",
        "available_codes": list(ACUPOINT_DB.keys()),
    }


@registry.register(
    name="acupuncture.by_meridian",
    description=(
        "List curated clinical acupoints belonging to a specific meridian/channel across all "
        "14 channels (12 Regular Meridians + GV/督脉 + CV/任脉)."
    ),
    category="acupuncture",
    parameters={"meridian": "Channel code or name (e.g., 'ST', '胃经', 'Stomach', 'GV', '督脉', '任脉')"},
    usage_guide="When exploring acupoints along a specific meridian or extraordinary vessel.",
)
def by_meridian(meridian: str) -> dict:
    """List acupoints on a given meridian/channel."""
    q = meridian.strip().lower()
    matched_code = None
    for ch_code, ch_meta in CHANNEL_INDEX.items():
        if (
            q == ch_code.lower()
            or q in ch_meta["aliases"]
            or any(a in q for a in ch_meta["aliases"] if len(a) >= 2)
        ):
            matched_code = ch_code
            break

    if not matched_code:
        return {
            "status": "not_found",
            "message": f"Meridian '{meridian}' not recognized. Supported channels: {list(CHANNEL_INDEX.keys())}.",
        }

    ch_info = CHANNEL_INDEX[matched_code]
    points = [pt for pt in ACUPOINT_DB.values() if pt["channel_code"] == matched_code]
    five_elem_meta = MERIDIAN_DB.get(ch_info["short_cn"])

    return {
        "status": "found",
        "channel_code": matched_code,
        "meridian_chinese": ch_info["chinese"],
        "meridian_english": ch_info["english"],
        "five_element_metadata": five_elem_meta,
        "count": len(points),
        "acupoints": points,
    }


@registry.register(
    name="acupuncture.protocol",
    description=(
        "Generate an evidence-grounded classical acupuncture & moxibustion point prescription "
        "(针灸处方) for a condition or TCM syndrome, including primary/supplemental points, "
        "reinforcing/reducing technique (补泻/艾灸), classical pairing rationale (e.g., 四关穴 LI4+LR3), "
        "and automatic filtering of pregnancy-forbidden points when pregnancy_safe=True."
    ),
    category="acupuncture",
    parameters={
        "condition_or_syndrome": "Clinical condition or TCM syndrome (e.g., '肝气郁结', 'insomnia', 'migraine', '胃痛')",
        "pregnancy_safe": "Boolean: if True, strips pregnancy-forbidden points (LI4, SP6, BL60, BL67, CV4, CV6, ST25, CV12) and substitutes safe gestational alternatives",
    },
    usage_guide="When designing an acupuncture/moxibustion point protocol or checking gestational acupuncture safety.",
)
def protocol(condition_or_syndrome: str, pregnancy_safe: bool = False) -> dict:
    """Build clinical acupuncture point prescription with optional pregnancy safety filtering."""
    q = condition_or_syndrome.strip().lower()
    if not q:
        return {
            "status": "not_found",
            "message": "Please provide a clinical condition or TCM syndrome.",
        }

    best_proto = None
    best_hits = 0
    for proto in CLINICAL_PROTOCOLS:
        hits = sum(1 for kw in proto["keywords"] if kw.lower() in q or q in kw.lower())
        if hits > best_hits:
            best_hits = hits
            best_proto = proto

    if best_proto is None:
        # Dynamic fallback searches ACUPOINT_DB indications directly
        matched_pts = [
            code for code, pt in ACUPOINT_DB.items()
            if any(q in ind.lower() or q in act.lower() for ind in pt["indications"] for act in pt["actions"])
        ]
        if not matched_pts:
            matched_pts = ["ST36", "PC6", "HT7", "GV20"]
        best_proto = {
            "name": f"辨证随症取穴方案: {condition_or_syndrome}",
            "primary_points": matched_pts[:3],
            "supplemental_points": matched_pts[3:6] or ["ST36"],
            "safe_pregnancy_substitutes": ["PC6", "ST36", "HT7"],
            "technique": "毫针平补平泻，虚补实泻，得气后留针 20-30 分钟。",
            "pairing_rationale": "远近配穴与循经取穴结合，调和脏腑气血阴阳。",
        }

    primary_codes = list(best_proto["primary_points"])
    supp_codes = list(best_proto["supplemental_points"])
    filtered_out: list[dict] = []

    if pregnancy_safe:
        kept_primary: list[str] = []
        for c in primary_codes:
            if c in PREGNANCY_FORBIDDEN_POINTS or ACUPOINT_DB.get(c, {}).get("pregnancy_safety") == "contraindicated":
                filtered_out.append({
                    "code": c,
                    "chinese_name": ACUPOINT_DB[c]["chinese_name"] if c in ACUPOINT_DB else c,
                    "reason": PREGNANCY_FORBIDDEN_POINTS.get(c, "Contraindicated in pregnancy"),
                })
            else:
                kept_primary.append(c)

        kept_supp: list[str] = []
        for c in supp_codes:
            if c in PREGNANCY_FORBIDDEN_POINTS or ACUPOINT_DB.get(c, {}).get("pregnancy_safety") == "contraindicated":
                if not any(f["code"] == c for f in filtered_out):
                    filtered_out.append({
                        "code": c,
                        "chinese_name": ACUPOINT_DB[c]["chinese_name"] if c in ACUPOINT_DB else c,
                        "reason": PREGNANCY_FORBIDDEN_POINTS.get(c, "Contraindicated in pregnancy"),
                    })
            else:
                kept_supp.append(c)

        for sub in best_proto.get("safe_pregnancy_substitutes", []):
            if sub not in kept_primary and sub not in kept_supp and sub not in PREGNANCY_FORBIDDEN_POINTS:
                kept_primary.append(sub)

        primary_codes = kept_primary
        supp_codes = kept_supp

    def _hydrate(codes: list[str]) -> list[dict]:
        out = []
        for c in codes:
            pt = ACUPOINT_DB.get(c)
            if pt:
                out.append({
                    "code": c,
                    "name": f"{pt['chinese_name']} ({pt['pinyin']})",
                    "chinese_name": pt["chinese_name"],
                    "pinyin": pt["pinyin"],
                    "meridian": pt["meridian"],
                    "role": pt["actions"][0] if pt["actions"] else "",
                    "location": pt["location"],
                    "needling": pt["needling"],
                    "pregnancy_safety": pt["pregnancy_safety"],
                })
        return out

    technique_note = best_proto["technique"]
    if pregnancy_safe:
        technique_note += " 【妊娠安全模式已启用】已剔除全部妊娠禁针及小腹穴位，手法宜轻柔温和，忌强刺激提插重泻及腰骶电针。"

    hydrated_primary = _hydrate(primary_codes)
    hydrated_supp = _hydrate(supp_codes)

    return {
        "status": "complete",
        "query": condition_or_syndrome,
        "condition": condition_or_syndrome,
        "protocol_name": best_proto["name"],
        "pregnancy_safe": pregnancy_safe,
        "pregnancy_safe_mode": pregnancy_safe,
        "primary_points": hydrated_primary,
        "supplemental_points": hydrated_supp,
        "points": hydrated_primary + hydrated_supp,
        "technique_and_moxibustion": technique_note,
        "classical_pairing_rationale": best_proto["pairing_rationale"],
        "filtered_pregnancy_forbidden_points": filtered_out,
    }
