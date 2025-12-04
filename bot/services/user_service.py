from aiogram.types import User
from loguru import logger
from redis.asyncio import Redis

from core.config import settings
from managers import RedisManager
from models import BotUser


class UserService:
    """Сервис для работы с пользователями (Redis + БД)"""
    
    @staticmethod
    async def set_user_banned(user_id: int, banned: bool) -> BotUser:
        bot_user = await BotUser.get_or_none(id=user_id)
        
        if bot_user:
            if bot_user.is_banned is not banned:
                bot_user.is_banned = banned
                await bot_user.save()

    @staticmethod
    async def register_user(user: User) -> BotUser:
        """
        Регистрирует нового пользователя или возвращает существующего.
        Автоматически разбанивает пользователя, если он вернулся после блокировки бота.

        Args:
            user: Объект пользователя из Telegram

        Returns:
            Объект пользователя из БД
        """
        bot_user = await BotUser.get_or_none(id=user.id)

        if bot_user:
            # Обновляем данные существующего пользователя
            updated = False

            # Если пользователь был забанен (заблокировал бота), но теперь вернулся - разбаниваем
            if bot_user.is_banned:
                bot_user.is_banned = False
                updated = True
                logger.info(f"User {user.id} unbanned (returned after blocking the bot)")

            if bot_user.username != user.username:
                bot_user.username = user.username
                updated = True

            if bot_user.full_name != user.full_name:
                bot_user.full_name = user.full_name
                updated = True

            if bot_user.language_code != user.language_code:
                bot_user.language_code = user.language_code
                updated = True

            if updated:
                await bot_user.save()
                logger.info(f"Updated user {user.id} data")

            return bot_user

        # Создаём нового пользователя
        bot_user = await BotUser.create(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            language_code=user.language_code or settings.default_language
        )

        logger.info(f"Registered new user {user.id} (@{user.username})")
        return bot_user

    @staticmethod
    async def get_user_locale(redis: Redis, user_id: int) -> str:
        """
        Получает локаль пользователя.
        Приоритет: Redis → БД → default locale
        """
        redis_key = RedisManager.make_key("user", user_id, "locale")
        redis_locale = await RedisManager.get_string(redis, redis_key)
        
        if redis_locale:
            return redis_locale
        
        user = await BotUser.get_or_none(id=user_id)
        if user and user.language_code:
            # Кешируем в Redis
            await RedisManager.set_string(
                redis, 
                redis_key, 
                user.language_code
            )
            return user.language_code
        
        return settings.default_language
    
    @staticmethod
    async def set_user_locale(redis: Redis, user_id: int, locale: str) -> bool:
        """
        Устанавливает локаль пользователя в Redis и БД.
        Возвращает True если успешно, иначе False
        """
        redis_key = RedisManager.make_key("user", user_id, "locale")
        
        # Сохраняем в Redis
        await RedisManager.set_string(
            redis, 
            redis_key, 
            locale
        )
        
        # Сохраняем в БД
        user = await BotUser.get_or_none(id=user_id)
        if user:
            user.language_code = locale
            await user.save()
            return True
        
        return False