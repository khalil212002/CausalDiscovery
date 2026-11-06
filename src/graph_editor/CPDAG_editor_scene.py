from graph_editor.graph_editor_scene import GraphEditorScene
import networkx as nx
from PySide6.QtCore import Qt
import matplotlib.pyplot as plt


class CPDAGEditorScene(GraphEditorScene):
    def __init__(self):
        super().__init__()
        self.graph = nx.DiGraph()

    def addNode(self, pos, name, type):
        id = super().addNode(pos, name, type)
        self.graph.add_node(id)

    def deleteNode(self, node):
        super().deleteNode(node)
        self.graph.remove_node(node.id)

    def addArrow(self, fromNode, toNode):
        super().addArrow(fromNode, toNode)
        self.graph.add_edge(fromNode.id, toNode.id)

    def deleteArrow(self, fromNode, toNode):
        super().deleteArrow(fromNode, toNode)
        self.graph.remove_edge(fromNode.id, toNode.id)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_G:
            nx.draw(
                self.graph,
                nx.spring_layout(self.graph),
                with_labels=True,
                node_color="lightblue",
                node_size=700,
                font_weight="bold",
                arrows=True,
            )
            plt.exec()
            event.accept()
            return
        super().keyPressEvent(event)

    def getGraph(self):
        return self.graph
