"""Entity service for coordinating entity-related operations."""

from datetime import datetime
from typing import Dict, List, Optional, Any

from local_newsifier.models.entity import Entity
from local_newsifier.models.entity_tracking import CanonicalEntity, EntityMentionContext, EntityProfile
from local_newsifier.database.engine import SessionManager

class EntityService:
    """Service for entity-related operations using the new refactored tools."""
    
    def __init__(
        self,
        entity_crud,
        canonical_entity_crud,
        entity_mention_context_crud,
        entity_profile_crud,
        entity_extractor,
        context_analyzer,
        entity_resolver,
        session_factory=None
    ):
        """Initialize with dependencies.
        
        Args:
            entity_crud: CRUD for entities
            canonical_entity_crud: CRUD for canonical entities
            entity_mention_context_crud: CRUD for entity mention contexts
            entity_profile_crud: CRUD for entity profiles
            entity_extractor: Tool for extracting entities from text
            context_analyzer: Tool for analyzing entity contexts
            entity_resolver: Tool for resolving entities to canonical forms
            session_factory: Factory for database sessions
        """
        self.entity_crud = entity_crud
        self.canonical_entity_crud = canonical_entity_crud
        self.entity_mention_context_crud = entity_mention_context_crud
        self.entity_profile_crud = entity_profile_crud
        self.entity_extractor = entity_extractor
        self.context_analyzer = context_analyzer
        self.entity_resolver = entity_resolver
        self.session_factory = session_factory
    
    def process_article_entities(
        self, 
        article_id: int,
        content: str,
        title: str,
        published_at: datetime
    ) -> List[Dict[str, Any]]:
        """Process an article to extract and track entities.
        
        Args:
            article_id: ID of the article
            content: Article content
            title: Article title
            published_at: Article publication date
            
        Returns:
            List of processed entities with metadata
        """
        # Extract entities using the new EntityExtractor
        entities = self.entity_extractor.extract_entities(content)
        
        processed_entities = []
        
        # Use the provided session_factory instead of creating a new SessionManager
        with self.session_factory() as session:
            # Get existing canonical entities for resolution
            existing_entities = [
                {
                    "name": entity.name,
                    "entity_type": entity.entity_type,
                    "id": entity.id
                }
                for entity in self.canonical_entity_crud.get_all(session)
            ]
            
            for entity in entities:
                # Analyze context using the new ContextAnalyzer
                context_analysis = self.context_analyzer.analyze_context(entity["context"])
                
                # Resolve entity using the new EntityResolver
                resolved_entity = self.entity_resolver.resolve_entity(
                    entity["text"], 
                    entity["type"],
                    existing_entities
                )
                
                # Handle canonical entity creation or retrieval
                if resolved_entity["is_new"]:
                    canonical_entity_data = CanonicalEntity(
                        name=resolved_entity["name"],
                        entity_type=resolved_entity["entity_type"],
                        entity_metadata={}
                    )
                    canonical_entity = self.canonical_entity_crud.create(
                        session, 
                        obj_in=canonical_entity_data
                    )
                else:
                    canonical_entity = self.canonical_entity_crud.get_by_name(
                        session,
                        name=resolved_entity["name"], 
                        entity_type=resolved_entity["entity_type"]
                    )
                
                # Store entity in database
                entity_data = Entity(
                    article_id=article_id,
                    text=entity["text"],
                    entity_type=entity["type"],
                    confidence=entity.get("confidence", 1.0)
                )
                db_entity = self.entity_crud.create(session, obj_in=entity_data)
                
                # Store entity mention context
                context_data = EntityMentionContext(
                    entity_id=db_entity.id,
                    article_id=article_id,
                    context_text=entity["context"],
                    context_type="sentence",
                    sentiment_score=context_analysis["sentiment"]["score"]
                )
                self.entity_mention_context_crud.create(session, obj_in=context_data)
                
                # Add to results
                processed_entities.append({
                    "original_text": entity["text"],
                    "canonical_name": canonical_entity.name,
                    "canonical_id": canonical_entity.id,
                    "context": entity["context"],
                    "sentiment_score": context_analysis["sentiment"]["score"],
                    "framing_category": context_analysis["framing"]["category"]
                })
        
        return processed_entities
