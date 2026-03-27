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
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiogram import Router

from data import data
from config import config
from lexicon import image_loader_error_text, image_loader_lex

logger = logging.getLogger(__name__)
image_loader_router = Router(name='image_loader_router')


async def safe_send(file) -> bool:
    attempts = 3
    for _ in range(attempts):
        try:
            await config.bot.bot.send_document(
                chat_id=config.bot.chat_id,
                document=FSInputFile(file)
            )
            return True
        except TelegramNetworkError as e:
            logger.exception(f"Send failed, retrying: {e}")
            await asyncio.sleep(5)
    return False


def unique_filename(uploaded_path: Path, filename: str) -> Path:
    dst = uploaded_path / filename

    if not dst.exists():
        return dst

    stem = dst.stem
    suffix = dst.suffix
    counter = 1

    while True:
        new_dst = uploaded_path / f"{stem} ({counter}){suffix}"
        if not new_dst.exists():
            return new_dst
        counter += 1


async def is_file_size_under_50mb(file_path: Path) -> bool:
    size_mb = file_path.stat().st_size / (1024 * 1024)
    logger.debug(f'File name: {file_path.name}, File size: {size_mb}')

    max_file_size_mb = 50
    if size_mb >= max_file_size_mb:
        logger.error(f'File {file_path.name} is too large {size_mb} (> {max_file_size_mb} MB)')
        await config.bot.bot.send_message(chat_id=config.bot.chat_id,
                                          text=image_loader_lex['error_file_is_too_large'])
        return False
    return True


async def image_loader_inner(path):
    uploaded_path: Path = path / 'Uploaded'
    allowed_suffix = (".jpg", ".png", ".heic")

    uploaded_path.mkdir(exist_ok=True)

    async for _ in awatch(path):
        for file_path in path.glob('*'):
            is_image = file_path.suffix.lower() in allowed_suffix

            if is_image and await is_file_size_under_50mb(file_path):
                try:
                    msg = await config.bot.bot.send_message(chat_id=config.bot.chat_id,
                                                            text=image_loader_lex['sending_file'])

                    success = await safe_send(file_path)
                    if success:
                        try:
                            file_path.rename(unique_filename(uploaded_path, file_path.name))
                        except FileNotFoundError as e:
                            logger.exception('File not found')
                            await config.bot.bot.send_message(chat_id=config.bot.chat_id,
                                                              text=image_loader_lex['error_file_not_found'])

                    await msg.delete()
                    await asyncio.sleep(2)

                except TelegramBadRequest:
                    logger.exception('Corrupted file or Wrong chat ID')
                    await config.bot.bot.send_message(chat_id=config.bot.chat_id,
                                                      text=image_loader_lex['error_corrupted_file'])
                except Exception:
                    logger.exception('Cannot send image')
                    await config.bot.bot.send_message(chat_id=config.bot.chat_id,
                                                      text=image_loader_lex['error_while_sending_file'])


async def image_loader() -> None:
    path: Path = data.image_loader_path

    while not path.exists():
        logger.error('Invalid Image loader path')
        await config.bot.bot.send_message(chat_id=config.bot.chat_id, text=image_loader_error_text())
        await asyncio.sleep(2 * 60)

    await image_loader_inner(path)
