"""Domain search: suggests an edge for each pair of selected variables.

For each pair: fetch meta-analyses from PubMed, ask the LLM what each paper
found, then apply the flowchart rules to choose the edge type.
"""

import logging
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from itertools import combinations

from decision_process.edge_suggestion import EdgeSuggestion, EdgeType, Evidence
from decision_process.errors import DecisionProcessError, LLMBadResponse
from decision_process.llm_provider import LLMProvider
from decision_process.prompts import (
    PairAnalysis,
    PaperFinding,
    PaperVerdict,
    build_pair_prompt,
    parse_pair_response,
)
from decision_process.pubmed_client import Article, search_meta_analyses

logger = logging.getLogger(__name__)

# Many fetched papers turn out not to study the pair, so fetch enough that
# some relevant ones remain after the LLM filters them out
MAX_PAPERS = 12

# Pairs searched at the same time. Most of the time is spent waiting on
# PubMed and the LLM, so threads are enough. PubMed's rate limit is
# respected inside pubmed_client.
MAX_PARALLEL_PAIRS = 4

# Times to ask the LLM for one pair when its answer can't be read
LLM_ATTEMPTS = 2

LINK_VERDICTS = {
    PaperVerdict.A_CAUSES_B,
    PaperVerdict.B_CAUSES_A,
    PaperVerdict.UNCLEAR_DIRECTION,
}


def domain_search(variables: list[str], llm: LLMProvider) -> list[EdgeSuggestion]:
    """One suggestion for every pair of the given variables, in pair order.

    Never raises for a failed pair: that pair gets an ERROR suggestion whose
    summary says why, and the other pairs still run. If an error means every
    pair would fail (daily quota used up, invalid API key), the pairs not yet
    started are skipped and also marked ERROR with that message.
    """
    pairs = list(combinations(variables, 2))
    stop = threading.Event()
    stop_reason: list[str] = []  # message of the error that stopped the search

    def run_pair(pair: tuple[str, str]) -> EdgeSuggestion:
        var_a, var_b = pair
        if stop.is_set():
            return _error_suggestion(var_a, var_b, f"Skipped: {stop_reason[0]}")
        try:
            return _analyze_pair(var_a, var_b, llm)
        except DecisionProcessError as error:
            if error.stops_search and not stop.is_set():
                stop_reason.append(error.message)
                stop.set()
            return _error_suggestion(var_a, var_b, error.message)
        except Exception:
            return _unexpected_error(var_a, var_b)

    with ThreadPoolExecutor(max_workers=MAX_PARALLEL_PAIRS) as pool:
        return list(pool.map(run_pair, pairs))


def suggest_edge(var_a: str, var_b: str, llm: LLMProvider) -> EdgeSuggestion:
    """The suggested edge between two variables, based on meta-analyses.

    Never raises: if the search fails, returns an ERROR suggestion whose
    summary says why.
    """
    try:
        return _analyze_pair(var_a, var_b, llm)
    except DecisionProcessError as error:
        return _error_suggestion(var_a, var_b, error.message)
    except Exception:
        return _unexpected_error(var_a, var_b)


def _error_suggestion(var_a: str, var_b: str, message: str) -> EdgeSuggestion:
    return EdgeSuggestion(var_a, var_b, EdgeType.ERROR, summary=message)


def _unexpected_error(var_a: str, var_b: str) -> EdgeSuggestion:
    # A bug, not an outside service failing: keep the full traceback in the
    # log for us, and show the user a short message
    logger.exception("Unexpected error while analyzing %r and %r", var_a, var_b)
    return _error_suggestion(
        var_a, var_b, "An unexpected error occurred while analyzing this pair."
    )


def _analyze_pair(var_a: str, var_b: str, llm: LLMProvider) -> EdgeSuggestion:
    """The actual search for one pair. Raises DecisionProcessError on failure."""
    articles = search_meta_analyses(var_a, var_b, max_results=MAX_PAPERS)
    if not articles:
        return EdgeSuggestion(
            var_a, var_b, EdgeType.NO_EVIDENCE,
            summary="No meta-analyses found on PubMed for this pair.",
        )

    analysis = _ask_llm(var_a, var_b, articles, llm)
    relevant = [f for f in analysis.findings if f.verdict != PaperVerdict.NOT_RELEVANT]

    by_pmid = {a.pmid: a for a in articles}
    evidence = [
        Evidence(f.pmid, by_pmid[f.pmid].title, f.claim, by_pmid[f.pmid].abstract)
        for f in relevant
    ]

    edge_type, source, target = decide_edge(var_a, var_b, relevant)
    summary = analysis.summary
    if edge_type == EdgeType.NO_EVIDENCE:
        summary = "Meta-analyses were found, but none studied this pair directly."
    return EdgeSuggestion(var_a, var_b, edge_type, source, target, summary, evidence)


def _ask_llm(
    var_a: str, var_b: str, articles: list[Article], llm: LLMProvider
) -> PairAnalysis:
    """The LLM's analysis of the articles, asking again if the answer is unreadable."""
    prompt = build_pair_prompt(var_a, var_b, articles)
    for attempt in range(LLM_ATTEMPTS):
        try:
            return parse_pair_response(llm.generate(prompt), articles)
        except LLMBadResponse:
            if attempt == LLM_ATTEMPTS - 1:
                raise
    raise AssertionError("unreachable")


def decide_edge(
    var_a: str, var_b: str, findings: list[PaperFinding]
) -> tuple[EdgeType, str | None, str | None]:
    """The flowchart rules: (edge type, source, target) from relevant findings.

    - no relevant papers                       -> NO_EVIDENCE
    - some find a link, others find none       -> CONFLICT (researcher decides)
    - all find no link                         -> NO_EDGE
    - all find a link, in one direction        -> DIRECTED
    - all find a link, directions conflict or
      none states a direction                  -> UNDIRECTED

    Papers that find a link but are unsure of its direction don't contradict
    papers that state one, so they don't stop an edge from being DIRECTED.
    """
    verdicts = {f.verdict for f in findings}
    if not verdicts:
        return EdgeType.NO_EVIDENCE, None, None

    has_link = bool(verdicts & LINK_VERDICTS)
    if has_link and PaperVerdict.NO_LINK in verdicts:
        return EdgeType.CONFLICT, None, None
    if not has_link:
        return EdgeType.NO_EDGE, None, None

    a_to_b = PaperVerdict.A_CAUSES_B in verdicts
    b_to_a = PaperVerdict.B_CAUSES_A in verdicts
    if a_to_b and not b_to_a:
        return EdgeType.DIRECTED, var_a, var_b
    if b_to_a and not a_to_b:
        return EdgeType.DIRECTED, var_b, var_a
    return EdgeType.UNDIRECTED, None, None


if __name__ == "__main__":
    # Try it from src/:  python -m decision_process.domain_search smoking "preterm birth" stress
    from decision_process.gemini_provider import GeminiProvider

    if len(sys.argv) < 3:
        sys.exit("Give at least two variable names")

    for s in domain_search(sys.argv[1:], GeminiProvider()):
        arrow = f"{s.source} -> {s.target}" if s.source else f"{s.var_a} -- {s.var_b}"
        print(f"\n[{s.edge_type.upper()}] {arrow}")
        print(f"  {s.summary}")
        for e in s.evidence:
            print(f"  - PMID {e.pmid}: {e.claim}")
