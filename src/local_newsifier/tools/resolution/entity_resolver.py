"""Entity resolver tool for resolving entity mentions to canonical forms."""

import re
from typing import Dict, List, Optional, Any
from difflib import SequenceMatcher


class EntityResolver:
    """Tool for resolving entity mentions to canonical forms."""

    def __init__(self, similarity_threshold: float = 0.85):
        """Initialize the entity resolver.

        Args:
            similarity_threshold: Threshold for entity name similarity (0.0 to 1.0)
        """
        self.similarity_threshold = similarity_threshold
        self.common_titles = [
            "mr", "mrs", "ms", "miss", "dr", "prof", "professor",
            "president", "senator", "representative", "mayor", "governor",
            "chief", "ceo", "cto", "cfo", "director", "chairman",
            "chairwoman", "judge", "justice", "secretary", "minister",
            "sir", "madam",
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
            r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+(?:Jr\.|Sr\.|II|III|IV|V)$": lambda m: m.group(1),
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

    def find_matching_entity(
        self, 
        entity_text: str, 
        entity_type: str,
        existing_entities: List[Dict]
    ) -> Optional[Dict]:
        """Find a matching canonical entity from a list of existing entities.

        Args:
            entity_text: Text of the entity to match
            entity_type: Type of the entity (e.g., "PERSON", "ORG")
            existing_entities: List of existing canonical entities to match against

        Returns:
            Matching canonical entity if found, None otherwise
        """
        # First, try exact match
        for entity in existing_entities:
            if entity["name"].lower() == entity_text.lower() and entity["entity_type"] == entity_type:
                return entity

        # If no exact match, try normalized match
        normalized_text = self.normalize_entity_name(entity_text)
        for entity in existing_entities:
            if entity["name"].lower() == normalized_text.lower() and entity["entity_type"] == entity_type:
                return entity

        # If still no match, search for similar entities
        best_match = None
        best_similarity = 0.0

        for entity in existing_entities:
            if entity["entity_type"] != entity_type:
                continue
                
            similarity = self.calculate_name_similarity(entity_text, entity["name"])
            if similarity > self.similarity_threshold and similarity > best_similarity:
                best_match = entity
                best_similarity = similarity

        return best_match

    def resolve_entity(
        self, 
        entity_text: str, 
        entity_type: str = "PERSON",
        existing_entities: Optional[List[Dict]] = None
    ) -> Dict:
        """Resolve an entity mention to a canonical form.

        Args:
            entity_text: Text of the entity to resolve
            entity_type: Type of the entity (e.g., "PERSON", "ORG")
            existing_entities: Optional list of existing canonical entities to match against

        Returns:
            Canonical entity data
        """
        # If no existing entities provided, create a new canonical entity
        if not existing_entities:
            normalized_name = self.normalize_entity_name(entity_text)
            return {
                "name": normalized_name,
                "entity_type": entity_type,
                "is_new": True,
                "confidence": 1.0,
                "original_text": entity_text
            }
        
        # Try to find a matching entity
        matching_entity = self.find_matching_entity(entity_text, entity_type, existing_entities)
        
        # If a match is found, return it with additional metadata
        if matching_entity:
            result = matching_entity.copy()
            result["is_new"] = False
            result["confidence"] = self.calculate_name_similarity(entity_text, matching_entity["name"])
            result["original_text"] = entity_text
            return result
            
        # If no match found, create a new canonical entity
        normalized_name = self.normalize_entity_name(entity_text)
        return {
            "name": normalized_name,
            "entity_type": entity_type,
            "is_new": True,
            "confidence": 1.0,
            "original_text": entity_text
        }
        
    def resolve_entities(
        self,
        entities: List[Dict],
        existing_entities: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """Resolve multiple entities to canonical forms.
        
        Args:
            entities: List of entity dictionaries with 'text' and 'type' fields
            existing_entities: Optional list of existing canonical entities
            
        Returns:
            List of resolved canonical entities
        """
        resolved_entities = []
        canonical_entities = existing_entities or []
        
        for entity in entities:
            # Skip entities without required fields
            if "text" not in entity or "type" not in entity:
                continue
                
            # Resolve entity
            canonical_entity = self.resolve_entity(
                entity["text"],
                entity["type"],
                canonical_entities
            )
            
            # Add original entity data
            resolved_entity = entity.copy()
            resolved_entity["canonical"] = canonical_entity
            
            # If this is a new entity, add it to our canonical entities list
            if canonical_entity["is_new"]:
                canonical_entities.append(canonical_entity)
                
            resolved_entities.append(resolved_entity)
            
        return resolved_entities
