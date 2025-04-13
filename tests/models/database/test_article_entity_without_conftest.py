"""Tests for the Article and Entity database models."""

import datetime
import pytest
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from local_newsifier.models.database.base import Base
from local_newsifier.models.database.article import ArticleDB
from local_newsifier.models.database.entity import EntityDB
from local_newsifier.models.state import AnalysisStatus
from local_newsifier.config.database import DatabaseSettings

@pytest.fixture(scope="module")
def postgres_engine():
    """Set up a PostgreSQL test database."""
    # Use environment variables for PostgreSQL connection
    settings = DatabaseSettings()
    
    # Use a unique test database name
    test_db_name = f"test_article_entity_{os.getenv('GITHUB_RUN_ID', 'local')}"
    db_url = settings.get_database_url().replace(settings.POSTGRES_DB, test_db_name)
    
    # Connect to default postgres database to create test db
    try:
        # Connect to default postgres database to create test db
        admin_url = db_url.rsplit('/', 1)[0] + "/postgres"
        admin_engine = create_engine(admin_url)
        
        # Create test database
        with admin_engine.connect() as conn:
            conn.execute(text(f"DROP DATABASE IF EXISTS {test_db_name}"))
            conn.execute(text(f"CREATE DATABASE {test_db_name}"))
            conn.commit()
    except Exception as e:
        print(f"Error creating test database: {e}")
        # If we can't create the database, try connecting directly
        # (it might already exist in CI)
    
    # Create engine for the test database
    engine = create_engine(db_url)
    
    # Create test tables
    Base.metadata.create_all(engine)
    
    yield engine
    
    # Clean up
    Base.metadata.drop_all(engine)
    engine.dispose()
    
    try:
        # Connect to default postgres database to drop test db
        admin_url = db_url.rsplit('/', 1)[0] + "/postgres"
        admin_engine = create_engine(admin_url)
        
        # Drop test database
        with admin_engine.connect() as conn:
            conn.execute(text(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{test_db_name}'
                AND pid <> pg_backend_pid();
            """))
            conn.execute(text(f"DROP DATABASE IF EXISTS {test_db_name}"))
            conn.commit()
    except Exception as e:
        print(f"Error dropping test database: {e}")


@pytest.fixture
def db_session(postgres_engine):
    """Create a test database session."""
    Session = sessionmaker(bind=postgres_engine)
    session = Session()
    yield session
    session.close()


def test_article_creation(db_session):
    """Test creating an ArticleDB instance."""
    article = ArticleDB(
        url="https://example.com/news/1",
        title="Test Article",
        source="example.com",
        content="This is a test article.",
        status=AnalysisStatus.INITIALIZED.value
    )
    db_session.add(article)
    db_session.commit()
    
    assert article.id is not None
    assert article.url == "https://example.com/news/1"
    assert article.title == "Test Article"
    assert article.source == "example.com"
    assert article.content == "This is a test article."
    assert article.status == AnalysisStatus.INITIALIZED.value
    assert isinstance(article.created_at, datetime.datetime)
    assert isinstance(article.updated_at, datetime.datetime)
    assert isinstance(article.scraped_at, datetime.datetime)


def test_article_entity_relationship(db_session):
    """Test relationship between ArticleDB and EntityDB."""
    article = ArticleDB(
        url="https://example.com/news/2",
        title="Test Article",
        source="example.com",
        content="This is a test article about Gainesville.",
        status=AnalysisStatus.SCRAPE_SUCCEEDED.value
    )
    
    entity = EntityDB(
        text="Gainesville",
        entity_type="GPE",
        sentence_context="This is a test article about Gainesville."
    )
    
    article.entities.append(entity)
    db_session.add(article)
    db_session.commit()
    
    # Refresh the session to ensure we're getting fresh data
    db_session.refresh(article)
    
    assert len(article.entities) == 1
    assert article.entities[0].text == "Gainesville"
    assert article.entities[0].entity_type == "GPE"
    assert article.entities[0].article_id == article.id
    assert article.entities[0].article == article


def test_article_unique_url_constraint(db_session):
    """Test that article URL must be unique."""
    article1 = ArticleDB(
        url="https://example.com/news/3",
        title="Test Article 1",
        source="example.com"
    )
    db_session.add(article1)
    db_session.commit()
    
    article2 = ArticleDB(
        url="https://example.com/news/3",  # Same URL as article1
        title="Test Article 2",
        source="example.com"
    )
    db_session.add(article2)
    
    # This should raise an exception due to unique constraint
    with pytest.raises(Exception):
        db_session.commit()


def test_article_cascade_delete(db_session):
    """Test that deleting an article cascades to its entities."""
    article = ArticleDB(
        url="https://example.com/news/4",
        title="Test Article",
        source="example.com"
    )
    
    entity = EntityDB(
        text="Gainesville",
        entity_type="GPE",
        sentence_context="This is a test article about Gainesville."
    )
    
    article.entities.append(entity)
    db_session.add(article)
    db_session.commit()
    
    # Get the entity ID for later check
    entity_id = entity.id
    
    # Delete the article
    db_session.delete(article)
    db_session.commit()
    
    # Check if entity is also deleted
    remaining_entity = db_session.query(EntityDB).filter_by(id=entity_id).first()
    assert remaining_entity is None
    

def test_entity_creation(db_session):
    """Test creating an EntityDB instance."""
    article = ArticleDB(
        url="https://example.com/news/5",
        title="Test Article",
        source="example.com",
        status=AnalysisStatus.SCRAPE_SUCCEEDED.value
    )
    db_session.add(article)
    db_session.commit()
    
    entity = EntityDB(
        article_id=article.id,
        text="Gainesville",
        entity_type="GPE",
        sentence_context="This is about Gainesville.",
        confidence=0.95
    )
    db_session.add(entity)
    db_session.commit()
    
    assert entity.id is not None
    assert entity.article_id == article.id
    assert entity.text == "Gainesville"
    assert entity.entity_type == "GPE"
    assert entity.sentence_context == "This is about Gainesville."
    assert entity.confidence == 0.95
    assert isinstance(entity.created_at, datetime.datetime)
    assert isinstance(entity.updated_at, datetime.datetime)


def test_multiple_entities_for_article(db_session):
    """Test that an article can have multiple entities."""
    article = ArticleDB(
        url="https://example.com/news/6",
        title="Test Article",
        source="example.com",
        status=AnalysisStatus.SCRAPE_SUCCEEDED.value
    )
    db_session.add(article)
    db_session.commit()
    
    entities = [
        EntityDB(text="Gainesville", entity_type="GPE"),
        EntityDB(text="University of Florida", entity_type="ORG"),
        EntityDB(text="John Smith", entity_type="PERSON")
    ]
    
    for entity in entities:
        article.entities.append(entity)
    
    db_session.commit()
    
    # Refresh the session
    db_session.refresh(article)
    
    assert len(article.entities) == 3
    
    # Check that all entities are properly associated
    entity_texts = [e.text for e in article.entities]
    assert "Gainesville" in entity_texts
    assert "University of Florida" in entity_texts
    assert "John Smith" in entity_texts


def test_entity_default_values(db_session):
    """Test default values for EntityDB fields."""
    article = ArticleDB(
        url="https://example.com/news/7",
        title="Test Article",
        source="example.com",
        status=AnalysisStatus.SCRAPE_SUCCEEDED.value
    )
    db_session.add(article)
    db_session.commit()
    
    entity = EntityDB(
        article_id=article.id,
        text="Gainesville",
        entity_type="GPE"
    )
    db_session.add(entity)
    db_session.commit()
    
    assert entity.confidence == 1.0  # Default confidence value
    assert entity.created_at is not None
    assert entity.updated_at is not None
    

def test_full_article_entity_workflow(db_session):
    """Test a full workflow of creating an article with entities."""
    # Create an article
    article = ArticleDB(
        url="https://example.com/news/8",
        title="Local News: City Council Approves New Budget",
        source="example.com",
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
            sentence_context="The Gainesville City Council approved a new budget yesterday.",
            confidence=0.92
        ),
        EntityDB(
            text="John Smith",
            entity_type="PERSON",
            sentence_context="Mayor John Smith praised the decision.",
            confidence=0.98
        ),
        EntityDB(
            text="University of Florida",
            entity_type="ORG",
            sentence_context="Critical infrastructure projects for the University of Florida community.",
            confidence=0.95
        ),
        EntityDB(
            text="Gainesville",
            entity_type="GPE",
            sentence_context="The Gainesville City Council approved a new budget yesterday.",
            confidence=0.97
        )
    ]
    
    # Add entities to article
    for entity in entities:
        article.entities.append(entity)
    
    # Save to database
    db_session.add(article)
    db_session.commit()
    
    # Retrieve article from database
    retrieved_article = db_session.query(ArticleDB).filter_by(url="https://example.com/news/8").first()
    
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
        assert entity.article_id == retrieved_article.id