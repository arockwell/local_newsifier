# Tool Registration and Dependency Injection Patterns

This document provides guidelines for registering tool classes in the dependency injection container, using them consistently throughout the application, and implementing advanced dependency injection patterns.

## Table of Contents
1. [Overview](#overview)
2. [Naming Conventions](#naming-conventions)
3. [Registration Patterns](#registration-patterns)
4. [Using Container-Provided Tools](#using-container-provided-tools)
5. [Advanced Dependency Injection Patterns](#advanced-dependency-injection-patterns)
6. [Testing](#testing)

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

## Advanced Dependency Injection Patterns

As the application evolves, we've implemented more sophisticated dependency injection patterns to handle complex requirements. This section covers these advanced patterns.

### Base/Derived Class Pattern for Flow Components

This pattern separates core functionality from dependency resolution by using a base class for business logic and a derived class for DI integration.

#### Pattern Structure

```
BaseFlowClass  <--- Contains core business logic 
     ^
     |
DerivedFlowClass  <--- Handles DI integration
```

#### Example Implementation

```python
# Base class with core logic
class EntityTrackingFlowBase(Flow):
    """Base class containing the core entity tracking functionality."""
    
    def __init__(
        self, 
        entity_service: Optional[EntityService] = None,
        entity_tracker: Optional[EntityTracker] = None,
        entity_extractor: Optional[EntityExtractor] = None,
        context_analyzer: Optional[ContextAnalyzer] = None,
        entity_resolver: Optional[EntityResolver] = None,
        session: Optional[Session] = None,
        session_factory: Optional[callable] = None
    ):
        """Initialize with optional dependencies.
        
        All dependencies are optional to allow for flexible initialization,
        but core functionality requires them to be provided either directly
        or through a container.
        """
        self.entity_service = entity_service
        self.entity_tracker = entity_tracker
        self.entity_extractor = entity_extractor
        self.context_analyzer = context_analyzer
        self.entity_resolver = entity_resolver
        self.session = session
        self.session_factory = session_factory
    
    def track_entities_in_article(self, article_id: int) -> Dict[str, Any]:
        """Core business logic method."""
        # Implementation using self.entity_service, self.entity_tracker, etc.
        pass

# Derived class for DI integration with fastapi-injectable
@injectable(use_cache=False)
class EntityTrackingFlow(EntityTrackingFlowBase):
    """DI-aware implementation that uses fastapi-injectable."""
    
    def __init__(
        self,
        entity_service: Annotated[EntityService, Depends(get_entity_service)],
        entity_tracker: Annotated[EntityTracker, Depends(get_entity_tracker_tool)],
        entity_extractor: Annotated[EntityExtractor, Depends(get_entity_extractor_tool)],
        context_analyzer: Annotated[ContextAnalyzer, Depends(get_context_analyzer_tool)],
        entity_resolver: Annotated[EntityResolver, Depends(get_entity_resolver_tool)],
        session: Annotated[Session, Depends(get_session)]
    ):
        """Initialize with dependencies from fastapi-injectable.
        
        All parameters are injected through the Depends() mechanism.
        """
        super().__init__(
            entity_service=entity_service,
            entity_tracker=entity_tracker,
            entity_extractor=entity_extractor,
            context_analyzer=context_analyzer,
            entity_resolver=entity_resolver,
            session=session
        )
```

#### Benefits

1. **Separation of Concerns**:
   - Base class focuses on business logic
   - Derived class handles dependency injection

2. **Testability**:
   - Base class can be tested with mock dependencies
   - No need to mock DI framework in tests

3. **Framework Independence**:
   - Core logic isn't tied to a specific DI framework
   - Allows migration between DI systems

4. **Flexibility**:
   - Supports both constructor injection and provider-based DI
   - Works with both DIContainer and fastapi-injectable

### Factory Pattern for Circular Dependencies

When components have circular dependencies, we use a factory pattern to break the dependency cycle.

#### Pattern Structure

```
Component A --> depends on --> Component B
     ^                             |
     |                             v
  Factory <---- depends on --- Component C
```

#### Example Implementation

```python
# Provider function using factory pattern to break circular dependencies
@injectable(use_cache=False)
def get_news_pipeline_flow(
    article_service: Annotated[ArticleService, Depends(get_article_service)],
    entity_service: Annotated[EntityService, Depends(get_entity_service)],
    web_scraper: Annotated[WebScraperTool, Depends(get_web_scraper_tool)],
    file_writer: Annotated[FileWriterTool, Depends(get_file_writer_tool)],
    session: Annotated[Session, Depends(get_session)]
) -> NewsPipelineFlow:
    """Factory function to create a NewsPipelineFlow.
    
    This breaks potential circular dependencies by creating the pipeline_service
    inside the function rather than injecting it.
    """
    # Create dependent service inside the factory function
    from local_newsifier.services.news_pipeline_service import NewsPipelineService
    
    # Create the service with its dependencies
    pipeline_service = NewsPipelineService(
        article_service=article_service, 
        entity_service=entity_service,
        session_factory=lambda: session
    )
    
    # Create and return the flow with the service
    return NewsPipelineFlow(
        article_service=article_service,
        entity_service=entity_service,
        web_scraper=web_scraper,
        file_writer=file_writer,
        session=session,
        pipeline_service=pipeline_service
    )
```

#### Benefits

1. **Resolves Circular Dependencies**:
   - Breaks dependency cycles by creating dependencies on demand
   - Avoids the "chicken and egg" problem

2. **Lazy Initialization**:
   - Components are created only when needed
   - Improves startup performance

3. **Encapsulated Creation Logic**:
   - Complex initialization code is contained in the factory
   - Consumers don't need to know how to create dependencies

4. **Configuration Flexibility**:
   - Factory can create differently configured instances based on context
   - Supports runtime decision-making

### Pattern Combination Strategy

These patterns can be combined for maximum flexibility:

1. Create a base class for core business logic
2. Implement a derived class for DI framework integration  
3. Use factory functions to resolve complex dependency graphs
4. Register the factories in the DI container

This combination allows for:
- Clean separation of business logic from DI framework
- Resolution of circular dependencies
- Testability with simple mocks
- Flexibility to evolve the DI approach over time

## Testing

### Testing Base/Derived Class Pattern

When testing components that use the base/derived class pattern, focus on testing the base class with explicit dependencies:

```python
def test_entity_tracking_flow_base():
    # Create mock dependencies
    mock_entity_service = Mock()
    mock_entity_tracker = Mock()
    mock_entity_extractor = Mock()
    mock_context_analyzer = Mock()
    mock_entity_resolver = Mock()
    
    # Setup expected return values
    mock_entity_service.get_article.return_value = sample_article
    mock_entity_extractor.extract_entities.return_value = sample_entities
    mock_context_analyzer.analyze_contexts.return_value = sample_contexts
    mock_entity_resolver.resolve_entities.return_value = sample_canonical_entities
    mock_entity_tracker.track_entities.return_value = sample_tracking_result
    
    # Create instance of the base class with mock dependencies
    flow = EntityTrackingFlowBase(
        entity_service=mock_entity_service,
        entity_tracker=mock_entity_tracker,
        entity_extractor=mock_entity_extractor,
        context_analyzer=mock_context_analyzer,
        entity_resolver=mock_entity_resolver
    )
    
    # Call the method to test
    result = flow.track_entities_in_article(article_id=123)
    
    # Verify interactions
    mock_entity_service.get_article.assert_called_once_with(123)
    mock_entity_extractor.extract_entities.assert_called_once()
    mock_context_analyzer.analyze_contexts.assert_called_once()
    mock_entity_resolver.resolve_entities.assert_called_once()
    mock_entity_tracker.track_entities.assert_called_once()
    
    # Verify the result
    assert result == sample_tracking_result
```

This approach has several advantages:
- Tests focus on business logic, not DI plumbing
- No need to mock the DI framework
- Tests remain valid even if the DI approach changes
- Clearer test assertions about component behavior

### Testing Factory Functions

For testing components created by factory functions, you can test the factory directly:

```python
def test_news_pipeline_flow_factory():
    # Create mock dependencies
    mock_article_service = Mock()
    mock_entity_service = Mock()
    mock_web_scraper = Mock()
    mock_file_writer = Mock()
    mock_session = Mock()
    
    # When testing a factory, we need to patch the imported class
    with patch("local_newsifier.services.news_pipeline_service.NewsPipelineService") as MockService:
        # Configure the mock service
        mock_service = Mock()
        MockService.return_value = mock_service
        
        # Call the factory function
        flow = get_news_pipeline_flow(
            article_service=mock_article_service,
            entity_service=mock_entity_service,
            web_scraper=mock_web_scraper,
            file_writer=mock_file_writer,
            session=mock_session
        )
        
        # Verify the service was created with correct dependencies
        MockService.assert_called_once_with(
            article_service=mock_article_service,
            entity_service=mock_entity_service,
            session_factory=ANY  # We can't directly compare lambdas
        )
        
        # Verify the flow was created with correct dependencies
        assert flow.article_service == mock_article_service
        assert flow.entity_service == mock_entity_service
        assert flow.web_scraper == mock_web_scraper
        assert flow.file_writer == mock_file_writer
        assert flow.session == mock_session
        assert flow.pipeline_service == mock_service
```

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

### Testing Components with FastAPI-Injectable

When testing components that use fastapi-injectable, you have two options:

#### Option 1: Test Without DI Framework

Test the component directly by providing all dependencies explicitly:

```python
def test_flow_without_di_framework():
    # Create mock dependencies
    mock_service = Mock()
    mock_tool = Mock()
    
    # Create the component with explicit dependencies
    flow = MyFlow(service=mock_service, tool=mock_tool)
    
    # Test the component
    flow.process()
    
    # Verify interactions
    mock_service.do_something.assert_called_once()
    mock_tool.process.assert_called_once()
```

#### Option 2: Test With DI Framework (Advanced)

For integration tests that need to verify the DI setup:

```python
def test_flow_with_di_framework():
    # Create mock providers
    mock_service = Mock()
    mock_tool = Mock()
    
    # Override the provider functions
    with override_provider(get_service, lambda: mock_service):
        with override_provider(get_tool, lambda: mock_tool):
            # Get the component through the DI system
            flow = resolve(MyFlow)
            
            # Test the component
            flow.process()
            
            # Verify interactions
            mock_service.do_something.assert_called_once()
            mock_tool.process.assert_called_once()
```

Note: The `override_provider` and `resolve` functions would need to be implemented as test utilities that interact with the fastapi-injectable system.

## Guidelines for Adding New Tools

When adding a new tool to the system:

1. Implement the tool class with a clear, focused responsibility
2. Follow the naming convention (verb + noun + Tool)
3. Register the tool in the appropriate function in container.py
4. Add both standard (_tool suffix) and backward compatibility registrations
5. Consider using the base/derived class pattern for complex tools
6. Use factory functions to resolve circular dependencies
7. Add appropriate tests for tool registration and functionality
8. Update documentation if the tool introduces new patterns or concepts

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
```

### Using with FastAPI-Injectable

For fastapi-injectable integration, add a provider function in `di/providers.py`:

```python
@injectable(use_cache=False)
def get_text_summarizer_tool(
    # Any dependencies needed by the tool
) -> TextSummarizerTool:
    """Provider function for TextSummarizerTool."""
    return TextSummarizerTool(max_length=100)
```