# Changelog

All notable changes to this project will be documented in this file.

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
