"""
Literature tools: PubMed, CNKI, and TCM literature search.
"""

import logging
import httpx
from tcm.tools import registry

logger = logging.getLogger("tcm.tools.literature")


@registry.register(
    name="literature.pubmed_search",
    description="Search PubMed for research articles on TCM topics. Returns titles, abstracts, and PMIDs.",
    category="literature",
    parameters={"query": "Search query", "max_results": "Maximum results (default 5)"},
    usage_guide="When searching for published research evidence on TCM herbs, formulas, or compounds.",
)
def pubmed_search(query: str, max_results: int = 5) -> dict:
    """Search PubMed via NCBI E-utilities."""
    try:
        # Step 1: Search
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": min(max_results, 20),
            "retmode": "json",
        }
        resp = httpx.get(search_url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        id_list = data.get("esearchresult", {}).get("idlist", [])

        if not id_list:
            return {"status": "no_results", "query": query, "message": "No PubMed articles found."}

        # Step 2: Fetch summaries
        summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "json",
        }
        resp = httpx.get(summary_url, params=params, timeout=15)
        resp.raise_for_status()
        summary_data = resp.json()

        articles = []
        result_map = summary_data.get("result", {})
        for pmid in id_list:
            article = result_map.get(pmid, {})
            if article:
                articles.append({
                    "pmid": pmid,
                    "title": article.get("title", ""),
                    "authors": ", ".join(
                        a.get("name", "") for a in article.get("authors", [])[:3]
                    ),
                    "journal": article.get("fulljournalname", ""),
                    "pub_date": article.get("pubdate", ""),
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                })

        return {
            "status": "found",
            "query": query,
            "count": len(articles),
            "articles": articles,
        }
    except Exception as e:
        return {"status": "error", "message": f"PubMed search failed: {str(e)}"}


@registry.register(
    name="literature.cnki_search",
    description="Search CNKI (China National Knowledge Infrastructure) for Chinese-language TCM research.",
    category="literature",
    parameters={"query": "Search query (Chinese or English)"},
    usage_guide="When searching for Chinese-language TCM research literature.",
)
def cnki_search(query: str) -> dict:
    """Search CNKI (stub — requires authentication)."""
    return {
        "status": "info",
        "query": query,
        "message": (
            "CNKI search requires institutional access. "
            "Visit https://www.cnki.net/ to search directly. "
            "Alternative: use literature.pubmed_search with Chinese medicine keywords."
        ),
    }


@registry.register(
    name="literature.systematic_review",
    description="Find systematic reviews and meta-analyses for a TCM topic on PubMed.",
    category="literature",
    parameters={"topic": "Research topic"},
    usage_guide="When looking for high-level evidence summaries.",
)
def systematic_review(topic: str) -> dict:
    """Search for systematic reviews on a topic."""
    query = f"({topic}) AND (systematic review[pt] OR meta-analysis[pt]) AND (traditional Chinese medicine OR herbal medicine)"
    return pubmed_search(query, max_results=10)
