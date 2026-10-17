from PySide6.QtWidgets import QGraphicsRectItem
from PySide6.QtCore import Qt, Signal, QObject, QPointF


class BackgroundItem(QGraphicsRectItem):
    def __init__(self, comm):
        super().__init__()
        self.comm = comm
        self.setZValue(-100)

    def mousePressEvent(self, event):
        self.comm.background_click.emit(event.button(), event.pos())
        return super().mousePressEvent(event)


class BackgroundSignal(QObject):
    background_click = Signal(Qt.MouseButton, QPointF)
