from __future__ import annotations
from typing import TYPE_CHECKING
from datetime import timedelta
from core.config import settings

if TYPE_CHECKING:
    from redis.asyncio import Redis
    from redis.typing import ExpiryT


class RedisManager:
    @staticmethod
    def make_key(*parts: str | int) -> str:
        """Создает ключ из частей, соединяя их через двоеточие."""
        return ":".join(str(part) for part in parts)
    
    @staticmethod
    async def get_string(redis: Redis, key: str) -> str | None:
        """Получает строковое значение по ключу."""
        value = await redis.get(key)
        if value:
            return value.decode() if isinstance(value, bytes) else value
        return None
    
    @staticmethod
    async def set_string(
        redis: Redis, 
        key: str, 
        value: str, 
        ttl: ExpiryT = timedelta(days=settings.redis_cache_ttl)
    ) -> bool:
        """Устанавливает строковое значение с TTL."""
        return await redis.setex(key, ttl, value)
    
    @staticmethod
    async def delete(redis: Redis, key: str) -> int:
        """Удаляет ключ."""
        return await redis.delete(key)
    
    @staticmethod
    async def exists(redis: Redis, key: str) -> bool:
        """Проверяет существование ключа."""
        return await redis.exists(key) > 0
    
    @staticmethod
    async def get_int(redis: Redis, key: str) -> int | None:
        """Получает целочисленное значение по ключу."""
        value = await redis.get(key)
        if value:
            value_str = value.decode() if isinstance(value, bytes) else value
            return int(value_str)
        return None
    
    @staticmethod
    async def set_int(
        redis: Redis,
        key: str,
        value: int,
        ttl: ExpiryT = timedelta(minutes=1)
    ) -> bool:
        """Устанавливает целочисленное значение с TTL."""
        return await redis.setex(key, ttl, value)
    
    @staticmethod
    async def increment(
        redis: Redis,
        key: str,
        amount: int = 1
    ) -> int:
        """
        Увеличивает значение счетчика.
        Возвращает новое значение.
        """
        return await redis.incrby(key, amount)
    
    @staticmethod
    async def decrement(
        redis: Redis,
        key: str,
        amount: int = 1
    ) -> int:
        """
        Уменьшает значение счетчика.
        Возвращает новое значение.
        """
        return await redis.decrby(key, amount)
    
    @staticmethod
    async def increment_with_ttl(
        redis: Redis,
        key: str,
        ttl: ExpiryT = timedelta(minutes=1),
        amount: int = 1
    ) -> int:
        """
        Увеличивает счетчик и устанавливает TTL, если ключ новый.
        Возвращает новое значение счетчика.
        """
        pipe = redis.pipeline()
        pipe.incrby(key, amount)
        pipe.expire(key, ttl)
        results = await pipe.execute()
        return results[0]
    
    @staticmethod
    async def get_ttl(redis: Redis, key: str) -> int:
        """
        Получает оставшееся время жизни ключа в секундах.
        Возвращает -1 если ключ существует без TTL, -2 если ключа нет.
        """
        return await redis.ttl(key)
    
    @staticmethod
    async def set_if_not_exists(
        redis: Redis,
        key: str,
        value: str,
        ttl: ExpiryT | None = None
    ) -> bool:
        """
        Устанавливает значение только если ключ не существует (SETNX).
        Возвращает True если значение установлено, False если ключ уже существует.
        """
        if ttl:
            return await redis.set(key, value, ex=ttl, nx=True)
        return await redis.setnx(key, value)
    
    @staticmethod
    async def get_and_delete(redis: Redis, key: str) -> str | None:
        """
        Атомарно получает и удаляет значение.
        """
        pipe = redis.pipeline()
        pipe.get(key)
        pipe.delete(key)
        results = await pipe.execute()
        value = results[0]
        if value:
            return value.decode() if isinstance(value, bytes) else value
        return None
    
    @staticmethod
    async def get_multiple(redis: Redis, *keys: str) -> list[str | None]:
        """
        Получает несколько значений за один запрос.
        """
        values = await redis.mget(*keys)
        return [
            (v.decode() if isinstance(v, bytes) else v) if v else None
            for v in values
        ]
    
    @staticmethod
    async def delete_multiple(redis: Redis, *keys: str) -> int:
        """
        Удаляет несколько ключей за один запрос.
        Возвращает количество удаленных ключей.
        """
        if not keys:
            return 0
        return await redis.delete(*keys)
    
    @staticmethod
    async def delete_by_pattern(redis: Redis, pattern: str) -> int:
        """
        Удаляет все ключи, соответствующие паттерну.
        Возвращает количество удаленных ключей.
        
        Примеры паттернов:
        - "user:*" - все ключи начинающиеся с "user:"
        - "antispam:*:123" - все антиспам ключи для пользователя 123
        """
        cursor = 0
        deleted_count = 0
        
        while True:
            cursor, keys = await redis.scan(cursor, match=pattern, count=100)
            if keys:
                deleted_count += await redis.delete(*keys)
            if cursor == 0:
                break
        
        return deleted_count