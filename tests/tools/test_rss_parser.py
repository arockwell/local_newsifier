"""
Tests for the RSS Parser tool.

This test suite covers:
1. Basic RSS and Atom feed parsing
2. Malformed XML handling
3. Feed caching mechanism
4. URL filtering and processing
5. Error handling for network issues
"""

import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest
import requests

from local_newsifier.tools.rss_parser import RSSItem, RSSParser, parse_rss_feed

# Sample RSS feed XML
SAMPLE_RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>Test Feed</title>
        <link>http://example.com</link>
        <description>Test feed for unit tests</description>
        <item>
            <title>Test Article 1</title>
            <link>http://example.com/1</link>
            <description>Test description 1</description>
            <pubDate>Fri, 12 Apr 2024 10:30:00 GMT</pubDate>
        </item>
        <item>
            <title>Test Article 2</title>
            <link>http://example.com/2</link>
            <description>Test description 2</description>
            <pubDate>Fri, 12 Apr 2024 11:30:00 GMT</pubDate>
        </item>
    </channel>
</rss>
"""

# Sample Atom feed XML
SAMPLE_ATOM_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
    <title>Test Feed</title>
    <link href="http://example.com"/>
    <entry>
        <title>Test Article 1</title>
        <link href="http://example.com/1"/>
        <summary>Test description 1</summary>
        <published>2024-04-12T10:30:00Z</published>
    </entry>
    <entry>
        <title>Test Article 2</title>
        <link href="http://example.com/2"/>
        <summary>Test description 2</summary>
        <published>2024-04-12T11:30:00Z</published>
    </entry>
</feed>
"""

# Sample malformed XML
MALFORMED_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>Malformed Feed</title>
        <link>http://example.com</link>
        <description>Malformed feed for testing</description>
        <item>
            <title>Malformed Article</title>
            <link>http://example.com/malformed</link>
            <!-- Missing closing tag for description -->
            <description>This description has no closing tag
            <pubDate>Invalid Date Format</pubDate>
        </item>
        <!-- Missing closing tags -->
</rss>
"""

# Sample RSS feed with missing elements
INCOMPLETE_RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>Incomplete Feed</title>
        <link>http://example.com</link>
        <description>Incomplete feed for testing</description>
        <item>
            <!-- Missing title -->
            <link>http://example.com/incomplete1</link>
            <description>Description for incomplete item 1</description>
            <!-- Missing pubDate -->
        </item>
        <item>
            <title>Incomplete Article 2</title>
            <!-- Missing link -->
            <description>Description for incomplete item 2</description>
            <pubDate>Fri, 12 Apr 2024 12:30:00 GMT</pubDate>
        </item>
    </channel>
</rss>
"""

# Sample Atom feed with missing elements
INCOMPLETE_ATOM_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
    <title>Incomplete Atom Feed</title>
    <!-- Missing link -->
    <entry>
        <!-- Missing title -->
        <link href="http://example.com/incomplete1"/>
        <!-- Missing summary -->
        <published>2024-04-12T12:30:00Z</published>
    </entry>
    <entry>
        <title>Incomplete Atom Article 2</title>
        <!-- Missing link -->
        <summary>Summary for incomplete atom item 2</summary>
        <!-- Missing published date -->
    </entry>
</feed>
"""

# Sample RSS feed with unusual date formats
UNUSUAL_DATES_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>Unusual Dates Feed</title>
        <link>http://example.com</link>
        <description>Feed with unusual date formats</description>
        <item>
            <title>Article with ISO Date</title>
            <link>http://example.com/iso-date</link>
            <description>This article has an ISO date format</description>
            <pubDate>2024-04-12T10:30:00Z</pubDate>
        </item>
        <item>
            <title>Article with RFC822 Date</title>
            <link>http://example.com/rfc822-date</link>
            <description>This article has an RFC822 date format</description>
            <pubDate>Fri, 12 Apr 2024 10:30:00 +0000</pubDate>
        </item>
        <item>
            <title>Article with Invalid Date</title>
            <link>http://example.com/invalid-date</link>
            <description>This article has an invalid date format</description>
            <pubDate>Not a real date</pubDate>
        </item>
    </channel>
</rss>
"""
@pytest.fixture
def mock_response():
    """Create a mock HTTP response."""
    response = Mock()
    response.raise_for_status = Mock()
    return response

# Import event loop fixture for handling async code with @injectable decorator
from tests.fixtures.event_loop import event_loop_fixture  # noqa


class TestRSSParser:
    @pytest.fixture(autouse=True)
    def setup_method(self, event_loop_fixture):
        # Use the fixture to handle potential event loop issues
        # Create parser in each test using event_loop_fixture to properly handle @injectable
        self.parser = RSSParser()

    def test_init_without_cache(self, event_loop_fixture):
        """Test initialization without cache file."""
        parser = RSSParser()
        assert parser.cache_file is None
        assert parser.processed_urls == set()

    def test_init_with_cache(self, tmp_path, event_loop_fixture):
        """Test initialization with cache file."""
        cache_file = tmp_path / "test_cache.json"
        urls = ["http://example.com/1", "http://example.com/2"]
        cache_file.write_text(json.dumps(urls))

        parser = RSSParser(str(cache_file))
        assert parser.cache_file == str(cache_file)
        assert parser.processed_urls == set(urls)

    def test_init_with_invalid_cache(self, tmp_path, event_loop_fixture):
        """Test initialization with invalid cache file."""
        cache_file = tmp_path / "invalid_cache.json"
        cache_file.write_text("invalid json")

        parser = RSSParser(str(cache_file))
        assert parser.processed_urls == set()

    def test_init_with_nonexistent_cache_dir(self, tmp_path, event_loop_fixture):
        """Test initialization with cache file in nonexistent directory."""
        nonexistent_dir = tmp_path / "nonexistent"
        cache_file = nonexistent_dir / "cache.json"
        
        # Directory doesn't exist yet
        assert not nonexistent_dir.exists()
        
        # Should not raise an error
        parser = RSSParser(str(cache_file))
        assert parser.cache_file == str(cache_file)
        assert parser.processed_urls == set()

    @patch("requests.get")
    def test_parse_rss_feed(self, mock_get, event_loop_fixture):
        """Test parsing an RSS feed."""
        # Setup mock response
        mock_response = Mock()
        mock_response.content = SAMPLE_RSS_XML.encode("utf-8")
        mock_get.return_value = mock_response

        # Test parsing
        items = self.parser.parse_feed("http://example.com/feed")

        assert len(items) == 2
        assert items[0].title == "Test Article 1"
        assert items[0].url == "http://example.com/1"
        assert items[0].description == "Test description 1"
        assert items[0].published is not None
        assert items[0].published.strftime("%Y-%m-%d %H:%M:%S") == "2024-04-12 10:30:00"

    @patch("requests.get")
    def test_parse_atom_feed(self, mock_get, event_loop_fixture):
        """Test parsing an Atom feed."""
        # Setup mock response
        mock_response = Mock()
        mock_response.content = SAMPLE_ATOM_XML.encode("utf-8")
        mock_get.return_value = mock_response

        # Test parsing
        items = self.parser.parse_feed("http://example.com/feed")

        assert len(items) == 2
        assert items[0].title == "Test Article 1"
        assert items[0].url == "http://example.com/1"
        assert items[0].description == "Test description 1"
        assert items[0].published is not None
        assert items[0].published.strftime("%Y-%m-%d %H:%M:%S") == "2024-04-12 10:30:00"

    @patch("requests.get")
    def test_parse_atom_feed_with_multiple_links(self, mock_get, event_loop_fixture):
        """Test parsing an Atom feed with multiple link elements."""
        # Atom feed with multiple links per entry
        atom_with_multiple_links = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <title>Multiple Links Feed</title>
            <link href="http://example.com" rel="alternate"/>
            <entry>
                <title>Article with Multiple Links</title>
                <link href="http://example.com/alternate" rel="alternate"/>
                <link href="http://example.com/related" rel="related"/>
                <link href="http://example.com/enclosure" rel="enclosure"/>
                <summary>Test description</summary>
                <published>2024-04-12T10:30:00Z</published>
            </entry>
        </feed>
        """
        
        mock_response = Mock()
        mock_response.content = atom_with_multiple_links.encode("utf-8")
        mock_get.return_value = mock_response

        # Test parsing
        items = self.parser.parse_feed("http://example.com/feed")

        assert len(items) == 1
        assert items[0].title == "Article with Multiple Links"
        # Should use the alternate link as the URL
        assert items[0].url == "http://example.com/alternate"
        assert items[0].description == "Test description"

    @patch("requests.get")
    def test_parse_feed_error(self, mock_get, event_loop_fixture):
        """Test parsing a feed with error."""
        mock_get.side_effect = Exception("Failed to fetch feed")

        items = self.parser.parse_feed("http://example.com/feed")
        assert len(items) == 0

    @patch("requests.get")
    def test_parse_malformed_xml(self, mock_get, event_loop_fixture):
        """Test parsing malformed XML."""
        mock_response = Mock()
        mock_response.content = MALFORMED_XML.encode("utf-8")
        mock_get.return_value = mock_response

        # Should not raise an exception, but return empty list
        items = self.parser.parse_feed("http://example.com/malformed")
        assert len(items) == 0

    @patch("requests.get")
    def test_parse_incomplete_rss(self, mock_get, event_loop_fixture):
        """Test parsing RSS with missing elements."""
        mock_response = Mock()
        mock_response.content = INCOMPLETE_RSS_XML.encode("utf-8")
        mock_get.return_value = mock_response

        items = self.parser.parse_feed("http://example.com/incomplete")
        
        # Should still parse items with missing elements
        # Note: The parser may skip items with missing required elements
        assert len(items) > 0
        
        # Check the first item that was successfully parsed
        item = items[0]
        # It should have either a default title or the actual title
        assert item.title in ["No title", "Incomplete Article 2"]
        # URL should be either the actual URL or empty
        if item.title == "No title":
            assert item.url == "http://example.com/incomplete1"
            assert item.description == "Description for incomplete item 1"
            assert item.published is None
        else:
            # This might be the second item if the first was skipped
            assert item.description == "Description for incomplete item 2"
            assert item.published is not None

    @patch("requests.get")
    def test_parse_incomplete_atom(self, mock_get, event_loop_fixture):
        """Test parsing Atom feed with missing elements."""
        mock_response = Mock()
        mock_response.content = INCOMPLETE_ATOM_XML.encode("utf-8")
        mock_get.return_value = mock_response

        items = self.parser.parse_feed("http://example.com/incomplete-atom")
        
        # Should still parse items with missing elements
        # Note: The parser may skip items with missing required elements
        assert len(items) > 0
        
        # Check the first item that was successfully parsed
        item = items[0]
        # It should have either a default title or the actual title
        assert item.title in ["No title", "Incomplete Atom Article 2"]
        
        # Check specific attributes based on which item was parsed
        if item.title == "No title":
            assert item.url == "http://example.com/incomplete1"
            assert item.description is None
            assert item.published is not None
        else:
            # This might be the second item if the first was skipped
            assert item.description == "Summary for incomplete atom item 2"
            assert item.published is None

    @patch("requests.get")
    def test_parse_unusual_dates(self, mock_get, event_loop_fixture):
        """Test parsing feeds with unusual date formats."""
        mock_response = Mock()
        mock_response.content = UNUSUAL_DATES_XML.encode("utf-8")
        mock_get.return_value = mock_response

        items = self.parser.parse_feed("http://example.com/unusual-dates")
        
        assert len(items) == 3
        
        # ISO date format
        assert items[0].title == "Article with ISO Date"
        assert items[0].published is not None
        assert items[0].published.strftime("%Y-%m-%d") == "2024-04-12"
        
        # RFC822 date format
        assert items[1].title == "Article with RFC822 Date"
        assert items[1].published is not None
        assert items[1].published.strftime("%Y-%m-%d") == "2024-04-12"
        
        # Invalid date format
        assert items[2].title == "Article with Invalid Date"
        assert items[2].published is None

    @patch("requests.get")
    def test_network_error_handling(self, mock_get, mock_response, event_loop_fixture):
        """Test handling of network errors."""
        # Test connection error
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        items = self.parser.parse_feed("http://example.com/connection-error")
        assert len(items) == 0
        
        # Test timeout error
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        items = self.parser.parse_feed("http://example.com/timeout")
        assert len(items) == 0
        
        # Test HTTP error
        mock_get.side_effect = requests.exceptions.HTTPError("404 Client Error")
        items = self.parser.parse_feed("http://example.com/http-error")
        assert len(items) == 0

    @patch("requests.get")
    def test_get_new_urls(self, mock_get, event_loop_fixture):
        """Test getting new URLs from feed."""
        # Setup mock response
        mock_response = Mock()
        mock_response.content = SAMPLE_RSS_XML.encode("utf-8")
        mock_get.return_value = mock_response

        # First call should return all items
        items = self.parser.get_new_urls("http://example.com/feed")
        assert len(items) == 2
        assert {item.url for item in items} == {
            "http://example.com/1",
            "http://example.com/2",
        }

        # Second call should return no items (all URLs cached)
        items = self.parser.get_new_urls("http://example.com/feed")
        assert len(items) == 0
        
        # Add a new item to the feed
        updated_rss = SAMPLE_RSS_XML.replace("</channel>", """
        <item>
            <title>Test Article 3</title>
            <link>http://example.com/3</link>
            <description>Test description 3</description>
            <pubDate>Fri, 12 Apr 2024 12:30:00 GMT</pubDate>
        </item>
        </channel>
        """)
        
        mock_response.content = updated_rss.encode("utf-8")
        
        # Third call should return only the new item
        items = self.parser.get_new_urls("http://example.com/feed")
        assert len(items) == 1
        assert items[0].url == "http://example.com/3"
        assert items[0].title == "Test Article 3"

    def test_cache_persistence(self, tmp_path, event_loop_fixture):
        """Test that processed URLs are persisted to cache file."""
        cache_file = tmp_path / "cache.json"
        parser = RSSParser(str(cache_file))

        # Add URLs to processed set
        parser.processed_urls.add("http://example.com/1")
        parser.processed_urls.add("http://example.com/2")
        parser._save_cache()

        # Read cache file directly
        with open(cache_file) as f:
            cached_urls = set(json.load(f))

        assert cached_urls == {"http://example.com/1", "http://example.com/2"}

        # Create new parser instance with same cache file
        new_parser = RSSParser(str(cache_file))
        assert new_parser.processed_urls == {
            "http://example.com/1",
            "http://example.com/2",
        }
        
    def test_cache_save_error_handling(self, tmp_path, event_loop_fixture):
        """Test error handling when saving cache fails."""
        # Create a directory where a file is expected (to cause an error)
        cache_path = tmp_path / "cache_dir"
        cache_path.mkdir()
        
        parser = RSSParser(str(cache_path))
        parser.processed_urls.add("http://example.com/test")
        
        # Should not raise an exception
        parser._save_cache()
        
        # The processed_urls should still be in memory
        assert "http://example.com/test" in parser.processed_urls

    @patch("builtins.open", side_effect=PermissionError("Permission denied"))
    def test_cache_load_permission_error(self, mock_open, tmp_path, event_loop_fixture):
        """Test error handling when loading cache fails due to permissions."""
        cache_file = tmp_path / "permission_denied.json"
        
        # Should not raise an exception
        parser = RSSParser(str(cache_file))
        
        # Should have empty processed_urls
        assert parser.processed_urls == set()

    @patch("requests.get")
    def test_global_parse_rss_feed_function(self, mock_get, mock_response, event_loop_fixture):
        """Test the global parse_rss_feed function."""
        mock_response.content = SAMPLE_RSS_XML.encode("utf-8")
        mock_get.return_value = mock_response
        
        result = parse_rss_feed("http://example.com/feed")
        
        assert isinstance(result, dict)
        assert "title" in result
        assert "feed_url" in result
        assert "entries" in result
        
        assert result["feed_url"] == "http://example.com/feed"
        assert len(result["entries"]) == 2
        
        # Check entry format
        entry = result["entries"][0]
        assert "title" in entry
        assert "link" in entry
        assert "description" in entry
        assert "published" in entry
        
        assert entry["title"] == "Test Article 1"
        assert entry["link"] == "http://example.com/1"

    @patch("requests.get")
    def test_global_parse_rss_feed_error_handling(self, mock_get, event_loop_fixture):
        """Test error handling in the global parse_rss_feed function."""
        mock_get.side_effect = Exception("Test error")
        
        result = parse_rss_feed("http://example.com/error")
        
        assert isinstance(result, dict)
        assert "title" in result
        assert "feed_url" in result
        assert "entries" in result
        
        # The implementation might not include an error field, but should have empty entries
        assert len(result["entries"]) == 0
        assert result["feed_url"] == "http://example.com/error"