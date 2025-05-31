# Gameplan: Fix Apify Webhook Payload Processing

## Objective

Fix the Apify webhook handler to correctly process the nested webhook payload structure sent by Apify's production servers.

## Step-by-Step Implementation Plan

### Step 1: Update Webhook Service to Handle Nested Structure

1. Modify `apify_webhook_service_sync.py` to extract fields from the correct nested locations:
   - Extract `actorRunId` from `eventData.actorRunId`
   - Extract `actorId` from `eventData.actorId`
   - Extract `status` from `resource.status`
   - Extract `defaultDatasetId` from `resource.defaultDatasetId`

### Step 2: Simplify Webhook Model

1. Either:
   - Option A: Update `ApifyWebhookPayload` to reflect the actual nested structure
   - Option B: Remove the strict Pydantic model and use a flexible dict approach (recommended)

2. If choosing Option B, remove the model validation from the webhook endpoint and work directly with the dict payload

### Step 3: Update Field Extraction Logic

1. Add helper methods to safely extract nested fields with proper error handling
2. Update the `handle_webhook` method to use these helpers
3. Ensure backward compatibility if needed

### Step 4: Update Tests

1. Update test fixtures to use realistic webhook payloads based on the actual structure
2. Add tests for:
   - Successful webhook processing with nested structure
   - Missing nested fields
   - Malformed payloads
   - Edge cases

### Step 5: Add Logging and Monitoring

1. Add detailed logging for field extraction to help debug future issues
2. Log the full payload structure when fields are missing
3. Consider adding metrics for webhook processing success/failure rates

### Step 6: Deploy and Verify

1. Test locally with the actual production webhook payload
2. Deploy to staging environment
3. Test with real Apify webhooks
4. Monitor logs for any issues
5. Deploy to production

## Implementation Priority

1. **Immediate fix** (Step 1): Update field extraction in `handle_webhook` to unblock production
2. **Follow-up improvements** (Steps 2-5): Refactor for better maintainability
3. **Final verification** (Step 6): Ensure the fix works in production

## Code Changes Summary

### Immediate Fix

```python
# In apify_webhook_service_sync.py, update handle_webhook method:

# Extract from nested structure
event_data = payload.get("eventData", {})
resource = payload.get("resource", {})

run_id = event_data.get("actorRunId", "") or resource.get("id", "")
actor_id = event_data.get("actorId", "") or resource.get("actId", "")
status = resource.get("status", "")
dataset_id = resource.get("defaultDatasetId", "")
```

### Long-term Solution

Consider creating a flexible webhook handler that can adapt to different payload structures without strict model validation.

## Success Criteria

1. Webhook endpoint returns 202 Accepted for valid Apify webhooks
2. Webhook data is correctly saved to the database
3. Articles are created from successful actor runs
4. No 400 Bad Request errors for valid webhooks
5. Comprehensive test coverage for various payload structures

## Risks and Mitigations

1. **Risk**: Apify might change their webhook structure
   - **Mitigation**: Use flexible field extraction with fallbacks

2. **Risk**: Breaking existing integrations
   - **Mitigation**: Ensure backward compatibility or version the endpoint

3. **Risk**: Missing data in nested fields
   - **Mitigation**: Add comprehensive logging and error handling

## Timeline

- Immediate fix: 30 minutes
- Full refactoring: 2-3 hours
- Testing and deployment: 1 hour

Total estimated time: 3-4 hours
