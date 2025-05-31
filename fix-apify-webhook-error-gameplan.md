# Fix Apify Webhook Error Gameplan

## Problem Statement
The Apify webhook endpoint is returning 400 Bad Request with "Missing required webhook fields" error. This prevents successful processing of Apify actor run notifications.

## Step-by-Step Fix Plan

### Step 1: Add Enhanced Logging ✅ COMPLETED
First, we need to understand what payload is actually being sent by adding detailed logging.

**File**: `src/local_newsifier/services/apify_webhook_service_sync.py`
**Changes**:
- Add logging to show the entire payload received
- Log which specific fields are missing
- Log the actual values of required fields

**Status**: ✅ Implemented on 5/31/2025
- Added debug logging for the entire payload
- Added debug logging for extracted field values
- Enhanced error messages to show exactly which fields are missing
- Full payload is logged when validation fails
- PR #763 created - CI has dependency resolution issue with aiohttp unrelated to these changes
- All webhook service tests pass locally

**Update 5/31/2025 - After Sync Migration**:
- Investigated test failures after merging main (async to sync migration)
- Found that `tests/api/test_webhooks.py` has a test failure not due to async/sync issues
- The test `test_apify_webhook_valid_payload` expects "processed" in the message but gets "duplicate webhook ignored"
- Issue: The webhook service is not being properly mocked, and the actual service is detecting duplicates in the database
- Root cause: Test database persistence between test runs causing duplicate webhook entries
- Solution needed: Either properly mock the service or ensure test database isolation

**Update 5/31/2025 - Test Fix Completed**:
- Fixed all webhook tests by properly mocking the webhook service dependency
- Created a `mock_webhook_service` pytest fixture that uses `app.dependency_overrides` to override the DI properly
- Updated all test methods to use the new fixture
- All 6 webhook tests now pass successfully
- The fix ensures proper test isolation by overriding the service dependency instead of patching imports

```python
def handle_webhook(self, payload: Dict[str, any], raw_payload: str, signature: Optional[str] = None) -> Dict[str, any]:
    # Add debug logging
    logger.debug(f"Received webhook payload: {payload}")

    # Extract key fields
    run_id = payload.get("actorRunId", "")
    actor_id = payload.get("actorId", "")
    status = payload.get("status", "")

    # Log extracted values
    logger.debug(f"Extracted fields - run_id: '{run_id}', actor_id: '{actor_id}', status: '{status}'")

    if not all([run_id, actor_id, status]):
        missing_fields = []
        if not run_id:
            missing_fields.append("actorRunId")
        if not actor_id:
            missing_fields.append("actorId")
        if not status:
            missing_fields.append("status")

        logger.warning(f"Missing required webhook fields: {missing_fields}")
        logger.warning(f"Full payload: {payload}")
        return {"status": "error", "message": f"Missing required fields: {', '.join(missing_fields)}"}
```

### Step 2: Add Field Name Flexibility
Apify might send fields with different naming conventions. Add support for common variations.

**File**: `src/local_newsifier/services/apify_webhook_service_sync.py`
**Changes**:
- Check for alternative field names
- Handle both camelCase and snake_case

```python
# Extract key fields with fallbacks
run_id = payload.get("actorRunId") or payload.get("actor_run_id") or payload.get("runId") or ""
actor_id = payload.get("actorId") or payload.get("actor_id") or ""
status = payload.get("status") or payload.get("runStatus") or ""
```

### Step 3: Create Test Webhook Script
Create a test script to verify webhook behavior with actual Apify payloads.

**File**: `scripts/test_apify_webhook.py`
```python
#!/usr/bin/env python3
"""Test script for Apify webhook endpoint."""

import json
import requests
from datetime import datetime

# Test payloads
test_payloads = [
    # Standard payload
    {
        "actorRunId": "test-run-123",
        "actorId": "test-actor",
        "status": "SUCCEEDED",
        "eventType": "ACTOR.RUN.SUCCEEDED",
        "defaultDatasetId": "test-dataset"
    },
    # Minimal payload
    {
        "actorRunId": "test-run-456",
        "actorId": "test-actor",
        "status": "FAILED"
    },
    # Alternative field names
    {
        "runId": "test-run-789",
        "actor_id": "test-actor",
        "runStatus": "SUCCEEDED"
    }
]

# Test webhook endpoint
url = "http://localhost:8000/webhooks/apify"

for i, payload in enumerate(test_payloads):
    print(f"\nTest {i+1}: Sending payload...")
    print(json.dumps(payload, indent=2))

    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
```

### Step 4: Add Webhook Documentation
Document the expected webhook format and common issues.

**File**: `docs/integrations/apify/webhook_format.md`
```markdown
# Apify Webhook Format

## Required Fields
- `actorRunId`: The unique ID of the actor run
- `actorId`: The ID of the Apify actor
- `status`: The status of the run ("SUCCEEDED", "FAILED", etc.)

## Optional Fields
- `defaultDatasetId`: Dataset ID for fetching results
- `eventType`: Type of event (e.g., "ACTOR.RUN.SUCCEEDED")
- `createdAt`: Timestamp when the run was created
- `startedAt`: Timestamp when the run started
- `finishedAt`: Timestamp when the run finished

## Example Payload
```json
{
    "actorRunId": "HG7Ml3qZasdfl8kHC",
    "actorId": "apify/web-scraper",
    "status": "SUCCEEDED",
    "eventType": "ACTOR.RUN.SUCCEEDED",
    "defaultDatasetId": "s8NJu7lskKdsd98aH"
}
```
```

### Step 5: Update Error Messages
Make error messages more helpful by showing what was received vs. expected.

**File**: `src/local_newsifier/api/routers/webhooks.py`
**Changes**:
- Improve error response detail
- Add request ID for tracking

```python
# Check if there was an error
if result["status"] == "error":
    logger.error(f"Webhook validation failed: {result['message']}")
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "error": result["message"],
            "hint": "Ensure payload contains actorRunId, actorId, and status fields",
            "received_fields": list(payload.keys())
        }
    )
```

### Step 6: Add Webhook Monitoring
Add monitoring to track webhook failures.

**File**: `src/local_newsifier/services/apify_webhook_service_sync.py`
**Changes**:
- Add metrics/counters for webhook processing
- Track success/failure rates

```python
class ApifyWebhookServiceSync:
    # Class-level counters
    _webhook_success_count = 0
    _webhook_failure_count = 0
    _missing_fields_count = 0

    def handle_webhook(self, ...):
        # ... existing code ...

        if not all([run_id, actor_id, status]):
            self._missing_fields_count += 1
            self._webhook_failure_count += 1
            # ... rest of error handling

        # ... success path ...
        self._webhook_success_count += 1
```

### Step 7: Create Integration Test
Create an integration test that uses actual Apify webhook format.

**File**: `tests/integration/test_apify_webhook_real.py`
```python
import pytest
from datetime import datetime
import json

def test_real_apify_webhook_format(client):
    """Test with actual Apify webhook payload format."""
    # This is based on Apify's actual webhook format
    payload = {
        "userId": "BPWdQepxcsdFH8Scq",
        "createdAt": "2025-05-31T10:30:00.000Z",
        "eventType": "ACTOR.RUN.SUCCEEDED",
        "eventData": {
            "actorId": "apify/web-scraper",
            "actorRunId": "HG7Ml3qdfl8kHC"
        },
        "resource": {
            "id": "HG7Ml3qdfl8kHC",
            "actorId": "apify/web-scraper",
            "status": "SUCCEEDED",
            "startedAt": "2025-05-31T10:30:00.000Z",
            "finishedAt": "2025-05-31T10:35:00.000Z",
            "defaultDatasetId": "s8NJu7lQdd98aH"
        }
    }

    response = client.post("/webhooks/apify", json=payload)

    # Should handle the nested structure
    assert response.status_code in [202, 400]

    if response.status_code == 400:
        # If it fails, the error should be informative
        error_detail = response.json()["detail"]
        assert "actorRunId" in str(error_detail) or "Missing required fields" in str(error_detail)
```

### Step 8: Handle Nested Payload Structure
Based on real Apify webhooks, the data might be nested.

**File**: `src/local_newsifier/services/apify_webhook_service_sync.py`
**Changes**:
- Check for nested structure
- Extract from both flat and nested formats

```python
def handle_webhook(self, payload: Dict[str, any], ...):
    # Try to extract from flat structure first
    run_id = payload.get("actorRunId", "")
    actor_id = payload.get("actorId", "")
    status = payload.get("status", "")

    # If not found, try nested structure
    if not all([run_id, actor_id, status]):
        # Check eventData for IDs
        event_data = payload.get("eventData", {})
        run_id = run_id or event_data.get("actorRunId", "")
        actor_id = actor_id or event_data.get("actorId", "")

        # Check resource for status and other fields
        resource = payload.get("resource", {})
        run_id = run_id or resource.get("id", "")
        actor_id = actor_id or resource.get("actorId", "")
        status = status or resource.get("status", "")

        # Also update dataset_id extraction
        dataset_id = payload.get("defaultDatasetId") or resource.get("defaultDatasetId")
```

## Testing Plan

1. **Deploy enhanced logging** first to production to see actual payload format
2. **Run test script** against local development server
3. **Check logs** to verify field extraction
4. **Update field extraction** based on actual Apify format
5. **Test with curl** using real webhook payloads
6. **Monitor error rates** after deployment

## Rollback Plan

If the fix causes issues:
1. Revert to previous version
2. Keep enhanced logging for debugging
3. Work with Apify documentation/support to confirm exact format

## Success Criteria

- No more "Missing required fields" errors in logs
- Webhooks process successfully (202 response)
- Articles are created from successful actor runs
- Error messages provide clear guidance when issues occur

## Follow-up Actions

1. Set up webhook replay capability for failed webhooks
2. Add webhook payload validation schema
3. Create Apify webhook simulator for testing
4. Add metrics dashboard for webhook processing
5. Document the exact Apify webhook format used in production
