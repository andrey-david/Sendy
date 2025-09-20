import logging
from pathlib import Path
import sys
from functools import partial

from PyQt5.QtWidgets import QDialog, QFileDialog, QListWidgetItem
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtCore import Qt, QFile, QTextStream

from cropper.settings_ui import Ui_SendySettings
from data import data

logger = logging.getLogger(__name__)


class SendySettings(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.ui = Ui_SendySettings()
        self.ui.setupUi(self)
        self.ui.pushButton_set_photo_processing_path.clicked.connect(partial(self.button_browse_pushed,
                                                                             self.ui.lineEdit_photo_processing_path))
        self.ui.pushButton_set_image_counter_path.clicked.connect(partial(self.button_browse_pushed,
                                                                  self.ui.lineEdit_image_counter_path))
        self.ui.pushButton_set_image_loader_path.clicked.connect(partial(self.button_browse_pushed,
                                                                 self.ui.lineEdit_image_loader_path))
        self.ui.pushButton_image_counter_exceptions_add_elem.clicked.connect(self.image_counter_exceptions_add_item)
        self.ui.lineEdit_image_counter_exceptions_add_elem.returnPressed.connect(self.image_counter_exceptions_add_item)
        self.ui.pushButton_settings_apply.clicked.connect(self.button_apply_settings_pushed)
        self.fill_values()

    def keyPressEvent(self, event):
        exceptions = self.ui.listWidget_image_counter_exceptions
        if event.key() == Qt.Key_Delete:
            if self.focusWidget() == exceptions:
                item = exceptions.currentItem()
                if item:
                    row = exceptions.row(item)
                    exceptions.takeItem(row)

    def closeEvent(self, event: QCloseEvent):
        self.ui.listWidget_image_counter_exceptions.clear()
        self.fill_values()
        super().closeEvent(event)

    def fill_values(self):
        # main
        current_theme = {':/cropper_bright.css': 0, ':/cropper_dark.css': 1}
        self.ui.comboBox_theme.setCurrentIndex(current_theme[data.cropper_css])

        # photo processing
        self.ui.lineEdit_photo_processing_path.setText(str(data.photo_processing_path))
        self.ui.lineEdit_photo_processing_wrap.setText(str(data.photo_processing_wrap_cm))
        self.ui.lineEdit_photo_processing_white.setText(str(data.photo_processing_white_cm))
        self.ui.lineEdit_photo_processing_black.setText(str(data.photo_processing_black_px))
        self.ui.lineEdit_photo_processing_dpi.setText(str(data.photo_processing_dpi))
        self.ui.lineEdit_photo_processing_fontsize.setText(str(data.photo_processing_font_size_px))
        self.ui.lineEdit_photo_processing_crop.setText(str(data.photo_processing_crop_px))

        # image counter
        self.ui.lineEdit_image_counter_path.setText(str(data.image_counter_path))
        self.ui.listWidget_image_counter_exceptions.addItems(data.image_counter_exceptions)
        self.ui.listWidget_image_counter_exceptions.itemDoubleClicked.connect(self.exceptions_edit_item)

        # image loader
        self.ui.lineEdit_image_loader_path.setText(str(data.image_loader_path))

    def button_browse_pushed(self, lineedit):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку",
            "",
            QFileDialog.ShowDirsOnly
        )
        if folder:
            lineedit.setText(folder)

    def image_counter_exceptions_add_item(self):
        text = self.ui.lineEdit_image_counter_exceptions_add_elem.text()
        item = QListWidgetItem(text)
        if text:
            self.ui.listWidget_image_counter_exceptions.addItem(item)
            self.ui.listWidget_image_counter_exceptions.scrollToItem(item)
            self.ui.listWidget_image_counter_exceptions.setCurrentItem(item)
            self.ui.lineEdit_image_counter_exceptions_add_elem.setText('')

    def exceptions_edit_item(self, item):
        self.ui.lineEdit_image_counter_exceptions_add_elem.setText(item.text())
        self.ui.listWidget_image_counter_exceptions.takeItem(
            self.ui.listWidget_image_counter_exceptions.row(item))

    def button_apply_settings_pushed(self):
        # main
        themes = {0: ':/cropper_bright.css', 1: ':/cropper_dark.css'}
        data.cropper_css = themes[self.ui.comboBox_theme.currentIndex()]
        self.main_window.set_CSS()

        # photo processing
        data.photo_processing_path = Path(self.ui.lineEdit_photo_processing_path.text())
        data.photo_processing_wrap_cm = float(self.ui.lineEdit_photo_processing_wrap.text())
        data.photo_processing_white_cm = float(self.ui.lineEdit_photo_processing_white.text())
        data.photo_processing_black_px = int(self.ui.lineEdit_photo_processing_black.text())
        data.photo_processing_dpi = int(self.ui.lineEdit_photo_processing_dpi.text())
        data.photo_processing_font_size_px = int(self.ui.lineEdit_photo_processing_fontsize.text())
        data.photo_processing_crop_px = int(self.ui.lineEdit_photo_processing_crop.text())

        # image counter
        list_widget = self.ui.listWidget_image_counter_exceptions
        data.image_counter_exceptions = [list_widget.item(i).text() for i in range(list_widget.count())]

        data.save()
        self.accept()

    def set_CSS(self):
        try:
            qss_file = QFile(':/cropper_dark.css')
            if not qss_file.exists():
                logger.error('No CSS file in resources')
                return

            if qss_file.open(QFile.ReadOnly | QFile.Text):
                stream = QTextStream(qss_file)
                qss = stream.readAll()
                qss_file.close()
                logger.debug('CSS is loaded')
                QApplication.instance().setStyleSheet(qss)
            else:
                logger.error('Cannot open CSS file')
                return

        except Exception:
            logger.exception(f'Cannot load CSS')
            return


if __name__ == '__main__':
    import resources_rc

    app = QApplication(sys.argv)
    dlg = SendySettings()
    dlg.set_CSS()
    dlg.exec_()
    sys.exit(0)
