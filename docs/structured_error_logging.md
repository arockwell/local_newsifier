# Structured Error Logging

This document explains the structured logging capabilities added to the error handling system in the Local Newsifier application.

## Overview

The error handling system now includes comprehensive structured logging capabilities, making it easier to:

1. **Track errors** with consistent log formats
2. **Filter logs** based on error properties
3. **Analyze error patterns** by service and type
4. **Enable automated monitoring** with structured data

## Key Features

The structured logging system provides:

1. **Automatic log level selection** based on error properties
2. **Rich context in log entries** including service, error type, and function details
3. **Standardized log format** across all services
4. **Customizable logging** with service-specific extensions

## Using the Logging System

### Automatic Logging

All errors handled by the service decorators are automatically logged with appropriate levels and context:

```python
@handle_rss_service
def fetch_feed(url):
    # If an error occurs, it will be automatically logged
    # with the appropriate level and context
    return requests.get(url).text
```

### Manual Logging

You can also manually log errors using the `log_error` method:

```python
try:
    result = service.fetch_data()
except ServiceError as e:
    # Log with the module's logger
    e.log_error()
    
    # Or use a specific logger
    custom_logger = logging.getLogger("my.custom.logger")
    e.log_error(custom_logger)
```

## Log Structure

Logs include the following structured data:

- `service`: The service identifier (e.g., "rss", "apify")
- `error_type`: The specific error type (e.g., "network", "parse")
- `full_type`: Combined service and type (e.g., "rss.network")
- `transient`: Whether the error is transient (boolean)
- `context`: All additional context from the error
  - `function`: The function that raised the error
  - `args`: Function arguments (truncated)
  - `kwargs`: Function keyword arguments (truncated)
  - `url`: The URL being accessed (if applicable)
  - `status_code`: HTTP status code (if applicable)

## Log Levels

Logs are assigned appropriate severity levels:

- **ERROR**: Non-transient errors (system configuration issues, permanent failures)
- **WARNING**: Transient errors (network timeouts, temporary issues)
- **INFO**: Informational messages (retry attempts, timing)
- **DEBUG**: Detailed diagnostics (original exceptions)

## Retry Logging

The retry system adds structured logging for retry attempts:

```
WARNING:local_newsifier.errors.error:Retrying fetch_feed due to transient error: network (attempt 1/3)
```

With structured context:
```json
{
  "service": "rss",
  "error_type": "network",
  "attempt": 1,
  "max_attempts": 3,
  "function": "fetch_feed",
  "url": "https://example.com/feed"
}
```

## Example Log Output

A typical error log entry might look like:

```
ERROR:local_newsifier.errors.error:rss.xml_parse: XML parsing error: syntax error at line 3
```

With the structured data containing:

```json
{
  "service": "rss",
  "error_type": "xml_parse",
  "full_type": "rss.xml_parse",
  "transient": false,
  "function": "parse_feed",
  "args": ["https://example.com/feed.xml"],
  "url": "https://example.com/feed.xml"
}
```

## Configuring Logging

To fully take advantage of structured logging, configure your logger to capture the extra fields:

```python
import logging
import json

class StructuredLogFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }
        
        # Add all extra fields from the record
        for key, value in record.__dict__.items():
            if key not in log_data and key not in ('args', 'exc_info', 'exc_text', 'msg'):
                log_data[key] = value
                
        return json.dumps(log_data)

# Set up a handler with the formatter
handler = logging.StreamHandler()
handler.setFormatter(StructuredLogFormatter())
logger = logging.getLogger("local_newsifier.errors")
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

## CLI Integration

The CLI error handling now uses a standardized format for all errors, with consistent color coding and structure:

- Error message in red and bold
- Troubleshooting hints in yellow
- Context information in plain text (verbose mode)

## Best Practices

1. **Monitor transient errors**: Track WARNING logs to identify recurring transient issues
2. **Set up alerts**: Configure alerts for ERROR level logs, which indicate non-recoverable failures
3. **Use structured parsing**: Process logs with JSON parsing to enable filtering and analysis
4. **Log rotation**: Implement log rotation for error logs to manage storage
5. **Analyze patterns**: Review logs periodically to identify patterns and common error types