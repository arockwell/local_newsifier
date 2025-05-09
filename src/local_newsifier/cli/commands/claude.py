"""CLI commands for Claude Code integration.

This module provides commands for setting up and managing Claude Code integration
with the Local Newsifier project.
"""

import logging
import os
import shutil
from pathlib import Path

import click

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@click.group(name="claude")
def claude_group():
    """Commands for managing Claude Code integration."""
    pass


@claude_group.command(name="init")
@click.argument("directory", type=click.Path(file_okay=False))
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force initialization even if directory exists and is not empty",
)
@click.option("--skip-db", is_flag=True, help="Skip database initialization")
def init_claude_code(directory, force, skip_db):
    """
    Initialize a new Claude Code workspace in the specified directory.

    This command:
    1. Creates the directory if it doesn't exist
    2. Copies project files to the new directory
    3. Initializes a cursor-specific database for the new directory
    4. Sets up environment files

    DIRECTORY is the path where the new workspace will be created.
    """
    # Convert to absolute path
    directory = Path(directory).resolve()

    # Check if directory exists and handle accordingly
    if directory.exists():
        if not directory.is_dir():
            raise click.BadParameter(f"'{directory}' exists but is not a directory")

        # Check if directory is empty or if force flag is set
        if any(directory.iterdir()) and not force:
            raise click.BadParameter(
                f"Directory '{directory}' is not empty. Use --force to initialize anyway."
            )
    else:
        # Create directory
        directory.mkdir(parents=True)
        click.echo(f"Created directory: {directory}")

    # Get current project root
    current_dir = Path.cwd()

    # Copy essential files for a minimal functioning project
    files_to_copy = [
        ".env.example",
        "pyproject.toml",
        "README.md",
    ]

    dirs_to_copy = [
        "src",
        "scripts",
    ]

    click.echo("Copying project files...")

    for file in files_to_copy:
        src_path = current_dir / file
        if src_path.exists():
            shutil.copy2(src_path, directory / file)
            click.echo(f"  ✓ Copied {file}")
        else:
            click.echo(f"  ! Skipped {file} (not found)")

    for dir_name in dirs_to_copy:
        src_path = current_dir / dir_name
        dest_path = directory / dir_name
        if src_path.exists():
            if dest_path.exists():
                shutil.rmtree(dest_path)
            shutil.copytree(src_path, dest_path)
            click.echo(f"  ✓ Copied {dir_name}/")
        else:
            click.echo(f"  ! Skipped {dir_name}/ (not found)")

    # Create CLAUDE.md file with default configuration
    claude_md_path = directory / "CLAUDE.md"
    claude_md_content = """# Local Newsifier Development Guide

## Project Overview
- News article analysis system using SQLModel, PostgreSQL, and dependency injection
- Focuses on entity tracking, sentiment analysis, and headline trend detection
- Uses NLP for entity recognition and relationship mapping
- Supports multiple content acquisition methods (RSS feeds, Apify web scraping)
- Uses Celery with Redis for asynchronous task processing

## Environment Setup

This project requires Python 3.10-3.12, with Python 3.12 recommended to match CI.

## Getting Started

1. Run database initialization:
   ```bash
   python scripts/init_cursor_db.py
   ```

2. Install spaCy models:
   ```bash
   python -m spacy download en_core_web_lg
   ```

3. Add an RSS feed:
   ```bash
   python -m src.local_newsifier.cli.main feeds add https://example.com/rss
   ```

4. Process a feed:
   ```bash
   python -m src.local_newsifier.cli.main feeds process <feed_id>
   ```

## Common Commands

### CLI Commands
- `nf help`: Show available commands and options
- `nf feeds list`: List configured RSS feeds
- `nf feeds add <URL>`: Add a new RSS feed
- `nf feeds process <ID>`: Process a specific feed
- `nf db stats`: Show database statistics
"""

    with open(claude_md_path, "w") as f:
        f.write(claude_md_content)
    click.echo("  ✓ Created CLAUDE.md with default configuration")

    # Create .env file with default configuration
    env_path = directory / ".env"
    env_content = """# Database settings
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
# POSTGRES_DB will be automatically set by the cursor system

# Output directories
OUTPUT_DIR=output
CACHE_DIR=cache

# Logging
LOG_LEVEL=INFO

# NLP settings
NER_MODEL=en_core_web_lg
"""

    with open(env_path, "w") as f:
        f.write(env_content)
    click.echo("  ✓ Created .env with default configuration")

    # Initialize database for the new directory if not skipped
    if not skip_db:
        click.echo("\nInitializing database...")

        # Change to the new directory to run the initialization script
        # This ensures .env.cursor is created in the right place
        os.chdir(directory)

        try:
            # Import here to avoid circular imports
            from scripts.init_cursor_db import init_cursor_db

            db_name = init_cursor_db()
            click.echo(f"  ✓ Initialized database: {db_name}")
            click.echo("  ✓ Created .env.cursor file")

        except Exception as e:
            click.echo(f"  ! Database initialization failed: {e}")
            click.echo("    You can run database initialization manually later:")
            click.echo("    cd " + str(directory))
            click.echo("    python scripts/init_cursor_db.py")

        # Change back to original directory
        os.chdir(current_dir)

    click.echo("\n✅ Claude Code workspace initialized successfully!")
    click.echo(f"Workspace directory: {directory}")
    click.echo("\nNext steps:")
    click.echo("1. cd " + str(directory))
    click.echo("2. source .env.cursor")
    click.echo("3. Run 'poetry install' to install dependencies")
    click.echo("4. Run 'python -m spacy download en_core_web_lg' to install NLP models")
    click.echo("5. Start working with Claude Code!")


@claude_group.command(name="validate")
@click.option(
    "--directory",
    "-d",
    type=click.Path(exists=True, file_okay=False),
    default=".",
    help="Directory to validate (defaults to current directory)",
)
def validate_claude_code(directory):
    """
    Validate that the current directory is a properly set up Claude Code workspace.

    This command checks for:
    1. Presence of required files
    2. Database configuration
    3. Environment setup
    """
    directory = Path(directory).resolve()
    click.echo(f"Validating Claude Code workspace in: {directory}")

    # Required files
    required_files = [
        "CLAUDE.md",
        ".env",
        "pyproject.toml",
        "src/local_newsifier/config/settings.py",
    ]

    # Check required files
    all_files_present = True
    click.echo("\nChecking required files:")
    for file in required_files:
        file_path = directory / file
        if file_path.exists():
            click.echo(f"  ✓ {file}")
        else:
            click.echo(f"  ✗ {file} (missing)")
            all_files_present = False

    # Check database environment
    click.echo("\nChecking database configuration:")
    env_cursor_path = directory / ".env.cursor"
    if env_cursor_path.exists():
        with open(env_cursor_path, "r") as f:
            cursor_content = f.read()
            if "CURSOR_DB_ID" in cursor_content:
                click.echo("  ✓ .env.cursor contains CURSOR_DB_ID")
            else:
                click.echo("  ✗ .env.cursor missing CURSOR_DB_ID (invalid format)")
    else:
        click.echo("  ✗ .env.cursor file missing (database not initialized)")

    # Check .env file content
    click.echo("\nChecking environment configuration:")
    env_path = directory / ".env"
    required_env_vars = [
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_HOST",
        "POSTGRES_PORT",
    ]

    if env_path.exists():
        with open(env_path, "r") as f:
            env_content = f.read()
            for var in required_env_vars:
                if var in env_content:
                    click.echo(f"  ✓ {var}")
                else:
                    click.echo(f"  ✗ {var} (missing from .env)")

    # Summary
    click.echo("\nValidation summary:")
    if all_files_present and env_cursor_path.exists():
        click.echo("✅ Claude Code workspace is properly configured.")
    else:
        click.echo("⚠️ Claude Code workspace has configuration issues.")
        click.echo(
            "   Run 'nf claude init --force .' to reinitialize in current directory."
        )


if __name__ == "__main__":
    claude_group()
