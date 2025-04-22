# Alembic Database Migrations

This directory contains database migration scripts for the Local Newsifier project using Alembic.

## Setup

The project is configured to run migrations automatically during deployment:

1. The initialization script (`scripts/init_alembic.sh`) checks if migrations have been applied
2. If this is the first deployment with Alembic, it stamps the database with the current migration version
3. Then regular migrations run with `alembic upgrade head`

## Working with Existing Tables

Since this project already had tables before Alembic was added, we've taken a special approach:

1. We've created a proper initial migration that represents the full schema
2. We use `alembic stamp head` on first run to mark the existing database as already up-to-date
3. Future migrations will run normally, only applying new changes

## Creating New Migrations

To create a new migration after changing your SQLModel models:

```bash
# Generate a migration based on model changes
alembic revision --autogenerate -m "description_of_changes"

# Review the generated migration in alembic/versions/
# Make any necessary adjustments to the migration script

# Apply the migration to your local database
alembic upgrade head
```

## Migration Commands

- `alembic current`: Show current migration version
- `alembic history`: Show migration history
- `alembic upgrade head`: Apply all migrations
- `alembic downgrade -1`: Downgrade one migration
- `alembic stamp head`: Mark the database as being at the latest migration (without running migrations)

## Handling Special Cases

If you need to make complex changes that Alembic can't auto-generate correctly:

1. Create an empty migration: `alembic revision -m "manual_migration_description"`
2. Edit the generated file in `alembic/versions/` to add your custom SQL operations
3. Run the migration: `alembic upgrade head`

## Deployment

The deployment process (Railway) is configured to automatically run migrations before starting the application. This happens via:

1. Procfile: `web: bash scripts/init_alembic.sh && alembic upgrade head && python -m uvicorn local_newsifier.api.main:app --host 0.0.0.0 --port $PORT`
2. railway.json: Same command in the `startCommand` configuration

## Troubleshooting

- If migrations fail, check the Railway logs
- For existing databases, ensure `scripts/init_alembic.sh` runs first to stamp the current version
- If you need to reset migrations, use `alembic stamp <revision>` to move to a specific point
