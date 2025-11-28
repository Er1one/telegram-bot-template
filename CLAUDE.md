# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a production-ready Telegram bot template built with:
- **aiogram 3.x** - Asynchronous Telegram Bot API
- **FastAPI** - Webhook endpoint for receiving updates
- **PostgreSQL + Tortoise ORM** - Persistent data storage with migrations (Aerich)
- **Redis** - FSM state storage and caching
- **Docker Compose** - Containerized dev/prod environments
- **aiogram-i18n + Fluent** - Multi-language support
- **Python 3.13+** - Minimum required version

The bot operates exclusively via **webhook mode** (not polling), requiring a public URL for receiving updates from Telegram.

## Quick Start Commands

All development commands use Docker Compose and `make`:

```bash
# Switch to development environment and start
make dev

# Switch to production environment and start
make prod

# Container management
make build      # Build images
make up         # Start containers
make down       # Stop containers
make ps         # Show container status
make logs [service]   # View logs (omit service name for all)
make shell SERVICE    # Enter a container shell (e.g., make shell bot)
make rebuild    # Rebuild and restart everything

# Database migrations (Aerich)
make aerich-init       # Initialize Aerich (run once)
make aerich migrate    # Create migration after model changes
make aerich upgrade    # Apply pending migrations
make aerich downgrade  # Rollback last migration
make aerich history    # View migration history

# Database backup
make db-backup   # Create backup in ./backups/

# Cleanup
make clean      # Remove current environment containers and volumes
make clean-all  # Remove both dev and prod environments completely
```

## Architecture Overview

### Entry Point
**[bot/main.py](bot/main.py)** - FastAPI app initialization, webhook setup, middleware registration, and event handlers (startup/shutdown)

### Core Configuration
- **[bot/core/config.py](bot/core/config.py)** - Settings class using pydantic, loads from `.env`, provides `tortoise_url` and `redis_url` properties
- **[bot/core/loader.py](bot/core/loader.py)** - Initializes FastAPI app, Bot instance, Dispatcher, RedisStorage, and Tortoise ORM configuration
- **[bot/core/logging.py](bot/core/logging.py)** - Loguru configuration for structured logging

### Request Flow Architecture

```
Telegram Updates
    ↓
FastAPI Webhook Endpoint [bot/routes/]
    ↓
Dispatcher (aiogram)
    ↓
Middlewares [bot/middlewares/]
    - UserRegistrationMiddleware: Registers users in DB on first interaction
    - i18n middleware: Sets user language from cache or detects it
    ↓
Routers & Handlers [bot/handlers/]
    ├─ private/ - Direct message handlers
    └─ groups/ - Group message handlers
    ↓
Filters [bot/filters/] - Custom filter logic applied at router level
    ↓
Services [bot/services/] - Business logic (UserService, BroadcastService)
    ↓
Managers [bot/managers/] - Direct DB/Redis/i18n access
    ↓
Models [bot/models/] - Tortoise ORM database models

State Management: Redis FSM storage via RedisStorage
```

### Directory Structure

- **[bot/handlers/](bot/handlers/)** - Command and message routers
  - `private/` - Private chat handlers
  - `groups/` - Group chat handlers
  - `errors_router.py` - Error logging handler (conditionally loaded)

- **[bot/filters/](bot/filters/)** - Custom filters (e.g., IsPrivateChat, IsAdmin, IsChatAdmin, HasMedia)

- **[bot/keyboards/](bot/keyboards/)** - Inline keyboard builders

- **[bot/middlewares/](bot/middlewares/)** - Global middlewares registered at dispatcher level
  - UserRegistrationMiddleware - Auto-registers users in DB
  - i18n middleware - Language detection and caching

- **[bot/models/](bot/models/)** - Tortoise ORM models (User, etc.)

- **[bot/services/](bot/services/)** - High-level business logic
  - `UserService` - User queries and operations
  - `BroadcastService` - Mass sending with rate limiting and batching (100 users at a time)

- **[bot/managers/](bot/managers/)** - Low-level managers for external services
  - `DatabaseManager` - Tortoise ORM initialization/closing
  - `RedisManager` - Redis connection and operations
  - `i18nManager` - Locale management

- **[bot/routes/](bot/routes/)** - FastAPI webhook endpoint

- **[bot/locales/](bot/locales/)** - Fluent `.ftl` translation files (ru, en)

- **[bot/utils/](bot/utils/)** - Helper utilities
  - `Template` - Unified interface for sending/editing messages with photos, media groups, documents
  - Other helpers as needed

## Configuration & Environment

The `.env` file controls everything (required before running):

- **COMPOSE_ENV** - `dev` or `prod` (determines which compose files are loaded)
- **BOT_TOKEN** - Telegram bot token from @BotFather
- **WEBHOOK_URL** - Public HTTPS URL where bot receives updates
- **POSTGRESQL** - Connection details (PG_HOST, PG_USER, PG_PASSWORD, PG_DATABASE)
- **REDIS** - Connection details (REDIS_HOST, REDIS_PASSWORD, REDIS_DATABASE)
- **LOGGING_ENABLED** - Send errors to Telegram if True
- **ADMIN_IDS** - List of admin user IDs (format: `[123,456]`)
- **DEFAULT_LANGUAGE** - Default language code (ru, en)

## Common Development Tasks

### Adding a New Handler

1. Create file: `bot/handlers/private/my_handler.py`
```python
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from filters import IsPrivateChat

router = Router()

@router.message(Command("mycommand"), IsPrivateChat())
async def cmd_mycommand(message: Message):
    await message.answer("Response!")
```

2. Register in `bot/handlers/private/__init__.py`:
```python
from .my_handler import router as my_router

routers = [..., my_router]
```

### Adding a Database Model

1. Create or modify model in `bot/models/` (e.g., `chat.py`)
```python
from tortoise import Model, fields

class Chat(Model):
    id = fields.BigIntField(primary_key=True)
    title = fields.CharField(max_length=255)

    class Meta:
        table = "chats"
```

2. Import in `bot/models/__init__.py`

3. Create and apply migration:
```bash
make aerich migrate
make aerich upgrade
```

### Using BroadcastService

```python
from services import BroadcastService
from utils import Template

template = Template(
    text="Hello everyone!",
    photo="https://example.com/image.jpg"
)

stats = await BroadcastService.broadcast_template(
    bot=bot,
    template=template,
    exclude_banned=True,
    delay=0.05  # Rate limiting
)
# stats = {"total": N, "success": N, "failed": N, "blocked": N}
```

### Using Template Utility

```python
from utils import Template

# Simple message
template = Template(text="Hello!")
await template.send(message)

# With photo
template = Template(text="Photo description", photo="photo.jpg")
await template.send(message)

# Media group
template = Template(text="Gallery", photos=["1.jpg", "2.jpg"])
await template.send(message)

# Edit message
template = Template(text="Updated!", buttons=keyboard)
await template.edit(callback_query)
```

## Database Migrations

Migrations are managed by **Aerich**. Tortoise ORM models are in `bot/models/`.

**After changing models:**
```bash
make aerich migrate      # Creates migration file
make aerich upgrade      # Applies to database
```

**Rollback:**
```bash
make aerich downgrade    # Undo last migration
make aerich history      # View all migrations
```

## Production Deployment

1. Change all passwords in `.env` to strong values
2. Set `WEBHOOK_URL` to your domain with SSL (https://)
3. Configure reverse proxy (nginx/caddy) to forward requests to port 5000
4. Enable logging: `LOGGING_ENABLED=True`
5. Run `make prod`
6. Setup database backups via cron:
   ```
   0 2 * * * cd /path/to/bot && make db-backup
   ```

### Nginx Reverse Proxy Example
```nginx
location /webhook {
    proxy_pass http://localhost:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### Caddy Reverse Proxy Example
```caddy
handle /webhook* {
    reverse_proxy localhost:5000 {
        header_up Host {host}
        header_up X-Real-IP {remote_host}
    }
}
```

## Testing & Debugging

```bash
make logs           # View all logs in real-time
make logs bot       # View only bot service logs
make shell bot      # Enter bot container shell
make ps             # Check container status
```

## Key Dependencies

- **aiogram** - Telegram Bot API wrapper
- **fastapi** - Web framework for webhook
- **tortoise-orm** - Async ORM for PostgreSQL
- **aerich** - Migration tool for Tortoise ORM
- **redis** - Python Redis client
- **aiogram-i18n** - i18n for aiogram
- **fluent-runtime** - Mozilla's translation format
- **loguru** - Structured logging
- **pydantic-settings** - Environment-based configuration
- **uvicorn** - ASGI server

## File Format Notes

- **Locales** use Mozilla Fluent (`.ftl` files) in `bot/locales/{lang}/`
- **Models** use Tortoise ORM with asyncpg backend
- **Configuration** uses Pydantic with `.env` file
- **FSM states** are stored in Redis via aiogram's RedisStorage
