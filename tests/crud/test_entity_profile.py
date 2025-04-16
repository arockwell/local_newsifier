"""Tests for the entity profile CRUD module."""

import pytest

from local_newsifier.crud.entity_profile import CRUDEntityProfile
from local_newsifier.crud.entity_profile import entity_profile as entity_profile_crud
from local_newsifier.models.entity_tracking import (
    EntityProfile,
    EntityProfileCreate,
    EntityProfileDB,
)


class TestEntityProfileCRUD:
    """Tests for EntityProfileCRUD class."""

    def test_create(
        self, db_session, create_canonical_entity, sample_entity_profile_data
    ):
        """Test creating a new entity profile."""
        # Ensure the canonical_entity_id matches the one we created
        sample_entity_profile_data["canonical_entity_id"] = create_canonical_entity.id

        obj_in = EntityProfileCreate(**sample_entity_profile_data)
        profile = entity_profile_crud.create(db_session, obj_in=obj_in)

        assert profile is not None
        assert profile.id is not None
        assert profile.canonical_entity_id == obj_in.canonical_entity_id
        assert profile.profile_type == obj_in.profile_type
        assert profile.content == obj_in.content
        assert profile.profile_metadata == obj_in.profile_metadata
        assert profile.created_at is not None
        assert profile.updated_at is not None

        # Verify it was saved to the database
        db_profile = (
            db_session.query(EntityProfileDB)
            .filter(EntityProfileDB.id == profile.id)
            .first()
        )
        assert db_profile is not None
        assert db_profile.canonical_entity_id == obj_in.canonical_entity_id
        assert db_profile.profile_type == obj_in.profile_type

    def test_create_duplicate_fails(
        self, db_session, create_canonical_entity, sample_entity_profile_data
    ):
        """Test creating a duplicate entity profile raises ValueError."""
        # Ensure the canonical_entity_id matches the one we created
        sample_entity_profile_data["canonical_entity_id"] = create_canonical_entity.id

        # Create the first profile
        obj_in = EntityProfileCreate(**sample_entity_profile_data)
        entity_profile_crud.create(db_session, obj_in=obj_in)

        # Attempt to create a duplicate profile
        with pytest.raises(
            ValueError,
            match=f"Profile already exists for entity {create_canonical_entity.id}",
        ):
            entity_profile_crud.create(db_session, obj_in=obj_in)

    def test_get(self, db_session, create_canonical_entity, sample_entity_profile_data):
        """Test getting an entity profile by ID."""
        # Ensure the canonical_entity_id matches the one we created
        sample_entity_profile_data["canonical_entity_id"] = create_canonical_entity.id

        # Create a profile
        db_profile = EntityProfileDB(**sample_entity_profile_data)
        db_session.add(db_profile)
        db_session.commit()

        # Test getting the profile by ID
        profile = entity_profile_crud.get(db_session, id=db_profile.id)

        assert profile is not None
        assert profile.id == db_profile.id
        assert profile.canonical_entity_id == db_profile.canonical_entity_id
        assert profile.profile_type == db_profile.profile_type
        assert profile.content == db_profile.content
        assert profile.profile_metadata == db_profile.profile_metadata

    def test_get_by_entity(
        self, db_session, create_canonical_entity, sample_entity_profile_data
    ):
        """Test getting a profile by entity ID."""
        # Ensure the canonical_entity_id matches the one we created
        sample_entity_profile_data["canonical_entity_id"] = create_canonical_entity.id

        # Create a profile
        db_profile = EntityProfileDB(**sample_entity_profile_data)
        db_session.add(db_profile)
        db_session.commit()

        # Test getting the profile by entity ID
        profile = entity_profile_crud.get_by_entity(
            db_session, entity_id=create_canonical_entity.id
        )

        assert profile is not None
        assert profile.canonical_entity_id == create_canonical_entity.id
        assert profile.profile_type == db_profile.profile_type
        assert profile.content == db_profile.content

    def test_get_by_entity_not_found(self, db_session):
        """Test getting a profile for a non-existent entity."""
        profile = entity_profile_crud.get_by_entity(db_session, entity_id=999)

        assert profile is None

    def test_get_by_entity_and_type(self, db_session, create_canonical_entity):
        """Test getting a profile by entity ID and profile type."""
        # Create multiple profiles for the same entity but different types
        profiles_data = [
            {
                "canonical_entity_id": create_canonical_entity.id,
                "profile_type": "summary",
                "content": "This is a summary profile.",
                "profile_metadata": {"key1": "value1"},
            },
            {
                "canonical_entity_id": create_canonical_entity.id,
                "profile_type": "background",
                "content": "This is a background profile.",
                "profile_metadata": {"key2": "value2"},
            },
            {
                "canonical_entity_id": create_canonical_entity.id,
                "profile_type": "timeline",
                "content": "This is a timeline profile.",
                "profile_metadata": {"key3": "value3"},
            },
        ]

        for profile_data in profiles_data:
            db_profile = EntityProfileDB(**profile_data)
            db_session.add(db_profile)
        db_session.commit()

        # Test getting a specific profile by type
        profile = entity_profile_crud.get_by_entity_and_type(
            db_session, entity_id=create_canonical_entity.id, profile_type="background"
        )

        assert profile is not None
        assert profile.canonical_entity_id == create_canonical_entity.id
        assert profile.profile_type == "background"
        assert profile.content == "This is a background profile."
        assert profile.profile_metadata == {"key2": "value2"}

    def test_get_by_entity_and_type_not_found(
        self, db_session, create_canonical_entity
    ):
        """Test getting a non-existent profile by entity ID and type."""
        profile = entity_profile_crud.get_by_entity_and_type(
            db_session, entity_id=create_canonical_entity.id, profile_type="nonexistent"
        )

        assert profile is None

    def test_update_or_create_update(
        self, db_session, create_canonical_entity, sample_entity_profile_data
    ):
        """Test updating an existing entity profile with update_or_create."""
        # Ensure the canonical_entity_id matches the one we created
        sample_entity_profile_data["canonical_entity_id"] = create_canonical_entity.id
        sample_entity_profile_data["profile_type"] = "summary"

        # Create a profile first
        db_profile = EntityProfileDB(**sample_entity_profile_data)
        db_session.add(db_profile)
        db_session.commit()

        # Original content
        original_content = db_profile.content

        # Update the profile
        update_data = {
            "canonical_entity_id": create_canonical_entity.id,
            "profile_type": "summary",
            "content": "Updated profile content.",
            "profile_metadata": {"updated": True},
        }
        obj_in = EntityProfileCreate(**update_data)
        updated_profile = entity_profile_crud.update_or_create(
            db_session, obj_in=obj_in
        )

        assert updated_profile is not None
        assert updated_profile.id == db_profile.id  # Same ID as before
        assert updated_profile.canonical_entity_id == create_canonical_entity.id
        assert updated_profile.profile_type == "summary"
        assert updated_profile.content == "Updated profile content."
        assert updated_profile.profile_metadata == {"updated": True}
        assert (
            updated_profile.content != original_content
        )  # Content should have changed

        # Verify it was updated in the database
        db_updated = (
            db_session.query(EntityProfileDB)
            .filter(EntityProfileDB.id == db_profile.id)
            .first()
        )
        assert db_updated.content == "Updated profile content."
        assert db_updated.profile_metadata == {"updated": True}

    def test_update_or_create_create(self, db_session, create_canonical_entity):
        """Test creating a new entity profile with update_or_create if none exists."""
        profile_data = {
            "canonical_entity_id": create_canonical_entity.id,
            "profile_type": "new_type",
            "content": "This is a new profile that didn't exist before.",
            "profile_metadata": {"new": True},
        }
        obj_in = EntityProfileCreate(**profile_data)
        profile = entity_profile_crud.update_or_create(db_session, obj_in=obj_in)

        assert profile is not None
        assert profile.id is not None
        assert profile.canonical_entity_id == create_canonical_entity.id
        assert profile.profile_type == "new_type"
        assert profile.content == "This is a new profile that didn't exist before."
        assert profile.profile_metadata == {"new": True}

        # Verify it was saved to the database
        db_profile = (
            db_session.query(EntityProfileDB)
            .filter(
                EntityProfileDB.canonical_entity_id == create_canonical_entity.id,
                EntityProfileDB.profile_type == "new_type",
            )
            .first()
        )
        assert db_profile is not None
        assert db_profile.content == "This is a new profile that didn't exist before."

    def test_singleton_instance(self):
        """Test that the entity_profile_crud is a singleton instance of CRUDEntityProfile."""
        assert isinstance(entity_profile_crud, CRUDEntityProfile)
        assert entity_profile_crud.model == EntityProfileDB
        assert entity_profile_crud.schema == EntityProfile
