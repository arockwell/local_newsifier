# Gameplan: Fix Apify Webhook Duplicate Detection

## Objective
Fix the webhook duplicate detection to allow multiple webhooks per run (STARTED, SUCCEEDED, etc.) while preventing true duplicates of the same status.

## Solution Approach
Modify duplicate detection to check both `run_id` AND `status` instead of just `run_id`.

## Implementation Steps

### 1. Create Database Migration
- Remove unique constraint on `run_id` in `apify_webhook_raw` table
- Add composite unique constraint on (`run_id`, `status`)
- Create migration file: `alembic/versions/fix_apify_webhook_unique_constraint.py`

### 2. Update Model
- Modify `ApifyWebhookRaw` in `src/local_newsifier/models/apify.py`
- Change from single unique constraint to table-level composite constraint
- Add `__table_args__` with unique constraint definition

### 3. Update Webhook Service
- Modify duplicate check in `src/local_newsifier/services/apify_webhook_service_sync.py`
- Check for existing webhook with same `run_id` AND `status`
- Update logging to include status in duplicate detection messages

### 4. Add Tests
- Test that STARTED and SUCCEEDED webhooks for same run are both accepted
- Test that duplicate SUCCEEDED webhooks are rejected
- Test article creation only occurs for SUCCEEDED status
- Add test cases in `tests/api/test_webhooks.py`

### 5. Update Documentation
- Document the webhook lifecycle (STARTED → SUCCEEDED/FAILED)
- Update `docs/integrations/apify/webhook_processing.md` with status handling details

## Code Changes

### 1. Model Update (models/apify.py)
```python
class ApifyWebhookRaw(TableBase, table=True):
    """Minimal model for storing raw Apify webhook data."""

    __tablename__ = "apify_webhook_raw"

    # Composite unique constraint on run_id + status
    __table_args__ = (
        UniqueConstraint("run_id", "status", name="uq_apify_webhook_raw_run_status"),
        {"extend_existing": True}
    )

    run_id: str = Field(index=True)  # Remove unique=True
    actor_id: str
    status: str
    data: Dict[str, Any] = Field(sa_type=JSON)
```

### 2. Service Update (apify_webhook_service_sync.py)
```python
# Line 119-128 replacement
existing = self.session.exec(
    select(ApifyWebhookRaw).where(
        ApifyWebhookRaw.run_id == run_id,
        ApifyWebhookRaw.status == status
    )
).first()

if existing:
    logger.info(f"Duplicate webhook detected: run_id={run_id}, status={status}, ignoring")
    return {"status": "ok", "message": "Duplicate webhook ignored"}
```

## Testing Strategy
1. Manual testing with webhook test functions
2. Unit tests for duplicate detection logic
3. Integration tests for full webhook flow
4. Verify existing webhooks in database are handled correctly

## Rollback Plan
If issues arise:
1. Revert code changes
2. Restore original unique constraint on run_id
3. Clear any duplicate entries from the database

## Success Criteria
- STARTED webhooks are stored without blocking SUCCEEDED webhooks
- SUCCEEDED webhooks trigger article creation
- True duplicate webhooks (same run_id + status) are properly rejected
- All existing tests continue to pass
- New tests verify the multi-status behavior
