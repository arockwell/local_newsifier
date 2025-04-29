"""Base class for flow components with standardized dependency injection."""

from typing import Any, Dict, Optional

from local_newsifier.di.dependency_base import DependencyBase


class FlowBase(DependencyBase):
    """Base class for all flows with standardized dependency injection.
    
    This class builds on DependencyBase to provide flow-specific functionality
    while maintaining a consistent approach to dependency injection.
    
    By inheriting from this class, flow implementations get:
    1. Standard dependency resolution from container
    2. Support for explicit dependency injection
    3. Easy access to the container for dynamic resolution
    4. Consistent cleanup mechanism
    """
    
    def __init__(self, container=None, **explicit_deps):
        """Initialize flow with container and explicit dependencies.
        
        Args:
            container: The DI container for resolving dependencies
            **explicit_deps: Explicit dependencies that override container-provided ones
        """
        super().__init__(container)
        
        # Register explicitly provided dependencies
        for name, instance in explicit_deps.items():
            self._register_dependency(name, instance)
    
    def ensure_dependencies(self) -> None:
        """Ensure all required dependencies are available.
        
        Override this method in subclasses to validate that all
        required dependencies are available before operations.
        """
        pass
        
    def cleanup(self) -> None:
        """Clean up resources when the flow is no longer needed.
        
        Override this method in subclasses to handle resource cleanup.
        This method will be called by the container when the flow is removed.
        """
        pass
