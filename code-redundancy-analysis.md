# Code Redundancy Analysis: URL Parsing

## Summary

Found multiple instances of URL parsing code duplicated across the codebase, specifically for extracting domain names from URLs to use as source identifiers.

## Duplicated Code Pattern

The following pattern appears in multiple locations:

```python
from urllib.parse import urlparse
parsed_url = urlparse(url)
source = parsed_url.netloc
```

## Locations Found

### 1. `/src/local_newsifier/services/article_service.py`

**Lines 57-60:**
```python
# Extract domain as source if not provided
from urllib.parse import urlparse

parsed_url = urlparse(url)
source = parsed_url.netloc or "Unknown Source"
```

**Lines 168-183:** (in `create_article_from_rss_entry`)
```python
# Extract source from feed data or URL
source = entry.get("source", {}).get("title", "")
if not source and "feed_url" in entry:
    # Try to get domain from feed URL
    from urllib.parse import urlparse

    parsed_url = urlparse(entry.get("feed_url", ""))
    source = parsed_url.netloc

# Fallback to domain name from article URL if source is still empty
if not source and url:
    from urllib.parse import urlparse

    parsed_url = urlparse(url)
    source = parsed_url.netloc

# Default source if all else fails
if not source:
    source = "Unknown Source"
```

### 2. `/src/local_newsifier/tools/file_writer.py`

**Lines 44-47:**
```python
# Extract domain from URL
from urllib.parse import urlparse

domain = urlparse(state.target_url).netloc.replace("www.", "")
```

### 3. `/src/local_newsifier/models/webhook.py`

While this file doesn't contain the actual URL parsing code, it defines a configuration option `extract_domain_as_source` (line 77) that suggests URL domain extraction should be happening somewhere when this flag is enabled.

## Analysis

### Problems Identified:

1. **Code Duplication**: The same URL parsing logic is repeated in multiple places
2. **Inconsistent Import**: `urllib.parse` is imported inline in multiple locations rather than at the top of files
3. **Inconsistent Handling**: Some places strip "www." prefix (file_writer.py), others don't
4. **Multiple Fallback Logic**: The RSS entry processing has complex, nested fallback logic that could be simplified

### Potential Issues:

1. **Maintenance**: Changes to URL parsing logic need to be made in multiple places
2. **Consistency**: Different parts of the codebase might handle URLs differently
3. **Testing**: Each instance needs separate tests
4. **Error Handling**: No consistent error handling for malformed URLs

## Recommendation

Create a centralized utility function for URL domain extraction:

```python
# src/local_newsifier/utils/url_utils.py
from urllib.parse import urlparse
from typing import Optional

def extract_domain_from_url(url: str, remove_www: bool = False) -> Optional[str]:
    """Extract domain from URL with consistent handling.

    Args:
        url: The URL to parse
        remove_www: Whether to remove 'www.' prefix

    Returns:
        Domain name or None if URL is invalid
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc

        if not domain:
            return None

        if remove_www and domain.startswith('www.'):
            domain = domain[4:]

        return domain
    except Exception:
        return None
```

Then replace all instances with calls to this utility function.
