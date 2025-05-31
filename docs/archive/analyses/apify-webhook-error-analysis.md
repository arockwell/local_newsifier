# Apify Webhook Error Analysis

## Issue Summary

The server.log shows a 400 Bad Request error for the Apify webhook endpoint with the following error:
- **Error**: "Missing required webhook fields"
- **Timestamp**: 2025-05-31 05:41:52
- **Endpoint**: `/webhooks/apify`
- **Response**: 400 Bad Request

## Root Cause Analysis

Based on the code analysis, the error occurs in `ApifyWebhookServiceSync.handle_webhook()` method (lines 74-81 in `apify_webhook_service_sync.py`):

```python
# Extract key fields
run_id = payload.get("actorRunId", "")
actor_id = payload.get("actorId", "")
status = payload.get("status", "")

if not all([run_id, actor_id, status]):
    logger.warning("Missing required webhook fields")
    return {"status": "error", "message": "Missing required fields"}
```

The webhook service expects three required fields in the payload:
1. `actorRunId` - The ID of the Apify actor run
2. `actorId` - The ID of the Apify actor
3. `status` - The status of the actor run (e.g., "SUCCEEDED", "FAILED")

## Webhook Payload Format

Based on the test files, the expected Apify webhook payload should look like:

```json
{
    "createdAt": "2025-05-31T10:30:00.000Z",
    "eventType": "ACTOR.RUN.SUCCEEDED",
    "actorId": "test_actor",
    "actorRunId": "abc123-def456-789",
    "userId": "test_user",
    "defaultKeyValueStoreId": "test_kvs",
    "defaultDatasetId": "test_dataset",
    "startedAt": "2025-05-31T10:30:00.000Z",
    "status": "SUCCEEDED",
    "webhookId": "webhook-123"
}
```

## Common Causes

The 400 error can occur when:

1. **Missing Fields**: The webhook payload is missing one or more of the required fields (`actorRunId`, `actorId`, or `status`)
2. **Empty Values**: The fields exist but have empty string values
3. **Incorrect Field Names**: The field names are misspelled or use different casing
4. **Malformed JSON**: The request body is not valid JSON

## Additional Context

- The webhook also supports signature validation if `APIFY_WEBHOOK_SECRET` is configured
- If signature validation fails, it returns a different error message: "Invalid signature"
- The webhook creates articles from the dataset if the status is "SUCCEEDED" and a `defaultDatasetId` is provided
- Duplicate webhooks (same `run_id`) are ignored gracefully
