"""Demo setup script for Local Newsifier."""

from datetime import datetime, timezone
from pathlib import Path

from .database.manager import DatabaseManager
from .models.database import ArticleDB

def setup_demo():
    """Initialize database and load sample data."""
    # Initialize database
    db_manager = DatabaseManager()
    db_manager.initialize_database()
    
    # Sample articles
    sample_articles = [
        ArticleDB(
            title="Local Business Expands Operations",
            url="https://example.com/business-expansion",
            content="Local tech company TechCorp announced plans to expand its operations in the downtown area. CEO John Smith stated that the expansion will create 50 new jobs.",
            published_at=datetime.now(timezone.utc),
            status="scraped"
        ),
        ArticleDB(
            title="City Council Approves New Development",
            url="https://example.com/city-council",
            content="The City Council voted unanimously to approve a new development project. Council member Jane Doe emphasized the project's economic benefits.",
            published_at=datetime.now(timezone.utc),
            status="scraped"
        ),
        ArticleDB(
            title="Local School District Receives Grant",
            url="https://example.com/school-grant",
            content="The local school district received a $1 million grant from the state. Superintendent Robert Johnson announced plans to use the funds for technology upgrades.",
            published_at=datetime.now(timezone.utc),
            status="scraped"
        )
    ]
    
    # Add sample articles to database
    for article in sample_articles:
        db_manager.add_article(article)
    
    print("Demo setup complete. Added 3 sample articles to the database.")

if __name__ == "__main__":
    setup_demo() 