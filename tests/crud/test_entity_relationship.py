"""Tests for the entity relationship CRUD module."""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from local_newsifier.crud.entity_relationship import CRUDEntityRelationship, entity_relationship as entity_relationship_crud
from local_newsifier.models.entity_tracking import (
    EntityRelationship, EntityRelationshipCreate, entity_relationships
)


class TestEntityRelationshipCRUD:
    """Tests for EntityRelationshipCRUD class."""

    def test_create_or_update_create(self, db_session, create_canonical_entities, sample_entity_relationship_data):
        """Test creating a new entity relationship with create_or_update."""
        # Ensure the entity IDs match the ones we created
        sample_entity_relationship_data["source_entity_id"] = create_canonical_entities[0].id
        sample_entity_relationship_data["target_entity_id"] = create_canonical_entities[1].id
        
        obj_in = EntityRelationshipCreate(**sample_entity_relationship_data)
        relationship = entity_relationship_crud.create_or_update(db_session, obj_in=obj_in)
        
        assert relationship is not None
        assert relationship.source_entity_id == obj_in.source_entity_id
        assert relationship.target_entity_id == obj_in.target_entity_id
        assert relationship.relationship_type == obj_in.relationship_type
        assert relationship.confidence == obj_in.confidence
        assert relationship.evidence == obj_in.evidence
        
        # Verify it was saved to the database
        db_relationship = db_session.query(entity_relationships).filter(
            entity_relationships.c.source_entity_id == obj_in.source_entity_id,
            entity_relationships.c.target_entity_id == obj_in.target_entity_id,
            entity_relationships.c.relationship_type == obj_in.relationship_type
        ).first()
        assert db_relationship is not None
        assert db_relationship.confidence == obj_in.confidence
        assert db_relationship.evidence == obj_in.evidence

    def test_create_or_update_update(self, db_session, create_canonical_entities, sample_entity_relationship_data):
        """Test updating an existing entity relationship with create_or_update."""
        # Ensure the entity IDs match the ones we created
        sample_entity_relationship_data["source_entity_id"] = create_canonical_entities[0].id
        sample_entity_relationship_data["target_entity_id"] = create_canonical_entities[1].id
        
        # Create the relationship first
        result = db_session.execute(
            entity_relationships.insert().values(
                source_entity_id=sample_entity_relationship_data["source_entity_id"],
                target_entity_id=sample_entity_relationship_data["target_entity_id"],
                relationship_type=sample_entity_relationship_data["relationship_type"],
                confidence=sample_entity_relationship_data["confidence"],
                evidence=sample_entity_relationship_data["evidence"],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
        )
        db_session.commit()
        
        # Update the relationship
        update_data = {
            "source_entity_id": sample_entity_relationship_data["source_entity_id"],
            "target_entity_id": sample_entity_relationship_data["target_entity_id"],
            "relationship_type": sample_entity_relationship_data["relationship_type"],
            "confidence": 0.95,  # Changed confidence
            "evidence": "Updated evidence."  # Changed evidence
        }
        obj_in = EntityRelationshipCreate(**update_data)
        updated_relationship = entity_relationship_crud.create_or_update(db_session, obj_in=obj_in)
        
        assert updated_relationship is not None
        assert updated_relationship.source_entity_id == obj_in.source_entity_id
        assert updated_relationship.target_entity_id == obj_in.target_entity_id
        assert updated_relationship.relationship_type == obj_in.relationship_type
        assert updated_relationship.confidence == 0.95  # Updated value
        assert updated_relationship.evidence == "Updated evidence."  # Updated value
        
        # Verify it was updated in the database
        db_updated = db_session.query(entity_relationships).filter(
            entity_relationships.c.source_entity_id == obj_in.source_entity_id,
            entity_relationships.c.target_entity_id == obj_in.target_entity_id,
            entity_relationships.c.relationship_type == obj_in.relationship_type
        ).first()
        assert db_updated.confidence == 0.95
        assert db_updated.evidence == "Updated evidence."

    def test_get(self, db_session, create_canonical_entities, sample_entity_relationship_data):
        """Test getting an entity relationship by source, target, and type."""
        # Ensure the entity IDs match the ones we created
        sample_entity_relationship_data["source_entity_id"] = create_canonical_entities[0].id
        sample_entity_relationship_data["target_entity_id"] = create_canonical_entities[1].id
        
        # Create the relationship
        result = db_session.execute(
            entity_relationships.insert().values(
                source_entity_id=sample_entity_relationship_data["source_entity_id"],
                target_entity_id=sample_entity_relationship_data["target_entity_id"],
                relationship_type=sample_entity_relationship_data["relationship_type"],
                confidence=sample_entity_relationship_data["confidence"],
                evidence=sample_entity_relationship_data["evidence"],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
        )
        db_session.commit()
        
        # Test getting the relationship
        relationship = entity_relationship_crud.get(
            db_session,
            source_entity_id=sample_entity_relationship_data["source_entity_id"],
            target_entity_id=sample_entity_relationship_data["target_entity_id"],
            relationship_type=sample_entity_relationship_data["relationship_type"]
        )
        
        assert relationship is not None
        assert relationship.source_entity_id == sample_entity_relationship_data["source_entity_id"]
        assert relationship.target_entity_id == sample_entity_relationship_data["target_entity_id"]
        assert relationship.relationship_type == sample_entity_relationship_data["relationship_type"]
        assert relationship.confidence == sample_entity_relationship_data["confidence"]
        assert relationship.evidence == sample_entity_relationship_data["evidence"]

    def test_get_not_found(self, db_session, create_canonical_entities):
        """Test getting a non-existent entity relationship."""
        relationship = entity_relationship_crud.get(
            db_session,
            source_entity_id=create_canonical_entities[0].id,
            target_entity_id=create_canonical_entities[1].id,
            relationship_type="NONEXISTENT"
        )
        
        assert relationship is None

    def test_get_by_source_entity(self, db_session, create_canonical_entities):
        """Test getting all relationships for a source entity."""
        # Create multiple relationships with the same source entity
        source_id = create_canonical_entities[0].id
        relationships_data = [
            {
                "source_entity_id": source_id,
                "target_entity_id": create_canonical_entities[1].id,
                "relationship_type": "RELATED_TO",
                "confidence": 0.9,
                "evidence": "Evidence 1",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "source_entity_id": source_id,
                "target_entity_id": create_canonical_entities[2].id,
                "relationship_type": "PART_OF",
                "confidence": 0.85,
                "evidence": "Evidence 2",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "source_entity_id": create_canonical_entities[1].id,  # Different source
                "target_entity_id": source_id,
                "relationship_type": "REFERS_TO",
                "confidence": 0.8,
                "evidence": "Evidence 3",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        ]
        
        for rel_data in relationships_data:
            db_session.execute(entity_relationships.insert().values(**rel_data))
        db_session.commit()
        
        # Test getting relationships by source entity
        relationships = entity_relationship_crud.get_by_source_entity(db_session, source_entity_id=source_id)
        
        assert len(relationships) == 2  # Should only get the relationships where this entity is the source
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

    def test_remove(self, db_session, create_canonical_entities, sample_entity_relationship_data):
        """Test removing an entity relationship."""
        # Ensure the entity IDs match the ones we created
        sample_entity_relationship_data["source_entity_id"] = create_canonical_entities[0].id
        sample_entity_relationship_data["target_entity_id"] = create_canonical_entities[1].id
        
        # Create the relationship
        result = db_session.execute(
            entity_relationships.insert().values(
                source_entity_id=sample_entity_relationship_data["source_entity_id"],
                target_entity_id=sample_entity_relationship_data["target_entity_id"],
                relationship_type=sample_entity_relationship_data["relationship_type"],
                confidence=sample_entity_relationship_data["confidence"],
                evidence=sample_entity_relationship_data["evidence"],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
        )
        db_session.commit()
        
        # Test removing the relationship
        removed = entity_relationship_crud.remove(
            db_session,
            source_entity_id=sample_entity_relationship_data["source_entity_id"],
            target_entity_id=sample_entity_relationship_data["target_entity_id"],
            relationship_type=sample_entity_relationship_data["relationship_type"]
        )
        
        assert removed is True
        
        # Verify it was removed from the database
        db_relationship = db_session.query(entity_relationships).filter(
            entity_relationships.c.source_entity_id == sample_entity_relationship_data["source_entity_id"],
            entity_relationships.c.target_entity_id == sample_entity_relationship_data["target_entity_id"],
            entity_relationships.c.relationship_type == sample_entity_relationship_data["relationship_type"]
        ).first()
        assert db_relationship is None

    def test_remove_not_found(self, db_session, create_canonical_entities):
        """Test removing a non-existent entity relationship."""
        removed = entity_relationship_crud.remove(
            db_session,
            source_entity_id=create_canonical_entities[0].id,
            target_entity_id=create_canonical_entities[1].id,
            relationship_type="NONEXISTENT"
        )
        
        assert removed is False  # Should return False when nothing was removed

    def test_singleton_instance(self):
        """Test that the entity_relationship_crud is a singleton instance of CRUDEntityRelationship."""
        assert isinstance(entity_relationship_crud, CRUDEntityRelationship)
        
    def test_create_or_update_failure(self, db_session, create_canonical_entities, sample_entity_relationship_data, monkeypatch):
        """Test that create_or_update raises ValueError when relationship creation fails."""
        # Ensure the entity IDs match the ones we created
        sample_entity_relationship_data["source_entity_id"] = create_canonical_entities[0].id
        sample_entity_relationship_data["target_entity_id"] = create_canonical_entities[1].id
        
        # Create a mock query that returns None for the created relationship
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        
        # Patch the db.query method to use our mock
        monkeypatch.setattr(db_session, "query", lambda x: mock_query)
        
        # Test that ValueError is raised
        with pytest.raises(ValueError, match="Failed to create entity relationship"):
            obj_in = EntityRelationshipCreate(**sample_entity_relationship_data)
            entity_relationship_crud.create_or_update(db_session, obj_in=obj_in)