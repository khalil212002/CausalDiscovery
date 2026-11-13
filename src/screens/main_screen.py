from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget, QMainWindow
from graph_editor.graph_editor import GraphEditor
from screens.independencies_screen import IndependenciesScreen


class MainScreen(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Causalitty")
        self.resize(1200, 800)

        self.graphEditor = GraphEditor()
        self.setCentralWidget(self.graphEditor)

        self.independenciesScreen = IndependenciesScreen(self.graphEditor.editorScene)
        self.independenciesDock = QDockWidget("Conditional Independencies", self)
        self.independenciesDock.setWidget(self.independenciesScreen)
        self.addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea, self.independenciesDock
        )

        viewMenu = self.menuBar().addMenu("View")
        viewMenu.addAction(self.independenciesDock.toggleViewAction())
