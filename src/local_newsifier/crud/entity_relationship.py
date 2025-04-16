"""CRUD operations for entity relationships."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlmodel import Session, select, delete

from local_newsifier.models.entity_tracking import EntityRelationship


class CRUDEntityRelationship:
    """CRUD operations for entity relationships."""

    def get(
        self,
        db: Session,
        *,
        source_entity_id: int,
        target_entity_id: int,
        relationship_type: str
    ) -> Optional[EntityRelationship]:
        """Get a relationship by source, target, and type.

        Args:
            db: Database session
            source_entity_id: ID of the source entity
            target_entity_id: ID of the target entity
            relationship_type: Type of the relationship

        Returns:
            Entity relationship if found, None otherwise
        """
        statement = select(EntityRelationship).where(
            EntityRelationship.source_entity_id == source_entity_id,
            EntityRelationship.target_entity_id == target_entity_id,
            EntityRelationship.relationship_type == relationship_type
        )
        results = db.exec(statement)
        return results.first()

    def get_by_source_entity(
        self, db: Session, *, source_entity_id: int
    ) -> List[EntityRelationship]:
        """Get all relationships for a source entity.

        Args:
            db: Database session
            source_entity_id: ID of the source entity

        Returns:
            List of entity relationships
        """
        statement = select(EntityRelationship).where(
            EntityRelationship.source_entity_id == source_entity_id
        )
        results = db.exec(statement)
        return results.all()

    def create_or_update(
        self, db: Session, *, obj_in: EntityRelationship
    ) -> EntityRelationship:
        """Create or update an entity relationship.

        Args:
            db: Database session
            obj_in: Relationship data to create or update

        Returns:
            Created or updated relationship
        """
        # Check if relationship already exists
        statement = select(EntityRelationship).where(
            EntityRelationship.source_entity_id == obj_in.source_entity_id,
            EntityRelationship.target_entity_id == obj_in.target_entity_id,
            EntityRelationship.relationship_type == obj_in.relationship_type
        )
        results = db.exec(statement)
        existing = results.first()

        if existing:
            # Update fields of existing relationship
            existing.confidence = obj_in.confidence
            existing.evidence = obj_in.evidence
            existing.updated_at = datetime.now(timezone.utc)
            
            db.add(existing)
            db.commit()
            db.refresh(existing)
            return existing
        
        # Create new relationship
        db_obj = EntityRelationship(
            source_entity_id=obj_in.source_entity_id,
            target_entity_id=obj_in.target_entity_id,
            relationship_type=obj_in.relationship_type,
            confidence=obj_in.confidence,
            evidence=obj_in.evidence
        )
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        return db_obj

    def remove(
        self,
        db: Session,
        *,
        source_entity_id: int,
        target_entity_id: int,
        relationship_type: str
    ) -> bool:
        """Remove a relationship.

        Args:
            db: Database session
            source_entity_id: ID of the source entity
            target_entity_id: ID of the target entity
            relationship_type: Type of the relationship

        Returns:
            True if the relationship was removed, False otherwise
        """
        statement = select(EntityRelationship).where(
            EntityRelationship.source_entity_id == source_entity_id,
            EntityRelationship.target_entity_id == target_entity_id,
            EntityRelationship.relationship_type == relationship_type
        )
        results = db.exec(statement)
        entity_to_delete = results.first()
        
        if entity_to_delete:
            db.delete(entity_to_delete)
            db.commit()
            return True
        
        return False


entity_relationship = CRUDEntityRelationship()
