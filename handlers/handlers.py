"""Bot Handlers

This module contains general-purpose bot handlers that are not directly related
to a specific feature but support essential functionality.

Currently, it includes:
    - `update` callback handler
"""

import asyncio
import logging
import os
import subprocess

from aiogram import F, Router
from aiogram.types import CallbackQuery

from config import config
from lexicon import handlers_lex

handlers_router = Router(name='handlers_router')
logger = logging.getLogger(__name__)


@handlers_router.callback_query(F.data == 'update')
async def update(callback: CallbackQuery) -> None:
    """Checks if `updater.exe` exists in the bot's directory.
       If found, notifies the user, starts the updater, and stops the bot gracefully.
       Otherwise, sends an error message.
    """
    updater_name = "updater.exe"
    updater_path = os.path.join(config.info.app_directory, updater_name)
    if os.path.exists(updater_path):
        await callback.answer(handlers_lex['reboot'])
        subprocess.Popen([
            "powershell",
            "-Command",
            f'Start-Process "{updater_path}" -Verb runAs'
        ])
        await config.bot.dp.stop_polling()
        loop = asyncio.get_running_loop()
        loop.stop()
        logger.info('UPDATING')
    else:
        await callback.answer(handlers_lex['updater_error'])
