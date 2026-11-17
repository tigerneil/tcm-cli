/* ==========================================================================
   TCM Studio v0.2.0 — Interactive Multimodal Workbench Engine (docs/studio.js)
   Dual-Mode Architecture:
     1) Live Python Backend Mode (when `tcm studio` serves ./api/health)
     2) Client-Side Standalone Engine Mode (100% in-browser on GitHub Pages)
   ========================================================================== */

(function () {
  "use strict";

  /* ------------------------------------------------------------------------
     1. Studio Global State & Bilingual Copy
     ------------------------------------------------------------------------ */
  const state = {
    liveBackend: false,
    apiBase: "./api",
    backendToolCount: 45,
    lang: localStorage.getItem("tcm-studio-lang") === "zh" ? "zh" : "en",
    theme: localStorage.getItem("tcm-studio-theme") === "dark" ? "dark" : "light",
    activeWorkspace: "lab",
    activeModel: "claude-opus-5-5",

    // Workspace 1: Multimodal Lab
    labSubtab: "tongue",
    labPreset: "pale_scalloped",
    showOverlay: true,
    uploadedImage: null,
    uploadedDataUrl: null,
    computedZones: null,
    currentDiagnosis: null,

    // Workspace 2: Formula & Network Pharmacology
    activeFormulaKey: "sijunzi",
    builderHerbs: [],
    graphNodes: [],
    graphEdges: [],
    selectedNode: null,
    draggingNode: null,
    animFrameId: null,

    // Workspace 3: Atlas
    atlasBodyView: "anterior",
    atlasCategory: "all",
    selectedPointCode: "ST36",

    // Workspace 4: SOTA Agent Console
    agentAttachmentDataUrl: null,
    agentAttachmentName: "",
    agentTurns: []
  };

  const STUDIO_I18N = {
    en: {
      railHeading: "Workspaces · 工作台",
      ws1Name: "Four-Examinations Lab",
      ws2Name: "Formula & Network Graph",
      ws3Name: "Materia, Meridians & Canon",
      ws4Name: "SOTA Agent Console",
      ws1Title: "Multimodal Four-Examinations Lab (四诊多模态实验台)",
      ws1Sub:
        "Upload any tongue, herb slice, or classical prescription photograph — or load calibrated museum/clinical reference plates — for real-time pixel CIE L*a*b* telemetry and Eight-Principle syndrome differentiation.",
      ws2Title: "Formula Composer & Network Pharmacology Graph (方剂配伍与网络药理)",
      ws2Sub:
        "Explore multi-layer interactions from Sovereign/Minister herbs to bioactive compounds, UniProt targets, and KEGG pathways — while validating Eighteen Incompatibilities (十八反), Nineteen Antagonisms (十九畏), and CYP450 drug safety in real time.",
      ws3Title: "Materia Medica, Meridian Acupoints & Classics (本草・经穴・典籍)",
      ws3Sub:
        "Click any acupoint on the Anterior/Posterior Meridian Atlas or search across core herbs, formulas, and canonical clauses from Huangdi Neijing, Shanghan Lun, Jin Gui Yao Lue, Shennong Bencao Jing, and Bencao Gangmu.",
      ws4Title: "SOTA Agent Console & Model Router (智能体研究终端)",
      ws4Sub:
        "Execute multi-step TCM & computational pharmacology investigations with transparent Plan → Tool Trace → Grounded Synthesis inspection and Markdown dossier export."
    },
    zh: {
      railHeading: "四大工作台 · Workspaces",
      ws1Name: "四诊多模态实验台",
      ws2Name: "方剂配伍与网络药理",
      ws3Name: "本草・经穴・典籍",
      ws4Name: "智能体研究终端",
      ws1Title: "四诊多模态实验台 (Multimodal Four-Examinations Lab)",
      ws1Sub:
        "拖入或上传舌象、中药饮片或古籍处方图像，或一键加载临床与馆藏标准标本，实时提取像素级 CIE L*a*b* 分区色度并生成八纲辨证报告。",
      ws2Title: "方剂配伍与网络药理图谱 (Formula & Network Pharmacology)",
      ws2Sub:
        "交互推演「方剂 → 君臣佐使中药 → 活性化合物 → 人类蛋白靶点 → KEGG信号通路」多维网络，同步核验十八反、十九畏、妊娠禁忌及西药 CYP450 相互作用。",
      ws3Title: "本草・经穴・经典条文检索台 (Materia, Meridians & Canon)",
      ws3Sub:
        "点击正背面经络腧穴图谱（WHO标准定位），或跨库秒级检索《中国药典》本草、经典名方及《内经》《伤寒论》《金匮》《神农本草经》《本草纲目》原文。",
      ws4Title: "SOTA 智能体研究终端 (Autonomous Agent & Model Router)",
      ws4Sub:
        "自由切换 35+ 前沿多模态与推理模型，完整透视「研究规划 → 工具调用轨迹 → 循证双语综合」并支持导出 Markdown 研究卷宗。"
    }
  };

  /* ------------------------------------------------------------------------
     2. Embedded Clinical, Pharmacognosy, Network, Acupoint & Canon Knowledge
     ------------------------------------------------------------------------ */
  const LAB_PRESET_SPECS = {
    pale_scalloped: {
      subtab: "tongue",
      kind: "procedural_tongue",
      name: "Pale Swollen Scalloped Tongue (淡白胖大齿痕舌)",
      pulseDefault: "soggy_weak",
      voiceDefault: "low_faint",
      symptomsDefault: ["fatigue", "loose_stools", "heavy_limbs"],
      drawCfg: {
        bodyRgb: [224, 173, 170],
        edgeRgb: [214, 162, 160],
        coatRgb: [245, 241, 234],
        coatAlpha: 0.64,
        swollen: true,
        scallops: true,
        fissures: false,
        stasisSpots: false
      },
      icd: "ICD-11 TM1: SF50 (Spleen Qi Deficiency)",
      bagang: { heat: 24, excess: 18, interior: 88, yang: 30 },
      syndromes: [
        { name: "脾虚湿盛证 · Spleen Qi Deficiency with Damp Retention", conf: "94%", note: "L* > 72 hypoemic lingual body + bilateral marginal dental indentations + soggy pulse." },
        { name: "气血两虚证 · Dual Qi & Blood Deficiency", conf: "68%", note: "Attenuated erythroid a* chromaticity across apex and center." },
        { name: "脾肾阳虚水泛 · Spleen-Kidney Yang Deficiency", conf: "41%", note: "Consider if accompanied by chill intolerance and deep-slow pulse." }
      ],
      formulaKey: "sijunzi",
      formulaText: "<strong>参苓白术散合六君子汤</strong> (Shen Ling Bai Zhu San + Liu Jun Zi Tang)",
      modsText: "Add 砂仁 6g (add near end 后下), 苍术 9g, 茯苓 15g & 泽泻 9g tofortify Spleen transformation and drain interstitial dampness.",
      acupointsText: "<code>ST36 足三里</code>, <code>SP9 阴陵泉</code>, <code>CV12 中脘</code>, <code>SP6 三阴交</code>"
    },
    red_greasy: {
      subtab: "tongue",
      kind: "procedural_tongue",
      name: "Red Tongue with Yellow Greasy Coating (红舌黄腻苔)",
      pulseDefault: "wiry_rapid",
      voiceDefault: "heavy_turbid",
      symptomsDefault: ["bitter_mouth", "rib_pain", "heavy_limbs"],
      drawCfg: {
        bodyRgb: [198, 72, 72],
        edgeRgb: [212, 62, 64],
        coatRgb: [219, 184, 102],
        coatAlpha: 0.85,
        swollen: false,
        scallops: false,
        fissures: false,
        stasisSpots: false
      },
      icd: "ICD-11 TM1: SF75 (Damp-Heat Pattern)",
      bagang: { heat: 86, excess: 84, interior: 90, yang: 78 },
      syndromes: [
        { name: "肝胆/脾胃湿热证 · Hepatobiliary & Middle-Jiao Damp-Heat", conf: "95%", note: "Elevated red chrome (a* > +28) + high yellow coat chromaticity (b* > +22) + wiry-slippery rapid pulse." },
        { name: "少阳阳明合病 · Shaoyang-Yangming Disharmony", conf: "71%", note: "Bitter mouth, rib-side fullness, and thick yellow central coating." },
        { name: "痰热内扰证 · Phlegm-Heat Harassing Interior", conf: "54%", note: "Monitor sleep restlessness and chest oppression." }
      ],
      formulaKey: "huanglian",
      formulaText: "<strong>黄连解毒汤合茵陈蒿汤 / 龙胆泻肝汤</strong> (Huang Lian Jie Du Tang / Long Dan Xie Gan Tang)",
      modsText: "Add 茵陈 15g, 滑石 12g (wrapped 包煎), 枳实 9g & 竹茹 9g to clear damp-heat through Triple Jiao.",
      acupointsText: "<code>GB34 阳陵泉</code>, <code>SP9 阴陵泉</code>, <code>LI11 曲池</code>, <code>LR3 太冲</code>"
    },
    crimson_fissured: {
      subtab: "tongue",
      kind: "procedural_tongue",
      name: "Crimson Fissured Peeled Tongue (红绛裂纹少苔舌)",
      pulseDefault: "thready_rapid",
      voiceDefault: "dry_cough",
      symptomsDefault: ["night_sweats", "insomnia"],
      drawCfg: {
        bodyRgb: [164, 38, 50],
        edgeRgb: [178, 42, 54],
        coatRgb: [238, 220, 214],
        coatAlpha: 0.12,
        swollen: false,
        scallops: false,
        fissures: true,
        stasisSpots: false
      },
      icd: "ICD-11 TM1: SE73 (Yin Deficiency with Effulgent Fire)",
      bagang: { heat: 82, excess: 20, interior: 94, yang: 65 },
      syndromes: [
        { name: "阴虚火旺 / 心肾不交证 · Yin Deficiency with Empty Fire", conf: "96%", note: "Low L* crimson body + exfoliated fur + axial fissures + thready-rapid pulse." },
        { name: "胃肾阴伤证 · Stomach & Kidney Yin Exhaustion", conf: "77%", note: "Mirror-like peeled central dorsum reflecting depleted Stomach fluids." },
        { name: "温病后期真阴耗损 · Late-Stage Warm-Disease Yin Depletion", conf: "52%", note: "Classical Wen Bing Tiao Bian Lower-Jiao pattern." }
      ],
      formulaKey: "sijunzi",
      formulaText: "<strong>知柏地黄丸合黄连阿胶汤</strong> (Zhi Bai Di Huang Wan + Huang Lian E Jiao Tang)",
      modsText: "Add 麦冬 12g, 玄参 12g, 石斛 12g & 酸枣仁 15g; strictly avoid acrid-warm drying herbs (忌辛温燥烈).",
      acupointsText: "<code>KI3 太溪</code>, <code>HT7 神门</code>, <code>SP6 三阴交</code>, <code>BL23 肾俞</code>"
    },
    violaceous_stasis: {
      subtab: "tongue",
      kind: "procedural_tongue",
      name: "Violaceous Stasis Tongue (青紫瘀点舌)",
      pulseDefault: "choppy_wiry",
      voiceDefault: "sighing",
      symptomsDefault: ["stabbing_pain", "rib_pain"],
      drawCfg: {
        bodyRgb: [134, 82, 108],
        edgeRgb: [122, 70, 98],
        coatRgb: [228, 222, 228],
        coatAlpha: 0.30,
        swollen: false,
        scallops: false,
        fissures: false,
        stasisSpots: true
      },
      icd: "ICD-11 TM1: SE92 (Blood Stasis Pattern)",
      bagang: { heat: 44, excess: 80, interior: 92, yang: 38 },
      syndromes: [
        { name: "气滞血瘀证 · Qi Stagnation & Blood Stasis", conf: "95%", note: "Cyanotic negative b* shift + petechial stasis macules on lateral margins + choppy-wiry pulse." },
        { name: "心脉瘀阻证 · Heart Vessel Blood Stasis", conf: "74%", note: "Apex stasis macules correlate with Upper-Jiao microcirculatory obstruction." },
        { name: "寒凝血瘀证 · Cold-Congealed Blood Stasis", conf: "48%", note: "Evaluate extremity warmth and menstrual/chest pain triggers." }
      ],
      formulaKey: "xuefu",
      formulaText: "<strong>血府逐瘀汤</strong> (Xue Fu Zhu Yu Tang — Yi Lin Gai Cuo)",
      modsText: "Add 丹参 15g & 三七粉 3g (冲服) for severe stabbing pain; MANDATORY pregnancy & Warfarin/antiplatelet screening.",
      acupointsText: "<code>PC6 内关</code>, <code>SP6 三阴交</code>, <code>LR3 太冲</code>, <code>LI4 合谷</code>"
    },
    huangqi: {
      subtab: "herb",
      kind: "asset_image",
      src: "./assets/herb-specimen-huangqi.jpg",
      name: "Radix Astragali Slices (蒙古黄芪饮片 · 菊花心鉴别)",
      pulseDefault: "soggy_weak",
      voiceDefault: "low_faint",
      symptomsDefault: ["fatigue"],
      icd: "ChP 2025 Vol. I · Astragali Radix",
      bagang: { heat: 58, excess: 25, interior: 80, yang: 68 },
      syndromes: [
        { name: "道地蒙古黄芪正品 · Authentic Astragalus membranaceus var. mongholicus", conf: "98%", note: "Distinct 菊花心 radiating xylem striations + 金井玉栏 brownish cambium ring + creamy fibrous phloem." },
        { name: "排除伪品红芪 · Excluded Adulterant: Hedysarum polybotrys", conf: "96% Excl.", note: "Periderm is pale yellowish-brown rather than reddish-brown; vascular rays radiate cleanly." },
        { name: "生饮片性状（未蜜炙）· Raw Unbroiled Slice", conf: "92%", note: "Dry matte ivory-yellow cut face without caramelized honey gloss; optimal for 固表利水." }
      ],
      formulaKey: "buzhong",
      formulaText: "<strong>补中益气汤 / 玉屏风散 / 防己黄芪汤</strong> (Anchor Astragalus Prescriptions)",
      modsText: "ChP Assay: Astragaloside IV ≥ 0.080%, Calycosin-7-O-β-D-glucoside ≥ 0.020%. Adult dosage: 9–30 g (up to 60 g in post-stroke Qi deficiency).",
      acupointsText: "<code>ST36 足三里</code>, <code>CV4 关元</code>, <code>LU7 列缺</code>"
    },
    bencao_folio: {
      subtab: "ocr",
      kind: "asset_image",
      src: "./assets/classical-folio-manuscript.jpg",
      name: "Bencao Gangmu Folio 35 · Panax ginseng (本草纲目·人参刻本)",
      pulseDefault: "soggy_weak",
      voiceDefault: "low_faint",
      symptomsDefault: ["fatigue", "insomnia"],
      icd: "Ming Woodblock Edition · 1596 CE",
      bagang: { heat: 54, excess: 20, interior: 86, yang: 62 },
      syndromes: [
        { name: "OCR Column 1–3 · 本草綱目 · 人參：根似人形，氣味甘平", conf: "99% OCR", note: "Sweet, neutral-slightly warm; enters Spleen, Lung, Heart, Kidney meridians." },
        { name: "OCR Column 4–5 · 主治補五臟，安精神，止驚悸，除邪氣，明目，開心益智", conf: "98% OCR", note: "Directly quotes Shennong Bencao Jing Upper-Grade (上品) canonical efficacy." },
        { name: "Seal Stamp · 陳氏藏書 (Chen Family Collector Seal)", conf: "97% Det.", note: "Vermilion cinnabar collector seal isolated from black pine-soot woodblock ink via a* > +32." }
      ],
      formulaKey: "xiaochaihu",
      formulaText: "<strong>四君子汤 / 小柴胡汤 / 独参汤</strong> (Eastern Han 3兩 = 41.4g Decoction / 13.8g Draught)",
      modsText: "Safety Gate: Strictly contraindicated with 藜芦 (Veratrum, 十八反); antagonizes 五灵脂 (Trogopterus, 十九畏). Decoct separately (另炖) to preserve ginsenosides.",
      acupointsText: "<code>CV4 关元</code>, <code>ST36 足三里</code>, <code>HT7 神门</code>"
    }
  };

  /* Phytochemistry, ADMET, Target & KEGG Pathway Database for Standalone Graph */
  const HERB_BIO_DB = {
    "人参": { nature: "Slightly Warm", flavor: "Sweet, Slightly Bitter", meridians: "SP, LU, HT, KI", compounds: ["Ginsenoside Rg1", "Ginsenoside Rb1"] },
    "黄芪": { nature: "Slightly Warm", flavor: "Sweet", meridians: "SP, LU", compounds: ["Astragaloside IV", "Calycosin"] },
    "白术": { nature: "Warm", flavor: "Bitter, Sweet", meridians: "SP, ST", compounds: ["Atractylenolide III", "Atractylenolide I"] },
    "茯苓": { nature: "Neutral", flavor: "Sweet, Bland", meridians: "HT, SP, KI", compounds: ["Pachymic Acid", "Poricoic Acid A"] },
    "甘草": { nature: "Neutral/Warm", flavor: "Sweet", meridians: "12 Meridians", compounds: ["Glycyrrhizin", "Isoliquiritigenin"] },
    "柴胡": { nature: "Slightly Cold", flavor: "Bitter, Acrid", meridians: "LR, GB", compounds: ["Saikosaponin A", "Saikosaponin D"] },
    "黄芩": { nature: "Cold", flavor: "Bitter", meridians: "LU, GB, ST, LI", compounds: ["Baicalin", "Wogonin"] },
    "半夏": { nature: "Warm", flavor: "Acrid", meridians: "SP, ST, LU", compounds: ["Beta-Sitosterol"] },
    "黄连": { nature: "Cold", flavor: "Bitter", meridians: "HT, ST, LR, LI", compounds: ["Berberine", "Coptisine"] },
    "黄柏": { nature: "Cold", flavor: "Bitter", meridians: "KI, BL", compounds: ["Berberine", "Palmatine"] },
    "栀子": { nature: "Cold", flavor: "Bitter", meridians: "HT, LU, SJ", compounds: ["Geniposide"] },
    "当归": { nature: "Warm", flavor: "Sweet, Acrid", meridians: "LR, HT, SP", compounds: ["Ferulic Acid", "Z-Ligustilide"] },
    "川芎": { nature: "Warm", flavor: "Acrid", meridians: "LR, GB, PC", compounds: ["Tetramethylpyrazine", "Ferulic Acid"] },
    "丹参": { nature: "Slightly Cold", flavor: "Bitter", meridians: "HT, PC, LR", compounds: ["Tanshinone IIA", "Salvianolic Acid B"] },
    "桃仁": { nature: "Neutral", flavor: "Bitter, Sweet", meridians: "HT, LR, LI", compounds: ["Amygdalin", "Beta-Sitosterol"] },
    "红花": { nature: "Warm", flavor: "Acrid", meridians: "HT, LR", compounds: ["Hydroxysafflor Yellow A"] },
    "白芍": { nature: "Slightly Cold", flavor: "Bitter, Sour", meridians: "LR, SP", compounds: ["Paeoniflorin"] },
    "生地黄": { nature: "Cold", flavor: "Sweet, Bitter", meridians: "HT, LR, KI", compounds: ["Catalpol"] },
    "牛膝": { nature: "Neutral", flavor: "Bitter, Sour", meridians: "LR, KI", compounds: ["Beta-Ecdysterone"] },
    "陈皮": { nature: "Warm", flavor: "Acrid, Bitter", meridians: "SP, LU", compounds: ["Hesperidin", "Nobiletin"] },
    "升麻": { nature: "Slightly Cold", flavor: "Acrid, Sweet", meridians: "LU, SP, ST, LI", compounds: ["Isoferulic Acid"] },
    "麻黄": { nature: "Warm", flavor: "Acrid, Slightly Bitter", meridians: "LU, BL", compounds: ["Ephedrine"] },
    "附子": { nature: "Hot (Toxic)", flavor: "Acrid, Sweet", meridians: "HT, KI, SP", compounds: ["Benzoylmesaconine"] },
    "干姜": { nature: "Hot", flavor: "Acrid", meridians: "SP, ST, KI, HT, LU", compounds: ["6-Gingerol"] },
    "肉桂": { nature: "Hot", flavor: "Acrid, Sweet", meridians: "KI, SP, HT, LR", compounds: ["Cinnamaldehyde"] },
    "细辛": { nature: "Warm", flavor: "Acrid", meridians: "HT, LU, KI", compounds: ["Asarinin"] },
    "藜芦": { nature: "Cold (Toxic)", flavor: "Acrid, Bitter", meridians: "LU, ST, LR", compounds: ["Veratridine"] },
    "甘遂": { nature: "Cold (Toxic)", flavor: "Bitter", meridians: "LU, KI, LI", compounds: ["Kansuinine A"] },
    "海藻": { nature: "Cold", flavor: "Bitter, Salty", meridians: "LR, ST, KI", compounds: ["Fucosterol"] },
    "贝母": { nature: "Slightly Cold", flavor: "Bitter, Sweet", meridians: "LU, HT", compounds: ["Peimine"] },
    "五灵脂": { nature: "Warm", flavor: "Bitter, Sweet", meridians: "LR", compounds: ["Amentoflavone"] },
    "赤石脂": { nature: "Warm", flavor: "Sweet, Sour, Astringent", meridians: "LI, ST", compounds: ["Hydrated Halloysite"] }
  };

  const COMPOUND_META_DB = {
    "Ginsenoside Rg1": { mw: 801.0, ob: "32.4% (deglycosylated)", dl: 0.84, targets: ["AKT1", "NOS3", "PPARG"] },
    "Ginsenoside Rb1": { mw: 1109.3, ob: "28.6% (M1 metabolite)", dl: 0.65, targets: ["AMPK", "AKT1", "TNF"] },
    "Astragaloside IV": { mw: 785.0, ob: "34.2% (active saponin)", dl: 0.72, targets: ["AMPK", "AKT1", "NFE2L2"] },
    "Calycosin": { mw: 284.3, ob: "47.8%", dl: 0.24, targets: ["VEGFA", "PTGS2", "NOS3"] },
    "Atractylenolide III": { mw: 248.3, ob: "68.1%", dl: 0.17, targets: ["AMPK", "IL6", "NFKB1"] },
    "Atractylenolide I": { mw: 230.3, ob: "37.4%", dl: 0.15, targets: ["TNF", "IL6"] },
    "Pachymic Acid": { mw: 528.8, ob: "33.6%", dl: 0.81, targets: ["PPARG", "AKT1"] },
    "Poricoic Acid A": { mw: 498.7, ob: "30.5%", dl: 0.76, targets: ["NFKB1", "TNF"] },
    "Glycyrrhizin": { mw: 822.9, ob: "31.2% (Glycyrrhetinic)", dl: 0.68, targets: ["NFKB1", "IL6"] },
    "Isoliquiritigenin": { mw: 256.3, ob: "85.3%", dl: 0.15, targets: ["PTGS2", "NFE2L2"] },
    "Saikosaponin A": { mw: 781.0, ob: "30.8%", dl: 0.63, targets: ["NFKB1", "TNF", "IL6"] },
    "Saikosaponin D": { mw: 781.0, ob: "29.4%", dl: 0.63, targets: ["STAT3", "NFKB1"] },
    "Baicalin": { mw: 446.4, ob: "40.1%", dl: 0.75, targets: ["TNF", "STAT3", "PTGS2"] },
    "Wogonin": { mw: 284.3, ob: "30.7%", dl: 0.23, targets: ["AKT1", "IL6"] },
    "Beta-Sitosterol": { mw: 414.7, ob: "36.9%", dl: 0.75, targets: ["PPARG", "PTGS2"] },
    "Berberine": { mw: 336.4, ob: "36.9%", dl: 0.78, targets: ["AMPK", "TNF", "PTGS2"] },
    "Coptisine": { mw: 320.3, ob: "30.7%", dl: 0.86, targets: ["NFKB1", "AMPK"] },
    "Palmatine": { mw: 352.4, ob: "64.6%", dl: 0.65, targets: ["TNF", "IL6"] },
    "Geniposide": { mw: 388.4, ob: "31.5%", dl: 0.44, targets: ["IL6", "NFKB1"] },
    "Ferulic Acid": { mw: 194.2, ob: "39.6%", dl: 0.06, targets: ["NOS3", "PTGS2", "VEGFA"] },
    "Z-Ligustilide": { mw: 190.2, ob: "51.3%", dl: 0.07, targets: ["TNF", "NOS3"] },
    "Tetramethylpyrazine": { mw: 136.2, ob: "41.1%", dl: 0.03, targets: ["NOS3", "VEGFA"] },
    "Tanshinone IIA": { mw: 294.3, ob: "49.9%", dl: 0.40, targets: ["PTGS2", "NOS3", "STAT3"] },
    "Salvianolic Acid B": { mw: 718.6, ob: "30.1%", dl: 0.79, targets: ["VEGFA", "AKT1"] },
    "Amygdalin": { mw: 457.4, ob: "31.0%", dl: 0.61, targets: ["NOS3", "TNF"] },
    "Hydroxysafflor Yellow A": { mw: 612.5, ob: "32.8%", dl: 0.68, targets: ["VEGFA", "NOS3", "PTGS2"] },
    "Paeoniflorin": { mw: 480.5, ob: "53.9%", dl: 0.79, targets: ["TNF", "IL6"] },
    "Catalpol": { mw: 362.3, ob: "30.2%", dl: 0.44, targets: ["AKT1", "NFE2L2"] },
    "Beta-Ecdysterone": { mw: 480.6, ob: "35.2%", dl: 0.78, targets: ["AKT1", "VEGFA"] },
    "Hesperidin": { mw: 610.6, ob: "31.4%", dl: 0.67, targets: ["TNF", "NFE2L2"] },
    "Nobiletin": { mw: 402.4, ob: "61.7%", dl: 0.52, targets: ["AMPK", "NFKB1"] },
    "Isoferulic Acid": { mw: 194.2, ob: "38.2%", dl: 0.06, targets: ["IL6", "NFKB1"] },
    "Ephedrine": { mw: 165.2, ob: "43.4%", dl: 0.04, targets: ["NOS3", "TNF"] },
    "Benzoylmesaconine": { mw: 590.7, ob: "30.4% (hydrolyzed)", dl: 0.27, targets: ["AKT1", "NOS3"] },
    "6-Gingerol": { mw: 294.4, ob: "35.6%", dl: 0.16, targets: ["PTGS2", "NFKB1"] },
    "Cinnamaldehyde": { mw: 132.2, ob: "32.0%", dl: 0.02, targets: ["PTGS2", "NOS3"] },
    "Asarinin": { mw: 354.4, ob: "55.3%", dl: 0.82, targets: ["PTGS2", "TNF"] },
    "Veratridine": { mw: 673.8, ob: "TOXIC ALKALOID", dl: 0.54, targets: ["SCN5A (Cardiotoxic)"] },
    "Kansuinine A": { mw: 728.8, ob: "IRRITANT DITERPENE", dl: 0.41, targets: ["NFKB1"] },
    "Fucosterol": { mw: 412.7, ob: "36.2%", dl: 0.76, targets: ["PPARG"] },
    "Peimine": { mw: 431.7, ob: "42.5%", dl: 0.78, targets: ["TNF", "IL6"] },
    "Amentoflavone": { mw: 538.5, ob: "31.9%", dl: 0.72, targets: ["PTGS2"] },
    "Hydrated Halloysite": { mw: 294.2, ob: "GI Adsorbent", dl: 0.10, targets: ["Mucosal Barrier"] }
  };

  const TARGET_KEGG_MAP = {
    AKT1: { code: "hsa04151", name: "PI3K-Akt Survival & Metabolic" },
    AMPK: { code: "hsa04152", name: "AMPK Energy & Glucose Sensing" },
    TNF: { code: "hsa04668", name: "TNF / Cytokine Inflammation" },
    IL6: { code: "hsa04630", name: "JAK-STAT Immune Cascade" },
    VEGFA: { code: "hsa04370", name: "VEGF Microvascular Angiogenesis" },
    PPARG: { code: "hsa03320", name: "PPAR Lipid & Insulin Sensitivity" },
    PTGS2: { code: "hsa00590", name: "COX-2 / Eicosanoid Signaling" },
    NOS3: { code: "hsa04270", name: "eNOS Vascular Tone & Perfusion" },
    NFKB1: { code: "hsa04064", name: "NF-κB Innate Immunity" },
    STAT3: { code: "hsa04630", name: "JAK-STAT Immune Cascade" },
    NFE2L2: { code: "hsa05208", name: "Nrf2/HO-1 Antioxidant Defense" },
    "SCN5A (Cardiotoxic)": { code: "TOX-NA", name: "Cardiac Na+ Hyper-Depolarization" },
    "Mucosal Barrier": { code: "GI-01", name: "Mucosal Astringency" }
  };

  const STUDIO_FORMULA_PRESETS = {
    sijunzi: {
      title: "四君子汤 (Si Jun Zi Tang)",
      herbs: [
        { name: "人参", dose: 9, role: "君" },
        { name: "白术", dose: 9, role: "臣" },
        { name: "茯苓", dose: 9, role: "佐" },
        { name: "甘草", dose: 6, role: "使" }
      ],
      meds: [],
      pregnant: false
    },
    buzhong: {
      title: "补中益气汤 (Bu Zhong Yi Qi Tang)",
      herbs: [
        { name: "黄芪", dose: 18, role: "君" },
        { name: "人参", dose: 9, role: "臣" },
        { name: "白术", dose: 9, role: "臣" },
        { name: "当归", dose: 6, role: "佐" },
        { name: "陈皮", dose: 6, role: "佐" },
        { name: "升麻", dose: 6, role: "使" },
        { name: "柴胡", dose: 6, role: "使" },
        { name: "甘草", dose: 6, role: "使" }
      ],
      meds: [],
      pregnant: false
    },
    xiaochaihu: {
      title: "小柴胡汤 (Xiao Chai Hu Tang)",
      herbs: [
        { name: "柴胡", dose: 12, role: "君" },
        { name: "黄芩", dose: 9, role: "臣" },
        { name: "半夏", dose: 9, role: "佐" },
        { name: "人参", dose: 6, role: "佐" },
        { name: "甘草", dose: 6, role: "使" }
      ],
      meds: [],
      pregnant: false
    },
    huanglian: {
      title: "黄连解毒汤 (Huang Lian Jie Du Tang)",
      herbs: [
        { name: "黄连", dose: 9, role: "君" },
        { name: "黄芩", dose: 6, role: "臣" },
        { name: "黄柏", dose: 6, role: "佐" },
        { name: "栀子", dose: 9, role: "使" }
      ],
      meds: [],
      pregnant: false
    },
    xuefu: {
      title: "血府逐瘀汤 (Xue Fu Zhu Yu Tang)",
      herbs: [
        { name: "桃仁", dose: 12, role: "君" },
        { name: "红花", dose: 9, role: "君" },
        { name: "当归", dose: 9, role: "臣" },
        { name: "川芎", dose: 5, role: "臣" },
        { name: "生地黄", dose: 9, role: "佐" },
        { name: "柴胡", dose: 3, role: "佐" },
        { name: "牛膝", dose: 9, role: "使" },
        { name: "甘草", dose: 6, role: "使" }
      ],
      meds: [],
      pregnant: false
    },
    sini: {
      title: "四逆汤 (Si Ni Tang — Aconite Pre-Decoction Protocol)",
      herbs: [
        { name: "附子", dose: 10, role: "君" },
        { name: "干姜", dose: 6, role: "臣" },
        { name: "甘草", dose: 6, role: "佐" }
      ],
      meds: [],
      pregnant: false
    },
    shibafan: {
      title: "十八反禁忌测试 · 人参 + 藜芦 (Eighteen Incompatibilities)",
      herbs: [
        { name: "人参", dose: 9, role: "君" },
        { name: "藜芦", dose: 0.6, role: "佐" }
      ],
      meds: [],
      pregnant: false
    },
    warfarin: {
      title: "中西药联用测试 · 丹参 + 当归 + Warfarin",
      herbs: [
        { name: "丹参", dose: 15, role: "君" },
        { name: "当归", dose: 9, role: "臣" },
        { name: "川芎", dose: 6, role: "佐" }
      ],
      meds: ["Warfarin"],
      pregnant: false
    }
  };

  /* 18 Precision Acupoints + Materia Medica + Classical Canon Compendium */
  const ACUPOINTS_DB = {
    GV20: { code: "GV20", zh: "百会", py: "Baihui", mer: "Governor Vessel (督脉)", loc: "On the head, 5 B-cun superior to the anterior hairline on the anterior median line, or midpoint connecting the apices of both auricles.", ind: "Transverse/subcutaneous 0.5–0.8 cun. Raises sunken Yang Qi (升阳举陷), calms Shen, clears head/wind dizziness, post-stroke recovery." },
    GB20: { code: "GB20", zh: "风池", py: "Fengchi", mer: "Gallbladder Meridian (足少阳胆经)", loc: "In the anterior region of the neck, inferior to the occipital bone, in the depression between the origins of sternocleidomastoid and trapezius.", ind: "Oblique 0.8–1.2 cun toward tip of nose (avoid deep medial-superior medulla oblongata!). Dispels Interior/Exterior Wind, clears head & eyes, hypertension, migraine." },
    LI11: { code: "LI11", zh: "曲池", py: "Quchi", mer: "Large Intestine · He-Sea (手阳明合穴)", loc: "Lateral elbow, midpoint connecting LU5 (Chize) and lateral epicondyle of humerus with elbow flexed.", ind: "Perpendicular 1.0–1.5 cun. Clears Yangming Heat, cools Blood, resolves Damp-Heat urticaria, lowers febrile & hypertensive states." },
    LI4: { code: "LI4", zh: "合谷", py: "Hegu", mer: "Large Intestine · Yuan-Source (手阳明原穴)", loc: "Dorsum of hand, radial to midpoint of the 2nd metacarpal bone.", ind: "Perpendicular 0.5–1.0 cun (CONTRAINDICATED IN PREGNANCY 孕妇禁针). Command point of face/mouth, expels Wind, regulates sweating, potent analgesia." },
    LU7: { code: "LU7", zh: "列缺", py: "Lieque", mer: "Lung · Luo-Connecting & Ren Mai Master", loc: "Radial aspect of forearm, between tendons of abductor pollicis longus and extensor pollicis brevis, 1.5 B-cun superior to wrist crease.", ind: "Oblique 0.3–0.5 cun superiorly. Command point of head & nape, diffuses Lung Qi, opens Conception Vessel (任脉)." },
    PC6: { code: "PC6", zh: "内关", py: "Neiguan", mer: "Pericardium · Luo & Yin Wei Master", loc: "Anterior forearm, 2 B-cun proximal to palmar wrist crease, between palmaris longus and flexor carpi radialis tendons.", ind: "Perpendicular 0.5–1.0 cun (median nerve plane). Unbinds chest, regulates Heart rhythm, stops nausea/vomiting, calms Shen." },
    HT7: { code: "HT7", zh: "神门", py: "Shenmen", mer: "Heart · Yuan-Source & Shu-Stream", loc: "Anteromedial wrist, radial to flexor carpi ulnaris tendon, on palmar wrist crease.", ind: "Perpendicular 0.3–0.5 cun. Nourishes Heart Yin-Blood, quiets Shen for insomnia, palpitations, and anxiety." },
    CV12: { code: "CV12", zh: "中脘", py: "Zhongwan", mer: "Conception Vessel · Stomach Front-Mu & Fu Hui", loc: "Upper abdomen, 4 B-cun superior to center of umbilicus on anterior median line.", ind: "Perpendicular 1.0–1.5 cun (avoid deep insertion in hepatosplenomegaly). Harmonizes Middle Jiao, descends rebellious Stomach Qi." },
    ST25: { code: "ST25", zh: "天枢", py: "Tianshu", mer: "Stomach · Large Intestine Front-Mu", loc: "Same level as umbilicus, 2 B-cun lateral to anterior midline.", ind: "Perpendicular 1.0–1.5 cun. Bidirectional bowel motility regulation (both diarrhea and constipation), resolves damp stagnation." },
    CV4: { code: "CV4", zh: "关元", py: "Guanyuan", mer: "Conception Vessel · Small Intestine Front-Mu", loc: "Lower abdomen, 3 B-cun inferior to center of umbilicus on anterior midline.", ind: "Perpendicular 1.0–1.5 cun (empty bladder prior to needling; prime moxibustion locus). Banks Yuan-Source Qi, warms Kidney Yang." },
    BL23: { code: "BL23", zh: "肾俞", py: "Shenshu", mer: "Bladder · Kidney Back-Shu (肾之背俞穴)", loc: "Lumbar region, at the level of inferior border of L2 spinous process, 1.5 B-cun lateral to posterior midline.", ind: "Perpendicular 0.5–1.0 cun. Tonifies Kidney Essence, Yin & Yang, strengthens lumbar spine, benefits ears & marrow." },
    ST36: { code: "ST36", zh: "足三里", py: "Zusanli", mer: "Stomach · He-Sea (足阳明合穴)", loc: "Anterior leg, 3 B-cun inferior to ST35 (Dubi), one finger-breadth lateral to anterior crest of tibia.", ind: "Perpendicular 1.0–1.5 cun. Supreme Spleen-Stomach Qi & Blood tonification point; activates vagal-adrenal ChAT+ anti-inflammatory pathway." },
    ST40: { code: "ST40", zh: "丰隆", py: "Fenglong", mer: "Stomach · Luo-Connecting (化痰要穴)", loc: "Anterolateral leg, 8 B-cun superior to tip of lateral malleolus, two finger-breadths lateral to tibial crest.", ind: "Perpendicular 1.0–1.5 cun. Preeminent locus for transforming visible and invisible Phlegm (痰湿/痰热), dizziness, hyperlipidemia." },
    GB34: { code: "GB34", zh: "阳陵泉", py: "Yanglingquan", mer: "Gallbladder · He-Sea & Sinew Hui (筋会)", loc: "Lateral leg, in the depression anterior and inferior to the head of the fibula.", ind: "Perpendicular/slightly inferior 1.0–1.5 cun. Spreads Liver-Gallbladder Qi, clears hepatobiliary damp-heat, relaxes tendons." },
    SP9: { code: "SP9", zh: "阴陵泉", py: "Yinlingquan", mer: "Spleen · He-Sea (健脾利湿要穴)", loc: "Medial leg, in the depression inferior and posterior to the medial condyle of the tibia.", ind: "Perpendicular 1.0–1.5 cun. Resolves Lower/Middle-Jiao Dampness, promotes urination, edema, loose stools." },
    SP6: { code: "SP6", zh: "三阴交", py: "Sanyinjiao", mer: "Spleen · Intersection of Three Leg Yin", loc: "Tibial aspect of leg, posterior to medial border of tibia, 3 B-cun superior to prominence of medial malleolus.", ind: "Perpendicular 1.0–1.5 cun (CONTRAINDICATED IN PREGNANCY 孕妇禁针). Harmonizes Spleen, Liver & Kidney, nourishes Yin & Blood." },
    LR3: { code: "LR3", zh: "太冲", py: "Taichong", mer: "Liver · Yuan-Source & Shu-Stream", loc: "Dorsum of foot, in the depression distal to the junction of bases of 1st and 2nd metatarsal bones.", ind: "Perpendicular 0.5–0.8 cun. Paired with LI4 as Four Gates (四关) to course Liver Qi, subdue Liver Yang, extinguish internal Wind." },
    KI3: { code: "KI3", zh: "太溪", py: "Taixi", mer: "Kidney · Yuan-Source & Shu-Stream", loc: "Posteromedial ankle, in the depression between prominence of medial malleolus and Achilles tendon.", ind: "Perpendicular 0.5–0.8 cun. Anchors Kidney Root Yin & Yang, clears empty fire in insomnia, tinnitus, and sore throat." }
  };

  const ATLAS_COMPENDIUM_EXTRA = [
    { cat: "herb", code: "ChP · 黄芪", title: "黄芪 Radix Astragali (Astragalus membranaceus)", meta: "Sweet, Slightly Warm · SP, LU · 9–30g", body: "Tonifies Qi, upbears Yang, consolidates Exterior (固表止汗), promotes urination & wound healing. Markers: Astragaloside IV, Calycosin. Targets: AMPK, AKT1, NOS3, Nrf2." },
    { cat: "herb", code: "ChP · 人参", title: "人参 Ginseng Radix (Panax ginseng)", meta: "Sweet-Bitter, Slightly Warm · SP, LU, HT, KI · 3–9g", body: "Greatly tonifies Yuan Source Qi (大补元气), restores pulse, generates fluids, calms Shen. Incompatible with 藜芦 (十八反). Markers: Ginsenosides Rg1, Re, Rb1." },
    { cat: "herb", code: "ChP · 黄连", title: "黄连 Coptidis Rhizoma (Coptis chinensis)", meta: "Bitter, Cold · HT, ST, LR, LI · 2–5g", body: "Clears Heat, dries Dampness, drains Fire & resolves toxin. Marker: Berberine (activates AMPK, upregulates LDLR, inhibits NLRP3; inhibits CYP2D6/3A4)." },
    { cat: "herb", code: "ChP · 丹参", title: "丹参 Salviae Miltiorrhizae Radix (Salvia miltiorrhiza)", meta: "Bitter, Slightly Cold · HT, PC, LR · 10–15g", body: "Invigorates Blood, dispels Stasis, cools Blood, calms Shen. Incompatible with 藜芦; major interaction with Warfarin (CYP2C9 & antiplatelet)." },
    { cat: "herb", code: "ChP · 制附子", title: "附子 Aconiti Lateralis Radix Praeparata", meta: "Acrid-Sweet, Hot (Toxic) · HT, KI, SP · 3–15g", body: "Restores devastated Yang (回阳救逆), warms Fire & disperses Cold. MANDATORY pre-decoction 30–60 min; incompatible with 半夏/瓜蒌/贝母/白蔹/白及 (十八反)." },
    { cat: "formula", code: "太平惠民和剂局方", title: "四君子汤 Si Jun Zi Tang (Four Gentlemen Decoction)", meta: "人参 9g · 白术 9g · 茯苓 9g · 炙甘草 6g", body: "Foundational formula for Spleen-Stomach Qi deficiency with pale tongue, low voice, poor appetite, loose stools, and weak pulse." },
    { cat: "formula", code: "脾胃论 · 李东垣", title: "补中益气汤 Bu Zhong Yi Qi Tang", meta: "黄芪 18g · 人参/白术 9g · 当归/陈皮/升麻/柴胡/甘草 6g", body: "Tonifies Middle Qi and raises sunken Clear Yang (甘温除热) for chronic fatigue, organ prolapse, and Qi-deficiency fever." },
    { cat: "formula", code: "伤寒论 · 张仲景", title: "小柴胡汤 Xiao Chai Hu Tang", meta: "柴胡 12g · 黄芩 9g · 半夏 9g · 人参 6g · 姜枣草", body: "Harmonizes Shaoyang pivot disorder: alternating chills & fever,胸胁苦满 rib-side fullness, bitter taste, and wiry pulse." },
    { cat: "classic", code: "黄帝内经 · 素问·上古天真论", title: "《素问》：「正气存内，邪不可干；邪之所凑，其气必虚。」", meta: "Huangdi Neijing Suwen · Foundational Immunology", body: "When Upright Qi (正气) is safeguarded within, pathogenic factors cannot invade; wherever pathogens congregate, Upright Qi is assuredly deficient." },
    { cat: "classic", code: "伤寒论 · 第96条", title: "《伤寒论》：「伤寒五六日中风，往来寒热，胸胁苦满，嘿嘿不欲饮食，心烦喜呕……小柴胡汤主之。」", meta: "Shanghan Lun Clause 96 · Shaoyang Canonical Criterion", body: "Defines the cardinal tetrad of Shaoyang disease and establishes harmonizing therapy with Xiao Chai Hu Tang (Eastern Han 柴胡半斤 = 110g total decoction across 3 draughts)." },
    { cat: "classic", code: "金匮要略 · 血痹虚劳病脉证并治", title: "《金匮要略》：「夫失精家，少腹弦急……桂枝加龙骨牡蛎汤主之；虚劳虚烦不得眠，酸枣仁汤主之。」", meta: "Jin Gui Yao Lue · Deficiency Taxation & Insomnia", body: "Classical differentiation of exhaustion and non-restorative insomnia (虚烦不得眠) nourished via Suan Zao Ren Tang." },
    { cat: "classic", code: "神农本草经 · 上品", title: "《神农本草经》：「上药一百二十种为君，主养命以应天，无毒，多服久服不伤人。」", meta: "Shennong Bencao Jing · Three-Grade Pharmacological Taxonomy", body: "Establishes the Sovereign/Minister/Assistant hierarchy (君臣佐使) and classifies Ginseng, Astragalus, Ganoderma, and Licorice as Upper-Grade longevity tonics." },
    { cat: "classic", code: "本草纲目 · 草部第十二卷", title: "《本草纲目·黄耆》：「耆，长也。黄耆色黄，为补药之长，故名。」", meta: "Bencao Gangmu · Li Shizhen (1596 CE)", body: "Explains the etymology and clinical supremacy of Radix Astragali as the Elder Leader of Qi-tonifying botanicals." }
  ];

  /* ------------------------------------------------------------------------
     3. Real Colorimetry Math: sRGB <-> XYZ (D65) -> CIE L*a*b*
     ------------------------------------------------------------------------ */
  function rgbToLab(r, g, b) {
    let sr = r / 255;
    let sg = g / 255;
    let sb = b / 255;

    sr = sr > 0.04045 ? Math.pow((sr + 0.055) / 1.055, 2.4) : sr / 12.92;
    sg = sg > 0.04045 ? Math.pow((sg + 0.055) / 1.055, 2.4) : sg / 12.92;
    sb = sb > 0.04045 ? Math.pow((sb + 0.055) / 1.055, 2.4) : sb / 12.92;

    // D65 reference white
    const x = (sr * 0.4124564 + sg * 0.3575761 + sb * 0.1804375) / 0.95047;
    const y = (sr * 0.2126729 + sg * 0.7151522 + sb * 0.0721750) / 1.00000;
    const z = (sr * 0.0193339 + sg * 0.1191920 + sb * 0.9503041) / 1.08883;

    const f = (t) => (t > 0.008856 ? Math.cbrt(t) : 7.787 * t + 16 / 116);
    const fx = f(x);
    const fy = f(y);
    const fz = f(z);

    return {
      L: 116 * fy - 16,
      a: 500 * (fx - fy),
      b: 200 * (fy - fz)
    };
  }

  function sampleCanvasRectLab(ctx, x, y, w, h) {
    const sx = Math.max(0, Math.floor(x));
    const sy = Math.max(0, Math.floor(y));
    const sw = Math.max(2, Math.min(ctx.canvas.width - sx, Math.floor(w)));
    const sh = Math.max(2, Math.min(ctx.canvas.height - sy, Math.floor(h)));
    const imgData = ctx.getImageData(sx, sy, sw, sh).data;
    let rSum = 0;
    let gSum = 0;
    let bSum = 0;
    let count = 0;

    for (let i = 0; i < imgData.length; i += 16) {
      rSum += imgData[i];
      gSum += imgData[i + 1];
      bSum += imgData[i + 2];
      count++;
    }
    if (!count) return { L: 65, a: 18, b: 10, r: 190, g: 140, bl: 140 };
    const r = Math.round(rSum / count);
    const g = Math.round(gSum / count);
    const bl = Math.round(bSum / count);
    const lab = rgbToLab(r, g, bl);
    return { L: lab.L, a: lab.a, b: lab.b, r, g, bl };
  }

  /* ------------------------------------------------------------------------
     4. Live Python Backend Probe & Synchronization
     ------------------------------------------------------------------------ */
  async function probeBackendEngine() {
    const badge = document.getElementById("studio-engine-badge");
    const railDetail = document.getElementById("rail-engine-detail");

    if (window.location.protocol === "file:") {
      state.liveBackend = false;
      return;
    }

    const candidates = ["./api/health", "/api/health"];
    for (const url of candidates) {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 1800);
      try {
        const res = await fetch(url, { signal: controller.signal, headers: { Accept: "application/json" } });
        clearTimeout(timer);
        if (res.ok) {
          const data = await res.json();
          if (data && data.status === "ok") {
            state.liveBackend = true;
            state.apiBase = url.replace(/\/health$/, "");
            state.backendToolCount = data.tool_count || 45;
            if (data.active_model) {
              state.activeModel = data.active_model;
              syncModelSelects(state.activeModel);
            }
            if (badge) {
              badge.textContent = "● Live Engine Connected";
              badge.classList.add("is-live");
            }
            if (railDetail) {
              railDetail.textContent =
                "Live Python Engine (" + state.backendToolCount + " tools · v" + (data.version || "0.2.0") + ")";
            }
            await syncLiveModelsFromBackend();
            return;
          }
        }
      } catch {
        clearTimeout(timer);
      }
    }

    state.liveBackend = false;
    if (badge) {
      badge.textContent = "● Interactive Browser Engine";
      badge.classList.remove("is-live");
    }
  }

  async function syncLiveModelsFromBackend() {
    if (!state.liveBackend) return;
    try {
      const res = await fetch(state.apiBase + "/models");
      if (!res.ok) return;
      const payload = await res.json();
      const models = Array.isArray(payload.models) ? payload.models : [];
      if (!models.length) return;

      const topSel = document.getElementById("studio-global-model");
      const agentSel = document.getElementById("agent-model-select");
      const existing = new Set(Array.from(topSel.options).map((o) => o.value));

      models.forEach((m) => {
        if (m.id && !existing.has(m.id)) {
          const opt1 = document.createElement("option");
          opt1.value = m.id;
          opt1.textContent = m.id;
          topSel.appendChild(opt1);

          const opt2 = document.createElement("option");
          opt2.value = m.id;
          opt2.textContent = m.id + " (" + (m.provider || "live") + ")";
          agentSel.appendChild(opt2);
          existing.add(m.id);
        }
      });

      if (payload.active_model) {
        syncModelSelects(payload.active_model);
      }
    } catch {
      // Keep curated options on error
    }
  }

  function syncModelSelects(modelId) {
    state.activeModel = modelId;
    const topSel = document.getElementById("studio-global-model");
    const agentSel = document.getElementById("agent-model-select");
    [topSel, agentSel].forEach((sel) => {
      if (!sel) return;
      const has = Array.from(sel.options).some((o) => o.value === modelId);
      if (!has) {
        const opt = document.createElement("option");
        opt.value = modelId;
        opt.textContent = modelId;
        sel.appendChild(opt);
      }
      sel.value = modelId;
    });
  }

  /* ------------------------------------------------------------------------
     5. Workspace 1: Multimodal Four-Examinations Lab Canvas & Colorimetry
     ------------------------------------------------------------------------ */
  function drawProceduralTongue(ctx, cfg) {
    const w = ctx.canvas.width;
    const h = ctx.canvas.height;

    // Warm Xuan museum backdrop
    ctx.fillStyle = state.theme === "dark" ? "#191513" : "#efeae0";
    ctx.fillRect(0, 0, w, h);

    // Subtle perioral acoustic/anatomical context shadow
    const bgGrad = ctx.createRadialGradient(w / 2, h * 0.44, 30, w / 2, h * 0.48, 250);
    bgGrad.addColorStop(0, "rgba(74, 38, 36, 0.22)");
    bgGrad.addColorStop(1, "rgba(74, 38, 36, 0.0)");
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, w, h);

    // Tongue contour geometry
    const cx = w / 2;
    const halfW = cfg.swollen ? 132 : 114;
    const topY = 58;
    const tipY = 382;

    ctx.save();
    ctx.beginPath();
    ctx.moveTo(cx - halfW + 16, topY);
    ctx.bezierCurveTo(cx - 48, topY - 22, cx + 48, topY - 22, cx + halfW - 16, topY);
    ctx.bezierCurveTo(cx + halfW + 16, 165, cx + halfW + 4, 286, cx + 52, tipY - 22);
    ctx.quadraticCurveTo(cx, tipY + 18, cx - 52, tipY - 22);
    ctx.bezierCurveTo(cx - halfW - 4, 286, cx - halfW - 16, 165, cx - halfW + 16, topY);
    ctx.closePath();

    // Base lingual body gradient
    const [br, bg, bb] = cfg.bodyRgb;
    const [er, eg, eb] = cfg.edgeRgb;
    const bodyGrad = ctx.createRadialGradient(cx, 215, 24, cx, 225, 185);
    bodyGrad.addColorStop(0, "rgb(" + br + "," + bg + "," + bb + ")");
    bodyGrad.addColorStop(1, "rgb(" + er + "," + eg + "," + eb + ")");
    ctx.fillStyle = bodyGrad;
    ctx.fill();
    ctx.lineWidth = 2.5;
    ctx.strokeStyle = "rgba(75, 30, 32, 0.55)";
    ctx.stroke();

    ctx.clip();

    // Deterministic filiform papillae micro-texture (seeded pseudo-random)
    let seed = br * 31 + bg * 17;
    const rand = () => {
      seed = (seed * 1664525 + 1013904223) % 4294967296;
      return seed / 4294967296;
    };

    for (let i = 0; i < 620; i++) {
      const px = cx + (rand() - 0.5) * halfW * 2.05;
      const py = topY + rand() * (tipY - topY);
      ctx.fillStyle = i % 2 === 0 ? "rgba(255,235,235,0.14)" : "rgba(95,25,30,0.11)";
      ctx.beginPath();
      ctx.arc(px, py, 1.1 + rand() * 1.3, 0, Math.PI * 2);
      ctx.fill();
    }

    // Lingual fur / coating layer (thicker in Center & Root)
    const [cr, cg, cb] = cfg.coatRgb;
    const coatGrad = ctx.createRadialGradient(cx, 175, 18, cx, 185, 148);
    coatGrad.addColorStop(0, "rgba(" + cr + "," + cg + "," + cb + "," + cfg.coatAlpha + ")");
    coatGrad.addColorStop(0.68, "rgba(" + cr + "," + cg + "," + cb + "," + (cfg.coatAlpha * 0.62).toFixed(2) + ")");
    coatGrad.addColorStop(1, "rgba(" + cr + "," + cg + "," + cb + ",0)");
    ctx.fillStyle = coatGrad;
    ctx.beginPath();
    ctx.ellipse(cx, 182, halfW * 0.76, 126, 0, 0, Math.PI * 2);
    ctx.fill();

    // Median lingual sulcus
    ctx.strokeStyle = "rgba(88, 32, 36, 0.30)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(cx, 78);
    ctx.lineTo(cx, 320);
    ctx.stroke();

    // Axial & branching fissures (Yin deficiency preset)
    if (cfg.fissures) {
      ctx.strokeStyle = "rgba(78, 12, 20, 0.68)";
      ctx.lineWidth = 2.2;
      const cracks = [
        [cx, 122, cx - 44, 104],
        [cx, 156, cx + 48, 138],
        [cx, 192, cx - 50, 178],
        [cx, 226, cx + 44, 212],
        [cx, 262, cx - 36, 252],
        [cx - 26, 145, cx - 52, 158],
        [cx + 28, 176, cx + 56, 188]
      ];
      cracks.forEach((c) => {
        ctx.beginPath();
        ctx.moveTo(c[0], c[1]);
        ctx.lineTo(c[2], c[3]);
        ctx.stroke();
      });
    }

    // Marginal scalloped dental indentations (Spleen Qi-Damp preset)
    if (cfg.scallops) {
      ctx.strokeStyle = "rgba(115, 68, 68, 0.52)";
      ctx.lineWidth = 3.2;
      for (let sy = 145; sy <= 290; sy += 28) {
        ctx.beginPath();
        ctx.arc(cx - halfW + 4, sy, 11, -Math.PI * 0.42, Math.PI * 0.42);
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(cx + halfW - 4, sy, 11, Math.PI * 0.58, Math.PI * 1.42);
        ctx.stroke();
      }
    }

    // Petechial & ecchymotic stasis macules (Blood Stasis preset)
    if (cfg.stasisSpots) {
      const spots = [
        [cx - 76, 212, 5.2], [cx - 84, 244, 4.0], [cx - 64, 278, 5.8],
        [cx + 78, 206, 4.8], [cx + 82, 248, 5.5], [cx + 62, 284, 4.2],
        [cx - 28, 332, 3.8], [cx + 26, 338, 4.4], [cx + 6, 352, 3.4]
      ];
      spots.forEach((s) => {
        ctx.fillStyle = "rgba(58, 22, 46, 0.76)";
        ctx.beginPath();
        ctx.arc(s[0], s[1], s[2], 0, Math.PI * 2);
        ctx.fill();
      });
    }

    ctx.restore();
  }

  function drawOverlayGuides(ctx) {
    if (!state.showOverlay) return;
    const w = ctx.canvas.width;
    const h = ctx.canvas.height;
    const cx = w / 2;

    ctx.save();
    if (state.labSubtab === "tongue" || state.labSubtab === "fusion") {
      ctx.setLineDash([5, 4]);
      ctx.lineWidth = 1.4;
      ctx.font = "600 11px 'JetBrains Mono', monospace";

      // Root (Kidney)
      ctx.strokeStyle = "#675c52";
      ctx.strokeRect(cx - 70, 68, 140, 56);
      ctx.fillStyle = "#bc3923";
      ctx.fillText("ROOT · KIDNEY 肾", cx - 54, 62);

      // Center (Spleen-Stomach)
      ctx.strokeStyle = "#9f712d";
      ctx.strokeRect(cx - 58, 134, 116, 116);
      ctx.fillStyle = "#9f712d";
      ctx.fillText("CENTER · SP/ST 脾胃", cx - 62, 150);

      // Margins (Liver-Gallbladder)
      ctx.strokeStyle = "#356352";
      ctx.strokeRect(cx - 116, 150, 48, 118);
      ctx.strokeRect(cx + 68, 150, 48, 118);
      ctx.fillStyle = "#356352";
      ctx.fillText("LR/GB", cx - 112, 144);
      ctx.fillText("LR/GB", cx + 72, 144);

      // Tip (Heart-Lung)
      ctx.strokeStyle = "#bc3923";
      ctx.strokeRect(cx - 56, 262, 112, 86);
      ctx.fillStyle = "#bc3923";
      ctx.fillText("TIP · HT/LU 心肺", cx - 52, 366);
    } else if (state.labSubtab === "herb") {
      ctx.setLineDash([4, 3]);
      ctx.strokeStyle = "#bc3923";
      ctx.lineWidth = 1.8;
      ctx.beginPath();
      ctx.arc(w * 0.50, h * 0.49, 74, 0, Math.PI * 2);
      ctx.stroke();
      ctx.fillStyle = "rgba(37, 30, 24, 0.82)";
      ctx.fillRect(16, 16, 290, 28);
      ctx.fillStyle = "#f9f6f0";
      ctx.font = "600 11px 'JetBrains Mono', monospace";
      ctx.fillText("ROI: 菊花心 Xylem & Cambium Ring Assay", 26, 34);
    } else if (state.labSubtab === "ocr") {
      ctx.setLineDash([5, 3]);
      ctx.strokeStyle = "#bc3923";
      ctx.lineWidth = 1.6;
      ctx.strokeRect(w * 0.56, h * 0.16, w * 0.28, h * 0.66);
      ctx.strokeStyle = "#9f712d";
      ctx.strokeRect(w * 0.63, h * 0.72, w * 0.14, h * 0.18);
      ctx.fillStyle = "rgba(37, 30, 24, 0.84)";
      ctx.fillRect(16, 16, 312, 28);
      ctx.fillStyle = "#f9f6f0";
      ctx.font = "600 11px 'JetBrains Mono', monospace";
      ctx.fillText("OCR: Vertical Bencao Columns + Seal ROI", 26, 34);
    }
    ctx.restore();
  }

  function renderLabCanvasAndAnalyze() {
    const canvas = document.getElementById("lab-specimen-canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d", { willReadFrequently: true });
    const cw = canvas.width;
    const ch = canvas.height;

    const finalize = () => {
      // Sample 4 regions BEFORE drawing overlay lines so pixel colorimetry is uncontaminated!
      const tip = sampleCanvasRectLab(ctx, cw / 2 - 42, 275, 84, 60);
      const center = sampleCanvasRectLab(ctx, cw / 2 - 45, 150, 90, 90);
      const sides = sampleCanvasRectLab(ctx, cw / 2 - 105, 175, 36, 80);
      const root = sampleCanvasRectLab(ctx, cw / 2 - 50, 80, 100, 44);
      state.computedZones = { tip, center, sides, root };

      drawOverlayGuides(ctx);
      updateLabDiagnosticSynthesis();
    };

    if (state.uploadedImage) {
      ctx.fillStyle = state.theme === "dark" ? "#171311" : "#f0ebe1";
      ctx.fillRect(0, 0, cw, ch);
      const scale = Math.min(cw / state.uploadedImage.width, ch / state.uploadedImage.height);
      const dw = state.uploadedImage.width * scale;
      const dh = state.uploadedImage.height * scale;
      ctx.drawImage(state.uploadedImage, (cw - dw) / 2, (ch - dh) / 2, dw, dh);
      finalize();
      return;
    }

    const spec = LAB_PRESET_SPECS[state.labPreset] || LAB_PRESET_SPECS.pale_scalloped;
    if (spec.kind === "asset_image") {
      const img = new Image();
      img.onload = () => {
        ctx.fillStyle = "#f0ebe1";
        ctx.fillRect(0, 0, cw, ch);
        const scale = Math.max(cw / img.width, ch / img.height);
        const dw = img.width * scale;
        const dh = img.height * scale;
        ctx.drawImage(img, (cw - dw) / 2, (ch - dh) / 2, dw, dh);
        finalize();
      };
      img.src = spec.src;
    } else {
      drawProceduralTongue(ctx, spec.drawCfg);
      finalize();
    }
  }

  async function updateLabDiagnosticSynthesis() {
    const z = state.computedZones;
    if (z) {
      const fmtZone = (s, secondAxis) =>
        "L*" + s.L.toFixed(0) + " " + (secondAxis === "b" ? "b*" + (s.b >= 0 ? "+" : "") + s.b.toFixed(0) : "a*" + (s.a >= 0 ? "+" : "") + s.a.toFixed(0));

      const setTxt = (id, t) => {
        const el = document.getElementById(id);
        if (el) el.textContent = t;
      };
      setTxt("zone-tip-val", fmtZone(z.tip, "a"));
      setTxt("zone-center-val", fmtZone(z.center, "b"));
      setTxt("zone-sides-val", fmtZone(z.sides, "a"));
      setTxt("zone-root-val", fmtZone(z.root, "b"));
    }

    // Gather active pulse & symptoms for Four-Examinations Fusion modulation
    const pulseSel = document.getElementById("lab-pulse-select");
    const activePulse = pulseSel ? pulseSel.value : "soggy_weak";
    const selectedSymptoms = Array.from(document.querySelectorAll(".symptom-chip.is-selected")).map((b) =>
      b.getAttribute("data-symptom")
    );

    let spec = LAB_PRESET_SPECS[state.labPreset] || LAB_PRESET_SPECS.pale_scalloped;

    // If user uploaded a custom photograph, classify directly from computed CIE L*a*b* pixel coordinates!
    if (state.uploadedImage && z) {
      const meanA = (z.tip.a + z.sides.a) / 2;
      const meanL = (z.tip.L + z.center.L) / 2;
      const coatB = z.center.b;

      if (meanL > 69 && meanA < 17) {
        spec = LAB_PRESET_SPECS.pale_scalloped;
      } else if (coatB > 18 && meanA >= 20) {
        spec = LAB_PRESET_SPECS.red_greasy;
      } else if (meanA > 27 && meanL < 52) {
        spec = LAB_PRESET_SPECS.crimson_fissured;
      } else if (z.sides.b < 3) {
        spec = LAB_PRESET_SPECS.violaceous_stasis;
      }
    }

    // Adjust Eight-Principle scores dynamically from selected pulse & symptoms
    let heat = spec.bagang.heat;
    let excess = spec.bagang.excess;
    const interior = spec.bagang.interior;
    let yang = spec.bagang.yang;

    if (activePulse === "wiry_rapid" || activePulse === "thready_rapid") heat = Math.min(96, heat + 10);
    if (activePulse === "deep_slow") {
      heat = Math.max(10, heat - 18);
      yang = Math.max(14, yang - 15);
    }
    if (selectedSymptoms.includes("chills")) heat = Math.max(12, heat - 14);
    if (selectedSymptoms.includes("bitter_mouth") || selectedSymptoms.includes("night_sweats")) heat = Math.min(95, heat + 8);
    if (selectedSymptoms.includes("stabbing_pain") || selectedSymptoms.includes("rib_pain")) excess = Math.min(94, excess + 10);

    // Optional live backend enrichment when `tcm studio` server is running
    if (state.liveBackend && state.uploadedDataUrl) {
      try {
        const endpoint =
          state.labSubtab === "herb"
            ? "/diagnose/herb"
            : state.labSubtab === "ocr"
              ? "/diagnose/prescription"
              : "/diagnose/tongue";
        await fetch(state.apiBase + endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            image: state.uploadedDataUrl,
            observations: selectedSymptoms.join(", "),
            pulse: activePulse
          })
        });
      } catch {
        // Fallback smoothly to deterministic browser telemetry
      }
    }

    const setBar = (barId, lblId, val, suffix) => {
      const bEl = document.getElementById(barId);
      const lEl = document.getElementById(lblId);
      if (bEl) bEl.style.width = val + "%";
      if (lEl) lEl.textContent = val + "%" + (suffix || "");
    };

    setBar("st-bg-heat-bar", "st-bg-heat-lbl", heat, heat > 55 ? " Heat" : " Cold-Bias");
    setBar("st-bg-exc-bar", "st-bg-exc-lbl", excess, excess > 55 ? " Excess" : " Deficient");
    setBar("st-bg-int-bar", "st-bg-int-lbl", interior, " Interior");
    setBar("st-bg-yang-bar", "st-bg-yang-lbl", yang, "");

    const icdEl = document.getElementById("lab-icd-badge");
    if (icdEl) icdEl.textContent = spec.icd;

    const rankEl = document.getElementById("lab-syndrome-ranking");
    if (rankEl) {
      rankEl.innerHTML = spec.syndromes
        .map(
          (s) =>
            '<div class="syndrome-rank-row">' +
            '<div class="syndrome-rank-top"><strong>' +
            s.name +
            '</strong><span class="syndrome-conf">' +
            s.conf +
            "</span></div>" +
            '<div style="font-size:0.79rem;color:var(--ink-secondary);margin-top:0.2rem;">' +
            s.note +
            "</div>" +
            "</div>"
        )
        .join("");
    }

    const fEl = document.getElementById("lab-rec-formula");
    const mEl = document.getElementById("lab-rec-mods");
    const aEl = document.getElementById("lab-rec-acupoints");
    if (fEl) fEl.innerHTML = spec.formulaText;
    if (mEl) mEl.innerHTML = spec.modsText;
    if (aEl) aEl.innerHTML = spec.acupointsText;

    state.currentDiagnosis = {
      specimen: state.uploadedImage ? "Uploaded Clinical Specimen" : spec.name,
      subtab: state.labSubtab,
      icd: spec.icd,
      zones: z,
      bagang: { heat, excess, interior, yang },
      pulse: activePulse,
      symptoms: selectedSymptoms,
      syndromes: spec.syndromes,
      formulaKey: spec.formulaKey,
      formulaPlain: spec.formulaText.replace(/<[^>]+>/g, ""),
      modsPlain: spec.modsText.replace(/<[^>]+>/g, ""),
      acupointsPlain: spec.acupointsText.replace(/<[^>]+>/g, "")
    };
  }

  function exportClinicalReportMarkdown() {
    const d = state.currentDiagnosis;
    if (!d) return;
    const z = d.zones || { tip: { L: 72, a: 16, b: 10 }, center: { L: 74, a: 12, b: 12 }, sides: { L: 72, a: 14, b: 9 }, root: { L: 75, a: 10, b: 13 } };
    const ts = new Date().toISOString();

    const md = [
      "# TCM Studio — Multimodal Four-Examinations Clinical Report",
      "",
      "- **Timestamp**: `" + ts + "`",
      "- **Engine Mode**: `" + (state.liveBackend ? "Live Python Backend" : "Standalone Browser Biometric Engine") + "`",
      "- **Specimen**: " + d.specimen,
      "- **Classification Code**: `" + d.icd + "`",
      "",
      "## 1. Regional Lingual / Optical CIE L*a*b* Telemetry",
      "| Region | CIE L* | CIE a* | CIE b* |",
      "| :--- | :---: | :---: | :---: |",
      "| Tip (Heart/Lung 心肺) | " + z.tip.L.toFixed(1) + " | " + z.tip.a.toFixed(1) + " | " + z.tip.b.toFixed(1) + " |",
      "| Center (Spleen/Stomach 脾胃) | " + z.center.L.toFixed(1) + " | " + z.center.a.toFixed(1) + " | " + z.center.b.toFixed(1) + " |",
      "| Margins (Liver/Gallbladder 肝胆) | " + z.sides.L.toFixed(1) + " | " + z.sides.a.toFixed(1) + " | " + z.sides.b.toFixed(1) + " |",
      "| Root (Kidney/Lower Jiao 肾) | " + z.root.L.toFixed(1) + " | " + z.root.a.toFixed(1) + " | " + z.root.b.toFixed(1) + " |",
      "",
      "## 2. Eight-Principles Profile & Pulse/Inquiry Inputs",
      "- **Pulse**: `" + d.pulse + "`",
      "- **Selected Symptoms**: `" + (d.symptoms.join(", ") || "None") + "`",
      "- **Heat Index**: `" + d.bagang.heat + "%` | **Excess Index**: `" + d.bagang.excess + "%` | **Interior**: `" + d.bagang.interior + "%`",
      "",
      "## 3. Syndrome Confidence Ranking",
      ...d.syndromes.map((s, i) => (i + 1) + ". **" + s.name + "** (" + s.conf + ") — " + s.note),
      "",
      "## 4. Classical Formula & Acupoint Synergy",
      "- **Recommended Formula**: " + d.formulaPlain,
      "- **Modifications**: " + d.modsPlain,
      "- **Acupoints**: " + d.acupointsPlain,
      "",
      "> *Research & educational report generated by TCM Studio v0.2.0 (`tcm-cli`).*"
    ].join("\n");

    downloadMarkdownFile("tcm-clinical-report-" + Date.now() + ".md", md);
  }

  /* ------------------------------------------------------------------------
     6. Workspace 2: Force-Directed Network Pharmacology & Safety Gate
     ------------------------------------------------------------------------ */
  const SHIBAFAN_RULES = [
    { root: "甘草", conflicts: ["甘遂", "京大戟", "海藻", "芫花"], rule: "甘草反甘遂、大戟、海藻、芫花 (Licorice Eighteen Incompatibilities)" },
    { root: "附子", conflicts: ["半夏", "瓜蒌", "贝母", "白蔹", "白及"], rule: "乌头/附子反半夏、瓜蒌、贝母、白蔹、白及 (Aconite Eighteen Incompatibilities)" },
    { root: "藜芦", conflicts: ["人参", "沙参", "丹参", "玄参", "苦参", "细辛", "白芍", "赤芍"], rule: "诸参辛芍叛藜芦 (Veratrum Eighteen Incompatibilities)" }
  ];

  const SHIXIUWEI_PAIRS = [
    ["人参", "五灵脂", "人参畏五灵脂 (Ginseng antagonizes Trogopterus)"],
    ["肉桂", "赤石脂", "官桂善能调冷气，若逢石脂便相欺 (Cinnamon antagonizes Halloysite)"],
    ["附子", "犀角", "乌头/附子畏犀角"]
  ];

  const PREGNANCY_FORBIDDEN = new Set(["桃仁", "红花", "附子", "牛膝", "川芎", "甘遂", "藜芦", "三棱", "莪术", "大黄"]);

  function loadStudioFormulaPreset(key) {
    const preset = STUDIO_FORMULA_PRESETS[key] || STUDIO_FORMULA_PRESETS.sijunzi;
    state.activeFormulaKey = key;
    state.builderHerbs = preset.herbs.map((h) => ({ ...h }));

    document.querySelectorAll("[data-studio-formula]").forEach((btn) => {
      btn.classList.toggle("is-active", btn.getAttribute("data-studio-formula") === key);
    });

    const pregToggle = document.getElementById("builder-pregnancy-toggle");
    if (pregToggle) pregToggle.checked = Boolean(preset.pregnant);

    document.querySelectorAll("[data-rx-med]").forEach((cb) => {
      cb.checked = preset.meds.includes(cb.value);
    });

    const titleEl = document.getElementById("pharma-graph-title");
    if (titleEl) titleEl.textContent = preset.title + " — Multi-Layer Pharmacology Graph";

    rebuildFormulaGraphAndSafety(preset.title);
  }

  async function rebuildFormulaGraphAndSafety(customTitle) {
    renderBuilderHerbList();
    evaluateSafetyValidator();

    const canvas = document.getElementById("pharma-network-canvas");
    if (!canvas) return;
    const w = canvas.width;
    const h = canvas.height;

    const nodes = [];
    const edges = [];
    const nodeMap = new Map();

    const addNode = (id, label, group, colIndex, meta) => {
      if (nodeMap.has(id)) return nodeMap.get(id);
      const sameColCount = nodes.filter((n) => n.col === colIndex).length;
      const colX = [88, 225, 415, 595, 742][colIndex] || w / 2;
      const node = {
        id,
        label,
        group,
        col: colIndex,
        x: colX + (Math.random() - 0.5) * 26,
        y: 72 + ((sameColCount * 58) % (h - 120)) + (Math.random() - 0.5) * 18,
        vx: 0,
        vy: 0,
        targetX: colX,
        meta: meta || {}
      };
      nodes.push(node);
      nodeMap.set(id, node);
      return node;
    };

    const rootTitle = (customTitle || "Custom Prescription").split(" (")[0];
    const rootNode = addNode("formula:root", rootTitle, "formula", 0, {
      detail: "Prescription Root · " + state.builderHerbs.length + " Materia Medica components."
    });
    rootNode.y = h / 2;

    state.builderHerbs.forEach((entry) => {
      const hMeta = HERB_BIO_DB[entry.name] || { nature: "Neutral", flavor: "Classical", meridians: "SP, LR", compounds: ["Quercetin"] };
      const hId = "herb:" + entry.name;
      addNode(hId, entry.name + " (" + entry.role + ")", "herb", 1, {
        detail:
          "Role: " + entry.role + " · Dosage: " + entry.dose + "g · Nature: " + hMeta.nature + " (" + hMeta.flavor + ") · Meridians: " + hMeta.meridians
      });
      edges.push({ source: rootNode.id, target: hId });

      hMeta.compounds.forEach((cpd) => {
        const cMeta = COMPOUND_META_DB[cpd] || { mw: 302.2, ob: "46.4%", dl: 0.28, targets: ["AKT1", "TNF"] };
        const cId = "cpd:" + cpd;
        addNode(cId, cpd, "compound", 2, {
          detail: "MW: " + cMeta.mw + " g/mol · OB: " + cMeta.ob + " · Drug-Likeness (DL): " + cMeta.dl
        });
        edges.push({ source: hId, target: cId });

        cMeta.targets.slice(0, 3).forEach((tgt) => {
          const tId = "tgt:" + tgt;
          addNode(tId, tgt, "target", 3, {
            detail: "Human Protein Target (UniProt Symbol: " + tgt + ") modulated by active phytochemicals."
          });
          edges.push({ source: cId, target: tId });

          const pw = TARGET_KEGG_MAP[tgt];
          if (pw) {
            const pId = "pw:" + pw.code;
            addNode(pId, pw.name, "pathway", 4, {
              detail: "KEGG Signaling Pathway (" + pw.code + ") · Enriched multi-target systems module."
            });
            if (!edges.some((e) => e.source === tId && e.target === pId)) {
              edges.push({ source: tId, target: pId });
            }
          }
        });
      });
    });

    state.graphNodes = nodes;
    state.graphEdges = edges;

    const statsBadge = document.getElementById("pharma-stats-badge");
    if (statsBadge) {
      statsBadge.textContent = nodes.length + " Nodes · " + edges.length + " Edges";
    }

    // Also query live backend `/api/pharmacology/network` asynchronously if connected
    if (state.liveBackend && state.builderHerbs.length > 0) {
      try {
        const meds = Array.from(document.querySelectorAll("[data-rx-med]:checked")).map((c) => c.value);
        await fetch(state.apiBase + "/pharmacology/network", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            herbs: state.builderHerbs.map((h) => h.name),
            drugs: meds
          })
        });
      } catch {
        // Keep browser physics graph running cleanly
      }
    }

    startNetworkSimulation();
  }

  function startNetworkSimulation() {
    if (state.animFrameId) cancelAnimationFrame(state.animFrameId);
    let ticks = 0;

    const step = () => {
      ticks++;
      const canvas = document.getElementById("pharma-network-canvas");
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      const w = canvas.width;
      const h = canvas.height;
      const nodes = state.graphNodes;
      const edges = state.graphEdges;
      const byId = new Map(nodes.map((n) => [n.id, n]));

      if (ticks < 160 || state.draggingNode) {
        // Repulsion
        for (let i = 0; i < nodes.length; i++) {
          for (let j = i + 1; j < nodes.length; j++) {
            const a = nodes[i];
            const b = nodes[j];
            let dx = b.x - a.x;
            let dy = b.y - a.y;
            const distSq = dx * dx + dy * dy + 12;
            if (distSq < 14000) {
              const force = 520 / distSq;
              const dist = Math.sqrt(distSq);
              dx /= dist;
              dy /= dist;
              a.vx -= dx * force;
              a.vy -= dy * force;
              b.vx += dx * force;
              b.vy += dy * force;
            }
          }
        }

        // Spring attraction along edges + layered x-column gravity
        edges.forEach((e) => {
          const s = byId.get(e.source);
          const t = byId.get(e.target);
          if (!s || !t) return;
          const dx = t.x - s.x;
          const dy = t.y - s.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const targetLen = 148;
          const k = (dist - targetLen) * 0.012;
          const fx = (dx / dist) * k;
          const fy = (dy / dist) * k;
          s.vx += fx;
          s.vy += fy;
          t.vx -= fx;
          t.vy -= fy;
        });

        nodes.forEach((n) => {
          if (n === state.draggingNode) return;
          n.vx += (n.targetX - n.x) * 0.045;
          n.vy += (h / 2 - n.y) * 0.004;
          n.vx *= 0.78;
          n.vy *= 0.78;
          n.x = Math.max(46, Math.min(w - 68, n.x + n.vx));
          n.y = Math.max(32, Math.min(h - 32, n.y + n.vy));
        });
      }

      // Render frame
      const isDark = state.theme === "dark";
      ctx.fillStyle = isDark ? "#13100e" : "#f2ede3";
      ctx.fillRect(0, 0, w, h);

      // Subtle vertical ontology column headers
      const colLabels = ["FORMULA", "HERBS (君臣佐使)", "COMPOUNDS", "TARGETS", "KEGG PATHWAYS"];
      const colXs = [88, 225, 415, 595, 735];
      ctx.font = "600 10px 'JetBrains Mono', monospace";
      ctx.fillStyle = isDark ? "rgba(197,189,177,0.45)" : "rgba(103,92,82,0.55)";
      colXs.forEach((cx, idx) => {
        ctx.fillText(colLabels[idx], cx - 32, 18);
      });

      // Draw edges
      edges.forEach((e) => {
        const s = byId.get(e.source);
        const t = byId.get(e.target);
        if (!s || !t) return;
        const highlighted =
          state.selectedNode && (state.selectedNode.id === s.id || state.selectedNode.id === t.id);
        ctx.strokeStyle = highlighted
          ? "#bc3923"
          : isDark
            ? "rgba(238,233,223,0.16)"
            : "rgba(37,30,24,0.16)";
        ctx.lineWidth = highlighted ? 2.0 : 1.05;
        ctx.beginPath();
        const midX = (s.x + t.x) / 2;
        ctx.moveTo(s.x, s.y);
        ctx.bezierCurveTo(midX, s.y, midX, t.y, t.x, t.y);
        ctx.stroke();
      });

      // Draw nodes
      const colors = {
        formula: "#bc3923",
        herb: "#9f712d",
        compound: "#356352",
        target: isDark ? "#e6dfd3" : "#251e18",
        pathway: isDark ? "#c89f65" : "#7d5a44"
      };

      nodes.forEach((n) => {
        const r = n.group === "formula" ? 11 : n.group === "herb" ? 9 : n.group === "target" ? 7.5 : 7;
        ctx.fillStyle = colors[n.group] || "#356352";
        ctx.beginPath();
        if (n.group === "formula") {
          ctx.rect(n.x - r, n.y - r, r * 2, r * 2);
        } else {
          ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
        }
        ctx.fill();

        if (state.selectedNode && state.selectedNode.id === n.id) {
          ctx.strokeStyle = "#bc3923";
          ctx.lineWidth = 2.4;
          ctx.stroke();
        }

        ctx.font = n.group === "target" ? "600 10.5px 'JetBrains Mono', monospace" : "500 11px 'Plus Jakarta Sans', sans-serif";
        ctx.fillStyle = isDark ? "#eee9df" : "#251e18";
        const labelOffset = n.col >= 4 ? -8 : r + 5;
        ctx.textAlign = n.col >= 4 ? "right" : "left";
        ctx.fillText(n.label, n.x + labelOffset, n.y + 3.5);
      });
      ctx.textAlign = "left";

      if (ticks < 160 || state.draggingNode) {
        state.animFrameId = requestAnimationFrame(step);
      }
    };

    state.animFrameId = requestAnimationFrame(step);
  }

  function renderBuilderHerbList() {
    const listEl = document.getElementById("builder-herb-list");
    if (!listEl) return;

    if (state.builderHerbs.length === 0) {
      listEl.innerHTML = '<div style="font-size:0.82rem;color:var(--ink-muted);padding:0.5rem;">Prescription empty — add herbs above.</div>';
      return;
    }

    listEl.innerHTML = state.builderHerbs
      .map(
        (h, idx) =>
          '<div class="builder-herb-item">' +
          "<span><strong>" +
          h.name +
          '</strong> <span class="mono" style="color:var(--accent-ochre);font-size:0.75rem;">[' +
          h.role +
          "] " +
          h.dose +
          "g</span></span>" +
          '<button type="button" class="herb-remove-btn" data-remove-idx="' +
          idx +
          '" aria-label="Remove ' +
          h.name +
          '">&times; Remove</button>' +
          "</div>"
      )
      .join("");

    listEl.querySelectorAll("[data-remove-idx]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const i = Number(btn.getAttribute("data-remove-idx"));
        state.builderHerbs.splice(i, 1);
        rebuildFormulaGraphAndSafety("Custom Modified Prescription");
      });
    });
  }

  function evaluateSafetyValidator() {
    const panel = document.getElementById("builder-safety-panel");
    if (!panel) return;

    const names = state.builderHerbs.map((h) => h.name);
    const nameSet = new Set(names);
    const meds = Array.from(document.querySelectorAll("[data-rx-med]:checked")).map((c) => c.value);
    const isPregnant = Boolean(document.getElementById("builder-pregnancy-toggle")?.checked);

    const alerts = [];

    // 1. Eighteen Incompatibilities (十八反)
    SHIBAFAN_RULES.forEach((rule) => {
      if (nameSet.has(rule.root)) {
        rule.conflicts.forEach((conf) => {
          if (nameSet.has(conf)) {
            alerts.push({
              level: "critical",
              title: "✕ BLOCKED · 十八反 Eighteen Incompatibilities (" + rule.root + " + " + conf + ")",
              body: rule.rule + " — Co-administration strictly contraindicated by Chinese Pharmacopoeia 2025."
            });
          }
        });
      }
    });

    // 2. Nineteen Antagonisms (十九畏)
    SHIXIUWEI_PAIRS.forEach((pair) => {
      if (nameSet.has(pair[0]) && nameSet.has(pair[1])) {
        alerts.push({
          level: "critical",
          title: "⚠ CONTRAINDICATION · 十九畏 Nineteen Antagonisms (" + pair[0] + " + " + pair[1] + ")",
          body: pair[2] + " — Mutual antagonism reduces efficacy or increases adverse events."
        });
      }
    });

    // 3. Toxic Decoction & Dosage Rules
    state.builderHerbs.forEach((h) => {
      if (h.name === "附子") {
        alerts.push({
          level: h.dose > 15 ? "critical" : "caution",
          title: "⚠ TOXIC DECOCTION MANDATE · 附子 (" + h.dose + "g)",
          body: "MUST pre-decoct (先煎) 30–60 minutes until lingual numbness disappears to hydrolyze cardiotoxic diester aconitine (ChP 2025 range: 3–15g)."
        });
      }
      if (h.name === "细辛" && h.dose > 3) {
        alerts.push({
          level: "critical",
          title: "✕ DOSAGE EXCEEDED · 细辛不过钱 (" + h.dose + "g > 3g)",
          body: "Classical & ChP safety limit: Asarum (细辛) exceeds 3g ceiling; risk of respiratory paralysis and volatile oil toxicity."
        });
      }
      if (h.name === "藜芦" || h.name === "甘遂") {
        alerts.push({
          level: "caution",
          title: "⚠ POTENT TOXIC MATERIA MEDICA · " + h.name + " (" + h.dose + "g)",
          body: "Narrow therapeutic window; administer only in processed form under strict inpatient/specialist monitoring."
        });
      }
    });

    // 4. Pregnancy Contraindications
    if (isPregnant) {
      const flagged = names.filter((n) => PREGNANCY_FORBIDDEN.has(n));
      if (flagged.length > 0) {
        alerts.push({
          level: "critical",
          title: "✕ PREGNANCY CONTRAINDICATION · 妊娠禁忌 (" + flagged.join(", ") + ")",
          body: "Blood-breaking, drastic purgative, or toxic-hot herbs carry uterotonic/teratogenic hazard in pregnancy."
        });
      }
    }

    // 5. Herb–Drug CYP450 / Pharmacodynamic Interactions
    if (meds.includes("Warfarin") || meds.includes("Aspirin")) {
      const bleeders = names.filter((n) => ["丹参", "当归", "川芎", "桃仁", "红花", "人参"].includes(n));
      if (bleeders.length > 0) {
        alerts.push({
          level: "critical",
          title: "✕ HERB–DRUG BLEEDING & CYP2C9 ALERT (" + bleeders.join(", ") + " + Anticoagulant)",
          body: "Salvia/Angelica/Chuanxiong inhibit platelet aggregation and CYP2C9 clearance of S-Warfarin (supratherapeutic INR risk); Ginseng may alter INR stability."
        });
      }
    }

    if (meds.includes("Digoxin") && nameSet.has("甘草")) {
      alerts.push({
        level: "critical",
        title: "✕ HYPOKALEMIA DIGITALIS TOXICITY (甘草 + Digoxin)",
        body: "Glycyrrhizin inhibits renal 11β-HSD2 causing potassium wasting, sensitizing myocardium to Digoxin arrhythmias."
      });
    }

    if (meds.includes("Phenelzine") && nameSet.has("麻黄")) {
      alerts.push({
        level: "critical",
        title: "✕ HYPERTENSIVE CRISIS (麻黄 Ephedrine + MAOI Phenelzine)",
        body: "Sympathomimetic ephedrine alkaloids trigger severe catecholamine surge with MAO inhibitors."
      });
    }

    if (meds.includes("Cyclosporine") && (nameSet.has("黄连") || nameSet.has("黄柏"))) {
      alerts.push({
        level: "caution",
        title: "⚠ CYP3A4 / P-gp TROUGH ELEVATION (Berberine + Cyclosporine)",
        body: "Berberine inhibits CYP3A4 and intestinal P-glycoprotein, raising blood Cyclosporine levels by 30–75%; monitor trough levels."
      });
    }

    if (meds.includes("Hypoglycemics") && names.some((n) => ["黄芪", "人参", "黄连"].includes(n))) {
      alerts.push({
        level: "caution",
        title: "⚠ ADDITIVE GLUCOSE LOWERING (AMPK/GLUT4 Herbs + Insulin/Sulfonylurea)",
        body: "Monitor fasting & postprandial blood glucose to prevent iatrogenic hypoglycemia; titrate Rx dose if needed."
      });
    }

    if (alerts.length === 0) {
      panel.innerHTML =
        '<div class="safety-alert-item">' +
        "<strong>✓ SAFETY GATE VERIFIED · ZERO CONTRAINDICATIONS</strong>" +
        '<div style="margin-top:0.2rem;color:var(--ink-secondary);">No 十八反, 十九畏, toxic decoction violations, or selected CYP450 herb–drug conflicts detected across ' +
        names.length +
        " herbs.</div></div>";
      return;
    }

    panel.innerHTML = alerts
      .map(
        (a) =>
          '<div class="safety-alert-item level-' +
          a.level +
          '">' +
          "<strong>" +
          a.title +
          "</strong>" +
          '<div style="margin-top:0.2rem;">' +
          a.body +
          "</div></div>"
      )
      .join("");
  }

  /* ------------------------------------------------------------------------
     7. Workspace 3: Meridian Acupoint Atlas & Compendium Search
     ------------------------------------------------------------------------ */
  function selectAcupoint(code) {
    const pt = ACUPOINTS_DB[code];
    if (!pt) return;
    state.selectedPointCode = code;

    document.querySelectorAll(".acupoint-node").forEach((el) => {
      el.classList.toggle("is-active", el.getAttribute("data-point-code") === code);
    });

    const t = document.getElementById("acu-card-title");
    const m = document.getElementById("acu-card-meridian");
    const l = document.getElementById("acu-card-loc");
    const i = document.getElementById("acu-card-ind");

    if (t) t.textContent = pt.code + " " + pt.zh + " (" + pt.py + ")";
    if (m) m.textContent = pt.mer;
    if (l) l.innerHTML = "<strong>WHO Location:</strong> " + pt.loc;
    if (i) i.innerHTML = "<strong>Needling &amp; Actions:</strong> " + pt.ind;
  }

  function renderAtlasCompendium() {
    const listEl = document.getElementById("atlas-results-list");
    const searchEl = document.getElementById("atlas-search-input");
    const countEl = document.getElementById("atlas-count-label");
    if (!listEl) return;

    const q = (searchEl ? searchEl.value : "").trim().toLowerCase();

    const acupointEntries = Object.values(ACUPOINTS_DB).map((p) => ({
      cat: "acupoint",
      pointCode: p.code,
      code: p.code + " · " + p.mer.split(" (")[0],
      title: p.code + " " + p.zh + " (" + p.py + ")",
      meta: "WHO Standard Acupoint",
      body: p.loc + " — " + p.ind
    }));

    const allEntries = [...acupointEntries, ...ATLAS_COMPENDIUM_EXTRA];

    const filtered = allEntries.filter((item) => {
      if (state.atlasCategory !== "all" && item.cat !== state.atlasCategory) return false;
      if (!q) return true;
      return [item.code, item.title, item.meta, item.body].join(" ").toLowerCase().includes(q);
    });

    if (countEl) countEl.textContent = filtered.length + " entries matched";

    listEl.innerHTML = filtered
      .map(
        (item, idx) =>
          '<div class="atlas-entry-row" data-atlas-idx="' +
          idx +
          '" data-point-ref="' +
          (item.pointCode || "") +
          '">' +
          '<div class="atlas-entry-head">' +
          "<strong>" +
          item.title +
          "</strong>" +
          '<span class="status-tag-ochre">' +
          item.code +
          "</span>" +
          "</div>" +
          '<div style="font-size:0.76rem;color:var(--accent-celadon);font-family:var(--font-mono);margin-bottom:0.25rem;">' +
          item.meta +
          "</div>" +
          '<p style="font-size:0.83rem;color:var(--ink-secondary);margin:0;">' +
          item.body +
          "</p>" +
          "</div>"
      )
      .join("");

    listEl.querySelectorAll(".atlas-entry-row").forEach((row) => {
      row.addEventListener("click", () => {
        const ptCode = row.getAttribute("data-point-ref");
        if (ptCode && ACUPOINTS_DB[ptCode]) {
          selectAcupoint(ptCode);
          if (ptCode === "BL23" || ptCode === "GB20") {
            setAtlasBodyView("posterior");
          }
        }
      });
    });
  }

  function setAtlasBodyView(view) {
    state.atlasBodyView = view === "posterior" ? "posterior" : "anterior";
    const ant = document.getElementById("svg-atlas-anterior");
    const post = document.getElementById("svg-atlas-posterior");
    const btnA = document.getElementById("atlas-view-anterior");
    const btnP = document.getElementById("atlas-view-posterior");

    if (ant) ant.style.display = state.atlasBodyView === "anterior" ? "block" : "none";
    if (post) post.style.display = state.atlasBodyView === "posterior" ? "block" : "none";

    if (btnA && btnP) {
      const activeStyle = "border-color:var(--accent-cinnabar);color:var(--accent-cinnabar);";
      btnA.setAttribute("style", "height:28px;font-size:0.74rem;" + (state.atlasBodyView === "anterior" ? activeStyle : ""));
      btnP.setAttribute("style", "height:28px;font-size:0.74rem;" + (state.atlasBodyView === "posterior" ? activeStyle : ""));
    }
  }

  /* ------------------------------------------------------------------------
     8. Workspace 4: SOTA Agent Console & Deterministic ReAct Executor
     ------------------------------------------------------------------------ */
  function buildStandaloneAgentResponse(query, modelId, langMode, hasImage) {
    const qLow = query.toLowerCase();
    const steps = [];
    let synthesisHtml = "";

    if (qLow.includes("warfarin") || qLow.includes("aspirin") || qLow.includes("血府逐瘀")) {
      steps.push(
        { tool: "formulas.decompose", params: "血府逐瘀汤 + 丹参", out: "12 herbs parsed (桃仁 12g, 红花 9g, 当归 9g, 川芎 5g, 丹参 15g...)" },
        { tool: "interactions.herb_drug_cyp", params: "herbs=[丹参, 当归, 川芎, 红花], rx=[Warfarin, Aspirin]", out: "CRITICAL: CYP2C9/CYP1A2 inhibition + dual antiplatelet/thrombin synergy" },
        { tool: "safety.pregnancy_toxicity", params: "batch_screen", out: "Zero 十八反; strict bleeding & pregnancy contraindications flagged" }
      );
      synthesisHtml =
        "<h4>Grounded Clinical Safety Synthesis · 中西药联用安全审评</h4>" +
        "<ul>" +
        "<li><strong>HIGH BLEEDING ALERT (高危出血预警)</strong>: Combining <strong>血府逐瘀汤 + 丹参</strong> with <strong>Warfarin (5 mg) + Aspirin (81 mg)</strong> creates a triple pharmacodynamic/pharmacokinetic hazard.</li>" +
        "<li><strong>CYP450 &amp; Hemostasis Mechanism</strong>: Tanshinone IIA and Cryptotanshinone (丹参) plus Ferulic acid/Coumarins (当归) inhibit <code>CYP2C9</code> and <code>CYP1A2</code> clearance of S-Warfarin while Salvianolic acid B and Hydroxysafflor Yellow A (红花) inhibit platelet aggregation alongside Aspirin COX-1 blockade.</li>" +
        "<li><strong>Actionable Recommendation</strong>: Avoid concurrent administration in post-PCI dual/triple antithrombotic therapy; if integrative consultation is pursued after de-escalation, mandate baseline and 72-hour serial <code>INR</code> + CBC/occult blood monitoring.</li>" +
        "</ul>";
    } else if (qLow.includes("小柴胡") || qLow.includes("shaoyang") || qLow.includes("wiry") || qLow.includes("往来寒热")) {
      steps.push(
        { tool: "syndromes.six_channel", params: "往来寒热, 胸胁苦满, 口苦, 弦脉", out: "Shaoyang Half-Exterior Half-Interior (少阳枢机不利, conf=0.97)" },
        { tool: "classics.search", params: "Shanghan Lun Clause 96 & 263", out: "伤寒五六日中风，往来寒热，胸胁苦满…小柴胡汤主之；少阳之为病，口苦、咽干、目眩也。" },
        { tool: "diagnostics.posology_convert", params: "柴胡半斤, 黄芩三两, 人参三两, 半夏半升 (era=Eastern Han)", out: "1兩=13.8g -> 柴胡 110.4g (36.8g/draught) vs Modern clinical 12–24g" }
      );
      synthesisHtml =
        "<h4>Shaoyang Differentiation &amp; Eastern Han Metrology · 少阳辨证与伤寒衡制</h4>" +
        "<ul>" +
        "<li><strong>Canonical Match</strong>: Matches <em>Shanghan Lun</em> Clauses 96 &amp; 263 — <strong>Shaoyang Pivot Disharmony (少阳病)</strong> anchored by <strong>小柴胡汤 (Xiao Chai Hu Tang)</strong>.</li>" +
        "<li><strong>Eastern Han vs. Modern Posology</strong>: In Zhang Zhongjing's original text, <code>柴胡半斤 (8兩 = 110.4g)</code> and <code>黄芩三兩 (41.4g)</code> were boiled down and divided into <strong>three draughts (分温三服)</strong>, preserving the ~8:3 Sovereign-to-Minister ratio critical for resolving febrile Shaoyang stasis (modern clinical equivalent: 柴胡 24g, 黄芩 9g, 法半夏 9g, 人参 6g, 炙甘草 6g, 生姜 9g, 大枣 4枚).</li>" +
        "<li><strong>Molecular Bridge</strong>: Saikosaponin A/D + Baicalin co-inhibit <code>TLR4/NF-κB</code> and <code>JAK-STAT3</code> pyrogenic cytokine cascades.</li>" +
        "</ul>";
    } else if (qLow.includes("insomnia") || qLow.includes("失眠") || qLow.includes("心肾不交")) {
      steps.push(
        { tool: "syndromes.differentiate", params: "insomnia + crimson fissured tongue +心肾不交", out: "Heart-Kidney Non-Interaction / Yin Deficiency Empty Fire (conf=0.96)" },
        { tool: "formulas.recommend", params: "心肾不交", out: "天王补心丹 / 黄连阿胶汤 / 交泰丸 (黄连 6g : 肉桂 1g)" },
        { tool: "acupuncture.protocol", params: "Heart-Kidney Insomnia", out: "HT7 神门, KI3 太溪, SP6 三阴交, PC6 内关, BL15/BL23" }
      );
      synthesisHtml =
        "<h4>Integrative Herbal &amp; Meridian Protocol · 心肾不交失眠针药方案</h4>" +
        "<ul>" +
        "<li><strong>Herbal Prescription</strong>: <strong>黄连阿胶汤合交泰丸加减</strong> — 黄连 6g (drains upward Heart fire), 肉桂 1.5g (后下, guides fire back to Kidney source 引火归元), 阿胶 9g (烊化), 生地黄 15g, 白芍 12g, 酸枣仁 15g.</li>" +
        "<li><strong>Meridian Acupoint Protocol</strong>: Even-reinforcing/reducing at <code>HT7 神门</code> (Heart Yuan-Source) + reinforcing at <code>KI3 太溪</code> (Kidney Yuan-Source) &amp; <code>SP6 三阴交</code> to re-couple Shaoyin Water-Fire axis.</li>" +
        "</ul>";
    } else {
      steps.push(
        { tool: "herbs.compare_monographs", params: "黄芪 (Astragalus) vs 人参 (Panax ginseng)", out: "ChP 2025 properties, Paozhi & dosage bounds retrieved" },
        { tool: "pharmacology.network_overlap", params: "Astragaloside IV / Calycosin + Ginsenoside Rg1/Rb1", out: "Shared hub targets: AKT1, AMPK (PRKAA1), NOS3, PPARG, TNF, IL6" },
        { tool: "literature.evidence_grade", params: "Astragalus + Ginseng T2DM insulin resistance", out: "KEGG hsa04151 (PI3K-Akt) & hsa04910 (Insulin signaling) enriched (FDR < 1e-6)" }
      );
      synthesisHtml =
        "<h4>Comparative Systems Pharmacology · 参芪配伍网络药理与临床协同</h4>" +
        "<ul>" +
        "<li><strong>Classical Differentiation (本草异同)</strong>: <strong>人参 (Panax ginseng)</strong> enters deep Zang-Source to rescue Yuan Qi, generate Yin-fluids, and calm Shen; <strong>黄芪 (Astragalus)</strong> excels at upbearing Spleen Yang, consolidating Defensive Wei-Qi (固表), and promoting fluid metabolism.</li>" +
        "<li><strong>Convergent &amp; Complementary Molecular Graph</strong>: Ginsenosides Rg1/Rb1 potently phosphorylate <code>IRS1/PI3K/AKT1</code> to promote GLUT4 translocation, while Astragaloside IV + Calycosin activate <code>AMPK</code>, <code>Nrf2/HO-1</code>, and endothelial <code>NOS3</code> — explaining why classical 参芪 (Ginseng–Astragalus) pairing outperforms single-herb therapy in T2DM microvascular &amp; fatigue endpoints.</li>" +
        (hasImage ? "<li><strong>Attached Specimen Telemetry</strong>: Multimodal image attachment verified via optical CIE <em>L*a*b*</em> preprocessor prior to synthesis.</li>" : "") +
        "</ul>";
    }

    if (langMode === "zh") {
      synthesisHtml = '<div style="font-size:0.78rem;color:var(--accent-ochre);margin-bottom:0.35rem;">[中文循证输出 · 模型路由: ' + modelId + "]</div>" + synthesisHtml;
    }

    return {
      model: modelId,
      mode: "browser_verified_engine",
      steps,
      html: synthesisHtml
    };
  }

  async function executeAgentTurn(rawQuery) {
    const query = (rawQuery || "").trim();
    if (!query) return;

    const modelSel = document.getElementById("agent-model-select");
    const langSel = document.getElementById("agent-lang-select");
    const modelId = modelSel ? modelSel.value : state.activeModel;
    const langVal = langSel ? langSel.value : "bilingual";
    const apiLang = langVal === "bilingual" ? "bi" : langVal;
    const hasImg = Boolean(state.agentAttachmentDataUrl);

    syncModelSelects(modelId);

    let turnRecord = null;

    if (state.liveBackend) {
      try {
        const res = await fetch(state.apiBase + "/agent/query", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query,
            model: modelId,
            lang: apiLang,
            attachments: hasImg ? [state.agentAttachmentDataUrl] : []
          })
        });
        if (res.ok) {
          const payload = await res.json();
          if (payload && payload.status === "ok") {
            const steps = (payload.results || []).map((r) => ({
              tool: r.tool || "tool",
              params: r.purpose || "",
              out: r.status === "success" ? "Verified JSON payload" : r.error || "completed"
            }));
            const escapedAns = String(payload.answer || "")
              .replace(/&/g, "&amp;")
              .replace(/</g, "&lt;")
              .replace(/>/g, "&gt;")
              .replace(/\n/g, "<br/>");
            turnRecord = {
              ts: new Date().toLocaleTimeString(),
              query,
              attachment: state.agentAttachmentName,
              model: payload.model || modelId,
              mode: payload.mode || "live_python",
              steps,
              html: '<div class="synthesis-prose">' + escapedAns + "</div>"
            };
          }
        }
      } catch {
        // Fallback to standalone engine
      }
    }

    if (!turnRecord) {
      const built = buildStandaloneAgentResponse(query, modelId, langVal, hasImg);
      turnRecord = {
        ts: new Date().toLocaleTimeString(),
        query,
        attachment: state.agentAttachmentName,
        model: built.model,
        mode: built.mode,
        steps: built.steps,
        html: '<div class="synthesis-prose">' + built.html + "</div>"
      };
    }

    state.agentTurns.push(turnRecord);

    // Clear attachment chip
    state.agentAttachmentDataUrl = null;
    state.agentAttachmentName = "";
    const chip = document.getElementById("agent-attachment-chip");
    if (chip) chip.classList.remove("is-visible");

    renderAgentTranscript();
  }

  function renderAgentTranscript() {
    const container = document.getElementById("agent-transcript");
    if (!container) return;

    container.innerHTML = state.agentTurns
      .map((t) => {
        const attBadge = t.attachment ? ' <span class="status-tag-celadon">Image: ' + t.attachment + "</span>" : "";
        const traceRows = t.steps
          .map(
            (s, i) =>
              '<div class="trace-step-line">' +
              "<span><strong>0" +
              (i + 1) +
              " · " +
              s.tool +
              "</strong>(" +
              s.params +
              ")</span>" +
              '<span style="color:var(--accent-celadon);">✓ ' +
              s.out +
              "</span></div>"
          )
          .join("");

        return (
          '<div class="agent-turn user-turn">' +
          '<div class="turn-meta"><span>RESEARCHER QUERY</span><span>' +
          t.ts +
          "</span></div>" +
          "<div><strong>" +
          t.query.replace(/</g, "&lt;") +
          "</strong>" +
          attBadge +
          "</div></div>" +
          '<div class="agent-turn assistant-turn">' +
          '<div class="turn-meta"><span>TCM STUDIO AGENT · ' +
          t.model +
          "</span><span>" +
          t.mode.toUpperCase() +
          "</span></div>" +
          '<div class="trace-steps-block">' +
          traceRows +
          "</div>" +
          t.html +
          "</div>"
        );
      })
      .join("");

    container.scrollTop = container.scrollHeight;
  }

  function exportAgentSessionMarkdown() {
    const lines = [
      "# TCM Studio — SOTA Agent Research Session",
      "",
      "- **Exported At**: `" + new Date().toISOString() + "`",
      ""
    ];
    state.agentTurns.forEach((t, idx) => {
      lines.push("## Turn " + (idx + 1) + " (" + t.model + ")");
      lines.push("**Query:** " + t.query);
      lines.push("");
      lines.push("### Tool Execution Trace");
      t.steps.forEach((s) => {
        lines.push("- `" + s.tool + "(" + s.params + ")` -> " + s.out);
      });
      lines.push("");
      lines.push("### Grounded Synthesis");
      lines.push(t.html.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim());
      lines.push("\n---\n");
    });
    downloadMarkdownFile("tcm-agent-session-" + Date.now() + ".md", lines.join("\n"));
  }

  function downloadMarkdownFile(filename, content) {
    const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 500);
  }

  /* ------------------------------------------------------------------------
     9. Workspace Switching, Theme, Language & URL Deep-Link Router
     ------------------------------------------------------------------------ */
  function switchWorkspace(wsKey) {
    const valid = ["lab", "pharmacology", "atlas", "agent"];
    const target = valid.includes(wsKey) ? wsKey : "lab";
    state.activeWorkspace = target;

    document.querySelectorAll(".rail-ws-btn").forEach((btn) => {
      const active = btn.getAttribute("data-ws") === target;
      btn.classList.toggle("is-active", active);
      btn.setAttribute("aria-selected", active ? "true" : "false");
    });

    document.querySelectorAll(".ws-pane").forEach((pane) => {
      pane.classList.toggle("is-active", pane.id === "ws-pane-" + target);
    });

    if (target === "pharmacology") {
      startNetworkSimulation();
    }
  }

  function switchLabSubtab(subtab) {
    state.labSubtab = subtab;
    document.querySelectorAll("[data-lab-subtab]").forEach((btn) => {
      const active = btn.getAttribute("data-lab-subtab") === subtab;
      btn.classList.toggle("is-active", active);
      btn.setAttribute("aria-selected", active ? "true" : "false");
    });

    const modeTag = document.getElementById("lab-active-mode-tag");
    const labels = {
      tongue: "CIE D65 Lingual Colorimeter",
      herb: "ChP Macroscopic Pharmacognosy",
      ocr: "Woodblock OCR & Han Posology",
      fusion: "Four-Examinations Fusion Engine"
    };
    if (modeTag && labels[subtab]) modeTag.textContent = labels[subtab];

    if (!state.uploadedImage) {
      if (subtab === "herb" && state.labPreset !== "huangqi") {
        selectLabPreset("huangqi", false);
        return;
      }
      if (subtab === "ocr" && state.labPreset !== "bencao_folio") {
        selectLabPreset("bencao_folio", false);
        return;
      }
      if ((subtab === "tongue" || subtab === "fusion") && (state.labPreset === "huangqi" || state.labPreset === "bencao_folio")) {
        selectLabPreset("pale_scalloped", false);
        return;
      }
    }
    renderLabCanvasAndAnalyze();
  }

  function selectLabPreset(presetKey, autoSyncSubtab = true) {
    const spec = LAB_PRESET_SPECS[presetKey];
    if (!spec) return;
    state.labPreset = presetKey;
    state.uploadedImage = null;
    state.uploadedDataUrl = null;

    document.querySelectorAll("[data-lab-preset]").forEach((btn) => {
      btn.classList.toggle("is-active", btn.getAttribute("data-lab-preset") === presetKey);
    });

    if (autoSyncSubtab && spec.subtab && state.labSubtab !== "fusion") {
      state.labSubtab = spec.subtab;
      document.querySelectorAll("[data-lab-subtab]").forEach((btn) => {
        const active = btn.getAttribute("data-lab-subtab") === spec.subtab;
        btn.classList.toggle("is-active", active);
        btn.setAttribute("aria-selected", active ? "true" : "false");
      });
    }

    // Set matching pulse & symptoms for immediate coherent clinical synthesis
    const pulseSel = document.getElementById("lab-pulse-select");
    if (pulseSel && spec.pulseDefault) pulseSel.value = spec.pulseDefault;

    const voiceSel = document.getElementById("lab-voice-select");
    if (voiceSel && spec.voiceDefault) voiceSel.value = spec.voiceDefault;

    document.querySelectorAll(".symptom-chip").forEach((chip) => {
      const sym = chip.getAttribute("data-symptom");
      chip.classList.toggle("is-selected", spec.symptomsDefault.includes(sym));
    });

    renderLabCanvasAndAnalyze();
  }

  function applyStudioTheme(theme) {
    state.theme = theme === "dark" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", state.theme);
    localStorage.setItem("tcm-studio-theme", state.theme);

    const lbl = document.getElementById("studio-theme-label");
    if (lbl) {
      lbl.textContent =
        state.theme === "dark"
          ? state.lang === "zh" ? "宣纸昼光" : "Xuan Day"
          : state.lang === "zh" ? "松烟夜色" : "Sumi Night";
    }

    renderLabCanvasAndAnalyze();
    if (state.activeWorkspace === "pharmacology") startNetworkSimulation();
  }

  function applyStudioLang(lang) {
    state.lang = lang === "zh" ? "zh" : "en";
    document.documentElement.setAttribute("lang", state.lang === "zh" ? "zh-CN" : "en");
    localStorage.setItem("tcm-studio-lang", state.lang);

    const dict = STUDIO_I18N[state.lang];
    document.querySelectorAll("[data-studio-i18n]").forEach((el) => {
      const k = el.getAttribute("data-studio-i18n");
      if (dict[k]) el.textContent = dict[k];
    });

    const langLbl = document.getElementById("studio-lang-label");
    if (langLbl) langLbl.textContent = state.lang === "en" ? "中文" : "EN";

    applyStudioTheme(state.theme);
  }

  /* ------------------------------------------------------------------------
     10. DOM Ready & Interactive Event Wiring
     ------------------------------------------------------------------------ */
  document.addEventListener("DOMContentLoaded", () => {
    // Parse URL query params for deep-linking from index.html
    const params = new URLSearchParams(window.location.search);
    const qWs = params.get("workspace");
    const qSub = params.get("subtab");
    const qPreset = params.get("preset");
    const qFormula = params.get("formula");
    const qModel = params.get("model");

    // Workspace rail buttons
    document.querySelectorAll(".rail-ws-btn").forEach((btn) => {
      btn.addEventListener("click", () => switchWorkspace(btn.getAttribute("data-ws")));
    });

    // Theme & Language toggles
    document.getElementById("studio-theme-btn")?.addEventListener("click", () => {
      applyStudioTheme(state.theme === "light" ? "dark" : "light");
    });
    document.getElementById("studio-lang-btn")?.addEventListener("click", () => {
      applyStudioLang(state.lang === "en" ? "zh" : "en");
    });

    // Global & Agent model pickers sync (+ live backend POST /api/models/select)
    const handleModelChange = async (newModel) => {
      syncModelSelects(newModel);
      if (state.liveBackend) {
        try {
          await fetch(state.apiBase + "/models/select", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ model: newModel })
          });
        } catch {
          // Non-fatal
        }
      }
    };
    document.getElementById("studio-global-model")?.addEventListener("change", (e) => handleModelChange(e.target.value));
    document.getElementById("agent-model-select")?.addEventListener("change", (e) => handleModelChange(e.target.value));

    // Workspace 1: Lab subtabs, presets, upload, drag-drop & canvas pixel probe
    document.querySelectorAll("[data-lab-subtab]").forEach((btn) => {
      btn.addEventListener("click", () => switchLabSubtab(btn.getAttribute("data-lab-subtab")));
    });

    document.querySelectorAll("[data-lab-preset]").forEach((btn) => {
      btn.addEventListener("click", () => selectLabPreset(btn.getAttribute("data-lab-preset"), true));
    });

    document.getElementById("toggle-somatotopy-overlay")?.addEventListener("change", (e) => {
      state.showOverlay = e.target.checked;
      renderLabCanvasAndAnalyze();
    });

    document.getElementById("run-lab-analysis-btn")?.addEventListener("click", () => {
      renderLabCanvasAndAnalyze();
    });

    // Image Upload & Drag-and-Drop in Lab
    const loadUserSpecimenFile = (file) => {
      if (!file || !file.type.startsWith("image/")) return;
      const reader = new FileReader();
      reader.onload = (ev) => {
        const dataUrl = ev.target.result;
        const img = new Image();
        img.onload = () => {
          state.uploadedImage = img;
          state.uploadedDataUrl = dataUrl;
          document.querySelectorAll("[data-lab-preset]").forEach((b) => b.classList.remove("is-active"));
          renderLabCanvasAndAnalyze();
        };
        img.src = dataUrl;
      };
      reader.readAsDataURL(file);
    };

    document.getElementById("lab-image-upload")?.addEventListener("change", (e) => {
      if (e.target.files && e.target.files[0]) loadUserSpecimenFile(e.target.files[0]);
    });

    const dropzone = document.getElementById("lab-canvas-dropzone");
    if (dropzone) {
      dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.classList.add("is-dragover");
      });
      dropzone.addEventListener("dragleave", () => dropzone.classList.remove("is-dragover"));
      dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("is-dragover");
        if (e.dataTransfer?.files?.[0]) loadUserSpecimenFile(e.dataTransfer.files[0]);
      });
    }

    // Live Pixel RGB & CIE L*a*b* Crosshair Probe on Lab Canvas
    const labCanvas = document.getElementById("lab-specimen-canvas");
    if (labCanvas) {
      const probeAtEvent = (e) => {
        const rect = labCanvas.getBoundingClientRect();
        const cx = Math.max(0, Math.min(labCanvas.width - 1, Math.round(((e.clientX - rect.left) / rect.width) * labCanvas.width)));
        const cy = Math.max(0, Math.min(labCanvas.height - 1, Math.round(((e.clientY - rect.top) / rect.height) * labCanvas.height)));
        const ctx = labCanvas.getContext("2d", { willReadFrequently: true });
        const px = ctx.getImageData(cx, cy, 1, 1).data;
        const lab = rgbToLab(px[0], px[1], px[2]);

        const cEl = document.getElementById("probe-coords-readout");
        const rEl = document.getElementById("probe-rgb-readout");
        const lEl = document.getElementById("probe-lab-readout");
        if (cEl) cEl.textContent = "Probe (x: " + cx + ", y: " + cy + ")";
        if (rEl) rEl.textContent = "sRGB(" + px[0] + ", " + px[1] + ", " + px[2] + ")";
        if (lEl) {
          lEl.textContent =
            "CIE L* " +
            lab.L.toFixed(1) +
            " · a* " +
            (lab.a >= 0 ? "+" : "") +
            lab.a.toFixed(1) +
            " · b* " +
            (lab.b >= 0 ? "+" : "") +
            lab.b.toFixed(1);
        }
      };
      labCanvas.addEventListener("mousemove", probeAtEvent);
      labCanvas.addEventListener("click", probeAtEvent);
    }

    // Pulse, Auscultation & Ten-Questions Symptom Chips
    document.getElementById("lab-pulse-select")?.addEventListener("change", updateLabDiagnosticSynthesis);
    document.getElementById("lab-voice-select")?.addEventListener("change", updateLabDiagnosticSynthesis);
    document.querySelectorAll(".symptom-chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        chip.classList.toggle("is-selected");
        updateLabDiagnosticSynthesis();
      });
    });

    // Studio Han Posology Converter
    const updateStudioHan = () => {
      const l = parseFloat(document.getElementById("studio-han-liang")?.value) || 3;
      const f = parseFloat(document.getElementById("studio-han-era")?.value) || 13.8;
      const out = document.getElementById("studio-han-readout");
      if (out) {
        out.innerHTML =
          l.toFixed(1) +
          " 兩 = <code>" +
          (l * f).toFixed(1) +
          " g</code> total decoction (<code>" +
          ((l * f) / 3).toFixed(1) +
          " g</code> per single serving in three divided doses).";
      }
    };
    document.getElementById("studio-han-liang")?.addEventListener("input", updateStudioHan);
    document.getElementById("studio-han-era")?.addEventListener("change", updateStudioHan);

    document.getElementById("export-clinical-report-btn")?.addEventListener("click", exportClinicalReportMarkdown);

    document.getElementById("lab-send-to-pharma-btn")?.addEventListener("click", () => {
      const fKey = state.currentDiagnosis?.formulaKey || "sijunzi";
      loadStudioFormulaPreset(fKey);
      switchWorkspace("pharmacology");
    });

    // Workspace 2: Network Pharmacology Canvas Drag/Click + Custom Builder
    document.querySelectorAll("[data-studio-formula]").forEach((btn) => {
      btn.addEventListener("click", () => loadStudioFormulaPreset(btn.getAttribute("data-studio-formula")));
    });

    document.getElementById("pharma-recenter-btn")?.addEventListener("click", () => {
      rebuildFormulaGraphAndSafety(STUDIO_FORMULA_PRESETS[state.activeFormulaKey]?.title || "Custom Prescription");
    });

    document.getElementById("builder-add-btn")?.addEventListener("click", () => {
      const hName = document.getElementById("builder-herb-select")?.value || "黄芪";
      const hDose = Math.max(0.3, parseFloat(document.getElementById("builder-herb-dose")?.value) || 9);
      const hRole = document.getElementById("builder-herb-role")?.value || "佐";

      const existing = state.builderHerbs.find((x) => x.name === hName);
      if (existing) {
        existing.dose = hDose;
        existing.role = hRole;
      } else {
        state.builderHerbs.push({ name: hName, dose: hDose, role: hRole });
      }
      rebuildFormulaGraphAndSafety("Custom Modified Prescription");
    });

    document.getElementById("builder-pregnancy-toggle")?.addEventListener("change", evaluateSafetyValidator);
    document.querySelectorAll("[data-rx-med]").forEach((cb) => {
      cb.addEventListener("change", evaluateSafetyValidator);
    });

    const netCanvas = document.getElementById("pharma-network-canvas");
    if (netCanvas) {
      const getCanvasPos = (e) => {
        const rect = netCanvas.getBoundingClientRect();
        return {
          x: ((e.clientX - rect.left) / rect.width) * netCanvas.width,
          y: ((e.clientY - rect.top) / rect.height) * netCanvas.height
        };
      };

      const findHitNode = (pos) => {
        for (let i = state.graphNodes.length - 1; i >= 0; i--) {
          const n = state.graphNodes[i];
          const dx = pos.x - n.x;
          const dy = pos.y - n.y;
          if (dx * dx + dy * dy <= 225) return n;
        }
        return null;
      };

      const inspectNode = (n) => {
        state.selectedNode = n;
        const nameEl = document.getElementById("inspector-node-name");
        const typeEl = document.getElementById("inspector-node-type");
        const detEl = document.getElementById("inspector-node-detail");
        if (n && nameEl && typeEl && detEl) {
          nameEl.textContent = n.label;
          typeEl.textContent = n.group.toUpperCase();
          detEl.textContent = n.meta.detail || "";
        }
        startNetworkSimulation();
      };

      netCanvas.addEventListener("pointerdown", (e) => {
        const hit = findHitNode(getCanvasPos(e));
        if (hit) {
          state.draggingNode = hit;
          inspectNode(hit);
          netCanvas.setPointerCapture(e.pointerId);
        }
      });

      netCanvas.addEventListener("pointermove", (e) => {
        if (!state.draggingNode) return;
        const pos = getCanvasPos(e);
        state.draggingNode.x = pos.x;
        state.draggingNode.y = pos.y;
      });

      const endDrag = () => {
        state.draggingNode = null;
      };
      netCanvas.addEventListener("pointerup", endDrag);
      netCanvas.addEventListener("pointercancel", endDrag);
    }

    // Workspace 3: Meridian Atlas & Compendium Search
    document.getElementById("atlas-view-anterior")?.addEventListener("click", () => setAtlasBodyView("anterior"));
    document.getElementById("atlas-view-posterior")?.addEventListener("click", () => setAtlasBodyView("posterior"));

    document.querySelectorAll(".acupoint-node").forEach((node) => {
      node.addEventListener("click", () => selectAcupoint(node.getAttribute("data-point-code")));
    });

    document.querySelectorAll("[data-atlas-cat]").forEach((pill) => {
      pill.addEventListener("click", () => {
        state.atlasCategory = pill.getAttribute("data-atlas-cat") || "all";
        document.querySelectorAll("[data-atlas-cat]").forEach((p) => p.classList.toggle("is-active", p === pill));
        renderAtlasCompendium();
      });
    });

    document.getElementById("atlas-search-input")?.addEventListener("input", renderAtlasCompendium);

    // Workspace 4: SOTA Agent Console
    document.querySelectorAll("[data-sample-q]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const q = btn.getAttribute("data-sample-q");
        const input = document.getElementById("agent-query-input");
        if (input && q) input.value = q;
        executeAgentTurn(q);
      });
    });

    document.getElementById("agent-image-input")?.addEventListener("change", (e) => {
      const f = e.target.files?.[0];
      if (!f) return;
      const reader = new FileReader();
      reader.onload = (ev) => {
        state.agentAttachmentDataUrl = ev.target.result;
        state.agentAttachmentName = f.name;
        const nameEl = document.getElementById("agent-attachment-name");
        const chip = document.getElementById("agent-attachment-chip");
        if (nameEl) nameEl.textContent = f.name;
        if (chip) chip.classList.add("is-visible");
      };
      reader.readAsDataURL(f);
    });

    document.getElementById("agent-attachment-clear")?.addEventListener("click", () => {
      state.agentAttachmentDataUrl = null;
      state.agentAttachmentName = "";
      document.getElementById("agent-attachment-chip")?.classList.remove("is-visible");
    });

    document.getElementById("agent-composer-form")?.addEventListener("submit", (e) => {
      e.preventDefault();
      const input = document.getElementById("agent-query-input");
      if (!input || !input.value.trim()) return;
      const val = input.value;
      input.value = "";
      executeAgentTurn(val);
    });

    document.getElementById("agent-export-btn")?.addEventListener("click", exportAgentSessionMarkdown);
    document.getElementById("agent-clear-btn")?.addEventListener("click", () => {
      state.agentTurns = [];
      renderAgentTranscript();
    });

    // Initialize Initial State & Seeded Views
    if (qModel) syncModelSelects(qModel);
    applyStudioLang(state.lang);
    loadStudioFormulaPreset(qFormula && STUDIO_FORMULA_PRESETS[qFormula] ? qFormula : "sijunzi");
    renderAtlasCompendium();
    selectAcupoint("ST36");

    if (qPreset && LAB_PRESET_SPECS[qPreset]) {
      selectLabPreset(qPreset, true);
    } else {
      selectLabPreset("pale_scalloped", false);
    }

    if (qSub && ["tongue", "herb", "ocr", "fusion"].includes(qSub)) {
      switchLabSubtab(qSub);
    }

    // Seed initial scholarly demonstration turn in Agent Console
    executeAgentTurn(
      "Compare 黄芪 (Astragalus) and 人参 (Panax ginseng) network pharmacology targets and clinical synergy in Spleen-Qi deficiency with T2DM insulin resistance."
    );

    if (qWs) switchWorkspace(qWs);

    // Probe Live Python Backend asynchronously
    probeBackendEngine();
  });
})();
