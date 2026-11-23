from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from models.var_types import VarTypes

if TYPE_CHECKING:
    from CPDAG.arrow import Arrow


class Node:
    # A node is identified by its id, not its name, so the name can change
    # while the node is a key in the graph. Pass `id` when loading a project.
    def __init__(self, name: str, varType: VarTypes, id: str | None = None):
        self.id = id if id is not None else uuid.uuid4().hex
        self.name = name
        self.varType = varType
        self.inArrows: set[Arrow] = set()
        self.outArrows: set[Arrow] = set()

    def __eq__(self, value):
        if not isinstance(value, Node):
            return NotImplemented
        return value.id == self.id

    def __hash__(self):
        return hash(self.id)

    def rename(self, name: str):
        self.name = name

    def toNodes(self) -> set[Node]:
        return {arrow.toNode for arrow in self.outArrows}

    def fromNodes(self) -> set[Node]:
        return {arrow.fromNode for arrow in self.inArrows}

    def arrows(self) -> set[Arrow]:
        return self.inArrows | self.outArrows
