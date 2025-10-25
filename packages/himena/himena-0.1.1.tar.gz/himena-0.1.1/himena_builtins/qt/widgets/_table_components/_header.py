from __future__ import annotations
from typing import TYPE_CHECKING, Iterator
from qtpy import QtWidgets as QtW, QtCore, QtGui
from qtpy.QtCore import Qt


if TYPE_CHECKING:
    from ._base import QTableBase


class QHeaderViewBase(QtW.QHeaderView):
    """The header view for the QTableBase."""

    _Orientation: Qt.Orientation

    def __init__(self, parent: QtW.QWidget | None = None) -> None:
        super().__init__(self._Orientation, parent)
        self.setSelectionMode(QtW.QHeaderView.SelectionMode.SingleSelection)
        self.setSectionsClickable(True)
        self.sectionPressed.connect(self._on_section_pressed)  # pressed
        self.sectionClicked.connect(self._on_section_clicked)  # released
        self.sectionEntered.connect(self._on_section_entered)  # dragged

    # fmt: off
    if TYPE_CHECKING:
        def parentWidget(self) -> QTableBase: ...
    # fmt: on

    @property
    def selection_model(self):
        return self.parentWidget()._selection_model

    def _on_section_pressed(self, logicalIndex: int) -> None:
        self.selection_model.jump_to(*self._index_for_selection_model(logicalIndex))
        self.selection_model.set_shift(True)
        return None

    def _on_section_entered(self, logicalIndex: int) -> None:
        self.selection_model.move_to(*self._index_for_selection_model(logicalIndex))
        return None

    def _on_section_clicked(self, logicalIndex) -> None:
        self.selection_model.set_shift(False)

    def _iter_selections(self) -> Iterator[slice]:
        """Iterate selections"""
        raise NotImplementedError()

    def _index_for_selection_model(self, logicalIndex: int) -> tuple[int, int]:
        raise NotImplementedError()

    def visualRectAtIndex(self, index: int) -> QtCore.QRect:
        """Return the visual rect of the given index."""
        raise NotImplementedError()

    @staticmethod
    def drawBorder(painter: QtGui.QPainter, rect: QtCore.QRect):
        """Draw the opened border of a section."""
        raise NotImplementedError()

    def drawCurrent(self, painter: QtGui.QPainter, rect: QtCore.QRect):
        """Draw the current index if exists."""
        raise NotImplementedError()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        super().paintEvent(event)
        painter = QtGui.QPainter(self.viewport())
        color = self.parentWidget()._selection_color
        pen = QtGui.QPen(color, 3)
        painter.setPen(pen)

        # paint selections
        for _slice in self._iter_selections():
            rect_start = self.visualRectAtIndex(_slice.start)
            rect_stop = self.visualRectAtIndex(_slice.stop - 1)
            rect = rect_start | rect_stop
            self.drawBorder(painter, rect)

        # paint current
        self.drawCurrent(painter)
        return None

    def mouseReleaseEvent(self, e: QtGui.QMouseEvent) -> None:
        self.selection_model.set_shift(False)
        return super().mouseReleaseEvent(e)

    def keyPressEvent(self, e):
        self._update_press_release(e.modifiers())
        return super().keyPressEvent(e)

    def keyReleaseEvent(self, a0):
        self._update_press_release(a0.modifiers())
        return super().keyReleaseEvent(a0)

    def _update_press_release(self, mod: Qt.KeyboardModifier):
        has_ctrl = mod & Qt.KeyboardModifier.ControlModifier
        has_shift = mod & Qt.KeyboardModifier.ShiftModifier
        self.selection_model.set_shift(has_shift)
        self.selection_model.set_ctrl(has_ctrl)


class QHorizontalHeaderView(QHeaderViewBase):
    _Orientation = Qt.Orientation.Horizontal

    def visualRectAtIndex(self, index: int) -> QtCore.QRect:
        x = self.sectionViewportPosition(index)
        y = self.rect().top()
        height = self.height()
        width = self.sectionSize(index)
        return QtCore.QRect(x, y, width, height)

    @staticmethod
    def drawBorder(painter: QtGui.QPainter, rect: QtCore.QRect):
        return painter.drawPolyline(
            rect.bottomLeft(),
            rect.topLeft(),
            rect.topRight(),
            rect.bottomRight(),
        )

    def drawCurrent(self, painter: QtGui.QPainter):
        row, col = self.selection_model.current_index
        if row < 0 and col >= 0:
            rect_current = self.visualRectAtIndex(col)
            rect_current.adjust(1, 1, -1, -1)
            color = self.parentWidget()._current_color
            pen = QtGui.QPen(color, 3)
            painter.setPen(pen)
            painter.drawRect(rect_current)
        return None

    def _iter_selections(self):
        yield from self.selection_model.iter_col_selections()

    def _index_for_selection_model(self, logicalIndex):
        return -1, logicalIndex


class QVerticalHeaderView(QHeaderViewBase):
    _Orientation = Qt.Orientation.Vertical

    def visualRectAtIndex(self, index: int) -> QtCore.QRect:
        x = self.rect().left()
        y = self.sectionViewportPosition(index)
        height = self.sectionSize(index)
        width = self.width()
        return QtCore.QRect(x, y, width, height)

    @staticmethod
    def drawBorder(painter: QtGui.QPainter, rect: QtCore.QRect):
        return painter.drawPolyline(
            rect.topRight(),
            rect.topLeft(),
            rect.bottomLeft(),
            rect.bottomRight(),
        )

    def drawCurrent(self, painter: QtGui.QPainter):
        row, col = self.selection_model.current_index
        if col < 0 and row >= 0:
            rect_current = self.visualRectAtIndex(row)
            rect_current.adjust(1, 1, -1, -1)
            color = self.parentWidget()._current_color
            pen = QtGui.QPen(color, 4)
            painter.setPen(pen)
            painter.drawRect(rect_current)
        return None

    def _iter_selections(self):
        yield from self.selection_model.iter_row_selections()

    def _index_for_selection_model(self, logicalIndex):
        return logicalIndex, -1
