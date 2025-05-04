# Local Newsifier Flows Guide

## Overview
The flows module contains high-level workflow definitions that orchestrate multiple steps of processing. Flows coordinate between services and implement complex business logic sequences.

## Key Flow Types

### Entity Tracking Flow
- **EntityTrackingFlow**: Processes articles to extract and track entities
- Located in `flows/entity_tracking_flow.py`

### News Pipeline Flow
- **NewsPipeline**: End-to-end processing of news articles
- Located in `flows/news_pipeline.py`

### Analysis Flows
- **HeadlineTrendFlow**: Analyzes headline trends over time
- **TrendAnalysisFlow**: General trend analysis workflow
- Located in `flows/analysis/`

### Scraping Flows
- **RSSScrapingFlow**: Fetches and processes RSS feeds
- Located in `flows/rss_scraping_flow.py`

### Public Opinion Flow
- **PublicOpinionFlow**: Analyzes public opinion on entities
- Located in `flows/public_opinion_flow.py`

## Flow Patterns

### State-Based Processing
Flows use state objects to track processing state:

```python
class EntityTrackingFlow:
    def __init__(self, entity_service=None, container=None):
        self.entity_service = entity_service
        self.container = container
        self._ensure_dependencies()
        
    def process(self, state: EntityTrackingState) -> EntityTrackingState:
        """Process an article using the entity service.
        
        Args:
            state: The current state of processing
            
        Returns:
            Updated state with processing results
        """
        try:
            # Delegate to service layer
            state = self.entity_service.process_article_with_state(state)
        except Exception as e:
            # Update state with error information
            state.status = TrackingStatus.ERROR
            state.set_error("entity_tracking_flow.process", e)
            
        return state
```

### Error Handling and Recovery
Flows implement robust error handling:

```python
def process_batch(self, batch_id, articles):
    """Process a batch of articles with error recovery.
    
    Args:
        batch_id: Identifier for the batch
        articles: List of articles to process
        
    Returns:
        BatchResult with processing statistics
    """
    results = BatchResult(batch_id=batch_id)
    
    for article in articles:
        try:
            # Process the article
            state = EntityTrackingState(
                article_id=article.id,
                content=article.content,
                title=article.title
            )
            
            processed_state = self.process(state)
            
            # Update batch results
            if processed_state.status == TrackingStatus.SUCCESS:
                results.success_count += 1
            else:
                results.error_count += 1
                results.errors.append(processed_state.error_details)
                
        except Exception as e:
            # Catch unexpected errors
            results.error_count += 1
            results.errors.append(
                ErrorDetails(task="process_batch", message=str(e))
            )
            
    return results
```

### Dependency Management
Flows get dependencies from the container:

```python
def _ensure_dependencies(self):
    """Ensure all dependencies are available."""
    if self.entity_service is None and self.container:
        self.entity_service = self.container.get("entity_service")
        
    if self.entity_service is None:
        raise ValueError("EntityTrackingFlow requires entity_service")
```

### Multi-stage Processing
Flows coordinate multiple processing stages:

```python
def execute(self, url):
    """Execute the news pipeline on a URL.
    
    Args:
        url: The URL to process
        
    Returns:
        ProcessingResult with pipeline results
    """
    result = ProcessingResult(url=url)
    
    try:
        # Stage 1: Fetch article
        article = self.article_service.fetch_article(url)
        result.article_id = article.id
        
        # Stage 2: Extract entities
        tracking_state = EntityTrackingState(
            article_id=article.id,
            content=article.content,
            title=article.title
        )
        
        tracking_state = self.entity_tracking_flow.process(tracking_state)
        result.entities_extracted = len(tracking_state.entities)
        
        # Stage 3: Analyze sentiment
        sentiment_result = self.analysis_service.analyze_article_sentiment(
            article.id
        )
        result.sentiment_score = sentiment_result.get("compound", 0)
        
        # Mark success
        result.success = True
        
    except Exception as e:
        result.success = False
        result.error = str(e)
        
    return result
```

### Session Management
Flows delegate session management to services:

```python
def process_article(self, article_id):
    """Process an article by ID using services.
    
    Args:
        article_id: ID of the article to process
        
    Returns:
        Processing result
    """
    # Services handle their own session management
    article_data = self.article_service.get_article_data(article_id)
    
    # Create state object
    state = EntityTrackingState(
        article_id=article_id,
        content=article_data["content"],
        title=article_data["title"]
    )
    
    # Process with entity tracking flow
    result_state = self.entity_tracking_flow.process(state)
    
    return {
        "article_id": article_id,
        "status": result_state.status,
        "entity_count": len(result_state.entities),
        "success": result_state.status == TrackingStatus.SUCCESS
    }
```

## Integration with Services

Flows coordinate between multiple services:

```python
class PublicOpinionFlow:
    def __init__(
        self, 
        entity_service=None, 
        analysis_service=None,
        container=None
    ):
        self.entity_service = entity_service
        self.analysis_service = analysis_service
        self.container = container
        self._ensure_dependencies()
        
    def analyze_entity_opinion(self, entity_id, date_range=None):
        """Analyze public opinion for an entity.
        
        Args:
            entity_id: ID of the entity to analyze
            date_range: Optional date range for analysis
            
        Returns:
            Dictionary with opinion analysis results
        """
        # Get entity profile from entity service
        profile = self.entity_service.get_entity_profile(entity_id)
        
        # Get sentiment analysis from analysis service
        sentiment = self.analysis_service.get_entity_sentiment(
            entity_id, date_range
        )
        
        # Get relationship data from entity service
        relationships = self.entity_service.get_entity_relationships(
            entity_id, limit=10
        )
        
        # Combine results
        return {
            "entity": profile,
            "sentiment": sentiment,
            "relationships": relationships,
            "analysis_timestamp": datetime.now(timezone.utc)
        }
```

## Flow Registration in Container

Flows are registered in the DI container:

```python
# In container initialization
container.register_factory("entity_tracking_flow", lambda c: EntityTrackingFlow(
    entity_service=c.get("entity_service"),
    container=c
))

container.register_factory("news_pipeline", lambda c: NewsPipeline(
    article_service=c.get("article_service"),
    entity_tracking_flow=c.get("entity_tracking_flow"),
    analysis_service=c.get("analysis_service"),
    container=c
))
```

## Best Practices

### Flow Design
- Focus on orchestration, not implementation details
- Use state objects to track progress and handle errors
- Delegate business logic to services
- Keep flows focused on a specific workflow or use case

### Error Handling
- Implement comprehensive error handling and recovery
- Use structured error objects
- Avoid silent failures
- Log detailed error information
- Preserve error context across services

### Testing
- Create unit tests mocking service dependencies
- Test error recovery paths
- Use state objects to verify flow behavior
- Test complex workflows with integration tests

### Flow Composition
- Build complex flows from simpler flows
- Inject flows into other flows as dependencies
- Use the container to resolve flow dependencies

### Documentation
- Document flow stages and state transitions
- Explain error handling and recovery strategies
- Describe integration points with other components