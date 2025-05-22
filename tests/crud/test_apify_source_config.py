"""Tests for ApifySourceConfig CRUD operations."""

import pytest
from datetime import datetime, timezone, timedelta
from sqlmodel import Session

from local_newsifier.crud.apify_source_config import apify_source_config
from local_newsifier.models.apify import ApifySourceConfig
from local_newsifier.errors.error import ServiceError


class TestApifySourceConfigCRUD:
    """Test ApifySourceConfig CRUD operations."""

    def test_create(self, db_session: Session, sample_apify_source_config_data):
        """Test creating a source configuration."""
        # Create the config
        created = apify_source_config.create(db_session, obj_in=sample_apify_source_config_data)

        # Verify
        assert created.id is not None
        assert created.name == sample_apify_source_config_data["name"]
        assert created.actor_id == sample_apify_source_config_data["actor_id"]
        assert created.is_active is True
        assert created.schedule == sample_apify_source_config_data["schedule"]
        assert created.source_type == sample_apify_source_config_data["source_type"]
        assert created.source_url == sample_apify_source_config_data["source_url"]
        assert created.input_configuration == sample_apify_source_config_data["input_configuration"]

    def test_create_duplicate_name(self, db_session: Session, sample_apify_source_config_data):
        """Test creating a source configuration with a duplicate name."""
        # Create the first config
        apify_source_config.create(db_session, obj_in=sample_apify_source_config_data)

        # Try to create another with the same name
        with pytest.raises(ServiceError) as excinfo:
            apify_source_config.create(db_session, obj_in=sample_apify_source_config_data)

        # Verify the error
        error = excinfo.value
        assert error.service == "apify"
        assert error.error_type == "validation"
        assert (
            f"Source configuration with name '{sample_apify_source_config_data['name']}' already exists"
            in str(error)
        )

    def test_get(self, db_session: Session, sample_apify_source_config_data):
        """Test getting a source configuration by ID."""
        # Create the config
        created = apify_source_config.create(db_session, obj_in=sample_apify_source_config_data)

        # Get by ID
        fetched = apify_source_config.get(db_session, id=created.id)

        # Verify
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == created.name

    def test_get_by_name(self, db_session: Session, sample_apify_source_config_data):
        """Test getting a source configuration by name."""
        # Create the config
        created = apify_source_config.create(db_session, obj_in=sample_apify_source_config_data)

        # Get by name
        fetched = apify_source_config.get_by_name(db_session, name=created.name)

        # Verify
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == created.name

    def test_get_by_actor_id(self, db_session: Session, sample_apify_source_config_data):
        """Test getting source configurations by actor ID."""
        # Create the first config
        created1 = apify_source_config.create(db_session, obj_in=sample_apify_source_config_data)

        # Create another config with the same actor ID
        config_data2 = sample_apify_source_config_data.copy()
        config_data2["name"] = "Another Test Source"
        created2 = apify_source_config.create(db_session, obj_in=config_data2)

        # Get by actor ID
        fetched = apify_source_config.get_by_actor_id(db_session, actor_id=created1.actor_id)

        # Verify
        assert len(fetched) == 2
        assert created1.id in [f.id for f in fetched]
        assert created2.id in [f.id for f in fetched]

    def test_get_active_configs(self, db_session: Session, sample_apify_source_config_data):
        """Test getting active configurations."""
        # Create an active config
        active_config = apify_source_config.create(
            db_session, obj_in=sample_apify_source_config_data
        )

        # Create an inactive config
        inactive_data = sample_apify_source_config_data.copy()
        inactive_data["name"] = "Inactive Source"
        inactive_data["is_active"] = False
        inactive_config = apify_source_config.create(db_session, obj_in=inactive_data)

        # Get active configs
        active_configs = apify_source_config.get_active_configs(db_session)

        # Verify
        assert len(active_configs) == 1
        assert active_configs[0].id == active_config.id
        assert inactive_config.id not in [c.id for c in active_configs]

    def test_get_by_source_type(self, db_session: Session, sample_apify_source_config_data):
        """Test getting configurations by source type."""
        # Create a news source
        news_config = apify_source_config.create(db_session, obj_in=sample_apify_source_config_data)

        # Create a blog source
        blog_data = sample_apify_source_config_data.copy()
        blog_data["name"] = "Blog Source"
        blog_data["source_type"] = "blog"
        blog_config = apify_source_config.create(db_session, obj_in=blog_data)

        # Get news sources
        news_sources = apify_source_config.get_by_source_type(db_session, source_type="news")

        # Get blog sources
        blog_sources = apify_source_config.get_by_source_type(db_session, source_type="blog")

        # Verify
        assert len(news_sources) == 1
        assert news_sources[0].id == news_config.id

        assert len(blog_sources) == 1
        assert blog_sources[0].id == blog_config.id

    def test_get_scheduled_configs(self, db_session: Session, sample_apify_source_config_data):
        """Test getting scheduled configurations."""
        # Create a scheduled config
        scheduled_config = apify_source_config.create(
            db_session, obj_in=sample_apify_source_config_data
        )

        # Create an unscheduled config
        unscheduled_data = sample_apify_source_config_data.copy()
        unscheduled_data["name"] = "Unscheduled Source"
        unscheduled_data["schedule"] = None
        unscheduled_config = apify_source_config.create(db_session, obj_in=unscheduled_data)

        # Get scheduled configs
        scheduled_configs = apify_source_config.get_scheduled_configs(db_session)

        # Verify
        assert len(scheduled_configs) == 1
        assert scheduled_configs[0].id == scheduled_config.id
        assert unscheduled_config.id not in [c.id for c in scheduled_configs]

    def test_update(self, db_session: Session, sample_apify_source_config_data):
        """Test updating a source configuration."""
        # Create the config
        created = apify_source_config.create(db_session, obj_in=sample_apify_source_config_data)

        # Update data
        update_data = {
            "name": "Updated Source",
            "schedule": "0 0 * * *",  # Run daily
            "input_configuration": {
                "startUrls": [{"url": "https://example.com/updated"}],
                "maxPagesPerCrawl": 20,
            },
        }

        # Update the config
        updated = apify_source_config.update(db_session, db_obj=created, obj_in=update_data)

        # Verify
        assert updated.id == created.id
        assert updated.name == update_data["name"]
        assert updated.schedule == update_data["schedule"]
        assert updated.input_configuration == update_data["input_configuration"]
        # These weren't updated
        assert updated.actor_id == sample_apify_source_config_data["actor_id"]
        assert updated.source_type == sample_apify_source_config_data["source_type"]

    def test_update_duplicate_name(self, db_session: Session, sample_apify_source_config_data):
        """Test updating a source configuration with a duplicate name."""
        # Create the first config
        first_config = apify_source_config.create(
            db_session, obj_in=sample_apify_source_config_data
        )

        # Create another config
        second_data = sample_apify_source_config_data.copy()
        second_data["name"] = "Second Source"
        second_config = apify_source_config.create(db_session, obj_in=second_data)

        # Try to update second config with the first config's name
        with pytest.raises(ServiceError) as excinfo:
            apify_source_config.update(
                db_session, db_obj=second_config, obj_in={"name": first_config.name}
            )

        # Verify the error
        error = excinfo.value
        assert error.service == "apify"
        assert error.error_type == "validation"
        assert f"Source configuration with name '{first_config.name}' already exists" in str(error)

    def test_update_last_run(self, db_session: Session, sample_apify_source_config_data):
        """Test updating the last_run_at timestamp."""
        # Create the config
        created = apify_source_config.create(db_session, obj_in=sample_apify_source_config_data)
        assert created.last_run_at is None

        # Update with a simple date/time for comparison since SQLModel might not preserve timezone info
        now = datetime.now()
        specific_date = datetime(now.year, now.month, now.day, 15, 30, 0)  # 3:30 PM today

        updated = apify_source_config.update_last_run(
            db_session, config_id=created.id, timestamp=specific_date
        )

        # Verify basic update worked
        assert updated is not None
        assert updated.id == created.id
        assert updated.last_run_at is not None

        # Verify the time components match even if timezone info is lost
        assert updated.last_run_at.hour == specific_date.hour
        assert updated.last_run_at.minute == specific_date.minute
        assert updated.last_run_at.second == specific_date.second

        # Manually check it was updated in the database by fetching fresh
        fetched = apify_source_config.get(db_session, id=created.id)
        assert fetched.last_run_at is not None

    def test_toggle_active(self, db_session: Session, sample_apify_source_config_data):
        """Test toggling the active status of a configuration."""
        # Create an active config
        created = apify_source_config.create(db_session, obj_in=sample_apify_source_config_data)
        assert created.is_active is True

        # Deactivate it
        deactivated = apify_source_config.toggle_active(
            db_session, config_id=created.id, is_active=False
        )

        # Verify
        assert deactivated is not None
        assert deactivated.id == created.id
        assert deactivated.is_active is False

        # Activate it again
        activated = apify_source_config.toggle_active(
            db_session, config_id=created.id, is_active=True
        )

        # Verify
        assert activated is not None
        assert activated.id == created.id
        assert activated.is_active is True

    def test_remove(self, db_session: Session, sample_apify_source_config_data):
        """Test removing a source configuration."""
        # Create the config
        created = apify_source_config.create(db_session, obj_in=sample_apify_source_config_data)

        # Remove it
        removed = apify_source_config.remove(db_session, id=created.id)

        # Verify
        assert removed is not None
        assert removed.id == created.id

        # Verify it's gone
        not_found = apify_source_config.get(db_session, id=created.id)
        assert not_found is None

    def test_methods_with_nonexistent_id(self, db_session: Session):
        """Test methods with a non-existent ID."""
        # Try to get a non-existent config
        not_found = apify_source_config.get(db_session, id=999)
        assert not_found is None

        # Try to update last_run
        not_updated = apify_source_config.update_last_run(db_session, config_id=999)
        assert not_updated is None

        # Try to toggle active
        not_toggled = apify_source_config.toggle_active(db_session, config_id=999, is_active=True)
        assert not_toggled is None

        # Try to remove
        not_removed = apify_source_config.remove(db_session, id=999)
        assert not_removed is None
