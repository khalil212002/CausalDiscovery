"""What the decision process suggests for one pair of variables.

Data only: the domain search fills these in, and the graph editor reads them
to draw the suggested edges.
"""

from dataclasses import dataclass, field
from enum import StrEnum, auto


class EdgeType(StrEnum):
    DIRECTED = auto()  # meta-analyses agree on a link and its direction
    UNDIRECTED = auto()  # agree on a link, conflict on its direction
    NO_EDGE = auto()  # agree there is no causal link
    CONFLICT = auto()  # disagree on whether a link exists; researcher decides
    NO_EVIDENCE = auto()  # no meta-analyses found for this pair


@dataclass
class Evidence:
    """One meta-analysis the suggestion was based on."""

    pmid: str  # PubMed ID, so the researcher can open the paper
    title: str
    claim: str  # one-line summary of what the paper says about the pair


@dataclass
class EdgeSuggestion:
    """The suggested edge (or lack of one) between two variables."""

    var_a: str
    var_b: str
    edge_type: EdgeType
    # Only set for DIRECTED edges: source -> target
    source: str | None = None
    target: str | None = None
    summary: str = ""  # shown to the researcher, especially for CONFLICT
    evidence: list[Evidence] = field(default_factory=list)
