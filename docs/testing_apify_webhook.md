# Testing Apify Webhook Integration

This document provides instructions for testing the Apify webhook integration, which receives notifications from Apify when scraping jobs are completed and processes the resulting datasets.

## Setting Up Local Testing Environment

### Prerequisites
- Local development environment set up according to `docs/python_setup.md`
- PostgreSQL database initialized
- Required environment variables set (particularly `APIFY_WEBHOOK_SECRET`)

## Running the FastAPI Server Locally

Run the following commands to start the FastAPI server:

```bash
cd /Users/alexrockwell/dev/cursor8/local_newsifier
export APIFY_WEBHOOK_SECRET="test_webhook_secret"
uvicorn src.local_newsifier.api.main:app --reload --port 8000
```

The server will start and listen on port 8000. The `--reload` flag ensures the server restarts automatically when code changes are detected.

## Testing with Curl

You can simulate Apify webhook calls using curl. Here are some examples:

### Success Case (RUN.SUCCEEDED with Valid Secret)

```bash
curl -X POST http://localhost:8000/api/webhooks/apify \
  -H "Content-Type: application/json" \
  -H "x-apify-webhook-secret: test_webhook_secret" \
  -d '{
    "createdAt": "2023-05-14T10:00:00.000Z",
    "eventType": "RUN.SUCCEEDED",
    "userId": "test_user",
    "webhookId": "test_webhook_123",
    "actorId": "test_actor",
    "actorRunId": "test_run_123",
    "datasetId": "test_dataset_123"
  }'
```

This should return a 202 Accepted response with a message confirming the webhook was received.

### Security Validation: Missing Secret Header (Should Fail)

```bash
curl -X POST http://localhost:8000/api/webhooks/apify \
  -H "Content-Type: application/json" \
  -d '{
    "createdAt": "2023-05-14T10:00:00.000Z",
    "eventType": "RUN.SUCCEEDED",
    "userId": "test_user",
    "webhookId": "test_webhook_123",
    "actorId": "test_actor", 
    "actorRunId": "test_run_123",
    "datasetId": "test_dataset_123"
  }'
```

This should return a 401 Unauthorized response since the secret header is missing.

### Security Validation: Invalid Secret Header (Should Fail)

```bash
curl -X POST http://localhost:8000/api/webhooks/apify \
  -H "Content-Type: application/json" \
  -H "x-apify-webhook-secret: wrong_secret" \
  -d '{
    "createdAt": "2023-05-14T10:00:00.000Z",
    "eventType": "RUN.SUCCEEDED",
    "userId": "test_user",
    "webhookId": "test_webhook_123",
    "actorId": "test_actor",
    "actorRunId": "test_run_123",
    "datasetId": "test_dataset_123"
  }'
```

This should return a 401 Unauthorized response due to an invalid secret.

### Event Filtering: Non-Succeeded Event (Should Be Ignored)

```bash
curl -X POST http://localhost:8000/api/webhooks/apify \
  -H "Content-Type: application/json" \
  -H "x-apify-webhook-secret: test_webhook_secret" \
  -d '{
    "createdAt": "2023-05-14T10:00:00.000Z",
    "eventType": "RUN.FAILED",
    "userId": "test_user",
    "webhookId": "test_webhook_123",
    "actorId": "test_actor",
    "actorRunId": "test_run_123",
    "datasetId": "test_dataset_123"
  }'
```

This should return a 202 Accepted response, but the webhook will not be processed (as indicated in the response message).

## Verifying Processing

### Check Server Logs

Look for the following indicators in the server logs:

1. Webhook reception confirmation
2. Security validation success/failure logs
3. Dataset processing steps
4. Article creation confirmations

### Inspect Database Records

Use the Local Newsifier CLI to inspect created database records:

```bash
cd /Users/alexrockwell/dev/cursor8/local_newsifier

# Check ApifyJob records
python -m local_newsifier.cli.main db inspect apify_jobs

# Check dataset items
python -m local_newsifier.cli.main db inspect apify_dataset_items

# Check created articles
python -m local_newsifier.cli.main db articles --limit 10
```

## Automated Testing

The project includes automated tests for the webhook functionality:

```bash
cd /Users/alexrockwell/dev/cursor8/local_newsifier
pytest tests/api/test_webhooks.py -v
```

The tests verify:
1. Security validation (with/without secret header)
2. Event type filtering
3. Dataset ID requirement
4. Successful webhook processing

## Setting Up a Real Apify Webhook

To configure a real webhook in the Apify UI:

1. Go to your Apify account
2. Navigate to Actor settings or Task settings
3. Go to the Webhooks section
4. Add a new webhook with:
   - URL: `https://yourdomain.com/api/webhooks/apify`
   - Secret: Same as your `APIFY_WEBHOOK_SECRET` setting
   - Event types: Select at least `RUN.SUCCEEDED`
   - Payload template: Leave as default

## Troubleshooting

### Common Issues

1. **401 Unauthorized**: Check that the `x-apify-webhook-secret` header matches your `APIFY_WEBHOOK_SECRET` environment variable
2. **Webhook not processing**: Ensure you're sending a `RUN.SUCCEEDED` event with a valid `datasetId`
3. **Database errors**: Verify database connection and schema migrations

### Checking Job Processing

To see the processing status of a job:

```bash
python -m local_newsifier.cli.main db inspect apify_jobs <job_id>
```

The job record will show:
- `processed`: Whether processing was attempted
- `articles_created`: Number of articles created
- `processed_at`: When processing completed