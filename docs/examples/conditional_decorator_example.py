"""Example implementation of the conditional decorator pattern for injectable components.

This file demonstrates how to implement the conditional decorator pattern
to avoid event loop issues when testing components that use the injectable decorator.
"""

import os
import logging
from typing import Optional, Dict, List, Any, TYPE_CHECKING

from sqlmodel import Session

# Import types only for type checking to avoid circular imports
if TYPE_CHECKING:
    from fastapi_injectable import injectable
    from sqlmodel import Session

logger = logging.getLogger(__name__)


class DataProcessorTool:
    """Example tool that processes data with optional database interaction.
    
    This example demonstrates the conditional decorator pattern for handling
    event loop issues in tests. The class is defined normally without the decorator,
    and the decorator is applied conditionally at the end of the file.
    """
    
    def __init__(self, session: Optional[Session] = None, container=None):
        """Initialize with optional dependencies.
        
        Args:
            session: Optional database session for data persistence
            container: Optional DI container for backward compatibility
        """
        self.session = session
        self._container = container
    
    def set_container(self, container):
        """Set the DI container for backward compatibility.
        
        Args:
            container: DIContainer instance
        """
        self._container = container
    
    def _ensure_dependencies(self):
        """Ensure all dependencies are available.
        
        This provides backward compatibility with the container approach
        and ensures the component can function in both approaches.
        """
        if self.session is None and self._container is not None:
            # Try to get a session from the container if available
            try:
                session_factory = self._container.get("session_factory")
                if session_factory:
                    self.session = session_factory()
            except (KeyError, AttributeError):
                # Failed to get from container, continue with None
                pass
    
    def process_data(self, 
                    data: Dict[str, Any], 
                    *, 
                    session: Optional[Session] = None) -> List[Dict]:
        """Process the provided data.
        
        Args:
            data: The data to process
            session: Optional session override
            
        Returns:
            Processing results
        """
        # Ensure dependencies are initialized
        self._ensure_dependencies()
        
        # Use provided session or instance session
        session = session or self.session
        
        # Process data...
        results = []
        
        if session:
            # Perform database operations with session
            logger.debug("Processing data with database session")
        else:
            # Process without database session
            logger.debug("Processing data without database session")
        
        # Return results
        return results
    
    def save_results(self, 
                    results: List[Dict], 
                    *, 
                    session: Optional[Session] = None) -> bool:
        """Save processing results to the database.
        
        Args:
            results: The processed results to save
            session: Optional session override
            
        Returns:
            True if successful, False otherwise
        """
        # Ensure dependencies are initialized
        self._ensure_dependencies()
        
        # Use provided session or instance session
        session = session or self.session
        
        if not session:
            logger.warning("No session available to save results")
            return False
        
        try:
            # Save results to database
            logger.info(f"Saving {len(results)} results to database")
            return True
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
            return False


# Apply injectable decorator conditionally to avoid test issues
try:
    # Only apply in non-test environments
    if not os.environ.get('PYTEST_CURRENT_TEST'):
        from fastapi_injectable import injectable
        DataProcessorTool = injectable(use_cache=False)(DataProcessorTool)
except (ImportError, Exception):
    pass


# Example provider function (would normally be in di/providers.py)
try:
    # Only define if injectable is available
    from fastapi_injectable import injectable
    from fastapi import Depends
    from typing import Annotated
    
    @injectable(use_cache=False)
    def get_data_processor_tool(
        session: Annotated[Session, Depends("get_session")]
    ) -> DataProcessorTool:
        """Provider for DataProcessorTool."""
        return DataProcessorTool(session=session)
except (ImportError, Exception):
    pass