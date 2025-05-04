"""Flow for tracking entities across news articles."""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Annotated

from crewai import Flow
from fastapi import Depends
from fastapi_injectable import injectable
from sqlmodel import Session

from local_newsifier.crud.article import article as article_crud
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


@injectable(use_cache=False)
class EntityTrackingFlow(Flow):
    """Flow for tracking entities across news articles using state-based pattern."""

    def __init__(
        self, 
        entity_service: EntityService,
        entity_tracker: EntityTracker,
        entity_extractor: EntityExtractor,
        context_analyzer: ContextAnalyzer,
        entity_resolver: EntityResolver,
        session: Session
    ):
        """Initialize the entity tracking flow with injected dependencies.
        
        Args:
            entity_service: Service for entity operations
            entity_tracker: Service for tracking entities
            entity_extractor: Tool for extracting entities
            context_analyzer: Tool for analyzing context
            entity_resolver: Tool for resolving entities
            session: Database session
        """
        super().__init__()
        self.session = session
        self.entity_service = entity_service
        self._entity_tracker = entity_tracker
        self._entity_extractor = entity_extractor
        self._context_analyzer = context_analyzer
        self._entity_resolver = entity_resolver

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
