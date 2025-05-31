# Documentation Updates Summary

## Overview

Based on your feedback, I've clarified the architectural direction for Local Newsifier and updated key documentation files. Here's what was done:

## Files Created

### 1. `/docs/architecture-clarification.md`
A comprehensive document that:
- Clarifies all 5 architectural decisions you asked about
- Provides clear direction on DI, CLI, background tasks, async/sync, and testing
- Includes implementation roadmap and success criteria
- Lists specific documentation updates needed

## Files Updated

### 2. `/CLAUDE.md` (Root)
Updated with the following clarifications:
- **DI Strategy**: "Use native FastAPI DI for API endpoints" + "CLI will use HTTP calls to FastAPI endpoints (migration in progress)"
- **Background Tasks**: "Use FastAPI BackgroundTasks (no Celery, no asyncio)"
- **Sync Status**: "project is fully sync-only" (removed "moving to")
- **Deployment**: "Moving to single web process, no Celery workers"
- **CLI Migration**: Added reference to migration plan

### 3. `/docs/plans/remove-celery.md`
Significantly updated to:
- Emphasize FastAPI BackgroundTasks as THE solution (not just an option)
- Remove confusing alternatives (async task manager, etc.)
- Provide clear implementation patterns for sync BackgroundTasks
- Add section on handling scheduled tasks (cron, APScheduler, Railway)
- Simplify timeline and benefits

## Key Clarifications Made

1. **FastAPI DI Everywhere**: API already uses it, CLI will use HTTP (no DI needed)
2. **CLI Architecture**: Will be a thin HTTP client calling API endpoints
3. **Background Tasks**: FastAPI BackgroundTasks only, no Celery, no complex alternatives
4. **Async/Sync**: Migration is essentially complete, just cosmetic cleanup remaining
5. **Testing**: Only use native FastAPI patterns, no injectable-specific testing

## What Still Needs Work

1. **Testing Documentation**: Still references injectable patterns
2. **FastAPI-Injectable References**: Need to be removed/archived once CLI migration completes
3. **Deployment Docs**: Need updating to reflect single-process architecture
4. **Archive Old Docs**: Completed migration plans should be moved to archive

## Next Steps

1. Create GitHub issues for each remaining task
2. Start with Celery removal (well-documented, straightforward)
3. Then tackle CLI HTTP migration (more complex but planned)
4. Update remaining docs as migrations complete

The architectural direction is now clear and documented. The main CLAUDE.md file accurately reflects the current state and future direction.
