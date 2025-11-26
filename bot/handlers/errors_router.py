import traceback
from aiogram import Bot, Router
from aiogram.types import ErrorEvent, Update
from loguru import logger

from core.config import settings
from utils import escape_html


router = Router()

@router.errors()
async def errors_handler(event: ErrorEvent, bot: Bot) -> None:
    update_info = format_update_info(event.update)
    
    # Форматируем traceback
    error_text = ''.join(traceback.format_exception(
        type(event.exception),
        event.exception,
        event.exception.__traceback__
    ))
    
    # Обрезаем если слишком длинный
    if len(error_text) > 2000:
        error_text = error_text[-2000:]
    
    message = (
        f"📛 ОШИБКА В БОТЕ 📛\n\n"
        f"{update_info}\n\n"
        f"Exception: {type(event.exception).__name__}\n"
        f"Message: {str(event.exception)}\n\n"
        f"<pre>{error_text}</pre>"
    )
    
    try:
        await bot.send_message(
            chat_id=settings.logging_chat_id,
            text=escape_html(message),
            message_thread_id=settings.errors_thread_id,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")


def format_update_info(update: Update) -> str:
    """Форматирует информацию об update в читаемый вид."""
    info = [f"Update ID: {update.update_id}"]
    
    if update.message:
        msg = update.message
        info.append(f"Type: Message")
        info.append(f"From: {msg.from_user.id} (@{msg.from_user.username or 'no username'})")
        info.append(f"Chat: {msg.chat.id} ({msg.chat.type})")
        if msg.text:
            text = msg.text[:100] + "..." if len(msg.text) > 100 else msg.text
            info.append(f"Text: {text}")
        elif msg.caption:
            caption = msg.caption[:100] + "..." if len(msg.caption) > 100 else msg.caption
            info.append(f"Caption: {caption}")
    
    elif update.callback_query:
        cb = update.callback_query
        info.append(f"Type: CallbackQuery")
        info.append(f"From: {cb.from_user.id} (@{cb.from_user.username or 'no username'})")
        info.append(f"Data: {cb.data}")
        if cb.message:
            info.append(f"Message ID: {cb.message.message_id}")
    
    elif update.inline_query:
        iq = update.inline_query
        info.append(f"Type: InlineQuery")
        info.append(f"From: {iq.from_user.id} (@{iq.from_user.username or 'no username'})")
        info.append(f"Query: {iq.query}")
    
    else:
        info.append(f"Type: {update.model_fields_set}")
    
    return "\n".join(info)