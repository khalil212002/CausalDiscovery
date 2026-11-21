from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QDockWidget, QMainWindow, QToolBar
from graph_editor.graph_editor import GraphEditor
from models.app_info import APP_NAME, MAIN_WINDOW_SIZE
from screens.independencies_screen import IndependenciesScreen


class MainScreen(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(APP_NAME)
        self.resize(*MAIN_WINDOW_SIZE)

        self.graphEditor = GraphEditor()
        self.setCentralWidget(self.graphEditor)

        self.independenciesScreen = IndependenciesScreen(self.graphEditor.editorScene)
        self.independenciesDock = QDockWidget("Conditional Independencies", self)
        self.independenciesDock.setWidget(self.independenciesScreen)
        self.addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea, self.independenciesDock
        )

        self.toolBar = QToolBar("Tools", self)
        self.toolBar.setObjectName("mainToolBar")
        self.toolBar.setMovable(False)
        self.toolBar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolBar)

        # Not connected yet — handlers will be wired up later.
        self.domainSearchAction = QAction("Domain Search", self)
        self.domainSearchAction.setToolTip("Run domain search")
        self.gesFixAction = QAction("GES Fix", self)
        self.gesFixAction.setToolTip("Run GES fix")

        self.toolBar.addAction(self.domainSearchAction)
        self.toolBar.addAction(self.gesFixAction)

        viewMenu = self.menuBar().addMenu("View")
        viewMenu.addAction(self.independenciesDock.toggleViewAction())
        viewMenu.addAction(self.toolBar.toggleViewAction())
