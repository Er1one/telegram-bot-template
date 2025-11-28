from aiogram.types import Update
from fastapi import APIRouter, Response
from core.loader import dispatcher, bot
from core.config import settings


router = APIRouter()


@router.post(f"/{settings.bot_token.get_secret_value()}")
async def webhook_endpoint(update: dict):
    """
    Обработчик webhook от Telegram.
    """
    telegram_update = Update(**update)
    await dispatcher.feed_webhook_update(bot, telegram_update)
    return Response(status_code=200)