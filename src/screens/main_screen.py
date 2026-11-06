from PySide6.QtWidgets import QMainWindow
from graph_editor.graph_editor import GraphEditor


class MainScreen(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Causalitty")
        self.resize(1200, 800)

        self.graphEditor = GraphEditor()
        self.setCentralWidget(self.graphEditor)
