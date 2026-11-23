from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QDockWidget, QMainWindow, QToolBar
from graph_editor.graph_editor import GraphEditor
from models.app_info import APP_NAME, MAIN_WINDOW_SIZE
from screens.independencies_screen import IndependenciesScreen
from screens.properties_screen import PropertiesScreen


class MainScreen(QMainWindow):
    # Starting size of the right dock column: its width, and the heights of
    # the Properties and CI docks (which share it)
    RIGHT_DOCKS_WIDTH = 380
    PROPERTIES_CI_HEIGHTS = (340, 400)

    def __init__(self):
        super().__init__()

        self.setWindowTitle(APP_NAME)
        self.resize(*MAIN_WINDOW_SIZE)

        self.graphEditor = GraphEditor()
        self.setCentralWidget(self.graphEditor)

        self.propertiesScreen = PropertiesScreen(self.graphEditor.editorScene)
        self.propertiesDock = QDockWidget("Properties", self)
        self.propertiesDock.setObjectName("propertiesDock")
        self.propertiesDock.setWidget(self.propertiesScreen)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.propertiesDock)

        self.independenciesScreen = IndependenciesScreen(self.graphEditor.editorScene)
        self.independenciesDock = QDockWidget("Conditional Independencies", self)
        self.independenciesDock.setWidget(self.independenciesScreen)
        self.addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea, self.independenciesDock
        )
        # Properties on top, CI panel below it
        self.splitDockWidget(
            self.propertiesDock, self.independenciesDock, Qt.Orientation.Vertical
        )
        self.resizeDocks(
            [self.propertiesDock, self.independenciesDock],
            list(self.PROPERTIES_CI_HEIGHTS),
            Qt.Orientation.Vertical,
        )
        self.resizeDocks(
            [self.propertiesDock], [self.RIGHT_DOCKS_WIDTH], Qt.Orientation.Horizontal
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
        viewMenu.addAction(self.propertiesDock.toggleViewAction())
        viewMenu.addAction(self.independenciesDock.toggleViewAction())
        viewMenu.addAction(self.toolBar.toggleViewAction())
