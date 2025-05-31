# Apify Webhook Processing Documentation

## Overview

This document describes the complete flow of Apify webhook processing, from receipt to data storage, and how to verify successful processing.

## Webhook Lifecycle

Apify sends multiple webhooks during an actor run lifecycle:

1. **STARTED** - When the actor run begins
2. **SUCCEEDED** - When the actor run completes successfully
3. **FAILED** - When the actor run fails
4. **ABORTED** - When the actor run is manually stopped
5. **TIMED-OUT** - When the actor run exceeds timeout

Each webhook contains the same `run_id` but different `status` values, allowing us to track the full lifecycle of an actor run.

## Webhook Processing Flow

### 1. Webhook Receipt

When an Apify actor run changes state, it sends a POST request to `/webhooks/apify`:

```
POST /webhooks/apify
Content-Type: application/json
Apify-Webhook-Signature: <optional-hmac-signature>

{
  "eventData": {
    "actorId": "actor-id",
    "actorRunId": "run-id"
  },
  "resource": {
    "id": "run-id",
    "actId": "actor-id",
    "status": "SUCCEEDED",
    "defaultDatasetId": "dataset-id"
  }
}
```

### 2. Processing Steps

#### Step 1: Signature Validation (Optional)
- If `APIFY_WEBHOOK_SECRET` environment variable is set
- Validates `Apify-Webhook-Signature` header using HMAC-SHA256
- Returns 400 Bad Request if signature is invalid

#### Step 2: Extract Key Fields
The webhook service extracts these fields from the nested payload:
- `run_id`: Unique identifier for the actor run
- `actor_id`: ID of the Apify actor that ran
- `status`: Run status (SUCCEEDED, FAILED, ABORTED, etc.)
- `dataset_id`: ID of the dataset containing results

#### Step 3: Duplicate Check
- Queries `apify_webhook_raw` table for existing `run_id` AND `status` combination
- If found, returns success without reprocessing
- Allows multiple webhooks per run (STARTED, SUCCEEDED, etc.)
- Prevents duplicate processing of the same status

#### Step 4: Store Raw Webhook Data
Creates an `ApifyWebhookRaw` record:
```python
{
    "run_id": "unique-run-id",      # Unique constraint
    "actor_id": "actor-id",
    "status": "SUCCEEDED",
    "data": {...}                    # Complete webhook payload
}
```

#### Step 5: Create Articles (Success Only)
**Only processes when status is SUCCEEDED**:
1. Fetches dataset items from Apify API
2. For each item:
   - Extracts `url`, `title`, and `content` (with fallbacks)
   - Validates minimum content length (100 chars)
   - Checks for existing article with same URL
   - Creates new `Article` record if not exists

**Other statuses (STARTED, FAILED, etc.) are stored but do not trigger article creation.**

### 3. Database Records Created

#### ApifyWebhookRaw Table
- **Always created** for every webhook received
- Contains raw webhook data for audit trail
- Composite unique constraint on `(run_id, status)` allows multiple statuses per run

```sql
CREATE TABLE apify_webhook_raw (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR NOT NULL,
    actor_id VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(run_id, status)  -- Composite constraint
);
```

#### Articles Table
- **Created only for successful runs** with valid data
- One article per dataset item with valid content

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

## Verification Guide

### 1. Check Webhook Receipt

Verify the webhook was received and stored:

```bash
# Using CLI
nf db inspect apify_webhook_raw <id>

# Using SQL - Check all statuses for a run
psql $DATABASE_URL -c "
SELECT id, run_id, actor_id, status, created_at
FROM apify_webhook_raw
WHERE run_id = 'your-run-id'
ORDER BY created_at;
"

# Check specific status
psql $DATABASE_URL -c "
SELECT id, run_id, actor_id, status, created_at
FROM apify_webhook_raw
WHERE run_id = 'your-run-id' AND status = 'SUCCEEDED';
"
```

### 2. Check Articles Created

Verify articles were created from the webhook:

```bash
# List recent Apify articles
nf db articles --source apify --limit 10

# Check specific timeframe
psql $DATABASE_URL -c "
SELECT id, url, title, LENGTH(content) as content_length, created_at
FROM articles
WHERE source = 'apify'
  AND created_at > NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC;
"
```

### 3. Check Processing Logs

Look for relevant log entries:

```bash
# Success logs
grep "Created article from Apify" logs/app.log

# Duplicate detection
grep "Duplicate webhook for run_id" logs/app.log

# Errors
grep "Error creating articles from webhook" logs/app.log
```

### 4. Verify Webhook Response

The webhook endpoint returns:
```json
{
    "status": "accepted",
    "actor_id": "actor-id",
    "dataset_id": "dataset-id",
    "articles_created": 5,
    "message": "Webhook processed successfully"
}
```

### 5. Common Issues and Solutions

#### No Articles Created
- Check webhook status - only SUCCEEDED runs create articles
- Verify dataset has items with valid url, title, content
- Check minimum content length (100 characters)
- Look for duplicate URLs in existing articles

#### Webhook Not Stored
- Check for signature validation errors
- Verify required fields in webhook payload
- Check database connectivity

#### Multiple Webhooks for Same Run
- Normal behavior - Apify sends webhooks for each status change
- STARTED webhook stored when run begins
- SUCCEEDED/FAILED webhook stored when run completes
- Each status is stored separately with same run_id

#### Duplicate Webhooks
- Same run_id + status combination is rejected as duplicate
- Returns success without reprocessing
- Check logs for "Duplicate webhook" messages with status

## Testing Webhook Processing

### Using Fish Shell Functions

```fish
# Test successful webhook
test_webhook_success

# Test with custom run ID
test_webhook --run-id "custom-run-123"

# Test batch of webhooks
test_webhook_batch
```

### Manual Testing

```bash
# Send test webhook
curl -X POST http://localhost:8000/webhooks/apify \
  -H "Content-Type: application/json" \
  -d '{
    "eventData": {
      "actorId": "test-actor",
      "actorRunId": "test-run-123"
    },
    "resource": {
      "id": "test-run-123",
      "actId": "test-actor",
      "status": "SUCCEEDED",
      "defaultDatasetId": "test-dataset"
    }
  }'
```

## Monitoring Checklist

- [ ] Webhook endpoint returns 202 Accepted
- [ ] ApifyWebhookRaw record created with correct run_id
- [ ] Articles created for successful runs
- [ ] No duplicate processing for same run_id
- [ ] Error logs capture failures
- [ ] Response includes correct article count

## Related Documentation

- [Webhook Testing Guide](webhook_testing.md)
- [Error Handling](error_handling.md)
- [Apify Integration Overview](integration.md)
