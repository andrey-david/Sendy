import logging

from PyQt5.QtWidgets import QDialog
from PyQt5.QtGui import QPixmap

from cropper.help_ui import Ui_CropperHelp

logger = logging.getLogger(__name__)


class SendyHelp(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_CropperHelp()
        self.ui.setupUi(self)
        self.ui.label_logo.setPixmap(QPixmap(":/sendy.ico"))