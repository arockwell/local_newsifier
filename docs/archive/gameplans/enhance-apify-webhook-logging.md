# GAMEPLAN: Enhance Apify Webhook Logging

## Objective
Add comprehensive logging throughout the Apify webhook processing flow to make it easier to track what's happening at each step, aid in debugging, and provide better visibility into the webhook lifecycle.

## Current State
- Basic error logging exists
- Limited visibility into successful processing steps
- Difficult to trace webhook flow without database queries
- Missing detailed information about data transformations

## Proposed Enhancements

### 1. Webhook Receipt Logging
**File**: `src/local_newsifier/api/routers/webhooks.py`

Add logging for:
- [x] Incoming webhook with run_id and actor_id
- [x] Signature validation attempt and result
- [x] Request headers (for debugging)
- [x] Response status and article count

### 2. Webhook Service Processing
**File**: `src/local_newsifier/services/apify_webhook_service_sync.py`

Add detailed logging for:
- [x] Payload extraction with extracted values
- [x] Duplicate check result
- [x] Raw webhook storage confirmation
- [x] Dataset fetch attempt and item count
- [x] Article creation progress (X of Y created)
- [x] Skipped items with reasons (missing fields, short content, duplicates)

### 3. Article Creation Details
**File**: `src/local_newsifier/services/apify_webhook_service_sync.py`

Log for each article:
- [x] URL being processed
- [x] Content length and validation result
- [x] Duplicate check result
- [x] Successful creation with article ID
- [x] Field extraction fallbacks used

### 4. Error Context Enhancement
Add more context to error logs:
- [x] Include run_id in all error messages
- [x] Log full exception stack traces
- [x] Include webhook payload in error scenarios
- [x] Log Apify API errors with response details

### 5. Performance Metrics
Add timing logs:
- [x] Total webhook processing time
- [x] Dataset fetch duration
- [x] Article creation batch time
- [x] Database query durations

## Implementation Steps

### Phase 1: Basic Flow Logging
1. Add entry/exit logs for main functions
2. Log key decision points (duplicate found, status check)
3. Add summary log at end of processing

### Phase 2: Detailed Data Logging
1. Log extracted field values
2. Add progress indicators for batch operations
3. Include data validation results

### Phase 3: Enhanced Error Handling
1. Wrap all operations in try/catch with specific error logging
2. Add context to all error messages
3. Log warnings for non-critical issues

### Phase 4: Metrics and Monitoring
1. Add timing measurements
2. Log performance metrics
3. Create log patterns for monitoring tools

## Log Format Standards

### Success Flow
```
INFO: Webhook received: run_id=abc123, actor_id=xyz789, status=SUCCEEDED
INFO: Signature validation: valid=True
INFO: Checking for duplicate webhook: run_id=abc123
INFO: Webhook not duplicate, proceeding with processing
INFO: Storing raw webhook data: run_id=abc123
INFO: Fetching dataset: dataset_id=dataset123
INFO: Dataset items received: count=10
INFO: Processing article 1/10: url=https://example.com/article1
INFO: Article created: id=456, url=https://example.com/article1
INFO: Processing article 2/10: url=https://example.com/article2
INFO: Skipping article: url=https://example.com/article2, reason=duplicate_url
INFO: Webhook processing complete: run_id=abc123, articles_created=8/10, duration=2.5s
```

### Error Flow
```
ERROR: Webhook processing failed: run_id=abc123, error=Dataset fetch failed
ERROR: Apify API error: status=404, message=Dataset not found, dataset_id=dataset123
ERROR: Full traceback: [stack trace]
ERROR: Webhook data saved but articles not created: run_id=abc123
```

## Benefits
1. **Debugging**: Easy to trace exact processing path
2. **Monitoring**: Clear patterns for alerting
3. **Audit Trail**: Complete record of webhook handling
4. **Performance**: Identify bottlenecks
5. **User Support**: Quickly diagnose issues

## Testing Plan
1. Test with successful webhook - verify all success logs
2. Test with duplicate webhook - verify duplicate detection logs
3. Test with failed actor run - verify status handling logs
4. Test with API errors - verify error context logs
5. Test with invalid data - verify validation logs

## Success Criteria
- [x] Can trace complete webhook flow from logs alone
- [x] All errors include sufficient context for debugging
- [x] Performance bottlenecks are measurable
- [x] Log volume is reasonable (not excessive)
- [x] Logs follow consistent format

## Implementation Status

✅ **Completed on 2025-05-31**

All logging enhancements have been successfully implemented:

1. **Webhook Receipt Logging**: The webhook router now logs incoming webhooks with full context including run_id, actor_id, status, signature validation attempts, and sanitized request headers.

2. **Service Processing Logging**: The webhook service logs detailed information about payload extraction, duplicate checks, raw data storage, and processing decisions.

3. **Article Creation Logging**: Full progress tracking with detailed skip reasons, content validation, and creation confirmations including article IDs.

4. **Error Context**: All errors now include run_id, full stack traces, webhook payloads on error, and specific Apify API error details when available.

5. **Performance Metrics**: Complete timing information for webhook processing, database operations, dataset fetching, and article creation batches.

The logging follows the specified format standards and provides comprehensive visibility into the webhook processing lifecycle.

## Future Enhancements
- Structured logging (JSON format)
- Log aggregation dashboard
- Automated alerting rules
- Webhook processing metrics dashboard
