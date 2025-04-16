"""Tests for the entity mention context CRUD module."""

from datetime import datetime, timedelta, timezone

import pytest

from local_newsifier.crud.entity_mention_context import CRUDEntityMentionContext
from local_newsifier.crud.entity_mention_context import (
    entity_mention_context as entity_mention_context_crud,
)
from local_newsifier.models.database.article import ArticleDB
from local_newsifier.models.database.entity import EntityDB
from local_newsifier.models.entity_tracking import (
    EntityMentionContext,
    EntityMentionContextCreate,
    EntityMentionContextDB,
    entity_mentions,
)


class TestEntityMentionContextCRUD:
    """Tests for EntityMentionContextCRUD class."""

    def test_create(
        self, db_session, create_entity, sample_entity_mention_context_data
    ):
        """Test creating a new entity mention context."""
        obj_in = EntityMentionContextCreate(**sample_entity_mention_context_data)
        context = entity_mention_context_crud.create(db_session, obj_in=obj_in)

        assert context is not None
        assert context.id is not None
        assert context.entity_id == obj_in.entity_id
        assert context.article_id == obj_in.article_id
        assert context.context_text == obj_in.context_text
        assert context.context_type == obj_in.context_type
        assert context.sentiment_score == obj_in.sentiment_score
        assert context.created_at is not None

        # Verify it was saved to the database
        db_context = (
            db_session.query(EntityMentionContextDB)
            .filter(EntityMentionContextDB.id == context.id)
            .first()
        )
        assert db_context is not None
        assert db_context.entity_id == obj_in.entity_id
        assert db_context.article_id == obj_in.article_id

    def test_get(self, db_session, create_entity, sample_entity_mention_context_data):
        """Test getting an entity mention context by ID."""
        # Create an entity mention context
        db_context = EntityMentionContextDB(**sample_entity_mention_context_data)
        db_session.add(db_context)
        db_session.commit()

        # Test getting the context by ID
        context = entity_mention_context_crud.get(db_session, id=db_context.id)

        assert context is not None
        assert context.id == db_context.id
        assert context.entity_id == db_context.entity_id
        assert context.article_id == db_context.article_id
        assert context.context_text == db_context.context_text
        assert context.context_type == db_context.context_type
        assert context.sentiment_score == db_context.sentiment_score

    def test_get_by_entity_and_article(
        self, db_session, create_entity, sample_entity_mention_context_data
    ):
        """Test getting an entity mention context by entity ID and article ID."""
        # Create an entity mention context
        db_context = EntityMentionContextDB(**sample_entity_mention_context_data)
        db_session.add(db_context)
        db_session.commit()

        # Test getting the context by entity ID and article ID
        context = entity_mention_context_crud.get_by_entity_and_article(
            db_session, entity_id=create_entity.id, article_id=create_entity.article_id
        )

        assert context is not None
        assert context.entity_id == create_entity.id
        assert context.article_id == create_entity.article_id
        assert context.context_text == db_context.context_text

    def test_get_by_entity_and_article_not_found(self, db_session, create_entity):
        """Test getting a non-existent entity mention context."""
        context = entity_mention_context_crud.get_by_entity_and_article(
            db_session,
            entity_id=create_entity.id,
            article_id=999,  # Non-existent article ID
        )

        assert context is None

    def test_get_by_entity(self, db_session, create_entity):
        """Test getting all contexts for an entity."""
        # Create multiple contexts for the same entity but different articles
        contexts_data = []
        for i in range(3):
            context_data = {
                "entity_id": create_entity.id,
                "article_id": i + 100,  # Different article IDs
                "context_text": f"Context {i} for entity {create_entity.id}",
                "context_type": "sentence",
                "sentiment_score": 0.5 + (i * 0.1),
            }
            contexts_data.append(context_data)
            db_context = EntityMentionContextDB(**context_data)
            db_session.add(db_context)
        db_session.commit()

        # Test getting all contexts for the entity
        contexts = entity_mention_context_crud.get_by_entity(
            db_session, entity_id=create_entity.id
        )

        assert len(contexts) == 3
        for i, context in enumerate(sorted(contexts, key=lambda c: c.article_id)):
            assert context.entity_id == create_entity.id
            assert context.article_id == i + 100
            assert context.context_text == f"Context {i} for entity {create_entity.id}"

    def test_get_by_entity_empty(self, db_session, create_entity):
        """Test getting contexts for an entity with no contexts."""
        contexts = entity_mention_context_crud.get_by_entity(
            db_session, entity_id=create_entity.id
        )

        assert len(contexts) == 0

    def test_get_sentiment_trend(
        self, db_session, create_canonical_entity, create_entity
    ):
        """Test getting the sentiment trend for an entity."""
        # Create articles with different published dates
        articles = []
        base_date = datetime.now(timezone.utc)
        for i in range(5):
            article = ArticleDB(
                title=f"Test Article {i}",
                content=f"This is test article {i}.",
                url=f"https://example.com/test-article-{i}",
                source="test_source",
                published_at=base_date - timedelta(days=i),
                status="new",
                scraped_at=datetime.now(timezone.utc),
            )
            db_session.add(article)
            db_session.flush()
            articles.append(article)
        db_session.commit()

        # Create entities for each article
        entities = []
        for i, article in enumerate(articles):
            entity = EntityDB(
                article_id=article.id,
                text=f"Entity {i}",
                entity_type="TEST",
                confidence=0.9,
                sentence_context=f"Context for entity {i}",
            )
            db_session.add(entity)
            db_session.flush()
            entities.append(entity)
        db_session.commit()

        # Add entity mentions linking entities to canonical entity
        for i, entity in enumerate(entities):
            db_session.execute(
                entity_mentions.insert().values(
                    canonical_entity_id=create_canonical_entity.id,
                    entity_id=entity.id,
                    article_id=entity.article_id,
                    confidence=0.9,
                )
            )
        db_session.commit()

        # Add entity mention contexts with different sentiment scores
        for i, entity in enumerate(entities):
            context = EntityMentionContextDB(
                entity_id=entity.id,
                article_id=entity.article_id,
                context_text=f"Context for entity {i}",
                context_type="sentence",
                sentiment_score=0.5 + (i * 0.1),  # Different sentiment scores
            )
            db_session.add(context)
        db_session.commit()

        # Test getting the sentiment trend
        start_date = base_date - timedelta(days=10)
        end_date = base_date + timedelta(days=1)
        trend = entity_mention_context_crud.get_sentiment_trend(
            db_session,
            entity_id=create_canonical_entity.id,
            start_date=start_date,
            end_date=end_date,
        )

        assert len(trend) == 5
        for i, entry in enumerate(sorted(trend, key=lambda e: e["date"], reverse=True)):
            assert entry["date"] == articles[i].published_at
            assert entry["avg_sentiment"] == pytest.approx(0.5 + (i * 0.1))

    def test_singleton_instance(self):
        """Test that the entity_mention_context_crud is a singleton instance of CRUDEntityMentionContext."""
        assert isinstance(entity_mention_context_crud, CRUDEntityMentionContext)
        assert entity_mention_context_crud.model == EntityMentionContextDB
        assert entity_mention_context_crud.schema == EntityMentionContext
