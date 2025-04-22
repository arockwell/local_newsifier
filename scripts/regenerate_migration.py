#!/usr/bin/env python
"""
Script to generate a clean initial Alembic migration.

This script:
1. Creates a temporary database
2. Configures Alembic to use the temporary database
3. Generates a clean initial migration
4. Cleans up the temporary database
"""

import os
import subprocess
import tempfile
import shutil
import time
from pathlib import Path
import argparse

def run_command(command, check=True):
    """Run a shell command and return the output."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, check=check, 
                         text=True, capture_output=True)
    if result.stdout:
        print(f"Output: {result.stdout.strip()}")
    if result.stderr and not check:
        print(f"Error: {result.stderr.strip()}")
    return result

def main():
    parser = argparse.ArgumentParser(description="Generate a clean initial Alembic migration")
    parser.add_argument("--message", default="initial_schema", 
                        help="Migration message (default: 'initial_schema')")
    args = parser.parse_args()
    
    # Create a temporary database name
    temp_db_name = f"temp_migration_{int(time.time())}"
    
    try:
        # Check if PostgreSQL is available
        result = run_command("psql --version", check=False)
        if result.returncode != 0:
            print("PostgreSQL command line tools not found. Make sure PostgreSQL is installed and psql is in your PATH.")
            return 1
        
        # Create a temporary database
        print(f"\n=== Creating temporary database: {temp_db_name} ===")
        run_command(f"createdb {temp_db_name}")
        
        # Create a temporary .env file
        original_env = ".env"
        temp_env = ".env.migration_temp"
        has_original_env = os.path.exists(original_env)
        
        if has_original_env:
            print("\n=== Backing up original .env file ===")
            shutil.copy2(original_env, temp_env)
        
        # Create a new .env file pointing to our temporary database
        print("\n=== Creating temporary .env file ===")
        with open(original_env, "w") as f:
            f.write(f"""# Temporary database for migration generation
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB={temp_db_name}

# App Settings
LOG_LEVEL=INFO
ENVIRONMENT=development
""")
        
        # Make sure the versions directory exists
        versions_dir = Path("alembic/versions")
        versions_dir.mkdir(exist_ok=True)
        
        # Remove any existing migrations
        print("\n=== Removing existing migrations ===")
        for migration_file in versions_dir.glob("*.py"):
            print(f"Removing {migration_file}")
            migration_file.unlink()
        
        # Generate the initial migration
        print(f"\n=== Generating initial migration with message: {args.message} ===")
        run_command(f"alembic revision --autogenerate -m \"{args.message}\"")
        
        print("\n=== Migration generated successfully ===")
        
        # List the generated migration
        for migration_file in versions_dir.glob("*.py"):
            print(f"Created migration file: {migration_file}")
            
    finally:
        # Clean up the temporary database
        print(f"\n=== Dropping temporary database: {temp_db_name} ===")
        run_command(f"dropdb {temp_db_name}", check=False)
        
        # Restore the original .env file
        if has_original_env:
            print("\n=== Restoring original .env file ===")
            shutil.move(temp_env, original_env)
        else:
            print("\n=== Removing temporary .env file ===")
            os.remove(original_env)
    
    print("\n=== Done! ===")
    return 0

if __name__ == "__main__":
    exit(main())
