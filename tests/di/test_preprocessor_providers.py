"""Tests for article preprocessor dependency injection providers."""

import pytest
from unittest.mock import patch

from fastapi_injectable import Injected, clear_cache

from local_newsifier.tools.preprocessing.content_cleaner import ContentCleaner
from local_newsifier.tools.preprocessing.content_extractor import ContentExtractor
from local_newsifier.tools.preprocessing.metadata_enhancer import MetadataEnhancer
from local_newsifier.tools.preprocessing.article_preprocessor import ArticlePreprocessor
from local_newsifier.di.providers import (
    get_content_cleaner_config,
    get_content_cleaner,
    get_content_extractor_config,
    get_content_extractor,
    get_metadata_enhancer_config,
    get_metadata_enhancer,
    get_article_preprocessor
)


class TestPreprocessorProviders:
    """Tests for the article preprocessor dependency injection providers."""
    
    def setup_method(self):
        """Set up before each test method."""
        # Clear the injection cache before each test
        clear_cache()
    
    def test_get_content_cleaner_config(self):
        """Test the content cleaner configuration provider."""
        config = get_content_cleaner_config()
        
        assert isinstance(config, dict)
        assert "remove_boilerplate" in config
        assert "normalize_whitespace" in config
        assert "handle_special_chars" in config
        assert "remove_duplicates" in config
        
        # Check default values
        assert config["remove_boilerplate"] is True
        assert config["normalize_whitespace"] is True
        assert config["handle_special_chars"] is True
        assert config["remove_duplicates"] is True
    
    def test_get_content_cleaner(self):
        """Test the content cleaner provider."""
        with patch("local_newsifier.di.providers.get_content_cleaner_config") as mock_config:
            mock_config.return_value = {
                "remove_boilerplate": False,
                "normalize_whitespace": True,
                "handle_special_chars": True,
                "remove_duplicates": False
            }
            
            cleaner = Injected(get_content_cleaner)
            
            assert isinstance(cleaner, ContentCleaner)
            assert cleaner.remove_boilerplate is False
            assert cleaner.normalize_whitespace is True
            assert cleaner.handle_special_chars is True
            assert cleaner.remove_duplicates is False
    
    def test_get_content_extractor_config(self):
        """Test the content extractor configuration provider."""
        config = get_content_extractor_config()
        
        assert isinstance(config, dict)
        assert "extract_images" in config
        assert "extract_links" in config
        assert "preserve_formatting" in config
        assert "extract_lists" in config
        assert "extract_quotes" in config
        
        # Check default values
        assert config["extract_images"] is True
        assert config["extract_links"] is True
        assert config["preserve_formatting"] is True
        assert config["extract_lists"] is True
        assert config["extract_quotes"] is True
    
    def test_get_content_extractor(self):
        """Test the content extractor provider."""
        with patch("local_newsifier.di.providers.get_content_extractor_config") as mock_config:
            mock_config.return_value = {
                "extract_images": False,
                "extract_links": True,
                "preserve_formatting": True,
                "extract_lists": False,
                "extract_quotes": True
            }
            
            extractor = Injected(get_content_extractor)
            
            assert isinstance(extractor, ContentExtractor)
            assert extractor.extract_images is False
            assert extractor.extract_links is True
            assert extractor.preserve_formatting is True
            assert extractor.extract_lists is False
            assert extractor.extract_quotes is True
    
    def test_get_metadata_enhancer_config(self):
        """Test the metadata enhancer configuration provider."""
        config = get_metadata_enhancer_config()
        
        assert isinstance(config, dict)
        assert "extract_date" in config
        assert "extract_categories" in config
        assert "extract_locations" in config
        assert "detect_language" in config
        assert "spacy_model" in config
        
        # Check default values
        assert config["extract_date"] is True
        assert config["extract_categories"] is True
        assert config["extract_locations"] is True
        assert config["detect_language"] is True
        assert config["spacy_model"] == "en_core_web_sm"
    
    def test_get_metadata_enhancer(self):
        """Test the metadata enhancer provider."""
        with patch("local_newsifier.di.providers.get_metadata_enhancer_config") as mock_config:
            mock_config.return_value = {
                "extract_date": True,
                "extract_categories": False,
                "extract_locations": True,
                "detect_language": False,
                "spacy_model": "en_core_web_sm"
            }
            
            enhancer = Injected(get_metadata_enhancer)
            
            assert isinstance(enhancer, MetadataEnhancer)
            assert enhancer.extract_date is True
            assert enhancer.extract_categories is False
            assert enhancer.extract_locations is True
            assert enhancer.detect_language is False
    
    def test_get_article_preprocessor(self):
        """Test the article preprocessor provider."""
        # Mock the component providers
        with patch("local_newsifier.di.providers.get_content_cleaner") as mock_cleaner, \
             patch("local_newsifier.di.providers.get_content_extractor") as mock_extractor, \
             patch("local_newsifier.di.providers.get_metadata_enhancer") as mock_enhancer:
            
            # Create mock instances
            mock_cleaner.return_value = ContentCleaner()
            mock_extractor.return_value = ContentExtractor()
            mock_enhancer.return_value = MetadataEnhancer()
            
            # Get the preprocessor
            preprocessor = Injected(get_article_preprocessor)
            
            # Check that the preprocessor was created correctly
            assert isinstance(preprocessor, ArticlePreprocessor)
            assert isinstance(preprocessor.content_cleaner, ContentCleaner)
            assert isinstance(preprocessor.content_extractor, ContentExtractor)
            assert isinstance(preprocessor.metadata_enhancer, MetadataEnhancer)