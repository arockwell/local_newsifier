# Gameplan: Fix Apify Dataset Processing

## Overview
Fix the field mapping issue that prevents articles from being created from Apify datasets. Update all processing locations to use correct field names and add a manual dataset processing command.

## Priority Tasks

### 1. Fix Field Mapping (URGENT)
Update the content extraction logic to match actual Apify output fields.

**Files to update:**
- `src/local_newsifier/services/apify_webhook_service.py` - `_create_articles_from_dataset()`
- `src/local_newsifier/api/routers/webhooks.py` - `debug_apify_dataset()` endpoint

**Changes:**
```python
# Update content extraction logic
content = (
    item.get("text", "")          # Primary field from most actors
    or item.get("markdown", "")   # Alternative format
    or item.get("content", "")    # Legacy/custom actors
    or item.get("body", "")       # Fallback
)

# Extract metadata if available
metadata = item.get("metadata", {})
if not content and metadata:
    content = metadata.get("description", "")

# Use metadata for additional fields
published_at = metadata.get("publishedAt") or datetime.now(UTC)
author = metadata.get("author", "")
keywords = metadata.get("keywords", "")
```

### 2. Add Manual Dataset Processing Command
Create a new CLI command to process any dataset ID into articles.

**New file:** `src/local_newsifier/cli/commands/apify.py` (add to existing)

**Command structure:**
```bash
nf apify process-dataset <dataset_id> [options]
  --dry-run          # Show what would be created without saving
  --min-content-length # Minimum content length (default: 500)
  --source-name      # Override source name (default: "apify")
  --force            # Process even if articles exist
```

### 3. Improve Content Quality Checks
Update minimum content length and add quality validation.

**Changes:**
- Increase minimum content length from 100 to 500 chars
- Add check for actual text content (not just HTML tags)
- Validate that content isn't just navigation/header text

### 4. Add Comprehensive Logging
Track exactly how articles are created from datasets.

**Add logging for:**
- Which fields were present in each item
- Which field was used for content
- Why items were skipped
- Success/failure counts by reason

### 5. Update Debug Endpoint
Enhance the debug endpoint to show field availability.

**Enhancements:**
- Show all available fields per item
- Highlight which fields contain usable content
- Show content preview from each field
- Indicate which field would be used

## Implementation Steps

### Phase 1: Emergency Fix (30 minutes)
1. Update field mapping in `ApifyWebhookService._create_articles_from_dataset()`
2. Test with existing datasets
3. Deploy hotfix

### Phase 2: CLI Command (1 hour)
1. Add `process-dataset` command to `apify.py`
2. Implement dry-run mode for testing
3. Add progress reporting
4. Test with various dataset types

### Phase 3: Enhanced Processing (1 hour)
1. Improve content extraction logic
2. Add metadata extraction
3. Implement quality checks
4. Update debug endpoint

### Phase 4: Testing & Documentation (30 minutes)
1. Test with real Apify datasets
2. Update documentation
3. Add examples to CLI help
4. Create test fixtures

## Testing Strategy

### Manual Testing
1. Process the dataset from `dataset.log`
2. Test with website-content-crawler output
3. Test with web-scraper output
4. Test with custom actor output

### Automated Tests
1. Add fixtures with real dataset structures
2. Test field mapping variations
3. Test content quality checks
4. Test duplicate handling

## Success Criteria
- [ ] Articles are created from standard Apify actor output
- [ ] Manual dataset processing works via CLI
- [ ] Debug endpoint accurately shows why articles aren't created
- [ ] All tests pass
- [ ] Documentation is updated

## Rollback Plan
If issues arise:
1. Revert field mapping changes
2. Keep webhook processing as-is
3. Use manual CLI command for processing
4. Investigate actor-specific adapters

## Future Enhancements
1. Actor-specific field mappings
2. Content enhancement (summarization, cleanup)
3. Automatic actor detection
4. Batch dataset processing
5. Dataset processing queue
6. Webhook retry for processing failures
