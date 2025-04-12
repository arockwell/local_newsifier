"""
Tests for the RSS Parser tool.
"""
import pytest
from unittest.mock import patch, mock_open
import json
from datetime import datetime
from pathlib import Path

from local_newsifier.tools.rss_parser import RSSParser, RSSItem

# Mock feed data that matches feedparser's output structure
SAMPLE_FEED = {
    'feed': {},  # Feed metadata
    'entries': [
        {
            'title': 'Test Article 1',
            'link': 'http://example.com/1',
            'description': 'Test description 1',
            'published_parsed': (2024, 4, 12, 10, 30, 0, 0, 0, 0)
        },
        {
            'title': 'Test Article 2',
            'link': 'http://example.com/2',
            'description': 'Test description 2',
            'published_parsed': (2024, 4, 12, 11, 30, 0, 0, 0, 0)
        }
    ],
    'bozo': 0,  # No errors in feed
    'status': 200,  # HTTP status
    'encoding': 'utf-8'
}

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
    
    @patch('feedparser.parse')
    def test_parse_feed(self, mock_parse):
        """Test parsing a feed."""
        # Setup mock
        mock_parse.return_value = SAMPLE_FEED
        
        # Test parsing
        items = self.parser.parse_feed('http://example.com/feed')
        
        assert len(items) == 2
        assert items[0].title == 'Test Article 1'
        assert items[0].url == 'http://example.com/1'
        assert items[0].description == 'Test description 1'
        assert items[0].published == datetime(2024, 4, 12, 10, 30, 0)
    
    @patch('feedparser.parse')
    def test_parse_feed_error(self, mock_parse):
        """Test parsing a feed with error."""
        mock_parse.side_effect = Exception("Failed to parse feed")
        
        items = self.parser.parse_feed('http://example.com/feed')
        assert len(items) == 0
    
    @patch('feedparser.parse')
    def test_get_new_urls(self, mock_parse):
        """Test getting new URLs from feed."""
        # Setup mock
        mock_parse.return_value = SAMPLE_FEED
        
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