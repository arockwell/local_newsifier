# Local Newsifier Tools Guide

## Overview
The tools module contains utility classes that perform specific processing tasks without direct database dependencies. Tools focus on data processing, analysis, and transformation.

## Key Tool Categories

### Extraction Tools
- **EntityExtractor**: Extracts named entities from text using spaCy
- Located in `tools/extraction/entity_extractor.py`

### Resolution Tools
- **EntityResolver**: Resolves similar entities to canonical forms
- Located in `tools/resolution/entity_resolver.py`

### Analysis Tools
- **TrendAnalyzer**: Analyzes keyword trends in headlines
- **ContextAnalyzer**: Analyzes context around entity mentions
- Located in `tools/analysis/`

### Processing Tools
- **WebScraper**: Fetches web content from URLs
- **RSSParser**: Parses RSS feeds to extract articles
- **SentimentAnalyzer**: Analyzes sentiment in text
- **SentimentTracker**: Tracks sentiment over time

### Output Tools
- **FileWriter**: Writes output to files in various formats
- **TrendReporter**: Generates reports on trends
- **OpinionVisualizer**: Visualizes opinion data

## Common Tool Patterns

### Tool Initialization
Tools accept external dependencies through the constructor:

```python
class EntityExtractor:
    def __init__(self, nlp=None):
        """Initialize the entity extractor.
        
        Args:
            nlp: Optional spaCy model. If not provided, one will be loaded.
        """
        self.nlp = nlp or spacy.load("en_core_web_lg")
        
    def extract_entities(self, text):
        """Extract entities from the given text."""
        doc = self.nlp(text)
        entities = []
        
        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "entity_type": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
                "confidence": 1.0
            })
            
        return entities
```

### Dependency Loading
Tools load dependencies lazily to avoid startup overhead:

```python
def _ensure_nlp_model(self):
    """Ensure the NLP model is loaded."""
    if self.nlp is None:
        try:
            self.nlp = spacy.load("en_core_web_lg")
        except OSError:
            # Download the model if not available
            download_command = "python -m spacy download en_core_web_lg"
            print(f"Model not found. Please run: {download_command}")
            raise
```

### Container-based Dependencies
Tools may get dependencies from the DI container:

```python
def _ensure_dependencies(self):
    """Ensure all dependencies are available."""
    if self.web_scraper is None and self.container:
        self.web_scraper = self.container.get("web_scraper_tool")
```

### Input Validation
Tools validate inputs before processing:

```python
def analyze_sentiment(self, text):
    """Analyze sentiment in the given text.
    
    Args:
        text: The text to analyze
        
    Returns:
        Dict with sentiment scores
        
    Raises:
        ValueError: If text is empty or None
    """
    if not text:
        raise ValueError("Text cannot be empty")
        
    # Analysis logic...
```

### Error Handling
Tools handle errors gracefully and provide clear messages:

```python
def fetch_content(self, url):
    """Fetch content from the given URL.
    
    Args:
        url: The URL to fetch
        
    Returns:
        The fetched content
        
    Raises:
        ConnectionError: If the URL cannot be accessed
        ValueError: If the URL is invalid
    """
    try:
        # Validate URL
        if not validators.url(url):
            raise ValueError(f"Invalid URL: {url}")
            
        response = requests.get(url, headers={"User-Agent": self.user_agent})
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        raise ConnectionError(f"Failed to fetch URL {url}: {str(e)}")
```

### Caching
Tools may implement caching for efficiency:

```python
class TrendAnalyzer:
    def __init__(self):
        self._cache = {}
        
    def analyze_trends(self, data, key=None):
        """Analyze trends in the data.
        
        Args:
            data: The data to analyze
            key: Optional cache key
            
        Returns:
            Trend analysis results
        """
        if key and key in self._cache:
            return self._cache[key]
            
        # Analysis logic...
        result = self._perform_analysis(data)
        
        if key:
            self._cache[key] = result
            
        return result
```

## Integration with Services

Tools are typically not used directly but are wrapped by services:

```python
# In a service
def analyze_entity_sentiment(self, entity_id):
    with self.session_factory() as session:
        entity = self.entity_crud.get(session, entity_id)
        if not entity:
            raise ValueError(f"Entity not found: {entity_id}")
            
        # Get the sentiment analyzer tool
        sentiment_analyzer = self.container.get("sentiment_analyzer_tool")
        
        # Analyze sentiment
        context = entity.sentence_context or ""
        sentiment = sentiment_analyzer.analyze_sentiment(context)
        
        # Save results
        # ...
        
        return sentiment
```

## Tool Registration in Container

Tools are registered in the DI container in standardized functions:

```python
def register_analysis_tools(container):
    """Register analysis tools in the container."""
    try:
        from local_newsifier.tools.analysis.trend_analyzer import TrendAnalyzer
        from local_newsifier.tools.analysis.context_analyzer import ContextAnalyzer
        
        # Register trend analyzer with configurable parameters
        container.register_factory_with_params(
            "trend_analyzer_tool", 
            lambda c, **kwargs: TrendAnalyzer(
                min_frequency=kwargs.get("min_frequency", 3)
            )
        )
        
        # Backward compatibility registration
        container.register_factory(
            "trend_analyzer", 
            lambda c: c.get("trend_analyzer_tool")
        )
        
        # ... more registrations ...
    except ImportError as e:
        print(f"Error registering analysis tools: {e}")
```

## Best Practices

### Tool Design
- Keep tools focused on a single responsibility
- Minimize dependencies on other components
- Accept dependencies through the constructor
- Make dependencies optional when possible
- Load expensive resources (like ML models) lazily

### Error Handling
- Provide clear error messages
- Use specific exception types
- Document exceptions in docstrings
- Handle expected errors, let unexpected ones propagate

### Testing
- Create unit tests for each tool
- Mock external dependencies
- Test edge cases and error conditions
- Use parameterized tests for different inputs

### Performance
- Consider caching for expensive operations
- Implement batch processing for efficiency
- Load resources only when needed
- Release resources when they're no longer needed

### Integration
- Use the container for tool registration
- Follow naming conventions (`tool_name_tool`)
- Use factory functions for configurable initialization