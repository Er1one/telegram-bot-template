"""Роутеры для личных сообщений"""

from .start import router as start_router
from .commands import router as commands_router
from .menu import router as menu_router
from .settings import router as settings_router

routers = [
    start_router,
    commands_router,
    menu_router,
    settings_router
]

__all__ = ["routers"]
