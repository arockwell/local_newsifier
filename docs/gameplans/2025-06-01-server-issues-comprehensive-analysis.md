# Comprehensive Analysis of Server Issues

## Executive Summary

The server logs reveal three distinct but interrelated issues affecting the Apify webhook processing system:

1. **Duplicate Key Constraint Violation**: Multiple webhook requests for the same `run_id` causing database integrity errors
2. **Session Transaction Rollback Error**: SQLAlchemy session management issues following the duplicate key violations
3. **Missing Article Fields**: All scraped articles are being skipped due to missing title fields

## Issue 1: Duplicate Key Constraint Violation

### Description
The primary issue is that multiple webhook requests are being received for the same Apify run ID (`IhQcgycyaMIzQOazn`), causing duplicate key violations when trying to insert into the `apify_webhook_raw` table.

### Error Details
```
sqlalchemy.exc.IntegrityError: (psycopg2.errors.UniqueViolation) duplicate key value violates unique constraint "ix_apify_webhook_raw_run_id"
DETAIL:  Key (run_id)=(IhQcgycyaMIzQOazn) already exists.
```

### Root Cause Analysis
- Apify appears to be sending multiple webhook notifications for the same run
- The webhook service claims to check for duplicates but still attempts to insert
- The duplicate check might be failing or checking the wrong table/criteria
- Multiple requests are hitting the endpoint at different times (02:28, 02:36, 02:44, 03:11)

### Impact
- Server returns 500 Internal Server Error
- Database session becomes corrupted
- Legitimate webhook processing fails

## Issue 2: Session Transaction Rollback Error

### Description
After the duplicate key violation, the SQLAlchemy session enters a rollback state, and subsequent operations fail with `PendingRollbackError`.

### Error Details
```
sqlalchemy.exc.PendingRollbackError: This Session's transaction has been rolled back due to a previous exception during flush. To begin a new transaction with this Session, first issue Session.rollback().
```

### Root Cause Analysis
- The session is not properly rolled back after the IntegrityError
- The session is being reused after a failed transaction
- The error handling in the webhook endpoint doesn't properly clean up the session
- The session commit in `get_session` dependency is failing

### Impact
- Cascading failures after the initial error
- Session becomes unusable
- All subsequent database operations fail

## Issue 3: Missing Article Fields

### Description
All articles being processed from the Apify dataset are missing required fields (specifically the `title` field).

### Log Evidence
```
Skipping article: url=https://www.alligator.org/section/news, reason=missing_fields (title)
Article processing summary: total=5, created=0, skipped=5
Skip reasons: missing_fields=5, short_content=0, duplicate_url=0
```

### Root Cause Analysis
- The Apify actor configuration might be incorrect
- The web scraper is not extracting the expected fields
- The field mapping between Apify output and expected article format is misaligned

### Impact
- No articles are being saved to the database
- The webhook processing completes but with no useful results
- System resources wasted on processing unusable data

## Timeline Analysis

1. **02:12:09**: Original Apify run completes (run_id: IhQcgycyaMIzQOazn)
2. **02:28:37**: First webhook received and processed (fails with duplicate key)
3. **02:36:28**: Second webhook for same run (fails with duplicate key + rollback error)
4. **02:44:14**: Third webhook for same run (same failures)
5. **03:11:02**: Fourth webhook for same run (same failures)

## Critical Observations

1. **Persistent Run ID**: The same run_id (IhQcgycyaMIzQOazn) appears in all requests, suggesting either:
   - Apify is retrying webhook delivery due to 500 errors
   - Multiple webhook endpoints are configured
   - The webhook is being triggered multiple times

2. **Duplicate Check Failure**: The service logs show "Webhook not duplicate, proceeding with processing" but then immediately fails on insert, indicating the duplicate check is not working correctly.

3. **No Successful Processing**: Despite multiple attempts, no articles are successfully created due to the field mapping issue.

## Recommendations

1. **Immediate**: Fix the duplicate key handling to properly detect and handle duplicate webhooks
2. **Immediate**: Implement proper session rollback in error handling
3. **Short-term**: Investigate and fix the article field mapping issue
4. **Long-term**: Implement idempotent webhook processing
5. **Long-term**: Add webhook signature validation to prevent duplicate processing
