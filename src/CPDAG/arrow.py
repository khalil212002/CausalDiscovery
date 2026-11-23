from __future__ import annotations

from typing import TYPE_CHECKING

from models.arrow_types import ArrowTypes

if TYPE_CHECKING:
    from CPDAG.node import Node


class Arrow:
    def __init__(self, arrowType: ArrowTypes = ArrowTypes.USER):
        self.arrowType = arrowType
        self.fromNode: Node | None = None
        self.toNode: Node | None = None

    def setArrowType(self, arrowType: ArrowTypes):
        self.arrowType = arrowType

    def isAttached(self) -> bool:
        return self.fromNode is not None and self.toNode is not None

    def oppositeArrow(self) -> Arrow | None:
        if not self.isAttached():
            return None
        return next(
            (a for a in self.toNode.outArrows if a.toNode is self.fromNode), None
        )

    def isUndirected(self) -> bool:
        return self.oppositeArrow() is not None

    def attach(self, fromNode: Node, toNode: Node):
        self.fromNode = fromNode
        self.toNode = toNode
        fromNode.outArrows.add(self)
        toNode.inArrows.add(self)

    def detach(self):
        self.fromNode.outArrows.discard(self)
        self.toNode.inArrows.discard(self)
