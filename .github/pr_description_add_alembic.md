# Add Database Migrations with Alembic

This PR adds Alembic for database migrations to Local Newsifier, providing a robust way to manage database schema changes over time.

## Changes Made

- Added Alembic as a dependency in `pyproject.toml` and `requirements.txt`
- Initialized Alembic with project configuration
- Configured Alembic to work with our SQLModel models and database settings
- Created a baseline migration that captures the current database schema
- Created a utility script (`scripts/db_migration.py`) to run common migration tasks
- Added documentation on how to use Alembic for database migrations

## Benefits

- **Version Control**: Track database schema changes alongside code changes
- **Safe Schema Evolution**: Apply schema changes in a controlled, repeatable way
- **Automated Migration Generation**: Automatically generate migration scripts from model changes
- **Bidirectional Migrations**: Support for both upgrading and downgrading the database
- **Development Workflow**: Easier collaboration when schema changes are being made by multiple developers

## How to Use

### Using the Helper Script

We've created a convenient script to run common migration tasks:

```bash
# Verify database connection
python scripts/db_migration.py verify

# Show current migration version
python scripts/db_migration.py current

# Show migration history
python scripts/db_migration.py history

# Upgrade database to latest version
python scripts/db_migration.py upgrade

# Create a new migration from model changes
python scripts/db_migration.py create --message "Description of changes"
```

### Migration Workflow

When you make changes to the SQLModel models:

1. Make your changes to the model definitions
2. Run: `python scripts/db_migration.py create --message "Description of changes"`
3. Review the generated migration script in `alembic/versions/`
4. Apply the migration: `python scripts/db_migration.py upgrade`

When pulling code that contains new migrations:

1. Run: `python scripts/db_migration.py upgrade`

## Testing Done

- Verified that Alembic correctly identifies the existing database schema
- Successfully generated a baseline migration
- Tested the database connection and migration utilities

## What's Next

- Integrate with CI/CD pipeline to run migrations during deployment
- Consider adding a pre-commit hook to ensure migrations are created for model changes
