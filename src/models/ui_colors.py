"""Colors used by the app's UI, other than the per-variable-type colors.

Kept as plain hex strings (like models/var_colors.py) so they can be shared
without importing Qt. Wrap them in QColor where they're drawn.
"""

# Graph editor nodes: neutral body, readable on dark and bright canvases
NODE_BODY_FILL: str = "#c1c6cd"
NODE_TEXT: str = "#161b22"  # name and badge text (dark on every type color)

# Selection ring drawn around a selected node
SELECTION_RING: str = "#ffffff"
SELECTION_HALO: str = "#28ffffff"  # white at 40/255 opacity (#AARRGGBB)

# Splash screen
SPLASH_BACKGROUND: str = "#1e1f22"
SPLASH_TITLE: str = "#e6e6e6"
SPLASH_TEXT: str = "#9aa0a6"
SPLASH_BAR_BACKGROUND: str = "#3a3c40"

# Node color in the matplotlib CPDAG preview (press G in the editor)
CPDAG_PLOT_NODE: str = "lightblue"
