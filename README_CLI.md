# Local Newsifier CLI

The Local Newsifier CLI provides command-line tools for managing RSS feeds, processing articles, interacting with Apify for web scraping, and other system operations.

## Installation - Development Mode

To install the CLI in development mode using Poetry:

```bash
# Navigate to the project directory
cd /path/to/local_newsifier

# Install in development mode
poetry install
```

Before running `nf`, initialize your Cursor database and load the environment:

```bash
poetry run python scripts/init_cursor_db.py
source .env.cursor
```

See [docs/db_initialization.md](docs/db_initialization.md) for details.

After installation, you can run the CLI using Poetry:

```bash
# Run with poetry run
poetry run nf --help
```

## Usage

### Get Help

```bash
# Show general help
poetry run nf --help

# Show help for feeds commands
poetry run nf feeds --help
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

### Managing Apify Source Configurations

#### List Configs

```bash
# List all configs
poetry run nf apify-config list

# Only active configs
poetry run nf apify-config list --active-only

# Output as JSON
poetry run nf apify-config list --json
```

#### Add a Config

```bash
# Add a configuration
poetry run nf apify-config add --name "Example" --actor-id apify/web-scraper --source-type news --source-url https://example.com

# With schedule and input from file
poetry run nf apify-config add --name "Example" --actor-id apify/web-scraper --source-type news --schedule "0 8 * * *" --input config.json
```

#### Show Config Details

```bash
# Show config details
poetry run nf apify-config show 1

# Output as JSON
poetry run nf apify-config show 1 --json
```

#### Update a Config

```bash
# Update name and deactivate
poetry run nf apify-config update 1 --name "Updated" --inactive

# Update schedule
poetry run nf apify-config update 1 --schedule "0 12 * * *"
```

#### Remove a Config

```bash
# Remove with confirmation
poetry run nf apify-config remove 1

# Skip confirmation
poetry run nf apify-config remove 1 --force
```

#### Run a Config

```bash
# Run actor using saved config
poetry run nf apify-config run 1

# Save output to file
poetry run nf apify-config run 1 --output result.json
```

### Managing Apify Schedules

#### List Schedules

```bash
# Show configured schedules
poetry run nf apify schedules list

# Include Apify status
poetry run nf apify schedules list --with-apify

# Output as JSON
poetry run nf apify schedules list --format json
```

#### Sync Schedules

```bash
# Synchronize database configs with Apify
poetry run nf apify schedules sync
```

#### Create a Schedule

```bash
# Create schedule for a config
poetry run nf apify schedules create 1
```

#### Update a Schedule

```bash
# Update schedule for a config
poetry run nf apify schedules update 1
```

#### Delete a Schedule

```bash
# Delete schedule for a config
poetry run nf apify schedules delete 1
```

#### Check Schedule Status

```bash
# Check schedule details
poetry run nf apify schedules status 1
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

## Troubleshooting

If you encounter any issues:

1. Make sure Poetry is correctly installed and the project is installed with `poetry install`
2. Ensure the database is properly set up and migrations are applied
3. Check the logs for more detailed error messages
