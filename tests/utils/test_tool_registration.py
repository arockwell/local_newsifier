"""
Tests for tool registration in the DI container.
"""

import pytest
from unittest.mock import MagicMock

from local_newsifier.container import (
    register_core_tools,
    register_analysis_tools,
    register_entity_tools,
    init_container
)


@pytest.fixture
def mock_container():
    """Fixture for a mock DI container."""
    container = MagicMock()
    container.register_factory.return_value = container
    container.register_factory_with_params.return_value = container
    container.get.return_value = MagicMock()
    return container


class TestCoreToolRegistration:
    """Tests for core tool registration in container."""
    
    def test_register_core_tools(self, mock_container, monkeypatch):
        """Test that core tools are registered correctly."""
        # Mock the imports
        mock_web_scraper = MagicMock()
        mock_rss_parser = MagicMock()
        mock_file_writer = MagicMock()
        
        monkeypatch.setattr("local_newsifier.tools.web_scraper.WebScraperTool", mock_web_scraper)
        monkeypatch.setattr("local_newsifier.tools.rss_parser.RSSParser", mock_rss_parser)
        monkeypatch.setattr("local_newsifier.tools.file_writer.FileWriterTool", mock_file_writer)
        
        # Register the tools
        register_core_tools(mock_container)
        
        # Verify tool registrations
        assert mock_container.register_factory_with_params.call_count == 3
        assert mock_container.register_factory.call_count == 3
        
        # Check specific tool registrations
        registration_names = []
        for call in mock_container.register_factory_with_params.call_args_list:
            registration_names.append(call[0][0])
        
        assert "web_scraper_tool" in registration_names
        assert "rss_parser_tool" in registration_names
        assert "file_writer_tool" in registration_names
        
        # Check backward compatibility registrations
        compatibility_names = []
        for call in mock_container.register_factory.call_args_list:
            compatibility_names.append(call[0][0])
            
        assert "web_scraper" in compatibility_names
        assert "rss_parser" in compatibility_names
        assert "file_writer" in compatibility_names


class TestAnalysisToolRegistration:
    """Tests for analysis tool registration in container."""
    
    def test_register_analysis_tools(self, mock_container, monkeypatch):
        """Test that analysis tools are registered correctly."""
        # Mock the imports
        mock_trend_analyzer = MagicMock()
        mock_context_analyzer = MagicMock()
        mock_sentiment_analyzer = MagicMock()
        mock_sentiment_tracker = MagicMock()
        mock_opinion_visualizer = MagicMock()
        mock_trend_reporter = MagicMock()
        mock_analysis_service = MagicMock()
        
        monkeypatch.setattr("local_newsifier.tools.analysis.trend_analyzer.TrendAnalyzer", mock_trend_analyzer)
        monkeypatch.setattr("local_newsifier.tools.analysis.context_analyzer.ContextAnalyzer", mock_context_analyzer)
        monkeypatch.setattr("local_newsifier.tools.sentiment_analyzer.SentimentAnalyzer", mock_sentiment_analyzer)
        monkeypatch.setattr("local_newsifier.tools.sentiment_tracker.SentimentTracker", mock_sentiment_tracker)
        monkeypatch.setattr("local_newsifier.tools.opinion_visualizer.OpinionVisualizerTool", mock_opinion_visualizer)
        monkeypatch.setattr("local_newsifier.tools.trend_reporter.TrendReporter", mock_trend_reporter)
        monkeypatch.setattr("local_newsifier.services.analysis_service.AnalysisService", mock_analysis_service)
        
        # Register the tools
        register_analysis_tools(mock_container)
        
        # Verify registrations
        factory_calls = mock_container.register_factory.call_count
        factory_params_calls = mock_container.register_factory_with_params.call_count
        
        assert factory_calls >= 2  # At least trend_analyzer and context_analyzer
        assert factory_params_calls >= 5  # At least the parameterized tools
        
        # Check specific tool registrations
        all_registrations = []
        for call in mock_container.register_factory.call_args_list:
            all_registrations.append(call[0][0])
        for call in mock_container.register_factory_with_params.call_args_list:
            all_registrations.append(call[0][0])
            
        # Check that all tools are registered
        assert "trend_analyzer_tool" in all_registrations
        assert "context_analyzer_tool" in all_registrations
        assert "sentiment_analyzer_tool" in all_registrations
        assert "sentiment_tracker_tool" in all_registrations
        assert "opinion_visualizer_tool" in all_registrations
        assert "trend_reporter_tool" in all_registrations
        assert "analysis_service" in all_registrations
        
        # Check backward compatibility
        compatibility_names = []
        for call in mock_container.register_factory.call_args_list:
            compatibility_names.append(call[0][0])
            
        assert "trend_analyzer" in compatibility_names
        assert "context_analyzer" in compatibility_names
        assert "sentiment_analyzer" in compatibility_names
        assert "sentiment_tracker" in compatibility_names
        assert "opinion_visualizer" in compatibility_names
        assert "trend_reporter" in compatibility_names


class TestEntityToolRegistration:
    """Tests for entity tool registration in container."""
    
    def test_register_entity_tools(self, mock_container, monkeypatch):
        """Test that entity tools are registered correctly."""
        # Mock the imports
        mock_entity_extractor = MagicMock()
        mock_entity_resolver = MagicMock()
        mock_entity_tracker = MagicMock()
        
        monkeypatch.setattr("local_newsifier.tools.extraction.entity_extractor.EntityExtractor", mock_entity_extractor)
        monkeypatch.setattr("local_newsifier.tools.resolution.entity_resolver.EntityResolver", mock_entity_resolver)
        monkeypatch.setattr("local_newsifier.tools.entity_tracker_service.EntityTracker", mock_entity_tracker)
        
        # Register the tools
        register_entity_tools(mock_container)
        
        # Verify registrations
        assert mock_container.register_factory.call_count == 6  # 3 tools + 3 backward compatibility
        
        # Check specific tool registrations
        registration_names = []
        for call in mock_container.register_factory.call_args_list:
            registration_names.append(call[0][0])
            
        assert "entity_extractor_tool" in registration_names
        assert "entity_resolver_tool" in registration_names
        assert "entity_tracker_tool" in registration_names
        
        # Check backward compatibility
        assert "entity_extractor" in registration_names
        assert "entity_resolver" in registration_names
        assert "entity_tracker" in registration_names


class TestContainerInitialization:
    """Tests for container initialization."""
    
    def test_init_container(self, monkeypatch):
        """Test that the container is properly initialized with all tools registered."""
        # Mock the registration functions
        mock_register_core = MagicMock()
        mock_register_analysis = MagicMock()
        mock_register_entity = MagicMock()
        mock_register_services = MagicMock()
        mock_register_flows = MagicMock()
        
        monkeypatch.setattr("local_newsifier.container.register_core_tools", mock_register_core)
        monkeypatch.setattr("local_newsifier.container.register_analysis_tools", mock_register_analysis)
        monkeypatch.setattr("local_newsifier.container.register_entity_tools", mock_register_entity)
        monkeypatch.setattr("local_newsifier.container.register_services", mock_register_services)
        monkeypatch.setattr("local_newsifier.container.register_flows", mock_register_flows)
        
        # Initialize the container
        container = init_container()
        
        # Verify that all registration functions were called
        assert mock_register_core.call_count == 1
        assert mock_register_analysis.call_count == 1
        assert mock_register_entity.call_count == 1
        assert mock_register_services.call_count == 1
        assert mock_register_flows.call_count == 1
        
        # Verify container object
        assert container is not None
        
        # Verify CRUD modules and other essentials were registered
        assert len(container._services) > 0 or len(container._factories) > 0
