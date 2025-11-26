.PHONY: help dev prod build up down logs restart clean shell aerich ps rebuild db-backup clean-all

# Загружаем переменные из .env, включая COMPOSE_ENV
include .env
export

# Определяем файлы compose на основе COMPOSE_ENV из .env
ifeq ($(COMPOSE_ENV),prod)
    COMPOSE = docker compose -f docker-compose.yml -f docker-compose.prod.yml
    ENV_NAME = PROD
else
    COMPOSE = docker compose -f docker-compose.yml -f docker-compose.dev.yml
    ENV_NAME = DEV
endif

help:
	@echo "═══════════════════════════════════════════════════════"
	@echo "  Docker Compose Manager"
	@echo "═══════════════════════════════════════════════════════"
	@echo ""
	@echo "Текущее окружение: $(ENV_NAME) (из .env: COMPOSE_ENV=$(COMPOSE_ENV))"
	@echo ""
	@echo "Быстрый старт:"
	@echo "  make dev                    - Переключить на DEV и запустить"
	@echo "  make prod                   - Переключить на PROD и запустить"
	@echo ""
	@echo "Управление контейнерами:"
	@echo "  make build                  - Собрать образы"
	@echo "  make up                     - Запустить контейнеры"
	@echo "  make down                   - Остановить контейнеры"
	@echo "  make restart [SERVICE]      - Перезапустить контейнеры"
	@echo "  make ps                     - Показать статус контейнеров"
	@echo ""
	@echo "Логи и отладка:"
	@echo "  make logs [SERVICE]         - Показать логи (все или конкретного сервиса)"
	@echo "  make shell SERVICE          - Войти в контейнер"
	@echo ""
	@echo "База данных (Aerich):"
	@echo "  make aerich-init            - Инициализировать Aerich"
	@echo "  make aerich ARGS            - Выполнить команду Aerich"
	@echo ""
	@echo "Примеры:"
	@echo "  make aerich migrate         - Создать миграцию"
	@echo "  make aerich upgrade         - Применить миграции"
	@echo "  make logs bot               - Логи бота"
	@echo "  make shell database         - Войти в PostgreSQL"
	@echo ""
	@echo "Очистка:"
	@echo "  make clean                  - Удалить контейнеры и volumes"
	@echo "  make clean-all              - Удалить ВСЁ (dev + prod)"
	@echo ""
	@echo "Дополнительно:"
	@echo "  make rebuild                - Пересборка и перезапуск"
	@echo "  make db-backup              - Создать бэкап БД"
	@echo "═══════════════════════════════════════════════════════"

# Переключение окружений
dev:
	@echo "🔄 Переключение на DEV окружение..."
	@sed -i.bak 's/^COMPOSE_ENV=.*/COMPOSE_ENV=dev/' .env && rm -f .env.bak
	@echo "✅ Переключено на DEV!"
	@$(MAKE) --no-print-directory _up

prod:
	@echo "🔄 Переключение на PROD окружение..."
	@sed -i.bak 's/^COMPOSE_ENV=.*/COMPOSE_ENV=prod/' .env && rm -f .env.bak
	@echo "✅ Переключено на PROD!"
	@$(MAKE) --no-print-directory _up

# Внутренняя команда для запуска (используется после переключения окружения)
_up:
	@echo "🚀 Запуск контейнеров ($(ENV_NAME))..."
	@$(MAKE) --no-print-directory up

# Универсальные команды
build:
	@echo "🔨 Сборка образов ($(ENV_NAME))..."
	$(COMPOSE) build

up:
	@echo "▶️  Запуск контейнеров ($(ENV_NAME))..."
	$(COMPOSE) up -d
	@echo "✅ Контейнеры запущены!"
	@$(MAKE) --no-print-directory ps

down:
	@echo "⏹️  Остановка контейнеров ($(ENV_NAME))..."
	$(COMPOSE) down
	@echo "✅ Контейнеры остановлены!"

ps:
	@echo "📊 Статус контейнеров ($(ENV_NAME)):"
	@$(COMPOSE) ps

logs:
	@echo "📜 Логи ($(ENV_NAME)):"
	$(COMPOSE) logs -f $(filter-out $@,$(MAKECMDGOALS))

restart:
	@echo "🔄 Перезапуск контейнеров ($(ENV_NAME))..."
	$(COMPOSE) restart $(filter-out $@,$(MAKECMDGOALS))
	@echo "✅ Контейнеры перезапущены!"

clean:
	@echo "🗑️  Очистка $(ENV_NAME) окружения..."
	$(COMPOSE) down -v
	@echo "✅ Очистка завершена!"

clean-all:
	@echo "🗑️  Полная очистка (dev + prod)..."
	@docker compose -f docker-compose.yml -f docker-compose.dev.yml down -v 2>/dev/null || true
	@docker compose -f docker-compose.yml -f docker-compose.prod.yml down -v 2>/dev/null || true
	@echo "✅ Всё удалено!"

shell:
	@echo "🐚 Вход в контейнер $(filter-out $@,$(MAKECMDGOALS)) ($(ENV_NAME))..."
	$(COMPOSE) exec $(filter-out $@,$(MAKECMDGOALS)) bash

# Команды для Aerich
aerich-init:
	@echo "🔧 Инициализация Aerich ($(ENV_NAME))..."
	$(COMPOSE) exec bot aerich init -t bot.core.loader.TORTOISE_CONFIG
	@echo "✅ Aerich инициализирован!"

aerich:
	@echo "🔧 Выполнение команды Aerich ($(ENV_NAME))..."
	$(COMPOSE) exec bot aerich $(filter-out $@,$(MAKECMDGOALS))

# Дополнительные полезные команды
rebuild:
	@echo "🔄 Пересборка и перезапуск ($(ENV_NAME))..."
	@$(MAKE) --no-print-directory down
	@$(MAKE) --no-print-directory build
	@$(MAKE) --no-print-directory up

db-backup:
	@echo "💾 Создание бэкапа БД ($(ENV_NAME))..."
	@mkdir -p ./backups
	$(COMPOSE) exec -T database pg_dump -U $(PG_USER) $(PG_DATABASE) > ./backups/backup_$(COMPOSE_ENV)_$$(date +%Y%m%d_%H%M%S).sql
	@echo "✅ Бэкап создан в ./backups/"

# Позволяет передавать аргументы без ошибок
%:
	@: