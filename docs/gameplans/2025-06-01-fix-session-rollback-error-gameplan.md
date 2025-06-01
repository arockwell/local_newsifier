# Gameplan: Fix SQLAlchemy Session Rollback Error

## Objective
Fix the PendingRollbackError that occurs after database errors, ensuring proper session cleanup and transaction management.

## Priority: HIGH
This issue causes cascading failures and masks the real errors, making debugging difficult.

## Implementation Steps

### Phase 1: Fix get_session Dependency (1 hour)

1. **Update `api/dependencies.py`**
   ```python
   def get_session():
       """Provide a transactional session for FastAPI routes."""
       session = SessionLocal()
       try:
           yield session
           # Only commit if we're still in a transaction
           if session.in_transaction():
               session.commit()
       except Exception:
           # Rollback on any exception
           if session.in_transaction():
               session.rollback()
           raise
       finally:
           # Always close the session
           session.close()
   ```

2. **Alternative approach using context manager**
   ```python
   @contextmanager
   def get_session():
       """Provide a transactional session with automatic cleanup."""
       session = SessionLocal()
       try:
           yield session
           session.commit()
       except Exception:
           session.rollback()
           raise
       finally:
           session.close()
   ```

### Phase 2: Update Webhook Service Error Handling (2 hours)

1. **Add explicit transaction management**
   ```python
   def handle_webhook(self, webhook_data: ApifyWebhook) -> Dict[str, Any]:
       """Handle incoming webhook with proper transaction management."""
       try:
           # Processing logic here
           result = self._process_webhook(webhook_data)
           self.session.commit()
           return result
       except IntegrityError as e:
           self.session.rollback()
           if "ix_apify_webhook_raw_run_id" in str(e):
               # Handle duplicate webhook
               return self._handle_duplicate_webhook(webhook_data)
           raise
       except Exception as e:
           self.session.rollback()
           logger.error(f"Webhook processing failed: {e}")
           raise
   ```

2. **Separate read and write operations**
   ```python
   def _check_duplicate(self, run_id: str) -> bool:
       """Check for duplicate in a separate transaction."""
       try:
           # Use a fresh query to avoid transaction issues
           exists = self.session.query(
               exists().where(ApifyWebhookRaw.run_id == run_id)
           ).scalar()
           return exists
       except Exception:
           # Don't let read errors affect write transaction
           self.session.rollback()
           raise
   ```

### Phase 3: Add Session State Validation (1 hour)

1. **Create session utilities**
   ```python
   def ensure_transaction_clean(session):
       """Ensure session is in a clean state."""
       if not session.in_transaction():
           return
       if session.dirty or session.new or session.deleted:
           session.rollback()

   def safe_commit(session):
       """Safely commit with state checking."""
       if not session.in_transaction():
           return
       try:
           session.commit()
       except Exception:
           session.rollback()
           raise
   ```

2. **Add decorators for transaction management**
   ```python
   def with_transaction(func):
       """Decorator to ensure proper transaction handling."""
       @wraps(func)
       def wrapper(self, *args, **kwargs):
           try:
               result = func(self, *args, **kwargs)
               if hasattr(self, 'session'):
                   self.session.commit()
               return result
           except Exception:
               if hasattr(self, 'session') and self.session.in_transaction():
                   self.session.rollback()
               raise
       return wrapper
   ```

### Phase 4: Update Error Handling Pattern (2 hours)

1. **Create custom exceptions**
   ```python
   class WebhookError(Exception):
       """Base webhook error."""
       pass

   class DuplicateWebhookError(WebhookError):
       """Raised when webhook is duplicate."""
       def __init__(self, run_id: str):
           self.run_id = run_id
           super().__init__(f"Duplicate webhook for run_id: {run_id}")
   ```

2. **Update endpoint error handling**
   ```python
   @router.post("/webhooks/apify")
   def apify_webhook(
       webhook_data: ApifyWebhook,
       session: Session = Depends(get_session)
   ):
       try:
           service = ApifyWebhookService(session)
           result = service.handle_webhook(webhook_data)
           return {"status": "success", **result}
       except DuplicateWebhookError as e:
           # Return success for duplicates
           return {"status": "duplicate", "run_id": e.run_id}
       except Exception as e:
           # Ensure session is clean for error response
           if session.in_transaction():
               session.rollback()
           raise HTTPException(
               status_code=500,
               detail=f"Webhook processing failed: {str(e)}"
           )
   ```

### Phase 5: Testing (2 hours)

1. **Test session state management**
   ```python
   def test_session_rollback_on_error():
       """Test session properly rolls back on error."""
       with get_session() as session:
           # Cause an integrity error
           # Verify session is rolled back
           # Verify session is reusable
   ```

2. **Test concurrent webhook handling**
   - Simulate multiple webhooks for same run_id
   - Verify proper error handling
   - Ensure no session corruption

3. **Test error recovery**
   - Force various error conditions
   - Verify session cleanup
   - Check connection pool health

### Phase 6: Add Monitoring (1 hour)

1. **Add session state logging**
   ```python
   def log_session_state(session, context=""):
       """Log session state for debugging."""
       logger.debug(f"Session state {context}: "
                   f"in_transaction={session.in_transaction()}, "
                   f"dirty={bool(session.dirty)}, "
                   f"new={bool(session.new)}, "
                   f"deleted={bool(session.deleted)}")
   ```

2. **Add metrics**
   - Track rollback frequency
   - Monitor session lifetimes
   - Alert on connection pool exhaustion

## Success Criteria

1. No more PendingRollbackError in logs
2. Clean error messages showing actual problems
3. Sessions properly cleaned up after errors
4. No connection pool exhaustion
5. Proper transaction boundaries

## Deployment Plan

1. Test thoroughly in development
2. Deploy to staging with monitoring
3. Run integration tests
4. Monitor for session-related errors
5. Deploy to production during low traffic

## Long-term Improvements

1. **Use async SQLAlchemy**
   - Better connection pooling
   - Cleaner transaction handling

2. **Implement Unit of Work pattern**
   - Explicit transaction boundaries
   - Better error handling

3. **Add circuit breakers**
   - Prevent cascade failures
   - Graceful degradation
