"""Colors and line styles used for each arrow type, like models/var_colors.py
for nodes."""

from models.arrow_types import ArrowTypes

ARROW_TYPE_COLORS: dict[ArrowTypes, str] = {
    ArrowTypes.USER: "#a0a0a4",  # Qt's standard gray
    ArrowTypes.DOMAIN_SEARCH_SUGGESTED: "#a371f7",  # purple
    ArrowTypes.DOMAIN_SEARCH_ACCEPTED: "#2bb5a5",  # teal
}

# Arrow types drawn with a dashed line: suggestions not accepted yet
DASHED_ARROW_TYPES: set[ArrowTypes] = {ArrowTypes.DOMAIN_SEARCH_SUGGESTED}

DEFAULT_ARROW_COLOR: str = ARROW_TYPE_COLORS[ArrowTypes.USER]

# Color of a selected arrow, whatever its type
SELECTED_ARROW_COLOR: str = "#f0883e"  # orange


def arrow_type_color(type: ArrowTypes | None) -> str:
    """Hex color for an arrow type, falling back to the default color."""
    return ARROW_TYPE_COLORS.get(type, DEFAULT_ARROW_COLOR)
