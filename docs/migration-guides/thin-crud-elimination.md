# Thin CRUD Wrapper Elimination Guide

## Overview

Several CRUD classes are thin wrappers that only add 1-3 simple query methods to CRUDBase. These can be eliminated by:
1. Using CRUDBase directly
2. Moving query logic to services where it's used

## Identified Thin Wrappers

1. **CRUDAnalysisResult** - 2 methods: `get_by_article`, `get_by_article_and_type`
2. **CRUDEntity** - 3 methods: `get_by_article`, `get_by_text_and_article`, `get_by_date_range_and_types`
3. **CRUDRSSFeed** - 3 methods: `get_by_url`, `get_active_feeds`, `update_last_fetched`

## Migration Strategy

### Option 1: Use CRUDBase Directly

```python
# Before - with CRUDAnalysisResult
from local_newsifier.crud.analysis_result import analysis_result

results = analysis_result.get_by_article(session, article_id=123)

# After - using CRUDBase directly
from local_newsifier.crud.base import CRUDBase
from local_newsifier.models.analysis_result import AnalysisResult

analysis_crud = CRUDBase(AnalysisResult)
results = session.exec(
    select(AnalysisResult).where(AnalysisResult.article_id == 123)
).all()
```

### Option 2: Move Logic to Services

```python
# Before - CRUD method
class CRUDAnalysisResult(CRUDBase[AnalysisResult]):
    def get_by_article(self, db: Session, *, article_id: int) -> List[AnalysisResult]:
        results = db.execute(
            select(AnalysisResult).where(AnalysisResult.article_id == article_id)
        ).all()
        return [row[0] for row in results]

# After - Service method
class AnalysisService:
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.analysis_crud = CRUDBase(AnalysisResult)

    def get_results_for_article(self, article_id: int) -> List[AnalysisResult]:
        with self.session_factory() as session:
            results = session.exec(
                select(AnalysisResult).where(AnalysisResult.article_id == article_id)
            ).all()
            return results
```

## Specific Migrations

### CRUDAnalysisResult → Service

```python
class AnalysisService:
    """Service handles analysis-specific queries."""

    def get_article_analysis(self, article_id: int, analysis_type: Optional[str] = None):
        """Get analysis results for an article."""
        with self.session_factory() as session:
            query = select(AnalysisResult).where(AnalysisResult.article_id == article_id)

            if analysis_type:
                query = query.where(AnalysisResult.analysis_type == analysis_type)

            return session.exec(query).all()
```

### CRUDEntity → Service

```python
class EntityService:
    """Service handles entity-specific queries."""

    def find_entities_in_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        entity_types: Optional[List[str]] = None
    ):
        """Find entities within a date range."""
        with self.session_factory() as session:
            query = (
                select(Entity)
                .join(Article, Entity.article_id == Article.id)
                .where(
                    Article.published_at >= start_date,
                    Article.published_at <= end_date
                )
            )

            if entity_types:
                query = query.where(Entity.entity_type.in_(entity_types))

            return session.exec(query).all()
```

### CRUDRSSFeed → Service

```python
class RSSFeedService:
    """Service handles RSS feed operations."""

    def get_active_feeds(self, limit: int = 100):
        """Get active RSS feeds."""
        with self.session_factory() as session:
            return session.exec(
                select(RSSFeed)
                .where(RSSFeed.is_active == True)
                .limit(limit)
            ).all()

    def mark_feed_fetched(self, feed_id: int):
        """Update last fetched timestamp."""
        with self.session_factory() as session:
            feed = session.get(RSSFeed, feed_id)
            if feed:
                feed.last_fetched_at = datetime.utcnow()
                session.add(feed)
                session.commit()
```

## Benefits

1. **Less code** - Eliminate ~200 lines of wrapper code
2. **Fewer files** - Remove 3 CRUD files
3. **Clearer ownership** - Business logic in services, not CRUD
4. **Better cohesion** - Related queries grouped in services
5. **Simpler testing** - Test business logic, not wrappers

## Provider Updates

Update providers to return CRUDBase instances:

```python
# Before
def get_analysis_result_crud():
    return analysis_result

# After
def get_analysis_result_crud():
    return CRUDBase(AnalysisResult)
```
