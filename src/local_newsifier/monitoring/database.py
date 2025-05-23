"""Database performance monitoring with SQLAlchemy event listeners."""

import logging
import time
from typing import Any, Dict, Optional

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import Pool

from local_newsifier.monitoring.metrics import (db_active_connections, db_connection_pool_size,
                                                db_query_duration, db_query_total, errors_total)

logger = logging.getLogger(__name__)

# Store query start times
_query_start_times: Dict[int, float] = {}


def setup_database_monitoring(engine: Engine):
    """Set up SQLAlchemy event listeners for database monitoring.

    Args:
        engine: SQLAlchemy engine instance
    """
    logger.info("Setting up database performance monitoring")

    # Monitor query execution
    event.listen(Engine, "before_cursor_execute", _before_cursor_execute, once=False)
    event.listen(Engine, "after_cursor_execute", _after_cursor_execute, once=False)

    # Monitor connection pool
    event.listen(Pool, "connect", _on_connect, once=False)
    event.listen(Pool, "checkout", _on_checkout, once=False)
    event.listen(Pool, "checkin", _on_checkin, once=False)

    # Monitor errors
    event.listen(Engine, "handle_error", _handle_db_error, once=False)
    event.listen(Engine, "handle_dbapi_exception", _handle_db_error, once=False)

    # Initialize pool metrics
    _update_pool_metrics(engine)


def _before_cursor_execute(
    conn: Any,
    cursor: Any,
    statement: str,
    parameters: Any,
    context: Optional[Any],
    executemany: bool,
):
    """Record query start time.

    Args:
        conn: Database connection
        cursor: Database cursor
        statement: SQL statement
        parameters: Query parameters
        context: Execution context
        executemany: Whether executemany is used
    """
    cursor_id = id(cursor)
    _query_start_times[cursor_id] = time.time()


def _after_cursor_execute(
    conn: Any,
    cursor: Any,
    statement: str,
    parameters: Any,
    context: Optional[Any],
    executemany: bool,
):
    """Record query execution time and metrics.

    Args:
        conn: Database connection
        cursor: Database cursor
        statement: SQL statement
        parameters: Query parameters
        context: Execution context
        executemany: Whether executemany is used
    """
    cursor_id = id(cursor)
    start_time = _query_start_times.pop(cursor_id, None)

    if start_time is None:
        return

    duration = time.time() - start_time

    # Extract operation and table from SQL statement
    operation, table = _parse_sql_statement(statement)

    # Record metrics
    labels = {"operation": operation, "table": table}

    db_query_duration.labels(**labels).observe(duration)
    db_query_total.labels(**labels).inc()

    # Log slow queries
    if duration > 1.0:
        logger.warning(f"Slow query detected: {operation} on {table} took {duration:.2f}s")
        logger.debug(f"Slow query SQL: {statement[:200]}...")


def _parse_sql_statement(statement: str) -> tuple[str, str]:
    """Parse SQL statement to extract operation and table.

    Args:
        statement: SQL statement

    Returns:
        Tuple of (operation, table)
    """
    statement_upper = statement.upper().strip()

    # Determine operation
    if statement_upper.startswith("SELECT"):
        operation = "select"
    elif statement_upper.startswith("INSERT"):
        operation = "insert"
    elif statement_upper.startswith("UPDATE"):
        operation = "update"
    elif statement_upper.startswith("DELETE"):
        operation = "delete"
    elif statement_upper.startswith("CREATE"):
        operation = "create"
    elif statement_upper.startswith("DROP"):
        operation = "drop"
    elif statement_upper.startswith("ALTER"):
        operation = "alter"
    else:
        operation = "other"

    # Try to extract table name
    table = "unknown"

    try:
        # Simple regex patterns for common cases
        import re

        if operation == "select":
            match = re.search(r'FROM\s+(["\w]+\.)?(["\w]+)', statement_upper)
            if match:
                table = match.group(2).strip('"')
        elif operation == "insert":
            match = re.search(r'INTO\s+(["\w]+\.)?(["\w]+)', statement_upper)
            if match:
                table = match.group(2).strip('"')
        elif operation in ["update", "delete"]:
            match = re.search(r'(UPDATE|DELETE\s+FROM)\s+(["\w]+\.)?(["\w]+)', statement_upper)
            if match:
                table = match.group(3).strip('"')
                return operation, table.lower()
        else:
            match = re.search(r'TABLE\s+(["\w]+)', statement_upper)
            if match:
                table = match.group(1).strip('"')

    except Exception as e:
        logger.debug(f"Error parsing SQL statement: {str(e)}")

    return operation, table.lower()


def _on_connect(dbapi_conn: Any, connection_record: Any):
    """Handle new database connection.

    Args:
        dbapi_conn: DBAPI connection
        connection_record: Connection record
    """
    logger.debug("New database connection established")


def _on_checkout(dbapi_conn: Any, connection_record: Any, connection_proxy: Any):
    """Handle connection checkout from pool.

    Args:
        dbapi_conn: DBAPI connection
        connection_record: Connection record
        connection_proxy: Connection proxy
    """
    db_active_connections.inc()


def _on_checkin(dbapi_conn: Any, connection_record: Any):
    """Handle connection checkin to pool.

    Args:
        dbapi_conn: DBAPI connection
        connection_record: Connection record
    """
    db_active_connections.dec()


def _handle_db_error(exception_context: Any):
    """Handle database errors.

    Args:
        exception_context: Exception context
    """
    error_type = type(exception_context.original_exception).__name__

    errors_total.labels(component="database", error_type=error_type).inc()

    logger.error(f"Database error: {error_type} - {str(exception_context.original_exception)}")


def _update_pool_metrics(engine: Engine):
    """Update connection pool metrics.

    Args:
        engine: SQLAlchemy engine
    """
    try:
        pool = engine.pool

        # Update pool size metric
        if hasattr(pool, "size"):
            db_connection_pool_size.set(pool.size())
        elif hasattr(pool, "_pool"):
            db_connection_pool_size.set(len(pool._pool))

    except Exception as e:
        logger.error(f"Error updating pool metrics: {str(e)}")
