# Technical Debt Reduction Knowledge Base

## Overview
This document consolidates all knowledge about technical debt in the Local Newsifier project, including identification, prioritization, and remediation strategies.

## Major Technical Debt Areas

### 1. Dependency Management

#### Offline Installation Issues
**Problem**: Pre-built wheels don't cover all dependencies, causing installation failures in offline environments.

**Root Causes**:
- Version mismatches between requirements files
- Missing platform-specific wheels
- Incorrect wheel organization
- Poetry vs pip dependency resolution differences

**Solution Strategy**:
```bash
# Comprehensive wheel building script
#!/bin/bash
set -euo pipefail

# Define platforms
PLATFORMS=("manylinux2014_x86_64" "manylinux2014_aarch64" "macosx_11_0_arm64")

# Build wheels for all platforms
for platform in "${PLATFORMS[@]}"; do
    echo "Building wheels for $platform..."

    # Create platform directory
    mkdir -p "wheels/$platform"

    # Generate consolidated requirements
    poetry export -f requirements.txt --without-hashes > temp_requirements.txt

    # Download wheels
    pip download \
        --platform "$platform" \
        --python-version 312 \
        --only-binary :all: \
        --dest "wheels/$platform" \
        -r temp_requirements.txt

    # Verify completeness
    pip install --dry-run \
        --find-links "wheels/$platform" \
        --no-index \
        -r temp_requirements.txt
done

# Create manifest
find wheels -name "*.whl" | sort > wheels/manifest.txt
```

**Validation Process**:
```python
# verify_wheels.py
import subprocess
import sys
from pathlib import Path

def verify_offline_install(wheel_dir: Path, requirements: Path):
    """Verify offline installation works."""
    cmd = [
        sys.executable, "-m", "pip", "install",
        "--no-index",
        "--find-links", str(wheel_dir),
        "-r", str(requirements),
        "--dry-run"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Verification failed:\n{result.stderr}")
        missing = extract_missing_packages(result.stderr)
        print(f"Missing packages: {missing}")
        return False

    return True
```

#### Version Conflicts
**Problem**: Different versions specified across requirements files

**Detection Script**:
```python
# check_version_conflicts.py
from packaging.requirements import Requirement
from collections import defaultdict

def check_version_conflicts():
    """Find version conflicts across requirement files."""
    files = [
        "requirements.txt",
        "requirements-dev.txt",
        "pyproject.toml"
    ]

    packages = defaultdict(list)

    # Parse all requirements
    for file in files:
        reqs = parse_requirements(file)
        for req in reqs:
            packages[req.name].append((file, req.specifier))

    # Find conflicts
    conflicts = []
    for package, specs in packages.items():
        if len(set(str(s[1]) for s in specs)) > 1:
            conflicts.append({
                'package': package,
                'specifications': specs
            })

    return conflicts
```

**Resolution Strategy**:
1. Single source of truth: Use pyproject.toml
2. Generate other files from poetry export
3. Pin versions for reproducibility
4. Regular dependency updates with testing

### 2. Test Infrastructure

#### Event Loop Issues
**Problem**: Async tests fail in CI due to event loop conflicts

**Root Cause Analysis**:
```python
# Event loop conflict scenario
# 1. pytest-asyncio creates an event loop
# 2. fastapi-injectable tries to access it from different thread
# 3. Tests fail with "attached to different loop" error
```

**Comprehensive Fix**:
```python
# tests/fixtures/async_fixtures.py
import asyncio
import pytest
from unittest.mock import AsyncMock, patch

@pytest.fixture(scope="function")
def event_loop():
    """Create an event loop for each test function."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop

    # Clean up
    try:
        _cancel_all_tasks(loop)
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.run_until_complete(loop.shutdown_default_executor())
    finally:
        loop.close()

def _cancel_all_tasks(loop):
    """Cancel all pending tasks."""
    tasks = asyncio.all_tasks(loop)
    for task in tasks:
        task.cancel()

    loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))

# Async test helper
class AsyncTestHelper:
    @staticmethod
    def mock_async_dependency(return_value):
        """Create a properly mocked async dependency."""
        mock = AsyncMock(return_value=return_value)
        mock._is_coroutine = lambda: True
        return mock

    @staticmethod
    async def run_with_timeout(coro, timeout=5):
        """Run coroutine with timeout."""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            pytest.fail(f"Test timed out after {timeout} seconds")
```

#### Slow Test Execution
**Problem**: Test suite takes too long to run

**Analysis Tool**:
```python
# identify_slow_tests.py
import json
import pytest
from datetime import datetime

class TestTimer:
    def __init__(self):
        self.results = []

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item, call):
        outcome = yield
        report = outcome.get_result()

        if report.when == "call":
            self.results.append({
                'test': item.nodeid,
                'duration': report.duration,
                'outcome': report.outcome
            })

    def generate_report(self):
        # Sort by duration
        slow_tests = sorted(
            self.results,
            key=lambda x: x['duration'],
            reverse=True
        )[:20]

        print("\nTop 20 Slowest Tests:")
        for test in slow_tests:
            print(f"{test['duration']:.2f}s - {test['test']}")
```

**Optimization Strategies**:
1. **Parallel Execution**:
   ```bash
   # Use pytest-xdist for parallel execution
   pytest -n auto  # Auto-detect CPU cores
   pytest -n 4     # Use 4 workers
   ```

2. **Database Optimization**:
   ```python
   @pytest.fixture(scope="session")
   def db_session():
       """Reuse database session across tests."""
       # Create test database once
       engine = create_engine("postgresql://test")
       Base.metadata.create_all(engine)

       # Create session
       Session = sessionmaker(bind=engine)
       session = Session()

       yield session

       # Cleanup
       session.close()
       Base.metadata.drop_all(engine)
   ```

3. **Mock External Services**:
   ```python
   @pytest.fixture(autouse=True)
   def mock_external_services():
       """Automatically mock all external services."""
       with patch.multiple(
           'local_newsifier.services',
           ApifyClient=Mock(),
           requests=Mock(),
           redis=Mock()
       ):
           yield
   ```

### 3. Code Quality Issues

#### Circular Dependencies
**Problem**: Modules importing each other causing import errors

**Detection Tool**:
```python
# detect_circular_imports.py
import ast
import os
from collections import defaultdict
from pathlib import Path

class ImportAnalyzer(ast.NodeVisitor):
    def __init__(self, module_path):
        self.module_path = module_path
        self.imports = []

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)

    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.append(node.module)

def find_circular_dependencies(src_dir):
    """Find circular import dependencies."""
    dependencies = defaultdict(set)

    # Build dependency graph
    for py_file in Path(src_dir).rglob("*.py"):
        module = str(py_file.relative_to(src_dir)).replace("/", ".")[:-3]

        with open(py_file) as f:
            tree = ast.parse(f.read())

        analyzer = ImportAnalyzer(module)
        analyzer.visit(tree)

        for imp in analyzer.imports:
            if imp.startswith("local_newsifier"):
                dependencies[module].add(imp)

    # Find cycles
    cycles = []
    visited = set()

    def find_cycle(module, path):
        if module in path:
            cycle_start = path.index(module)
            cycles.append(path[cycle_start:])
            return

        if module in visited:
            return

        visited.add(module)
        path.append(module)

        for dep in dependencies.get(module, []):
            find_cycle(dep, path[:])

    for module in dependencies:
        find_cycle(module, [])

    return cycles
```

**Resolution Patterns**:
1. **Interface Segregation**:
   ```python
   # interfaces/service_interface.py
   from abc import ABC, abstractmethod

   class ServiceInterface(ABC):
       @abstractmethod
       def process(self, data): pass

   # services/implementation.py
   from interfaces.service_interface import ServiceInterface

   class ServiceImpl(ServiceInterface):
       def process(self, data):
           return processed_data
   ```

2. **Lazy Imports**:
   ```python
   # Avoid circular imports with lazy loading
   def get_service():
       from .services import Service  # Import inside function
       return Service()
   ```

3. **Dependency Inversion**:
   ```python
   # High-level module defines interface
   class DataProcessor:
       def __init__(self, storage: StorageInterface):
           self.storage = storage

   # Low-level module implements interface
   class DatabaseStorage(StorageInterface):
       def save(self, data):
           # Implementation
   ```

#### Missing Validation
**Problem**: Data validation gaps causing runtime errors

**Comprehensive Validation Strategy**:
```python
# models/validation.py
from pydantic import BaseModel, validator, Field
from typing import Optional, List
import re

class ArticleValidation(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=10)
    url: str = Field(..., regex=r'^https?://')
    author: Optional[str] = Field(None, max_length=200)
    published_at: Optional[datetime] = None

    @validator('title')
    def clean_title(cls, v):
        # Remove excessive whitespace
        v = ' '.join(v.split())
        # Remove control characters
        v = ''.join(c for c in v if c.isprintable())
        return v

    @validator('url')
    def validate_url(cls, v):
        # Additional URL validation
        if not is_valid_domain(v):
            raise ValueError("Invalid domain")
        return v

    @validator('content')
    def validate_content(cls, v):
        # Check for minimum word count
        word_count = len(v.split())
        if word_count < 10:
            raise ValueError(f"Content too short: {word_count} words")
        return v

# Apply validation in CRUD operations
class ArticleCRUD(CRUDBase):
    def create(self, session: Session, article_data: dict) -> Article:
        # Validate before saving
        validated = ArticleValidation(**article_data)

        # Create model instance
        article = Article(**validated.dict())

        # Save to database
        session.add(article)
        session.commit()

        return article
```

### 4. Performance Issues

#### Database Query Optimization
**Problem**: N+1 queries and inefficient database access

**Query Analysis Tool**:
```python
# utils/query_analyzer.py
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time
import logging

class QueryAnalyzer:
    def __init__(self):
        self.queries = []
        self.threshold = 0.1  # 100ms

    def enable(self):
        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters,
                                 context, executemany):
            conn.info.setdefault('query_start_time', []).append(time.time())

        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters,
                               context, executemany):
            total = time.time() - conn.info['query_start_time'].pop(-1)

            self.queries.append({
                'statement': statement,
                'parameters': parameters,
                'duration': total
            })

            if total > self.threshold:
                logging.warning(
                    f"Slow query ({total:.3f}s): {statement[:100]}..."
                )

    def report(self):
        # Find duplicate queries (N+1 problem)
        query_counts = {}
        for q in self.queries:
            key = q['statement']
            query_counts[key] = query_counts.get(key, 0) + 1

        print("\nPotential N+1 Queries:")
        for query, count in query_counts.items():
            if count > 10:
                print(f"  {count}x: {query[:80]}...")

        # Find slow queries
        slow_queries = sorted(
            self.queries,
            key=lambda x: x['duration'],
            reverse=True
        )[:10]

        print("\nTop 10 Slowest Queries:")
        for q in slow_queries:
            print(f"  {q['duration']:.3f}s: {q['statement'][:80]}...")
```

**Optimization Patterns**:
1. **Eager Loading**:
   ```python
   # Avoid N+1 with eager loading
   articles = session.query(Article)\
       .options(selectinload(Article.entities))\
       .options(selectinload(Article.analysis_results))\
       .all()
   ```

2. **Query Batching**:
   ```python
   # Batch queries for better performance
   def get_articles_with_stats(article_ids: List[int]):
       # Single query for all articles
       articles = session.query(Article)\
           .filter(Article.id.in_(article_ids))\
           .all()

       # Single query for all stats
       stats = session.query(
           ArticleStats.article_id,
           func.count(Entity.id).label('entity_count'),
           func.avg(AnalysisResult.sentiment_score).label('avg_sentiment')
       ).join(Entity).join(AnalysisResult)\
       .filter(ArticleStats.article_id.in_(article_ids))\
       .group_by(ArticleStats.article_id)\
       .all()

       # Combine results
       stats_map = {s.article_id: s for s in stats}

       return [
           {
               'article': article,
               'stats': stats_map.get(article.id)
           }
           for article in articles
       ]
   ```

3. **Database Indexes**:
   ```python
   # Add indexes for common queries
   class Article(SQLModel, table=True):
       __tablename__ = "articles"

       id: Optional[int] = Field(default=None, primary_key=True)
       url: str = Field(unique=True, index=True)
       published_at: datetime = Field(index=True)

       __table_args__ = (
           Index('idx_published_url', 'published_at', 'url'),
           Index('idx_content_search', 'title', 'content',
                 postgresql_using='gin')
       )
   ```

### 5. Error Handling

#### Incomplete Error Recovery
**Problem**: Services fail without proper recovery mechanisms

**Comprehensive Error Handling Framework**:
```python
# services/error_handling.py
from typing import TypeVar, Callable, Optional
from functools import wraps
import logging

T = TypeVar('T')

class RetryPolicy:
    def __init__(self,
                 max_attempts: int = 3,
                 backoff_factor: float = 2.0,
                 max_delay: float = 60.0,
                 exceptions: tuple = (Exception,)):
        self.max_attempts = max_attempts
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
        self.exceptions = exceptions

def with_retry(policy: RetryPolicy):
    """Decorator for automatic retry with exponential backoff."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            delay = 1.0

            for attempt in range(policy.max_attempts):
                try:
                    return func(*args, **kwargs)

                except policy.exceptions as e:
                    last_exception = e

                    if attempt < policy.max_attempts - 1:
                        sleep_time = min(delay, policy.max_delay)
                        logging.warning(
                            f"Attempt {attempt + 1} failed: {e}. "
                            f"Retrying in {sleep_time}s..."
                        )
                        time.sleep(sleep_time)
                        delay *= policy.backoff_factor
                    else:
                        logging.error(
                            f"All {policy.max_attempts} attempts failed"
                        )

            raise last_exception

        return wrapper
    return decorator

# Circuit breaker pattern
class CircuitBreaker:
    def __init__(self,
                 failure_threshold: int = 5,
                 recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.is_open = False

    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        if self.is_open:
            if self._should_attempt_reset():
                self.is_open = False
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except Exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )

    def _on_success(self):
        self.failure_count = 0
        self.last_failure_time = None

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.is_open = True
            logging.error("Circuit breaker opened")
```

## Debt Prioritization Matrix

### High Priority (Critical)
1. **Offline Installation**: Blocking deployments
2. **Event Loop Issues**: Causing CI failures
3. **Database Performance**: User-facing impact

### Medium Priority (Important)
1. **Circular Dependencies**: Development friction
2. **Test Performance**: Slowing development
3. **Validation Gaps**: Data quality issues

### Low Priority (Nice to Have)
1. **Code Duplication**: Maintenance burden
2. **Documentation Gaps**: Onboarding friction
3. **Deprecated Dependencies**: Future risk

## Remediation Roadmap

### Phase 1: Critical Fixes (2 weeks)
- [ ] Fix offline installation
- [ ] Resolve event loop issues
- [ ] Optimize critical queries

### Phase 2: Quality Improvements (4 weeks)
- [ ] Eliminate circular dependencies
- [ ] Implement comprehensive validation
- [ ] Speed up test suite

### Phase 3: Long-term Health (Ongoing)
- [ ] Automated debt tracking
- [ ] Regular dependency updates
- [ ] Performance monitoring

## Monitoring Technical Debt

### Automated Metrics
```python
# scripts/tech_debt_report.py
def generate_tech_debt_report():
    """Generate comprehensive technical debt report."""

    report = {
        'code_quality': analyze_code_quality(),
        'test_coverage': get_test_coverage(),
        'dependency_health': check_dependencies(),
        'performance_metrics': collect_performance_metrics(),
        'security_issues': run_security_scan()
    }

    # Calculate debt score
    debt_score = calculate_debt_score(report)

    # Generate recommendations
    recommendations = generate_recommendations(report)

    return {
        'report': report,
        'debt_score': debt_score,
        'recommendations': recommendations
    }
```

## References

- [Martin Fowler on Technical Debt](https://martinfowler.com/bliki/TechnicalDebt.html)
- [SonarQube Technical Debt](https://docs.sonarqube.org/latest/user-guide/concepts/)
- Project Issues: #84, #126, #169, #212, #255, #298, #341, #384, #427, #470, #513, #556, #599, #642, #685, #706, #713
