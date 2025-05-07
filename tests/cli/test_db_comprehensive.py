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

    @patch('local_newsifier.cli.commands.db.get_db_stats')
    @patch('local_newsifier.cli.commands.db.next')
    def test_db_stats_with_data(self, mock_next, mock_get_db_stats, mock_article):
        """Test the db stats command with actual data."""
        # Create a mock article with created_at attribute
        mock_article.created_at = datetime.now(timezone.utc)
        
        # Set up mock statistics return value
        mock_get_db_stats.return_value = (
            5,  # article_count
            mock_article,  # latest_article
            mock_article,  # oldest_article
            3,  # feed_count
            2,  # active_feed_count
            7,  # processing_log_count
            4   # entity_count
        )
        
        runner = CliRunner()
        result = runner.invoke(cli, ["db", "stats"])

        assert result.exit_code == 0
        assert "Database Statistics" in result.output
        assert "Articles" in result.output
        assert "Total count: 5" in result.output
        assert "RSS Feeds" in result.output
        assert "Active: 2" in result.output
        assert "Inactive: 1" in result.output
        
        # Verify that the injectable provider was called
        mock_get_db_stats.assert_called_once()
        # The fallback mechanism should not be used
        mock_next.assert_not_called()

    @patch('local_newsifier.cli.commands.db.get_db_stats')
    @patch('local_newsifier.cli.commands.db.next')
    def test_db_stats_json_output(self, mock_next, mock_get_db_stats, mock_article):
        """Test the db stats command with JSON output."""
        # Create a mock article with created_at attribute
        mock_article.created_at = datetime.now(timezone.utc)
        
        # Set up mock statistics return value
        mock_get_db_stats.return_value = (
            5,  # article_count
            mock_article,  # latest_article
            mock_article,  # oldest_article
            3,  # feed_count
            2,  # active_feed_count
            7,  # processing_log_count
            4   # entity_count
        )
        
        runner = CliRunner()
        result = runner.invoke(cli, ["db", "stats", "--json"])

        assert result.exit_code == 0
        
        # Verify JSON output can be parsed
        output = json.loads(result.output)
        assert output["articles"]["count"] == 5
        assert output["rss_feeds"]["active"] == 2
        assert output["rss_feeds"]["inactive"] == 1
        
        # Verify that the injectable provider was called
        mock_get_db_stats.assert_called_once()
        # The fallback mechanism should not be used
        mock_next.assert_not_called()


class TestDBDuplicates:
    """Tests for the db duplicates command."""

    @patch('local_newsifier.cli.commands.db.get_injectable_session')
    @patch('local_newsifier.cli.commands.db.next')
    def test_check_duplicates_with_duplicates(self, mock_next, mock_get_injectable_session, mock_article):
        """Test the duplicates command when duplicates are found."""
        # Set up mock session
        mock_session = MagicMock()
        mock_get_injectable_session.return_value = mock_session

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
        
        # Verify the injectable session was used
        mock_get_injectable_session.assert_called_once()
        # Verify the fallback wasn't used
        mock_next.assert_not_called()

    @patch('local_newsifier.cli.commands.db.get_injectable_session')
    @patch('local_newsifier.cli.commands.db.next')
    def test_check_duplicates_json_output(self, mock_next, mock_get_injectable_session, mock_article):
        """Test the duplicates command with JSON output."""
        # Set up mock session
        mock_session = MagicMock()
        mock_get_injectable_session.return_value = mock_session

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
        
        # Verify the injectable session was used
        mock_get_injectable_session.assert_called_once()
        # Verify the fallback wasn't used
        mock_next.assert_not_called()


class TestDBArticles:
    """Tests for the db articles command."""

    @patch('local_newsifier.cli.commands.db.get_injectable_session')
    @patch('local_newsifier.cli.commands.db.next')
    def test_list_articles_with_results(self, mock_next, mock_get_injectable_session, mock_article):
        """Test the articles command when articles are found."""
        # Set up mock session
        mock_session = MagicMock()
        mock_get_injectable_session.return_value = mock_session

        # Mock articles query
        articles = [mock_article, mock_article]
        mock_session.exec.return_value.all.return_value = articles

        runner = CliRunner()
        result = runner.invoke(cli, ["db", "articles"])

        assert result.exit_code == 0
        assert "Articles (2 results)" in result.output
        assert "Test Article" in result.output
        assert "https://example.com/test" in result.output

        # Verify the injectable session was used
        mock_get_injectable_session.assert_called_once()
        # Verify the fallback wasn't used
        mock_next.assert_not_called()

    @patch('local_newsifier.cli.commands.db.get_injectable_session')
    @patch('local_newsifier.cli.commands.db.next')
    def test_list_articles_with_filters(self, mock_next, mock_get_injectable_session):
        """Test the articles command with various filters."""
        # Set up mock session
        mock_session = MagicMock()
        mock_get_injectable_session.return_value = mock_session

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

        # Verify the injectable session was used
        assert mock_get_injectable_session.call_count == 3
        # Verify the fallback wasn't used
        mock_next.assert_not_called()

    @patch('local_newsifier.cli.commands.db.get_injectable_session')
    @patch('local_newsifier.cli.commands.db.next')
    def test_list_articles_json_output(self, mock_next, mock_get_injectable_session, mock_article):
        """Test the articles command with JSON output."""
        # Set up mock session
        mock_session = MagicMock()
        mock_get_injectable_session.return_value = mock_session

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

        # Verify the injectable session was used
        mock_get_injectable_session.assert_called_once()
        # Verify the fallback wasn't used
        mock_next.assert_not_called()

    @patch('local_newsifier.cli.commands.db.get_injectable_session')
    @patch('local_newsifier.cli.commands.db.next')
    def test_list_articles_invalid_date(self, mock_next, mock_get_injectable_session):
        """Test the articles command with invalid date format."""
        # Set up mock session
        mock_session = MagicMock()
        mock_get_injectable_session.return_value = mock_session

        # Test with invalid date format
        runner = CliRunner()
        result = runner.invoke(cli, ["db", "articles", "--after", "invalid-date"])
        assert result.exit_code == 0
        assert "Error: Invalid date format" in result.output

        # Verify the injectable session was used
        mock_get_injectable_session.assert_called_once()
        # Verify the fallback wasn't used
        mock_next.assert_not_called()


class TestDBInspect:
    """Tests for the db inspect command."""

    @patch('local_newsifier.cli.commands.db.get_injectable_session')
    @patch('local_newsifier.cli.commands.db.get_article_crud')
    @patch('local_newsifier.cli.commands.db.next')
    def test_inspect_article_found(self, mock_next, mock_get_article_crud, mock_get_injectable_session, mock_article):
        """Test the inspect command with a found article."""
        # Set up mock session
        mock_session = MagicMock()
        mock_get_injectable_session.return_value = mock_session
        
        # Set up mock article CRUD
        mock_article_crud = MagicMock()
        mock_get_article_crud.return_value = mock_article_crud
        
        # Mock article crud.get to return an article
        mock_article_crud.get.return_value = mock_article

        runner = CliRunner()
        result = runner.invoke(cli, ["db", "inspect", "article", "1"])

        assert result.exit_code == 0
        assert "ARTICLE (ID: 1)" in result.output
        assert "Test Article" in result.output
        assert "https://example.com/test" in result.output
        
        # Verify the injectable dependencies were used
        mock_get_injectable_session.assert_called_once()
        mock_get_article_crud.assert_called_once()
        # Verify the fallback wasn't used
        mock_next.assert_not_called()

    @patch('local_newsifier.cli.commands.db.get_injectable_session')
    @patch('local_newsifier.cli.commands.db.get_rss_feed_crud')
    @patch('local_newsifier.cli.commands.db.next')
    def test_inspect_rss_feed_found(self, mock_next, mock_get_rss_feed_crud, mock_get_injectable_session, mock_feed, mock_feed_log):
        """Test the inspect command with a found RSS feed."""
        # Set up mock session
        mock_session = MagicMock()
        mock_get_injectable_session.return_value = mock_session
        
        # Set up mock RSS feed CRUD
        mock_rss_feed_crud = MagicMock()
        mock_get_rss_feed_crud.return_value = mock_rss_feed_crud
        
        # Mock rss_feed_crud.get to return a feed
        mock_rss_feed_crud.get.return_value = mock_feed
        
        # Mock session.exec for the logs
        mock_session.exec.return_value.all.return_value = [mock_feed_log]

        runner = CliRunner()
        result = runner.invoke(cli, ["db", "inspect", "rss_feed", "1"])

        assert result.exit_code == 0
        assert "RSS_FEED (ID: 1)" in result.output
        assert "Test Feed" in result.output
        assert "https://example.com/feed.xml" in result.output
        assert "Recent Processing Logs" in result.output
        assert "success" in result.output
        
        # Verify the injectable dependencies were used
        mock_get_injectable_session.assert_called_once()
        mock_get_rss_feed_crud.assert_called_once()
        # Verify the fallback wasn't used
        mock_next.assert_not_called()

    @patch('local_newsifier.cli.commands.db.get_injectable_session')
    @patch('local_newsifier.cli.commands.db.next')
    def test_inspect_feed_log_found(self, mock_next, mock_get_injectable_session, mock_feed_log):
        """Test the inspect command with a found feed log."""
        # Set up mock session
        mock_session = MagicMock()
        mock_get_injectable_session.return_value = mock_session

        # Mock session.get for the log
        mock_session.get.return_value = mock_feed_log

        runner = CliRunner()
        result = runner.invoke(cli, ["db", "inspect", "feed_log", "1"])

        assert result.exit_code == 0
        assert "FEED_LOG (ID: 1)" in result.output
        assert "success" in result.output
        assert "10" in result.output  # articles_found
        assert "5" in result.output   # articles_added
        
        # Verify the injectable session was used
        mock_get_injectable_session.assert_called_once()
        # Verify the fallback wasn't used
        mock_next.assert_not_called()

    @patch('local_newsifier.cli.commands.db.get_injectable_session')
    @patch('local_newsifier.cli.commands.db.next')
    def test_inspect_entity_found(self, mock_next, mock_get_injectable_session, mock_entity):
        """Test the inspect command with a found entity."""
        # Set up mock session
        mock_session = MagicMock()
        mock_get_injectable_session.return_value = mock_session

        # Mock session.get for the entity
        mock_session.get.return_value = mock_entity

        runner = CliRunner()
        result = runner.invoke(cli, ["db", "inspect", "entity", "1"])

        assert result.exit_code == 0
        assert "ENTITY (ID: 1)" in result.output
        assert "Test Entity" in result.output
        assert "PERSON" in result.output
        
        # Verify the injectable session was used
        mock_get_injectable_session.assert_called_once()
        # Verify the fallback wasn't used
        mock_next.assert_not_called()

    @patch('local_newsifier.cli.commands.db.get_injectable_session')
    @patch('local_newsifier.cli.commands.db.get_rss_feed_crud')
    @patch('local_newsifier.cli.commands.db.next')
    def test_inspect_rss_feed_not_found(self, mock_next, mock_get_rss_feed_crud, mock_get_injectable_session):
        """Test the inspect command with a non-existent RSS feed."""
        # Set up mock session
        mock_session = MagicMock()
        mock_get_injectable_session.return_value = mock_session
        
        # Set up mock RSS feed CRUD
        mock_rss_feed_crud = MagicMock()
        mock_get_rss_feed_crud.return_value = mock_rss_feed_crud
        
        # Mock rss_feed_crud.get to return None
        mock_rss_feed_crud.get.return_value = None

        runner = CliRunner()
        result = runner.invoke(cli, ["db", "inspect", "rss_feed", "999"])

        assert result.exit_code == 0
        assert "Error: RSS Feed with ID 999 not found" in result.output
        
        # Verify the injectable dependencies were used
        mock_get_injectable_session.assert_called_once()
        mock_get_rss_feed_crud.assert_called_once()
        # Verify the fallback wasn't used
        mock_next.assert_not_called()

    @patch('local_newsifier.cli.commands.db.get_injectable_session')
    @patch('local_newsifier.cli.commands.db.next')
    def test_inspect_feed_log_not_found(self, mock_next, mock_get_injectable_session):
        """Test the inspect command with a non-existent feed log."""
        # Set up mock session
        mock_session = MagicMock()
        mock_get_injectable_session.return_value = mock_session

        # Mock session.get for the log to return None
        mock_session.get.return_value = None

        runner = CliRunner()
        result = runner.invoke(cli, ["db", "inspect", "feed_log", "999"])

        assert result.exit_code == 0
        assert "Error: Feed Processing Log with ID 999 not found" in result.output
        
        # Verify the injectable session was used
        mock_get_injectable_session.assert_called_once()
        # Verify the fallback wasn't used
        mock_next.assert_not_called()

    @patch('local_newsifier.cli.commands.db.get_injectable_session')
    @patch('local_newsifier.cli.commands.db.next')
    def test_inspect_entity_not_found(self, mock_next, mock_get_injectable_session):
        """Test the inspect command with a non-existent entity."""
        # Set up mock session
        mock_session = MagicMock()
        mock_get_injectable_session.return_value = mock_session

        # Mock session.get for the entity to return None
        mock_session.get.return_value = None

        runner = CliRunner()
        result = runner.invoke(cli, ["db", "inspect", "entity", "999"])

        assert result.exit_code == 0
        assert "Error: Entity with ID 999 not found" in result.output
        
        # Verify the injectable session was used
        mock_get_injectable_session.assert_called_once()
        # Verify the fallback wasn't used
        mock_next.assert_not_called()

    @patch('local_newsifier.cli.commands.db.get_injectable_session')
    @patch('local_newsifier.cli.commands.db.get_article_crud')
    @patch('local_newsifier.cli.commands.db.next')
    def test_inspect_json_output(self, mock_next, mock_get_article_crud, mock_get_injectable_session, mock_article):
        """Test the inspect command with JSON output."""
        # Set up mock session
        mock_session = MagicMock()
        mock_get_injectable_session.return_value = mock_session
        
        # Set up mock article CRUD
        mock_article_crud = MagicMock()
        mock_get_article_crud.return_value = mock_article_crud
        
        # Mock article crud.get to return an article
        mock_article_crud.get.return_value = mock_article

        runner = CliRunner()
        result = runner.invoke(cli, ["db", "inspect", "article", "1", "--json"])

        assert result.exit_code == 0
        
        # Verify JSON output can be parsed
        output = json.loads(result.output)
        assert output["id"] == 1
        assert output["title"] == "Test Article"
        assert output["url"] == "https://example.com/test"
        
        # Verify the injectable dependencies were used
        mock_get_injectable_session.assert_called_once()
        mock_get_article_crud.assert_called_once()
        # Verify the fallback wasn't used
        mock_next.assert_not_called()


class TestDBPurgeDuplicates:
    """Tests for the db purge-duplicates command."""

    @patch('local_newsifier.cli.commands.db.get_injectable_session')
    @patch('local_newsifier.cli.commands.db.next')
    def test_purge_duplicates_with_duplicates(self, mock_next, mock_get_injectable_session, mock_article):
        """Test the purge-duplicates command when duplicates are found."""
        # Set up mock session
        mock_session = MagicMock()
        mock_get_injectable_session.return_value = mock_session

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
        
        # Verify session.delete was called with article2
        mock_session.delete.assert_called_once_with(article2)
        # Verify session.commit was called
        mock_session.commit.assert_called_once()
        
        # Verify the injectable session was used
        mock_get_injectable_session.assert_called_once()
        # Verify the fallback wasn't used
        mock_next.assert_not_called()

    @patch('local_newsifier.cli.commands.db.get_injectable_session')
    @patch('local_newsifier.cli.commands.db.next')
    def test_purge_duplicates_dry_run(self, mock_next, mock_get_injectable_session, mock_article):
        """Test the purge-duplicates command with dry run option."""
        # Set up mock session
        mock_session = MagicMock()
        mock_get_injectable_session.return_value = mock_session

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
        
        # Verify session.delete was not called
        mock_session.delete.assert_not_called()
        # Verify session.commit was not called
        mock_session.commit.assert_not_called()
        
        # Verify the injectable session was used
        mock_get_injectable_session.assert_called_once()
        # Verify the fallback wasn't used
        mock_next.assert_not_called()

    @patch('local_newsifier.cli.commands.db.get_injectable_session')
    @patch('local_newsifier.cli.commands.db.next')
    def test_purge_duplicates_json_output(self, mock_next, mock_get_injectable_session, mock_article):
        """Test the purge-duplicates command with JSON output."""
        # Set up mock session
        mock_session = MagicMock()
        mock_get_injectable_session.return_value = mock_session

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
        
        # Verify the injectable session was used
        mock_get_injectable_session.assert_called_once()
        # Verify the fallback wasn't used
        mock_next.assert_not_called()
