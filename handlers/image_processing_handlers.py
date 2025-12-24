"""Image Processing Handlers

This module handles all image-related logic for the Telegram bot.

It processes incoming images, parses captions for size/material/order info,
runs them through the cropper if needed, and sends the final result back to the user.

Main parts:
- parser() - extracts size, number, material, crop, and urgent flags from captions.
- processed_photo_btns_handler() - handles buttons for opening, locating in folder, or deleting photos.
- add_image_to_queue() - adds images to the user queue and starts processing.
- _image_queue_worker() - processes all images for one user.
- process_image_add_to_queue() - main image workflow: download, parse, crop, process, send result.
- choose_size() - handles size selection from inline buttons.
- any_message() - handles user text replies (used for waiting inputs).

Notes:
- Uses `asyncio` queues and locks per user to avoid conflicts.
- Image handling with Pillow and pillow-heif.
- Cropper runs in a separate thread via `sendy_cropper()`.
- Processed results handled by `PhotoProc`.
- Interactive flow managed via inline keyboards.
"""

import asyncio
import re
import logging
import os
import subprocess
from io import BytesIO
from threading import Thread
from pathlib import Path
from queue import Queue

from aiogram import F, Router
from aiogram import Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from PIL import Image, ImageOps
import pillow_heif

from cropper.cropper_main import sendy_cropper
from photo_processing import PhotoProc
from keyboards import photo_paths, manage_photo_inline_kb
from lexicon import handlers_lex
from config import config

image_processing_router = Router(name='image_processing_router')
logger = logging.getLogger(__name__)

user_choice_size_futures: dict[int, asyncio.Future] = {}
user_message_text_futures: dict[int, asyncio.Future] = {}
image_queue: dict[int, asyncio.Queue] = {}
locks: dict[int, asyncio.Lock] = {}
image_queue_tasks: dict[int, asyncio.Task[None]] = {}


def parser(text: str) -> dict[str, list[str] | str | bool]:
    """Parses an input text and extracts order-related parameters.

        Args:
            text (str): image caption.

        Returns:
            dict[str, list[str] | str | bool]: A dictionary with parsed data:
                - "sizes" (list[str]): List of sizes in the format "(Width)х(Height)", if found (empty list if not).
                - "number" (str | None): Number of order.
                - "material" (str): Material type ("Canvas", "Matte Canvas", "Cotton", "Banner").
                - "cropper" (bool): True if cropping indicators are present (%, ✂️, cropper).
                - "urgent" (bool): True if urgency markers are detected (!, ‼️, 🚨).
    """
    parser_sizes = []
    parser_width_height = re.finditer(r'(\d{2,})[xх*ч/\\;:.,-](\d{2,})', text.lower())
    for w_h in parser_width_height:
        parser_sizes.append(f'{w_h.group(1)}х{w_h.group(2)}')

    parser_number = re.search(r'(?:[#№Nn ]|^)(\d+[a-wyzA-WYZа-фц-яА-ФЦ-ЯёЁ]*)-?\b', text)
    if parser_number:
        parser_number = parser_number.group(1)
    else:
        parser_number = False

    parser_no_material = False
    if re.search(r'мат', text.lower()):
        parser_material = 'Матовый холст'
    elif re.search(r'холст|глян|хол', text.lower()):
        parser_material = 'Холст'
    elif re.search(r'хлоп', text.lower()):
        parser_material = 'Хлопок'
    elif re.search(r'бан{1,2}ер|бан', text.lower()):
        parser_material = 'Баннер'
    else:
        parser_material = 'Холст'
        parser_no_material = True

    parser_cropper = re.search(r'%|✂️|cropper', text)

    parser_urgent = re.search(r'[!‼️🚨]', text)

    return {'sizes': parser_sizes,
            'number': parser_number,
            'material': parser_material,
            'no_material': parser_no_material,
            'cropper': bool(parser_cropper),
            'urgent': bool(parser_urgent)
            }


@image_processing_router.callback_query(F.data.startswith(('open_photo:', 'open_photo_folder:', 'del_photo:')))
async def processed_photo_btns_handler(callback: CallbackQuery) -> None:
    """This handler responds to three types of photo-related callbacks:
            - "open_photo:<file_id>": Opens the photo file with the default system viewer.
            - "open_photo_folder:<file_id>": Opens the folder containing the photo and selects the file.
            - "del_photo:<file_id>": Deletes the photo file and updates the message text.

        Args:
            callback (CallbackQuery): The callback query object from a Telegram inline button.
    """
    attr, file_id = callback.data.split(':', 1)
    filepath = photo_paths.get(file_id)

    try:
        if attr == 'open_photo':
            os.startfile(filepath)
            await callback.answer(handlers_lex['processed_photo_open_photo'], show_alert=False)

        elif attr == 'open_photo_folder':
            if filepath:
                subprocess.Popen(["explorer", "/select,", str(filepath)])
                await callback.answer(handlers_lex['processed_photo_open_folder'], show_alert=False)
            else:
                raise FileNotFoundError

        elif attr == 'del_photo':
            os.remove(filepath)
            await callback.answer(handlers_lex['processed_photo_was_deleted'], show_alert=False)
            await callback.message.edit_text(
                f"{handlers_lex['processed_photo_del']}\n\n🏷 <s>{os.path.basename(filepath)}</s>"
            )

    except (TypeError, FileNotFoundError):
        logger.debug('No such file or the button is deprecated')
        await callback.answer(handlers_lex['processed_photo_error'], show_alert=False)


@image_processing_router.message(F.photo | (F.document & F.document.mime_type.startswith("image/")))
async def add_image_to_queue(message: Message, cropper=False) -> None:
    """Handles images from user:
        - Rejects files larger than 20 MB (Telegram limitation).
        - Puts valid messages into the image processing queue.
        - Starts a new queue worker for the user if none is running.
    """
    user_id = message.from_user.id
    if not cropper:
        file_size = message.document.file_size if message.document else message.photo[-1].file_size
        max_file_size = 20 * 1024 * 1024  # 20 Mb

        if file_size > max_file_size:
            await message.reply(handlers_lex['file_size_error'])
            logger.info(f'20 MB limit exceeded. File size is {file_size}, from user_id {user_id}.')
            return

    if user_id not in image_queue:
        image_queue[user_id] = asyncio.Queue()

    await image_queue[user_id].put(message)

    if user_id not in locks:
        locks[user_id] = asyncio.Lock()

    async with locks[user_id]:
        task = image_queue_tasks.get(user_id)
        if not task or task.done():
            image_queue_tasks[user_id] = asyncio.create_task(_image_queue_worker(user_id, config.bot.bot))


async def _image_queue_worker(user_id: int, bot: Bot) -> None:
    """Worker that processes all pending images for a specific user.
    - Runs the image queue handler for the user.
    - Removes the worker task from the global registry when finished.
    """
    try:
        await process_image_add_to_queue(user_id, bot)
    except Exception:
        logger.exception("Error processing image queue for user %s", user_id)
    finally:
        _ = image_queue_tasks.pop(user_id, None)


async def download_image(file, bot: Bot):
    img_data = BytesIO()
    await bot.download_file(file.file_path, destination=img_data)
    pillow_heif.register_heif_opener()
    img_data.seek(0)
    image = Image.open(img_data).convert("RGB")
    image = ImageOps.exif_transpose(image)

    return image


async def send_result(path, no_material, number, message=None):
    try:
        text = (f'{handlers_lex['processing_image_saved']}\n'
                f'{handlers_lex['processing_no_material'] if no_material else ''}'
                f'{'' if number else handlers_lex['processing_no_number']}\n'
                f'🏷 <code>{path.name}</code>'
                )

        if message:
            await message.edit_text(text, reply_markup=manage_photo_inline_kb(path))
        else:
            await config.bot.bot.send_message(config.bot.chat_id, text, reply_markup=manage_photo_inline_kb(path))

    except Exception as e:
        await config.bot.bot.send_message(chat_id=config.bot.chat_id,
                                          text=f"{handlers_lex['processing_error']} {e}"
                                               f"\n"
                                               f"\n{handlers_lex['processing_image_saved']}"
                                               f"\n<code>{path}</code>"
                                          )


async def process_image_add_to_queue(user_id: int, bot: Bot):
    while not image_queue[user_id].empty():
        user_message = await image_queue[user_id].get()
        reply_message = await user_message.reply(handlers_lex['processing_downloading'])

        # Downloading
        if user_message.photo or user_message.document:
            file_id = (user_message.photo[-1] if user_message.photo else user_message.document).file_id
            file = await bot.get_file(file_id)
            image = await download_image(file, bot)

        else:
            image = None

        # Parsing
        await reply_message.edit_text(handlers_lex['processing_processing'])
        if image:
            parsed = parser(user_message.caption or '')
        else:
            parsed = {'sizes': [],
                      'number': None,
                      'material': 'Холст',
                      'no_material': True,
                      'cropper': True,
                      'urgent': False
                      }

        width_height = parsed['sizes']
        cropper = parsed['cropper']

        # Waiting data from user
        if not width_height and not cropper:
            await reply_message.edit_text(handlers_lex['processing_waiting_data'])

            width_height_future = asyncio.get_event_loop().create_future()
            user_message_text_futures[user_message.from_user.id] = width_height_future

            new_caption = await width_height_future
            parsed = parser(new_caption)
            width_height = parsed['sizes']

            if not width_height:
                cropper = True

        # Waiting for user to choose the size
        elif len(width_height) > 1 and not cropper:
            kb = InlineKeyboardBuilder()
            for size in width_height:
                kb.add(InlineKeyboardButton(
                    text=size,
                    callback_data=f"choose_size:{size}"
                ))
            kb.adjust(1)

            await reply_message.edit_text(handlers_lex['processing_waiting_size'], reply_markup=kb.as_markup())

            size_future = asyncio.get_event_loop().create_future()
            user_choice_size_futures[user_message.from_user.id] = size_future
            size = await size_future
            width_height = [size]
            del user_choice_size_futures[user_message.from_user.id]

        number = parsed['number']
        if not number:
            number = ''  # Ø

        material = parsed['material']
        no_material = parsed['no_material']

        if parsed['urgent']:
            number += ' ‼'

        processing = PhotoProc()
        if width_height:
            width_cm, height_cm = width_height[0].split('х')
        else:
            width_cm, height_cm = 0, 0

        width_cm, height_cm = int(width_cm), int(height_cm)

        if image and image.size[0] > image.size[1] and width_cm < height_cm:
            width_cm, height_cm = height_cm, width_cm

        # Waiting for Cropper to open
        if cropper:
            await reply_message.edit_text(handlers_lex['processing_waiting_for_cropper'])
            cropper_queue = Queue()

            def wrapper():
                result = sendy_cropper(
                    image=image,
                    number=number,
                    width=width_cm,
                    height=height_cm,
                    material=material
                )
                cropper_queue.put(result)

            Thread(target=wrapper, daemon=True).start()
            # Waiting for Cropper to return result
            result = True
            while result:
                try:
                    result = cropper_queue.get_nowait()
                    number = result['number']
                    no_material = False
                    processing.presets(**result)
                    break
                except:
                    await asyncio.sleep(3)
            else:
                # Deleting reply message if no result from Cropper (user closed Cropper)
                await reply_message.delete()
                return

        else:
            processing.presets(
                image=image,
                number=number,
                width_cm=width_cm,
                height_cm=height_cm,
                material=material
            )

        filepath: Path = processing.process_image()

        # Sending result to user chat
        await send_result(filepath, no_material, number, reply_message)


@image_processing_router.callback_query(F.data.startswith("choose_size:"))
async def choose_size(callback: CallbackQuery) -> None:
    """Handles user size selection from inline buttons and sets the result in the user's Future."""
    size = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    fut = user_choice_size_futures.get(user_id)

    if fut and not fut.done():
        fut.set_result(size)
    else:
        logger.info(f'No pending Future for user {user_id}')
    await callback.answer()


@image_processing_router.message()
async def any_message(message: Message) -> None:
    """Sets the result of a pending Future for the user with the received message text."""
    user_id = message.from_user.id
    fut = user_message_text_futures.pop(user_id, None)

    if fut and not fut.done():
        fut.set_result(message.text)
    else:
        logger.info(f'No pending Future for user {user_id}')
