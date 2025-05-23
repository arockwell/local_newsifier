"""Tests for database performance monitoring."""

import time
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import Pool

from local_newsifier.monitoring.database import (_after_cursor_execute, _before_cursor_execute,
                                                 _handle_db_error, _on_checkin, _on_checkout,
                                                 _on_connect, _parse_sql_statement,
                                                 _query_start_times, _update_pool_metrics,
                                                 setup_database_monitoring)


class TestDatabaseMonitoring:
    """Test database monitoring functionality."""

    @patch("local_newsifier.monitoring.database.event")
    @patch("local_newsifier.monitoring.database._update_pool_metrics")
    @patch("local_newsifier.monitoring.database.logger")
    def test_setup_database_monitoring(self, mock_logger, mock_update_pool, mock_event):
        """Test setting up database monitoring listeners."""
        mock_engine = MagicMock()

        setup_database_monitoring(mock_engine)

        # Verify event listeners are registered
        # Should be 5 or 6 depending on SQLAlchemy version
        assert mock_event.listen.call_count in [5, 6, 7]  # Different event types

        # Verify specific event registrations
        event_calls = mock_event.listen.call_args_list
        registered_events = [(call[0][0], call[0][1]) for call in event_calls]

        assert (Engine, "before_cursor_execute") in registered_events
        assert (Engine, "after_cursor_execute") in registered_events
        assert (Pool, "connect") in registered_events
        assert (Pool, "checkout") in registered_events
        assert (Pool, "checkin") in registered_events

        # Verify pool metrics are initialized
        mock_update_pool.assert_called_once_with(mock_engine)

        # Verify logging
        mock_logger.info.assert_called_with("Setting up database performance monitoring")

    def test_before_cursor_execute(self):
        """Test recording query start time."""
        mock_cursor = MagicMock()
        cursor_id = id(mock_cursor)

        # Clear any existing entries
        _query_start_times.clear()

        _before_cursor_execute(
            conn=MagicMock(),
            cursor=mock_cursor,
            statement="SELECT * FROM users",
            parameters=None,
            context=None,
            executemany=False,
        )

        # Verify start time is recorded
        assert cursor_id in _query_start_times
        assert isinstance(_query_start_times[cursor_id], float)
        assert _query_start_times[cursor_id] > 0

    @patch("local_newsifier.monitoring.database.db_query_duration")
    @patch("local_newsifier.monitoring.database.db_query_total")
    def test_after_cursor_execute_success(self, mock_total, mock_duration):
        """Test recording query completion metrics."""
        mock_cursor = MagicMock()
        cursor_id = id(mock_cursor)

        # Set up start time
        _query_start_times[cursor_id] = time.time() - 0.1  # 100ms ago

        _after_cursor_execute(
            conn=MagicMock(),
            cursor=mock_cursor,
            statement="SELECT id, name FROM users WHERE active = true",
            parameters=None,
            context=None,
            executemany=False,
        )

        # Verify metrics are recorded
        mock_duration.labels.assert_called_with(operation="select", table="users")
        mock_total.labels.assert_called_with(operation="select", table="users")

        # Verify duration is observed
        observe_mock = mock_duration.labels.return_value.observe
        assert observe_mock.called
        duration = observe_mock.call_args[0][0]
        assert 0.09 < duration < 0.15  # Allow some variance

        # Verify counter is incremented
        mock_total.labels.return_value.inc.assert_called_once()

        # Verify start time is cleaned up
        assert cursor_id not in _query_start_times

    @patch("local_newsifier.monitoring.database.logger")
    @patch("local_newsifier.monitoring.database.db_query_duration")
    def test_after_cursor_execute_slow_query(self, mock_duration, mock_logger):
        """Test that slow queries are logged."""
        mock_cursor = MagicMock()
        cursor_id = id(mock_cursor)

        # Set up start time for a slow query (>1 second)
        _query_start_times[cursor_id] = time.time() - 1.5

        _after_cursor_execute(
            conn=MagicMock(),
            cursor=mock_cursor,
            statement="SELECT * FROM large_table",
            parameters=None,
            context=None,
            executemany=False,
        )

        # Verify warning is logged
        mock_logger.warning.assert_called()
        warning_call = str(mock_logger.warning.call_args)
        assert "Slow query detected" in warning_call
        assert "select on large_table" in warning_call

        # Verify debug log with SQL
        mock_logger.debug.assert_called()
        debug_call = str(mock_logger.debug.call_args)
        assert "SELECT * FROM large_table" in debug_call

    def test_parse_sql_statement_select(self):
        """Test parsing SELECT statements."""
        cases = [
            ("SELECT * FROM users", ("select", "users")),
            ("SELECT id FROM articles WHERE status = 'published'", ("select", "articles")),
            ('SELECT * FROM "public"."posts"', ("select", "posts")),
            ("SELECT u.* FROM users u JOIN roles r", ("select", "users")),
        ]

        for sql, expected in cases:
            assert _parse_sql_statement(sql) == expected

    def test_parse_sql_statement_insert(self):
        """Test parsing INSERT statements."""
        cases = [
            ("INSERT INTO users (name) VALUES ('test')", ("insert", "users")),
            ('INSERT INTO "articles" VALUES (1, 2, 3)', ("insert", "articles")),
        ]

        for sql, expected in cases:
            assert _parse_sql_statement(sql) == expected

    def test_parse_sql_statement_update(self):
        """Test parsing UPDATE statements."""
        cases = [
            ("UPDATE users SET active = false", ("update", "users")),
            ('UPDATE "posts" SET views = views + 1', ("update", "posts")),
        ]

        for sql, expected in cases:
            assert _parse_sql_statement(sql) == expected

    def test_parse_sql_statement_delete(self):
        """Test parsing DELETE statements."""
        cases = [
            ("DELETE FROM users WHERE id = 1", ("delete", "users")),
            ("DELETE FROM articles", ("delete", "articles")),
        ]

        for sql, expected in cases:
            assert _parse_sql_statement(sql) == expected

    def test_parse_sql_statement_other(self):
        """Test parsing other SQL statements."""
        cases = [
            ("CREATE TABLE test (id INT)", ("create", "test")),
            ("DROP TABLE old_data", ("drop", "old_data")),
            ("ALTER TABLE users ADD COLUMN email", ("alter", "users")),
            ("BEGIN", ("other", "unknown")),
        ]

        for sql, expected in cases:
            assert _parse_sql_statement(sql) == expected

    @patch("local_newsifier.monitoring.database.db_active_connections")
    def test_on_checkout(self, mock_active):
        """Test connection checkout tracking."""
        _on_checkout(
            dbapi_conn=MagicMock(), connection_record=MagicMock(), connection_proxy=MagicMock()
        )

        mock_active.inc.assert_called_once()

    @patch("local_newsifier.monitoring.database.db_active_connections")
    def test_on_checkin(self, mock_active):
        """Test connection checkin tracking."""
        _on_checkin(dbapi_conn=MagicMock(), connection_record=MagicMock())

        mock_active.dec.assert_called_once()

    @patch("local_newsifier.monitoring.database.logger")
    def test_on_connect(self, mock_logger):
        """Test new connection logging."""
        _on_connect(dbapi_conn=MagicMock(), connection_record=MagicMock())

        mock_logger.debug.assert_called_with("New database connection established")

    @patch("local_newsifier.monitoring.database.errors_total")
    @patch("local_newsifier.monitoring.database.logger")
    def test_handle_db_error(self, mock_logger, mock_errors):
        """Test database error handling."""
        mock_exception = ValueError("Database error")
        mock_context = MagicMock()
        mock_context.original_exception = mock_exception

        _handle_db_error(mock_context)

        # Verify error counter
        mock_errors.labels.assert_called_with(component="database", error_type="ValueError")
        mock_errors.labels.return_value.inc.assert_called_once()

        # Verify error logging
        mock_logger.error.assert_called()
        error_call = str(mock_logger.error.call_args)
        assert "Database error: ValueError" in error_call

    @patch("local_newsifier.monitoring.database.db_connection_pool_size")
    def test_update_pool_metrics(self, mock_pool_size):
        """Test updating connection pool metrics."""
        # Test with pool that has size() method
        mock_pool = MagicMock()
        mock_pool.size.return_value = 10
        mock_engine = MagicMock()
        mock_engine.pool = mock_pool

        _update_pool_metrics(mock_engine)

        mock_pool_size.set.assert_called_with(10)

    @patch("local_newsifier.monitoring.database.db_connection_pool_size")
    def test_update_pool_metrics_with_pool_attribute(self, mock_pool_size):
        """Test updating pool metrics with _pool attribute."""
        # Test with pool that has _pool attribute
        mock_pool = MagicMock(spec=[])
        mock_pool._pool = [1, 2, 3, 4, 5]  # 5 connections
        mock_engine = MagicMock()
        mock_engine.pool = mock_pool

        _update_pool_metrics(mock_engine)

        mock_pool_size.set.assert_called_with(5)

    @patch("local_newsifier.monitoring.database.logger")
    def test_update_pool_metrics_error(self, mock_logger):
        """Test pool metrics update handles errors gracefully."""
        mock_engine = MagicMock()
        # Create a mock that will raise AttributeError when accessed
        mock_pool = MagicMock()
        mock_pool.size.side_effect = AttributeError("No size method")
        mock_engine.pool = mock_pool

        _update_pool_metrics(mock_engine)

        # Should log error but not raise
        mock_logger.error.assert_called()
        error_call = str(mock_logger.error.call_args)
        assert "Error updating pool metrics" in error_call
