from PySide6.QtWidgets import QGraphicsItem, QGraphicsView, QMainWindow, QApplication
from graph_editor.background_item import BackgroundItem, BackgroundSignal
from graph_editor.graph_editor_scene import GraphEditorScene
from PySide6.QtCore import Qt
import sys


class GraphEditor(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.backgroundSignal = BackgroundSignal()
        self.scene = GraphEditorScene(self.backgroundSignal)
        self.setScene(self.scene)

        self.bg_item = BackgroundItem(self.backgroundSignal)
        self.scene.addItem(self.bg_item)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        view_size = self.viewport().size()
        width = view_size.width()
        height = view_size.height()

        self.scene.setSceneRect(0, 0, width, height)
        self.bg_item.setRect(0, 0, width, height)

    def keyPressEvent(self, event):
        # Delete Item
        if event.key() == Qt.Key.Key_Delete:
            for item in self.scene.selectedItems():
                selectedItem = item.group() if item.group() else item
                self.scene.removeItem(selectedItem)
            event.accept()
            return
        return super().keyPressEvent(event)

    def mousePressEvent(self, event):
        # Deselect on second click
        item = self.itemAt(event.position().toPoint())
        item = item.group() if item.group() else item
        if item:
            is_selectable = (
                QGraphicsItem.GraphicsItemFlag.ItemIsSelectable in item.flags()
            )
            if is_selectable and item.isSelected():
                item.setSelected(False)
                event.accept()
                return

        super().mousePressEvent(event)


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
