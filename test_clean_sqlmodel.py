"""Clean test of SQLModel implementation with actual application models."""

import os
import sys
from datetime import datetime, timezone

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from sqlmodel import SQLModel, create_engine, Session

# Import all models to ensure they're registered
from local_newsifier.models.database.article import Article
from local_newsifier.models.database.entity import Entity  
from local_newsifier.models.database.analysis_result import AnalysisResult
from local_newsifier.models.entity_tracking import (
    CanonicalEntity,
    EntityMention,
    EntityMentionContext, 
    EntityProfile,
    EntityRelationship
)
    
def main():
    """Test the SQLModel setup with all tables."""
    # Create in-memory SQLite database
    engine = create_engine("sqlite:///:memory:", echo=True)
    
    # Drop all tables and recreate them
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    
    # Create a session
    with Session(engine) as session:
        # Create test article
        article = Article(
            title="Test Article",
            content="This is test content about John Doe.",
            url="https://example.com/test",
            source="Test Source",
            published_at=datetime.now(timezone.utc),
            status="INITIALIZED",
            scraped_at=datetime.now(timezone.utc)
        )
        session.add(article)
        session.commit()
        session.refresh(article)
        print(f"Created article: {article.id} - {article.title}")
        
        # Create entity
        entity = Entity(
            article_id=article.id,
            text="John Doe",
            entity_type="PERSON",
            confidence=0.95
        )
        session.add(entity)
        session.commit()
        session.refresh(entity)
        print(f"Created entity: {entity.id} - {entity.text}")
        
        # Create canonical entity
        canonical = CanonicalEntity(
            name="John Doe",
            entity_type="PERSON",
            description="A test person",
            entity_metadata={"test": "data"}
        )
        session.add(canonical)
        session.commit()
        session.refresh(canonical)
        print(f"Created canonical entity: {canonical.id} - {canonical.name}")
        
        # Create entity mention
        mention = EntityMention(
            canonical_entity_id=canonical.id,
            entity_id=entity.id,
            article_id=article.id,
            confidence=0.9
        )
        session.add(mention)
        session.commit()
        session.refresh(mention)
        print(f"Created entity mention: {mention.id}")
        
        # Test entity mention context
        context = EntityMentionContext(
            entity_id=entity.id,
            article_id=article.id,
            context_text="This is test content about John Doe.",
            sentiment_score=0.5
        )
        session.add(context)
        session.commit()
        session.refresh(context)
        print(f"Created entity mention context: {context.id}")
        
        # Test relationship
        relationship = EntityRelationship(
            source_entity_id=canonical.id,
            target_entity_id=canonical.id,  # self-reference as test
            relationship_type="SELF",
            confidence=1.0,
            evidence="Test evidence"
        )
        session.add(relationship)
        session.commit()
        session.refresh(relationship)
        print(f"Created entity relationship: {relationship.id}")
        
        # Test entity profile
        profile = EntityProfile(
            canonical_entity_id=canonical.id,
            profile_type="SUMMARY",
            content="This is a test profile for John Doe",
            profile_metadata={"test": "profile"}
        )
        session.add(profile)
        session.commit()
        session.refresh(profile)
        print(f"Created entity profile: {profile.id}")
        
        print("\nAll models created successfully!")

if __name__ == "__main__":
    main()