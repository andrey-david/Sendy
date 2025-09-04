import asyncio
import threading
import random
import os
import logging

logger = logging.getLogger()
logging_handler = logging.FileHandler('sendy.log')
logging_console = logging.StreamHandler()
logging.basicConfig(
    level=logging.INFO,
    format='[{asctime}] #{levelname:8} {filename}:{lineno} - {name} - {message}',
    style='{',
    handlers=[logging_handler, logging_console],
    encoding='utf-8'
)

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
import aiohttp

from config import config
from handlers.handlers import sendy_tray, router, image_loader
from keyboards.keyboards import MENU_COMMANDS, keyboard_inline_update, hello, hello_new_year, hello_emoji_new_year, \
    easter_egg_days
from lexicon.lexicon import sendy_info


# Проверка на обновления, если обновление есть, то выводит сообщение с кнопкой для обновления
async def updater(bot: Bot) -> None:
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
                        await bot.send_message(chat_id=config.chat_id,
                                               text=f'<b><i>🆕 Доступно обновление до Sendy {latest_version}</i></b>',
                                               reply_markup=keyboard_inline_update)
                except Exception as e:
                    print(f"[updater] Ошибка: {e}")  # Сделать через логирование


async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(
            command=command,
            description=description
        ) for command, description in MENU_COMMANDS.items()
    ]
    await bot.set_my_commands(main_menu_commands)


# Отправить сообщение при запуске
async def welcome_message(bot: Bot, datatime_on_start, chat_id) -> None:
    if ((datatime_on_start.day in [24, 25, 26, 27, 28, 29, 30, 31] and datatime_on_start.month == 12) or
            (datatime_on_start.day in [1, 2, 3, 4, 5, 6, 7] and datatime_on_start.month == 1)):
        await bot.send_message(chat_id=chat_id, text=random.choice(hello_emoji_new_year))
        await bot.send_message(chat_id=chat_id, text=random.choice(hello_new_year))
    elif datatime_on_start.day == 23 and datatime_on_start.month == 1:
        await bot.send_message(chat_id=chat_id, text="🎂")
        await bot.send_message(chat_id=chat_id, text='🎉 С днём рождения!')
    elif datatime_on_start.day == 1 and datatime_on_start.month == 4:
        await bot.send_message(chat_id=chat_id, text='🎉 С первым апреля!')
    else:
        await bot.send_message(chat_id=chat_id, text='🤖 ' + random.choice(hello))

    if (datatime_on_start.day, datatime_on_start.month) in easter_egg_days:
        msg = easter_egg_days[(datatime_on_start.day, datatime_on_start.month)]
        await bot.send_message(chat_id=chat_id, text=msg)


async def tray():
    await asyncio.sleep(1)
    threading.Thread(target=sendy_tray.run, daemon=True).start()


async def main():
    logger.info('BOT JUST STARTED')

    bot = Bot(token=config.BOT_TOKEN,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML)
              )
    config.bot = bot

    dp = Dispatcher()
    config.dp = dp

    dp.include_router(router)
    dp.startup.register(set_main_menu)
    _ = asyncio.create_task(image_loader())

    try:
        config.bot_loop = asyncio.get_running_loop()
        await asyncio.gather(welcome_message(bot, config.datatime_on_start, config.chat_id), updater(bot),
                             dp.start_polling(bot, skip_updates=True), tray())
    except (KeyboardInterrupt, SystemExit):
        logger.info('Stopped by console interrupt')
    except asyncio.CancelledError:
        logger.info("Tasks were cancelled")
    finally:
        try:
            await dp.stop_polling()
        except RuntimeError as e:
            if "Polling is not started" not in str(e):
                raise
        await bot.session.close()
        logger.info('BOT STOPPED')


if __name__ == '__main__':
    asyncio.run(main())
