"""Script to add test headlines to the database."""

import logging
from datetime import datetime, timedelta, UTC

from local_newsifier.database.engine import get_session
from local_newsifier.database.adapter import create_article
from local_newsifier.models.pydantic_models import ArticleCreate

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Sample headlines with different topics and dates
TEST_HEADLINES = [
    {
        "title": "City Council Approves New Downtown Development Project",
        "url": "https://example.com/news/1",
        "published_at": datetime.now(UTC) - timedelta(days=1),
    },
    {
        "title": "Local High School Football Team Wins State Championship",
        "url": "https://example.com/news/2",
        "published_at": datetime.now(UTC) - timedelta(days=2),
    },
    {
        "title": "New Restaurant Opening in Downtown Gainesville",
        "url": "https://example.com/news/3",
        "published_at": datetime.now(UTC) - timedelta(days=3),
    },
    {
        "title": "University of Florida Announces New Research Initiative",
        "url": "https://example.com/news/4",
        "published_at": datetime.now(UTC) - timedelta(days=4),
    },
    {
        "title": "Local Business Owners Discuss Economic Growth",
        "url": "https://example.com/news/5",
        "published_at": datetime.now(UTC) - timedelta(days=5),
    },
    {
        "title": "City Council Meeting Addresses Downtown Development",
        "url": "https://example.com/news/6",
        "published_at": datetime.now(UTC) - timedelta(days=6),
    },
    {
        "title": "Gainesville High School Students Win Science Competition",
        "url": "https://example.com/news/7",
        "published_at": datetime.now(UTC) - timedelta(days=7),
    },
    {
        "title": "New Downtown Development Project Faces Delays",
        "url": "https://example.com/news/8",
        "published_at": datetime.now(UTC) - timedelta(days=8),
    },
    {
        "title": "Local Restaurant Scene Continues to Grow",
        "url": "https://example.com/news/9",
        "published_at": datetime.now(UTC) - timedelta(days=9),
    },
    {
        "title": "University Research Leads to New Downtown Development",
        "url": "https://example.com/news/10",
        "published_at": datetime.now(UTC) - timedelta(days=10),
    },
]

def main():
    """Add test headlines to the database."""
    with get_session() as session:
        try:
            # Add each headline to the database
            for headline in TEST_HEADLINES:
                article = ArticleCreate(
                    title=headline["title"],
                    url=headline["url"],
                    published_at=headline["published_at"],
                    status="analyzed"
                )
                create_article(article, session=session)
                logger.info(f"Added headline: {headline['title']}")
                
            logger.info("Successfully added all test headlines to the database")
            
        except Exception as e:
            logger.error(f"Error adding test headlines: {e}")

if __name__ == "__main__":
    main() 