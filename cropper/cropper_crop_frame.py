import logging

from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsItem, QApplication
from PyQt5.QtGui import QPen, QPainterPath, QBrush, QColor
from PyQt5.QtCore import Qt, QObject, QEvent, QRectF, QPointF

logger = logging.getLogger(__name__)


class CropFrame(QGraphicsRectItem):
    def __init__(self, rect, bounding_rect=None, on_move_callback=None):
        super().__init__(rect)
        self.pen = QPen(QColor("#FF0000"), 2)
        self.setPen(self.pen)
        self.setCursor(Qt.OpenHandCursor)

        self.setFlags(
            QGraphicsRectItem.ItemIsMovable |
            QGraphicsRectItem.ItemSendsGeometryChanges
        )

        self.on_move_callback = on_move_callback
        self.bounding_rect = bounding_rect

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.bounding_rect:
            new_pos = value
            rect = self.rect()


            if new_pos.x() < self.bounding_rect.left():
                new_pos.setX(self.bounding_rect.left())
            if new_pos.y() < self.bounding_rect.top():
                new_pos.setY(self.bounding_rect.top())
            if new_pos.x() + rect.width() > self.bounding_rect.right():
                new_pos.setX(self.bounding_rect.right() - rect.width())
            if new_pos.y() + rect.height() > self.bounding_rect.bottom():
                new_pos.setY(self.bounding_rect.bottom() - rect.height())

            new_pos.setX(round(new_pos.x()))
            new_pos.setY(round(new_pos.y()))

            return new_pos

        elif change == QGraphicsItem.ItemPositionHasChanged:
            if self.on_move_callback:
                self.on_move_callback()

        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.OpenHandCursor)
        super().mouseReleaseEvent(event)

    def color(self, clr=QColor("#FF0000")):
        self.pen = QPen(clr, 2)
        self.setPen(self.pen)


class DarkOverlay(QGraphicsItem):
    def __init__(self, scene_rect, crop_frame):
        super().__init__()
        self.setZValue(1)
        self.scene_rect = scene_rect
        self.crop_frame = crop_frame
        self.setOpacity(0.6)
        self.setAcceptedMouseButtons(Qt.NoButton)
        self.overlay_color = QColor("#000000")

    def boundingRect(self):
        return self.scene_rect

    def paint(self, painter, option, widget=None):
        painter.setBrush(QBrush(self.overlay_color))
        painter.setPen(Qt.NoPen)

        full = QPainterPath()
        full.addRect(self.scene_rect)

        hole = QPainterPath()
        hole.addRect(self.crop_frame.sceneBoundingRect())

        final_path = full.subtracted(hole)
        painter.drawPath(final_path)

    def color(self, clr=QColor("#000000")):
        self.overlay_color = clr


class ResizeHandle(QGraphicsItem):
    def __init__(self, cropper, crop_frame):
        super().__init__()
        self.handle_size = 36
        self.setZValue(2)
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.resize_handle_color = QColor("#FF0000")
        self.setCursor(Qt.SizeFDiagCursor)
        self.crop_frame = crop_frame
        self.cropper = cropper

        self._dragging = False
        self._start_mouse_pos = None
        self._start_frame_rect = self.crop_frame.rect()

        self.update_position()

    def update_position(self):
        crop_frame = self.crop_frame.sceneBoundingRect()
        x = crop_frame.right() - self.handle_size / 2
        y = crop_frame.bottom() - self.handle_size / 2
        self.setPos(QPointF(x, y))

    def boundingRect(self):
        return QRectF(0, 0, self.handle_size, self.handle_size)

    def paint(self, painter, option, widget=None):
        painter.setBrush(QBrush(self.resize_handle_color))
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, 0, self.handle_size, self.handle_size)

    def color(self, clr=QColor("#FF0000")):
        self.resize_handle_color = clr

    def mousePressEvent(self, event):
        self._dragging = True
        self._start_mouse_pos = event.scenePos()
        self._start_frame_rect = self.crop_frame.rect()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self._dragging:
            return

        delta_x = self._start_frame_rect.width() + ((event.scenePos().x() - self._start_mouse_pos.x()))
        delta_y = self._start_frame_rect.height() + ((event.scenePos().y() - self._start_mouse_pos.y()))
        self.cropper.resize_by_handle(delta_x, delta_y)

        event.accept()

    def mouseReleaseEvent(self, event):
        self._dragging = False
        super().mouseReleaseEvent(event)


class WheelFilter(QObject):
    def __init__(self, cropper):
        super().__init__()
        self.cropper = cropper

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel and Qt.ControlModifier:
            self.cropper.resize_by_wheel(event)
            return True
        return False
