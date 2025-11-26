"""Фильтры для проверки типа чата"""

from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery


class ChatTypeFilter(BaseFilter):
    """
    Базовый фильтр для проверки типа чата.

    Примеры использования:
        @router.message(ChatTypeFilter(chat_type="private"))
        async def private_handler(message: Message):
            ...
    """

    def __init__(self, chat_type: Union[str, list[str]]):
        """
        Args:
            chat_type: Тип чата ('private', 'group', 'supergroup', 'channel')
                      Может быть строкой или списком строк
        """
        self.chat_types = [chat_type] if isinstance(chat_type, str) else chat_type

    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        """Проверяет тип чата"""
        if isinstance(event, CallbackQuery):
            event = event.message

        if not event:
            return False

        return event.chat.type in self.chat_types


class IsPrivateChat(ChatTypeFilter):
    """
    Фильтр для проверки, что сообщение из приватного чата.

    Примеры использования:
        @router.message(IsPrivateChat())
        async def private_handler(message: Message):
            await message.answer("Это приватный чат")
    """

    def __init__(self):
        super().__init__(chat_type="private")


class IsGroupChat(ChatTypeFilter):
    """
    Фильтр для проверки, что сообщение из обычной группы.

    Примеры использования:
        @router.message(IsGroupChat())
        async def group_handler(message: Message):
            await message.answer("Это обычная группа")
    """

    def __init__(self):
        super().__init__(chat_type="group")


class IsSuperGroupChat(ChatTypeFilter):
    """
    Фильтр для проверки, что сообщение из супергруппы.

    Примеры использования:
        @router.message(IsSuperGroupChat())
        async def supergroup_handler(message: Message):
            await message.answer("Это супергруппа")

        # Для любой группы (group или supergroup):
        @router.message(ChatTypeFilter(chat_type=["group", "supergroup"]))
        async def any_group_handler(message: Message):
            await message.answer("Это группа или супергруппа")
    """

    def __init__(self):
        super().__init__(chat_type="supergroup")
