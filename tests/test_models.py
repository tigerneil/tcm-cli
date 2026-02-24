"""Tests for model catalog and provider resolution."""

from tcm.models.llm import (
    MODEL_CATALOG,
    ModelInfo,
    list_models,
    model_pricing,
    resolve_provider,
)


class TestModelCatalog:
    def test_catalog_not_empty(self):
        assert len(MODEL_CATALOG) >= 9

    def test_all_entries_are_model_info(self):
        for model_id, info in MODEL_CATALOG.items():
            assert isinstance(info, ModelInfo)
            assert info.id == model_id

    def test_has_anthropic_models(self):
        anthropic = [m for m in MODEL_CATALOG.values() if m.provider == "anthropic"]
        assert len(anthropic) >= 3

    def test_has_openai_models(self):
        openai = [m for m in MODEL_CATALOG.values() if m.provider == "openai"]
        assert len(openai) >= 6


class TestResolveProvider:
    def test_known_anthropic_model(self):
        assert resolve_provider("claude-sonnet-4-5-20250929") == "anthropic"

    def test_known_openai_model(self):
        assert resolve_provider("gpt-4o") == "openai"

    def test_prefix_anthropic(self):
        assert resolve_provider("claude-future-model") == "anthropic"

    def test_prefix_openai_gpt(self):
        assert resolve_provider("gpt-5-turbo") == "openai"

    def test_prefix_openai_o3(self):
        assert resolve_provider("o3-large") == "openai"

    def test_unknown_model(self):
        assert resolve_provider("llama-3.1-70b") is None

    def test_empty_string(self):
        assert resolve_provider("") is None


class TestListModels:
    def test_list_all(self):
        models = list_models()
        assert len(models) >= 9

    def test_filter_anthropic(self):
        models = list_models(provider="anthropic")
        assert all(m.provider == "anthropic" for m in models)
        assert len(models) >= 3

    def test_filter_openai(self):
        models = list_models(provider="openai")
        assert all(m.provider == "openai" for m in models)
        assert len(models) >= 6

    def test_filter_unknown(self):
        assert list_models(provider="llama") == []


class TestModelPricing:
    def test_known_model(self):
        p = model_pricing("gpt-4o")
        assert p is not None
        assert "input" in p
        assert "output" in p
        assert p["input"] > 0
        assert p["output"] > 0

    def test_unknown_model(self):
        assert model_pricing("nonexistent-model") is None


class TestConfigAutoDetect:
    def test_set_openai_model_auto_sets_provider(self):
        from tcm.agent.config import Config

        cfg = Config()
        cfg.set("llm.model", "gpt-4o")
        assert cfg.get("llm.provider") == "openai"

    def test_set_anthropic_model_auto_sets_provider(self):
        from tcm.agent.config import Config

        cfg = Config()
        cfg.set("llm.model", "claude-sonnet-4-5-20250929")
        assert cfg.get("llm.provider") == "anthropic"

    def test_set_unknown_model_keeps_provider(self):
        from tcm.agent.config import Config

        cfg = Config({"llm.provider": "anthropic"})
        cfg.set("llm.model", "some-random-model")
        # Provider unchanged since model can't be resolved
        assert cfg.get("llm.provider") == "anthropic"

    def test_switch_provider_via_model(self):
        from tcm.agent.config import Config

        cfg = Config()
        cfg.set("llm.model", "claude-opus-4-6")
        assert cfg.get("llm.provider") == "anthropic"
        cfg.set("llm.model", "gpt-4.1")
        assert cfg.get("llm.provider") == "openai"
