"""Tests for performance monitoring decorators."""

import time
from unittest.mock import MagicMock, patch

import pytest

from local_newsifier.monitoring.decorators import (monitor_article_processing,
                                                   monitor_database_operation,
                                                   monitor_entity_extraction, monitor_performance,
                                                   monitor_rss_feed_fetch)


class TestMonitoringDecorators:
    """Test monitoring decorator functionality."""

    @patch("local_newsifier.monitoring.decorators.logger")
    def test_monitor_performance_success(self, mock_logger):
        """Test generic performance monitoring decorator with successful execution."""

        @monitor_performance(metric_name="test_operation")
        def test_function(x, y):
            return x + y

        result = test_function(1, 2)

        assert result == 3

        # Verify debug logging
        debug_calls = [call for call in mock_logger.debug.call_args_list]
        assert any("test_operation completed" in str(call) for call in debug_calls)
        assert any("success" in str(call) for call in debug_calls)

    @patch("local_newsifier.monitoring.decorators.logger")
    @patch("local_newsifier.monitoring.decorators.errors_total")
    def test_monitor_performance_error(self, mock_errors, mock_logger):
        """Test generic performance monitoring decorator with error."""

        @monitor_performance(metric_name="failing_operation")
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            failing_function()

        # Verify error tracking
        mock_errors.labels.assert_called_with(
            component="failing_operation", error_type="ValueError"
        )
        mock_errors.labels.return_value.inc.assert_called_once()

        # Verify error logging
        mock_logger.error.assert_called()
        error_call = str(mock_logger.error.call_args)
        assert "failing_operation" in error_call
        assert "ValueError" in error_call

    @patch("local_newsifier.monitoring.decorators.logger")
    def test_monitor_performance_slow_operation(self, mock_logger):
        """Test that slow operations are logged as warnings."""

        @monitor_performance()
        def slow_function():
            time.sleep(1.1)
            return "done"

        result = slow_function()

        assert result == "done"

        # Verify slow operation warning
        mock_logger.warning.assert_called()
        warning_call = str(mock_logger.warning.call_args)
        assert "Slow operation" in warning_call
        assert "slow_function" in warning_call

    @patch("local_newsifier.monitoring.decorators.article_processing_duration")
    @patch("local_newsifier.monitoring.decorators.logger")
    def test_monitor_article_processing_success(self, mock_logger, mock_duration):
        """Test article processing monitoring decorator."""

        @monitor_article_processing
        def process_article():
            return {"status": "processed"}

        result = process_article()

        assert result == {"status": "processed"}

        # Verify metric observation
        mock_duration.observe.assert_called_once()
        duration_arg = mock_duration.observe.call_args[0][0]
        assert isinstance(duration_arg, float)
        assert duration_arg >= 0  # Duration could be very small

        # Verify logging
        mock_logger.info.assert_called()
        info_call = str(mock_logger.info.call_args)
        assert "Article processing completed" in info_call

    @patch("local_newsifier.monitoring.decorators.entity_extraction_duration")
    @patch("local_newsifier.monitoring.decorators.logger")
    def test_monitor_entity_extraction_with_list_result(self, mock_logger, mock_duration):
        """Test entity extraction monitoring with list result."""

        @monitor_entity_extraction(source="test_extractor")
        def extract_entities():
            return ["entity1", "entity2", "entity3"]

        result = extract_entities()

        assert result == ["entity1", "entity2", "entity3"]

        # Verify metric observation with correct label
        mock_duration.labels.assert_called_with(source="test_extractor")
        mock_duration.labels.return_value.observe.assert_called_once()

        # Verify logging includes entity count
        mock_logger.info.assert_called()
        info_call = str(mock_logger.info.call_args)
        assert "found 3 entities" in info_call
        assert "test_extractor" in info_call

    @patch("local_newsifier.monitoring.decorators.entity_extraction_duration")
    @patch("local_newsifier.monitoring.decorators.logger")
    def test_monitor_entity_extraction_with_dict_result(self, mock_logger, mock_duration):
        """Test entity extraction monitoring with non-list result."""

        @monitor_entity_extraction(source="custom")
        def extract_entities():
            return {"entities": ["a", "b"], "count": 2}

        result = extract_entities()

        assert result == {"entities": ["a", "b"], "count": 2}

        # Verify metric observation
        mock_duration.labels.assert_called_with(source="custom")
        mock_duration.labels.return_value.observe.assert_called_once()

        # Verify logging without entity count
        mock_logger.info.assert_called()
        info_call = str(mock_logger.info.call_args)
        assert "Entity extraction (custom) completed" in info_call
        assert "found" not in info_call  # No count for non-list results

    @patch("local_newsifier.monitoring.decorators.rss_feed_fetch_duration")
    @patch("local_newsifier.monitoring.decorators.logger")
    def test_monitor_rss_feed_fetch_with_entries(self, mock_logger, mock_duration):
        """Test RSS feed fetch monitoring with entries."""

        @monitor_rss_feed_fetch()
        def fetch_feed(url):
            return {"entries": [{"title": "Article 1"}, {"title": "Article 2"}]}

        result = fetch_feed("https://example.com/feed.rss")

        assert len(result["entries"]) == 2

        # Verify metric observation with URL
        mock_duration.labels.assert_called_with(feed_url="https://example.com/feed.rss")
        mock_duration.labels.return_value.observe.assert_called_once()

        # Verify logging includes article count
        mock_logger.info.assert_called()
        info_call = str(mock_logger.info.call_args)
        assert "found 2 articles" in info_call

    @patch("local_newsifier.monitoring.decorators.rss_feed_fetch_duration")
    def test_monitor_rss_feed_fetch_url_extraction(self, mock_duration):
        """Test RSS feed monitoring extracts URL from arguments."""

        @monitor_rss_feed_fetch()
        def fetch_feed(feed_url, timeout=30):
            return {"entries": []}

        # Test with positional argument
        fetch_feed("https://example.com/feed1.rss")
        mock_duration.labels.assert_called_with(feed_url="https://example.com/feed1.rss")

        # Test with no URL provided (decorator without feed_url parameter)
        @monitor_rss_feed_fetch()
        def fetch_no_args():
            return {"entries": []}

        fetch_no_args()
        mock_duration.labels.assert_called_with(feed_url=None)

    @patch("local_newsifier.monitoring.decorators.logger")
    def test_monitor_database_operation_slow(self, mock_logger):
        """Test database operation monitoring for slow queries."""

        @monitor_database_operation(operation="select", table="articles")
        def slow_query():
            time.sleep(0.6)  # Exceed 0.5s threshold
            return ["result"]

        result = slow_query()

        assert result == ["result"]

        # Verify slow operation warning
        mock_logger.warning.assert_called()
        warning_call = str(mock_logger.warning.call_args)
        assert "Slow database operation" in warning_call
        assert "select on articles" in warning_call

    @patch("local_newsifier.monitoring.decorators.errors_total")
    @patch("local_newsifier.monitoring.decorators.logger")
    def test_monitor_database_operation_error(self, mock_logger, mock_errors):
        """Test database operation monitoring with error."""

        @monitor_database_operation(operation="insert", table="users")
        def failing_query():
            raise ConnectionError("Database unavailable")

        with pytest.raises(ConnectionError, match="Database unavailable"):
            failing_query()

        # Verify error tracking
        mock_errors.labels.assert_called_with(component="database", error_type="ConnectionError")
        mock_errors.labels.return_value.inc.assert_called_once()

        # Verify error logging
        mock_logger.error.assert_called()
        error_call = str(mock_logger.error.call_args)
        assert "insert on users" in error_call
        assert "Database unavailable" in error_call
