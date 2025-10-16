"""Data - Storage for Sendy

This class stores all user-editable configuration data for the Sendy application,
such as paths, image processing parameters, and UI preferences.
The configuration can be saved to disk and loaded back using pickle.

data = Data.load() - is singleton instance

Usage:
    from data import data

    data.photo_processing_wrap_cm = 5.0
    data.save()  # If you need to save to a file via pickle

Attributes:
    image_loader_path (Path): Path where images are loaded from, and then sent to the user's chat.

    image_counter_path (Path): Path used for counting images.
    image_counter_exceptions (list[str]): List of files or folders to exclude from counting.

    photo_processing_path (Path): Path where processed photos are saved.
    photo_processing_wrap_cm (float): Width of wrap in centimeters.
    photo_processing_white_cm (float): Width of white border in centimeters.
    photo_processing_black_px (int): Width of black border in pixels.
    photo_processing_dpi (int): Output resolution in DPI.
    photo_processing_crop_px (int): Cropping border of image in pixels.
    photo_processing_font_size_px (int): Font size in pixels for nuber on image.

    cropper_css (str): Path to the stylesheet used by the Cropper windows.

Methods:
    save(): Saves current configuration to `sendy.data`.
    load(): Loads configuration from `sendy.data`. If the file does not exist, creates a new one with default values.
"""

import os
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
import pickle

from config import config

logger = logging.getLogger(__name__)


@dataclass
class Data:
    image_loader_path: Path = Path(r'C:\Users\PrinterPC\OneDrive\Pictures\CameraRoll')

    image_counter_path: Path = Path(r'D:\Печать\Фото')
    image_counter_exceptions: list[str] = field(default_factory=lambda: ['Макеты', 'макеты', '_Макеты', '_макеты', 'BOT', 'отмены'])

    photo_processing_path: Path = Path(r'D:\Печать\Фото\BOT')
    photo_processing_wrap_cm: float = 2.8
    photo_processing_white_cm: float = 1.2
    photo_processing_black_px: int = 4
    photo_processing_dpi: int = 300
    photo_processing_crop_px: int = 9
    photo_processing_font_size_px: int = 85

    cropper_css: str = ':/cropper_bright.css'

    def save(self):
        data_path = os.path.join(config.app_dir, 'sendy.data')

        with open(data_path, 'wb') as file:
            pickle.dump(asdict(self), file)

    @classmethod
    def load(cls):
        data_path = os.path.join(config.app_dir, 'sendy.data')

        if not os.path.exists(data_path):
            with open(data_path, 'wb') as file:
                pickle.dump(asdict(cls()), file)
            return cls()
        try:
            with open(data_path, 'rb') as file:
                data_from_pickle = pickle.load(file)
                return cls(**data_from_pickle)
        except (EOFError, pickle.UnpicklingError):
            logger.warning("Data corrupted. Resetting to defaults.")
            return cls()


data = Data.load()
