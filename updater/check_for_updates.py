import os
import logging

import aiohttp
from aiogram import Bot

from keyboards import update_inline_kb
from config import config
from lexicon import sendy_info

logger = logging.getLogger(__name__)

async def check_for_updates(bot: Bot) -> None:
    if 'updater_new.exe' in os.listdir() and 'updater.exe' in os.listdir():
        os.replace('updater_new.exe', 'updater.exe')

    url = "https://drive.usercontent.google.com/u/0/uc?id=1vjf8McN-gm7pc3Gfl4sYyOpOcXph5nXz&export=download"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                try:
                    text = await response.text()
                    latest_version, update_link = text.split('|')
                    if latest_version != sendy_info['version']:
                        await bot.send_message(chat_id=config.chat_id,
                                               text=f'<b><i>🆕 Доступно обновление до Sendy {latest_version}</i></b>',
                                               reply_markup=update_inline_kb)
                except Exception:
                    logger.exception('Update checker error')