"""
Unified LLM client: supports Anthropic and OpenAI.

Provides a consistent interface regardless of backend.
"""

from dataclasses import dataclass, field
from typing import Optional, Generator
import logging
import os
import time

logger = logging.getLogger("tcm.llm")


@dataclass
class LLMResponse:
    """Standardized response from any LLM backend."""
    content: str
    model: str
    usage: dict = None
    raw: object = None
    content_blocks: list = None


# ─── Model catalog ────────────────────────────────────────────

@dataclass
class ModelInfo:
    """Metadata for a supported LLM model."""
    id: str
    provider: str
    display_name: str
    context_window: int
    input_price: float   # USD per million tokens
    output_price: float  # USD per million tokens
    description: str = ""


MODEL_CATALOG: dict[str, ModelInfo] = {}


def _register(*models: ModelInfo):
    for m in models:
        MODEL_CATALOG[m.id] = m


_register(
    # ── Anthropic ──────────────────────────────────────────
    ModelInfo(
        id="claude-sonnet-4-5-20250929",
        provider="anthropic",
        display_name="Claude Sonnet 4.5",
        context_window=200_000,
        input_price=3.00,
        output_price=15.00,
        description="Best balance of speed and intelligence",
    ),
    ModelInfo(
        id="claude-haiku-4-5-20251001",
        provider="anthropic",
        display_name="Claude Haiku 4.5",
        context_window=200_000,
        input_price=0.80,
        output_price=4.00,
        description="Fastest and most affordable",
    ),
    ModelInfo(
        id="claude-opus-4-6",
        provider="anthropic",
        display_name="Claude Opus 4.6",
        context_window=200_000,
        input_price=15.00,
        output_price=75.00,
        description="Most capable for complex research",
    ),
    # ── OpenAI ─────────────────────────────────────────────
    ModelInfo(
        id="gpt-4o",
        provider="openai",
        display_name="GPT-4o",
        context_window=128_000,
        input_price=2.50,
        output_price=10.00,
        description="High-intelligence flagship model",
    ),
    ModelInfo(
        id="gpt-4o-mini",
        provider="openai",
        display_name="GPT-4o Mini",
        context_window=128_000,
        input_price=0.15,
        output_price=0.60,
        description="Fast and affordable small model",
    ),
    ModelInfo(
        id="o3-mini",
        provider="openai",
        display_name="o3-mini",
        context_window=200_000,
        input_price=1.10,
        output_price=4.40,
        description="Reasoning model, good for analysis",
    ),
    ModelInfo(
        id="gpt-4.1",
        provider="openai",
        display_name="GPT-4.1",
        context_window=1_047_576,
        input_price=2.00,
        output_price=8.00,
        description="Latest flagship with 1M context",
    ),
    ModelInfo(
        id="gpt-4.1-mini",
        provider="openai",
        display_name="GPT-4.1 Mini",
        context_window=1_047_576,
        input_price=0.40,
        output_price=1.60,
        description="Balanced speed and intelligence",
    ),
    ModelInfo(
        id="gpt-4.1-nano",
        provider="openai",
        display_name="GPT-4.1 Nano",
        context_window=1_047_576,
        input_price=0.10,
        output_price=0.40,
        description="Fastest, most cost-effective",
    ),
    # ── DeepSeek ───────────────────────────────────────────
    ModelInfo(
        id="deepseek-v3.2",
        provider="deepseek",
        display_name="DeepSeek V3.2",
        context_window=128_000,
        input_price=0.00,
        output_price=0.00,
        description="Latest general model",
    ),
    ModelInfo(
        id="deepseek-r1",
        provider="deepseek",
        display_name="DeepSeek R1",
        context_window=128_000,
        input_price=0.00,
        output_price=0.00,
        description="Reasoning model",
    ),
    # ── Moonshot Kimi ──────────────────────────────────────
    ModelInfo(
        id="kimi-k2.5",
        provider="kimi",
        display_name="Kimi K2.5",
        context_window=200_000,
        input_price=0.00,
        output_price=0.00,
        description="Flagship Kimi model",
    ),
    # ── MiniMax ────────────────────────────────────────────
    ModelInfo(
        id="minimax-m2.5",
        provider="minimax",
        display_name="MiniMax M2.5",
        context_window=200_000,
        input_price=0.00,
        output_price=0.00,
        description="Flagship MiniMax model",
    ),
    # ── Qwen (DashScope) ───────────────────────────────────
    ModelInfo(
        id="qwen3-max",
        provider="qwen",
        display_name="Qwen3-Max",
        context_window=1_000_000,
        input_price=0.00,
        output_price=0.00,
        description="Flagship Qwen model",
    ),
    ModelInfo(
        id="qwen-plus",
        provider="qwen",
        display_name="Qwen-Plus",
        context_window=200_000,
        input_price=0.00,
        output_price=0.00,
        description="Balanced speed/cost",
    ),
    # ── Google (Gemini) ─────────────────────────────────────
    # Stable production models
    ModelInfo(
        id="gemini-2.5-pro",
        provider="google",
        display_name="Gemini 2.5 Pro",
        context_window=1_048_576,
        input_price=1.25,
        output_price=10.00,
        description="Most capable Gemini, best for complex reasoning",
    ),
    ModelInfo(
        id="gemini-2.5-flash",
        provider="google",
        display_name="Gemini 2.5 Flash",
        context_window=1_048_576,
        input_price=0.15,
        output_price=0.60,
        description="Fast mid-size multimodal model",
    ),
    ModelInfo(
        id="gemini-2.5-flash-lite",
        provider="google",
        display_name="Gemini 2.5 Flash-Lite",
        context_window=1_048_576,
        input_price=0.075,
        output_price=0.30,
        description="Cost-efficient Gemini 2.5 model",
    ),
    ModelInfo(
        id="gemini-2.0-flash",
        provider="google",
        display_name="Gemini 2.0 Flash",
        context_window=1_048_576,
        input_price=0.10,
        output_price=0.40,
        description="Fast, versatile next-gen multimodal model",
    ),
    ModelInfo(
        id="gemini-2.0-flash-lite",
        provider="google",
        display_name="Gemini 2.0 Flash-Lite",
        context_window=1_048_576,
        input_price=0.075,
        output_price=0.30,
        description="Most cost-efficient Gemini 2.0 model",
    ),
    # Preview / frontier models
    ModelInfo(
        id="gemini-3.1-pro-preview",
        provider="google",
        display_name="Gemini 3.1 Pro Preview",
        context_window=1_048_576,
        input_price=0.00,
        output_price=0.00,
        description="Frontier Gemini 3.1 Pro, early access",
    ),
    ModelInfo(
        id="gemini-3-pro-preview",
        provider="google",
        display_name="Gemini 3 Pro Preview",
        context_window=1_048_576,
        input_price=0.00,
        output_price=0.00,
        description="Frontier Gemini 3 Pro, early access",
    ),
    ModelInfo(
        id="gemini-3-flash-preview",
        provider="google",
        display_name="Gemini 3 Flash Preview",
        context_window=1_048_576,
        input_price=0.00,
        output_price=0.00,
        description="Frontier Gemini 3 Flash, early access",
    ),
    # Convenience aliases (always point to latest stable)
    ModelInfo(
        id="gemini-pro-latest",
        provider="google",
        display_name="Gemini Pro Latest",
        context_window=1_048_576,
        input_price=0.00,
        output_price=0.00,
        description="Alias to latest stable Gemini Pro",
    ),
    ModelInfo(
        id="gemini-flash-latest",
        provider="google",
        display_name="Gemini Flash Latest",
        context_window=1_048_576,
        input_price=0.00,
        output_price=0.00,
        description="Alias to latest stable Gemini Flash",
    ),
)

# Provider prefix patterns for auto-detection of unknown models
_PROVIDER_PREFIXES = [
    ("claude-", "anthropic"),
    ("gpt-", "openai"),
    ("o1-", "openai"),
    ("o3-", "openai"),
    ("o4-", "openai"),
    ("deepseek-", "deepseek"),
    ("kimi-", "kimi"),
    ("minimax", "minimax"),
    ("qwen", "qwen"),
    ("gemini-", "google"),
]


def resolve_provider(model: str) -> Optional[str]:
    """Resolve the provider for a model name.

    Returns the provider string, or None if unrecognizable.
    Checks the catalog first, then falls back to prefix matching.
    """
    info = MODEL_CATALOG.get(model)
    if info:
        return info.provider
    model_lower = model.lower()
    for prefix, provider in _PROVIDER_PREFIXES:
        if model_lower.startswith(prefix):
            return provider
    return None


def list_models(provider: str = None) -> list[ModelInfo]:
    """List models from the catalog, optionally filtered by provider."""
    models = list(MODEL_CATALOG.values())
    if provider:
        models = [m for m in models if m.provider == provider]
    return models


def list_google_models(api_key: str = None) -> list[dict]:
    """Query the Google Gemini API for all available models that support generateContent.

    Returns a list of dicts: {name, display_name, context_window, methods}.
    Requires a valid GOOGLE_API_KEY.
    """
    import os
    from google import genai as genai_sdk
    key = api_key or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise ValueError(
            "Google API key not configured. Run: tcm keys set -p google"
            " or export GOOGLE_API_KEY=..."
        )
    client = genai_sdk.Client(api_key=key)
    result = []
    for m in client.models.list():
        name = getattr(m, "name", "") or ""
        methods = list(getattr(m, "supported_actions", None) or [])
        # Prefer short id without "models/" prefix
        short_id = name.replace("models/", "")
        result.append({
            "id": short_id,
            "name": name,
            "display_name": getattr(m, "display_name", short_id),
            "description": getattr(m, "description", ""),
            "input_token_limit": getattr(m, "input_token_limit", None),
            "output_token_limit": getattr(m, "output_token_limit", None),
            "methods": methods,
        })
    # Sort: generateContent-capable first, then alpha
    result.sort(key=lambda x: ("generateContent" not in str(x["methods"]), x["id"]))
    return result


def model_pricing(model: str) -> Optional[dict]:
    """Get pricing info for a model. Returns {input, output} or None."""
    info = MODEL_CATALOG.get(model)
    if info:
        return {"input": info.input_price, "output": info.output_price}
    return None


@dataclass
class UsageTracker:
    """Tracks cumulative token usage and cost across LLM calls."""
    calls: list = field(default_factory=list)

    @property
    def total_input_tokens(self) -> int:
        return sum(c.get("input", 0) for c in self.calls)

    @property
    def total_output_tokens(self) -> int:
        return sum(c.get("output", 0) for c in self.calls)

    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens

    @property
    def total_cost(self) -> float:
        return sum(c.get("cost", 0.0) for c in self.calls)

    def record(self, model: str, usage: dict):
        """Record a single LLM call's usage."""
        if not usage:
            return
        cost = self._estimate_cost(model, usage)
        self.calls.append({
            "model": model,
            "input": usage.get("input", 0),
            "output": usage.get("output", 0),
            "cost": cost,
        })

    def _estimate_cost(self, model: str, usage: dict) -> float:
        pricing = model_pricing(model)
        if not pricing:
            return 0.0
        input_cost = (usage.get("input", 0) / 1_000_000) * pricing["input"]
        output_cost = (usage.get("output", 0) / 1_000_000) * pricing["output"]
        return input_cost + output_cost

    def summary(self) -> str:
        """Human-readable usage summary."""
        if not self.calls:
            return "No LLM calls made."
        models_used = set(c["model"] for c in self.calls)
        return (
            f"{len(self.calls)} LLM calls | "
            f"{self.total_input_tokens:,} in + {self.total_output_tokens:,} out tokens | "
            f"${self.total_cost:.4f} | "
            f"models: {', '.join(models_used)}"
        )

    def reset(self):
        self.calls.clear()


class LLMClient:
    """Unified LLM client supporting multiple providers."""

    DEFAULT_MODELS = {
        "anthropic": "claude-sonnet-4-5-20250929",
        "openai": "gpt-4o",
        "deepseek": "deepseek-v3.2",
        "kimi": "kimi-k2.5",
        "minimax": "minimax-m2.5",
        "qwen": "qwen3-max",
        "google": "gemini-2.5-flash",
        "mistral": "mistral-large-latest",
        "groq": "llama-3.1-70b-versatile",
        "cohere": "command-r-plus",
    }

    def __init__(self, provider: str = "anthropic", model: str = None,
                 api_key: str = None, base_url: str | None = None):
        self.provider = provider
        self.model = model or self.DEFAULT_MODELS.get(provider)
        self.api_key = api_key
        self.base_url = base_url
        self._client = None
        self.usage = UsageTracker()

    def _get_client(self):
        """Lazily initialize the appropriate client."""
        if self._client is not None:
            return self._client

        if self.provider == "anthropic":
            import anthropic
            self._client = anthropic.Anthropic(
                api_key=self.api_key or os.environ.get("ANTHROPIC_API_KEY")
            )
        elif self.provider in {"openai", "deepseek", "kimi", "minimax", "qwen", "mistral", "groq"}:
            import openai
            # Determine key/env by provider; openai lib allows base_url override for compatible backends
            key = self.api_key
            if not key:
                env_fallbacks = {
                    "openai": "OPENAI_API_KEY",
                    "deepseek": "DEEPSEEK_API_KEY",
                    "kimi": "MOONSHOT_API_KEY",
                    "minimax": "MINIMAX_API_KEY",
                    "qwen": "DASHSCOPE_API_KEY",
                    "mistral": "MISTRAL_API_KEY",
                    "groq": "GROQ_API_KEY",
                }
                key = os.environ.get(env_fallbacks.get(self.provider, "OPENAI_API_KEY"))
            # Pick base_url if provided, else sensible defaults for compatibles
            base_urls = {
                "openai": None,
                "deepseek": "https://api.deepseek.com/v1",
                "kimi": "https://api.moonshot.cn/v1",
                "minimax": "https://api.minimax.chat/v1",
                "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "mistral": "https://api.mistral.ai/v1",
                "groq": "https://api.groq.com/openai/v1",
            }
            base_url = self.base_url if self.base_url is not None else base_urls.get(self.provider)
            if base_url:
                self._client = openai.OpenAI(api_key=key, base_url=base_url)
            else:
                self._client = openai.OpenAI(api_key=key)
        elif self.provider == "google":
            from google import genai as genai_sdk
            key = self.api_key or os.environ.get("GOOGLE_API_KEY")
            self._client = genai_sdk.Client(api_key=key)
        elif self.provider == "cohere":
            import cohere
            key = self.api_key or os.environ.get("COHERE_API_KEY")
            self._client = cohere.Client(api_key=key)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

        return self._client

    def chat(self, system: str, messages: list[dict], temperature: float = 0.1,
             max_tokens: int = 4096, tools: list[dict] | None = None) -> LLMResponse:
        """Send a chat completion request."""
        client = self._get_client()

        if self.provider == "anthropic":
            resp = self._chat_anthropic(client, system, messages, temperature, max_tokens, tools)
        elif self.provider in {"openai", "deepseek", "kimi", "minimax", "qwen", "mistral", "groq"}:
            resp = self._chat_openai(client, system, messages, temperature, max_tokens)
        elif self.provider == "google":
            resp = self._chat_google(client, system, messages, temperature, max_tokens)
        elif self.provider == "cohere":
            resp = self._chat_cohere(client, system, messages, temperature, max_tokens)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

        if resp.usage:
            self.usage.record(resp.model, resp.usage)

        return resp

    def stream(self, system: str, messages: list[dict], temperature: float = 0.1,
               max_tokens: int = 4096) -> Generator[str, None, None]:
        """Stream a chat completion, yielding text chunks."""
        client = self._get_client()

        if self.provider == "anthropic":
            yield from self._stream_anthropic(client, system, messages, temperature, max_tokens)
        elif self.provider in {"openai", "deepseek", "kimi", "minimax", "qwen", "mistral", "groq"}:
            yield from self._stream_openai(client, system, messages, temperature, max_tokens)
        elif self.provider == "google":
            yield from self._stream_google(client, system, messages, temperature, max_tokens)
        elif self.provider == "cohere":
            resp = self.chat(system, messages, temperature, max_tokens)
            yield resp.content
        else:
            resp = self.chat(system, messages, temperature, max_tokens)
            yield resp.content

    def _retry(self, fn, max_retries: int = 3, base_delay: float = 2.0):
        """Retry with exponential backoff on transient errors."""
        for attempt in range(1, max_retries + 1):
            try:
                return fn()
            except Exception as e:
                err_str = str(e).lower()
                is_transient = any(w in err_str for w in (
                    "rate_limit", "rate limit", "429", "overloaded",
                    "529", "500", "502", "503", "connection", "timeout",
                ))
                if is_transient and attempt < max_retries:
                    delay = base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        "LLM call failed (attempt %d/%d): %s — retrying in %.1fs",
                        attempt, max_retries, e, delay,
                    )
                    time.sleep(delay)
                else:
                    raise

    def _chat_anthropic(self, client, system, messages, temperature, max_tokens, tools=None):
        return self._retry(
            lambda: self._call_anthropic(client, system, messages, temperature, max_tokens, tools)
        )

    def _call_anthropic(self, client, system, messages, temperature, max_tokens, tools=None):
        kwargs = dict(
            model=self.model,
            system=system,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if tools:
            kwargs["tools"] = tools
        response = client.messages.create(**kwargs)
        if not response.content:
            content_text = ""
        else:
            text_parts = [b.text for b in response.content if hasattr(b, "text")]
            content_text = "\n".join(text_parts) if text_parts else ""
        return LLMResponse(
            content=content_text,
            model=self.model,
            usage={"input": response.usage.input_tokens, "output": response.usage.output_tokens},
            raw=response,
            content_blocks=list(response.content) if response.content else [],
        )

    def _stream_anthropic(self, client, system, messages, temperature, max_tokens):
        """Stream from Anthropic API, yielding text deltas."""
        with client.messages.stream(
            model=self.model,
            system=system,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        ) as stream:
            try:
                for text in stream.text_stream:
                    yield text
            finally:
                try:
                    response = stream.get_final_message()
                    usage = {
                        "input": response.usage.input_tokens,
                        "output": response.usage.output_tokens,
                    }
                    self.usage.record(self.model, usage)
                except Exception:
                    pass

    def _chat_openai(self, client, system, messages, temperature, max_tokens):
        return self._retry(
            lambda: self._call_openai(client, system, messages, temperature, max_tokens)
        )

    def _chat_google(self, client, system, messages, temperature, max_tokens):
        return self._retry(
            lambda: self._call_google(client, system, messages, temperature, max_tokens)
        )

    def _call_google(self, client, system, messages, temperature, max_tokens):
        from google.genai import types as genai_types
        # Build contents list
        contents = []
        if system:
            contents.append(genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=f"[System instructions]\n{system}")],
            ))
            contents.append(genai_types.Content(
                role="model",
                parts=[genai_types.Part(text="Understood. I will follow those instructions.")],
            ))
        for m in messages:
            role = m.get("role", "user")
            api_role = "model" if role == "assistant" else "user"
            contents.append(genai_types.Content(
                role=api_role,
                parts=[genai_types.Part(text=m.get("content", ""))],
            ))
        config = genai_types.GenerateContentConfig(
            temperature=float(temperature),
            max_output_tokens=int(max_tokens),
        )
        response = client.models.generate_content(
            model=self.model,
            contents=contents,
            config=config,
        )
        text = response.text or ""
        usage = None
        meta = getattr(response, "usage_metadata", None)
        if meta:
            usage = {
                "input": getattr(meta, "prompt_token_count", 0),
                "output": getattr(meta, "candidates_token_count", 0),
            }
        return LLMResponse(content=text, model=self.model, usage=usage, raw=response)

    def _stream_google(self, client, system, messages, temperature, max_tokens):
        from google.genai import types as genai_types
        contents = []
        if system:
            contents.append(genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=f"[System instructions]\n{system}")],
            ))
            contents.append(genai_types.Content(
                role="model",
                parts=[genai_types.Part(text="Understood. I will follow those instructions.")],
            ))
        for m in messages:
            role = m.get("role", "user")
            api_role = "model" if role == "assistant" else "user"
            contents.append(genai_types.Content(
                role=api_role,
                parts=[genai_types.Part(text=m.get("content", ""))],
            ))
        config = genai_types.GenerateContentConfig(
            temperature=float(temperature),
            max_output_tokens=int(max_tokens),
        )
        for chunk in client.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=config,
        ):
            txt = chunk.text
            if txt:
                yield txt

    def _chat_cohere(self, client, system, messages, temperature, max_tokens):
        return self._retry(
            lambda: self._call_cohere(client, system, messages, temperature, max_tokens)
        )

    def _call_cohere(self, client, system, messages, temperature, max_tokens):
        parts = [f"[system]\n{system}"] if system else []
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            parts.append(f"[{role}]\n{content}")
        prompt = "\n\n".join(parts)
        resp = client.chat(
            model=self.model,
            message=prompt,
            temperature=float(temperature),
            max_tokens=int(max_tokens),
        )
        text = getattr(resp, "text", None) or getattr(resp, "message", None) or ""
        usage = None
        try:
            tok = getattr(resp, "meta", {}).get("billed_units", {})
            usage = {"input": tok.get("input_tokens", 0), "output": tok.get("output_tokens", 0)}
        except Exception:
            pass
        return LLMResponse(content=text, model=self.model, usage=usage, raw=resp)

    def _call_openai(self, client, system, messages, temperature, max_tokens):
        # Normalize temperature for OpenAI-compatible providers
        # Kimi (Moonshot) only accepts temperature=1 for some models
        if self.provider == "kimi":
            temperature = 1.0
        oai_messages = [{"role": "system", "content": system}] + messages
        response = client.chat.completions.create(
            model=self.model,
            messages=oai_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        choice = response.choices[0]
        usage_data = {}
        if response.usage:
            usage_data = {
                "input": response.usage.prompt_tokens,
                "output": response.usage.completion_tokens,
            }
        return LLMResponse(
            content=(getattr(choice, "message", None) and (choice.message.content or "")) or "",
            model=self.model,
            usage=usage_data,
            raw=response,
        )

    def _stream_openai(self, client, system, messages, temperature, max_tokens):
        """Stream from OpenAI-compatible APIs, yielding text deltas."""
        # Normalize temperature for OpenAI-compatible providers
        if self.provider == "kimi":
            temperature = 1.0
        oai_messages = [{"role": "system", "content": system}] + messages
        stream = client.chat.completions.create(
            model=self.model,
            messages=oai_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            try:
                if getattr(chunk, "choices", None) and chunk.choices:
                    delta = getattr(chunk.choices[0], "delta", None)
                    if delta and getattr(delta, "content", None):
                        yield delta.content
            except Exception:
                continue
