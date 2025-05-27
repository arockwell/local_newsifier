# Documentation Update Plan

## Overview
Comprehensive documentation update to reflect architectural changes, new patterns, and current best practices.

## Priority Documentation Updates

### 1. Architecture Documentation
**Files to update:**
- `CLAUDE.md` - Primary developer guide
- `docs/di_architecture.md` - Dependency injection patterns
- `docs/dependency_injection.md` - DI usage guide

**Changes needed:**
- Remove all async pattern references
- Document sync-only approach
- Update code examples to sync patterns
- Remove fastapi-injectable async references
- Add migration notes from async to sync

### 2. API Documentation
**Files to update:**
- `src/local_newsifier/api/CLAUDE.md`
- Create `docs/api_guide.md`

**Changes needed:**
- Document all sync endpoints
- Remove async endpoint examples
- Add request/response examples
- Document authentication flow
- Add webhook integration guide

### 3. Development Guides
**Files to update/create:**
- `docs/development_guide.md` (new)
- `docs/testing_guide.md` (update)
- `docs/python_setup.md` (update)

**Content to add:**
- Sync-only development patterns
- Testing sync code
- Common pitfalls to avoid
- Performance considerations
- Debugging techniques

### 4. Deployment Documentation
**Files to update:**
- `docs/plans/deployment-configuration.md`
- `README.md` deployment section
- Create `docs/deployment_guide.md`

**Changes needed:**
- Remove Celery configuration
- Update Procfile documentation
- Simplify Railway deployment
- Document environment variables
- Add monitoring setup

### 5. CLI Documentation
**Files to update:**
- `README_CLI.md`
- `src/local_newsifier/cli/CLAUDE.md`

**Changes needed:**
- Update command examples
- Document HTTP-based CLI (if implemented)
- Add troubleshooting section
- Update configuration options

### 6. Service Documentation
**Create service-specific docs:**
- `docs/services/article_service.md`
- `docs/services/entity_service.md`
- `docs/services/apify_service.md`
- `docs/services/rss_feed_service.md`

**Content for each:**
- Service responsibilities
- Key methods and usage
- Integration patterns
- Error handling
- Testing approaches

### 7. Migration Guides
**Create migration documentation:**
- `docs/migrations/async_to_sync.md`
- `docs/migrations/celery_removal.md`
- `docs/migrations/fastapi_injectable_removal.md`

**Content:**
- Step-by-step migration instructions
- Before/after code examples
- Common issues and solutions
- Rollback procedures

### 8. Troubleshooting Documentation
**Create/update:**
- `docs/troubleshooting.md` (update)
- `docs/common_errors.md` (new)
- `docs/performance_tuning.md` (new)

**Content:**
- Common error messages and fixes
- Performance optimization tips
- Database query optimization
- Memory usage patterns

### 9. Code Examples
**Update all examples in:**
- `docs/examples/`
- `docs/injectable_examples.md`
- `tests/examples/`

**Changes:**
- Convert all async examples to sync
- Add new pattern examples
- Include error handling examples
- Show testing patterns

### 10. README Updates
**Files:**
- `README.md` (main)
- Module-specific READMEs

**Updates needed:**
- Reflect sync-only architecture
- Update installation instructions
- Simplify quickstart guide
- Update feature list
- Fix broken links

## Documentation Standards
1. **Code examples must:**
   - Be executable
   - Include imports
   - Show error handling
   - Follow project patterns

2. **Each guide should have:**
   - Clear overview
   - Prerequisites
   - Step-by-step instructions
   - Troubleshooting section
   - Related documentation links

3. **Maintain consistency:**
   - Use same terminology
   - Follow markdown standards
   - Include update timestamps
   - Version documentation

## Priority Order
1. CLAUDE.md and architecture docs (Week 1)
2. API and deployment docs (Week 2)
3. Service documentation (Week 3)
4. Migration and troubleshooting guides (Week 4)
5. Examples and README updates (Week 5)

## Success Criteria
- No references to deprecated patterns
- All code examples work
- Clear migration paths documented
- Troubleshooting covers common issues
- New developers can onboard easily
