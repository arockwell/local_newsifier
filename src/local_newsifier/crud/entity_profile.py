"""CRUD operations for entity profiles."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from local_newsifier.crud.base import CRUDBase
from local_newsifier.models.entity_tracking import (
    EntityProfileDB, EntityProfile, EntityProfileCreate
)


class CRUDEntityProfile(CRUDBase[EntityProfileDB, EntityProfileCreate, EntityProfile]):
    """CRUD operations for entity profiles."""

    def get_by_entity(self, db: Session, *, entity_id: int) -> Optional[EntityProfile]:
        """Get the profile for an entity.

        Args:
            db: Database session
            entity_id: ID of the entity

        Returns:
            Entity profile if found, None otherwise
        """
        db_profile = (
            db.query(EntityProfileDB)
            .filter(EntityProfileDB.canonical_entity_id == entity_id)
            .first()
        )
        return EntityProfile.model_validate(db_profile) if db_profile else None

    def get_by_entity_and_type(
        self, db: Session, *, entity_id: int, profile_type: str
    ) -> Optional[EntityProfile]:
        """Get the profile for an entity by type.

        Args:
            db: Database session
            entity_id: ID of the entity
            profile_type: Type of profile

        Returns:
            Entity profile if found, None otherwise
        """
        db_profile = (
            db.query(EntityProfileDB)
            .filter(
                EntityProfileDB.canonical_entity_id == entity_id,
                EntityProfileDB.profile_type == profile_type,
            )
            .first()
        )
        return EntityProfile.model_validate(db_profile) if db_profile else None

    def create(self, db: Session, *, obj_in: EntityProfileCreate) -> EntityProfile:
        """Create a new entity profile.

        Args:
            db: Database session
            obj_in: Profile data to create

        Returns:
            Created profile
        """
        # Check if profile already exists
        existing_profile = (
            db.query(EntityProfileDB)
            .filter(EntityProfileDB.canonical_entity_id == obj_in.canonical_entity_id)
            .first()
        )
        
        if existing_profile:
            raise ValueError(f"Profile already exists for entity {obj_in.canonical_entity_id}")
            
        return super().create(db, obj_in=obj_in)

    def update_or_create(self, db: Session, *, obj_in: EntityProfileCreate) -> EntityProfile:
        """Update an entity profile or create if it doesn't exist.

        Args:
            db: Database session
            obj_in: Profile data to update or create

        Returns:
            Updated or created profile
        """
        # Get existing profile
        db_profile = (
            db.query(EntityProfileDB)
            .filter(
                EntityProfileDB.canonical_entity_id == obj_in.canonical_entity_id,
                EntityProfileDB.profile_type == obj_in.profile_type
            )
            .first()
        )
        
        if db_profile:
            # Update profile data
            update_data = obj_in.model_dump()
            update_data["updated_at"] = datetime.now(timezone.utc)
            
            for field, value in update_data.items():
                if hasattr(db_profile, field):
                    setattr(db_profile, field, value)
            
            db.add(db_profile)
            db.commit()
            db.refresh(db_profile)
            return EntityProfile.model_validate(db_profile)
        
        # If profile doesn't exist, create it
        return self.create(db, obj_in=obj_in)


entity_profile = CRUDEntityProfile(EntityProfileDB, EntityProfile)