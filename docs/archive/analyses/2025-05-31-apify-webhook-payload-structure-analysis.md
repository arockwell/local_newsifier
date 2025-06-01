# Apify Webhook Payload Structure Analysis

## Problem Summary

Our Apify webhook handler is failing with 400 Bad Request because we're expecting a flat payload structure, but Apify sends a nested structure with the key fields distributed across different sections.

## Actual Apify Webhook Structure (from production)

```json
{
  "userId": "qXv5lHkKPgB4D5S3g",
  "createdAt": "2025-05-31T07:37:19.269Z",
  "eventType": "ACTOR.RUN.SUCCEEDED",
  "eventData": {
    "actorId": "aYG0l9s7dbB7j3gbS",
    "actorTaskId": "z2WD0CwFgvaN2F2Sl",
    "actorRunId": "sht8ejsKC0sSUygKy"
  },
  "resource": {
    "id": "sht8ejsKC0sSUygKy",
    "actId": "aYG0l9s7dbB7j3gbS",
    "userId": "qXv5lHkKPgB4D5S3g",
    "actorTaskId": "z2WD0CwFgvaN2F2Sl",
    "startedAt": "2025-05-31T07:33:47.147Z",
    "finishedAt": "2025-05-31T07:37:13.177Z",
    "status": "SUCCEEDED",
    "statusMessage": "Finished! Total 18 requests: 18 succeeded, 0 failed.",
    "isStatusMessageTerminal": true,
    "meta": { ... },
    "stats": { ... },
    "options": { ... },
    "buildId": "qd2nxvUfFzMmR7kTK",
    "exitCode": 0,
    "defaultKeyValueStoreId": "0JuCT2tNDtuFZFZY8",
    "defaultDatasetId": "73wUXwVp3yDBKjzsd",
    "defaultRequestQueueId": "9dbG01hgtf0sJakEU",
    "generalAccess": "FOLLOW_USER_SETTING",
    "buildNumber": null,
    "containerUrl": "https://hfbe6hqblym0.runs.apify.net",
    "usage": { ... },
    "usageTotalUsd": 0.7321066666666667,
    "usageUsd": { ... },
    "links": { ... }
  }
}
```

## Current Code Issues

### 1. Field Location Mismatch

Our code expects flat structure:
```python
run_id = payload.get("actorRunId", "")
actor_id = payload.get("actorId", "")
status = payload.get("status", "")
```

But the actual structure is nested:
- `actorRunId` → `eventData.actorRunId`
- `actorId` → `eventData.actorId`
- `status` → `resource.status`
- `defaultDatasetId` → `resource.defaultDatasetId`

### 2. Model Structure Mismatch

Our `ApifyWebhookPayload` model expects many fields at the root level that are actually nested within `resource`:
- `defaultKeyValueStoreId`
- `defaultDatasetId`
- `defaultRequestQueueId`
- `startedAt`
- `finishedAt`
- `exitCode`
- `statusMessage`

### 3. Missing Fields

Our model expects fields that don't exist in the actual payload:
- `webhookId`
- `payloadTemplate`
- `secret`
- `taskId` (it's `actorTaskId` in `eventData`)

## Key Findings

1. **Event-driven structure**: The webhook follows an event notification pattern with:
   - `eventType`: The type of event (e.g., "ACTOR.RUN.SUCCEEDED")
   - `eventData`: Key identifiers for the event
   - `resource`: Detailed information about the resource that triggered the event

2. **Duplicate data**: Some fields appear in multiple places:
   - `actorId` appears in both `eventData.actorId` and `resource.actId`
   - `actorRunId` appears in both `eventData.actorRunId` and `resource.id`

3. **Dataset location**: The crucial `defaultDatasetId` field is in `resource.defaultDatasetId`, not at the root level

## Recommendations

1. Update the webhook handler to properly navigate the nested structure
2. Consider using a more flexible approach that doesn't require a strict Pydantic model for the incoming webhook
3. Update tests to use realistic webhook payloads based on the actual structure
4. Add defensive coding to handle variations in the webhook structure
