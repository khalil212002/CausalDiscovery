from itertools import combinations

import networkx as nx
from pgmpy.base import DAG, PDAG
from pgmpy.independencies import IndependenceAssertion

from CPDAG.node import Node
from CPDAG.arrow import Arrow
from models.var_types import VarTypes


class CPDAG(nx.DiGraph):
    def __init__(self, incoming_graph_data=None, **attr):
        super().__init__(incoming_graph_data, **attr)

    def has_variable(self, name: str) -> bool:
        return any(node.name == name for node in self.nodes)

    def is_undirected(self, u: Node, v: Node) -> bool:
        return self.has_edge(u, v) and self.has_edge(v, u)

    def directed_edges(self) -> list[tuple[Node, Node]]:
        return [(u, v) for u, v in self.edges if not self.has_edge(v, u)]

    def undirected_edges(self) -> list[tuple[Node, Node]]:
        seen = set()
        result = []
        for u, v in self.edges:
            if self.has_edge(v, u) and (v, u) not in seen:
                seen.add((u, v))
                result.append((u, v))
        return result

    def toCPDAG(self) -> "CPDAG":
        graph = CPDAG()
        nodes = {
            node: graph.add_variable(Node(node.name, node.varType))
            for node in self.nodes
        }
        for u, v in self.edges:
            graph.add_arrow(nodes[u], nodes[v])
        return graph

    def to_pgmpy_dag(self) -> DAG:
        directed = [(u.name, v.name) for u, v in self.directed_edges()]
        undirected = [(u.name, v.name) for u, v in self.undirected_edges()]
        if not nx.is_directed_acyclic_graph(nx.DiGraph(directed)):
            raise ValueError("The graph contains a directed cycle")

        pdag = PDAG(directed_ebunch=directed, undirected_ebunch=undirected)
        pdag.add_nodes_from(node.name for node in self.nodes)
        dag = pdag.to_dag()
        if not nx.is_directed_acyclic_graph(dag) or self._has_new_collider(dag):
            raise ValueError(
                "The undirected edges can't be oriented without creating "
                "a cycle or a new collider"
            )

        def names(varType):
            return {node.name for node in self.nodes if node.varType == varType}

        dag.latents = names(VarTypes.UNOBSERVED)
        dag.exposures = names(VarTypes.EXPOSURE)
        dag.outcomes = names(VarTypes.OUTCOME)
        return dag

    def _has_new_collider(self, dag: DAG) -> bool:
        undirected = {frozenset((u.name, v.name)) for u, v in self.undirected_edges()}
        for child in dag.nodes():
            for a, b in combinations(dag.predecessors(child), 2):
                if dag.has_edge(a, b) or dag.has_edge(b, a):
                    continue
                if (
                    frozenset((a, child)) in undirected
                    or frozenset((b, child)) in undirected
                ):
                    return True
        return False

    def get_CIs(self) -> list[IndependenceAssertion]:
        dag = self.to_pgmpy_dag()
        observed = sorted(node for node in dag.nodes() if node not in dag.latents)
        CIs = []
        for x, y in combinations(observed, 2):
            if dag.has_edge(x, y) or dag.has_edge(y, x):
                continue
            separator = dag.minimal_dseparator(x, y)
            if separator is not None:
                CIs.append(IndependenceAssertion(x, y, sorted(separator)))
        return CIs

    def add_variable(self, node: Node) -> Node:
        if not node.name.strip():
            raise ValueError("Variable name can't be empty")
        if node in self:
            raise ValueError(f"Variable '{node.name}' already exists")
        self.add_node(node)
        return node

    def add_arrow(
        self, fromNode: Node, toNode: Node, arrow: Arrow | None = None
    ) -> Arrow:
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
