"""Фильтры для проверки прав администратора"""

from typing import Union

from aiogram import Bot
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from loguru import logger
from core.config import settings


class IsAdmin(BaseFilter):
    """
    Фильтр для проверки, является ли пользователь администратором бота.
    Список админов берется из конфига (ADMIN_IDS).

    Примеры использования:
        @router.message(Command("admin"), IsAdmin())
        async def admin_command(message: Message):
            await message.answer("Вы администратор бота!")
    """

    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        """Проверяет, есть ли пользователь в списке админов"""

        return event.from_user.id in settings.admin_ids


class IsChatAdmin(BaseFilter):
    """
    Фильтр для проверки, является ли пользователь администратором чата.
    Работает только в группах и супергруппах.

    Примеры использования:
        @router.message(Command("ban"), IsChatAdmin())
        async def ban_user(message: Message):
            await message.answer("Только для админов чата!")

        # С комбинацией фильтров:
        @router.message(
            Command("stats"),
            ChatTypeFilter(chat_type=["group", "supergroup"]),
            IsChatAdmin()
        )
        async def chat_stats(message: Message):
            await message.answer("Статистика для админов")
    """

    async def __call__(self, message: Message, bot: Bot) -> bool:
        """Проверяет права администратора в чате"""
        # Работает только в группах
        if message.chat.type not in ["group", "supergroup"]:
            return False

        try:
            member = await bot.get_chat_member(
                chat_id=message.chat.id,
                user_id=message.from_user.id
            )
            return member.status in ["creator", "administrator"]

        except Exception as e:
            logger.error(f"Failed to check admin status: {e}")
            return False
