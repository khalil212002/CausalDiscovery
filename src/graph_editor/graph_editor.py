import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGraphicsView, QMainWindow, QApplication
from graph_editor.CPDAG_editor_scene import CPDAGEditorScene
from models.editor_modes import EditorMode
from models.app_info import APP_NAME, MAIN_WINDOW_SIZE


class GraphEditor(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.editorScene = CPDAGEditorScene()
        self.setScene(self.editorScene)

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
