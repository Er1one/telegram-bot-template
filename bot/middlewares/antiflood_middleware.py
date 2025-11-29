from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update
from loguru import logger
from redis.asyncio import Redis
import time


class AntiFloodMiddleware(BaseMiddleware):
    """
    Middleware для предотвращения флуда.
    - Для CallbackQuery: отправляет уведомление через i18n
    - Для Message: просто дропает обновление
    """
    def __init__(
        self,
        redis: Redis,
        min_interval: float = 0.2
    ):
        self.redis = redis
        self.min_interval = min_interval
        super().__init__()
        logger.info(f"AntiFloodMiddleware initialized with interval: {min_interval}s")
    
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        # Извлекаем реальное событие из Update
        actual_event = None
        if event.message:
            actual_event = event.message
        elif event.callback_query:
            actual_event = event.callback_query
        else:
            # Если это не message и не callback_query, пропускаем
            return await handler(event, data)
        
        user_id = actual_event.from_user.id
        current_time = time.time()
        
        key = f"flood:{user_id}"
        
        # Получаем время последнего действия
        last_action_raw = await self.redis.get(key)
        
        if last_action_raw is not None:
            last_action_str = last_action_raw.decode() if isinstance(last_action_raw, bytes) else str(last_action_raw)
            last_time = float(last_action_str)
            time_passed = current_time - last_time
            
            if time_passed < self.min_interval:
                # Флуд обнаружен
                if isinstance(actual_event, CallbackQuery):
                    i18n = data.get("i18n")
                    if i18n:
                        message = i18n.get("antiflood-warning")
                    else:
                        message = "⚠️ Too fast!"
                    
                    await actual_event.answer(message, show_alert=True)
                    
                    logger.warning(
                        f"User {user_id} FLOOD (callback): interval={time_passed:.3f}s"
                    )
                else:
                    logger.warning(
                        f"User {user_id} FLOOD (message): interval={time_passed:.3f}s - DROPPED"
                    )
                
                return  # Не вызываем handler
        
        # Сохраняем время текущего действия
        ttl_ms = int(self.min_interval * 3 * 1000)  # Конвертируем в миллисекунды
        await self.redis.psetex(key, ttl_ms, str(current_time))
        
        logger.debug(f"User {user_id} action allowed, TTL: {ttl_ms}ms")
        
        return await handler(event, data)