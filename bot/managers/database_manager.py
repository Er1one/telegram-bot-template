from loguru import logger
from tortoise import Tortoise

from core.loader import TORTOISE_CONFIG


class DatabaseManager:
    """Менеджер для управления подключением к базе данных"""

    @staticmethod
    @logger.catch
    async def init() -> None:
        """Инициализация подключения к БД"""
        logger.debug("Инициализация подключения к базе данных")
        await Tortoise.init(config=TORTOISE_CONFIG)
        logger.success("База данных успешно подключена")

    @staticmethod
    @logger.catch
    async def close() -> None:
        """Закрытие подключения к БД"""
        logger.debug("Закрытие подключений к базе данных")
        await Tortoise.close_connections()
        logger.success("Подключения к базе данных закрыты")
