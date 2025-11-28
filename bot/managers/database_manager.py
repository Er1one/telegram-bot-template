from loguru import logger
from tortoise import Tortoise

from core.loader import TORTOISE_CONFIG


class DatabaseManager:
    """Менеджер для управления подключением к базе данных"""

    @staticmethod
    @logger.catch
    async def init() -> None:
        """Инициализация подключения к БД"""
        logger.debug("Initializing the connection to the database")
        await Tortoise.init(config=TORTOISE_CONFIG)
        logger.success("Database successfully connected")

    @staticmethod
    @logger.catch
    async def close() -> None:
        """Закрытие подключения к БД"""
        logger.debug("Closing database connections")
        await Tortoise.close_connections()
        logger.success("Database connections are closed")
