"""Шаблонизатор для унифицированной работы с сообщениями бота."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Union

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    CallbackQuery,
    ForceReply,
    InlineKeyboardMarkup,
    InputFile,
    InputMediaPhoto,
    InputMediaDocument,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    BufferedInputFile,
    FSInputFile,
)
from loguru import logger

if TYPE_CHECKING:
    from aiogram import Bot

# Type aliases для улучшения читаемости
ReplyMarkup = Union[
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    ForceReply,
    None,
]
MediaType = Union[InputFile, str, BufferedInputFile, FSInputFile]
TargetType = Union[int, str, Message, CallbackQuery]


class TemplateError(Exception):
    """Базовое исключение для ошибок Template."""
    pass


class Template:
    """
    Шаблонизатор для работы с сообщениями Telegram.

    Поддерживает:
    - Текстовые сообщения
    - Одно фото
    - Медиагруппы (несколько фото)
    - Файлы и документы
    - Клавиатуры

    Примеры использования:
        # Простое сообщение
        template = Template(text="Привет!")
        await template.send(message)

        # С одним фото
        template = Template(
            text="Описание",
            photo="path/to/photo.jpg",
            buttons=keyboard
        )
        await template.send(message)

        # Несколько фото (медиагруппа)
        template = Template(
            text="Описание первого фото",
            photos=["photo1.jpg", "photo2.jpg", "photo3.jpg"]
        )
        await template.send(message)

        # Отправка файла
        template = Template(
            text="Вот ваш файл",
            document="document.pdf"
        )
        await template.send(message)

        # Fluent interface
        await (Template()
            .with_text("Текст")
            .with_photo("photo.jpg")
            .with_buttons(keyboard)
            .send(message))
    """

    def __init__(
        self,
        bot_instance: Bot | None = None,
        text: str | None = None,
        photo: MediaType | None = None,
        photos: List[MediaType] | None = None,
        document: MediaType | None = None,
        buttons: ReplyMarkup = None,
    ) -> None:
        """
        Инициализирует шаблон сообщения.

        Args:
            bot_instance: Экземпляр бота (требуется для отправки по chat_id)
            text: Текст сообщения
            photo: Одно фото (путь, file_id или InputFile)
            photos: Список фото для медиагруппы
            document: Документ/файл
            buttons: Клавиатура (inline или reply)
        """
        self.bot_instance = bot_instance
        self.text = text
        self.photo = photo
        self.photos = photos or []
        self.document = document
        self.buttons = buttons

        # Валидация: нельзя одновременно использовать photo и photos
        if self.photo and self.photos:
            raise TemplateError("Cannot use both 'photo' and 'photos'. Use either one.")

        # Валидация: нельзя одновременно использовать медиа и документ
        if (self.photo or self.photos) and self.document:
            raise TemplateError("Cannot use photos and document together.")

    def with_bot(self, bot: Bot) -> Template:
        """Устанавливает экземпляр бота."""
        return self.__class__(
            bot_instance=bot,
            text=self.text,
            photo=self.photo,
            photos=self.photos,
            document=self.document,
            buttons=self.buttons,
        )

    def with_text(self, text: str) -> Template:
        """Устанавливает текст сообщения."""
        return self.__class__(
            bot_instance=self.bot_instance,
            text=text,
            photo=self.photo,
            photos=self.photos,
            document=self.document,
            buttons=self.buttons,
        )

    def with_photo(self, photo: MediaType) -> Template:
        """Устанавливает одно фото."""
        return self.__class__(
            bot_instance=self.bot_instance,
            text=self.text,
            photo=photo,
            photos=None,
            document=self.document,
            buttons=self.buttons,
        )

    def with_photos(self, photos: List[MediaType]) -> Template:
        """Устанавливает несколько фото (медиагруппа)."""
        return self.__class__(
            bot_instance=self.bot_instance,
            text=self.text,
            photo=None,
            photos=photos,
            document=self.document,
            buttons=self.buttons,
        )

    def with_document(self, document: MediaType) -> Template:
        """Устанавливает документ."""
        return self.__class__(
            bot_instance=self.bot_instance,
            text=self.text,
            photo=None,
            photos=None,
            document=document,
            buttons=self.buttons,
        )

    def with_buttons(self, buttons: ReplyMarkup) -> Template:
        """Устанавливает клавиатуру."""
        return self.__class__(
            bot_instance=self.bot_instance,
            text=self.text,
            photo=self.photo,
            photos=self.photos,
            document=self.document,
            buttons=buttons,
        )

    def format(self, *args, **kwargs) -> Template:
        """Форматирует текст с использованием str.format()."""
        if self.text is None:
            raise TemplateError("Cannot format: text is not set")

        try:
            formatted_text = self.text.format(*args, **kwargs)
        except (KeyError, IndexError) as e:
            logger.warning(f"Template format error: {e}, text: {self.text}")
            formatted_text = self.text

        return self.__class__(
            bot_instance=self.bot_instance,
            text=formatted_text,
            photo=self.photo,
            photos=self.photos,
            document=self.document,
            buttons=self.buttons,
        )

    async def send(self, target: TargetType) -> Message | List[Message]:
        """
        Отправляет сообщение.

        Args:
            target: Message, CallbackQuery или chat_id

        Returns:
            Отправленное сообщение или список сообщений (для медиагруппы)
        """
        if isinstance(target, CallbackQuery):
            return await self._send_via_callback(target)

        if isinstance(target, Message):
            return await self._send_via_message(target)

        # Отправка по chat_id
        if self.bot_instance is None:
            raise TemplateError("bot_instance is required for sending by chat_id")

        return await self._send_to_chat(target)

    async def edit(self, target: TargetType, message_id: int | None = None) -> Message:
        """
        Редактирует существующее сообщение.

        Note: Медиагруппы нельзя редактировать, только удалять и отправлять заново.
        """
        if self.photos:
            raise TemplateError("Cannot edit media groups. Delete and send new instead.")

        if isinstance(target, CallbackQuery):
            return await self._edit_via_callback(target)

        if isinstance(target, Message):
            return await self._edit_message(target)

        if self.bot_instance is None:
            raise TemplateError("bot_instance is required for editing by chat_id")

        if message_id is None:
            raise TemplateError("message_id is required when editing by chat_id")

        return await self._edit_chat_message(target, message_id)

    # === Приватные методы для отправки ===

    async def _send_via_callback(self, callback: CallbackQuery) -> Message | List[Message]:
        """Отправляет через callback query."""
        try:
            result = None

            # Медиагруппа
            if self.photos:
                media_group = self._build_media_group()
                result = await callback.message.answer_media_group(media=media_group)
                # Если есть кнопки, отправляем отдельным сообщением
                if self.buttons:
                    await callback.message.answer(
                        text=self.text or "...",
                        reply_markup=self.buttons
                    )

            # Документ
            elif self.document:
                result = await callback.message.answer_document(
                    document=self.document,
                    caption=self.text,
                    reply_markup=self.buttons,
                )

            # Одно фото
            elif self.photo:
                result = await callback.message.answer_photo(
                    photo=self.photo,
                    caption=self.text,
                    reply_markup=self.buttons,
                )

            # Просто текст
            else:
                result = await callback.message.answer(
                    text=self.text or "...",
                    reply_markup=self.buttons,
                )

            await callback.answer()
            logger.debug(f"Message sent via callback to user {callback.from_user.id}")
            return result

        except TelegramBadRequest as e:
            logger.error(f"Failed to send via callback: {e}")
            raise

    async def _send_via_message(self, message: Message) -> Message | List[Message]:
        """Отправляет через объект Message."""
        try:
            # Медиагруппа
            if self.photos:
                media_group = self._build_media_group()
                result = await message.answer_media_group(media=media_group)
                # Кнопки отдельно
                if self.buttons:
                    await message.answer(
                        text=self.text or "...",
                        reply_markup=self.buttons
                    )
                return result

            # Документ
            if self.document:
                return await message.answer_document(
                    document=self.document,
                    caption=self.text,
                    reply_markup=self.buttons,
                )

            # Одно фото
            if self.photo:
                return await message.answer_photo(
                    photo=self.photo,
                    caption=self.text,
                    reply_markup=self.buttons,
                )

            # Текст
            return await message.answer(
                text=self.text or "...",
                reply_markup=self.buttons,
            )

        except TelegramBadRequest as e:
            logger.error(f"Failed to send via message: {e}")
            raise

    async def _send_to_chat(self, chat_id: int | str) -> Message | List[Message]:
        """Отправляет напрямую в чат."""
        try:
            # Медиагруппа
            if self.photos:
                media_group = self._build_media_group()
                result = await self.bot_instance.send_media_group(
                    chat_id=chat_id,
                    media=media_group
                )
                if self.buttons:
                    await self.bot_instance.send_message(
                        chat_id=chat_id,
                        text=self.text or "...",
                        reply_markup=self.buttons
                    )
                return result

            # Документ
            if self.document:
                return await self.bot_instance.send_document(
                    chat_id=chat_id,
                    document=self.document,
                    caption=self.text,
                    reply_markup=self.buttons,
                )

            # Фото
            if self.photo:
                return await self.bot_instance.send_photo(
                    chat_id=chat_id,
                    photo=self.photo,
                    caption=self.text,
                    reply_markup=self.buttons,
                )

            # Текст
            return await self.bot_instance.send_message(
                chat_id=chat_id,
                text=self.text or "...",
                reply_markup=self.buttons,
            )

        except TelegramBadRequest as e:
            logger.error(f"Failed to send to chat {chat_id}: {e}")
            raise

    # === Приватные методы для редактирования ===

    async def _edit_via_callback(self, callback: CallbackQuery) -> Message:
        """Редактирует через callback query."""
        try:
            message = callback.message

            # Новое фото
            if self.photo:
                result = await message.edit_media(
                    media=InputMediaPhoto(media=self.photo, caption=self.text),
                    reply_markup=self.buttons,
                )

            # Новый документ
            elif self.document:
                result = await message.edit_media(
                    media=InputMediaDocument(media=self.document, caption=self.text),
                    reply_markup=self.buttons,
                )

            # Старое фото есть, нового нет
            elif message.photo:
                result = await message.edit_caption(
                    caption=self.text or "",
                    reply_markup=self.buttons,
                )

            # Текстовое сообщение
            elif self.text:
                result = await message.edit_text(
                    text=self.text,
                    reply_markup=self.buttons,
                )
            else:
                result = message

            await callback.answer()
            logger.debug(f"Message edited via callback for user {callback.from_user.id}")
            return result

        except TelegramBadRequest as e:
            if "message is not modified" in str(e).lower():
                logger.debug("Message not modified, skipping edit")
                await callback.answer()
                return callback.message

            if "message can't be edited" in str(e).lower():
                logger.warning("Message can't be edited, sending new")
                return await self._send_via_callback(callback)

            logger.error(f"Failed to edit via callback: {e}")
            raise

    async def _edit_message(self, message: Message) -> Message:
        """Редактирует существующее сообщение."""
        try:
            # Сообщение с фото
            if message.photo:
                if self.photo:
                    return await message.edit_media(
                        media=InputMediaPhoto(media=self.photo, caption=self.text),
                        reply_markup=self.buttons,
                    )
                if self.text:
                    return await message.edit_caption(
                        caption=self.text,
                        reply_markup=self.buttons,
                    )

            # Текстовое сообщение
            if self.text:
                return await message.edit_text(
                    text=self.text,
                    reply_markup=self.buttons,
                )

            return message

        except TelegramBadRequest as e:
            if "message is not modified" in str(e).lower():
                logger.debug("Message not modified, skipping")
                return message

            logger.error(f"Failed to edit message: {e}")
            raise

    async def _edit_chat_message(self, chat_id: int | str, message_id: int) -> Message:
        """Редактирует сообщение по chat_id и message_id."""
        try:
            if self.photo:
                return await self.bot_instance.edit_message_media(
                    chat_id=chat_id,
                    message_id=message_id,
                    media=InputMediaPhoto(media=self.photo, caption=self.text),
                    reply_markup=self.buttons,
                )

            return await self.bot_instance.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=self.text or "...",
                reply_markup=self.buttons,
            )

        except TelegramBadRequest as e:
            if "message is not modified" in str(e).lower():
                logger.debug("Message not modified")
                return None

            logger.error(f"Failed to edit message in chat {chat_id}: {e}")
            raise

    # === Вспомогательные методы ===

    def _build_media_group(self) -> List[InputMediaPhoto]:
        """Строит медиагруппу из списка фото."""
        if not self.photos:
            return []

        media_group = []
        for idx, photo in enumerate(self.photos):
            # Текст добавляется только к первому фото
            caption = self.text if idx == 0 else None
            media_group.append(
                InputMediaPhoto(media=photo, caption=caption)
            )

        return media_group

    def __repr__(self) -> str:
        """Строковое представление для отладки."""
        return (
            f"Template("
            f"text={self.text!r}, "
            f"has_photo={bool(self.photo)}, "
            f"photos_count={len(self.photos)}, "
            f"has_document={bool(self.document)}, "
            f"has_buttons={bool(self.buttons)}, "
            f"has_bot={bool(self.bot_instance)})"
        )
