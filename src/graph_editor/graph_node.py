from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsItemGroup,
    QGraphicsPathItem,
    QGraphicsSimpleTextItem,
)
from PySide6.QtCore import Qt, QPoint, QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QFont, QPainterPath
from models.var_types import VarTypes
from models import ui_colors
from models.var_colors import var_type_color
from CPDAG.node import Node


class GraphNode(Node, QGraphicsItemGroup):
    # Geometry (local coordinates, origin at the top-left corner)
    MIN_WIDTH = 120  # nodes never shrink below this, even for tiny names
    HEIGHT = 70
    CORNER_RADIUS = 10
    BADGE_HEIGHT = 16
    BADGE_FONT_SIZE = 7  # smaller than the name font
    BADGE_PAD = 5  # horizontal padding inside the badge
    BADGE_INSET = 8  # distance from the badge to the node's top/left edge
    NAME_PAD = 16  # horizontal padding kept around the full name
    NAME_FONT_SIZE = 10
    BORDER_WIDTH = 2

    BODY_FILL = QColor(ui_colors.NODE_BODY_FILL)
    TEXT = QColor(ui_colors.NODE_TEXT)

    # Selection highlight: white ring drawn around the node
    SELECTION_COLOR = QColor(ui_colors.SELECTION_RING)
    SELECTION_HALO = QColor(ui_colors.SELECTION_HALO)
    SELECTION_OUTSET = 4  # how far the ring sits outside the node body

    def __init__(self, name: str, type: VarTypes, pos=QPoint(0, 0), id=None):
        Node.__init__(self, name, type, id)
        QGraphicsItemGroup.__init__(self)

        self.setFlag(QGraphicsItemGroup.ItemIsMovable, True)
        self.setFlag(QGraphicsItemGroup.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setFiltersChildEvents(True)

        # --- Text items (created first, since the node width fits them) ---
        badge_font = QFont()
        badge_font.setBold(True)
        badge_font.setPointSize(self.BADGE_FONT_SIZE)

        self._badge_text = QGraphicsSimpleTextItem(str(type).upper())
        self._badge_text.setFont(badge_font)
        self._badge_text.setBrush(self.TEXT)

        name_font = QFont()
        name_font.setPointSize(self.NAME_FONT_SIZE)
        name_font.setBold(True)

        self._name_text = QGraphicsSimpleTextItem(name)  # full name, never elided
        self._name_text.setFont(name_font)
        self._name_text.setBrush(self.TEXT)

        self.WIDTH = self.MIN_WIDTH  # stretched to fit the name in _layout()

        # --- Body (rounded rectangle) and badge; paths are set in _layout()
        # and type colors in _applyTypeColor() ---
        self._rect = QGraphicsPathItem()
        self._rect.setBrush(self.BODY_FILL)
        self._badge = QGraphicsPathItem()
        self._badge.setPen(QPen(Qt.PenStyle.NoPen))
        self._applyTypeColor()

        # Add sub-items securely to this group instance (bottom to top)
        self.addToGroup(self._rect)
        self.addToGroup(self._badge)
        self.addToGroup(self._badge_text)
        self.addToGroup(self._name_text)
        self._layout()

        # Set the position after parenting, so children keep their local
        # coordinates relative to the group instead of the scene origin.
        # `pos` is the desired center of the node, so offset by half its size.
        self.setPos(QPointF(pos) - QPointF(self.WIDTH / 2, self.HEIGHT / 2))

    def _applyTypeColor(self):
        # Border and badge both use the node's type color
        color = QColor(var_type_color(self.varType))
        self._rect.setPen(QPen(color, self.BORDER_WIDTH))
        self._badge.setBrush(color)

    def _layout(self):
        # Badge inside the top-left of the body, sized to its text
        badge_width = self._badge_text.boundingRect().width() + 2 * self.BADGE_PAD
        badge_rect = QRectF(
            self.BADGE_INSET, self.BADGE_INSET, badge_width, self.BADGE_HEIGHT
        )
        badge_path = QPainterPath()
        badge_path.addRoundedRect(
            badge_rect, self.CORNER_RADIUS // 2, self.CORNER_RADIUS // 2
        )
        self._badge.setPath(badge_path)
        self._badge_text.setPos(
            badge_rect.left() + self.BADGE_PAD,
            badge_rect.top()
            + (self.BADGE_HEIGHT - self._badge_text.boundingRect().height()) / 2,
        )

        # Stretch the width to always fit the full name and the badge, then
        # center the name in the body.
        self.prepareGeometryChange()
        self.WIDTH = max(
            self.MIN_WIDTH,
            badge_width + 2 * self.BADGE_INSET,
            self._name_text.boundingRect().width() + 2 * self.NAME_PAD,
        )

        body_path = QPainterPath()
        body_path.addRoundedRect(
            QRectF(0, 0, self.WIDTH, self.HEIGHT),
            self.CORNER_RADIUS,
            self.CORNER_RADIUS,
        )
        self._rect.setPath(body_path)

        name_text_rect = self._name_text.boundingRect()
        self._name_text.setPos(
            (self.WIDTH - name_text_rect.width()) / 2,
            (self.HEIGHT - name_text_rect.height()) / 2,
        )

    def rename(self, name: str):
        super().rename(name)
        self._name_text.setText(name)
        self._relayoutCentered()

    def setVarType(self, varType: VarTypes):
        super().setVarType(varType)
        self._badge_text.setText(str(varType).upper())
        self._applyTypeColor()
        self._relayoutCentered()

    def _relayoutCentered(self):
        # Keep the node centered where it was while its width changes
        center = self.pos() + QPointF(self.WIDTH / 2, self.HEIGHT / 2)
        self._layout()
        self.setPos(center - QPointF(self.WIDTH / 2, self.HEIGHT / 2))
        for arrow in self.arrows():
            arrow.update_position()

    def boundingRect(self):
        # Computed from the body instead of the group's cached children rect,
        # which doesn't follow renames. The margin keeps the selection ring,
        # drawn slightly outside the body, inside scene updates.
        margin = self.SELECTION_OUTSET + 1
        return QRectF(0, 0, self.WIDTH, self.HEIGHT).adjusted(
            -margin, -margin, margin, margin
        )

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for arrow in self.arrows():
                arrow.update_position()
        return super().itemChange(change, value)

    def paint(self, painter, option, widget=None):
        # Note: intentionally NOT calling QGraphicsItemGroup.paint() here. Qt's
        # default group paint draws a plain square around itemsBoundingRect when
        # the group is selected (in the ambient pen color, which shows up as a
        # white square on a dark palette). We draw our own rounded ring instead.

        # Draw a rounded highlight ring around the node if it is selected
        if self.isSelected():
            ring_rect = QRectF(0, 0, self.WIDTH, self.HEIGHT).adjusted(
                -self.SELECTION_OUTSET,
                -self.SELECTION_OUTSET,
                self.SELECTION_OUTSET,
                self.SELECTION_OUTSET,
            )
            radius = self.CORNER_RADIUS + self.SELECTION_OUTSET
            ring_path = QPainterPath()
            ring_path.addRoundedRect(ring_rect, radius, radius)

            painter.setPen(QPen(self.SELECTION_COLOR, 1, Qt.PenStyle.DashLine))
            painter.setBrush(self.SELECTION_HALO)
            painter.drawPath(ring_path)
