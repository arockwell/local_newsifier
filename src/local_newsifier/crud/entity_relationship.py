"""CRUD operations for entity relationships."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from local_newsifier.models.entity_tracking import (EntityRelationship,
                                                    EntityRelationshipCreate,
                                                    entity_relationships)


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
        result = (
            db.query(entity_relationships)
            .filter(
                entity_relationships.c.source_entity_id == source_entity_id,
                entity_relationships.c.target_entity_id == target_entity_id,
                entity_relationships.c.relationship_type == relationship_type,
            )
            .first()
        )

        if result:
            return EntityRelationship(
                id=result.id,  # type: ignore
                source_entity_id=result.source_entity_id,
                target_entity_id=result.target_entity_id,
                relationship_type=result.relationship_type,
                confidence=result.confidence,
                evidence=result.evidence,
                created_at=result.created_at,  # type: ignore
                updated_at=result.updated_at,  # type: ignore
            )
        return None

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
        results = (
            db.query(entity_relationships)
            .filter(
                entity_relationships.c.source_entity_id == source_entity_id
            )
            .all()
        )

        return [
            EntityRelationship(
                id=result.id,  # type: ignore
                source_entity_id=result.source_entity_id,
                target_entity_id=result.target_entity_id,
                relationship_type=result.relationship_type,
                confidence=result.confidence,
                evidence=result.evidence,
                created_at=result.created_at,  # type: ignore
                updated_at=result.updated_at,  # type: ignore
            )
            for result in results
        ]

    def create_or_update(
        self, db: Session, *, obj_in: EntityRelationshipCreate
    ) -> EntityRelationship:
        """Create or update an entity relationship.

        Args:
            db: Database session
            obj_in: Relationship data to create or update

        Returns:
            Created or updated relationship
        """
        # Check if relationship already exists
        existing = (
            db.query(entity_relationships)
            .filter(
                entity_relationships.c.source_entity_id
                == obj_in.source_entity_id,
                entity_relationships.c.target_entity_id
                == obj_in.target_entity_id,
                entity_relationships.c.relationship_type
                == obj_in.relationship_type,
            )
            .first()
        )

        if existing:
            # Update existing relationship
            db.execute(
                entity_relationships.update()
                .where(
                    entity_relationships.c.source_entity_id
                    == obj_in.source_entity_id,
                    entity_relationships.c.target_entity_id
                    == obj_in.target_entity_id,
                    entity_relationships.c.relationship_type
                    == obj_in.relationship_type,
                )
                .values(
                    confidence=obj_in.confidence,
                    evidence=obj_in.evidence,
                    updated_at=datetime.now(timezone.utc),
                )
            )
            db.commit()

            # Get the updated relationship
            updated = (
                db.query(entity_relationships)
                .filter(
                    entity_relationships.c.source_entity_id
                    == obj_in.source_entity_id,
                    entity_relationships.c.target_entity_id
                    == obj_in.target_entity_id,
                    entity_relationships.c.relationship_type
                    == obj_in.relationship_type,
                )
                .first()
            )

            if updated:
                return EntityRelationship(
                    id=updated.id,  # type: ignore
                    source_entity_id=updated.source_entity_id,
                    target_entity_id=updated.target_entity_id,
                    relationship_type=updated.relationship_type,
                    confidence=updated.confidence,
                    evidence=updated.evidence,
                    created_at=updated.created_at,  # type: ignore
                    updated_at=updated.updated_at,  # type: ignore
                )

        # Create new relationship
        _ = db.execute(
            entity_relationships.insert().values(
                source_entity_id=obj_in.source_entity_id,
                target_entity_id=obj_in.target_entity_id,
                relationship_type=obj_in.relationship_type,
                confidence=obj_in.confidence,
                evidence=obj_in.evidence,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )
        db.commit()

        # Get the created relationship
        created = (
            db.query(entity_relationships)
            .filter(
                entity_relationships.c.source_entity_id
                == obj_in.source_entity_id,
                entity_relationships.c.target_entity_id
                == obj_in.target_entity_id,
                entity_relationships.c.relationship_type
                == obj_in.relationship_type,
            )
            .first()
        )

        if created:
            return EntityRelationship(
                id=created.id,  # type: ignore
                source_entity_id=created.source_entity_id,
                target_entity_id=created.target_entity_id,
                relationship_type=created.relationship_type,
                confidence=created.confidence,
                evidence=created.evidence,
                created_at=created.created_at,  # type: ignore
                updated_at=created.updated_at,  # type: ignore
            )

        raise ValueError("Failed to create entity relationship")

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
        result = db.execute(
            entity_relationships.delete().where(
                entity_relationships.c.source_entity_id == source_entity_id,
                entity_relationships.c.target_entity_id == target_entity_id,
                entity_relationships.c.relationship_type == relationship_type,
            )
        )
        db.commit()
        return result.rowcount > 0


entity_relationship = CRUDEntityRelationship()
