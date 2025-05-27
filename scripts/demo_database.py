"""Demo script for database functionality."""

import logging
from datetime import UTC, datetime

from local_newsifier.crud.analysis_result import analysis_result as analysis_result_crud
from local_newsifier.crud.article import article as article_crud
from local_newsifier.crud.entity import entity as entity_crud
from local_newsifier.database.engine import get_session
from local_newsifier.models.analysis_result import AnalysisResult
from local_newsifier.models.article import Article
from local_newsifier.models.entity import Entity

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def show_database_state(session):
    """Show current state of the database."""
    logger.info("\n=== Current Database State ===")

    # Get all articles
    articles = session.query(Article).all()
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
                f"  - {entity.text} ({entity.entity_type}, " f"confidence: {entity.confidence})"
            )

        # Analysis Results
        logger.info("\nAnalysis Results:")
        for result in article.analysis_results:
            logger.info(f"  - {result.analysis_type}: {result.results}")

        logger.info("-" * 50)


def main():
    """Run the database demo."""
    # Use a context manager for the session
    with get_session() as session:
        # Show current state
        show_database_state(session)

        # Create a new article with unique URL
        logger.info("\nCreating new article...")
        timestamp = datetime.now(UTC).timestamp()
        article = Article(
            url=f"https://example.com/demo-{timestamp}",
            title="New Demo Article",
            content=("This is a new demo article for testing the database functionality."),
            published_at=datetime.now(UTC),
            status="new",
            source="Demo Source",
            scraped_at=datetime.now(UTC),
        )
        created_article = article_crud.create(session, obj_in=article)
        logger.info(f"Created article with ID: {created_article.id}")

        # Add an entity
        logger.info("Adding entity to article...")
        entity = Entity(
            article_id=created_article.id,
            text="New Demo Entity",
            entity_type="PERSON",
            confidence=0.95,
        )
        created_entity = entity_crud.create(session, obj_in=entity)
        logger.info(f"Added entity: {created_entity.text} ({created_entity.entity_type})")

        # Add analysis result
        logger.info("Adding analysis result...")
        result = AnalysisResult(
            article_id=created_article.id,
            analysis_type="NER",
            results={"entities": ["New Demo Entity"]},
        )
        created_result = analysis_result_crud.create(session, obj_in=result)
        logger.info(f"Added analysis result: {created_result.analysis_type}")

        # Update article status
        logger.info("Updating article status...")
        updated_article = article_crud.update_status(
            session, article_id=created_article.id, status="analyzed"
        )
        if updated_article:
            logger.info(f"Updated article status to: {updated_article.status}")
        else:
            logger.warning("Failed to update article status")

        # Show final state
        show_database_state(session)


if __name__ == "__main__":
    main()
