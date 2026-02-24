"""
Modern evidence tools: clinical trial search, pharmacokinetic data, modern indication mapping.
"""

import logging
import httpx
from tcm.tools import registry

logger = logging.getLogger("tcm.tools.modern")


@registry.register(
    name="modern.clinical_trials",
    description="Search ClinicalTrials.gov for clinical trials on a TCM herb, formula, or compound.",
    category="modern",
    parameters={"query": "Search query (herb, formula, or compound name)"},
    usage_guide="When looking for clinical trial evidence for a TCM intervention.",
)
def clinical_trials(query: str) -> dict:
    """Search ClinicalTrials.gov."""
    try:
        url = "https://clinicaltrials.gov/api/v2/studies"
        params = {
            "query.term": f"{query} traditional Chinese medicine",
            "pageSize": 5,
        }
        resp = httpx.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        studies = data.get("studies", [])
        results = []
        for study in studies:
            proto = study.get("protocolSection", {})
            id_mod = proto.get("identificationModule", {})
            status_mod = proto.get("statusModule", {})
            results.append({
                "nct_id": id_mod.get("nctId", ""),
                "title": id_mod.get("briefTitle", ""),
                "status": status_mod.get("overallStatus", ""),
                "url": f"https://clinicaltrials.gov/study/{id_mod.get('nctId', '')}",
            })
        if results:
            return {"status": "found", "count": len(results), "trials": results}
        return {"status": "no_results", "message": f"No clinical trials found for '{query}'."}
    except Exception as e:
        return {"status": "error", "message": f"ClinicalTrials.gov search failed: {str(e)}"}


@registry.register(
    name="modern.evidence_summary",
    description="Summarize modern scientific evidence for a TCM herb or formula. Combines PubMed and clinical trial data.",
    category="modern",
    parameters={"query": "Herb or formula name"},
    usage_guide="When creating an evidence-based summary for a TCM intervention.",
)
def evidence_summary(query: str) -> dict:
    """Create evidence summary combining multiple sources."""
    from tcm.tools.literature import pubmed_search
    pubmed_result = pubmed_search(f"{query} randomized controlled trial", max_results=3)
    trial_result = clinical_trials(query)

    return {
        "status": "complete",
        "query": query,
        "pubmed_evidence": pubmed_result,
        "clinical_trials": trial_result,
        "note": "This is an automated summary. Review individual sources for full details.",
    }


@registry.register(
    name="modern.indication_map",
    description="Map a TCM syndrome to its closest modern medical diagnoses (ICD-10).",
    category="modern",
    parameters={"syndrome": "TCM syndrome name"},
    usage_guide="When bridging TCM diagnosis with modern medical classification.",
)
def indication_map(syndrome: str) -> dict:
    """Map TCM syndrome to modern diagnoses."""
    SYNDROME_ICD_MAP = {
        "脾气虚": [
            {"icd10": "K30", "diagnosis": "Functional dyspepsia"},
            {"icd10": "K59.1", "diagnosis": "Functional diarrhea"},
            {"icd10": "R53", "diagnosis": "Malaise and fatigue"},
        ],
        "肝气郁结": [
            {"icd10": "F32", "diagnosis": "Major depressive disorder"},
            {"icd10": "F41.1", "diagnosis": "Generalized anxiety disorder"},
            {"icd10": "K80", "diagnosis": "Cholelithiasis"},
        ],
        "肾阴虚": [
            {"icd10": "N95.1", "diagnosis": "Menopausal and perimenopausal disorders"},
            {"icd10": "E11", "diagnosis": "Type 2 diabetes mellitus"},
            {"icd10": "N18", "diagnosis": "Chronic kidney disease"},
        ],
        "风寒表证": [
            {"icd10": "J00", "diagnosis": "Acute nasopharyngitis (common cold)"},
            {"icd10": "J06.9", "diagnosis": "Acute upper respiratory infection"},
        ],
        "湿热蕴脾": [
            {"icd10": "K29", "diagnosis": "Gastritis and duodenitis"},
            {"icd10": "A09", "diagnosis": "Infectious gastroenteritis"},
            {"icd10": "K76.0", "diagnosis": "Fatty liver disease"},
        ],
    }

    for name, mappings in SYNDROME_ICD_MAP.items():
        if syndrome.lower() in name.lower() or name.lower() in syndrome.lower():
            return {"status": "found", "syndrome": name, "modern_diagnoses": mappings}
    return {
        "status": "not_found",
        "message": f"No ICD-10 mapping found for '{syndrome}'. This is a simplified mapping; consult TCM-Western medicine integration references.",
    }
