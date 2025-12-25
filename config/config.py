from datetime import datetime
from pathlib import Path
import asyncio
import logging
import os
import sys
from dataclasses import dataclass
from environs import Env

from aiogram import Bot, Dispatcher

logger = logging.getLogger(__name__)

if getattr(sys, 'frozen', False):
    app_dir = os.path.dirname(sys.executable)
else:
    app_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.abspath(os.path.join(app_dir, os.pardir))


@dataclass
class TgBot:
    token: str
    admin_ids: list[int]
    chat_id: int
    developer_id: str
    bot_loop: asyncio.AbstractEventLoop | None
    bot: Bot | None
    dp: Dispatcher | None


@dataclass
class BotInfo:
    datetime_on_start: datetime
    app_directory: str


@dataclass
class LogSettings:
    level: str
    format: str


@dataclass
class Config:
    bot: TgBot
    info: BotInfo
    log: LogSettings


env: Env = Env()
env_path: Path = Path(app_dir) / '.env'
env.read_env(env_path)

config = Config(
    bot=TgBot(
        token=env('BOT_TOKEN'),
        admin_ids=list(map(int, env.list('ADMIN_IDS'))),
        chat_id=env('CHAT_ID'),
        developer_id='445925989',
        bot_loop=None,
        bot=None,
        dp=None
    ),
    info=BotInfo(
        datetime_on_start=datetime.now(),
        app_directory=app_dir
    ),
    log=LogSettings(
        level=env('LOG_LEVEL'),
        format=env('LOG_FORMAT')
    )
)
