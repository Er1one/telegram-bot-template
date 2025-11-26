from core.config import settings
from .private import routers as private_routers
from .groups import routers as group_routers
from .errors_router import router as error_router

# Собираем все роутеры
routers = [
    *private_routers,  # Роутеры для личных сообщений
    *group_routers,    # Роутеры для групп
]

# Добавляем error router если логирование включено
if settings.logging_enabled:
    routers.append(error_router)