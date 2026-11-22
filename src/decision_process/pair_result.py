"""Reading the result of the decision process for one pair of variables.

Run the search once with suggest_edge() (or domain_search() for many pairs),
then pass the EdgeSuggestion to these functions. They only read it, so no
extra PubMed or LLM calls are made.

Try it from src/:
    python -m decision_process.pair_result smoking "heart disease"
"""

import sys

from decision_process.edge_suggestion import EdgeSuggestion, EdgeType, Evidence


def get_relationship(suggestion: EdgeSuggestion) -> str:
    """The decided relationship between the two variables, as one line."""
    a, b = suggestion.var_a, suggestion.var_b
    match suggestion.edge_type:
        case EdgeType.DIRECTED:
            return f"{suggestion.source} -> {suggestion.target} ({suggestion.source} causes {suggestion.target})"
        case EdgeType.UNDIRECTED:
            return f"{a} -- {b} (linked, direction unclear)"
        case EdgeType.NO_EDGE:
            return f"{a}    {b} (no causal link)"
        case EdgeType.CONFLICT:
            return f"{a} ?? {b} (studies disagree, researcher decides)"
        case EdgeType.NO_EVIDENCE:
            return f"{a}    {b} (no evidence found)"
        case EdgeType.ERROR:
            return f"{a} !! {b} (search failed: {suggestion.summary})"


def get_summary(suggestion: EdgeSuggestion) -> str:
    """Why this relationship was chosen, summarized from the abstracts."""
    return suggestion.summary


def get_abstracts(suggestion: EdgeSuggestion) -> list[Evidence]:
    """The papers the decision was based on, most relevant first.

    Each entry has the PMID, title, the paper's claim about the pair, and the
    full abstract. Papers the LLM judged not relevant are left out.
    """
    return list(suggestion.evidence)


if __name__ == "__main__":
    from decision_process.domain_search import suggest_edge
    from decision_process.gemini_provider import GeminiProvider

    if len(sys.argv) != 3:
        sys.exit('Give exactly two variable names, e.g. smoking "heart disease"')

    result = suggest_edge(sys.argv[1], sys.argv[2], GeminiProvider())
    print("Relationship:", get_relationship(result))
    print("\nSummary:", get_summary(result))
    papers = get_abstracts(result)
    print(f"\nAbstracts used ({len(papers)}):")
    for paper in papers:
        print(f"\n--- PMID {paper.pmid}: {paper.title}")
        print(paper.abstract)
