import logging
from pathlib import Path

from PyQt5.QtWidgets import QDialog, QFileDialog

from cropper.settings_ui import Ui_SendySettings
from data import data

logger = logging.getLogger(__name__)


class SendySettings(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.main_window = parent
        self.ui = Ui_SendySettings()
        self.ui.setupUi(self)
        self.ui.pushButton_set_photo_processing_path.clicked.connect(self.browse_button_photo_processing_path_pushed)
        self.ui.pushButton_settings_apply.clicked.connect(self.button_apply_settings_pushed)

        self.ui.lineEdit_photo_processing_path.setText(str(data.photo_processing_path))
        self.ui.lineEdit_photo_processing_wrap.setText(str(data.photo_processing_wrap_cm))
        self.ui.lineEdit_photo_processing_white.setText(str(data.photo_processing_white_cm))
        self.ui.lineEdit_photo_processing_black.setText(str(data.photo_processing_black_px))
        self.ui.lineEdit_photo_processing_dpi.setText(str(data.photo_processing_dpi))
        self.ui.lineEdit_photo_processing_fontsize.setText(str(data.photo_processing_font_size_px))
        self.ui.lineEdit_photo_processing_crop.setText(str(data.photo_processing_crop_px))

        current_theme = {':/cropper_bright.css': 0, ':/cropper_dark.css': 1}
        self.ui.comboBox_theme.setCurrentIndex(current_theme[data.cropper_css])

    def browse_button_photo_processing_path_pushed(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку",
            "",
            QFileDialog.ShowDirsOnly
        )
        if folder:
            self.ui.lineEdit_photo_processing_path.setText(folder)

    def button_apply_settings_pushed(self):
        data.photo_processing_path = Path(self.ui.lineEdit_photo_processing_path.text())
        data.photo_processing_wrap_cm = float(self.ui.lineEdit_photo_processing_wrap.text())
        data.photo_processing_white_cm = float(self.ui.lineEdit_photo_processing_white.text())
        data.photo_processing_black_px = int(self.ui.lineEdit_photo_processing_black.text())
        data.photo_processing_dpi = int(self.ui.lineEdit_photo_processing_dpi.text())
        data.photo_processing_font_size_px = int(self.ui.lineEdit_photo_processing_fontsize.text())
        data.photo_processing_crop_px = int(self.ui.lineEdit_photo_processing_crop.text())

        themes = {0: ':/cropper_bright.css', 1: ':/cropper_dark.css'}
        data.cropper_css = themes[self.ui.comboBox_theme.currentIndex()]
        self.main_window.set_CSS()

        data.save()
        self.accept()