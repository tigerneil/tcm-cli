"""Tests for tcm.agent.config."""

import json
import pytest
from pathlib import Path


def test_config_defaults():
    from tcm.agent.config import Config, DEFAULTS
    cfg = Config()
    assert cfg.get("llm.provider") == "anthropic"
    assert cfg.get("llm.model") == "claude-sonnet-4-5-20250929"
    assert cfg.get("nonexistent", "fallback") == "fallback"


def test_config_set_get():
    from tcm.agent.config import Config
    cfg = Config()
    cfg.set("llm.model", "claude-opus-4-6")
    assert cfg.get("llm.model") == "claude-opus-4-6"


def test_config_invalid_provider():
    from tcm.agent.config import Config
    cfg = Config()
    with pytest.raises(ValueError, match="Invalid provider"):
        cfg.set("llm.provider", "invalid_provider")


def test_config_profile_presets():
    from tcm.agent.config import Config
    cfg = Config()
    cfg.set("agent.profile", "clinical")
    assert cfg.get("agent.allow_creative_hypotheses") is False
    assert cfg.get("agent.enforce_grounded_synthesis") is True


def test_config_invalid_profile():
    from tcm.agent.config import Config
    cfg = Config()
    with pytest.raises(ValueError, match="Unknown profile"):
        cfg.set("agent.profile", "nonexistent")


def test_config_validate_unknown_keys():
    from tcm.agent.config import Config
    cfg = Config(data={"unknown.key": "value"})
    issues = cfg.validate()
    assert any("unknown.key" in issue for issue in issues)


def test_config_validate_type_errors():
    from tcm.agent.config import Config
    cfg = Config(data={"agent.max_iterations": "not_a_number"})
    issues = cfg.validate()
    assert any("max_iterations" in issue for issue in issues)


def test_config_save_load(tmp_path, monkeypatch):
    from tcm.agent import config as config_mod
    monkeypatch.setattr(config_mod, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config_mod, "CONFIG_FILE", tmp_path / "config.json")

    from tcm.agent.config import Config
    cfg = Config(data={"llm.model": "test-model"})
    cfg.save()
    assert (tmp_path / "config.json").exists()

    loaded = Config.load()
    assert loaded.get("llm.model") == "test-model"


def test_config_api_key(monkeypatch):
    from tcm.agent.config import Config
    cfg = Config(data={"llm.api_key": "sk-ant-test123"})
    assert cfg.llm_api_key("anthropic") == "sk-ant-test123"

    # Test env var fallback
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-test")
    assert cfg.llm_api_key("openai") == "sk-openai-test"
