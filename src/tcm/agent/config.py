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
VALID_LLM_PROVIDERS = frozenset({"anthropic", "openai"})
logger = logging.getLogger("tcm.config")

DEFAULTS = {
    "llm.provider": "anthropic",
    "llm.model": "claude-sonnet-4-5-20250929",
    "llm.api_key": None,
    "llm.openai_api_key": None,
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
    "ui.language": "en",  # "en" or "zh"

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
        self._data[key] = value

    def llm_api_key(self, provider: str = None) -> Optional[str]:
        """Get the API key for the given LLM provider."""
        provider = provider or self.get("llm.provider", "anthropic")
        if provider == "anthropic":
            return (
                self._data.get("llm.api_key")
                or os.environ.get("ANTHROPIC_API_KEY")
            )
        elif provider == "openai":
            return (
                self._data.get("llm.openai_api_key")
                or os.environ.get("OPENAI_API_KEY")
            )
        return None

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

        # Anthropic
        key = self.llm_api_key("anthropic")
        status = "[green]✓ configured[/green]" if key else "[red]✗ missing[/red]"
        table.add_row("Anthropic", status, "Primary LLM provider")

        # OpenAI
        key = self.llm_api_key("openai")
        status = "[green]✓ configured[/green]" if key else "[dim]○ optional[/dim]"
        table.add_row("OpenAI", status, "Alternative LLM provider")

        return table
