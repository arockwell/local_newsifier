"""Integration tests for the database models."""

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from local_newsifier.models.database import Base
from local_newsifier.models.database.article import ArticleDB
from local_newsifier.models.database.entity import EntityDB
from local_newsifier.models.state import AnalysisStatus


@pytest.fixture
def engine():
    """Create a SQLite in-memory engine for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    """Create a session for testing."""
    with Session(engine) as session:
        yield session


def test_schema_generation(engine):
    """Test that the schema is properly generated."""
    inspector = inspect(engine)
    
    # Check that all tables are created
    tables = inspector.get_table_names()
    assert "articles" in tables
    assert "entities" in tables
    
    # Check article table columns
    article_columns = {col["name"] for col in inspector.get_columns("articles")}
    expected_article_columns = {
        "id", "url", "title", "source", "content", 
        "scraped_at", "status", "created_at", "updated_at"
    }
    assert expected_article_columns.issubset(article_columns)
    
    # Check entity table columns
    entity_columns = {col["name"] for col in inspector.get_columns("entities")}
    expected_entity_columns = {
        "id", "article_id", "text", "entity_type", "sentence_context",
        "created_at", "updated_at"
    }
    assert expected_entity_columns.issubset(entity_columns)


def test_full_article_entity_workflow(session):
    """Test a full workflow of creating an article with entities."""
    # Create an article
    article = ArticleDB(
        url="https://example.com/news/1",
        title="Local News: City Council Approves New Budget",
        source="Example News",
        content=(
            "The Gainesville City Council approved a new budget yesterday. "
            "Mayor John Smith praised the decision, saying it would help fund "
            "critical infrastructure projects for the University of Florida community."
        ),
        status=AnalysisStatus.ANALYSIS_SUCCEEDED.value
    )
    
    # Create entities
    entities = [
        EntityDB(
            text="Gainesville City Council",
            entity_type="ORG",
            sentence_context="The Gainesville City Council approved a new budget yesterday."
        ),
        EntityDB(
            text="John Smith",
            entity_type="PERSON",
            sentence_context="Mayor John Smith praised the decision."
        ),
        EntityDB(
            text="University of Florida",
            entity_type="ORG",
            sentence_context="Critical infrastructure projects for the University of Florida community."
        ),
        EntityDB(
            text="Gainesville",
            entity_type="GPE",
            sentence_context="The Gainesville City Council approved a new budget yesterday."
        )
    ]
    
    # Add entities to article
    for entity in entities:
        article.entities.append(entity)
    
    # Save to database
    session.add(article)
    session.commit()
    
    # Retrieve article from database
    retrieved_article = session.query(ArticleDB).filter_by(url="https://example.com/news/1").first()
    
    # Verify article data
    assert retrieved_article is not None
    assert retrieved_article.title == "Local News: City Council Approves New Budget"
    assert retrieved_article.status == AnalysisStatus.ANALYSIS_SUCCEEDED.value
    
    # Verify entities
    assert len(retrieved_article.entities) == 4
    
    # Check for specific entities
    entity_texts = [e.text for e in retrieved_article.entities]
    assert "Gainesville City Council" in entity_texts
    assert "John Smith" in entity_texts
    assert "University of Florida" in entity_texts
    assert "Gainesville" in entity_texts
    
    # Verify entity types
    person_entities = [e for e in retrieved_article.entities if e.entity_type == "PERSON"]
    org_entities = [e for e in retrieved_article.entities if e.entity_type == "ORG"]
    gpe_entities = [e for e in retrieved_article.entities if e.entity_type == "GPE"]
    
    assert len(person_entities) == 1
    assert len(org_entities) == 2
    assert len(gpe_entities) == 1
    
    # Verify relationships
    for entity in retrieved_article.entities:
        assert entity.article == retrieved_article