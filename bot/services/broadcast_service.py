"""Сервис для рассылки сообщений пользователям"""

import asyncio
from typing import List

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter, TelegramBadRequest
from loguru import logger

from models import BotUser
from utils import Template


class BroadcastService:
    """Сервис массовой рассылки сообщений"""

    @staticmethod
    async def broadcast_template(
        bot: Bot,
        template: Template,
        exclude_banned: bool = True,
        delay: float = 0.05,
        batch_size: int = 100
    ) -> dict:
        """
        Рассылает шаблон сообщения всем пользователям с батчингом.

        Args:
            bot: Экземпляр бота
            template: Шаблон сообщения для рассылки
            exclude_banned: Исключить заблокированных пользователей
            delay: Задержка между отправками (секунды)
            batch_size: Размер батча для загрузки пользователей из БД

        Returns:
            Статистика рассылки
        """
        query = BotUser.all()
        if exclude_banned:
            query = query.filter(is_banned=False)

        # Получаем только ID для экономии памяти
        total = await query.count()
        logger.info(f"Starting broadcast to {total} users")

        success = 0
        failed = 0
        blocked = 0
        template_with_bot = template.with_bot(bot)

        # Батчинг для экономии памяти на больших базах
        offset = 0
        while offset < total:
            users = await query.offset(offset).limit(batch_size).all()
            if not users:
                break

            for user in users:
                try:
                    await template_with_bot.send(user.id)
                    success += 1

                    if delay > 0:
                        await asyncio.sleep(delay)

                except TelegramForbiddenError:
                    blocked += 1
                    logger.debug(f"User {user.id} blocked the bot")
                    user.is_banned = True
                    await user.save()

                except TelegramRetryAfter as e:
                    logger.warning(f"Rate limit hit, waiting {e.retry_after} seconds")
                    await asyncio.sleep(e.retry_after)
                    try:
                        await template_with_bot.send(user.id)
                        success += 1
                    except Exception:
                        failed += 1

                except TelegramBadRequest as e:
                    failed += 1
                    logger.error(f"Failed to send to user {user.id}: {e}")

                except Exception as e:
                    failed += 1
                    logger.error(f"Unexpected error sending to user {user.id}: {e}")

            offset += batch_size

        stats = {
            "total": total,
            "success": success,
            "failed": failed,
            "blocked": blocked
        }

        logger.info(
            f"Broadcast completed: {success}/{total} successful, "
            f"{blocked} blocked, {failed} failed"
        )

        return stats

    @staticmethod
    async def broadcast_to_users(
        bot: Bot,
        user_ids: List[int],
        template: Template,
        delay: float = 0.05
    ) -> dict:
        """
        Рассылает сообщение конкретным пользователям.

        Args:
            bot: Экземпляр бота
            user_ids: Список ID пользователей
            template: Шаблон сообщения
            delay: Задержка между отправками (секунды)

        Returns:
            Статистика рассылки
        """
        total = len(user_ids)
        logger.info(f"Starting broadcast to {total} specific users")

        success = 0
        failed = 0

        template_with_bot = template.with_bot(bot)

        for user_id in user_ids:
            try:
                await template_with_bot.send(user_id)
                success += 1

                if delay > 0:
                    await asyncio.sleep(delay)

            except TelegramRetryAfter as e:
                logger.warning(f"Rate limit hit, waiting {e.retry_after} seconds")
                await asyncio.sleep(e.retry_after)

                try:
                    await template_with_bot.send(user_id)
                    success += 1
                except Exception:
                    failed += 1

            except Exception as e:
                failed += 1
                logger.error(f"Failed to send to user {user_id}: {e}")

        stats = {
            "total": total,
            "success": success,
            "failed": failed
        }

        logger.info(f"Broadcast completed: {success}/{total} successful, {failed} failed")

        return stats
