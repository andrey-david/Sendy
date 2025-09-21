import asyncio
import os
import logging

from watchfiles import awatch
from aiogram.types import FSInputFile, CallbackQuery
from aiogram import F, Router

from data import data
from config import config
from keyboards import back_to_image_loader_inline_kb

logger = logging.getLogger(__name__)
image_loader_router = Router(name='image_loader_router')


async def image_loader():
    await asyncio.sleep(5)  # waiting for data to read
    try:
        async for _ in awatch(data.image_loader_path):
            await image_load_handler()
    except Exception as e:
        logger.exception(f"[image_loader] Ошибка: {e}")
        await config.bot.send_message(chat_id=config.chat_id, text=f"💀 <b>Произошла ошибка загрузки фото:</b> {e}"
                                                                   f"\n\n Проверьте путь в /settings")


async def image_load_handler():
    file_path = '`Путь не найден`'
    try:
        path = data.image_loader_path
        for file in os.listdir(path):
            if file != 'Uploaded' and (file.endswith('.jpg') or file.endswith('.png') or file.endswith('.heic')):
                file_path = os.path.join(path, file)
                await config.bot.send_document(chat_id=config.chat_id, document=FSInputFile(file_path))
                if 'Uploaded' in os.listdir(path):
                    os.replace(file_path, os.path.join(path, 'Uploaded', file))
                else:
                    os.mkdir(os.path.join(path, 'Uploaded'))
                    os.replace(file_path, os.path.join(path, 'Uploaded', file))
    except:
        try:
            await config.bot.send_message(chat_id=config.chat_id,
                                          text=f'💀 <b>Произошла ошибка: невозможно отправить файл.</b>'
                                               f'\n'
                                               f'\nПуть к файлу:'
                                               f'\n<code>{file_path}</code>'
                                               f'\n'
                                               f'\n• Проверьте папку выгрузки на отсутвие в ней постороних файлов или папок.'
                                               f'\n• Проверьте/смените путь /settings',
                                          reply_markup=back_to_image_loader_inline_kb)
            await asyncio.sleep(60)
        except:
            await config.bot.send_message(chat_id=config.chat_id,
                                          text=f'💀 <b>Произошла ошибка: путь указан неверно.</b>'
                                               f'\n'
                                               f'\n• Проверьте/смените путь /settings',
                                          )
            await asyncio.sleep(60)
