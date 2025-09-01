import os
import subprocess
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards import *
from data import data, save_to_data
from io import BytesIO
from PIL import Image, ImageOps
import pillow_heif
from pathlib import Path
import sys
import winshell
import time
import pyautogui
from image_counter.image_counter import counter_outer
from lexicon import is_admin
import asyncio
from cropper.cropper_main import sendy_cropper
from photo_processing import PhotoProc
import re
from threading import Thread
import pystray
from datetime import datetime
from config.config import datatime_on_start, dp, bot, bot_loop, chat_id
from watchfiles import awatch

router = Router()


class SettingsStates(StatesGroup):
    path = State()  # Состояние ожидания ввода пути
    Alex_path = State()  # Состояние ожидания ввода пути Алекс
    Alex_exceptions = State()  # Состояние ожидания ввода исключений Алекс
    photo_processing_path = State()  # Состояние ожидания ввода пути для обработчика фото
    photo_processing_zav = State()  # Состояние ожидания ввода заворота для обработчика фото
    photo_processing_white = State()  # Состояние ожидания ввода белой рамки для обработчика фото
    photo_processing_dpi = State()  # Состояние ожидания ввода дипиай для обработчика фото
    photo_processing_black = State()  # Состояние ожидания ввода чёрной рамки для обработчика фото
    photo_processing_fontsize = State()  # Состояние ожидания ввода размера шрифта для обработчика фото
    photo_processing_crop = State()  # Состояние ожидания ввода обрезки для обработчика фото


# /команды
@router.message(Command(commands=["start"]))  # запустить бота
async def process_start_command(message: Message):
    await message.answer(
        f'<b>{message.from_user.username} подключился. <i>Sendy {sendy_info[0]}</i> приветствует вас.</b>'
        f'\n'
        f'\n📌 В Sandy Cropper добавлен tab order. Выделенный элемент теперь подсвечивается синим.\n'
        f'\n📌 Обновлено лого.\n'
        f'\n📌 Произведён полный рефакторинг updater, улучшен визуал.\n'
        f'\n📌 % = ✂️ = /cropper; команда /cropper добавлена в меню.\n',
        reply_markup=main_keyboard
    )


@router.message(Command(commands=["info", "help"]))
async def process_help_command(message: Message):
    await message.answer(f'''Sendy {sendy_info[0]}\nandrey-david {sendy_info[1]}
          (V\\__/V)
          (=ᵔᴥᵔ=)
          (") ‿ (")
@Andrey_David''')


@router.message(Command(commands=["stop"]))  # остановка бота
async def stop_command(message: Message):
    if await is_admin(message.from_user.id, message):
        await message.answer(text='Запустить процедуру умерщвления Сенди?',
                             reply_markup=keyboard_inline_shutdown)


async def stop_sendy():
    sendy_tray.stop()
    await dp.stop_polling()
    await bot.session.close()


@router.callback_query(F.data == 'button_shutdown')  # кнопка /stop нажата
async def process_button_shutdown_press(callback: CallbackQuery):
    time = datetime.now() - datatime_on_start
    time = str(time).split('.')[0]
    await callback.message.edit_text(text='🪦 Сенди\n'
                                          '\n'
                                          f'😭 Он прожил всего {time}')
    await stop_sendy()


def stop_sendy_from_tray():
    asyncio.run_coroutine_threadsafe(stop_sendy(), bot_loop)

icon_path = Path(__file__).parent / "sendy.ico"
sendy_tray = pystray.Icon('Sendy', Image.open(icon_path),
                          menu=pystray.Menu(pystray.MenuItem('Остановить', stop_sendy_from_tray)))


async def image_load_handler():
    file_path = '`Путь не найден`'
    try:
        for file in os.listdir(data['path']):
            if file != 'Uploaded' and (file.endswith('.jpg') or file.endswith('.png') or file.endswith('.heic')):
                file_path = data['path'] + '\\' + file
                await bot.send_document(chat_id=chat_id, document=FSInputFile(file_path))
                if 'Uploaded' in os.listdir(data['path']):
                    os.replace(file_path, data['path'] + '\\Uploaded\\' + file)
                else:
                    os.mkdir(data['path'] + '\\Uploaded\\')
                    os.replace(file_path, data['path'] + '\\Uploaded\\' + file)
    except:
        try:
            await bot.send_message(chat_id=chat_id, text=f'💀 <b>Произошла ошибка: невозможно отправить файл.</b>'
                                                         f'\n'
                                                         f'\nПуть к файлу:'
                                                         f'\n<code>{file_path}</code>'
                                                         f'\n'
                                                         f'\n• Проверьте папку выгрузки на отсутвие в ней постороних файлов или папок.'
                                                         f'\n• Проверьте/смените путь /settings',
                                          reply_markup=keyboard_inline_open_folder)
            await asyncio.sleep(60)
        except:
            await bot.send_message(chat_id=chat_id, text=f'💀 <b>Произошла ошибка: путь указан неверно.</b>'
                                                                f'\n'
                                                                f'\n• Проверьте/смените путь /settings',
                                          )
            await asyncio.sleep(60)


# Запустить проверку папки и отправить картинки, если они там есть
async def image_loader():
    await asyncio.sleep(5)
    try:
        async for _ in awatch(data['path']):
            await image_load_handler()
    except Exception as e:
        print(f"[image_loader] Ошибка: {e}")  # Сделать через логирование
        await bot.send_message(chat_id=chat_id, text=f"💀 <b>Произошла ошибка загрузки фото:</b> {e} "
                                                                   f"\n\n Проверьте путь /settings")


@router.message(F.text.lower() == '🧮')
async def Alex_plus_button_pressed(message: Message):
    if await is_admin(message.from_user.id, message):
        try:
            await counter_outer(data['Alex_path'], message)
        except Exception as e:
            await message.answer(text=f'💀 <b>Произошла ошибка: {e}</b>'
                                      f'\n'
                                      f'\nПуть Алекс+:'
                                      f'\n<code>{data['Alex_path']}</code>'
                                      f'\n'
                                      f'\n• Смените путь Алекс+ в /settings')


@router.message(F.text.lower() == '📸')
async def button_pressed(message: Message):
    save_folder = "screenshots"
    os.makedirs(save_folder, exist_ok=True)

    # Генерируем имя файла с текущей датой и временем
    timestamp = time.strftime("%H-%M-%S__%d.%m.%Y")
    filename = os.path.join(save_folder, f"screenshot_{timestamp}.png")
    try:
        # Делаем скриншот и сохраняем
        screenshot = pyautogui.screenshot()
        screenshot.save(filename)
        if await is_admin(message.from_user.id, message):
            await message.answer_document(document=FSInputFile(filename),
                                          caption=f"✅ <b>Скриншот сохранен</b>\n\n🏷 <code>{filename}</code>",
                                          )
    except Exception as e:
        await message.bot.send_message(chat_id=chat_id, text=f"Ошибка при создании скриншота: {e}")


# НАСТРОЙКИ
@router.message(Command("settings"))  # настройки
async def settings_command(message: Message):
    if await is_admin(message.from_user.id, message):
        await message.answer(text=get_settings_main_text(data), reply_markup=keyboard_inline_settings_main
                             )


@router.message(F.text == "⚙️")  # настройки
async def settings_command(message: Message):
    if await is_admin(message.from_user.id, message):
        await message.answer(text=get_settings_main_text(data), reply_markup=keyboard_inline_settings_main
                             )


# НАСТРОЙКИ ЗАГРУЗКА
@router.callback_query(F.data == 'settings_photo_loader')
async def settings_photo_loader(callback: CallbackQuery):
    await callback.message.edit_text(text=get_settings_photo_loader_text(data),
                                     reply_markup=keyboard_inline_settings_photo_loader
                                     )
    await callback.answer()


@router.callback_query(F.data == 'button_clean_folder_uploaded')
async def button_clean_folder_uploaded_pressed(callback: CallbackQuery):
    await callback.message.edit_text(text='🔥 <b>Очистить папку Uploaded?</b>',
                                     reply_markup=keyboard_inline_clean_folder
                                     )
    await callback.answer()


@router.callback_query(F.data == 'button_back_to_settings_photo_loader')
async def settings_photo_loader(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text=get_settings_photo_loader_text(data),
                                     reply_markup=keyboard_inline_settings_photo_loader
                                     )
    await state.clear()
    await callback.answer()


# НАСТРОЙКИ ЗАГРУЗКА путь
@router.callback_query(F.data == 'button_settings_path')
async def button_settings_path(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='Введите новый путь к папке:',
                                     reply_markup=keyboard_inline_back_to_settings_photo_loader
                                     )
    await state.set_state(SettingsStates.path)
    await state.update_data(msg_id=callback.message.message_id)
    await callback.answer()


@router.message(SettingsStates.path)
async def receive_alex_path(message: Message, state: FSMContext):
    data['path'] = message.text
    await save_to_data(key='path', value=message.text, message=message)
    await message.answer(f'✅ <b>Путь был успешно изменён</b>\n\n📁 <code>{data["path"]}</code>',
                         reply_markup=keyboard_inline_back_to_settings_photo_loader
                         )
    _ = asyncio.create_task(image_loader())
    await state.clear()


# НАСТРОЙКИ ОБРАБОТКА
@router.callback_query(F.data == 'settings_photo_processing')  # кнопка Настройки обработчика фото
async def button_photo_processing_settings(callback: CallbackQuery):
    await callback.message.edit_text(text=get_settings_photo_processing_text(data),
                                     reply_markup=keyboard_inline_settings_photo_processing
                                     )


# НАСТРОЙКИ ОБРАБОТКА путь
@router.callback_query(F.data == 'photo_processing_settings_path')
async def photo_processing_settings_path(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='Введите новый путь к папке, куда будуть сохраняться обработанные фото:',
                                     reply_markup=keyboard_inline_back_to_settings_photo_processing)
    await state.set_state(SettingsStates.photo_processing_path)
    await state.update_data(msg_id=callback.message.message_id)
    await callback.answer()


@router.message(SettingsStates.photo_processing_path)
async def receive_photo_processing_settings_path(message: Message, state: FSMContext):
    data['photo_processing_path'] = message.text
    await save_to_data(key='photo_processing_path', value=message.text, message=message)
    await state.clear()
    await message.answer(f'✅ <b>Путь успешно изменён</b>\n\n📁 <code>{data["photo_processing_path"]}</code>',
                         reply_markup=keyboard_inline_back_to_settings_photo_processing
                         )


# НАСТРОЙКИ ОБРАБОТКА заворот
@router.callback_query(F.data == 'photo_processing_settings_zav')
async def photo_processing_settings_zav(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='Введите заворот для фото в сантиметрах:',
                                     reply_markup=keyboard_inline_back_to_settings_photo_processing)
    await state.set_state(SettingsStates.photo_processing_zav)
    await state.update_data(msg_id=callback.message.message_id)
    await callback.answer()


@router.message(SettingsStates.photo_processing_zav)
async def receive_photo_processing_settings_zav(message: Message, state: FSMContext):
    try:
        data['photo_processing_zav'] = float(message.text)
        await save_to_data(key='photo_processing_zav', value=message.text, message=message)
        await state.clear()
        await message.answer(
            text=f'✅ <b>Заворот был успешно изменён</b>\n\n📃 <code>{data['photo_processing_zav']} см</code>',
            reply_markup=keyboard_inline_back_to_settings_photo_processing)
    except:
        await message.answer(f'💀 <b>Что-то хуйня какая-то, введи ещё раз нормально</b>')


# НАСТРОЙКИ ОБРАБОТКА белая рамка
@router.callback_query(F.data == 'photo_processing_settings_white')
async def photo_processing_settings_white(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='Введите размеры белой рамки в сантиметрах:',
                                     reply_markup=keyboard_inline_back_to_settings_photo_processing)
    await state.set_state(SettingsStates.photo_processing_white)
    await state.update_data(msg_id=callback.message.message_id)
    await callback.answer()


@router.message(SettingsStates.photo_processing_white)
async def receive_photo_processing_settings_white(message: Message, state: FSMContext):
    try:
        data['photo_processing_white'] = float(message.text)
        await save_to_data(key='photo_processing_white', value=message.text, message=message)
        await state.clear()
        await message.answer(
            f'✅ <b>Размеры белой рамки были успешно изменёны</b>\n\n🔳 <code>{data['photo_processing_white']} см</code>',
            reply_markup=keyboard_inline_back_to_settings_photo_processing)
    except:
        await message.answer(f'💀 <b>Что-то хуйня какая-то, введи ещё раз нормально</b>')


# НАСТРОЙКИ ОБРАБОТКА дипиай
@router.callback_query(F.data == 'photo_processing_settings_dpi')
async def photo_processing_settings_dpi(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='Введите новое значение DPI:',
                                     reply_markup=keyboard_inline_back_to_settings_photo_processing)
    await state.set_state(SettingsStates.photo_processing_dpi)
    await state.update_data(msg_id=callback.message.message_id)
    await callback.answer()


@router.message(SettingsStates.photo_processing_dpi)
async def receive_photo_processing_settings_dpi(message: Message, state: FSMContext):
    try:
        data['photo_processing_dpi'] = int(message.text)
        await save_to_data(key='photo_processing_dpi', value=message.text, message=message)
        await state.clear()
        await message.answer(f'✅ <b>DPI был успешно изменён</b>\n\n◼️ <code>{data['photo_processing_dpi']}</code>',
                             reply_markup=keyboard_inline_back_to_settings_photo_processing)
    except:
        await message.answer(f'💀 <b>Что-то хуйня какая-то, введи ещё раз нормально</b>')


# НАСТРОЙКИ ОБРАБОТКА чёрная рамка
@router.callback_query(F.data == 'photo_processing_settings_black')
async def photo_processing_settings_black(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='Введите размеры чёрной рамки в пикселях:',
                                     reply_markup=keyboard_inline_back_to_settings_photo_processing)
    await state.set_state(SettingsStates.photo_processing_black)
    await state.update_data(msg_id=callback.message.message_id)
    await callback.answer()


@router.message(SettingsStates.photo_processing_black)
async def receive_photo_processing_settings_black(message: Message, state: FSMContext):
    try:
        data['photo_processing_black'] = int(message.text)
        await save_to_data(key='photo_processing_black', value=message.text, message=message)
        await state.clear()
        await message.answer(
            f'✅ <b>Размеры чёрной рамки были успешно изменёны</b>\n\n🔲 <code>{data['photo_processing_black']} px</code>',
            reply_markup=keyboard_inline_back_to_settings_photo_processing)
    except:
        await message.answer(f'💀 <b>Что-то хуйня какая-то, введи ещё раз нормально</b>')


# НАСТРОЙКИ ОБРАБОТКА шрифт
@router.callback_query(F.data == 'photo_processing_settings_fontsize')
async def photo_processing_settings_fontsize(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='Введите размеры шрифта в пикселях:',
                                     reply_markup=keyboard_inline_back_to_settings_photo_processing)
    await state.set_state(SettingsStates.photo_processing_fontsize)
    await state.update_data(msg_id=callback.message.message_id)
    await callback.answer()


@router.message(SettingsStates.photo_processing_fontsize)
async def receive_photo_processing_settings_fontsize(message: Message, state: FSMContext):
    try:
        data['photo_processing_fontsize'] = int(message.text)
        await save_to_data(key='photo_processing_fontsize', value=message.text, message=message)
        await state.clear()
        await message.answer(
            f'✅ <b>Размеры шрифта были успешно изменёны</b>\n\n🔠 <code>{data['photo_processing_fontsize']} px</code>',
            reply_markup=keyboard_inline_back_to_settings_photo_processing)
    except:
        await message.answer(f'💀 <b>Что-то хуйня какая-то, введи ещё раз нормально</b>')


# НАСТРОЙКИ ОБРАБОТКА обрезание
@router.callback_query(F.data == 'photo_processing_settings_crop')
async def photo_processing_settings_crop(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='Введите на сколько пикселей подрезать изображение:',
                                     reply_markup=keyboard_inline_back_to_settings_photo_processing)
    await state.set_state(SettingsStates.photo_processing_crop)
    await state.update_data(msg_id=callback.message.message_id)
    await callback.answer()


@router.message(SettingsStates.photo_processing_crop)
async def receive_photo_processing_settings_crop(message: Message, state: FSMContext):
    try:
        data['photo_processing_crop'] = int(message.text)
        await save_to_data(key='photo_processing_crop', value=message.text, message=message)
        await state.clear()
        await message.answer(
            f'✅ <b>Обрезка края фото была успешно изменёна</b>\n\n✂️ <code>{data['photo_processing_crop']} px</code>',
            reply_markup=keyboard_inline_back_to_settings_photo_processing)
    except:
        await message.answer(f'💀 <b>Что-то хуйня какая-то, введи ещё раз нормально</b>')


# НАСТРОЙКИ ОБРАБОТКА назад к основным настройкам
@router.callback_query(F.data == 'button_back_to_settings_main')
async def button_back_to_settings(callback: CallbackQuery):
    await callback.message.edit_text(text=get_settings_main_text(data),
                                     reply_markup=keyboard_inline_settings_main)


@router.callback_query(F.data == 'button_back_to_settings_photo_processing')
async def button_back_to_settings_photo_processing(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(text=get_settings_photo_processing_text(data),
                                     reply_markup=keyboard_inline_settings_photo_processing)


# НАСТРОЙКИ ПОДСЧЁТ
@router.callback_query(F.data == 'settings_print_counter')
async def settings_print_counter(callback: CallbackQuery):
    await callback.message.edit_text(text=get_settings_print_counter_text(data),
                                     reply_markup=keyboard_inline_settings_print_counter)


@router.callback_query(F.data == 'button_back_to_settings_print_counter')
async def button_back_to_settings_print_counter(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text=get_settings_print_counter_text(data),
                                     reply_markup=keyboard_inline_settings_print_counter)
    await state.clear()


# НАСТРОЙКИ ПОДСЧЁТ путь
@router.callback_query(F.data == 'button_Alex_path')
async def button_Alex_path(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='Введите новый путь к папке для подсчёта файлов:',
                                     reply_markup=keyboard_inline_back_to_settings_print_counter)
    await state.set_state(SettingsStates.Alex_path)
    await state.update_data(msg_id=callback.message.message_id)
    await callback.answer()


@router.message(SettingsStates.Alex_path)
async def receive_alex_path(message: Message, state: FSMContext):
    data['Alex_path'] = message.text
    await save_to_data(key='Alex_path', value=message.text, message=message)
    await message.answer(f'✅ <b>Путь к Alex+ был успешно изменён</b>\n\n📁 <code>{data["Alex_path"]}</code>')
    await state.clear()


# НАСТРОЙКИ ПОДСЧЁТ исключения
@router.callback_query(F.data == 'button_Alex_exceptions')  # кнопка /settings Алекс+ путь нажата
async def process_button_settings_Alex_exceptions_press(callback: CallbackQuery, state: FSMContext):
    exceptions = ', '.join(data['Alex_exceptions'])
    await callback.message.edit_text(text=f'Текущий список: <code>{exceptions}</code>'
                                          f'\n'
                                          f'\nВведите исключения для Alex+ через запятую, для удаления используйте символ "-" перед словом (напр. -Алекс), регистр имеет значение:',
                                     reply_markup=keyboard_inline_settings_cancel)
    await state.set_state(SettingsStates.Alex_exceptions)
    await state.update_data(msg_id=callback.message.message_id)
    await callback.answer()


@router.message(SettingsStates.Alex_exceptions)
async def receive_alex_path(message: Message, state: FSMContext):
    user_text = message.text.strip()
    exceptions = data['Alex_exceptions']

    # Обрабатываем ввод пользователя
    if user_text.endswith(','):
        user_text = user_text[:-1]

    words = [w.strip() for w in user_text.split(',')]
    words = [w for w in words if w]  # удаляем пустые

    for word in words:
        if word.startswith('-'):
            try:
                exceptions.remove(word[1:])  # удаляем "-"
            except TypeError:
                await message.answer(f'💀 Нет такого исключения: <code>{word[1:]}</code>')
        else:
            exceptions.append(word)  # добавляем новое

    data['Alex_exceptions'] = exceptions
    await save_to_data(key='Alex_exceptions', value=exceptions, message=message)
    exceptions = ', '.join(data['Alex_exceptions'])
    await message.answer(f'✅ <b>Исключения для Alex+ успешно обновлены</b>\n\n🖋 <code>{exceptions}</code>')
    await state.clear()


@router.callback_query(F.data == 'update')
async def button_processed_update(callback: CallbackQuery):
    await callback.answer('Sendy будет перезапущен')
    subprocess.Popen("updater.exe")
    sendy_tray.stop()
    await config.dp.stop_polling()
    loop = asyncio.get_running_loop()
    loop.stop()


# НАСТРОЙКИ ПРОЧЕЕ
@router.callback_query(F.data == 'settings_other')
async def process_settings_photo_loader(callback: CallbackQuery):
    await callback.message.edit_text(text=get_settings_other_text(data), reply_markup=keyboard_inline_settings_other)
    await callback.answer()


@router.callback_query(F.data == 'button_back_to_settings_other')
async def button_back_to_settings_other(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text=get_settings_other_text(data), reply_markup=keyboard_inline_settings_other)
    await state.clear()
    await callback.answer()


# НАСТРОЙКИ ПРОЧЕЕ автозагрузка
@router.callback_query(F.data == 'button_startup')  # кнопка /settings автозагрузка нажата
async def process_button_settings_startup_press(callback: CallbackQuery):
    await callback.message.edit_text(text='Добавить Сенди в автозагрузку?',
                                     reply_markup=keyboard_inline_settings_other_startup)


@router.callback_query(F.data == 'button_startup_open_folder')  # кнопка открыть папку автозагрузки нажата
async def process_button_no_press(callback: CallbackQuery):
    os.system('explorer shell:startup')


@router.callback_query(F.data == 'button_open_folder')  # кнопка открыть папку нажата
async def button_open_folder(callback: CallbackQuery):
    os.system(f"explorer.exe {data['path']}")
    await callback.answer()


@router.callback_query(F.data == 'button_yes_clean_folder')  # кнопка Да для очистки папки uploaded нажата
async def button_yes_clean_folder(callback: CallbackQuery):
    files_size = 0
    for file in os.listdir(data['path'] + '/Uploaded/'):
        files_size += os.path.getsize(data['path'] + '/Uploaded/' + file)
        os.remove(data['path'] + '/Uploaded/' + file)
    files_size_mb = files_size / (1024 * 1024)
    await callback.message.edit_text(text=f'✅ Папка Uploaded была успешно очищена [{files_size_mb:.2f} МБ]',
                                     reply_markup=keyboard_inline_open_folder)


@router.callback_query(F.data == 'button_no')
async def button_no(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(text='❌ Действие отменено')


@router.callback_query(F.data == 'button_processed_photos_open_folder_pressed')  # кнопка посмотреть фото в папке нажата
async def button_processed_photos_open_folder_press(callback: CallbackQuery):
    os.system(f"explorer.exe {data['photo_processing']}")


@router.callback_query(F.data == 'button_startup_yes')  # кнопка /settings автозагрузка нажата
async def process_button_settings_startup_press(callback: CallbackQuery):
    try:
        if getattr(sys, 'frozen', False):
            current_folder_path = Path(sys.executable).parent.resolve()
        else:
            current_folder_path = Path(__file__).parent.resolve()
        # Путь к файлу, для которого нужно создать ярлык
        file_path = str(current_folder_path / f"Sendy.exe")
        # Путь к папке автозагрузки
        startup_folder = winshell.folder("Startup")
        # Полный путь к ярлыку
        shortcut_path = os.path.join(startup_folder, f"Sendy.lnk")
        # Создание ярлыка
        with winshell.shortcut(shortcut_path) as shortcut:
            shortcut.path = file_path
            shortcut.description = "Shortcut for Sendy"
            shortcut.working_directory = os.path.dirname(file_path)

        await callback.message.edit_text(text='✅ Сенди теперь запускаестся вместе с системой',
                                         reply_markup=keyboard_inline_startup_open_folder)
    except:
        await callback.message.edit_text(text='💀 <b>Произошла ошибка: невозможно добавить Сенди в автозагрузку.</b>'
                                              '\n'
                                              '\nСделайте это вручную:'
                                              '\n• [WIN]+[R]'
                                              '\n• shell:startup'
                                              '\n• Создать ярлык указывающий на Сенди в папке автозагрузки',
                                         reply_markup=keyboard_inline_startup_open_folder
                                         )


@router.callback_query(F.data.startswith('open_photo:'))
async def process_button_open_photo(callback: CallbackQuery):
    file_id = callback.data.split(':', 1)[1]
    filepath = photo_paths.get(file_id)
    try:
        os.startfile(filepath)
        await callback.answer("ОТКРЫВАЮ", show_alert=False)
    except:
        await callback.answer("Файл не найден или кнопка устарела", show_alert=False)
    await callback.answer()


@router.callback_query(F.data.startswith('open_photo_folder:'))
async def process_button_open_photo(callback: CallbackQuery):
    file_id = callback.data.split(':', 1)[1]
    filepath = photo_paths.get(file_id)
    try:
        subprocess.Popen(f'explorer /select,"{filepath}"')
        await callback.answer("ОТКРЫВАЮ ПАПКУ", show_alert=False)
    except:
        await callback.answer("Файл не найден или кнопка устарела", show_alert=False)
    await callback.answer()


@router.callback_query(F.data.startswith('del_photo:'))
async def process_button_open_photo(callback: CallbackQuery):
    file_id = callback.data.split(':', 1)[1]
    filepath = photo_paths.get(file_id)
    try:
        os.remove(filepath)
        await callback.answer("УДАЛЕНО", show_alert=False)
        await callback.message.edit_text(f"<b>🔥 Изображение удалёно</b>\n\n🏷 <s>{filepath.split('\\')[-1]}</s>")
    except:
        await callback.answer("Файл не найден или кнопка устарела", show_alert=False)
    await callback.answer()

@router.message(Command(commands=["cropper"]))
@router.message(F.text.lower().in_(['✂️', '%']))
async def button_pressed(message: Message):
    Thread(target=sendy_cropper, kwargs={
        'message': message,
    }).start()


@router.message(F.photo | (F.document & F.document.mime_type.startswith("image/")))
async def send(message: Message, bot):
    caption = ''
    file_size = message.document.file_size if message.document else message.photo[-1].file_size

    if file_size > 20 * 1024 * 1024:  # 20 Mb
        await message.reply("💀 <b>Ошибка:</b> Файл слишком большой! Максимум 20 МБ. Воспользуйтесь /cropper")
        return

    file_id = (message.photo[-1] if message.photo else message.document).file_id
    file = await bot.get_file(file_id)
    img_data = BytesIO()
    await bot.download_file(file.file_path, destination=img_data)
    img_data.seek(0)

    pillow_heif.register_heif_opener()

    img = Image.open(img_data).convert("RGB")
    img = ImageOps.exif_transpose(img)

    if message.caption:
        caption += message.caption
    caption += ' ' + message.document.file_name
    caption = caption.strip()
    caption_need_crop_match = re.search(r"%", caption)
    caption_urgent = re.search(r"!", caption)
    caption_size_match = re.search(r"(\d+)[xхХХ*чЧ/\\:*.](\d+)", caption)
    caption_number_match = re.search(r"\b(\d+[a-zA-Zа-яА-Я]*)\b", caption)

    if caption_size_match:
        width_cm = int(caption_size_match.group(1))
        height_cm = int(caption_size_match.group(2))
    else:
        width_cm = ''
        height_cm = ''

    if caption_number_match:
        number = caption_number_match.group(1)
    else:
        number = ''

    if caption_urgent:
        number += ' !!'

    if any(word in caption.lower() for word in ['баннер', 'банер', 'бан']):
        material = 'Баннер'
    elif any(word in caption.lower() for word in ['мх', 'матовый', 'мат']):
        material = 'Матовый холст'
    else:
        material = 'Холст'

    if caption_need_crop_match or not width_cm or not height_cm:
        material_dict = {'Холст': 0, 'Баннер': 1, 'Хлопок': 2, 'Матовый холст': 3}
        Thread(target=sendy_cropper, kwargs={
            'image': img,
            'number': number,
            'material': material_dict[material],
            'width': width_cm,
            'height': height_cm,
            'message': message
        }).start()
    else:
        img_proc = PhotoProc()
        img_proc.add_image(img)
        img_proc.set_presets(number=number, width_cm=width_cm, height_cm=height_cm, material=material, message=message)
        img_proc.process_image()
