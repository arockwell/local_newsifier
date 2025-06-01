# Apify Webhook Simplification Plan

## Overview

This document outlines the changes made to simplify the Apify webhook implementation based on the complexity analysis.

## Key Changes

### 1. Simplified Duplicate Detection

**Before:**
- Pre-checked for duplicates with a SELECT query
- Then tried to INSERT and caught IntegrityError
- Complex error handling with session rollback and re-checking

**After:**
- Simply try to INSERT
- Let the database unique constraint handle duplicates
- Catch IntegrityError and continue (truly idempotent)

### 2. Clean Session Management

**Before:**
- Session passed through dependency injection
- Complex rollback handling
- Session state could become corrupted

**After:**
- Fresh session for each webhook
- Simple commit/rollback pattern
- Let FastAPI handle session cleanup

### 3. Simplified Payload Extraction

**Before:**
- Checked multiple nested locations for fields
- Complex fallback logic between eventData and resource
- Excessive logging for debugging

**After:**
- Extract from standard `resource` object only
- Simple field extraction
- Only log essential information

### 4. Proper HTTP Status Codes

**Before:**
- Always returned 200 OK to "prevent retry storms"
- Errors were hidden from Apify

**After:**
- Return 202 Accepted for successful webhooks
- Return 400 Bad Request for invalid webhooks
- Let Apify's exponential backoff handle retries naturally

### 5. Simplified Article Creation

**Before:**
- Complex skip logic with detailed tracking
- Multiple validation steps
- Excessive logging

**After:**
- Simple loop through dataset items
- Skip if missing fields or duplicate URL
- Create articles in bulk, commit once

## Files Created

1. **`src/local_newsifier/services/apify_webhook_service_simple.py`**
   - Simplified webhook service implementation
   - ~200 lines vs ~377 lines (47% reduction)
   - Clear, focused methods

2. **`src/local_newsifier/api/routers/webhooks_simple.py`**
   - Simplified webhook endpoint
   - ~100 lines vs ~145 lines (31% reduction)
   - Proper HTTP status codes

## Migration Steps

1. **Testing Phase:**
   - Deploy both old and new endpoints side by side
   - Route a percentage of webhooks to new endpoint
   - Monitor for issues

2. **Gradual Rollout:**
   - Update webhook URL in Apify to use new endpoint
   - Monitor logs for any issues
   - Keep old endpoint available as fallback

3. **Cleanup:**
   - Remove old webhook implementation
   - Remove excessive logging
   - Update documentation

## Benefits

1. **Reliability:**
   - True idempotency via database constraints
   - No race conditions
   - Clean error handling

2. **Performance:**
   - Fewer database queries
   - Bulk article creation
   - Less logging overhead

3. **Maintainability:**
   - 40% less code
   - Clear, simple logic
   - Easy to debug

4. **Proper Integration:**
   - Works with Apify's retry mechanism
   - Standard HTTP status codes
   - Clear error messages

## Testing

The simplified webhook can be tested with:

```bash
# Test successful webhook
curl -X POST http://localhost:8000/webhooks/apify \
  -H "Content-Type: application/json" \
  -d '{
    "resource": {
      "id": "test-run-123",
      "actId": "test-actor",
      "status": "SUCCEEDED",
      "defaultDatasetId": "test-dataset"
    }
  }'

# Test duplicate webhook (run twice)
curl -X POST http://localhost:8000/webhooks/apify \
  -H "Content-Type: application/json" \
  -d '{
    "resource": {
      "id": "test-run-456",
      "actId": "test-actor",
      "status": "SUCCEEDED"
    }
  }'
```

## Next Steps

1. Add comprehensive tests for the new implementation
2. Deploy to staging environment
3. Run side-by-side comparison
4. Gradually migrate traffic
5. Remove old implementation
