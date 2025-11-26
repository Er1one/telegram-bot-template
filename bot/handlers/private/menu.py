"""Обработчики callback'ов главного меню"""

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram_i18n import I18nContext

from keyboards import get_main_menu_keyboard, get_settings_keyboard
from utils import Template

router = Router(name="private_menu")


@router.callback_query(F.data == "menu:main")
async def callback_main_menu(callback: CallbackQuery, i18n: I18nContext) -> None:
    """Вернуться в главное меню"""
    template = Template(
        text=i18n.get("main-menu"),
        buttons=get_main_menu_keyboard(i18n)
    )
    await template.edit(callback)


@router.callback_query(F.data == "menu:profile")
async def callback_profile(callback: CallbackQuery, i18n: I18nContext) -> None:
    """Показать профиль"""
    user = callback.from_user

    back_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=i18n.get("back-button"), callback_data="menu:main")]
        ]
    )

    template = Template(
        text=i18n.get(
            "profile",
            user_id=user.id,
            username=user.username or i18n.get("no-username"),
            first_name=user.first_name,
            language=i18n.locale
        ),
        buttons=back_kb
    )
    await template.edit(callback)


@router.callback_query(F.data == "menu:settings")
async def callback_settings(callback: CallbackQuery, i18n: I18nContext) -> None:
    """Открыть настройки"""
    template = Template(
        text=i18n.get("settings-menu"),
        buttons=get_settings_keyboard(i18n)
    )
    await template.edit(callback)


@router.callback_query(F.data == "menu:help")
async def callback_help(callback: CallbackQuery, i18n: I18nContext) -> None:
    """Показать справку"""
    back_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=i18n.get("back-button"), callback_data="menu:main")]
        ]
    )

    template = Template(
        text=i18n.get("help-text"),
        buttons=back_kb
    )
    await template.edit(callback)
