"""Tests for the entity relationship CRUD module using model inputs."""

from sqlmodel import select

from local_newsifier.crud.entity_relationship import entity_relationship as entity_relationship_crud
from local_newsifier.models.entity_tracking import EntityRelationship


def test_create_or_update_with_model_input(
    db_session,
    create_canonical_entities,
    sample_entity_relationship_data,
):
    """Test creating an entity relationship with a model instance instead of dict."""
    # Ensure the entity IDs match the ones we created
    source_id = create_canonical_entities[0].id
    target_id = create_canonical_entities[1].id

    # Create an EntityRelationship instance instead of using a dict
    relationship_model = EntityRelationship(
        source_entity_id=source_id,
        target_entity_id=target_id,
        relationship_type="TEST_MODEL_RELATIONSHIP",
        confidence=0.88,
        evidence="Evidence for model test",
    )

    # Test create_or_update with model instance
    created_relationship = entity_relationship_crud.create_or_update(
        db_session, obj_in=relationship_model
    )

    # Verify the result
    assert created_relationship is not None
    assert created_relationship.source_entity_id == source_id
    assert created_relationship.target_entity_id == target_id
    assert created_relationship.relationship_type == "TEST_MODEL_RELATIONSHIP"
    assert created_relationship.confidence == 0.88
    assert created_relationship.evidence == "Evidence for model test"

    # Verify it was saved to the database
    statement = select(EntityRelationship).where(
        EntityRelationship.source_entity_id == source_id,
        EntityRelationship.target_entity_id == target_id,
        EntityRelationship.relationship_type == "TEST_MODEL_RELATIONSHIP",
    )
    result = db_session.execute(statement).first()
    db_relationship = result[0] if result else None
    assert db_relationship is not None
    assert db_relationship.confidence == 0.88
    assert db_relationship.evidence == "Evidence for model test"


def test_create_or_update_update_with_model_input(
    db_session,
    create_canonical_entities,
):
    """Test updating a relationship using a model instance."""
    # Create entities for the relationship
    source_id = create_canonical_entities[0].id
    target_id = create_canonical_entities[1].id

    # First create the relationship
    initial_relationship = EntityRelationship(
        source_entity_id=source_id,
        target_entity_id=target_id,
        relationship_type="UPDATE_TEST_RELATIONSHIP",
        confidence=0.75,
        evidence="Initial evidence",
    )
    db_session.add(initial_relationship)
    db_session.commit()

    # Create a new model instance with updated values for the same relationship
    updated_model = EntityRelationship(
        source_entity_id=source_id,
        target_entity_id=target_id,
        relationship_type="UPDATE_TEST_RELATIONSHIP",  # Same key fields
        confidence=0.90,  # Updated confidence
        evidence="Updated evidence",  # Updated evidence
    )

    # Test update with model instance
    updated_relationship = entity_relationship_crud.create_or_update(
        db_session, obj_in=updated_model
    )

    # Verify the result has updated values
    assert updated_relationship is not None
    assert updated_relationship.source_entity_id == source_id
    assert updated_relationship.target_entity_id == target_id
    assert updated_relationship.relationship_type == "UPDATE_TEST_RELATIONSHIP"
    assert updated_relationship.confidence == 0.90  # Updated
    assert updated_relationship.evidence == "Updated evidence"  # Updated

    # Verify it was updated in the database - should be only one record
    statement = select(EntityRelationship).where(
        EntityRelationship.source_entity_id == source_id,
        EntityRelationship.target_entity_id == target_id,
        EntityRelationship.relationship_type == "UPDATE_TEST_RELATIONSHIP",
    )
    results = db_session.exec(statement).all()
    assert len(results) == 1  # Should only be one relationship
    assert results[0].confidence == 0.90
    assert results[0].evidence == "Updated evidence"
