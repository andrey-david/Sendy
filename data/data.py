import os
import logging
from dataclasses import dataclass, field
from pathlib import Path

import pickle
from aiogram.types import Message

logger = logging.getLogger(__name__)


@dataclass
class Data:
    image_loader_path: Path = Path(r'D:\MyPY\Sendy\Новая папка\photos')

    image_counter_path: Path = Path(r'D:\MyPY\Sendy\Alextest')
    image_counter_exceptions: list[str] = field(default_factory=list)

    photo_processing_path: Path = Path(r'D:\MyPY\Sendy\photo_processing')
    photo_processing_wrap_cm: float = 4.5
    photo_processing_white_cm: float = 0.8
    photo_processing_black_px: int = 1
    photo_processing_dpi: str = 300
    photo_processing_crop_px: str = 8
    photo_processing_font_size_px: int = 85

    cropper_css: str = ':/cropper_bright.css'

test = Data
data = {}


def load_sendy_data():
    global data
    if not os.path.exists('sendy.data'):
        # data = data_default.copy()
        with open('sendy.data', 'wb') as f:
            pickle.dump(data, f)
        return

    try:
        with open('sendy.data', 'rb') as f:
            data = pickle.load(f)

        updated = False
        # for key, value in data_default.items():
        #     if key not in data:
        #         data[key] = value
        #         updated = True

        if updated:
            with open("sendy.data", "wb") as file:
                pickle.dump(data, file)

    except Exception:
        logger.exception('Data error')
        # with open("sendy.data", "wb") as file:
        #     pickle.dump(data_default, file)


load_sendy_data()


async def save_to_data(key, value, message: Message):
    try:
        data[key] = value
        with open('sendy.data', 'wb') as f:
            pickle.dump(data, f)
    except Exception as e:
        logging.error(f"Ошибка при сохранении: {e}")
        await message.answer(f"💀 Ошибка при сохранении: {e}")


if __name__ == '__main__':
    load_sendy_data()
