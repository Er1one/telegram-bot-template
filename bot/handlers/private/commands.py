"""Обработчики команд в личных сообщениях"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram_i18n import I18nContext
from loguru import logger

from filters import IsPrivateChat
from keyboards import get_main_menu_keyboard
from utils import Template

router = Router(name="private_commands")


@router.message(Command("menu"), IsPrivateChat())
async def cmd_menu(message: Message, i18n: I18nContext) -> None:
    """Главное меню"""
    logger.debug(f"User {message.from_user.id} opened menu")

    template = Template(
        text=i18n.get("main-menu"),
        buttons=get_main_menu_keyboard(i18n)
    )
    await template.send(message)


@router.message(Command("help"), IsPrivateChat())
async def cmd_help(message: Message, i18n: I18nContext) -> None:
    """Справка по использованию бота"""
    template = Template(text=i18n.get("help-text"))
    await template.send(message)


@router.message(Command("profile"), IsPrivateChat())
async def cmd_profile(message: Message, i18n: I18nContext) -> None:
    """Профиль пользователя"""
    user = message.from_user

    template = Template(
        text=i18n.get(
            "profile",
            user_id=user.id,
            username=user.username or i18n.get("no-username"),
            first_name=user.first_name,
            language=i18n.locale
        )
    )
    await template.send(message)
