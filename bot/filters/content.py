"""Фильтры для проверки содержимого сообщений"""

import re

from aiogram.filters import BaseFilter
from aiogram.types import Message


class HasText(BaseFilter):
    """
    Фильтр для проверки наличия текста в сообщении.

    Примеры использования:
        @router.message(HasText())
        async def text_handler(message: Message):
            await message.answer("Получил текстовое сообщение")
    """

    async def __call__(self, message: Message) -> bool:
        """Проверяет наличие текста"""
        return bool(message.text and message.text.strip())


class HasMedia(BaseFilter):
    """
    Фильтр для проверки наличия медиа в сообщении.
    Проверяет наличие фото, видео, документов, аудио, голосовых сообщений.

    Примеры использования:
        @router.message(HasMedia())
        async def media_handler(message: Message):
            await message.answer("Получил медиафайл")
    """

    async def __call__(self, message: Message) -> bool:
        """Проверяет наличие медиа"""
        return bool(
            message.photo
            or message.video
            or message.document
            or message.audio
            or message.voice
            or message.video_note
            or message.sticker
            or message.animation
        )


class TextLengthFilter(BaseFilter):
    """
    Фильтр для проверки длины текста сообщения.

    Примеры использования:
        # Минимум 10 символов
        @router.message(TextLengthFilter(min_length=10))
        async def long_text(message: Message):
            await message.answer("Текст достаточно длинный")

        # Максимум 100 символов
        @router.message(TextLengthFilter(max_length=100))
        async def short_text(message: Message):
            await message.answer("Текст короткий")

        # От 10 до 100 символов
        @router.message(TextLengthFilter(min_length=10, max_length=100))
        async def medium_text(message: Message):
            await message.answer("Текст средней длины")
    """

    def __init__(self, min_length: int = 0, max_length: int = None):
        """
        Args:
            min_length: Минимальная длина текста (включительно)
            max_length: Максимальная длина текста (включительно)
        """
        self.min_length = min_length
        self.max_length = max_length

    async def __call__(self, message: Message) -> bool:
        """Проверяет длину текста"""
        if not message.text:
            return False

        text_length = len(message.text)

        if text_length < self.min_length:
            return False

        if self.max_length is not None and text_length > self.max_length:
            return False

        return True


class HasLinks(BaseFilter):
    """
    Фильтр для проверки наличия ссылок в сообщении.
    Проверяет как текстовые ссылки, так и entities (urls, text_links).

    Примеры использования:
        @router.message(HasLinks())
        async def link_handler(message: Message):
            await message.answer("Обнаружена ссылка в сообщении")

        # Антиспам для групп:
        @router.message(
            ChatTypeFilter(chat_type=["group", "supergroup"]),
            HasLinks()
        )
        async def check_spam(message: Message):
            # Проверка на спам со ссылками
            pass
    """

    # Простой regex для поиска URL
    URL_PATTERN = re.compile(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    )

    async def __call__(self, message: Message) -> bool:
        """Проверяет наличие ссылок"""
        # Проверяем entities
        if message.entities:
            for entity in message.entities:
                if entity.type in ["url", "text_link"]:
                    return True

        # Проверяем текст regex'ом
        if message.text and self.URL_PATTERN.search(message.text):
            return True

        # Проверяем caption (для медиа)
        if message.caption:
            if message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type in ["url", "text_link"]:
                        return True

            if self.URL_PATTERN.search(message.caption):
                return True

        return False
