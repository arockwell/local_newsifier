#!/usr/bin/env python

"""
Script to verify database connection and tables.
This can be useful for debugging Railway deployment issues.
"""

import sys
import os
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

try:
    # Add src to path to allow local imports
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    from sqlmodel import select, text
    from local_newsifier.database.engine import get_engine
    from local_newsifier.config.settings import get_settings
    
    def verify_db_connection():
        """Verify database connection and print detailed information."""
        print("\n=== DATABASE CONNECTION TEST ===")
        print(f"Time: {datetime.now().isoformat()}")
        
        # Get settings
        settings = get_settings()
        db_url = settings.DATABASE_URL
        safe_url = db_url
        if settings.POSTGRES_PASSWORD and settings.POSTGRES_PASSWORD in db_url:
            safe_url = db_url.replace(settings.POSTGRES_PASSWORD, "********")
        
        print(f"Database URL: {safe_url}")
        print(f"Database Host: {settings.POSTGRES_HOST}")
        print(f"Database Port: {settings.POSTGRES_PORT}")
        print(f"Database Name: {settings.POSTGRES_DB}")
        print(f"Database User: {settings.POSTGRES_USER}")
        print(f"Pool Size: {settings.DB_POOL_SIZE}")
        
        # Try to get database engine
        print("\n--- Attempting to create database engine ---")
        start_time = time.time()
        try:
            engine = get_engine()
            if engine is None:
                print("ERROR: Engine creation failed, got None")
                return False
            
            print(f"Engine created successfully in {(time.time() - start_time):.2f} seconds")
            
            # Test simple query
            print("\n--- Testing simple query ---")
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).fetchone()
                print(f"Query result: {result}")
            
            # Get database metadata
            print("\n--- Database Info ---")
            with engine.connect() as conn:
                # Get PostgreSQL version
                version = conn.execute(text("SELECT version()")).fetchone()[0]
                print(f"Database version: {version}")
                
                # List tables
                tables = conn.execute(text(
                    """
                    SELECT tablename 
                    FROM pg_catalog.pg_tables 
                    WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema'
                    """
                )).fetchall()
                
                print("\nTables in database:")
                if not tables:
                    print("No tables found")
                else:
                    for table in tables:
                        print(f"- {table[0]}")
                        # Get row count for each table
                        try:
                            count = conn.execute(text(
                                f"SELECT COUNT(*) FROM {table[0]}"
                            )).fetchone()[0]
                            print(f"  Rows: {count}")
                        except Exception as e:
                            print(f"  Error getting row count: {str(e)}")
            
            print("\nDatabase connection test SUCCESSFUL")
            return True
            
        except Exception as e:
            print(f"ERROR: {str(e)}")
            import traceback
            print(traceback.format_exc())
            print("\nDatabase connection test FAILED")
            return False
    
    if __name__ == "__main__":
        verify_db_connection()
        
except Exception as e:
    logger.error(f"Error: {str(e)}")
    import traceback
    logger.error(traceback.format_exc())
