# Local Newsifier CLI

The Local Newsifier CLI provides command-line tools for managing RSS feeds, processing articles, and interacting with the system.

## Installation - Development Mode

To install the CLI in development mode using Poetry:

```bash
# Navigate to the project directory
cd /path/to/local_newsifier

# Install in development mode
poetry install

# Activate the Poetry shell (virtual environment)
poetry shell
```

After installation, the `nf` command will be available in your shell.

## Usage

### Get Help

```bash
# Show general help
nf --help

# Show help for feeds commands
nf feeds --help
```

### Managing RSS Feeds

#### List Feeds

```bash
# List all feeds
nf feeds list

# List only active feeds
nf feeds list --active-only

# Output as JSON
nf feeds list --json

# Limit number of results
nf feeds list --limit 5
```

#### Add a Feed

```bash
# Add a feed with default name (URL)
nf feeds add https://example.com/feed.xml

# Add a feed with custom name and description
nf feeds add https://example.com/feed.xml --name "Example Feed" --description "An example RSS feed"
```

#### Show Feed Details

```bash
# Show basic feed details (replace 1 with the feed ID)
nf feeds show 1

# Show feed details with processing logs
nf feeds show 1 --show-logs

# Output as JSON
nf feeds show 1 --json
```

#### Update Feed Properties

```bash
# Update feed name
nf feeds update 1 --name "New Feed Name"

# Update feed description
nf feeds update 1 --description "Updated description"

# Set feed as inactive
nf feeds update 1 --inactive

# Set feed as active
nf feeds update 1 --active
```

#### Process a Feed

```bash
# Process a specific feed to fetch new articles
nf feeds process 1
```

#### Remove a Feed

```bash
# Remove a feed (with confirmation prompt)
nf feeds remove 1

# Remove a feed (skip confirmation)
nf feeds remove 1 --force
```

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

1. Make sure you have activated the Poetry shell with `poetry shell`
2. Ensure the database is properly set up and migrations are applied
3. Check the logs for more detailed error messages
