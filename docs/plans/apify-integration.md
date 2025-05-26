# Apify Integration Knowledge Base

## Overview
This document consolidates all knowledge about Apify integration from GitHub issues, providing a comprehensive guide for implementation patterns, decisions, and future development.

## Core Architecture Decisions

### Webhook Implementation Strategy
- **Start Minimal**: Begin with a single ApifyWebhookData table to store raw webhook payloads
- **Fire-and-Forget**: Initial implementation should acknowledge webhooks immediately and process asynchronously
- **Domain Separation**: Keep Apify-specific models separate from core business models
- **Interface-Based**: Use abstract interfaces to decouple Apify implementation from business logic

### Data Flow Architecture
```
Webhook → ApifyWebhookData → Background Task → Domain Models → Analysis Pipeline
```

## Implementation Patterns

### Actor Configuration
```python
class ApifySourceConfig(SQLModel, table=True):
    __tablename__ = "apify_source_configs"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    actor_id: str
    run_input: str  # JSON string of actor input
    schedule_id: Optional[str] = None  # Apify schedule ID
    webhook_url: Optional[str] = None
    is_active: bool = True
```

### Webhook Handler Pattern
```python
@router.post("/webhooks/apify")
async def handle_apify_webhook(
    request: Request,
    apify_service: Annotated[ApifyService, Depends(get_apify_service)],
    background_tasks: BackgroundTasks
):
    # 1. Validate webhook (if secret configured)
    # 2. Store raw payload
    # 3. Trigger background processing
    # 4. Return immediate response
```

### Actor Output Transformation
Different actors return different output formats that need transformation:

1. **Website Content Crawler**: Returns `ListPage` objects
2. **Web Scraper**: Returns structured data
3. **Google Search Scraper**: Returns search results

Each requires a specific transformer:
```python
def transform_actor_output(actor_id: str, output_data: dict) -> List[Article]:
    transformer = get_transformer_for_actor(actor_id)
    return transformer.transform(output_data)
```

## Known Issues and Solutions

### ListPage Object Handling
**Problem**: Apify returns `ListPage` objects that need pagination handling
**Solution**:
- Extract items from the first page initially
- Implement pagination support in future iterations
- Store raw data for reprocessing if needed

### Schedule Synchronization
**Problem**: Schedules can be modified outside the application
**Solution**:
- Implement two-way sync with Apify API
- Store schedule_id in database
- Provide sync command: `nf apify sync-schedules`

### Actor Run Failures
**Problem**: Actor runs can fail for various reasons
**Solution**:
- Store failure details in webhook data
- Implement retry logic with exponential backoff
- Alert on repeated failures
- Provide manual retry command

## Configuration Management

### Environment Variables
```bash
APIFY_TOKEN=your_token_here
APIFY_WEBHOOK_SECRET=optional_webhook_secret
APIFY_API_BASE_URL=https://api.apify.com/v2  # Optional override
```

### Actor Input Templates
Store commonly used actor configurations as templates:
```python
ACTOR_TEMPLATES = {
    "news_crawler": {
        "actor_id": "apify/website-content-crawler",
        "default_input": {
            "startUrls": [{"url": "https://example.com"}],
            "maxCrawlDepth": 1,
            "maxCrawlPages": 10
        }
    }
}
```

## Testing Strategies

### Webhook Testing
Use the Fish shell functions for comprehensive testing:
```fish
# Test successful webhook
test_webhook_success

# Test with custom data
test_webhook --status SUCCEEDED --actor-id custom/actor

# Test batch scenarios
test_webhook_batch
```

### Mock Apify Client
```python
@pytest.fixture
def mock_apify_client():
    client = Mock()
    client.actor.return_value.call.return_value = {
        "id": "run_123",
        "status": "SUCCEEDED"
    }
    return client
```

## Future Enhancements

### Scheduling Features
1. **Cron Expression Support**: Allow complex scheduling patterns
2. **Schedule Groups**: Group related schedules for bulk operations
3. **Conditional Scheduling**: Run based on previous results
4. **Schedule Templates**: Reusable schedule configurations

### Data Processing Pipeline
1. **Stream Processing**: Process large datasets without loading into memory
2. **Parallel Processing**: Process multiple actor outputs concurrently
3. **Data Validation**: Validate actor output against expected schema
4. **Incremental Updates**: Only process new/changed data

### Monitoring and Observability
1. **Metrics Collection**:
   - Actor run success/failure rates
   - Processing times
   - Data volume metrics
   - Cost tracking

2. **Alerting**:
   - Failed runs
   - Cost thresholds
   - Data quality issues
   - Schedule failures

### Advanced Integration
1. **Actor Chaining**: Run actors in sequence based on outputs
2. **Dynamic Input Generation**: Generate actor inputs from database state
3. **Result Aggregation**: Combine outputs from multiple actors
4. **Custom Actors**: Deploy and manage custom Apify actors

## Best Practices

### Error Handling
- Always store raw webhook data for debugging
- Implement idempotent processing
- Use structured logging for traceability
- Provide clear error messages in UI

### Security
- Validate webhook signatures when configured
- Sanitize actor inputs to prevent injection
- Use least-privilege API tokens
- Audit all Apify operations

### Performance
- Process webhooks asynchronously
- Batch database operations
- Implement caching for frequently accessed data
- Use connection pooling for API calls

### Maintenance
- Regular cleanup of old webhook data
- Monitor Apify API changes
- Keep actor configurations versioned
- Document custom actor requirements

## Migration Path

### Phase 1: Basic Integration (Complete)
- ✅ Webhook endpoint
- ✅ Basic actor running
- ✅ Source configuration CRUD

### Phase 2: Advanced Features (In Progress)
- 🔄 Schedule management
- 🔄 Two-way sync
- 🔄 Error recovery

### Phase 3: Production Readiness
- ⏳ Monitoring and metrics
- ⏳ Advanced scheduling
- ⏳ Cost optimization
- ⏳ Multi-tenant support

## Common Patterns

### Running Actors
```python
# Simple run
result = apify_service.run_actor(actor_id, run_input)

# With webhook
result = apify_service.run_actor(
    actor_id,
    run_input,
    webhook_url="https://app.com/webhooks/apify"
)

# With custom build
result = apify_service.run_actor(
    actor_id,
    run_input,
    build="latest"
)
```

### Processing Results
```python
# Fetch and process results
dataset_items = apify_service.get_dataset_items(dataset_id)
for item in dataset_items:
    article = transform_to_article(item)
    process_article(article)
```

### Schedule Management
```python
# Create schedule
schedule = apify_service.create_schedule(
    name="Daily News Crawl",
    actor_id=actor_id,
    cron="0 8 * * *",
    run_input=run_input
)

# Update schedule
apify_service.update_schedule(
    schedule_id,
    is_enabled=False
)
```

## Troubleshooting Guide

### Common Issues

1. **Webhook Not Received**
   - Check webhook URL is publicly accessible
   - Verify actor configuration includes webhook
   - Check Apify dashboard for delivery attempts

2. **Authentication Failures**
   - Verify APIFY_TOKEN is set correctly
   - Check token has required permissions
   - Ensure token hasn't expired

3. **Data Transformation Errors**
   - Log raw actor output for debugging
   - Verify actor output matches expected schema
   - Check for null/missing required fields

4. **Performance Issues**
   - Monitor webhook processing times
   - Check for database query bottlenecks
   - Verify background task worker capacity

## References

- [Apify API Documentation](https://docs.apify.com/api/v2)
- [Apify Python Client](https://docs.apify.com/sdk/python)
- [Webhook Documentation](https://docs.apify.com/platform/integrations/webhooks)
- Project Issues: #112, #195, #212, #220, #297, #334, #381, #408, #563, #583, #602, #644
