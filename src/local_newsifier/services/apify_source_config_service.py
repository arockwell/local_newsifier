"""
Service for managing Apify source configurations.

This module provides functionality for Apify source configuration management,
including adding, updating, and retrieving configurations.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from sqlmodel import Session

from local_newsifier.crud.apify_source_config import apify_source_config
from local_newsifier.models.apify import ApifySourceConfig
from local_newsifier.services.apify_service import ApifyService

logger = logging.getLogger(__name__)


class ApifySourceConfigService:
    """Service for Apify source configuration management."""

    def __init__(
        self,
        apify_source_config_crud=None,
        apify_service=None,
        session_factory=None,
        container=None,
    ):
        """Initialize with dependencies.

        Args:
            apify_source_config_crud: CRUD for Apify source configurations
            apify_service: Service for interacting with Apify API
            session_factory: Factory for database sessions
            container: The DI container for resolving additional dependencies
        """
        self.apify_source_config_crud = apify_source_config_crud or apify_source_config
        self.apify_service = apify_service
        self.session_factory = session_factory
        self.container = container

    def _get_session(self) -> Session:
        """Get a database session."""
        if self.session_factory:
            return self.session_factory()
            
        # Get session factory from container as fallback
        if self.container:
            session_factory = self.container.get("session_factory")
            if session_factory:
                return session_factory()
            
        # Last resort fallback to direct import
        from local_newsifier.database.engine import get_session
        return next(get_session())

    def _get_apify_service(self) -> ApifyService:
        """Get the ApifyService.
        
        Returns:
            ApifyService: Service for interacting with Apify API
        """
        if self.apify_service:
            return self.apify_service
            
        # Get from container as fallback
        if self.container:
            try:
                return self.container.get("apify_service")
            except:
                pass
                
        # Last resort fallback to direct creation
        return ApifyService()

    def get_config(self, config_id: int) -> Optional[Dict[str, Any]]:
        """Get an Apify source configuration by ID.

        Args:
            config_id: Configuration ID

        Returns:
            Configuration data as dict if found, None otherwise
        """
        with self._get_session() as session:
            config = self.apify_source_config_crud.get(session, id=config_id)
            if not config:
                return None
            return self._format_config_dict(config)

    def get_config_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get an Apify source configuration by name.

        Args:
            name: Configuration name

        Returns:
            Configuration data as dict if found, None otherwise
        """
        with self._get_session() as session:
            config = self.apify_source_config_crud.get_by_name(session, name=name)
            if not config:
                return None
            return self._format_config_dict(config)

    def list_configs(
        self, skip: int = 0, limit: int = 100, active_only: bool = False, source_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List Apify source configurations with optional filtering.

        Args:
            skip: Number of items to skip
            limit: Maximum number of items to return
            active_only: Whether to return only active configurations
            source_type: Filter by source type

        Returns:
            List of configuration data as dicts
        """
        with self._get_session() as session:
            if source_type:
                configs = self.apify_source_config_crud.get_by_source_type(session, source_type=source_type)
                if active_only:
                    configs = [c for c in configs if c.is_active]
            elif active_only:
                configs = self.apify_source_config_crud.get_active_configs(session, skip=skip, limit=limit)
            else:
                configs = self.apify_source_config_crud.get_multi(session, skip=skip, limit=limit)
            return [self._format_config_dict(config) for config in configs]

    def create_config(
        self,
        name: str,
        actor_id: str,
        source_type: str,
        source_url: Optional[str] = None,
        schedule: Optional[str] = None,
        input_configuration: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new Apify source configuration.

        Args:
            name: Configuration name
            actor_id: Apify actor ID
            source_type: Type of source (e.g., "news", "blog", "social_media")
            source_url: Source URL (optional)
            schedule: Cron schedule expression (optional)
            input_configuration: Actor input configuration (optional)

        Returns:
            Created configuration data as dict

        Raises:
            ValueError: If configuration with the name already exists or actor_id is invalid
        """
        # Validate actor_id by checking if it exists
        try:
            apify_service = self._get_apify_service()
            actor = apify_service.get_actor_details(actor_id)
            if not actor or 'id' not in actor:
                raise ValueError(f"Invalid Apify actor ID: {actor_id}")
        except Exception as e:
            raise ValueError(f"Error validating Apify actor: {str(e)}")

        with self._get_session() as session:
            # Check if configuration already exists
            existing = self.apify_source_config_crud.get_by_name(session, name=name)
            if existing:
                raise ValueError(f"Configuration with name '{name}' already exists")
            
            # Create new configuration
            new_config = self.apify_source_config_crud.create(
                session,
                obj_in={
                    "name": name,
                    "actor_id": actor_id,
                    "source_type": source_type,
                    "source_url": source_url,
                    "schedule": schedule,
                    "input_configuration": input_configuration or {},
                    "is_active": True,
                },
            )
            
            return self._format_config_dict(new_config)

    def update_config(
        self,
        config_id: int,
        name: Optional[str] = None,
        actor_id: Optional[str] = None,
        source_type: Optional[str] = None,
        source_url: Optional[str] = None,
        schedule: Optional[str] = None,
        is_active: Optional[bool] = None,
        input_configuration: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update an Apify source configuration.

        Args:
            config_id: Configuration ID
            name: New name (optional)
            actor_id: New actor ID (optional)
            source_type: New source type (optional)
            source_url: New source URL (optional)
            schedule: New schedule expression (optional)
            is_active: New active status (optional)
            input_configuration: New input configuration (optional)

        Returns:
            Updated configuration data as dict if found, None otherwise

        Raises:
            ValueError: If new name conflicts with an existing configuration
            ValueError: If new actor_id is invalid
        """
        with self._get_session() as session:
            # Get configuration
            config = self.apify_source_config_crud.get(session, id=config_id)
            if not config:
                return None
            
            # Validate actor_id if provided
            if actor_id:
                try:
                    apify_service = self._get_apify_service()
                    actor = apify_service.get_actor_details(actor_id)
                    if not actor or 'id' not in actor:
                        raise ValueError(f"Invalid Apify actor ID: {actor_id}")
                except Exception as e:
                    raise ValueError(f"Error validating Apify actor: {str(e)}")
            
            # Prepare update data
            update_data = {}
            if name is not None:
                update_data["name"] = name
            if actor_id is not None:
                update_data["actor_id"] = actor_id
            if source_type is not None:
                update_data["source_type"] = source_type
            if source_url is not None:
                update_data["source_url"] = source_url
            if schedule is not None:
                update_data["schedule"] = schedule
            if is_active is not None:
                update_data["is_active"] = is_active
            if input_configuration is not None:
                update_data["input_configuration"] = input_configuration
            
            # If no updates, return current config
            if not update_data:
                return self._format_config_dict(config)
            
            # Update configuration
            updated = self.apify_source_config_crud.update(session, db_obj=config, obj_in=update_data)
            return self._format_config_dict(updated)

    def remove_config(self, config_id: int) -> Optional[Dict[str, Any]]:
        """Remove an Apify source configuration.

        Args:
            config_id: Configuration ID

        Returns:
            Removed configuration data as dict if found, None otherwise
        """
        with self._get_session() as session:
            # Get configuration
            config = self.apify_source_config_crud.get(session, id=config_id)
            if not config:
                return None
            
            # Remove configuration
            removed = self.apify_source_config_crud.remove(session, id=config_id)
            if not removed:
                return None
            
            return self._format_config_dict(removed)

    def run_configuration(self, config_id: int) -> Dict[str, Any]:
        """Run an Apify actor based on a configuration.

        Args:
            config_id: Configuration ID

        Returns:
            Result information including run details

        Raises:
            ValueError: If configuration not found or Apify API error
        """
        with self._get_session() as session:
            # Get configuration
            config = self.apify_source_config_crud.get(session, id=config_id)
            if not config:
                raise ValueError(f"Configuration with ID {config_id} not found")
            
            try:
                # Get ApifyService
                apify_service = self._get_apify_service()
                
                # Run the actor with the configured input
                run_result = apify_service.run_actor(
                    config.actor_id,
                    config.input_configuration
                )
                
                # Update last run timestamp
                self.apify_source_config_crud.update_last_run(
                    session,
                    config_id=config_id,
                    timestamp=datetime.now(timezone.utc)
                )
                
                # Return the result
                return {
                    "status": "success",
                    "config_id": config_id,
                    "config_name": config.name,
                    "actor_id": config.actor_id,
                    "run_id": run_result.get("id"),
                    "dataset_id": run_result.get("defaultDatasetId"),
                    "details": run_result
                }
                
            except Exception as e:
                logger.exception(f"Error running configuration {config_id}: {str(e)}")
                return {
                    "status": "error",
                    "config_id": config_id,
                    "config_name": config.name if config else "Unknown",
                    "message": str(e)
                }

    def _format_config_dict(self, config: ApifySourceConfig) -> Dict[str, Any]:
        """Format configuration as a dict.

        Args:
            config: Configuration model instance

        Returns:
            Configuration data as dict
        """
        return {
            "id": config.id,
            "name": config.name,
            "actor_id": config.actor_id,
            "source_type": config.source_type,
            "source_url": config.source_url,
            "schedule": config.schedule,
            "is_active": config.is_active,
            "input_configuration": config.input_configuration,
            "last_run_at": config.last_run_at.isoformat() if config.last_run_at else None,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat() if hasattr(config, "updated_at") else None,
        }


# Singleton instance
apify_source_config_service = ApifySourceConfigService()