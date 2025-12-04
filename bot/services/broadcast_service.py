"""Сервис для рассылки сообщений пользователям"""

import asyncio
import time
from typing import List
from collections import deque

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter, TelegramBadRequest
from loguru import logger

from models import BotUser
from utils import Template


class RateLimiter:
    def __init__(self, max_rate: int = 20):
        self.max_rate = max_rate
        self.timestamps = deque()
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        async with self.lock:
            now = time.time()
            
            while self.timestamps and now - self.timestamps[0] >= 1.0:
                self.timestamps.popleft()
            
            if len(self.timestamps) >= self.max_rate:
                sleep_time = 1.0 - (now - self.timestamps[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                    now = time.time()
                    while self.timestamps and now - self.timestamps[0] >= 1.0:
                        self.timestamps.popleft()
            
            self.timestamps.append(now)


class BroadcastService:
    @staticmethod
    async def _send_to_user(
        template_with_bot: Template,
        user_id: int,
        rate_limiter: RateLimiter,
        user_obj=None
    ) -> dict:
        await rate_limiter.acquire()
        
        try:
            await template_with_bot.send(user_id)
            return {'status': 'success', 'user_id': user_id}

        except TelegramForbiddenError:
            logger.debug(f"User {user_id} blocked the bot")
            if user_obj:
                user_obj.is_banned = True
                await user_obj.save()
            return {'status': 'blocked', 'user_id': user_id}

        except TelegramRetryAfter as e:
            logger.warning(f"Rate limit for user {user_id}, skipping")
            return {'status': 'failed', 'user_id': user_id}

        except TelegramBadRequest as e:
            logger.error(f"Failed to send to user {user_id}: {e}")
            return {'status': 'failed', 'user_id': user_id}

        except Exception as e:
            logger.error(f"Unexpected error sending to user {user_id}: {e}")
            return {'status': 'failed', 'user_id': user_id}

    @staticmethod
    async def broadcast_template(
        bot: Bot,
        template: Template,
        exclude_banned: bool = True,
        batch_size: int = 100,
        concurrent_limit: int = 30,
        max_rate: int = 20
    ) -> dict:
        query = BotUser.all()
        if exclude_banned:
            query = query.filter(is_banned=False)

        total = await query.count()
        logger.info(f"Starting broadcast to {total} users")

        success = failed = blocked = 0
        template_with_bot = template.with_bot(bot)
        semaphore = asyncio.Semaphore(concurrent_limit)
        rate_limiter = RateLimiter(max_rate=max_rate)

        async def send_with_limits(user):
            async with semaphore:
                return await BroadcastService._send_to_user(
                    template_with_bot, user.id, rate_limiter, user
                )

        last_id = 0
        while True:
            users = await query.filter(id__gt=last_id).order_by('id').limit(batch_size).all()
            if not users:
                break

            results = await asyncio.gather(
                *[send_with_limits(user) for user in users],
                return_exceptions=True
            )

            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Exception in broadcast: {result}")
                    failed += 1
                elif result['status'] == 'success':
                    success += 1
                elif result['status'] == 'blocked':
                    blocked += 1
                else:
                    failed += 1

            last_id = users[-1].id

        logger.info(
            f"Broadcast completed: {success}/{total} successful, "
            f"{blocked} blocked, {failed} failed"
        )

        return {
            "total": total,
            "success": success,
            "failed": failed,
            "blocked": blocked
        }

    @staticmethod
    async def broadcast_to_users(
        bot: Bot,
        user_ids: List[int],
        template: Template,
        concurrent_limit: int = 30,
        max_rate: int = 20
    ) -> dict:
        total = len(user_ids)
        logger.info(f"Starting broadcast to {total} specific users")

        template_with_bot = template.with_bot(bot)
        semaphore = asyncio.Semaphore(concurrent_limit)
        rate_limiter = RateLimiter(max_rate=max_rate)

        async def send_with_limits(user_id):
            async with semaphore:
                return await BroadcastService._send_to_user(
                    template_with_bot, user_id, rate_limiter
                )

        results = await asyncio.gather(
            *[send_with_limits(user_id) for user_id in user_ids],
            return_exceptions=True
        )

        success = failed = blocked = 0
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Exception in broadcast: {result}")
                failed += 1
            elif result['status'] == 'success':
                success += 1
            elif result['status'] == 'blocked':
                blocked += 1
            else:
                failed += 1

        logger.info(
            f"Broadcast completed: {success}/{total} successful, "
            f"{blocked} blocked, {failed} failed"
        )

        return {
            "total": total,
            "success": success,
            "failed": failed,
            "blocked": blocked
        }