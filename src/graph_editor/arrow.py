from PySide6.QtWidgets import QGraphicsLineItem
from PySide6.QtCore import QLineF, QPointF, Qt
from PySide6.QtGui import QBrush, QPen, QPolygonF
import math


class Arrow(QGraphicsLineItem):
    ARROW_WIDTH = 2
    ARROW_COLOR = Qt.GlobalColor.gray
    ARROW_HEAD_SIZE = 7

    def __init__(self, from_node, to_node):
        super().__init__()

        self.from_node = from_node
        self.to_node = to_node
        self.from_node.arrows.add(self)
        self.to_node.arrows.add(self)

        self.update_position()
        self.setPen(
            QPen(
                self.ARROW_COLOR,
                self.ARROW_WIDTH,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )

    def detach(self):
        self.from_node.arrows.remove(self)
        self.to_node.arrows.remove(self)

    def boundingRect(self):
        # Start with the basic box containing just the line line
        rect = super().boundingRect()

        # Expand the rectangle in all directions by the size of the arrowhead plus pen width
        # This ensures the arrowhead is completely enclosed in the update region
        padding = self.ARROW_HEAD_SIZE + self.pen().width()
        return rect.adjusted(-padding, -padding, padding, padding)

    def find_rect_intersection(self, center_line, rect):
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
        c1 = self.from_node.sceneBoundingRect().center()
        c2 = self.to_node.sceneBoundingRect().center()
        center_line = QLineF(c1, c2)

        # Get full scene-space rectangles enclosing all contents inside the groups
        rect1 = self.from_node.sceneBoundingRect()
        rect2 = self.to_node.sceneBoundingRect()

        p1 = self.find_rect_intersection(center_line, rect1)
        p2 = self.find_rect_intersection(center_line, rect2)

        if not p1:
            p1 = c1
        if not p2:
            p2 = c2

        line = QLineF(p1, p2)
        line.setLength(line.length() + 3)
        self.setLine(line)

    def paint(self, painter, option, /, widget=...):
        if self.from_node.collidesWithItem(self.to_node):
            return

        pen = self.pen()
        pen.setColor(self.ARROW_COLOR)
        painter.setPen(pen)
        painter.setBrush(QBrush(self.ARROW_COLOR))

        # Get line coordinates
        line = self.line()

        # Calculate angle of the line
        # Calculate the base trajectory angle of the line
        angle = math.atan2(line.dy(), line.dx())

        # Corrected arrowhead wing offsets for screen-space geometry (Y down)
        # Using 30 degrees (pi / 6) spread on either side of the backward vector (angle + pi)
        arrow_p1 = line.p2() + QPointF(
            math.cos(angle + math.pi + math.pi / 6) * self.ARROW_HEAD_SIZE,
            math.sin(angle + math.pi + math.pi / 6) * self.ARROW_HEAD_SIZE,
        )
        arrow_p2 = line.p2() + QPointF(
            math.cos(angle + math.pi - math.pi / 6) * self.ARROW_HEAD_SIZE,
            math.sin(angle + math.pi - math.pi / 6) * self.ARROW_HEAD_SIZE,
        )

        arrow_head = QPolygonF([line.p2(), arrow_p1, arrow_p2])

        # Draw the line and the arrowhead polygon
        painter.drawLine(line)
        painter.drawPolygon(arrow_head)
