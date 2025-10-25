from __future__ import annotations
import math
from typing import TYPE_CHECKING
from psygnal import Signal
from qtpy import QtWidgets as QtW, QtCore, QtGui
from qtpy.QtCore import Qt

from ._roi_items import (
    QLineRoi,
    QPointRoi,
    QPointsRoi,
    QPolygonRoi,
    QRectangleRoi,
    QEllipseRoi,
    QCircleRoi,
    QRotatedRectangleRoi,
    QSegmentedLineRoi,
)

if TYPE_CHECKING:
    from ._graphics_view import QImageGraphicsView, QBaseGraphicsScene


class QHandleRect(QtW.QGraphicsRectItem):
    """The rect item for the ROI handles"""

    # NOTE: QGraphicsItem is not a QObject, so we can't use QtCore.Signal here
    moved_by_mouse = Signal(QtCore.QPointF, QtCore.QPointF)

    def __init__(self, x: int, y: int, width: int, height: int, parent=None):
        super().__init__(x, y, width, height, parent)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        # this flag is needed to trigger mouseMoveEvent
        self.setFlag(QtW.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self._pos_drag_start: QtCore.QPointF | None = None
        self._pos_drag_prev: QtCore.QPointF | None = None
        self._cursor_shape = Qt.CursorShape.PointingHandCursor
        self.setCursor(self._cursor_shape)
        self.setZValue(100000)

    def setColor(self, color: QtGui.QColor):
        self.setBrush(QtGui.QBrush(color))

    def center(self) -> QtCore.QPointF:
        """Return the center of the rect."""
        return self.rect().center()

    def setCenter(self, point: QtCore.QPointF):
        """Set the center of the rect."""
        x, y = point.x(), point.y()
        w, h = self.rect().width(), self.rect().height()
        self.setRect(x - w / 2, y - h / 2, w, h)

    def setSize(self, size: float):
        """Set the size of the rect."""
        x, y = self.center().x(), self.center().y()
        self.setRect(x - size / 2, y - size / 2, size, size)

    def translate(self, dx: float, dy: float):
        self.setRect(self.rect().translated(dx, dy))

    def mousePressEvent(self, event: QtW.QGraphicsSceneMouseEvent):
        grab = self.scene().grabSource()
        if grab is not None and grab is not self:
            return super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            view = self.view()
            view.set_mode(self.view().Mode.SELECT)
            self.scene().setGrabSource(self)
        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtW.QGraphicsSceneMouseEvent | None) -> None:
        if self.scene().grabSource() is not self:
            return super().mouseMoveEvent(event)
        self.moved_by_mouse.emit(event.pos(), event.lastPos())
        return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtW.QGraphicsSceneMouseEvent | None) -> None:
        self.view().set_mode(self.view()._last_mode_before_key_hold)
        self.scene().setGrabSource(None)
        return super().mouseReleaseEvent(event)

    def view(self) -> QImageGraphicsView:
        return self.scene().views()[0]

    def scene(self) -> QBaseGraphicsScene:
        return super().scene()


class RoiSelectionHandles:
    draw_finished = Signal()

    def __init__(self, view: QImageGraphicsView):
        self._view = view
        self._handle_size = 2
        self._pen = QtGui.QPen(Qt.GlobalColor.black, 2)
        self._pen.setCosmetic(True)
        self._brush = QtGui.QBrush(Qt.GlobalColor.white)
        self._another_color = QtGui.QColor(Qt.GlobalColor.red)
        self._handles: list[QHandleRect] = []
        # This attribute is needed for drawing polygons and segmented lines.
        # When the mouse is hovering, the last vertice should not be considered as a
        # point yet, until the mouse is clicked.
        self._is_drawing_polygon = False
        self._is_last_vertex_added = False

    def make_handle_at(
        self,
        pos: QtCore.QPointF,
        color: QtGui.QColor | None = None,
    ) -> QHandleRect:
        """Construct a handle at the given position and add to the view."""
        s = self._handle_size
        handle = QHandleRect(pos.x() - s / 2, pos.y() - s / 2, s, s)
        handle.setPen(self._pen)
        handle.setBrush(self._brush)
        self._handles.append(handle)
        self.view().scene().addItem(handle)
        if color:
            handle.setColor(color)
        return handle

    def update_handle_size(self, scale: float):
        if scale == 0:
            return
        self._handle_size = 4 / scale
        for handle in self._handles:
            handle.setSize(self._handle_size)

    def clear_handles(self):
        """Remove all handles from the view."""
        view = self.view()
        for handle in self._handles:
            view.scene().removeItem(handle)
            handle.moved_by_mouse.disconnect()
        self._handles.clear()
        self.draw_finished.disconnect()

    def connect_line(self, line: QLineRoi):
        self.clear_handles()
        _line = line.line()
        h1 = self.make_handle_at(_line.p1())
        h2 = self.make_handle_at(_line.p2())
        hc = self.make_handle_at(_line.center(), self._another_color)
        self._handles = [h1, h2, hc]

        @h1.moved_by_mouse.connect
        def _1_moved(pos, last_pos):
            qline = line.line()
            qline.setP1(pos)
            line.setLine(qline)
            self._view.current_roi_updated.emit()

        @h2.moved_by_mouse.connect
        def _2_moved(pos, last_pos):
            qline = line.line()
            qline.setP2(pos)
            line.setLine(qline)
            self._view.current_roi_updated.emit()

        @hc.moved_by_mouse.connect
        def _c_moved(pos, last_pos):
            delta = pos - last_pos
            qline = line.line()
            qline.translate(delta.x(), delta.y())
            line.setLine(qline)
            self._view.current_roi_updated.emit()

        @line.changed.connect
        def _line_changed(qline: QtCore.QLineF):
            h1.setCenter(qline.p1())
            h2.setCenter(qline.p2())
            hc.setCenter(qline.center())
            self._view.current_roi_updated.emit()

    def connect_rect(self, rect: QRectangleRoi | QEllipseRoi):
        self.clear_handles()
        _rect = rect.rect()
        h_tl = self.make_handle_at(_rect.topLeft())
        h_br = self.make_handle_at(_rect.bottomRight())
        h_tr = self.make_handle_at(_rect.topRight())
        h_bl = self.make_handle_at(_rect.bottomLeft())
        h_t = self.make_handle_at(
            (_rect.topLeft() + _rect.topRight()) / 2, self._another_color
        )
        h_b = self.make_handle_at(
            (_rect.bottomLeft() + _rect.bottomRight()) / 2, self._another_color
        )
        h_l = self.make_handle_at(
            (_rect.topLeft() + _rect.bottomLeft()) / 2, self._another_color
        )
        h_r = self.make_handle_at(
            (_rect.topRight() + _rect.bottomRight()) / 2, self._another_color
        )
        self._handles = [h_tl, h_br, h_tr, h_bl, h_t, h_b, h_l, h_r]

        @h_tl.moved_by_mouse.connect
        def _tl_moved(pos, last_pos):
            other = rect.rect().bottomRight()
            ex, ey = self.view()._pos_to_tuple(pos)
            x0, x1 = sorted([other.x(), ex])
            y0, y1 = sorted([other.y(), ey])
            rect.setRect(x0, y0, x1 - x0, y1 - y0)
            self._view.current_roi_updated.emit()

        @h_br.moved_by_mouse.connect
        def _br_moved(pos, last_pos):
            other = rect.rect().topLeft()
            ex, ey = self.view()._pos_to_tuple(pos)
            x0, x1 = sorted([other.x(), ex])
            y0, y1 = sorted([other.y(), pos.y()])
            rect.setRect(x0, y0, x1 - x0, y1 - y0)
            self._view.current_roi_updated.emit()

        @h_tr.moved_by_mouse.connect
        def _tr_moved(pos, last_pos):
            other = rect.rect().bottomLeft()
            ex, ey = self.view()._pos_to_tuple(pos)
            x0, x1 = sorted([other.x(), ex])
            y0, y1 = sorted([other.y(), ey])
            rect.setRect(x0, y0, x1 - x0, y1 - y0)
            self._view.current_roi_updated.emit()

        @h_bl.moved_by_mouse.connect
        def _bl_moved(pos, last_pos):
            other = rect.rect().topRight()
            ex, ey = self.view()._pos_to_tuple(pos)
            x0, x1 = sorted([other.x(), ex])
            y0, y1 = sorted([other.y(), ey])
            rect.setRect(x0, y0, x1 - x0, y1 - y0)
            self._view.current_roi_updated.emit()

        @h_t.moved_by_mouse.connect
        def _t_moved(pos, last_pos):
            r0 = rect.rect()
            _, ey = self.view()._pos_to_tuple(pos)
            y0, y1 = sorted([r0.bottom(), ey])
            rect.setRect(r0.x(), y0, r0.width(), y1 - y0)
            self._view.current_roi_updated.emit()

        @h_b.moved_by_mouse.connect
        def _b_moved(pos, last_pos):
            r0 = rect.rect()
            _, ey = self.view()._pos_to_tuple(pos)
            y0, y1 = sorted([r0.top(), ey])
            rect.setRect(r0.x(), y0, r0.width(), y1 - y0)
            self._view.current_roi_updated.emit()

        @h_l.moved_by_mouse.connect
        def _l_moved(pos, last_pos):
            r0 = rect.rect()
            ex, _ = self.view()._pos_to_tuple(pos)
            x0, x1 = sorted([r0.right(), ex])
            rect.setRect(x0, r0.y(), x1 - x0, r0.height())
            self._view.current_roi_updated.emit()

        @h_r.moved_by_mouse.connect
        def _r_moved(pos, last_pos):
            r0 = rect.rect()
            ex, _ = self.view()._pos_to_tuple(pos)
            x0, x1 = sorted([r0.left(), ex])
            rect.setRect(x0, r0.y(), x1 - x0, r0.height())
            self._view.current_roi_updated.emit()

        @rect.changed.connect
        def _rect_changed(r: QtCore.QRectF):
            tl = r.topLeft()
            br = r.bottomRight()
            tr = r.topRight()
            bl = r.bottomLeft()
            h_tl.setCenter(tl)
            h_br.setCenter(br)
            h_tr.setCenter(tr)
            h_bl.setCenter(bl)
            h_t.setCenter((tl + tr) / 2)
            h_b.setCenter((bl + br) / 2)
            h_l.setCenter((tl + bl) / 2)
            h_r.setCenter((tr + br) / 2)
            self._view.current_roi_updated.emit()

    def connect_path(self, path: QPolygonRoi | QSegmentedLineRoi):
        self.clear_handles()
        _path = path.path()
        for i in range(_path.elementCount()):
            element = _path.elementAt(i)
            h = self.make_handle_at(QtCore.QPointF(element.x, element.y))
            h.moved_by_mouse.connect(lambda pos, _, i=i: path.update_point(i, pos))

        @path.changed.connect
        def _path_changed(p: QtGui.QPainterPath):
            offset = 0 if self._is_last_vertex_added else 1
            self.remove_handles(p.elementCount() - offset, len(self._handles))
            for i in range(len(self._handles), p.elementCount() - offset):
                element = p.elementAt(i)
                h = self.make_handle_at(QtCore.QPointF(element.x, element.y))
                h.moved_by_mouse.connect(lambda pos, _, i=i: path.update_point(i, pos))
            for i, h in enumerate(self._handles):
                element = p.elementAt(i)
                h.setCenter(QtCore.QPointF(element.x, element.y))
            self._view.current_roi_updated.emit()

        self.draw_finished.connect(lambda: self._finish_drawing_path(path))

    def connect_point(self, point: QPointRoi):
        self.clear_handles()
        h = self.make_handle_at(point.point())
        h.moved_by_mouse.connect(lambda pos, _: point.setPoint(pos))

        @point.changed.connect
        def _point_changed(ps: QtCore.QPointF):
            h.setCenter(ps)
            self._view.current_roi_updated.emit()

    def connect_points(self, points: QPointsRoi):
        self.clear_handles()
        for i in range(points.count()):
            h = self.make_handle_at(points.pointAt(i))
            h.moved_by_mouse.connect(lambda pos, _, i=i: points.update_point(i, pos))

        @points.changed.connect
        def _points_changed(ps: list[QtCore.QPointF]):
            self.remove_handles(len(ps), len(self._handles))
            for i in range(len(self._handles), len(ps)):
                h = self.make_handle_at(ps[i])
                h.moved_by_mouse.connect(
                    lambda pos, _, i=i: points.update_point(i, pos)
                )
            for i, h in enumerate(self._handles):
                h.setCenter(ps[i])
            self._view.current_roi_updated.emit()

    def connect_circle(self, circle: QCircleRoi):
        self.clear_handles()
        h_c = self.make_handle_at(circle.center())
        h_br = self.make_handle_at(circle.rect().bottomRight(), self._another_color)

        @h_c.moved_by_mouse.connect
        def _c_moved(pos: QtCore.QPointF, last_pos):
            circle.setCenterAndRadius((pos.x(), pos.y()), circle.radius())

        @h_br.moved_by_mouse.connect
        def _br_moved(pos: QtCore.QPointF, last_pos):
            radius = abs(pos.x() - circle.center().x())
            center = circle.center()
            circle.setCenterAndRadius((center.x(), center.y()), radius)

        @circle.changed.connect
        def _circle_changed(rect: QtCore.QRectF):
            h_c.setCenter(circle.center())
            h_br.setCenter(circle.rect().bottomRight())
            self._view.current_roi_updated.emit()

    def connect_rotated_rect(self, rect: QRotatedRectangleRoi):
        self.clear_handles()
        h_l = self.make_handle_at(rect.start())
        h_r = self.make_handle_at(rect.end())
        h_t = self.make_handle_at(rect.top(), self._another_color)
        h_b = self.make_handle_at(rect.bottom(), self._another_color)

        @h_t.moved_by_mouse.connect
        @h_b.moved_by_mouse.connect
        def _t_b_moved(pos, last_pos):
            ex = rect.vector_x()
            ex = ex / math.sqrt(ex.x() ** 2 + ex.y() ** 2)  # unit vector
            pos_rel = pos - rect.start()
            pos_proj = ex * QtCore.QPointF.dotProduct(pos_rel, ex)
            dist_vec = pos_rel - pos_proj
            dist = math.sqrt(dist_vec.x() ** 2 + dist_vec.y() ** 2)
            rect.set_width(dist * 2)
            self._view.current_roi_updated.emit()

        @h_l.moved_by_mouse.connect
        def _l_moved(pos, last_pos):
            rect.set_start(pos)
            self._view.current_roi_updated.emit()

        @h_r.moved_by_mouse.connect
        def _r_moved(pos, last_pos):
            rect.set_end(pos)
            self._view.current_roi_updated.emit()

        @rect.changed.connect
        def _rect_changed():
            h_l.setCenter(rect.start())
            h_r.setCenter(rect.end())
            h_t.setCenter(rect.top())
            h_b.setCenter(rect.bottom())
            self._view.current_roi_updated.emit()

    def connect_roi(self, roi_item):
        if isinstance(roi_item, QLineRoi):
            self.connect_line(roi_item)
        elif isinstance(roi_item, (QRectangleRoi, QEllipseRoi)):
            self.connect_rect(roi_item)
        elif isinstance(roi_item, (QPolygonRoi, QSegmentedLineRoi)):
            self.connect_path(roi_item)
        elif isinstance(roi_item, QPointRoi):
            self.connect_point(roi_item)
        elif isinstance(roi_item, QPointsRoi):
            self.connect_points(roi_item)
        elif isinstance(roi_item, QCircleRoi):
            self.connect_circle(roi_item)
        elif isinstance(roi_item, QRotatedRectangleRoi):
            self.connect_rotated_rect(roi_item)
        else:
            pass

    def _finish_drawing_path(self, path: QPolygonRoi | QSegmentedLineRoi):
        painter_path = path.path()
        if isinstance(path, QPolygonRoi):
            painter_path.closeSubpath()
        path.setPath(painter_path)

    def view(self) -> QImageGraphicsView:
        return self._view

    def start_drawing_polygon(self):
        self._is_drawing_polygon = True
        self._is_last_vertex_added = False

    def is_drawing_polygon(self) -> bool:
        return self._is_drawing_polygon

    def finish_drawing_polygon(self):
        was_drawing_polygon = self._is_drawing_polygon
        self._is_drawing_polygon = False
        if was_drawing_polygon:
            self.draw_finished.emit()

    def remove_handles(self, start: int, end: int):
        for i in range(start, end):
            self.view().scene().removeItem(self._handles[i])
        del self._handles[start:end]
