# Issue: API Dependency Layer Enhancement

## Title
Enhance API Dependency Layer with Comprehensive DI Support

## Description
The API dependency layer needs improvements to fully leverage the dependency injection system. While the current implementation provides basic dependency resolution for core services, it should be expanded to include all registered services and flows, and incorporate request-scoped container support.

## Current Status
Currently, the API dependencies layer only provides access to:
- get_session() for database sessions
- get_article_service() for the ArticleService
- get_rss_feed_service() for the RSSFeedService

## Tasks
1. Add dependencies for all remaining services:
   - get_entity_service() - For entity management
   - get_news_pipeline_service() - For pipeline operations
   - get_analysis_service() - For data analysis

2. Add dependencies for accessing flow classes:
   - get_entity_tracking_flow()
   - get_news_pipeline_flow()
   - get_trend_analysis_flow()
   - get_public_opinion_flow()
   - get_rss_scraping_flow()

3. Implement request-scoped container functionality:
   - Create a request-specific container accessor
   - Properly handle request lifecycle with container
   - Ensure resources are cleaned up after request completion

4. Improve error handling and logging:
   - Add proper fallbacks for dependency resolution failures
   - Implement detailed logging for dependency resolution
   - Add consistency checks to prevent runtime errors

5. Standardize dependency patterns:
   - Create consistent interfaces for all dependencies
   - Document usage patterns in function docstrings
   - Add type annotations for better IDE support

## Acceptance Criteria
- All services and flows are accessible through dedicated dependency functions
- Request scoping is properly implemented with resource cleanup
- Error handling provides useful feedback and graceful fallbacks
- API routes can use any registered service or flow through dependencies
- Test coverage for API dependencies is 90% or higher

## Technical Context
- The current dependency implementation is in `src/local_newsifier/api/dependencies.py`
- The container instance is available in `src/local_newsifier/container.py`
- FastAPI dependency system is used to inject dependencies into route handlers
