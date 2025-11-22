import asyncio
import random
import logging
import os
import sys

logger = logging.getLogger()
if getattr(sys, 'frozen', False):
    app_dir = os.path.dirname(sys.executable)
else:
    app_dir = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.join(app_dir, 'sendy.log')
logging_handler = logging.FileHandler(filename=log_path, encoding='utf-8')
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

from config import config
from tray import tray
from handlers import (
    menu_router,
    set_main_menu,
    handlers_router,
    settings_router,
    image_processing_router
)
from lexicon import sendy_info
from lexicon.lexicon import (
    hello,
    hello_new_year,
    hello_emoji_new_year,
    easter_egg_days,
)
from updater import check_for_updates
from image_loader.image_loader import (
    image_loader,
    image_loader_router
)
from middlewares import IsAdminMiddleware


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
        await bot.send_message(chat_id=chat_id, text='🎉 С первым мая!')
    else:
        await bot.send_message(chat_id=chat_id, text='🤖 ' + random.choice(hello))

    if (datatime_on_start.day, datatime_on_start.month) in easter_egg_days:
        msg = easter_egg_days[(datatime_on_start.day, datatime_on_start.month)]
        await bot.send_message(chat_id=chat_id, text=msg)


async def main():
    logger.info(f'BOT {sendy_info['version']} JUST STARTED')
    # dotenv.load_dotenv()
    try:
        bot = Bot(token=config.BOT_TOKEN,
                  default=DefaultBotProperties(parse_mode=ParseMode.HTML)
                  )
        config.bot = bot

        dp = Dispatcher()
        config.dp = dp

        dp.include_router(handlers_router)
        dp.include_router(settings_router)
        dp.include_router(menu_router)
        dp.include_router(image_loader_router)
        dp.include_router(image_processing_router)

        dp.startup.register(set_main_menu)

        dp.update.outer_middleware(IsAdminMiddleware())

        _ = asyncio.create_task(image_loader())
    except Exception as e:
        logger.exception(f'Cannot run BOT: {e}')

    try:
        config.bot_loop = asyncio.get_running_loop()
        await asyncio.gather(
            welcome_message(bot, config.datatime_on_start, config.chat_id),
            check_for_updates(bot),
            dp.start_polling(bot, skip_updates=True),
            tray()
        )
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
    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception("Fatal error in event loop: %s", e)
