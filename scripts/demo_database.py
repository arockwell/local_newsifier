"""Demo script for database functionality."""

import logging
from datetime import UTC, datetime

from local_newsifier.config.database import get_db_session
from local_newsifier.database.manager import DatabaseManager
from local_newsifier.models.database import (AnalysisResultCreate,
                                             ArticleCreate, ArticleDB,
                                             EntityCreate)

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def show_database_state(db_manager):
    """Show current state of the database."""
    logger.info("\n=== Current Database State ===")

    # Get all articles
    articles = db_manager.session.query(ArticleDB).all()
    logger.info(f"\nFound {len(articles)} articles in database:")

    for article in articles:
        logger.info(f"\nArticle ID: {article.id}")
        logger.info(f"URL: {article.url}")
        logger.info(f"Title: {article.title}")
        logger.info(f"Status: {article.status}")
        logger.info(f"Published: {article.published_at}")
        logger.info(f"Scraped: {article.scraped_at}")

        # Entities
        logger.info("\nEntities:")
        for entity in article.entities:
            logger.info(
                f"  - {entity.text} ({entity.entity_type}, confidence: {entity.confidence})"
            )

        # Analysis Results
        logger.info("\nAnalysis Results:")
        for result in article.analysis_results:
            logger.info(f"  - {result.analysis_type}: {result.results}")

        logger.info("-" * 50)


def main():
    # Get database session
    session_factory = get_db_session(".env.test")
    session = session_factory()
    db_manager = DatabaseManager(session)

    try:
        # Show current state
        show_database_state(db_manager)

        # Create a new article with unique URL
        logger.info("\nCreating new article...")
        article = ArticleCreate(
            url=f"https://example.com/demo-{datetime.now(UTC).timestamp()}",
            title="New Demo Article",
            content="This is a new demo article for testing the database functionality.",
            published_at=datetime.now(UTC),
            status="new",
        )
        created_article = db_manager.create_article(article)
        logger.info(f"Created article with ID: {created_article.id}")

        # Add an entity
        logger.info("Adding entity to article...")
        entity = EntityCreate(
            article_id=created_article.id,
            text="New Demo Entity",
            entity_type="PERSON",
            confidence=0.95,
        )
        created_entity = db_manager.add_entity(entity)
        logger.info(
            f"Added entity: {created_entity.text} ({created_entity.entity_type})"
        )

        # Add analysis result
        logger.info("Adding analysis result...")
        result = AnalysisResultCreate(
            article_id=created_article.id,
            analysis_type="NER",
            results={"entities": ["New Demo Entity"]},
        )
        created_result = db_manager.add_analysis_result(result)
        logger.info(f"Added analysis result: {created_result.analysis_type}")

        # Update article status
        logger.info("Updating article status...")
        updated_article = db_manager.update_article_status(
            created_article.id, "analyzed"
        )
        if updated_article:
            logger.info(f"Updated article status to: {updated_article.status}")
        else:
            logger.warning("Failed to update article status")

        # Show final state
        show_database_state(db_manager)

    finally:
        session.close()


if __name__ == "__main__":
    main()
