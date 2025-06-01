# Server Log Analysis - Missing Article Creation

## Executive Summary

The Apify webhook system is receiving and processing webhooks correctly, but articles are not being created due to a duplicate webhook detection issue. The system received multiple SUCCEEDED webhooks for the same run ID, and all but the first were rejected as duplicates.

## Key Findings

### 1. Webhook Reception Pattern
- **Initial webhook**: ACTOR.RUN.CREATED at 05:29:30 (status: RUNNING)
- **Success webhooks**: Multiple ACTOR.RUN.SUCCEEDED webhooks at 05:31:29 (status: SUCCEEDED)
- The system correctly processed the RUNNING webhook but rejected the SUCCEEDED webhooks as duplicates

### 2. Duplicate Detection Issue
From the logs:
```
Line 318-320: "Webhook not duplicate, proceeding with processing: run_id=Ej4N1TdcWesWV06Ne"
              "Duplicate webhook received for run_id: Ej4N1TdcWesWV06Ne, status: SUCCEEDED"
```

The duplicate check is working correctly but is preventing article creation because:
1. The first SUCCEEDED webhook starts processing
2. Additional SUCCEEDED webhooks arrive simultaneously
3. The duplicate check prevents the additional webhooks from processing
4. However, it appears the first webhook also didn't create articles

### 3. Critical Issue: No Dataset Fetch Attempt
The logs show NO evidence of:
- "Fetching dataset" log message
- "Dataset items received" log message
- "DATASET ITEM STRUCTURE" log message
- Any article creation attempts

This indicates the `_create_articles_from_dataset` method was never called, even for the first non-duplicate webhook.

### 4. Webhook Processing Flow
The code shows articles should be created when:
1. Status is "SUCCEEDED"
2. Dataset ID exists in the resource
3. Webhook is not a duplicate

Looking at the webhook payload:
- Status: "SUCCEEDED" ✓
- Dataset ID: "rQxBovQANNURSa5MG" ✓
- First webhook was not duplicate ✓

### 5. Root Cause Analysis

The issue appears to be a race condition in the duplicate detection logic:

1. Line 318: First webhook detected as NOT duplicate
2. Line 319: But immediately after, it's logged as duplicate
3. This suggests the webhook was saved to the database between these two operations

The logic flow shows:
```python
# Line 121-126: Check for duplicate
existing = self.session.exec(
    select(ApifyWebhookRaw).where(
        ApifyWebhookRaw.run_id == run_id, ApifyWebhookRaw.status == status
    )
).first()

# Line 129-133: If not duplicate, proceed
if existing:
    return {"status": "ok", "message": "Duplicate webhook ignored"}

# Line 145-169: Save webhook (with duplicate handling)
try:
    webhook_raw = ApifyWebhookRaw(...)
    self.session.add(webhook_raw)
    self.session.flush()
except IntegrityError:
    # Handle duplicate
```

The problem: Multiple webhooks are being processed simultaneously, and the duplicate check at line 121 doesn't see the record that's being inserted by another concurrent request.

### 6. Article Creation Never Reached

The logs show that even the first "non-duplicate" webhook returned with `articles_created=0`, indicating the article creation code block (lines 175-197) was never executed or failed silently.

## Conclusion

The system has two issues:
1. **Race condition in duplicate detection**: Multiple concurrent webhooks cause confusion in duplicate detection
2. **Article creation not executing**: Even when a webhook is processed, the article creation logic is not being triggered

The most likely cause is that the first webhook is being rolled back due to the duplicate key violation, preventing any article creation from occurring.
