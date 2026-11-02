"""Searches PubMed for meta-analyses about a pair of variables.

Uses NCBI's free E-utilities API in two steps: esearch turns a query into a
list of paper IDs (PMIDs), then efetch returns each paper's title and abstract.
"""

import threading
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass

import requests

from decision_process.config import NCBI_API_KEY

EUTILS_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
TIMEOUT_SECONDS = 15

# PubMed allows 3 requests per second without a key, 10 with one. Pairs are
# searched in parallel, so every request waits its turn here.
_MIN_INTERVAL = 0.12 if NCBI_API_KEY else 0.4
_MAX_RETRIES = 3  # PubMed can still answer 429 (too many requests) when busy
_rate_lock = threading.Lock()
_last_request = 0.0


@dataclass
class Article:
    """One PubMed paper. Only the abstract is sent to the LLM."""

    pmid: str
    title: str
    abstract: str


def search_meta_analyses(var_a: str, var_b: str, max_results: int = 10) -> list[Article]:
    """Meta-analyses that mention both variables, most relevant first.

    Returns an empty list when PubMed finds nothing.
    """
    # Papers naming both variables in the title are the most on-topic, but
    # there are often only a few. Fill the remaining slots with papers that
    # name both in the title or abstract (these include broad umbrella
    # reviews that list many risk factors, so they come second).
    # Without field tags PubMed expands terms so widely that off-topic
    # papers come back. [pt] = publication type, so only meta-analyses.
    title_ids = _search_ids(_pair_query(var_a, var_b, "ti"), max_results)
    abstract_ids = _search_ids(_pair_query(var_a, var_b, "tiab"), max_results)
    pmids = list(dict.fromkeys(title_ids + abstract_ids))[:max_results]
    if not pmids:
        return []
    return _fetch_articles(pmids)


def _pair_query(var_a: str, var_b: str, field: str) -> str:
    return f"({var_a}[{field}]) AND ({var_b}[{field}]) AND meta-analysis[pt]"


def _base_params() -> dict:
    params = {"db": "pubmed", "tool": "Causalitty"}
    # A key raises PubMed's rate limit from 3 to 10 requests per second
    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY
    return params


def _get(endpoint: str, params: dict) -> requests.Response:
    """GET an E-utilities endpoint, spacing requests to stay under the rate limit.

    If PubMed still says "too many requests", wait a moment and try again.
    """
    global _last_request
    for attempt in range(_MAX_RETRIES + 1):
        with _rate_lock:
            wait = _last_request + _MIN_INTERVAL - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            _last_request = time.monotonic()
        response = requests.get(f"{EUTILS_URL}/{endpoint}", params=params, timeout=TIMEOUT_SECONDS)
        if response.status_code != 429 or attempt == _MAX_RETRIES:
            return response
        time.sleep(1 + attempt)  # 1s, 2s, 3s


def _search_ids(query: str, max_results: int) -> list[str]:
    params = _base_params() | {
        "term": query,
        "retmax": max_results,
        "sort": "relevance",
        "retmode": "json",
    }
    response = _get("esearch.fcgi", params)
    response.raise_for_status()
    return response.json()["esearchresult"]["idlist"]


def _fetch_articles(pmids: list[str]) -> list[Article]:
    params = _base_params() | {"id": ",".join(pmids), "retmode": "xml"}
    response = _get("efetch.fcgi", params)
    response.raise_for_status()

    root = ET.fromstring(response.content)
    articles = [_parse_article(node) for node in root.iter("PubmedArticle")]
    # efetch doesn't promise to keep our order, so restore relevance order
    articles.sort(key=lambda a: pmids.index(a.pmid) if a.pmid in pmids else len(pmids))
    return articles


def _parse_article(node: ET.Element) -> Article:
    pmid = node.findtext(".//PMID", default="")

    # itertext() keeps text inside formatting tags like <i> or <sup>
    title_node = node.find(".//ArticleTitle")
    title = "".join(title_node.itertext()).strip() if title_node is not None else ""

    # Structured abstracts are split into labeled parts (BACKGROUND, METHODS, ...)
    parts = []
    for section in node.findall(".//Abstract/AbstractText"):
        text = "".join(section.itertext()).strip()
        label = section.get("Label")
        parts.append(f"{label}: {text}" if label else text)

    return Article(pmid=pmid, title=title, abstract="\n".join(parts))
