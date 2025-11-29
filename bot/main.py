from aiogram.types import WebhookInfo
import uvicorn
from loguru import logger

from managers import DatabaseManager
from middlewares import AntiFloodMiddleware, i18n_middleware, UserRegistrationMiddleware
from routes import webhook_router
from core import setup_logging
from core.config import settings
from core.loader import dispatcher, app, bot
from handlers import routers


async def set_webhook():
    """Установка webhook"""
    webhook_url = settings.webhook_url.rstrip("/")
    webhook_path = f"{webhook_url}/{settings.bot_token.get_secret_value()}"
    
    old_webhook: WebhookInfo = await bot.get_webhook_info()
    
    if old_webhook.url == webhook_path:
        logger.info("The current webhook is already setup!")
        return
    
    await bot.set_webhook(webhook_path)
    logger.info(f"Webhook setup: {webhook_url}/{settings.bot_token.get_secret_value()[0:6]}...")
    

async def register_middlewares():
    # Регистрируем middleware на уровне диспетчера
    user_middleware = UserRegistrationMiddleware()
    dispatcher.update.outer_middleware(user_middleware)
    logger.debug("UserRegistration middleware registered")
    
    # Регистрируем AntiFloodMiddleware для предотвращения флуда
    flood_middleware = AntiFloodMiddleware(redis=dispatcher.storage.redis, min_interval=0.3) # 0.3 секунды между действиями
    dispatcher.update.outer_middleware(flood_middleware)
    logger.debug("AntiFloodMiddleware middleware registered")

    # Регистрируем i18n middleware
    i18n_middleware.setup(dispatcher=dispatcher)
    await i18n_middleware.core.startup()
    logger.debug("i18n middleware registered")


async def on_startup():    
    app.include_router(webhook_router)
    
    dispatcher.include_routers(*routers)
    
    await set_webhook()
    await register_middlewares()
    await DatabaseManager.init()


async def on_shutdown():
    """Действия при остановке"""
    await bot.session.close()
    await DatabaseManager.close()
    logger.info("Bot stopped")


if __name__ == "__main__":
    setup_logging()
    
    app.add_event_handler("startup", on_startup)
    app.add_event_handler("shutdown", on_shutdown)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.app_port,
        access_log=False,
        log_config=None
    )