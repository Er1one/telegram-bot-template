from aiogram.types import User
from aiogram_i18n.managers import BaseManager
from redis.asyncio import Redis
from services import UserService


class I18nManager(BaseManager):
    key: str

    def __init__(self, key: str = "locale") -> None:
        super().__init__()
        self.key = key

    async def get_locale(
        self,
        event_from_user: User,
        redis: Redis,
    ) -> str:
        return await UserService.get_user_locale(redis, event_from_user.id)

    async def set_locale(
        self, 
        locale: str
    ) -> None:
        ...