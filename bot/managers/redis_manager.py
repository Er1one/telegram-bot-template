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
        return ":".join(str(part) for part in parts)
    
    @staticmethod
    async def get_string(redis: Redis, key: str) -> str | None:
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
        return await redis.setex(key, ttl, value)
    
    @staticmethod
    async def delete(redis: Redis, key: str) -> int:
        return await redis.delete(key)
    
    @staticmethod
    async def exists(redis: Redis, key: str) -> bool:
        return await redis.exists(key) > 0