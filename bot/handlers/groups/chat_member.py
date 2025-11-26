from aiogram import Router
from aiogram.filters import ChatMemberUpdatedFilter, MEMBER, ADMINISTRATOR, LEFT, KICKED
from aiogram.types import ChatMemberUpdated
from loguru import logger

router = Router(name="group_chat_member")


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=LEFT | KICKED))
async def bot_removed_from_chat(event: ChatMemberUpdated) -> None:
    """Бот удалён из чата"""
    
    logger.info(
        f"Bot removed from chat",
        chat_id=event.chat.id,
        chat_title=event.chat.title
    )


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER | ADMINISTRATOR))
async def bot_added_to_chat(event: ChatMemberUpdated) -> None:
    """Бот добавлен в чат"""
    
    logger.info(
        f"Bot added to chat",
        chat_id=event.chat.id,
        chat_title=event.chat.title,
        added_by=event.from_user.id
    )
