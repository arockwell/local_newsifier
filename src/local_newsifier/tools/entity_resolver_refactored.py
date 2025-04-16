"""Entity resolver tool for resolving entity mentions to canonical entities (refactored version).

This module provides a refactored version of the EntityResolver that uses
the database adapter functions directly instead of DatabaseManager.
"""

from typing import Optional

import spacy
from sqlalchemy.orm import Session
from thefuzz import fuzz

from local_newsifier.database import (
    get_canonical_entity_by_name,
    create_canonical_entity,
    with_session,
)
from local_newsifier.models.entity_tracking import (
    CanonicalEntity, CanonicalEntityCreate,
)


class EntityResolverRefactored:
    """Tool for resolving entity mentions to canonical entities."""

    def __init__(
        self,
        session: Optional[Session] = None,
        similarity_threshold: float = 0.85
    ):
        """Initialize the entity resolver.

        Args:
            session: Database session (optional)
            similarity_threshold: Threshold for entity name similarity (0.0 to 1.0)
        """
        self.session = session
        self.similarity_threshold = similarity_threshold

    @with_session
    def resolve_entity(
        self, entity_text: str, entity_type: str = "PERSON", *, session: Session
    ) -> CanonicalEntity:
        """Resolve an entity mention to a canonical entity.

        Args:
            entity_text: Text of the entity mention
            entity_type: Type of the entity
            session: Database session

        Returns:
            Canonical entity
        """
        # First, try to find an exact match
        canonical_entity = get_canonical_entity_by_name(
            name=entity_text, entity_type=entity_type, session=session
        )
        if canonical_entity:
            return canonical_entity

        # If no exact match, try fuzzy matching
        # Try to find existing canonical entities of this type
        canonical_entities = []
        # We need to use a session-specific query here
        # Implement this in the adapter module later
        from local_newsifier.crud.canonical_entity import canonical_entity as canonical_entity_crud
        canonical_entities = canonical_entity_crud.get_by_type(session, entity_type=entity_type)

        best_match = None
        best_score = 0

        # Check each existing entity for similarity
        for entity in canonical_entities:
            # Calculate similarity score
            similarity = fuzz.ratio(entity.name.lower(), entity_text.lower()) / 100.0

            # If similarity is above threshold and better than previous matches
            if similarity > self.similarity_threshold and similarity > best_score:
                best_match = entity
                best_score = similarity

        # If we found a good match, return it
        if best_match:
            return best_match

        # Otherwise, create a new canonical entity
        entity_create = CanonicalEntityCreate(
            name=entity_text,
            entity_type=entity_type,
        )
        new_entity = create_canonical_entity(entity_create, session=session)
        return new_entity