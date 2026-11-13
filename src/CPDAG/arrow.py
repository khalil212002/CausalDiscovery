from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from CPDAG.node import Node


class Arrow:
    def __init__(self):
        self.fromNode: Node | None = None
        self.toNode: Node | None = None

    def isAttached(self) -> bool:
        return self.fromNode is not None and self.toNode is not None

    def attach(self, fromNode: Node, toNode: Node):
        self.fromNode = fromNode
        self.toNode = toNode
        fromNode.outArrows.add(self)
        toNode.inArrows.add(self)

    def detach(self):
        self.fromNode.outArrows.discard(self)
        self.toNode.inArrows.discard(self)
