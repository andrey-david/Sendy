import sys
import logging
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QGraphicsScene,
    QGraphicsPixmapItem,
    QShortcut,
    QFileDialog,
)
from PyQt5.QtGui import (
    QPixmap,
    QTransform,
    QKeySequence,
    QColor,
    QImage,
    QIcon
)
from PyQt5.QtCore import (
    QRectF,
    Qt,
    QFile,
    QTextStream,
    QTimer
)
from PIL import Image
import pillow_heif
import io

from cropper.cropper_help import SendyHelp
from cropper.cropper_ui import Ui_Cropper
from cropper.cropper_settings import SendySettings
from cropper.cropper_save import SendySave
from cropper.cropper_crop_frame import CropFrame, DarkOverlay, ResizeHandle, WheelFilter
from data import data
from photo_processing import PhotoProc
import resources_rc

logger = logging.getLogger(__name__)


class SendyCropper(QMainWindow):
    def __init__(self):
        super().__init__()

        # Window configuration
        self.setAcceptDrops(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setWindowIcon(self.load_icon())
        self.frame_scale = 1.2

        # UI setup
        self.ui = Ui_Cropper()
        self.ui.setupUi(self)

        # Load QSS
        self.set_QSS()

        # Internal state variables
        _instance = None  # static instance for single window

        self.pixmap_main = None
        self.image_item = None
        self.original_image = None
        self.cropped_image = None
        self.cropped_result_image = None
        self.result = None

        self.rotation_angle = 0
        self.crop_width = 0
        self.crop_height = 0
        self.frame_coordinates = (0, 0, 0, 0)

        # Colors
        self.crop_frame_color = QColor("#FF0000")
        self.overlay_color = QColor("#000000")

        # Graphics scenes
        self.scene = QGraphicsScene()
        self.scene_preview = QGraphicsScene()

        # Graphics items
        self.crop_frame = None
        self.overlay = None
        self.resize_handle = None

        # Event filters
        self.wheel_filter = WheelFilter(self)
        self.ui.graphicsView_main.installEventFilter(self.wheel_filter)

        # Secondary windows
        self.settings_window = None
        self.save_window = None
        self.help_window = None

        # Buttons connections
        self.ui.pushButton_rotate.clicked.connect(self.rotate_image)
        self.ui.pushButton_contrast.clicked.connect(self.contrast)
        self.ui.pushButton_swap.clicked.connect(self.swap_wight_and_height)
        self.ui.pushButton_full_screen.clicked.connect(self.full_screen)
        self.ui.pushButton_test.clicked.connect(self.test)
        self.ui.pushButton_crop.clicked.connect(self.crop_and_close)

        # Line edits connections
        self.ui.lineEdit_width.textChanged.connect(self.lineedit_width_or_height_changed)
        self.ui.lineEdit_height.textChanged.connect(self.lineedit_width_or_height_changed)

        # Keyboard shortcuts
        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(self.rotate_image)
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(self.full_screen)
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self.swap_wight_and_height)
        QShortcut(QKeySequence("Ctrl+C"), self).activated.connect(self.contrast)
        QShortcut(QKeySequence("Ctrl+T"), self).activated.connect(self.test)
        QShortcut(QKeySequence("F3"), self).activated.connect(self.save)

        # Menu actions
        self.ui.action_open.triggered.connect(self.open_file_dialog)
        self.ui.action_settings.triggered.connect(self.open_settings)
        self.ui.action_save.triggered.connect(self.save)
        self.ui.action_about.triggered.connect(self.help)

        # Size collection
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

    # UI
    def set_QSS(self):
        try:
            qss_file = QFile(data.cropper_css)
            if not qss_file.exists():
                logger.error('No QSS file in resources')
                return

            if qss_file.open(QFile.ReadOnly | QFile.Text):
                stream = QTextStream(qss_file)
                qss = stream.readAll()
                qss_file.close()
                logger.debug('QSS is loaded')
                QApplication.instance().setStyleSheet(qss)
            else:
                logger.error('Cannot open QSS file')
                return

        except Exception:
            logger.exception(f'Cannot load QSS')
            return

    def load_icon(self):
        if QFile.exists(":/sendy.ico"):
            return QIcon(":/sendy.ico")
        logger.error('No icon in resources')
        return QIcon()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.width() < 1500:
            self.ui.sizes.hide()
            self.ui.graphicsView_preview.hide()
            self.ui.pushButton_full_screen.setText('🗗')
        else:
            self.ui.sizes.show()
            self.ui.graphicsView_preview.show()
            self.ui.pushButton_full_screen.setText('⛶')
        self.rescale_main()
        self.rescale_preview()

    # Set image and other presets
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
        if self.pixmap_main:
            self.scene.setSceneRect(0, 0, self.pixmap_main.width(), self.pixmap_main.height())
        self.scene.addItem(self.image_item)
        self.ui.graphicsView_main.setScene(self.scene)
        self.rescale_main()

    def open_file_dialog(self):
        image_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл",
            "",
            "Изображения (*.jpg *.png *.heic);;Все файлы (*)"
        )
        if image_path:
            self.open_file(image_path)
        else:
            self.statusBar().showMessage("Ошибка при открытии файла", 3000)

    def open_file(self, image_path):
        try:
            self.scene.clear()
            self.crop_frame = None
            self.overlay = None
            self.resize_handle = None
            self.rotation_angle = 0
            self.ui.graphicsView_main.setScene(None)
            self.scene_preview.clear()
            self.ui.graphicsView_preview.setScene(None)
            pillow_heif.register_heif_opener()
            Image.MAX_IMAGE_PIXELS = None
            image = Image.open(image_path).convert("RGB")
            if not image:
                logging.info('Не удалось загрузить изображение')
                self.statusBar().showMessage("Не удалось загрузить изображение", 3000)
                return
            self.load_image(image)
            self.ui.graphicsView_main.setStyleSheet('')
        except:
            logger.exception('load image error')
            self.statusBar().showMessage("Ошибка при открытии файла", 3000)

    def set_number(self, number):
        self.ui.lineEdit_number.setText(str(number))

    def set_material(self, material):
        material_dict = {
            'Холст': 0,
            'Баннер': 1,
            'Хлопок': 2,
            'Матовый холст': 3
        }
        self.ui.comboBox_material.setCurrentIndex(material_dict[material])

    def set_width_and_height(self, width, height):
        if width and height:
            self.ui.lineEdit_width.setText(str(width))
            self.ui.lineEdit_height.setText(str(height))

    # Drag and drop
    def dragEnterEvent(self, event):
        drag_image_qss = """
                                      QGraphicsView {
                                          background-color: #232c3b;
                                          border: 2px solid #0078d7;
                                      }
                                  """

        if event.mimeData().hasUrls():
            self.ui.graphicsView_main.setScene(None)
            self.ui.graphicsView_main.setStyleSheet(drag_image_qss)
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        global_pos = self.mapToGlobal(event.pos())
        win_rect = self.frameGeometry()

        if not win_rect.contains(global_pos):
            self.ui.graphicsView_main.setStyleSheet('')
            self.ui.graphicsView_main.setScene(self.scene)

        event.accept()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.open_file(file_path)
        self.ui.graphicsView_main.setStyleSheet('')

    # Secondary windows
    def open_settings(self):
        try:
            if self.settings_window is None:
                self.settings_window = SendySettings(self)
            self.settings_window.exec_()
        except Exception as e:
            logger.exception(f'open_settings: {e}')

    def save(self):
        try:
            if self.save_window is None and self.crop_frame:
                number = self.ui.lineEdit_number.text()
                width_height = f'{self.ui.lineEdit_width.text()}х{self.ui.lineEdit_height.text()}'
                self.save_window = SendySave(width_height=width_height, number=number, parent=self)
                self.save_window.cropper_window = self
                self.save_window.show()
            else:
                self.statusBar().showMessage("Нечего сохранять", 3000)
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

    # Graphics View
    @staticmethod
    def rescale_graphics_view(graphics_view, image_width, image_height, hide_scroll_factor):
        view_width = graphics_view.width()
        view_height = graphics_view.height()
        scale = min((view_width / image_width), (view_height / image_height)) - hide_scroll_factor

        graphics_view.resetTransform()
        graphics_view.scale(scale, scale)

    def rescale_main(self):
        if self.pixmap_main is None:
            logging.debug('No image for rescale main')
            return

        self.rescale_graphics_view(self.ui.graphicsView_main,
                                   self.image_item.pixmap().width(),
                                   self.image_item.pixmap().height(),
                                   0.005
                                   )

    def rescale_preview(self):
        if self.cropped_image is None:
            logging.debug('No image for preview rescale')
            return

        self.rescale_graphics_view(self.ui.graphicsView_preview,
                                   self.cropped_image.width(),
                                   self.cropped_image.height(),
                                   0.05
                                   )

    def update_preview(self):
        if self.pixmap_main is None:
            logging.debug("No image for update_preview")
            return

        if self.crop_frame is None:
            logging.debug("No crop frame for update_preview")
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
        self.resize_handle.update_position()
        self.rescale_preview()

    # Tool buttons
    def rotate_image(self):
        error_image_qss = """
                              QGraphicsView {
                                  border: 2px solid #FF6B6B;
                              }
                          """

        if self.pixmap_main is None:
            logging.debug('No image for rotation')
            self.statusBar().showMessage("Нет изображения для поворота.", 2000)
            self.ui.graphicsView_main.setStyleSheet(error_image_qss)
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

    def contrast(self):
        crop_frame_standard = '#FF0000'
        crop_frame_contrast = '#0000FF'
        overlay_standard = '#000000'
        overlay_contrast = '#FF00FF'
        if self.crop_frame:
            if self.ui.pushButton_contrast.text() == '◐':
                self.crop_frame.color(clr=QColor(crop_frame_contrast))
                self.overlay.color(clr=QColor(overlay_contrast))
                self.resize_handle.color(clr=QColor(crop_frame_contrast))
                self.crop_frame_color = QColor(crop_frame_contrast)
                self.overlay_color = QColor(overlay_contrast)
                self.scene.removeItem(self.overlay)
                self.scene.addItem(self.overlay)
                self.ui.pushButton_contrast.setText('◑')
            else:
                self.ui.pushButton_contrast.setText('◐')
                self.crop_frame.color()
                self.overlay.color()
                self.resize_handle.color()
                self.crop_frame_color = QColor(crop_frame_standard)
                self.overlay_color = QColor(overlay_standard)
                self.scene.removeItem(self.overlay)
                self.scene.addItem(self.overlay)
        else:
            self.statusBar().showMessage(f"Нет изображения.", 2000)
            logger.debug('No frame for Contrast')

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
        error_qss = """
                        QLineEdit {
                            border: 2px solid #FF6B6B;
                            color: #fa5f5f;
                        }
                    """

        error_image_qss = """
                              QGraphicsView {
                                  border: 2px solid #FF6B6B;
                              }
                          """

        if self.pixmap_main is None:
            logging.debug('No image for lineedit_width_or_height_changed')
            self.statusBar().showMessage("Нет изображения.", 3000)
            self.ui.graphicsView_main.setStyleSheet(error_image_qss)
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
            self.ui.lineEdit_width.setStyleSheet(error_qss)
            if self.crop_frame:
                self.scene.removeItem(self.crop_frame)
            if self.overlay:
                self.scene.removeItem(self.overlay)
            logger.debug('Width is wrong')
            return

        try:  # height
            self.crop_height = int(self.ui.lineEdit_height.text())
            self.ui.lineEdit_height.setStyleSheet('')
            if 0 >= int(self.ui.lineEdit_height.text()) or int(
                    self.ui.lineEdit_height.text()) > self.pixmap_main.height():
                raise ValueError
        except ValueError:
            self.ui.lineEdit_height.setStyleSheet(error_qss)
            if self.crop_frame:
                self.scene.removeItem(self.crop_frame)
            if self.overlay:
                self.scene.removeItem(self.overlay)
            logger.debug('Height is wrong')
            return

        self.create_crop_frame()

    # Crop frame
    def create_crop_frame(self):
        if self.crop_frame:
            self.scene.removeItem(self.crop_frame)
        if self.overlay:
            self.scene.removeItem(self.overlay)
        if self.resize_handle:
            self.scene.removeItem(self.resize_handle)

        image_rect = self.image_item.boundingRect()

        if self.crop_width <= 20:
            scale = 30
        elif self.crop_width <= 50:
            scale = 22
        else:
            scale = 20

        self.crop_width = self.crop_width * scale
        self.crop_height = self.crop_height * scale

        if self.crop_width > 0 and self.crop_height > 0:
            self.crop_frame = CropFrame(QRectF(0, 0, self.crop_width, self.crop_height),
                                        bounding_rect=image_rect,
                                        on_move_callback=self.update_preview
                                        )
            self.crop_frame.color(clr=self.crop_frame_color)
            self.scene.addItem(self.crop_frame)

            self.overlay = DarkOverlay(image_rect, self.crop_frame)
            self.overlay.color(clr=self.overlay_color)
            self.scene.addItem(self.overlay)

            self.resize_handle = ResizeHandle(self, self.crop_frame)
            self.resize_handle.color(clr=self.crop_frame_color)
            self.scene.addItem(self.resize_handle)

            self.update_preview()

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

    def resize_by_wheel(self, event):
        if self.crop_frame is None:
            return

        rect = self.crop_frame.rect()
        delta = event.angleDelta().y()
        factor = self.frame_scale if delta > 0 else 1 / self.frame_scale

        new_width = rect.width() * factor
        new_height = rect.height()

        self.resize_crop_frame(new_width, new_height)

    def resize_by_handle(self, delta_x, delta_y):
        new_width = delta_x
        new_height = delta_y

        self.resize_crop_frame(new_width, new_height)

    def resize_crop_frame(self, new_width, new_height):
        if self.crop_frame is None:
            return

        rect = self.crop_frame.rect()
        pos = self.crop_frame.pos()

        shift_modifier = QApplication.keyboardModifiers() & Qt.ShiftModifier

        if not shift_modifier:
            aspect_ratio = int(self.ui.lineEdit_width.text()) / int(self.ui.lineEdit_height.text())
            new_height = new_width / aspect_ratio

            max_width = self.pixmap_main.width() - pos.x()
            max_height = self.pixmap_main.height() - pos.y()

            if new_width > max_width:
                new_width = max_width
                new_height = new_width / aspect_ratio

            if new_height > max_height:
                new_height = max_height
                new_width = new_height * aspect_ratio

        min_size = 10
        if new_width < min_size or new_height < min_size:
            return

        self.crop_width = int(new_width)
        self.crop_height = int(new_height)
        self.crop_frame.setRect(rect.x(), rect.y(), self.crop_width, self.crop_height)

        self.update_preview()

    # On Test button
    def test(self):
        if not self.crop_frame:
            return

        coordinates = (
            self.frame_coordinates[0],
            self.frame_coordinates[1],
            self.frame_coordinates[0] + self.frame_coordinates[2],
            self.frame_coordinates[1] + self.frame_coordinates[3]
        )

        img = self.original_image
        img = img.rotate(self.rotation_angle, expand=True)

        process_image = PhotoProc()
        process_image.presets(
            image=img,
            number=self.ui.lineEdit_number.text(),
            width_cm=int(self.ui.lineEdit_width.text()),
            height_cm=int(self.ui.lineEdit_height.text()),
            material=None,
            coordinates=coordinates
        )
        process_image.set_dpi(150)

        preview = process_image.get_result_image()

        def pil_image_to_pixmap(pil_image):
            buffer = io.BytesIO()
            pil_image.save(buffer, format="PNG")
            qimage = QImage()
            qimage.loadFromData(buffer.getvalue(), "PNG")
            return QPixmap.fromImage(qimage)

        if isinstance(preview, Image.Image):
            preview = pil_image_to_pixmap(preview)

        self.scene_preview = QGraphicsScene()
        self.scene_preview.addItem(QGraphicsPixmapItem(preview))
        self.ui.graphicsView_preview.setScene(self.scene_preview)

        view_width = self.ui.graphicsView_preview.width()
        view_height = self.ui.graphicsView_preview.height()

        scale = min((view_width / preview.width()), (view_height / preview.height())) - 0.03

        self.ui.graphicsView_preview.resetTransform()
        self.ui.graphicsView_preview.scale(scale, scale)

    # On Crop button
    def crop_and_close(self, material=None):
        try:
            material_dict = {0: 'Холст',
                             1: 'Баннер',
                             2: 'Хлопок',
                             3: 'Матовый холст'
                             }
            if not material:
                material = self.ui.comboBox_material.currentIndex()

            coordinates = (
                self.frame_coordinates[0],
                self.frame_coordinates[1],
                self.frame_coordinates[0] + self.frame_coordinates[2],
                self.frame_coordinates[1] + self.frame_coordinates[3]
            )

            img = self.original_image
            img = img.rotate(self.rotation_angle, expand=True)
            result_dict = {
                'image': img,
                'number': self.ui.lineEdit_number.text(),
                'width_cm': int(self.ui.lineEdit_width.text()),
                'height_cm': int(self.ui.lineEdit_height.text()),
                'material': material_dict[material],
                'coordinates': coordinates
            }

            self.result = result_dict

        except Exception as e:
            logging.exception('Cropper error', e)
            return Path()
        finally:
            self.close()


def sendy_cropper(
        image=None,
        number='',
        material='Холст',
        width=None,
        height=None,
):
    try:
        app = QApplication(sys.argv)
        window = SendyCropper()
        window.showMaximized()
        window.load_image(image)
        window.set_number(number)
        window.set_width_and_height(width, height)
        window.set_material(material)
        app.exec_()

        return window.result
    except:
        logger.exception('Cropper error')


if __name__ == '__main__':
    sendy_cropper()
