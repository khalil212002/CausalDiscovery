from __future__ import annotations

from typing import TYPE_CHECKING

from models.var_types import VarTypes

if TYPE_CHECKING:
    from CPDAG.arrow import Arrow


class Node:
    def __init__(self, name: str, varType: VarTypes):
        self.name = name
        self.varType = varType
        self.inArrows: set[Arrow] = set()
        self.outArrows: set[Arrow] = set()

    def __eq__(self, value):
        if not isinstance(value, Node):
            return NotImplemented
        return value.name == self.name

    def __hash__(self):
        return hash(self.name)

    def toNodes(self) -> set[Node]:
        return {arrow.toNode for arrow in self.outArrows}

    def fromNodes(self) -> set[Node]:
        return {arrow.fromNode for arrow in self.inArrows}

    def arrows(self) -> set[Arrow]:
        return self.inArrows | self.outArrows
