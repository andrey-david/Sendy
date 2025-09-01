from aiogram.types import KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from lexicon import *
import uuid

# Главная панель кнопок
kb_builder = ReplyKeyboardBuilder()
MainButtons = ['🧮', '✂️', '📸', '⚙️']
for btn in MainButtons:
    kb_builder.add(KeyboardButton(text=btn))
kb_builder.adjust(4)
main_keyboard = kb_builder.as_markup(resize_keyboard=True)


# Инлайн кнопки
def create_inline_kb(width: int,
                     *args: str,
                     last_btn: str | None = None,
                     **kwargs: str) -> InlineKeyboardMarkup:
    # Инициализируем билдер
    kb_builder = InlineKeyboardBuilder()
    # Инициализируем список для кнопок
    buttons: list[InlineKeyboardButton] = []

    # Заполняем список кнопками из аргументов args и kwargs
    if args:
        for button in args:
            buttons.append(InlineKeyboardButton(
                text=LEXICON[button] if button in LEXICON else button,
                callback_data=button))
    if kwargs:
        for button, text in kwargs.items():
            buttons.append(InlineKeyboardButton(
                text=text,
                callback_data=button))

    # Распаковываем список с кнопками в билдер методом row c параметром width
    kb_builder.row(*buttons, width=width)
    # Добавляем в билдер последнюю кнопку, если она передана в функцию
    if last_btn:
        kb_builder.row(InlineKeyboardButton(
            text=last_btn,
            callback_data='button_no'
        ))

    # Возвращаем объект инлайн-клавиатуры
    return kb_builder.as_markup()

keyboard_inline_clean_folder = create_inline_kb(2, **clean_folder)
keyboard_inline_shutdown = create_inline_kb(2, **shutdown)
keyboard_inline_open_folder = create_inline_kb(1, **open_folder)
keyboard_inline_startup_open_folder = create_inline_kb(1, **startup_folder)
keyboard_inline_settings_cancel = create_inline_kb(1, **cancel)



keyboard_inline_settings_main = create_inline_kb(1, **settings_main)

keyboard_inline_settings_photo_loader = create_inline_kb(1, **settings_photo_loader)
keyboard_inline_back_to_settings_photo_loader = create_inline_kb(1, **back_to_settings_photo_loader)

keyboard_inline_settings_photo_processing = create_inline_kb(2, **settings_photo_processing)
keyboard_inline_back_to_settings_photo_processing = create_inline_kb(1, **back_to_settings_photo_processing)

keyboard_inline_settings_print_counter = create_inline_kb(1, **settings_print_counter)
keyboard_inline_back_to_settings_print_counter = create_inline_kb(1, **back_to_settings_print_counter)

keyboard_inline_settings_other = create_inline_kb(1, **settings_other)
keyboard_inline_back_to_settings_other = create_inline_kb(1, **back_to_settings_other)
keyboard_inline_settings_other_startup = create_inline_kb(2, **startup_set)

keyboard_inline_update = create_inline_kb(1, **update)

photo_paths = {}

def keyboard_inline_open_photo(filepath):
    file_id = str(uuid.uuid4())[:8]  # генерируем короткий уникальный ID
    photo_paths[file_id] = filepath  # сохраняем путь по этому ID

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔍", callback_data=f"open_photo:{file_id}"),
            InlineKeyboardButton(text="📂", callback_data=f"open_photo_folder:{file_id}"),
            InlineKeyboardButton(text="🔥", callback_data=f"del_photo:{file_id}")
        ]
    ])
