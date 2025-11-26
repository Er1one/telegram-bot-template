from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from services import UserService


class UserRegistrationMiddleware(BaseMiddleware):
    """Middleware для автоматической регистрации пользователей"""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user: User | None = data.get("event_from_user")

        if user and not user.is_bot:
            # Автоматически регистрируем или обновляем пользователя
            await UserService.register_user(user)

        return await handler(event, data)
