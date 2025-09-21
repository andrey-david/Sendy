import logging
import os
import re
import asyncio

import subprocess
from aiogram.types import CallbackQuery, Message
from aiogram import F, Router
from io import BytesIO
from PIL import Image, ImageOps
import pillow_heif
from threading import Thread

from config import config
from cropper.cropper_main import sendy_cropper
from photo_processing.photo_processing import PhotoProc
from keyboards.keyboards import *

handlers_router = Router(name='handlers_router')
logger = logging.getLogger(__name__)


@handlers_router.callback_query(F.data == 'update')
async def button_processed_update(callback: CallbackQuery):
    await callback.answer('Sendy будет перезапущен')
    subprocess.Popen("updater.exe")
    await config.dp.stop_polling()
    loop = asyncio.get_running_loop()
    loop.stop()
    logger.info('UPDATING')


@handlers_router.callback_query(F.data.startswith('open_photo:'))
async def process_button_open_photo(callback: CallbackQuery):
    file_id = callback.data.split(':', 1)[1]
    filepath = photo_paths.get(file_id)
    try:
        os.startfile(filepath)
        await callback.answer("ОТКРЫВАЮ", show_alert=False)
    except:
        await callback.answer("Файл не найден или кнопка устарела", show_alert=False)
    await callback.answer()


@handlers_router.callback_query(F.data.startswith('open_photo_folder:'))
async def process_button_open_photo(callback: CallbackQuery):
    file_id = callback.data.split(':', 1)[1]
    filepath = photo_paths.get(file_id)
    try:
        subprocess.Popen(f'explorer /select,"{filepath}"')
        await callback.answer("ОТКРЫВАЮ ПАПКУ", show_alert=False)
    except:
        await callback.answer("Файл не найден или кнопка устарела", show_alert=False)
    await callback.answer()


@handlers_router.callback_query(F.data.startswith('del_photo:'))
async def process_button_open_photo(callback: CallbackQuery):
    file_id = callback.data.split(':', 1)[1]
    filepath = photo_paths.get(file_id)
    try:
        os.remove(filepath)
        await callback.answer("УДАЛЕНО", show_alert=False)
        await callback.message.edit_text(f"<b>🔥 Изображение удалёно</b>\n\n🏷 <s>{filepath.split('\\')[-1]}</s>")
    except:
        await callback.answer("Файл не найден или кнопка устарела", show_alert=False)
    await callback.answer()


@handlers_router.message(F.photo | (F.document & F.document.mime_type.startswith("image/")))
async def send(message: Message, bot):
    caption = ''
    file_size = message.document.file_size if message.document else message.photo[-1].file_size

    if file_size > 20 * 1024 * 1024:  # 20 Mb
        await message.reply("💀 <b>Ошибка:</b> Файл слишком большой! Максимум 20 МБ. Воспользуйтесь /cropper")
        return

    file_id = (message.photo[-1] if message.photo else message.document).file_id
    file = await bot.get_file(file_id)
    img_data = BytesIO()
    await bot.download_file(file.file_path, destination=img_data)
    img_data.seek(0)

    pillow_heif.register_heif_opener()

    img = Image.open(img_data).convert("RGB")
    img = ImageOps.exif_transpose(img)

    if message.caption:
        caption += message.caption
    caption += ' ' + message.document.file_name
    caption = caption.strip()
    caption_need_crop_match = re.search(r"%", caption)
    caption_urgent = re.search(r"!", caption)
    caption_size_match = re.search(r"(\d+)[xхХХ*чЧ/\\:*.](\d+)", caption)
    caption_number_match = re.search(r"\b(\d+[a-zA-Zа-яА-Я]*)\b", caption)

    if caption_size_match:
        width_cm = int(caption_size_match.group(1))
        height_cm = int(caption_size_match.group(2))
    else:
        width_cm = ''
        height_cm = ''

    if caption_number_match:
        number = caption_number_match.group(1)
    else:
        number = ''

    if caption_urgent:
        number += ' !!'

    if any(word in caption.lower() for word in ['баннер', 'банер', 'бан']):
        material = 'Баннер'
    elif any(word in caption.lower() for word in ['мх', 'матовый', 'мат']):
        material = 'Матовый холст'
    else:
        material = 'Холст'

    if caption_need_crop_match or not width_cm or not height_cm:
        material_dict = {'Холст': 0, 'Баннер': 1, 'Хлопок': 2, 'Матовый холст': 3}
        Thread(target=sendy_cropper, kwargs={
            'image': img,
            'number': number,
            'material': material_dict[material],
            'width': width_cm,
            'height': height_cm,
            'message': message
        }).start()
    else:
        img_proc = PhotoProc()
        img_proc.add_image(img)
        img_proc.set_presets(number=number, width_cm=width_cm, height_cm=height_cm, material=material, message=message)
        img_proc.process_image()
