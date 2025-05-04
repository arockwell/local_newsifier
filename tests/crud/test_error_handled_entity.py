"""Tests for the error-handled entity CRUD module."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlmodel import select

from local_newsifier.crud.error_handled_base import (EntityNotFoundError,
                                                     TransactionError,
                                                     ValidationError)
from local_newsifier.crud.error_handled_entity import (ErrorHandledCRUDEntity,
                                                       error_handled_entity)
from local_newsifier.models.article import Article
from local_newsifier.models.entity import Entity


class TestErrorHandledEntityCRUD:
    """Tests for ErrorHandledCRUDEntity class."""

    def test_create(self, db_session, create_article, sample_entity_data):
        """Test creating a new entity with error handling."""
        entity = error_handled_entity.create(db_session, obj_in=sample_entity_data)

        assert entity is not None
        assert entity.id is not None
        assert entity.text == sample_entity_data["text"]
        assert entity.entity_type == sample_entity_data["entity_type"]
        assert entity.confidence == sample_entity_data["confidence"]
        assert entity.article_id == sample_entity_data["article_id"]

        # Verify it was saved to the database
        statement = select(Entity).where(Entity.id == entity.id)
        db_entity = db_session.exec(statement).first()
        assert db_entity is not None
        assert db_entity.text == sample_entity_data["text"]

    def test_create_invalid_article_id(self, db_session, sample_entity_data):
        """Test creating an entity with an invalid article ID."""
        # Modify the sample data to use a non-existent article ID
        invalid_data = dict(sample_entity_data)
        invalid_data["article_id"] = 999  # Non-existent article ID

        # Mock the database error that would occur
        with patch.object(db_session, "commit") as mock_commit:
            # Simulate an IntegrityError for foreign key violation
            mock_commit.side_effect = IntegrityError(
                "FOREIGN KEY constraint failed", params=None, orig=None
            )

            with pytest.raises(ValidationError) as excinfo:
                error_handled_entity.create(db_session, obj_in=invalid_data)

            assert "constraint violation" in str(excinfo.value).lower()
            assert excinfo.value.error_type == "validation"

    def test_get(self, db_session, create_entity):
        """Test getting an entity by ID with error handling."""
        entity = error_handled_entity.get(db_session, id=create_entity.id)

        assert entity is not None
        assert entity.id == create_entity.id
        assert entity.text == create_entity.text
        assert entity.entity_type == create_entity.entity_type
        assert entity.article_id == create_entity.article_id

    def test_get_not_found(self, db_session):
        """Test getting a non-existent entity."""
        with pytest.raises(EntityNotFoundError) as excinfo:
            error_handled_entity.get(db_session, id=999)

        assert "Entity with id 999 not found" in str(excinfo.value)
        assert excinfo.value.error_type == "not_found"
        assert excinfo.value.context["id"] == 999

    def test_get_by_article(self, db_session, create_article):
        """Test getting entities by article ID with error handling."""
        # Create multiple entities for the same article
        entities_data = [
            {
                "article_id": create_article.id,
                "text": "Entity 1",
                "entity_type": "TYPE1",
                "confidence": 0.9,
                "sentence_context": "Context for entity 1.",
            },
            {
                "article_id": create_article.id,
                "text": "Entity 2",
                "entity_type": "TYPE2",
                "confidence": 0.85,
                "sentence_context": "Context for entity 2.",
            },
            {
                "article_id": create_article.id,
                "text": "Entity 3",
                "entity_type": "TYPE1",
                "confidence": 0.95,
                "sentence_context": "Context for entity 3.",
            },
        ]

        for entity_data in entities_data:
            db_entity = Entity(**entity_data)
            db_session.add(db_entity)
        db_session.commit()

        # Test getting all entities for the article
        entities = error_handled_entity.get_by_article(
            db_session, article_id=create_article.id
        )

        assert len(entities) == 3
        entity_texts = [entity.text for entity in entities]
        assert "Entity 1" in entity_texts
        assert "Entity 2" in entity_texts
        assert "Entity 3" in entity_texts

    def test_get_by_article_empty(self, db_session, create_article):
        """Test getting entities for an article with no entities."""
        entities = error_handled_entity.get_by_article(
            db_session, article_id=create_article.id
        )

        assert len(entities) == 0

    def test_get_by_text_and_article(self, db_session, create_article):
        """Test getting an entity by text and article ID with error handling."""
        # Create an entity
        entity_data = {
            "article_id": create_article.id,
            "text": "Specific Entity",
            "entity_type": "SPECIFIC",
            "confidence": 0.9,
            "sentence_context": "Context for specific entity.",
        }
        db_entity = Entity(**entity_data)
        db_session.add(db_entity)
        db_session.commit()

        # Test getting the entity by text and article ID
        entity = error_handled_entity.get_by_text_and_article(
            db_session, text="Specific Entity", article_id=create_article.id
        )

        assert entity is not None
        assert entity.text == "Specific Entity"
        assert entity.article_id == create_article.id

    def test_get_by_text_and_article_not_found(self, db_session, create_article):
        """Test getting a non-existent entity by text and article ID."""
        with pytest.raises(EntityNotFoundError) as excinfo:
            error_handled_entity.get_by_text_and_article(
                db_session, text="Nonexistent Entity", article_id=create_article.id
            )

        assert "Entity with text 'Nonexistent Entity' not found in article" in str(
            excinfo.value
        )
        assert excinfo.value.error_type == "not_found"
        assert excinfo.value.context["text"] == "Nonexistent Entity"
        assert excinfo.value.context["article_id"] == create_article.id

    def test_get_by_date_range_and_types(self, db_session):
        """Test getting entities by date range and entity types with error handling."""
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
            db_session.add(article)
            db_session.commit()
            db_session.refresh(article)
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
            db_session.add(entity)
        db_session.commit()

        # Test getting entities within a date range (last 3 days)
        start_date = now - timedelta(days=3)
        end_date = now
        entities = error_handled_entity.get_by_date_range_and_types(
            db_session, start_date=start_date, end_date=end_date
        )

        # Should return 3 entities (from 3 days ago until now)
        assert len(entities) == 3

        # Test with entity type filter
        person_entities = error_handled_entity.get_by_date_range_and_types(
            db_session,
            start_date=start_date,
            end_date=end_date,
            entity_types=["PERSON"],
        )

        # Should return 1 entity of type PERSON in the date range
        assert len(person_entities) == 1
        assert person_entities[0].entity_type == "PERSON"

        # Test with multiple entity types
        filtered_entities = error_handled_entity.get_by_date_range_and_types(
            db_session,
            start_date=start_date,
            end_date=end_date,
            entity_types=["PERSON", "LOCATION"],
        )

        # Should return 1 entity (based on our test data)
        assert len(filtered_entities) == 1

    def test_remove(self, db_session, create_entity):
        """Test removing an entity with error handling."""
        # Store the entity ID before removal
        entity_id = create_entity.id

        # Remove the entity
        removed_entity = error_handled_entity.remove(db_session, id=entity_id)

        # Verify the entity was returned
        assert removed_entity is not None
        assert removed_entity.id == entity_id

        # Verify it was removed from the database
        db_entity = db_session.get(Entity, entity_id)
        assert db_entity is None

    def test_remove_not_found(self, db_session):
        """Test removing a non-existent entity."""
        with pytest.raises(EntityNotFoundError) as excinfo:
            error_handled_entity.remove(db_session, id=999)

        assert "Entity with id 999 not found" in str(excinfo.value)
        assert excinfo.value.error_type == "not_found"

    def test_update(self, db_session, create_entity):
        """Test updating an entity with error handling."""
        # Update data
        update_data = {
            "text": "Updated Entity",
            "entity_type": "UPDATED_TYPE",
            "confidence": 0.99,
        }

        # Update the entity
        updated_entity = error_handled_entity.update(
            db_session, db_obj=create_entity, obj_in=update_data
        )

        # Verify the update was applied
        assert updated_entity.text == "Updated Entity"
        assert updated_entity.entity_type == "UPDATED_TYPE"
        assert updated_entity.confidence == 0.99

        # Verify it's updated in the database
        db_entity = db_session.get(Entity, create_entity.id)
        assert db_entity.text == "Updated Entity"
        assert db_entity.entity_type == "UPDATED_TYPE"

    def test_database_connection_error(self, db_session, sample_entity_data):
        """Test handling of database connection errors."""
        # Mock a database connection error
        with patch.object(db_session, "commit") as mock_commit:
            mock_commit.side_effect = OperationalError(
                "connection refused", params=None, orig=None
            )

            with pytest.raises(TransactionError) as excinfo:
                error_handled_entity.create(db_session, obj_in=sample_entity_data)

            assert "Database error" in str(excinfo.value)
            assert excinfo.value.error_type == "server"

    def test_singleton_instance(self):
        """Test that the error_handled_entity is a singleton instance of ErrorHandledCRUDEntity."""
        assert isinstance(error_handled_entity, ErrorHandledCRUDEntity)
        assert error_handled_entity.model == Entity
