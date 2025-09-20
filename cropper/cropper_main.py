import sys
import logging
import time
from threading import Thread

from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsPixmapItem, QShortcut, \
    QGraphicsRectItem, QGraphicsItem, QFileDialog
from PyQt5.QtGui import QPixmap, QTransform, QKeySequence, QPen, QColor, QPainterPath, QBrush, QImage, QIcon
from PyQt5.QtCore import QRectF, QObject, QEvent, Qt, QFile, QTextStream, QTimer
from PIL import Image
import pillow_heif
import io

from cropper.cropper_help import SendyHelp
from photo_processing.photo_processing import PhotoProc
from cropper.cropper_ui import Ui_Cropper
from cropper.cropper_settings import SendySettings
from cropper.cropper_save import SendySave
from data import data

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
        self.bounding_rect = bounding_rect  # Область, в которой можно двигать рамку

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.bounding_rect:
            new_pos = value
            rect = self.rect()

            # Ограничим позицию по bounding_rect
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
        self.setOpacity(0.5)
        self.setAcceptedMouseButtons(Qt.NoButton)
        self.overlay_color = QColor("#000000")

    def boundingRect(self):
        return self.scene_rect

    def paint(self, painter, option, widget=None):
        # Общая область
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


class WheelFilter(QObject):
    def __init__(self, cropper):
        super().__init__()
        self.cropper = cropper

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel:
            if Qt.ControlModifier:
                self.cropper.resize_frame_by_wheel(event)
                return True
        return False


class SendyCropper(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Cropper()
        self.ui.setupUi(self)
        self.set_CSS()
        self.setWindowIcon(self.load_icon())
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.pixmap_main = None
        self.ui.pushButton_rotate.clicked.connect(self.rotate_image)
        self.ui.pushButton_contrast.clicked.connect(self.contrast)
        self.ui.pushButton_swap.clicked.connect(self.swap_wight_and_height)
        self.ui.pushButton_full_screen.clicked.connect(self.full_screen)
        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(self.rotate_image)
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(self.full_screen)
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self.swap_wight_and_height)
        QShortcut(QKeySequence("Ctrl+C"), self).activated.connect(self.contrast)
        QShortcut(QKeySequence("F3"), self).activated.connect(self.save)
        self.ui.pushButton_crop.clicked.connect(self.crop_and_close)
        self.ui.lineEdit_width.textChanged.connect(self.lineedit_width_or_height_changed)
        self.ui.lineEdit_height.textChanged.connect(self.lineedit_width_or_height_changed)
        self.image_item = None
        self.cropped_image = None
        self.frame_coordinates = (0, 0, 0, 0)
        self.scene = QGraphicsScene()
        self.scene_preview = QGraphicsScene()
        self.crop_frame = None
        self.overlay = None
        self.wheel_filter = WheelFilter(self)
        self.ui.graphicsView_main.installEventFilter(self.wheel_filter)
        self.crop_width = 0
        self.crop_height = 0
        self.cropped_result_image = None
        self.ui.action_open.triggered.connect(self.open_file)
        self.ui.action_settings.triggered.connect(self.open_settings)
        self.ui.action_save.triggered.connect(self.save)
        self.ui.action_about.triggered.connect(self.help)
        self.settings_window = None
        self.save_window = None
        self.help_window = None
        self.frame_scale = 1.2
        self.setFocusPolicy(Qt.StrongFocus)
        self.message = None
        self.original_image = None
        self.rotation_angle = 0
        self.crop_frame_color = QColor("#FF0000")
        self.overlay_color = QColor("#000000")

        for w, h in [(20, 30), (30, 40), (30, 45), (30, 55),
                     (40, 60), (45, 60), (40, 70), (50, 60),
                     (50, 70), (60, 80), (60, 90), (90, 120),

                     (20, 20), (30, 30), (35, 35), (40, 40),
                     (50, 50), (60, 60), (70, 70), (80, 80),
                     (90, 90), (100, 100), (110, 110),

                     (20, 35), (20, 40), (25, 30), (30, 50),
                     (30, 60), (40, 50), (40, 80), (40, 90),
                     (50, 55), (50, 75), (50, 80), (50, 90),
                     (70, 80), (70, 90), (70, 120), (80, 110),
                     (80, 120), (80, 130), (90, 110), (90, 130)]:
            button = getattr(self.ui, f"pushButton_{w}_{h}")
            if button:
                button.clicked.connect(self.set_width_height_from_button)

    def set_CSS(self):
        try:
            css_file = QFile(data.cropper_css)
            if not css_file.exists():
                logger.error('No CSS file in resources')
                return

            if css_file.open(QFile.ReadOnly | QFile.Text):
                stream = QTextStream(css_file)
                css = stream.readAll()
                css_file.close()
                logger.debug('CSS is loaded')
                QApplication.instance().setStyleSheet(css)
            else:
                logger.error('Cannot open CSS file')
                return

        except Exception:
            logger.exception(f'Cannot load CSS')
            return

    def load_icon(self):
        if QFile.exists(":/sendy.ico"):
            return QIcon(":/sendy.ico")
        logger.error('No icon in resources')
        return QIcon()

    def load_image(self, image):
        self.original_image = image

        def pil_image_to_pixmap(pil_image):
            buffer = io.BytesIO()
            pil_image.save(buffer, format="PNG")
            qimage = QImage()
            qimage.loadFromData(buffer.getvalue(), "PNG")
            return QPixmap.fromImage(qimage)

        if isinstance(image, Image.Image):
            image = pil_image_to_pixmap(image)

        self.pixmap_main = image
        self.image_item = QGraphicsPixmapItem(self.pixmap_main)
        self.scene.addItem(self.image_item)
        self.ui.graphicsView_main.setScene(self.scene)
        self.rescale_main()

    def open_file(self):
        image_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл",
            "",  # начальная папка (пустая - текущая)
            "Изображения (*.jpg *.png *.heic);;Все файлы (*)"
        )
        if image_path:
            self.scene.clear()
            self.crop_frame = None
            self.overlay = None
            self.ui.graphicsView_main.setScene(None)
            self.scene_preview.clear()
            self.ui.graphicsView_preview.setScene(None)
            pillow_heif.register_heif_opener()
            image = Image.open(image_path).convert("RGB")
            if not image:
                logging.info('Не удалось загрузить изображение')
                self.statusBar().showMessage("Не удалось загрузить изображение", 3000)
                return
            self.load_image(image)
            self.ui.graphicsView_main.setStyleSheet('')

    def open_settings(self):
        try:
            if self.settings_window is None:
                self.settings_window = SendySettings(self)
            self.settings_window.exec_()
        except Exception as e:
            logger.exception(f'open_settings: {e}')

    def save(self):
        try:
            if self.save_window is None:
                self.save_window = SendySave(self)
            self.save_window.exec_()
        except Exception:
            logger.exception('save_window')

    def help(self):
        try:
            if self.help_window is None:
                self.help_window = SendyHelp(self)
            self.help_window.show()
            self.help_window.raise_()
        except Exception:
            logger.exception(f'help_window')

    def set_number(self, number):
        self.ui.lineEdit_number.setText(str(number))

    def set_material(self, n):
        self.ui.comboBox_material.setCurrentIndex(n)

    def set_width_and_height(self, width, height):
        if width and height:
            self.ui.lineEdit_width.setText(str(width))
            self.ui.lineEdit_height.setText(str(height))

    def set_bot(self, message):
        self.message = message

    def rescale_main(self):
        if self.pixmap_main is None:
            logging.debug('No image for rescale main')
            return

        view_width = self.ui.graphicsView_main.width()
        view_height = self.ui.graphicsView_main.height()
        image_width = self.image_item.pixmap().width()
        image_height = self.image_item.pixmap().height()
        if image_width > 0 and image_height > 0:
            scale = min((view_width / image_width), (
                    view_height / image_height)) - 0.005  # 0.005 - позволяет уменьшить изобр так, чтобы убрать scroll
            self.ui.graphicsView_main.resetTransform()
            self.ui.graphicsView_main.scale(scale, scale)

    def rescale_preview(self):
        if self.cropped_image is None:
            logging.debug('No image for preview rescale')
            return

        view_width = self.ui.graphicsView_preview.width()
        view_height = self.ui.graphicsView_preview.height()
        cropped_image_width = self.cropped_image.width()
        cropped_image_height = self.cropped_image.height()
        scale = min((view_width / cropped_image_width), (
                view_height / cropped_image_height)) - 0.05  # 0.05 - позволяет уменьшить изобр так, чтобы убрать scroll
        self.ui.graphicsView_preview.resetTransform()
        self.ui.graphicsView_preview.scale(scale, scale)

    def rotate_image(self):
        error_image_css = """
                              QGraphicsView {
                                  border: 2px solid #FF6B6B;
                              }
                          """

        if self.pixmap_main is None:
            logging.debug('No image for rotation')
            self.statusBar().showMessage("Нет изображения для поворота.", 2000)
            self.ui.graphicsView_main.setStyleSheet(error_image_css)
            return

        self.ui.graphicsView_main.setStyleSheet('')

        rotated = self.pixmap_main.transformed(QTransform().rotate(90))
        self.scene.setSceneRect(0, 0, rotated.width(), rotated.height())
        self.pixmap_main = rotated

        if hasattr(self, 'image_item') and self.image_item:
            self.image_item.setPixmap(self.pixmap_main)
        else:
            self.image_item = QGraphicsPixmapItem(self.pixmap_main)
            self.scene.addItem(self.image_item)
        self.rescale_main()
        self.create_crop_frame()

        angles = [0, -90, -180, -270]  # минус в PIL это поворот по часовой стрелке
        current_angle_index = angles.index(self.rotation_angle)
        self.rotation_angle = angles[(current_angle_index + 1) % len(angles)]

    def swap_wight_and_height(self):
        self.crop_width, self.crop_height = self.crop_height, self.crop_width
        lineEdit_width = self.ui.lineEdit_width.text()
        lineEdit_height = self.ui.lineEdit_height.text()
        self.ui.lineEdit_width.setText(lineEdit_height)
        self.ui.lineEdit_height.setText(lineEdit_width)
        self.create_crop_frame()

    def full_screen(self):
        if self.ui.pushButton_full_screen.text() == '⛶':
            self.ui.graphicsView_preview.hide()
            self.ui.pushButton_full_screen.setText('🗗')
        else:
            self.ui.pushButton_full_screen.setText('⛶')
            self.ui.graphicsView_preview.show()
            QTimer.singleShot(0, self.rescale_preview)
        QTimer.singleShot(0, self.rescale_main)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.rescale_preview()
        self.rescale_main()

    def set_width_height_from_button(self):
        if self.image_item:
            button = self.sender()
            name = button.objectName()

            try:
                _, width, height = name.split('_')
                self.ui.lineEdit_width.setText(width)
                self.ui.lineEdit_height.setText(height)
            except Exception as e:
                logging.error(f'Ошибка set_width_height_from_button: {e}')

    def lineedit_width_or_height_changed(self):
        error_css = """
                        QLineEdit {
                            border: 2px solid #FF6B6B;
                            color: #fa5f5f;
                        }
                    """

        error_image_css = """
                              QGraphicsView {
                                  border: 2px solid #FF6B6B;
                              }
                          """

        if self.pixmap_main is None:
            logging.debug('No image for lineedit_width_or_height_changed')
            self.statusBar().showMessage("Нет изображения.", 3000)
            self.ui.graphicsView_main.setStyleSheet(error_image_css)
            return
        else:
            self.ui.graphicsView_main.setStyleSheet('')

        try:  # width
            self.crop_width = int(self.ui.lineEdit_width.text())
            self.ui.lineEdit_width.setStyleSheet('')
            if 0 >= int(self.ui.lineEdit_width.text()) or int(
                    self.ui.lineEdit_width.text()) > self.pixmap_main.width():
                raise ValueError
        except ValueError:
            self.ui.lineEdit_width.setStyleSheet(error_css)
            logger.debug('Width is wrong')
            return

        try:  # height
            self.crop_height = int(self.ui.lineEdit_height.text())
            self.ui.lineEdit_height.setStyleSheet('')
            if 0 >= int(self.ui.lineEdit_height.text()) or int(
                    self.ui.lineEdit_height.text()) > self.pixmap_main.height():
                raise ValueError
        except ValueError:
            self.ui.lineEdit_height.setStyleSheet(error_css)
            logger.debug('Height is wrong')
            return

        self.create_crop_frame()

    def create_crop_frame(self):
        if self.crop_frame:
            self.scene.removeItem(self.crop_frame)
        if self.overlay:
            self.scene.removeItem(self.overlay)
        image_rect = self.image_item.boundingRect()
        if self.crop_width > 0 and self.crop_height > 0:
            self.crop_frame = CropFrame(QRectF(0, 0, self.crop_width, self.crop_height), bounding_rect=image_rect,
                                        on_move_callback=self.update_preview)

            self.crop_frame.color(clr=self.crop_frame_color)
            self.scene.addItem(self.crop_frame)

            self.overlay = DarkOverlay(image_rect, self.crop_frame)
            self.overlay.color(clr=self.overlay_color)
            self.scene.addItem(self.overlay)

            self.update_preview()

    def contrast(self):
        crop_frame_standard = '#FF0000'
        crop_frame_contrast = '#0000FF'
        overlay_standard = '#000000'
        overlay_contrast = '#FF00FF'
        if self.crop_frame:
            if self.ui.pushButton_contrast.text() == '◐':
                self.crop_frame.color(clr=QColor(crop_frame_contrast))
                self.overlay.color(clr=QColor(overlay_contrast))
                self.crop_frame_color = QColor(crop_frame_contrast)
                self.overlay_color = QColor(overlay_contrast)
                self.scene.removeItem(self.overlay)
                self.scene.addItem(self.overlay)
                self.ui.pushButton_contrast.setText('◑')
            else:
                self.ui.pushButton_contrast.setText('◐')
                self.crop_frame.color()
                self.overlay.color()
                self.crop_frame_color = QColor(crop_frame_standard)
                self.overlay_color = QColor(overlay_standard)
                self.scene.removeItem(self.overlay)
                self.scene.addItem(self.overlay)
        else:
            self.statusBar().showMessage(f"Нет изображения.", 2000)
            logger.debug('No frame for Contrast')

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.frame_scale = 1.005
            self.statusBar().showMessage(f"Масштабирование {self.frame_scale * 100}%", 2000)
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.frame_scale = 1.2
            self.statusBar().showMessage(f"Масштабирование {self.frame_scale * 100}%", 2000)
        super().keyReleaseEvent(event)

    def resize_frame_by_wheel(self, event):
        if self.crop_frame is None:
            return

        # Пропорции (ширина / высота), введённые пользователем
        aspect_ratio = int(self.ui.lineEdit_width.text()) / int(self.ui.lineEdit_height.text())

        delta = event.angleDelta().y()
        factor = self.frame_scale if delta > 0 else 1 / self.frame_scale

        rect = self.crop_frame.rect()
        pos = self.crop_frame.pos()

        # Новая ширина с учётом масштабирования
        new_width = rect.width() * factor
        # Новая высота рассчитывается по заданному соотношению сторон
        new_height = new_width / aspect_ratio

        # Минимальный размер рамки
        min_size = 50
        if delta < 0 and (new_width < min_size or new_height < min_size):
            return

        # Максимальные размеры, чтобы рамка не вышла за изображение
        max_width = self.pixmap_main.width() - pos.x()
        max_height = self.pixmap_main.height() - pos.y()

        # Учитываем ограничения по ширине/высоте и пересчитываем в соответствии с aspect_ratio
        if new_width > max_width:
            new_width = max_width
            new_height = new_width / aspect_ratio
        if new_height > max_height:
            new_height = max_height
            new_width = new_height * aspect_ratio

        # Применяем
        self.crop_width = int(new_width)
        self.crop_height = int(new_height)
        self.crop_frame.setRect(rect.x(), rect.y(), self.crop_width, self.crop_height)
        self.update_preview()

    def update_preview(self):
        if self.pixmap_main is None:
            logging.debug("No image for update_preview")
            return

        if self.crop_frame is None:
            logging.debug("Crop frame for update_preview")
            return

        crop_frame_XY = self.crop_frame.sceneBoundingRect()
        self.cropped_image = self.pixmap_main.copy(int(crop_frame_XY.x()) + 1, int(crop_frame_XY.y()) + 1,
                                                   self.crop_width,
                                                   self.crop_height)  # +1 это пиксель красной рамки заходящий за край
        self.frame_coordinates = (
            int(crop_frame_XY.x()) + 1, int(crop_frame_XY.y()) + 1, self.crop_width, self.crop_height)
        self.scene_preview = QGraphicsScene()
        self.scene_preview.addPixmap(self.cropped_image)
        self.ui.graphicsView_preview.setScene(self.scene_preview)
        self.rescale_preview()

    def crop_and_close(self):
        try:
            material_dict = {0: 'Холст',
                             1: 'Баннер',
                             2: 'Хлопок',
                             3: 'Матовый холст'
                             }
            material = self.ui.comboBox_material.currentIndex()
            coordinates = (
                self.frame_coordinates[0], self.frame_coordinates[1],
                self.frame_coordinates[0] + self.frame_coordinates[2],
                self.frame_coordinates[1] + self.frame_coordinates[3])
            processing = PhotoProc()
            img = self.original_image
            img = img.rotate(self.rotation_angle, expand=True)
            processing.add_image(img)
            processing.set_presets(
                number=self.ui.lineEdit_number.text(),
                width_cm=int(self.ui.lineEdit_width.text()),
                height_cm=int(self.ui.lineEdit_height.text()),
                material=material_dict[material],
                message=self.message,
                flag=False,
                coordinates=coordinates
            )
            processing.process_image()

        except Exception:
            logging.exception('Cropper error')
        finally:
            self.close()


def sendy_cropper(image=None, number='', material=0, width=None, height=None, message=None):
    app = QApplication(sys.argv)
    window = SendyCropper()
    window.showMaximized()
    window.load_image(image)
    window.set_number(number)
    window.set_width_and_height(width, height)
    window.set_bot(message)
    window.set_material(material)
    sys.exit(app.exec_())
