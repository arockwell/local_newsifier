"""Database performance monitoring using SQLAlchemy events."""

import logging
import time

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import Pool

from .metrics import (db_connection_pool_size, db_query_counter, db_query_duration,
                      db_slow_query_counter)

logger = logging.getLogger(__name__)


def setup_database_monitoring(engine: Engine) -> None:
    """
    Set up database monitoring for the given engine.

    Args:
        engine: SQLAlchemy engine to monitor
    """

    # Monitor query execution
    @event.listens_for(Engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Track query start time."""
        conn.info.setdefault("query_start_time", []).append(time.time())

        # Extract operation and table from SQL statement
        operation = _extract_operation(statement)
        table = _extract_table(statement)

        conn.info.setdefault("query_operation", []).append(operation)
        conn.info.setdefault("query_table", []).append(table)

        # Increment query counter
        db_query_counter.labels(operation=operation, table=table).inc()

    @event.listens_for(Engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Track query completion and duration."""
        if "query_start_time" in conn.info and conn.info["query_start_time"]:
            start_time = conn.info["query_start_time"].pop(-1)
            duration = time.time() - start_time

            # Get operation and table
            operation = (
                conn.info["query_operation"].pop(-1)
                if "query_operation" in conn.info
                else "unknown"
            )
            table = conn.info["query_table"].pop(-1) if "query_table" in conn.info else "unknown"

            # Record duration
            db_query_duration.labels(operation=operation, table=table).observe(duration)

            # Track slow queries (>1s)
            if duration > 1.0:
                db_slow_query_counter.labels(operation=operation, table=table).inc()
                logger.warning(
                    f"Slow query detected: {operation} on {table} took {duration:.2f}s\n"
                    f"Statement: {statement[:200]}..."
                )

    # Monitor connection pool
    @event.listens_for(Pool, "connect")
    def on_connect(dbapi_conn, connection_record):
        """Track new database connections."""
        pool = connection_record.pool
        pool_name = pool.__class__.__name__
        db_connection_pool_size.labels(pool_name=pool_name).set(pool.size())

    @event.listens_for(Pool, "checkout")
    def on_checkout(dbapi_conn, connection_record, connection_proxy):
        """Track connection checkouts."""
        pool = connection_record.pool
        pool_name = pool.__class__.__name__
        db_connection_pool_size.labels(pool_name=pool_name).set(pool.size())

    @event.listens_for(Pool, "checkin")
    def on_checkin(dbapi_conn, connection_record):
        """Track connection checkins."""
        pool = connection_record.pool
        pool_name = pool.__class__.__name__
        db_connection_pool_size.labels(pool_name=pool_name).set(pool.size())

    logger.info("Database monitoring setup completed")


def _extract_operation(statement: str) -> str:
    """Extract operation type from SQL statement."""
    statement_upper = statement.strip().upper()

    if statement_upper.startswith("SELECT"):
        return "select"
    elif statement_upper.startswith("INSERT"):
        return "insert"
    elif statement_upper.startswith("UPDATE"):
        return "update"
    elif statement_upper.startswith("DELETE"):
        return "delete"
    elif statement_upper.startswith("CREATE"):
        return "create"
    elif statement_upper.startswith("DROP"):
        return "drop"
    elif statement_upper.startswith("ALTER"):
        return "alter"
    else:
        return "other"


def _extract_table(statement: str) -> str:
    """Extract table name from SQL statement."""
    import re

    statement_upper = statement.upper()

    # Patterns to extract table names
    patterns = [
        r"FROM\s+([^\s,]+)",  # SELECT ... FROM table
        r"INTO\s+([^\s(]+)",  # INSERT INTO table
        r"UPDATE\s+([^\s]+)",  # UPDATE table
        r"DELETE\s+FROM\s+([^\s]+)",  # DELETE FROM table
        r"CREATE\s+TABLE\s+([^\s(]+)",  # CREATE TABLE table
        r"DROP\s+TABLE\s+([^\s]+)",  # DROP TABLE table
        r"ALTER\s+TABLE\s+([^\s]+)",  # ALTER TABLE table
    ]

    for pattern in patterns:
        match = re.search(pattern, statement_upper)
        if match:
            table_name = match.group(1).lower()
            # Remove schema prefix if present
            if "." in table_name:
                table_name = table_name.split(".")[-1]
            # Remove quotes
            table_name = table_name.strip("\"'`")
            return table_name

    return "unknown"
