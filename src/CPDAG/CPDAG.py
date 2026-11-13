import networkx as nx

from CPDAG.node import Node
from CPDAG.arrow import Arrow


class CPDAG(nx.DiGraph):
    def __init__(self, incoming_graph_data=None, **attr):
        super().__init__(incoming_graph_data, **attr)

    def has_variable(self, name: str) -> bool:
        return any(node.name == name for node in self.nodes)

    def add_variable(self, node: Node) -> Node:
        if node in self:
            raise ValueError(f"Variable '{node.name}' already exists")
        self.add_node(node)
        return node

    def add_arrow(self, fromNode: Node, toNode: Node, arrow: Arrow | None = None) -> Arrow:
        if fromNode not in self or toNode not in self:
            raise ValueError("Both nodes must be added to the graph first")
        if self.has_edge(fromNode, toNode):
            raise ValueError("Arrow already exists")
        arrow = arrow if arrow is not None else Arrow()
        arrow.attach(fromNode, toNode)
        self.add_edge(fromNode, toNode, arrow=arrow)
        return arrow

    def remove_variable(self, node: Node) -> set[Arrow]:
        arrows = node.arrows()
        for arrow in arrows:
            arrow.detach()
        self.remove_node(node)
        return arrows

    def remove_arrow(self, fromNode: Node, toNode: Node) -> Arrow:
        arrow = self.edges[fromNode, toNode]["arrow"]
        arrow.detach()
        self.remove_edge(fromNode, toNode)
        return arrow
