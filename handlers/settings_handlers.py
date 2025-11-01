"""Settings Handlers

This module handles commands and callback queries related to Sendy bot settings.

Features:
    • Opens and navigates between /settings sections
      (main, image loader, photo processing, counter, other).
    • Updates photo processing parameters (DPI, crop, wrap, font size, etс.) via FSM (FSMSettings).
    • Clears the "Uploaded" folder.
    • Sends log files to the developer.

Technologies:
    • Aiogram Router for registering handlers.
    • FSMContext to manage states while updating settings.
    • STATE_TO_ATTR and ATTR_TO_STATE dictionaries for linking FSM states to attributes in `data`.

Note:
    All changes are saved to the `data` object by calling its `save()` method.
"""

import os

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, FSInputFile

from data import data
from config import config
from lexicon import (
    settings_image_loader_text,
    settings_photo_processing_text,
    settings_lexicon,
    settings_image_counter_text
)
from keyboards import (
    settings_main_inline_kb,
    settings_image_loader_inline_kb,
    image_loader_clean_folder_inline_kb,
    settings_photo_processing_inline_kb,
    back_to_settings_photo_processing_inline_kb,
    settings_image_counter_inline_kb,
    settings_other_inline_kb,
    back_to_settings_other_inline_kb,
    back_to_image_loader_inline_kb
)

settings_router = Router(name='settings_router')


class FSMSettings(StatesGroup):
    photo_processing_wrap_cm = State()
    photo_processing_white_cm = State()
    photo_processing_black_px = State()
    photo_processing_dpi = State()
    photo_processing_crop_px = State()
    photo_processing_font_size_px = State()


STATE_TO_ATTR: dict[State, str] = {
    FSMSettings.photo_processing_wrap_cm: "photo_processing_wrap_cm",
    FSMSettings.photo_processing_white_cm: "photo_processing_white_cm",
    FSMSettings.photo_processing_black_px: "photo_processing_black_px",
    FSMSettings.photo_processing_dpi: "photo_processing_dpi",
    FSMSettings.photo_processing_font_size_px: "photo_processing_font_size_px",
    FSMSettings.photo_processing_crop_px: "photo_processing_crop_px",
}

ATTR_TO_STATE: dict[str, State] = {v: k for k, v in STATE_TO_ATTR.items()}

ATTR_type: dict[str, type] = {
    "photo_processing_wrap_cm": float,
    "photo_processing_white_cm": float,
    "photo_processing_black_px": int,
    "photo_processing_dpi": int,
    "photo_processing_font_size_px": int,
    "photo_processing_crop_px": int
}

# settings main
@settings_router.callback_query(F.data == 'back_to_settings_main')
async def settings_image_loader(callback: CallbackQuery):
    await callback.message.edit_text(text=settings_lexicon['settings_main_text'],
                                     reply_markup=settings_main_inline_kb
                                     )


@settings_router.callback_query(F.data == 'settings_close')
async def button_no(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.clear()


# image_loader
@settings_router.callback_query(F.data == 'settings_image_loader')
@settings_router.callback_query(F.data == 'back_to_settings_image_loader')
async def settings_image_loader(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text=settings_image_loader_text(),
                                     reply_markup=settings_image_loader_inline_kb
                                     )
    await state.clear()


@settings_router.callback_query(F.data == 'open_folder_uploaded')
async def open_folder_uploaded(callback: CallbackQuery):
    os.system(f"explorer.exe {data.image_loader_path}")
    await callback.answer()


@settings_router.callback_query(F.data == 'clean_folder_uploaded')
async def clean_folder_uploaded(callback: CallbackQuery):
    await callback.message.edit_text(text=settings_lexicon['clean_uploaded'],
                                     reply_markup=image_loader_clean_folder_inline_kb
                                     )


@settings_router.callback_query(F.data == 'clean_folder_uploaded_confirm')
async def clean_folder_uploaded_confirm(callback: CallbackQuery):
    files_size = 0
    uploaded_dir = os.path.join(data.image_loader_path, 'Uploaded')
    for file in os.listdir(uploaded_dir):
        file = os.path.join(uploaded_dir, file)
        files_size += os.path.getsize(file)
        os.remove(file)
    files_size_mb = files_size / (1024 * 1024)
    await callback.message.edit_text(text=f'{settings_lexicon['was_cleaned']} [{files_size_mb:.2f} Mb]',
                                     reply_markup=back_to_image_loader_inline_kb)


# photo processing
@settings_router.callback_query(F.data == 'settings_photo_processing')
@settings_router.callback_query(F.data == 'back_to_settings_photo_processing')
async def settings_photo_processing(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text=settings_photo_processing_text(),
                                     reply_markup=settings_photo_processing_inline_kb
                                     )
    await state.clear()


@settings_router.callback_query(F.data.in_(list(ATTR_TO_STATE.keys())))
async def settings_photo_processing_set_value(callback: CallbackQuery, state: FSMContext):
    target_state = ATTR_TO_STATE[callback.data]
    await callback.message.edit_text(text=settings_lexicon[callback.data],
                                     reply_markup=back_to_settings_photo_processing_inline_kb
                                     )
    await state.set_state(target_state)
    await state.update_data(msg_id=callback.message.message_id)


@settings_router.message(StateFilter(*STATE_TO_ATTR.keys()))
async def receive_settings_photo_processing_value(message: Message, state: FSMContext):
    current_state = await state.get_state()
    attr = STATE_TO_ATTR.get(current_state)
    try:
        value = message.text.replace(',', '.')
        if 1 <= float(value) <= 500:
            setattr(data, attr, ATTR_type[attr](value))
            data.save()
            await state.clear()
            await message.answer(
                text=settings_lexicon['setting_value_success'],
                reply_markup=back_to_settings_photo_processing_inline_kb
            )
        else:
            raise ValueError
    except ValueError:
        await message.answer(settings_lexicon['value_error'])


# image counter
@settings_router.callback_query(F.data == 'settings_image_counter')
@settings_router.callback_query(F.data == 'back_to_settings_main')
async def settings_image_counter(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text=settings_image_counter_text(),
                                     reply_markup=settings_image_counter_inline_kb
                                     )
    await state.clear()


# settings other
@settings_router.callback_query(F.data == 'settings_other')
@settings_router.callback_query(F.data == 'button_back_to_settings_other')
async def settings_other(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text=settings_lexicon['settings_other_text'],
                                     reply_markup=settings_other_inline_kb
                                     )
    await state.clear()


@settings_router.callback_query(F.data == 'send_logs')
async def settings_other_send_logs(callback: CallbackQuery):
    log_path: str = 'sendy.log'
    developer_id: str = '445925989'
    if os.path.exists(log_path):
        await config.bot.send_document(chat_id=developer_id, document=FSInputFile(log_path))
        await callback.message.edit_text(text=settings_lexicon['logs_send'],
                                         reply_markup=back_to_settings_other_inline_kb)
    else:
        await callback.message.edit_text(text=settings_lexicon['logs_error'],
                                         reply_markup=back_to_settings_other_inline_kb)
