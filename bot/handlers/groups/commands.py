from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram_i18n import I18nContext
from loguru import logger

from filters import  ChatTypeFilter, IsChatAdmin
from utils import Template

router = Router(name="group_commands")


@router.message(Command("help"), ChatTypeFilter(chat_type=["group", "supergroup"]))
async def cmd_help_group(message: Message, i18n: I18nContext) -> None:
    """Справка для группы"""
    
    await Template(
        text=i18n.get("help-text-chat")
    ).send(message)


@router.message(Command("stats"), ChatTypeFilter(chat_type=["group", "supergroup"]), IsChatAdmin())
async def cmd_stats_group(message: Message, i18n: I18nContext) -> None:
    """Статистика группы (для админов)"""
    
    # Получаем количество участников
    member_count = await message.bot.get_chat_member_count(message.chat.id)
    
    await Template(
        text=i18n.get("chat-stats", member_count=member_count,
                      chat_title=message.chat.title, chat_id=str(message.chat.id))
    ).send(message)
    
    logger.debug(f"User {message.from_user.id} requested stats for chat {message.chat.id}")
