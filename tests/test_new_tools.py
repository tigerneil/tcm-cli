"""Tests for diagnostics, acupuncture, and classics TCM tools."""
from __future__ import annotations

import pytest

from tcm.tools import ensure_loaded, registry, tool_load_errors
from tcm.tools.acupuncture import by_meridian, point_lookup, protocol
from tcm.tools.classics import classics_search, clause_lookup, herb_monograph
from tcm.tools.diagnostics import (
    four_examinations,
    herb_identify,
    prescription_parse,
    tongue_analyze,
)


@pytest.fixture(autouse=True)
def _ensure_tools():
    ensure_loaded()


class TestDiagnosticsTools:
    def test_zero_tool_load_errors_and_50_tools(self):
        assert tool_load_errors() == {}
        assert len(registry.list_tools()) >= 50

    def test_tongue_analyze_pale_swollen_scalloped(self):
        res = tongue_analyze(
            body_color="淡白",
            body_shape="胖大齿痕",
            coating_color="白",
            coating_texture="滑",
        )
        assert res["status"] == "complete"
        assert "primary_syndrome" in res
        assert "eight_principles" in res
        assert "somatotopy_zones" in res

    def test_tongue_analyze_with_biometrics(self):
        bio = {
            "lab_approx": {"L": 48.0, "a": 38.5, "b": 26.0},
            "tcm_visual_hints": ["Deep red/crimson body (high CIE a*)", "Yellow coating"],
        }
        res = tongue_analyze(
            observations="Red tongue with yellow greasy coating",
            biometrics=bio,
        )
        assert res["status"] == "complete"
        assert "eight_principles" in res
        assert "biometric_interpretation" in res

    def test_herb_identify_huangqi_and_chuanbeimu(self):
        hq = herb_identify("菊花心 chrysanthemum striations, 豆腥气 bean aroma, pale yellow cortex")
        assert hq["status"] == "found"
        top_names = [m["herb"] for m in hq["matches"]]
        assert "黄芪" in top_names

        cb = herb_identify("怀中抱月 holding the moon, 观音合掌")
        assert cb["status"] == "found"
        assert cb["matches"][0]["herb"] == "川贝母"

    def test_prescription_parse_han_guizhi_tang(self):
        res = prescription_parse(
            "桂枝三两 芍药三两 甘草二两炙 生姜三两切 大枣十二枚擘",
            era="han",
        )
        assert res["status"] == "complete"
        herb_names = [h["herb"] for h in res["herbs"]]
        assert "桂枝" in herb_names
        assert "甘草" in herb_names
        guizhi = next(h for h in res["herbs"] if h["herb"] == "桂枝")
        assert guizhi["metric_g"] == pytest.approx(41.4, rel=1e-2)
        assert guizhi["clinical_conservative_g"] == pytest.approx(9.0, rel=1e-2)
        assert any("桂枝汤" in str(m) for m in res["classical_formula_matches"])

    def test_prescription_parse_eighteen_incompatibilities(self):
        res = prescription_parse("人参 9g, 藜芦 3g, 附子 12g", era="modern")
        assert res["status"] == "complete"
        audit = res["safety_audit"]
        assert audit["herb_interactions"]["status"] == "warnings"
        assert len(audit["toxicity_alerts"]) >= 1

    def test_four_examinations_fusion(self):
        res = four_examinations(
            inspection="面色萎黄，舌淡胖有齿痕，苔白滑",
            auscultation="语声低微，少气懒言",
            inquiry="神疲乏力，食少便溏，畏寒肢冷",
            pulse="脉沉迟弱",
        )
        assert res["status"] == "complete"
        assert "eight_principles" in res
        assert len(res["ranked_syndromes"]) >= 1


class TestAcupunctureTools:
    def test_point_lookup_by_code_and_chinese(self):
        st36 = point_lookup("ST36")
        assert st36["status"] == "found"
        assert st36["acupoint"]["chinese_name"] == "足三里"

        li4 = point_lookup("合谷")
        assert li4["status"] == "found"
        assert li4["acupoint"]["code"] == "LI4"

    def test_by_meridian(self):
        res = by_meridian("ST")
        assert res["status"] == "found"
        assert res["count"] >= 2

    def test_protocol_pregnancy_safe_strips_forbidden_points(self):
        std = protocol("肝气郁结", pregnancy_safe=False)
        preg = protocol("肝气郁结", pregnancy_safe=True)
        assert std["status"] == "complete"
        assert preg["status"] == "complete"
        preg_codes = [p["code"] if isinstance(p, dict) else str(p) for p in preg["points"]]
        for forbidden in ("LI4", "SP6", "BL60", "BL67", "CV4", "CV6"):
            assert forbidden not in preg_codes
        assert len(preg["filtered_pregnancy_forbidden_points"]) >= 1


class TestClassicsTools:
    def test_classics_search(self):
        res = classics_search("治未病")
        assert res["status"] == "found"
        assert res["count"] >= 1

    def test_clause_lookup_shanghan_lun_96(self):
        res = clause_lookup("伤寒论", "96")
        assert res["status"] == "found"
        assert "小柴胡汤" in str(res)

    def test_herb_monograph(self):
        res = herb_monograph("人参")
        assert res["status"] == "found"
        assert "人参" in str(res)
