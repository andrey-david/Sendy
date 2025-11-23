"""On startup

Send a welcome or holiday message to a user on bot startup.
"""

import random
from datetime import datetime

from aiogram import Bot

from lexicon import (
    welcome_message,
    welcome_emoji_new_year,
    welcome_message_new_year,
    celebration_days,
)


async def send_welcome_message(bot: Bot, datetime_on_start: datetime, chat_id: int) -> None:
    day = datetime_on_start.day
    month = datetime_on_start.month

    # 24.12 - 07.01
    new_year = (
            (month == 12 and day in range(24, 32)) or
            (month == 1 and day in range(1, 8))
    )

    celebration_day = (day, month) in celebration_days

    if new_year:
        await bot.send_message(chat_id=chat_id, text=random.choice(welcome_emoji_new_year))
        msg = random.choice(welcome_message_new_year)
    else:
        msg = f'🤖 {random.choice(welcome_message)}'

    if celebration_day:
        msg = celebration_days[(day, month)]

    await bot.send_message(chat_id=chat_id, text=msg)
