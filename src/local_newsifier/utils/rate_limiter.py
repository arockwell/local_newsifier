"""Rate limiting utilities for external API calls.

This module provides a token bucket-based rate limiter that uses Redis
for distributed state management. It supports per-service rate limits
with configurable periods and automatic retry with exponential backoff.
"""

import asyncio
import functools
import logging
import time
from typing import Any, Callable, Dict, Optional, TypeVar

import redis
from pydantic import BaseModel

from local_newsifier.config.settings import settings

logger = logging.getLogger(__name__)

# Type variable for generic decorator
F = TypeVar("F", bound=Callable[..., Any])


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""

    def __init__(self, service: str, retry_after: float):
        """Initialize RateLimitExceeded exception.

        Args:
            service: Name of the service that exceeded rate limi
            retry_after: Number of seconds to wait before retrying
        """
        self.service = service
        self.retry_after = retry_after
        super().__init__(
            f"Rate limit exceeded for service '{service}'. "
            f"Retry after {retry_after:.1f} seconds."
        )


class RateLimitConfig(BaseModel):
    """Configuration for a rate limiter."""

    service: str
    max_calls: int
    period: int  # seconds
    enable_backoff: bool = True
    max_retries: int = 3
    initial_backoff: float = 1.0
    backoff_multiplier: float = 2.0


class RateLimiter:
    """Token bucket rate limiter using Redis for distributed state."""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """Initialize rate limiter with Redis client."""
        self._redis = redis_client or self._create_redis_client()
        self._key_prefix = "rate_limit"

    def _create_redis_client(self) -> redis.Redis:
        """Create Redis client from settings."""
        # Parse Redis URL from Celery broker URL
        redis_url = settings.CELERY_BROKER_URL
        return redis.from_url(redis_url, decode_responses=True)

    def _get_key(self, service: str) -> str:
        """Get Redis key for service rate limit."""
        return f"{self._key_prefix}:{service}"

    def _get_bucket_state(self, service: str, max_calls: int, period: int) -> tuple[int, float]:
        """Get current bucket state from Redis.

        Returns:
            tuple: (available_tokens, last_refill_time)
        """
        key = self._get_key(service)
        pipe = self._redis.pipeline()

        # Get current values
        pipe.hget(key, "tokens")
        pipe.hget(key, "last_refill")
        pipe.ttl(key)

        results = pipe.execute()
        tokens_str, last_refill_str, ttl = results

        current_time = time.time()

        # Initialize if not exists
        if tokens_str is None:
            pipe = self._redis.pipeline()
            pipe.hset(key, "tokens", max_calls)
            pipe.hset(key, "last_refill", current_time)
            pipe.expire(key, period * 2)  # Expire after 2 periods of inactivity
            pipe.execute()
            return max_calls, current_time

        tokens = int(tokens_str)
        last_refill = float(last_refill_str)

        # Calculate tokens to add based on time elapsed
        time_elapsed = current_time - last_refill
        tokens_to_add = int(time_elapsed / period * max_calls)

        if tokens_to_add > 0:
            # Refill tokens
            new_tokens = min(tokens + tokens_to_add, max_calls)
            pipe = self._redis.pipeline()
            pipe.hset(key, "tokens", new_tokens)
            pipe.hset(key, "last_refill", current_time)
            pipe.expire(key, period * 2)
            pipe.execute()
            return new_tokens, current_time

        return tokens, last_refill

    def check_limit(self, service: str, max_calls: int, period: int) -> bool:
        """Check if request is within rate limit.

        Returns:
            bool: True if request is allowed, False otherwise
        """
        key = self._get_key(service)

        # Use Redis transaction for atomic check and decremen
        with self._redis.pipeline() as pipe:
            while True:
                try:
                    # Watch the key for changes
                    pipe.watch(key)

                    # Get current state
                    tokens, _ = self._get_bucket_state(service, max_calls, period)

                    if tokens <= 0:
                        pipe.unwatch()
                        return False

                    # Start transaction
                    pipe.multi()
                    pipe.hincrby(key, "tokens", -1)
                    pipe.expire(key, period * 2)
                    pipe.execute()

                    logger.debug(
                        f"Rate limit check passed for {service}. " f"Tokens remaining: {tokens - 1}"
                    )
                    return True

                except redis.WatchError:
                    # Key was modified, retry
                    continue

    def get_retry_after(self, service: str, period: int) -> float:
        """Calculate how long to wait before retry."""
        key = self._get_key(service)
        last_refill_str = self._redis.hget(key, "last_refill")

        if last_refill_str is None:
            return 0.0

        last_refill = float(last_refill_str)
        current_time = time.time()
        time_until_next_token = period - (current_time - last_refill) % period

        return max(0.0, time_until_next_token)

    def get_usage_stats(self, service: str, max_calls: int, period: int) -> Dict[str, Any]:
        """Get current usage statistics for a service."""
        tokens, last_refill = self._get_bucket_state(service, max_calls, period)

        return {
            "service": service,
            "available_tokens": tokens,
            "max_tokens": max_calls,
            "usage_percentage": (max_calls - tokens) / max_calls * 100,
            "period_seconds": period,
            "last_refill": last_refill,
            "time_until_refill": self.get_retry_after(service, period),
        }


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def rate_limit(
    service: str,
    max_calls: int,
    period: int,
    enable_backoff: bool = True,
    max_retries: int = 3,
    initial_backoff: float = 1.0,
    backoff_multiplier: float = 2.0,
) -> Callable[[F], F]:
    """Decorator to apply rate limiting to a function.

    Args:
        service: Name of the service being rate limited
        max_calls: Maximum number of calls allowed
        period: Time period in seconds
        enable_backoff: Whether to automatically retry with backoff
        max_retries: Maximum number of retry attempts
        initial_backoff: Initial backoff time in seconds
        backoff_multiplier: Multiplier for exponential backoff

    Example:
        @rate_limit(service='apify', max_calls=100, period=3600)
        async def call_apify_api():
            # API call here
            pass
    """
    config = RateLimitConfig(
        service=service,
        max_calls=max_calls,
        period=period,
        enable_backoff=enable_backoff,
        max_retries=max_retries,
        initial_backoff=initial_backoff,
        backoff_multiplier=backoff_multiplier,
    )

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            limiter = get_rate_limiter()
            attempt = 0
            backoff = config.initial_backoff

            while attempt <= config.max_retries:
                if limiter.check_limit(config.service, config.max_calls, config.period):
                    try:
                        return await func(*args, **kwargs)
                    except Exception:
                        # Don't retry on non-rate-limit errors
                        raise

                # Rate limit exceeded
                retry_after = limiter.get_retry_after(config.service, config.period)

                if not config.enable_backoff or attempt >= config.max_retries:
                    raise RateLimitExceeded(config.service, retry_after)

                # Log retry attemp
                logger.warning(
                    f"Rate limit exceeded for {config.service}. "
                    f"Retrying in {backoff:.1f}s (attempt {attempt + 1}/{config.max_retries})"
                )

                # Wait with backoff
                await asyncio.sleep(backoff)
                backoff *= config.backoff_multiplier
                attempt += 1

            # Final check after all retries
            retry_after = limiter.get_retry_after(config.service, config.period)
            raise RateLimitExceeded(config.service, retry_after)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            limiter = get_rate_limiter()
            attempt = 0
            backoff = config.initial_backoff

            while attempt <= config.max_retries:
                if limiter.check_limit(config.service, config.max_calls, config.period):
                    try:
                        return func(*args, **kwargs)
                    except Exception:
                        # Don't retry on non-rate-limit errors
                        raise

                # Rate limit exceeded
                retry_after = limiter.get_retry_after(config.service, config.period)

                if not config.enable_backoff or attempt >= config.max_retries:
                    raise RateLimitExceeded(config.service, retry_after)

                # Log retry attemp
                logger.warning(
                    f"Rate limit exceeded for {config.service}. "
                    f"Retrying in {backoff:.1f}s (attempt {attempt + 1}/{config.max_retries})"
                )

                # Wait with backoff
                time.sleep(backoff)
                backoff *= config.backoff_multiplier
                attempt += 1

            # Final check after all retries
            retry_after = limiter.get_retry_after(config.service, config.period)
            raise RateLimitExceeded(config.service, retry_after)

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
