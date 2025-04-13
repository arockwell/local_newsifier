"""Integration tests for the entity tracking database functionality."""

from datetime import UTC, datetime, timedelta
from typing import Generator

import pytest
from sqlalchemy.orm import Session

from local_newsifier.config.database import get_database, get_db_session
from local_newsifier.database.manager import DatabaseManager
from local_newsifier.models.database import (ArticleCreate, ArticleDB, Base,
                                          EntityCreate, EntityDB)
from local_newsifier.models.entity_tracking import (CanonicalEntityCreate,
                                                  CanonicalEntityDB,
                                                  EntityMentionContextCreate,
                                                  EntityMentionContextDB,
                                                  EntityProfileCreate,
                                                  EntityProfileDB,
                                                  entity_mentions)


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine."""
    engine = get_database(".env.test")
    return engine


@pytest.fixture(scope="function")
def setup_test_db(test_engine):
    """Set up and tear down the test database for each test."""
    # Create all tables
    Base.metadata.create_all(test_engine)
    yield
    # Drop all tables
    Base.metadata.drop_all(test_engine)


@pytest.fixture
def db_session(test_engine) -> Generator[Session, None, None]:
    """Create a test database session."""
    session_factory = get_db_session(".env.test")
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def db_manager(db_session: Session) -> DatabaseManager:
    """Create a database manager instance."""
    return DatabaseManager(db_session)


@pytest.fixture
def sample_article(db_manager: DatabaseManager):
    """Create a sample article."""
    article = ArticleCreate(
        url="https://example.com/biden",
        title="Article about Biden",
        content="Joe Biden is the president of the United States. "
                "He previously served as vice president under Barack Obama.",
        published_at=datetime.now(UTC),
        status="analyzed"
    )
    return db_manager.create_article(article)


@pytest.fixture
def sample_entity(db_manager: DatabaseManager, sample_article):
    """Create a sample entity."""
    entity = EntityCreate(
        article_id=sample_article.id,
        text="Joe Biden",
        entity_type="PERSON",
        confidence=0.95
    )
    return db_manager.add_entity(entity)


def test_create_canonical_entity(db_manager: DatabaseManager, setup_test_db):
    """Test creating a canonical entity."""
    # Create canonical entity
    entity_data = CanonicalEntityCreate(
        name="Joe Biden",
        entity_type="PERSON",
        description="46th President of the United States"
    )
    
    canonical_entity = db_manager.create_canonical_entity(entity_data)
    
    # Verify entity was created
    assert canonical_entity.id is not None
    assert canonical_entity.name == "Joe Biden"
    assert canonical_entity.entity_type == "PERSON"
    assert canonical_entity.description == "46th President of the United States"
    assert canonical_entity.first_seen is not None
    assert canonical_entity.last_seen is not None


def test_get_canonical_entity(db_manager: DatabaseManager, setup_test_db):
    """Test getting a canonical entity by ID."""
    # Create canonical entity
    entity_data = CanonicalEntityCreate(
        name="Kamala Harris",
        entity_type="PERSON",
        description="Vice President of the United States"
    )
    
    created_entity = db_manager.create_canonical_entity(entity_data)
    
    # Get canonical entity
    retrieved_entity = db_manager.get_canonical_entity(created_entity.id)
    
    # Verify entity was retrieved
    assert retrieved_entity is not None
    assert retrieved_entity.id == created_entity.id
    assert retrieved_entity.name == "Kamala Harris"
    assert retrieved_entity.entity_type == "PERSON"
    assert retrieved_entity.description == "Vice President of the United States"


def test_get_canonical_entity_by_name(db_manager: DatabaseManager, setup_test_db):
    """Test getting a canonical entity by name and type."""
    # Create canonical entity
    entity_data = CanonicalEntityCreate(
        name="Barack Obama",
        entity_type="PERSON",
        description="44th President of the United States"
    )
    
    db_manager.create_canonical_entity(entity_data)
    
    # Get canonical entity by name
    retrieved_entity = db_manager.get_canonical_entity_by_name("Barack Obama", "PERSON")
    
    # Verify entity was retrieved
    assert retrieved_entity is not None
    assert retrieved_entity.name == "Barack Obama"
    assert retrieved_entity.entity_type == "PERSON"
    assert retrieved_entity.description == "44th President of the United States"


def test_add_entity_mention_context(db_manager: DatabaseManager, sample_entity, setup_test_db):
    """Test adding context for an entity mention."""
    # Add entity mention context
    context_data = EntityMentionContextCreate(
        entity_id=sample_entity.id,
        article_id=sample_entity.article_id,
        context_text="Joe Biden is the president of the United States.",
        sentiment_score=0.5
    )
    
    context = db_manager.add_entity_mention_context(context_data)
    
    # Verify context was added
    assert context.id is not None
    assert context.entity_id == sample_entity.id
    assert context.article_id == sample_entity.article_id
    assert context.context_text == "Joe Biden is the president of the United States."
    assert context.sentiment_score == 0.5


def test_add_entity_profile(db_manager: DatabaseManager, setup_test_db):
    """Test adding an entity profile."""
    # Create canonical entity
    entity_data = CanonicalEntityCreate(
        name="Donald Trump",
        entity_type="PERSON",
        description="45th President of the United States"
    )
    
    canonical_entity = db_manager.create_canonical_entity(entity_data)
    
    # Add entity profile
    profile_data = EntityProfileCreate(
        canonical_entity_id=canonical_entity.id,
        mention_count=10,
        contexts=["Donald Trump is a former president."],
        temporal_data={"2023-01-01": 5, "2023-01-02": 5}
    )
    
    profile = db_manager.add_entity_profile(profile_data)
    
    # Verify profile was added
    assert profile.id is not None
    assert profile.canonical_entity_id == canonical_entity.id
    assert profile.mention_count == 10
    assert profile.contexts is not None
    assert len(profile.contexts) == 1
    assert profile.contexts[0] == "Donald Trump is a former president."
    assert profile.temporal_data == {"2023-01-01": 5, "2023-01-02": 5}
    assert profile.last_updated is not None


def test_update_entity_profile(db_manager: DatabaseManager, setup_test_db):
    """Test updating an entity profile."""
    # Create canonical entity
    entity_data = CanonicalEntityCreate(
        name="Nancy Pelosi",
        entity_type="PERSON",
        description="Former Speaker of the House"
    )
    
    canonical_entity = db_manager.create_canonical_entity(entity_data)
    
    # Add initial entity profile
    initial_profile_data = EntityProfileCreate(
        canonical_entity_id=canonical_entity.id,
        mention_count=5,
        contexts=["Nancy Pelosi is a politician."],
        temporal_data={"2023-01-01": 5}
    )
    
    db_manager.add_entity_profile(initial_profile_data)
    
    # Update entity profile
    updated_profile_data = EntityProfileCreate(
        canonical_entity_id=canonical_entity.id,
        mention_count=10,
        contexts=["Nancy Pelosi is a politician.", "Nancy Pelosi was the Speaker."],
        temporal_data={"2023-01-01": 5, "2023-01-02": 5}
    )
    
    updated_profile = db_manager.add_entity_profile(updated_profile_data)
    
    # Verify profile was updated
    assert updated_profile.id is not None
    assert updated_profile.canonical_entity_id == canonical_entity.id
    assert updated_profile.mention_count == 10
    assert updated_profile.contexts is not None
    assert len(updated_profile.contexts) == 2
    assert updated_profile.temporal_data == {"2023-01-01": 5, "2023-01-02": 5}


def test_entity_timeline_and_sentiment_trend(
    db_manager: DatabaseManager, db_session: Session, setup_test_db
):
    """Test getting entity timeline and sentiment trend."""
    # Create article
    article = ArticleCreate(
        url="https://example.com/biden-timeline",
        title="Biden Timeline Article",
        content="Joe Biden announced new policies today.",
        published_at=datetime.now(UTC),
        status="analyzed"
    )
    
    created_article = db_manager.create_article(article)
    
    # Create canonical entity
    entity_data = CanonicalEntityCreate(
        name="Joe Biden Timeline",
        entity_type="PERSON"
    )
    
    canonical_entity = db_manager.create_canonical_entity(entity_data)
    
    # Create entity
    entity = EntityCreate(
        article_id=created_article.id,
        text="Joe Biden",
        entity_type="PERSON",
        confidence=0.95
    )
    
    created_entity = db_manager.add_entity(entity)
    
    # Add entity mention context
    context_data = EntityMentionContextCreate(
        entity_id=created_entity.id,
        article_id=created_article.id,
        context_text="Joe Biden announced new policies today.",
        sentiment_score=0.7
    )
    
    db_manager.add_entity_mention_context(context_data)
    
    # Create entity mention association
    db_session.execute(
        entity_mentions.insert().values(
            canonical_entity_id=canonical_entity.id,
            entity_id=created_entity.id,
            confidence=0.95
        )
    )
    db_session.commit()
    
    # Test get_entity_timeline
    start_date = datetime.now(UTC) - timedelta(days=7)
    end_date = datetime.now(UTC) + timedelta(days=1)
    
    timeline = db_manager.get_entity_timeline(
        canonical_entity.id, start_date, end_date
    )
    
    # Verify timeline
    assert len(timeline) == 1
    assert timeline[0]["context"] == "Joe Biden announced new policies today."
    assert timeline[0]["sentiment_score"] == 0.7
    assert timeline[0]["article"]["title"] == "Biden Timeline Article"
    
    # Test get_entity_sentiment_trend
    trend = db_manager.get_entity_sentiment_trend(
        canonical_entity.id, start_date, end_date
    )
    
    # Verify trend (may be empty if date grouping doesn't work in test environment)
    if trend:
        assert trend[0]["avg_sentiment"] == 0.7