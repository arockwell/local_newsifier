"""Tests for the async entity CRUD module."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from local_newsifier.crud.async_entity import AsyncCRUDEntity, async_entity
from local_newsifier.models.article import Article
from local_newsifier.models.entity import Entity


@pytest.mark.asyncio
class TestAsyncEntityCRUD:
    """Tests for AsyncCRUDEntity class."""

    async def test_create(self, async_db_session, async_create_article, sample_entity_data):
        """Test creating a new entity asynchronously."""
        sample_entity_data["article_id"] = async_create_article.id
        entity = await async_entity.create(async_db_session, obj_in=Entity(**sample_entity_data))

        assert entity is not None
        assert entity.id is not None
        assert entity.text == sample_entity_data["text"]
        assert entity.entity_type == sample_entity_data["entity_type"]
        assert entity.confidence == sample_entity_data["confidence"]
        assert entity.article_id == sample_entity_data["article_id"]

        # Verify it was saved to the database
        result = await async_db_session.execute(select(Entity).where(Entity.id == entity.id))
        db_entity = result.scalar_one_or_none()
        assert db_entity is not None
        assert db_entity.text == sample_entity_data["text"]

    async def test_get(self, async_db_session, async_create_entity):
        """Test getting an entity by ID asynchronously."""
        entity = await async_entity.get(async_db_session, id=async_create_entity.id)

        assert entity is not None
        assert entity.id == async_create_entity.id
        assert entity.text == async_create_entity.text
        assert entity.entity_type == async_create_entity.entity_type
        assert entity.article_id == async_create_entity.article_id

    async def test_get_by_article(self, async_db_session, async_create_article):
        """Test getting entities by article ID asynchronously."""
        # Create multiple entities for the same article
        entities_data = [
            {
                "article_id": async_create_article.id,
                "text": "Entity 1",
                "entity_type": "TYPE1",
                "confidence": 0.9,
                "sentence_context": "Context for entity 1.",
            },
            {
                "article_id": async_create_article.id,
                "text": "Entity 2",
                "entity_type": "TYPE2",
                "confidence": 0.85,
                "sentence_context": "Context for entity 2.",
            },
            {
                "article_id": async_create_article.id,
                "text": "Entity 3",
                "entity_type": "TYPE1",
                "confidence": 0.95,
                "sentence_context": "Context for entity 3.",
            },
        ]

        for entity_data in entities_data:
            db_entity = Entity(**entity_data)
            async_db_session.add(db_entity)
        await async_db_session.commit()

        # Test getting all entities for the article
        entities = await async_entity.get_by_article(
            async_db_session, article_id=async_create_article.id
        )

        assert len(entities) == 3
        entity_texts = [entity.text for entity in entities]
        assert "Entity 1" in entity_texts
        assert "Entity 2" in entity_texts
        assert "Entity 3" in entity_texts

    async def test_get_by_article_empty(self, async_db_session, async_create_article):
        """Test getting entities for an article with no entities asynchronously."""
        entities = await async_entity.get_by_article(
            async_db_session, article_id=async_create_article.id
        )

        assert len(entities) == 0

    async def test_get_by_text_and_article(self, async_db_session, async_create_article):
        """Test getting an entity by text and article ID asynchronously."""
        # Create an entity
        entity_data = {
            "article_id": async_create_article.id,
            "text": "Specific Entity",
            "entity_type": "SPECIFIC",
            "confidence": 0.9,
            "sentence_context": "Context for specific entity.",
        }
        db_entity = Entity(**entity_data)
        async_db_session.add(db_entity)
        await async_db_session.commit()

        # Test getting the entity by text and article ID
        entity = await async_entity.get_by_text_and_article(
            async_db_session, text="Specific Entity", article_id=async_create_article.id
        )

        assert entity is not None
        assert entity.text == "Specific Entity"
        assert entity.article_id == async_create_article.id

    async def test_get_by_text_and_article_not_found(self, async_db_session, async_create_article):
        """Test getting a non-existent entity by text and article ID asynchronously."""
        entity = await async_entity.get_by_text_and_article(
            async_db_session, text="Nonexistent Entity", article_id=async_create_article.id
        )

        assert entity is None

    async def test_get_by_date_range_and_types(self, async_db_session):
        """Test getting entities by date range and entity types asynchronously."""
        now = datetime.now(timezone.utc)

        # Create articles with different publication dates
        article_dates = [
            now - timedelta(days=5),  # 5 days ago
            now - timedelta(days=4),  # 4 days ago
            now - timedelta(days=3),  # 3 days ago
            now - timedelta(days=2),  # 2 days ago
            now - timedelta(days=1),  # 1 day ago
        ]

        articles = []
        for i, date in enumerate(article_dates):
            article = Article(
                title=f"Article {i}",
                content=f"Content of article {i}",
                url=f"https://example.com/article-{i}",
                source="test_source",
                published_at=date,
                status="new",
                scraped_at=now,
            )
            async_db_session.add(article)
            await async_db_session.commit()
            await async_db_session.refresh(article)
            articles.append(article)

        # Create entities with different types for each article
        entity_types = ["PERSON", "LOCATION", "ORGANIZATION", "PERSON", "MISC"]

        for article, entity_type in zip(articles, entity_types):
            entity = Entity(
                article_id=article.id,
                text=f"Entity for article {article.id}",
                entity_type=entity_type,
                confidence=0.9,
                sentence_context=f"Context for article {article.id}",
            )
            async_db_session.add(entity)
        await async_db_session.commit()

        # Test getting entities within a date range (last 3 days)
        start_date = now - timedelta(days=3)
        end_date = now
        entities = await async_entity.get_by_date_range_and_types(
            async_db_session, start_date=start_date, end_date=end_date
        )

        # Should return 3 entities (from 3 days ago until now)
        assert len(entities) == 3

        # Test with entity type filter
        person_entities = await async_entity.get_by_date_range_and_types(
            async_db_session,
            start_date=start_date,
            end_date=end_date,
            entity_types=["PERSON"],
        )

        # Should return 1 entity of type PERSON in the date range
        assert len(person_entities) == 1
        assert person_entities[0].entity_type == "PERSON"

        # Test with multiple entity types
        filtered_entities = await async_entity.get_by_date_range_and_types(
            async_db_session,
            start_date=start_date,
            end_date=end_date,
            entity_types=["PERSON", "LOCATION"],
        )

        # Should return 1 entity (based on our test data, there's only 1 matching entity in range)
        assert len(filtered_entities) == 1

        # Test with a longer date range
        full_date_range = await async_entity.get_by_date_range_and_types(
            async_db_session,
            start_date=now - timedelta(days=10),
            end_date=now,
        )

        # Should return all 5 entities
        assert len(full_date_range) == 5

    async def test_create_bulk(self, async_db_session, async_create_article):
        """Test creating multiple entities in bulk."""
        entities_data = [
            Entity(
                article_id=async_create_article.id,
                text="Bulk Entity 1",
                entity_type="TYPE1",
                confidence=0.9,
                sentence_context="Context for bulk entity 1.",
            ),
            Entity(
                article_id=async_create_article.id,
                text="Bulk Entity 2",
                entity_type="TYPE2",
                confidence=0.85,
                sentence_context="Context for bulk entity 2.",
            ),
            Entity(
                article_id=async_create_article.id,
                text="Bulk Entity 3",
                entity_type="TYPE3",
                confidence=0.95,
                sentence_context="Context for bulk entity 3.",
            ),
        ]

        created_entities = await async_entity.create_bulk(async_db_session, entities=entities_data)

        assert len(created_entities) == 3
        for entity in created_entities:
            assert entity.id is not None
            assert entity.article_id == async_create_article.id

        # Verify they were saved to the database
        result = await async_db_session.execute(
            select(Entity).where(Entity.article_id == async_create_article.id)
        )
        db_entities = result.scalars().all()
        assert len(db_entities) == 3

    async def test_get_with_article(self, async_db_session, async_create_entity):
        """Test getting an entity with its associated article eagerly loaded."""
        entity = await async_entity.get_with_article(
            async_db_session, entity_id=async_create_entity.id
        )

        assert entity is not None
        assert entity.id == async_create_entity.id
        # Check that the article relationship is loaded
        assert entity.article is not None
        assert entity.article.id == async_create_entity.article_id

    async def test_singleton_instance(self):
        """Test that the async_entity is a singleton instance of AsyncCRUDEntity."""
        assert isinstance(async_entity, AsyncCRUDEntity)
        assert async_entity.model == Entity
