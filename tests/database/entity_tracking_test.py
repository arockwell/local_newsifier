"""Integration tests for the entity tracking database functionality."""

import time
from datetime import UTC, datetime, timedelta
from typing import Generator

import pytest
from sqlalchemy.orm import Session

from local_newsifier.database.manager import DatabaseManager
from local_newsifier.models.database.base import Base
from local_newsifier.models.entity_tracking import (CanonicalEntity,
                                                    CanonicalEntityCreate,
                                                    CanonicalEntityDB,
                                                    EntityMentionContext,
                                                    EntityMentionContextCreate,
                                                    EntityMentionContextDB,
                                                    EntityProfile,
                                                    EntityProfileCreate,
                                                    EntityProfileDB,
                                                    entity_mentions)
from local_newsifier.models.pydantic_models import ArticleCreate, EntityCreate
from local_newsifier.models.state import AnalysisStatus


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
        source="example.com",
        status=AnalysisStatus.INITIALIZED.value,
    )
    return db_manager.create_article(article)


@pytest.fixture
def sample_entity(db_manager: DatabaseManager, sample_article):
    """Create a sample entity."""
    entity = EntityCreate(
        article_id=sample_article.id,
        text="Joe Biden",
        entity_type="PERSON",
        confidence=0.95,
    )
    return db_manager.add_entity(entity)


def test_add_entity_mention_context(db_manager: DatabaseManager, sample_entity):
    """Test adding context for an entity mention."""
    # Add entity mention context
    context_data = EntityMentionContextCreate(
        entity_id=sample_entity.id,
        article_id=sample_entity.article_id,
        context_text="Joe Biden is the president of the United States.",
        sentiment_score=0.5,
    )

    context = db_manager.add_entity_mention_context(context_data)

    # Verify context was added
    assert context.id is not None
    assert context.entity_id == sample_entity.id
    assert context.article_id == sample_entity.article_id
    assert context.context_text == "Joe Biden is the president of the United States."
    assert context.sentiment_score == 0.5


def test_add_entity_profile(db_manager: DatabaseManager):
    """Test adding an entity profile."""
    # Create canonical entity
    entity_data = CanonicalEntityCreate(
        name="Donald Trump",
        entity_type="PERSON",
        description="45th President of the United States",
    )

    canonical_entity = db_manager.create_canonical_entity(entity_data)

    # Add entity profile
    profile_data = EntityProfileCreate(
        canonical_entity_id=canonical_entity.id,
        profile_type="summary",
        content="Donald Trump is a former president.",
        profile_metadata={
            "mention_count": 10,
            "contexts": ["Donald Trump is a former president."],
            "temporal_data": {"2023-01-01": 5, "2023-01-02": 5},
        },
    )

    profile = db_manager.add_entity_profile(profile_data)

    # Verify profile was added
    assert profile.canonical_entity_id == canonical_entity.id
    assert profile.profile_type == "summary"
    assert profile.content == "Donald Trump is a former president."
    assert profile.profile_metadata["mention_count"] == 10


def test_update_entity_profile(db_manager: DatabaseManager):
    """Test updating an entity profile."""
    # Create canonical entity
    entity_data = CanonicalEntityCreate(
        name="Joe Biden",
        entity_type="PERSON",
        description="46th President of the United States",
    )

    canonical_entity = db_manager.create_canonical_entity(entity_data)

    # Add initial profile
    profile_data = EntityProfileCreate(
        canonical_entity_id=canonical_entity.id,
        profile_type="summary",
        content="Joe Biden is the president.",
        profile_metadata={
            "mention_count": 5,
            "contexts": ["Joe Biden is the president."],
            "temporal_data": {"2023-01-01": 5},
        },
    )

    initial_profile = db_manager.add_entity_profile(profile_data)

    # Update profile
    updated_profile_data = EntityProfileCreate(
        canonical_entity_id=canonical_entity.id,
        profile_type="summary",
        content="Joe Biden is the 46th president.",
        profile_metadata={
            "mention_count": 10,
            "contexts": ["Joe Biden is the president.", "Biden announced new policy."],
            "temporal_data": {"2023-01-01": 5, "2023-01-02": 5},
        },
    )

    updated_profile = db_manager.update_entity_profile(updated_profile_data)

    # Verify profile was updated
    assert updated_profile.profile_metadata["mention_count"] == 10
    assert len(updated_profile.profile_metadata["contexts"]) == 2


def test_entity_timeline_and_sentiment_trend(
    db_manager: DatabaseManager, db_session: Session
):
    """Test getting entity timeline and sentiment trend."""
    # Create article
    article = ArticleCreate(
        url="https://example.com/biden-timeline",
        title="Biden Timeline Article",
        content="Joe Biden announced new policies today.",
        published_at=datetime.now(UTC),
        source="example.com",
        status=AnalysisStatus.INITIALIZED.value,
    )

    created_article = db_manager.create_article(article)

    # Create canonical entity
    entity_data = CanonicalEntityCreate(name="Joe Biden", entity_type="PERSON")

    canonical_entity = db_manager.create_canonical_entity(entity_data)

    # Create entity
    entity = EntityCreate(
        article_id=created_article.id,
        text="Joe Biden",
        entity_type="PERSON",
        confidence=0.95,
    )

    created_entity = db_manager.add_entity(entity)

    # Add entity mention context
    context_data = EntityMentionContextCreate(
        entity_id=created_entity.id,
        article_id=created_article.id,
        context_text="Joe Biden announced new policies today.",
        sentiment_score=0.5,
    )

    db_manager.add_entity_mention_context(context_data)

    # Create entity mention association
    db_session.execute(
        entity_mentions.insert().values(
            canonical_entity_id=canonical_entity.id,
            entity_id=created_entity.id,
            article_id=created_article.id,
            confidence=0.95,
        )
    )
    db_session.commit()

    # Get timeline
    start_date = datetime.now(UTC) - timedelta(days=1)
    end_date = datetime.now(UTC) + timedelta(days=1)

    timeline = db_manager.get_entity_timeline(canonical_entity.id, start_date, end_date)

    # Verify timeline
    assert len(timeline) == 1
    assert "date" in timeline[0]
    assert "mention_count" in timeline[0]
    assert timeline[0]["mention_count"] > 0

    # Get sentiment trend
    sentiment_trend = db_manager.get_entity_sentiment_trend(
        canonical_entity.id, start_date, end_date
    )

    # Verify results
    assert len(sentiment_trend) > 0
    assert sentiment_trend[0]["date"] is not None
    assert sentiment_trend[0]["avg_sentiment"] is not None
