"""App-wide settings: the app's name, window size and startup steps."""

APP_NAME: str = "Causalitty"
APP_SUBTITLE: str = "Causal discovery"

# Default size of the main window, as (width, height).
MAIN_WINDOW_SIZE: tuple[int, int] = (1200, 800)

# Heavy modules loaded on the splash screen, as (message shown, module name).
SPLASH_STEPS: list[tuple[str, str]] = [
    ("Loading the plotting library...", "matplotlib.pyplot"),
    ("Loading the causal inference library...", "pgmpy.base"),
    ("Opening the graph editor...", "screens.main_screen"),
]
