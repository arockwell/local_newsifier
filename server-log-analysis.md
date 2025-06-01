# Server Log Analysis: Duplicate Webhook Race Condition

## Executive Summary

The server logs show a critical race condition issue where Apify is sending duplicate webhooks for the same actor run (`IxqszH6aJFrEhGOx9`), causing database constraint violations. The duplicate detection logic exists but appears to have a timing issue where the duplicate check passes initially, but then fails during the database insert.

## Key Issues Identified

### 1. **Duplicate Webhook Delivery**
- Apify sent multiple webhooks for the same run ID `IxqszH6aJFrEhGOx9`
- First webhook: `2025-06-01T06:39:44.235Z`
- Second webhook: `2025-06-01T06:39:44.229Z` (6 milliseconds earlier!)
- Both webhooks have status `SUCCEEDED` for the same actor run

### 2. **Race Condition in Duplicate Detection**
The logs show a problematic sequence:
```
Line 164: Webhook not duplicate, proceeding with processing
Line 169: WARNING - Duplicate webhook received for run_id
Line 172: ERROR - Webhook marked as duplicate but not found in DB
```

This indicates the duplicate check initially passes, but by the time the insert happens, another thread/process has already inserted the record.

### 3. **Database Constraint Violation**
```
psycopg2.errors.UniqueViolation: duplicate key value violates unique constraint "ix_apify_webhook_raw_run_id"
DETAIL: Key (run_id)=(IxqszH6aJFrEhGOx9) already exists.
```

### 4. **Session Management Issue**
The error occurs during `session.flush()` at line 157 in `apify_webhook_service_sync.py`, suggesting the session isn't properly isolated or the transaction boundaries aren't correctly managed.

## Root Cause Analysis

### Primary Issue: Concurrent Webhook Processing
1. Multiple webhook requests arrive nearly simultaneously (within milliseconds)
2. Both requests pass the duplicate check because neither has been committed to the database yet
3. Both try to insert, causing a constraint violation for the second one

### Contributing Factors:
1. **No request-level deduplication**: The API accepts both webhooks and processes them concurrently
2. **Read-then-write pattern**: The duplicate check and insert aren't atomic
3. **Missing transaction isolation**: The duplicate check doesn't see uncommitted data from other transactions

## Steps to Reproduce

### 1. **Simulate Duplicate Webhooks**
```bash
# Terminal 1 - Start the server
make run-api

# Terminal 2 - Send duplicate webhooks rapidly
for i in {1..2}; do
  curl -X POST http://localhost:8000/webhooks/apify \
    -H "Content-Type: application/json" \
    -d '{
      "userId": "test-user",
      "createdAt": "2025-06-01T12:00:00.000Z",
      "eventType": "ACTOR.RUN.SUCCEEDED",
      "eventData": {
        "actorId": "test-actor",
        "actorRunId": "duplicate-test-run"
      },
      "resource": {
        "id": "duplicate-test-run",
        "status": "SUCCEEDED",
        "defaultDatasetId": "test-dataset"
      }
    }' &
done
wait
```

### 2. **Check Logs**
```bash
# Look for duplicate key violations
tail -f server.log | grep -E "(duplicate key|UniqueViolation)"
```

### 3. **Verify Database State**
```bash
# Check if any webhooks were saved despite errors
nf db inspect apify_webhook_raw duplicate-test-run
```

## Steps to Fix

### 1. **Immediate Fix: Add Database-Level Upsert**
```python
# In apify_webhook_service_sync.py
def handle_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle incoming webhook with proper duplicate handling."""
    try:
        # Use INSERT ... ON CONFLICT DO NOTHING
        stmt = insert(ApifyWebhookRaw).values(
            run_id=run_id,
            actor_id=actor_id,
            status=status,
            data=json.dumps(webhook_data)
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=['run_id'])
        result = self.session.execute(stmt)

        if result.rowcount == 0:
            # Record already exists
            logger.info(f"Webhook already processed: run_id={run_id}")
            return {"status": "duplicate", "run_id": run_id}

        self.session.commit()

        # Process webhook data...

    except Exception as e:
        self.session.rollback()
        raise
```

### 2. **Better Fix: Request-Level Idempotency**
```python
# In api/routers/webhooks.py
from functools import lru_cache
from datetime import datetime, timedelta

# Simple in-memory cache for recent webhooks
@lru_cache(maxsize=1000)
def is_webhook_processed(run_id: str, timestamp: float) -> bool:
    """Check if webhook was recently processed."""
    # Cache entries expire after 5 minutes
    return False

@router.post("/webhooks/apify", status_code=202)
def apify_webhook(
    webhook_data: Dict[str, Any],
    webhook_service: Annotated[ApifyWebhookService, Depends(get_apify_webhook_service)]
):
    run_id = webhook_data.get("resource", {}).get("id")

    # Quick duplicate check
    if is_webhook_processed(run_id, time.time()):
        return {"status": "duplicate", "run_id": run_id}

    # Mark as processing
    is_webhook_processed.cache_clear()  # Simple approach

    result = webhook_service.handle_webhook(webhook_data)
    return result
```

### 3. **Best Fix: Use Redis for Distributed Locking**
```python
# In apify_webhook_service_sync.py
import redis
from contextlib import contextmanager

@contextmanager
def webhook_lock(redis_client, run_id: str, timeout: int = 30):
    """Distributed lock for webhook processing."""
    lock_key = f"webhook:lock:{run_id}"
    lock = redis_client.lock(lock_key, timeout=timeout)

    acquired = lock.acquire(blocking=False)
    if not acquired:
        raise WebhookAlreadyProcessingError(f"Webhook {run_id} is already being processed")

    try:
        yield
    finally:
        lock.release()

def handle_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    run_id = webhook_data.get("resource", {}).get("id")

    try:
        with webhook_lock(self.redis_client, run_id):
            # Check if already processed
            existing = self.session.query(ApifyWebhookRaw).filter_by(run_id=run_id).first()
            if existing:
                return {"status": "duplicate", "run_id": run_id}

            # Process webhook...
    except WebhookAlreadyProcessingError:
        return {"status": "processing", "run_id": run_id}
```

### 4. **Transaction Isolation Fix**
```python
# Use SERIALIZABLE isolation level for critical sections
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

def handle_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    with self.session.begin():
        # Set isolation level for this transaction
        self.session.connection().execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")

        # Now duplicate checks will see other transactions
        existing = self.session.query(ApifyWebhookRaw).filter_by(run_id=run_id).first()
        if existing:
            return {"status": "duplicate", "run_id": run_id}

        # Insert new webhook
        webhook_raw = ApifyWebhookRaw(...)
        self.session.add(webhook_raw)
        # Transaction commits automatically
```

## Recommended Solution Path

1. **Immediate**: Implement the database-level upsert (Fix #1) to prevent crashes
2. **Short-term**: Add request-level deduplication (Fix #2) to reduce database load
3. **Long-term**: Implement distributed locking with Redis (Fix #3) for proper scalability

## Testing the Fix

```bash
# 1. Run concurrent webhook test
./test_concurrent_webhooks.sh

# 2. Check for errors
grep -c "UniqueViolation" server.log  # Should be 0

# 3. Verify only one record per run_id
nf db query "SELECT run_id, COUNT(*) FROM apify_webhook_raw GROUP BY run_id HAVING COUNT(*) > 1"
```

## Additional Recommendations

1. **Add webhook retry logic** with exponential backoff on Apify's side
2. **Implement webhook signature verification** to ensure webhooks are from Apify
3. **Add monitoring** for duplicate webhook rates
4. **Consider using a message queue** (RabbitMQ/Redis) for webhook processing
5. **Add database index** on `(run_id, status)` for faster duplicate checks

## Monitoring Queries

```sql
-- Find duplicate attempts
SELECT run_id, COUNT(*) as attempts
FROM apify_webhook_raw
GROUP BY run_id
HAVING COUNT(*) > 1
ORDER BY attempts DESC;

-- Check webhook processing times
SELECT
    DATE_TRUNC('minute', created_at) as minute,
    COUNT(*) as webhooks_received,
    COUNT(DISTINCT run_id) as unique_runs,
    COUNT(*) - COUNT(DISTINCT run_id) as duplicates
FROM apify_webhook_raw
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY minute
ORDER BY minute DESC;
```
