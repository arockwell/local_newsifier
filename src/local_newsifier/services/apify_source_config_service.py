"""
Service for managing Apify source configurations.

This module provides a service for managing Apify source configurations, including
creating, updating, listing, and running configurations.
"""

import json
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import logging

from sqlmodel import Session

from local_newsifier.crud.apify_source_config import CRUDApifySourceConfig 
from local_newsifier.models.apify import ApifySourceConfig
from local_newsifier.errors.error import ServiceError, handle_service_error

logger = logging.getLogger(__name__)

class ApifySourceConfigService:
    """Service for managing Apify source configurations."""
    
    def __init__(
        self, 
        apify_source_config_crud: CRUDApifySourceConfig,
        apify_service,  # ApifyService, but avoiding circular imports
        session_factory,
    ):
        """Initialize the service.
        
        Args:
            apify_source_config_crud: CRUD for Apify source configurations
            apify_service: Service for interacting with Apify API
            session_factory: Function that returns a database session
        """
        self.apify_source_config_crud = apify_source_config_crud
        self.apify_service = apify_service
        self.session_factory = session_factory
    
    @handle_service_error(service="apify")
    def list_configs(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        active_only: bool = False,
        source_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List Apify source configurations with optional filtering.
        
        Args:
            skip: Number of items to skip
            limit: Maximum number of items to return
            active_only: If True, only return active configurations
            source_type: Optional source type to filter by
            
        Returns:
            List of configuration dictionaries
        """
        with self.session_factory() as session:
            # Apply filters
            if active_only:
                configs = self.apify_source_config_crud.get_active_configs(
                    session, skip=skip, limit=limit
                )
            elif source_type:
                configs = self.apify_source_config_crud.get_by_source_type(
                    session, source_type=source_type
                )
                # Apply skip and limit manually since the method doesn't support it
                configs = configs[skip:skip+limit]
            else:
                configs = self.apify_source_config_crud.get_multi(
                    session, skip=skip, limit=limit
                )
            
            # Convert to dictionaries
            return [config.model_dump() for config in configs]
    
    @handle_service_error(service="apify")
    def get_config(self, config_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific Apify source configuration.
        
        Args:
            config_id: Configuration ID
            
        Returns:
            Configuration dictionary or None if not found
        """
        with self.session_factory() as session:
            config = self.apify_source_config_crud.get(session, id=config_id)
            if not config:
                return None
            return config.model_dump()
    
    @handle_service_error(service="apify")
    def create_config(
        self,
        name: str,
        actor_id: str,
        source_type: str,
        source_url: Optional[str] = None,
        schedule: Optional[str] = None,
        input_configuration: Optional[Dict[str, Any]] = None,
        is_active: bool = True
    ) -> Dict[str, Any]:
        """Create a new Apify source configuration.
        
        Args:
            name: Configuration name
            actor_id: Apify actor ID
            source_type: Type of source (e.g., "news", "blog")
            source_url: Optional source URL
            schedule: Optional cron schedule expression
            input_configuration: Optional actor input parameters
            is_active: Whether the configuration is active
            
        Returns:
            Created configuration as a dictionary
            
        Raises:
            ServiceError: If a configuration with the same name already exists
        """
        # Prepare configuration data
        config_data = {
            "name": name,
            "actor_id": actor_id,
            "source_type": source_type,
            "is_active": is_active,
            "input_configuration": input_configuration or {}
        }
        
        if source_url:
            config_data["source_url"] = source_url
            
        if schedule:
            config_data["schedule"] = schedule
        
        # Create in database
        with self.session_factory() as session:
            try:
                config = self.apify_source_config_crud.create(
                    session, obj_in=config_data
                )
                return config.model_dump()
            except ServiceError as e:
                # Re-raise ServiceError
                raise e
            except Exception as e:
                raise ServiceError(
                    service="apify",
                    error_type="database",
                    message=f"Error creating Apify source configuration: {str(e)}",
                    context={"name": name, "actor_id": actor_id}
                )
    
    @handle_service_error(service="apify")
    def update_config(
        self,
        config_id: int,
        name: Optional[str] = None,
        actor_id: Optional[str] = None,
        source_type: Optional[str] = None,
        source_url: Optional[str] = None,
        schedule: Optional[str] = None,
        input_configuration: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        """Update an existing Apify source configuration.
        
        Args:
            config_id: Configuration ID
            name: New configuration name
            actor_id: New actor ID
            source_type: New source type
            source_url: New source URL
            schedule: New schedule expression
            input_configuration: New actor input parameters
            is_active: New active status
            
        Returns:
            Updated configuration as a dictionary, or None if not found
            
        Raises:
            ServiceError: If a configuration with the new name already exists
        """
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
        if input_configuration is not None:
            update_data["input_configuration"] = input_configuration
        if is_active is not None:
            update_data["is_active"] = is_active
        
        # Update in database
        with self.session_factory() as session:
            # Get existing config
            db_config = self.apify_source_config_crud.get(session, id=config_id)
            if not db_config:
                return None
            
            # Update the config
            try:
                updated_config = self.apify_source_config_crud.update(
                    session, db_obj=db_config, obj_in=update_data
                )
                return updated_config.model_dump()
            except ServiceError as e:
                # Re-raise ServiceError
                raise e
            except Exception as e:
                raise ServiceError(
                    service="apify",
                    error_type="database",
                    message=f"Error updating Apify source configuration: {str(e)}",
                    context={"config_id": config_id}
                )
    
    @handle_service_error(service="apify")
    def remove_config(self, config_id: int) -> bool:
        """Remove an Apify source configuration.
        
        Args:
            config_id: Configuration ID
            
        Returns:
            True if successful, False otherwise
        """
        with self.session_factory() as session:
            try:
                # Attempt to delete the schedule in Apify if it exists
                config = self.apify_source_config_crud.get(session, id=config_id)
                if config and config.schedule_id:
                    try:
                        self.apify_service.delete_schedule(config.schedule_id)
                    except Exception as e:
                        logger.warning(
                            f"Failed to delete Apify schedule {config.schedule_id}: {str(e)}"
                        )
                
                # Remove from database
                result = self.apify_source_config_crud.remove(session, id=config_id)
                return result is not None
            except Exception as e:
                raise ServiceError(
                    service="apify",
                    error_type="database",
                    message=f"Error removing Apify source configuration: {str(e)}",
                    context={"config_id": config_id}
                )
    
    @handle_service_error(service="apify")
    def toggle_active(self, config_id: int, is_active: bool) -> Optional[Dict[str, Any]]:
        """Toggle the active status of a configuration.
        
        Args:
            config_id: Configuration ID
            is_active: New active status
            
        Returns:
            Updated configuration as a dictionary, or None if not found
        """
        with self.session_factory() as session:
            updated_config = self.apify_source_config_crud.toggle_active(
                session, config_id=config_id, is_active=is_active
            )
            if not updated_config:
                return None
            return updated_config.model_dump()
    
    @handle_service_error(service="apify")
    def run_configuration(self, config_id: int) -> Dict[str, Any]:
        """Run an Apify actor based on a source configuration.
        
        Args:
            config_id: Configuration ID
            
        Returns:
            Dictionary with run results
            
        Raises:
            ServiceError: If the configuration is not found or actor run fails
        """
        with self.session_factory() as session:
            # Get the configuration
            config = self.apify_source_config_crud.get(session, id=config_id)
            if not config:
                raise ServiceError(
                    service="apify",
                    error_type="not_found",
                    message=f"Configuration with ID {config_id} not found",
                    context={"config_id": config_id}
                )
            
            if not config.is_active:
                raise ServiceError(
                    service="apify",
                    error_type="validation",
                    message=f"Configuration '{config.name}' is not active",
                    context={"config_id": config_id, "name": config.name}
                )
            
            # Run the actor
            try:
                # Update last run timestamp
                self.apify_source_config_crud.update_last_run(
                    session, config_id=config_id
                )
                
                # Run the actor
                result = self.apify_service.run_actor(
                    actor_id=config.actor_id,
                    run_input=config.input_configuration
                )
                
                # Process result
                run_id = result.get("id")
                dataset_id = result.get("defaultDatasetId")
                
                # Create success response
                return {
                    "status": "success",
                    "config_id": config_id,
                    "config_name": config.name,
                    "actor_id": config.actor_id,
                    "run_id": run_id,
                    "dataset_id": dataset_id
                }
            
            except Exception as e:
                # Handle failure
                raise ServiceError(
                    service="apify",
                    error_type="execution",
                    message=f"Error running Apify actor: {str(e)}",
                    context={
                        "config_id": config_id,
                        "name": config.name,
                        "actor_id": config.actor_id
                    }
                )
    
    @handle_service_error(service="apify")
    def get_scheduled_configs(self, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """Get all configurations with a schedule.
        
        Args:
            enabled_only: If True, only return active configurations
            
        Returns:
            List of configuration dictionaries
        """
        with self.session_factory() as session:
            configs = self.apify_source_config_crud.get_scheduled_configs(
                session, enabled_only=enabled_only
            )
            return [config.model_dump() for config in configs]