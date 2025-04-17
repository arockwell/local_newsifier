"""Simple test to verify SQLModel implementation works."""

import os
import sys
from datetime import datetime, timezone

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from local_newsifier.models.database import (
    SQLModel, 
    get_engine, 
    get_session_context,
    Article, 
    Entity, 
    AnalysisResult
)

def main():
    """Create in-memory database and test models."""
    # Create an in-memory database
    engine = get_engine("sqlite:///:memory:")
    
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
    
    entity = Entity(
        article_id=1,  # This would be set after article is saved
        text="Test Entity",
        entity_type="PERSON",
        confidence=0.95
    )
    
    analysis = AnalysisResult(
        article_id=1,  # This would be set after article is saved
        analysis_type="test",
        results={"test": "result"}
    )
    
    # Use our context manager for the session
    with get_session_context(engine) as session:
        session.add(article)
        session.flush()  # Flush to get the ID
        
        # Set article_id for entity and analysis
        entity.article_id = article.id
        analysis.article_id = article.id
        
        session.add(entity)
        session.add(analysis)
        
        # Query data
        print("\nQuery Article:")
        db_article = session.get(Article, article.id)
        print(f"Article: {db_article.title} - {db_article.url}")
        
        print("\nQuery Entity:")
        db_entity = session.get(Entity, entity.id)
        print(f"Entity: {db_entity.text} ({db_entity.entity_type})")
        
        print("\nQuery Analysis:")
        db_analysis = session.get(AnalysisResult, analysis.id)
        print(f"Analysis: {db_analysis.analysis_type} - {db_analysis.results}")
        
        print("\nRelationships:")
        print(f"Article -> Entities: {db_article.entities}")
        print(f"Article -> Analysis Results: {db_article.analysis_results}")
        print(f"Entity -> Article: {db_entity.article}")
        print(f"Analysis -> Article: {db_analysis.article}")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    main()