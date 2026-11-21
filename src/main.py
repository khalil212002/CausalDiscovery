from PySide6.QtWidgets import QApplication
from models.app_info import SPLASH_STEPS
from screens.splash_screen import SplashScreen
import sys

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
