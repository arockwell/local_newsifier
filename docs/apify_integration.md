# Apify Integration Guide

## Overview

[Apify](https://apify.com/) is a web scraping and automation platform that Local Newsifier leverages to extract content from websites that don't offer RSS feeds. This integration allows the system to collect news articles from a wider range of sources.

## Why Apify?

Apify provides several advantages for the Local Newsifier system:

1. **Powerful Web Scraping**: Apify offers pre-built actors (like web-scraper and website-content-crawler) that handle complex websites, JavaScript rendering, and anti-bot protections.

2. **Scalability**: Apify handles the infrastructure for running scraping workloads, allowing Local Newsifier to focus on processing and analyzing the data.

3. **Scheduling & Automation**: Apify supports scheduled runs and webhooks, making it easy to regularly collect new content.

4. **Data Management**: Apify stores scraped data in datasets that can be easily accessed via API.

## Setup Requirements

To use Apify with Local Newsifier, you need:

1. **Apify Account**: Register at [apify.com](https://apify.com/)
2. **API Token**: Generate an API token in your Apify account settings
3. **Configure Environment**: Set the `APIFY_TOKEN` environment variable

### Setting the API Token

You can set the API token in several ways:

```bash
# As an environment variable
export APIFY_TOKEN=your_token_here

# In a .env file
echo "APIFY_TOKEN=your_token_here" >> .env

# When running a command (temporary)
nf apify test --token your_token_here
```

## CLI Commands for Apify

Local Newsifier includes several CLI commands for interacting with Apify:

### Test Connection

Verify your Apify credentials and connection:

```bash
nf apify test
```

### Scrape Web Content

Extract content from a specific URL using Apify's website-content-crawler:

```bash
# Basic usage
nf apify scrape-content https://example.com

# Advanced options
nf apify scrape-content https://example.com --max-pages 10 --max-depth 2 --output results.json
```

### Use Web Scraper

For more control over scraping, use Apify's web-scraper actor:

```bash
# Basic usage
nf apify web-scraper https://example.com

# With custom selectors
nf apify web-scraper https://example.com --selector "article a" --output results.json

# With custom page function
nf apify web-scraper https://example.com --page-function "path/to/page_function.js"
```

### Run Custom Actors

Run any Apify actor with custom input:

```bash
# With JSON input
nf apify run-actor apify/web-scraper --input '{"startUrls":[{"url":"https://example.com"}]}'

# With input from file
nf apify run-actor apify/web-scraper --input input.json
```

### Get Dataset Items

Retrieve data from an Apify dataset:

```bash
# Get dataset items (after running an actor)
nf apify get-dataset dataset_id --limit 20 --format table
```

## Adding New Apify Sources

To add a new source for scraping with Apify:

1. **Identify the Website**: Determine which news source you want to scrape
2. **Select the Appropriate Actor**: Choose between:
   - `website-content-crawler`: For general content extraction
   - `web-scraper`: For more precise control with custom page functions

3. **Test the Scraping Configuration**:
   ```bash
   # Test with content crawler
   nf apify scrape-content https://new-source-url.com --max-pages 3 --output test_output.json

   # Or test with web scraper
   nf apify web-scraper https://new-source-url.com --selector "article.news-item a" --output test_output.json
   ```

4. **Configure Database Entry**:
   Once you've established a working configuration, register it with the CLI so it can be scheduled automatically:

   - Use `nf apify-config add` to create an `ApifySourceConfig` record with the actor ID and input configuration
   - Set the cron schedule and mark the source as active
   - Manage schedules with `nf apify schedules` (e.g., `create`, `status`, `update`)

   These commands persist the configuration in the `ApifySourceConfig` table and synchronize scheduling information with Apify.

   After the configuration is stored, run `nf apify schedules create <CONFIG_ID>` to create the schedule in Apify and use `nf apify schedules update` to keep it synchronized with any changes.

## Scheduling & Webhooks

Apify supports two main approaches for scheduling content scraping:

### 1. Time-Based Scheduling

Configure sources to run on a schedule using cron expressions:

```
# Example cron schedule (daily at 8 AM)
0 8 * * *
```

### 2. Webhook Integration

You can set up Apify to call back to Local Newsifier when scraping jobs complete:

1. Configure a webhook URL in your application deployment
2. Set up the webhook in Apify to trigger when runs complete
3. Local Newsifier will automatically process new data when notified

## Common Troubleshooting

### Rate Limits

If you encounter rate limit errors:

- Space out your scraping jobs
- Reduce concurrency in actor settings
- Use Apify proxy services if available on your plan

### Selector Issues

If data isn't being extracted correctly:

- Test selectors using browser developer tools
- Start with broad selectors and refine
- Check if the site structure changes based on user agent or JavaScript execution

### Authentication Issues

If you see authentication errors:

```
Error: Authentication failed. Check your API token.
```

Verify your APIFY_TOKEN is:
- Correctly set in your environment
- Valid and not expired
- Has the required permissions

## Environment Variables

| Variable      | Description                          | Required | Default |
|---------------|--------------------------------------|----------|---------|
| APIFY_TOKEN   | API token for Apify authentication   | Yes      | None    |

## Performance Considerations

For optimal performance:

- Limit the number of pages scraped per job
- Set appropriate request delays to avoid overloading sites
- Schedule scraping during off-peak hours
- Use selective scraping with targeted URLs rather than crawling entire sites

## Security Notes

- Your Apify API token provides access to your Apify account and should be kept secure
- Avoid committing the token to version control
- Consider using short-lived tokens for production deployments
- Review scraped data for sensitive information before processing
