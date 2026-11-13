import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QGraphicsView, QMainWindow, QApplication
from graph_editor.CPDAG_editor_scene import CPDAGEditorScene


class GraphEditor(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.editorScene = CPDAGEditorScene()
        self.setScene(self.editorScene)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        view_size = self.viewport().size()
        width = view_size.width()
        height = view_size.height()

        self.editorScene.setSceneRect(0, 0, width, height)


class GraphEditorTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Causalitty - Graph Editor Test")
        self.resize(1200, 800)
        self.setCentralWidget(GraphEditor())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GraphEditorTestWindow()
    window.show()
    sys.exit(app.exec())
