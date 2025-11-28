import logging
import sys

from loguru import logger

from core.config import settings


def setup_logging() -> None:
    tortoisedb_logger = logging.getLogger("tortoise.db_client")
    tortoisedb_logger.setLevel(logging.INFO)
    tortoise_logger = logging.getLogger("tortoise")
    tortoise_logger.setLevel(logging.INFO)
    logger.remove()

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # Консольный вывод
    logger.add(
        sys.stderr,
        format=log_format,
        level="DEBUG" if settings.debug else "INFO",
        colorize=True,
        backtrace=False,
        diagnose=False,
    )

    # Файловое логирование
    logger.add(
        "logs/bot.log",
        format=log_format,
        level="INFO",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        backtrace=False,
        diagnose=False,
        enqueue=True,
    )

    # Отдельный файл для ошибок
    logger.add(
        "logs/errors.log",
        format=log_format,
        level="ERROR",
        rotation="5 MB",
        retention="60 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
        enqueue=True,
    )

    _setup_intercept_handler()

    logger.info("The logging system has been successfully configured")


def _setup_intercept_handler() -> None:
    """Перехват логов от библиотек, использующих стандартный logging"""

    class InterceptHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            frame, depth = sys._getframe(6), 6
            while frame and frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)