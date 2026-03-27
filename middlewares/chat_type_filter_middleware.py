from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message

from data import data as data

class ChatTypeFilterMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            event_data: dict[str, Any]
    ) -> Any:

        if isinstance(event, Message):
            chat_type = event.chat.type
            allowed_chat = data.photo_processing_chat

            if allowed_chat != "any" and allowed_chat != chat_type:
                return

        return await handler(event, event_data)
