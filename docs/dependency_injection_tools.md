# Tool Registration in Dependency Injection Container

This document provides guidelines for registering tool classes in the dependency injection container and using them consistently throughout the application.

## Table of Contents
1. [Overview](#overview)
2. [Naming Conventions](#naming-conventions)
3. [Registration Patterns](#registration-patterns)
4. [Using Container-Provided Tools](#using-container-provided-tools)
5. [Testing](#testing)

## Overview

All tool classes are now registered in the dependency injection container to provide:
- Centralized management of tool instances
- Consistent access patterns
- Configurable initialization
- Clear dependency relationships
- Improved testability

Tools are organized into three main categories:
1. **Core Tools** - Basic utilities like web scraping and file handling
2. **Analysis Tools** - Specialized analysis functionality like trend analysis and sentiment analysis
3. **Entity Tools** - Entity extraction, resolution, and tracking

## Naming Conventions

### Standard Tool Names

Tools registered in the container follow this naming pattern:

- Standard name: `{tool_name}_tool`
- Example: `web_scraper_tool`, `rss_parser_tool`, `trend_analyzer_tool`

### Backward Compatibility

For backward compatibility with existing code, each tool is also registered with a legacy name:

- Legacy name: `{tool_name}` (without the _tool suffix)
- Example: `web_scraper`, `rss_parser`, `trend_analyzer`

This dual registration allows gradual migration to the new naming scheme without breaking existing code.

## Registration Patterns

Tool registration is handled in the `container.py` module, which initializes the DI container and registers all services and dependencies. Tools are registered in three dedicated functions:

### 1. Core Tools Registration

```python
def register_core_tools(container):
    """Register core tool classes in the container."""
    try:
        from local_newsifier.tools.web_scraper import WebScraperTool
        from local_newsifier.tools.rss_parser import RSSParser
        from local_newsifier.tools.file_writer import FileWriterTool
        
        # Register tools with standard names and configurable parameters
        container.register_factory_with_params(
            "web_scraper_tool", 
            lambda c, **kwargs: WebScraperTool(
                user_agent=kwargs.get("user_agent")
            )
        )
        
        # Backward compatibility registration
        container.register_factory(
            "web_scraper", 
            lambda c: c.get("web_scraper_tool")
        )
        
        # More tool registrations...
    except ImportError as e:
        # Log error but continue initialization
        print(f"Error registering core tools: {e}")
```

### 2. Analysis Tools Registration

```python
def register_analysis_tools(container):
    """Register analysis tools in the container."""
    try:
        # Import and register trend analysis, sentiment analysis, and other tools
        from local_newsifier.tools.analysis.trend_analyzer import TrendAnalyzer
        # More imports...
        
        container.register_factory(
            "trend_analyzer_tool", 
            lambda c: TrendAnalyzer()
        )
        
        # Tools with session dependency
        container.register_factory_with_params(
            "sentiment_analyzer_tool", 
            lambda c, **kwargs: SentimentAnalysisTool(
                session=kwargs.get("session")
            )
        )
        
        # Backward compatibility...
    except ImportError as e:
        # Log error but continue initialization
        print(f"Error registering analysis tools: {e}")
```

### 3. Entity Tools Registration

```python
def register_entity_tools(container):
    """Register entity-related tools in the container."""
    try:
        # Import and register entity extraction, resolution, and tracking tools
        from local_newsifier.tools.extraction.entity_extractor import EntityExtractor
        # More imports...
        
        container.register_factory(
            "entity_extractor_tool", 
            lambda c: EntityExtractor()
        )
        
        # Backward compatibility...
    except ImportError as e:
        # Log error but continue initialization
        print(f"Error registering entity tools: {e}")
```

## Tool Registration Strategies

### Simple Factory Registration

For tools without dependencies or configuration options:

```python
container.register_factory(
    "tool_name_tool", 
    lambda c: ToolClass()
)
```

### Parameterized Factory Registration

For tools with configuration options or dependencies:

```python
container.register_factory_with_params(
    "tool_name_tool", 
    lambda c, **kwargs: ToolClass(
        param1=kwargs.get("param1", default_value),
        param2=kwargs.get("param2")
    )
)
```

### Dependency Injection Configuration

For tools that require other services:

```python
container.register_factory(
    "tool_name_tool", 
    lambda c: ToolClass(
        dependency1=c.get("other_service"),
        dependency2=c.get("another_service")
    )
)
```

## Using Container-Provided Tools

### Direct Access Pattern

For simple tool access without parameters:

```python
from local_newsifier.container import container

def some_function():
    # Get a tool instance
    web_scraper = container.get("web_scraper_tool")
    
    # Use the tool
    result = web_scraper.scrape_url("https://example.com")
```

### Parameterized Access Pattern

For tools that need runtime configuration:

```python
from local_newsifier.container import container

def some_function():
    # Get a tool instance with specific parameters
    file_writer = container.get("file_writer_tool", output_dir="custom_output")
    
    # Use the tool
    file_writer.save(state)
```

### Service Constructor Injection Pattern

The preferred pattern is to accept dependencies in service constructors:

```python
class NewsService:
    def __init__(
        self, 
        web_scraper=None, 
        rss_parser=None,
        container=None
    ):
        self.container = container
        
        # Prefer passed dependencies
        self.web_scraper = web_scraper
        self.rss_parser = rss_parser
        
    def _ensure_dependencies(self):
        """Ensure all dependencies are available."""
        if self.web_scraper is None and self.container:
            self.web_scraper = self.container.get("web_scraper_tool")
            
        if self.rss_parser is None and self.container:
            self.rss_parser = self.container.get("rss_parser_tool")
```

### Constructor Registration Pattern

When registering services that use tools:

```python
# Register a service that uses tools
container.register_factory(
    "news_service", 
    lambda c: NewsService(
        web_scraper=c.get("web_scraper_tool"),
        rss_parser=c.get("rss_parser_tool"),
        container=c  # For lazy resolution of other dependencies
    )
)
```

## Testing

### Mocking Container-Provided Tools

When testing code that uses container-provided tools:

```python
@patch("local_newsifier.container.container.get")
def test_function_with_container_tools(mock_container_get):
    # Setup the mock
    mock_tool = Mock()
    mock_tool.some_method.return_value = expected_result
    
    # Configure the mock to return our mock tool when requested
    mock_container_get.side_effect = lambda name, **kwargs: {
        "tool_name_tool": mock_tool
    }.get(name)
    
    # Call the function under test
    result = function_to_test()
    
    # Assertions
    mock_container_get.assert_called_with("tool_name_tool")
    mock_tool.some_method.assert_called_once()
    assert result == expected_result
```

### Testing Services with Container Injection

When testing services that use the container:

```python
def test_service_with_container():
    # Create a mock container
    mock_container = Mock()
    mock_tool = Mock()
    
    # Configure the mock container
    mock_container.get.side_effect = lambda name, **kwargs: {
        "tool_name_tool": mock_tool
    }.get(name)
    
    # Create the service with the mock container
    service = MyService(container=mock_container)
    
    # Call method that uses a tool
    service.method_that_needs_tool()
    
    # Verify
    mock_container.get.assert_called_with("tool_name_tool")
    mock_tool.some_method.assert_called_once()
```

## Guidelines for Adding New Tools

When adding a new tool to the system:

1. Implement the tool class with a clear, focused responsibility
2. Follow the naming convention (verb + noun + Tool)
3. Register the tool in the appropriate function in container.py
4. Add both standard (_tool suffix) and backward compatibility registrations
5. Add appropriate tests for tool registration
6. Update documentation if the tool introduces new patterns or concepts

Example of adding a new tool:

```python
# 1. Implement the tool
# in local_newsifier/tools/text_summarizer.py
class TextSummarizerTool:
    def __init__(self, max_length=100):
        self.max_length = max_length
        
    def summarize(self, text):
        # Implementation...
        return summary

# 2. Register the tool in container.py
from local_newsifier.tools.text_summarizer import TextSummarizerTool

# In register_analysis_tools function:
container.register_factory_with_params(
    "text_summarizer_tool",
    lambda c, **kwargs: TextSummarizerTool(
        max_length=kwargs.get("max_length", 100)
    )
)

# Backward compatibility
container.register_factory(
    "text_summarizer",
    lambda c: c.get("text_summarizer_tool")
)

# 3. Add tests in tests/utils/test_tool_registration.py
