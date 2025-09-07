import pickle
from aiogram.types import Message
import os
import logging

logger = logging.getLogger(__name__)

data = {}

data_default = {
    'path': r'D:\MyPY\Sendy\Новая папка\photos',
    'Alex_path': r'D:\MyPY\Sendy\Alextest',
    'Alex_exceptions': [],
    'photo_processing_path': r'D:\MyPY\Sendy\photo_processing',
    'photo_processing_zav': '4.5',
    'photo_processing_white': '0.8',
    'photo_processing_dpi': '300',
    'photo_processing_black': '1',
    'photo_processing_fontsize': '50',
    'photo_processing_crop': '8'
}


def load_sendy_data():
    global data
    if not os.path.exists('sendy.data'):
        data = data_default.copy()
        with open('sendy.data', 'wb') as f:
            pickle.dump(data, f)
        return

    try:
        with open('sendy.data', 'rb') as f:
            data = pickle.load(f)

        updated = False
        for key, value in data_default.items():
            if key not in data:
                data[key] = value
                updated = True

        if updated:
            with open("sendy.data", "wb") as file:
                pickle.dump(data, file)

    except Exception as e:
        # Сохраняем настройки по умолчанию
        with open("sendy.data", "wb") as file:
            pickle.dump(data_default, file)


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
