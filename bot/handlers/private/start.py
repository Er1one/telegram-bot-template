from aiogram import Bot, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram_i18n import I18nContext
from loguru import logger

from filters import IsPrivateChat, IsAdmin
from services import BroadcastService
from utils import Template

router = Router()


@router.message(CommandStart(), IsPrivateChat())
async def cmd_start(message: Message, i18n: I18nContext) -> None:
    """Обработчик команды /start"""
    logger.info(f"User {message.from_user.id} started bot")

    await message.answer(
        i18n.get("welcome", name=message.from_user.first_name)
    )


#
#
# Пример реализации рассылки
#
# @router.message(Command("mail"), IsPrivateChat(), IsAdmin())
# async def cmd_mail(message: Message, i18n: I18nContext, bot: Bot) -> None:
#     """Обработчик команды /mail - только для администраторов"""
#     logger.info(f"Admin {message.from_user.id} started broadcast")

#     template = Template(
#         text="<b>Тестовая рассылка!</b>\n\n🚀Сегодня эта тестовая рассылка, а завтра что? Обычная рассылка вот и думай головой что происходит <i><b>арбуз</b></i> веревка оксимирон абоба.",
#         photos=["https://img.freepik.com/premium-photo/minimalistic-black-background-with-silhouette-ancient-samurai-red-holding-up-his-sword-ready-fight_380677-103.jpg",
#                 "https://i.pinimg.com/originals/da/e4/ff/dae4ff486b9572ec9bddb40f3be52a7c.jpg"]
#     )

#     stats = await BroadcastService.broadcast_template(bot, template)

#     await message.answer(
#         f"📤 <b>Рассылка завершена</b>\n\n"
#         f"✅ Успешно: {stats['success']}\n"
#         f"❌ Ошибок: {stats['failed']}\n"
#         f"🚫 Заблокировали: {stats['blocked']}\n"
#         f"📊 Всего: {stats['total']}"
#     )
#     logger.info(f"Broadcast stats: {stats}")