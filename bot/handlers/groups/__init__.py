"""Роутеры для групповых чатов"""

from .chat_member import router as chat_member_router
from .commands import router as commands_router

routers = [
    chat_member_router,
    commands_router
]

__all__ = ["routers"]
