# Apify Webhook Article Creation Debug Report

## Executive Summary

Articles are not being created from Apify webhooks. Initial investigation reveals the webhook processing flow is properly designed but there may be issues with:

1. **Database Configuration**: The ApifyWebhookRaw model lacks a `dataset_id` field, though the service extracts it from the payload JSON
2. **Field Mapping**: The article creation process expects specific field names that may not match what Apify actors return
3. **Content Validation**: Articles require at least 500 characters of content, which may be filtering out valid items

## Current Architecture

### Webhook Flow
1. Apify sends webhook to `/webhooks/apify` endpoint
2. Webhook payload is validated (signature check if configured)
3. Webhook data is stored in `apify_webhook_raw` table (idempotent via unique constraint on run_id + status)
4. If status is "SUCCEEDED" and dataset_id is present, articles are created from the dataset
5. Response is returned with processing status

### Key Components

#### Models
- **ApifyWebhookRaw**: Stores raw webhook data
  - Fields: `run_id`, `actor_id`, `status`, `data` (JSON)
  - Missing: `dataset_id` as a separate field (stored in JSON data)
- **Article**: Core article model
  - Required: `url`, `content`
  - Optional: `title` (recently made optional)
  - Minimum content length: 500 characters

#### Services
- **ApifyWebhookService**: Handles webhook processing
  - Validates signatures
  - Stores webhooks idempotently
  - Creates articles from datasets
- **ApifyService**: Interacts with Apify API
  - Fetches dataset items
  - Manages actor runs

### Article Creation Logic

The service attempts to extract content from multiple fields in order:
1. `text` - Primary field from most actors
2. `markdown` - Alternative format
3. `content` - Legacy/custom actors
4. `body` - Fallback
5. `metadata.description` - Last resort

Articles are skipped if:
- No URL present
- Content length < 500 characters
- Article with same URL already exists

## Identified Issues

### 1. Field Mapping Mismatch
Different Apify actors output different field structures. The current mapping may not cover all cases.

### 2. Content Length Threshold
The 500-character minimum may be too restrictive, filtering out valid articles that are shorter but still valuable.

### 3. Missing Observability
While the webhook endpoint logs the full payload, there's limited visibility into:
- Which webhooks have been received
- Which datasets have been processed
- Why specific articles were skipped

### 4. Database Access
The webhook data is stored but there's no easy way to query it to understand patterns or failures.

## Debug Tools Available

1. **API Debug Endpoint**: `/webhooks/apify/debug/{dataset_id}`
   - Analyzes dataset contents
   - Shows why articles would/wouldn't be created
   - Provides field analysis and recommendations

2. **CLI Commands**:
   - `nf apify debug-dataset <dataset_id>`: Debug dataset processing
   - `nf apify process-dataset <dataset_id>`: Manually process a dataset
   - `nf apify get-dataset <dataset_id>`: View dataset contents

## Recommendations for Investigation

1. **Check Recent Webhooks**: Query the database for recent webhook data to see if webhooks are being received and stored correctly

2. **Analyze Dataset Structure**: Use the debug endpoint with a known dataset ID to understand the actual field structure being returned

3. **Review Actor Configuration**: Ensure Apify actors are configured to output the expected fields (url, title, text/content)

4. **Monitor Logs**: Check application logs for webhook processing errors or dataset fetch failures

5. **Test Manual Processing**: Use `nf apify process-dataset` to manually process a known good dataset and observe the results

## Next Steps

1. Query production database for webhook data patterns
2. Use debug tools to analyze a sample dataset
3. Review Apify actor configurations
4. Implement fixes based on findings
5. Add better monitoring and logging for future debugging
