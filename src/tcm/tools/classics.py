"""
Classical TCM Canons & Materia Medica Monographs (中医四大经典与历代本草文献库):
Authentic bilingual passages and clause-level lookup across Huangdi Neijing (黄帝内经),
Shanghan Lun (伤寒论), Jin Gui Yao Lue (金匮要略), Shennong Bencao Jing (神农本草经),
Wenbing Tiaobian (温病条辨), Pi Wei Lun (脾胃论), and Bencao Gangmu (本草纲目).
"""
from __future__ import annotations

import logging
import re

from tcm.tools import registry
from tcm.tools.herbs import _search_herb
from tcm.tools.safety import toxicity_check

logger = logging.getLogger("tcm.tools.classics")


BOOK_ALIASES: dict[str, list[str]] = {
    "黄帝内经": ["黄帝内经", "内经", "素问", "灵枢", "huangdi neijing", "neijing", "suwen", "lingshu"],
    "伤寒论": ["伤寒论", "伤寒杂病论", "shanghan lun", "shanghan", "treatise on cold damage"],
    "金匮要略": ["金匮要略", "金匮", "jin gui yao lue", "jingui", "essential prescriptions of the golden cabinet"],
    "神农本草经": ["神农本草经", "本经", "shennong bencao jing", "shennong", "divine farmer"],
    "温病条辨": ["温病条辨", "温病", "wenbing tiaobian", "wenbing", "warm diseases"],
    "脾胃论": ["脾胃论", "pi wei lun", "piweilun", "treatise on the spleen and stomach"],
    "本草纲目": ["本草纲目", "纲目", "bencao gangmu", "gangmu", "compendium of materia medica"],
}


# ─── Curated Bilingual Corpus of 26 Foundational Passages & Clauses ──────────────

CLASSICS_CORPUS: list[dict] = [
    # 1. 黄帝内经 (Huangdi Neijing — Suwen & Lingshu)
    {
        "id": "HDNJ-SW01",
        "clause_numbers": ["1", "72", "SW1", "SW72"],
        "book": "黄帝内经",
        "sub_book": "素问・上古天真论 / 刺法论 (Suwen Ch. 1 & 72)",
        "dynasty_author": "战国至秦汉 (Warring States - Qin/Han Medical Canon)",
        "title": "正气存内，邪不可干 (Righteous Qi Prevents Pathogenic Intrusion)",
        "chinese_text": "虚邪贼风，避之有时，恬惔虚无，真气从之，精神内守，病安从来……正气存内，邪不可干；邪之所凑，其气必虚。",
        "english_translation": (
            "Avoid seasonal pathogenic winds in timely fashion; remain tranquil and free of excessive "
            "craving so Genuine Qi follows naturally and Spirit is guarded within—whence could disease "
            "arise? When Righteous Qi (Zheng Qi) resides abundantly within, pathogenic factors cannot "
            "invade; wherever pathogens congregate, Righteous Qi must first be deficient."
        ),
        "clinical_significance": "奠定中医发病学与扶正祛邪总纲，揭示机体免疫稳态（正气）在疾病预防与转归中的决定作用。",
        "tags": ["正气存内", "邪不可干", "扶正祛邪", "免疫", "养生", "zheng qi", "immunity", "prevention"],
        "related_formulas": ["玉屏风散", "四君子汤", "补中益气汤"],
    },
    {
        "id": "HDNJ-SW02",
        "clause_numbers": ["2", "SW2"],
        "book": "黄帝内经",
        "sub_book": "素问・四气调神大论 (Suwen Ch. 2)",
        "dynasty_author": "战国至秦汉",
        "title": "圣人不治已病治未病・春夏养阳秋冬养阴 (Preventive Medicine & Four-Season Cultivation)",
        "chinese_text": (
            "夫四时阴阳者，万物之根本也。所以圣人春夏养阳，秋冬养阴，以从其根……"
            "是故圣人不治已病治未病，不治已乱治未乱，此之谓也。夫病已成而后药之，乱已成而后治之，譬犹渴而穿井，斗而铸锥，不亦晚乎！"
        ),
        "english_translation": (
            "The Yin and Yang of the four seasons are the root of the myriad things. Therefore the sage "
            "nourishes Yang in spring and summer, and nourishes Yin in autumn and winter, following the "
            "root... Hence the sage treats not disease already formed, but treats pre-disease (Zhi Wei Bing). "
            "Administering medicine only after illness has developed is like digging a well after becoming "
            "thirsty or forging weapons after battle has begun—is that not too late?"
        ),
        "clinical_significance": "确立中医『上工治未病』（未病先防、既病防变、瘥后防复）三级预防体系及顺应四时时间医学原则。",
        "tags": ["上工治未病", "治未病", "四气调神", "春夏养阳", "秋冬养阴", "preventive medicine", "circadian", "seasons"],
        "related_formulas": [],
    },
    {
        "id": "HDNJ-SW05",
        "clause_numbers": ["5", "SW5"],
        "book": "黄帝内经",
        "sub_book": "素问・阴阳应象大论 (Suwen Ch. 5)",
        "dynasty_author": "战国至秦汉",
        "title": "阴阳总纲与气味药理 (Yin-Yang Ontology & Four-Nature Five-Flavor Pharmacology)",
        "chinese_text": (
            "阴阳者，天地之道也，万物之纲纪，变化之父母，生杀之本始，神明之府也，治病必求于本……"
            "阴静阳躁，阳生阴长，阳杀阴藏。阳化气，阴成形……味厚者为阴，薄为阴之阳；气厚者为阳，薄为阳之阴。辛甘发散为阳，酸苦涌泄为阴。"
        ),
        "english_translation": (
            "Yin and Yang are the Way of heaven and earth, the governing rubric of all things, the parents "
            "of transformation, the origin of life and death... In treating disease, one must seek the "
            "root (Yin-Yang). Yang transforms Qi while Yin shapes physical form. Acrid and sweet disperse "
            "and pertain to Yang; sour and bitter drain and pertain to Yin."
        ),
        "clinical_significance": "确立『治病必求于本』临床总则，并奠定中药气味阴阳升降浮沉药理学基础。",
        "tags": ["阴阳应象大论", "治病必求于本", "阳化气阴成形", "辛甘发散为阳", "yin yang", "pharmacology"],
        "related_formulas": ["桂枝汤", "六味地黄丸", "肾气丸"],
    },
    {
        "id": "HDNJ-SW08",
        "clause_numbers": ["8", "SW8", "SW9"],
        "book": "黄帝内经",
        "sub_book": "素问・灵兰秘典论 & 六节藏象论 (Suwen Ch. 8 & 9)",
        "dynasty_author": "战国至秦汉",
        "title": "十二脏腑藏象学说 (Zang-Fu Visceral Manifestation Doctrine)",
        "chinese_text": (
            "心者，君主之官也，神明出焉。肺者，相傅之官，治节出焉。肝者，将军之官，谋虑出焉。"
            "胆者，中正之官，决断出焉……脾胃者，仓廪之官，五味出焉……肾者，作强之官，伎巧出焉。"
        ),
        "english_translation": (
            "The Heart is the Sovereign Monarch whence Spirit-Brilliance (Shenming) issues. The Lung is "
            "the Chancellor whence rhythmic regulation issues. The Liver is the General whence strategic "
            "planning issues. The Gallbladder is the Just Official whence decision issues. The Spleen and "
            "Stomach are the Granary Officials whence the five flavors are distributed. The Kidney is the "
            "Official of Vigor whence skill and endurance issue."
        ),
        "clinical_significance": "构建中医藏象学说生理核心模型，阐明心主神明、肺主治节、肝主疏泄、脾主运化、肾藏精之协同关系。",
        "tags": ["藏象学说", "灵兰秘典论", "君主之官", "仓廪之官", "zang-fu", "visceral manifestation"],
        "related_formulas": ["天王补心丹", "四君子汤", "逍遥散"],
    },
    {
        "id": "HDNJ-LS10",
        "clause_numbers": ["10", "LS10"],
        "book": "黄帝内经",
        "sub_book": "灵枢・经脉篇 (Lingshu Ch. 10)",
        "dynasty_author": "战国至秦汉",
        "title": "经脉决死生调虚实 (Meridians Determine Life/Death and Regulate Deficiency/Excess)",
        "chinese_text": "经脉者，所以能决死生，处百病，调虚实，不可不通。盛则泻之，虚则补之，热则疾之，寒则留之，陷下则灸之。",
        "english_translation": (
            "The meridians are that by which life and death are determined, the hundred diseases treated, "
            "and deficiency and excess regulated—they must never remain obstructed. Drain excess, tonify "
            "deficiency, needle swiftly in heat, retain in cold, and apply moxibustion when Qi sinks."
        ),
        "clinical_significance": "针灸经络学与补泻灸法之最高总纲。",
        "tags": ["灵枢", "经脉", "盛则泻之", "虚则补之", "陷下则灸之", "meridian", "acupuncture", "moxibustion"],
        "related_formulas": [],
    },

    # 2. 伤寒论 (Shanghan Lun — Zhang Zhongjing)
    {
        "id": "SHL-001",
        "clause_numbers": ["1", "条文1", "第1条"],
        "book": "伤寒论",
        "sub_book": "辨太阳病脉证并治上・第1条 (Taiyang Disease Clause 1)",
        "dynasty_author": "东汉・张仲景 (Zhang Zhongjing, ~200 CE)",
        "title": "太阳病提纲 (Outline Clause of Taiyang Syndrome)",
        "chinese_text": "太阳之为病，脉浮，头项强痛而恶寒。",
        "english_translation": (
            "In Taiyang disease, the pulse is floating, there is stiffness and pain of the head and nape, "
            "and aversion to cold."
        ),
        "clinical_significance": "六经辨证首条提纲：邪袭肌表卫阳，正气抗邪于外则脉浮，太阳经脉循头项受阻则强痛，卫阳被遏则必恶寒（『有一分恶寒，便有一分表证』）。",
        "tags": ["太阳病", "脉浮", "头项强痛", "恶寒", "表证", "taiyang", "floating pulse", "chills"],
        "related_formulas": ["桂枝汤", "麻黄汤", "葛根汤"],
    },
    {
        "id": "SHL-012",
        "clause_numbers": ["12", "条文12", "第12条"],
        "book": "伤寒论",
        "sub_book": "辨太阳病脉证并治上・第12条 (Clause 12)",
        "dynasty_author": "东汉・张仲景",
        "title": "桂枝汤证——群方之冠调和营卫 (Guizhi Tang — Sovereign Formula Harmonizing Ying & Wei)",
        "chinese_text": (
            "太阳中风，阳浮而阴弱，阳浮者，热自发；阴弱者，汗自出。啬啬恶寒，淅淅恶风，翕翕发热，鼻鸣干呕者，桂枝汤主之。"
            "【方组】桂枝三两（去皮），芍药三两，甘草二两（炙），生姜三两（切），大枣十二枚（擘）。服已须臾，啜热稀粥一升余，以助药力，温覆令一时许，遍身漐漐微似有汗者益佳。"
        ),
        "english_translation": (
            "In Taiyang wind-strike, Yang is floating and Yin is weak: floating Yang manifests as spontaneous "
            "fever, weak Yin as spontaneous sweating, with shivering chills, aversion to wind, gentle fever, "
            "nasal snuffling, and dry retching—Guizhi Decoction governs it. Sip hot thin rice porridge "
            "shortly after taking to aid the medicine and warm-cover for mild generalized perspiration."
        ),
        "clinical_significance": "尊为『群方之冠』，创辛甘化阳（桂枝甘草）与酸甘化阴（芍药甘草）双向调和营卫阴阳之法度，并详载药后啜粥微汗护理规范。",
        "tags": ["桂枝汤", "太阳中风", "汗出恶风", "调和营卫", "啜热稀粥", "guizhi tang", "sweating"],
        "related_formulas": ["桂枝汤"],
    },
    {
        "id": "SHL-035",
        "clause_numbers": ["35", "条文35", "第35条"],
        "book": "伤寒论",
        "sub_book": "辨太阳病脉证并治中・第35条 (Clause 35)",
        "dynasty_author": "东汉・张仲景",
        "title": "麻黄汤证——太阳伤寒表实无汗而喘 (Mahuang Tang — Exterior Excess Cold with Dyspnea)",
        "chinese_text": (
            "太阳病，头痛发热，身疼腰痛，骨节疼痛，恶风，无汗而喘者，麻黄汤主之。"
            "【方组】麻黄三两（去节，先煮去上沫），桂枝二两（去皮），甘草一两（炙），杏仁七十个（去皮尖）。"
        ),
        "english_translation": (
            "In Taiyang disease with headache, fever, body aches, lumbar pain, generalized joint pain, "
            "aversion to wind, absence of sweating, and wheezing/dyspnea—Mahuang Decoction governs it."
        ),
        "clinical_significance": "外感风寒表实证代表方：寒邪束表、卫闭营郁、肺气不宣（麻桂相须开表发汗，麻杏一宣一降平喘）。",
        "tags": ["麻黄汤", "太阳伤寒", "无汗而喘", "身疼腰痛", "辛温峻汗", "mahuang tang", "ephedra"],
        "related_formulas": ["麻黄汤"],
    },
    {
        "id": "SHL-096",
        "clause_numbers": ["96", "条文96", "第96条"],
        "book": "伤寒论",
        "sub_book": "辨太阳病脉证并治中・第96条 (Clause 96)",
        "dynasty_author": "东汉・张仲景",
        "title": "小柴胡汤证——和解少阳枢机总方 (Xiao Chaihu Tang — Harmonizing the Shaoyang Pivot)",
        "chinese_text": (
            "伤寒五六日中风，往来寒热，胸胁苦满，嘿嘿不欲饮食，心烦喜呕，或胸中烦而不呕，或渴，或腹中痛，或胁下痞硬，或心下悸、小便不利，或不渴、身有微热，或咳者，小柴胡汤主之。"
            "【第101条补义】伤寒中风，有柴胡证，但见一证便是，不必悉具。"
        ),
        "english_translation": (
            "Five or six days after cold damage or wind-strike, if there are alternating chills and fever, "
            "fullness and discomfort in the chest and hypochondrium, taciturnity with no desire to eat, "
            "vexation and frequent nausea—or any of the seven optional symptoms—Minor Bupleurum Decoction "
            "(Xiao Chaihu Tang) governs it. Seeing even one cardinal Chaihu sign suffices; not all need be present."
        ),
        "clinical_significance": "少阳半表半里和解法之祖方：柴芩透泄少阳胆热，姜夏和胃降逆，参草枣扶正防邪内传，广泛应用于发热、肝胆脾胃及情志诸疾。",
        "tags": ["小柴胡汤", "往来寒热", "胸胁苦满", "和解少阳", "但见一证便是", "xiao chaihu tang", "shaoyang"],
        "related_formulas": ["小柴胡汤", "大柴胡汤", "柴胡桂枝汤"],
    },
    {
        "id": "SHL-154",
        "clause_numbers": ["154", "条文154", "第154条"],
        "book": "伤寒论",
        "sub_book": "辨太阳病脉证并治下・第154条 (Clause 154)",
        "dynasty_author": "东汉・张仲景",
        "title": "大黄黄连泻心汤证——无形邪热心下痞 (Dahuang Huanglian Xiexin Tang — Epigastric Pi Focal Distension)",
        "chinese_text": (
            "心下痞，按之濡，其脉关上浮者，大黄黄连泻心汤主之。"
            "【煎法精义】大黄二两，黄连一两，以麻沸汤二升渍之须臾，绞去滓，分温再服。"
        ),
        "english_translation": (
            "For focal distension below the heart (epigastric Pi) that feels soft upon palpation and "
            "presents with a floating pulse at the Guan position, Dahuang Huanglian Xiexin Decoction "
            "governs it—steeped briefly in boiling water (Mafei Tang) rather than prolonged boiling."
        ),
        "clinical_significance": "辨别有形结胸（硬满痛拒按）与无形热痞（按之濡软不痛）：特创『麻沸汤渍服』取其轻清苦寒之气以泄上中焦无形邪热，而不取重浊峻下之味。",
        "tags": ["大黄黄连泻心汤", "心下痞", "按之濡", "麻沸汤", "泻心汤", "epigastric fullness"],
        "related_formulas": ["大黄黄连泻心汤", "半夏泻心汤"],
    },
    {
        "id": "SHL-177",
        "clause_numbers": ["177", "条文177", "第177条"],
        "book": "伤寒论",
        "sub_book": "辨太阳病脉证并治下・第177条 (Clause 177)",
        "dynasty_author": "东汉・张仲景",
        "title": "炙甘草汤证——脉结代心动悸 (Zhigancao Tang — Arrhythmia with Knotted/Intermittent Pulse)",
        "chinese_text": (
            "伤寒脉结代，心动悸，炙甘草汤主之。"
            "【方组】甘草四两（炙），生姜三两，人参二两，生地黄一斤，桂枝三两，阿胶二两，麦门冬半升，麻仁半升，大枣三十枚；以清酒七升、水八升煮，烊阿胶尽服。"
        ),
        "english_translation": (
            "In cold damage presenting with a knotted (Jie) or intermittent (Dai) pulse and palpitations "
            "of the Heart—Honey-Fried Licorice Decoction (Zhigancao Tang /复脉汤) governs it."
        ),
        "clinical_significance": "中医治疗心律失常（房早、室早、传导阻滞）之千古名方，重用生地一斤、炙甘草四两配清酒通脉，益气滋阴、通阳复脉并举。",
        "tags": ["炙甘草汤", "复脉汤", "脉结代", "心动悸", "心律失常", "arrhythmia", "palpitations", "zhigancao tang"],
        "related_formulas": ["炙甘草汤"],
    },
    {
        "id": "SHL-281",
        "clause_numbers": ["281", "323", "条文281", "第281条"],
        "book": "伤寒论",
        "sub_book": "辨少阴病脉证并治・第281条 & 第323条 (Shaoyin Disease Clause 281 & 323)",
        "dynasty_author": "东汉・张仲景",
        "title": "少阴病提纲与四逆汤回阳救逆 (Shaoyin Outline: Faint-Fine Pulse & Somnolence)",
        "chinese_text": "少阴之为病，脉微细，但欲寐也。（第323条：少阴病，脉沉者，急温之，宜四逆汤。）",
        "english_translation": (
            "In Shaoyin disease, the pulse is faint and thready (Wei-Xi), and the patient desires only "
            "to sleep (lethargic somnolence). When the Shaoyin pulse is deep, warm it urgently with Sini Tang."
        ),
        "clinical_significance": "心肾阳虚、阴寒内盛之全身性衰竭提纲：心肾真阳衰微鼓动无力则脉微，营血不足则脉细，阳虚神失温养则精神萎靡似睡非睡，急用附子干姜炙甘草回阳救逆。",
        "tags": ["少阴病", "脉微细", "但欲寐", "四逆汤", "回阳救逆", "shaoyin", "sini tang", "yang collapse"],
        "related_formulas": ["四逆汤", "真武汤"],
    },
    {
        "id": "SHL-318",
        "clause_numbers": ["318", "条文318", "第318条"],
        "book": "伤寒论",
        "sub_book": "辨少阴病脉证并治・第318条 (Clause 318)",
        "dynasty_author": "东汉・张仲景",
        "title": "四逆散证——阳郁厥逆疏肝理脾祖方 (Sini San — Yang Qi Stagnation Cold Limbs)",
        "chinese_text": (
            "少阴病，四逆，其人或咳，或悸，或小便不利，或腹中痛，或泄利下重者，四逆散主之。"
            "【方组】甘草（炙）、枳实（破，水渍炙干）、柴胡、芍药各十分，捣筛白饮和服方寸匕。"
        ),
        "english_translation": (
            "In Shaoyin disease with coldness of the four limbs (from internal Qi constraint rather than "
            "Yang collapse), possibly accompanied by cough, palpitations, dysuria, abdominal pain, or "
            "diarrhea with tenesmus—Frigid Extremities Powder (Sini San) governs it."
        ),
        "clinical_significance": "鉴别阳衰寒厥（四逆汤）与气机郁遏阳不达四末之『气厥/热厥』（四逆散）；后世柴胡疏肝散、逍遥散皆胎息于此方。",
        "tags": ["四逆散", "阳郁四逆", "疏肝理脾", "泄利下重", "sini san", "liver stagnation"],
        "related_formulas": ["四逆散", "柴胡疏肝散", "逍遥散"],
    },

    # 3. 金匮要略 (Jin Gui Yao Lue — Zhang Zhongjing)
    {
        "id": "JGYL-06-15",
        "clause_numbers": ["JG15", "6-15", "肾气丸"],
        "book": "金匮要略",
        "sub_book": "血痹虚劳病脉证并治第六・第15条",
        "dynasty_author": "东汉・张仲景",
        "title": "八味肾气丸——阴中求阳少火生气 (Shenqi Wan — Seeking Yang Within Yin)",
        "chinese_text": (
            "虚劳腰痛，少腹拘急，小便不利者，八味肾气丸主之。（亦主男子消渴，小便反多，以饮一斗，小便一斗。）"
            "【方组】干地黄八两，山药、山茱萸各四两，泽泻、牡丹皮、茯苓各三两，桂枝、附子（炮）各一两。"
        ),
        "english_translation": (
            "For consumptive deficiency (Xulao) with lumbar pain, cramping tension in the lower abdomen, "
            "and dysuria (or wasting-thirst polyuria)—Eight-Ingredient Kidney Qi Pill (Shenqi Wan) governs it."
        ),
        "clinical_significance": "温补肾阳祖方：于大队滋阴药（地黄山萸山药）中仅入桂附各一两，旨在『微微生火以生肾气』（少火生气）而非峻燥劫阴；钱乙减桂附即化裁为六味地黄丸。",
        "tags": ["肾气丸", "金匮肾气丸", "八味丸", "虚劳腰痛", "消渴", "少火生气", "shenqi wan", "kidney yang"],
        "related_formulas": ["肾气丸", "六味地黄丸"],
    },
    {
        "id": "JGYL-06-17",
        "clause_numbers": ["JG17", "6-17", "酸枣仁汤"],
        "book": "金匮要略",
        "sub_book": "血痹虚劳病脉证并治第六・第17条",
        "dynasty_author": "东汉・张仲景",
        "title": "酸枣仁汤——虚劳虚烦不得眠 (Suanzaoren Tang — Consumptive Vexation & Insomnia)",
        "chinese_text": (
            "虚劳虚烦不得眠，酸枣仁汤主之。"
            "【方组】酸枣仁二升，甘草一两，知母二两，茯苓二两，川芎二两；先煮酸枣仁，纳诸药再煮。"
        ),
        "english_translation": (
            "For consumptive deficiency with deficiency-vexation and inability to sleep, Sour Jujube "
            "Decoction (Suanzaoren Tang) governs it."
        ),
        "clinical_significance": "治肝血不足、虚热扰神不寐第一经方：重用酸枣仁酸甘养肝血安心神，配川芎辛散调畅肝气（酸收辛散相成），知母清虚热，茯苓甘草宁心健脾。",
        "tags": ["酸枣仁汤", "虚烦不得眠", "失眠", "养血安神", "suanzaoren tang", "insomnia"],
        "related_formulas": ["酸枣仁汤"],
    },
    {
        "id": "JGYL-22-05",
        "clause_numbers": ["JG22-5", "22-5", "半夏厚朴汤"],
        "book": "金匮要略",
        "sub_book": "妇人杂病脉证并治第二十二・第5条",
        "dynasty_author": "东汉・张仲景",
        "title": "半夏厚朴汤——妇人咽中如有炙脔（梅核气） (Banxia Houpo Tang — Plum-Pit Qi Globus)",
        "chinese_text": (
            "妇人咽中如有炙脔，半夏厚朴汤主之。"
            "【方组】半夏一升，厚朴三两，茯苓四两，生姜五两，干苏叶二两。"
        ),
        "english_translation": (
            "When a woman feels as if a piece of roasted meat is stuck in her throat (neither swallowed "
            "down nor coughed up)—Pinellia and Magnolia Bark Decoction (Banxia Houpo Tang) governs it."
        ),
        "clinical_significance": "痰气互结之『梅核气』（现代咽异感症、焦虑躯体化障碍）专方，开创辛开苦降、行气散结化痰并治情志郁结之范式。",
        "tags": ["半夏厚朴汤", "咽中如有炙脔", "梅核气", "痰气互结", "banxia houpo tang", "globus"],
        "related_formulas": ["半夏厚朴汤"],
    },
    {
        "id": "JGYL-20-05",
        "clause_numbers": ["JG20-5", "20-5", "当归芍药散"],
        "book": "金匮要略",
        "sub_book": "妇人妊娠病脉证并治第二十・第5条",
        "dynasty_author": "东汉・张仲景",
        "title": "当归芍药散——肝脾血虚湿滞腹痛 (Danggui Shaoyao San — Blood-Spleen Disharmony)",
        "chinese_text": (
            "妇人怀妊，腹中㽲痛，当归芍药散主之。（亦主妇人腹中诸疾痛。）"
            "【方组】当归三两，芍药一斤，茯苓四两，白术四两，泽泻半斤，川芎半斤（杵为散）。"
        ),
        "english_translation": (
            "For cramping abdominal pain during pregnancy (and all gynecological abdominal pains from "
            "Liver Blood deficiency with Spleen dampness)—Danggui Shaoyao Powder governs it."
        ),
        "clinical_significance": "肝脾同调、血水并治代表方：重用芍药缓急养血柔肝，归芎和血，苓术泽健脾渗湿安胎，现代广用于痛经、黄褐斑、慢性盆腔痛及水肿。",
        "tags": ["当归芍药散", "腹中㽲痛", "血水同治", "调肝理脾", "danggui shaoyao san", "dysmenorrhea"],
        "related_formulas": ["当归芍药散"],
    },

    # 4. 神农本草经 (Shennong Bencao Jing — Three-Grade Materia Medica)
    {
        "id": "SNBCJ-00",
        "clause_numbers": ["序录", "三品", "PREFACE"],
        "book": "神农本草经",
        "sub_book": "序录・三品分类法 (General Preface — Three Grades)",
        "dynasty_author": "秦汉辑成（现存最早本草经典）",
        "title": "上中下三品君臣佐使总论 (Superior, Middle, and Inferior Herbal Grades)",
        "chinese_text": (
            "上药一百二十种为君，主养命以应天，无毒，多服久服不伤人，欲轻身益气不老延年者本上经；"
            "中药一百二十种为臣，主养性以应人，无毒有毒，斟酌其宜；"
            "下药一百二十五种为佐使，主治病以应地，多毒，不可久服，欲除寒热邪气、破积聚愈疾者本下经。"
        ),
        "english_translation": (
            "120 Superior-grade medicinals act as Sovereigns to nourish life, non-toxic and safe for "
            "long-term use; 120 Middle-grade medicinals act as Ministers to cultivate constitutional "
            "nature, toxic or non-toxic requiring measured judgment; 125 Inferior-grade medicinals act "
            "as Assistants/Envoys to attack disease and break accumulations—often toxic and not to be "
            "taken protractedly."
        ),
        "clinical_significance": "中国药学史上最早药物毒理分级与君臣佐使配伍纲领，严明补益养生药（上品）与攻邪有毒药（下品中病即止）之界限。",
        "tags": ["三品", "上品", "中品", "下品", "君臣佐使", "毒理", "three grades", "toxicity"],
        "related_formulas": [],
    },
    {
        "id": "SNBCJ-RENSHEN",
        "clause_numbers": ["人参", "RENSHEN"],
        "book": "神农本草经",
        "sub_book": "上品・草部 (Superior Grade)",
        "dynasty_author": "秦汉辑成",
        "title": "人参本经条文 (Ginseng Monograph in Shennong Bencao Jing)",
        "chinese_text": "人参，味甘微寒。主补五脏，安精神，定魂魄，止惊悸，除邪气，明目，开心益智。久服轻身延年。",
        "english_translation": (
            "Renshen (Ginseng): sweet and slightly cool/neutral. Mainly tonifies the Five Zang organs, "
            "quiets Essence and Spirit, settles Hun and Po, stops fright palpitations, eliminates "
            "pathogenic Qi through righteous support, brightens vision, opens the Heart, and benefits wisdom."
        ),
        "clinical_significance": "揭示人参大补五脏元气并具显著中枢安神益智作用，仲景于伤寒津伤气耗方中每奉为扶正中坚。",
        "tags": ["人参", "补五脏", "安精神", "开心益智", "上品", "ginseng"],
        "related_formulas": ["四君子汤", "小柴胡汤", "白虎加人参汤", "炙甘草汤"],
    },
    {
        "id": "SNBCJ-HUANGQI",
        "clause_numbers": ["黄芪", "黄耆", "HUANGQI"],
        "book": "神农本草经",
        "sub_book": "上品・草部 (Superior Grade)",
        "dynasty_author": "秦汉辑成",
        "title": "黄芪（黄耆）本经条文 (Astragalus Monograph in Shennong Bencao Jing)",
        "chinese_text": "黄耆，味甘微温。主痈疽，久败疮，排脓止痛，大风癞疾，五痔鼠瘘，补虚，小儿百病。",
        "english_translation": (
            "Huangqi (Astragalus): sweet and slightly warm. Governs carbuncles, chronic non-healing "
            "ulcers, drains pus and stops pain, treats wind-skin disorders, supplements deficiency, "
            "and addresses pediatric deficiency illnesses."
        ),
        "clinical_significance": "阐明黄芪既能补一身之气虚，又能走表托毒排脓敛疮（外科圣药），张仲景黄芪建中汤、黄芪桂枝五物汤与李东垣补中益气汤皆承此旨。",
        "tags": ["黄芪", "黄耆", "托毒排脓", "补虚", "上品", "astragalus"],
        "related_formulas": ["补中益气汤", "玉屏风散", "防己黄芪汤"],
    },
    {
        "id": "SNBCJ-GANCAO",
        "clause_numbers": ["甘草", "GANCAO"],
        "book": "神农本草经",
        "sub_book": "上品・草部 (Superior Grade)",
        "dynasty_author": "秦汉辑成",
        "title": "甘草（国老）本经条文 (Licorice Monograph in Shennong Bencao Jing)",
        "chinese_text": "甘草，味甘平。主五脏六腑寒热邪气，坚筋骨，长肌肉，倍力，金疮尰，解毒。久服轻身延年。",
        "english_translation": (
            "Gancao (Licorice): sweet and neutral. Governs cold and heat pathogenic Qi across all Five "
            "Zang and Six Fu organs, strengthens sinews and bones, builds flesh, doubles strength, treats "
            "incised-wound swelling, and resolves toxins."
        ),
        "clinical_significance": "陶弘景尊为『国老』，通行十二经、解百药毒、调和诸药寒热刚柔，炙用温中复脉，生用清火解毒。",
        "tags": ["甘草", "国老", "解毒", "调和诸药", "上品", "licorice"],
        "related_formulas": ["炙甘草汤", "芍药甘草汤", "甘草泻心汤"],
    },
    {
        "id": "SNBCJ-HUANGLIAN",
        "clause_numbers": ["黄连", "HUANGLIAN"],
        "book": "神农本草经",
        "sub_book": "上品・草部 (Superior Grade)",
        "dynasty_author": "秦汉辑成",
        "title": "黄连本经条文 (Coptis Monograph in Shennong Bencao Jing)",
        "chinese_text": "黄连，味苦寒。主热气，目痛眦伤泣出，明目，肠澼腹痛下痢，妇人阴中肿痛。",
        "english_translation": (
            "Huanglian (Coptis): bitter and cold. Governs pathogenic heat Qi, eye pain with injured "
            "canthi and tearing, brightens vision, treats dysenteric intestinal Griping and diarrhea "
            "(Changpi), and damp-heat vulvar swelling and pain."
        ),
        "clinical_significance": "千古治湿热泻痢（肠澼）与清心胃火毒之首药，与现代小檗碱抗菌抗炎调控肠道菌群高度契合。",
        "tags": ["黄连", "肠澼", "下痢", "苦寒清热", "明目", "coptis", "berberine"],
        "related_formulas": ["葛根芩连汤", "白头翁汤", "黄连解毒汤", "大黄黄连泻心汤"],
    },

    # 5. 温病条辨 (Wenbing Tiaobian — Wu Jutong)
    {
        "id": "WBTB-SJ04",
        "clause_numbers": ["4", "上焦4", "SJ4", "银翘散"],
        "book": "温病条辨",
        "sub_book": "卷一・上焦篇第4条 (Upper Jiao Clause 4)",
        "dynasty_author": "清・吴鞠通 (Wu Jutong, 1798)",
        "title": "银翘散——辛凉平剂透卫清热 (Yinqiao San — Acrid-Cool Standard Formula for Warm Disease)",
        "chinese_text": (
            "太阴风温、温热、温疫、冬温，初起恶风寒者，桂枝汤主之；但热不恶寒而渴者，辛凉平剂银翘散主之。"
            "【煎服戒律】香气大出，即取服，勿过煮。肺药取轻清，过煮则味厚而入中焦矣。"
        ),
        "english_translation": (
            "In Taiyin wind-warmth, warm-heat, warm-epidemic, or winter-warmth presenting with fever "
            "without chills (or slight transient chill) and thirst—the acrid-cool balanced formula "
            "Yinqiao San governs it. Decoct only briefly until full aroma emerges; do not over-boil, "
            "for Lung medicinals rely on light, clear volatility."
        ),
        "clinical_significance": "温病卫分证第一代表方，确立『治上焦如羽，非轻不举』及挥发性芳香透表药不可久煎之科学煎法准则。",
        "tags": ["银翘散", "温病", "风温", "辛凉平剂", "治上焦如羽", "勿过煮", "yinqiao san", "warm disease"],
        "related_formulas": ["银翘散"],
    },
    {
        "id": "WBTB-SJ06",
        "clause_numbers": ["6", "上焦6", "SJ6", "桑菊饮"],
        "book": "温病条辨",
        "sub_book": "卷一・上焦篇第6条 (Upper Jiao Clause 6)",
        "dynasty_author": "清・吴鞠通",
        "title": "桑菊饮——辛凉轻剂宣肺止咳 (Sangju Yin — Gentle Acrid-Cool Formula for Wind-Heat Cough)",
        "chinese_text": "太阴风温，但咳，身不甚热，微渴者，辛凉轻剂桑菊饮主之。",
        "english_translation": (
            "In Taiyin wind-warmth manifesting predominantly as cough, without high fever and with slight "
            "thirst—the gentle acrid-cool formula Mulberry Leaf and Chrysanthemum Drink (Sangju Yin) governs it."
        ),
        "clinical_significance": "风热犯肺轻证止咳专方：桑叶菊花清透肺络风热，杏仁桔梗一宣一降开提肺气。",
        "tags": ["桑菊饮", "辛凉轻剂", "风温咳嗽", "sangju yin", "cough"],
        "related_formulas": ["桑菊饮"],
    },
    {
        "id": "WBTB-SJ43",
        "clause_numbers": ["43", "上焦43", "SJ43", "三仁汤"],
        "book": "温病条辨",
        "sub_book": "卷一・上焦篇第43条 (Upper Jiao Clause 43)",
        "dynasty_author": "清・吴鞠通",
        "title": "三仁汤——分消走泄宣畅三焦湿温 (Sanren Tang — Three-Nut Decoction for Damp-Warmth)",
        "chinese_text": (
            "头痛恶寒，身重疼痛，舌白不渴，脉弦细而濡，面色淡黄，胸闷不饥，午后身热，状若阴虚，病难速已，名曰湿温。"
            "汗之则神昏耳聋……润之则病深不解，长夏深秋冬日同法，三仁汤主之。"
        ),
        "english_translation": (
            "Headache with chills, heavy aching body, white tongue without thirst, wiry-fine-soggy pulse, "
            "sallow complexion, chest oppression without hunger, and afternoon fever resembling Yin "
            "deficiency—this lingering illness is Damp-Warmth (Shiwen). Diaphoresis causes delirium and "
            "moistening deepens stagnation; Three-Nut Decoction (Sanren Tang:杏仁、白蔻仁、薏苡仁) governs it."
        ),
        "clinical_significance": "湿温初起湿重于热之圭臬：杏仁开上焦肺气、白蔻仁畅中焦脾气、薏苡仁渗下焦湿浊，并严明湿温三禁（禁汗、禁下、禁滋润）。",
        "tags": ["三仁汤", "湿温", "午后身热", "身重胸闷", "三焦分消", "sanren tang", "damp-heat"],
        "related_formulas": ["三仁汤"],
    },

    # 6. 脾胃论 & 本草纲目 (Pi Wei Lun — Li Dongyuan & Bencao Gangmu — Li Shizhen)
    {
        "id": "PWL-01",
        "clause_numbers": ["BZYQT", "补中益气汤", "1"],
        "book": "脾胃论",
        "sub_book": "卷中・饮食劳倦所伤始为热中论",
        "dynasty_author": "金元・李东垣 (Li Dongyuan, 1249)",
        "title": "补中益气汤——甘温除大热升阳举陷 (Buzhong Yiqi Tang — Sweet-Warm Medicinals Clearing Yin-Fire)",
        "chinese_text": (
            "内伤脾胃，乃伤其气……脾胃气衰，元气不足，而心火独盛。心火者，阴火也，起于下焦……"
            "惟当以辛甘温之剂，补其中而升其阳，甘寒以泻其火则愈，《内经》曰『劳者温之』『损者益之』，补中益气汤主之。"
        ),
        "english_translation": (
            "Internal damage to Spleen and Stomach injures Original Qi... When Spleen-Stomach Qi declines, "
            "pathological Yin-Fire surges upward. One must employ acrid-sweet-warm medicinals to supplement "
            "the Middle Jiao and raise clear Yang—thus 'warm the exhausted' with Buzhong Yiqi Tang."
        ),
        "clinical_significance": "补土派代表作，创立『甘温除热』与『升阳举陷』大法（黄芪参术草补中气，升麻柴胡引清阳上升）。",
        "tags": ["脾胃论", "李东垣", "补中益气汤", "甘温除热", "阴火", "中气下陷", "buzhong yiqi tang"],
        "related_formulas": ["补中益气汤"],
    },
    {
        "id": "BCGM-DANGGUI",
        "clause_numbers": ["当归", "DANGGUI", "三七"],
        "book": "本草纲目",
        "sub_book": "草部第十四卷・当归 & 第十二卷・三七纲目发明",
        "dynasty_author": "明・李时珍 (Li Shizhen, 1578)",
        "title": "李时珍本草纲目条辨：血家圣药当归与金疮要药三七 (Li Shizhen's Compendium Commentaries)",
        "chinese_text": (
            "【当归发明】古人娶妻为嗣续也，当归调血，为女人要药，有思夫之意，故有当归之名……头止血而上行，身养血而中守，梢破血而下流，全活血而不走。"
            "【三七发明】止血散血定痛，金刃箭伤、跌扑杖疮血出不止者，嚼烂涂或为末掺之即止；亦主吐血衄血下血，乃阳明厥阴血分之药，故能治一切血病。"
        ),
        "english_translation": (
            "[Danggui] Regulates Blood as the foremost gynecological medicinal: the head stops bleeding "
            "and ascends, the body nourishes Blood and abides in the center, the tail breaks stasis and "
            "descends, while the whole root activates Blood harmoniously. [Sanqi / Notoginseng] Stops "
            "bleeding, disperses stasis, and halts pain—entering the Yangming and Jueyin Blood aspect to "
            "govern all hemorrhagic and traumatic stasis disorders."
        ),
        "clinical_significance": "体现《本草纲目》正名、释名、集解、修治、气味、主治、发明、附方之严谨体例，奠定药用部位分用与活血止血双向调控理论。",
        "tags": ["本草纲目", "李时珍", "当归", "三七", "血家圣药", "止血散血", "li shizhen", "bencao gangmu"],
        "related_formulas": ["四物汤", "当归补血汤", "桃红四物汤"],
    },
]


# ─── Dedicated Classical Herb Monographs (历代本草专论汇总库) ─────────────────────

HERB_CLASSICAL_MONOGRAPHS: dict[str, dict] = {
    "人参": {
        "herb": "人参", "pinyin": "Rén Shēn", "english": "Ginseng",
        "shennong_grade": "上品 (Superior Grade — Sovereign)",
        "shennong_bencao_jing": "味甘微寒。主补五脏，安精神，定魂魄，止惊悸，除邪气，明目，开心益智。久服轻身延年。",
        "mingyi_bielu": "微温，无毒。主肠胃中冷，心腹鼓痛，胸胁逆满，霍乱吐逆，调中，消渴，通血脉，破坚积，令人不忘。",
        "bencao_gangmu": "李时珍曰：治男妇一切虚证，发热自汗，眩晕头痛，反胃吐食，滑泄久痢，小便频数淋沥，劳倦内伤，中风中暑，吐血嗽血下血，胎前产后诸病。",
        "zhongjing_classical_usage": "《伤寒》《金匮》共39方用人参（如四君子辈之祖理中汤、白虎加人参汤、小柴胡汤、半夏泻心汤、炙甘草汤），专用于津气两伤、心下痞硬、汗吐下后虚羸。",
    },
    "黄芪": {
        "herb": "黄芪", "pinyin": "Huáng Qí", "english": "Astragalus",
        "shennong_grade": "上品 (Superior Grade)",
        "shennong_bencao_jing": "黄耆，味甘微温。主痈疽，久败疮，排脓止痛，大风癞疾，五痔鼠瘘，补虚，小儿百病。",
        "mingyi_bielu": "主妇人子脏风邪气，逐五脏间恶血，补丈夫虚损，五劳羸瘦，止渴，腹痛泄利，益气，利阴气。",
        "bencao_gangmu": "李时珍曰：耆，长也。黄耆色黄，为补药之长，故名。入肺脾气分及三焦肌表，实卫固表、托疮生肌、升清阳。",
        "zhongjing_classical_usage": "张仲景用黄芪主治『汗出、身重、风水、血痹、虚劳』（防己黄芪汤、黄芪桂枝五物汤、黄芪建中汤）。",
    },
    "甘草": {
        "herb": "甘草", "pinyin": "Gān Cǎo", "english": "Licorice",
        "shennong_grade": "上品 (Superior Grade — 国老 National Elder)",
        "shennong_bencao_jing": "味甘平。主五脏六腑寒热邪气，坚筋骨，长肌肉，倍力，金疮尰，解毒。久服轻身延年。",
        "mingyi_bielu": "温中下气，烦满短气，伤脏咳嗽，止渴，通经脉，利血气，解百药毒。",
        "bencao_gangmu": "李时珍曰：甘草外赤中黄，色兼坤离，味浓气薄，生用气平泻火解毒，炙用气温补三焦元气而散表寒、缓正气。",
        "zhongjing_classical_usage": "《伤寒论》113方中70方用甘草！单味甘草汤治少阴咽痛，芍药甘草汤酸甘缓急，炙甘草汤复脉定悸，四逆汤缓姜附燥烈以护阴恋阳。",
    },
    "黄连": {
        "herb": "黄连", "pinyin": "Huáng Lián", "english": "Coptis",
        "shennong_grade": "上品 (Superior Grade)",
        "shennong_bencao_jing": "味苦寒。主热气，目痛眦伤泣出，明目，肠澼腹痛下痢，妇人阴中肿痛。",
        "mingyi_bielu": "微寒，无毒。主五脏冷热，久下泄澼脓血，止消渴，大惊，调胃厚肠益胆，疗口疮。",
        "bencao_gangmu": "李时珍曰：黄连治目及痢为要药。心火盛则用酒炒，胃热呕逆用姜汁炒，肝火郁痛用吴茱萸汤炒，下焦伏火用盐水炒。",
        "zhongjing_classical_usage": "仲景用黄连清上中下湿热痞利：大黄黄连泻心汤治热痞，半夏泻心汤辛开苦降，葛根芩连汤治协热下利，乌梅丸寒热并用安蛔止厥利。",
    },
    "当归": {
        "herb": "当归", "pinyin": "Dāng Guī", "english": "Chinese Angelica",
        "shennong_grade": "中品 (Middle Grade)",
        "shennong_bencao_jing": "味甘温。主咳逆上气，温疟寒热洗在皮肤中，妇人漏下绝子，诸恶疮疡金疮，煮饮之。",
        "mingyi_bielu": "辛，大温，无毒。温中止痛，除客血内塞，中风痉汗不出，湿痹中恶，补五脏，生肌肉。",
        "bencao_gangmu": "李时珍曰：当归调血，为女人要药。头止血而上行，身养血而中守，梢破血而下流，全活血而不走。",
        "zhongjing_classical_usage": "当归四逆汤养血通脉散寒，当归芍药散调肝脾血水，当归生姜羊肉汤温养产后虚寒腹痛，温经汤调冲任。",
    },
    "柴胡": {
        "herb": "柴胡", "pinyin": "Chái Hú", "english": "Bupleurum",
        "shennong_grade": "上品 (Superior Grade — 原名茈胡)",
        "shennong_bencao_jing": "味苦平。主心腹，去肠胃中结气，饮食积聚，寒热邪气，推陈致新。久服轻身明目益精。",
        "mingyi_bielu": "微寒，无毒。除伤寒心下烦热，诸痰热结实，胸中邪逆，五脏间游气。",
        "bencao_gangmu": "李时珍曰：柴胡乃手足少阳、厥阴四经行经之药。劳乏内伤、少阳寒热，引清气上升退热必用之。",
        "zhongjing_classical_usage": "小柴胡汤重用八两和解少阳往来寒热，大柴胡汤和解兼通阳明，四逆散疏透少阴郁阳。",
    },
    "白术": {
        "herb": "白术", "pinyin": "Bái Zhú", "english": "White Atractylodes",
        "shennong_grade": "上品 (Superior Grade — 《本经》名术，苍白未分)",
        "shennong_bencao_jing": "术，味苦温。主风寒湿痹死肌，痉疸，止汗，除热，消食。",
        "mingyi_bielu": "甘，无毒。主大风在身面，风眩头痛，消痰水，逐皮间风水结肿，除心下急满及霍乱吐下不止，利腰脐间血。",
        "bencao_gangmu": "李时珍曰：古方二术通用，陶弘景始分苍、白二种。白术甘温而性燥，健脾燥湿、安胎止汗之功胜。",
        "zhongjing_classical_usage": "五苓散、苓桂术甘汤、真武汤、理中汤皆倚术健脾崇土以制水饮。",
    },
    "茯苓": {
        "herb": "茯苓", "pinyin": "Fú Líng", "english": "Poria",
        "shennong_grade": "上品 (Superior Grade)",
        "shennong_bencao_jing": "味甘平。主胸胁逆气，忧恚惊邪恐悸，心下结痛，寒热烦满咳逆，口焦舌干，利小便。",
        "mingyi_bielu": "止消渴，好睡，大腹淋沥，膈中痰水，水肿淋结，开胸腑，调脏气，伐肾邪，长阴益气力，保神守中。",
        "bencao_gangmu": "李时珍曰：茯苓气味淡而渗，其性上行生津液、开腠理，下行利小便，故张洁古谓其属阳、浮而升，言其性也；东垣谓其为阳中之阴、降而下，言其功也。",
        "zhongjing_classical_usage": "治水饮眩悸核心药（『水停心下，甚者则悸，微者短气』）：苓桂术甘汤、茯苓甘草汤、五苓散、猪苓汤、真武汤。",
    },
    "附子": {
        "herb": "附子", "pinyin": "Fù Zǐ", "english": "Prepared Lateral Aconite Root",
        "shennong_grade": "下品 (Inferior Grade — 大毒/有毒，回阳猛将)",
        "shennong_bencao_jing": "味辛温。主风寒咳逆邪气，温中，金疮，破癥坚积聚，血瘕，寒湿踒躄拘挛膝痛不能行步。",
        "mingyi_bielu": "甘，大热，有大毒。主脚疼冷弱，腰脊风寒，心腹冷痛，霍乱转筋，下利赤白，强阴，坚肌骨，又堕胎，为百药长。",
        "bencao_gangmu": "李时珍曰：附子乃阴症要药，补下焦命门阳虚。生用则发散，熟用则峻补；必制熟先煎去麻毒，孕妇禁服。",
        "zhongjing_classical_usage": "张仲景生附子配干姜回阳救逆（四逆汤、通脉四逆汤），炮附子温阳固表止痛利水（桂枝加附子汤、真武汤、麻黄附子细辛汤、乌头桂枝汤）。",
    },
    "三七": {
        "herb": "三七", "pinyin": "Sān Qī", "english": "Notoginseng",
        "shennong_grade": "《本草纲目》始载（明代增补上品金疮圣药）",
        "shennong_bencao_jing": "《神农本草经》未载，始载于明・李时珍《本草纲目》。",
        "mingyi_bielu": "近世医家张锡纯《医学衷中参西录》推崇：『三七善化瘀血，又善止血妄行，病愈后不至瘀血留于经络证变虚劳，诚化瘀止血第一圣药。』",
        "bencao_gangmu": "味甘微苦，温，无毒。止血散血定痛，金刃箭伤、跌扑杖疮血出不止，亦主吐血衄血下血血痢崩中经水不止。",
        "zhongjing_classical_usage": "虽出汉后，今临床常冲服1.5-3g融合经方桃核承气汤、血府逐瘀汤或炙甘草汤调治冠心病胸痹及出血兼瘀证。",
    },
}


def _resolve_canonical_book(book_query: str) -> str | None:
    """Resolve user book query (Chinese, pinyin, or English) into canonical book title."""
    q = book_query.strip().lower().strip("《》<>")
    if not q:
        return None
    for canon_book, aliases in BOOK_ALIASES.items():
        if any(q == a or q in a or a in q for a in aliases):
            return canon_book
    return None


@registry.register(
    name="classics.search",
    description=(
        "Search foundational TCM classical canons (黄帝内经, 伤寒论, 金匮要略, 神农本草经, "
        "温病条辨, 脾胃论, 本草纲目) by Chinese or English keyword, concept, syndrome, or formula. "
        "Returns bilingual passages, dynasty/author attribution, and clinical commentary."
    ),
    category="classics",
    parameters={
        "query": "Keyword, phrase, syndrome, or formula (e.g., '治未病', '往来寒热', '桂枝汤', 'Yinqiao', 'preventive')",
        "book": "Optional classic book filter (e.g., '伤寒论', '黄帝内经', '温病条辨', 'Shanghan Lun')",
    },
    usage_guide="When citing authentic classical TCM passages, pathogenesis theories, or classical formula clauses.",
)
def classics_search(query: str, book: str = "") -> dict:
    """Full-text and tag search across the bilingual TCM classics corpus."""
    q = query.strip()
    canon_book = _resolve_canonical_book(book) if book.strip() else None
    if book.strip() and canon_book is None:
        return {
            "status": "not_found",
            "message": f"Book '{book}' not recognized. Supported classics: {list(BOOK_ALIASES.keys())}.",
        }

    q_low = q.lower()
    tokens = [t for t in re.split(r"[,，\s()（）/・]+", q_low) if len(t) >= 2 or ("\u4e00" <= t <= "\u9fff")]
    results: list[dict] = []

    for entry in CLASSICS_CORPUS:
        if canon_book and entry["book"] != canon_book:
            continue

        searchable = " ".join([
            entry["id"],
            entry["book"],
            entry["sub_book"],
            entry["title"],
            entry["chinese_text"],
            entry["english_translation"],
            entry["clinical_significance"],
            " ".join(entry["tags"]),
            " ".join(entry["related_formulas"]),
        ]).lower()

        score = 0
        if q_low and q_low in searchable:
            score += 4
        for tok in tokens:
            if tok in searchable:
                score += 2
        if not q:
            score = 1

        if score > 0:
            results.append({
                "relevance_score": score,
                "canon": f"《{entry['book']}》",
                "section": entry["sub_book"],
                "text": entry["chinese_text"],
                "translation": entry["english_translation"],
                **entry,
            })

    results.sort(key=lambda r: r["relevance_score"], reverse=True)
    if not results:
        return {
            "status": "not_found",
            "message": f"No classical passages matched '{query}'" + (f" in 《{canon_book}》." if canon_book else "."),
            "supported_books": list(BOOK_ALIASES.keys()),
        }

    return {
        "status": "found",
        "query": query,
        "count": len(results),
        "book_filter": canon_book or "all",
        "passages": results[:10],
        "results": results[:10],
    }


@registry.register(
    name="classics.clause_lookup",
    description=(
        "Look up a specific numbered clause or chapter from a TCM classic (e.g., Shanghan Lun "
        "Clause 96 '小柴胡汤', Clause 12 '桂枝汤', Clause 177 '炙甘草汤', Huangdi Neijing Suwen Ch. 2, "
        "or list all curated clauses of a book when clause_id is omitted)."
    ),
    category="classics",
    parameters={
        "book": "Classic book title (e.g., '伤寒论', 'Shanghan Lun', '黄帝内经', '金匮要略', '温病条辨')",
        "clause_id": "Optional clause number, ID, or formula title (e.g., '96', 'SHL-096', '第12条', '酸枣仁汤')",
    },
    usage_guide="When retrieving an exact numbered clause from Shanghan Lun, Jin Gui Yao Lue, Wenbing Tiaobian, or Neijing.",
)
def clause_lookup(book: str, clause_id: str = "") -> dict:
    """Look up exact clause(s) by book and optional clause identifier."""
    canon_book = _resolve_canonical_book(book)
    if canon_book is None:
        return {
            "status": "not_found",
            "message": f"Book '{book}' not recognized. Supported classics: {list(BOOK_ALIASES.keys())}.",
        }

    book_entries = [e for e in CLASSICS_CORPUS if e["book"] == canon_book]
    cid = clause_id.strip()
    if not cid:
        return {
            "status": "found",
            "book": f"《{canon_book}》",
            "count": len(book_entries),
            "clauses": book_entries,
        }

    cid_low = cid.lower()
    digits_only = re.sub(r"\D+", "", cid)

    matched = []
    for entry in book_entries:
        c_nums_low = [c.lower() for c in entry["clause_numbers"]]
        if (
            cid_low == entry["id"].lower()
            or cid_low in c_nums_low
            or (digits_only and digits_only in c_nums_low)
            or cid_low in entry["title"].lower()
            or cid in entry["chinese_text"]
        ):
            matched.append(entry)

    if matched:
        return {
            "status": "found",
            "book": f"《{canon_book}》",
            "clause_query": clause_id,
            "clause": matched[0],
            "matches": matched,
        }

    return {
        "status": "not_found",
        "message": f"Clause '{clause_id}' not found in curated 《{canon_book}》 corpus.",
        "available_clauses_in_book": [
            {"id": e["id"], "clause_numbers": e["clause_numbers"], "title": e["title"]}
            for e in book_entries
        ],
    }


@registry.register(
    name="classics.herb_monograph",
    description=(
        "Retrieve the multi-dynasty classical Materia Medica monograph (历代本草专论) for a Chinese "
        "herb across Shennong Bencao Jing (神农本草经), Mingyi Bielu (名医别录), Bencao Gangmu "
        "(本草纲目・李时珍), and Zhang Zhongjing's classical usage, linked with modern pharmacopoeia data."
    ),
    category="classics",
    parameters={"herb": "Herb name in Chinese, pinyin, or English (e.g., '人参', '黄芪', '黄连', '附子', 'Ginseng')"},
    usage_guide="When researching historical Bencao literature, Shennong grade (上中下三品), or classical usage of a herb.",
)
def herb_monograph(herb: str) -> dict:
    """Look up classical Bencao monograph cross-referenced with modern herb & safety data."""
    q = herb.strip()
    q_low = q.lower()
    q_plain = re.sub(r"\s+", "", q_low)

    for cn_name, mono in HERB_CLASSICAL_MONOGRAPHS.items():
        pinyin_plain = re.sub(r"\s+", "", mono["pinyin"].lower())
        if (
            q == cn_name
            or q_low == mono["english"].lower()
            or q_low == mono["pinyin"].lower()
            or q_plain == pinyin_plain
            or cn_name in q
        ):
            modern_profile = _search_herb(cn_name)
            safety_info = toxicity_check(cn_name)
            return {
                "status": "found",
                "herb": cn_name,
                "monograph": mono,
                "modern_pharmacopoeia_profile": modern_profile,
                "safety_profile": safety_info,
            }

    return {
        "status": "not_found",
        "message": f"Classical Bencao monograph for '{herb}' not found in local curated monographs.",
        "available_monographs": list(HERB_CLASSICAL_MONOGRAPHS.keys()),
    }
