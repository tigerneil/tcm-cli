# SOTA Multimodal Model Catalog & TCM Task Routing

`tcm` ships a curated **November 2026 SOTA Model Catalog** (`MODEL_CATALOG` in `src/tcm/models/llm.py`) spanning **15 cloud and local providers** with first-class support for **Text**, **Vision**, **Audio**, **Video**, **PDF**, and **Adaptive Thinking** modalities, paired with quantitative CIE $L^*a^*b^*$ tongue/herb colorimetry (`src/tcm/models/multimodal.py`).

See [PROVIDERS.md](./PROVIDERS.md) for API key setup, environment variables, and custom base URLs.

---

## 1. November 2026 SOTA Frontier & Flagship Models

### Anthropic (`anthropic`)

| Model ID | Display Name | Context | Max Out | Modalities | Tier | Price (In / Out per 1M) |
| --- | --- | --- | --- | --- | --- | --- |
| `claude-fable-5-2` | Claude Fable 5.2 | 1,000,000 | 128,000 | `text`, `vision`, `pdf`, `thinking` | `frontier` | \$8.00 / \$40.00 |
| `claude-opus-5-5` | Claude Opus 5.5 | 1,000,000 | 128,000 | `text`, `vision`, `pdf`, `thinking` | `frontier` | \$4.00 / \$20.00 |
| `claude-sonnet-5-5` | Claude Sonnet 5.5 | 1,000,000 | 128,000 | `text`, `vision`, `pdf`, `thinking` | `flagship` | \$2.00 / \$10.00 |
| `claude-haiku-5-5` | Claude Haiku 5.5 | 1,000,000 | 128,000 | `text`, `vision`, `pdf` | `fast` | \$0.10 / \$0.50 |
| `claude-sonnet-4-5-20250929` | Claude Sonnet 4.5 *(default)* | 200,000 | 64,000 | `text`, `vision`, `pdf`, `thinking` | `flagship` | \$3.00 / \$15.00 |
| `claude-opus-4-6` | Claude Opus 4.6 | 200,000 | 64,000 | `text`, `vision`, `pdf`, `thinking` | `frontier` | \$15.00 / \$75.00 |
| `claude-haiku-4-5-20251001` | Claude Haiku 4.5 | 200,000 | 64,000 | `text`, `vision`, `pdf` | `fast` | \$0.80 / \$4.00 |

### OpenAI (`openai`)

| Model ID | Display Name | Context | Max Out | Modalities | Tier | Price (In / Out per 1M) |
| --- | --- | --- | --- | --- | --- | --- |
| `gpt-6-astra` | GPT-6 Astra | 1,050,000 | 128,000 | `text`, `vision`, `audio`, `pdf`, `thinking` | `frontier` | \$10.00 / \$50.00 |
| `gpt-6.1-sol` | GPT-6.1 Sol | 1,050,000 | 128,000 | `text`, `vision`, `pdf`, `thinking` | `flagship` | \$2.00 / \$10.00 |
| `gpt-6.1-terra` | GPT-6.1 Terra | 1,050,000 | 128,000 | `text`, `vision`, `pdf` | `balanced` | \$1.00 / \$5.00 |
| `gpt-6-luna` | GPT-6 Luna | 1,050,000 | 128,000 | `text`, `vision` | `fast` | \$0.10 / \$0.50 |
| `gpt-5.4` | GPT-5.4 | 1,000,000 | 64,000 | `text`, `vision`, `thinking` | `flagship` | \$1.75 / \$7.00 |
| `gpt-rosalind-research` | GPT-Rosalind | 1,000,000 | 64,000 | `text`, `vision`, `thinking` | `specialized` | \$6.00 / \$24.00 |
| `gpt-4.1` / `mini` / `nano` | GPT-4.1 Family | 1,047,576 | 32,768 | `text`, `vision`, `pdf` | `flagship`–`fast` | \$0.10–\$2.00 / \$0.40–\$8.00 |
| `gpt-4o` / `gpt-4o-mini` / `o3-mini` | GPT-4o & o3-mini | 128k–200k | 16k–65k | `text`, `vision`, `audio`, `thinking` | `flagship`–`fast` | \$0.15–\$2.50 / \$0.60–\$10.00 |

### Google Gemini (`google`)

| Model ID | Display Name | Context | Max Out | Modalities | Tier | Price (In / Out per 1M) |
| --- | --- | --- | --- | --- | --- | --- |
| `gemini-3.6-flash` | Gemini 3.6 Flash | 1,048,576 | 65,536 | `text`, `vision`, `audio`, `video`, `pdf`, `thinking` | `flagship` | \$0.20 / \$0.80 |
| `gemini-3.5-flash-lite` | Gemini 3.5 Flash-Lite | 1,048,576 | 65,536 | `text`, `vision`, `audio`, `pdf` | `fast` | \$0.08 / \$0.32 |
| `gemini-3.1-pro-preview` | Gemini 3.1 Pro Preview | 1,048,576 | 65,536 | `text`, `vision`, `audio`, `video`, `pdf`, `thinking` | `frontier` | \$2.00 / \$12.00 |
| `gemini-2.5-pro` | Gemini 2.5 Pro | 1,048,576 | 65,536 | `text`, `vision`, `audio`, `video`, `pdf`, `thinking` | `flagship` | \$1.25 / \$10.00 |
| `gemini-2.5-flash` | Gemini 2.5 Flash | 1,048,576 | 65,536 | `text`, `vision`, `audio`, `video`, `pdf`, `thinking` | `balanced` | \$0.15 / \$0.60 |

> Additional Gemini models in catalog: `gemini-3-pro-preview`, `gemini-3-flash-preview`, `gemini-2.5-flash-lite`, `gemini-2.0-flash`, `gemini-2.0-flash-lite`, `gemini-pro-latest`, `gemini-flash-latest`.

### Bilingual TCM & Global Cloud Providers

| Provider | Model ID | Display Name | Context | Modalities | Tier | Price (In / Out per 1M) |
| --- | --- | --- | --- | --- | --- | --- |
| `deepseek` | `deepseek-v4-pro` | DeepSeek V4 Pro (1.6T MoE) | 1,000,000 | `text`, `thinking` | `frontier` | \$0.66 / \$1.98 |
| `deepseek` | `deepseek-v4.1-flash` | DeepSeek V4.1 Flash (552B MoE) | 1,000,000 | `text`, `vision`, `thinking` | `flagship` | \$0.15 / \$0.60 |
| `qwen` | `qwen3.8-max` | Qwen 3.8 Max | 1,000,000 | `text`, `vision`, `thinking` | `frontier` | \$0.80 / \$2.40 |
| `qwen` | `qwen-vl-max` | Qwen-VL Max | 1,000,000 | `text`, `vision`, `pdf` | `specialized` | \$0.40 / \$1.20 |
| `qwen` | `qwen3.8-27b` | Qwen 3.8 27B | 262,144 | `text`, `thinking` | `balanced` | \$0.15 / \$0.45 |
| `kimi` | `kimi-k3.1-pro` | Kimi K3.1 Pro | 1,000,000 | `text`, `vision`, `thinking` | `frontier` | \$0.90 / \$2.80 |
| `kimi` | `kimi-k3` | Kimi K3 (2.8T MoE) | 1,000,000 | `text`, `vision` | `flagship` | \$0.50 / \$1.80 |
| `glm` | `glm-5.3` | GLM-5.3 | 1,000,000 | `text`, `thinking` | `frontier` | \$0.50 / \$1.50 |
| `glm` | `glm-5.3-flash` | GLM-5.3 Flash | 1,000,000 | `text` | `fast` | \$0.08 / \$0.25 |
| `glm` | `glm-4v-plus` | GLM-4V Plus | 128,000 | `text`, `vision` | `specialized` | \$0.35 / \$1.05 |
| `minimax` | `minimax-m3` | MiniMax M3 | 1,000,000 | `text`, `vision`, `audio` | `flagship` | \$0.40 / \$1.20 |
| `minimax` | `minimax-m3.1-flash` | MiniMax M3.1 Flash | 1,000,000 | `text`, `vision` | `fast` | \$0.10 / \$0.30 |
| `xai` | `grok-4.8` | Grok 4.8 | 1,000,000 | `text`, `vision`, `thinking` | `frontier` | \$3.00 / \$15.00 |
| `xai` | `grok-4-vision` | Grok 4 Vision | 256,000 | `text`, `vision` | `flagship` | \$2.00 / \$10.00 |
| `mistral` | `mistral-large-latest` | Mistral Large | 256,000 | `text` | `flagship` | \$2.00 / \$6.00 |
| `mistral` | `pixtral-large-latest` | Pixtral Large | 128,000 | `text`, `vision` | `specialized` | \$2.00 / \$6.00 |
| `groq` | `llama-3.3-70b-versatile` | Llama 3.3 70B Versatile | 128,000 | `text` | `fast` | \$0.59 / \$0.79 |
| `groq` | `llama-3.1-70b-versatile` | Llama 3.1 70B Versatile | 128,000 | `text` | `fast` | \$0.59 / \$0.79 |
| `cohere` | `command-a-03-2025` | Command A | 256,000 | `text` | `flagship` | \$2.50 / \$10.00 |
| `cohere` | `command-r-plus` | Command R+ | 128,000 | `text` | `balanced` | \$2.50 / \$10.00 |
| `openrouter` | `openrouter/auto` | OpenRouter Auto SOTA | 1,000,000 | `text`, `vision` | `balanced` | Dynamic |
| `together` | `together/deepseek-v4-pro` | DeepSeek V4 Pro (Together) | 1,000,000 | `text`, `thinking` | `flagship` | \$0.80 / \$2.40 |

### Private On-Premise Medical Models (`ollama`)

| Model ID | Display Name | Context | Modalities | Tier | Clinical Role |
| --- | --- | --- | --- | --- | --- |
| `ollama/medgemma:27b` | MedGemma 27B Multimodal (Local) | 131,072 | `text`, `vision` | `local` | Local medical imaging & clinical decision support |
| `ollama/huatuogpt-vision:7b` | HuatuoGPT-Vision 7B (Local) | 32,768 | `text`, `vision` | `local` | Specialized Chinese TCM & tongue diagnosis local VLM |
| `ollama/qwen3:32b` | Qwen3 32B (Local Ollama) | 131,072 | `text`, `thinking` | `local` | Private on-premise bilingual TCM reasoning |

---

## 2. Task-Specific TCM Model Recommendations

Use `recommend_models_for_task(task=..., modalities=...)` from `tcm.models.multimodal` to rank top models for specialized Traditional Chinese Medicine workflows:

| Task Key | Primary Top-Ranked Models | Rationale |
| --- | --- | --- |
| `general` | `claude-sonnet-5-5`, `gpt-6.1-sol`, `gemini-3.6-flash` | Balanced multimodal intelligence, tool orchestration, and 1M context |
| `tongue_vision` | `gemini-3.6-flash`, `qwen-vl-max`, `gpt-6.1-terra`, `glm-4v-plus` | High-resolution tongue coating, sublingual veins & Four Examinations (四诊合参) |
| `herb_identification` | `gpt-6.1-terra`, `qwen-vl-max`, `gemini-3.6-flash`, `pixtral-large-latest` | Decoction-piece (`饮片`) morphology, slice cross-sections & pharmacognosy |
| `classical_ocr` | `qwen-vl-max`, `kimi-k3.1-pro`, `gemini-3.1-pro-preview` | Vertical woodblock printing (`本草纲目`, `伤寒论`), traditional characters & scanned PDFs |
| `network_pharmacology` | `gpt-rosalind-research`, `claude-fable-5-2`, `deepseek-v4-pro` | Multi-compound ADMET, SMILES/target docking & Jun-Chen-Zuo-Shi synergy |
| `clinical_safety` | `claude-opus-5-5`, `claude-fable-5-2`, `gpt-6-astra`, `gpt-rosalind-research` | CYP450 herb-drug interactions, Eighteen Incompatibilities (`十八反`) & DILI safety |
| `bilingual_synthesis` | `qwen3.8-max`, `deepseek-v4-pro`, `kimi-k3.1-pro`, `glm-5.3` | Classical Chinese (`文言文`) philology aligned with WHO ICD-11 & biomedical English |
| `offline_local` | `ollama/medgemma:27b`, `ollama/huatuogpt-vision:7b`, `ollama/qwen3:32b` | Zero-egress local clinical & tongue vision inference via Ollama |

---

## 3. Quantitative CIE $L^*a^*b^*$ Tongue & Herb Colorimetry

Before sending tongue or herb specimen imagery to a vision LLM, `extract_image_biometrics()` computes deterministic sRGB $\rightarrow$ CIE XYZ (D65) $\rightarrow$ CIE $L^*a^*b^*$ biometrics in pure Python + NumPy:

- **Colorimetric Axes**:
  - $L^*$ (`0–100`): Lightness / pallor index ($L^* > 68, a^* < 16 \Rightarrow$ Pale tongue `淡白舌`, Qi/Blood/Yang deficiency hint).
  - $a^*$ (`green–magenta`): Erythema / Heat index ($a^* > 32 \Rightarrow$ Red tongue `红舌`; $a^* > 42 \Rightarrow$ Crimson `绛舌`, Yin-deficiency fire or Ying/Blood heat).
  - $b^*$ (`blue–yellow`): Greasy-yellow coating / stasis axis ($b^* > 22$ in center $\Rightarrow$ Yellow coating `黄腻苔`, Spleen-Stomach Damp-Heat; $b^* < 5, a^* < 20 \Rightarrow$ Cyanotic/purple `青紫舌`, Blood stasis `血瘀`).
  - `moisture_gloss_index` (`0.0–1.0`): Fraction of high-luminance, low-chroma specular highlight pixels (`水滑苔` vs. `燥苔`).
- **TCM Tongue Somatotopy (`zones`)**:
  - `tip`: **Heart / Lung (心肺)**
  - `center`: **Spleen / Stomach (脾胃)**
  - `sides`: **Liver / Gallbladder (肝胆)**
  - `root`: **Kidney (肾)**

---

## 4. Python API Quickstart

```python
from tcm.models.llm import LLMClient, list_models
from tcm.models.multimodal import (
    extract_image_biometrics,
    load_attachment,
    recommend_models_for_task,
)

# 1. Filter catalog by modality and tier
omni_models = list_models(modality="audio", tier="flagship")

# 2. Get top 5 SOTA recommendations for tongue diagnostics
top_tongue = recommend_models_for_task("tongue_vision", modalities=["vision"])

# 3. Extract quantitative CIE L*a*b* tongue somatotopy metrics
biometrics = extract_image_biometrics("patient_tongue.png")

# 4. Run multimodal chat across any supported provider
att = load_attachment("patient_tongue.png")
client = LLMClient(provider="google", model="gemini-3.6-flash")
resp = client.chat(
    system="You are an integrative TCM tongue diagnosis specialist.",
    messages=[{"role": "user", "content": f"Analyze tongue image with biometrics: {biometrics}"}],
    attachments=[att],
)
```
