# tcm-cli

An autonomous agent for Traditional Chinese Medicine research and discovery. Like Claude Code, but for TCM.

Ask questions in natural language. tcm-cli plans the analysis, selects the right tools, executes them, validates results, and returns data-backed conclusions.

## Why tcm?

- **30+ TCM research tools** — Herb lookup, formula analysis, syndrome differentiation, network pharmacology, safety checks, literature search, and more.
- **Claude-powered reasoning** — Built on the Anthropic API. Claude plans multi-step research workflows, calls tools, and synthesizes findings.
- **Bilingual** — Supports both Chinese (中文) and English terminology throughout.
- **10+ database APIs** — PubMed, TCMSP, UniProt, STRING, KEGG, ClinicalTrials.gov, Open Targets — no setup required.
- **Research UX** — Interactive terminal with @mentions, slash commands, session export, and clipboard support.
- **Open source** — MIT licensed.

## Installation

### Quick install

```bash
curl -fsSL https://raw.githubusercontent.com/tcm-cli/tcm-cli/main/install.sh | bash
```

### Manual install

```bash
# With pipx (recommended)
pipx install tcm-cli

# Or with pip
pip install tcm-cli

# Or with optional scientific stacks
pip install "tcm-cli[all]"

# Run the setup wizard
tcm setup
```

### Authentication

```bash
# Interactive setup (recommended)
tcm setup

# Or set directly
export ANTHROPIC_API_KEY="sk-ant-..."

# Non-interactive
tcm setup --api-key sk-ant-api03-...
```

## Getting Started

### Basic usage

```bash
# Start interactive session
tcm

# Single query
tcm "What herbs are used for Spleen Qi deficiency?"

# Validate setup
tcm doctor
```

### Interactive commands

Inside `tcm` interactive mode:

- `/help` — command reference + examples
- `/tools` — list all tools with status
- `/model` — switch LLM model/provider
- `/usage` — token and cost tracking
- `/copy` — copy last answer to clipboard
- `/export` — export session transcript
- `/clear` — clear screen
- `/exit` — exit

### Quick examples

**Herb lookup**

```
$ tcm "Tell me about 黄芪 (Astragalus) — properties, compounds, and clinical evidence"
```

**Formula analysis**

```
$ tcm "Analyze the composition of 四君子汤 using the 君臣佐使 framework"
```

**Syndrome differentiation**

```
$ tcm "Patient has fatigue, loose stools, poor appetite, pale tongue. What TCM syndrome?"
```

**Network pharmacology**

```
$ tcm "Build a network pharmacology analysis for 补中益气汤 against diabetes targets"
```

**Safety check**

```
$ tcm "Check interactions between 人参, 藜芦, and Warfarin"
```

## Key Features

### 30+ Domain Tools

| Category | Examples |
| --- | --- |
| **Herbs** | Lookup, property classification, meridian search, compound listing |
| **Formulas** | Classical formula search, 君臣佐使 analysis, modifications |
| **Syndromes** | Pattern differentiation, symptom-to-syndrome mapping, treatment plans |
| **Compounds** | Active compound search, ADMET prediction, target identification |
| **Pharmacology** | Network pharmacology, pathway enrichment, herb-target networks |
| **Interactions** | 十八反/十九畏 checks, herb-drug interactions, formula safety |
| **Literature** | PubMed search, systematic review finder, CNKI integration |
| **Meridians** | Channel lookup, Five Element associations, meridian-herb mapping |
| **Safety** | Toxicity profiling, pregnancy safety, dosage validation |
| **Modern** | Clinical trial search, ICD-10 mapping, evidence summaries |
| **Data APIs** | TCMSP, UniProt, STRING, KEGG, ClinicalTrials.gov, Open Targets |
| **Code** | Python sandbox for custom analysis |

### Data Management

```bash
tcm data pull tcmsp      # TCMSP compound-target data
tcm data pull tcmid       # TCMID herb-compound data
tcm data pull formulas    # Classical formula database
tcm data pull herbs       # Herb monograph database
tcm data status           # Show dataset status
```

Without local data, tcm still works using database APIs and built-in knowledge.

## Configuration

```bash
tcm config show             # Show all settings
tcm config set key value    # Set a value
tcm config validate         # Check for issues
```

### Agent profiles

```bash
tcm config set agent.profile research    # Default — balanced
tcm config set agent.profile clinical    # Strict evidence, no hypotheses
tcm config set agent.profile education   # Relaxed, creative
```

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `tcm` fails at startup | `tcm doctor` |
| No API key | `tcm setup` or `export ANTHROPIC_API_KEY=...` |
| Missing dependency | `pip install "tcm-cli[all]"` |
| Tool module failed | Check `tcm tool list` for errors |

## Contributing

```bash
git clone https://github.com/tcm-cli/tcm-cli.git
cd tcm-cli
pip install -e ".[dev]"
tcm setup
pytest tests/
```

## License

MIT
