# CLI Usage Guide

This guide covers how to use the Local Newsifier CLI (`nf`) for all news processing operations.

## Installation

```bash
# Install with Poetry
poetry install

# Or install from requirements
pip install -r requirements.txt
```

## Available Commands

### RSS Feed Management

```bash
# List all configured RSS feeds
nf feeds list

# Add a new RSS feed
nf feeds add <URL> [--name NAME] [--category CATEGORY]

# Show details for a specific feed
nf feeds show <FEED_ID>

# Update feed properties
nf feeds update <FEED_ID> [--name NAME] [--category CATEGORY] [--active/--inactive]

# Remove a feed
nf feeds remove <FEED_ID>

# Process a specific feed
nf feeds process <FEED_ID>
```

### Database Operations

```bash
# Show database statistics
nf db stats

# Find duplicate articles
nf db duplicates

# List articles with filtering
nf db articles [--limit N] [--days D] [--source SOURCE]

# Inspect a specific database record
nf db inspect <TABLE> <ID>
```

### Apify Integration

```bash
# Test Apify API connection
nf apify test

# Scrape content from a URL
nf apify scrape-content <URL>

# Run website scraper
nf apify web-scraper <URL> [--max-pages N]

# Run a specific Apify actor
nf apify run-actor <ACTOR_ID> [--input JSON]

# Configure Apify source
nf apify-config create --name NAME --actor-id ACTOR_ID
nf apify-config list
nf apify-config show <CONFIG_ID>
```

## CLI Architecture

The CLI is currently in transition:
- **Current**: Uses fastapi-injectable for dependency injection
- **Target**: Will make HTTP calls to FastAPI endpoints
- **Local Mode**: Uses TestClient for direct API access without running server

### Command Structure

Each command follows this pattern:
1. Parse command-line arguments
2. Validate inputs
3. Call appropriate service method (current) or API endpoint (future)
4. Format and display results

### Error Handling

The CLI provides user-friendly error messages:
- Network errors: Suggests checking API connectivity
- Validation errors: Shows what fields are invalid
- Database errors: Indicates if records don't exist

## Common Workflows

### Processing News Articles

```bash
# Process a single article from URL
nf process <URL>

# Process all feeds
nf feeds process-all

# Generate trend report
nf report trends --days 7
```

### Managing RSS Feeds

```bash
# Add multiple news sources
nf feeds add https://example.com/rss --name "Example News"
nf feeds add https://another.com/feed --category "Tech"

# Check feed status
nf feeds list --active

# Process new articles
nf feeds process-all --since "1 hour ago"
```

### Database Maintenance

```bash
# Check for duplicates
nf db duplicates --remove

# Export articles
nf db export --format json --days 30

# Clean old data
nf db clean --older-than "90 days"
```

## Configuration

### Environment Variables

```bash
# Database connection
export DATABASE_URL="postgresql://user:pass@localhost/newsifier"

# Apify integration
export APIFY_TOKEN="your-api-token"

# API endpoint (for future HTTP mode)
export NEWSIFIER_API_URL="http://localhost:8000"
```

### Config File

Create `~/.newsifier/config.yaml`:
```yaml
database:
  url: postgresql://localhost/newsifier

apify:
  token: ${APIFY_TOKEN}

cli:
  output_format: rich  # or json, plain
  color: true
```

## Output Formats

The CLI supports multiple output formats:

### Rich (default)
Beautiful terminal output with tables and colors

### JSON
```bash
nf feeds list --format json
```

### Plain Text
```bash
nf feeds list --format plain
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check database status
   nf db health

   # Verify connection string
   echo $DATABASE_URL
   ```

2. **Apify Token Invalid**
   ```bash
   # Test Apify connection
   nf apify test

   # Re-set token
   export APIFY_TOKEN="new-token"
   ```

3. **Command Not Found**
   ```bash
   # Ensure CLI is in PATH
   poetry shell
   # or
   python -m local_newsifier.cli
   ```

## Advanced Usage

### Batch Operations

```bash
# Process multiple URLs from file
nf batch process urls.txt

# Import RSS feeds from OPML
nf feeds import feeds.opml
```

### Scheduling

```bash
# Run feed processing on schedule
nf schedule create "*/30 * * * *" "feeds process-all"

# List schedules
nf schedule list
```

### API Mode (Future)

When CLI migrates to HTTP client:
```bash
# Use remote API
export NEWSIFIER_API_URL="https://api.newsifier.com"
nf feeds list

# Use local API
export NEWSIFIER_API_URL="http://localhost:8000"
nf feeds list
```

## Best Practices

1. **Regular Processing**: Set up cron jobs for feed processing
2. **Monitor Duplicates**: Run duplicate check weekly
3. **Database Maintenance**: Clean old articles monthly
4. **Error Logs**: Check `~/.newsifier/logs/` for detailed errors
5. **Backup**: Export important data regularly

## Getting Help

```bash
# General help
nf --help

# Command-specific help
nf feeds --help
nf feeds add --help

# Version info
nf --version
```
