"""Script to clear the articles table and all dependent tables."""

import logging

from sqlalchemy import text
from sqlmodel import Session, select

from local_newsifier.database.engine import get_engine
from local_newsifier.models.article import Article

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def confirm(prompt):
    """Prompt for confirmation."""
    response = input(f"{prompt} (yes/no): ")
    return response.lower() in ("yes", "y")


def clear_articles():
    """Remove all articles and related data."""
    engine = get_engine()

    with Session(engine) as session:
        # Check how many articles we'll delete
        articles_count = session.exec(select(Article)).all()
        logger.info(f"Found {len(articles_count)} articles to delete")

        if not confirm("This will delete ALL articles and related data. Continue?"):
            logger.info("Operation cancelled")
            return

        # Use SQL directly to handle all dependencies
        logger.info("Deleting all related entity data...")
        session.exec(text("DELETE FROM entity_mention_contexts"))
        session.exec(text("DELETE FROM entity_profiles"))
        session.exec(text("DELETE FROM canonical_entities"))
        session.exec(text("DELETE FROM entity_relationships"))
        session.commit()

        # Delete entities
        logger.info("Deleting entities...")
        session.exec(text("DELETE FROM entities"))
        session.commit()

        # Delete analysis results
        logger.info("Deleting analysis results...")
        session.exec(text("DELETE FROM analysis_results"))
        session.commit()

        # Finally delete articles
        logger.info("Deleting articles...")
        session.exec(text("DELETE FROM articles"))
        session.commit()

        logger.info("Articles table cleared successfully")


if __name__ == "__main__":
    clear_articles()
