"""Entity tracker tool that uses the EntityService."""

import os
from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlmodel import Session

from local_newsifier.database.engine import with_session, get_session
from local_newsifier.services.entity_service import EntityService
from local_newsifier.crud.entity import entity as entity_crud
from local_newsifier.crud.canonical_entity import canonical_entity as canonical_entity_crud
from local_newsifier.crud.entity_mention_context import entity_mention_context as entity_mention_context_crud
from local_newsifier.crud.entity_profile import entity_profile as entity_profile_crud
from local_newsifier.crud.article import article as article_crud
from local_newsifier.tools.extraction.entity_extractor import EntityExtractor
from local_newsifier.tools.analysis.context_analyzer import ContextAnalyzer
from local_newsifier.tools.resolution.entity_resolver import EntityResolver


class EntityTracker:
    """Tool for tracking entities across news articles using the EntityService."""
    
    def __init__(self, entity_service=None, session=None, container=None):
        """Initialize with dependencies.
        
        Args:
            entity_service: Service for entity operations
            session: Database session
            container: Optional DI container for backward compatibility
        """
        self.entity_service = entity_service
        self.session = session
        self._container = container
        
        # Initialize dependencies if needed
        self._ensure_dependencies()
    
    def _ensure_dependencies(self):
        """Ensure all dependencies are available.
        
        This handles backward compatibility by attempting to get
        missing dependencies from the container.
        """
        # Create a default entity service if none was provided
        if self.entity_service is None:
            if self._container is not None:
                try:
                    # Try to get from container first
                    self.entity_service = self._container.get("entity_service")
                except (KeyError, AttributeError):
                    # Fall back to creating a default service
                    self.entity_service = self._create_default_service()
            else:
                # No container, create default service
                self.entity_service = self._create_default_service()
    
    def _create_default_service(self):
        """Create default entity service with all dependencies."""
        return EntityService(
            entity_crud=entity_crud,
            canonical_entity_crud=canonical_entity_crud,
            entity_mention_context_crud=entity_mention_context_crud,
            entity_profile_crud=entity_profile_crud,
            article_crud=article_crud,
            entity_extractor=EntityExtractor(),
            context_analyzer=ContextAnalyzer(),
            entity_resolver=EntityResolver(),
            session_factory=get_session
        )
    
    @with_session
    def process_article(
        self, 
        article_id: int,
        content: str,
        title: str,
        published_at: datetime,
        *,
        session: Session = None
    ) -> List[Dict[str, Any]]:
        """Process an article to track entity mentions.
        
        Args:
            article_id: ID of the article being processed
            content: Article content
            title: Article title
            published_at: Article publication date
            session: Database session
            
        Returns:
            List of processed entity mentions
        """
        # Ensure dependencies are available
        self._ensure_dependencies()
        
        # Delegate to the service
        return self.entity_service.process_article_entities(
            article_id=article_id,
            content=content,
            title=title,
            published_at=published_at
        )