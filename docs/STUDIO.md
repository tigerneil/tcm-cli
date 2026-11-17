# Multimodal TCM Studio

**TCM Studio** (`tcm studio`) transforms `tcm-cli` from a text-only terminal agent into a full **Multimodal Traditional Chinese Medicine Research & Clinical Application Workbench**. It bridges classical **Four Examinations (`四诊合参`: Inspection `望`, Auscultation/Olfaction `闻`, Inquiry `问`, Palpation `切`)** with **Computational Network Pharmacology**, **Classical Canon Philology**, and **35+ SOTA Foundation Models**.

---

## Launching TCM Studio

```bash
# Start local TCM Studio server on http://127.0.0.1:8765 and open in browser
tcm studio --open

# Bind to a custom port or pre-select a SOTA multimodal model
tcm studio --port 8890 --model claude-opus-5-5

# Use a local open-weight medical VLM via Ollama (air-gapped / private clinical use)
tcm studio --model ollama/huatuogpt-vision:7b
```

You can also open the standalone interactive web application directly from `docs/studio.html` (or on GitHub Pages). When the local Python server (`tcm studio`) is running, the frontend automatically connects to `/api/*` for live Python tool execution and SOTA multimodal LLM synthesis; when hosted statically, it runs via its built-in client-side colorimetric and pharmacological engine.

---

## Core Studio Workspaces

### 1. Multimodal Four-Examinations Lab (`四诊多模态实验台`)

- **Tongue Vision & CIE-$L^*a^*b^*$ Colorimetry (`望舌象`)**
  - Upload clinical tongue photographs or inspect built-in reference archetypes.
  - Computes quantitative sRGB and CIE $L^*a^*b^*$ metrics ($L^*$ pallor/lightness, $a^*$ erythema/heat index, $b^*$ yellow-greasy coating index, specular moisture index) across classical tongue somatotopy zones:
    - **Tip (`舌尖`)** — Heart & Lung (`心肺`)
    - **Center (`舌中`)** — Spleen & Stomach (`脾胃`)
    - **Margins (`舌边`)** — Liver & Gallbladder (`肝胆`)
    - **Root (`舌根`)** — Kidney & Lower Jiao (`肾与下焦`)
  - Combines quantitative biometrics with SOTA Vision LLMs (`claude-opus-5-5`, `gpt-6.1-terra`, `gemini-3.6-flash`, `qwen-vl-max`, `deepseek-v4.1-flash`) and `diagnostics.tongue_analyze`.

- **Crude Herb & Decoction Piece Authentication (`饮片性状鉴别`)**
  - Macroscopic pharmacognosy analysis via `diagnostics.herb_identify` (e.g., *chrysanthemum-heart* `菊花心` striations in *Radix Astragali* `黄芪`, *pearl warts* `珍珠点` in *Panax ginseng* `人参`, *chicken-claw* `鸡爪连` rhizomes in *Coptis* `黄连`, *holding-the-moon* `怀中抱月` scales in *Fritillaria cirrhosa* `川贝母`).
  - Highlights common adulterants, `炮制` processing specifications (`生用`, `蜜炙`, `酒制`, `盐制`, `先煎`), and chemical quality markers.

- **Classical Prescription & Woodblock OCR (`古籍方笺解析`)**
  - Parses modern clinical prescriptions and classical unpunctuated formulas via `diagnostics.prescription_parse`.
  - Converts historical metrology into modern metric grams:
    - **Eastern Han (*Shanghan Lun*)**: archeological `1两 ≈ 13.8g` and conservative clinical `1两 ≈ 3.0g`
    - **Ming / Qing Dynasty**: `1两 ≈ 31.2g`, `1钱 ≈ 3.12g`, `1分 ≈ 0.31g`
    - **Modern Clinical**: metric `g` (`克`) and `1钱 ≈ 3.0g`
  - Automatically runs **Eighteen Incompatibilities (`十八反`)**, **Nineteen Antagonisms (`十九畏`)**, aconitine/toxic herb decoction checks, and pregnancy contraindications.

- **Four-Examinations Synthesis (`四诊合参`)**
  - Integrates visual inspection (`望`), acoustic/respiratory observations (`闻`), Ten Questions symptom vectors (`十问歌`), and the **28 Classical Pulse Qualities (`二十八脉`)** into an Eight-Principles (`八纲`) profile, ranked Zang-Fu syndromes, classical formula + modifications, and acupuncture protocol.

---

### 2. Formula Composer & Network Pharmacology Lab (`方剂配伍与网络药理`)

- Interactive **Force-Directed Multi-Layer Graph**:
  `Classical Formula → Sovereign/Minister/Assistant/Courier Herbs (君臣佐使) → Bioactive Compounds → Human Protein Targets → Signaling Pathways`
- Node inspection for Oral Bioavailability (`OB%`), Drug-Likeness (`DL`), UniProt target symbols, and pathway enrichment.
- Real-time **Herb–Herb & Herb–Drug Safety Engine** checking anticoagulants (`Warfarin`, `Aspirin`), cardiac glycosides (`Digoxin`), immunosuppressants (`Cyclosporine`), and pregnancy safety.

---

### 3. Materia Medica, Meridian Acupoints & Classics (`本草・经穴・典籍`)

- **Acupoint & Meridian Atlas (`acupuncture.*`)**: WHO standard codes (`ST36 足三里`, `LI4 合谷`, `LR3 太冲`, `PC6 内关`, `GV20 百会`, `SP6 三阴交`, `KI3 太溪`, `CV4 关元`, etc.), anatomical locations, needling depth, moxibustion notes, and pregnancy-safe protocol filtering.
- **Classical TCM Canon Corpus (`classics.*`)**: Bilingual clause search across *Huangdi Neijing* (`黄帝内经`), *Shanghan Lun* (`伤寒论`), *Jin Gui Yao Lue* (`金匮要略`), *Shennong Bencao Jing* (`神农本草经`), *Wenbing Tiaobian* (`温病条辨`), *Pi Wei Lun* (`脾胃论`), and *Bencao Gangmu* (`本草纲目`).

---

### 4. SOTA Model Router & Research Console (`大模型路由与智能体终端`)

- Multi-step `Plan → Execute → Grounded Bilingual Synthesis` workflow with support for image, audio, and PDF attachments.
- Task-aware SOTA model routing (`tcm model recommend tongue_vision`) across 14 cloud and local providers.

---

## Multimodal CLI Usage

All multimodal capabilities are also available directly from your terminal:

```bash
# Analyze a tongue image with a Vision-capable SOTA model
tcm -i tongue_photo.jpg --model claude-opus-5-5 --lang bi \
  "Perform tongue diagnosis (望舌象) and recommend a classical formula"

# Authenticate a decoction piece photograph
tcm -i specimen.jpg --model qwen-vl-max \
  "Identify this crude herb slice, authentication markers, and processing notes"

# Parse an image or PDF of a classical prescription
tcm -f prescription.pdf --model gemini-3.6-flash \
  "Extract herbs, convert Eastern Han dosages to grams, and check 十八反 safety"

# Recommend top SOTA models for a specific TCM modality/task
tcm model recommend tongue_vision
tcm model list --modality vision
```

---

## REST API Reference (`tcm studio`)

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Server health, active model/provider, configured keys, tool count |
| `GET` | `/api/models` | Filterable SOTA model catalog (`?provider=&modality=&tier=&task=`) |
| `POST` | `/api/models/select` | Switch active LLM model/provider and output language |
| `GET` | `/api/tools` | List all registered computational TCM tools by category |
| `POST` | `/api/tools/run` | Execute any registered TCM tool directly with JSON parameters |
| `POST` | `/api/diagnose/tongue` | Quantitative CIE-$L^*a^*b^*$ tongue biometrics + syndrome differentiation + optional Vision LLM |
| `POST` | `/api/diagnose/herb` | Macroscopic decoction piece authentication + Materia Medica lookup |
| `POST` | `/api/diagnose/prescription` | Classical/modern prescription parser + metrology conversion + safety screen |
| `POST` | `/api/diagnose/four-examinations` | Full `四诊合参` synthesis + acupoint protocol + classical canon references |
| `POST` | `/api/pharmacology/network` | Build `Formula → Herb → Compound → Target → Pathway` graph & safety profile |
| `POST` | `/api/agent/query` | Full multimodal `Plan → Execute → Synthesize` research pipeline |
