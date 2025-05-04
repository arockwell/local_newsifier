# Database Initialization Guide

This guide explains how to initialize and set up a new database instance for Local Newsifier development.

## Understanding Cursor-Specific Databases

Local Newsifier uses a unique database instance for each Cursor environment to avoid conflicts. Each database is named according to this pattern:

```
local_newsifier_<cursor_id>
```

Where `<cursor_id>` is a unique identifier stored in the `CURSOR_DB_ID` environment variable.

## Quick Start

To initialize a new database for your Cursor instance:

```bash
# Install dependencies first
poetry install

# Initialize the database
poetry run python scripts/init_cursor_db.py

# Source the environment file to use in current shell
source .env.cursor
```

The initialization script will:
1. Create a unique cursor ID if none exists
2. Create a new database with the cursor ID
3. Set up all required tables
4. Save the cursor ID to `.env.cursor` for future sessions

## How It Works

### Environment Variables

- `CURSOR_DB_ID`: Unique identifier for your Cursor instance
- The `.env.cursor` file stores your cursor ID for easy reuse

### Database Creation Process

1. The `init_cursor_db.py` script generates or uses an existing cursor ID
2. It connects to PostgreSQL and creates a new database
3. It initializes all tables using SQLModel's metadata
4. The script writes the cursor ID to `.env.cursor` for future reference

## Using in Different Shells

To use your database in a new terminal session:

```bash
# Option 1: Source the environment file
source .env.cursor

# Option 2: Set the environment variable directly
export CURSOR_DB_ID=<your-cursor-id>
```

## Troubleshooting

### Database Connection Issues

If you see errors about connecting to the database:

1. Verify PostgreSQL is running:
   ```bash
   pg_isready
   ```

2. Check your cursor ID is correctly set:
   ```bash
   echo $CURSOR_DB_ID
   ```

3. Verify the database exists:
   ```bash
   psql -U postgres -c "\l" | grep local_newsifier_
   ```

### Missing Tables

If database tables are missing:

```bash
# Check if tables exist
poetry run python -m src.local_newsifier.cli.main db stats
```

### Script Execution Errors

If the initialization script fails:

1. Make sure dependencies are installed:
   ```bash
   poetry install
   ```

2. Check PostgreSQL connection parameters in `src/local_newsifier/config/common.py`

## Advanced: Manual Setup

If you need to set up manually:

1. Generate a cursor ID:
   ```bash
   export CURSOR_DB_ID=$(python -c "import uuid; print(str(uuid.uuid4())[:8])")
   ```

2. Create the database:
   ```bash
   createdb -U postgres "local_newsifier_$CURSOR_DB_ID"
   ```

3. Run Alembic migrations:
   ```bash
   CURSOR_DB_ID=$CURSOR_DB_ID poetry run python -m alembic upgrade head
   ```

## Additional Commands

Check database status:
```bash
poetry run python -m src.local_newsifier.cli.main db stats
```

Reset the database (caution - removes all data):
```bash
poetry run python scripts/reset_db.py
```

## Related Documentation

- See `CLAUDE.md` for details on the project's architecture
- See `docs/db_diagnostics.md` for troubleshooting database issues