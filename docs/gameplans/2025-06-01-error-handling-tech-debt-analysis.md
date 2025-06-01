# Error Handling Tech Debt Analysis

## Date: 2025-06-01

## Summary

Analysis of error handling patterns in service files reveals significant technical debt:

1. **Only 1 out of 11 service files** imports and uses the documented error handling decorators
2. **Widespread use of generic `except Exception` catches** instead of specific exception handling
3. **No consistent use of the error handling framework** despite it being well-documented
4. **Direct database operations without proper error handling decorators**

## Findings

### Services Using Proper Error Handling
- ✅ `analysis_service.py` - Uses `@handle_database` decorator correctly

### Services NOT Using Error Handling Decorators
- ❌ `apify_schedule_manager.py` - 10+ generic `except Exception` blocks
- ❌ `apify_service.py` - 15+ generic `except Exception` blocks
- ❌ `apify_source_config_service.py` - 5+ generic `except Exception` blocks
- ❌ `apify_webhook_service.py` - 2 generic `except Exception` blocks
- ❌ `apify_webhook_service_sync.py` - 2 generic `except Exception` blocks
- ❌ `article_service.py` - 1 generic `except Exception` block
- ❌ `entity_service.py` - 5+ generic `except Exception` blocks
- ❌ `news_pipeline_service.py` - 4 generic `except Exception` blocks
- ❌ `rss_feed_service.py` - 2 generic `except Exception` blocks

### Key Issues

1. **Generic Exception Catching**
   - Over 50 instances of `except Exception` across service files
   - No specific error types being caught
   - Violates documented best practice: "Don't catch generic Exception - catch specific exceptions"

2. **Missing Error Decorators**
   - Database operations without `@handle_database`
   - Apify API calls without `@handle_apify`
   - RSS operations without `@handle_rss`
   - Web scraping without `@handle_web_scraper`

3. **Inconsistent Error Handling**
   - Some services use `ServiceError` directly
   - Others just log errors and return None/0
   - No consistent pattern for error propagation

4. **Database Operations at Risk**
   - Direct `session.add()`, `session.commit()`, `session.exec()` without proper error handling
   - Examples in webhook services could lead to data inconsistencies

## Examples of Poor Error Handling

### Example 1: Generic Exception in apify_service.py
```python
except Exception as e:
    logging.error(f"Error calling Apify API: {str(e)}")
    error_details = self._format_error(e, "API Error")
```

### Example 2: Bare Exception in apify_webhook_service.py
```python
except Exception as e:
    logger.error(f"Error creating articles from webhook: {e}")
    # Don't fail the webhook - just log the error
```

### Example 3: Database operations without protection
```python
self.session.add(webhook_raw)
# ... more operations ...
self.session.commit()  # No error handling!
```

## Impact

1. **Debugging Difficulty**: Generic exceptions make it hard to identify root causes
2. **Data Integrity Risk**: Database operations without proper rollback handling
3. **Poor User Experience**: Generic error messages don't help users troubleshoot
4. **Monitoring Issues**: Can't track specific error types for alerting
5. **Technical Debt**: Harder to maintain and refactor code

## Recommendations

1. **Immediate Actions**:
   - Add error handling decorators to all service methods
   - Replace generic `except Exception` with specific exceptions
   - Ensure all database operations use `@handle_database`

2. **Migration Plan**:
   - Start with high-risk services (webhook handlers, database operations)
   - Add proper error handling one service at a time
   - Update tests to verify error handling behavior

3. **Standards Enforcement**:
   - Add linting rules to catch generic exceptions
   - Code review checklist for error handling
   - Update service template to include decorators by default
