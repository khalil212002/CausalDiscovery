import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGraphicsView, QMainWindow, QApplication
from graph_editor.CPDAG_editor_scene import CPDAGEditorScene
from graph_editor.mode_panel import EditorModePanel
from models.editor_modes import EditorMode
from models.app_info import APP_NAME, MAIN_WINDOW_SIZE


class GraphEditor(QGraphicsView):
    MODE_PANEL_MARGIN = 10  # gap between the floating mode panel and the edges

    def __init__(self):
        super().__init__()

        self.editorScene = CPDAGEditorScene()
        self.setScene(self.editorScene)

        # Parented to the view (not the viewport) so it never scrolls with
        # the scene. The actions also live on the view so the 1/2/3
        # shortcuts work wherever the focus is in the editor.
        self.modePanel = EditorModePanel(self.editorScene, self)
        self.addActions(list(self.modePanel.modeActions.values()))
        self.modePanel.raise_()
        self.editorScene.modeChanged.connect(self.onModeChanged)
        self.onModeChanged(self.editorScene.mode)

    def onModeChanged(self, mode):
        self.setDragMode(
            QGraphicsView.DragMode.RubberBandDrag
            if mode is EditorMode.SELECT
            else QGraphicsView.DragMode.NoDrag
        )
        self.viewport().setCursor(
            Qt.CursorShape.CrossCursor
            if mode is EditorMode.ARROWS
            else Qt.CursorShape.ArrowCursor
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)

        view_size = self.viewport().size()
        width = view_size.width()
        height = view_size.height()

        self.editorScene.setSceneRect(0, 0, width, height)

        corner = self.viewport().geometry().topLeft()
        self.modePanel.move(
            corner.x() + self.MODE_PANEL_MARGIN, corner.y() + self.MODE_PANEL_MARGIN
        )


class GraphEditorTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} - Graph Editor Test")
        self.resize(*MAIN_WINDOW_SIZE)
        self.setCentralWidget(GraphEditor())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GraphEditorTestWindow()
    window.show()
    sys.exit(app.exec())
