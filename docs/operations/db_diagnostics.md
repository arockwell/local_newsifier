# Database Diagnostics Commands

The Local Newsifier CLI provides powerful commands for database inspection and management through the `nf db` command group. These commands help you understand the state of your database, diagnose issues, and perform maintenance operations.

## Command Overview

| Command | Description |
|---------|-------------|
| `nf db stats` | Display statistics about all database tables |
| `nf db duplicates` | Find and display duplicate articles |
| `nf db articles` | List articles with detailed filtering options |
| `nf db inspect` | Show detailed information about a specific record |
| `nf db purge-duplicates` | Remove duplicate articles, keeping the oldest version |

## Detailed Usage

### Statistics

Get a quick overview of your database state:

```bash
# Basic stats
nf db stats

# Output as JSON
nf db stats --json
```

This command shows:
- Article counts and date ranges
- RSS feed counts (total, active, inactive)
- Processing log counts
- Entity counts

### Finding Duplicates

When you encounter duplicate article errors, use this command to identify them:

```bash
# Show top 10 URLs with duplicates
nf db duplicates

# Show more duplicates
nf db duplicates --limit 20

# Output as JSON
nf db duplicates --json
```

### Listing Articles

Browse and filter articles with flexible criteria:

```bash
# List recent articles
nf db articles

# Filter by source
nf db articles --source www.cbsnews.com

# Filter by status
nf db articles --status analyzed

# Date filtering
nf db articles --after 2025-03-01 --before 2025-04-01

# Show more results
nf db articles --limit 50

# Output as JSON
nf db articles --json
```

### Inspecting Records

Examine detailed information about specific database records:

```bash
# Inspect an article
nf db inspect article 123

# Inspect an RSS feed (includes recent processing logs)
nf db inspect rss_feed 2

# Inspect a feed processing log
nf db inspect feed_log 45

# Inspect an entity
nf db inspect entity 67

# Output as JSON
nf db inspect article 123 --json
```

### Managing Duplicates

Clean up duplicate articles from the database:

```bash
# Show what would be deleted (dry run)
nf db purge-duplicates --dry-run

# Actually remove duplicates (will prompt for confirmation)
nf db purge-duplicates

# Output as JSON
nf db purge-duplicates --json
```

This command keeps the oldest article for each URL and removes newer duplicates.

## Troubleshooting Tips

### Duplicate Article Errors

If you're seeing errors like:

```
Error processing article: (psycopg2.errors.UniqueViolation) duplicate key value violates unique constraint "articles_url_key"
```

Use these steps to diagnose and fix:

1. Run `nf db duplicates` to identify duplicate articles
2. Inspect one of the articles with `nf db inspect article <id>`
3. Use `nf db purge-duplicates --dry-run` to see what would be cleaned up
4. Run `nf db purge-duplicates` to remove duplicates if appropriate

### Database Inconsistencies

If you're troubleshooting database-related issues:

1. Check overall stats with `nf db stats`
2. Examine specific records with `nf db inspect`
3. Look for patterns in the data using the filtering options in `nf db articles`

This information can help identify root causes of issues in the processing pipeline.
