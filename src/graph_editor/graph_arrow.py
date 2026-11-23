from PySide6.QtWidgets import QGraphicsLineItem
from PySide6.QtCore import QLineF, QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QPen, QPolygonF
import math
from CPDAG.arrow import Arrow
from models import ui_colors


class GraphArrow(Arrow, QGraphicsLineItem):
    ARROW_WIDTH = 2
    ARROW_COLOR = QColor(ui_colors.ARROW)
    ARROW_HEAD_SIZE = 7
    ARROW_HEAD_SPREAD = math.pi / 6  # angle of each wing from the line (30°)
    LINE_EXTENSION = 3  # push the tip slightly into the target node's border

    def __init__(self):
        Arrow.__init__(self)
        QGraphicsLineItem.__init__(self)
        self.setPen(
            QPen(
                self.ARROW_COLOR,
                self.ARROW_WIDTH,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )

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
        padding = self.ARROW_HEAD_SIZE + self.pen().width()
        return rect.adjusted(-padding, -padding, padding, padding)

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

        pen = self.pen()
        pen.setColor(self.ARROW_COLOR)
        painter.setPen(pen)
        painter.setBrush(QBrush(self.ARROW_COLOR))

        # Get line coordinates
        line = self.line()

        partner = self.oppositeArrow()
        if partner is not None:
            if id(partner) < id(self):
                return
            painter.drawLine(line)
            return

        painter.drawLine(line)
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

    def __init__(self, fromNode):
        super().__init__()
        self.fromNode = fromNode
        self.setOpacity(self.OPACITY)
        self.setPen(
            QPen(
                GraphArrow.ARROW_COLOR,
                GraphArrow.ARROW_WIDTH,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )

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
        painter.setBrush(QBrush(GraphArrow.ARROW_COLOR))
        painter.drawLine(line)
        painter.drawPolygon(GraphArrow.arrowHead(line))
