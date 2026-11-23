"""Arrow types: who added an arrow to the graph."""

from enum import StrEnum, auto


class ArrowTypes(StrEnum):
    USER = auto()  # drawn by the user in the editor
    DOMAIN_SEARCH_SUGGESTED = auto()  # suggested by Domain Search (PubMed + LLM)
    DOMAIN_SEARCH_ACCEPTED = auto()  # a Domain Search suggestion the user accepted


# Names shown in the UI for each arrow type.
ARROW_TYPE_LABELS: dict[ArrowTypes, str] = {
    ArrowTypes.USER: "User",
    ArrowTypes.DOMAIN_SEARCH_SUGGESTED: "Domain Search (suggested)",
    ArrowTypes.DOMAIN_SEARCH_ACCEPTED: "Domain Search (accepted)",
}
