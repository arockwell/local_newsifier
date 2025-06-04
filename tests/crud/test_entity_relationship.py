"""Tests for the entity relationship CRUD module."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from sqlmodel import Session, select

from local_newsifier.crud.entity_relationship import CRUDEntityRelationship
from local_newsifier.crud.entity_relationship import entity_relationship as entity_relationship_crud
from local_newsifier.models.entity_tracking import EntityRelationship


class TestEntityRelationshipCRUD:
    """Tests for EntityRelationshipCRUD class."""

    def test_create_or_update_create(
        self,
        db_session,
        create_canonical_entities,
        sample_entity_relationship_data,
    ):
        """Test creating a new entity relationship with create_or_update."""
        # Ensure the entity IDs match the ones we created
        sample_entity_relationship_data["source_entity_id"] = create_canonical_entities[0].id
        sample_entity_relationship_data["target_entity_id"] = create_canonical_entities[1].id

        # We can use the dict directly with SQLModel
        relationship = entity_relationship_crud.create_or_update(
            db_session, obj_in=sample_entity_relationship_data
        )

        assert relationship is not None
        assert relationship.source_entity_id == sample_entity_relationship_data["source_entity_id"]
        assert relationship.target_entity_id == sample_entity_relationship_data["target_entity_id"]
        assert (
            relationship.relationship_type == sample_entity_relationship_data["relationship_type"]
        )
        assert relationship.confidence == sample_entity_relationship_data["confidence"]
        assert relationship.evidence == sample_entity_relationship_data["evidence"]

        # Verify it was saved to the database
        statement = select(EntityRelationship).where(
            EntityRelationship.source_entity_id
            == sample_entity_relationship_data["source_entity_id"],
            EntityRelationship.target_entity_id
            == sample_entity_relationship_data["target_entity_id"],
            EntityRelationship.relationship_type
            == sample_entity_relationship_data["relationship_type"],
        )
        result = db_session.execute(statement).first()
        db_relationship = result[0] if result else None
        assert db_relationship is not None
        assert db_relationship.confidence == sample_entity_relationship_data["confidence"]
        assert db_relationship.evidence == sample_entity_relationship_data["evidence"]

    def test_create_or_update_update(
        self,
        db_session,
        create_canonical_entities,
        sample_entity_relationship_data,
    ):
        """Test updating relationship with create_or_update."""
        # Ensure the entity IDs match the ones we created
        sample_entity_relationship_data["source_entity_id"] = create_canonical_entities[0].id
        sample_entity_relationship_data["target_entity_id"] = create_canonical_entities[1].id

        # Create the relationship first
        relationship = EntityRelationship(
            source_entity_id=sample_entity_relationship_data["source_entity_id"],
            target_entity_id=sample_entity_relationship_data["target_entity_id"],
            relationship_type=sample_entity_relationship_data["relationship_type"],
            confidence=sample_entity_relationship_data["confidence"],
            evidence=sample_entity_relationship_data["evidence"],
        )
        db_session.add(relationship)
        db_session.commit()

        # Update the relationship
        update_data = {
            "source_entity_id": sample_entity_relationship_data["source_entity_id"],
            "target_entity_id": sample_entity_relationship_data["target_entity_id"],
            "relationship_type": sample_entity_relationship_data["relationship_type"],
            "confidence": 0.95,  # Changed confidence
            "evidence": "Updated evidence.",  # Changed evidence
        }
        updated_relationship = entity_relationship_crud.create_or_update(
            db_session, obj_in=update_data
        )

        assert updated_relationship is not None
        assert updated_relationship.source_entity_id == update_data["source_entity_id"]
        assert updated_relationship.target_entity_id == update_data["target_entity_id"]
        assert updated_relationship.relationship_type == update_data["relationship_type"]
        assert updated_relationship.confidence == 0.95  # Updated value
        assert updated_relationship.evidence == "Updated evidence."  # Updated value

        # Verify it was updated in the database
        statement = select(EntityRelationship).where(
            EntityRelationship.source_entity_id == update_data["source_entity_id"],
            EntityRelationship.target_entity_id == update_data["target_entity_id"],
            EntityRelationship.relationship_type == update_data["relationship_type"],
        )
        result = db_session.execute(statement).first()
        db_updated = result[0] if result else None
        assert db_updated.confidence == 0.95
        assert db_updated.evidence == "Updated evidence."

    def test_get(
        self,
        db_session,
        create_canonical_entities,
        sample_entity_relationship_data,
    ):
        """Test getting an entity relationship by source, target, and type."""
        # Ensure the entity IDs match the ones we created
        sample_entity_relationship_data["source_entity_id"] = create_canonical_entities[0].id
        sample_entity_relationship_data["target_entity_id"] = create_canonical_entities[1].id

        # Create the relationship
        relationship = EntityRelationship(
            source_entity_id=sample_entity_relationship_data["source_entity_id"],
            target_entity_id=sample_entity_relationship_data["target_entity_id"],
            relationship_type=sample_entity_relationship_data["relationship_type"],
            confidence=sample_entity_relationship_data["confidence"],
            evidence=sample_entity_relationship_data["evidence"],
        )
        db_session.add(relationship)
        db_session.commit()

        # Test getting the relationship
        relationship = entity_relationship_crud.get(
            db_session,
            source_entity_id=sample_entity_relationship_data["source_entity_id"],
            target_entity_id=sample_entity_relationship_data["target_entity_id"],
            relationship_type=sample_entity_relationship_data["relationship_type"],
        )

        assert relationship is not None
        assert relationship.source_entity_id == sample_entity_relationship_data["source_entity_id"]
        assert relationship.target_entity_id == sample_entity_relationship_data["target_entity_id"]
        assert (
            relationship.relationship_type == sample_entity_relationship_data["relationship_type"]
        )
        assert relationship.confidence == sample_entity_relationship_data["confidence"]
        assert relationship.evidence == sample_entity_relationship_data["evidence"]

    def test_get_not_found(self, db_session, create_canonical_entities):
        """Test getting a non-existent entity relationship."""
        relationship = entity_relationship_crud.get(
            db_session,
            source_entity_id=create_canonical_entities[0].id,
            target_entity_id=create_canonical_entities[1].id,
            relationship_type="NONEXISTENT",
        )

        assert relationship is None

    def test_get_by_source_entity(self, db_session, create_canonical_entities):
        """Test getting all relationships for a source entity."""
        # Create multiple relationships with the same source entity
        source_id = create_canonical_entities[0].id
        relationships_data = [
            EntityRelationship(
                source_entity_id=source_id,
                target_entity_id=create_canonical_entities[1].id,
                relationship_type="RELATED_TO",
                confidence=0.9,
                evidence="Evidence 1",
            ),
            EntityRelationship(
                source_entity_id=source_id,
                target_entity_id=create_canonical_entities[2].id,
                relationship_type="PART_OF",
                confidence=0.85,
                evidence="Evidence 2",
            ),
            EntityRelationship(
                source_entity_id=create_canonical_entities[1].id,  # Different source
                target_entity_id=source_id,
                relationship_type="REFERS_TO",
                confidence=0.8,
                evidence="Evidence 3",
            ),
        ]

        for relationship in relationships_data:
            db_session.add(relationship)
        db_session.commit()

        # Test getting relationships by source entity
        relationships = entity_relationship_crud.get_by_source_entity(
            db_session, source_entity_id=source_id
        )

        assert (
            len(relationships) == 2
        )  # Should only get the relationships where this entity is the source
        relationship_types = [rel.relationship_type for rel in relationships]
        assert "RELATED_TO" in relationship_types
        assert "PART_OF" in relationship_types
        assert "REFERS_TO" not in relationship_types  # This one has a different source

    def test_get_by_source_entity_empty(self, db_session, create_canonical_entities):
        """Test getting relationships for an entity with no relationships."""
        relationships = entity_relationship_crud.get_by_source_entity(
            db_session, source_entity_id=create_canonical_entities[0].id
        )

        assert len(relationships) == 0

    def test_remove(
        self,
        db_session,
        create_canonical_entities,
        sample_entity_relationship_data,
    ):
        """Test removing an entity relationship."""
        # Ensure the entity IDs match the ones we created
        sample_entity_relationship_data["source_entity_id"] = create_canonical_entities[0].id
        sample_entity_relationship_data["target_entity_id"] = create_canonical_entities[1].id

        # Create the relationship
        relationship = EntityRelationship(
            source_entity_id=sample_entity_relationship_data["source_entity_id"],
            target_entity_id=sample_entity_relationship_data["target_entity_id"],
            relationship_type=sample_entity_relationship_data["relationship_type"],
            confidence=sample_entity_relationship_data["confidence"],
            evidence=sample_entity_relationship_data["evidence"],
        )
        db_session.add(relationship)
        db_session.commit()

        # Test removing the relationship
        removed = entity_relationship_crud.remove(
            db_session,
            source_entity_id=sample_entity_relationship_data["source_entity_id"],
            target_entity_id=sample_entity_relationship_data["target_entity_id"],
            relationship_type=sample_entity_relationship_data["relationship_type"],
        )

        assert removed is True

        # Verify it was removed from the database
        statement = select(EntityRelationship).where(
            EntityRelationship.source_entity_id
            == sample_entity_relationship_data["source_entity_id"],
            EntityRelationship.target_entity_id
            == sample_entity_relationship_data["target_entity_id"],
            EntityRelationship.relationship_type
            == sample_entity_relationship_data["relationship_type"],
        )
        result = db_session.execute(statement).first()
        db_relationship = result[0] if result else None
        assert db_relationship is None

    def test_remove_not_found(self, db_session, create_canonical_entities):
        """Test removing a non-existent entity relationship."""
        removed = entity_relationship_crud.remove(
            db_session,
            source_entity_id=create_canonical_entities[0].id,
            target_entity_id=create_canonical_entities[1].id,
            relationship_type="NONEXISTENT",
        )

        assert removed is False  # Should return False when nothing was removed

    def test_singleton_instance(self):
        """Test singleton instance behavior."""
        assert isinstance(entity_relationship_crud, CRUDEntityRelationship)

    def test_create_or_update_failure(
        self,
        db_session,
        create_canonical_entities,
        sample_entity_relationship_data,
        monkeypatch,
    ):
        """Test create_or_update raises ValueError on creation failure."""
        # Ensure the entity IDs match the ones we created
        sample_entity_relationship_data["source_entity_id"] = create_canonical_entities[0].id
        sample_entity_relationship_data["target_entity_id"] = create_canonical_entities[1].id

        # Create a mock statement that returns None for the created relationship
        def mock_execute(*args, **kwargs):
            mock_result = MagicMock()
            mock_result.first.return_value = None
            return mock_result

        # Patch the exec method to use our mock
        monkeypatch.setattr(db_session, "exec", mock_execute)

        # Test that ValueError is raised
        with pytest.raises(ValueError, match="Failed to create entity relationship"):
            entity_relationship_crud.create_or_update(
                db_session, obj_in=sample_entity_relationship_data
            )
