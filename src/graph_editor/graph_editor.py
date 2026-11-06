from PySide6.QtWidgets import QGraphicsView, QMainWindow, QApplication
from graph_editor.CPDAG_editor_scene import CPDAGEditorScene
import sys


class GraphEditor(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.scene = CPDAGEditorScene()
        self.setScene(self.scene)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        view_size = self.viewport().size()
        width = view_size.width()
        height = view_size.height()

        self.scene.setSceneRect(0, 0, width, height)


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
