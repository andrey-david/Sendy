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
import asyncio

import aiohttp
from aiogram import Bot

from keyboards import update_inline_kb
from config import config
from lexicon import sendy_info, handlers_lex

logger = logging.getLogger(__name__)


async def check_for_updates(bot: Bot) -> None:
    list_dir = os.listdir(config.info.app_directory)
    url = "https://drive.usercontent.google.com/u/0/uc?id=1vjf8McN-gm7pc3Gfl4sYyOpOcXph5nXz&export=download"
    latest_version = sendy_info['version']

    if 'updater_new.exe' in list_dir:
        os.replace('updater_new.exe', 'updater.exe')

    if 'updater.exe' not in list_dir:
        logger.warning('`updater.exe` not found')
        return

    try:
        timeout = aiohttp.ClientTimeout(total=3)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Update server returned {response.status}")
                    return

                text = await response.text()

    except aiohttp.ClientError as e:
        logger.error(f"Network error during update check: {e}")
        return
    except asyncio.TimeoutError:
        logger.error("Update check timeout")
        return
    except Exception as e:
        logger.error(f"Update request failed: {e}")
        return

    try:
        latest_version, update_link = text.split('|')
    except ValueError:
        logger.error('Wrong update data format')
        return

    if latest_version != sendy_info['version']:
        await bot.send_message(chat_id=config.bot.chat_id,
                               text=f'🆕',
                               )

        await bot.send_message(chat_id=config.bot.chat_id,
                               text=f'<b><i>{handlers_lex['update_available']} {latest_version}</i></b>',
                               reply_markup=update_inline_kb,
                               )
