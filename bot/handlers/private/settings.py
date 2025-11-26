"""Обработчики настроек пользователя"""

from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram_i18n import I18nContext
from loguru import logger
from redis.asyncio import Redis

from keyboards import get_language_keyboard, get_settings_keyboard
from services import UserService
from utils import Template

router = Router(name="private_settings")


@router.callback_query(F.data == "settings:language")
async def callback_language(callback: CallbackQuery, i18n: I18nContext) -> None:
    """Показать выбор языка"""
    template = Template(
        text=i18n.get("select-language"),
        buttons=get_language_keyboard()
    )
    await template.edit(callback)


@router.callback_query(F.data.startswith("lang:"))
async def callback_set_language(
    callback: CallbackQuery,
    i18n: I18nContext,
    redis: Redis
) -> None:
    """Установить выбранный язык"""
    new_lang = callback.data.split(":")[1]

    success = await UserService.set_user_locale(redis, callback.from_user.id, new_lang)

    if success:
        i18n.locale = new_lang
        logger.info(f"User {callback.from_user.id} changed language to {new_lang}")

        template = Template(
            text=i18n.get("language-changed"),
            buttons=get_settings_keyboard(i18n)
        )
        await template.edit(callback)
    else:
        await callback.answer(i18n.get("language-error"), show_alert=True)
