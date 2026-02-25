"""
Configuration management for tcm.

Config is stored at ~/.tcm/config.json and manages:
- LLM provider settings (Anthropic, OpenAI)
- Data directory paths (TCMSP, TCMID, etc.)
- Output preferences
- Agent settings
"""

import json
import os
import logging
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv

load_dotenv()

from rich.table import Table

CONFIG_DIR = Path.home() / ".tcm"
CONFIG_FILE = CONFIG_DIR / "config.json"
# Providers currently supported by the runtime LLM client
VALID_LLM_PROVIDERS = frozenset({
    "anthropic",
    "openai",
    "deepseek",
    "kimi",
    "minimax",
    "qwen",
    "google",
    "mistral",
    "groq",
    "cohere",
})
logger = logging.getLogger("tcm.config")

# Additional common providers for key storage/UX (may not be runtime-supported yet)
PROVIDER_SPECS = {
    "anthropic": {"label": "Anthropic", "config_key": "llm.api_key", "env": "ANTHROPIC_API_KEY", "primary": True},
    "openai":    {"label": "OpenAI", "config_key": "llm.openai_api_key", "env": "OPENAI_API_KEY", "primary": False},
    "google":    {"label": "Google (Gemini)", "config_key": "llm.google_api_key", "env": "GOOGLE_API_KEY", "primary": False},
    "mistral":   {"label": "Mistral", "config_key": "llm.mistral_api_key", "env": "MISTRAL_API_KEY", "primary": False},
    "groq":      {"label": "Groq", "config_key": "llm.groq_api_key", "env": "GROQ_API_KEY", "primary": False},
    "cohere":    {"label": "Cohere", "config_key": "llm.cohere_api_key", "env": "COHERE_API_KEY", "primary": False},
    "together":  {"label": "Together AI", "config_key": "llm.together_api_key", "env": "TOGETHER_API_KEY", "primary": False},
    "ollama":    {"label": "Ollama (local)", "config_key": "llm.ollama_api_key", "env": None, "primary": False},  # typically not needed
    # Newly added providers
    "deepseek":  {"label": "DeepSeek", "config_key": "llm.deepseek_api_key", "env": "DEEPSEEK_API_KEY", "primary": False},
    "kimi":      {"label": "Moonshot Kimi", "config_key": "llm.kimi_api_key", "env": "MOONSHOT_API_KEY", "primary": False},
    "minimax":   {"label": "MiniMax", "config_key": "llm.minimax_api_key", "env": "MINIMAX_API_KEY", "primary": False},
    "qwen":      {"label": "Qwen (DashScope)", "config_key": "llm.qwen_api_key", "env": "DASHSCOPE_API_KEY", "primary": False},
}

DEFAULTS = {
    "llm.provider": "anthropic",
    "llm.model": "claude-sonnet-4-5-20250929",
    # Provider API keys
    "llm.api_key": None,               # Anthropic (historical default)
    "llm.openai_api_key": None,
    "llm.google_api_key": None,
    "llm.mistral_api_key": None,
    "llm.groq_api_key": None,
    "llm.cohere_api_key": None,
    "llm.together_api_key": None,
    "llm.ollama_api_key": None,
    "llm.deepseek_api_key": None,
    "llm.kimi_api_key": None,
    "llm.minimax_api_key": None,
    "llm.qwen_api_key": None,
    # Provider base URLs (overridable)
    "llm.deepseek_base_url": "https://api.deepseek.com/v1",
    "llm.kimi_base_url": "https://api.moonshot.cn/v1",
    "llm.minimax_base_url": "https://api.minimax.chat/v1",
    "llm.qwen_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "llm.mistral_base_url": "https://api.mistral.ai/v1",
    "llm.groq_base_url": "https://api.groq.com/openai/v1",

    # Model parameters
    "llm.temperature": 0.1,

    "data.base": str(CONFIG_DIR / "data"),
    "data.tcmsp": None,
    "data.tcmid": None,
    "data.herbs": None,
    "data.formulas": None,
    "data.batman": None,
    "data.symmap": None,

    "output.format": "markdown",
    "output.verbose": False,
    "output.auto_publish_html_interactive": True,
    "output.auto_publish_html_batch": False,

    "ui.spinner": "dots",
    "ui.language": "en",  # "en" (English), "zh" (中文), or "bi" (bilingual)

    "sandbox.timeout": 30,
    "sandbox.output_dir": str(Path.cwd() / "outputs"),
    "sandbox.max_retries": 2,

    "agent.max_iterations": 3,
    "agent.enable_experimental_tools": False,
    "agent.executor_max_retries": 2,
    "agent.executor_loop_limit": 50,
    "agent.synthesis_max_tokens": 8192,
    "agent.enforce_grounded_synthesis": True,
    "agent.confidence_scoring_enabled": True,
    "agent.min_step_success_rate": 0.5,
    "agent.allow_creative_hypotheses": True,
    "agent.max_hypotheses": 3,
    "agent.profile": "research",
    "agent.planner_max_tools": 60,
    "agent.tool_health_enabled": True,
    "agent.tool_health_fail_threshold": 2,
    "agent.tool_health_failure_window_s": 1800,
    "agent.tool_health_suppress_seconds": 900,
}

AGENT_PROFILE_PRESETS = {
    "research": {
        "agent.enforce_grounded_synthesis": True,
        "agent.allow_creative_hypotheses": True,
        "agent.confidence_scoring_enabled": True,
    },
    "clinical": {
        "agent.enforce_grounded_synthesis": True,
        "agent.allow_creative_hypotheses": False,
        "agent.confidence_scoring_enabled": True,
    },
    "education": {
        "agent.enforce_grounded_synthesis": False,
        "agent.allow_creative_hypotheses": True,
        "agent.confidence_scoring_enabled": False,
    },
}


class Config:
    """Manages tcm configuration."""

    def __init__(self, data: dict = None):
        self._data = data or {}

    @classmethod
    def load(cls) -> "Config":
        """Load config from ~/.tcm/config.json, falling back to defaults."""
        if CONFIG_FILE.exists():
            try:
                raw = json.loads(CONFIG_FILE.read_text())
                return cls(data=raw)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Failed to load config: %s", exc)
        return cls()

    def save(self):
        """Persist config to ~/.tcm/config.json."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(self._data, indent=2) + "\n")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value, falling back to DEFAULTS then the provided default."""
        if key in self._data:
            return self._data[key]
        if key in DEFAULTS:
            return DEFAULTS[key]
        return default

    def set(self, key: str, value: Any):
        """Set a config value.

        Special handling:
        - llm.provider: validates against known providers.
        - llm.model: auto-detects and sets the matching provider.
        - agent.profile: applies profile presets.
        """
        if key == "llm.provider" and value not in VALID_LLM_PROVIDERS:
            raise ValueError(
                f"Invalid provider '{value}'. Valid: {', '.join(sorted(VALID_LLM_PROVIDERS))}"
            )
        if key == "llm.model":
            from tcm.models.llm import resolve_provider, MODEL_CATALOG
            provider = resolve_provider(value)
            if provider:
                self._data["llm.provider"] = provider
            if value not in MODEL_CATALOG:
                logger.warning(
                    "Model '%s' is not in the catalog — it may still work if your provider supports it.",
                    value,
                )
        if key == "agent.profile":
            preset = AGENT_PROFILE_PRESETS.get(value)
            if not preset:
                raise ValueError(
                    f"Unknown profile '{value}'. "
                    f"Valid: {', '.join(sorted(AGENT_PROFILE_PRESETS))}"
                )
            for pk, pv in preset.items():
                self._data[pk] = pv
        if key == "ui.language":
            norm = str(value).strip().lower()
            if norm not in {"en", "zh", "bi"}:
                raise ValueError("ui.language must be one of: en, zh, bi")
            value = norm
        self._data[key] = value

    def set_llm_api_key(self, provider: str, api_key: Optional[str]):
        """Set API key for a specific provider, normalizing provider names.

        If the provider is unknown (not in PROVIDER_SPECS), raises ValueError.
        """
        if not provider:
            raise ValueError("Provider is required")
        prov = provider.lower().strip()
        spec = PROVIDER_SPECS.get(prov)
        if not spec:
            raise ValueError(
                f"Unknown provider '{provider}'. Known: {', '.join(sorted(PROVIDER_SPECS))}"
            )
        cfg_key = spec["config_key"]
        self._data[cfg_key] = api_key

    def llm_api_key(self, provider: str = None) -> Optional[str]:
        """Get the API key for the given LLM provider.

        Looks up provider-specific config key first, then environment fallback per PROVIDER_SPECS.
        """
        provider = (provider or self.get("llm.provider", "anthropic")).lower()
        spec = PROVIDER_SPECS.get(provider)
        if not spec:
            return None
        cfg_key = spec["config_key"]
        env = spec.get("env")
        return self._data.get(cfg_key) or (os.environ.get(env) if env else None)

    def validate(self) -> list[str]:
        """Validate configuration and return a list of issues."""
        issues = []
        known_keys = set(DEFAULTS.keys())
        for key in self._data:
            if key not in known_keys:
                issues.append(f"Unknown config key '{key}' (possible typo)")
        # Type checks
        for key, value in self._data.items():
            if key not in DEFAULTS or value is None:
                continue
            default = DEFAULTS[key]
            if default is None:
                continue
            expected_type = type(default)
            if expected_type == bool and not isinstance(value, bool):
                issues.append(f"'{key}' should be bool, got {type(value).__name__}")
            elif expected_type in (int, float) and not isinstance(value, (int, float)):
                issues.append(f"'{key}' should be numeric, got {type(value).__name__}")
        return issues

    def to_table(self) -> Table:
        """Render config as a Rich table."""
        table = Table(title="tcm Configuration")
        table.add_column("Key", style="cyan")
        table.add_column("Value")
        table.add_column("Source", style="dim")

        for key in sorted(DEFAULTS):
            if key.endswith("api_key"):
                val = self.get(key)
                if val:
                    val = val[:7] + "..." + val[-4:] if len(val) > 11 else "***"
                else:
                    val = "(not set)"
                source = "config" if key in self._data else "default"
            else:
                val = str(self.get(key))
                source = "config" if key in self._data else "default"
            table.add_row(key, val, source)
        return table

    def keys_table(self) -> Table:
        """Show API key status table."""
        table = Table(title="API Keys")
        table.add_column("Service", style="cyan")
        table.add_column("Status")
        table.add_column("Description")

        # Show primary providers first, then the rest alphabetically
        def sort_key(item):
            name, spec = item
            return (0 if spec.get("primary") else 1, name)

        for name, spec in sorted(PROVIDER_SPECS.items(), key=sort_key):
            label = spec.get("label", name.title())
            key = self.llm_api_key(name)
            if spec.get("primary"):
                desc = "Primary LLM provider"
                status = "[green]✓ configured[/green]" if key else "[red]✗ missing[/red]"
            else:
                desc = "Additional provider (optional)"
                status = "[green]✓ configured[/green]" if key else "[dim]○ optional[/dim]"

            # Special-case providers that usually don't need keys
            if name == "ollama":
                desc = "Local runtime (no key typically required)"
                status = "[green]✓ available[/green]" if key else "[dim]○ n/a[/dim]"

            table.add_row(label, status, desc)

        return table
