# Telegram Bot Template

Production-ready шаблон для Telegram ботов на aiogram 3.x с PostgreSQL, Redis и Docker.

## Stack

- **aiogram 3.x** — async Telegram Bot API
- **FastAPI** — webhook endpoint
- **PostgreSQL + Tortoise ORM** — база данных с миграциями (Aerich)
- **Redis** — FSM storage и кэширование
- **aiogram-i18n + Fluent** — мультиязычность
- **Docker Compose** — dev/prod окружения
- **Loguru** — структурированное логирование

## Quick Start

```bash
# Клонируйте и настройте окружение
git clone https://github.com/Er1one/telegram-bot-template.git && cd bot-template
cp .env.example .env

# Отредактируйте .env (BOT_TOKEN, пароли, WEBHOOK_URL)

# Запустите
make dev                    # разработка (hot reload, pgadmin)
# или
make prod                   # продакшен (оптимизировано)

# Инициализируйте БД
make aerich-init
make aerich migrate
make aerich upgrade
```

## Структура

```
bot/
├── core/           # Конфигурация, loader, логирование
├── handlers/       # Роутеры (private/, groups/)
├── filters/        # Кастомные фильтры
├── keyboards/      # Inline клавиатуры
├── middlewares/    # User registration, i18n
├── models/         # Tortoise ORM модели
├── services/       # Бизнес-логика (UserService, BroadcastService)
├── managers/       # Database, Redis, i18n менеджеры
├── routes/         # FastAPI webhook endpoint
├── locales/        # Переводы (ru/en)
└── utils/          # Template, хелперы
```

## Основные команды

### Docker
```bash
make dev/prod       # Переключить окружение и запустить
make up/down        # Запустить/остановить
make logs [service] # Просмотр логов
make shell service  # Войти в контейнер
make rebuild        # Пересобрать
```

### Миграции БД
```bash
make aerich-init            # Первая инициализация
make aerich migrate         # Создать миграцию
make aerich upgrade         # Применить миграции
make aerich downgrade       # Откат миграции
make aerich history         # История
make db-backup              # Бэкап БД
```

## Работа с миграциями

### Создание миграции после изменения моделей

```bash
# 1. Измените модель в bot/models/
# 2. Создайте миграцию
make aerich migrate

# 3. Примените
make aerich upgrade
```

### Откат миграции

```bash
# Откатить последнюю
make aerich downgrade

# Посмотреть историю
make aerich history
```

## Добавление функционала

### Новый handler

`bot/handlers/private/my_handler.py`:
```python
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from filters import IsPrivateChat

router = Router()

@router.message(Command("test"), IsPrivateChat())
async def cmd_test(message: Message):
    await message.answer("Test!")
```

Зарегистрируйте в `bot/handlers/private/__init__.py`:
```python
from .my_handler import router as my_router

routers = [..., my_router]
```

### Новая модель

`bot/models/chat.py`:
```python
from tortoise import Model, fields

class Chat(Model):
    id = fields.BigIntField(primary_key=True)
    title = fields.CharField(max_length=255)

    class Meta:
        table = "chats"
```

Импортируйте в `bot/models/__init__.py` и создайте миграцию:
```bash
make aerich migrate --name "add_chat_model"
make aerich upgrade
```

### Новый фильтр

`bot/filters/my_filter.py`:
```python
from aiogram.filters import BaseFilter
from aiogram.types import Message

class MyFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.text.startswith("!")
```

### Рассылка

```python
from services import BroadcastService
from utils import Template

template = Template(
    text="Привет всем!",
    photo="https://example.com/image.jpg"
)

stats = await BroadcastService.broadcast_template(
    bot=bot,
    template=template,
    exclude_banned=True,
    delay=0.05
)
# stats = {total, success, failed, blocked}
```

### Template (отправка/редактирование сообщений)

```python
from utils import Template

# Простое сообщение
template = Template(text="Привет!")
await template.send(message)

# С фото
template = Template(text="Описание", photo="photo.jpg")
await template.send(message)

# Несколько фото (media group)
template = Template(
    text="Галерея",
    photos=["1.jpg", "2.jpg", "3.jpg"]
)
await template.send(message)

# Редактирование
template = Template(text="Обновлено", buttons=keyboard)
await template.edit(callback_query)
```

## Переменные окружения

Обязательные:
- `BOT_TOKEN` — токен от @BotFather
- `PG_PASSWORD` — пароль PostgreSQL
- `REDIS_PASSWORD` — пароль Redis
- `WEBHOOK_URL` — публичный URL для webhook
- `ADMIN_IDS` — список ID админов через запятую в квадратных скобках

Опциональные:
- `DEFAULT_LANGUAGE` — ru/en (default: ru)
- `APP_PORT` — порт webhook (default: 5000)
- `LOGGING_ENABLED` — отправка ошибок в TG (default: False)
- `REDIS_CACHE_TTL` — TTL кэша в днях (default: 7)

Полный список в `.env.example`.

## Оптимизации

- **Батчинг рассылок** — загрузка пользователей по 100 шт (экономия RAM)
- **Индексы БД** — `is_banned` для быстрых фильтров
- **Redis connection pool** — max_connections=10
- **Middleware на уровне dispatcher** — один экземпляр для всех событий
- **Автоматический разбан** — пользователи разбаниваются при возвращении

## Production

1. Измените пароли в `.env`
2. Настройте `WEBHOOK_URL` с SSL
3. Включите логирование: `LOGGING_ENABLED=True`
4. Настройте reverse proxy (nginx/traefik)
5. Бэкапы БД через cron: `0 2 * * * cd /path && make db-backup`

### Nginx пример

```nginx
location /webhook {
    proxy_pass http://localhost:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## Полезные фичи

- **Фильтры**: `IsPrivateChat`, `IsGroupChat`, `IsChatAdmin`, `IsAdmin`, `HasMedia`, `HasLinks`, `TextLengthFilter`
- **Template**: единый интерфейс для send/edit с поддержкой фото, медиагрупп, документов
- **BroadcastService**: массовая рассылка с обработкой rate limits
- **Автоматическая регистрация**: middleware регистрирует пользователей в БД
- **i18n**: автоопределение языка с кэшированием в Redis

## Troubleshooting

```bash
# Проверить статус
make ps

# Логи
make logs
make logs bot

# Пересобрать
make rebuild

# Полная очистка
make clean-all
```

## Ссылки

- [aiogram 3.x](https://docs.aiogram.dev/)
- [Tortoise ORM](https://tortoise.github.io/)
- [Aerich](https://github.com/tortoise/aerich)
- [Fluent](https://projectfluent.org/)

## License

MIT
