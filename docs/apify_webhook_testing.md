# Apify Webhook Testing Guide

## Overview

This guide provides instructions for setting up, testing, and troubleshooting the Apify webhook integration with Local Newsifier. The webhook system allows Apify to notify your application when web scraping jobs complete, enabling automatic article creation and processing.

## Prerequisites

Before testing webhooks, ensure you have:

1. A working Local Newsifier deployment with webhook endpoint enabled
2. An Apify account with API token configured
3. At least one configured Apify actor that extracts content

## Setting Up Webhooks in Apify

### 1. Create a Webhook in Apify UI

1. Log in to your [Apify Console](https://console.apify.com)
2. Navigate to **Webhooks** in the left sidebar
3. Click **Create new webhook**
4. Configure the webhook with these settings:
   - **Name**: Local Newsifier Integration
   - **URL**: `https://your-deployment-url.com/api/webhooks/apify`
   - **Event types**: Select "Actor run succeeded" (optionally also "Actor run failed" for error handling)
   - **Secret**: Create a random string to use as a shared secret (must match your APIFY_WEBHOOK_SECRET environment variable)

### 2. Configure Environment Variables

Ensure your Local Newsifier deployment has these environment variables set:

```
APIFY_TOKEN=your_api_token
APIFY_WEBHOOK_SECRET=your_shared_webhook_secret
```

## Testing the Webhook Flow

### Method 1: Test with Real Apify Run

1. **Configure an Apify Source**:
   ```bash
   # Add a test source configuration
   nf apify-config add --name "Test Source" --url "https://example.com" --actor "apify/website-content-crawler"
   ```

2. **Run the Actor Manually**:
   ```bash
   # Get the config ID first
   nf apify-config list

   # Run the actor for a specific configuration
   nf apify-config run <config_id>
   ```

3. **Monitor the Webhook**:
   - Check your application logs for webhook receipt
   - Verify the webhook signature validation succeeds
   - Confirm dataset items are retrieved and processed

### Method 2: Simulate a Webhook Call

You can use tools like curl to simulate a webhook call from Apify:

```bash
# Generate a signature for testing
SIGNATURE=$(echo -n '{"data":{"id":"test_run_id","actorId":"apify/website-content-crawler","defaultDatasetId":"test_dataset_id"}}' | \
  openssl dgst -sha256 -hmac "your_webhook_secret" | awk '{print $2}')

# Send a test webhook payload
curl -X POST \
  https://your-deployment-url.com/api/webhooks/apify \
  -H "Content-Type: application/json" \
  -H "X-Apify-Webhook-Secret: $SIGNATURE" \
  -d '{"data":{"id":"test_run_id","actorId":"apify/website-content-crawler","defaultDatasetId":"test_dataset_id"}}'
```

### Method 3: Use the Test Endpoint

Local Newsifier provides a test endpoint for validating webhook processing without requiring actual Apify runs:

```bash
# Trigger test processing with a sample dataset
curl -X POST \
  https://your-deployment-url.com/api/webhooks/apify/test \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_key" \
  -d '{"datasetId":"test_dataset_id"}'
```

## Verifying Successful Processing

After a webhook is received, confirm:

1. **Dataset Retrieval**:
   - Check logs for successful dataset item retrieval
   - Verify item counts match expected values

2. **Article Creation**:
   - Confirm articles are created in the database
   - Check for correct metadata (URL, title, publication date)

3. **Entity Processing**:
   - Verify entities are extracted from article content
   - Check entity relationships are created

4. **Error Handling**:
   - Test with malformed data to ensure robust error handling
   - Verify failed items don't block processing of valid items

## Monitoring and Debugging

### Logging

Enable detailed logging to track webhook processing:

```bash
# Set enhanced logging for webhook processing
export LOG_LEVEL=DEBUG
```

Key logging events to monitor:

- Webhook receipt and signature validation
- Dataset item retrieval
- Content transformation
- Article creation and processing

### Database Inspection

Examine the database to verify processing:

```bash
# Check for created articles
nf db articles --source "apify" --limit 10

# Inspect specific article processing
nf db inspect articles <article_id>
```

### Common Issues and Solutions

1. **Webhook Not Received**:
   - Verify network connectivity and firewall rules
   - Check webhook URL matches your application's endpoint
   - Ensure your deployment is accessible from the internet

2. **Signature Validation Failures**:
   - Confirm APIFY_WEBHOOK_SECRET matches the secret in Apify UI
   - Check for URL encoding or whitespace issues in the secret
   - Verify payload is not modified in transit

3. **Empty Dataset**:
   - Review Apify actor run results for content extraction issues
   - Check actor configuration (selectors, start URLs)
   - Inspect the target website for structural changes

4. **Duplicate Content**:
   - Verify URL normalization is working correctly
   - Check for issues with article uniqueness detection
   - Review deduplication logic in the webhook handler

## Production Readiness Checklist

Before relying on webhooks in production:

- [ ] Test webhooks with all configured actor types
- [ ] Verify error handling for various failure scenarios
- [ ] Implement monitoring for webhook processing success/failure
- [ ] Configure appropriate timeouts for dataset processing
- [ ] Set up alerts for processing failures
- [ ] Document recovery procedures for webhook processing issues
- [ ] Test performance with large datasets

## Advanced Configuration

### Rate Limiting

For high-volume sources, configure rate limiting:

```
# Maximum webhook processing concurrency
APIFY_WEBHOOK_MAX_CONCURRENCY=5

# Dataset item processing batch size
APIFY_DATASET_BATCH_SIZE=100
```

### Processing Priorities

Configure processing priority for different sources:

```
# Priority configuration (higher number = higher priority)
APIFY_SOURCE_PRIORITIES={"critical-source": 10, "standard-source": 5}
```

## Security Considerations

- Webhook secrets should be treated as sensitive credentials
- Periodically rotate webhook secrets for enhanced security
- Validate all incoming data before processing
- Implement rate limiting to prevent abuse
- Consider IP whitelisting for additional security
