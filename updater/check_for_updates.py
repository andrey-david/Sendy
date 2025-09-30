"""Update Checker

Checks for application updates and notifies the user.
Then user can push update button, to run `updater.exe` script.

Functionality:
    - Replaces `updater_new.exe` with `updater.exe` if found (to update `updater.exe`).
    - Fetches version info from a remote URL in the format "latext_version|link_to_update.zip".
    - Compares the remote version with the local one.
    - Sends a Telegram message with an inline keyboard if an update is available.
"""

import os
import logging

import aiohttp
from aiogram import Bot

from keyboards import update_inline_kb
from config import config
from lexicon import sendy_info, handlers_lex

logger = logging.getLogger(__name__)

async def check_for_updates(bot: Bot) -> None:
    cwd = os.getcwd()
    url = "https://drive.usercontent.google.com/u/0/uc?id=1vjf8McN-gm7pc3Gfl4sYyOpOcXph5nXz&export=download"
    latest_version = sendy_info['version']

    if 'updater_new.exe' in cwd:
        os.replace('updater_new.exe', 'updater.exe')
    elif 'updater.exe' in cwd:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    text = await response.text()
                    try:
                        latest_version, update_link = text.split('|')
                    except ValueError:
                        logger.error('Wrong update data')
                    if latest_version != sendy_info['version']:
                        await bot.send_message(chat_id=config.chat_id,
                                               text=f'<b><i>{handlers_lex['update_available']} {latest_version}</i></b>',
                                               reply_markup=update_inline_kb)
    else:
        logger.warning('`updater.exe` not found')