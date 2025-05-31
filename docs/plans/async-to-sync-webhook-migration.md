# Async to Sync Webhook Migration Case Study

## Overview

This document details the successful migration of the Apify webhook handler from async to sync patterns, resolving the "generator didn't stop after throw()" error and improving code reliability.

## Problem Statement

The webhook endpoint was experiencing errors when exceptions were raised inside database session context managers. FastAPI attempted to clean up sync generators in an async context, causing runtime errors.

### Symptoms
- HTTP 500 errors with "generator didn't stop after throw()"
- Validation errors (422) being masked by session cleanup errors
- Difficult to debug error traces
- Inconsistent error responses

## Root Cause Analysis

The issue occurred due to:
1. HTTPException raised inside a database session context manager
2. FastAPI trying to clean up the sync generator in an async context
3. Mismatch between sync code execution and async cleanup

## Solution Implementation

### Phase 1: Fix Immediate Error

We implemented a simple session provider that properly handles exceptions:

```python
# api/dependencies.py
def get_session() -> Session:
    """Get a database session using FastAPI's native DI."""
    engine = get_engine()
    if engine is None:
        raise HTTPException(status_code=500, detail="Database unavailable")

    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

### Phase 2: Migrate to Native FastAPI DI

We migrated from fastapi-injectable to FastAPI's native dependency injection:

#### Before (fastapi-injectable)
```python
from injectable import injectable

@injectable(use_cache=False)
def get_apify_webhook_service(
    session=Depends(get_session),
    apify_crud=Depends(get_apify_crud)
):
    return ApifyWebhookService(session, apify_crud)
```

#### After (Native FastAPI)
```python
from typing import Annotated
from fastapi import Depends

def get_apify_webhook_service(
    session: Annotated[Session, Depends(get_session)],
    apify_webhook_crud: Annotated[CRUDApifyWebhookRaw, Depends(get_apify_webhook_crud)]
) -> ApifyWebhookService:
    return ApifyWebhookService(
        session=session,
        apify_webhook_crud=apify_webhook_crud,
        webhook_secret=settings.APIFY_WEBHOOK_SECRET
    )
```

## Key Changes Made

### 1. Webhook Route Handler
```python
@router.post("/webhooks/apify", status_code=202)
def apify_webhook(
    webhook_data: ApifyWebhook,
    webhook_service: Annotated[ApifyWebhookService, Depends(get_apify_webhook_service)]
):
    """
    Handle Apify webhooks.

    This endpoint receives webhooks from Apify when actor runs complete.
    """
    result = webhook_service.handle_webhook(webhook_data)

    return {
        "status": "accepted",
        "actor_id": result.get("actor_id"),
        "dataset_id": result.get("dataset_id"),
        "processing_status": result.get("status")
    }
```

### 2. Service Implementation
```python
class ApifyWebhookService:
    def __init__(
        self,
        session: Session,
        apify_webhook_crud: CRUDApifyWebhookRaw,
        webhook_secret: Optional[str] = None
    ):
        self.session = session
        self.apify_webhook_crud = apify_webhook_crud
        self.webhook_secret = webhook_secret

    def handle_webhook(self, webhook_data: ApifyWebhook) -> dict:
        """Process webhook synchronously."""
        # Validation logic
        if webhook_data.secret != self.webhook_secret:
            raise HTTPException(
                status_code=401,
                detail="Invalid webhook secret"
            )

        # Store webhook data
        webhook_raw = self.apify_webhook_crud.create(
            self.session,
            obj_in=webhook_data
        )

        return {
            "webhook_id": webhook_raw.id,
            "actor_id": webhook_data.actorId,
            "dataset_id": webhook_data.defaultDatasetId,
            "status": webhook_data.status
        }
```

## Benefits Achieved

1. **Error Resolution**: No more "generator didn't stop after throw()" errors
2. **Proper Status Codes**: Validation errors return 422, auth errors return 401
3. **Simpler Code**: Removed async complexity where not needed
4. **Better Testing**: Easier to test sync endpoints
5. **Consistent Patterns**: All API endpoints now use the same sync pattern

## Testing Approach

### Unit Tests
```python
def test_webhook_validation_error():
    """Test that validation errors return proper status code."""
    response = client.post(
        "/webhooks/apify",
        json={"invalid": "data"}
    )
    assert response.status_code == 422
```

### Integration Tests
```python
def test_webhook_with_database(db_session):
    """Test webhook creates database record."""
    response = client.post(
        "/webhooks/apify",
        json=valid_webhook_data
    )
    assert response.status_code == 202

    # Verify database record
    webhook = db_session.query(ApifyWebhookRaw).first()
    assert webhook is not None
```

## Lessons Learned

1. **Sync is Simpler**: For database operations, sync patterns are often more straightforward
2. **Native DI is Better**: FastAPI's native DI provides better error messages than third-party solutions
3. **Session Management Matters**: Proper session cleanup prevents resource leaks
4. **Test Error Paths**: Always test validation and error scenarios

## Migration Checklist

When migrating from async to sync:

- [ ] Remove all `async def` and `await` keywords
- [ ] Replace AsyncSession with Session
- [ ] Update dependency injection to use sync providers
- [ ] Test all error paths
- [ ] Verify proper HTTP status codes
- [ ] Check session cleanup in finally blocks
- [ ] Update documentation

## Future Considerations

1. **Performance**: Monitor response times to ensure sync approach meets requirements
2. **Scalability**: Consider connection pooling settings for high load
3. **Monitoring**: Add metrics for webhook processing times
4. **Error Tracking**: Implement proper error logging and alerting

## Conclusion

The migration from async to sync webhook handling successfully resolved the generator cleanup error while simplifying the codebase. The use of FastAPI's native dependency injection further improved code clarity and maintainability.
