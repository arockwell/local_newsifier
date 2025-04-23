"""Entity Resolver for mapping detected entities to canonical forms."""

from typing import Dict, List, Any, Optional


class EntityResolver:
    """Entity resolver for mapping detected entities to canonical forms."""
    
    def resolve_entity(
        self, 
        text: str, 
        entity_type: str,
        existing_entities: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Resolve an entity text to its canonical form.
        
        Args:
            text: Entity text
            entity_type: Type of entity
            existing_entities: List of existing canonical entities
            
        Returns:
            Resolved entity information
        """
        # Simple implementation for testing
        if not existing_entities:
            existing_entities = []
            
        # Check if entity already exists
        for entity in existing_entities:
            if entity["name"].lower() == text.lower() and entity["entity_type"] == entity_type:
                return {
                    "name": entity["name"],
                    "entity_type": entity["entity_type"],
                    "id": entity["id"],
                    "is_new": False
                }
        
        # Entity doesn't exist, return as new
        return {
            "name": text,
            "entity_type": entity_type,
            "is_new": True
        }
