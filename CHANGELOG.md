# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2026-11-16

### Added
- **Multimodal TCM Studio (`tcm studio` & `docs/studio.html`)**:
  - Zero-dependency thread-safe HTTP + REST API server (`src/tcm/studio/server.py`) with 11 endpoints (`/api/health`, `/api/models`, `/api/models/select`, `/api/tools`, `/api/tools/run`, `/api/diagnose/tongue`, `/api/diagnose/herb`, `/api/diagnose/prescription`, `/api/diagnose/four-examinations`, `/api/pharmacology/network`, `/api/agent/query`) and deterministic offline fallback.
  - 4-workspace interactive web studio: **Four-Examinations Lab (`四诊多模态实验台`)**, **Formula & Force-Directed Network Pharmacology (`方剂配伍与网络药理`)**, **Materia Medica, Meridian Acupoints & Classics (`本草・经穴・典籍`)**, and **SOTA Agent Console (`智能体研究终端`)**.
- **Multimodal Media & Quantitative CIE-$L^*a^*b^*$ Biometrics (`src/tcm/models/multimodal.py`)**:
  - `MediaAttachment` & `load_attachment()` for images, audio, video, and PDF documents.
  - Pure-Python + NumPy PNG/JPEG colorimetric analyzer (`extract_image_biometrics`) computing sRGB, CIE $L^*a^*b^*$, redness/yellowness/moisture indices, and 4-zone TCM tongue somatotopy (`舌尖心肺`, `舌中脾胃`, `舌边肝胆`, `舌根肾`).
  - Multimodal payload builders for Anthropic, OpenAI-compatible, and Google Gemini SDKs, plus `recommend_models_for_task()`.
- **SOTA Foundation Model Catalog & New Providers (`src/tcm/models/llm.py`, `src/tcm/agent/config.py`)**:
  - Expanded catalog to **61 models across 15 providers**, adding Anthropic Claude 5.2/5.5 (`claude-fable-5-2`, `claude-opus-5-5`, `claude-sonnet-5-5`, `claude-haiku-5-5`), OpenAI GPT-6 & Life Sciences (`gpt-6-astra`, `gpt-6.1-sol`, `gpt-6.1-terra`, `gpt-6-luna`, `gpt-5.4`, `gpt-rosalind-research`), Google Gemini 3.6/3.5 (`gemini-3.6-flash`, `gemini-3.5-flash-lite`), DeepSeek V4 (`deepseek-v4-pro`, `deepseek-v4.1-flash`), Qwen 3.8 & VL (`qwen3.8-max`, `qwen-vl-max`, `qwen3.8-27b`), Moonshot Kimi K3 (`kimi-k3.1-pro`, `kimi-k3`), Zhipu GLM (`glm-5.3`, `glm-5.3-flash`, `glm-4v-plus`), MiniMax M3 (`minimax-m3`, `minimax-m3.1-flash`), xAI Grok (`grok-4.8`, `grok-4-vision`), Mistral Pixtral (`pixtral-large-latest`), Groq (`llama-3.3-70b-versatile`), Cohere (`command-a-03-2025`), Together, OpenRouter, and Local Ollama medical models (`ollama/medgemma:27b`, `ollama/huatuogpt-vision:7b`, `ollama/qwen3:32b`).
- **3 New Computational TCM Tool Modules (bringing total to 50 tools across 15 modules)**:
  - `diagnostics`: `tongue_analyze`, `herb_identify`, `prescription_parse` (Eastern Han, Ming/Qing, and Modern metrology conversion + automated safety checks), and `four_examinations` (with 28 classical pulse qualities `二十八脉`).
  - `acupuncture`: `point_lookup`, `by_meridian`, and `protocol` across 28 WHO acupoints on 14 channels with `pregnancy_safe` substitution.
  - `classics`: `search`, `clause_lookup`, and `herb_monograph` across 7 foundational canons (*Huangdi Neijing*, *Shanghan Lun*, *Jin Gui Yao Lue*, *Shennong Bencao Jing*, *Wenbing Tiaobian*, *Pi Wei Lun*, *Bencao Gangmu*).
- **Multimodal CLI & REPL Commands**:
  - `tcm studio`, `tcm -i/--image`, `--audio`, `-f/--file`, `tcm model list --modality ...`, `tcm model recommend <task>`, plus REPL `/attach`, `/attachments`, `/studio`, and Linux/macOS clipboard support.
- **Refactored Official Website & Documentation**:
  - Complete editorial redesign of `docs/index.html`, `docs/styles.css`, and `docs/script.js` with Xuan Parchment Daylight & Sumi Ink Night themes, instant `EN / 中文` bilingual switching, interactive Four-Examinations plates, and bespoke botanical/manuscript photography.
  - Added `docs/STUDIO.md` and `docs/MODELS.md`; updated `docs/PROVIDERS.md` and `docs/README.md`.

## [0.1.4] - 2026-02-27

Fixed
- Python 3.9/3.10/3.11 compatibility: added `from __future__ import annotations` to all
  source files that use PEP 604 (`X | Y`) union type syntax.
- Lowered `requires-python` from `>=3.10` to `>=3.9`; added Python 3.9 classifier.

## [0.1.3] - 2026-02-27

Added
- Google (Gemini) full support via new `google-genai` SDK (migrated from deprecated `google.generativeai`).
- Updated Google Gemini model catalog with real API model IDs:
  - Stable: `gemini-2.5-pro`, `gemini-2.5-flash` (new default), `gemini-2.5-flash-lite`, `gemini-2.0-flash`, `gemini-2.0-flash-lite`
  - Preview/Frontier: `gemini-3.1-pro-preview`, `gemini-3-pro-preview`, `gemini-3-flash-preview`
  - Aliases: `gemini-pro-latest`, `gemini-flash-latest`
- New CLI command `tcm model google` — fetches all available Gemini models live from the API.
- `list_google_models()` helper for programmatic model discovery.

Changed
- Dependency: `google-generativeai` → `google-genai>=1.0`.
- Default Google model: `gemini-1.5-pro` → `gemini-2.5-flash`.

Fixed
- Removed non-existent model IDs (`gemini-3.0-pro`, `gemini-3.1-pro`, `gemini-2.5-pro-preview-03-25`, `gemini-1.5-flash-8b`).

## [0.1.2] - 2026-02-25

Added
- Language switch for synthesizer output: English (`en`), Chinese (`zh`), and Bilingual (`bi`).
  - CLI flag: `--language` / `--lang`
  - REPL command: `/lang en|zh|bi`
  - Config key: `ui.language`
- Docs: `docs/LANGUAGE.md` and links from README.

Fixed
- Kimi provider temperature constraint: normalize to `temperature=1.0` for Moonshot Kimi to avoid API error.
- Indentation error in `src/tcm/ui/terminal.py` (moved `_lang_switch` into `InteractiveTerminal`).

## [0.1.1] - 2026-02-XX

- Initial public release with core agent, tools, and CLI.
