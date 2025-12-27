"""
Settings Lexicon
----------------

Provides all texts, prompts, and button labels for the settings section of the Sendy bot.

Contents:
    • `settings_lexicon`: Texts for user prompts, confirmations, and error messages.
    • `settings_main_btns`, `settings_image_loader_btns`, etc.: Button labels for inline keyboards.

Usage:
    Import this module and use dict's to display text or btn's to create keyboards.
"""

import logging

from data import data

logger = logging.getLogger(__name__)

settings_lexicon: dict[str, str] = {
    'settings_main_text': '⚙️ <b>НАСТРОЙКИ</b>\n',

    'photo_processing_wrap_cm': 'Введите заворот для фото в сантиметрах:',
    'photo_processing_white_cm': 'Введите размеры белой рамки в сантиметрах:',
    'photo_processing_black_px': 'Введите размеры чёрной рамки в пикселях:',
    'photo_processing_dpi': 'Введите новое значение DPI:',
    'photo_processing_font_size_px': 'Введите размеры шрифта в пикселях:',
    'photo_processing_crop_px': 'Введите на сколько пикселей подрезать изображение:',
    'value_error': '💀 <b>Введи ещё раз нормально</b>',
    'setting_value_success': '✅ Значение успешно изменено!',

    'settings_other_text': '⚙️ <b>ПРОЧЕЕ</b>\n',
    'clean_uploaded': '🚮 <b>Очистить папку Uploaded?</b>',
    'was_cleaned': '✅ Папка Uploaded была успешно очищена',
    'logs_send': '<b>🗃 Файл с логами был отправлен @Andrey_David.</b>',
    'logs_error': '<b>💀 Файл с логами не найден.</b>'
}

# settings main
settings_main_btns: dict[str, str] = {
    'settings_cropper': '🧰 Открыть окно настроек',
    'settings_image_loader': '📤 Загрузка фото',
    'settings_photo_processing': '🌄 Обработка фото',
    'settings_image_counter': '🧮 Подсчёт печати',
    'settings_other': '📦 Прочее',
    'settings_close': '❌ Закрыть'
}


# image loader
def settings_image_loader_text() -> str:
    return (f'⚙️ <b>ЗАГРУЗКА ФОТО</b>'
            f'\n'
            f'\n<b>Путь к папке:</b>'
            f'\n📁 <code>{data.image_loader_path}</code>'
            )


settings_image_loader_btns: dict[str, str] = {
    'open_folder_uploaded': '📂 Открыть папку',
    'clean_folder_uploaded': '🚮 Очистить папку',
    'back_to_settings_main': '⬅️ Настройки',
}

image_loader_clean_folder_btns: dict[str, str] = {
    'clean_folder_uploaded_confirm': '🔥',
    'back_to_settings_image_loader': '⬅️ Загрузка фото'
}

back_to_image_loader_btn: dict[str, str] = {
    'back_to_settings_image_loader': '⬅️ Загрузка фото',
}


# photo processing
def settings_photo_processing_text() -> str:
    return (f'⚙️ <b>ОБРАБОТКА ФОТО</b>'
            f'\n'
            f'\n<b>Путь для сохранения файлов:</b>'
            f'\n📁 <code>{data.photo_processing_path}</code>'
            f'\n'
            f'\n<b>Заворот края фото:</b>'
            f'\n📃 <code>{data.photo_processing_wrap_cm} см</code>'
            f'\n'
            f'\n<b>Белая рамка:</b>'
            f'\n🔳 <code>{data.photo_processing_white_cm} см</code>'
            f'\n'
            f'\n<b>Чёрная рамка:</b>'
            f'\n🔲 <code>{data.photo_processing_black_px} px</code>'
            f'\n'
            f'\n<b>DPI:</b>'
            f'\n⚫ <code>{data.photo_processing_dpi} </code>'
            f'\n'
            f'\n<b>Размер шрифта:</b>'
            f'\n🔠 <code>{data.photo_processing_font_size_px} px</code>'
            f'\n'
            f'\n<b>Обрезка края фото:</b>'
            f'\n✂️ <code>{data.photo_processing_crop_px} px</code>'
            )


settings_photo_processing_btns: dict[str, str] = {
    'photo_processing_wrap_cm': 'Заворот',
    'photo_processing_white_cm': 'Белая рамка',
    'photo_processing_black_px': 'Чёрная рамка',
    'photo_processing_dpi': 'DPI',
    'photo_processing_font_size_px': 'Размер шрифта',
    'photo_processing_crop_px': 'Обрезка края',
    'back_to_settings_main': '⬅️ Настройки',
}

back_to_settings_photo_processing_btn: dict[str, str] = {
    'back_to_settings_photo_processing': '⬅️ Обработка фото'
}


# image counter
def settings_image_counter_text() -> str:
    return (f'⚙️ <b>ПОДСЧЁТ ПЕЧАТИ</b>'
            f'\n'
            f'\n<b>Путь к папке:</b>'
            f'\n📁 <code>{data.image_loader_path}</code>'
            f'\n'
            f'\n<b>Исключения:</b>'
            f'\n🖋 <code>{', '.join(data.image_counter_exceptions)}</code>'
            )


settings_image_counter_btn: dict[str, str] = {
    'back_to_settings_main': '⬅️ Настройки',
}

# settings other
settings_other_btns: dict[str, str] = {
    'send_logs': 'Отправить логи',
    'back_to_settings_main': '⬅️ Настройки'
}

back_to_settings_other_btn: dict[str, str] = {
    'button_back_to_settings_other': '⬅️ Прочее'
}
