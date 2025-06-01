# Gameplan: Fix Article Creation from Apify Webhooks

## Problem Summary

Articles are not being created from Apify webhooks due to:
1. Race condition in duplicate webhook detection causing transaction rollbacks
2. Article creation logic not being reached even for processed webhooks

## Immediate Fix (Track 1)

### 1. Fix Duplicate Detection Race Condition
**File**: `src/local_newsifier/services/apify_webhook_service_sync.py`

**Solution**: Use database-level locking to prevent race conditions

```python
# Option A: Use SELECT FOR UPDATE
existing = self.session.exec(
    select(ApifyWebhookRaw)
    .where(
        ApifyWebhookRaw.run_id == run_id,
        ApifyWebhookRaw.status == status
    )
    .with_for_update(skip_locked=True)
).first()

# Option B: Handle the duplicate at save time only
# Remove the pre-check and rely solely on the unique constraint
```

### 2. Ensure Article Creation Executes
**Problem**: The webhook is being saved but article creation is skipped

**Investigation needed**:
1. Add more logging to understand the flow
2. Check if the session is being rolled back after duplicate detection
3. Verify the dataset_id is being extracted correctly

## Implementation Steps

### Step 1: Add Diagnostic Logging
First, add comprehensive logging to understand the exact flow:

```python
def handle_webhook(self, payload: Dict[str, any], ...):
    # ... existing code ...

    # After status check
    logger.info(f"Status check: status='{status}', is_succeeded={status == 'SUCCEEDED'}")
    logger.info(f"Dataset ID: '{dataset_id}', has_dataset={bool(dataset_id)}")

    # Before article creation
    if status == "SUCCEEDED":
        logger.info("Status is SUCCEEDED, checking for dataset_id")
        if dataset_id:
            logger.info(f"Dataset ID found: {dataset_id}, attempting article creation")
        else:
            logger.info("No dataset ID found")
```

### Step 2: Fix Transaction Handling
The current code has a flaw where duplicate detection and save are in the same transaction:

```python
def handle_webhook(self, payload: Dict[str, any], ...):
    # Use separate transaction for duplicate check
    with self.session.begin_nested():
        existing = self.session.exec(
            select(ApifyWebhookRaw).where(...)
        ).first()

        if existing:
            return {"status": "ok", "message": "Duplicate webhook ignored"}

    # Save webhook in new transaction
    try:
        webhook_raw = ApifyWebhookRaw(...)
        self.session.add(webhook_raw)
        self.session.flush()

        # Process articles if SUCCEEDED
        if status == "SUCCEEDED" and dataset_id:
            articles_created = self._create_articles_from_dataset(dataset_id)

        # Commit everything together
        self.session.commit()

    except IntegrityError as e:
        self.session.rollback()
        if "unique_run_id_status" in str(e):
            # This is OK - another request processed it
            return {"status": "ok", "message": "Webhook already processed"}
        raise
```

### Step 3: Alternative Approach - Idempotent Processing
Make the webhook processing idempotent by checking if articles already exist:

```python
def handle_webhook(self, payload: Dict[str, any], ...):
    # Try to save webhook
    try:
        webhook_raw = ApifyWebhookRaw(...)
        self.session.add(webhook_raw)
        self.session.flush()
        is_new = True
    except IntegrityError:
        self.session.rollback()
        is_new = False
        # Check if articles were already created
        webhook_raw = self.session.exec(
            select(ApifyWebhookRaw).where(
                ApifyWebhookRaw.run_id == run_id,
                ApifyWebhookRaw.status == status
            )
        ).first()

    # Process articles only if new and SUCCEEDED
    articles_created = 0
    if status == "SUCCEEDED" and dataset_id:
        if is_new:
            articles_created = self._create_articles_from_dataset(dataset_id)
            self.session.commit()
        else:
            # Check if articles exist for this dataset
            logger.info("Webhook was duplicate, checking if articles were created")
```

## Testing Plan

1. **Local Testing with Concurrent Webhooks**:
   - Use the fish shell webhook test functions
   - Send multiple SUCCEEDED webhooks simultaneously
   - Verify only one processes and creates articles

2. **Verify Article Creation**:
   - Confirm dataset items are fetched
   - Verify articles are saved to database
   - Check for proper error handling

3. **Production Monitoring**:
   - Deploy with enhanced logging
   - Monitor for successful article creation
   - Track duplicate webhook frequency

## Rollback Plan

If issues persist:
1. Revert to previous webhook handling
2. Process webhooks sequentially using a queue
3. Add manual retry mechanism for failed article creation

## Long-term Improvements

1. **Webhook Queue**: Process webhooks through a queue to avoid race conditions
2. **Separate Article Creation**: Decouple article creation from webhook processing
3. **Better Observability**: Add metrics for webhook processing and article creation
4. **Retry Logic**: Implement automatic retry for failed article creation

## Priority Actions

1. **Immediate**: Add diagnostic logging to understand why article creation is skipped
2. **High**: Fix the transaction/race condition issue
3. **Medium**: Implement idempotent processing
4. **Low**: Add long-term improvements

## Success Criteria

- Webhooks process without race condition errors
- Articles are created from successful Apify runs
- Duplicate webhooks are handled gracefully
- System logs clearly show the processing flow
