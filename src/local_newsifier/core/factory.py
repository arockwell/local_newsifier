"""Factories for creating application components."""

from local_newsifier.database.session_manager import get_session_manager
from local_newsifier.services.entity_service import EntityService
from local_newsifier.tools.context_analyzer import ContextAnalyzer
from local_newsifier.tools.entity_tracker_v2 import EntityTracker


class ToolFactory:
    """Factory for creating tool instances with their dependencies."""

    @staticmethod
    def create_entity_tracker(
        session_manager=None,
        entity_service=None,
        context_analyzer=None,
        model_name="en_core_web_lg",
        similarity_threshold=0.85
    ):
        """Create an EntityTracker instance with dependencies.

        Args:
            session_manager: Session manager (optional)
            entity_service: Entity service (optional)
            context_analyzer: Context analyzer (optional)
            model_name: Name of the spaCy model
            similarity_threshold: Threshold for name matching

        Returns:
            Configured EntityTracker instance
        """
        # Use provided dependencies or create defaults
        session_mgr = session_manager or get_session_manager()
        entity_svc = entity_service or EntityService(session_manager=session_mgr)
        ctx_analyzer = context_analyzer or ContextAnalyzer(model_name)

        return EntityTracker(
            entity_service=entity_svc,
            context_analyzer=ctx_analyzer,
            session_manager=session_mgr,
            model_name=model_name,
            similarity_threshold=similarity_threshold
        )


class ServiceFactory:
    """Factory for creating service instances."""

    @staticmethod
    def create_entity_service(session_manager=None):
        """Create an EntityService instance.

        Args:
            session_manager: Session manager (optional)

        Returns:
            Configured EntityService instance
        """
        return EntityService(session_manager=session_manager or get_session_manager())
