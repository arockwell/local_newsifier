# Performance Monitoring Guide

## Overview

Local Newsifier includes comprehensive performance monitoring using Prometheus metrics. This allows you to track system health, identify bottlenecks, and optimize performance.

## Accessing Metrics

### Raw Prometheus Metrics
- **Endpoint**: `/metrics`
- **Format**: Prometheus text format
- **Authentication**: None required (consider securing in production)
- **Usage**: Can be scraped by Prometheus or compatible monitoring systems

### Metrics Dashboard
- **Endpoint**: `/system/metrics/dashboard`
- **Authentication**: Admin required
- **Format**: HTML dashboard with visualizations
- **Features**: Real-time metrics, performance trends, system health overview

### API Endpoints
- **Summary**: `/system/metrics/api` - JSON format of dashboard data
- **Baseline**: `/system/metrics/baseline` - Performance baseline metrics

## Metrics Collected

### API Metrics
- **Request Count**: Total requests by endpoint and status code
- **Request Duration**: Response time histogram with percentiles
- **Active Requests**: Currently processing requests
- **Error Rates**: 4xx and 5xx errors by endpoint

### Database Metrics
- **Query Count**: Total queries by operation type (SELECT, INSERT, etc.)
- **Query Duration**: Execution time with percentiles
- **Slow Queries**: Queries taking longer than 1 second
- **Connection Pool**: Active database connections

### Celery Task Metrics
- **Task Count**: Total tasks by name and status
- **Task Duration**: Execution time by task type
- **Success/Failure Rates**: Task completion statistics
- **Queue Length**: Pending tasks in queues

### System Metrics
- **Memory Usage**: Current memory consumption
- **CPU Usage**: CPU utilization percentage
- **Application Info**: Version, Python version, PID

### Entity Processing Metrics
- **Entity Extraction**: Count and duration by entity type
- **Sentiment Analysis**: Processing time for sentiment analysis
- **RSS Feed Processing**: Feed processing duration and article count

## Using Monitoring Decorators

### Basic Performance Monitoring
```python
from local_newsifier.monitoring.decorators import monitor_performance

@monitor_performance()
def process_article(article_id: int):
    # Your code here
    pass
```

### Database Query Monitoring
```python
from local_newsifier.monitoring.decorators import monitor_db_query

@monitor_db_query(operation="select", table="articles")
def get_articles(session, start_date, end_date):
    # Your query here
    pass
```

### Entity Extraction Monitoring
```python
from local_newsifier.monitoring.decorators import monitor_entity_extraction

@monitor_entity_extraction(source_type="article")
def extract_entities(text: str):
    # Entity extraction logic
    pass
```

## Slow Query Alerts

The system automatically tracks queries taking longer than 1 second:
- Increments the `newsifier_db_slow_queries_total` counter
- Logs a warning with query details
- Visible in the dashboard under "Slow Queries"

## Performance Baseline

Access `/system/metrics/baseline` to get current performance baseline:
- Average API response time
- Average database query time
- Celery task success rate
- System resource usage

## Integration with Monitoring Systems

### Prometheus Configuration
```yaml
scrape_configs:
  - job_name: 'local_newsifier'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboard
You can import the metrics into Grafana for advanced visualization:
1. Add Prometheus as a data source
2. Import dashboard using Prometheus metrics
3. Create alerts based on thresholds

## Best Practices

1. **Regular Monitoring**: Check the dashboard regularly for anomalies
2. **Set Alerts**: Configure alerts for:
   - High error rates (>5%)
   - Slow queries (>1s)
   - High memory usage (>80%)
   - Failed Celery tasks
3. **Performance Optimization**: Use metrics to identify:
   - Slow endpoints needing optimization
   - Expensive database queries
   - Resource-intensive tasks
4. **Capacity Planning**: Track trends to plan for:
   - Database scaling
   - Worker scaling
   - API server scaling

## Troubleshooting

### Missing Metrics
- Ensure the monitoring module is properly initialized
- Check application logs for monitoring setup errors
- Verify database and Celery connections

### High Memory Usage
- Check for memory leaks in entity processing
- Monitor Celery worker memory consumption
- Review database connection pool settings

### Slow Queries
- Review the slow query log in metrics
- Add database indexes where needed
- Optimize complex queries
- Consider query result caching
