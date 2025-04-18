"""Entity resolver tool for resolving entity mentions to canonical entities."""

import re
from typing import Dict, List, Optional, Tuple, Union, Any

from difflib import SequenceMatcher
from sqlmodel import Session

from local_newsifier.database.engine import with_session
from local_newsifier.crud.canonical_entity import canonical_entity as canonical_entity_crud
from local_newsifier.models.entity_tracking import CanonicalEntity


class EntityResolver:
    """Tool for resolving entity mentions to canonical entities."""

    def __init__(
        self, 
        session: Optional[Session] = None, 
        similarity_threshold: float = 0.85
    ):
        """Initialize the entity resolver.

        Args:
            session: SQLAlchemy session instance
            similarity_threshold: Threshold for entity name similarity (0.0 to 1.0)
        """
        self.session = session
        self.similarity_threshold = similarity_threshold
        self.common_titles = [
            "mr",
            "mrs",
            "ms",
            "miss",
            "dr",
            "prof",
            "professor",
            "president",
            "senator",
            "representative",
            "mayor",
            "governor",
            "chief",
            "ceo",
            "cto",
            "cfo",
            "director",
            "chairman",
            "chairwoman",
            "judge",
            "justice",
            "secretary",
            "minister",
            "sir",
            "madam",
        ]
        self.name_patterns = {
            # Standard name with titles: "President Joe Biden" -> "Joe Biden"
            r"^(?:{})\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)$".format(
                "|".join(self.common_titles)
            ): lambda m: m.group(1),
            # Reversed name with comma: "Biden, Joe" -> "Joe Biden"
            r"^([A-Z][a-z]+),\s+([A-Z][a-z]+)$": lambda m: f"{m.group(2)} {m.group(1)}",
            # Name with middle initial: "Joe R. Biden" -> "Joe Biden"
            r"^([A-Z][a-z]+)\s+[A-Z]\.\s+([A-Z][a-z]+)$": lambda m: f"{m.group(1)} {m.group(2)}",
            # Name with suffix: "Joe Biden Jr." -> "Joe Biden"
            r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+(?:Jr\.|Sr\.|II|III|IV|V)$": lambda m: m.group(
                1
            ),
        }

    def normalize_entity_name(self, name: str) -> str:
        """Normalize an entity name by removing titles, suffixes, etc.

        Args:
            name: Entity name to normalize

        Returns:
            Normalized entity name
        """
        # Convert to lowercase for comparison
        name = name.strip()

        # Apply patterns to normalize name
        for pattern, replacement in self.name_patterns.items():
            match = re.match(pattern, name, re.IGNORECASE)
            if match:
                return replacement(match)

        return name

    def calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two entity names.

        Args:
            name1: First entity name
            name2: Second entity name

        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Normalize names
        norm_name1 = self.normalize_entity_name(name1)
        norm_name2 = self.normalize_entity_name(name2)

        # Calculate similarity
        return SequenceMatcher(None, norm_name1.lower(), norm_name2.lower()).ratio()

    @with_session
    def find_matching_entity(
        self, name: str, entity_type: str = "PERSON", *, session: Session = None
    ) -> Optional[CanonicalEntity]:
        """Find a matching canonical entity for a given entity name.

        Args:
            name: Entity name to find
            entity_type: Type of the entity (default: "PERSON")
            session: Database session

        Returns:
            Matching canonical entity if found, None otherwise
        """
        # Use provided session if available, otherwise use the stored session
        if session is None and self.session is not None:
            session = self.session
            
        # First, try exact match
        canonical_entity = canonical_entity_crud.get_by_name(
            session, name=name, entity_type=entity_type
        )
        if canonical_entity:
            return canonical_entity

        # If no exact match, try normalized match
        normalized_name = self.normalize_entity_name(name)
        canonical_entity = canonical_entity_crud.get_by_name(
            session, name=normalized_name, entity_type=entity_type
        )
        if canonical_entity:
            return canonical_entity

        # If still no match, search for similar entities
        all_canonical_entities = canonical_entity_crud.get_all(
            session, entity_type=entity_type
        )

        best_match = None
        best_similarity = 0.0

        for entity in all_canonical_entities:
            similarity = self.calculate_name_similarity(name, entity.name)
            if similarity > self.similarity_threshold and similarity > best_similarity:
                best_match = entity
                best_similarity = similarity

        return best_match

    @with_session
    def resolve_entity(
        self, 
        name: str, 
        entity_type: str = "PERSON", 
        metadata: Dict = None,
        *, 
        session: Session = None
    ) -> CanonicalEntity:
        """Resolve an entity mention to a canonical entity, creating a new one if needed.

        Args:
            name: Entity name to resolve
            entity_type: Type of the entity (default: "PERSON")
            metadata: Optional metadata for the entity
            session: Database session

        Returns:
            Resolved canonical entity
        """
        # Use provided session if available, otherwise use the stored session
        if session is None and self.session is not None:
            session = self.session
            
        # Try to find a matching entity
        canonical_entity = self.find_matching_entity(name, entity_type, session=session)

        # If no matching entity found, create a new one
        if not canonical_entity:
            normalized_name = self.normalize_entity_name(name)
            canonical_entity_data = CanonicalEntity(
                name=normalized_name,
                entity_type=entity_type,
                entity_metadata=metadata or {},
            )
            
            canonical_entity = canonical_entity_crud.create(
                session, obj_in=canonical_entity_data
            )

        return canonical_entity
