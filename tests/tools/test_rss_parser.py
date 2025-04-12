"""
Tests for the RSS Parser tool.
"""
import pytest
from unittest.mock import patch, mock_open, Mock
import json
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

from local_newsifier.tools.rss_parser import RSSParser, RSSItem

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

class TestRSSParser:
    def setup_method(self):
        self.parser = RSSParser()
    
    def test_init_without_cache(self):
        """Test initialization without cache file."""
        parser = RSSParser()
        assert parser.cache_file is None
        assert parser.processed_urls == set()
    
    def test_init_with_cache(self, tmp_path):
        """Test initialization with cache file."""
        cache_file = tmp_path / "test_cache.json"
        urls = ["http://example.com/1", "http://example.com/2"]
        cache_file.write_text(json.dumps(urls))
        
        parser = RSSParser(str(cache_file))
        assert parser.cache_file == str(cache_file)
        assert parser.processed_urls == set(urls)
    
    def test_init_with_invalid_cache(self, tmp_path):
        """Test initialization with invalid cache file."""
        cache_file = tmp_path / "invalid_cache.json"
        cache_file.write_text("invalid json")
        
        parser = RSSParser(str(cache_file))
        assert parser.processed_urls == set()
    
    @patch('requests.get')
    def test_parse_rss_feed(self, mock_get):
        """Test parsing an RSS feed."""
        # Setup mock response
        mock_response = Mock()
        mock_response.content = SAMPLE_RSS_XML.encode('utf-8')
        mock_get.return_value = mock_response
        
        # Test parsing
        items = self.parser.parse_feed('http://example.com/feed')
        
        assert len(items) == 2
        assert items[0].title == 'Test Article 1'
        assert items[0].url == 'http://example.com/1'
        assert items[0].description == 'Test description 1'
        assert items[0].published is not None
        assert items[0].published.strftime('%Y-%m-%d %H:%M:%S') == '2024-04-12 10:30:00'
    
    @patch('requests.get')
    def test_parse_atom_feed(self, mock_get):
        """Test parsing an Atom feed."""
        # Setup mock response
        mock_response = Mock()
        mock_response.content = SAMPLE_ATOM_XML.encode('utf-8')
        mock_get.return_value = mock_response
        
        # Test parsing
        items = self.parser.parse_feed('http://example.com/feed')
        
        assert len(items) == 2
        assert items[0].title == 'Test Article 1'
        assert items[0].url == 'http://example.com/1'
        assert items[0].description == 'Test description 1'
        assert items[0].published is not None
        assert items[0].published.strftime('%Y-%m-%d %H:%M:%S') == '2024-04-12 10:30:00'
    
    @patch('requests.get')
    def test_parse_feed_error(self, mock_get):
        """Test parsing a feed with error."""
        mock_get.side_effect = Exception("Failed to fetch feed")
        
        items = self.parser.parse_feed('http://example.com/feed')
        assert len(items) == 0
    
    @patch('requests.get')
    def test_get_new_urls(self, mock_get):
        """Test getting new URLs from feed."""
        # Setup mock response
        mock_response = Mock()
        mock_response.content = SAMPLE_RSS_XML.encode('utf-8')
        mock_get.return_value = mock_response
        
        # First call should return all items
        items = self.parser.get_new_urls('http://example.com/feed')
        assert len(items) == 2
        assert {item.url for item in items} == {"http://example.com/1", "http://example.com/2"}
        
        # Second call should return no items (all URLs cached)
        items = self.parser.get_new_urls('http://example.com/feed')
        assert len(items) == 0
    
    def test_cache_persistence(self, tmp_path):
        """Test that processed URLs are persisted to cache file."""
        cache_file = tmp_path / "cache.json"
        parser = RSSParser(str(cache_file))
        
        # Add URLs to processed set
        parser.processed_urls.add('http://example.com/1')
        parser.processed_urls.add('http://example.com/2')
        parser._save_cache()
        
        # Read cache file directly
        with open(cache_file) as f:
            cached_urls = set(json.load(f))
        
        assert cached_urls == {'http://example.com/1', 'http://example.com/2'}
        
        # Create new parser instance with same cache file
        new_parser = RSSParser(str(cache_file))
        assert new_parser.processed_urls == {'http://example.com/1', 'http://example.com/2'} 