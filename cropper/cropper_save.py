"""Sendy Cropper - Save

This module defines the SendySave dialog window used to select a material type
for image cropping and saving within the SendyCropper workflow.

The SendySave class provides:
- UI initialization and setup (via `Ui_CropperSave`).
- Dynamic filename preview updates when hovering over material buttons.
- Button and keyboard shortcut bindings for material selection.
- Communication with the parent cropper window to trigger the crop-and-save process.

Classes:
    SendySave(QDialog): A dialog for selecting material type and confirming the save action.

Usage example:
    save_dialog = SendySave(width_height="30x40", number="001", parent=self)
    save_dialog.cropper_window = cropper_instance
    save_dialog.exec_()
"""

import logging
from functools import partial

from PyQt5.QtCore import QEvent
from PyQt5.QtWidgets import QDialog, QShortcut
from PyQt5.QtGui import QKeySequence

from cropper.save_ui import Ui_CropperSave

logger = logging.getLogger(__name__)


class SendySave(QDialog):
    def __init__(self, width_height=None, number=None, parent=None):
        super().__init__(parent)
        self.width_height = width_height
        self.number = number
        self.cropper_window = None
        self.ui = Ui_CropperSave()
        self.ui.setupUi(self)
        self.ui.pushButton_canvas.installEventFilter(self)
        self.ui.pushButton_banner.installEventFilter(self)
        self.ui.pushButton_cotton.installEventFilter(self)
        self.ui.pushButton_matte.installEventFilter(self)

        self.ui.pushButton_canvas.clicked.connect(partial(self.button_material_pushed, 0))
        self.ui.pushButton_banner.clicked.connect(partial(self.button_material_pushed, 1))
        self.ui.pushButton_cotton.clicked.connect(partial(self.button_material_pushed, 2))
        self.ui.pushButton_matte.clicked.connect(partial(self.button_material_pushed, 3))

        QShortcut(QKeySequence("1"), self).activated.connect(partial(self.button_material_pushed, 0))
        QShortcut(QKeySequence("2"), self).activated.connect(partial(self.button_material_pushed, 1))
        QShortcut(QKeySequence("3"), self).activated.connect(partial(self.button_material_pushed, 2))
        QShortcut(QKeySequence("4"), self).activated.connect(partial(self.button_material_pushed, 3))

        self.ui.filename.setText(f'{self.width_height} {self.number} _______.jpg')

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Enter:
            if obj == self.ui.pushButton_canvas:
                self.ui.filename.setText(f'{self.width_height} {self.number} Холст.jpg')
            elif obj == self.ui.pushButton_banner:
                self.ui.filename.setText(f'_{self.width_height} {self.number} Баннер.jpg')
            elif obj == self.ui.pushButton_cotton:
                self.ui.filename.setText(f'{self.width_height} {self.number} Хлопок.jpg')
            elif obj == self.ui.pushButton_matte:
                self.ui.filename.setText(f'@{self.width_height} {self.number} Матовый холст.jpg')

        elif event.type() == QEvent.Leave:
            self.ui.filename.setText(f'{self.width_height} {self.number} _______.jpg')

        return super().eventFilter(obj, event)

    def button_material_pushed(self, material):
        if self.cropper_window:
            self.cropper_window.crop_and_close(material=material)
