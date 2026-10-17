"""Colors used for each variable type.

Kept in models/ so every part of the app (not just the graph editor) can
share the same per-type color without duplicating hex values.
"""

from models.var_types import VarTypes

# One color per variable type.
VAR_TYPE_COLORS: dict[VarTypes, str] = {
    VarTypes.EXPOSURE: "#5fc97d",  # green (light, not dark)
    VarTypes.OUTCOME: "#4f9bf5",  # blue
    VarTypes.ADJUSTED: "#f7f8f9",  # white
    VarTypes.UNOBSERVED: "#9aa0a6",  # gray
}

DEFAULT_VAR_COLOR: str = VAR_TYPE_COLORS[VarTypes.UNOBSERVED]


def var_type_color(type: VarTypes | None) -> str:
    """Hex color for a variable type, falling back to the default color."""
    return VAR_TYPE_COLORS.get(type, DEFAULT_VAR_COLOR)
