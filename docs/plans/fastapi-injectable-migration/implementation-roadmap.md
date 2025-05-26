# FastAPI-Injectable Migration Implementation Roadmap

This document provides a detailed implementation plan for migrating away from FastAPI-Injectable, coordinated with the async and CLI-to-HTTP migrations.

## Overview

The migration away from FastAPI-Injectable is intertwined with two other major architectural changes:
1. **Async Migration**: Converting the codebase to fully async operations
2. **CLI-to-HTTP Migration**: Moving CLI from direct DI to HTTP-based architecture

These migrations are synergistic - each makes the others easier and more beneficial.

## Implementation Phases

### Phase 0: Preparation (Week 0)
**Goal**: Set up foundation for migration

#### Tasks:
1. **Create Migration Branches**
   ```bash
   git checkout -b feature/remove-fastapi-injectable
   git checkout -b feature/async-migration
   git checkout -b feature/cli-to-http
   ```

2. **Set Up Test Infrastructure**
   - Install async testing dependencies
   - Create async test database fixtures
   - Set up performance benchmarks

3. **Document Current State**
   - Inventory all uses of `@injectable`
   - List all provider functions
   - Map service dependencies

#### Deliverables:
- [ ] Migration branches created
- [ ] Async test infrastructure ready
- [ ] Complete inventory of injectable usage

### Phase 1: Database Layer (Week 1)
**Goal**: Convert database layer to async

#### Tasks:
1. **Install Async Database Driver**
   ```toml
   [tool.poetry.dependencies]
   asyncpg = "^0.29.0"  # For PostgreSQL
   aiosqlite = "^0.19.0"  # For SQLite testing
   ```

2. **Create Async Engine**
   ```python
   # database/engine.py
   from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

   async_engine = create_async_engine(
       settings.async_database_url,
       echo=settings.debug
   )
   ```

3. **Update CRUD Base**
   - Create `AsyncCRUDBase` class
   - Convert all CRUD operations to async

4. **Migrate Provider Functions**
   ```python
   # From: di/providers.py
   @injectable(use_cache=False)
   def get_session():
       # Sync session

   # To: api/dependencies.py
   async def get_session() -> AsyncSession:
       # Async session
   ```

#### Deliverables:
- [ ] Async database engine configured
- [ ] AsyncCRUDBase implemented
- [ ] All CRUD classes converted
- [ ] Session provider migrated

### Phase 2: Service Layer - Part 1 (Week 2)
**Goal**: Convert external API services to async

#### Priority Services:
1. **ApifyService** (Heavy HTTP I/O)
2. **RSSFeedService** (Multiple HTTP calls)
3. **WebScraperTool** (Network operations)

#### For Each Service:
1. Remove `@injectable` decorator
2. Update constructor to accept explicit dependencies
3. Convert methods to async
4. Create FastAPI dependency function
5. Update tests

#### Example Migration:
```python
# Before
@injectable(use_cache=False)
class ApifyService:
    def __init__(self, token: str = None):
        self.token = token

    def run_actor(self, actor_id: str):
        # Sync implementation

# After
class ApifyService:
    def __init__(self, token: str):
        self.token = token
        self.client = httpx.AsyncClient()

    async def run_actor(self, actor_id: str):
        # Async implementation
```

#### Deliverables:
- [ ] ApifyService migrated
- [ ] RSSFeedService migrated
- [ ] WebScraperTool migrated
- [ ] All tests updated

### Phase 3: CLI Migration (Week 3)
**Goal**: Migrate CLI to HTTP-based architecture

#### Tasks:
1. **Create CLI HTTP Client**
   - Implement sync client for simple operations
   - Implement async client for batch operations

2. **Create API Endpoints for CLI**
   ```python
   # api/routers/cli.py
   @router.post("/cli/process-feed/{feed_id}")
   async def process_feed_cli(feed_id: int, ...):
       # Implementation for CLI
   ```

3. **Update CLI Commands**
   - Remove all `Depends()` usage
   - Replace with HTTP client calls
   - Add progress indicators

4. **Remove CLI Provider Functions**
   - Delete CLI-specific providers
   - Remove injectable imports from CLI

#### Deliverables:
- [ ] CLI HTTP client implemented
- [ ] All CLI commands migrated
- [ ] CLI-specific endpoints created
- [ ] CLI tests updated

### Phase 4: Service Layer - Part 2 (Week 4)
**Goal**: Complete service migration

#### Remaining Services:
1. **ArticleService**
2. **EntityService**
3. **AnalysisService**
4. **NewsPipelineService**

#### Additional Tasks:
1. Update service composition patterns
2. Implement proper error handling
3. Add transaction management

#### Deliverables:
- [ ] All services migrated to async
- [ ] Service dependencies updated
- [ ] Transaction handling implemented
- [ ] Error handling standardized

### Phase 5: API Endpoints (Week 5)
**Goal**: Update all FastAPI endpoints

#### Tasks:
1. **Update Endpoint Dependencies**
   ```python
   # From
   from local_newsifier.di.providers import get_service

   # To
   from local_newsifier.api.dependencies import get_service
   ```

2. **Convert Endpoints to Async**
   - Add `await` for all async operations
   - Update error handling
   - Handle transactions properly

3. **Remove Old Providers**
   - Delete `di/providers.py`
   - Remove fastapi-injectable imports

#### Deliverables:
- [ ] All endpoints updated
- [ ] Old provider file deleted
- [ ] Import statements cleaned up
- [ ] API tests updated

### Phase 6: Testing and Cleanup (Week 6)
**Goal**: Ensure quality and clean up codebase

#### Tasks:
1. **Update All Tests**
   - ~~Remove `event_loop_fixture`~~ (COMPLETED)
   - ~~Remove `@ci_skip_async`~~ (COMPLETED)
   - Update mocking patterns

2. **Performance Testing**
   - Benchmark async vs sync performance
   - Validate concurrency benefits
   - Check resource usage

3. **Code Cleanup**
   - Remove fastapi-injectable from dependencies
   - Update documentation
   - Clean up imports

#### Deliverables:
- [ ] All tests passing
- [ ] Performance benchmarks complete
- [ ] Documentation updated
- [ ] Dependencies cleaned up

## Rollback Plan

### Phase-Based Rollback
Each phase can be rolled back independently:

1. **Database Layer**: Keep sync and async engines side-by-side
2. **Services**: Maintain dual-mode services during transition
3. **CLI**: Keep both DI and HTTP modes available
4. **Endpoints**: Use feature flags to switch between old/new

### Rollback Procedure
```python
# Feature flags for gradual rollout
class FeatureFlags:
    USE_ASYNC_DB = os.getenv("USE_ASYNC_DB", "false") == "true"
    USE_HTTP_CLI = os.getenv("USE_HTTP_CLI", "false") == "true"
    USE_NATIVE_DI = os.getenv("USE_NATIVE_DI", "false") == "true"
```

## Success Metrics

### Performance Metrics
- [ ] API response time improved by 30%+
- [ ] Concurrent request handling 3x better
- [ ] Database connection pool usage optimized

### Quality Metrics
- [ ] All tests pass without event loop fixtures
- [ ] No `@ci_skip_async` decorators needed
- [ ] Test execution time reduced by 25%+

### Code Metrics
- [ ] Zero imports from `fastapi_injectable`
- [ ] All services use explicit dependency injection
- [ ] Simplified test mocking patterns

## Risk Mitigation

### Risk 1: Breaking Changes
**Mitigation**:
- Maintain backward compatibility during migration
- Use feature flags for gradual rollout
- Comprehensive test coverage

### Risk 2: Performance Regression
**Mitigation**:
- Benchmark each phase
- Monitor production metrics
- Have rollback plan ready

### Risk 3: Team Disruption
**Mitigation**:
- Clear documentation
- Pair programming sessions
- Gradual migration approach

## Daily Checklist

### During Migration
- [ ] All tests pass locally
- [ ] CI/CD pipeline green
- [ ] No new injectable usage added
- [ ] Documentation updated
- [ ] Team notified of changes

### Code Review Checklist
- [ ] No `@injectable` decorators
- [ ] No `use_cache` parameters
- [ ] Explicit dependency injection
- [ ] Async patterns used correctly
- [ ] Tests don't use event loop fixtures

## Communication Plan

### Week 0
- Team meeting to explain migration plan
- Set up dedicated Slack channel
- Create migration dashboard

### Weekly Updates
- Progress against roadmap
- Blockers and solutions
- Performance metrics
- Next week's goals

### Documentation
- Update README with new patterns
- Create migration guide for team
- Document architectural decisions
- Update onboarding materials

## Post-Migration Tasks

### Week 7: Optimization
- [ ] Connection pool tuning
- [ ] Query optimization
- [ ] Caching strategy
- [ ] Load testing

### Week 8: Documentation and Training
- [ ] Complete architecture documentation
- [ ] Team training sessions
- [ ] Update deployment guides
- [ ] Create troubleshooting guide

## Conclusion

This roadmap provides a structured approach to migrating away from FastAPI-Injectable while simultaneously improving the architecture through async operations and CLI-to-HTTP migration. The phased approach minimizes risk while delivering incremental value throughout the migration process.
