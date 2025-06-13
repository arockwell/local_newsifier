"""CRUD operations for Apify source configurations."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from sqlmodel import Session, select

from local_newsifier.crud.base import CRUDBase
from local_newsifier.errors.error import ServiceError, handle_service_error
from local_newsifier.models.apify import ApifySourceConfig


class CRUDApifySourceConfig(CRUDBase[ApifySourceConfig]):
    """CRUD operations for Apify source configurations."""

    @handle_service_error(service="apify")
    def get_by_name(self, db: Session, *, name: str) -> Optional[ApifySourceConfig]:
        """Get a source configuration by name.

        Args:
            db: Database session
            name: Name of the configuration to find

        Returns:
            Source configuration if found, None otherwise
        """
        return db.exec(select(ApifySourceConfig).where(ApifySourceConfig.name == name)).first()

    @handle_service_error(service="apify")
    def get_by_actor_id(self, db: Session, *, actor_id: str) -> List[ApifySourceConfig]:
        """Get all source configurations for a specific actor.

        Args:
            db: Database session
            actor_id: Apify actor ID

        Returns:
            List of source configurations using this actor
        """
        return db.exec(
            select(ApifySourceConfig).where(ApifySourceConfig.actor_id == actor_id)
        ).all()

    @handle_service_error(service="apify")
    def get_active_configs(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ApifySourceConfig]:
        """Get all active source configurations.

        Args:
            db: Database session
            skip: Number of items to skip
            limit: Maximum number of items to return

        Returns:
            List of active source configurations
        """
        return db.exec(
            select(ApifySourceConfig)
            .where(ApifySourceConfig.is_active == True)
            .offset(skip)
            .limit(limit)
        ).all()

    @handle_service_error(service="apify")
    def get_by_source_type(self, db: Session, *, source_type: str) -> List[ApifySourceConfig]:
        """Get all source configurations of a specific type.

        Args:
            db: Database session
            source_type: Type of source (e.g., "news", "blog", "social_media")

        Returns:
            List of configurations of the specified type
        """
        return db.exec(
            select(ApifySourceConfig).where(ApifySourceConfig.source_type == source_type)
        ).all()

    @handle_service_error(service="apify")
    def get_scheduled_configs(
        self, db: Session, enabled_only: bool = True
    ) -> List[ApifySourceConfig]:
        """Get all configurations with a schedule.

        Args:
            db: Database session
            enabled_only: If True, only return active configs

        Returns:
            List of configurations with a schedule
        """
        query = select(ApifySourceConfig).where(ApifySourceConfig.schedule != None)

        if enabled_only:
            query = query.where(ApifySourceConfig.is_active == True)

        return db.exec(query).all()

    @handle_service_error(service="apify")
    def get_configs_with_schedule_ids(self, db: Session) -> List[ApifySourceConfig]:
        """Get all configurations that have Apify schedule IDs.

        Args:
            db: Database session

        Returns:
            List of configurations with schedule IDs
        """
        return db.exec(select(ApifySourceConfig).where(ApifySourceConfig.schedule_id != None)).all()

    @handle_service_error(service="apify")
    def update_schedule_id(
        self, db: Session, config_id: int, schedule_id: Optional[str]
    ) -> Optional[ApifySourceConfig]:
        """Update the schedule_id field for a configuration.

        Args:
            db: Database session
            config_id: Configuration ID
            schedule_id: New schedule ID or None to clear

        Returns:
            Updated configuration if found, None otherwise
        """
        config = self.get(db, id=config_id)
        if config:
            config.schedule_id = schedule_id
            db.add(config)
            db.commit()
            db.refresh(config)
            return config
        return None

    @handle_service_error(service="apify")
    def create(
        self, db: Session, *, obj_in: Union[Dict[str, Any], ApifySourceConfig]
    ) -> ApifySourceConfig:
        """Create a new source configuration.

        Args:
            db: Database session
            obj_in: Configuration data

        Returns:
            Created configuration

        Raises:
            ServiceError: If a configuration with the same name already exists
        """
        # Handle dict or model instance
        if isinstance(obj_in, dict):
            config_data = obj_in
            name = config_data.get("name")
        else:
            config_data = obj_in.model_dump(exclude_unset=True)
            name = obj_in.name

        # Check if configuration with this name already exists
        existing = self.get_by_name(db, name=name)
        if existing:
            raise ServiceError(
                service="apify",
                error_type="validation",
                message=f"Source configuration with name '{name}' already exists",
                context={"name": name},
            )

        db_config = ApifySourceConfig(**config_data)
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
        return db_config

    @handle_service_error(service="apify")
    def update(
        self,
        db: Session,
        *,
        db_obj: ApifySourceConfig,
        obj_in: Union[Dict[str, Any], ApifySourceConfig],
    ) -> ApifySourceConfig:
        """Update a source configuration.

        Args:
            db: Database session
            db_obj: Existing configuration to update
            obj_in: New configuration data

        Returns:
            Updated configuration
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        # If name is being changed, check for conflicts
        if "name" in update_data and update_data["name"] != db_obj.name:
            existing = self.get_by_name(db, name=update_data["name"])
            if existing and existing.id != db_obj.id:
                raise ServiceError(
                    service="apify",
                    error_type="validation",
                    message=f"Source configuration with name '{update_data['name']}' already exists",
                    context={"name": update_data["name"]},
                )

        # Update the object
        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @handle_service_error(service="apify")
    def update_last_run(
        self, db: Session, *, config_id: int, timestamp: Optional[datetime] = None
    ) -> Optional[ApifySourceConfig]:
        """Update the last_run_at timestamp for a configuration.

        Args:
            db: Database session
            config_id: Configuration ID
            timestamp: Timestamp to set (defaults to now)

        Returns:
            Updated configuration if found, None otherwise
        """
        config = self.get(db, id=config_id)
        if config:
            # Ensure timestamp has timezone info if provided
            actual_timestamp = timestamp or datetime.now(timezone.utc)
            if timestamp and timestamp.tzinfo is None:
                actual_timestamp = timestamp.replace(tzinfo=timezone.utc)

            config.last_run_at = actual_timestamp
            db.add(config)
            db.commit()
            db.refresh(config)
            return config
        return None

    @handle_service_error(service="apify")
    def toggle_active(
        self, db: Session, *, config_id: int, is_active: bool
    ) -> Optional[ApifySourceConfig]:
        """Toggle the active status of a configuration.

        Args:
            db: Database session
            config_id: Configuration ID
            is_active: New active status

        Returns:
            Updated configuration if found, None otherwise
        """
        config = self.get(db, id=config_id)
        if config:
            config.is_active = is_active
            db.add(config)
            db.commit()
            db.refresh(config)
            return config
        return None

    @handle_service_error(service="apify")
    def remove(self, db: Session, *, id: int) -> Optional[ApifySourceConfig]:
        """Remove a source configuration.

        This overrides the base implementation to handle relationships.

        Args:
            db: Database session
            id: Configuration ID

        Returns:
            Removed configuration if found, None otherwise
        """
        db_obj = db.exec(select(ApifySourceConfig).where(ApifySourceConfig.id == id)).first()
        if db_obj:
            # This will rely on SQLModel/SQLAlchemy cascade settings
            db.delete(db_obj)
            db.commit()
            return db_obj
        return None


# Create a singleton instance
apify_source_config = CRUDApifySourceConfig(ApifySourceConfig)
