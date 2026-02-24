"""
Pharmacology tools: network pharmacology analysis, target prediction, pathway enrichment.

Supports building herb-compound-target-disease networks for mechanistic studies.
"""

import logging
import httpx
from tcm.tools import registry

logger = logging.getLogger("tcm.tools.pharmacology")


# ─── ASCII network rendering ─────────────────────────────────────

def _render_network_ascii(
    herbs: list[str],
    compound_target_map: dict[str, list[str]],
    formula_name: str = "Formula",
) -> str:
    """Render a herb→compound→target network as an ASCII diagram.

    Layout:
        [Formula]
            │
        ┌───┼───┐
      Herb1  Herb2  …
        │      │
      Cpd_A  Cpd_B  …
        │╲     │
      Tgt1 Tgt2 Tgt3 …
    """
    lines: list[str] = []

    # --- Collect data ---
    herb_compounds: dict[str, list[str]] = {}  # herb → [compound, …]
    compound_targets: dict[str, list[str]] = {}  # compound → [target, …]
    all_compounds: list[str] = []
    all_targets: set[str] = set()

    for herb_name in herbs:
        from tcm.tools.herbs import _search_herb
        herb = _search_herb(herb_name)
        cpds = herb.get("key_compounds", []) if herb else []
        herb_compounds[herb_name] = cpds
        for cpd in cpds:
            if cpd not in all_compounds:
                all_compounds.append(cpd)
            targets = compound_target_map.get(cpd, [])
            compound_targets[cpd] = targets
            all_targets.update(targets)

    all_targets_sorted = sorted(all_targets)

    # --- Title ---
    lines.append(f"  ┌{'─' * (len(formula_name) + 2)}┐")
    lines.append(f"  │ {formula_name} │")
    lines.append(f"  └{'─' * (len(formula_name) + 2)}┘")
    lines.append("        │")
    lines.append("        ▼")

    # --- Herb layer ---
    lines.append("  ╔═══════════════════════════════════════╗")
    lines.append("  ║  HERBS (中药)                         ║")
    lines.append("  ╠═══════════════════════════════════════╣")
    for herb in herbs:
        lines.append(f"  ║  ● {herb:35}║")
    lines.append("  ╚═══════════════════════════════════════╝")

    # --- Herb → Compound edges ---
    lines.append("        │")
    lines.append("        ▼")
    lines.append("  ╔═══════════════════════════════════════╗")
    lines.append("  ║  COMPOUNDS (活性成分)                 ║")
    lines.append("  ╠═══════════════════════════════════════╣")
    for herb in herbs:
        cpds = herb_compounds.get(herb, [])
        if cpds:
            lines.append(f"  ║  {herb}:")
            for cpd in cpds:
                tgt_count = len(compound_targets.get(cpd, []))
                arrow = f" → {tgt_count} target(s)" if tgt_count else ""
                lines.append(f"  ║    ├─ {cpd}{arrow}")
    lines.append("  ╚═══════════════════════════════════════╝")

    # --- Compound → Target edges ---
    lines.append("        │")
    lines.append("        ▼")
    lines.append("  ╔═══════════════════════════════════════╗")
    lines.append("  ║  TARGETS (靶点)                       ║")
    lines.append("  ╠═══════════════════════════════════════╣")
    if all_targets_sorted:
        # Show which compounds hit each target
        target_sources: dict[str, list[str]] = {}
        for cpd, tgts in compound_targets.items():
            for t in tgts:
                target_sources.setdefault(t, []).append(cpd)
        for target in all_targets_sorted:
            sources = target_sources.get(target, [])
            src_str = ", ".join(sources[:3])
            if len(sources) > 3:
                src_str += f" +{len(sources) - 3}"
            lines.append(f"  ║  ◆ {target:20} ← {src_str}")
    else:
        lines.append("  ║  (no targets resolved)")
    lines.append("  ╚═══════════════════════════════════════╝")

    # --- Stats ---
    lines.append("")
    lines.append("  ─── Network Statistics ───")
    lines.append(f"  Herbs:     {len(herbs)}")
    lines.append(f"  Compounds: {len(all_compounds)}")
    lines.append(f"  Targets:   {len(all_targets_sorted)}")
    lines.append(f"  Edges:     {sum(len(v) for v in compound_targets.values())}")

    return "\n".join(lines)


@registry.register(
    name="pharmacology.herb_targets",
    description="Get all known molecular targets for a herb's active compounds. Builds herb→compound→target mapping.",
    category="pharmacology",
    parameters={"herb_name": "Herb name (Chinese or English)"},
    usage_guide="When building herb-target networks or investigating herb mechanisms.",
)
def herb_targets(herb_name: str) -> dict:
    """Get molecular targets for all active compounds in a herb."""
    from tcm.tools.herbs import _search_herb
    herb = _search_herb(herb_name)
    if not herb:
        return {"status": "not_found", "message": f"Herb '{herb_name}' not found."}

    compounds = herb.get("key_compounds", [])
    target_map = {}
    for compound in compounds:
        from tcm.tools.compounds import compounds_search
        result = compounds_search(compound)
        if result["status"] == "found":
            targets = result["compound"].get("known_targets", [])
            target_map[compound] = targets

    all_targets = set()
    for targets in target_map.values():
        all_targets.update(targets)

    return {
        "status": "found",
        "herb": herb["chinese_name"],
        "compound_target_map": target_map,
        "unique_targets": sorted(all_targets),
        "total_compounds": len(compounds),
        "total_targets": len(all_targets),
    }


@registry.register(
    name="pharmacology.disease_targets",
    description="Retrieve disease-associated targets from public databases (GeneCards, OMIM, DisGeNET). Returns target gene list.",
    category="pharmacology",
    parameters={"disease": "Disease name in English"},
    usage_guide="When identifying disease targets for network pharmacology analysis.",
)
def disease_targets(disease: str) -> dict:
    """Get disease-associated targets (uses public API)."""
    try:
        # Use Open Targets API
        url = "https://api.platform.opentargets.org/api/v4/graphql"
        query_gql = """
        query($disease: String!) {
            search(queryString: $disease, entityNames: ["disease"], page: {size: 1, index: 0}) {
                hits { id name }
            }
        }
        """
        resp = httpx.post(url, json={"query": query_gql, "variables": {"disease": disease}}, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            hits = data.get("data", {}).get("search", {}).get("hits", [])
            if hits:
                return {
                    "status": "found",
                    "disease": disease,
                    "disease_id": hits[0].get("id"),
                    "message": "Use Open Targets platform for full target list. Disease ID found.",
                }
        return {
            "status": "partial",
            "disease": disease,
            "message": "Could not retrieve full target list. Try searching manually on Open Targets, GeneCards, or DisGeNET.",
        }
    except Exception as e:
        return {"status": "error", "message": f"API error: {str(e)}"}


@registry.register(
    name="pharmacology.pathway_enrichment",
    description="Perform KEGG/GO pathway enrichment analysis on a gene/target list.",
    category="pharmacology",
    parameters={"gene_list": "Comma-separated list of gene symbols"},
    usage_guide="When analyzing which biological pathways are enriched in a set of targets.",
)
def pathway_enrichment(gene_list: str) -> dict:
    """Perform pathway enrichment (stub — requires enrichr or gseapy)."""
    genes = [g.strip() for g in gene_list.split(",") if g.strip()]
    if not genes:
        return {"status": "error", "message": "No genes provided."}

    return {
        "status": "info",
        "gene_count": len(genes),
        "genes": genes,
        "message": (
            "For full pathway enrichment, install gseapy (`pip install gseapy`) "
            "or use the Enrichr API. The following databases are supported: "
            "KEGG_2021_Human, GO_Biological_Process_2021, Reactome_2022, WikiPathways_2023."
        ),
        "enrichr_url": "https://maayanlab.cloud/Enrichr/",
    }


@registry.register(
    name="pharmacology.network_build",
    description="Build a herb-compound-target-disease network from formula composition. Returns network statistics and key nodes.",
    category="pharmacology",
    parameters={"formula_name": "Formula name or comma-separated herb list"},
    usage_guide="When performing network pharmacology analysis of a TCM formula.",
)
def network_build(formula_name: str) -> dict:
    """Build network pharmacology overview for a formula or herb combination."""
    from tcm.tools.formulas import FORMULA_DB

    # Try to find formula
    herbs_list = []
    formula_found = None
    for name, data in FORMULA_DB.items():
        if formula_name.lower() in (name.lower(), data["pinyin"].lower(), data["english"].lower()):
            formula_found = name
            for role_herbs in data["composition"].values():
                for h in role_herbs:
                    herbs_list.append(h["herb"])
            break

    if not herbs_list:
        # Treat as comma-separated herb list
        herbs_list = [h.strip() for h in formula_name.split(",") if h.strip()]

    if not herbs_list:
        return {"status": "error", "message": "No herbs found. Provide a formula name or herb list."}

    # Collect all compound-target mappings
    network = {"herbs": [], "compounds": [], "targets": set()}
    compound_target_map: dict[str, list[str]] = {}
    for herb_name in herbs_list:
        result = herb_targets(herb_name)
        if result["status"] == "found":
            network["herbs"].append(herb_name)
            for compound, targets in result.get("compound_target_map", {}).items():
                network["compounds"].append(compound)
                network["targets"].update(targets)
                compound_target_map[compound] = targets

    # Build ASCII network diagram
    ascii_network = _render_network_ascii(
        herbs=network["herbs"],
        compound_target_map=compound_target_map,
        formula_name=formula_found or formula_name,
    )

    return {
        "status": "found",
        "formula": formula_found or "custom",
        "network_stats": {
            "herbs": len(network["herbs"]),
            "compounds": len(network["compounds"]),
            "targets": len(network["targets"]),
        },
        "herbs": network["herbs"],
        "compounds": network["compounds"],
        "targets": sorted(network["targets"]),
        "ascii_network": ascii_network,
    }


@registry.register(
    name="pharmacology.visualize",
    description="Visualize a herb-compound-target network as an ASCII diagram in the terminal. Shows the multi-layer network for a formula or herb list.",
    category="pharmacology",
    parameters={"formula_name": "Formula name or comma-separated herb list"},
    usage_guide="When user asks to visualize, draw, or display a network pharmacology diagram.",
)
def network_visualize(formula_name: str) -> dict:
    """Build and return an ASCII visualization of the pharmacology network."""
    result = network_build(formula_name)
    if result["status"] != "found":
        return result
    return {
        "status": "found",
        "formula": result["formula"],
        "network_stats": result["network_stats"],
        "visualization": result["ascii_network"],
    }
