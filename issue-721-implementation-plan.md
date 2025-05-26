# Issue #721: Minimal Apify Webhook Handler Implementation Plan

## Issue Analysis

### 1. Scope Assessment
**Estimated Lines**: ~150-250 lines total
- Model definition: ~20 lines
- Service logic: ~80 lines
- API endpoint: ~30 lines
- Migration: ~20 lines
- Tests: ~100 lines

**Verdict**: ✅ Well within scope (target was <500 lines preferred)

### 2. Sensibility Assessment
**Do we need it?**: Yes
- Currently no way to automatically process Apify actor results
- Manual processing limits scalability
- Webhook integration is standard practice for async job processing

**Is it worth it?**: Yes
- Minimal implementation reduces complexity
- Leverages existing Article infrastructure
- Provides immediate value with option to enhance later

**Verdict**: ✅ Makes sense to implement

### 3. Feasibility Assessment
**Difficulty**: Low
- Uses existing patterns from the codebase
- No complex state management required
- Clear requirements and boundaries
- Existing Apify service can be reused

**Verdict**: ✅ Straightforward to implement

## Implementation Plan

### Phase 1: Database Setup

#### 1.1 Create Migration File
```
alembic/versions/add_apify_webhook_raw_table.py
```
- Create `apify_webhook_raw` table with:
  - `id`: Primary key
  - `run_id`: String, unique index (Apify's run identifier)
  - `actor_id`: String (which actor was run)
  - `status`: String (webhook status: SUCCEEDED, FAILED, etc.)
  - `data`: JSON column for complete webhook payload
  - `created_at`: Timestamp
  - `processed_at`: Optional timestamp (if articles were created)

### Phase 2: Model Implementation

#### 2.1 Create ApifyWebhookRaw Model
```python
# src/local_newsifier/models/apify_webhook.py
class ApifyWebhookRaw(SQLModel, table=True):
    __tablename__ = "apify_webhook_raw"

    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: str = Field(unique=True, index=True)
    actor_id: str
    status: str
    data: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
```

### Phase 3: Service Layer

#### 3.1 Create Webhook Service
```python
# src/local_newsifier/services/apify_webhook_service.py
class ApifyWebhookService:
    def __init__(self, session_factory, apify_service, article_service):
        self.session_factory = session_factory
        self.apify_service = apify_service
        self.article_service = article_service

    def validate_signature(self, payload: bytes, signature: str) -> bool:
        # Implement HMAC validation if secret configured
        pass

    def handle_webhook(self, webhook_data: dict) -> ApifyWebhookRaw:
        # 1. Check for duplicate by run_id
        # 2. Save raw webhook data
        # 3. If status == "SUCCEEDED", fetch dataset and create articles
        # 4. Return saved webhook record
        pass
```

### Phase 4: API Endpoint

#### 4.1 Create Webhook Router
```python
# src/local_newsifier/api/routers/webhooks.py
@router.post("/apify")
async def handle_apify_webhook(
    request: Request,
    webhook_service: Annotated[ApifyWebhookService, Depends(get_apify_webhook_service)]
):
    # 1. Get raw body for signature validation
    # 2. Validate signature if secret configured
    # 3. Parse JSON payload
    # 4. Call service to handle webhook
    # 5. Return simple success response
```

#### 4.2 Register Router
Update `src/local_newsifier/api/main.py` to include webhook router

### Phase 5: Dependency Injection

#### 5.1 Create Provider
```python
# src/local_newsifier/di/providers.py
@injectable(use_cache=False)
def get_apify_webhook_service(...):
    return ApifyWebhookService(...)
```

### Phase 6: Testing

#### 6.1 Unit Tests
```python
# tests/services/test_apify_webhook_service.py
- test_save_webhook_data
- test_duplicate_detection
- test_article_creation_on_success
- test_signature_validation
```

#### 6.2 Integration Tests
```python
# tests/api/test_webhooks.py
- test_webhook_endpoint_success
- test_webhook_endpoint_duplicate
- test_webhook_endpoint_invalid_signature
```

### Phase 7: Configuration

#### 7.1 Update Settings
Add to `src/local_newsifier/config/settings.py`:
- `APIFY_WEBHOOK_SECRET`: Optional secret for HMAC validation

## Testing Strategy

1. **Unit Tests**:
   - Mock Apify service for dataset fetching
   - Test duplicate detection logic
   - Test article creation logic
   - Test signature validation

2. **Integration Tests**:
   - Test full webhook flow with test database
   - Test API endpoint responses
   - Test error handling

3. **Manual Testing**:
   - Use fish shell webhook test functions
   - Test with real Apify webhooks

## Key Design Decisions

1. **Single Transaction**: Save webhook and create articles in one transaction when possible
2. **Idempotent**: Multiple webhooks with same run_id are ignored
3. **Best Effort**: Article creation failures don't fail the webhook
4. **Minimal State**: No complex processing state, just processed_at timestamp
5. **Preserve Data**: Always save raw webhook data for debugging

## Implementation Order

1. Create migration and run it
2. Create model
3. Create service with basic save functionality
4. Create API endpoint
5. Add webhook validation
6. Add article creation logic
7. Write tests
8. Manual testing with webhook functions

## Success Criteria

- [ ] Webhook endpoint accepts POST requests
- [ ] Duplicate webhooks are ignored (by run_id)
- [ ] Raw webhook data is saved to database
- [ ] Articles are created for successful actor runs
- [ ] Signature validation works when secret configured
- [ ] All tests pass
- [ ] Can handle real Apify webhooks

## Risks and Mitigations

1. **Risk**: Article creation might fail
   - **Mitigation**: Log errors but don't fail webhook, set processed_at only on success

2. **Risk**: Large dataset might timeout
   - **Mitigation**: Consider async processing for large datasets in future iteration

3. **Risk**: Duplicate articles from same content
   - **Mitigation**: Rely on existing Article URL uniqueness constraint

## Future Enhancements (Not in Scope)

- Async task processing for large datasets
- Detailed error tracking
- Webhook retry logic
- Status dashboard
- Batch processing optimizations
