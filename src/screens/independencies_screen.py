from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLabel, QListWidget, QVBoxLayout, QWidget


class IndependenciesScreen(QWidget):
    REFRESH_DELAY_MS = 200

    def __init__(self, scene, parent=None):
        super().__init__(parent)
        self.scene = scene

        layout = QVBoxLayout(self)
        self.status = QLabel(self)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.list = QListWidget(self)
        layout.addWidget(self.list)

        self.debouncer = QTimer(self)
        self.debouncer.setSingleShot(True)
        self.debouncer.setInterval(self.REFRESH_DELAY_MS)
        self.debouncer.timeout.connect(self.refresh)
        self.scene.graphChanged.connect(self.debouncer.start)

        self.refresh()

    def refresh(self):
        self.list.clear()
        if len(self.scene.cpdag) == 0:
            self.status.setText(
                "Add variables to see their conditional independencies."
            )
            return
        try:
            independencies = self.scene.cpdag.toCPDAG().get_CIs()
        except ValueError as e:
            self.status.setText(str(e))
            return
        if independencies:
            self.status.setText(
                f"{len(independencies)} implied conditional independencies:"
            )
        else:
            self.status.setText("The graph implies no conditional independencies.")
        self.list.addItems(str(assertion) for assertion in independencies)
