# Rate Limiting Guide

## Overview

Local Newsifier implements rate limiting for all external API calls to prevent hitting service limits, manage costs, and ensure reliable operation. The rate limiting system uses a token bucket algorithm with Redis for distributed state management.

## Features

- **Per-service rate limits**: Different limits for each external service (Apify, RSS, web scraping, OpenAI)
- **Token bucket algorithm**: Smooth rate limiting with burst capacity
- **Automatic retry with backoff**: Configurable exponential backoff for rate-limited requests
- **Redis-based state**: Distributed rate limiting across multiple workers
- **CLI monitoring**: Commands to check rate limit status and usage
- **Environment configuration**: All limits configurable via environment variables

## Configuration

Rate limits are configured through environment variables or in your `.env` file:

```bash
# Apify API (100 calls per hour)
RATE_LIMIT_APIFY_CALLS=100
RATE_LIMIT_APIFY_PERIOD=3600

# RSS feeds (10 calls per minute)
RATE_LIMIT_RSS_CALLS=10
RATE_LIMIT_RSS_PERIOD=60

# Web scraping (30 calls per minute)
RATE_LIMIT_WEB_CALLS=30
RATE_LIMIT_WEB_PERIOD=60

# OpenAI API (60 calls per minute)
RATE_LIMIT_OPENAI_CALLS=60
RATE_LIMIT_OPENAI_PERIOD=60

# Backoff configuration
RATE_LIMIT_ENABLE_BACKOFF=true
RATE_LIMIT_MAX_RETRIES=3
RATE_LIMIT_INITIAL_BACKOFF=1.0
RATE_LIMIT_BACKOFF_MULTIPLIER=2.0
```

## Usage

### Automatic Rate Limiting

Rate limiting is automatically applied to all external API calls:

- **Apify API**: All methods in `ApifyService` (run_actor, create_schedule, etc.)
- **RSS feeds**: The `parse_feed` method in `RSSParser`
- **Web scraping**: The `_fetch_url` method in `WebScraperTool`

### Manual Rate Limiting

To add rate limiting to a new service or function:

```python
from local_newsifier.utils.rate_limiter import rate_limit

@rate_limit(
    service='my_service',
    max_calls=100,
    period=3600,  # seconds
    enable_backoff=True,
    max_retries=3
)
def call_external_api():
    # Your API call here
    pass
```

For async functions:

```python
@rate_limit(service='my_service', max_calls=100, period=3600)
async def async_api_call():
    # Your async API call here
    pass
```

### CLI Commands

Monitor and manage rate limits using the CLI:

```bash
# Show rate limit status for all services
nf rate-limits status

# Output as JSON
nf rate-limits status --json

# Check if a specific service has capacity
nf rate-limits check apify

# Reset rate limits (for testing only)
nf rate-limits reset apify
nf rate-limits reset all
```

Example output:

```
Rate Limit Status:
+----------------+---------------+---------+--------+-----------+
| Service        | Available/Max | Usage % | Period | Refill In |
+================+===============+=========+========+===========+
| Apify API      | 95/100        | 5.0%    | 3600s  | 2543.2s   |
| RSS Feeds      | 8/10          | 20.0%   | 60s    | 42.1s     |
| Web Scraping   | 30/30         | 0.0%    | 60s    | 0.0s      |
| OpenAI API     | 60/60         | 0.0%    | 60s    | 0.0s      |
+----------------+---------------+---------+--------+-----------+

Backoff enabled: True
Max retries: 3
Initial backoff: 1.0s
Backoff multiplier: 2.0x
```

## Error Handling

When a rate limit is exceeded, the system will:

1. **With backoff enabled** (default):
   - Wait for the initial backoff period (1 second by default)
   - Retry the request
   - If still rate limited, wait longer (exponential backoff)
   - Continue up to max_retries times

2. **Without backoff**:
   - Raise a `RateLimitExceeded` exception immediately
   - The exception includes the service name and retry_after time

Example error handling:

```python
from local_newsifier.utils.rate_limiter import RateLimitExceeded

try:
    result = apify_service.run_actor(actor_id, run_input)
except RateLimitExceeded as e:
    print(f"Rate limited on {e.service}. Retry after {e.retry_after} seconds")
```

## Implementation Details

### Token Bucket Algorithm

The rate limiter uses a token bucket algorithm:

1. Each service has a bucket with a maximum number of tokens (max_calls)
2. Tokens are consumed when API calls are made
3. Tokens are refilled at a constant rate based on the period
4. If no tokens are available, the request is rate limited

### Redis Storage

Rate limit state is stored in Redis with keys like:
- `rate_limit:apify` - Stores tokens and last refill time
- `rate_limit:rss` - Stores tokens and last refill time
- etc.

Keys expire after 2x the period of inactivity to clean up unused state.

### Distributed Operation

The rate limiter works correctly across multiple workers/processes:
- Uses Redis transactions for atomic token consumption
- Handles race conditions with optimistic locking
- Shared state ensures consistent rate limiting

## Best Practices

1. **Set conservative limits**: Start with lower limits and increase as needed
2. **Monitor usage**: Use `nf rate-limits status` to track usage patterns
3. **Handle exceptions**: Always handle `RateLimitExceeded` in production code
4. **Test with resets**: Use `nf rate-limits reset` for testing
5. **Adjust backoff**: Tune backoff parameters based on service behavior

## Troubleshooting

### "Rate limit exceeded" errors

1. Check current status: `nf rate-limits status`
2. Verify configuration matches service limits
3. Consider increasing limits if consistently hitting them
4. Check Redis connectivity

### Redis connection issues

1. Verify Redis is running: `redis-cli ping`
2. Check `CELERY_BROKER_URL` environment variable
3. Ensure Redis has enough memory

### Unexpected behavior

1. Check for multiple workers consuming the same limits
2. Verify time synchronization between servers
3. Look for retry loops in logs
