# tcm-cli

An autonomous agent for Traditional Chinese Medicine research and discovery.

Ask questions in natural language. tcm-cli plans the analysis, selects the right tools, executes them, validates results, and returns data-backed conclusions.

## Why tcm?

- **30+ TCM research tools** — Herb lookup, formula analysis, syndrome differentiation, network pharmacology, safety checks, literature search, and more.
- **Multi-model reasoning** — Powered by leading LLMs (OpenAI GPT-4o, o3, and more). Automatically plans multi-step research workflows, calls tools, and synthesizes findings.
- **Bilingual** — Supports both Chinese (中文) and English terminology throughout.
- **10+ database APIs** — PubMed, TCMSP, UniProt, STRING, KEGG, ClinicalTrials.gov, Open Targets — no setup required.
- **Research UX** — Interactive terminal with slash commands, session export, and clipboard support.
- **Open source** — MIT licensed.

## Requirements

- Python 3.10+
- An LLM API key (OpenAI or compatible)

## Installation

### Quick install (script)

```bash
curl -fsSL https://raw.githubusercontent.com/tigerneil/tcm-cli/main/install.sh | bash
```

The script detects `pipx`, `uv`, or falls back to `pip --user`, then runs `tcm setup`.

### With pipx (recommended)

```bash
pipx install tcm-cli
```

### With pip

```bash
# Core install
pip install tcm-cli

# With chemistry support (RDKit)
pip install "tcm-cli[chemistry]"

# With ML support (PyTorch + Transformers)
pip install "tcm-cli[ml]"

# With analysis stack (scikit-learn, seaborn, scipy)
pip install "tcm-cli[analysis]"

# Everything
pip install "tcm-cli[all]"
```

### Authentication

```bash
# Interactive setup wizard (recommended)
tcm setup

# Or export directly
export OPENAI_API_KEY="sk-..."

# Non-interactive (CI/scripting)
tcm setup --api-key YOUR_API_KEY
```

API keys are stored at `~/.tcm/config.json`. Check key status with:

```bash
tcm keys
```

## Getting Started

### Basic usage

```bash
# Start interactive session
tcm

# Single query
tcm "What herbs are used for Spleen Qi deficiency?"

# Use a specific model
tcm --model gpt-4o "Analyze 四君子汤"

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
| **Code** | Python sandbox for custom analysis (experimental) |

List all tools and their status:

```bash
tcm tool list
```

### Supported Models

| Provider | Model | Context | Notes |
| --- | --- | --- | --- |
| OpenAI | `gpt-4o` | 128k | Default — best balance |
| OpenAI | `gpt-4o-mini` | 128k | Fast and affordable |
| OpenAI | `o3-mini` | 200k | Reasoning model |
| OpenAI | `gpt-4.1` | 1M | Latest flagship with 1M context |
| OpenAI | `gpt-4.1-mini` | 1M | Balanced speed and intelligence |
| OpenAI | `gpt-4.1-nano` | 1M | Fastest, most cost-effective |

Switch models:

```bash
tcm model list              # Show all models with pricing
tcm model set gpt-4o        # Switch to GPT-4o
tcm model show              # Show current model
```

### Local Datasets

Without local data, tcm works via database APIs and built-in knowledge. To boost accuracy and offline support, pull datasets:

```bash
tcm data pull tcmsp      # TCMSP — herbs, compounds, targets (~50 MB)
tcm data pull tcmid      # TCMID — herb-compound-disease (~30 MB)
tcm data pull herbs      # Chinese Pharmacopoeia herb monographs (~5 MB)
tcm data pull formulas   # Classical formula database (~3 MB)
tcm data pull batman     # BATMAN-TCM bioinformatics data (~100 MB)
tcm data pull symmap     # SymMap symptom-mapping database (~20 MB)
tcm data status          # Show dataset status
```

> **Note:** Automated download is not yet implemented for all datasets. The command shows the source URL and target path; download manually and configure the path with `tcm config set data.<name> <path>`.

## Configuration

```bash
tcm config show             # Show all settings
tcm config set key value    # Set a value
tcm config get key          # Get a single value
tcm config validate         # Check for issues
```

Config is stored at `~/.tcm/config.json`.

### Common config keys

```bash
tcm config set llm.provider openai          # openai or compatible
tcm config set llm.model gpt-4o
tcm config set ui.language zh               # en (default) or zh
```

### Agent profiles

```bash
tcm config set agent.profile research    # Default — balanced, allows hypotheses
tcm config set agent.profile clinical    # Strict evidence only, no hypotheses
tcm config set agent.profile education   # Relaxed, creative responses
```

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `tcm` fails at startup | `tcm doctor` |
| Authentication error | `tcm setup` or `tcm keys` |
| Missing API key | `export OPENAI_API_KEY=...` or `tcm config set llm.openai_api_key ...` |
| Missing dependency | `pip install "tcm-cli[all]"` |
| Tool module failed | `tcm tool list` — check for load errors |

## Contributing

```bash
git clone https://github.com/tigerneil/tcm-cli.git
cd tcm-cli
pip install -e ".[dev]"
tcm setup
pytest tests/
```

## License

MIT
