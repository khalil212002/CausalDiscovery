import importlib

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

from models.var_colors import var_type_color
from models.var_types import VarTypes


class SplashScreen(QSplashScreen):
    WIDTH = 480
    HEIGHT = 260
    BAR_MARGIN = 40
    BAR_TOP = 196
    BAR_HEIGHT = 6

    BACKGROUND = QColor("#1e1f22")
    TITLE_COLOR = QColor("#e6e6e6")
    TEXT_COLOR = QColor("#9aa0a6")
    BAR_BACKGROUND = QColor("#3a3c40")
    BAR_COLOR = QColor(var_type_color(VarTypes.OUTCOME))

    def __init__(self):
        super().__init__(self._createPixmap())
        self.progress = 0.0
        self.message = ""

    def _createPixmap(self) -> QPixmap:
        ratio = QApplication.primaryScreen().devicePixelRatio()
        pixmap = QPixmap(int(self.WIDTH * ratio), int(self.HEIGHT * ratio))
        pixmap.setDevicePixelRatio(ratio)
        pixmap.fill(self.BACKGROUND)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        titleFont = QFont()
        titleFont.setPointSize(26)
        titleFont.setBold(True)
        painter.setFont(titleFont)
        painter.setPen(self.TITLE_COLOR)
        painter.drawText(
            QRectF(0, 70, self.WIDTH, 50), Qt.AlignmentFlag.AlignCenter, "Causalitty"
        )

        subtitleFont = QFont()
        subtitleFont.setPointSize(10)
        painter.setFont(subtitleFont)
        painter.setPen(self.TEXT_COLOR)
        painter.drawText(
            QRectF(0, 122, self.WIDTH, 24),
            Qt.AlignmentFlag.AlignCenter,
            "Causal discovery",
        )
        painter.end()
        return pixmap

    def load(self, steps: list[tuple[str, str]]):
        for index, (message, module) in enumerate(steps):
            self.message = message
            self.progress = index / len(steps)
            self.repaint()
            QApplication.processEvents()
            importlib.import_module(module)
        self.progress = 1.0
        self.repaint()
        QApplication.processEvents()

    def drawContents(self, painter: QPainter):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bar = QRectF(
            self.BAR_MARGIN,
            self.BAR_TOP,
            self.WIDTH - 2 * self.BAR_MARGIN,
            self.BAR_HEIGHT,
        )
        radius = self.BAR_HEIGHT / 2

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self.BAR_BACKGROUND)
        painter.drawRoundedRect(bar, radius, radius)

        if self.progress > 0:
            filled = QRectF(bar.x(), bar.y(), bar.width() * self.progress, bar.height())
            painter.setBrush(self.BAR_COLOR)
            painter.drawRoundedRect(filled, radius, radius)

        messageFont = QFont()
        messageFont.setPointSize(9)
        painter.setFont(messageFont)
        painter.setPen(self.TEXT_COLOR)
        painter.drawText(
            QRectF(bar.x(), bar.bottom() + 10, bar.width(), 22),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            self.message,
        )
