# Gameplan: Fix Duplicate Key Violation in Apify Webhook Processing

## Objective
Fix the duplicate key constraint violation error that occurs when Apify sends multiple webhook notifications for the same run ID.

## Priority: CRITICAL
This issue is causing production errors and preventing webhook processing.

## Implementation Steps

### Phase 1: Immediate Hotfix (1-2 hours)

1. **Update `apify_webhook_service_sync.py`**
   - Wrap the raw webhook insert in proper error handling
   - Catch `IntegrityError` specifically
   - Return success for duplicates to stop Apify retries

```python
# In handle_webhook method
try:
    raw_webhook = ApifyWebhookRaw(
        run_id=payload.run_id,
        actor_id=payload.actor_id,
        status=payload.status,
        data=webhook_data.model_dump_json()
    )
    self.session.add(raw_webhook)
    self.session.flush()  # Force the constraint check
except IntegrityError as e:
    if "ix_apify_webhook_raw_run_id" in str(e):
        self.session.rollback()
        logger.warning(f"Duplicate webhook received for run_id: {payload.run_id}")
        # Return success to prevent Apify retries
        return {
            "status": "duplicate",
            "message": "Webhook already processed",
            "run_id": payload.run_id
        }
    raise  # Re-raise other integrity errors
```

2. **Update webhook endpoint to handle duplicates**
   - Return 200 OK for duplicate webhooks
   - Log as info/warning, not error

### Phase 2: Fix Duplicate Detection (2-3 hours)

1. **Fix the duplicate check logic**
   - Identify why current check is failing
   - Ensure it queries the correct table
   - Make it consistent with the insert

```python
def _is_duplicate_webhook(self, run_id: str) -> bool:
    """Check if webhook for this run_id already exists."""
    exists = self.session.query(
        exists().where(ApifyWebhookRaw.run_id == run_id)
    ).scalar()
    return exists
```

2. **Add proper transaction boundaries**
   - Ensure duplicate check and insert are in same transaction
   - Use SELECT FOR UPDATE if needed

### Phase 3: Implement Idempotent Processing (4-6 hours)

1. **Use INSERT ... ON CONFLICT**
   ```sql
   INSERT INTO apify_webhook_raw (run_id, actor_id, status, data, created_at, updated_at)
   VALUES (?, ?, ?, ?, ?, ?)
   ON CONFLICT (run_id) DO UPDATE SET
       updated_at = EXCLUDED.updated_at,
       status = EXCLUDED.status
   RETURNING id, (xmax = 0) as inserted;
   ```

2. **Separate webhook receipt from processing**
   - Store raw webhook immediately (idempotent)
   - Process asynchronously
   - Track processing status separately

3. **Add webhook event type handling**
   - Different handling for SUCCEEDED, FAILED, etc.
   - Allow status updates for same run_id

### Phase 4: Testing (2-3 hours)

1. **Unit Tests**
   - Test duplicate webhook handling
   - Test race conditions
   - Test error scenarios

2. **Integration Tests**
   - Test with actual Apify webhooks
   - Test retry scenarios
   - Load test for race conditions

3. **Manual Testing**
   - Use webhook testing functions
   - Verify Apify stops retrying
   - Monitor logs for issues

### Phase 5: Deployment (1 hour)

1. **Pre-deployment**
   - Review all changes
   - Ensure rollback plan
   - Notify team

2. **Deploy**
   - Deploy to staging first
   - Test with real webhooks
   - Deploy to production

3. **Post-deployment**
   - Monitor error logs
   - Verify webhooks processing
   - Check for retry storms

## Success Criteria

1. No more duplicate key violations in logs
2. Apify webhooks process successfully
3. Duplicate webhooks handled gracefully
4. No 500 errors for duplicate webhooks
5. Proper logging of duplicate attempts

## Rollback Plan

If issues arise:
1. Revert code changes
2. Clear any stuck webhooks
3. Manually process failed webhooks
4. Investigate and fix issues

## Long-term Recommendations

1. **Webhook Signature Validation**
   - Verify webhooks are from Apify
   - Prevent replay attacks

2. **Redis Deduplication**
   - Fast duplicate detection
   - TTL-based cleanup

3. **Event Sourcing**
   - Store all webhook events
   - Process idempotently
   - Full audit trail

4. **API Gateway Rate Limiting**
   - Prevent webhook storms
   - Per-client rate limits
