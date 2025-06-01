# Analysis: Duplicate Key Constraint Violation in Apify Webhook Processing

## Issue Overview

The Apify webhook endpoint is receiving multiple requests for the same run ID, causing duplicate key violations when attempting to insert into the `apify_webhook_raw` table.

## Technical Details

### Error Signature
```
sqlalchemy.exc.IntegrityError: (psycopg2.errors.UniqueViolation) duplicate key value violates unique constraint "ix_apify_webhook_raw_run_id"
DETAIL:  Key (run_id)=(IhQcgycyaMIzQOazn) already exists.
```

### Affected Components
- **Endpoint**: `/webhooks/apify`
- **Service**: `ApifyWebhookService.handle_webhook()`
- **Table**: `apify_webhook_raw`
- **Constraint**: `ix_apify_webhook_raw_run_id` (unique index on run_id)

## Root Cause Analysis

### 1. Failed Duplicate Detection
The service logs indicate a duplicate check is performed:
```
Checking for duplicate webhook: run_id=IhQcgycyaMIzQOazn, status=SUCCEEDED
Webhook not duplicate, proceeding with processing: run_id=IhQcgycyaMIzQOazn
```

However, the insert still fails, suggesting:
- The duplicate check queries a different table or uses different criteria
- The check is not transactionally consistent with the insert
- Race condition between check and insert

### 2. Multiple Webhook Deliveries
The same run_id appears at multiple timestamps:
- 02:28:37
- 02:36:28 (8 minutes later)
- 02:44:14 (8 minutes later)
- 03:11:02 (27 minutes later)

This pattern suggests:
- Apify is retrying webhook delivery due to 500 errors
- The retry interval appears to be ~8 minutes initially
- No acknowledgment mechanism to stop retries

### 3. Database Transaction Issues
The unique constraint is working correctly, but:
- No proper error handling for duplicate key violations
- The error propagates up causing a 500 response
- This triggers Apify to retry, creating a cycle

## Code Analysis

Based on the logs, the problematic flow appears to be:

1. `apify_webhook()` endpoint receives request
2. `webhook_service.handle_webhook()` is called
3. Duplicate check returns false (incorrectly)
4. Attempt to insert into `apify_webhook_raw`
5. Insert fails with unique constraint violation
6. Error propagates up, no rollback handling
7. 500 error returned to Apify
8. Apify retries after delay

## Business Impact

1. **Service Availability**: Webhook endpoint returns 500 errors
2. **Data Loss**: Legitimate webhook data might be lost
3. **Resource Waste**: Multiple retry attempts consume resources
4. **Monitoring Noise**: Error logs filled with duplicate attempts

## Proposed Solutions

### Immediate Fix
1. Wrap the insert in a try-catch for IntegrityError
2. Return success (200/202) for duplicate webhooks
3. Log duplicates as warnings, not errors

### Proper Fix
1. Fix the duplicate detection logic
2. Make webhook processing idempotent
3. Use INSERT ... ON CONFLICT DO NOTHING
4. Add proper transaction boundaries

### Long-term Improvements
1. Implement webhook signature validation
2. Add request deduplication at API gateway level
3. Use a separate deduplication cache (Redis)
4. Implement proper webhook acknowledgment protocol
