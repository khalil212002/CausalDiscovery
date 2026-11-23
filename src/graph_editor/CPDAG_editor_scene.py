from graph_editor.graph_editor_scene import GraphEditorScene
from CPDAG.CPDAG import CPDAG
import networkx as nx
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QMessageBox
import matplotlib.pyplot as plt
from models import ui_colors
from models.arrow_types import ArrowTypes


class CPDAGEditorScene(GraphEditorScene):
    graphChanged = Signal()

    PLOT_NODE_SIZE = 700

    def __init__(self):
        super().__init__()
        self.cpdag = CPDAG()
        self.plotFigure = None

    def addNode(self, pos, name, type):
        if self.cpdag.has_variable(name):
            QMessageBox.warning(None, "Add Variable", f"'{name}' already exists.")
            return None
        node = super().addNode(pos, name, type)
        self.cpdag.add_variable(node)
        self.graphChanged.emit()
        return node

    def deleteNode(self, node):
        super().deleteNode(node)
        self.cpdag.remove_variable(node)
        self.graphChanged.emit()

    def renameNode(self, node, name):
        try:
            self.cpdag.rename_variable(node, name)
        except ValueError as e:
            QMessageBox.warning(None, "Rename Variable", str(e))
            return
        self.graphChanged.emit()

    def setNodeType(self, node, varType):
        self.cpdag.set_variable_type(node, varType)
        self.graphChanged.emit()

    def addArrow(self, fromNode, toNode, arrowType=ArrowTypes.USER):
        arr = super().addArrow(fromNode, toNode, arrowType)
        self.cpdag.add_arrow(fromNode, toNode, arr)
        self.graphChanged.emit()
        return arr

    def deleteArrow(self, fromNode, toNode):
        arr = super().deleteArrow(fromNode, toNode)
        self.cpdag.remove_arrow(fromNode, toNode)
        self.graphChanged.emit()
        return arr

    def setArrowType(self, arrow, arrowType):
        super().setArrowType(arrow, arrowType)
        self.graphChanged.emit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_G:
            if self.plotFigure is None or not plt.fignum_exists(
                self.plotFigure.number
            ):
                self.plotFigure = plt.figure()
            else:
                self.plotFigure.clear()
            graph = self.cpdag.toCPDAG()
            nx.draw(
                graph,
                nx.spring_layout(graph),
                ax=self.plotFigure.add_subplot(),
                labels={node: node.name for node in graph.nodes},
                node_color=ui_colors.CPDAG_PLOT_NODE,
                node_size=self.PLOT_NODE_SIZE,
                font_weight="bold",
                arrows=True,
            )
            self.plotFigure.canvas.draw_idle()
            plt.show(block=False)
            event.accept()
            return
        super().keyPressEvent(event)
