"""
Compound tools: active compound analysis, molecular properties, ADMET prediction.
"""

import logging
from tcm.tools import registry

logger = logging.getLogger("tcm.tools.compounds")


@registry.register(
    name="compounds.search",
    description="Search for active compounds by name or herb source. Returns molecular properties and known targets.",
    category="compounds",
    parameters={"query": "Compound name or herb source"},
    usage_guide="When investigating specific active compounds from TCM herbs.",
)
def compounds_search(query: str) -> dict:
    """Search for active compounds."""
    # Known compound data
    COMPOUND_DB = {
        "berberine": {
            "name": "Berberine",
            "chinese_name": "小檗碱",
            "source_herbs": ["黄连 (Coptis)", "黄柏 (Phellodendron)"],
            "molecular_formula": "C20H18NO4+",
            "molecular_weight": 336.36,
            "ob_percent": 36.86,
            "dl": 0.78,
            "known_targets": ["DPP4", "AChE", "PTGS2", "HMGCR", "AMPK"],
            "pharmacological_actions": [
                "Anti-inflammatory", "Antimicrobial", "Hypoglycemic",
                "Lipid-lowering", "Neuroprotective",
            ],
        },
        "ginsenoside rg1": {
            "name": "Ginsenoside Rg1",
            "chinese_name": "人参皂苷Rg1",
            "source_herbs": ["人参 (Ginseng)"],
            "molecular_formula": "C42H72O14",
            "molecular_weight": 801.01,
            "ob_percent": 12.28,
            "dl": 0.84,
            "known_targets": ["ESR1", "AR", "GR", "PPARG"],
            "pharmacological_actions": [
                "Neuroprotective", "Anti-fatigue", "Immunomodulatory", "Cardioprotective",
            ],
        },
        "astragaloside iv": {
            "name": "Astragaloside IV",
            "chinese_name": "黄芪甲苷",
            "source_herbs": ["黄芪 (Astragalus)"],
            "molecular_formula": "C41H68O14",
            "molecular_weight": 784.97,
            "ob_percent": 17.74,
            "dl": 0.15,
            "known_targets": ["TLR4", "NF-κB", "PI3K", "AKT"],
            "pharmacological_actions": [
                "Cardioprotective", "Anti-inflammatory", "Immunomodulatory", "Anti-fibrotic",
            ],
        },
    }
    query_lower = query.lower().strip()
    for key, data in COMPOUND_DB.items():
        if query_lower in key or query_lower in data["chinese_name"].lower():
            return {"status": "found", "compound": data}
    # Check by herb source
    for key, data in COMPOUND_DB.items():
        for herb in data["source_herbs"]:
            if query_lower in herb.lower():
                return {"status": "found", "compound": data}
    return {"status": "not_found", "message": f"Compound '{query}' not found. Try data_api.tcmsp_search."}


@registry.register(
    name="compounds.admet",
    description="Predict ADMET (Absorption, Distribution, Metabolism, Excretion, Toxicity) properties for a compound.",
    category="compounds",
    parameters={"compound_name": "Compound name"},
    usage_guide="When evaluating drug-likeness or pharmacokinetic properties of a compound.",
)
def compounds_admet(compound_name: str) -> dict:
    """Predict ADMET properties (simplified)."""
    return {
        "status": "info",
        "message": f"ADMET prediction for '{compound_name}' requires online TCMSP or SwissADME lookup. Use data_api.tcmsp_search or data_api.swiss_adme.",
        "general_criteria": {
            "OB_threshold": "≥30% (oral bioavailability)",
            "DL_threshold": "≥0.18 (drug-likeness)",
            "Lipinski_rule": "MW≤500, LogP≤5, HBD≤5, HBA≤10",
        },
    }


@registry.register(
    name="compounds.targets",
    description="Retrieve known molecular targets for a compound.",
    category="compounds",
    parameters={"compound_name": "Compound name"},
    usage_guide="When building compound-target networks or investigating mechanism of action.",
)
def compounds_targets(compound_name: str) -> dict:
    """Get molecular targets for a compound."""
    result = compounds_search(compound_name)
    if result["status"] == "found":
        compound = result["compound"]
        return {
            "status": "found",
            "compound": compound["name"],
            "targets": compound.get("known_targets", []),
            "pharmacological_actions": compound.get("pharmacological_actions", []),
        }
    return result
