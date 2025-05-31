# Local Newsifier Architecture Clarification

## Overview

This document clarifies the architectural direction for Local Newsifier, resolving ambiguities found in the documentation analysis.

## Architectural Decisions

### 1. Dependency Injection Strategy
**Decision**: Use FastAPI's native DI everywhere.
- **API**: Already migrated to native FastAPI DI ✅
- **CLI**: Will be migrated to use HTTP calls to FastAPI endpoints (no direct DI needed)
- **Action**: Remove all fastapi-injectable references once CLI migration is complete

### 2. CLI Architecture
**Decision**: CLI will use HTTP calls to FastAPI endpoints.
- **Current**: CLI uses fastapi-injectable and direct database access
- **Target**: CLI becomes a thin client making HTTP requests to the API
- **Benefits**: Eliminates DI complexity, event loop issues, and duplicate business logic
- **Migration Plan**: Already documented in `docs/plans/cli-to-fastapi-overview.md`

### 3. Background Tasks
**Decision**: Use FastAPI BackgroundTasks, remove Celery entirely.
- **Current**: Celery infrastructure still present but being phased out
- **Target**: FastAPI BackgroundTasks for all async processing needs
- **Benefits**: Simpler deployment, fewer dependencies, no separate worker processes
- **Note**: The `docs/plans/remove-celery.md` plan needs to be updated to emphasize FastAPI BackgroundTasks as the primary solution

### 4. Async/Sync Status
**Decision**: Project is fully synchronous.
- **Completed**: Webhook migration to sync ✅
- **Completed**: All services/CRUD/tools are sync ✅
- **Mostly Done**: The async-to-sync migration is essentially complete
- **Remaining**: Some API route declarations may still be `async def` (cosmetic only)
- **Action**: Clean up any remaining `async def` declarations for consistency

### 5. Testing Strategy
**Decision**: Use only FastAPI's native testing patterns.
- **API Tests**: Use TestClient with native DI
- **CLI Tests**: Will use TestClient once migrated to HTTP
- **No Injectable**: Remove all injectable-specific test patterns
- **Action**: Update all test documentation to reflect this

## Implementation Roadmap

### Phase 1: Documentation Cleanup (Immediate)
1. Update CLAUDE.md to reflect these decisions
2. Remove contradictory information from guides
3. Archive completed migration plans
4. Create clear architectural overview

### Phase 2: Complete Celery Removal (Week 1)
1. Implement FastAPI BackgroundTasks for remaining async needs
2. Remove Celery dependencies from pyproject.toml
3. Update Railway deployment configuration
4. Remove Redis if only used for Celery

### Phase 3: CLI Migration (Weeks 2-3)
1. Implement CLI HTTP client (as designed in existing plans)
2. Create API endpoints for all CLI operations
3. Migrate CLI commands incrementally
4. Update CLI tests to use HTTP/TestClient
5. Remove fastapi-injectable dependency

### Phase 4: Final Cleanup (Week 4)
1. Remove any remaining `async def` route declarations
2. Clean up all imports and dependencies
3. Final documentation review
4. Performance validation

## Success Criteria

### Technical
- [ ] No fastapi-injectable imports in codebase
- [ ] No Celery imports or configuration
- [ ] All routes use sync pattern (`def`, not `async def`)
- [ ] CLI only makes HTTP requests (no direct DB access)
- [ ] Single, consistent DI pattern (native FastAPI)

### Documentation
- [ ] CLAUDE.md accurately reflects current architecture
- [ ] No contradictory information across docs
- [ ] Completed migrations properly archived
- [ ] Testing guide uses only native FastAPI patterns

### Deployment
- [ ] No worker or beat processes in Railway config
- [ ] No Redis dependency (unless needed for other purposes)
- [ ] Single web process handles everything
- [ ] Simplified deployment documentation

## Key Documentation Updates Required

### 1. Root CLAUDE.md Updates
```diff
- Use native FastAPI DI for API, fastapi-injectable for CLI
+ Use native FastAPI DI for API endpoints
+ CLI will use HTTP calls to FastAPI endpoints (migration in progress)

+ Background tasks use FastAPI BackgroundTasks (no Celery)
+ Project is fully synchronous (async-to-sync migration complete)
```

### 2. Documentation to Archive
These docs describe completed or obsolete patterns:
- `/docs/guides/dependency_injection.md` (if it emphasizes injectable)
- `/docs/integrations/celery_integration.md`
- `/docs/plans/fastapi-injectable-migration/*` (migration complete for API)
- Any guides mentioning async patterns

### 3. Documentation to Update
- `/docs/guides/testing_guide.md` - Remove injectable test patterns
- `/docs/plans/deployment-configuration.md` - Remove worker/beat processes
- `/docs/plans/remove-celery.md` - Emphasize FastAPI BackgroundTasks
- All CLI documentation - Note upcoming HTTP migration

### 4. Documentation to Create/Emphasize
- `/docs/architecture/overview.md` - Clear, current architectural vision
- `/docs/guides/background-tasks.md` - FastAPI BackgroundTasks patterns
- `/docs/guides/cli-http-migration.md` - Status and approach

## Notes on Current State

Based on the code analysis:
1. **CLI still uses fastapi-injectable** - This is why the migration to HTTP is important
2. **Celery is still present** - But the plan to remove it exists and should be executed
3. **Async-to-sync is mostly done** - Webhook was the complex case and it's complete
4. **Testing has mixed patterns** - Needs cleanup to standardize on native FastAPI

## Next Steps

1. Update CLAUDE.md immediately with these clarifications
2. Create tracking issues for each migration phase
3. Start with Celery removal (simpler, well-documented)
4. Then proceed with CLI HTTP migration (more complex but planned)
5. Clean up documentation as migrations complete
