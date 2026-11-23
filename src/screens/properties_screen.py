import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import shiboken6
from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtGui import QFont, QPalette
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QLabel,
    QLineEdit,
    QStackedWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from models.arrow_types import ARROW_TYPE_LABELS, ArrowTypes
from models.var_types import VarTypes


class PropertySheet(QTreeWidget):
    """Visual Studio style property grid: collapsible categories holding
    name / value rows, with the value editors embedded in the grid."""

    NAME_COLUMN_RATIO = 0.42  # share of the width given to the names
    INDENTATION = 12
    ROW_HEIGHT = 24
    DESCRIPTION_ROLE = Qt.ItemDataRole.UserRole

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(2)
        self.setHeaderHidden(True)
        self.setIndentation(self.INDENTATION)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # Grid lines between cells; with an item style set, the selected
        # colors must be given too or the selected name turns invisible.
        self.setStyleSheet(
            "QTreeWidget { border: 1px solid palette(mid); }"
            "QTreeWidget::item { border-bottom: 1px solid palette(midlight);"
            " border-right: 1px solid palette(midlight); }"
            "QTreeWidget::item:selected { background: palette(highlight);"
            " color: palette(highlighted-text); }"
        )
        self.categories = []
        self.readOnlyRows = []
        self.editorRows = {}  # editor widget -> its row

    def addCategory(self, title):
        item = QTreeWidgetItem(self, [title])
        item.setSizeHint(0, QSize(0, self.ROW_HEIGHT))
        item.setFirstColumnSpanned(True)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        font = QFont(self.font())
        font.setBold(True)
        item.setFont(0, font)
        item.setExpanded(True)
        self.categories.append(item)
        self.applyPalette()
        return item

    def addRow(self, category, name, description, editor=None):
        item = QTreeWidgetItem(category, [name])
        item.setSizeHint(0, QSize(0, self.ROW_HEIGHT))
        item.setData(0, self.DESCRIPTION_ROLE, description)
        if editor is None:
            self.readOnlyRows.append(item)
        else:
            # Clicking into an editor selects its row (and shows its description)
            editor.installEventFilter(self)
            self.editorRows[editor] = item
            editor.setFixedHeight(self.ROW_HEIGHT - 1)  # keep the grid line
            self.setItemWidget(item, 1, editor)
        self.applyPalette()
        return item

    def sizeHint(self):
        # Tall enough to show every row without scrolling
        rows = len(self.categories) + len(self.rows())
        height = rows * self.ROW_HEIGHT + 2 * self.frameWidth()
        return QSize(super().sizeHint().width(), height)

    def minimumSizeHint(self):
        return QSize(super().minimumSizeHint().width(), self.sizeHint().height())

    def setValue(self, row, text):
        row.setText(1, text)
        row.setToolTip(1, text)

    def rows(self):
        return [
            category.child(i)
            for category in self.categories
            for i in range(category.childCount())
        ]

    def applyPalette(self):
        # Category bands and read-only values follow the light / dark palette
        palette = self.palette()
        band = palette.color(QPalette.ColorRole.Button)
        for category in self.categories:
            category.setBackground(0, band)
        muted = palette.color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text)
        for row in self.readOnlyRows:
            row.setForeground(1, muted)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.FocusIn and watched in self.editorRows:
            self.setCurrentItem(self.editorRows[watched])
        return super().eventFilter(watched, event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.setColumnWidth(0, int(self.viewport().width() * self.NAME_COLUMN_RATIO))

    def changeEvent(self, event):
        if event.type() == QEvent.Type.PaletteChange:
            self.applyPalette()
        super().changeEvent(event)


class PropertiesScreen(QWidget):
    """Shows and edits the selected node or arrow of the graph editor."""

    EMPTY_TEXT = (
        "Select a node or an arrow (in Nodes or Arrows mode) to see its "
        "properties."
    )
    DESCRIPTION_HEIGHT = 96

    PAGE_MESSAGE = 0
    PAGE_NODE = 1
    PAGE_ARROW = 2

    # Direction choices for the edge between u and v, as (label, arrows)
    DIRECTIONS = [
        ("{u} → {v}", lambda u, v: [(u, v)]),
        ("{v} → {u}", lambda u, v: [(v, u)]),
        ("{u} — {v}", lambda u, v: [(u, v), (v, u)]),
    ]

    def __init__(self, scene, parent=None):
        super().__init__(parent)
        self.scene = scene
        self.node = None
        self.arrow = None
        self.edgeEnds = None  # (u, v) kept stable while the edge is edited
        self.editing = False  # pauses refresh() while the panel applies an edit

        layout = QVBoxLayout(self)

        # --- Header: the selected object's name and kind, like VS ---
        self.titleLabel = QLabel(self)
        titleFont = QFont(self.titleLabel.font())
        titleFont.setBold(True)
        self.titleLabel.setFont(titleFont)
        self.kindLabel = QLabel(self)
        self.kindLabel.setEnabled(False)  # muted text
        layout.addWidget(self.titleLabel)
        layout.addWidget(self.kindLabel)

        self.stack = QStackedWidget(self)
        layout.addWidget(self.stack, 1)

        self.message = QLabel(self)
        self.message.setWordWrap(True)
        self.message.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.stack.addWidget(self.message)

        self.nodeSheet = self.buildNodeSheet()
        self.stack.addWidget(self.nodeSheet)
        self.arrowSheet = self.buildArrowSheet()
        self.stack.addWidget(self.arrowSheet)

        # --- Description of the selected property, at the bottom like VS ---
        self.descriptionBox = QFrame(self)
        self.descriptionBox.setFrameShape(QFrame.Shape.StyledPanel)
        # Fixed height so wrapped text never squeezes the sheet above it
        self.descriptionBox.setFixedHeight(self.DESCRIPTION_HEIGHT)
        descriptionLayout = QVBoxLayout(self.descriptionBox)
        self.descriptionTitle = QLabel(self.descriptionBox)
        self.descriptionTitle.setFont(titleFont)
        self.descriptionText = QLabel(self.descriptionBox)
        self.descriptionText.setWordWrap(True)
        self.descriptionText.setAlignment(Qt.AlignmentFlag.AlignTop)
        descriptionLayout.addWidget(self.descriptionTitle)
        descriptionLayout.addWidget(self.descriptionText, 1)
        layout.addWidget(self.descriptionBox)

        for sheet in (self.nodeSheet, self.arrowSheet):
            sheet.currentItemChanged.connect(self.showDescription)

        self.scene.selectionChanged.connect(self.refresh)
        self.scene.graphChanged.connect(self.refresh)
        self.refresh()

    def buildNodeSheet(self):
        sheet = PropertySheet(self)
        variable = sheet.addCategory("Variable")

        self.nameEdit = QLineEdit()
        self.nameEdit.setFrame(False)
        self.nameEdit.editingFinished.connect(self.applyName)
        sheet.addRow(
            variable,
            "Name",
            "The variable's name. It must be unique, and it is the name used "
            "in the conditional independence tests.",
            self.nameEdit,
        )

        self.nodeTypeCombo = QComboBox()
        self.nodeTypeCombo.setFrame(False)
        for varType in VarTypes:
            self.nodeTypeCombo.addItem(str(varType).capitalize(), varType)
        self.nodeTypeCombo.activated.connect(self.applyNodeType)
        sheet.addRow(
            variable,
            "Type",
            "The variable's role in the analysis. Unobserved variables are "
            "latent, so they are left out of the CI tests.",
            self.nodeTypeCombo,
        )

        self.nodeIdRow = sheet.addRow(
            variable,
            "ID",
            "Stable identifier of the node. It never changes, even when the "
            "node is renamed.",
        )

        arrows = sheet.addCategory("Arrows")
        self.inArrowsRow = sheet.addRow(
            arrows, "Incoming", "Number of arrows pointing into this node."
        )
        self.outArrowsRow = sheet.addRow(
            arrows, "Outgoing", "Number of arrows leaving this node."
        )
        return sheet

    def buildArrowSheet(self):
        sheet = PropertySheet(self)
        edge = sheet.addCategory("Edge")

        self.directionCombo = QComboBox()
        self.directionCombo.setFrame(False)
        self.directionCombo.activated.connect(self.applyDirection)
        sheet.addRow(
            edge,
            "Direction",
            "Which way the edge points. An undirected edge (—) means the "
            "direction is unknown, as in a CPDAG.",
            self.directionCombo,
        )
        self.edgeKindRow = sheet.addRow(
            edge, "Kind", "Whether the edge is directed or undirected."
        )

        origin = sheet.addCategory("Origin")
        self.arrowTypeCombo = QComboBox()
        self.arrowTypeCombo.setFrame(False)
        for arrowType in ArrowTypes:
            self.arrowTypeCombo.addItem(ARROW_TYPE_LABELS[arrowType], arrowType)
        self.arrowTypeCombo.activated.connect(self.applyArrowType)
        sheet.addRow(
            origin,
            "Added by",
            "Who added the arrow: the user (gray), a Domain Search suggestion "
            "(dashed purple), or a Domain Search suggestion the user accepted "
            "(teal).",
            self.arrowTypeCombo,
        )
        return sheet

    def refresh(self):
        # The scene emits selectionChanged while it is being destroyed at exit
        if self.editing or not shiboken6.isValid(self.scene):
            return
        nodes = self.scene.getSelectedNodes()
        arrows = self.scene.getSelectedArrows()
        self.node = next(iter(nodes)) if len(nodes) == 1 and not arrows else None
        self.arrow = next(iter(arrows)) if len(arrows) == 1 and not nodes else None

        if self.node is not None:
            self.showNode()
        elif self.arrow is not None:
            self.showArrow()
        else:
            self.edgeEnds = None
            self.titleLabel.setText("")
            self.kindLabel.setText("")
            if nodes:
                self.message.setText(f"{len(nodes)} nodes selected.")
            else:
                self.message.setText(self.EMPTY_TEXT)
            self.showPage(self.PAGE_MESSAGE)

    def showNode(self):
        self.edgeEnds = None
        self.titleLabel.setText(self.node.name)
        self.kindLabel.setText("Node")
        self.nameEdit.setText(self.node.name)
        self.nodeTypeCombo.setCurrentIndex(
            self.nodeTypeCombo.findData(self.node.varType)
        )
        self.nodeSheet.setValue(self.nodeIdRow, self.node.id)
        self.nodeSheet.setValue(self.inArrowsRow, str(len(self.node.inArrows)))
        self.nodeSheet.setValue(self.outArrowsRow, str(len(self.node.outArrows)))
        self.showPage(self.PAGE_NODE)

    def showArrow(self):
        ends = (self.arrow.fromNode, self.arrow.toNode)
        # Keep the same endpoint order when the same edge is still selected
        # (e.g. after flipping it), so the direction list doesn't reshuffle.
        if self.edgeEnds is None or set(self.edgeEnds) != set(ends):
            self.edgeEnds = ends
        u, v = self.edgeEnds

        self.directionCombo.clear()
        for label, _ in self.DIRECTIONS:
            self.directionCombo.addItem(label.format(u=u.name, v=v.name))
        if self.arrow.isUndirected():
            index = 2
        else:
            index = 0 if self.arrow.fromNode is u else 1
        self.directionCombo.setCurrentIndex(index)
        self.arrowSheet.setValue(
            self.edgeKindRow,
            "Undirected" if self.arrow.isUndirected() else "Directed",
        )
        self.arrowTypeCombo.setCurrentIndex(
            self.arrowTypeCombo.findData(self.arrow.arrowType)
        )

        self.titleLabel.setText(self.directionCombo.currentText())
        self.kindLabel.setText("Arrow")
        self.showPage(self.PAGE_ARROW)

    def showPage(self, page):
        self.stack.setCurrentIndex(page)
        sheet = self.stack.currentWidget()
        self.descriptionBox.setVisible(isinstance(sheet, PropertySheet))
        if isinstance(sheet, PropertySheet):
            # Qt may make a category the current row; start on a property
            current = sheet.currentItem()
            if current is None or current.parent() is None:
                sheet.setCurrentItem(sheet.rows()[0])
            self.showDescription(sheet.currentItem())

    def showDescription(self, row, previous=None):
        if row is None or row.parent() is None:  # nothing or a category
            return
        self.descriptionTitle.setText(row.text(0))
        self.descriptionText.setText(row.data(0, PropertySheet.DESCRIPTION_ROLE))

    # --- Edits ---

    def applyName(self):
        # editingFinished also fires when a warning dialog takes the focus,
        # so ignore it while a rename is already being applied.
        if self.node is None or self.editing:
            return
        name = self.nameEdit.text().strip()
        if name and name != self.node.name:
            self.editing = True
            self.scene.renameNode(self.node, name)
            self.editing = False
        self.nameEdit.setText(self.node.name)  # also reverts a rejected name
        self.refresh()

    def applyNodeType(self, index):
        if self.node is not None:
            varType = VarTypes(self.nodeTypeCombo.itemData(index))
            self.scene.setNodeType(self.node, varType)

    def applyDirection(self, index):
        if self.arrow is None:
            return
        u, v = self.edgeEnds
        # Replacing arrows changes the selection mid-edit, so refresh once at the end
        self.editing = True
        arrow = self.scene.setEdgeArrows(u, v, self.DIRECTIONS[index][1](u, v))
        self.scene.clearSelection()
        arrow.setSelected(True)
        self.editing = False
        self.refresh()

    def applyArrowType(self, index):
        if self.arrow is not None:
            arrowType = ArrowTypes(self.arrowTypeCombo.itemData(index))
            self.scene.setArrowType(self.arrow, arrowType)


if __name__ == "__main__":
    from PySide6.QtCore import QPointF
    from PySide6.QtWidgets import QApplication, QDockWidget, QMainWindow
    from graph_editor.graph_editor import GraphEditor

    app = QApplication(sys.argv)
    window = QMainWindow()
    editor = GraphEditor()
    window.setCentralWidget(editor)
    scene = editor.editorScene
    a = scene.addNode(QPointF(200, 200), "Smoking", VarTypes.EXPOSURE)
    b = scene.addNode(QPointF(500, 200), "Cancer", VarTypes.OUTCOME)
    scene.addArrow(a, b)
    dock = QDockWidget("Properties", window)
    dock.setWidget(PropertiesScreen(scene))
    window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
    window.resize(1000, 600)
    window.show()
    sys.exit(app.exec())
