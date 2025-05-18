"""Tests for article preprocessor dependency injection providers."""

import pytest
from unittest.mock import patch

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
        # Test the provider directly 
        config = get_content_cleaner_config()
        cleaner = ContentCleaner(
            remove_boilerplate=config["remove_boilerplate"],
            normalize_whitespace=config["normalize_whitespace"],
            handle_special_chars=config["handle_special_chars"],
            remove_duplicates=config["remove_duplicates"]
        )
        
        assert isinstance(cleaner, ContentCleaner)
        assert cleaner.remove_boilerplate is True  # Default value
        assert cleaner.normalize_whitespace is True  # Default value
        assert cleaner.handle_special_chars is True  # Default value
        assert cleaner.remove_duplicates is True  # Default value
    
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
        # Test the provider directly
        config = get_content_extractor_config()
        extractor = ContentExtractor(
            extract_images=config["extract_images"],
            extract_links=config["extract_links"],
            preserve_formatting=config["preserve_formatting"],
            extract_lists=config["extract_lists"],
            extract_quotes=config["extract_quotes"]
        )
        
        assert isinstance(extractor, ContentExtractor)
        assert extractor.extract_images is True  # Default value
        assert extractor.extract_links is True  # Default value
        assert extractor.preserve_formatting is True  # Default value
        assert extractor.extract_lists is True  # Default value
        assert extractor.extract_quotes is True  # Default value
    
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
        # Test the provider directly
        config = get_metadata_enhancer_config()
        enhancer = MetadataEnhancer(
            extract_date=config["extract_date"],
            extract_categories=config["extract_categories"],
            extract_locations=config["extract_locations"],
            detect_language=config["detect_language"],
            spacy_model=config["spacy_model"]
        )
        
        assert isinstance(enhancer, MetadataEnhancer)
        assert enhancer.extract_date is True  # Default value
        assert enhancer.extract_categories is True  # Default value
        assert enhancer.extract_locations is True  # Default value
        assert enhancer.detect_language is True  # Default value
    
    def test_get_article_preprocessor(self):
        """Test the article preprocessor provider."""
        # Create the components directly
        cleaner = ContentCleaner()
        extractor = ContentExtractor()
        enhancer = MetadataEnhancer()
        
        # Create the preprocessor directly
        preprocessor = ArticlePreprocessor(
            content_cleaner=cleaner,
            content_extractor=extractor,
            metadata_enhancer=enhancer
        )
        
        # Check that the preprocessor was created correctly
        assert isinstance(preprocessor, ArticlePreprocessor)
        assert isinstance(preprocessor.content_cleaner, ContentCleaner)
        assert isinstance(preprocessor.content_extractor, ContentExtractor)
        assert isinstance(preprocessor.metadata_enhancer, MetadataEnhancer)