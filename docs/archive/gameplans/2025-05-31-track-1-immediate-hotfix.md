# Track 1: Immediate Production Hotfix (2-3 hours)

**Priority: CRITICAL - System is DOWN**

## Issue
The webhook endpoint is returning 500 errors for duplicate key violations, causing Apify to retry indefinitely and creating a retry storm that's overwhelming the system.

## Implementation Scope

### 1. Fix Duplicate Key Handling (1 hour)
From `2025-06-01-fix-duplicate-key-violation-gameplan.md`:
- **ONLY implement steps 1-3**: Basic duplicate handling
- Add try/catch for IntegrityError in webhook handler
- Return 200 OK for duplicates (not 409) to stop Apify retries
- Skip steps 4-7 (comprehensive testing, monitoring) for now

### 2. Fix Session Rollback (30 min)
From `2025-06-01-fix-session-rollback-error-gameplan.md`:
- **ONLY implement step 1**: Add session.rollback() in error handlers
- Focus on webhook handler and critical save operations
- Skip the comprehensive refactoring for now

### 3. Emergency Logging (30 min)
From `2025-06-01-server-issues-comprehensive-analysis.md`:
- Add basic logging to understand what data Apify is sending
- Log webhook payload structure before processing
- Log any errors with full context

## Success Criteria
- Webhook endpoint returns 200 for all requests (even errors)
- No more 500 errors in logs
- Apify stops retry storms
- Basic visibility into what's happening

## Next Steps
Once system is stable, move to Track 2 for proper fixes.
