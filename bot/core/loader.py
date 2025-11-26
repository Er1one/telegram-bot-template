from functools import partial
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from fastapi import FastAPI
import msgspec

from .config import settings


app = FastAPI(docs_url=None, redoc_url=None)

TORTOISE_CONFIG = {
    "connections": {
        "default": settings.tortoise_url,
    },
    "apps": {
        "models": {
            "models": ["models", "aerich.models"],
            "default_connection": "default",
        },
    },
}

bot = Bot(token=settings.bot_token.get_secret_value(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))

storage = RedisStorage.from_url(
    url=settings.redis_url,
    key_builder=DefaultKeyBuilder(with_bot_id=True, with_destiny=True),
    json_loads=msgspec.json.decode,
    json_dumps=partial(lambda obj: str(msgspec.json.encode(obj), encoding="utf-8")),
    connection_kwargs={
        "max_connections": 10,
        "decode_responses": False,
    }
)

dispatcher = Dispatcher(storage=storage,
                        redis=storage.redis)