import importlib

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

from models import ui_colors
from models.app_info import APP_NAME, APP_SUBTITLE
from models.var_colors import var_type_color
from models.var_types import VarTypes


class SplashScreen(QSplashScreen):
    WIDTH = 480
    HEIGHT = 260
    BAR_MARGIN = 40
    BAR_TOP = 196
    BAR_HEIGHT = 6

    TITLE_TOP = 70
    TITLE_HEIGHT = 50
    TITLE_FONT_SIZE = 26
    SUBTITLE_TOP = 122
    SUBTITLE_HEIGHT = 24
    SUBTITLE_FONT_SIZE = 10
    MESSAGE_GAP = 10  # space between the progress bar and the message under it
    MESSAGE_HEIGHT = 22
    MESSAGE_FONT_SIZE = 9

    BACKGROUND = QColor(ui_colors.SPLASH_BACKGROUND)
    TITLE_COLOR = QColor(ui_colors.SPLASH_TITLE)
    TEXT_COLOR = QColor(ui_colors.SPLASH_TEXT)
    BAR_BACKGROUND = QColor(ui_colors.SPLASH_BAR_BACKGROUND)
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
        titleFont.setPointSize(self.TITLE_FONT_SIZE)
        titleFont.setBold(True)
        painter.setFont(titleFont)
        painter.setPen(self.TITLE_COLOR)
        painter.drawText(
            QRectF(0, self.TITLE_TOP, self.WIDTH, self.TITLE_HEIGHT),
            Qt.AlignmentFlag.AlignCenter,
            APP_NAME,
        )

        subtitleFont = QFont()
        subtitleFont.setPointSize(self.SUBTITLE_FONT_SIZE)
        painter.setFont(subtitleFont)
        painter.setPen(self.TEXT_COLOR)
        painter.drawText(
            QRectF(0, self.SUBTITLE_TOP, self.WIDTH, self.SUBTITLE_HEIGHT),
            Qt.AlignmentFlag.AlignCenter,
            APP_SUBTITLE,
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
        messageFont.setPointSize(self.MESSAGE_FONT_SIZE)
        painter.setFont(messageFont)
        painter.setPen(self.TEXT_COLOR)
        painter.drawText(
            QRectF(
                bar.x(),
                bar.bottom() + self.MESSAGE_GAP,
                bar.width(),
                self.MESSAGE_HEIGHT,
            ),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            self.message,
        )
