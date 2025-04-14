"""Demo script for entity tracking functionality."""

import argparse
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

from local_newsifier.config.database import get_db_session
from local_newsifier.database.manager import DatabaseManager
from local_newsifier.flows.entity_tracking_flow import EntityTrackingFlow
from local_newsifier.models.database.article import ArticleCreate, ArticleDB
from local_newsifier.models.database.entity import EntityCreate

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def add_sample_articles(db_manager: DatabaseManager):
    """Add sample articles to the database."""
    logger.info("Adding sample articles...")

    # Get current timestamp for unique URLs
    timestamp = int(datetime.now(timezone.utc).timestamp())

    # Sample articles with different entities
    articles = [
        {
            "url": f"https://example.com/tech-news-{timestamp}",
            "title": "Tech Giants Announce AI Partnership",
            "source": "Tech News",
            "content": (
                "Microsoft and Google have announced a groundbreaking partnership "
                "in artificial intelligence research. The collaboration, announced "
                "in Silicon Valley, will focus on developing responsible AI "
                "technologies. Satya Nadella, CEO of Microsoft, emphasized the "
                "importance of industry cooperation."
            ),
            "published_at": datetime.now(timezone.utc),
            "status": "new"
        },
        {
            "url": f"https://example.com/local-news-{timestamp}",
            "title": "City Council Approves New Development",
            "source": "Local News",
            "content": (
                "The San Francisco City Council has approved a major development "
                "project in the Mission District. Mayor London Breed supported "
                "the initiative, stating it would create new jobs. The project, "
                "led by Bay Area Development Corp, will include affordable housing."
            ),
            "published_at": datetime.now(timezone.utc),
            "status": "new"
        }
    ]

    for article_data in articles:
        try:
            article = ArticleCreate(**article_data)
            created_article = db_manager.create_article(article)
            logger.info(f"Added article: {created_article.title}")
        except Exception as e:
            logger.error(f"Error adding article: {e}")


def process_articles(db_manager: DatabaseManager):
    """Process articles for entity tracking."""
    flow = EntityTrackingFlow(db_manager)
    
    # Process all articles
    results = flow.process_new_articles()
    
    # Display results
    logger.info(f"\nProcessed {len(results)} articles:")
    for result in results:
        logger.info(f"\nArticle: {result['title']}")
        logger.info(f"Found {result['entity_count']} entities:")
        for entity in result['entities']:
            logger.info(f"  - {entity['original_text']} -> {entity['canonical_name']}")
            logger.info(f"    Sentiment: {entity['sentiment_score']:.2f}")
            logger.info(f"    Context: {entity['context']}")


def show_entity_dashboard(db_manager: DatabaseManager, days: int = 30):
    """Show entity tracking dashboard."""
    flow = EntityTrackingFlow(db_manager)
    
    # Get dashboard data
    dashboard = flow.get_entity_dashboard(days=days)
    
    # Display dashboard
    logger.info("\n=== Entity Tracking Dashboard ===")
    logger.info(f"Time period: {dashboard['date_range']['start']} to {dashboard['date_range']['end']}")
    logger.info(f"Total entities: {dashboard['entity_count']}")
    logger.info(f"Total mentions: {dashboard['total_mentions']}")
    
    logger.info("\nTop entities:")
    for entity in dashboard['entities']:
        logger.info(f"\n{entity['name']} ({entity['type']})")
        logger.info(f"  Mentions: {entity['mention_count']}")
        logger.info(f"  First seen: {entity['first_seen']}")
        logger.info(f"  Last seen: {entity['last_seen']}")
        if entity['sentiment_trend']:
            logger.info(f"  Recent sentiment trend: {entity['sentiment_trend']}")


def show_entity_relationships(db_manager: DatabaseManager, entity_id: int, days: int = 30):
    """Show relationships between entities."""
    flow = EntityTrackingFlow(db_manager)
    
    # Get relationships data
    relationships = flow.find_entity_relationships(entity_id, days)
    
    # Display relationships
    logger.info(f"\n=== Entity Relationships for {relationships['entity_name']} ===")
    logger.info(f"Time period: {relationships['date_range']['start']} to {relationships['date_range']['end']}")
    
    logger.info("\nTop co-occurring entities:")
    for rel in relationships['relationships']:
        logger.info(f"\n{rel['entity_name']} ({rel['entity_type']})")
        logger.info(f"  Co-occurrences: {rel['co_occurrence_count']}")
        logger.info(f"  Articles: {rel['article_count']}")


def main():
    """Run the entity tracking demo."""
    parser = argparse.ArgumentParser(description="Entity tracking demo script")
    parser.add_argument("--days", type=int, default=30, help="Number of days to analyze")
    args = parser.parse_args()

    # Initialize database connection
    session_factory = get_db_session()
    session = session_factory()
    db_manager = DatabaseManager(session)

    try:
        # Add sample articles
        add_sample_articles(db_manager)

        # Process articles for entity tracking
        process_articles(db_manager)

        # Show entity dashboard
        show_entity_dashboard(db_manager, days=args.days)

        # Get first entity ID for relationship demo
        first_entity = db_manager.get_canonical_entities_by_type("PERSON")[0]
        if first_entity:
            show_entity_relationships(db_manager, first_entity.id, days=args.days)

    finally:
        session.close()


if __name__ == "__main__":
    main() 