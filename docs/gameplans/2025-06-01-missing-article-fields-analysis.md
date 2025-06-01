# Analysis: Missing Article Fields in Apify Webhook Data

## Issue Overview

All articles received from Apify webhooks are being skipped because they're missing required fields, specifically the `title` field. This results in zero articles being saved despite successful webhook processing.

## Technical Details

### Log Evidence
```
Processing article 1/5: url=https://www.alligator.org/section/news
Skipping article: url=https://www.alligator.org/section/news, reason=missing_fields (title)
...
Article processing summary: total=5, created=0, skipped=5
Skip reasons: missing_fields=5, short_content=0, duplicate_url=0
```

### Affected Components
- **Service**: `ApifyWebhookService._create_articles_from_dataset()`
- **Actor**: Web scraper actor (id: aYG0l9s7dbB7j3gbS)
- **Dataset**: 3ZuZMft5IVrLEPEDc

## Root Cause Analysis

### 1. Incorrect Field Mapping
The service expects articles with specific fields:
- `title` (required)
- `content` or `text` (required)
- `url` (required)
- `publishedAt` (optional)

But the Apify actor might be returning data with different field names.

### 2. Wrong Actor Configuration
The URLs being scraped suggest navigation/category pages:
- `/section/news`
- `/section/news?page=10&per_page=20`
- `/section/news/campus/sfc`

These are likely index pages, not article pages, indicating:
- Actor is scraping the wrong pages
- Actor configuration needs article URL extraction
- Need to follow links to actual articles

### 3. Actor Output Schema Mismatch
Without seeing the actual data structure, common issues include:
- Data nested in unexpected structure
- Field names in different format (camelCase vs snake_case)
- Articles in a sub-object or array

## Data Flow Analysis

1. **Webhook Received**: Contains dataset ID
2. **Dataset Fetched**: 5 items retrieved successfully
3. **Item Processing**: Each item has a URL but missing title
4. **Validation Fails**: Items skipped due to missing fields
5. **Result**: 0 articles created

## Business Impact

1. **No Data Collection**: Despite successful scraping, no articles saved
2. **Wasted Resources**: Apify actor runs consuming credits with no results
3. **Broken Pipeline**: Downstream analysis has no data to process
4. **False Success**: System appears to work but produces no output

## Investigation Steps

1. **Examine Raw Dataset**
   ```python
   # Log the actual structure of dataset items
   logger.info(f"Dataset item structure: {json.dumps(items[0], indent=2)}")
   ```

2. **Check Actor Configuration**
   - Review the Apify actor's output schema
   - Verify selector configuration
   - Check if pagination is handled correctly

3. **Verify Expected Fields**
   - Document expected article structure
   - Map Apify fields to article fields
   - Add field transformation if needed

## Proposed Solutions

### Immediate: Add Detailed Logging
```python
def _create_articles_from_dataset(self, items: List[Dict]) -> Dict[str, Any]:
    for item in items:
        logger.debug(f"Processing item: {json.dumps(item, indent=2)}")

        # Log what fields are present
        logger.info(f"Item fields: {list(item.keys())}")

        # Check for common field variations
        title = item.get('title') or item.get('headline') or item.get('name')
        content = item.get('content') or item.get('text') or item.get('body')

        if not title:
            logger.warning(f"Missing title. Available fields: {list(item.keys())}")
```

### Short-term: Flexible Field Mapping
```python
FIELD_MAPPINGS = {
    'title': ['title', 'headline', 'name', 'articleTitle'],
    'content': ['content', 'text', 'body', 'articleBody', 'description'],
    'url': ['url', 'link', 'href'],
    'publishedAt': ['publishedAt', 'datePublished', 'pubDate', 'date']
}

def extract_field(item: Dict, field_name: str) -> Optional[str]:
    """Extract field using multiple possible names."""
    for possible_name in FIELD_MAPPINGS.get(field_name, [field_name]):
        if value := item.get(possible_name):
            return value
    return None
```

### Long-term: Schema Validation
1. Define expected schema using Pydantic
2. Add schema transformation layer
3. Validate actor output on configuration
4. Alert on schema mismatches

## Actor Configuration Review

The actor needs to:
1. **Extract article URLs** from index pages
2. **Visit individual articles** to get content
3. **Use correct selectors** for title, content, etc.
4. **Output standardized schema**

Example configuration:
```javascript
{
    "startUrls": [{"url": "https://www.alligator.org/section/news"}],
    "pseudoUrls": [{
        "purl": "https://www.alligator.org/article/[.*]"
    }],
    "selectors": {
        "title": "h1.article-title",
        "content": "div.article-content",
        "publishedAt": "time[datetime]",
        "author": "span.byline"
    }
}
```
