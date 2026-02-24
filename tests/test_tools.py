"""Tests for tcm tools."""

import pytest


@pytest.fixture(autouse=True)
def _load_tools():
    from tcm.tools import ensure_loaded
    ensure_loaded()


class TestHerbs:
    def test_lookup_by_chinese(self):
        from tcm.tools.herbs import herbs_lookup
        result = herbs_lookup("人参")
        assert result["status"] == "found"
        assert result["herb"]["english"] == "Ginseng"

    def test_lookup_by_english(self):
        from tcm.tools.herbs import herbs_lookup
        result = herbs_lookup("Ginseng")
        assert result["status"] == "found"
        assert result["herb"]["chinese_name"] == "人参"

    def test_lookup_not_found(self):
        from tcm.tools.herbs import herbs_lookup
        result = herbs_lookup("nonexistent_herb")
        assert result["status"] == "not_found"

    def test_properties(self):
        from tcm.tools.herbs import herbs_properties
        result = herbs_properties("黄连")
        assert result["status"] == "found"
        assert "寒" in result["nature"]

    def test_by_category(self):
        from tcm.tools.herbs import herbs_by_category
        result = herbs_by_category("补气")
        assert result["status"] == "found"
        assert result["count"] >= 1

    def test_by_meridian(self):
        from tcm.tools.herbs import herbs_by_meridian
        result = herbs_by_meridian("Liver")
        assert result["status"] == "found"
        assert result["count"] >= 1

    def test_compounds(self):
        from tcm.tools.herbs import herbs_compounds
        result = herbs_compounds("黄连")
        assert result["status"] == "found"
        assert "Berberine" in result["key_compounds"]


class TestFormulas:
    def test_search_by_chinese(self):
        from tcm.tools.formulas import formulas_search
        result = formulas_search("四君子汤")
        assert result["status"] == "found"
        assert "Four Gentlemen" in result["formula"]["english"]

    def test_composition(self):
        from tcm.tools.formulas import formulas_composition
        result = formulas_composition("四君子汤")
        assert result["status"] == "found"
        assert "君 (Sovereign)" in result["composition"]

    def test_modifications(self):
        from tcm.tools.formulas import formulas_modifications
        result = formulas_modifications("四君子汤")
        assert result["status"] == "found"
        assert len(result["modifications"]) > 0


class TestSyndromes:
    def test_lookup(self):
        from tcm.tools.syndromes import syndromes_lookup
        result = syndromes_lookup("脾气虚")
        assert result["status"] == "found"
        assert result["syndrome"]["english"] == "Spleen Qi Deficiency"

    def test_identify_by_symptoms(self):
        from tcm.tools.syndromes import syndromes_identify
        result = syndromes_identify("fatigue, loose stools, poor appetite")
        assert result["status"] == "found"
        assert len(result["matches"]) >= 1

    def test_treatment(self):
        from tcm.tools.syndromes import syndromes_treatment
        result = syndromes_treatment("脾气虚")
        assert result["status"] == "found"
        assert "四君子汤" in result["representative_formulas"]


class TestInteractions:
    def test_check_incompatible_herbs(self):
        from tcm.tools.interactions import check_herbs
        result = check_herbs("甘草, 海藻")
        assert result["status"] == "warnings"
        assert result["count"] > 0

    def test_check_safe_herbs(self):
        from tcm.tools.interactions import check_herbs
        result = check_herbs("人参, 白术, 茯苓")
        assert result["status"] == "safe"

    def test_herb_drug_interaction(self):
        from tcm.tools.interactions import herb_drug
        result = herb_drug("人参", "Warfarin")
        assert result["status"] == "found"


class TestSafety:
    def test_toxicity_toxic_herb(self):
        from tcm.tools.safety import toxicity_check
        result = toxicity_check("附子")
        assert result["status"] == "toxic"
        assert "Aconitine" in result["toxic_compounds"]

    def test_toxicity_safe_herb(self):
        from tcm.tools.safety import toxicity_check
        result = toxicity_check("甘草")
        assert result["status"] == "not_toxic"

    def test_pregnancy_check(self):
        from tcm.tools.safety import pregnancy_check
        result = pregnancy_check("附子, 当归, 人参")
        assert result["status"] == "contraindicated"
        assert "附子" in result["contraindicated"]


class TestCompounds:
    def test_search(self):
        from tcm.tools.compounds import compounds_search
        result = compounds_search("berberine")
        assert result["status"] == "found"
        assert result["compound"]["name"] == "Berberine"

    def test_targets(self):
        from tcm.tools.compounds import compounds_targets
        result = compounds_targets("berberine")
        assert result["status"] == "found"
        assert len(result["targets"]) > 0


class TestToolRegistry:
    def test_registry_has_tools(self):
        from tcm.tools import registry
        tools = registry.list_tools()
        assert len(tools) > 20  # Should have 25+ tools

    def test_registry_categories(self):
        from tcm.tools import registry
        cats = registry.categories()
        assert "herbs" in cats
        assert "formulas" in cats
        assert "syndromes" in cats

    def test_tool_descriptions_for_llm(self):
        from tcm.tools import registry
        desc = registry.tool_descriptions_for_llm()
        assert "herbs.lookup" in desc
        assert "formulas.search" in desc
