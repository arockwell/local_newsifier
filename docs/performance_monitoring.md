# Performance Monitoring Guide

## Overview

Local Newsifier now includes comprehensive performance monitoring capabilities using Prometheus metrics. This system tracks API response times, database query performance, entity extraction processing times, memory usage patterns, and Celery task execution metrics.

## Architecture

### Components

1. **Metrics Collection** (`src/local_newsifier/monitoring/metrics.py`)
   - Defines Prometheus metrics for various system components
   - Provides decorators for timing and counting operations
   - Handles memory usage tracking

2. **FastAPI Middleware** (`src/local_newsifier/monitoring/middleware.py`)
   - Automatically tracks all HTTP requests
   - Records request duration and counts by endpoint, method, and status
   - Normalizes dynamic paths to prevent metric explosion

3. **Database Monitoring** (`src/local_newsifier/monitoring/database.py`)
   - Uses SQLAlchemy event listeners to track query performance
   - Monitors connection pool usage
   - Logs slow queries (>1 second)

4. **Celery Monitoring** (`src/local_newsifier/monitoring/celery_monitor.py`)
   - Tracks task execution times and success/failure rates
   - Monitors queue depths
   - Uses Celery signals for comprehensive coverage

5. **Service Decorators** (`src/local_newsifier/monitoring/decorators.py`)
   - Provides specialized decorators for different operations
   - Includes context-aware logging

## Metrics Endpoint

The metrics are exposed at `/metrics` in Prometheus text format, ready for scraping.

```bash
curl http://localhost:8000/metrics
```

## Available Metrics

### API Metrics
- `newsifier_api_request_duration_seconds` - Request duration histogram
- `newsifier_api_requests_total` - Total request counter
- `newsifier_api_active_requests` - Currently active requests gauge

### Database Metrics
- `newsifier_db_query_duration_seconds` - Query execution time
- `newsifier_db_queries_total` - Total query count
- `newsifier_db_connection_pool_size` - Connection pool size
- `newsifier_db_active_connections` - Active connections

### Processing Metrics
- `newsifier_entity_extraction_duration_seconds` - Entity extraction time
- `newsifier_entities_extracted_total` - Total entities extracted
- `newsifier_article_processing_duration_seconds` - Article processing time
- `newsifier_articles_processed_total` - Total articles processed

### Celery Metrics
- `newsifier_celery_task_duration_seconds` - Task execution time
- `newsifier_celery_tasks_total` - Total task count
- `newsifier_celery_queue_depth` - Queue depth gauge

### RSS Feed Metrics
- `newsifier_rss_feed_fetch_duration_seconds` - Feed fetch time
- `newsifier_rss_feed_articles_total` - Articles from feeds

### System Metrics
- `newsifier_memory_usage_bytes` - Memory usage (RSS, VMS, shared)
- `newsifier_errors_total` - Error counts by component and type
- `newsifier_system_info` - System information

## Configuration

Performance monitoring is automatically initialized when the application starts. No additional configuration is required for basic functionality.

### Prometheus Configuration

Example Prometheus configuration to scrape the metrics:

```yaml
scrape_configs:
  - job_name: 'local_newsifier'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8000']
```

### Grafana Dashboard

You can visualize the metrics using Grafana. Here's an example query for average response time:

```promql
rate(newsifier_api_request_duration_seconds_sum[5m])
/
rate(newsifier_api_request_duration_seconds_count[5m])
```

## Performance Baselines

Based on initial implementation, expected performance baselines:

- **API Response Times**
  - Simple endpoints (health, config): <50ms
  - Database queries: <200ms
  - Complex operations: <1s

- **Database Queries**
  - Simple SELECT: <50ms
  - Complex JOIN queries: <200ms
  - Bulk operations: <500ms

- **Entity Extraction**
  - Small text (<1000 chars): <100ms
  - Medium text (<5000 chars): <500ms
  - Large articles: <2s

- **Celery Tasks**
  - Article processing: 1-5s
  - RSS feed fetch: 2-10s per feed

## Alerting Rules

Example Prometheus alerting rules:

```yaml
groups:
  - name: newsifier_alerts
    rules:
      - alert: SlowAPIResponse
        expr: rate(newsifier_api_request_duration_seconds_sum[5m]) / rate(newsifier_api_request_duration_seconds_count[5m]) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API responses are slow"

      - alert: HighErrorRate
        expr: rate(newsifier_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"

      - alert: DatabaseConnectionPoolExhausted
        expr: newsifier_db_active_connections >= newsifier_db_connection_pool_size * 0.9
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Database connection pool nearly exhausted"
```

## Using Performance Decorators

### Basic Performance Monitoring

```python
from local_newsifier.monitoring.decorators import monitor_performance

@monitor_performance(metric_name="custom_operation")
def my_function():
    # Your code here
    pass
```

### Article Processing

```python
from local_newsifier.monitoring.decorators import monitor_article_processing

@monitor_article_processing
def process_article(article_id: int):
    # Processing logic
    pass
```

### Entity Extraction

```python
from local_newsifier.monitoring.decorators import monitor_entity_extraction

@monitor_entity_extraction(source='spacy')
def extract_entities(text: str):
    # Extraction logic
    return entities
```

### RSS Feed Fetching

```python
from local_newsifier.monitoring.decorators import monitor_rss_feed_fetch

@monitor_rss_feed_fetch()
def fetch_feed(feed_url: str):
    # Fetch logic
    return feed_data
```

## Troubleshooting

### High Memory Usage

Monitor the `newsifier_memory_usage_bytes` metric. If RSS memory keeps growing:
1. Check for memory leaks in entity extraction
2. Verify database connections are being closed
3. Review Celery task memory usage

### Slow Queries

Queries slower than 1 second are logged as warnings. To investigate:
1. Check logs for "Slow query detected" messages
2. Review the `newsifier_db_query_duration_seconds` metric
3. Use `EXPLAIN ANALYZE` on problematic queries

### API Performance Issues

1. Check `newsifier_api_request_duration_seconds` by endpoint
2. Look for endpoints with high 99th percentile latencies
3. Review `newsifier_api_active_requests` for request queuing

## Best Practices

1. **Avoid High Cardinality Labels**
   - Use normalized paths in metrics
   - Limit label values to known sets
   - Don't include user IDs or request IDs in labels

2. **Resource Management**
   - Metrics are lightweight but not free
   - Periodically review metric usage
   - Remove unused metrics

3. **Alert Fatigue**
   - Set reasonable thresholds
   - Use multi-window alerts
   - Focus on actionable alerts

4. **Dashboard Design**
   - Group related metrics
   - Use consistent time ranges
   - Include both rates and totals

## Integration with Existing Logging

Performance monitoring complements existing logging:
- Metrics provide aggregated performance data
- Logs provide detailed context for issues
- Slow operations are logged automatically
- Correlation through timestamps

## Future Enhancements

Potential improvements for the monitoring system:
1. Distributed tracing integration
2. Custom business metrics
3. Real-time anomaly detection
4. Automated performance regression detection
5. Integration with APM tools
