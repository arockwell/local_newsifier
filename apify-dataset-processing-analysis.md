# Apify Dataset Processing Analysis

## Current State

Based on the `dataset.log` file and code analysis, we have a fundamental issue with how we're processing Apify datasets:

### Dataset Structure
The dataset.log shows that Apify actors (like website-content-crawler) return data with these common fields:
- `url`: The page URL
- `title`: The page title
- `text` or `markdown`: The extracted content
- `crawl`: Metadata about the crawl (depth, status code, etc.)
- `metadata`: Page metadata (description, author, keywords, etc.)

### Current Processing Logic

1. **Webhook Handler** (`src/local_newsifier/api/routers/webhooks.py`):
   - Receives webhook notifications from Apify
   - Validates and stores webhook data
   - Calls `_create_articles_from_dataset()` for successful runs

2. **Article Creation** (`src/local_newsifier/services/apify_webhook_service.py`):
   - Looks for content in these fields: `content`, `text`, `body`, `description`
   - Requires `url`, `title`, and content length >= 100 chars
   - Creates articles only if all conditions are met

### The Problem

The fields we're looking for (`content`, `body`) don't match what Apify actors typically return (`text`, `markdown`). This means most dataset items are being skipped because we can't find the content.

## Impact on Multiple Processing Points

We need to update article creation logic in multiple places:

### 1. Webhook Processing
- **Location**: `ApifyWebhookService._create_articles_from_dataset()`
- **Current**: Only processes webhooks, looks for wrong field names
- **Needed**: Update field mapping to match actual Apify output

### 2. CLI Commands
- **Location**: `nf apify scrape-content`, `nf apify web-scraper`
- **Current**: These commands fetch datasets but don't create articles
- **Needed**: Add option to create articles directly from CLI

### 3. Debug Endpoint
- **Location**: `/webhooks/apify/debug/{dataset_id}`
- **Current**: Analyzes datasets but uses same flawed field mapping
- **Needed**: Update to reflect correct field names

### 4. Manual Dataset Processing
- **Current**: No way to manually process a dataset into articles
- **Needed**: CLI command to process any dataset ID

## Field Mapping Issues

### Current Mapping (Incorrect)
```python
content = (
    item.get("content", "")      # Rarely exists
    or item.get("text", "")       # Common field!
    or item.get("body", "")       # Rarely exists
    or item.get("description", "") # Too short
)
```

### Recommended Mapping
```python
content = (
    item.get("text", "")          # Primary content field
    or item.get("markdown", "")   # Alternative format
    or item.get("content", "")    # Legacy support
    or item.get("body", "")       # Fallback
)

# Also consider extracting from metadata
if not content and "metadata" in item:
    metadata = item["metadata"]
    content = metadata.get("description", "")
```

## Additional Considerations

### 1. Content Quality
- Current 100-char minimum is too low for meaningful articles
- Should increase to 500-1000 chars for quality content
- Add content validation (not just length)

### 2. Metadata Extraction
- We're ignoring valuable metadata fields:
  - `published_at` from metadata
  - `author` information
  - `keywords` for tagging
  - `description` for summary

### 3. Source Attribution
- Currently hardcoded as "apify"
- Should include actor name/ID for better tracking
- Add dataset_id reference for debugging

### 4. Duplicate Handling
- Only checking URL uniqueness
- Should also check title similarity
- Consider content hashing for near-duplicates

## Recommendations

1. **Immediate Fix**: Update field mapping in all processing locations
2. **Add CLI Command**: Create `nf apify process-dataset` command
3. **Improve Content Extraction**: Use all available fields intelligently
4. **Add Monitoring**: Log which fields were used for each article
5. **Batch Processing**: Support processing multiple datasets
6. **Error Recovery**: Allow reprocessing of failed items
