# Apify Webhook Complexity Analysis

## Executive Summary

You're right to be skeptical. The Apify webhook implementation has become unnecessarily complex for what should be a simple webhook handler. The current implementation has multiple layers of complexity that are contributing to persistent failures.

## Key Issues Identified

### 1. Overly Complex Duplicate Detection

The webhook service has a convoluted duplicate detection mechanism:
- First checks for duplicates in memory (lines 123-128 in webhook service)
- Then tries to insert and catches `IntegrityError` (lines 153-184)
- Has both a unique index on `run_id` AND a composite constraint on `run_id + status`
- The migration shows only `run_id` unique constraint, but the model shows composite constraint

**Why it's failing**: The duplicate check queries for `run_id + status` but the database might only have the `run_id` unique constraint, causing mismatched expectations.

### 2. Session Management Nightmare

The session handling is overly complex:
- Session is passed through dependency injection
- Errors cause session rollback but the session isn't properly cleaned up
- The webhook endpoint tries to return 200 OK even on errors to "stop Apify retry storms" (line 137-144 in webhooks.py)
- Session commits happen at multiple levels causing transaction conflicts

### 3. Nested Payload Extraction Complexity

The webhook tries to extract data from multiple nested locations:
```python
# From webhook service lines 85-92
event_data = payload.get("eventData", {})
resource = payload.get("resource", {})
run_id = event_data.get("actorRunId", "") or resource.get("id", "")
actor_id = event_data.get("actorId", "") or resource.get("actId", "")
status = resource.get("status", "")
```

This suggests the payload structure isn't well-defined or Apify sends different formats.

### 4. Article Creation Failures

The webhook is failing to create articles because:
- Field mapping is incorrect (looking for "title" but data has different field names)
- Multiple fallback fields for content (`content`, `text`, `body`)
- Complex skip logic with multiple conditions
- No clear error when fields are missing

### 5. Excessive Logging

The code is littered with emergency logging (lines 56-59, 268-273) suggesting ongoing debugging of persistent issues. This indicates the real problem hasn't been solved.

## Why It's Constantly Failing

1. **Race Conditions**: Multiple webhook requests for the same run hit the endpoint simultaneously
2. **Constraint Mismatches**: Database constraints don't match what the code expects
3. **Session State Issues**: Failed transactions corrupt the session, causing cascade failures
4. **Field Mapping Problems**: The expected article fields don't match what Apify actually sends
5. **Error Handling**: Trying to be "clever" by returning 200 OK on errors creates more problems

## Recommendations for Simplification

### 1. Simple Idempotent Design
```python
def handle_webhook(self, payload):
    run_id = payload.get("resource", {}).get("id")
    if not run_id:
        return {"error": "Missing run_id"}

    # Simple upsert - let the database handle duplicates
    webhook = self.session.merge(ApifyWebhookRaw(
        run_id=run_id,
        data=payload
    ))
    self.session.commit()

    # Process in background if needed
    if payload.get("resource", {}).get("status") == "SUCCEEDED":
        process_webhook_task.delay(run_id)

    return {"status": "accepted"}
```

### 2. Fix the Database Constraints
- Either use ONLY `run_id` unique OR use the composite constraint
- Don't try to handle both in code

### 3. Simplify Field Extraction
- Define a clear contract for what fields Apify sends
- Use a simple mapper class instead of complex nested extraction
- Fail fast if required fields are missing

### 4. Remove Session Complexity
- Use a fresh session for each webhook
- Don't try to reuse sessions across operations
- Let FastAPI handle session cleanup

### 5. Proper Error Responses
- Return proper HTTP error codes
- Let Apify handle retries with exponential backoff
- Don't try to outsmart the webhook retry mechanism

## The Real Problem

The implementation is trying to handle too many edge cases and potential failures instead of following the simple webhook pattern:
1. Receive webhook
2. Store it (idempotently)
3. Process it (asynchronously if needed)
4. Return success/failure

The current implementation mixes all these concerns together, creating a complex, fragile system that's hard to debug and maintain.
