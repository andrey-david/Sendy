"""
Bot Keyboards
-------------

Defines:
- Main reply keyboard
- Inline keyboards for settings, image loader, photo processing, image counter, shutdown, update
- Dynamic inline keyboards for individual photos (manage_photo_inline_kb)

The `create_inline_kb` helper generates inline keyboards from button definitions.
Photo keyboards store file paths in `photo_paths` using short UUIDs.
"""

import logging
import uuid
from pathlib import Path

from aiogram.types import KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from lexicon import (LEXICON,
                     MAIN_BUTTONS,
                     settings_main_btns,
                     settings_image_loader_btns,
                     image_loader_clean_folder_btns,
                     back_to_image_loader_btn,
                     settings_photo_processing_btns,
                     back_to_settings_photo_processing_btn,
                     settings_image_counter_btn,
                     settings_other_btns,
                     back_to_settings_other_btn,
                     shutdown_btns,
                     update_btn)

logger = logging.getLogger(__name__)

# MAIN KEYBOARD
kb_builder = ReplyKeyboardBuilder()
for btn in MAIN_BUTTONS:
    kb_builder.add(KeyboardButton(text=btn))
kb_builder.adjust(4)
main_kb = kb_builder.as_markup(resize_keyboard=True)


def create_inline_kb(width: int,
                     *args: str,
                     last_btn: str | None = None,
                     **kwargs: str) -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()
    buttons: list[InlineKeyboardButton] = []

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

    kb_builder.row(*buttons, width=width)
    if last_btn:
        kb_builder.row(InlineKeyboardButton(
            text=last_btn,
            callback_data='button_no'
        ))

    return kb_builder.as_markup()


# settings main
settings_main_inline_kb = create_inline_kb(1, **settings_main_btns)

# image loader
settings_image_loader_inline_kb = create_inline_kb(1, **settings_image_loader_btns)
image_loader_clean_folder_inline_kb = create_inline_kb(2, **image_loader_clean_folder_btns)
back_to_image_loader_inline_kb = create_inline_kb(1, **back_to_image_loader_btn)

# photo processing
settings_photo_processing_inline_kb = create_inline_kb(2, **settings_photo_processing_btns)
back_to_settings_photo_processing_inline_kb = create_inline_kb(1, **back_to_settings_photo_processing_btn)

# image counter
settings_image_counter_inline_kb = create_inline_kb(1, **settings_image_counter_btn)

# settings other
settings_other_inline_kb = create_inline_kb(1, **settings_other_btns)
back_to_settings_other_inline_kb = create_inline_kb(1, **back_to_settings_other_btn)

# other keyboards
shutdown_inline_kb = create_inline_kb(2, **shutdown_btns)
update_inline_kb = create_inline_kb(1, **update_btn)

photo_paths: dict[str, Path] = {}


def manage_photo_inline_kb(filepath: Path) -> InlineKeyboardMarkup:
    """
    Creates an inline keyboard for interacting with a photo made by `photo processing`.

    The function generates a unique ID for the given file,
    which is stored in the `photo_paths` dictionary.
    The keyboard contains three buttons:
        🔍 — open the photo,
        📂 — open the folder containing the photo,
        🔥 — delete the photo.

    Note: after the bot restarts, all paths are cleared.
    It is not necessary to store them persistently.

    :param filepath: Path
        Path to the photo file for which the inline keyboard is created.
    :return: InlineKeyboardMarkup
        An inline keyboard with three buttons for interacting with the specified photo.
    """
    file_id = str(uuid.uuid4())[:8]
    photo_paths[file_id] = filepath

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔍", callback_data=f"open_photo:{file_id}"),
            InlineKeyboardButton(text="📂", callback_data=f"open_photo_folder:{file_id}"),
            InlineKeyboardButton(text="🔥", callback_data=f"del_photo:{file_id}")
        ]
    ])
