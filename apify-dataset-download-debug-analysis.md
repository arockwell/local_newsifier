# Apify Dataset Download Debug Analysis

## Current Problem

The Apify webhook system is receiving webhook notifications but failing to download and process datasets. Based on the codebase analysis and server logs, the key issues are:

1. **Dataset fetch is never attempted** - The webhook handler receives the dataset ID but never calls the dataset download code
2. **No error logging** - When dataset download fails, errors are caught but not properly surfaced
3. **Limited debugging visibility** - No way to test dataset download independently of webhook processing

## Root Cause Analysis

### 1. Silent Failures in Dataset Download
From `apify_webhook_service.py:_create_articles_from_dataset()`:
```python
try:
    # Fetch dataset items
    logger.info(f"Fetching dataset: {dataset_id}")
    dataset_items = self.apify_service.client.dataset(dataset_id).list_items().items
    # ...
except Exception as e:
    logger.error(f"Error processing dataset {dataset_id}: {str(e)}", exc_info=True)
    return 0
```

The error is logged but the webhook still returns success, making it hard to diagnose failures.

### 2. Authentication Issues
The dataset download requires proper Apify authentication, but:
- The webhook handler might not have the correct token
- Token validation happens late in the process
- No way to test authentication separately

### 3. Dataset Access Timing
Apify datasets might not be immediately available when the webhook fires:
- Dataset might still be processing
- Access permissions might not be set correctly
- Dataset might be private/restricted

## Proposed Solution: Debug Endpoint & CLI Command

### Benefits of a Debug Endpoint

1. **Direct Testing** - Test dataset download without webhook complexity
2. **Better Error Visibility** - Return detailed error information
3. **Authentication Testing** - Verify token works for dataset access
4. **Manual Retry** - Allow manual retries for failed webhooks
5. **Development Aid** - Easier to debug during development

### Implementation Approach

1. **New API Endpoint**: `/debug/download-dataset/{dataset_id}`
   - Accepts dataset ID
   - Returns detailed status and any errors
   - Shows step-by-step progress
   - Returns created articles or failure reason

2. **New CLI Command**: `nf apify download-dataset <dataset_id>`
   - Calls the debug endpoint
   - Shows detailed progress
   - Useful for manual testing and recovery

3. **Enhanced Error Handling**
   - Return specific error types (auth, not found, parsing, etc.)
   - Include Apify API error responses
   - Log full stack traces for debugging

4. **Dataset Processing Improvements**
   - Add retry logic for temporary failures
   - Validate dataset structure before processing
   - Better field mapping for different actor outputs
   - Progress tracking for large datasets

### Why This Will Help

1. **Immediate Diagnosis** - Can test specific dataset IDs that failed
2. **Webhook Independence** - Debug without webhook complexity
3. **Manual Recovery** - Process missed datasets manually
4. **Better Monitoring** - See exactly where the process fails
5. **Development Speed** - Faster iteration on fixes

## Alternative Approaches Considered

1. **Enhanced Logging Only** - Not sufficient, need interactive testing
2. **Webhook Replay** - Too complex, doesn't isolate the issue
3. **Direct Apify Client Testing** - Doesn't test our processing logic
4. **Database Inspection** - Doesn't help with download failures

## Conclusion

Creating a debug endpoint for dataset downloading will:
- Provide immediate visibility into failures
- Allow manual recovery of failed webhooks
- Speed up development and debugging
- Improve system reliability

This approach isolates the dataset download functionality, making it easier to test, debug, and maintain.
