# Apify Webhook Article Creation Fix - Gameplan

## Problem Summary

Articles are not being created from Apify webhooks due to a fundamental flaw in the webhook processing logic. The current implementation only creates articles when a webhook is successfully saved (webhook_saved=True), but webhooks for SUCCEEDED status are often duplicates because:

1. Apify may send multiple webhooks for the same run (CREATED, RUNNING, SUCCEEDED)
2. Multiple SUCCEEDED webhooks may arrive simultaneously
3. The unique constraint (run_id + status) prevents duplicate SUCCEEDED webhooks from being saved
4. Since webhook_saved=False for duplicates, article creation is skipped

## Root Cause

The logic at line 136 is flawed:
```python
if webhook_saved and status == "SUCCEEDED" and dataset_id:
```

This means articles are ONLY created for the first SUCCEEDED webhook. If that webhook arrives simultaneously with others (race condition) or if we've already seen a SUCCEEDED webhook for this run, no articles will be created.

## Solution

We need to decouple article creation from webhook storage. Articles should be created for ANY SUCCEEDED webhook with a dataset_id, regardless of whether it's a duplicate.

## Implementation Plan

### Option 1: Check if Articles Already Exist (Recommended)

Modify the webhook handler to:
1. Always attempt article creation for SUCCEEDED webhooks with dataset_id
2. Check if we've already processed this dataset by looking for a processing marker
3. Use a separate table or field to track which datasets have been processed

### Option 2: Always Process Datasets (Simple but Redundant)

Modify the webhook handler to:
1. Remove the `webhook_saved` condition
2. Always call `_create_articles_from_dataset` for SUCCEEDED webhooks
3. Rely on the URL deduplication in article creation to prevent duplicates

### Chosen Approach: Option 2 with Optimization

We'll implement Option 2 because:
- It's simpler and more robust
- The article creation already has URL deduplication
- Processing the same dataset multiple times is idempotent
- We can add a simple cache to avoid redundant API calls

## Code Changes

### 1. Update ApifyWebhookService.handle_webhook()

```python
# Line 134-146: Process dataset for ANY successful run with dataset_id
articles_created = 0
if status == "SUCCEEDED" and dataset_id:
    # Check if we've recently processed this dataset (simple in-memory cache)
    cache_key = f"processed_dataset_{dataset_id}"
    if not hasattr(self, '_processed_datasets'):
        self._processed_datasets = {}

    # Skip if processed in last 5 minutes
    if cache_key in self._processed_datasets:
        last_processed = self._processed_datasets[cache_key]
        if (datetime.now(UTC) - last_processed).total_seconds() < 300:
            logger.info(f"Dataset recently processed, skipping: {dataset_id}")
            return {
                "status": "ok",
                "run_id": run_id,
                "actor_id": actor_id,
                "dataset_id": dataset_id,
                "articles_created": 0,
                "is_new": webhook_saved,
                "message": "Dataset already processed recently",
            }

    try:
        articles_created = self._create_articles_from_dataset(dataset_id)
        self._processed_datasets[cache_key] = datetime.now(UTC)
        logger.info(f"Articles created: dataset_id={dataset_id}, count={articles_created}")
    except Exception as e:
        # Log error but don't fail the webhook
        logger.error(
            f"Failed to create articles: dataset_id={dataset_id}, error={str(e)}",
            exc_info=True,
        )
```

### 2. Add Better Logging

Add more detailed logging to understand what's happening:
- Log when entering article creation
- Log dataset fetch success/failure
- Log each article creation attempt
- Log why articles are skipped

### 3. Add Monitoring

Add a new endpoint or CLI command to:
- Show recent webhook processing history
- Show which datasets have been processed
- Show article creation statistics

## Testing Plan

1. **Unit Tests**: Update tests to verify articles are created even for duplicate webhooks
2. **Integration Test**: Create a test that simulates multiple webhooks for the same run
3. **Manual Testing**:
   - Use the webhook testing Fish functions
   - Send multiple SUCCEEDED webhooks for the same run
   - Verify articles are created

## Rollback Plan

If issues arise:
1. The change is backward compatible
2. Can revert to webhook_saved condition if needed
3. No database migrations required

## Success Criteria

1. Articles are created from Apify datasets when SUCCEEDED webhooks are received
2. Duplicate webhooks don't prevent article creation
3. The same dataset isn't processed multiple times in quick succession
4. All existing functionality continues to work

## Timeline

1. Implement code changes: 30 minutes
2. Update tests: 20 minutes
3. Testing and verification: 20 minutes
4. Create PR and monitor build: 10 minutes

Total: ~1.5 hours
