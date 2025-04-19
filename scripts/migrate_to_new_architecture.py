#!/usr/bin/env python
"""Migration script to demonstrate how to migrate from old to new architecture."""

import datetime
from pprint import pprint

# Old imports
from sqlmodel import Session
from local_newsifier.database.engine import with_session
from local_newsifier.tools.entity_tracker import EntityTracker as OldEntityTracker
from local_newsifier.flows.entity_tracking_flow import EntityTrackingFlow as OldEntityTrackingFlow

# New imports
from local_newsifier.core.factory import ServiceFactory
from local_newsifier.database.session_manager import get_session_manager
from local_newsifier.flows.entity_tracking_flow_v2 import EntityTrackingFlow as NewEntityTrackingFlow


def demonstrate_old_approach():
    """Demonstrate the old approach with session passing."""
    print("\n==== OLD ARCHITECTURE ====")
    
    # Create tracker directly, passing session
    old_tracker = OldEntityTracker()
    
    # Create flow, passing session
    old_flow = OldEntityTrackingFlow()
    
    # Use the old flow with decorated session management
    print("Processing articles with old architecture...")
    try:
        # Note how the session is implicitly handled by @with_session decorator
        results = old_flow.process_new_articles()
        print(f"Processed {len(results)} articles with old architecture.")
    except Exception as e:
        print(f"Error with old architecture: {e}")


def demonstrate_new_approach():
    """Demonstrate the new approach with dependency injection."""
    print("\n==== NEW ARCHITECTURE ====")
    
    # Get the session manager
    session_manager = get_session_manager()
    
    # Create services using factories
    entity_service = ServiceFactory.create_entity_service(
        session_manager=session_manager
    )
    
    # Create flows using services directly
    entity_tracking_flow = NewEntityTrackingFlow(
        session_manager=session_manager,
        entity_service=entity_service
    )
    
    # Use the new flow with explicit context manager
    print("Processing articles with new architecture...")
    try:
        # Note how session management is now explicit with context manager
        results = entity_tracking_flow.process_new_articles()
        print(f"Processed {len(results)} articles with new architecture.")
    except Exception as e:
        print(f"Error with new architecture: {e}")


def demonstrate_gradual_migration():
    """Demonstrate how to gradually migrate code."""
    print("\n==== GRADUAL MIGRATION ====")
    
    # Step 1: Get session manager but still use old components
    session_manager = get_session_manager()
    
    # Step 2: Use old components with session manager
    # This is a bridge between old and new architectures
    with session_manager.session() as session:
        # We can use the old architecture with the new session management
        old_tracker = OldEntityTracker(session=session)
        old_flow = OldEntityTrackingFlow(session=session)
        
        print("Processing with old components but new session management...")
        try:
            # Explicitly pass session to old-style functions
            results = old_flow.process_article(1, session=session)
            print(f"Processed article with hybrid approach.")
        except Exception as e:
            print(f"Error with hybrid approach: {e}")
    
    # Step 3: Now use new components with session manager (full migration)
    print("Full migration to new architecture...")
    entity_service = ServiceFactory.create_entity_service(
        session_manager=session_manager
    )
    entity_flow = NewEntityTrackingFlow(
        session_manager=session_manager,
        entity_service=entity_service
    )
    
    # New architecture handles sessions internally
    try:
        results = entity_flow.process_article(1)
        print("Successfully migrated to new architecture!")
    except Exception as e:
        print(f"Error with full migration: {e}")


def migration_patterns():
    """Print out common migration patterns."""
    print("\n==== MIGRATION PATTERNS ====")
    
    print("""
HOW TO MIGRATE CODE FROM OLD TO NEW ARCHITECTURE

1. FROM @with_session decorator:
   
   # Old approach:
   @with_session
   def my_function(param1, param2, *, session=None):
       # Use session...
       session.query(...)
   
   # New approach:
   def my_function(param1, param2, session_manager=None):
       sm = session_manager or get_session_manager()
       with sm.session() as session:
           # Use session...
           session.query(...)

2. FROM direct session usage:
   
   # Old approach:
   session = Session(get_engine())
   try:
       # Use session...
       session.commit()
   finally:
       session.close()
   
   # New approach:
   session_manager = get_session_manager()
   with session_manager.session() as session:
       # Use session...
       # No need for explicit commit/rollback/close

3. FROM tools to services:
   
   # Old approach:
   tracker = EntityTracker(session=session)
   tracker.process_article(article_id, content, title, published_at)
   
   # New approach:
   service = ServiceFactory.create_entity_service(
       session_manager=session_manager
   )
   service.process_article(article_id, content, title, published_at)

4. FROM direct flow instantiation:
   
   # Old approach:
   flow = EntityTrackingFlow(session=session)
   
   # New approach:
   flow = EntityTrackingFlow(
       session_manager=session_manager,
       entity_service=service  # Pass services directly
   )
""")


def main():
    """Run the migration examples."""
    print("MIGRATION EXAMPLES FROM OLD TO NEW ARCHITECTURE")
    
    demonstrate_old_approach()
    demonstrate_new_approach()
    demonstrate_gradual_migration()
    migration_patterns()
    
    print("\nMigration script complete - refer to the patterns for transitioning your code.")


if __name__ == "__main__":
    main()
