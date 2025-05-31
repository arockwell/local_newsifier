# Apify Webhook Testing Guide

## Overview

This guide provides comprehensive information about testing Apify webhooks in the Local Newsifier project. It includes corrected HTTPie syntax, working Fish shell functions, and complete testing procedures.

**Important:** All webhook handlers are now implemented using sync-only patterns (no async/await) for better compatibility and simpler error handling.

## Table of Contents
1. [Webhook Endpoint Status](#webhook-endpoint-status)
2. [Required Webhook Fields](#required-webhook-fields)
3. [Fish Shell Testing Functions](#fish-shell-testing-functions)
4. [HTTPie Testing (Corrected Syntax)](#httpie-testing-corrected-syntax)
5. [Testing with curl](#testing-with-curl)
6. [Common Issues and Solutions](#common-issues-and-solutions)
7. [Production Testing](#production-testing)

## Webhook Endpoint Status

The Apify webhook endpoint is fully functional at `/webhooks/apify` with the following features:
- ✅ Accepts valid webhook payloads with 202 status
- ✅ Validates all required fields (returns 422 for missing fields)
- ✅ Handles different event types (SUCCEEDED, FAILED, ABORTED)
- ✅ Returns proper response with actor_id, dataset_id, and processing_status
- ✅ Webhook secret validation logic is implemented
- ✅ Uses sync-only implementation (no async/await)
- ✅ Proper database session management with error handling
- ✅ Fixed "generator didn't stop after throw()" errors

## Required Webhook Fields

All webhook requests must include these fields:
- `createdAt` (datetime string)
- `eventType` (string: "ACTOR.RUN.SUCCEEDED", "ACTOR.RUN.FAILED", "ACTOR.RUN.ABORTED")
- `actorId` (string)
- `actorRunId` (string)
- `userId` (string)
- `defaultKeyValueStoreId` (string)
- `defaultDatasetId` (string)
- `startedAt` (datetime string)
- `status` (string: "SUCCEEDED", "FAILED", "ABORTED")
- `webhookId` (string)

Optional fields:
- `finishedAt` (datetime string)
- `exitCode` (integer)
- `statusMessage` (string)
- `secret` (string - required if APIFY_WEBHOOK_SECRET is configured)

## Fish Shell Testing Functions

The project includes several Fish shell functions for easy webhook testing. These are pre-installed and ready to use:

### 1. `test_webhook` - Main Testing Function
```fish
# Show help
test_webhook --help

# Basic usage with defaults
test_webhook

# Custom parameters
test_webhook --event ACTOR.RUN.FAILED --status FAILED --actor my_actor
test_webhook -e ACTOR.RUN.ABORTED -s ABORTED -a custom_actor -r run_123
```

**Options:**
- `-e, --event`: Event type (default: ACTOR.RUN.SUCCEEDED)
- `-a, --actor`: Actor ID (default: tom_cruise)
- `-s, --status`: Status (default: SUCCEEDED)
- `-r, --run-id`: Actor run ID (default: test-run-123)
- `-w, --webhook-id`: Webhook ID (default: webhook-456)
- `-u, --url`: Webhook URL (default: http://localhost:8000/webhooks/apify)

**Note:** There's a known issue with the `status` variable being read-only in Fish. This doesn't affect the webhook functionality.

### 2. `test_webhook_success` - Test Successful Run
```fish
test_webhook_success
# Sends a webhook for a successful actor run
```

### 3. `test_webhook_failure` - Test Failed Run
```fish
test_webhook_failure
# Sends a webhook for a failed actor run
```

### 4. `test_webhook_abort` - Test Aborted Run
```fish
test_webhook_abort
# Sends a webhook for an aborted actor run
```

### 5. `test_webhook_invalid` - Test Validation
```fish
test_webhook_invalid
# Sends an invalid payload missing required fields
# Useful for testing error handling
```

### 6. `test_webhook_custom` - Test Custom Payloads
```fish
# Using a JSON file
test_webhook_custom --file webhook_payload.json

# Using inline JSON
test_webhook_custom '{"eventType": "ACTOR.RUN.SUCCEEDED", ...}'

# Show help
test_webhook_custom --help
```

### 7. `test_webhook_batch` - Run Multiple Tests
```fish
# Run one of each test type
test_webhook_batch

# Run multiple iterations
test_webhook_batch --count 3

# Custom URL
test_webhook_batch --url http://staging.example.com/webhooks/apify
```

## HTTPie Testing (Corrected Syntax)

### ⚠️ Important: Common HTTPie Mistake
The documentation previously showed incorrect HTTPie syntax. The following does NOT send JSON:

```bash
# ❌ INCORRECT - Sends form-encoded data
http POST http://localhost:8000/webhooks/apify \
    Content-Type:application/json \
    eventType=ACTOR.RUN.SUCCEEDED \
    actorId=tom_cruise
```

### ✅ Correct HTTPie Methods

#### Method 1: Pipe JSON
```bash
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

#### Method 2: Using JSON File
```bash
# Create payload file
cat > webhook_test.json << 'EOF'
{
    "eventType": "ACTOR.RUN.SUCCEEDED",
    "actorId": "web_scraper",
    "actorRunId": "run_$(date +%s)",
    "webhookId": "webhook_123",
    "createdAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "userId": "user_456",
    "defaultKeyValueStoreId": "kvs_789",
    "defaultDatasetId": "dataset_abc",
    "startedAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "status": "SUCCEEDED"
}
EOF

# Send request
http POST http://localhost:8000/webhooks/apify < webhook_test.json
```

#### Method 3: HTTPie with := Syntax (for simple cases)
```bash
# Note: This is less reliable for complex JSON
http POST http://localhost:8000/webhooks/apify \
    eventType:='"ACTOR.RUN.SUCCEEDED"' \
    actorId:='"tom_cruise"' \
    actorRunId:='"test-123"' \
    webhookId:='"webhook-456"' \
    createdAt:='"2025-01-25T12:00:00Z"' \
    userId:='"test_user"' \
    defaultKeyValueStoreId:='"test_kvs"' \
    defaultDatasetId:='"test_dataset"' \
    startedAt:='"2025-01-25T12:00:00Z"' \
    status:='"SUCCEEDED"'
```

### HTTPie Debugging Options
```bash
# Verbose output
http --verbose POST http://localhost:8000/webhooks/apify < webhook_test.json

# Print request and response
http --print=HhBb POST http://localhost:8000/webhooks/apify < webhook_test.json

# Headers only
http --headers POST http://localhost:8000/webhooks/apify < webhook_test.json
```

## Testing with curl

### Basic curl Example
```bash
curl -X POST http://localhost:8000/webhooks/apify \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

### curl with Dynamic Timestamps
```bash
curl -X POST http://localhost:8000/webhooks/apify \
  -H "Content-Type: application/json" \
  -d "{
    \"eventType\": \"ACTOR.RUN.SUCCEEDED\",
    \"actorId\": \"web_scraper\",
    \"actorRunId\": \"run_$(date +%s)\",
    \"webhookId\": \"webhook_$(date +%s)\",
    \"createdAt\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
    \"userId\": \"user_123\",
    \"defaultKeyValueStoreId\": \"kvs_456\",
    \"defaultDatasetId\": \"dataset_789\",
    \"startedAt\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
    \"status\": \"SUCCEEDED\"
  }"
```

## Common Issues and Solutions

### 1. HTTPie Syntax Issues
**Problem:** Using `key=value` syntax sends form data, not JSON.
**Solution:** Use piped JSON or the `:=` operator for JSON values.

### 2. Missing Required Fields
**Problem:** 422 Unprocessable Entity errors.
**Solution:** Ensure all required fields are included. Use `test_webhook_invalid` to see which fields are required.

### 3. Read-only Variable Error in Fish
**Problem:** "set: Tried to change the read-only variable 'status'"
**Solution:** This is a known issue with the Fish function but doesn't affect webhook functionality. The webhook still processes correctly.

### 4. Timestamp Format
**Problem:** Invalid timestamp format.
**Solution:** Use ISO 8601 format: `YYYY-MM-DDTHH:MM:SSZ` or `YYYY-MM-DDTHH:MM:SS.sssZ`

### 5. Server Not Running
**Problem:** Connection refused errors.
**Solution:** Start the server with `make run-api` or `uvicorn src.local_newsifier.api.main:app --reload`

## Production Testing

### Environment Variables
```bash
# For webhook secret validation
export APIFY_WEBHOOK_SECRET="your_production_secret"

# Test without secret (development)
unset APIFY_WEBHOOK_SECRET
```

### Testing Webhook Secret Validation
```bash
# With correct secret
echo '{
    "eventType": "ACTOR.RUN.SUCCEEDED",
    "actorId": "production_actor",
    "actorRunId": "prod_run_123",
    "webhookId": "prod_webhook",
    "createdAt": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "userId": "prod_user",
    "defaultKeyValueStoreId": "prod_kvs",
    "defaultDatasetId": "prod_dataset",
    "startedAt": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "status": "SUCCEEDED",
    "secret": "your_production_secret"
}' | http POST https://your-app.railway.app/webhooks/apify

# With wrong secret (should return 401)
```

### Production Checklist
- [ ] Verify APIFY_WEBHOOK_SECRET is set in production
- [ ] Test webhook endpoint is accessible
- [ ] Confirm webhook secret matches Apify configuration
- [ ] Monitor logs for webhook receipts
- [ ] Check for validation failures
- [ ] Verify response times are acceptable

## Sample Webhook Payload File

The repository includes a sample webhook payload at `webhook_payload.json`:
```json
{
    "eventType": "ACTOR.RUN.SUCCEEDED",
    "actorId": "tom_cruise",
    "actorRunId": "test-run-123",
    "webhookId": "webhook-456",
    "createdAt": "2025-05-25T21:02:35Z",
    "userId": "test_user",
    "defaultKeyValueStoreId": "test_kvs",
    "defaultDatasetId": "test_dataset",
    "startedAt": "2025-05-25T21:02:35Z",
    "status": "0"
}
```

You can use this with:
```bash
# HTTPie
http POST http://localhost:8000/webhooks/apify < webhook_payload.json

# curl
curl -X POST http://localhost:8000/webhooks/apify \
  -H "Content-Type: application/json" \
  -d @webhook_payload.json

# Fish function
test_webhook_custom --file webhook_payload.json
```

## Quick Testing Commands

```bash
# Test successful webhook (Fish)
test_webhook_success

# Test all scenarios (Fish)
test_webhook_batch

# Test with HTTPie (correct syntax)
echo '{"eventType":"ACTOR.RUN.SUCCEEDED","actorId":"test","actorRunId":"123","webhookId":"456","createdAt":"2025-01-25T12:00:00Z","userId":"user","defaultKeyValueStoreId":"kvs","defaultDatasetId":"dataset","startedAt":"2025-01-25T12:00:00Z","status":"SUCCEEDED"}' | http POST http://localhost:8000/webhooks/apify

# Test with curl
curl -sS -X POST http://localhost:8000/webhooks/apify -H "Content-Type: application/json" -d @webhook_payload.json | jq '.'
```

## Implementation Details

### Sync-Only Architecture
The webhook implementation follows the project's sync-only pattern:

1. **Route Handler**: Uses standard `def` (not `async def`)
   ```python
   @router.post("/webhooks/apify")
   def apify_webhook(
       webhook_data: ApifyWebhook,
       webhook_service: Annotated[ApifyWebhookService, Depends(get_apify_webhook_service)]
   ):
       # Sync processing
   ```

2. **Database Sessions**: Managed via FastAPI dependency injection
   - Sessions are created and closed automatically
   - Proper error handling prevents session leaks
   - No async context managers used

3. **Error Handling**: Exceptions are properly handled without async complications
   - Validation errors return 422
   - Authentication errors return 401
   - Processing errors return appropriate status codes

### Session Management Pattern
The webhook uses a simple session provider that avoids the "generator didn't stop after throw()" error:
```python
def get_session() -> Session:
    engine = get_engine()
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

## Summary

The Apify webhook infrastructure is fully functional and ready for use. The Fish shell functions provide the easiest way to test webhooks locally, while HTTPie and curl offer more flexibility for custom testing scenarios. Remember to use the correct JSON syntax with HTTPie to avoid common pitfalls.

The sync-only implementation ensures better reliability and simpler error handling compared to async patterns.
