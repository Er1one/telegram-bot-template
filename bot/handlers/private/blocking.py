from aiogram import Router
from aiogram.filters import KICKED, MEMBER, ChatMemberUpdatedFilter
from aiogram.types import ChatMemberUpdated
from loguru import logger

from services import UserService


router = Router()

@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=KICKED))
async def user_blocked_bot(event: ChatMemberUpdated):
    if event.chat.type != "private":
        
        user_id = event.from_user.id
        
        UserService.set_user_banned(user_id, True)
        logger.debug(f"User {user_id} has blocked the bot")


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def user_unblocked_bot(event: ChatMemberUpdated):
    if event.chat.type != "private":
        
        user_id = event.from_user.id
        
        UserService.set_user_banned(user_id, False)
        logger.debug(f"User {user_id} has unblocked the bot")