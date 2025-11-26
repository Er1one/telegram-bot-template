from pathlib import Path
from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores import FluentRuntimeCore
from loguru import logger

from core.config import settings
from managers import I18nManager

LOCALES_DIR = Path(__file__).parent.parent / "locales"

i18n_middleware = I18nMiddleware(
    core=FluentRuntimeCore(
        path=LOCALES_DIR / "{locale}",  
        raise_key_error=False
    ),
    manager=I18nManager(),
    default_locale=settings.default_language
)