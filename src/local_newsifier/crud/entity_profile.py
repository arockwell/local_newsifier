"""CRUD operations for entity profiles."""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, Union

from sqlmodel import Session, select

from local_newsifier.crud.base import CRUDBase
from local_newsifier.models.entity_tracking import EntityProfile


class CRUDEntityProfile(CRUDBase[EntityProfile]):
    """CRUD operations for entity profiles."""

    def get_by_entity(
        self, db: Session, *, entity_id: int
    ) -> Optional[EntityProfile]:
        """Get the profile for an entity.

        Args:
            db: Database session
            entity_id: ID of the entity

        Returns:
            Entity profile if found, None otherwise
        """
        statement = select(EntityProfile).where(
            EntityProfile.canonical_entity_id == entity_id
        )
        results = db.execute(statement)
        result = results.first()
        return result[0] if result else None

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
        statement = select(EntityProfile).where(
            EntityProfile.canonical_entity_id == entity_id,
            EntityProfile.profile_type == profile_type
        )
        results = db.execute(statement)
        result = results.first()
        return result[0] if result else None

    def create(
        self, db: Session, *, obj_in: Union[Dict[str, Any], EntityProfile]
    ) -> EntityProfile:
        """Create a new entity profile.

        Args:
            db: Database session
            obj_in: Profile data to create

        Returns:
            Created profile
        """
        # Get the canonical_entity_id from obj_in
        if isinstance(obj_in, dict):
            canonical_entity_id = obj_in["canonical_entity_id"]
        else:
            canonical_entity_id = obj_in.canonical_entity_id
            
        # Check if profile already exists
        statement = select(EntityProfile).where(
            EntityProfile.canonical_entity_id == canonical_entity_id
        )
        result = db.execute(statement).first()
        existing_profile = result[0] if result else None

        if existing_profile:
            entity_id = canonical_entity_id
            raise ValueError(f"Profile already exists for entity {entity_id}")

        return super().create(db, obj_in=obj_in)

    def update_or_create(
        self, db: Session, *, obj_in: Union[Dict[str, Any], EntityProfile]
    ) -> EntityProfile:
        """Update an entity profile or create if it doesn't exist.

        Args:
            db: Database session
            obj_in: Profile data to update or create

        Returns:
            Updated or created profile
        """
        # Get data from obj_in
        if isinstance(obj_in, dict):
            canonical_entity_id = obj_in["canonical_entity_id"]
            profile_type = obj_in["profile_type"]
        else:
            canonical_entity_id = obj_in.canonical_entity_id
            profile_type = obj_in.profile_type
            
        # Get existing profile
        statement = select(EntityProfile).where(
            EntityProfile.canonical_entity_id == canonical_entity_id,
            EntityProfile.profile_type == profile_type
        )
        result = db.execute(statement).first()
        db_profile = result[0] if result else None

        if db_profile:
            # Update profile data
            if isinstance(obj_in, dict):
                update_data = obj_in.copy()
            else:
                update_data = obj_in.model_dump(exclude_unset=True)
                
            update_data["updated_at"] = datetime.now(timezone.utc)

            for field, value in update_data.items():
                if hasattr(db_profile, field):
                    setattr(db_profile, field, value)

            db.add(db_profile)
            db.commit()
            db.refresh(db_profile)
            return db_profile

        # If profile doesn't exist, create it
        return self.create(db, obj_in=obj_in)


entity_profile = CRUDEntityProfile(EntityProfile)
