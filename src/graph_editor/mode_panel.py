import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import QEvent, QSize
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import QFrame, QLayout, QToolButton, QVBoxLayout

import qtawesome as qta

from models.editor_modes import EditorMode


class EditorModePanel(QFrame):
    """Small vertical panel, always shown over the graph view, to pick the mode."""

    ICON_SIZE = 20
    PADDING = 4
    SPACING = 2
    CORNER_RADIUS = 8

    # (mode, label, icon, shortcut, tooltip)
    MODES = [
        (
            EditorMode.NODES,
            "Nodes",
            "mdi6.circle-outline",
            "1",
            "Add nodes by clicking empty space, and drag them around",
        ),
        (
            EditorMode.ARROWS,
            "Arrows",
            "mdi6.ray-start-arrow",
            "2",
            "Click a source node then a target node (or drag between them) "
            "to add or remove an arrow",
        ),
        (
            EditorMode.SELECT,
            "Select",
            "mdi6.book-search-outline",
            "3",
            "Select several nodes by clicking them or dragging a box",
        ),
    ]

    def __init__(self, scene, parent=None):
        super().__init__(parent)
        self.scene = scene
        self.setObjectName("editorModePanel")
        self.setStyleSheet(
            f"#editorModePanel {{ background: palette(window);"
            f" border: 1px solid palette(mid);"
            f" border-radius: {self.CORNER_RADIUS}px; }}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(*[self.PADDING] * 4)
        layout.setSpacing(self.SPACING)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        self.group = QActionGroup(self)
        self.group.setExclusive(True)
        self.modeActions = {}
        for mode, label, _, shortcut, tooltip in self.MODES:
            action = QAction(label, self)
            action.setCheckable(True)
            action.setShortcut(shortcut)
            action.setToolTip(f"{label}: {tooltip} ({shortcut})")
            action.triggered.connect(lambda _, m=mode: self.scene.setMode(m))
            self.group.addAction(action)
            self.modeActions[mode] = action

            button = QToolButton(self)
            button.setAutoRaise(True)
            button.setIconSize(QSize(self.ICON_SIZE, self.ICON_SIZE))
            button.setDefaultAction(action)
            layout.addWidget(button)

        self.setIcons()
        self.scene.modeChanged.connect(self.onModeChanged)
        self.onModeChanged(self.scene.mode)

    def setIcons(self):
        for mode, _, icon, _, _ in self.MODES:
            self.modeActions[mode].setIcon(qta.icon(icon))

    def onModeChanged(self, mode):
        self.modeActions[mode].setChecked(True)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.PaletteChange:
            qta.reset_cache()
            self.setIcons()
        super().changeEvent(event)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    from graph_editor.graph_editor import GraphEditor

    app = QApplication(sys.argv)
    editor = GraphEditor()
    editor.resize(900, 600)
    editor.show()
    sys.exit(app.exec())
