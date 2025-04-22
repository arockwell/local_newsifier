#!/usr/bin/env python
"""Database migration script using Alembic.

This script provides a convenient way to run Alembic migration commands
for the Local Newsifier database.
"""

import argparse
import logging
import os
import subprocess
import sys

from local_newsifier.config.settings import get_settings
from local_newsifier.database.engine import get_engine

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("db_migration")


def verify_database_connection():
    """Verify database connection.

    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        logger.info("Verifying database connection...")
        settings = get_settings()
        logger.info(f"Using database URL: {settings.DATABASE_URL}")
        
        engine = get_engine()
        if engine is None:
            logger.error("Failed to create database engine")
            return False
            
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return False


def run_alembic_command(command, *args):
    """Run an Alembic command with the given arguments.

    Args:
        command: The Alembic command to run
        *args: Additional arguments for the command

    Returns:
        bool: True if the command executed successfully, False otherwise
    """
    try:
        cmd = ["alembic", command]
        if args:
            cmd.extend(args)
            
        logger.info(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
            
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return False


def upgrade(revision="head"):
    """Upgrade the database to the specified revision.

    Args:
        revision: Target revision, default is "head"

    Returns:
        bool: True if upgrade was successful, False otherwise
    """
    logger.info(f"Upgrading database to revision: {revision}")
    if not verify_database_connection():
        return False
    
    return run_alembic_command("upgrade", revision)


def downgrade(revision):
    """Downgrade the database to the specified revision.

    Args:
        revision: Target revision to downgrade to

    Returns:
        bool: True if downgrade was successful, False otherwise
    """
    if not revision:
        logger.error("Revision is required for downgrade")
        return False
        
    logger.info(f"Downgrading database to revision: {revision}")
    if not verify_database_connection():
        return False
    
    return run_alembic_command("downgrade", revision)


def create_migration(message):
    """Create a new migration revision.

    Args:
        message: Migration message

    Returns:
        bool: True if creation was successful, False otherwise
    """
    if not message:
        logger.error("Message is required for creating a migration")
        return False
        
    logger.info(f"Creating new migration with message: {message}")
    return run_alembic_command("revision", "--autogenerate", "-m", message)


def show_history():
    """Show migration history.

    Returns:
        bool: True if command was successful, False otherwise
    """
    logger.info("Showing migration history")
    return run_alembic_command("history", "--verbose")


def show_current():
    """Show current migration revision.

    Returns:
        bool: True if command was successful, False otherwise
    """
    logger.info("Showing current migration revision")
    return run_alembic_command("current", "--verbose")


def main():
    """Main function to parse arguments and run commands."""
    parser = argparse.ArgumentParser(description="Database migration tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Upgrade command
    upgrade_parser = subparsers.add_parser("upgrade", help="Upgrade database")
    upgrade_parser.add_argument(
        "--revision", default="head", help="Target revision (default: head)"
    )
    
    # Downgrade command
    downgrade_parser = subparsers.add_parser("downgrade", help="Downgrade database")
    downgrade_parser.add_argument(
        "--revision", required=True, help="Target revision"
    )
    
    # Create migration command
    create_parser = subparsers.add_parser("create", help="Create new migration")
    create_parser.add_argument(
        "--message", required=True, help="Migration message"
    )
    
    # History command
    subparsers.add_parser("history", help="Show migration history")
    
    # Current command
    subparsers.add_parser("current", help="Show current migration revision")
    
    # Verify command
    subparsers.add_parser("verify", help="Verify database connection")
    
    args = parser.parse_args()
    
    if args.command == "upgrade":
        success = upgrade(args.revision)
    elif args.command == "downgrade":
        success = downgrade(args.revision)
    elif args.command == "create":
        success = create_migration(args.message)
    elif args.command == "history":
        success = show_history()
    elif args.command == "current":
        success = show_current()
    elif args.command == "verify":
        success = verify_database_connection()
    else:
        parser.print_help()
        return 0
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
