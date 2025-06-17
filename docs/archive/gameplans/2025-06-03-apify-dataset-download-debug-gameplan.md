# Apify Dataset Download Debug Implementation Gameplan

## Overview

Implement a debug endpoint and CLI command to test Apify dataset downloads independently of webhooks, providing better visibility into failures and enabling manual recovery.

## Implementation Steps

### Phase 1: Create Debug API Endpoint

#### 1.1 Add Debug Router (New File)
**File**: `src/local_newsifier/api/routers/debug.py`
- Create new router with `/debug` prefix
- Add authentication/authorization (admin only)
- Include detailed error handling

#### 1.2 Implement Dataset Download Endpoint
**Endpoint**: `POST /debug/download-dataset/{dataset_id}`
- Accept dataset ID as path parameter
- Optional query parameters:
  - `dry_run`: Preview without creating articles
  - `limit`: Limit number of items to process
  - `verbose`: Include detailed processing info
- Return detailed response:
  ```json
  {
    "status": "success|error",
    "dataset_id": "...",
    "items_found": 10,
    "articles_created": 8,
    "articles_skipped": 2,
    "errors": [],
    "processing_details": {
      "fetch_time_ms": 1234,
      "process_time_ms": 5678,
      "items": [...]  // if verbose=true
    }
  }
  ```

#### 1.3 Update Main API
**File**: `src/local_newsifier/api/main.py`
- Include debug router (only in development mode)
- Add environment variable to enable/disable debug endpoints

### Phase 2: Refactor Dataset Processing

#### 2.1 Extract Dataset Processing Logic
**File**: `src/local_newsifier/services/apify_dataset_service.py` (New)
- Move `_create_articles_from_dataset` from webhook service
- Add detailed error handling and progress tracking
- Implement retry logic for transient failures
- Add field mapping configuration

#### 2.2 Enhance Error Handling
- Create specific exception types:
  - `DatasetNotFoundError`
  - `DatasetAuthenticationError`
  - `DatasetParsingError`
  - `ArticleValidationError`
- Include Apify API error details
- Add structured error responses

### Phase 3: Create CLI Command

#### 3.1 Add Dataset Download Command
**File**: `src/local_newsifier/cli/commands/apify.py`
- Add `download-dataset` command
- Show progress bar for large datasets
- Display detailed results in table format
- Support output to file (JSON)

#### 3.2 Command Implementation
```bash
nf apify download-dataset <dataset_id> [options]
  --dry-run              Preview without creating articles
  --limit <n>            Process only first n items
  --verbose              Show detailed processing info
  --output <file>        Save results to JSON file
  --token <token>        Override Apify token
```

### Phase 4: Add Webhook Recovery Command

#### 4.1 List Failed Webhooks
**Command**: `nf apify webhooks list-failed`
- Query webhooks with SUCCEEDED status but 0 articles created
- Show dataset IDs for manual recovery

#### 4.2 Reprocess Webhook
**Command**: `nf apify webhooks reprocess <webhook_id>`
- Find webhook by ID
- Extract dataset ID
- Call dataset download service
- Update webhook status

### Phase 5: Testing & Documentation

#### 5.1 Add Tests
- Unit tests for dataset service
- Integration tests for debug endpoint
- CLI command tests
- Mock Apify API responses

#### 5.2 Update Documentation
- Add troubleshooting guide
- Document debug endpoint usage
- Add webhook recovery procedures
- Include common error solutions

## Implementation Priority

1. **Critical** - Dataset processing service refactor (enables everything else)
2. **High** - Debug API endpoint (immediate debugging capability)
3. **High** - CLI download command (manual recovery)
4. **Medium** - Webhook recovery commands (nice to have)
5. **Low** - Enhanced error types (can add incrementally)

## Success Metrics

- Can manually download any dataset by ID
- Clear error messages when download fails
- Ability to recover failed webhooks
- Reduced debugging time from hours to minutes

## Rollback Plan

- Debug endpoints are isolated and optional
- Can disable via environment variable
- Original webhook flow unchanged
- No impact on production if not enabled

## Next Steps

1. Create the dataset service to centralize logic
2. Implement debug endpoint
3. Add CLI command
4. Test with real failed webhooks
5. Document the debugging process
