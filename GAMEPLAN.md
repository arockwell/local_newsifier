# Game Plan: Fix Server Crash - Timezone Issue in Apify Webhook

## Problem Analysis

The server is crashing when processing Apify webhooks due to a timezone mismatch error:
- **Error**: `can't subtract offset-naive and offset-aware datetimes`
- **Location**: `/webhooks/apify` endpoint
- **Root Cause**: The code is trying to insert timezone-aware datetime objects (`datetime.datetime(..., tzinfo=datetime.timezone.utc)`) into PostgreSQL columns defined as `TIMESTAMP WITHOUT TIME ZONE`

## Key Error Details
1. The error occurs during an INSERT operation into the `apify_webhook_raw` table
2. The `created_at` and `updated_at` fields are being passed timezone-aware datetime objects
3. PostgreSQL columns expect timezone-naive timestamps (`TIMESTAMP WITHOUT TIME ZONE`)
4. The session rolls back but the async context manager tries to commit, causing a secondary `PendingRollbackError`

## Investigation Steps

1. **Examine the webhook router** - Check how datetime objects are created
2. **Review the apify_webhook_raw model** - Verify column definitions
3. **Check async session management** - Understand why rollback isn't handled properly
4. **Look at other working endpoints** - See how they handle datetime fields

## Solution Strategy

### Primary Fix: Timezone Handling
1. Convert timezone-aware datetimes to timezone-naive before database insertion
2. Options:
   - Remove timezone info: `dt.replace(tzinfo=None)`
   - Convert to UTC and remove timezone: `dt.astimezone(timezone.utc).replace(tzinfo=None)`
   - Use SQLModel's datetime handling patterns from other models

### Secondary Fix: Async Session Error Handling
1. Add proper error handling in the async session context manager
2. Ensure rollback is called before attempting commit on error
3. Consider if async patterns should be replaced with sync (per project direction)

## Implementation Plan

1. **Locate and examine the webhook endpoint**
   - Find `/webhooks/apify` route in `src/local_newsifier/api/routers/webhooks.py`
   - Identify where datetime objects are created

2. **Fix datetime handling**
   - Ensure all datetime objects are timezone-naive before database insertion
   - Follow existing patterns in the codebase

3. **Improve error handling**
   - Add try/except blocks around database operations
   - Ensure proper rollback on errors

4. **Test the fix**
   - Use the webhook testing functions mentioned in CLAUDE.md
   - Verify no timezone errors occur
   - Ensure data is properly saved

5. **Consider migration to sync**
   - The project is moving away from async patterns
   - If time permits, convert the webhook endpoint to sync

## Testing Plan

1. Run existing webhook tests: `test_webhook_success`, `test_webhook_failure`
2. Create specific test for timezone handling
3. Verify fix with `make test`
4. Check CI passes after pushing PR

## Notes

- The project is moving to sync-only implementations, so async patterns should be avoided in new code
- Follow existing datetime handling patterns in the codebase
- Ensure compatibility with PostgreSQL's timestamp storage
