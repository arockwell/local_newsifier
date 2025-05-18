#!/usr/bin/env python
"""
Apply event loop fixes to the Local Newsifier CLI.

This script replaces the current apify_config.py and main.py files with 
fixed versions that properly handle asyncio event loops.

Usage:
    python scripts/apply_event_loop_fixes.py

The script will:
1. Create backup files of the originals
2. Replace them with the fixed versions
3. Test that the 'nf apify-config list' command works properly
"""

import os
import sys
import shutil
import subprocess
import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# File paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLI_DIR = os.path.join(BASE_DIR, "src", "local_newsifier", "cli")

MAIN_ORIG = os.path.join(CLI_DIR, "main.py")
MAIN_FIXED = os.path.join(CLI_DIR, "main_fixed.py")
MAIN_BACKUP = os.path.join(CLI_DIR, f"main.py.bak.{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}")

APIFY_CONFIG_ORIG = os.path.join(CLI_DIR, "commands", "apify_config.py")
APIFY_CONFIG_FIXED = os.path.join(CLI_DIR, "commands", "apify_config_fixed.py")
APIFY_CONFIG_BACKUP = os.path.join(CLI_DIR, "commands", f"apify_config.py.bak.{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}")

def backup_and_replace(original_file, fixed_file, backup_file):
    """Backup the original file and replace it with the fixed version."""
    if not os.path.exists(fixed_file):
        logger.error(f"Fixed file {fixed_file} does not exist!")
        return False
    
    if not os.path.exists(original_file):
        logger.error(f"Original file {original_file} does not exist!")
        return False
    
    try:
        # Create backup
        logger.info(f"Creating backup of {original_file} to {backup_file}")
        shutil.copy2(original_file, backup_file)
        
        # Replace with fixed version
        logger.info(f"Replacing {original_file} with {fixed_file}")
        shutil.copy2(fixed_file, original_file)
        
        return True
    except Exception as e:
        logger.error(f"Error during backup and replace: {e}")
        return False

def test_cli_command():
    """Test that the apify-config list command works properly."""
    logger.info("Testing CLI command: nf apify-config list")
    
    # Set environment variables to enable debugging
    env = os.environ.copy()
    env["LOCAL_NEWSIFIER_DEBUG"] = "1"
    env["LOCAL_NEWSIFIER_EVENT_LOOP_DIAGNOSTICS"] = "1"
    
    # Run the command
    try:
        result = subprocess.run(
            ["nf", "apify-config", "list"], 
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=20
        )
        
        # Check result
        if result.returncode == 0:
            logger.info("CLI command executed successfully!")
            return True
        else:
            logger.error(f"CLI command failed with return code {result.returncode}")
            logger.error(f"Stderr: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error running CLI command: {e}")
        return False

def main():
    """Main entry point for the script."""
    logger.info("Applying event loop fixes to Local Newsifier CLI")
    
    # Check if fixed files exist
    if not os.path.exists(MAIN_FIXED) or not os.path.exists(APIFY_CONFIG_FIXED):
        logger.error("Fixed files not found! Run the script from the project root directory.")
        return 1
    
    # Backup and replace main.py
    if not backup_and_replace(MAIN_ORIG, MAIN_FIXED, MAIN_BACKUP):
        logger.error("Failed to replace main.py")
        return 1
    
    # Backup and replace apify_config.py
    if not backup_and_replace(APIFY_CONFIG_ORIG, APIFY_CONFIG_FIXED, APIFY_CONFIG_BACKUP):
        logger.error("Failed to replace apify_config.py")
        # Try to restore main.py
        logger.info("Restoring main.py from backup")
        shutil.copy2(MAIN_BACKUP, MAIN_ORIG)
        return 1
    
    logger.info("Files replaced successfully. Testing CLI command...")
    
    # Test CLI command
    if test_cli_command():
        logger.info("Success! The fixes have been applied and tested.")
        
        # Cleanup fixed files
        os.remove(MAIN_FIXED)
        os.remove(APIFY_CONFIG_FIXED)
        
        logger.info("Original files have been backed up to:")
        logger.info(f"  - {MAIN_BACKUP}")
        logger.info(f"  - {APIFY_CONFIG_BACKUP}")
        
        return 0
    else:
        logger.error("CLI command test failed. Restoring original files.")
        
        # Restore original files
        shutil.copy2(MAIN_BACKUP, MAIN_ORIG)
        shutil.copy2(APIFY_CONFIG_BACKUP, APIFY_CONFIG_ORIG)
        
        logger.info("Original files restored.")
        return 1

if __name__ == "__main__":
    sys.exit(main())