import logging

from PyQt5.QtWidgets import QDialog, QFileDialog

from cropper.settings_ui import Ui_SendySettings
from data.data import data, Data

logger = logging.getLogger(__name__)


class SendySettings(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.main_window = parent
        self.ui = Ui_SendySettings()
        self.ui.setupUi(self)
        self.ui.pushButton_set_photo_processing_path.clicked.connect(self.browse_button_photo_processing_path_pushed)
        self.ui.pushButton_settings_apply.clicked.connect(self.button_apply_settings_pushed)
        self.ui.lineEdit_photo_processing_path.setText(data['photo_processing_path'])
        self.ui.lineEdit_photo_processing_zav.setText(data['photo_processing_zav'])
        self.ui.lineEdit_photo_processing_white.setText(data['photo_processing_white'])
        self.ui.lineEdit_photo_processing_black.setText(data['photo_processing_black'])
        self.ui.lineEdit_photo_processing_dpi.setText(data['photo_processing_dpi'])
        self.ui.lineEdit_photo_processing_fontsize.setText(data['photo_processing_fontsize'])
        self.ui.lineEdit_photo_processing_crop.setText(data['photo_processing_crop'])

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
        data['photo_processing_path'] = self.ui.lineEdit_photo_processing_path.text()
        data['photo_processing_zav'] = self.ui.lineEdit_photo_processing_zav.text()
        data['photo_processing_white'] = self.ui.lineEdit_photo_processing_white.text()
        data['photo_processing_black'] = self.ui.lineEdit_photo_processing_black.text()
        data['photo_processing_dpi'] = self.ui.lineEdit_photo_processing_dpi.text()
        data['photo_processing_fontsize'] = self.ui.lineEdit_photo_processing_fontsize.text()
        data['photo_processing_crop'] = self.ui.lineEdit_photo_processing_crop.text()
        themes = {0: ':/cropper_bright.css', 1: ':/cropper_dark.css'}
        Data.cropper_css = themes[self.ui.comboBox_theme.currentIndex()]
        self.main_window.set_CSS()
        self.accept()