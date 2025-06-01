#!/bin/bash
# Test concurrent webhook handling

echo "Testing concurrent webhook handling..."

# Function to send a webhook
send_webhook() {
    local run_id=$1
    local index=$2

    curl -X POST http://localhost:8000/webhooks/apify \
        -H "Content-Type: application/json" \
        -d "{
            \"userId\": \"test-user\",
            \"createdAt\": \"2025-06-01T12:00:00.${index}00Z\",
            \"eventType\": \"ACTOR.RUN.SUCCEEDED\",
            \"eventData\": {
                \"actorId\": \"test-actor\",
                \"actorRunId\": \"${run_id}\"
            },
            \"resource\": {
                \"id\": \"${run_id}\",
                \"status\": \"SUCCEEDED\",
                \"defaultDatasetId\": \"test-dataset-${run_id}\"
            }
        }" 2>/dev/null
}

# Generate a unique run ID for this test
RUN_ID="concurrent-test-$(date +%s)-$(uuidgen | cut -c1-8)"

echo "Using run_id: $RUN_ID"
echo "Sending 5 concurrent webhooks..."

# Send 5 webhooks concurrently
for i in {1..5}; do
    send_webhook "$RUN_ID" "$i" &
done

# Wait for all background jobs to complete
wait

echo "All webhooks sent. Check the server logs for results."
echo ""
echo "To check for duplicate key violations:"
echo "grep -i 'duplicate' server.log | tail -20"
echo ""
echo "To verify only one webhook was saved:"
echo "nf db inspect apify_webhook_raw $RUN_ID"
