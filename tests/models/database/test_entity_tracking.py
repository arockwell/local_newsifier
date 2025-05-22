"""Integration tests for the entity tracking database functionality."""

import time
from datetime import UTC, datetime, timedelta
from typing import Generator

import pytest
from sqlmodel import Session, select

from local_newsifier.crud.article import article as article_crud
from local_newsifier.crud.canonical_entity import canonical_entity as canonical_entity_crud
from local_newsifier.crud.entity import entity as entity_crud
from local_newsifier.crud.entity_mention_context import \
    entity_mention_context as entity_mention_context_crud
from local_newsifier.crud.entity_profile import entity_profile as entity_profile_crud
from local_newsifier.models.article import Article
from local_newsifier.models.entity import Entity
from local_newsifier.models.entity_tracking import (CanonicalEntity, EntityMention,
                                                    EntityMentionContext, EntityProfile)
from local_newsifier.models.state import AnalysisStatus


@pytest.fixture
def sample_article(db_session: Session):
    """Create a sample article."""
    article = Article(
        url="https://example.com/biden",
        title="Article about Biden",
        content="Joe Biden is the president of the United States. "
        "He previously served as vice president under Barack Obama.",
        published_at=datetime.now(UTC),
        source="example.com",
        status=AnalysisStatus.INITIALIZED.value,
        scraped_at=datetime.now(UTC)
    )
    return article_crud.create(db_session, obj_in=article)


@pytest.fixture
def sample_entity(db_session: Session, sample_article):
    """Create a sample entity."""
    entity = Entity(
        article_id=sample_article.id,
        text="Joe Biden",
        entity_type="PERSON",
        confidence=0.95,
    )
    return entity_crud.create(db_session, obj_in=entity)


def test_add_entity_mention_context(db_session: Session, sample_entity):
    """Test adding context for an entity mention."""
    # Add entity mention context
    context_data = EntityMentionContext(
        entity_id=sample_entity.id,
        article_id=sample_entity.article_id,
        context_text="Joe Biden is the president of the United States.",
        sentiment_score=0.5,
    )

    context = entity_mention_context_crud.create(db_session, obj_in=context_data)

    # Verify context was added
    assert context.id is not None
    assert context.entity_id == sample_entity.id
    assert context.article_id == sample_entity.article_id
    assert context.context_text == "Joe Biden is the president of the United States."
    assert context.sentiment_score == 0.5


def test_add_entity_profile(db_session: Session):
    """Test adding an entity profile."""
    # Create canonical entity
    entity_data = CanonicalEntity(
        name="Donald Trump",
        entity_type="PERSON",
        description="45th President of the United States",
    )

    canonical_entity = canonical_entity_crud.create(db_session, obj_in=entity_data)

    # Add entity profile
    profile_data = EntityProfile(
        canonical_entity_id=canonical_entity.id,
        profile_type="summary",
        content="Donald Trump is a former president.",
        profile_metadata={
            "mention_count": 10,
            "contexts": ["Donald Trump is a former president."],
            "temporal_data": {"2023-01-01": 5, "2023-01-02": 5},
        },
    )

    profile = entity_profile_crud.create(db_session, obj_in=profile_data)

    # Verify profile was added
    assert profile.canonical_entity_id == canonical_entity.id
    assert profile.profile_type == "summary"
    assert profile.content == "Donald Trump is a former president."
    assert profile.profile_metadata["mention_count"] == 10


def test_update_entity_profile(db_session: Session):
    """Test updating an entity profile."""
    # Create canonical entity
    entity_data = CanonicalEntity(
        name="Joe Biden",
        entity_type="PERSON",
        description="46th President of the United States",
    )

    canonical_entity = canonical_entity_crud.create(db_session, obj_in=entity_data)

    # Add initial profile
    profile_data = EntityProfile(
        canonical_entity_id=canonical_entity.id,
        profile_type="summary",
        content="Joe Biden is the president.",
        profile_metadata={
            "mention_count": 5,
            "contexts": ["Joe Biden is the president."],
            "temporal_data": {"2023-01-01": 5},
        },
    )

    initial_profile = entity_profile_crud.create(db_session, obj_in=profile_data)

    # Update profile
    updated_profile_data = EntityProfile(
        canonical_entity_id=canonical_entity.id,
        profile_type="summary",
        content="Joe Biden is the 46th president.",
        profile_metadata={
            "mention_count": 10,
            "contexts": ["Joe Biden is the president.", "Biden announced new policy."],
            "temporal_data": {"2023-01-01": 5, "2023-01-02": 5},
        },
    )

    updated_profile = entity_profile_crud.update_or_create(db_session, obj_in=updated_profile_data)

    # Verify profile was updated
    assert updated_profile.profile_metadata["mention_count"] == 10
    assert len(updated_profile.profile_metadata["contexts"]) == 2


def test_entity_timeline_and_sentiment_trend(db_session: Session):
    """Test getting entity timeline and sentiment trend."""
    # Create article
    article = Article(
        url="https://example.com/biden-timeline",
        title="Biden Timeline Article",
        content="Joe Biden announced new policies today.",
        published_at=datetime.now(UTC),
        source="example.com",
        status=AnalysisStatus.INITIALIZED.value,
        scraped_at=datetime.now(UTC)
    )

    created_article = article_crud.create(db_session, obj_in=article)

    # Create canonical entity
    entity_data = CanonicalEntity(
        name="Joe Biden", 
        entity_type="PERSON"
    )

    canonical_entity = canonical_entity_crud.create(db_session, obj_in=entity_data)

    # Create entity
    entity = Entity(
        article_id=created_article.id,
        text="Joe Biden",
        entity_type="PERSON",
        confidence=0.95,
    )

    created_entity = entity_crud.create(db_session, obj_in=entity)

    # Add entity mention context
    context_data = EntityMentionContext(
        entity_id=created_entity.id,
        article_id=created_article.id,
        context_text="Joe Biden announced new policies today.",
        sentiment_score=0.5,
    )

    entity_mention_context_crud.create(db_session, obj_in=context_data)

    # Create entity mention association
    entity_mention = EntityMention(
        canonical_entity_id=canonical_entity.id,
        entity_id=created_entity.id,
        article_id=created_article.id,
        confidence=0.95
    )
    db_session.add(entity_mention)
    db_session.commit()

    # Get timeline
    start_date = datetime.now(UTC) - timedelta(days=1)
    end_date = datetime.now(UTC) + timedelta(days=1)

    timeline = canonical_entity_crud.get_entity_timeline(
        db_session, entity_id=canonical_entity.id, start_date=start_date, end_date=end_date
    )

    # Verify timeline
    assert len(timeline) == 1
    assert "date" in timeline[0]
    assert "mention_count" in timeline[0]
    assert timeline[0]["mention_count"] > 0

    # Get sentiment trend
    sentiment_trend = entity_mention_context_crud.get_sentiment_trend(
        db_session, entity_id=canonical_entity.id, start_date=start_date, end_date=end_date
    )

    # Verify results
    assert len(sentiment_trend) > 0
    assert sentiment_trend[0]["date"] is not None
    assert sentiment_trend[0]["avg_sentiment"] is not None
