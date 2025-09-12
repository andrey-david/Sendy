import logging

from PyQt5.QtWidgets import QDialog, QShortcut
from PyQt5.QtGui import QKeySequence

from cropper.save_ui import Ui_CropperSave

logger = logging.getLogger(__name__)


class SendySave(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_CropperSave()
        self.ui.setupUi(self)
        self.ui.pushButton_canvas.clicked.connect(self.button_canvas_pushed)
        self.ui.pushButton_banner.clicked.connect(self.button_banner_pushed)
        self.ui.pushButton_cotton.clicked.connect(self.button_cotton_pushed)
        self.ui.pushButton_matte.clicked.connect(self.button_matte_pushed)
        QShortcut(QKeySequence("1"), self).activated.connect(self.button_canvas_pushed)
        QShortcut(QKeySequence("2"), self).activated.connect(self.button_banner_pushed)
        QShortcut(QKeySequence("3"), self).activated.connect(self.button_cotton_pushed)
        QShortcut(QKeySequence("4"), self).activated.connect(self.button_matte_pushed)

    def button_canvas_pushed(self):
        print('1')

    def button_banner_pushed(self):
        print('2')

    def button_cotton_pushed(self):
        print('3')

    def button_matte_pushed(self):
        print('4')
