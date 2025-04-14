"""Demo setup script for Local Newsifier."""

import sys
from datetime import datetime, timezone
from pathlib import Path

# Add src directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from local_newsifier.database.manager import DatabaseManager
from local_newsifier.models.database import ArticleDB, ArticleCreate, Base
from local_newsifier.models.entity_tracking import (CanonicalEntityDB, EntityMentionContextDB,
                                                   EntityProfileDB, entity_mentions, entity_relationships,
                                                   CanonicalEntityCreate, EntityMentionContextCreate, EntityMentionCreate)
from local_newsifier.config.database import get_db_session, get_database

def setup_demo():
    """Initialize database and load sample data."""
    # Initialize database engine and create tables
    engine = get_database()
    Base.metadata.drop_all(engine)  # Drop all tables
    Base.metadata.create_all(engine)  # Create all tables
    
    # Initialize database session
    Session = get_db_session()
    session = Session()
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager(session)
        
        # Sample articles
        sample_articles = [
            ArticleCreate(
                title="Local Business Expands Operations",
                url="https://example.com/business-expansion",
                content="Local tech company TechCorp announced plans to expand its operations in the downtown area. CEO John Smith stated that the expansion will create 50 new jobs.",
                published_at=datetime.now(timezone.utc),
                status="scraped"
            ),
            ArticleCreate(
                title="City Council Approves New Development",
                url="https://example.com/city-council",
                content="The City Council voted unanimously to approve a new development project. Council member Jane Doe emphasized the project's economic benefits.",
                published_at=datetime.now(timezone.utc),
                status="scraped"
            ),
            ArticleCreate(
                title="Local School District Receives Grant",
                url="https://example.com/school-grant",
                content="The local school district received a $1 million grant from the state. Superintendent Robert Johnson announced plans to use the funds for technology upgrades.",
                published_at=datetime.now(timezone.utc),
                status="scraped"
            )
        ]
        
        # Add sample articles to database
        articles = []
        for article in sample_articles:
            articles.append(db_manager.create_article(article))
        
        # Create canonical entities
        entities = {
            "john_smith": db_manager.create_canonical_entity(
                CanonicalEntityCreate(
                    name="John Smith",
                    entity_type="PERSON",
                    description="CEO of TechCorp",
                    entity_metadata={"role": "CEO", "company": "TechCorp"}
                )
            ),
            "jane_doe": db_manager.create_canonical_entity(
                CanonicalEntityCreate(
                    name="Jane Doe",
                    entity_type="PERSON",
                    description="City Council Member",
                    entity_metadata={"role": "Council Member", "organization": "City Council"}
                )
            ),
            "robert_johnson": db_manager.create_canonical_entity(
                CanonicalEntityCreate(
                    name="Robert Johnson",
                    entity_type="PERSON",
                    description="School District Superintendent",
                    entity_metadata={"role": "Superintendent", "organization": "School District"}
                )
            ),
            "techcorp": db_manager.create_canonical_entity(
                CanonicalEntityCreate(
                    name="TechCorp",
                    entity_type="ORG",
                    description="Local technology company",
                    entity_metadata={"industry": "Technology", "location": "Downtown"}
                )
            ),
            "city_council": db_manager.create_canonical_entity(
                CanonicalEntityCreate(
                    name="City Council",
                    entity_type="ORG",
                    description="Local government body",
                    entity_metadata={"type": "Government", "jurisdiction": "City"}
                )
            ),
            "school_district": db_manager.create_canonical_entity(
                CanonicalEntityCreate(
                    name="School District",
                    entity_type="ORG",
                    description="Local educational institution",
                    entity_metadata={"type": "Education", "jurisdiction": "Local"}
                )
            )
        }
        
        # Create entity mentions
        for article in articles:
            for entity in entities.values():
                db_manager.create_entity_mention(
                    EntityMentionCreate(
                        article_id=article.id,
                        canonical_entity_id=entity.id,
                        mention_text=entity.name,
                        context=EntityMentionContextCreate(
                            sentence="Sample context sentence",
                            paragraph="Sample context paragraph",
                            position=0
                        )
                    )
                )
        
        print("Demo setup completed successfully!")
        
    finally:
        session.close()

if __name__ == "__main__":
    setup_demo() 