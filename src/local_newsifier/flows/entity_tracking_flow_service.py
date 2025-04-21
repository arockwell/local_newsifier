"""Entity tracking flow that uses the updated EntityTracker."""

from datetime import datetime
from typing import Dict, List, Optional, Any

from crewai import Flow

from local_newsifier.models.state import EntityTrackingState, TrackingStatus
from local_newsifier.tools.entity_tracker_service import EntityTracker


class EntityTrackingFlow(Flow):
    """Flow for tracking entities in news articles using the updated EntityTracker."""
    
    def __init__(self, entity_tracker=None):
        """Initialize with dependencies.
        
        Args:
            entity_tracker: Tool for tracking entities
        """
        super().__init__()
        self.entity_tracker = entity_tracker or self._create_default_tracker()
    
    def _create_default_tracker(self):
        """Create default entity tracker."""
        return EntityTracker()
    
    def process(self, state: EntityTrackingState) -> EntityTrackingState:
        """Process an article to track entities.
        
        Args:
            state: Current state with article information
            
        Returns:
            Updated state with entity tracking results
        """
        try:
            # Update state status
            state.status = TrackingStatus.PROCESSING
            state.add_log("Starting entity tracking process")
            
            # Process article using the tracker
            entities = self.entity_tracker.process_article(
                article_id=state.article_id,
                content=state.content,
                title=state.title,
                published_at=state.published_at
            )
            
            # Update state with results
            state.entities = entities
            state.status = TrackingStatus.SUCCESS
            state.add_log("Successfully tracked entities in article")
            
        except Exception as e:
            # Handle errors
            state.set_error("entity_tracking", e)
            state.add_log(f"Error tracking entities: {str(e)}")
        
        return state
