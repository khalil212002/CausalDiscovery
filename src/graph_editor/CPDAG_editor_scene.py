from graph_editor.graph_editor_scene import GraphEditorScene
from CPDAG.CPDAG import CPDAG
import networkx as nx
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox
import matplotlib.pyplot as plt


class CPDAGEditorScene(GraphEditorScene):
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
        return node

    def deleteNode(self, node):
        super().deleteNode(node)
        self.cpdag.remove_variable(node)

    def addArrow(self, fromNode, toNode):
        arr = super().addArrow(fromNode, toNode)
        self.cpdag.add_arrow(fromNode, toNode, arr)
        return arr

    def deleteArrow(self, fromNode, toNode):
        arr = super().deleteArrow(fromNode, toNode)
        self.cpdag.remove_arrow(fromNode, toNode)
        return arr

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
                node_color="lightblue",
                node_size=700,
                font_weight="bold",
                arrows=True,
            )
            self.plotFigure.canvas.draw_idle()
            plt.show(block=False)
            event.accept()
            return
        super().keyPressEvent(event)
