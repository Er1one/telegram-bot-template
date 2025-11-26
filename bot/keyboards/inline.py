from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram_i18n import I18nContext


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора языка"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")
            ]
        ]
    )
    return keyboard


def get_main_menu_keyboard(i18n: I18nContext) -> InlineKeyboardMarkup:
    """Главное меню бота"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.get("menu-profile"),
                    callback_data="menu:profile"
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.get("menu-settings"),
                    callback_data="menu:settings"
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.get("menu-help"),
                    callback_data="menu:help"
                )
            ]
        ]
    )
    return keyboard


def get_settings_keyboard(i18n: I18nContext) -> InlineKeyboardMarkup:
    """Клавиатура настроек"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.get("settings-language"),
                    callback_data="settings:language"
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.get("back-button"),
                    callback_data="menu:main"
                )
            ]
        ]
    )
    return keyboard
