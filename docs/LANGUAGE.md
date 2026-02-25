# Language Modes

TCM CLI can answer in English, Chinese, or Bilingual. You can set the language per run, in the interactive REPL, or persist it in config.

## Quick usage

```bash
# Per run
 tcm --lang en "Check interactions between 人参 and 藜芦"
 tcm --lang zh "分析 四君子汤 的组成与配伍"
 tcm --lang bi "Network pharmacology for 补中益气汤"

# Interactive REPL
 tcm
 /lang           # show current (en|zh|bi)
 /lang bi        # set to bilingual

# Persist default
 tcm config set ui.language bi   # en (default) | zh | bi
```

## Behavior by mode

- en: English-only output (no Chinese characters unless quoted), with pinyin when helpful (e.g., Ren Shen (ginseng)).
- zh: 仅中文输出（除非为引用或专名不宜翻译）。
- bi: Bilingual; headings are paired (e.g., "## 关键信息 | Key Findings"), and bullet points are aligned across languages.

## Notes

- The language setting controls the synthesizer’s output style. Tool execution remains unchanged.
- You can switch languages at any time in a session; the next answer will follow the new setting.
- To reset to English-only for CI or scripts, pass `--lang en` explicitly.
