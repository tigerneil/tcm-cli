# Providers and API Keys

This project supports multiple LLM providers. You only need ONE provider to use `tcm`, but you can configure several and switch at any time.

## Provider summary

| Provider | Default model in tcm | Config key for API key | Environment variable | Default base URL |
| --- | --- | --- | --- | --- |
| Anthropic | `claude-sonnet-4-5-20250929` | `llm.api_key` | `ANTHROPIC_API_KEY` | (Anthropic SDK default) |
| OpenAI | `gpt-4o` | `llm.openai_api_key` | `OPENAI_API_KEY` | (OpenAI default) |
| DeepSeek | `deepseek-v3.2` | `llm.deepseek_api_key` | `DEEPSEEK_API_KEY` | `https://api.deepseek.com/v1` |
| Kimi (Moonshot) | `kimi-k2.5` | `llm.kimi_api_key` | `MOONSHOT_API_KEY` | `https://api.moonshot.cn/v1` |
| MiniMax | `minimax-m2.5` | `llm.minimax_api_key` | `MINIMAX_API_KEY` | `https://api.minimax.chat/v1` |
| Qwen (DashScope) | `qwen3-max` | `llm.qwen_api_key` | `DASHSCOPE_API_KEY` | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| Google (Gemini) | `gemini-1.5-pro` | `llm.google_api_key` | `GOOGLE_API_KEY` | (Gemini SDK) |
| Mistral | `mistral-large-latest` | `llm.mistral_api_key` | `MISTRAL_API_KEY` | `https://api.mistral.ai/v1` |
| Groq | `llama-3.1-70b-versatile` | `llm.groq_api_key` | `GROQ_API_KEY` | `https://api.groq.com/openai/v1` |
| Cohere | `command-r-plus` | `llm.cohere_api_key` | `COHERE_API_KEY` | (Cohere SDK) |

Note: Together and Ollama keys can be stored via `tcm keys`, though they may not be active runtime providers yet.

## Commands

```bash
# Show the status of all providers
tcm keys

# Set a provider key (prompts securely)
tcm keys set -p openai

tcm keys set -p kimi

tcm keys set -p deepseek

# Make a provider default for new sessions (optional)
tcm keys set -p openai --make-default

# Switch the active model (provider is auto-detected)
tcm model set gpt-4o

tcm model set kimi-k2.5
```

## Tips

- If a provider uses an OpenAI-compatible API, `tcm` will set the appropriate base URL automatically.
- You can override base URLs in config (e.g., `llm.deepseek_base_url`).
- For CI, set environment variables and avoid interactive prompts.
