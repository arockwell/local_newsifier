"""Comprehensive tests for database diagnostics CLI commands."""

import pytest
import json
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timezone
from click.testing import CliRunner

from local_newsifier.cli.main import cli
from local_newsifier.models.article import Article
from local_newsifier.models.entity import Entity
from local_newsifier.models.rss_feed import RSSFeed, RSSFeedProcessingLog
from local_newsifier.di.providers import (
    get_session, 
    get_article_crud, 
    get_rss_feed_crud,
    get_entity_crud,
    get_feed_processing_log_crud
)


@pytest.fixture
def mock_article():
    """Create a mock article for testing."""
    article = MagicMock(spec=Article)
    article.id = 1
    article.title = "Test Article"
    article.url = "https://example.com/test"
    article.source = "test_source"
    article.status = "processed"
    article.content = "This is test content" * 10  # Some content with length
    article.created_at = datetime.now(timezone.utc)
    article.updated_at = datetime.now(timezone.utc)
    article.published_at = datetime.now(timezone.utc)
    article.scraped_at = datetime.now(timezone.utc)
    return article


@pytest.fixture
def mock_feed():
    """Create a mock RSS feed for testing."""
    feed = MagicMock(spec=RSSFeed)
    feed.id = 1
    feed.name = "Test Feed"
    feed.url = "https://example.com/feed.xml"
    feed.description = "A test feed"
    feed.is_active = True
    feed.created_at = datetime.now(timezone.utc)
    feed.updated_at = datetime.now(timezone.utc)
    feed.last_fetched_at = datetime.now(timezone.utc)
    return feed


@pytest.fixture
def mock_feed_log():
    """Create a mock RSS feed processing log for testing."""
    log = MagicMock(spec=RSSFeedProcessingLog)
    log.id = 1
    log.feed_id = 1
    log.status = "success"
    log.started_at = datetime.now(timezone.utc)
    log.completed_at = datetime.now(timezone.utc)
    log.articles_found = 10
    log.articles_added = 5
    log.error_message = None
    return log


@pytest.fixture
def mock_entity():
    """Create a mock entity for testing."""
    entity = MagicMock(spec=Entity)
    entity.id = 1
    entity.name = "Test Entity"
    entity.entity_type = "PERSON"
    entity.created_at = datetime.now(timezone.utc)
    entity.updated_at = datetime.now(timezone.utc)
    return entity


class TestDBStats:
    """Tests for the db stats command."""

    @patch('local_newsifier.cli.cli_utils.load_dependency')
    def test_db_stats_with_data(self, mock_get_injected_obj, mock_article):
        """Test the db stats command with actual data."""
        # Set up mock session
        mock_session = MagicMock()
        mock_session_gen = MagicMock()
        mock_session_gen.__next__.return_value = mock_session
        mock_get_injected_obj.return_value = mock_session_gen

        # Mock query results for articles
        mock_session.exec.return_value.one.side_effect = [5, 3, 2, 7, 4]  # article count, feed count, active feeds, processing log count, entity count
        mock_session.exec.return_value.first.side_effect = [mock_article, mock_article]  # latest article, oldest article

        runner = CliRunner()
        result = runner.invoke(cli, ["db", "stats"])

        assert result.exit_code == 0
        assert "Database Statistics" in result.output
        assert "Articles" in result.output
        assert "Total count: 5" in result.output
        assert "RSS Feeds" in result.output
        assert "Active: 2" in result.output
        assert "Inactive: 1" in result.output

    @patch('local_newsifier.cli.cli_utils.load_dependency')
    def test_db_stats_json_output(self, mock_get_injected_obj, mock_article):
        """Test the db stats command with JSON output."""
        # Set up mock session
        mock_session = MagicMock()
        mock_session_gen = MagicMock()
        mock_session_gen.__next__.return_value = mock_session
        mock_get_injected_obj.return_value = mock_session_gen

        # Mock query results for articles
        mock_session.exec.return_value.one.side_effect = [5, 3, 2, 7, 4]  # article count, feed count, active feeds, processing log count, entity count
        mock_session.exec.return_value.first.side_effect = [mock_article, mock_article]  # latest article, oldest article

        runner = CliRunner()
        result = runner.invoke(cli, ["db", "stats", "--json"])

        assert result.exit_code == 0
        
        # Verify JSON output can be parsed
        output = json.loads(result.output)
        assert output["articles"]["count"] == 5
        assert output["rss_feeds"]["active"] == 2
        assert output["rss_feeds"]["inactive"] == 1


class TestDBDuplicates:
    """Tests for the db duplicates command."""

    @patch('local_newsifier.cli.cli_utils.load_dependency')
    def test_check_duplicates_with_duplicates(self, mock_get_injected_obj, mock_article):
        """Test the duplicates command when duplicates are found."""
        # Set up mock session
        mock_session = MagicMock()
        mock_session_gen = MagicMock()
        mock_session_gen.__next__.return_value = mock_session
        mock_get_injected_obj.return_value = mock_session_gen

        # Mock duplicate URLs query
        duplicate_urls = [
            ("https://example.com/duplicate1", 2),
            ("https://example.com/duplicate2", 3)
        ]
        mock_session.exec.return_value.all.side_effect = [
            duplicate_urls,  # First call returns the duplicate URLs
            [mock_article, mock_article],  # Second call for first URL's articles
            [mock_article, mock_article, mock_article]  # Third call for second URL's articles
        ]

        runner = CliRunner()
        result = runner.invoke(cli, ["db", "duplicates"])

        assert result.exit_code == 0
        assert "Found 2 URLs with duplicate articles" in result.output
        assert "https://example.com/duplicate1" in result.output
        assert "https://example.com/duplicate2" in result.output
        assert "Number of duplicates: 2" in result.output
        assert "Number of duplicates: 3" in result.output

    @patch('local_newsifier.cli.cli_utils.load_dependency')
    def test_check_duplicates_json_output(self, mock_get_injected_obj, mock_article):
        """Test the duplicates command with JSON output."""
        # Set up mock session
        mock_session = MagicMock()
        mock_session_gen = MagicMock()
        mock_session_gen.__next__.return_value = mock_session
        mock_get_injected_obj.return_value = mock_session_gen

        # Mock duplicate URLs query
        duplicate_urls = [("https://example.com/duplicate", 2)]
        mock_session.exec.return_value.all.side_effect = [
            duplicate_urls,  # First call returns the duplicate URLs
            [mock_article, mock_article]  # Second call for the articles
        ]

        runner = CliRunner()
        result = runner.invoke(cli, ["db", "duplicates", "--json"])

        assert result.exit_code == 0
        
        # Verify JSON output can be parsed
        output = json.loads(result.output)
        assert len(output) == 1
        assert output[0]["url"] == "https://example.com/duplicate"
        assert output[0]["count"] == 2
        assert len(output[0]["articles"]) == 2


class TestDBArticles:
    """Tests for the db articles command."""

    @patch('local_newsifier.cli.cli_utils.load_dependency')
    def test_list_articles_with_results(self, mock_get_injected_obj, mock_article):
        """Test the articles command when articles are found."""
        # Set up mock session
        mock_session = MagicMock()
        mock_session_gen = MagicMock()
        mock_session_gen.__next__.return_value = mock_session
        mock_get_injected_obj.return_value = mock_session_gen

        # Mock articles query
        articles = [mock_article, mock_article]
        mock_session.exec.return_value.all.return_value = articles

        runner = CliRunner()
        result = runner.invoke(cli, ["db", "articles"])

        assert result.exit_code == 0
        assert "Articles (2 results)" in result.output
        assert "Test Article" in result.output
        assert "https://example.com/test" in result.output

    @patch('local_newsifier.cli.cli_utils.load_dependency')
    def test_list_articles_with_filters(self, mock_get_injected_obj):
        """Test the articles command with various filters."""
        # Set up mock session
        mock_session = MagicMock()
        mock_session_gen = MagicMock()
        mock_session_gen.__next__.return_value = mock_session
        mock_get_injected_obj.return_value = mock_session_gen

        # Mock empty result
        mock_session.exec.return_value.all.return_value = []

        # Test with source filter
        runner = CliRunner()
        result = runner.invoke(cli, ["db", "articles", "--source", "cnn"])
        assert result.exit_code == 0
        assert "No articles found matching the criteria" in result.output

        # Test with status filter
        result = runner.invoke(cli, ["db", "articles", "--status", "pending"])
        assert result.exit_code == 0
        assert "No articles found matching the criteria" in result.output

        # Test with date filters
        result = runner.invoke(cli, ["db", "articles", "--after", "2025-01-01", "--before", "2025-12-31"])
        assert result.exit_code == 0
        assert "No articles found matching the criteria" in result.output

    @patch('local_newsifier.cli.cli_utils.load_dependency')
    def test_list_articles_json_output(self, mock_get_injected_obj, mock_article):
        """Test the articles command with JSON output."""
        # Set up mock session
        mock_session = MagicMock()
        mock_session_gen = MagicMock()
        mock_session_gen.__next__.return_value = mock_session
        mock_get_injected_obj.return_value = mock_session_gen

        # Mock articles query
        articles = [mock_article]
        mock_session.exec.return_value.all.return_value = articles

        runner = CliRunner()
        result = runner.invoke(cli, ["db", "articles", "--json"])

        assert result.exit_code == 0
        
        # Verify JSON output can be parsed
        output = json.loads(result.output)
        assert len(output) == 1
        assert output[0]["title"] == "Test Article"
        assert output[0]["url"] == "https://example.com/test"

    @patch('local_newsifier.cli.cli_utils.load_dependency')
    def test_list_articles_invalid_date(self, mock_get_injected_obj):
        """Test the articles command with invalid date format."""
        # Set up mock session
        mock_session = MagicMock()
        mock_session_gen = MagicMock()
        mock_session_gen.__next__.return_value = mock_session
        mock_get_injected_obj.return_value = mock_session_gen

        # Test with invalid date format
        runner = CliRunner()
        result = runner.invoke(cli, ["db", "articles", "--after", "invalid-date"])
        assert result.exit_code == 0
        assert "Error: Invalid date format" in result.output


class TestDBInspect:
    """Tests for the db inspect command."""

    @patch('local_newsifier.cli.cli_utils.load_dependency')
    def test_inspect_article_found(self, mock_get_injected_obj, mock_article):
        """Test the inspect command with a found article."""
        # Create mocks for session and crud
        mock_session = MagicMock()
        mock_session_gen = MagicMock()
        mock_session_gen.__next__.return_value = mock_session
        mock_article_crud = MagicMock()
        
        # Setup the article_crud.get to return an article
        mock_article_crud.get.return_value = mock_article
        
        # Configure get_injected_obj to return appropriate objects based on the argument
        def side_effect(provider):
            if provider == get_session:
                return mock_session_gen
            elif provider == get_article_crud:
                return mock_article_crud
            else:
                return MagicMock()
                
        mock_get_injected_obj.side_effect = side_effect

        runner = CliRunner()
        result = runner.invoke(cli, ["db", "inspect", "article", "1"])

        assert result.exit_code == 0
        assert "ARTICLE (ID: 1)" in result.output
        assert "Test Article" in result.output
        assert "https://example.com/test" in result.output

    @patch('local_newsifier.cli.cli_utils.load_dependency')
    def test_inspect_rss_feed_found(self, mock_get_injected_obj, mock_feed, mock_feed_log):
        """Test the inspect command with a found RSS feed."""
        # Create mocks for session and crud
        mock_session = MagicMock()
        mock_session_gen = MagicMock()
        mock_session_gen.__next__.return_value = mock_session
        mock_rss_feed_crud = MagicMock()
        
        # Setup the rss_feed_crud.get to return a feed
        mock_rss_feed_crud.get.return_value = mock_feed
        
        # Mock session.exec for the logs
        mock_session.exec.return_value.all.return_value = [mock_feed_log]
        
        # Configure get_injected_obj to return appropriate objects based on the argument
        def side_effect(provider):
            if provider == get_session:
                return mock_session_gen
            elif provider == get_rss_feed_crud:
                return mock_rss_feed_crud
            else:
                return MagicMock()
                
        mock_get_injected_obj.side_effect = side_effect

        runner = CliRunner()
        result = runner.invoke(cli, ["db", "inspect", "rss_feed", "1"])

        assert result.exit_code == 0
        assert "RSS_FEED (ID: 1)" in result.output
        assert "Test Feed" in result.output
        assert "https://example.com/feed.xml" in result.output
        assert "Recent Processing Logs" in result.output
        assert "success" in result.output

    @patch('local_newsifier.cli.cli_utils.load_dependency')
    def test_inspect_feed_log_found(self, mock_get_injected_obj, mock_feed_log):
        """Test the inspect command with a found feed log."""
        # Create mocks for session and crud
        mock_session = MagicMock()
        mock_session_gen = MagicMock()
        mock_session_gen.__next__.return_value = mock_session
        mock_feed_log_crud = MagicMock()
        
        # Setup the feed_log_crud.get to return a log
        mock_feed_log_crud.get.return_value = mock_feed_log
        
        # Configure get_injected_obj to return appropriate objects based on the argument
        def side_effect(provider):
            if provider == get_session:
                return mock_session_gen
            elif provider == get_feed_processing_log_crud:
                return mock_feed_log_crud
            else:
                return MagicMock()
                
        mock_get_injected_obj.side_effect = side_effect

        runner = CliRunner()
        result = runner.invoke(cli, ["db", "inspect", "feed_log", "1"])

        assert result.exit_code == 0
        assert "FEED_LOG (ID: 1)" in result.output
        assert "success" in result.output
        assert "10" in result.output  # articles_found
        assert "5" in result.output   # articles_added

    @patch('local_newsifier.cli.cli_utils.load_dependency')
    def test_inspect_entity_found(self, mock_get_injected_obj, mock_entity):
        """Test the inspect command with a found entity."""
        # Create mocks for session and crud
        mock_session = MagicMock()
        mock_session_gen = MagicMock()
        mock_session_gen.__next__.return_value = mock_session
        mock_entity_crud = MagicMock()
        
        # Setup the entity_crud.get to return an entity
        mock_entity_crud.get.return_value = mock_entity
        
        # Configure get_injected_obj to return appropriate objects based on the argument
        def side_effect(provider):
            if provider == get_session:
                return mock_session_gen
            elif provider == get_entity_crud:
                return mock_entity_crud
            else:
                return MagicMock()
                
        mock_get_injected_obj.side_effect = side_effect

        runner = CliRunner()
        result = runner.invoke(cli, ["db", "inspect", "entity", "1"])

        assert result.exit_code == 0
        assert "ENTITY (ID: 1)" in result.output
        assert "Test Entity" in result.output
        assert "PERSON" in result.output

    @patch('local_newsifier.cli.cli_utils.load_dependency')
    def test_inspect_rss_feed_not_found(self, mock_get_injected_obj):
        """Test the inspect command with a non-existent RSS feed."""
        # Create mocks for session and crud
        mock_session = MagicMock()
        mock_session_gen = MagicMock()
        mock_session_gen.__next__.return_value = mock_session
        mock_rss_feed_crud = MagicMock()
        
        # Setup the rss_feed_crud.get to return None
        mock_rss_feed_crud.get.return_value = None
        
        # Configure get_injected_obj to return appropriate objects based on the argument
        def side_effect(provider):
            if provider == get_session:
                return mock_session_gen
            elif provider == get_rss_feed_crud:
                return mock_rss_feed_crud
            else:
                return MagicMock()
                
        mock_get_injected_obj.side_effect = side_effect

        runner = CliRunner()
        result = runner.invoke(cli, ["db", "inspect", "rss_feed", "999"])

        assert result.exit_code == 0
        assert "Error: RSS Feed with ID 999 not found" in result.output

    @patch('local_newsifier.cli.cli_utils.load_dependency')
    def test_inspect_feed_log_not_found(self, mock_get_injected_obj):
        """Test the inspect command with a non-existent feed log."""
        # Create mocks for session and crud
        mock_session = MagicMock()
        mock_session_gen = MagicMock()
        mock_session_gen.__next__.return_value = mock_session
        mock_feed_log_crud = MagicMock()
        
        # Setup the feed_log_crud.get to return None
        mock_feed_log_crud.get.return_value = None
        
        # Configure get_injected_obj to return appropriate objects based on the argument
        def side_effect(provider):
            if provider == get_session:
                return mock_session_gen
            elif provider == get_feed_processing_log_crud:
                return mock_feed_log_crud
            else:
                return MagicMock()
                
        mock_get_injected_obj.side_effect = side_effect

        runner = CliRunner()
        result = runner.invoke(cli, ["db", "inspect", "feed_log", "999"])

        assert result.exit_code == 0
        assert "Error: Feed Processing Log with ID 999 not found" in result.output

    @patch('local_newsifier.cli.cli_utils.load_dependency')
    def test_inspect_entity_not_found(self, mock_get_injected_obj):
        """Test the inspect command with a non-existent entity."""
        # Create mocks for session and crud
        mock_session = MagicMock()
        mock_session_gen = MagicMock()
        mock_session_gen.__next__.return_value = mock_session
        mock_entity_crud = MagicMock()
        
        # Setup the entity_crud.get to return None
        mock_entity_crud.get.return_value = None
        
        # Configure get_injected_obj to return appropriate objects based on the argument
        def side_effect(provider):
            if provider == get_session:
                return mock_session_gen
            elif provider == get_entity_crud:
                return mock_entity_crud
            else:
                return MagicMock()
                
        mock_get_injected_obj.side_effect = side_effect

        runner = CliRunner()
        result = runner.invoke(cli, ["db", "inspect", "entity", "999"])

        assert result.exit_code == 0
        assert "Error: Entity with ID 999 not found" in result.output

    @patch('local_newsifier.cli.cli_utils.load_dependency')
    def test_inspect_json_output(self, mock_get_injected_obj, mock_article):
        """Test the inspect command with JSON output."""
        # Create mocks for session and crud
        mock_session = MagicMock()
        mock_session_gen = MagicMock()
        mock_session_gen.__next__.return_value = mock_session
        mock_article_crud = MagicMock()
        
        # Setup the article_crud.get to return an article
        mock_article_crud.get.return_value = mock_article
        
        # Configure get_injected_obj to return appropriate objects based on the argument
        def side_effect(provider):
            if provider == get_session:
                return mock_session_gen
            elif provider == get_article_crud:
                return mock_article_crud
            else:
                return MagicMock()
                
        mock_get_injected_obj.side_effect = side_effect

        runner = CliRunner()
        result = runner.invoke(cli, ["db", "inspect", "article", "1", "--json"])

        assert result.exit_code == 0
        
        # Verify JSON output can be parsed
        output = json.loads(result.output)
        assert output["id"] == 1
        assert output["title"] == "Test Article"
        assert output["url"] == "https://example.com/test"


class TestDBPurgeDuplicates:
    """Tests for the db purge-duplicates command."""

    @patch('local_newsifier.cli.cli_utils.load_dependency')
    def test_purge_duplicates_with_duplicates(self, mock_get_injected_obj, mock_article):
        """Test the purge-duplicates command when duplicates are found."""
        # Set up mock session and mock article_crud
        mock_session = MagicMock()
        mock_session_gen = MagicMock()
        mock_session_gen.__next__.return_value = mock_session
        mock_article_crud = MagicMock()
        
        # Configure get_injected_obj to return appropriate objects based on the argument
        def side_effect(provider):
            if provider == get_session:
                return mock_session_gen
            elif provider == get_article_crud:
                return mock_article_crud
            else:
                return MagicMock()
                
        mock_get_injected_obj.side_effect = side_effect

        # Create two different article instances
        article1 = MagicMock(spec=Article)
        article1.id = 1
        article1.url = "https://example.com/duplicate"
        article1.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)

        article2 = MagicMock(spec=Article)
        article2.id = 2
        article2.url = "https://example.com/duplicate"
        article2.created_at = datetime(2025, 2, 1, tzinfo=timezone.utc)

        # Mock duplicate URLs query
        duplicate_urls = [("https://example.com/duplicate", 2)]
        mock_session.exec.return_value.all.side_effect = [
            duplicate_urls,  # First call returns the duplicate URLs
            [article1, article2]  # Second call for the articles
        ]

        runner = CliRunner()
        # Use --yes to skip confirmation prompt
        result = runner.invoke(cli, ["db", "purge-duplicates", "--yes"])

        assert result.exit_code == 0
        assert "Removed 1 duplicate articles across 1 URLs" in result.output
        assert "Kept article ID: 1" in result.output
        assert "Removed article IDs: 2" in result.output
        
        # Verify article_crud.remove was called with the correct arguments
        mock_article_crud.remove.assert_called_once_with(mock_session, id=article2.id)
        # Verify session.commit was called
        mock_session.commit.assert_called_once()

    @patch('local_newsifier.cli.cli_utils.load_dependency')
    def test_purge_duplicates_dry_run(self, mock_get_injected_obj, mock_article):
        """Test the purge-duplicates command with dry run option."""
        # Set up mock session and mock article_crud
        mock_session = MagicMock()
        mock_session_gen = MagicMock()
        mock_session_gen.__next__.return_value = mock_session
        mock_article_crud = MagicMock()
        
        # Configure get_injected_obj to return appropriate objects based on the argument
        def side_effect(provider):
            if provider == get_session:
                return mock_session_gen
            elif provider == get_article_crud:
                return mock_article_crud
            else:
                return MagicMock()
                
        mock_get_injected_obj.side_effect = side_effect

        # Create two different article instances
        article1 = MagicMock(spec=Article)
        article1.id = 1
        article1.url = "https://example.com/duplicate"
        article1.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)

        article2 = MagicMock(spec=Article)
        article2.id = 2
        article2.url = "https://example.com/duplicate"
        article2.created_at = datetime(2025, 2, 1, tzinfo=timezone.utc)

        # Mock duplicate URLs query
        duplicate_urls = [("https://example.com/duplicate", 2)]
        mock_session.exec.return_value.all.side_effect = [
            duplicate_urls,  # First call returns the duplicate URLs
            [article1, article2]  # Second call for the articles
        ]

        runner = CliRunner()
        # Use --yes to skip confirmation prompt and --dry-run
        result = runner.invoke(cli, ["db", "purge-duplicates", "--yes", "--dry-run"])

        assert result.exit_code == 0
        assert "Would remove 1 duplicate articles across 1 URLs" in result.output
        assert "(DRY RUN - No changes were made)" in result.output
        
        # Verify article_crud.remove was not called
        mock_article_crud.remove.assert_not_called()
        # Verify session.commit was not called
        mock_session.commit.assert_not_called()

    @patch('local_newsifier.cli.cli_utils.load_dependency')
    def test_purge_duplicates_json_output(self, mock_get_injected_obj, mock_article):
        """Test the purge-duplicates command with JSON output."""
        # Set up mock session and mock article_crud
        mock_session = MagicMock()
        mock_session_gen = MagicMock()
        mock_session_gen.__next__.return_value = mock_session
        mock_article_crud = MagicMock()
        
        # Configure get_injected_obj to return appropriate objects based on the argument
        def side_effect(provider):
            if provider == get_session:
                return mock_session_gen
            elif provider == get_article_crud:
                return mock_article_crud
            else:
                return MagicMock()
                
        mock_get_injected_obj.side_effect = side_effect

        # Create two different article instances
        article1 = MagicMock(spec=Article)
        article1.id = 1
        article1.url = "https://example.com/duplicate"
        article1.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)

        article2 = MagicMock(spec=Article)
        article2.id = 2
        article2.url = "https://example.com/duplicate"
        article2.created_at = datetime(2025, 2, 1, tzinfo=timezone.utc)

        # Mock duplicate URLs query
        duplicate_urls = [("https://example.com/duplicate", 2)]
        mock_session.exec.return_value.all.side_effect = [
            duplicate_urls,  # First call returns the duplicate URLs
            [article1, article2]  # Second call for the articles
        ]

        runner = CliRunner()
        # Use --yes to skip confirmation prompt, --json for output format
        result = runner.invoke(cli, ["db", "purge-duplicates", "--yes", "--json"])

        assert result.exit_code == 0
        
        # Verify JSON output can be parsed
        output = json.loads(result.output)
        assert output["total_urls"] == 1
        assert output["total_removed"] == 1
        assert output["dry_run"] is False
        assert len(output["details"]) == 1
        assert output["details"][0]["kept_id"] == 1
        assert output["details"][0]["removed_ids"] == [2]
        
        # Verify article_crud.remove was called with the correct arguments
        mock_article_crud.remove.assert_called_once_with(mock_session, id=article2.id)
        # Verify session.commit was called
        mock_session.commit.assert_called_once()