#!/usr/bin/env python
"""Demo script to showcase the refactored architecture."""

import datetime
from pprint import pprint

from local_newsifier.core.factory import ToolFactory, ServiceFactory
from local_newsifier.database.session_manager import get_session_manager
from local_newsifier.flows.entity_tracking_flow_v2 import EntityTrackingFlow


def main():
    """Run the demo script."""
    print("Demonstrating refactored architecture...")
    
    # Get the session manager
    session_manager = get_session_manager()
    
    # Create services using factories
    entity_service = ServiceFactory.create_entity_service(
        session_manager=session_manager
    )
    
    # Create tools using factories
    entity_tracker = ToolFactory.create_entity_tracker(
        session_manager=session_manager,
        entity_service=entity_service
    )
    
    # Create flows using the tools
    entity_tracking_flow = EntityTrackingFlow(
        session_manager=session_manager,
        entity_tracker=entity_tracker
    )
    
    # Process any new articles
    print("\nProcessing new articles...")
    try:
        results = entity_tracking_flow.process_new_articles()
        print(f"Processed {len(results)} articles.")
        if results:
            print("\nSample article results:")
            pprint(results[0])
    except Exception as e:
        print(f"Error processing articles: {e}")
    
    # Get entity dashboard
    print("\nGenerating entity dashboard (last 30 days)...")
    try:
        dashboard = entity_tracking_flow.get_entity_dashboard(days=30)
        print(f"Found {dashboard['entity_count']} entities with {dashboard['total_mentions']} total mentions.")
        if dashboard["entities"]:
            print("\nTop entities:")
            for entity in dashboard["entities"][:5]:  # Show top 5
                print(f"- {entity['name']} ({entity['mention_count']} mentions)")
    except Exception as e:
        print(f"Error generating dashboard: {e}")
    
    # Show how to resolve an entity
    print("\nDemonstrating entity resolution:")
    try:
        entity = entity_service.resolve_entity("Joe Biden", "PERSON")
        print(f"Resolved 'Joe Biden' to canonical entity: {entity['name']} (ID: {entity['id']})")
    except Exception as e:
        print(f"Error resolving entity: {e}")
    
    print("\nRefactored architecture demo complete.")


if __name__ == "__main__":
    main()
