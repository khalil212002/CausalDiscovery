from graph_editor.graph_editor_scene import GraphEditorScene
from CPDAG.CPDAG import CPDAG
import networkx as nx
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox
import matplotlib.pyplot as plt


class CPDAGEditorScene(GraphEditorScene, CPDAG):
    def __init__(self):
        GraphEditorScene.__init__(self)
        CPDAG.__init__(self)

    def addNode(self, pos, name, type):
        if self.has_variable(name):
            QMessageBox.warning(None, "Add Variable", f"'{name}' already exists.")
            return None
        node = super().addNode(pos, name, type)
        self.add_variable(node)
        return node

    def deleteNode(self, node):
        super().deleteNode(node)
        self.remove_variable(node)

    def addArrow(self, fromNode, toNode):
        arr = super().addArrow(fromNode, toNode)
        self.add_arrow(fromNode, toNode, arr)
        return arr

    def deleteArrow(self, fromNode, toNode):
        super().deleteArrow(fromNode, toNode)
        self.remove_arrow(fromNode, toNode)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_G:
            plt.figure()
            nx.draw(
                self,
                nx.spring_layout(self),
                labels={node: node.name for node in self.nodes},
                node_color="lightblue",
                node_size=700,
                font_weight="bold",
                arrows=True,
            )
            plt.show(block=False)
            event.accept()
            return
        super().keyPressEvent(event)
