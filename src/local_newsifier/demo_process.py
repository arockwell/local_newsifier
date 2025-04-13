"""Demo processing script for Local Newsifier."""

from .database.manager import DatabaseManager
from .flows.news_pipeline import NewsPipelineFlow
from .flows.entity_tracking_flow import EntityTrackingFlow

def process_demo():
    """Process sample articles and run entity tracking."""
    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Initialize flows
    pipeline = NewsPipelineFlow()
    entity_tracking = EntityTrackingFlow(db_manager)
    
    # Get all articles
    articles = db_manager.get_articles_by_status("scraped")
    
    # Process each article
    for article in articles:
        print(f"Processing article: {article.title}")
        
        # Run pipeline
        state = pipeline.start_pipeline(article.url)
        if state.status == "analysis_succeeded":
            print(f"Successfully analyzed article: {article.title}")
        else:
            print(f"Failed to analyze article: {article.title}")
            print(f"Error: {state.error_details}")
    
    # Run entity tracking
    print("\nRunning entity tracking...")
    entity_results = entity_tracking.process_new_articles()
    
    # Print entity tracking results
    print("\nEntity Tracking Results:")
    for result in entity_results:
        print(f"\nArticle: {result['title']}")
        print(f"Entity Count: {result['entity_count']}")
        print("Entities:")
        for entity in result['entities']:
            print(f"- {entity['text']} ({entity['type']})")
    
    # Generate entity dashboard
    print("\nGenerating entity dashboard...")
    dashboard = entity_tracking.get_entity_dashboard(days=30)
    print(f"\nDashboard Summary:")
    print(f"Total Entities: {dashboard['entity_count']}")
    print(f"Total Mentions: {dashboard['total_mentions']}")
    
    # Find entity relationships
    print("\nFinding entity relationships...")
    for entity in dashboard['entities'][:3]:  # Analyze top 3 entities
        relationships = entity_tracking.find_entity_relationships(entity['id'])
        print(f"\nRelationships for {entity['name']}:")
        for rel in relationships['relationships'][:3]:  # Show top 3 relationships
            print(f"- {rel['entity_name']}: {rel['co_occurrence_count']} co-occurrences")

if __name__ == "__main__":
    process_demo() 