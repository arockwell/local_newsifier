# State Model Migration Guide

## Overview

The multiple specific state models (`NewsAnalysisState`, `EntityTrackingState`, etc.) are being replaced with a single generic `ProcessingState` model to reduce code duplication.

## Migration Examples

### Before: Using NewsAnalysisState

```python
from local_newsifier.models.state import NewsAnalysisState, AnalysisStatus

# Create state
state = NewsAnalysisState(
    target_url="https://example.com/article",
    status=AnalysisStatus.INITIALIZED,
    analysis_config={"entity_types": ["PERSON", "ORG"]}
)

# Update state during processing
state.scraped_text = "Article content..."
state.scraped_at = datetime.now()
state.status = AnalysisStatus.SCRAPE_SUCCEEDED

# Access state data
url = state.target_url
text = state.scraped_text
```

### After: Using ProcessingState

```python
from local_newsifier.models.processing_state import ProcessingState, ProcessingStatus

# Create state
state = ProcessingState(
    processing_type="news_analysis",
    target_url="https://example.com/article",
    status=ProcessingStatus.INITIALIZED,
    data={
        "analysis_config": {"entity_types": ["PERSON", "ORG"]}
    }
)

# Update state during processing
state.set_data("scraped_text", "Article content...")
state.set_data("scraped_at", datetime.now())
state.status = ProcessingStatus.SCRAPE_SUCCEEDED

# Access state data
url = state.target_url
text = state.get_data("scraped_text")
```

## Migration Mapping

### NewsAnalysisState → ProcessingState

| Old Field | New Location |
|-----------|--------------|
| `target_url` | `target_url` (same) |
| `scraped_text` | `data["scraped_text"]` |
| `scraped_at` | `data["scraped_at"]` |
| `analyzed_at` | `data["analyzed_at"]` |
| `analysis_config` | `data["analysis_config"]` |
| `analysis_results` | `data["analysis_results"]` |
| `saved_at` | `data["saved_at"]` |
| `save_path` | `data["save_path"]` |

### EntityTrackingState → ProcessingState

| Old Field | New Location |
|-----------|--------------|
| `article_id` | `target_id` |
| `content` | `data["content"]` |
| `title` | `data["title"]` |
| `published_at` | `data["published_at"]` |
| `entities` | `data["entities"]` |

### EntityBatchTrackingState → ProcessingState

| Old Field | New Location |
|-----------|--------------|
| `status_filter` | `data["status_filter"]` |
| `processed_articles` | `data["processed_articles"]` |
| `total_articles` | `total_items` |
| `processed_count` | `processed_items` |
| `error_count` | `error_count` (same) |

## Common Patterns

### Starting Processing

```python
# Old way (specific to each state model)
state.status = AnalysisStatus.SCRAPING
state.add_log("Starting scraping")

# New way (generic)
state.start_processing()
```

### Completing Processing

```python
# Old way
state.status = AnalysisStatus.COMPLETED_SUCCESS
state.add_log("Processing completed")

# New way
state.complete_processing(success=True)
```

### Error Handling

```python
# Old way
state.set_error("scraping", exception)
state.status = AnalysisStatus.SCRAPE_FAILED

# New way
state.set_error("scraping", exception)
state.add_error(str(exception))
```

### Batch Processing

```python
# Old way (EntityBatchTrackingState)
state.add_processed_article(article_data, success=True)
state.processed_count += 1

# New way
state.increment_processed(success=True)
articles = state.get_data("processed_articles", [])
articles.append(article_data)
state.set_data("processed_articles", articles)
```

## Benefits

1. **Single model to maintain** - Reduce code duplication
2. **Flexible data storage** - Use the `data` dict for any custom fields
3. **Consistent interface** - Same methods for all processing types
4. **Easy to extend** - Add new processing types without new models
5. **Better type safety** - ProcessingStatus enum covers all statuses
