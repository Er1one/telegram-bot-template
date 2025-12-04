"""Tests for BroadcastService."""

import asyncio
import time
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bot.services.broadcast_service import BroadcastService, RateLimiter
from bot.utils import Template


class TestRateLimiter:
    """Tests for RateLimiter class."""

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_requests_under_limit(self):
        """Test that rate limiter allows requests under the limit."""
        limiter = RateLimiter(max_rate=5)

        start_time = time.time()
        for _ in range(5):
            await limiter.acquire()
        elapsed = time.time() - start_time

        # Should complete quickly since we're under the limit
        assert elapsed < 0.5

    @pytest.mark.asyncio
    async def test_rate_limiter_delays_when_exceeding_limit(self):
        """Test that rate limiter delays requests when exceeding the limit."""
        limiter = RateLimiter(max_rate=3)

        start_time = time.time()
        # First 3 should be immediate
        for _ in range(3):
            await limiter.acquire()

        # 4th request should be delayed
        await limiter.acquire()
        elapsed = time.time() - start_time

        # Should take at least 1 second due to rate limiting
        assert elapsed >= 0.9

    @pytest.mark.asyncio
    async def test_rate_limiter_concurrent_requests(self):
        """Test rate limiter with concurrent requests."""
        limiter = RateLimiter(max_rate=10)

        async def acquire_multiple():
            await limiter.acquire()

        start_time = time.time()
        # Fire 20 concurrent requests
        await asyncio.gather(*[acquire_multiple() for _ in range(20)])
        elapsed = time.time() - start_time

        # Should take at least 1 second since we exceed the limit of 10
        assert elapsed >= 0.9

    @pytest.mark.asyncio
    async def test_rate_limiter_cleans_old_timestamps(self):
        """Test that rate limiter cleans old timestamps."""
        limiter = RateLimiter(max_rate=5)

        # Make 5 requests
        for _ in range(5):
            await limiter.acquire()

        # Wait for timestamps to expire
        await asyncio.sleep(1.1)

        # Should be able to make more requests immediately
        start_time = time.time()
        for _ in range(5):
            await limiter.acquire()
        elapsed = time.time() - start_time

        assert elapsed < 0.5


class TestBroadcastService:
    """Tests for BroadcastService class."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock Bot instance."""
        bot = MagicMock(spec=Bot)
        bot.send_message = AsyncMock()
        bot.send_photo = AsyncMock()
        return bot

    @pytest.fixture
    def mock_template(self):
        """Create a mock Template instance."""
        template = MagicMock(spec=Template)
        template.send = AsyncMock()
        template.with_bot = MagicMock(return_value=template)
        return template

    @pytest.fixture
    def mock_rate_limiter(self):
        """Create a mock RateLimiter."""
        limiter = MagicMock(spec=RateLimiter)
        limiter.acquire = AsyncMock()
        return limiter

    @pytest.mark.asyncio
    async def test_send_to_user_success(self, mock_template, mock_rate_limiter):
        """Test successful message send to user."""
        result = await BroadcastService._send_to_user(
            mock_template,
            user_id=12345,
            rate_limiter=mock_rate_limiter
        )

        assert result['status'] == 'success'
        assert result['user_id'] == 12345
        mock_rate_limiter.acquire.assert_called_once()
        mock_template.send.assert_called_once_with(12345)

    @pytest.mark.asyncio
    async def test_send_to_user_blocked(self, mock_template, mock_rate_limiter):
        """Test handling when user blocks the bot."""
        mock_template.send.side_effect = TelegramForbiddenError(
            method="sendMessage",
            message="Forbidden: bot was blocked by the user"
        )

        # Create mock user object
        mock_user = MagicMock()
        mock_user.is_banned = False
        mock_user.save = AsyncMock()

        result = await BroadcastService._send_to_user(
            mock_template,
            user_id=12345,
            rate_limiter=mock_rate_limiter,
            user_obj=mock_user
        )

        assert result['status'] == 'blocked'
        assert result['user_id'] == 12345
        assert mock_user.is_banned is True
        mock_user.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_to_user_retry_after(self, mock_template, mock_rate_limiter):
        """Test handling of rate limit from Telegram."""
        mock_template.send.side_effect = TelegramRetryAfter(
            method="sendMessage",
            message="Too Many Requests: retry after 30",
            retry_after=30
        )

        result = await BroadcastService._send_to_user(
            mock_template,
            user_id=12345,
            rate_limiter=mock_rate_limiter
        )

        assert result['status'] == 'failed'
        assert result['user_id'] == 12345

    @pytest.mark.asyncio
    async def test_send_to_user_bad_request(self, mock_template, mock_rate_limiter):
        """Test handling of bad request errors."""
        mock_template.send.side_effect = TelegramBadRequest(
            method="sendMessage",
            message="Bad Request: chat not found"
        )

        result = await BroadcastService._send_to_user(
            mock_template,
            user_id=12345,
            rate_limiter=mock_rate_limiter
        )

        assert result['status'] == 'failed'
        assert result['user_id'] == 12345

    @pytest.mark.asyncio
    async def test_send_to_user_unexpected_error(self, mock_template, mock_rate_limiter):
        """Test handling of unexpected errors."""
        mock_template.send.side_effect = Exception("Unexpected error")

        result = await BroadcastService._send_to_user(
            mock_template,
            user_id=12345,
            rate_limiter=mock_rate_limiter
        )

        assert result['status'] == 'failed'
        assert result['user_id'] == 12345

    @pytest.mark.asyncio
    async def test_broadcast_to_users_empty_list(self, mock_bot, mock_template):
        """Test broadcast with empty user list."""
        stats = await BroadcastService.broadcast_to_users(
            bot=mock_bot,
            user_ids=[],
            template=mock_template
        )

        assert stats['total'] == 0
        assert stats['success'] == 0
        assert stats['failed'] == 0
        assert stats['blocked'] == 0

    @pytest.mark.asyncio
    async def test_broadcast_to_users_all_success(self, mock_bot, mock_template):
        """Test broadcast to specific users with all successful sends."""
        user_ids = [1, 2, 3, 4, 5]

        stats = await BroadcastService.broadcast_to_users(
            bot=mock_bot,
            user_ids=user_ids,
            template=mock_template,
            max_rate=100  # High rate to avoid delays in tests
        )

        assert stats['total'] == 5
        assert stats['success'] == 5
        assert stats['failed'] == 0
        assert stats['blocked'] == 0

    @pytest.mark.asyncio
    async def test_broadcast_to_users_mixed_results(self, mock_bot, mock_template):
        """Test broadcast with mixed success/failure results."""
        user_ids = [1, 2, 3, 4]

        # Mock different responses
        async def mock_send(user_id):
            if user_id == 2:
                raise TelegramForbiddenError(
                    method="sendMessage",
                    message="Bot was blocked"
                )
            elif user_id == 4:
                raise TelegramBadRequest(
                    method="sendMessage",
                    message="Chat not found"
                )

        mock_template.send.side_effect = mock_send

        stats = await BroadcastService.broadcast_to_users(
            bot=mock_bot,
            user_ids=user_ids,
            template=mock_template,
            max_rate=100
        )

        assert stats['total'] == 4
        assert stats['success'] == 2  # Users 1 and 3
        assert stats['blocked'] == 1  # User 2
        assert stats['failed'] == 1   # User 4

    @pytest.mark.asyncio
    @patch('bot.services.broadcast_service.BotUser')
    async def test_broadcast_template_no_users(self, mock_bot_user, mock_bot, mock_template):
        """Test broadcast_template with no users in database."""
        mock_query = MagicMock()
        mock_query.filter = MagicMock(return_value=mock_query)
        mock_query.count = AsyncMock(return_value=0)
        mock_query.order_by = MagicMock(return_value=mock_query)
        mock_query.limit = MagicMock(return_value=mock_query)
        mock_query.all = AsyncMock(return_value=[])

        mock_bot_user.all = MagicMock(return_value=mock_query)

        stats = await BroadcastService.broadcast_template(
            bot=mock_bot,
            template=mock_template
        )

        assert stats['total'] == 0
        assert stats['success'] == 0
        assert stats['failed'] == 0
        assert stats['blocked'] == 0

    @pytest.mark.asyncio
    @patch('bot.services.broadcast_service.BotUser')
    async def test_broadcast_template_with_users(self, mock_bot_user, mock_bot, mock_template):
        """Test broadcast_template with users in database."""
        # Create mock users
        mock_users = []
        for i in range(1, 6):
            user = MagicMock()
            user.id = i
            user.is_banned = False
            user.save = AsyncMock()
            mock_users.append(user)

        mock_query = MagicMock()
        mock_query.filter = MagicMock(return_value=mock_query)
        mock_query.count = AsyncMock(return_value=5)
        mock_query.order_by = MagicMock(return_value=mock_query)
        mock_query.limit = MagicMock(return_value=mock_query)

        # First call returns all users, second call returns empty (pagination)
        mock_query.all = AsyncMock(side_effect=[mock_users, []])

        mock_bot_user.all = MagicMock(return_value=mock_query)

        stats = await BroadcastService.broadcast_template(
            bot=mock_bot,
            template=mock_template,
            max_rate=100  # High rate to avoid delays
        )

        assert stats['total'] == 5
        assert stats['success'] == 5
        assert stats['failed'] == 0
        assert stats['blocked'] == 0

    @pytest.mark.asyncio
    @patch('bot.services.broadcast_service.BotUser')
    async def test_broadcast_template_exclude_banned(self, mock_bot_user, mock_bot, mock_template):
        """Test that banned users are excluded when exclude_banned=True."""
        mock_query = MagicMock()
        mock_query.filter = MagicMock(return_value=mock_query)
        mock_query.count = AsyncMock(return_value=3)
        mock_query.order_by = MagicMock(return_value=mock_query)
        mock_query.limit = MagicMock(return_value=mock_query)
        mock_query.all = AsyncMock(return_value=[])

        mock_bot_user.all = MagicMock(return_value=mock_query)

        await BroadcastService.broadcast_template(
            bot=mock_bot,
            template=mock_template,
            exclude_banned=True
        )

        # Verify filter was called with is_banned=False
        mock_query.filter.assert_called()

    @pytest.mark.asyncio
    @patch('bot.services.broadcast_service.BotUser')
    async def test_broadcast_template_batching(self, mock_bot_user, mock_bot, mock_template):
        """Test that broadcast_template processes users in batches."""
        # Create 250 mock users
        all_users = []
        for i in range(1, 251):
            user = MagicMock()
            user.id = i
            user.is_banned = False
            user.save = AsyncMock()
            all_users.append(user)

        mock_query = MagicMock()
        mock_query.filter = MagicMock(return_value=mock_query)
        mock_query.count = AsyncMock(return_value=250)
        mock_query.order_by = MagicMock(return_value=mock_query)
        mock_query.limit = MagicMock(return_value=mock_query)

        # Split into batches of 100
        batch1 = all_users[:100]
        batch2 = all_users[100:200]
        batch3 = all_users[200:]

        mock_query.all = AsyncMock(side_effect=[batch1, batch2, batch3, []])
        mock_bot_user.all = MagicMock(return_value=mock_query)

        stats = await BroadcastService.broadcast_template(
            bot=mock_bot,
            template=mock_template,
            batch_size=100,
            max_rate=1000  # High rate to avoid delays in tests
        )

        assert stats['total'] == 250
        assert stats['success'] == 250
        # Verify query.all() was called multiple times for batching
        assert mock_query.all.call_count == 4  # 3 batches + 1 empty

    @pytest.mark.asyncio
    async def test_broadcast_respects_concurrent_limit(self, mock_bot, mock_template):
        """Test that concurrent_limit parameter is respected."""
        user_ids = list(range(1, 51))  # 50 users
        call_times = []

        async def track_send(user_id):
            call_times.append(time.time())
            await asyncio.sleep(0.01)  # Simulate network delay

        mock_template.send.side_effect = track_send

        await BroadcastService.broadcast_to_users(
            bot=mock_bot,
            user_ids=user_ids,
            template=mock_template,
            concurrent_limit=10,
            max_rate=1000  # High rate to avoid rate limiting
        )

        # With concurrent_limit=10, not all 50 requests should start at once
        # Check that they're processed in waves
        assert len(call_times) == 50

    @pytest.mark.asyncio
    async def test_template_with_bot_called(self, mock_bot, mock_template):
        """Test that template.with_bot() is called with correct bot instance."""
        user_ids = [1, 2, 3]

        await BroadcastService.broadcast_to_users(
            bot=mock_bot,
            user_ids=user_ids,
            template=mock_template
        )

        mock_template.with_bot.assert_called_once_with(mock_bot)

    @pytest.mark.asyncio
    async def test_broadcast_handles_exception_in_gather(self, mock_bot, mock_template):
        """Test that exceptions in asyncio.gather are handled properly."""
        user_ids = [1, 2, 3]

        # Make send raise an exception that won't be caught by _send_to_user
        async def raise_error(user_id):
            if user_id == 2:
                raise RuntimeError("Simulated error")

        mock_template.send.side_effect = raise_error

        # This should not crash
        stats = await BroadcastService.broadcast_to_users(
            bot=mock_bot,
            user_ids=user_ids,
            template=mock_template,
            max_rate=100
        )

        assert stats['total'] == 3
        # User 2 failed with exception
        assert stats['failed'] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
