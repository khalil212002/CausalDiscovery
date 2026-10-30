from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsScene,
    QDialog,
    QLabel,
    QVBoxLayout,
    QLineEdit,
    QDialogButtonBox,
    QRadioButton,
    QHBoxLayout,
    QGraphicsRectItem,
)
from PySide6.QtGui import QBrush, QPen, QColor, QTransform
from PySide6.QtCore import QPoint, QTimer, Qt
from models.var_types import VarTypes
from graph_editor.node import Node
from graph_editor.arrow import Arrow


class GraphEditorScene(QGraphicsScene):

    def __init__(self):
        super().__init__()

        self.prevSelection = set()
        self.selectionChanged.connect(self.itemSelected)

    def addNodeDialog(self, pos):
        dialog = AddNodeDialog()
        if dialog.exec():
            self.addNode(pos, dialog.get_name(), dialog.get_type())

    def addNode(self, pos, name, type):
        newNode = Node(name, type, pos)
        self.addItem(newNode)
        self.prevSelection = set()
        self.clearSelection()

    def mousePressEvent(self, event):
        self.prevPressPos = event.scenePos()
        transform = transform = (
            self.views()[0].transform() if self.views() else QTransform()
        )

        item = self.itemAt(event.scenePos(), transform)
        if item:
            item = item.group() or item.topLevelItem()
            is_selectable = (
                QGraphicsItem.GraphicsItemFlag.ItemIsSelectable in item.flags()
            )
            if is_selectable and item.isSelected():
                item.setSelected(False)
                event.accept()
                return
        else:
            if event.button() == Qt.MouseButton.LeftButton:
                self.addNodeDialog(event.scenePos())
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.scenePos() != self.prevPressPos:
            self.clearSelection()
        return super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        # Delete Item
        if event.key() == Qt.Key.Key_Delete:
            for item in self.getSelectedNodes():
                # delete node's arrows
                for arrow in set(item.arrows):
                    arrow.detach()
                    self.removeItem(arrow)
                self.prevSelection = self.getSelectedNodes() - set([item])
                self.removeItem(item)
            event.accept()
            return
        elif event.key() == Qt.Key.Key_Escape:
            self.clearSelection()
            self.prevSelection = self.getSelectedNodes()
        return super().keyPressEvent(event)

    def getSelectedNodes(self):
        return set([item for item in self.selectedItems() if isinstance(item, Node)])

    def itemSelected(self):
        # add arrow
        newSelection = self.getSelectedNodes()
        if newSelection and not (newSelection & self.prevSelection):
            for fromItem in self.prevSelection:
                for toItem in newSelection:
                    if (
                        toItem not in fromItem.toNodes()
                        and fromItem not in toItem.fromNodes()
                    ):
                        arr = Arrow(fromItem, toItem)
                        self.addItem(arr)

                    else:
                        arr = [
                            arr for arr in toItem.arrows if arr.from_node == fromItem
                        ][0]
                        arr.detach()
                        self.removeItem(arr)
        self.prevSelection = newSelection


class AddNodeDialog(QDialog):
    def __init__(self):
        super().__init__(None)
        self.setWindowTitle("Add Variable")

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Enter Variable Name:"))
        self.var_name = QLineEdit(self)
        layout.addWidget(self.var_name)

        self.nodeTypesRadios = [(QRadioButton(t.name), t) for t in VarTypes]
        self.nodeTypesRadiosLayout = QHBoxLayout()
        for n in self.nodeTypesRadios:
            self.nodeTypesRadiosLayout.addWidget(n[0])
        self.nodeTypesRadios[0][0].setChecked(True)
        layout.addLayout(self.nodeTypesRadiosLayout)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(buttons)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

    def get_name(self):
        return self.var_name.text()

    def get_type(self):
        return next((n[1] for n in self.nodeTypesRadios if n[0].isChecked()), None)
