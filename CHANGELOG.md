# Changelog

All notable changes to this project will be documented in this file.

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
