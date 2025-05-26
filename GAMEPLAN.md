# Async Migration Game Plan

## Current State Summary

### What's Been Completed
1. **Event Loop Stabilization (Issue #730)** ✅
   - Removed problematic event_loop_fixture causing CI failures
   - Eliminated flaky @ci_skip_async decorators
   - Fixed imports in 20+ test files
   - Updated documentation with modern patterns
   - Tests now pass reliably in CI

2. **Initial Async Foundation (Issue #721)** ✅
   - Created async database session management
   - Implemented async webhook handler (`/webhooks/apify`)
   - Established key async patterns for CRUD and services
   - Fixed timezone handling and session lifecycle issues

### What Remains
1. **28 test files** still import old event_loop_fixture
2. **Only 1 test file** uses proper @pytest.mark.asyncio
3. **Most services** are still synchronous
4. **FastAPI-Injectable** creates async/sync boundary issues
5. **No async HTTP clients** (still using requests instead of httpx)

## Prioritized Action Plan

### Phase 1: Complete Event Loop Cleanup (Week 1)
**Goal:** Remove all remaining event_loop_fixture usage

#### Sprint 1.1: Service Tests (Days 1-2)
Fix 4 service test files:
- `tests/services/test_analysis_service.py`
- `tests/services/test_apify_service_schedules.py`
- `tests/services/test_entity_service.py`
- `tests/services/test_entity_service_extended.py`

**Actions:**
1. Remove event_loop_fixture imports
2. Convert async tests to use @pytest.mark.asyncio
3. Update mocks to use AsyncMock
4. Ensure all tests pass

#### Sprint 1.2: DI Provider Tests (Days 3-4)
Fix 4 DI provider test files:
- `tests/di/test_db_inspect_command_provider.py`
- `tests/di/test_file_writer_provider.py`
- `tests/di/test_rss_parser_provider.py`
- `tests/di/test_sentiment_analyzer_provider.py`

#### Sprint 1.3: High-Impact Tool Tests (Days 5-7)
Start with tools that are I/O bound:
- `tests/tools/test_rss_parser.py`
- `tests/tools/test_web_scraper.py`
- `tests/tools/test_file_writer.py`

### Phase 2: Async Service Migration (Weeks 2-3)
**Goal:** Convert I/O-bound services to async

#### Sprint 2.1: External API Services (Week 2)
1. **ApifyService**
   - Convert to use httpx instead of requests
   - Make all methods async
   - Update existing async webhook handler to use new async service

2. **RSS Feed Service**
   - Convert feedparser operations to async
   - Use httpx for fetching feeds
   - Update database operations to async

3. **Web Scraper Tool**
   - Replace requests with httpx
   - Make scraping methods async
   - Handle BeautifulSoup parsing in thread pool

#### Sprint 2.2: Database Services (Week 3)
1. **ArticleService**
   - Convert all methods to async
   - Use AsyncSession throughout
   - Update CRUD operations

2. **EntityService**
   - Make entity extraction async
   - Convert database queries to async
   - Update relationship tracking

3. **AnalysisService**
   - Convert sentiment analysis workflow
   - Make trend detection async
   - Update result storage

### Phase 3: Remove FastAPI-Injectable (Weeks 4-5)
**Goal:** Simplify dependency injection and remove async/sync conflicts

#### Sprint 3.1: Service Refactoring (Week 4)
1. Remove @injectable decorators from services
2. Convert services to accept dependencies via constructor
3. Create factory functions for service instantiation
4. Update tests to use direct instantiation

#### Sprint 3.2: FastAPI Endpoint Migration (Week 5)
1. Replace injectable providers with FastAPI Depends()
2. Create async dependency functions
3. Remove use_cache=False workarounds
4. Update endpoint signatures

### Phase 4: Complete Async Stack (Weeks 6-7)
**Goal:** Full async implementation across the stack

#### Sprint 4.1: Async Flows (Week 6)
1. Convert all flow orchestration to async
2. Implement concurrent processing with asyncio.gather()
3. Update flow tests to async patterns

#### Sprint 4.2: Async Tools & Optimization (Week 7)
1. Convert remaining tools to async
2. Implement connection pooling for HTTP clients
3. Add async caching where beneficial
4. Performance testing and optimization

### Phase 5: CLI-to-HTTP Migration (Week 8)
**Goal:** Remove direct async/sync conflicts in CLI

1. Implement HTTP client for CLI commands
2. Remove all direct service dependencies from CLI
3. Update CLI tests to use mock HTTP responses
4. Remove CLI-specific DI providers

## Key Implementation Patterns

### Async Service Pattern
```python
class AsyncArticleService:
    def __init__(self, session_factory: Callable[[], AsyncSession]):
        self.session_factory = session_factory
        self.crud = AsyncArticleCRUD()

    async def process_article(self, url: str) -> Article:
        async with self.session_factory() as session:
            # Fetch content
            async with httpx.AsyncClient() as client:
                response = await client.get(url)

            # Process and save
            article = await self.crud.create_async(
                session,
                {"url": url, "content": response.text}
            )

            # Process concurrently
            await asyncio.gather(
                self._extract_entities(session, article),
                self._analyze_sentiment(session, article)
            )

            return article
```

### Async Test Pattern
```python
@pytest.mark.asyncio
async def test_article_service():
    # Setup
    async with AsyncSessionLocal() as session:
        service = AsyncArticleService(lambda: session)

        # Mock HTTP
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock:
            mock.return_value.text = "Article content"

            # Test
            article = await service.process_article("http://example.com")

            # Assert
            assert article.url == "http://example.com"
```

### FastAPI Dependency Pattern
```python
async def get_article_service(
    session: Annotated[AsyncSession, Depends(get_async_session)]
) -> AsyncArticleService:
    return AsyncArticleService(lambda: session)

@router.post("/articles")
async def create_article(
    url: str,
    service: Annotated[AsyncArticleService, Depends(get_article_service)]
):
    article = await service.process_article(url)
    return {"id": article.id, "url": article.url}
```

## Success Metrics

### Phase 1 Completion
- [ ] 0 files importing event_loop_fixture
- [ ] All async tests use @pytest.mark.asyncio
- [ ] No test failures in CI

### Phase 2 Completion
- [ ] All I/O-bound services are async
- [ ] httpx replaces requests everywhere
- [ ] 50%+ performance improvement in API response times

### Phase 3 Completion
- [ ] No @injectable decorators remain
- [ ] All services use constructor injection
- [ ] FastAPI endpoints use native Depends()

### Phase 4 Completion
- [ ] 100% async coverage for I/O operations
- [ ] Concurrent processing implemented
- [ ] Performance benchmarks show improvement

### Phase 5 Completion
- [ ] CLI uses HTTP client exclusively
- [ ] No direct async/sync boundary issues
- [ ] Complete async stack from API to database

## Risk Mitigation

1. **Incremental Migration**
   - Small, focused PRs for each phase
   - Maintain backward compatibility during transition
   - Feature flags for gradual rollout

2. **Comprehensive Testing**
   - Add async integration tests
   - Performance benchmarks before/after
   - Load testing for concurrent operations

3. **Documentation**
   - Update patterns in CLAUDE.md as we go
   - Create migration guides for each component
   - Document new async patterns

## Next Immediate Steps

1. **Today:** Create PR for Phase 1, Sprint 1.1 (service tests)
2. **This Week:** Complete Phase 1 (all event loop cleanup)
3. **Next Week:** Begin Phase 2 with ApifyService async conversion

## Long-term Vision

By completing this migration, we'll have:
- **3x better performance** for concurrent operations
- **Simpler codebase** without DI framework complexity
- **Modern async Python** patterns throughout
- **Foundation for scaling** to handle more traffic
- **Improved developer experience** with clearer code flow
