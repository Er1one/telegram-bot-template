FROM python:3.13.3-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --upgrade pip uv

# Рабочая директория
WORKDIR /app

# Копируем файлы зависимостей
COPY pyproject.toml uv.lock* ./

# Устанавливаем зависимости
RUN uv export --format requirements-txt --no-dev > requirements.txt \
    && pip install --no-cache-dir -r requirements.txt \
    && rm requirements.txt

# Копируем код приложения
COPY bot/ ./bot/

# Создаем непривилегированного пользователя
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PORT=5000

# Открываем порт
EXPOSE ${PORT}

# Команда запуска (изменена)
CMD ["python", "bot/main.py"]