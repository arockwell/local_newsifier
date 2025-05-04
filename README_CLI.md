# Local Newsifier CLI

The Local Newsifier CLI provides command-line tools for managing RSS feeds, processing articles, interacting with Apify for web scraping, and other system operations. It supports multiple environments (development, staging, production) with appropriate safeguards.

## Installation - Development Mode

To install the CLI in development mode using Poetry:

```bash
# Navigate to the project directory
cd /path/to/local_newsifier

# Install in development mode
poetry install
```

After installation, you can run the CLI using Poetry:

```bash
# Run with poetry run
poetry run nf --help
```

## Usage

### Global Options

```bash
# Run with a specific environment
poetry run nf --env production --verbose <command>

# Set the NF_ENV environment variable (alternative to --env)
export NF_ENV=production
poetry run nf <command>
```

### Get Help

```bash
# Show general help
poetry run nf --help

# Show help for feeds commands
poetry run nf feeds --help

# Show help for environment configuration
poetry run nf config --help
```

### Managing RSS Feeds

#### List Feeds

```bash
# List all feeds
poetry run nf feeds list

# List only active feeds
poetry run nf feeds list --active-only

# Output as JSON
poetry run nf feeds list --json

# Limit number of results
poetry run nf feeds list --limit 5
```

#### Add a Feed

```bash
# Add a feed with default name (URL)
poetry run nf feeds add https://example.com/feed.xml

# Add a feed with custom name and description
poetry run nf feeds add https://example.com/feed.xml --name "Example Feed" --description "An example RSS feed"
```

#### Show Feed Details

```bash
# Show basic feed details (replace 1 with the feed ID)
poetry run nf feeds show 1

# Show feed details with processing logs
poetry run nf feeds show 1 --show-logs

# Output as JSON
poetry run nf feeds show 1 --json
```

#### Update Feed Properties

```bash
# Update feed name
poetry run nf feeds update 1 --name "New Feed Name"

# Update feed description
poetry run nf feeds update 1 --description "Updated description"

# Set feed as inactive
poetry run nf feeds update 1 --inactive

# Set feed as active
poetry run nf feeds update 1 --active
```

#### Process a Feed

```bash
# Process a specific feed to fetch new articles
poetry run nf feeds process 1
```

#### Remove a Feed

```bash
# Remove a feed (with confirmation prompt)
poetry run nf feeds remove 1

# Remove a feed (skip confirmation)
poetry run nf feeds remove 1 --force
```

### Using Apify for Web Scraping

Local Newsifier integrates with Apify for scraping content from websites without RSS feeds.

#### Test Apify Connection

```bash
# Test API connection
poetry run nf apify test

# Test with a specific token
poetry run nf apify test --token your_token_here
```

#### Scrape Content from a Website

```bash
# Basic content scraping
poetry run nf apify scrape-content https://example.com

# Advanced options
poetry run nf apify scrape-content https://example.com --max-pages 10 --max-depth 2 --output results.json
```

#### Use Web Scraper Actor

```bash
# Basic web scraping
poetry run nf apify web-scraper https://example.com

# With custom selectors
poetry run nf apify web-scraper https://example.com --selector "article a" --output results.json

# With wait-for selector
poetry run nf apify web-scraper https://example.com --wait-for "#content .loaded"
```

#### Run Custom Apify Actors

```bash
# Run a custom actor with JSON input
poetry run nf apify run-actor apify/web-scraper --input '{"startUrls":[{"url":"https://example.com"}]}'

# Run actor with input from file
poetry run nf apify run-actor apify/web-scraper --input input.json --output results.json
```

#### Get Dataset Items

```bash
# Get items from a dataset
poetry run nf apify get-dataset dataset_id

# With formatting options
poetry run nf apify get-dataset dataset_id --limit 20 --format table
```

For more comprehensive documentation on Apify integration, see [docs/apify_integration.md](docs/apify_integration.md).

## Testing the CLI

You can run the CLI tests using pytest:

```bash
# Run all CLI tests
poetry run pytest tests/cli

# Run specific test file
poetry run pytest tests/cli/test_feeds.py
```

### Environment Management

The CLI supports multiple environments (development, staging, production) with different configurations.

#### List Environments

```bash
# List configured environments
poetry run nf config list-env

# Show details of the current environment
poetry run nf config show-env

# Show details of a specific environment
poetry run nf config show-env production
```

#### Create and Configure Environments

```bash
# Create a new environment
poetry run nf config create-env production --name "Production" --database-url "postgresql://user:pass@host:port/db" --is-production

# Update an existing environment
poetry run nf config update-env staging --database-url "postgresql://user:pass@staging-host:port/db"

# Set the current environment
poetry run nf config set-env staging
```

#### Import/Export Environments

```bash
# Export environments to a file
poetry run nf config export config.json --include-all

# Import environments from a file
poetry run nf config import config.json
```

#### Delete an Environment

```bash
# Delete an environment (with confirmation prompt)
poetry run nf config delete-env staging
```

### Production Safeguards

When running commands against production environments:

1. Commands that modify data will display warnings
2. Destructive operations require confirmation
3. The current environment is clearly marked

For example:

```bash
# This will show a warning when run against production
poetry run nf feeds add https://example.com/feed.xml

# This will require confirmation when run against production
poetry run nf feeds remove 1
```

## Troubleshooting

If you encounter any issues:

1. Make sure Poetry is correctly installed and the project is installed with `poetry install`
2. Ensure the database is properly set up and migrations are applied
3. Check the logs for more detailed error messages
4. Verify your environment configuration with `nf config show-env`
