"""
Bot Menu
--------

Contains message handlers for bot's main menu:
- /start: shows welcome text and main keyboard (main_kb duplicate some main menu commands)
- /settings: opens settings panel (admin only)
- /cropper: launches Sendy Cropper in separate thread
- /counter: counts images in folder (admin only)
- /screenshoot: takes and sends screenshot (admin only)
- /info, /help: shows info text
- /stop: shows shutdown confirmation and stops the Sendy application (admin only)
"""

from threading import Thread
import os
import logging
import time
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile, CallbackQuery
import pyautogui

from lexicon import is_admin, settings_main_text
from config import config
from keyboards import main_kb, shutdown_inline_kb, settings_main_inline_kb
from cropper.cropper_main import sendy_cropper
from lexicon.lexicon import menu_commands
from data import data
from image_counter.image_counter import count_images_in_folder

logger = logging.getLogger(__name__)
menu_router = Router(name='menu_router')


@menu_router.message(Command(commands=["start"]))
async def start_command(message: Message):
    await message.answer(text=menu_commands['/start'], reply_markup=main_kb)


@menu_router.message(Command("settings"))
@menu_router.message(F.text == "⚙️")
async def settings_command(message: Message):
    if await is_admin(message.from_user.id, message):
        await message.answer(text=settings_main_text, reply_markup=settings_main_inline_kb)


@menu_router.message(Command(commands=["cropper"]))
@menu_router.message(F.text.lower().in_(['✂️', '%']))
async def open_cropper(message: Message):
    Thread(target=sendy_cropper, kwargs={'message': message}).start()


@menu_router.message(Command(commands=["counter"]))
@menu_router.message(F.text.lower() == '🧮')
async def image_counter_start_counting(message: Message):
    if await is_admin(message.from_user.id, message):
        try:
            await count_images_in_folder(data.image_counter_path, message)
        except Exception:
            logger.exception('image_counter')


@menu_router.message(Command(commands=["screenshoot"]))
@menu_router.message(F.text.lower() == '📸')
async def take_screenshoot(message: Message):
    save_folder = "screenshots"
    os.makedirs(save_folder, exist_ok=True)
    timestamp = time.strftime("%H-%M-%S__%d.%m.%Y")
    filename = os.path.join(save_folder, f"screenshot_{timestamp}.png")
    try:
        screenshot = pyautogui.screenshot()
        screenshot.save(filename)
        if await is_admin(message.from_user.id, message):
            await message.answer_document(document=FSInputFile(filename),
                                          caption=f"{menu_commands['/screenshoot']}\n\n🏷 <code>{filename}</code>",
                                          )
    except Exception:
        logger.exception('Error while making screenshoot')


@menu_router.message(Command(commands=["info", "help"]))
async def help_command(message: Message):
    await message.answer(menu_commands['/info'])


@menu_router.message(Command(commands=["stop"]))
async def stop_command(message: Message):
    if await is_admin(message.from_user.id, message):
        await message.answer(text=menu_commands['/stop'],
                             reply_markup=shutdown_inline_kb)


async def stop_sendy():
    await config.dp.stop_polling()
    await config.bot.session.close()
    logger.info('STOPPED BY USER')


@menu_router.callback_query(F.data == 'stop_sendy')
async def process_button_shutdown_press(callback: CallbackQuery):
    time = datetime.now() - config.datatime_on_start
    time = str(time).split('.')[0]
    await callback.message.edit_text(text='🪦 Сенди\n'
                                          '\n'
                                          f'😭 Он прожил всего {time}')
    await stop_sendy()
