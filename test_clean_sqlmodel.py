"""Clean test of SQLModel implementation without entity_tracking dependencies."""

import os
import sys
from datetime import datetime, timezone

from sqlmodel import SQLModel, Field, create_engine, Session

# Create clean models for testing without dependencies
class Article(SQLModel, table=True):
    """Article model for testing."""
    
    id: int = Field(default=None, primary_key=True)
    title: str
    content: str
    url: str = Field(unique=True)
    source: str
    status: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": datetime.now(timezone.utc)}
    )
    published_at: datetime
    scraped_at: datetime

class Entity(SQLModel, table=True):
    """Entity model for testing."""
    
    id: int = Field(default=None, primary_key=True)
    article_id: int = Field(foreign_key="article.id")
    text: str
    entity_type: str
    confidence: float = Field(default=1.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
def main():
    """Create in-memory database and test models."""
    # Create an in-memory database
    engine = create_engine("sqlite:///:memory:", echo=True)
    
    # Create tables
    SQLModel.metadata.create_all(engine)
    
    # Create instances
    article = Article(
        title="Test Article",
        content="This is a test article",
        url="http://example.com/test",
        source="Test Source",
        published_at=datetime.now(timezone.utc),
        status="new",
        scraped_at=datetime.now(timezone.utc)
    )
    
    # Use session context
    with Session(engine) as session:
        session.add(article)
        session.commit()
        
        # Create entity after article is saved
        entity = Entity(
            article_id=article.id,
            text="Test Entity",
            entity_type="PERSON",
            confidence=0.95
        )
        
        session.add(entity)
        session.commit()
        
        # Query data
        print("\nQuery Article:")
        db_article = session.get(Article, article.id)
        print(f"Article: {db_article.title} - {db_article.url}")
        
        print("\nQuery Entity:")
        db_entity = session.get(Entity, entity.id)
        print(f"Entity: {db_entity.text} ({db_entity.entity_type})")
        
    print("\nTest completed successfully!")

if __name__ == "__main__":
    main()