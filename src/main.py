from PySide6.QtWidgets import QApplication
from screens.splash_screen import SplashScreen
import sys

SPLASH_STEPS = [
    ("Loading the plotting library...", "matplotlib.pyplot"),
    ("Loading the causal inference library...", "pgmpy.base"),
    ("Opening the graph editor...", "screens.main_screen"),
]

if __name__ == "__main__":
    app = QApplication(sys.argv)
    splashScreen = SplashScreen()
    splashScreen.show()
    splashScreen.load(SPLASH_STEPS)

    from screens.main_screen import MainScreen

    mainScreen = MainScreen()
    mainScreen.show()
    splashScreen.finish(mainScreen)
    sys.exit(app.exec())
