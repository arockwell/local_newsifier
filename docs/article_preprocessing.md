# Article Preprocessing Module

This document describes the article preprocessing module that standardizes and enhances content before analysis.

## Overview

The article preprocessing module provides utilities for cleaning and normalizing article content, extracting structured elements, and enhancing metadata. This ensures consistent treatment of content regardless of source, which is critical for accurate analysis results.

## Key Components

### ContentCleaner

The `ContentCleaner` class provides methods for cleaning and normalizing text content:

- **Boilerplate Removal**: Removes common boilerplate text like newsletter subscriptions, social media links, and advertisement text.
- **Whitespace Normalization**: Standardizes spacing and paragraph breaks.
- **Special Character Handling**: Handles HTML entities, Unicode normalization, and conversion of special characters.
- **Duplicate Paragraph Removal**: Removes repeated paragraphs that might appear in content.

```python
from local_newsifier.tools.preprocessing.content_cleaner import ContentCleaner

cleaner = ContentCleaner()
cleaned_content = cleaner.clean_content(original_content)
```

### ContentExtractor

The `ContentExtractor` class extracts the main article content and structured elements from HTML:

- **Main Content Extraction**: Identifies and extracts the main article body from HTML.
- **Structural Element Preservation**: Preserves important structural elements like headings, lists, and quotes.
- **Media Element Extraction**: Extracts and formats images, links, and other media elements.
- **Clean HTML Generation**: Produces clean HTML with non-content elements removed.

```python
from local_newsifier.tools.preprocessing.content_extractor import ContentExtractor

extractor = ContentExtractor()
results = extractor.extract_content(html_content)
# Results contain text, html, images, links, lists, quotes, etc.
```

### MetadataEnhancer

The `MetadataEnhancer` class extracts and enhances article metadata:

- **Publication Date Extraction**: Extracts or improves publication date information.
- **Category/Topic Identification**: Identifies content categories and topics.
- **Location Extraction**: Extracts mentioned locations from content.
- **Language Detection**: Detects the content language.

```python
from local_newsifier.tools.preprocessing.metadata_enhancer import MetadataEnhancer

enhancer = MetadataEnhancer()
enhanced_metadata = enhancer.enhance_metadata(
    content=article_text,
    html_content=html_content,
    url=article_url,
    existing_metadata=original_metadata
)
```

### ArticlePreprocessor

The `ArticlePreprocessor` service combines the above components into a complete preprocessing pipeline:

- **Unified API**: Provides a simple interface for article preprocessing.
- **Configurable Processing**: Allows selective enabling/disabling of processing steps.
- **Format Conversion**: Handles different input formats (text, HTML, article data).

```python
from local_newsifier.tools.preprocessing.article_preprocessor import ArticlePreprocessor

preprocessor = ArticlePreprocessor()
result = preprocessor.preprocess(
    content=article_text,
    html_content=html_content,
    url=article_url,
    metadata=original_metadata
)
```

## Integration with ArticleService

The preprocessing module is integrated into the `ArticleService` to enhance article content during processing:

```python
# Process an article with preprocessing
service.process_article(
    url="https://example.com/article",
    content=raw_content,
    title="Article Title",
    published_at=datetime.now(),
    html_content=html_content,  # Optional HTML for better extraction
    preprocess=True  # Enable preprocessing
)

# Create from RSS entry with preprocessing
service.create_article_from_rss_entry(
    entry=rss_entry,
    preprocess=True,
    html_content=html_content  # Optional
)
```

## Dependency Injection

The preprocessing components are available through dependency injection:

```python
from fastapi_injectable import injectable
from typing import Annotated
from fastapi import Depends

from local_newsifier.di.providers import get_article_preprocessor

@injectable(use_cache=False)
def my_service(
    preprocessor: Annotated["ArticlePreprocessor", Depends(get_article_preprocessor)]
):
    # Use the preprocessor
    result = preprocessor.preprocess(content, html_content)
```

## Configuration

The preprocessing components are configurable through the DI system:

```python
# Example: Configure content cleaner
@injectable(use_cache=False)
def get_custom_content_cleaner_config():
    return {
        "remove_boilerplate": True,
        "normalize_whitespace": True,
        "handle_special_chars": True,
        "remove_duplicates": False  # Disable duplicate removal
    }
```

## Benefits

- **Improved Data Quality**: Removing noise and standardizing content improves analysis results.
- **Enhanced Metadata**: Better publication dates, categories, and location information.
- **Consistent Processing**: Standardized content regardless of the original source.
- **Simplified Analysis**: Clean content makes entity extraction and sentiment analysis more accurate.

## Performance Considerations

- **Processing Cost**: Full preprocessing adds computational overhead, but improves analysis quality.
- **Selective Processing**: Use the options to enable only needed processing steps.
- **Cache Results**: Consider caching preprocessed content for frequently accessed articles.