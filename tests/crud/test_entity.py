"""Tests for the entity CRUD module."""

# We need pytest for fixtures but don't explicitly use it
from sqlmodel import select

from local_newsifier.crud.entity import CRUDEntity
from local_newsifier.crud.entity import entity as entity_crud
from local_newsifier.models.database.entity import Entity


class TestEntityCRUD:
    """Tests for EntityCRUD class."""

    def test_create(self, db_session, create_article, sample_entity_data):
        """Test creating a new entity."""
        entity = entity_crud.create(db_session, obj_in=sample_entity_data)

        assert entity is not None
        assert entity.id is not None
        assert entity.text == sample_entity_data["text"]
        assert entity.entity_type == sample_entity_data["entity_type"]
        assert entity.confidence == sample_entity_data["confidence"]
        assert entity.article_id == sample_entity_data["article_id"]

        # Verify it was saved to the database
        db_entity = (
            db_session.exec(select(Entity)).filter(Entity.id == entity.id).first()
        )
        assert db_entity is not None
        assert db_entity.text == sample_entity_data["text"]

    def test_get(self, db_session, create_entity):
        """Test getting an entity by ID."""
        entity = entity_crud.get(db_session, id=create_entity.id)

        assert entity is not None
        assert entity.id == create_entity.id
        assert entity.text == create_entity.text
        assert entity.entity_type == create_entity.entity_type
        assert entity.article_id == create_entity.article_id

    def test_get_by_article(self, db_session, create_article):
        """Test getting entities by article ID."""
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
        entities = entity_crud.get_by_article(
            db_session, article_id=create_article.id
        )

        assert len(entities) == 3
        entity_texts = [entity.text for entity in entities]
        assert "Entity 1" in entity_texts
        assert "Entity 2" in entity_texts
        assert "Entity 3" in entity_texts

    def test_get_by_article_empty(self, db_session, create_article):
        """Test getting entities for an article with no entities."""
        entities = entity_crud.get_by_article(
            db_session, article_id=create_article.id
        )

        assert len(entities) == 0

    def test_get_by_text_and_article(self, db_session, create_article):
        """Test getting an entity by text and article ID."""
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
        entity = entity_crud.get_by_text_and_article(
            db_session, text="Specific Entity", article_id=create_article.id
        )

        assert entity is not None
        assert entity.text == "Specific Entity"
        assert entity.article_id == create_article.id

    def test_get_by_text_and_article_not_found(
        self, db_session, create_article
    ):
        """Test getting a non-existent entity by text and article ID."""
        entity = entity_crud.get_by_text_and_article(
            db_session, text="Nonexistent Entity", article_id=create_article.id
        )

        assert entity is None

    def test_singleton_instance(self):
        """Test that the entity_crud is a singleton instance of CRUDEntity."""
        assert isinstance(entity_crud, CRUDEntity)
        assert entity_crud.model == Entity
