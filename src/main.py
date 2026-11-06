from PySide6.QtWidgets import QApplication
from screens.main_screen import MainScreen
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainScreen = MainScreen()
    mainScreen.show()
    sys.exit(app.exec())
