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
from PySide6.QtCore import Qt, Signal
from models.arrow_types import ArrowTypes
from models.editor_modes import DEFAULT_EDITOR_MODE, EditorMode
from models.var_types import VarTypes
from graph_editor.graph_node import GraphNode
from graph_editor.graph_arrow import GraphArrow, PreviewArrow


class GraphEditorScene(QGraphicsScene):
    """Graph canvas whose mouse behaviour depends on the current EditorMode.

    - NODES:  click empty space to add a node, drag nodes to move them,
              click a node or an arrow to select it (for the Properties
              panel). Nodes and arrows are never selected together.
    - ARROWS: click a source then a target (or drag from one to the other)
              to add an arrow; doing it again removes the arrow. Ctrl+click
              picks several sources at once. Clicking an arrow selects it.
    - SELECT: click nodes or drag a box to select several of them.
    """

    modeChanged = Signal(object)

    def __init__(self):
        super().__init__()

        self.mode = DEFAULT_EDITOR_MODE
        self.arrowStartNode = None  # node pressed in ARROWS mode
        self.previewArrow = None  # faded arrow shown while dragging an arrow

    def setMode(self, mode):
        if mode is self.mode:
            return
        self.cancelArrowDrag()
        self.clearSelection()
        self.mode = mode
        for item in self.nodes() + self.arrows():
            self.applyMode(item)
        self.modeChanged.emit(mode)

    def applyMode(self, item):
        # Nodes move only in NODES mode; arrows can be selected in NODES and
        # ARROWS modes (SELECT mode picks nodes only)
        if isinstance(item, GraphNode):
            item.setFlag(
                QGraphicsItem.GraphicsItemFlag.ItemIsMovable,
                self.mode is EditorMode.NODES,
            )
        else:
            item.setFlag(
                QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,
                self.mode is not EditorMode.SELECT,
            )

    def nodes(self):
        return [item for item in self.items() if isinstance(item, GraphNode)]

    def arrows(self):
        return [item for item in self.items() if isinstance(item, GraphArrow)]

    def arrowAt(self, pos):
        return next(
            (item for item in self.items(pos) if isinstance(item, GraphArrow)), None
        )

    def nodeAt(self, pos):
        for item in self.items(pos):
            item = item.group() or item.topLevelItem()
            if isinstance(item, GraphNode):
                return item
        return None

    def addNodeDialog(self, pos):
        dialog = AddNodeDialog()
        if dialog.exec():
            self.addNode(pos, dialog.get_name(), dialog.get_type())

    def addNode(self, pos, name, type):
        newNode = GraphNode(name, type, pos)
        self.applyMode(newNode)
        self.addItem(newNode)
        self.clearSelection()
        return newNode

    def deleteNode(self, node):
        if node is self.arrowStartNode:
            self.cancelArrowDrag()
        for arrow in node.arrows():
            self.removeItem(arrow)
        self.removeItem(node)

    def renameNode(self, node, name):
        node.rename(name)

    def setNodeType(self, node, varType):
        node.setVarType(varType)

    def addArrow(self, fromNode, toNode, arrowType=ArrowTypes.USER):
        arr = GraphArrow(arrowType)
        self.applyMode(arr)
        self.addItem(arr)
        return arr

    def setArrowType(self, arrow, arrowType):
        for a in arrow.edgeArrows():
            a.setArrowType(arrowType)

    def setEdgeArrows(self, u, v, pairs):
        """Make the edge between u and v exactly the given (from, to) pairs:
        [(u, v)], [(v, u)] or both for an undirected edge. The edge keeps its
        arrow type. Returns the arrow of the first pair."""
        existing = {
            (a.fromNode, a.toNode): a
            for a in u.arrows()
            if v in (a.fromNode, a.toNode)
        }
        arrowType = (
            next(iter(existing.values())).arrowType if existing else ArrowTypes.USER
        )
        for pair in existing.keys() - set(pairs):
            self.deleteArrow(*pair)
        for pair in pairs:
            if pair not in existing:
                self.addArrow(*pair, arrowType)
        fromNode, toNode = pairs[0]
        return next(a for a in fromNode.outArrows if a.toNode is toNode)

    def deleteEdge(self, arrow):
        for a in arrow.edgeArrows():
            self.deleteArrow(a.fromNode, a.toNode)

    def deleteArrow(self, fromNode, toNode):
        arr = next(a for a in fromNode.outArrows if a.toNode is toNode)
        self.removeItem(arr)
        return arr

    def toggleArrows(self, sources, target):
        for source in sources:
            if source is target:
                continue
            if target in source.toNodes():
                self.deleteArrow(source, target)
            else:
                self.addArrow(source, target)
        self.clearSelection()

    def getSelectedNodes(self):
        return {item for item in self.selectedItems() if isinstance(item, GraphNode)}

    def getSelectedArrows(self):
        return {item for item in self.selectedItems() if isinstance(item, GraphArrow)}

    # --- Mouse handling, routed by mode ---

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        node = self.nodeAt(event.scenePos())
        if self.mode is EditorMode.NODES:
            if node is None:
                arrow = self.arrowAt(event.scenePos())
                self.clearSelection()
                if arrow is not None:
                    arrow.setSelected(True)
                else:
                    self.addNodeDialog(event.scenePos())
                event.accept()
                return
            super().mousePressEvent(event)
            # A node was clicked: drop any selected arrow (e.g. on ctrl+click)
            for arrow in self.getSelectedArrows():
                arrow.setSelected(False)
        elif self.mode is EditorMode.ARROWS:
            self.arrowStartNode = node
            if node is None:
                arrow = self.arrowAt(event.scenePos())
                self.clearSelection()
                if arrow is not None:
                    arrow.setSelected(True)
            event.accept()
        elif self.mode is EditorMode.SELECT:
            if node is None:
                # Left unaccepted so the view starts a rubber band selection
                super().mousePressEvent(event)
                return
            node.setSelected(not node.isSelected())
            event.accept()

    def mouseDoubleClickEvent(self, event):
        # Treat the second click of a double click as a normal press, so fast
        # clicking (e.g. source then target) never loses a click.
        self.mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.mode is EditorMode.ARROWS:
            if self.arrowStartNode is not None:
                self.updatePreviewArrow(event.scenePos())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.mode is not EditorMode.ARROWS:
            super().mouseReleaseEvent(event)
            return

        event.accept()
        start = self.arrowStartNode
        self.cancelArrowDrag()
        end = self.nodeAt(event.scenePos())
        if start is None or end is None:
            return

        # Nodes are being picked: drop a selected arrow so they never mix
        for arrow in self.getSelectedArrows():
            arrow.setSelected(False)
        if end is not start:
            # Dragged from one node to another
            self.toggleArrows({start}, end)
        elif event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            start.setSelected(not start.isSelected())
        else:
            sources = self.getSelectedNodes()
            if start in sources:
                start.setSelected(False)
            elif sources:
                self.toggleArrows(sources, start)
            else:
                start.setSelected(True)

    def updatePreviewArrow(self, pos):
        if self.previewArrow is None:
            # Only show the arrow once the cursor leaves the start node
            if self.nodeAt(pos) is self.arrowStartNode:
                return
            self.previewArrow = PreviewArrow(self.arrowStartNode)
            self.addItem(self.previewArrow)
        self.previewArrow.pointTo(pos)

    def cancelArrowDrag(self):
        self.arrowStartNode = None
        if self.previewArrow is not None:
            self.removeItem(self.previewArrow)
            self.previewArrow = None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            for arrow in self.getSelectedArrows():
                if arrow.isAttached():  # may be gone with its partner already
                    self.deleteEdge(arrow)
            for item in self.getSelectedNodes():
                self.deleteNode(item)
            event.accept()
            return
        elif event.key() == Qt.Key.Key_Escape:
            self.cancelArrowDrag()
            self.clearSelection()
        return super().keyPressEvent(event)


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
