from PySide6.QtCore import QEvent, QSize, Qt, QTimer
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

import qtawesome as qta


class IndependenciesScreen(QWidget):
    REFRESH_DELAY_MS = 200

    COLUMN_CI = 0
    COLUMN_RESULT = 1
    COLUMN_RUN = 2

    RUN_ICON = "mdi6.play"
    RUN_ALL_ICON = "mdi6.fast-forward"

    RUN_COLUMN_WIDTH = 32
    RUN_ALL_ICON_SIZE = 18

    NOT_TESTED_TEXT = "—"

    def __init__(self, scene, parent=None):
        super().__init__(parent)
        self.scene = scene
        self.independencies = []

        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        self.status = QLabel(self)
        self.status.setWordWrap(True)
        header.addWidget(self.status, 1)

        # Not connected yet — the test runner will be wired up later.
        self.runAllButton = QToolButton(self)
        self.runAllButton.setIcon(qta.icon(self.RUN_ALL_ICON))
        self.runAllButton.setIconSize(
            QSize(self.RUN_ALL_ICON_SIZE, self.RUN_ALL_ICON_SIZE)
        )
        self.runAllButton.setAutoRaise(True)
        self.runAllButton.setToolTip(
            "Run the test for every conditional independence in the list"
        )
        header.addWidget(self.runAllButton, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header)

        self.table = QTableWidget(0, 3, self)
        self.table.setHorizontalHeaderLabels(["Independence", "Result", ""])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setShowGrid(False)
        headerView = self.table.horizontalHeader()
        headerView.setSectionResizeMode(self.COLUMN_CI, QHeaderView.ResizeMode.Stretch)
        headerView.setSectionResizeMode(
            self.COLUMN_RESULT, QHeaderView.ResizeMode.ResizeToContents
        )
        headerView.setSectionResizeMode(self.COLUMN_RUN, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(self.COLUMN_RUN, self.RUN_COLUMN_WIDTH)
        layout.addWidget(self.table)

        self.debouncer = QTimer(self)
        self.debouncer.setSingleShot(True)
        self.debouncer.setInterval(self.REFRESH_DELAY_MS)
        self.debouncer.timeout.connect(self.refresh)
        self.scene.graphChanged.connect(self.debouncer.start)

        self.refresh()

    def refresh(self):
        self.table.setRowCount(0)
        self.independencies = []
        self.runAllButton.setEnabled(False)
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

        self.independencies = list(independencies)
        self.runAllButton.setEnabled(bool(self.independencies))
        for assertion in self.independencies:
            self._addRow(assertion)

    def _addRow(self, assertion):
        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, self.COLUMN_CI, QTableWidgetItem(str(assertion)))

        result = QTableWidgetItem(self.NOT_TESTED_TEXT)
        result.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        result.setToolTip("Not tested yet")
        self.table.setItem(row, self.COLUMN_RESULT, result)

        # Not connected yet — the test runner will be wired up later.
        runButton = QToolButton(self.table)
        runButton.setIcon(qta.icon(self.RUN_ICON))
        runButton.setAutoRaise(True)
        runButton.setToolTip(f"Run the test for {assertion}")
        self.table.setCellWidget(row, self.COLUMN_RUN, runButton)

    def changeEvent(self, event):
        # qtawesome caches icons in the old text color, so rebuild on light/dark change
        if event.type() == QEvent.Type.PaletteChange:
            qta.reset_cache()
            self.runAllButton.setIcon(qta.icon(self.RUN_ALL_ICON))
            icon = qta.icon(self.RUN_ICON)
            for row in range(self.table.rowCount()):
                self.table.cellWidget(row, self.COLUMN_RUN).setIcon(icon)
        super().changeEvent(event)
