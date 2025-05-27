# PLAN A: Complete Sync Migration and Stabilization

## Overview
The most critical workstream is completing the sync migration and stabilizing the codebase. This resolves architectural conflicts and simplifies the entire system.

## Priority Tasks (4-6 weeks)

### Phase 1: Resolve Architectural Direction (Week 1)
1. **Finalize sync-only decision**
   - Remove all async code patterns
   - Update CLAUDE.md to reflect sync-only approach
   - Remove fastapi-injectable async providers

2. **Complete event loop cleanup** (28 test files remaining)
   - Remove event_loop_fixture imports from all test files
   - Standardize on sync test patterns
   - Ensure CI remains stable

### Phase 2: Convert FastAPI Routes to Sync (Week 2-3)
1. **Convert main.py routes**
   - Change all `async def` to `def`
   - Remove `await` keywords
   - Update request handlers

2. **Convert remaining routers**
   - auth.py: Convert login/logout endpoints
   - system.py: Convert system status endpoints
   - tasks.py: Convert task management endpoints
   - webhooks.py: Convert webhook handlers

3. **Update dependencies**
   - Convert all async providers to sync in di/providers.py
   - Remove di/async_providers.py
   - Update database sessions to use sync patterns

### Phase 3: Remove Async Infrastructure (Week 4)
1. **Remove async database components**
   - Delete database/async_engine.py
   - Remove async session factories
   - Update all CRUD operations to sync

2. **Update services**
   - Convert apify_service_async.py to sync
   - Convert apify_webhook_service_async.py to sync
   - Remove all AsyncSession imports

3. **Clean up models and utilities**
   - Remove async-specific model methods
   - Update error handlers for sync patterns
   - Remove httpx in favor of requests

### Phase 4: Testing and Validation (Week 5-6)
1. **Comprehensive test suite update**
   - Remove all @pytest.mark.asyncio decorators
   - Convert async test functions to sync
   - Ensure 100% test coverage maintained

2. **Integration testing**
   - Test all API endpoints
   - Verify webhook processing
   - Validate database operations

3. **Performance testing**
   - Benchmark sync vs previous async performance
   - Optimize any bottlenecks
   - Document performance characteristics

## Success Criteria
- All async code removed
- All tests passing without event loop issues
- CI/CD pipeline stable
- No performance regressions
- Documentation updated

## Dependencies
- Must decide on sync-only approach first
- Requires updating all dependent systems
- May impact deployment configuration

## Next Steps
1. Create branch for sync migration
2. Start with event loop cleanup (quick win)
3. Convert one router at a time
4. Update tests incrementally
5. Monitor CI stability throughout
