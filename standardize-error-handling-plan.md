# Standardizing on the Decorator-based Error Handling Approach

## Overview

This document details the plan to eliminate the `ErrorHandledCRUD` class in favor of the more consistent decorator-based approach (`@handle_database` decorator) for error handling. This will simplify the codebase and reduce duplication of error handling logic.

## Current State

1. **Two parallel approaches exist**:
   - **ErrorHandledCRUD** - A subclass of `CRUDBase` that wraps all CRUD methods with error handling
   - **@handle_database** - A decorator that can be applied to service methods that interact with the database

2. **Duplicate error handling code**:
   - Both approaches convert SQL exceptions to domain-specific exceptions
   - Both implement similar retry logic for transient errors
   - Each has its own error classification logic

3. **Inconsistent usage**:
   - Services already use `@handle_database` (article_service.py, entity_service.py)
   - The `ErrorHandledCRUD` classes are implemented but not fully integrated

## Benefits of Decorator-based Approach

1. **Simpler architecture**:
   - No need for parallel class hierarchies
   - Single, centralized error handling mechanism
   - Error handling clearly visible at the call site

2. **Better separation of concerns**:
   - CRUD classes handle data access only
   - Services handle business logic and error handling
   - Clearer responsibility boundaries

3. **Reduced code duplication**:
   - One unified error handling mechanism
   - Consistent error messaging
   - Central place for improvements

4. **Better integration with the architecture**:
   - Aligns better with the service-oriented architecture
   - Services can customize retry behavior as needed
   - More consistent with FastAPI error handling approach

## Implementation Plan

### Phase 1: Remove ErrorHandledCRUD References

1. **Update CRUD initialization**:
   - Remove error_handled_article.py and similar files
   - Ensure all code references CRUDBase implementations, not ErrorHandledCRUD

2. **Delete unneeded files**:
   - error_handled_base.py
   - error_handled_article.py
   - error_handled_entity.py
   - error_handled_feed_processing_log.py
   - error_handled_rss_feed.py

3. **Update error_handling.py**:
   - Keep the error response model for API endpoints
   - Keep HTTP exception conversion logic
   - Remove references to ErrorHandledCRUD

### Phase 2: Standardize Service Error Handling

1. **Audit all services**:
   - Ensure key service methods use `@handle_database` decorator
   - Add decorator to any methods missing it
   - Consistent error handling in article_service.py, entity_service.py, etc.

2. **Document approach**:
   - Update error_handling.md to clarify the standard pattern
   - Add examples showing service methods with `@handle_database`
   - Document when and how to use the decorator

3. **Testing**:
   - Ensure all existing tests still pass
   - Add tests for error scenarios in services
   - Verify error classification is working correctly

### Phase 3: API Error Handling Standardization

1. **API Endpoints**:
   - Ensure API endpoints properly catch ServiceError
   - Return standardized error responses
   - Use consistent status codes

2. **Documentation**:
   - Add examples for API error handling
   - Document the error response format
   - Show integration between service and API layers

## Example Patterns

### Standard Service Method Pattern

```python
from local_newsifier.errors import handle_database

class ArticleService:
    
    @handle_database
    def get_article(self, article_id: int):
        """Get article by ID with database error handling."""
        with self.session_factory() as session:
            article = self.article_crud.get(session, id=article_id)
            if not article:
                # This will be converted to ServiceError with type="not_found"
                raise ValueError(f"Article with ID {article_id} not found")
            return article
```

### API Endpoint Pattern

```python
from fastapi import Depends, HTTPException
from local_newsifier.errors import ServiceError

@router.get("/articles/{article_id}")
def get_article(
    article_id: int,
    article_service: ArticleService = Depends(get_article_service)
):
    """Get article by ID endpoint."""
    try:
        return article_service.get_article(article_id)
    except ServiceError as e:
        if e.error_type == "not_found":
            raise HTTPException(status_code=404, detail=f"Article not found")
        # Convert other error types to appropriate status codes
        raise HTTPException(status_code=500, detail=str(e))
```

## Timeline

1. **Phase 1 (Remove ErrorHandledCRUD)**: 1-2 days
2. **Phase 2 (Standardize Service Error Handling)**: 2-3 days
3. **Phase 3 (API Error Handling)**: 1-2 days

Total estimated time: 4-7 days