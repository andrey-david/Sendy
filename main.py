import asyncio
import threading
import random
import os

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
import aiohttp

import config
from handlers import sendy_tray, router, image_loader
from keyboards import MENU_COMMANDS, keyboard_inline_update, hello, hello_new_year, hello_emoji_new_year, easter_egg_days
from lexicon import sendy_info

bot = Bot(token=config.BOT_TOKEN)
config.bot = bot
dp = Dispatcher()
config.dp = dp
dp.include_router(router)


# Проверка на обновления, если обновление есть, то выводит сообщение с кнопкой для обновления
async def updater():
    if 'updater_new.exe' in os.listdir() and 'updater.exe' in os.listdir():
        os.replace('updater_new.exe', 'updater.exe')

    url = "https://drive.usercontent.google.com/u/0/uc?id=1vjf8McN-gm7pc3Gfl4sYyOpOcXph5nXz&export=download"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                try:
                    text = await response.text()
                    latest_version, update_link = text.split('|')
                    if latest_version != sendy_info[0]:
                        await bot.send_message(chat_id=config.chat_id, text=f'<b><i>🆕 Доступно обновление до Sendy {latest_version}</i></b>', parse_mode='HTML', reply_markup=keyboard_inline_update)
                except Exception as e:
                    print(f"[updater] Ошибка: {e}")  # Сделать через логирование


# Задать меню с командами
async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(
            command=command,
            description=description
        ) for command, description in MENU_COMMANDS.items()
    ]
    await bot.set_my_commands(main_menu_commands)
dp.startup.register(set_main_menu)


# Отправить сообщение при запуске
async def welcome_message():
    if ((config.datatime_on_start.day in [24, 25, 26, 27, 28, 29, 30, 31] and config.datatime_on_start.month == 12) or
            (config.datatime_on_start.day in [1, 2, 3, 4, 5, 6, 7] and config.datatime_on_start.month == 1)):
        await bot.send_message(chat_id=config.chat_id, text=random.choice(hello_emoji_new_year))
        await bot.send_message(chat_id=config.chat_id, text=random.choice(hello_new_year))
    elif config.datatime_on_start.day == 23 and config.datatime_on_start.month == 1:
        await bot.send_message(chat_id=config.chat_id, text="🎂")
        await bot.send_message(chat_id=config.chat_id, text='🎉 С днём рождения!')
    elif config.datatime_on_start.day == 1 and config.datatime_on_start.month == 4:
        await bot.send_message(chat_id=config.chat_id, text='🎉 С первым апреля!')
    else:
        await bot.send_message(chat_id=config.chat_id, text='🤖 ' + random.choice(hello))

    if (config.datatime_on_start.day, config.datatime_on_start.month) in easter_egg_days:
        msg = easter_egg_days[(config.datatime_on_start.day, config.datatime_on_start.month)]
        await bot.send_message(chat_id=config.chat_id, text=msg)


async def tray():
    await asyncio.sleep(1)
    threading.Thread(target=sendy_tray.run, daemon=True).start()


async def main():
    task_image_loader = asyncio.create_task(image_loader())
    try:
        config.bot_loop = asyncio.get_running_loop()
        await asyncio.gather(welcome_message(), updater(), dp.start_polling(bot, skip_updates=True), tray())
    finally:
        task_image_loader.cancel()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print('Остановлен')  # Сделать через логирование
