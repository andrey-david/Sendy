"""Bot Handlers

pass
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
    await callback.answer(handlers_lex['reboot'])
    if 'updater.exe' in os.getcwd():
        subprocess.Popen("updater.exe")
        await config.dp.stop_polling()
        loop = asyncio.get_running_loop()
        loop.stop()
        logger.info('UPDATING')
    else:
        await callback.answer(handlers_lex['updater_error'])
