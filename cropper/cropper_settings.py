import logging

from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtCore import QFile, QTextStream
from PyQt5.QtGui import QIcon

from cropper.settings_ui import Ui_SendySettings

logger = logging.getLogger(__name__)


class SendySettings(QDialog, Ui_SendySettings):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)