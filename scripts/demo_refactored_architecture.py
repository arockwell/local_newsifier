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
    
    # Create flows using services directly
    entity_tracking_flow = EntityTrackingFlow(
        session_manager=session_manager,
        entity_service=entity_service
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
    
    # Process an article directly with the service
    print("\nDemonstrating direct service usage:")
    try:
        article_id = 1  # Assuming article ID 1 exists
        processed = entity_service.process_article(
            article_id=article_id,
            content="President Joe Biden met with Vice President Kamala Harris today.",
            title="Biden and Harris Meet",
            published_at=datetime.datetime.now(datetime.timezone.utc)
        )
        print(f"Processed article directly with service, found {len(processed)} entities")
        if processed:
            print("\nEntities found:")
            for entity in processed:
                print(f"- {entity['canonical_name']} (sentiment: {entity['sentiment_score']:.2f})")
    except Exception as e:
        print(f"Error with direct service usage: {e}")
    
    print("\nRefactored architecture demo complete.")


if __name__ == "__main__":
    main()
