# Providers and API Keys

`tcm` supports **15 LLM providers** across frontier cloud labs, Chinese bilingual medical ecosystems, open-weight inference routers, and 100% private local Ollama deployments. You only need **one** provider to run `tcm`, and you can configure multiple providers to switch models mid-session or route tasks by modality.

See [MODELS.md](./MODELS.md) for the complete November 2026 SOTA model catalog, pricing, multimodal support matrix, and TCM task-routing recommendations.

## Provider Summary

| Provider ID | Label | Default Model | Config Key | Environment Variable(s) | Default Base URL / SDK | Native Modalities |
| --- | --- | --- | --- | --- | --- | --- |
| `anthropic` | Anthropic | `claude-sonnet-4-5-20250929` | `llm.api_key` | `ANTHROPIC_API_KEY` | Anthropic SDK default | Text, Vision, PDF, Thinking |
| `openai` | OpenAI | `gpt-4o` | `llm.openai_api_key` | `OPENAI_API_KEY` | OpenAI SDK default | Text, Vision, Audio, PDF, Thinking |
| `google` | Google (Gemini) | `gemini-2.5-flash` | `llm.google_api_key` | `GOOGLE_API_KEY` | `google-genai` SDK | Text, Vision, Audio, Video, PDF, Thinking |
| `deepseek` | DeepSeek | `deepseek-v3.2` | `llm.deepseek_api_key` | `DEEPSEEK_API_KEY` | `https://api.deepseek.com/v1` | Text, Vision, Thinking |
| `qwen` | Qwen (DashScope) | `qwen3-max` | `llm.qwen_api_key` | `DASHSCOPE_API_KEY` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | Text, Vision, PDF, Thinking |
| `kimi` | Moonshot Kimi | `kimi-k2.5` | `llm.kimi_api_key` | `MOONSHOT_API_KEY` | `https://api.moonshot.cn/v1` | Text, Vision, Thinking |
| `glm` | Zhipu GLM | `glm-5.3` | `llm.glm_api_key` | `ZHIPUAI_API_KEY` (or `GLM_API_KEY`) | `https://open.bigmodel.cn/api/paas/v4` | Text, Vision, Thinking |
| `minimax` | MiniMax | `minimax-m2.5` | `llm.minimax_api_key` | `MINIMAX_API_KEY` | `https://api.minimax.chat/v1` | Text, Vision, Audio |
| `xai` | xAI (Grok) | `grok-4.8` | `llm.xai_api_key` | `XAI_API_KEY` | `https://api.x.ai/v1` | Text, Vision, Thinking |
| `mistral` | Mistral | `mistral-large-latest` | `llm.mistral_api_key` | `MISTRAL_API_KEY` | `https://api.mistral.ai/v1` | Text, Vision |
| `groq` | Groq | `llama-3.1-70b-versatile` | `llm.groq_api_key` | `GROQ_API_KEY` | `https://api.groq.com/openai/v1` | Text |
| `cohere` | Cohere | `command-r-plus` | `llm.cohere_api_key` | `COHERE_API_KEY` | Cohere SDK | Text |
| `openrouter` | OpenRouter | `openrouter/auto` | `llm.openrouter_api_key` | `OPENROUTER_API_KEY` | `https://openrouter.ai/api/v1` | Text, Vision |
| `together` | Together AI | `together/deepseek-v4-pro` | `llm.together_api_key` | `TOGETHER_API_KEY` | `https://api.together.xyz/v1` | Text, Thinking |
| `ollama` | Ollama (Local) | `ollama/qwen3:32b` | `llm.ollama_api_key` | `OLLAMA_API_KEY` *(optional)* | `http://localhost:11434/v1` | Text, Vision, Thinking |

## Configuring API Keys & Switching Providers

```bash
# Show the status of all configured providers
tcm keys

# Configure cloud provider API keys securely
tcm keys set -p anthropic
tcm keys set -p openai
tcm keys set -p google
tcm keys set -p deepseek
tcm keys set -p qwen
tcm keys set -p glm
tcm keys set -p xai
tcm keys set -p openrouter

# Make a provider the default for new sessions
tcm keys set -p openai --make-default

# Switch the active model (provider is auto-detected from model ID or prefix)
tcm model set claude-sonnet-5-5
tcm model set gpt-6.1-sol
tcm model set gemini-3.6-flash
tcm model set qwen-vl-max
tcm model set glm-5.3
tcm model set ollama/huatuogpt-vision:7b
```

## Multimodal Capabilities Across Providers

`LLMClient.chat(..., attachments=[...])` and `LLMClient.stream(..., attachments=[...])` normalize `MediaAttachment` inputs (local files, `data:` URIs, base64 payloads, and `https://` URLs) into each provider's native wire protocol:

- **Anthropic (`anthropic`)**: Native `image` (`image/png`, `image/jpeg`, `image/webp`, `image/gif`) and `document` (`application/pdf`) content blocks, with text/transcript fallback descriptors for audio/video attachments.
- **OpenAI & OpenAI-Compatible (`openai`, `deepseek`, `qwen`, `kimi`, `glm`, `minimax`, `xai`, `mistral`, `openrouter`, `ollama`)**: Native `image_url`, `input_audio` (`wav`, `mp3`, `m4a`, `ogg`), and PDF `file` content blocks.
- **Google Gemini (`google`)**: Native `google.genai.types.Part.from_bytes` & `Part.from_uri` omni-modal ingestion for **Vision**, **Audio** (pulse/cough/auscultation recordings), **Video**, and multi-page **PDF** treatises.

## Private Local Medical Inference with Ollama

For clinics and HIPAA/privacy-sensitive research environments, `tcm` supports zero-egress local inference via Ollama (`http://localhost:11434/v1`) with no API key required:

```bash
# Pull recommended local TCM & multimodal medical models
ollama pull qwen3:32b
ollama pull medgemma:27b
ollama pull huatuogpt-vision:7b

# Point tcm to a local Ollama model (the leading "ollama/" prefix is stripped automatically on wire calls)
tcm model set ollama/huatuogpt-vision:7b

# Optional: override Ollama server endpoint if hosted on a LAN GPU workstation
tcm config set llm.ollama_base_url http://192.168.1.50:11434/v1
```

## Custom Base URLs, Profiles & Studio Settings

- **Custom Base URLs**: Override any OpenAI-compatible endpoint in `~/.tcm/config.json`:
  - `llm.deepseek_base_url`, `llm.kimi_base_url`, `llm.minimax_base_url`, `llm.qwen_base_url`
  - `llm.glm_base_url`, `llm.xai_base_url`, `llm.mistral_base_url`, `llm.groq_base_url`
  - `llm.together_base_url`, `llm.openrouter_base_url`, `llm.ollama_base_url`
- **Agent Profiles**: Choose between `research` (default), `clinical` (strictly grounded synthesis, creative hypotheses disabled), `education`, and `studio` (`tcm config set agent.profile studio`).
- **Studio Host & Port**: Configure local web studio binding via `studio.host` (default `127.0.0.1`) and `studio.port` (default `8765`).
- **Live Gemini Discovery**: Run `tcm model google` with `GOOGLE_API_KEY` set to query live `generateContent`-capable models directly from Google's API.

