# Add Database Migrations with Alembic

This PR adds Alembic for database migrations to Local Newsifier, providing a robust way to manage database schema changes over time. The implementation is minimal and focused on core functionality.

## Changes Made

- Added Alembic as a dependency in `pyproject.toml` and `requirements.txt`
- Initialized Alembic with project configuration
- Configured Alembic to work with our SQLModel models and database settings
- Created a baseline migration that captures the current database schema
- Added Alembic documentation to the project's memory bank

## Benefits

- **Version Control**: Track database schema changes alongside code changes
- **Safe Schema Evolution**: Apply schema changes in a controlled, repeatable way
- **Automated Migration Generation**: Automatically generate migration scripts from model changes
- **Bidirectional Migrations**: Support for both upgrading and downgrading the database
- **Development Workflow**: Easier collaboration when schema changes are being made by multiple developers

## How to Use

Alembic provides a simple and powerful CLI that can be used directly:

```bash
# Show current migration version
alembic current

# Show migration history
alembic history

# Create a new migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Apply all pending migrations
alembic upgrade head

# Revert to a previous version
alembic downgrade <revision>
```

### Migration Workflow

When you make changes to the SQLModel models:

1. Make your changes to the model definitions
2. Run: `alembic revision --autogenerate -m "Description of changes"`
3. Review the generated migration script in `alembic/versions/`
4. Apply the migration: `alembic upgrade head`

When pulling code that contains new migrations:

1. Run: `alembic upgrade head`

## Testing Done

- Verified that Alembic correctly identifies the existing database schema
- Successfully generated a baseline migration
- Tested database migrations with SQLModel

## What's Next

- Integrate with CI/CD pipeline to run migrations during deployment
- Consider adding a pre-commit hook to ensure migrations are created for model changes
