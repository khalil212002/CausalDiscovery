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
from PySide6.QtGui import QBrush, QPen, QColor
from PySide6.QtCore import Qt
from models.var_types import VarTypes
from graph_editor.node import Node


class GraphEditorScene(QGraphicsScene):

    def __init__(self, comm):
        super().__init__()
        comm.background_click.connect(self.bgItemClickEvent)

    def addNodeDialog(self, pos):
        dialog = AddNodeDialog()
        if dialog.exec():
            self.addNode(pos, dialog.get_name(), dialog.get_type())

    def addNode(self, pos, name, type):
        newNode = Node(name, type, pos)
        self.addItem(newNode)

    def bgItemClickEvent(self, button, pos):
        if button == Qt.MouseButton.LeftButton:
            self.addNodeDialog(pos)


class AddNodeDialog(QDialog):
    def __init__(self):
        super().__init__(None)
        self.setWindowTitle("Add Variable")

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Enter Variable Name:"))
        self.var_name = QLineEdit(self)
        layout.addWidget(self.var_name)

        self.nodeTypesRadios = [(QRadioButton(t), t) for t in VarTypes]
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
