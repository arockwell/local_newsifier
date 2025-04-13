"""Demo setup script for Local Newsifier."""

from datetime import datetime, timezone
from pathlib import Path

from .database.manager import DatabaseManager
from .models.database import ArticleDB, ArticleCreate, Base
from .models.entity_tracking import (CanonicalEntityDB, EntityMentionContextDB,
                                   EntityProfileDB, entity_mentions, entity_relationships,
                                   CanonicalEntityCreate, EntityMentionContextCreate, EntityMentionCreate)
from .config.database import get_db_session, get_database

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
                    entity_metadata={"type": "Education", "level": "K-12"}
                )
            )
        }
        
        # Commit entities to database before creating mentions
        session.commit()
        
        # Add entity mentions and contexts
        for article in articles:
            if "TechCorp" in article.content:
                mention = db_manager.add_entity_mention(
                    EntityMentionCreate(
                        canonical_entity_id=entities["techcorp"].id,
                        article_id=article.id,
                        mention_text="TechCorp",
                        mention_type="ORG"
                    )
                )
                db_manager.add_entity_mention_context(
                    EntityMentionContextCreate(
                        entity_id=mention.id,
                        article_id=article.id,
                        context_text=article.content,
                        context_type="article",
                        sentiment_score=0.8
                    )
                )
            if "John Smith" in article.content:
                mention = db_manager.add_entity_mention(
                    EntityMentionCreate(
                        canonical_entity_id=entities["john_smith"].id,
                        article_id=article.id,
                        mention_text="John Smith",
                        mention_type="PERSON"
                    )
                )
                db_manager.add_entity_mention_context(
                    EntityMentionContextCreate(
                        entity_id=mention.id,
                        article_id=article.id,
                        context_text=article.content,
                        context_type="article",
                        sentiment_score=0.6
                    )
                )
            if "Jane Doe" in article.content:
                mention = db_manager.add_entity_mention(
                    EntityMentionCreate(
                        canonical_entity_id=entities["jane_doe"].id,
                        article_id=article.id,
                        mention_text="Jane Doe",
                        mention_type="PERSON"
                    )
                )
                db_manager.add_entity_mention_context(
                    EntityMentionContextCreate(
                        entity_id=mention.id,
                        article_id=article.id,
                        context_text=article.content,
                        context_type="article",
                        sentiment_score=0.7
                    )
                )
            if "Robert Johnson" in article.content:
                mention = db_manager.add_entity_mention(
                    EntityMentionCreate(
                        canonical_entity_id=entities["robert_johnson"].id,
                        article_id=article.id,
                        mention_text="Robert Johnson",
                        mention_type="PERSON"
                    )
                )
                db_manager.add_entity_mention_context(
                    EntityMentionContextCreate(
                        entity_id=mention.id,
                        article_id=article.id,
                        context_text=article.content,
                        context_type="article",
                        sentiment_score=0.9
                    )
                )
        
        print("Demo setup complete. Added 3 sample articles and entities to the database.")
    finally:
        session.close()

if __name__ == "__main__":
    setup_demo() 