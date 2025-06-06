# Local Newsifier Refactoring Gameplan

## Overview

This gameplan provides a step-by-step approach to refactoring the Local Newsifier codebase, addressing the critical issues identified in the analysis while minimizing disruption to ongoing development.

## Refactoring Phases

### Phase 1: Critical Fixes (Week 1)
**Goal**: Stabilize the system by removing async complexity and fixing immediate issues

#### Day 1-2: Complete Sync-Only Migration
1. **Remove all async webhook handlers**
   ```bash
   # Files to fix:
   - src/local_newsifier/api/routers/webhooks.py
   - src/local_newsifier/services/apify_webhook_service.py
   - tests/api/test_webhooks.py
   ```

2. **Convert async functions to sync**
   - Search for all `async def` and convert to `def`
   - Replace `await` calls with synchronous equivalents
   - Update httpx async clients to requests or httpx sync

3. **Fix test infrastructure**
   - Remove async test fixtures
   - Update test patterns to sync-only
   - Remove pytest-asyncio dependency

#### Day 3-4: Standardize Session Handling
1. **Create session management pattern**
   ```python
   # src/local_newsifier/services/base.py
   class BaseService:
       def __init__(self, session_factory=None):
           self.session_factory = session_factory or get_session

       def with_session(self, func):
           """Decorator for session management"""
           def wrapper(*args, **kwargs):
               with self.session_factory() as session:
                   return func(session, *args, **kwargs)
           return wrapper
   ```

2. **Update all services to use consistent pattern**
   - Always pass session as first parameter
   - Use context managers consistently
   - Never return SQLModel objects across boundaries

#### Day 5: Fix Critical Bugs
1. **Fix webhook processing errors**
   - Ensure proper error handling
   - Add logging for debugging
   - Test with real Apify webhooks

2. **Resolve session boundary issues**
   - Return IDs instead of objects
   - Add explicit session commits
   - Fix "Instance not bound" errors

### Phase 2: Architectural Consolidation (Week 2-3)

#### Week 2: Consolidate Dependency Injection
1. **Create unified factory pattern**
   ```python
   # src/local_newsifier/factories.py
   class ServiceFactory:
       _instances = {}

       @classmethod
       def get_service(cls, service_type: Type[T], session: Session) -> T:
           """Get or create service instance"""
           key = f"{service_type.__name__}_{id(session)}"
           if key not in cls._instances:
               cls._instances[key] = cls._create_service(service_type, session)
           return cls._instances[key]
   ```

2. **Remove fastapi-injectable**
   - Strip `@injectable` decorators
   - Update imports in all files
   - Modify CLI to use new factory

3. **Update dependency providers**
   - Consolidate `di/providers.py` and `api/dependencies.py`
   - Create single source of truth
   - Update all references

#### Week 3: Standardize Service Patterns
1. **Implement base service class**
   ```python
   class BaseService:
       def execute(self, operation: str, **params) -> ServiceResult:
           """Standard execution pattern"""
           session = params.pop('session', None)
           if not session:
               with self.session_factory() as session:
                   return self._execute_with_session(session, operation, **params)
           return self._execute_with_session(session, operation, **params)
   ```

2. **Create consistent return types**
   ```python
   @dataclass
   class ServiceResult:
       success: bool
       data: Optional[Dict[str, Any]] = None
       error: Optional[str] = None
       metadata: Dict[str, Any] = field(default_factory=dict)
   ```

3. **Implement error handling decorator**
   ```python
   def handle_errors(operation: str):
       def decorator(func):
           @functools.wraps(func)
           def wrapper(self, *args, **kwargs):
               try:
                   return func(self, *args, **kwargs)
               except ServiceError:
                   raise
               except Exception as e:
                   logger.error(f"{operation} failed: {e}")
                   raise ServiceError(operation, e)
           return wrapper
       return decorator
   ```

### Phase 3: Performance Optimization (Week 4-5)

#### Week 4: Database Optimization
1. **Add missing indexes**
   ```python
   # Migration to add indexes
   def upgrade():
       op.create_index('idx_article_published', 'articles', ['published_at'])
       op.create_index('idx_article_status', 'articles', ['status'])
       op.create_index('idx_article_status_published', 'articles', ['status', 'published_at'])
   ```

2. **Implement eager loading**
   ```python
   def get_articles_with_entities(session: Session, limit: int = 100):
       return session.exec(
           select(Article)
           .options(selectinload(Article.entities))
           .options(selectinload(Article.analysis_results))
           .limit(limit)
       ).all()
   ```

3. **Add query optimization**
   - Profile slow queries
   - Add appropriate joins
   - Batch operations where possible

#### Week 5: Implement Caching
1. **Add caching layer**
   ```python
   # src/local_newsifier/cache.py
   class CacheManager:
       def __init__(self, ttl: int = 3600):
           self._cache = {}
           self._ttl = ttl

       def get_or_set(self, key: str, factory: Callable):
           if key in self._cache:
               return self._cache[key]
           value = factory()
           self._cache[key] = value
           return value
   ```

2. **Cache expensive operations**
   - Entity resolution results
   - NLP processing outputs
   - Aggregated statistics

### Phase 4: Long-term Improvements (Month 2+)

#### Month 2: CLI to API Migration
1. **Design API client**
   ```python
   class NewsifierAPIClient:
       def __init__(self, base_url: str):
           self.base_url = base_url
           self.session = requests.Session()

       def process_feed(self, feed_id: int):
           response = self.session.post(f"{self.base_url}/feeds/{feed_id}/process")
           return response.json()
   ```

2. **Migrate CLI commands**
   - Start with simple commands (list, show)
   - Move to complex operations
   - Maintain backward compatibility

3. **Add authentication**
   - Implement API key system
   - Add to CLI configuration
   - Secure endpoints

#### Month 3: Advanced Features
1. **Background task management**
   - Implement task queue (without Celery)
   - Use FastAPI BackgroundTasks
   - Add progress tracking

2. **Monitoring and metrics**
   - Add performance metrics
   - Implement health checks
   - Create dashboards

## Implementation Guidelines

### Testing Strategy
1. **Write tests for new patterns first**
2. **Maintain test coverage above 90%**
3. **Use TDD for refactoring**

### Migration Process
1. **Feature flags for gradual rollout**
   ```python
   FEATURES = {
       'use_new_di': os.getenv('USE_NEW_DI', 'false').lower() == 'true',
       'use_caching': os.getenv('USE_CACHING', 'false').lower() == 'true',
   }
   ```

2. **Parallel implementation**
   - Keep old code working
   - Implement new alongside
   - Switch when stable

3. **Rollback plan**
   - Tag releases before major changes
   - Document rollback procedures
   - Test rollback process

### Communication Plan
1. **Daily updates during critical phases**
2. **Weekly progress reports**
3. **Documentation updates with each phase**

## Success Metrics

### Phase 1 Success Criteria
- [ ] All async code removed
- [ ] No async-related test failures
- [ ] Webhook processing working reliably
- [ ] No session boundary errors

### Phase 2 Success Criteria
- [ ] Single DI pattern throughout
- [ ] Consistent service patterns
- [ ] Reduced code duplication by 50%
- [ ] All tests passing

### Phase 3 Success Criteria
- [ ] Query performance improved by 30%
- [ ] Cache hit rate > 80%
- [ ] Response times < 200ms for common operations

### Phase 4 Success Criteria
- [ ] CLI fully migrated to API calls
- [ ] Background tasks processing reliably
- [ ] Monitoring in place with alerts

## Risk Mitigation

### High-Risk Changes
1. **Async removal**: Test thoroughly in staging
2. **DI migration**: Use feature flags
3. **Database changes**: Test migrations carefully

### Contingency Plans
1. **If async removal breaks features**: Implement sync workarounds
2. **If DI migration causes issues**: Maintain dual system temporarily
3. **If performance degrades**: Add caching incrementally

## Timeline Summary

```
Week 1: Critical Fixes
- Day 1-2: Sync-only migration
- Day 3-4: Session standardization
- Day 5: Bug fixes

Week 2-3: Architectural Consolidation
- Week 2: DI consolidation
- Week 3: Service standardization

Week 4-5: Performance Optimization
- Week 4: Database optimization
- Week 5: Caching implementation

Month 2+: Long-term Improvements
- Month 2: CLI to API migration
- Month 3: Advanced features
```

## Next Steps

1. **Get team buy-in on the plan**
2. **Create tracking issues for each phase**
3. **Set up monitoring for success metrics**
4. **Begin Phase 1 implementation**

## Conclusion

This gameplan provides a structured approach to addressing the architectural issues while maintaining system stability. The phased approach allows for continuous delivery while systematically improving the codebase. Success depends on disciplined execution and clear communication throughout the process.
