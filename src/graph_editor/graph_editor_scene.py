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
)
from PySide6.QtGui import QTransform
from PySide6.QtCore import Qt
from models.var_types import VarTypes
from graph_editor.graph_node import GraphNode
from graph_editor.graph_arrow import GraphArrow


class GraphEditorScene(QGraphicsScene):

    def __init__(self):
        super().__init__()

        self.prevSelection = set()
        self.prevPressPos = None
        self.pressedSelectedItem = None

    def addNodeDialog(self, pos):
        dialog = AddNodeDialog()
        if dialog.exec():
            self.addNode(pos, dialog.get_name(), dialog.get_type())

    def addNode(self, pos, name, type):
        newNode = GraphNode(name, type, pos)
        self.addItem(newNode)
        self.prevSelection = set()
        self.clearSelection()
        return newNode

    def deleteNode(self, node):
        for arrow in node.arrows():
            self.removeItem(arrow)
        self.prevSelection = self.getSelectedNodes() - set([node])
        self.removeItem(node)

    def addArrow(self, fromNode, toNode):
        arr = GraphArrow()
        self.addItem(arr)
        return arr

    def deleteArrow(self, fromNode, toNode):
        arr = next(a for a in fromNode.outArrows if a.toNode is toNode)
        self.removeItem(arr)
        return arr

    def mousePressEvent(self, event):
        self.prevPressPos = event.scenePos()
        transform = (
            self.views()[0].transform() if self.views() else QTransform()
        )

        item = self.itemAt(event.scenePos(), transform)
        if item:
            item = item.group() or item.topLevelItem()
            is_selectable = (
                QGraphicsItem.GraphicsItemFlag.ItemIsSelectable in item.flags()
            )
            if is_selectable and item.isSelected():
                self.pressedSelectedItem = item
        else:
            if event.button() == Qt.MouseButton.LeftButton:
                self.addNodeDialog(event.scenePos())
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.scenePos() != self.prevPressPos:
            self.clearSelection()
            self.prevSelection = set()
        elif self.pressedSelectedItem is not None:
            self.pressedSelectedItem.setSelected(False)
            self.prevSelection = self.getSelectedNodes()
        else:
            self.itemSelected()
        self.pressedSelectedItem = None

    def keyPressEvent(self, event):
        # Delete Item
        if event.key() == Qt.Key.Key_Delete:
            for item in self.getSelectedNodes():
                self.deleteNode(item)
            event.accept()
            return
        elif event.key() == Qt.Key.Key_Escape:
            self.clearSelection()
            self.prevSelection = self.getSelectedNodes()
        return super().keyPressEvent(event)

    def getSelectedNodes(self):
        return set(
            [item for item in self.selectedItems() if isinstance(item, GraphNode)]
        )

    def itemSelected(self):
        # add arrow
        newSelection = self.getSelectedNodes()
        if (
            newSelection
            and self.prevSelection
            and not (newSelection & self.prevSelection)
        ):
            for fromItem in self.prevSelection:
                for toItem in newSelection:
                    if toItem not in fromItem.toNodes():
                        self.addArrow(fromItem, toItem)
                    else:
                        self.deleteArrow(fromItem, toItem)
            self.clearSelection()
            self.prevSelection = set()
            return
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

        self.okButton = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self.okButton.setEnabled(False)
        self.var_name.textChanged.connect(
            lambda: self.okButton.setEnabled(bool(self.get_name()))
        )

    def get_name(self):
        return self.var_name.text().strip()

    def get_type(self):
        return next((n[1] for n in self.nodeTypesRadios if n[0].isChecked()), None)
