"""Interaction modes of the graph editor."""

from enum import Enum, auto


class EditorMode(Enum):
    NODES = auto()  # add nodes and drag them around
    ARROWS = auto()  # connect nodes with arrows
    SELECT = auto()  # pick several nodes (used later by Domain Search)


DEFAULT_EDITOR_MODE: EditorMode = EditorMode.NODES
