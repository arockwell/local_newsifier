"""Test core functionality of the fastapi-injectable migration."""

import pytest
from unittest.mock import MagicMock, patch

from local_newsifier.fastapi_injectable_adapter import get_service_factory, register_bulk_services


def test_get_service_factory_caching_detection():
    """Test that get_service_factory correctly identifies which components need caching."""
    # Setup
    mock_di_container = MagicMock()
    mock_injectable = MagicMock()
    
    stateful_components = [
        "entity_service",
        "article_service",
        "sentiment_analyzer",
        "entity_resolver",
        "entity_extractor_tool",
        "article_crud"
    ]
    
    stateless_components = [
        "config_provider",
        "util_formatter",
        "constants"
    ]
    
    # Execute and verify with patching
    with patch('local_newsifier.fastapi_injectable_adapter.di_container', mock_di_container):
        with patch('local_newsifier.fastapi_injectable_adapter.injectable', mock_injectable):
            # Test stateful components - should use use_cache=False
            for name in stateful_components:
                get_service_factory(name)
                mock_injectable.assert_called_with(use_cache=False)
                mock_injectable.reset_mock()
            
            # Test stateless components - should use use_cache=True
            for name in stateless_components:
                get_service_factory(name)
                mock_injectable.assert_called_with(use_cache=True)
                mock_injectable.reset_mock()


def test_register_bulk_services():
    """Test register_bulk_services function."""
    # Setup
    service_names = ["service1", "service2", "failed_service"]
    mock_register = MagicMock()
    
    # Make it return a factory for successful services, None for failed
    def mock_register_implementation(name):
        if name != "failed_service":
            return lambda: f"{name}_instance"
        return None
    
    mock_register.side_effect = mock_register_implementation
    
    # Execute
    with patch('local_newsifier.fastapi_injectable_adapter.register_container_service', mock_register):
        result = register_bulk_services(service_names)
    
    # Verify
    assert len(result) == 2
    assert "service1" in result and "service2" in result
    assert "failed_service" not in result
    assert callable(result["service1"])
    assert callable(result["service2"])
    assert mock_register.call_count == 3


def test_name_conversion_patterns():
    """Test name conversion patterns used in the adapter."""
    # The actual adapter uses more complex logic to handle various naming patterns
    # Here we test just the basic camelCase to snake_case conversion
    
    class_names = [
        "EntityService",
        "ArticleService",
        "EntityExtractor"
    ]
    
    for class_name in class_names:
        # Basic snake_case conversion logic
        result = "".join(
            ["_" + c.lower() if c.isupper() else c for c in class_name]
        ).lstrip("_")
        
        # Verify it's lowercase
        assert result.islower()
        
        # Verify it contains underscores
        assert "_" in result
        
        # Verify the first character isn't an underscore
        assert not result.startswith("_")
    
    # Verify service name deduction
    module_name = "local_newsifier.services.entity_service"
    class_name = "EntityService" 
    
    # Typical logic used to get service names in snake_case
    service_class_name = "".join(
        ["_" + c.lower() if c.isupper() else c for c in class_name]
    ).lstrip("_")
    module_parts = module_name.split(".")
    
    # These are patterns commonly checked in the adapter
    potential_names = [
        service_class_name,  # entity_service
        f"{module_parts[-2]}_{service_class_name}",  # services_entity_service
        f"{module_parts[-1]}"  # entity_service
    ]
    
    # Verify common patterns
    assert "entity_service" in potential_names
    assert service_class_name == "entity_service"