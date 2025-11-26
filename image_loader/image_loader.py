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
import os
import logging

from watchfiles import awatch
from aiogram.types import FSInputFile
from aiogram.exceptions import TelegramBadRequest
from aiogram import Router

from data import data
from config import config
from lexicon import image_loader_error_text

logger = logging.getLogger(__name__)
image_loader_router = Router(name='image_loader_router')


async def image_loader() -> None:
    path = data.image_loader_path
    uploaded_path = os.path.join(path, 'Uploaded')

    if os.path.exists(path):
        os.makedirs(uploaded_path, exist_ok=True)
        async for _ in awatch(path):
            for file_name in os.listdir(path):
                if file_name.lower().endswith((".jpg", ".png", ".heic")):
                    file_path = os.path.join(path, file_name)

                    try:
                        if os.path.exists(file_path):
                            await config.bot.send_document(chat_id=config.bot.chat_id, document=FSInputFile(file_path))
                            os.replace(file_path, os.path.join(uploaded_path, file_name))
                    except TelegramBadRequest:
                        logger.exception('Corrupted file or Wrong chat ID')

                    await asyncio.sleep(1)

    else:
        await config.bot.send_message(chat_id=config.bot.chat_id, text=image_loader_error_text())
        logger.error('Invalid Image loader path')
