"""Test script for verifying injectable service changes."""

import unittest
from unittest.mock import MagicMock
from datetime import datetime

class TestArticleService(unittest.TestCase):
    def test_article_service_init(self):
        """Test that ArticleService correctly initializes with dependencies."""
        from local_newsifier.services.article_service import ArticleService

        # Create mocks
        mock_article_crud = MagicMock()
        mock_analysis_result_crud = MagicMock()
        mock_entity_service = MagicMock()
        mock_session_factory = MagicMock()

        # Create service
        service = ArticleService(
            article_crud=mock_article_crud,
            analysis_result_crud=mock_analysis_result_crud,
            entity_service=mock_entity_service,
            session_factory=mock_session_factory
        )

        # Verify dependencies were correctly assigned
        self.assertEqual(service.article_crud, mock_article_crud)
        self.assertEqual(service.analysis_result_crud, mock_analysis_result_crud)
        self.assertEqual(service.entity_service, mock_entity_service)
        self.assertEqual(service.session_factory, mock_session_factory)
        
        # Verify service is injectable
        from fastapi_injectable import injectable
        self.assertTrue(hasattr(ArticleService, "__injectable__"))

class TestEntityService(unittest.TestCase):
    def test_entity_service_init(self):
        """Test that EntityService correctly initializes with dependencies."""
        from local_newsifier.services.entity_service import EntityService

        # Create mocks
        mock_entity_crud = MagicMock()
        mock_canonical_entity_crud = MagicMock()
        mock_entity_mention_context_crud = MagicMock()
        mock_entity_profile_crud = MagicMock()
        mock_article_crud = MagicMock()
        mock_entity_extractor = MagicMock()
        mock_context_analyzer = MagicMock()
        mock_entity_resolver = MagicMock()
        mock_session_factory = MagicMock()

        # Create service
        service = EntityService(
            entity_crud=mock_entity_crud,
            canonical_entity_crud=mock_canonical_entity_crud,
            entity_mention_context_crud=mock_entity_mention_context_crud,
            entity_profile_crud=mock_entity_profile_crud,
            article_crud=mock_article_crud,
            entity_extractor=mock_entity_extractor,
            context_analyzer=mock_context_analyzer,
            entity_resolver=mock_entity_resolver,
            session_factory=mock_session_factory
        )

        # Verify dependencies were correctly assigned
        self.assertEqual(service.entity_crud, mock_entity_crud)
        self.assertEqual(service.canonical_entity_crud, mock_canonical_entity_crud)
        self.assertEqual(service.entity_mention_context_crud, mock_entity_mention_context_crud)
        self.assertEqual(service.entity_profile_crud, mock_entity_profile_crud)
        self.assertEqual(service.article_crud, mock_article_crud)
        self.assertEqual(service.entity_extractor, mock_entity_extractor)
        self.assertEqual(service.context_analyzer, mock_context_analyzer)
        self.assertEqual(service.entity_resolver, mock_entity_resolver)
        self.assertEqual(service.session_factory, mock_session_factory)
        
        # Verify service is injectable
        from fastapi_injectable import injectable
        self.assertTrue(hasattr(EntityService, "__injectable__"))

class TestRSSFeedService(unittest.TestCase):
    def test_rss_feed_service_init(self):
        """Test that RSSFeedService correctly initializes with dependencies."""
        from local_newsifier.services.rss_feed_service import RSSFeedService

        # Create mocks
        mock_rss_feed_crud = MagicMock()
        mock_feed_processing_log_crud = MagicMock()
        mock_article_service = MagicMock()
        mock_session_factory = MagicMock()

        # Create service
        service = RSSFeedService(
            rss_feed_crud=mock_rss_feed_crud,
            feed_processing_log_crud=mock_feed_processing_log_crud,
            article_service=mock_article_service,
            session_factory=mock_session_factory
        )

        # Verify dependencies were correctly assigned
        self.assertEqual(service.rss_feed_crud, mock_rss_feed_crud)
        self.assertEqual(service.feed_processing_log_crud, mock_feed_processing_log_crud)
        self.assertEqual(service.article_service, mock_article_service)
        self.assertEqual(service.session_factory, mock_session_factory)
        
        # Verify service is injectable
        from fastapi_injectable import injectable
        self.assertTrue(hasattr(RSSFeedService, "__injectable__"))

class TestAnalysisService(unittest.TestCase):
    def test_analysis_service_init(self):
        """Test that AnalysisService correctly initializes with dependencies."""
        from local_newsifier.services.analysis_service import AnalysisService

        # Create mocks
        mock_analysis_result_crud = MagicMock()
        mock_article_crud = MagicMock()
        mock_entity_crud = MagicMock()
        mock_session_factory = MagicMock()

        # Create service
        service = AnalysisService(
            analysis_result_crud=mock_analysis_result_crud,
            article_crud=mock_article_crud,
            entity_crud=mock_entity_crud,
            session_factory=mock_session_factory
        )

        # Verify dependencies were correctly assigned
        self.assertEqual(service.analysis_result_crud, mock_analysis_result_crud)
        self.assertEqual(service.article_crud, mock_article_crud)
        self.assertEqual(service.entity_crud, mock_entity_crud)
        self.assertEqual(service.session_factory, mock_session_factory)
        
        # Verify service is injectable
        from fastapi_injectable import injectable
        self.assertTrue(hasattr(AnalysisService, "__injectable__"))

class TestProviders(unittest.TestCase):
    def test_provider_functions(self):
        """Test that provider functions are correctly defined."""
        from local_newsifier.di.providers import (
            get_article_service,
            get_entity_service,
            get_rss_feed_service,
            get_analysis_service,
        )
        
        # Verify providers have injectable decorator
        from fastapi_injectable import injectable
        self.assertTrue(hasattr(get_article_service, "__injectable__"))
        self.assertTrue(hasattr(get_entity_service, "__injectable__"))
        self.assertTrue(hasattr(get_rss_feed_service, "__injectable__"))
        self.assertTrue(hasattr(get_analysis_service, "__injectable__"))

if __name__ == "__main__":
    unittest.main()