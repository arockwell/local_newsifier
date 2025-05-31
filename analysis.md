# Apify Webhook Duplicate Detection Analysis

## Issue Summary
The webhook duplicate detection system is incorrectly treating all webhooks with the same `run_id` as duplicates, regardless of their status. This means when Apify sends multiple webhooks for the same run (e.g., STARTED, SUCCEEDED), only the first one is processed and subsequent ones are ignored.

## Evidence from server.log
1. Two webhook requests arrived for the same run_id `2mzWpPBeXWyTRdqxX`
2. Both had status `SUCCEEDED`
3. The second request was rejected as a duplicate
4. No articles were created from either webhook

## Root Cause Analysis

### Current Implementation (apify_webhook_service_sync.py)
```python
# Line 119-128
existing = self.session.exec(
    select(ApifyWebhookRaw).where(ApifyWebhookRaw.run_id == run_id)
).first()

if existing:
    logger.info(f"Duplicate webhook detected: run_id={run_id}, ignoring")
    return {"status": "ok", "message": "Duplicate webhook ignored"}
```

The duplicate check only looks at `run_id` without considering the webhook status. This is problematic because:

1. **Apify sends multiple webhooks per run**: Typically STARTED when a run begins and SUCCEEDED/FAILED when it completes
2. **Only SUCCEEDED webhooks should trigger article creation**: The code correctly checks for `status == "SUCCEEDED"` before creating articles (line 152)
3. **Current logic blocks legitimate status updates**: If a STARTED webhook arrives first, the SUCCEEDED webhook is blocked as a duplicate

### Database Schema Issue
The `ApifyWebhookRaw` table has a unique constraint on `run_id`:
```python
# Line 137 in models/apify.py
run_id: str = Field(unique=True, index=True)
```

This enforces the one-webhook-per-run limitation at the database level.

## Impact
- Article creation from Apify webhooks is completely broken
- Only the first webhook for any run is processed
- If STARTED arrives before SUCCEEDED, no articles are created
- The system logs show webhooks being received but no processing occurs

## Recommended Solution
The duplicate detection needs to consider both `run_id` AND `status` to allow multiple webhooks per run while preventing true duplicates. The database schema also needs to be updated to allow multiple records per run_id.
