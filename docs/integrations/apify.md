# Apify Integration Guide

## Overview

[Apify](https://apify.com/) is a web scraping and automation platform that Local Newsifier uses to extract content from websites that don't offer RSS feeds. This integration allows the system to collect news articles from a wider range of sources.

## Table of Contents
- [Setup](#setup)
- [CLI Commands](#cli-commands)
- [Webhook Integration](#webhook-integration)
- [Database Schema](#database-schema)
- [Error Handling](#error-handling)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## Setup

### Requirements

1. **Apify Account**: Register at [apify.com](https://apify.com/)
2. **API Token**: Generate an API token in your Apify account settings
3. **Environment Variables**:

```bash
# Required
export APIFY_TOKEN=your_token_here

# Optional (for webhook validation)
export APIFY_WEBHOOK_SECRET=your_webhook_secret
```

### Configuration Methods

```bash
# Environment variable
export APIFY_TOKEN=your_token_here

# .env file
echo "APIFY_TOKEN=your_token_here" >> .env

# CLI parameter
nf apify test --token your_token_here
```

## CLI Commands

### Test Connection
```bash
nf apify test
```

### Scrape Content
```bash
# Basic usage
nf apify scrape-content https://example.com

# Advanced options
nf apify scrape-content https://example.com \
  --max-pages 10 \
  --max-depth 2 \
  --output results.json
```

### Web Scraper
```bash
# Basic usage
nf apify web-scraper https://example.com

# With custom selectors
nf apify web-scraper https://example.com \
  --selector "article a" \
  --output results.json

# With page function
nf apify web-scraper https://example.com \
  --page-function "path/to/page_function.js"
```

### Run Custom Actors
```bash
# With JSON input
nf apify run-actor apify/web-scraper \
  --input '{"startUrls":[{"url":"https://example.com"}]}'

# With input file
nf apify run-actor apify/web-scraper --input input.json
```

### Get Dataset Items
```bash
nf apify get-dataset dataset_id --limit 20 --format table
```

## Webhook Integration

### Overview

The webhook endpoint at `/webhooks/apify` processes Apify actor run notifications with:
- **Sync-only implementation**: No async/await for reliability
- **Proper validation**: All required fields are validated
- **Duplicate prevention**: Same run_id won't be processed twice
- **Automatic article creation**: Successful runs create articles

### Setting Up Webhooks

1. In your Apify actor settings, navigate to "Webhooks"
2. Add a new webhook with:
   - Event types: `ACTOR.RUN.SUCCEEDED`, `ACTOR.RUN.FAILED`, `ACTOR.RUN.ABORTED`
   - URL: `https://your-app.com/webhooks/apify`
   - Secret: (Optional, set `APIFY_WEBHOOK_SECRET` if used)

### Webhook Processing Flow

1. **Receipt**: Webhook received at `/webhooks/apify`
2. **Validation**: Signature validated if secret configured
3. **Storage**: Raw payload stored in `apify_webhook_raw` table
4. **Duplicate Check**: Prevents reprocessing same run_id
5. **Article Creation**: For successful runs, creates articles from dataset

### Required Webhook Fields

```json
{
  "eventType": "ACTOR.RUN.SUCCEEDED",
  "actorId": "actor-id",
  "actorRunId": "run-id",
  "userId": "user-id",
  "webhookId": "webhook-id",
  "createdAt": "2025-01-25T12:00:00Z",
  "defaultKeyValueStoreId": "kvs-id",
  "defaultDatasetId": "dataset-id",
  "startedAt": "2025-01-25T12:00:00Z",
  "status": "SUCCEEDED"
}
```

## Database Schema

### ApifyWebhookRaw
Stores raw webhook payloads for audit trail:

```sql
CREATE TABLE apify_webhook_raw (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR UNIQUE NOT NULL,
    actor_id VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### ApifySourceConfig
Manages actor configurations:

```sql
CREATE TABLE apify_source_configs (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    actor_id VARCHAR NOT NULL,
    run_input JSONB NOT NULL,
    schedule_id VARCHAR,
    webhook_url VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Articles
Articles created from Apify data:

```sql
CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
    url VARCHAR UNIQUE NOT NULL,
    title VARCHAR NOT NULL,
    content TEXT NOT NULL,
    source VARCHAR DEFAULT 'apify',
    published_at TIMESTAMP,
    status VARCHAR DEFAULT 'published',
    scraped_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Error Handling

### Decorator Pattern

The project uses decorators for consistent error handling:

```python
from local_newsifier.errors import handle_apify

class ApifyService:
    @handle_apify
    def run_actor(self, actor_id, run_input):
        """Automatically handles errors, retry, and logging."""
        return self.client.actor(actor_id).call(run_input=run_input)
```

### Error Types

- **Network Error**: Connection issues with Apify API
- **Authentication Error**: Invalid or expired token
- **Rate Limit Error**: Too many requests
- **Validation Error**: Invalid input or missing fields
- **Actor Error**: Actor execution failures

### Error Messages

```
# Network Error
apify.network: Failed to connect to Apify API: Connection refused
Hint: Check your internet connection.

# Authentication Error
apify.auth: Authentication failed: 401 Unauthorized
Hint: Check your APIFY_TOKEN in settings.

# Rate Limit Error
apify.rate_limit: Rate limit exceeded: 429 Too Many Requests
Hint: Try again later or upgrade your plan.
```

## Testing

### Fish Shell Functions

```bash
# Test successful webhook
test_webhook_success

# Test failed webhook
test_webhook_failure

# Test all scenarios
test_webhook_batch

# Custom parameters
test_webhook --event ACTOR.RUN.FAILED --status FAILED --actor my_actor
```

### HTTPie Testing

```bash
# Correct JSON syntax
echo '{
    "eventType": "ACTOR.RUN.SUCCEEDED",
    "actorId": "tom_cruise",
    "actorRunId": "test-run-123",
    "webhookId": "webhook-456",
    "createdAt": "2025-01-25T12:00:00Z",
    "userId": "test_user",
    "defaultKeyValueStoreId": "test_kvs",
    "defaultDatasetId": "test_dataset",
    "startedAt": "2025-01-25T12:00:00Z",
    "status": "SUCCEEDED"
}' | http POST http://localhost:8000/webhooks/apify Content-Type:application/json
```

### Verification

```bash
# Check webhook receipt
nf db inspect apify_webhook_raw <id>

# List recent Apify articles
nf db articles --source apify --limit 10

# Check logs
grep "Created article from Apify" logs/app.log
```

### Mock Testing

The ApifyService automatically uses mock data when no token is provided:

```python
def test_apify_run_actor():
    # No token = test mode
    service = ApifyService()
    result = service.run_actor(
        "apify/web-scraper",
        {"startUrls": [{"url": "https://example.com"}]}
    )
    assert result["status"] == "SUCCEEDED"
```

## Troubleshooting

### Common Issues

#### No Articles Created
- Check webhook status (only SUCCEEDED creates articles)
- Verify dataset has valid url, title, content
- Check minimum content length (100 chars)
- Look for duplicate URLs

#### Webhook Not Received
- Verify webhook URL is publicly accessible
- Check actor configuration includes webhook
- Review Apify dashboard for delivery attempts

#### Authentication Failures
- Verify APIFY_TOKEN is set correctly
- Check token permissions
- Ensure token hasn't expired

#### Rate Limits
- Space out scraping jobs
- Reduce concurrency in actor settings
- Use Apify proxy services if available

### Debug Commands

```bash
# Check recent webhooks
psql $DATABASE_URL -c "
SELECT id, run_id, actor_id, status, created_at
FROM apify_webhook_raw
ORDER BY created_at DESC
LIMIT 10;
"

# Check article creation
psql $DATABASE_URL -c "
SELECT COUNT(*) as article_count, source, DATE(created_at) as date
FROM articles
WHERE source = 'apify'
GROUP BY source, DATE(created_at)
ORDER BY date DESC;
"
```

## Performance Considerations

- **Limit pages scraped**: Set appropriate maxCrawlPages
- **Request delays**: Avoid overloading target sites
- **Off-peak scheduling**: Run during low-traffic hours
- **Selective scraping**: Target specific URLs vs entire sites

## Security Notes

- Keep API tokens secure (never commit to git)
- Use webhook secrets in production
- Validate and sanitize scraped content
- Review scraped data for sensitive information
- Use least-privilege API tokens

## Best Practices

### Actor Configuration
- Start with minimal crawl depth
- Test selectors before production use
- Store actor configurations as templates
- Version control input configurations

### Data Processing
- Validate required fields before creating articles
- Handle missing data gracefully
- Store raw webhook data for debugging
- Implement idempotent processing

### Monitoring
- Track success/failure rates
- Monitor processing times
- Set up alerts for failures
- Regular cleanup of old webhook data

## See Also

- [Testing Guide](../guides/testing_guide.md#apify-webhook-testing) - Webhook testing details
- [CLI Usage Guide](../guides/cli_usage.md) - Complete CLI reference
- [Error Handling Guide](../guides/error_handling.md) - Error handling patterns
- [Apify API Documentation](https://docs.apify.com/api/v2)
