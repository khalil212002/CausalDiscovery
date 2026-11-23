from PySide6.QtWidgets import QGraphicsItem, QGraphicsLineItem
from PySide6.QtCore import QLineF, QPointF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QPainterPath,
    QPainterPathStroker,
    QPen,
    QPolygonF,
)
import math
from CPDAG.arrow import Arrow
from models.arrow_types import ArrowTypes
from models.arrow_colors import (
    DASHED_ARROW_TYPES,
    SELECTED_ARROW_COLOR,
    arrow_type_color,
)


def arrow_pen(color, width, dashed=False):
    return QPen(
        QColor(color),
        width,
        Qt.PenStyle.DashLine if dashed else Qt.PenStyle.SolidLine,
        Qt.PenCapStyle.RoundCap,
        Qt.PenJoinStyle.RoundJoin,
    )


class GraphArrow(Arrow, QGraphicsLineItem):
    ARROW_WIDTH = 2
    SELECTED_WIDTH = 3
    CLICK_WIDTH = 10  # width of the clickable area around the line
    ARROW_HEAD_SIZE = 7
    ARROW_HEAD_SPREAD = math.pi / 6  # angle of each wing from the line (30°)
    LINE_EXTENSION = 3  # push the tip slightly into the target node's border

    def __init__(self, arrowType: ArrowTypes = ArrowTypes.USER):
        Arrow.__init__(self, arrowType)
        QGraphicsLineItem.__init__(self)
        self.setPen(arrow_pen(arrow_type_color(arrowType), self.ARROW_WIDTH))

    def setArrowType(self, arrowType: ArrowTypes):
        super().setArrowType(arrowType)
        self.update()

    def edgeArrows(self):
        """This arrow plus its opposite one when the edge is undirected."""
        partner = self.oppositeArrow()
        return [self] if partner is None else [self, partner]

    def isEdgeSelected(self):
        return any(arrow.isSelected() for arrow in self.edgeArrows())

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            # Only one arrow of an undirected pair paints the shared line
            partner = self.oppositeArrow()
            if partner is not None:
                partner.update()
        return super().itemChange(change, value)

    def attach(self, fromNode, toNode):
        super().attach(fromNode, toNode)
        self.update_position()
        partner = self.oppositeArrow()
        if partner is not None:
            partner.update()

    def detach(self):
        partner = self.oppositeArrow()
        super().detach()
        if partner is not None:
            partner.update()

    def boundingRect(self):
        # Start with the basic box containing just the line line
        rect = super().boundingRect()

        # Expand the rectangle in all directions by the size of the arrowhead plus pen width
        # This ensures the arrowhead is completely enclosed in the update region
        padding = self.ARROW_HEAD_SIZE + max(self.SELECTED_WIDTH, self.CLICK_WIDTH)
        return rect.adjusted(-padding, -padding, padding, padding)

    def shape(self):
        # A wider band than the drawn line, so the arrow is easy to click
        path = QPainterPath(self.line().p1())
        path.lineTo(self.line().p2())
        stroker = QPainterPathStroker()
        stroker.setWidth(self.CLICK_WIDTH)
        return stroker.createStroke(path)

    @staticmethod
    def find_rect_intersection(center_line, rect):
        # Break the combined group bounding box into 4 edge lines
        top_wall = QLineF(rect.topLeft(), rect.topRight())
        bottom_wall = QLineF(rect.bottomLeft(), rect.bottomRight())
        left_wall = QLineF(rect.topLeft(), rect.bottomLeft())
        right_wall = QLineF(rect.topRight(), rect.bottomRight())

        walls = [top_wall, bottom_wall, left_wall, right_wall]
        intersect_point = QPointF()

        for wall in walls:
            intersect_type, intersect_point = center_line.intersects(wall)
            if intersect_type == QLineF.IntersectionType.BoundedIntersection:
                return intersect_point

        return None

    def update_position(self):
        if not self.isAttached():
            return
        c1 = self.fromNode.sceneBoundingRect().center()
        c2 = self.toNode.sceneBoundingRect().center()
        center_line = QLineF(c1, c2)

        # Get full scene-space rectangles enclosing all contents inside the groups
        rect1 = self.fromNode.sceneBoundingRect()
        rect2 = self.toNode.sceneBoundingRect()

        p1 = self.find_rect_intersection(center_line, rect1)
        p2 = self.find_rect_intersection(center_line, rect2)

        if not p1:
            p1 = c1
        if not p2:
            p2 = c2

        line = QLineF(p1, p2)
        line.setLength(line.length() + self.LINE_EXTENSION)
        self.setLine(line)

    def paint(self, painter, option, /, widget=...):
        if not self.isAttached() or self.fromNode.collidesWithItem(self.toNode):
            return

        selected = self.isEdgeSelected()
        color = (
            SELECTED_ARROW_COLOR if selected else arrow_type_color(self.arrowType)
        )
        width = self.SELECTED_WIDTH if selected else self.ARROW_WIDTH
        dashed = self.arrowType in DASHED_ARROW_TYPES
        painter.setPen(arrow_pen(color, width, dashed))
        painter.setBrush(QBrush(QColor(color)))

        # Get line coordinates
        line = self.line()

        partner = self.oppositeArrow()
        if partner is not None:
            if id(partner) < id(self):
                return
            painter.drawLine(line)
            return

        painter.drawLine(line)
        # The head stays solid, even on a dashed arrow
        painter.setPen(arrow_pen(color, width))
        painter.drawPolygon(self.arrowHead(line))

    @classmethod
    def arrowHead(cls, line):
        # Wings spread ARROW_HEAD_SPREAD on either side of the backward
        # direction (angle + pi), in screen space (Y down)
        angle = math.atan2(line.dy(), line.dx())
        wings = [
            line.p2()
            + QPointF(
                math.cos(angle + math.pi + side * cls.ARROW_HEAD_SPREAD)
                * cls.ARROW_HEAD_SIZE,
                math.sin(angle + math.pi + side * cls.ARROW_HEAD_SPREAD)
                * cls.ARROW_HEAD_SIZE,
            )
            for side in (1, -1)
        ]
        return QPolygonF([line.p2(), *wings])


class PreviewArrow(QGraphicsLineItem):
    """Faded arrow following the cursor while an arrow is being dragged."""

    OPACITY = 0.45
    COLOR = arrow_type_color(ArrowTypes.USER)  # new arrows are always user arrows

    def __init__(self, fromNode):
        super().__init__()
        self.fromNode = fromNode
        self.setOpacity(self.OPACITY)
        self.setPen(arrow_pen(self.COLOR, GraphArrow.ARROW_WIDTH))

    def pointTo(self, pos):
        # Start on the source node's border, like a real arrow
        rect = self.fromNode.sceneBoundingRect()
        center_line = QLineF(rect.center(), pos)
        start = GraphArrow.find_rect_intersection(center_line, rect)
        self.setLine(QLineF(start or rect.center(), pos))

    def boundingRect(self):
        padding = GraphArrow.ARROW_HEAD_SIZE + self.pen().width()
        return super().boundingRect().adjusted(-padding, -padding, padding, padding)

    def paint(self, painter, option, /, widget=...):
        line = self.line()
        if line.isNull():
            return
        painter.setPen(self.pen())
        painter.setBrush(QBrush(QColor(self.COLOR)))
        painter.drawLine(line)
        painter.drawPolygon(GraphArrow.arrowHead(line))
