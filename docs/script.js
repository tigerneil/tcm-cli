/* ==========================================================================
   TCM Studio & CLI v0.2.0 — Flagship Landing Page Controller (docs/script.js)
   ========================================================================== */

(function () {
  "use strict";

  /* ------------------------------------------------------------------------
     1. Bilingual Copy Dictionary (EN / 中文)
     ------------------------------------------------------------------------ */
  const I18N = {
    en: {
      brandTitle: "TCM Studio",
      navMultimodal: "Multimodal",
      navWorkbench: "Workbench",
      navModels: "SOTA Models",
      navArch: "Architecture",
      navInstall: "CLI & Install",
      themeToggleNight: "Sumi Night",
      themeToggleDay: "Xuan Day",
      launchStudioCta: "Launch TCM Studio →",
      heroRubric: "Zhenglei Bencao Philology × Computational Systems Pharmacology",
      heroHeadline: "Multimodal Traditional Chinese Medicine, from Classical Canon to Molecular Graph.",
      heroLead:
        "<strong>TCM Studio &amp; CLI</strong> unifies Four-Examinations CIE <em>L*a*b*</em> vision &amp; pulse diagnostics (望闻问切), 45+ computational pharmacology &amp; clinical safety tools, and unified routing across 35+ SOTA foundation models in a single verifiable research instrument.",
      cmdTabStudio: "Studio Web App",
      cmdTabCli: "Multimodal CLI",
      cmdTabInstall: "Install",
      copyBtn: "Copy",
      cmdFootnoteStudio: "Starts local Python TCM Studio API engine at 127.0.0.1:8765 — or run 100% in-browser right now.",
      heroPrimaryCta: "Launch Interactive Studio →",
      heroSecondaryCta: "Inspect Four-Examinations Engine ↓",
      statTools: "Domain & Bio Tools",
      statModels: "SOTA Models (Nov 2026)",
      statVision: "Quantitative Vision",
      statSafety: "Clinical Safety Gate",
      heroPlateCaption:
        "Materia Medica Pharmacognosy & Molecular Saponin Architecture: Panax ginseng (人參), Radix Astragali (黃耆), Bencao Folio & Ginsenoside Rb1.",
      sec1Rubric: "Folio I · Four-Examinations Multimodal Engine",
      sec1Title: "Four-Examinations Diagnostics, Grounded in Optical & Acoustic Telemetry",
      sec1Sub:
        "Instead of opaque text prompts, TCM Studio extracts objective CIE L*a*b* chromatic coordinates, pharmacognosy tissue landmarks, Eastern Han posology ratios, and radial sphygmogram harmonics before invoking syndrome synthesis.",
      tab1Title: "Tongue Colorimetry",
      tab2Title: "Decoction Piece ID",
      tab3Title: "Classical Canon OCR",
      tab4Title: "28-Pulse & Acoustics",
      sec2Rubric: "Folio II · Formula Compatibility & Clinical Safety Gate",
      sec2Title: "Jun-Chen-Zuo-Shi Decomposition Meets Network Pharmacology & Safety",
      sec2Sub:
        "Inspect classical prescriptions or challenge the safety engine with Eighteen Incompatibilities (十八反) and Herb–Drug CYP450 / anticoagulant interactions before opening the full force-directed graph in TCM Studio.",
      openFullStudioBtn: "Open Full Interactive Studio →",
      sec3Rubric: "Folio III · Unified SOTA Foundation Model Router",
      sec3Title: "35+ Frontier & Open-Weight Models, One Deterministic Clinical Interface",
      sec3Sub:
        "Route multimodal tongue diagnostics, ancient Bencao OCR, multi-hop network pharmacology, or air-gapped hospital workloads across Anthropic, OpenAI, Google DeepMind, Chinese Frontier labs, xAI, Mistral, and local Ollama weights.",
      taskRecommenderLabel: "SOTA Task-Based Model Recommender",
      modelSearchLabel: "Filter by Provider, Model ID, or Capability",
      sec4Rubric: "Folio IV · Autonomous ReAct Architecture & 45+ Domain Tools",
      sec4Title: "Deterministic Biometrics + Multi-Step Tool Verification",
      sec4Sub:
        "Every query traverses a grounded four-stage scientific loop across 15 domain modules and 10+ live biomedical knowledge bases — eliminating unverified dosage or target hallucinations.",
      sec5Rubric: "Colophon · Installation, Documentation & FAQ",
      sec5Title: "Deploy in Seconds — Terminal CLI or Local Web Studio",
      sec5Sub:
        "Requires Python 3.10+. Works out-of-the-box with remote biomedical APIs or completely air-gapped with local Ollama weights."
    },
    zh: {
      brandTitle: "本草工作室 TCM Studio",
      navMultimodal: "四诊多模态",
      navWorkbench: "方剂药理台",
      navModels: "前沿大模型",
      navArch: "工具与架构",
      navInstall: "安装与文档",
      themeToggleNight: "松烟夜色",
      themeToggleDay: "宣纸昼光",
      launchStudioCta: "启动 TCM Studio →",
      heroRubric: "证类本草考据学 × 计算系统药理学与精密仪器",
      heroHeadline: "四诊合参，从本草典籍到分子药理的多模态中医工作室",
      heroLead:
        "<strong>TCM Studio &amp; CLI (v0.2.0)</strong> 将四诊（望舌象 CIE <em>L*a*b*</em> 色度、辨饮片、析古籍、切脉波）多模态诊断、45+ 计算药理与十八反/CYP临床安全工具，以及 35+ 前沿大模型路由统一于可验证的科研工作台。",
      cmdTabStudio: "启动 Web 工作室",
      cmdTabCli: "多模态命令行",
      cmdTabInstall: "一键安装",
      copyBtn: "复制",
      cmdFootnoteStudio: "在本地 localhost:8765 启动 Python 引擎，或直接点击下方按钮在浏览器内零配置运行。",
      heroPrimaryCta: "立即打开交互式 Studio →",
      heroSecondaryCta: "探索四诊多模态引擎 ↓",
      statTools: "中药与药理工具",
      statModels: "2026 前沿大模型",
      statVision: "舌象色度学定量",
      statSafety: "十八反与药物相互作用",
      heroPlateCaption:
        "本草生药学与皂苷分子构型标本：人参、蒙古黄芪饮片、《本草》刻本及人参皂苷 Rb1 / 黄芪甲苷化学结构。",
      sec1Rubric: "卷一 · 四诊合参多模态引擎",
      sec1Title: "以光学色度、显微性状与脉波谐波锚定中医辨证",
      sec1Sub:
        "告别黑盒纯文本提示词：先提取舌体分区的 CIE L*a*b* 定量坐标、道地饮片形成层与菊花心特征、东汉伤寒衡制换算及寸关尺脉波参数，再驱动八纲与脏腑辨证。",
      tab1Title: "望舌象色度",
      tab2Title: "辨道地饮片",
      tab3Title: "析古籍方笺",
      tab4Title: "闻声与切脉",
      sec2Rubric: "卷二 · 君臣佐使配伍与临床安全闸门",
      sec2Title: "经典名方拆解、多靶点网络药理与配伍禁忌实时核验",
      sec2Sub:
        "点击切换经典方剂或测试「人参+藜芦（十八反）」、「丹参+华法林（CYP2C9出血风险）」，即时检视活性分子—靶点通路并一键进入完整 Studio 力导向图谱。",
      openFullStudioBtn: "在完整 Studio 中打开图谱 →",
      sec3Rubric: "卷三 · 35+ 全球与中国前沿大模型统一路由",
      sec3Title: "35+ 旗舰与开源权重模型，统一于确定性工具链",
      sec3Sub:
        "按任务智能调度 Claude 5.5、GPT-6 Astra / Rosalind、Gemini 3.6、DeepSeek V4、Qwen 3.8、GLM-5.3、Kimi K3.1 或院内私有化 Ollama MedGemma / HuatuoGPT。",
      taskRecommenderLabel: "按中医科研场景推荐最佳模型",
      modelSearchLabel: "搜索厂商、模型 ID 或多模态能力",
      sec4Rubric: "卷四 · 自主规划智能体与 45+ 专业工具矩阵",
      sec4Title: "确定性生物计量计算 + 多步药典数据库核验",
      sec4Sub:
        "每次查询均历经四阶段闭环验证，覆盖 15 大工具模块与 10+ 权威生物医学数据库，杜绝剂量越界与靶点幻觉。",
      sec5Rubric: "跋 · 安装部署、技术文档与常见问答",
      sec5Title: "数秒内即可部署 — 终端 REPL 与本地 Web 工作室双形态",
      sec5Sub:
        "支持 Python 3.10+。既可开箱即用连接云端 API，亦可配合本地 Ollama 权重在医院内网离线运行。"
    }
  };

  /* ------------------------------------------------------------------------
     2. Hero Quickstart Commands
     ------------------------------------------------------------------------ */
  const HERO_COMMANDS = {
    studio: {
      cmd: "tcm studio --open",
      noteEn: "Starts local Python clinical engine at localhost:8765 — or run 100% in-browser right now.",
      noteZh: "启动本地 localhost:8765 临床与药理后端服务，或直接点击按钮在浏览器内独立运行。"
    },
    cli: {
      cmd: 'tcm -i tongue.jpg --model claude-opus-5-5 "Diagnose tongue & build formula network"',
      noteEn: "Streams CIE L*a*b* vision telemetry, Eight-Principle differentiation, and KEGG target enrichment.",
      noteZh: "多模态读取舌象照片，执行 L*a*b* 分区色度计算、八纲辨证与方剂网络药理富集。"
    },
    install: {
      cmd: 'pipx install "tcm-cli[all]" && tcm setup',
      noteEn: "Installs CLI + RDKit chemistry, NetworkX analysis, and Studio server with interactive key setup.",
      noteZh: "一键安装完整化学信息学、网络药理与 Studio 服务栈，并运行交互式密钥配置向导。"
    }
  };

  /* ------------------------------------------------------------------------
     3. Multimodal Engine Datasets (Tongue, Herb Pins, Pulse Waveforms)
     ------------------------------------------------------------------------ */
  const TONGUE_ARCHETYPES = [
    {
      key: "pale_scalloped",
      code: "PATTERN · SPLEEN QI DEFICIENCY WITH DAMPNESS",
      title: "脾虚湿盛证 — Pale Swollen Scalloped Tongue (淡白胖大齿痕舌)",
      desc: "Elevated luminance (L* > 72) with attenuated erythroid chrome (a* = +11.2) indicates diminished Qi-Blood perfusion to the lingual papillae; marginal dental indentations reflect interstitial fluid retention from impaired Spleen transformation.",
      L: "74.8",
      dL: "+9.4 vs norm (Pale)",
      a: "+11.2",
      da: "-11.6 vs norm (Hypoemic)",
      b: "+12.6",
      db: "Thin white moist fur",
      bodyFill: "#e3b3b0",
      bodyStroke: "#9d6866",
      coatFill: "#f6f3ee",
      coatOpacity: "0.72",
      fissures: 0,
      scallops: 1,
      stasis: 0,
      bagang: { heat: 24, heatLbl: "Cold-Biased (24%)", excess: 18, excessLbl: "Deficient (18%)", interior: 88, intLbl: "Interior (88%)", yang: 30, yangLbl: "Yin/Damp (30%)" },
      formula: "<strong>参苓白术散 / 六君子汤</strong> (Shen Ling Bai Zhu San) — Codonopsis, Atractylodes, Poria, Coix, Amomum",
      cli: 'tcm -i pale_tongue.jpg "Quantify L*a*b* & build Spleen-Qi formula"'
    },
    {
      key: "red_greasy",
      code: "PATTERN · DAMP-HEAT IN SPLEEN-STOMACH / HEPATOBILIARY TRACT",
      title: "肝胆/脾胃湿热证 — Red Body with Yellow Greasy Coating (红舌黄腻苔)",
      desc: "Strong positive erythroid shift (a* = +31.8) paired with high yellow-ochre fur chromaticity (b* = +24.5) reflects inflammatory hyperemia and turbid damp-heat accumulation across the Middle Jiao and Liver-Gallbladder margins.",
      L: "53.4",
      dL: "-12.0 vs norm (Deep Red)",
      a: "+31.8",
      da: "+9.0 vs norm (Hyperemic)",
      b: "+24.5",
      db: "Thick yellow greasy fur",
      bodyFill: "#c94c4c",
      bodyStroke: "#7a2323",
      coatFill: "#dfbe6f",
      coatOpacity: "0.84",
      fissures: 0,
      scallops: 0,
      stasis: 0,
      bagang: { heat: 86, heatLbl: "Heat (86%)", excess: 84, excessLbl: "Excess (84%)", interior: 90, intLbl: "Interior (90%)", yang: 78, yangLbl: "Yang Excess (78%)" },
      formula: "<strong>龙胆泻肝汤 / 连朴饮</strong> (Long Dan Xie Gan Tang) — Gentiana, Scutellaria, Gardenia, Coptis, Magnolia",
      cli: 'tcm -i damp_heat_tongue.jpg --model gpt-6.1-terra "Analyze yellow greasy fur"'
    },
    {
      key: "crimson_fissured",
      code: "PATTERN · YIN DEFICIENCY WITH EFFULGENT EMPTY FIRE",
      title: "阴虚火旺证 — Crimson Fissured Tongue with Scanty Coat (红绛裂纹少苔)",
      desc: "Low lightness (L* = 44.2) and intense crimson saturation (a* = +36.4) with exfoliated coating (coat opacity < 0.18) and axial lingual fissures signify exhaustion of Stomach-Kidney Yin fluids and unrestrained ministerial fire.",
      L: "44.2",
      dL: "-21.2 vs norm (Crimson)",
      a: "+36.4",
      da: "+13.6 vs norm (Empty Fire)",
      b: "+9.8",
      db: "Peeled / mirror-like fur",
      bodyFill: "#a82833",
      bodyStroke: "#5e1118",
      coatFill: "#f3e5dc",
      coatOpacity: "0.14",
      fissures: 1,
      scallops: 0,
      stasis: 0,
      bagang: { heat: 82, heatLbl: "Empty Heat (82%)", excess: 22, excessLbl: "Yin Deficient (22%)", interior: 94, intLbl: "Deep Interior (94%)", yang: 64, yangLbl: "Relative Yang (64%)" },
      formula: "<strong>知柏地黄丸 / 一贯煎</strong> (Zhi Bai Di Huang Wan) — Rehmannia, Anemarrhena, Phellodendron, Ophiopogon",
      cli: 'tcm -i crimson_fissured.jpg "Differentiate Yin-fire & check滋阴 formulas"'
    },
    {
      key: "violaceous_stasis",
      code: "PATTERN · QI STAGNATION & BLOOD STASIS",
      title: "气滞血瘀证 — Violaceous Tongue with Ecchymotic Macules (青紫瘀点舌)",
      desc: "Depressed red-yellow warmth with negative blue shift (b* = -4.2, L* = 46.9) and marginal petechial macules reflect microcirculatory hemorheological stasis, elevated fibrinogen viscosity, and deoxygenated venous pooling.",
      L: "46.9",
      dL: "-18.5 vs norm (Dusky)",
      a: "+19.5",
      da: "Cyanotic shift",
      b: "-4.2",
      db: "Bluish-purple stasis shift",
      bodyFill: "#8b566b",
      bodyStroke: "#4d2838",
      coatFill: "#e6dfe4",
      coatOpacity: "0.35",
      fissures: 0,
      scallops: 0,
      stasis: 1,
      bagang: { heat: 44, heatLbl: "Neutral-Cool (44%)", excess: 79, excessLbl: "Stasis Excess (79%)", interior: 92, intLbl: "Vessels/Luo (92%)", yang: 38, yangLbl: "Yin/Blood (38%)" },
      formula: "<strong>血府逐瘀汤</strong> (Xue Fu Zhu Yu Tang) — Persica, Carthamus, Angelica, Ligusticum, Salvia (check anticoagulants!)",
      cli: 'tcm -i stasis_tongue.jpg "Evaluate blood stasis & screen Warfarin safety"'
    }
  ];

  const HERB_CALLOUTS = [
    {
      badge: "LANDMARK 01 · MACROSCOPIC XYLEM ANATOMY",
      title: "菊花心 (Chrysanthemum-Heart Radial Striations)",
      desc: "Authentic Inner Mongolian Astragalus membranaceus var. mongholicus exhibits a bright pale-yellow wooden core with fine, radiating vascular rays and micro-fissures resembling an open chrysanthemum blossom — immediately distinguishing it from non-radiating woody substitutes."
    },
    {
      badge: "LANDMARK 02 · CAMBIUM & CORTEX HISTOLOGY",
      title: "金井玉栏 (Golden-Well Jade-Fence Cortex Ring)",
      desc: "A distinct brownish cambium ring separates the creamy yellowish-white fibrous phloem cortex ('Jade Fence') from the golden xylem center ('Golden Well'). Hedysarum polybotrys (红芪) instead shows a reddish-brown cork and compact darker wood."
    },
    {
      badge: "LANDMARK 03 · QUANTITATIVE PHYTOCHEMICAL ASSAY",
      title: "Astragaloside IV & Calycosin-7-O-β-D-Glucoside",
      desc: "ChP 2025 mandates Astragaloside IV ≥ 0.080% (HPLC-ELSD) and Calycosin glucoside ≥ 0.020%. TCM Studio links these saponin and isoflavonoid markers directly to AMPK, AKT1, NOS3, and Nrf2 signaling pathways."
    },
    {
      badge: "LANDMARK 04 · PAOZHI PROCESSING TRANSFORMATION",
      title: "生黄芪 (Raw) vs. 蜜炙黄芪 (Honey-Broiled)",
      desc: "Rawslices consolidate Defensive Qi (卫气), promote diuresis, and accelerate tissue granulation; honey-broiling (蜜炙) increases polysaccharide bioavailability and redirects therapeutic tropism toward tonifying Middle-Jiao Spleen-Lung Qi."
    }
  ];

  const PULSE_WAVEFORMS = {
    wiry: {
      bpmBadge: "76 BPM · h3/h1 = 0.78",
      code: "PULSE MORPHOLOGY · TAUT BOWSTRING HARMONIC",
      title: "弦脉 (Wiry / String-Taut Pulse) — 端直以长，如按琴弦",
      desc: "Elevated tidal wave amplitude (h3/h1 = 0.78) with broadened systolic plateau (w/t = 0.29) reflects heightened peripheral arterial smooth-muscle tone — classically correlated with Liver Qi constraint, Shaoyang pivot disharmony, or pain syndromes.",
      path: "M24,172 L52,172 L72,42 L94,62 L112,54 L132,124 L148,112 L188,172 L218,172 L238,42 L260,62 L278,54 L298,124 L314,112 L354,172 L384,172 L404,42 L426,62 L444,54 L464,124 L480,112 L496,158",
      hemo: "<code>h3/h1 = 0.78</code> (High Vascular Tension) &middot; <code>w/t = 0.29</code> &middot; <code>h4/h1 = 0.56</code>",
      acoustic: "Auscultation (闻诊): Frequent sighing (善太息), taut vocal resonance (角音偏亢) &rarr; high concordance with Liver Depression.",
      canon: "<em>Shanghan Lun</em> Clause 263 / 96: <strong>小柴胡汤</strong> (Shaoyang Wiry Pulse) or <strong>柴胡疏肝散</strong>."
    },
    slippery: {
      bpmBadge: "84 BPM · h5/h1 = 0.44",
      code: "PULSE MORPHOLOGY · FLUENT PEARL-ROLLING HARMONIC",
      title: "滑脉 (Slippery / Rolling Pulse) — 往来流利，如珠走盘",
      desc: "Steep systolic upstroke, low tidal shoulder, deep dicrotic notch (h4), and prominent dicrotic wave (h5/h1 = 0.44) reflect high stroke compliance and hyperdynamic flow — seen in phlegm-damp retention, food stagnation, damp-heat, or healthy pregnancy.",
      path: "M24,172 L48,172 L68,38 L88,136 L108,96 L152,172 L188,172 L208,38 L228,136 L248,96 L292,172 L328,172 L348,38 L368,136 L388,96 L432,172 L468,172 L488,48",
      hemo: "<code>h3/h1 = 0.34</code> (Low Resistance) &middot; <code>h5/h1 = 0.44</code> (Prominent Dicrotic) &middot; <code>84 BPM</code>",
      acoustic: "Auscultation (闻诊): Heavy turbid cough or throat sputum rattle (痰鸣音) &rarr; Phlegm-Heat / Phlegm-Damp.",
      canon: "<em>Jin Gui Yao Lue</em> &amp; <em>Mai Jing</em>: <strong>二陈汤 / 温胆汤</strong> (Phlegm-Fluid Disharmony)."
    },
    choppy: {
      bpmBadge: "68 BPM · Jagged Systolic Rise",
      code: "PULSE MORPHOLOGY · ROUGH BAMBOO-SCRAPING HARMONIC",
      title: "涩脉 (Choppy / Hesitant Pulse) — 细而迟短，往来艰涩",
      desc: "Slurred, notched ascending limb with blunted peak amplitude and irregular micro-oscillations indicates elevated blood viscosity, microcirculatory stasis, or severe depletion of Yin-Blood and Essence (精血亏虚 / 气滞血瘀).",
      path: "M24,172 L58,172 L70,128 L79,134 L92,86 L104,94 L116,78 L142,138 L184,172 L226,172 L238,126 L247,133 L260,84 L272,92 L284,76 L310,138 L352,172 L394,172 L406,128 L415,134 L428,86 L440,94 L452,78 L486,154",
      hemo: "<code>Upstroke t1 = 0.19s</code> (Delayed) &middot; <code>Amplitude = Low-Mod</code> &middot; High Hemorheological Viscosity",
      acoustic: "Auscultation (闻诊): Low, hesitant speech or nocturnal sighing with fixed chest/hypochondriac pain.",
      canon: "<em>Yi Lin Gai Cuo</em>: <strong>桃红四物汤 / 血府逐瘀汤</strong> (Stasis) or <strong>归脾汤</strong> (Blood Deficiency)."
    },
    thready: {
      bpmBadge: "102 BPM · Narrow Thread",
      code: "PULSE MORPHOLOGY · LOW-AMPLITUDE TACHYCARDIC",
      title: "细数脉 (Thready & Rapid Pulse) — 脉细如线，一息六至",
      desc: "Shortened cardiac cycle (102 BPM, >5 beats per breath) with narrow, low-volume percussion wave signifies Yin-Fluid depletion generating internal deficiency heat (阴虚内热).",
      path: "M24,172 L38,172 L52,102 L66,144 L78,132 L102,172 L120,172 L134,102 L148,144 L160,132 L184,172 L202,172 L216,102 L230,144 L242,132 L266,172 L284,172 L298,102 L312,144 L324,132 L348,172 L366,172 L380,102 L394,144 L406,132 L430,172 L448,172 L462,102 L476,144 L492,166",
      hemo: "<code>Rate = 102 BPM</code> &middot; <code>Pulse Pressure = Narrow</code> &middot; Sympathetic predominance",
      acoustic: "Auscultation (闻诊): Dry short non-productive cough, hoarse afternoon voice (金破不鸣), malar flush.",
      canon: "<em>Wen Bing Tiao Bian</em>: <strong>六味地黄丸 / 天王补心丹 / 百合固金汤</strong>."
    },
    deep: {
      bpmBadge: "52 BPM · Bradycardic Deep",
      code: "PULSE MORPHOLOGY · SUBMERGED YANG-DEFICIENT HARMONIC",
      title: "沉迟脉 (Deep & Slow Pulse) — 重按始得，一息三至",
      desc: "Prolonged diastolic baseline (52 BPM, <4 beats per breath) sensed only under firm radial compression near the radius bone reflects Interior Cold and Heart-Kidney Yang insufficiency (里寒 / 脾肾阳虚).",
      path: "M24,172 L86,172 L114,114 L138,136 L158,150 L238,172 L312,172 L340,114 L364,136 L384,150 L464,172 L496,172",
      hemo: "<code>Rate = 52 BPM</code> &middot; <code>Optimal Sensor Pressure &gt; 160 gf</code> &middot; Low Cardiac Output",
      acoustic: "Auscultation (闻诊): Faint low-volume voice (语声低微), chill intolerance, clear copious urination.",
      canon: "<em>Shanghan Lun</em> Shaoyin Chapter Clause 281 / 323: <strong>四逆汤 / 真武汤</strong> (Pre-decoct 附子!)."
    }
  };

  /* ------------------------------------------------------------------------
     4. Formula & Safety Mini-Bench Dataset
     ------------------------------------------------------------------------ */
  const MINIBENCH_FORMULAS = {
    sijunzi: {
      source: "Tai Ping Hui Min He Ji Ju Fang (1107 CE)",
      title: "四君子汤 (Si Jun Zi Tang)",
      action: "益气健脾 · Tonify Qi",
      pathway: "KEGG: PI3K-Akt / AMPK / Gut Barrier",
      cliHint: '$ tcm "Network pharmacology of 四君子汤"',
      herbs: [
        { role: "君 Sovereign", cls: "role-jun", name: "人参", latin: "Panax ginseng", dose: "9 g", prop: "Sweet, Warm · SP, LU, HT" },
        { role: "臣 Minister", cls: "role-chen", name: "白术", latin: "Atractylodes macrocephala", dose: "9 g", prop: "Bitter-Sweet, Warm · SP, ST" },
        { role: "佐 Assistant", cls: "role-zuo", name: "茯苓", latin: "Poria cocos", dose: "9 g", prop: "Sweet-Bland, Neutral · HT, SP, KI" },
        { role: "使 Courier", cls: "role-shi", name: "炙甘草", latin: "Glycyrrhiza uralensis", dose: "6 g", prop: "Sweet, Warm · All 12 Meridians" }
      ],
      targets: [
        ["Ginsenoside Rg1", "AKT1"],
        ["Atractylenolide III", "AMPK"],
        ["Pachymic Acid", "TNF"],
        ["Licochalcone A", "IL6"],
        ["Ginsenoside Rb1", "PPARG"]
      ],
      danger: false,
      safetyHead: "✓ SAFETY GATE PASSED · ZERO 十八反 / 十九畏 VIOLATIONS",
      safetyBody:
        "All 4 herbs satisfy Chinese Pharmacopoeia 2025 adult dosage bounds. Clinical note: Prolonged high-dose 炙甘草 (>15g/day) warrants serum K+ and BP monitoring due to 11β-HSD2 inhibition."
    },
    buzhong: {
      source: "Pi Wei Lun · Li Dongyuan (1249 CE)",
      title: "补中益气汤 (Bu Zhong Yi Qi Tang)",
      action: "补中益气，升阳举陷",
      pathway: "KEGG: AMPK / HIF-1 / T-Cell Receptor",
      cliHint: '$ tcm "Build network pharmacology for 补中益气汤"',
      herbs: [
        { role: "君 Sovereign", cls: "role-jun", name: "蜜炙黄芪", latin: "Astragalus membranaceus", dose: "18 g", prop: "Sweet, Slightly Warm · SP, LU" },
        { role: "臣 Minister", cls: "role-chen", name: "党参 / 白术", latin: "Codonopsis / Atractylodes", dose: "9 g + 9 g", prop: "Sweet, Warm · SP, ST" },
        { role: "佐 Assistant", cls: "role-zuo", name: "当归 / 陈皮", latin: "Angelica sinensis / Citrus", dose: "6 g + 6 g", prop: "Nourish Blood & Regulate Qi" },
        { role: "使 Courier", cls: "role-shi", name: "升麻 / 柴胡 / 炙甘草", latin: "Cimicifuga / Bupleurum", dose: "6 g + 6 g + 6 g", prop: "Upbear Clear Yang" }
      ],
      targets: [
        ["Astragaloside IV", "AMPK"],
        ["Calycosin", "NOS3"],
        ["Ferulic Acid", "VEGFA"],
        ["Saikosaponin D", "STAT3"],
        ["Hesperidin", "TNF"],
        ["Glycyrrhizin", "IL6"]
      ],
      danger: false,
      safetyHead: "✓ SAFETY GATE PASSED · HARMONIOUS UPBEARING ARCHITECTURE",
      safetyBody:
        "Zero 十八反/十九畏 conflicts. Caution in Yin-deficiency with ascendant Liver Yang or uncontrolled Stage-2 hypertension due to Qi-raising acrid herbs (升麻, 柴胡)."
    },
    xiaochaihu: {
      source: "Shanghan Lun · Zhang Zhongjing (~205 CE)",
      title: "小柴胡汤 (Xiao Chai Hu Tang)",
      action: "和解少阳 · Harmonize Shaoyang",
      pathway: "KEGG: Toll-like Receptor / NF-κB /JAK-STAT",
      cliHint: '$ tcm "Analyze 小柴胡汤 Shanghan Lun posology & targets"',
      herbs: [
        { role: "君 Sovereign", cls: "role-jun", name: "柴胡", latin: "Bupleurum chinense", dose: "12 g", prop: "Bitter-Acrid, Cool · LR, GB" },
        { role: "臣 Minister", cls: "role-chen", name: "黄芩", latin: "Scutellaria baicalensis", dose: "9 g", prop: "Bitter, Cold · GB, LU, LI" },
        { role: "佐 Assistant", cls: "role-zuo", name: "法半夏 / 人参 / 生姜", latin: "Pinellia / Ginseng / Zingiber", dose: "9 g + 6 g + 9 g", prop: "Harmonize Stomach & Boost Qi" },
        { role: "使 Courier", cls: "role-shi", name: "大枣 / 炙甘草", latin: "Ziziphus jujuba / Glycyrrhiza", dose: "4 pcs + 6 g", prop: "Harmonize Middle Jiao" }
      ],
      targets: [
        ["Saikosaponin A", "NFKB1"],
        ["Baicalin", "TNF"],
        ["Wogonin", "IL6"],
        ["Beta-Sitosterol", "CASP3"],
        ["Ginsenoside Rg1", "AKT1"],
        ["6-Gingerol", "PTGS2"]
      ],
      danger: false,
      safetyHead: "✓ SAFETY GATE PASSED · PINELIA PROPERLY PROCESSED WITH GINGER",
      safetyBody:
        "法半夏 (processed Pinellia) + 生姜 (fresh ginger) exemplifies classical mutual detoxification (相畏/相杀). Contraindicated if co-administered with 乌头/附子 (Aconite). Monitor hepatic transaminases in Interferon co-therapy."
    },
    huanglian: {
      source: "Wai Tai Mi Yao · Wang Tao (752 CE)",
      title: "黄连解毒汤 (Huang Lian Jie Du Tang)",
      action: "泻火解毒 · Drain Fire & Resolve Toxin",
      pathway: "KEGG: TNF / IL-17 / NLRP3 Inflammasome / AMPK",
      cliHint: '$ tcm "Evaluate 黄连解毒汤 anti-inflammatory hub targets"',
      herbs: [
        { role: "君 Sovereign", cls: "role-jun", name: "黄连", latin: "Coptis chinensis", dose: "9 g", prop: "Bitter, Cold · HT, ST, LR" },
        { role: "臣 Minister", cls: "role-chen", name: "黄芩", latin: "Scutellaria baicalensis", dose: "6 g", prop: "Bitter, Cold · LU, GB, LI" },
        { role: "佐 Assistant", cls: "role-zuo", name: "黄柏", latin: "Phellodendron chinense", dose: "6 g", prop: "Bitter, Cold · KI, BL" },
        { role: "使 Courier", cls: "role-shi", name: "栀子", latin: "Gardenia jasminoides", dose: "9 g", prop: "Bitter, Cold · Triple Energizer" }
      ],
      targets: [
        ["Berberine", "AMPK"],
        ["Berberine", "LDLR"],
        ["Baicalein", "PTGS2"],
        ["Palmatine", "TNF"],
        ["Geniposide", "IL1B"],
        ["Coptisine", "NLRP3"]
      ],
      danger: false,
      safetyHead: "✓ COMPATIBLE · BITTER-COLD DURATION GUARDRAIL ACTIVE",
      safetyBody:
        "Bitter-cold quartet strongly clears Triple-Jiao fire; avoid prolonged administration in Spleen-Stomach deficiency-cold. Berberine inhibits CYP2D6 & CYP3A4 — check Cyclosporine/Metformin plasma levels."
    },
    xuefu: {
      source: "Yi Lin Gai Cuo · Wang Qingren (1830 CE)",
      title: "血府逐瘀汤 (Xue Fu Zhu Yu Tang)",
      action: "活血化瘀，行气止痛",
      pathway: "KEGG: VEGF / Fluid Shear Stress / Platelet Activation",
      cliHint: '$ tcm "Xue Fu Zhu Yu Tang pregnancy & anticoagulant check"',
      herbs: [
        { role: "君 Sovereign", cls: "role-jun", name: "桃仁 / 红花", latin: "Prunus persica / Carthamus", dose: "12 g + 9 g", prop: "Break Blood Stasis · HT, LR" },
        { role: "臣 Minister", cls: "role-chen", name: "当归 / 川芎 / 赤芍", latin: "Angelica / Chuanxiong / Paeonia", dose: "9 g + 5 g + 6 g", prop: "Quicken Blood & Dispel Stasis" },
        { role: "佐 Assistant", cls: "role-zuo", name: "生地黄 / 枳壳 / 柴胡", latin: "Rehmannia / Aurantium / Bupleurum", dose: "9 g + 6 g + 3 g", prop: "Nourish Yin & Move Chest Qi" },
        { role: "使 Courier", cls: "role-shi", name: "怀牛膝 / 桔梗 / 甘草", latin: "Achyranthes / Platycodon", dose: "9 g + 5 g + 6 g", prop: "Guide Blood Downward & Open Chest" }
      ],
      targets: [
        ["Hydroxysafflor Yellow A", "VEGFA"],
        ["Amygdalin", "NOS3"],
        ["Ligustrazine", "PTGS2"],
        ["Paeoniflorin", "TNF"],
        ["Ferulic Acid", "SERPINE1"]
      ],
      danger: false,
      safetyHead: "✓ COMPATIBLE · STRICT PREGNANCY CONTRAINDICATION FLAGGED",
      safetyBody:
        "Zero herb-herb incompatibility, but STRICTLY CONTRAINDICATED IN PREGNANCY (桃仁, 红花, 怀牛膝, 川芎). Requires INR check if combined with antiplatelets or anticoagulants."
    },
    shibafan: {
      source: "SAFETY CHALLENGE · Eighteen Incompatibilities (本草经集注 · 十八反)",
      title: "人参 + 藜芦 (Panax ginseng + Veratrum nigrum)",
      action: "CONTRAINDICATED · 十八反",
      pathway: "TOXICOLOGY: Voltage-Gated Na+ Channel Hyper-Activation",
      cliHint: '$ tcm "Check safety of 人参 and 藜芦"',
      herbs: [
        { role: "补气 Herb A", cls: "role-jun", name: "人参", latin: "Panax ginseng", dose: "9 g", prop: "Sweet, Slightly Warm · HT, LU, SP" },
        { role: "催吐涌痰 Herb B", cls: "role-hazard", name: "藜芦", latin: "Veratrum nigrum", dose: "0.6 g", prop: "Acrid-Bitter, Cold · TOXIC (有毒)" }
      ],
      targets: [
        ["Veratridine", "SCN5A (Cardiac Na+ Channel)"],
        ["Jervine", "SMO"],
        ["Ginsenoside Rg1", "CYP3A4 Modulation"]
      ],
      danger: true,
      safetyHead: "✕ BLOCKED · EIGHTEEN INCOMPATIBILITIES VIOLATION (诸参辛芍叛藜芦)",
      safetyBody:
        "CRITICAL CONTRAINDICATION: ChP 2025 forbids combining Veratrum nigrum (藜芦) with Panax ginseng, Codonopsis, Salvia, Scrophularia, Sophora, Asarum, or Paeonia. Co-decoction increases steroidal alkaloid extraction and triggers severe bradycardia, hypotension, and neurocardiotoxicity."
    },
    warfarin: {
      source: "SAFETY CHALLENGE · Herb–Drug Pharmacokinetic & Pharmacodynamic Gate",
      title: "丹参 + Warfarin (Salvia miltiorrhiza + Warfarin)",
      action: "MAJOR INTERACTION · CYP2C9 + INR",
      pathway: "PK/PD: CYP2C9 / VKORC1 / Platelet P2Y12 & Thrombin",
      cliHint: '$ tcm "Check interaction between 丹参 and Warfarin"',
      herbs: [
        { role: "活血 Herb", cls: "role-hazard", name: "丹参", latin: "Salvia miltiorrhiza", dose: "15 g", prop: "Bitter, Slightly Cold · HT, PC, LR" },
        { role: "Rx Anticoagulant", cls: "role-hazard", name: "Warfarin Sodium", latin: "Vitamin K Epoxide Reductase Inhibitor", dose: "5 mg PO", prop: "Narrow Therapeutic Index (INR 2.0–3.0)" }
      ],
      targets: [
        ["Tanshinone IIA", "CYP2C9 Inhibition"],
        ["Cryptotanshinone", "CYP1A2 / CYP3A4"],
        ["Salvianolic Acid B", "F2 (Thrombin) / Platelet"],
        ["S-Warfarin", "VKORC1"]
      ],
      danger: true,
      safetyHead: "✕ HIGH ALERT · MAJOR BLEEDING & SUPRATHERAPEUTIC INR RISK",
      safetyBody:
        "Salvia tanshinones competitively inhibit CYP2C9/CYP1A2 clearance of S-warfarin and displace plasma protein binding while Salvianolic acid B inhibits platelet aggregation — documented clinical cases of INR > 5.0 and hemorrhage. Avoid co-administration or mandate serial INR monitoring."
    }
  };

  /* ------------------------------------------------------------------------
     5. Verified November 2026 SOTA Foundation Model Ecosystem (36 Models)
     ------------------------------------------------------------------------ */
  const SOTA_MODELS = [
    // Anthropic
    { provider: "Anthropic", name: "Claude Fable 5.2", id: "claude-fable-5-2", ctx: "1M", mods: ["vision", "pdf", "thinking"], cats: ["vision", "1m", "thinking"], desc: "Frontier scholarly synthesis, full-book Bencao PDF philology & deep causal reasoning." },
    { provider: "Anthropic", name: "Claude Opus 5.5", id: "claude-opus-5-5", ctx: "1M", mods: ["vision", "pdf", "thinking"], cats: ["vision", "1m", "thinking"], desc: "Gold-standard clinical safety verification, tongue vision & complex multi-tool planning." },
    { provider: "Anthropic", name: "Claude Sonnet 5.5", id: "claude-sonnet-5-5", ctx: "1M", mods: ["vision", "pdf", "thinking"], cats: ["vision", "1m", "thinking"], desc: "Balanced low-latency multimodal workhorse for daily TCM Studio interactive sessions." },
    { provider: "Anthropic", name: "Claude Haiku 5.5", id: "claude-haiku-5-5", ctx: "1M", mods: ["vision", "pdf"], cats: ["vision", "1m"], desc: "Sub-second herb monograph triage, ChP dosage checks & high-volume extraction." },

    // OpenAI
    { provider: "OpenAI", name: "GPT-6 Astra", id: "gpt-6-astra", ctx: "1.05M", mods: ["vision", "audio", "thinking"], cats: ["vision", "audio", "1m", "thinking"], desc: "Flagship omni-modal reasoning across visual inspection, vocal auscultation & pharmacology." },
    { provider: "OpenAI", name: "GPT-6.1 Sol", id: "gpt-6.1-sol", ctx: "1.05M", mods: ["vision", "audio", "thinking"], cats: ["vision", "audio", "1m", "thinking"], desc: "High-speed multimodal streaming for interactive Four-Examinations clinical interviews." },
    { provider: "OpenAI", name: "GPT-6.1 Terra", id: "gpt-6.1-terra", ctx: "1.05M", mods: ["vision", "pdf", "thinking"], cats: ["vision", "1m", "thinking"], desc: "High-precision fine-grained visual diagnostics for lingual coating & herb slice histology." },
    { provider: "OpenAI", name: "GPT-Rosalind Research", id: "gpt-rosalind-research", ctx: "1M", mods: ["vision", "thinking"], cats: ["vision", "1m", "thinking"], desc: "Life-sciences specialist optimized for SMILES, ChEMBL docking, UniProt & KEGG graphs." },
    { provider: "OpenAI", name: "GPT-5.4", id: "gpt-5.4", ctx: "400K", mods: ["vision", "audio"], cats: ["vision", "audio"], desc: "Reliable production general-purpose agent routing & structured JSON tool calling." },
    { provider: "OpenAI", name: "o4-mini", id: "o4-mini", ctx: "200K", mods: ["vision", "thinking"], cats: ["vision", "thinking"], desc: "Fast quantitative reasoning for RDKit Python scripts & statistical meta-analysis." },

    // Google DeepMind
    { provider: "Google DeepMind", name: "Gemini 3.6 Flash", id: "gemini-3.6-flash", ctx: "1M", mods: ["vision", "audio", "video", "pdf", "thinking"], cats: ["vision", "audio", "1m", "thinking"], desc: "Native video/audio/PDF/image engine for dynamic tongue & gait inspection + rapid tool calls." },
    { provider: "Google DeepMind", name: "Gemini 3.1 Pro", id: "gemini-3.1-pro-preview", ctx: "1M", mods: ["vision", "audio", "video", "pdf", "thinking"], cats: ["vision", "audio", "1m", "thinking"], desc: "Long-horizon corpus synthesis across entire Shanghan, Jin Gui & PubMed trial collections." },
    { provider: "Google DeepMind", name: "Gemini 2.5 Pro", id: "gemini-2.5-pro", ctx: "1M", mods: ["vision", "audio", "video", "pdf", "thinking"], cats: ["vision", "audio", "1m", "thinking"], desc: "Proven 1M-token scientific reasoning and cross-lingual biomedical literature review." },
    { provider: "Google DeepMind", name: "Gemini 2.5 Flash", id: "gemini-2.5-flash", ctx: "1M", mods: ["vision", "audio", "pdf"], cats: ["vision", "audio", "1m"], desc: "Cost-efficient multimodal batch processing for pharmacognosy datasets." },

    // Chinese Frontier (Classical TCM Powerhouses)
    { provider: "DeepSeek", name: "DeepSeek V4 Pro", id: "deepseek-v4-pro", ctx: "1M", mods: ["vision", "thinking"], cats: ["vision", "1m", "thinking", "chinese"], desc: "Deep classical Chinese medical reasoning (伤寒/温病/本草) + MoE systems pharmacology." },
    { provider: "DeepSeek", name: "DeepSeek V4.1 Flash", id: "deepseek-v4.1-flash", ctx: "1M", mods: ["vision", "thinking"], cats: ["vision", "1m", "thinking", "chinese"], desc: "Ultra-fast bilingual syndrome differentiation & Jun-Chen-Zuo-Shi formula optimization." },
    { provider: "DeepSeek", name: "DeepSeek R2", id: "deepseek-r2", ctx: "256K", mods: ["thinking"], cats: ["thinking", "chinese"], desc: "Reinforcement-verified multi-hop chain-of-thought for complex differential diagnosis." },
    { provider: "Alibaba Qwen", name: "Qwen 3.8 Max", id: "qwen3.8-max", ctx: "1M", mods: ["vision", "thinking"], cats: ["vision", "1m", "thinking", "chinese"], desc: "Top-tier classical Chinese philology, variant character normalization & ChP standards." },
    { provider: "Alibaba Qwen", name: "Qwen-VL Max", id: "qwen-vl-max", ctx: "1M", mods: ["vision", "video", "pdf"], cats: ["vision", "1m", "chinese"], desc: "State-of-the-art vertical woodblock OCR, handwritten Rx transcription & tongue segmentation." },
    { provider: "Alibaba Qwen", name: "Qwen3-235B-A22B", id: "qwen3-235b-a22b", ctx: "256K", mods: ["thinking"], cats: ["thinking", "chinese", "local"], desc: "Open-weight flagship hybrid-thinking MoE deployable on institutional GPU clusters." },
    { provider: "Zhipu AI", name: "GLM-5.3", id: "glm-5.3", ctx: "512K", mods: ["vision", "thinking"], cats: ["vision", "thinking", "chinese"], desc: "Strong agentic tool orchestration and structured Chinese Hospital EHR integration." },
    { provider: "Zhipu AI", name: "GLM-4V Plus", id: "glm-4v-plus", ctx: "128K", mods: ["vision", "video"], cats: ["vision", "chinese"], desc: "High-resolution decoction-piece surface texture & microscopic tissue authentication." },
    { provider: "Moonshot AI", name: "Kimi K3.1 Pro", id: "kimi-k3.1-pro", ctx: "1M", mods: ["vision", "pdf", "thinking"], cats: ["vision", "1m", "thinking", "chinese"], desc: "Lossless long-context cross-referencing across dozens of classical medical treatises." },
    { provider: "Moonshot AI", name: "Kimi-VL-A3B", id: "kimi-vl-a3b", ctx: "256K", mods: ["vision", "thinking"], cats: ["vision", "thinking", "chinese", "local"], desc: "Lightweight MoE vision-reasoning model for document & specimen scanning." },
    { provider: "MiniMax", name: "MiniMax M3", id: "minimax-m3", ctx: "1M", mods: ["vision", "audio", "thinking"], cats: ["vision", "audio", "1m", "thinking", "chinese"], desc: "1M linear-attention multimodal model with expressive vocal auscultation & audio synthesis." },
    { provider: "ByteDance", name: "Doubao 2.0 Pro", id: "doubao-2.0-pro", ctx: "256K", mods: ["vision", "thinking"], cats: ["vision", "thinking", "chinese"], desc: "Fast bilingual clinical consultation and patient-facing health education synthesis." },
    { provider: "Baichuan", name: "Baichuan-M2 Med", id: "baichuan-m2-med", ctx: "192K", mods: ["vision", "thinking"], cats: ["vision", "thinking", "chinese"], desc: "Domain-tuned integrative Chinese-Western clinical guidelines & lab interpretation." },

    // Global & Private Local
    { provider: "xAI", name: "Grok 4.8", id: "grok-4.8", ctx: "1M", mods: ["vision", "thinking"], cats: ["vision", "1m", "thinking"], desc: "Deep scientific literature synthesis, statistical critique & mechanism hypothesis testing." },
    { provider: "xAI", name: "Grok 4.8 Mini", id: "grok-4.8-mini", ctx: "256K", mods: ["vision", "thinking"], cats: ["vision", "thinking"], desc: "Low-latency analytical reasoning for rapid compound-target screening." },
    { provider: "Mistral AI", name: "Pixtral Large", id: "pixtral-large", ctx: "128K", mods: ["vision", "pdf"], cats: ["vision", "local"], desc: "124B multimodal visual parser for chemical structure diagrams & clinical charts." },
    { provider: "Mistral AI", name: "Mistral Large 3", id: "mistral-large-3", ctx: "256K", mods: ["thinking"], cats: ["thinking"], desc: "Multilingual European/Asian regulatory pharmacopoeia & EMA herbal monograph analysis." },
    { provider: "Meta", name: "Llama 4 Maverick", id: "llama-4-maverick", ctx: "1M", mods: ["vision"], cats: ["vision", "1m", "local"], desc: "Open-weight 1M multimodal MoE for customizable academic pharmacology pipelines." },
    { provider: "Ollama (Local)", name: "MedGemma 27B", id: "ollama/medgemma:27b", ctx: "128K", mods: ["vision"], cats: ["vision", "local"], desc: "Air-gapped hospital biomedical vision & clinical reasoning on a single workstation." },
    { provider: "Ollama (Local)", name: "HuatuoGPT-Vision 7B", id: "ollama/huatuogpt-vision:7b", ctx: "32K", mods: ["vision"], cats: ["vision", "chinese", "local"], desc: "Specialized local TCM tongue/herb medical vision model with zero external data egress." },
    { provider: "Ollama (Local)", name: "Qwen3 32B Local", id: "ollama/qwen3:32b", ctx: "128K", mods: ["thinking"], cats: ["thinking", "chinese", "local"], desc: "Private on-premise classical TCM & tool-calling model for clinics and labs." },
    { provider: "Ollama (Local)", name: "DeepSeek-R1 Distill 32B", id: "ollama/deepseek-r1:32b", ctx: "128K", mods: ["thinking"], cats: ["thinking", "chinese", "local"], desc: "Offline chain-of-thought syndrome & safety verification engine." }
  ];

  const TASK_RECOMMENDATIONS = {
    vision:
      'Recommended primary: <code>claude-opus-5-5</code> &middot; Visual histology specialist: <code>gpt-6.1-terra</code> &middot; TCM Bilingual Vision: <code>qwen-vl-max</code>',
    ocr:
      'Recommended primary: <code>qwen-vl-max</code> &amp; <code>qwen3.8-max</code> &middot; Full-treatise context: <code>claude-fable-5-2</code> &middot; Classical philology: <code>deepseek-v4-pro</code>',
    pharma:
      'Recommended primary: <code>gpt-rosalind-research</code> &middot; Multi-tool synthesis: <code>claude-opus-5-5</code> &middot; 1M corpus graph: <code>gemini-3.1-pro-preview</code>',
    safety:
      'Recommended primary: <code>claude-opus-5-5</code> &middot; Omni-clinical verification: <code>gpt-6-astra</code> &middot; ChP bilingual rules: <code>deepseek-v4-pro</code>',
    audio:
      'Recommended primary: <code>gemini-3.6-flash</code> (Native Audio/Video) &middot; Real-time clinical stream: <code>gpt-6.1-sol</code> &middot; Chinese acoustic: <code>minimax-m3</code>',
    local:
      'Recommended air-gapped stack: <code>ollama/medgemma:27b</code> (Biomedical Vision) + <code>ollama/huatuogpt-vision:7b</code> (TCM Vision) + <code>ollama/qwen3:32b</code>'
  };

  /* ------------------------------------------------------------------------
     6. State & Initialization
     ------------------------------------------------------------------------ */
  let currentLang = localStorage.getItem("tcm-studio-lang") === "zh" ? "zh" : "en";
  let currentTheme = localStorage.getItem("tcm-studio-theme") === "dark" ? "dark" : "light";
  let currentHeroCmd = "studio";
  let currentModelFilter = "all";

  function applyTheme(theme) {
    currentTheme = theme === "dark" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", currentTheme);
    localStorage.setItem("tcm-studio-theme", currentTheme);
    updateThemeButtonLabel();
  }

  function updateThemeButtonLabel() {
    const labelEl = document.getElementById("theme-toggle-label");
    if (!labelEl) return;
    const dict = I18N[currentLang];
    labelEl.textContent = currentTheme === "dark" ? dict.themeToggleDay : dict.themeToggleNight;
  }

  function applyLanguage(lang) {
    currentLang = lang === "zh" ? "zh" : "en";
    document.documentElement.setAttribute("lang", currentLang === "zh" ? "zh-CN" : "en");
    localStorage.setItem("tcm-studio-lang", currentLang);

    const dict = I18N[currentLang];
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (!dict[key]) return;
      if (key === "heroLead") {
        el.innerHTML = dict[key];
      } else {
        el.textContent = dict[key];
      }
    });

    const langLabel = document.getElementById("lang-toggle-label");
    if (langLabel) {
      langLabel.textContent = currentLang === "en" ? "中文" : "EN";
    }

    updateThemeButtonLabel();
    updateHeroCommand(currentHeroCmd);
  }

  /* ------------------------------------------------------------------------
     7. Hero Command Switcher & Universal Copy Handler
     ------------------------------------------------------------------------ */
  function updateHeroCommand(key) {
    if (!HERO_COMMANDS[key]) return;
    currentHeroCmd = key;

    document.querySelectorAll(".cmd-tab").forEach((btn) => {
      const active = btn.getAttribute("data-cmd-key") === key;
      btn.classList.toggle("is-active", active);
      btn.setAttribute("aria-selected", active ? "true" : "false");
    });

    const codeEl = document.getElementById("hero-cmd-code");
    const noteEl = document.getElementById("hero-cmd-footnote");
    if (codeEl) codeEl.textContent = HERO_COMMANDS[key].cmd;
    if (noteEl) {
      noteEl.textContent = currentLang === "zh" ? HERO_COMMANDS[key].noteZh : HERO_COMMANDS[key].noteEn;
    }
  }

  async function copyTextWithFeedback(text, btn) {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    }
    if (!btn) return;
    const orig = btn.textContent;
    btn.classList.add("is-copied");
    btn.textContent = currentLang === "zh" ? "已复制 ✓" : "Copied ✓";
    setTimeout(() => {
      btn.classList.remove("is-copied");
      btn.textContent = orig;
    }, 1500);
  }

  /* ------------------------------------------------------------------------
     8. Multimodal Section Controllers
     ------------------------------------------------------------------------ */
  function selectSpecimenTab(tabKey) {
    document.querySelectorAll(".specimen-tab-btn").forEach((btn) => {
      const active = btn.getAttribute("data-specimen-tab") === tabKey;
      btn.classList.toggle("is-active", active);
      btn.setAttribute("aria-selected", active ? "true" : "false");
    });
    document.querySelectorAll(".specimen-panel").forEach((panel) => {
      panel.classList.toggle("is-active", panel.id === "panel-" + tabKey);
    });
  }

  function selectTongueArchetype(index) {
    const item = TONGUE_ARCHETYPES[index];
    if (!item) return;

    document.querySelectorAll("[data-tongue-idx]").forEach((btn) => {
      btn.classList.toggle("is-active", Number(btn.getAttribute("data-tongue-idx")) === index);
    });

    const bodyPath = document.getElementById("svg-tongue-body");
    const coatPath = document.getElementById("svg-tongue-coat");
    const fissures = document.getElementById("svg-tongue-fissures");
    const scallops = document.getElementById("svg-tongue-scallops");
    const stasis = document.getElementById("svg-tongue-stasis");

    if (bodyPath) {
      bodyPath.setAttribute("fill", item.bodyFill);
      bodyPath.setAttribute("stroke", item.bodyStroke);
    }
    if (coatPath) {
      coatPath.setAttribute("fill", item.coatFill);
      coatPath.setAttribute("fill-opacity", item.coatOpacity);
    }
    if (fissures) fissures.setAttribute("opacity", String(item.fissures));
    if (scallops) scallops.setAttribute("opacity", String(item.scallops));
    if (stasis) stasis.setAttribute("opacity", String(item.stasis));

    const setTxt = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val;
    };
    const setHtml = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.innerHTML = val;
    };

    setTxt("tongue-syndrome-code", item.code);
    setTxt("tongue-syndrome-title", item.title);
    setTxt("tongue-syndrome-desc", item.desc);
    setTxt("tongue-val-l", item.L);
    setTxt("tongue-delta-l", item.dL);
    setTxt("tongue-val-a", item.a);
    setTxt("tongue-delta-a", item.da);
    setTxt("tongue-val-b", item.b);
    setTxt("tongue-delta-b", item.db);

    setTxt("bg-lbl-heat", item.bagang.heatLbl);
    setTxt("bg-lbl-excess", item.bagang.excessLbl);
    setTxt("bg-lbl-int", item.bagang.intLbl);
    setTxt("bg-lbl-yang", item.bagang.yangLbl);

    const setBar = (id, pct) => {
      const el = document.getElementById(id);
      if (el) el.style.width = pct + "%";
    };
    setBar("bg-bar-heat", item.bagang.heat);
    setBar("bg-bar-excess", item.bagang.excess);
    setBar("bg-bar-int", item.bagang.interior);
    setBar("bg-bar-yang", item.bagang.yang);

    setHtml("tongue-formula-rec", item.formula);
    setTxt("tongue-cli-cmd", item.cli);

    const studioBtn = document.getElementById("tongue-open-studio-btn");
    if (studioBtn) {
      studioBtn.setAttribute("href", "./studio.html?workspace=lab&preset=" + encodeURIComponent(item.key));
    }
  }

  function selectHerbCallout(idx) {
    const item = HERB_CALLOUTS[idx];
    if (!item) return;

    document.querySelectorAll("[data-herb-pin]").forEach((el) => {
      el.classList.toggle("is-active", Number(el.getAttribute("data-herb-pin")) === idx);
    });

    const b = document.getElementById("herb-callout-badge");
    const t = document.getElementById("herb-callout-title");
    const d = document.getElementById("herb-callout-desc");
    if (b) b.textContent = item.badge;
    if (t) t.textContent = item.title;
    if (d) d.textContent = item.desc;
  }

  function updateHanPosology() {
    const liangInput = document.getElementById("han-liang-input");
    const regimeSelect = document.getElementById("han-regime-select");
    const out = document.getElementById("han-conversion-output");
    if (!liangInput || !regimeSelect || !out) return;

    const liang = Math.max(0.1, parseFloat(liangInput.value) || 3);
    const factor = parseFloat(regimeSelect.value) || 13.8;
    const totalGrams = (liang * factor).toFixed(1);
    const draughtGrams = ((liang * factor) / 3).toFixed(1);

    out.innerHTML =
      "<strong>" +
      liang.toFixed(1) +
      " 兩</strong> in <em>Shanghan Lun</em> = <code>" +
      totalGrams +
      " g</code> total decoction yield (<code>" +
      draughtGrams +
      " g</code> per single draught across 三服 three divided doses).";
  }

  function selectPulseWaveform(key) {
    const item = PULSE_WAVEFORMS[key];
    if (!item) return;

    document.querySelectorAll("[data-pulse-key]").forEach((btn) => {
      btn.classList.toggle("is-active", btn.getAttribute("data-pulse-key") === key);
    });

    const pathEl = document.getElementById("pulse-wave-path");
    if (pathEl) pathEl.setAttribute("d", item.path);

    const setHtml = (id, html) => {
      const el = document.getElementById(id);
      if (el) el.innerHTML = html;
    };
    const setTxt = (id, txt) => {
      const el = document.getElementById(id);
      if (el) el.textContent = txt;
    };

    setTxt("pulse-bpm-badge", item.bpmBadge);
    setTxt("pulse-tag-code", item.code);
    setTxt("pulse-readout-title", item.title);
    setTxt("pulse-readout-desc", item.desc);
    setHtml("pulse-hemo-val", item.hemo);
    setHtml("pulse-acoustic-val", item.acoustic);
    setHtml("pulse-canon-val", item.canon);
  }

  /* ------------------------------------------------------------------------
     9. Formula & Safety Mini-Bench Controller
     ------------------------------------------------------------------------ */
  function selectMinibenchFormula(key) {
    const f = MINIBENCH_FORMULAS[key];
    if (!f) return;

    document.querySelectorAll("[data-formula-key]").forEach((btn) => {
      btn.classList.toggle("is-active", btn.getAttribute("data-formula-key") === key);
    });

    const setTxt = (id, txt) => {
      const el = document.getElementById(id);
      if (el) el.textContent = txt;
    };

    setTxt("bench-source-text", f.source);
    setTxt("bench-formula-title", f.title);
    setTxt("bench-action-tag", f.action);
    setTxt("bench-pathway-label", f.pathway);
    setTxt("bench-cli-hint", f.cliHint);

    const actionTag = document.getElementById("bench-action-tag");
    if (actionTag) {
      actionTag.className = f.danger ? "status-tag-cinnabar" : "status-tag-ochre";
    }

    const tbody = document.getElementById("bench-herbs-tbody");
    if (tbody) {
      tbody.innerHTML = f.herbs
        .map(
          (h) =>
            "<tr>" +
            '<td><span class="role-tag ' +
            h.cls +
            '">' +
            h.role +
            "</span></td>" +
            "<td><strong>" +
            h.name +
            "</strong> <em>" +
            h.latin +
            "</em></td>" +
            '<td class="mono">' +
            h.dose +
            "</td>" +
            "<td>" +
            h.prop +
            "</td>" +
            "</tr>"
        )
        .join("");
    }

    const cloud = document.getElementById("bench-targets-cloud");
    if (cloud) {
      cloud.innerHTML = f.targets
        .map((pair) => '<span class="bio-target-chip">' + pair[0] + " &rarr; <span>" + pair[1] + "</span></span>")
        .join("");
    }

    const banner = document.getElementById("bench-safety-banner");
    if (banner) {
      banner.classList.toggle("is-danger", Boolean(f.danger));
    }
    setTxt("bench-safety-head", f.safetyHead);
    setTxt("bench-safety-body", f.safetyBody);

    const openLink = document.getElementById("bench-open-studio-link");
    if (openLink) {
      openLink.setAttribute("href", "./studio.html?workspace=pharmacology&formula=" + encodeURIComponent(key));
    }
  }

  /* ------------------------------------------------------------------------
     10. SOTA Foundation Model Table & Recommender
     ------------------------------------------------------------------------ */
  function renderModelsTable() {
    const tbody = document.getElementById("models-ledger-tbody");
    const searchInput = document.getElementById("model-search-input");
    if (!tbody) return;

    const query = (searchInput ? searchInput.value : "").trim().toLowerCase();

    const filtered = SOTA_MODELS.filter((m) => {
      const catOk = currentModelFilter === "all" || m.cats.includes(currentModelFilter);
      if (!catOk) return false;
      if (!query) return true;
      const hay = [m.provider, m.name, m.id, m.ctx, m.mods.join(" "), m.desc].join(" ").toLowerCase();
      return hay.includes(query);
    });

    if (filtered.length === 0) {
      tbody.innerHTML =
        '<tr><td colspan="6" style="text-align:center;color:var(--ink-muted);padding:1.5rem;">No models match the current filter. Reset filters to inspect all 36 SOTA models.</td></tr>';
      return;
    }

    tbody.innerHTML = filtered
      .map((m) => {
        const badges = m.mods
          .map((mod) => {
            let cls = "mod-badge";
            if (mod === "vision" || mod === "video") cls += " vision";
            if (mod === "thinking") cls += " thinking";
            return '<span class="' + cls + '">' + mod.toUpperCase() + "</span>";
          })
          .join("");

        return (
          "<tr>" +
          '<td class="provider-label">' +
          m.provider +
          "</td>" +
          "<td><strong>" +
          m.name +
          "</strong></td>" +
          '<td><a class="model-cli-id" href="./studio.html?workspace=agent&model=' +
          encodeURIComponent(m.id) +
          '" data-model-id="' +
          m.id +
          '" title="Open in TCM Studio with ' +
          m.id +
          '">' +
          m.id +
          " &rarr;</a></td>" +
          '<td class="mono">' +
          m.ctx +
          "</td>" +
          "<td>" +
          badges +
          "</td>" +
          '<td style="color:var(--ink-secondary);">' +
          m.desc +
          "</td>" +
          "</tr>"
        );
      })
      .join("");
  }

  /* ------------------------------------------------------------------------
     11. Event Binding on DOMContentLoaded
     ------------------------------------------------------------------------ */
  document.addEventListener("DOMContentLoaded", () => {
    // Footer year
    const yearEl = document.getElementById("footer-year");
    if (yearEl) yearEl.textContent = String(new Date().getFullYear());

    // Apply persisted theme & language
    applyTheme(currentTheme);
    applyLanguage(currentLang);

    // Theme & Language buttons
    const themeBtn = document.getElementById("theme-toggle-btn");
    if (themeBtn) {
      themeBtn.addEventListener("click", () => {
        applyTheme(currentTheme === "light" ? "dark" : "light");
      });
    }

    const langBtn = document.getElementById("lang-toggle-btn");
    if (langBtn) {
      langBtn.addEventListener("click", () => {
        applyLanguage(currentLang === "en" ? "zh" : "en");
      });
    }

    // Mobile menu
    const mobileBtn = document.getElementById("mobile-menu-btn");
    const primaryNav = document.getElementById("primary-nav");
    if (mobileBtn && primaryNav) {
      mobileBtn.addEventListener("click", () => {
        const isOpen = primaryNav.classList.toggle("is-open");
        mobileBtn.setAttribute("aria-expanded", isOpen ? "true" : "false");
      });
      primaryNav.querySelectorAll("a").forEach((link) => {
        link.addEventListener("click", () => {
          primaryNav.classList.remove("is-open");
          mobileBtn.setAttribute("aria-expanded", "false");
        });
      });
    }

    // Hero command tabs
    document.querySelectorAll(".cmd-tab").forEach((btn) => {
      btn.addEventListener("click", () => {
        updateHeroCommand(btn.getAttribute("data-cmd-key"));
      });
    });

    // All Copy buttons
    document.querySelectorAll("[data-copy-target]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const targetId = btn.getAttribute("data-copy-target");
        const targetEl = document.getElementById(targetId);
        if (targetEl) {
          copyTextWithFeedback(targetEl.textContent.trim(), btn);
        }
      });
    });

    // Multimodal 4-tab bar
    document.querySelectorAll("[data-specimen-tab]").forEach((btn) => {
      btn.addEventListener("click", () => {
        selectSpecimenTab(btn.getAttribute("data-specimen-tab"));
      });
    });

    // Tongue somatotopy zone hover
    const zoneBadge = document.getElementById("tongue-zone-badge");
    document.querySelectorAll(".somatotopy-zone").forEach((zone) => {
      const label = zone.getAttribute("data-zone");
      zone.addEventListener("mouseenter", () => {
        if (zoneBadge && label) zoneBadge.textContent = label;
      });
      zone.addEventListener("click", () => {
        if (zoneBadge && label) zoneBadge.textContent = label;
      });
    });

    // Tongue presets
    document.querySelectorAll("[data-tongue-idx]").forEach((btn) => {
      btn.addEventListener("click", () => {
        selectTongueArchetype(Number(btn.getAttribute("data-tongue-idx")));
      });
    });

    // Herb callout pins & chips
    document.querySelectorAll("[data-herb-pin]").forEach((el) => {
      el.addEventListener("click", () => {
        selectHerbCallout(Number(el.getAttribute("data-herb-pin")));
      });
    });

    // Classical Han posology converter
    const hanInput = document.getElementById("han-liang-input");
    const hanSelect = document.getElementById("han-regime-select");
    if (hanInput) hanInput.addEventListener("input", updateHanPosology);
    if (hanSelect) hanSelect.addEventListener("change", updateHanPosology);

    // Pulse waveform buttons
    document.querySelectorAll("[data-pulse-key]").forEach((btn) => {
      btn.addEventListener("click", () => {
        selectPulseWaveform(btn.getAttribute("data-pulse-key"));
      });
    });

    // Formula mini-bench buttons
    document.querySelectorAll("[data-formula-key]").forEach((btn) => {
      btn.addEventListener("click", () => {
        selectMinibenchFormula(btn.getAttribute("data-formula-key"));
      });
    });

    // SOTA Model Task Recommender
    const taskSelect = document.getElementById("model-task-select");
    const taskRec = document.getElementById("model-task-recommendation");
    if (taskSelect && taskRec) {
      taskSelect.addEventListener("change", () => {
        const rec = TASK_RECOMMENDATIONS[taskSelect.value];
        if (rec) taskRec.innerHTML = rec;
      });
    }

    // SOTA Model Filter Pills & Search
    document.querySelectorAll("[data-model-filter]").forEach((pill) => {
      pill.addEventListener("click", () => {
        currentModelFilter = pill.getAttribute("data-model-filter") || "all";
        document.querySelectorAll("[data-model-filter]").forEach((p) => {
          p.classList.toggle("is-active", p === pill);
        });
        renderModelsTable();
      });
    });

    const searchInput = document.getElementById("model-search-input");
    if (searchInput) {
      searchInput.addEventListener("input", renderModelsTable);
    }

    const modelsTbody = document.getElementById("models-ledger-tbody");
    const cliPreview = document.getElementById("selected-model-cli-preview");
    if (modelsTbody && cliPreview) {
      modelsTbody.addEventListener("mouseover", (e) => {
        const link = e.target.closest("[data-model-id]");
        if (link) {
          cliPreview.textContent = "tcm model set " + link.getAttribute("data-model-id");
        }
      });
    }

    renderModelsTable();
  });
})();
