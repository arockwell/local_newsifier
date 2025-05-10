"""Test example for the conditional decorator pattern implementation.

This file demonstrates various techniques for testing components
that use the conditional decorator pattern to avoid event loop issues.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

# Import the fixture for event loop handling
from tests.fixtures.event_loop import event_loop_fixture

# Import the CI skip decorator
from tests.ci_skip_config import ci_skip_injectable

# Import the component to test
from docs.examples.conditional_decorator_example import DataProcessorTool


class TestDataProcessorToolBasic:
    """Basic tests for DataProcessorTool using direct instantiation.
    
    These tests don't require the event_loop_fixture because they use
    direct instantiation and don't interact with fastapi-injectable.
    """
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return Mock()
    
    @pytest.fixture
    def processor(self, mock_session):
        """Create a DataProcessorTool instance with mocked dependencies."""
        return DataProcessorTool(session=mock_session)
    
    def test_process_data_with_session(self, processor, mock_session):
        """Test processing data with a session provided."""
        # Arrange
        test_data = {"key": "value"}
        
        # Act
        results = processor.process_data(test_data)
        
        # Assert
        assert isinstance(results, list)
        # Additional assertions based on expected behavior
    
    def test_process_data_without_session(self):
        """Test processing data without a session."""
        # Arrange
        processor = DataProcessorTool()  # No session provided
        test_data = {"key": "value"}
        
        # Act
        results = processor.process_data(test_data)
        
        # Assert
        assert isinstance(results, list)
        # Additional assertions based on expected behavior
    
    def test_save_results_with_session(self, processor, mock_session):
        """Test saving results with a session."""
        # Arrange
        test_results = [{"result": "value"}]
        
        # Act
        success = processor.save_results(test_results)
        
        # Assert
        assert success is True
    
    def test_save_results_without_session(self):
        """Test saving results without a session should fail."""
        # Arrange
        processor = DataProcessorTool()  # No session provided
        test_results = [{"result": "value"}]
        
        # Act
        success = processor.save_results(test_results)
        
        # Assert
        assert success is False


@ci_skip_injectable
class TestDataProcessorToolAdvanced:
    """Advanced tests for DataProcessorTool that might require event loop handling.
    
    These tests demonstrate techniques for handling event loop issues
    when testing components that use the injectable pattern.
    
    The entire class is decorated with @ci_skip_injectable to avoid
    running these tests in CI environments where they might fail due
    to event loop issues.
    """
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return Mock()
    
    def test_container_fallback(self, mock_session, event_loop_fixture):
        """Test the container fallback mechanism for getting dependencies."""
        # Arrange
        mock_container = Mock()
        session_factory_mock = Mock(return_value=mock_session)
        mock_container.get.return_value = session_factory_mock
        
        # Create processor with container but no session
        processor = DataProcessorTool(container=mock_container)
        
        # Act
        processor.process_data({"key": "value"})
        
        # Assert
        mock_container.get.assert_called_with("session_factory")
    
    def test_set_container(self, mock_session, event_loop_fixture):
        """Test setting the container after initialization."""
        # Arrange
        processor = DataProcessorTool()  # No dependencies
        
        mock_container = Mock()
        session_factory_mock = Mock(return_value=mock_session)
        mock_container.get.return_value = session_factory_mock
        
        # Act
        processor.set_container(mock_container)
        processor.process_data({"key": "value"})
        
        # Assert
        mock_container.get.assert_called_with("session_factory")
    
    def test_session_override(self, mock_session, event_loop_fixture):
        """Test providing a session override to a method."""
        # Arrange
        processor = DataProcessorTool()  # No dependencies
        override_session = Mock()
        
        # Act
        processor.process_data({"key": "value"}, session=override_session)
        
        # The method should use the override session
        # Additional assertions based on expected behavior


class TestDataProcessorToolWithMockedInjectable:
    """Tests that mock the injectable decorator to avoid event loop issues.
    
    These tests demonstrate how to mock the injectable decorator
    to test injectable behavior without requiring an event loop.
    """
    
    @pytest.fixture
    def mock_injectable(self):
        """Create a mock injectable decorator."""
        mock_injectable = MagicMock()
        
        # Create a simple wrapper function
        def mock_decorator(use_cache=True):
            def wrapper(cls):
                # Just return the class unmodified
                cls.__injectable_config = {"use_cache": use_cache}
                return cls
            return wrapper
        
        mock_injectable.side_effect = mock_decorator
        return mock_injectable
    
    def test_with_mocked_injectable(self, mock_injectable):
        """Test with a mocked injectable decorator."""
        # Patch the injectable decorator
        with patch('fastapi_injectable.injectable', mock_injectable):
            # Import the module again to apply the mock
            import importlib
            importlib.reload(__import__('docs.examples.conditional_decorator_example'))
            
            # Now we can create an instance normally
            from docs.examples.conditional_decorator_example import DataProcessorTool
            processor = DataProcessorTool()
            
            # Test normal functionality
            results = processor.process_data({"key": "value"})
            assert isinstance(results, list)
            
            # Verify our mock decorator was applied correctly
            mock_injectable.assert_called_with(use_cache=False)


class TestDataProcessorToolTestingStrategies:
    """Demonstrates different strategies for testing injectable components.
    
    This class shows various approaches to testing components that
    use the injectable pattern, with a focus on handling event loop issues.
    """
    
    def test_with_direct_instantiation(self):
        """Strategy 1: Direct instantiation with mock dependencies.
        
        This is the simplest and most reliable approach, as it bypasses
        dependency injection entirely.
        """
        # Create mock dependencies
        mock_session = Mock()
        
        # Create component directly
        processor = DataProcessorTool(session=mock_session)
        
        # Test the component
        results = processor.process_data({"key": "value"})
        assert isinstance(results, list)
    
    @ci_skip_injectable
    def test_with_event_loop_fixture(self, event_loop_fixture):
        """Strategy 2: Use event_loop_fixture for components requiring injection.
        
        This approach is necessary when testing components that must
        use the injectable system directly.
        """
        # Create component (could use injection in a real test)
        processor = DataProcessorTool()
        
        # Test the component
        results = processor.process_data({"key": "value"})
        assert isinstance(results, list)
    
    def test_with_monkeypatch(self, monkeypatch):
        """Strategy 3: Monkeypatch the injectable system to avoid event loop issues.
        
        This approach patches the injectable system to return predetermined
        values, avoiding the need for an event loop.
        """
        # Create mock dependencies
        mock_session = Mock()
        
        # Mock the injectable dependency
        monkeypatch.setattr(
            "docs.examples.conditional_decorator_example.get_session",
            lambda: mock_session
        )
        
        # Create component using normal instantiation
        processor = DataProcessorTool()
        
        # Test the component
        results = processor.process_data({"key": "value"})
        assert isinstance(results, list)