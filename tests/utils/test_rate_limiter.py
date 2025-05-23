"""Tests for rate limiting functionality."""

import time
from unittest.mock import MagicMock, patch

import pytest
import redis

from local_newsifier.utils.rate_limiter import (RateLimiter, RateLimitExceeded, get_rate_limiter,
                                                rate_limit)


class TestRateLimiter:
    """Test the RateLimiter class."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        mock = MagicMock(spec=redis.Redis)
        mock.pipeline.return_value = MagicMock()
        return mock

    @pytest.fixture
    def rate_limiter(self, mock_redis):
        """Create a RateLimiter instance with mock Redis."""
        limiter = RateLimiter(redis_client=mock_redis)
        return limiter

    def test_get_key(self, rate_limiter):
        """Test Redis key generation."""
        key = rate_limiter._get_key("test_service")
        assert key == "rate_limit:test_service"

    def test_get_bucket_state_initial(self, rate_limiter, mock_redis):
        """Test getting bucket state when it doesn't exist."""
        # Mock pipeline execution to return no existing data
        pipe_mock = MagicMock()
        pipe_mock.execute.return_value = [None, None, -1]
        mock_redis.pipeline.return_value = pipe_mock

        tokens, last_refill = rate_limiter._get_bucket_state("test", 100, 60)

        assert tokens == 100  # Should return max tokens
        assert isinstance(last_refill, float)  # Should be current time

    def test_get_bucket_state_existing(self, rate_limiter, mock_redis):
        """Test getting bucket state when it exists."""
        # Mock pipeline execution to return existing data
        current_time = time.time()

        # Use only 0.5 seconds elapsed - this gives 0 tokens to add
        # since int(0.5/60 * 100) = int(0.833...) = 0
        pipe_mock = MagicMock()
        pipe_mock.execute.return_value = ["50", str(current_time - 0.5), 120]
        mock_redis.pipeline.return_value = pipe_mock

        tokens, last_refill = rate_limiter._get_bucket_state("test", 100, 60)

        # Should not refill (tokens_to_add = 0)
        assert tokens == 50
        # Last refill should be the same since no refill happened
        assert abs(last_refill - (current_time - 0.5)) < 0.01

    def test_check_limit_allowed(self, rate_limiter, mock_redis):
        """Test check_limit when request is allowed."""
        # Mock the get_bucket_state to return available tokens
        with patch.object(rate_limiter, "_get_bucket_state", return_value=(10, time.time())):
            # Mock pipeline for the transaction
            pipe_mock = MagicMock()
            pipe_mock.watch = MagicMock()
            pipe_mock.unwatch = MagicMock()
            pipe_mock.multi = MagicMock()
            pipe_mock.hincrby = MagicMock()
            pipe_mock.expire = MagicMock()
            pipe_mock.execute = MagicMock()

            # Use context manager to simulate pipeline behavior
            pipe_mock.__enter__ = MagicMock(return_value=pipe_mock)
            pipe_mock.__exit__ = MagicMock(return_value=None)

            mock_redis.pipeline.return_value = pipe_mock

            result = rate_limiter.check_limit("test", 100, 60)

            assert result is True
            pipe_mock.hincrby.assert_called_once_with("rate_limit:test", "tokens", -1)

    def test_check_limit_denied(self, rate_limiter, mock_redis):
        """Test check_limit when request is denied."""
        # Mock the get_bucket_state to return no tokens
        with patch.object(rate_limiter, "_get_bucket_state", return_value=(0, time.time())):
            result = rate_limiter.check_limit("test", 100, 60)
            assert result is False

    def test_get_retry_after(self, rate_limiter, mock_redis):
        """Test calculating retry after time."""
        current_time = time.time()
        mock_redis.hget.return_value = str(current_time - 30)

        retry_after = rate_limiter.get_retry_after("test", 60)

        # Should be approximately 30 seconds (60 - 30)
        assert 29 < retry_after < 31

    def test_get_usage_stats(self, rate_limiter):
        """Test getting usage statistics."""
        with patch.object(rate_limiter, "_get_bucket_state", return_value=(75, time.time())):
            with patch.object(rate_limiter, "get_retry_after", return_value=15.0):
                stats = rate_limiter.get_usage_stats("test", 100, 60)

                assert stats["service"] == "test"
                assert stats["available_tokens"] == 75
                assert stats["max_tokens"] == 100
                assert stats["usage_percentage"] == 25.0
                assert stats["period_seconds"] == 60
                assert stats["time_until_refill"] == 15.0


class TestRateLimitDecorator:
    """Test the rate_limit decorator."""

    @pytest.fixture
    def mock_limiter(self):
        """Create a mock rate limiter."""
        with patch("local_newsifier.utils.rate_limiter.get_rate_limiter") as mock:
            limiter = MagicMock()
            mock.return_value = limiter
            yield limiter

    def test_sync_function_allowed(self, mock_limiter):
        """Test rate limiting a sync function when allowed."""
        mock_limiter.check_limit.return_value = True

        @rate_limit(service="test", max_calls=10, period=60)
        def test_func():
            return "success"

        result = test_func()
        assert result == "success"
        mock_limiter.check_limit.assert_called_once_with("test", 10, 60)

    def test_sync_function_denied_no_backoff(self, mock_limiter):
        """Test rate limiting a sync function when denied without backoff."""
        mock_limiter.check_limit.return_value = False
        mock_limiter.get_retry_after.return_value = 5.0

        @rate_limit(service="test", max_calls=10, period=60, enable_backoff=False)
        def test_func():
            return "success"

        with pytest.raises(RateLimitExceeded) as exc_info:
            test_func()

        assert exc_info.value.service == "test"
        assert exc_info.value.retry_after == 5.0

    def test_sync_function_with_backoff(self, mock_limiter):
        """Test rate limiting with backoff enabled."""
        # First call fails, second succeeds
        mock_limiter.check_limit.side_effect = [False, True]
        mock_limiter.get_retry_after.return_value = 0.1

        @rate_limit(
            service="test", max_calls=10, period=60, enable_backoff=True, initial_backoff=0.1
        )
        def test_func():
            return "success"

        start_time = time.time()
        result = test_func()
        elapsed = time.time() - start_time

        assert result == "success"
        assert elapsed >= 0.1  # Should have waited for backoff
        assert mock_limiter.check_limit.call_count == 2

    @pytest.mark.asyncio
    async def test_async_function_allowed(self, mock_limiter):
        """Test rate limiting an async function when allowed."""
        mock_limiter.check_limit.return_value = True

        @rate_limit(service="test", max_calls=10, period=60)
        async def test_func():
            return "success"

        result = await test_func()
        assert result == "success"
        mock_limiter.check_limit.assert_called_once_with("test", 10, 60)

    @pytest.mark.asyncio
    async def test_async_function_denied(self, mock_limiter):
        """Test rate limiting an async function when denied."""
        mock_limiter.check_limit.return_value = False
        mock_limiter.get_retry_after.return_value = 5.0

        @rate_limit(service="test", max_calls=10, period=60, enable_backoff=False)
        async def test_func():
            return "success"

        with pytest.raises(RateLimitExceeded) as exc_info:
            await test_func()

        assert exc_info.value.service == "test"
        assert exc_info.value.retry_after == 5.0

    @pytest.mark.asyncio
    async def test_async_function_with_backoff(self, mock_limiter):
        """Test async rate limiting with backoff."""
        # First call fails, second succeeds
        mock_limiter.check_limit.side_effect = [False, True]
        mock_limiter.get_retry_after.return_value = 0.1

        @rate_limit(
            service="test", max_calls=10, period=60, enable_backoff=True, initial_backoff=0.1
        )
        async def test_func():
            return "success"

        start_time = time.time()
        result = await test_func()
        elapsed = time.time() - start_time

        assert result == "success"
        assert elapsed >= 0.1  # Should have waited for backoff
        assert mock_limiter.check_limit.call_count == 2

    def test_exponential_backoff(self, mock_limiter):
        """Test exponential backoff behavior."""
        # All calls fail to test max retries
        mock_limiter.check_limit.return_value = False
        mock_limiter.get_retry_after.return_value = 0.01

        @rate_limit(
            service="test",
            max_calls=10,
            period=60,
            enable_backoff=True,
            max_retries=2,
            initial_backoff=0.01,
            backoff_multiplier=2.0,
        )
        def test_func():
            return "success"

        with pytest.raises(RateLimitExceeded):
            test_func()

        # Should have tried: initial, retry 1, retry 2 = 3 times
        assert mock_limiter.check_limit.call_count == 3


class TestGetRateLimiter:
    """Test the get_rate_limiter function."""

    def test_singleton_pattern(self):
        """Test that get_rate_limiter returns the same instance."""
        # Reset the global instance
        import local_newsifier.utils.rate_limiter

        local_newsifier.utils.rate_limiter._rate_limiter = None

        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()

        assert limiter1 is limiter2


class TestRateLimitExceeded:
    """Test the RateLimitExceeded exception."""

    def test_exception_message(self):
        """Test the exception message format."""
        exc = RateLimitExceeded("apify", 30.5)

        assert exc.service == "apify"
        assert exc.retry_after == 30.5
        assert "Rate limit exceeded for service 'apify'" in str(exc)
        assert "Retry after 30.5 seconds" in str(exc)
