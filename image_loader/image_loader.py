"""Image Loader

This module watches a configured by user folder for new images, sends them to user via Telegram,
and moves processed files into an 'Uploaded' subfolder.

Functionality:
    - Ensures the 'Uploaded' directory exists.
    - Monitors the target folder using `watchfiles.awatch`.
    - Sends .jpg, .png, and .heic files to the configured Telegram chat.
    - Moves successfully sent files into 'Uploaded'.

Usage:
    from image_loader import image_loader
    await image_loader()
"""

import asyncio
from pathlib import Path
import logging

from watchfiles import awatch
from aiogram.types import FSInputFile
from aiogram.exceptions import TelegramBadRequest
from aiogram import Router

from data import data
from config import config
from lexicon import image_loader_error_text, image_loader_lex

logger = logging.getLogger(__name__)
image_loader_router = Router(name='image_loader_router')


async def image_loader() -> None:
    path: Path = data.image_loader_path
    uploaded_path: Path = path / 'Uploaded'
    allowed_suffix = (".jpg", ".png", ".heic")

    if path.exists():
        uploaded_path.mkdir(exist_ok=True)
        async for _ in awatch(path):
            for file_name in path.glob('*'):
                if file_name.suffix.lower() in allowed_suffix:
                    file_path = path / file_name

                    try:
                        size_mb = file_path.stat().st_size / (1024 * 1024)
                        logger.debug(f'File name: {file_path.name}, File size: {size_mb}')
                        if size_mb >= 50:
                            raise Exception

                        msg = await config.bot.bot.send_message(chat_id=config.bot.chat_id, text=image_loader_lex['sending_file'])
                        await config.bot.bot.send_document(chat_id=config.bot.chat_id, document=FSInputFile(file_path))
                        await msg.delete()

                        dst = uploaded_path / file_path.name
                        file_path.rename(dst)
                        await asyncio.sleep(1)

                    except TelegramBadRequest:
                        logger.exception('Corrupted file or Wrong chat ID')
                        await config.bot.bot.send_message(chat_id=config.bot.chat_id, text=image_loader_lex['error_corrupted_file'])
                    except Exception:
                        logger.exception('Cannot send image')

    else:
        logger.error('Invalid Image loader path')
        await config.bot.bot.send_message(chat_id=config.bot.chat_id, text=image_loader_error_text())
