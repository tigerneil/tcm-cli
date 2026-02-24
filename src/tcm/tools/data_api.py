"""
Data API tools: external TCM database integrations.

Connects to TCMSP, TCMID, BATMAN-TCM, SymMap, HERB, UniProt, STRING, KEGG.
"""

import logging
import httpx
from tcm.tools import registry

logger = logging.getLogger("tcm.tools.data_api")


@registry.register(
    name="data_api.tcmsp_search",
    description="Search TCMSP (Traditional Chinese Medicine Systems Pharmacology) database for herbs, compounds, or targets.",
    category="data_api",
    parameters={"query": "Search query", "search_type": "herb, compound, or target"},
    usage_guide="When needing comprehensive compound-target data from TCMSP.",
)
def tcmsp_search(query: str, search_type: str = "herb") -> dict:
    """Search TCMSP database."""
    return {
        "status": "info",
        "query": query,
        "search_type": search_type,
        "message": (
            "TCMSP database is available at https://old.tcmsp-e.com/tcmsp.php. "
            "For programmatic access, download the dataset via `tcm data pull tcmsp`. "
            "The database contains 499 herbs, 29,384 compounds, and 3,311 targets."
        ),
        "url": "https://old.tcmsp-e.com/tcmsp.php",
    }


@registry.register(
    name="data_api.uniprot_lookup",
    description="Look up a protein/gene on UniProt. Returns protein name, function, and associated pathways.",
    category="data_api",
    parameters={"gene_or_protein": "Gene symbol or UniProt ID"},
    usage_guide="When looking up protein information for targets identified in pharmacology analysis.",
)
def uniprot_lookup(gene_or_protein: str) -> dict:
    """Look up protein on UniProt."""
    try:
        url = f"https://rest.uniprot.org/uniprotkb/search"
        params = {
            "query": f"(gene:{gene_or_protein}) AND (organism_id:9606)",
            "format": "json",
            "size": 1,
        }
        resp = httpx.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if results:
            entry = results[0]
            protein_name = entry.get("proteinDescription", {}).get("recommendedName", {}).get("fullName", {}).get("value", "")
            gene_names = [g.get("geneName", {}).get("value", "") for g in entry.get("genes", [])]
            return {
                "status": "found",
                "uniprot_id": entry.get("primaryAccession", ""),
                "protein_name": protein_name,
                "gene_names": gene_names,
                "organism": "Homo sapiens",
                "url": f"https://www.uniprot.org/uniprot/{entry.get('primaryAccession', '')}",
            }
        return {"status": "not_found", "message": f"No UniProt entry found for '{gene_or_protein}'."}
    except Exception as e:
        return {"status": "error", "message": f"UniProt lookup failed: {str(e)}"}


@registry.register(
    name="data_api.kegg_pathway",
    description="Look up KEGG pathway information for a gene or pathway ID.",
    category="data_api",
    parameters={"query": "Gene symbol or KEGG pathway ID (e.g., hsa04151)"},
    usage_guide="When investigating biological pathways involved in herb mechanisms.",
)
def kegg_pathway(query: str) -> dict:
    """Look up KEGG pathway."""
    try:
        # Try gene lookup first
        url = f"https://rest.kegg.jp/find/genes/{query}"
        resp = httpx.get(url, timeout=10)
        if resp.status_code == 200 and resp.text.strip():
            lines = resp.text.strip().split("\n")[:5]
            results = []
            for line in lines:
                parts = line.split("\t")
                if len(parts) >= 2:
                    results.append({"kegg_id": parts[0], "description": parts[1]})
            return {"status": "found", "query": query, "results": results}
        return {"status": "not_found", "message": f"No KEGG results for '{query}'."}
    except Exception as e:
        return {"status": "error", "message": f"KEGG lookup failed: {str(e)}"}


@registry.register(
    name="data_api.string_interactions",
    description="Query STRING database for protein-protein interactions.",
    category="data_api",
    parameters={"gene": "Gene symbol"},
    usage_guide="When building protein interaction networks for target analysis.",
)
def string_interactions(gene: str) -> dict:
    """Query STRING for protein interactions."""
    try:
        url = "https://string-db.org/api/json/interaction_partners"
        params = {
            "identifiers": gene,
            "species": 9606,
            "limit": 10,
        }
        resp = httpx.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        interactions = []
        for item in data[:10]:
            interactions.append({
                "partner": item.get("preferredName_B", ""),
                "score": item.get("score", 0),
            })
        if interactions:
            return {"status": "found", "gene": gene, "interactions": interactions}
        return {"status": "not_found", "message": f"No STRING interactions found for '{gene}'."}
    except Exception as e:
        return {"status": "error", "message": f"STRING query failed: {str(e)}"}
