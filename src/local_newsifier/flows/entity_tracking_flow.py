"""Flow for tracking entities across news articles."""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Annotated

from crewai import Flow
from fastapi import Depends
from fastapi_injectable import injectable
from sqlmodel import Session

from local_newsifier.crud.article import article as article_crud
from local_newsifier.crud.canonical_entity import canonical_entity as canonical_entity_crud
from local_newsifier.crud.entity import entity as entity_crud
from local_newsifier.crud.entity_mention_context import entity_mention_context as entity_mention_context_crud
from local_newsifier.crud.entity_profile import entity_profile as entity_profile_crud
from local_newsifier.models.entity_tracking import CanonicalEntity
from local_newsifier.models.state import (
    EntityTrackingState, EntityBatchTrackingState, 
    EntityDashboardState, EntityRelationshipState, TrackingStatus
)
from local_newsifier.services.entity_service import EntityService
from local_newsifier.tools.entity_tracker_service import EntityTracker
from local_newsifier.tools.extraction.entity_extractor import EntityExtractor
from local_newsifier.tools.analysis.context_analyzer import ContextAnalyzer
from local_newsifier.tools.resolution.entity_resolver import EntityResolver


class EntityTrackingFlow(Flow):
    """Flow for tracking entities across news articles using state-based pattern."""

    def __init__(
        self, 
        entity_service: Optional[EntityService] = None,
        entity_tracker: Optional[EntityTracker] = None,
        entity_extractor: Optional[EntityExtractor] = None,
        context_analyzer: Optional[ContextAnalyzer] = None,
        entity_resolver: Optional[EntityResolver] = None,
        session_factory: Optional[callable] = None,
        session: Optional[Session] = None
    ):
        """Initialize the entity tracking flow.
        
        Args:
            entity_service: Service for entity operations
            entity_tracker: Service for tracking entities
            entity_extractor: Tool for extracting entities
            context_analyzer: Tool for analyzing context
            entity_resolver: Tool for resolving entities
            session_factory: Function to create database sessions
            session: Optional database session
        """
        super().__init__()
        self.session = session

        # Use provided tool dependencies or create defaults
        self._entity_extractor = entity_extractor or EntityExtractor()
        self._context_analyzer = context_analyzer or ContextAnalyzer()
        self._entity_resolver = entity_resolver or EntityResolver()

        # Use provided entity service or create one with dependencies
        if entity_service:
            self.entity_service = entity_service
        else:
            self.entity_service = EntityService(
                entity_crud=entity_crud,
                canonical_entity_crud=canonical_entity_crud,
                entity_mention_context_crud=entity_mention_context_crud,
                entity_profile_crud=entity_profile_crud,
                article_crud=article_crud,
                entity_extractor=self._entity_extractor,
                context_analyzer=self._context_analyzer,
                entity_resolver=self._entity_resolver,
                session_factory=session_factory
            )

        # Entity tracker depends on the entity service
        self._entity_tracker = entity_tracker or EntityTracker(
            entity_service=self.entity_service
        )

    def process(self, state: EntityTrackingState) -> EntityTrackingState:
        """Process a single article for entity tracking.
        
        Args:
            state: EntityTrackingState containing article info
            
        Returns:
            Updated state with processed entities
        """
        try:
            return self.entity_service.process_article_with_state(state)
        except Exception as e:
            # Handle errors by updating the state
            state.status = TrackingStatus.FAILED
            state.set_error("entity_processing", e)
            state.add_log(f"Error processing article: {str(e)}")
            return state

    def process_new_articles(self, state: Optional[EntityBatchTrackingState] = None) -> EntityBatchTrackingState:
        """Process all new articles for entity tracking.
        
        Args:
            state: Optional EntityBatchTrackingState (if not provided, a new one is created)
            
        Returns:
            EntityBatchTrackingState with processed article results
        """
        # Create state if not provided
        if state is None:
            state = EntityBatchTrackingState(status_filter="analyzed")
            
        return self.entity_service.process_articles_batch(state)

    def process_article(self, article_id: int) -> List[Dict]:
        """Legacy method for processing a single article by ID.
        
        Args:
            article_id: ID of the article to process
            
        Returns:
            List of processed entity mentions
        """
        with self.entity_service.session_factory() as session:
            # Get article
            article = article_crud.get(session, id=article_id)
                
            if not article:
                raise ValueError(f"Article with ID {article_id} not found")
            
            # Create state for processing
            state = EntityTrackingState(
                article_id=article.id,
                content=article.content,
                title=article.title,
                published_at=article.published_at or datetime.now(timezone.utc)
            )
            
            # Process article
            result_state = self.process(state)
            
            # Return processed entities
            return result_state.entities

    def get_entity_dashboard(
        self, days: int = 30, entity_type: str = "PERSON"
    ) -> Dict:
        """Generate entity tracking dashboard data.
        
        Args:
            days: Number of days to include in the dashboard
            entity_type: Type of entities to include
            
        Returns:
            Dashboard data with entity statistics
        """
        # Create state for dashboard generation
        state = EntityDashboardState(
            days=days,
            entity_type=entity_type
        )
        
        # Generate dashboard
        result_state = self.entity_service.generate_entity_dashboard(state)
        
        # Return dashboard data
        return result_state.dashboard_data

    def find_entity_relationships(
        self, entity_id: int, days: int = 30
    ) -> Dict:
        """Find relationships between entities based on co-occurrence.
        
        Args:
            entity_id: ID of the canonical entity
            days: Number of days to include
            
        Returns:
            Entity relationships data
        """
        # Create state for relationship analysis
        state = EntityRelationshipState(
            entity_id=entity_id,
            days=days
        )
        
        # Find relationships
        result_state = self.entity_service.find_entity_relationships(state)
        
        # Return relationship data
        return result_state.relationship_data
        
