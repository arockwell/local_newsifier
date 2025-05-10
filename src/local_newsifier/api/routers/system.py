"""System information router for database tables."""

import logging
import os
from typing import Annotated, Dict, List

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, text

from local_newsifier.api.dependencies import get_session, require_admin, get_templates

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/system",
    tags=["system"],
    responses={404: {"description": "Not found"}},
)

# Flag to indicate if we're in minimal mode (no database)
MINIMAL_MODE = False  # Permanently disabled


@router.get("/tables", response_class=HTMLResponse)
async def get_tables(
    request: Request,
    _: bool = Depends(require_admin),
    session: Session = Depends(get_session),
    templates: Jinja2Templates = Depends(get_templates),
):
    """Get information about all tables in the database.

    Args:
        request: FastAPI request
        session: Database session
        templates: Jinja2 templates

    Returns:
        HTML response with table information
    """
    if MINIMAL_MODE:
        # Return a template with a message that we're in minimal mode
        return templates.TemplateResponse(
            "tables.html",
            {
                "request": request,
                "tables_info": [],
                "title": "Database Tables - Minimal Mode",
                "minimal_mode": True,
                "message": (
                    "Running in minimal mode - database features are disabled."
                ),
            },
        )

    try:
        tables_info = get_tables_info(session)
        return templates.TemplateResponse(
            "tables.html",
            {
                "request": request,
                "tables_info": tables_info,
                "title": "Database Tables",
                "minimal_mode": False,
            },
        )
    except Exception as e:
        logger.error(f"Error fetching tables: {str(e)}")
        return templates.TemplateResponse(
            "tables.html",
            {
                "request": request,
                "tables_info": [],
                "title": "Database Tables - Error",
                "minimal_mode": True,
                "message": f"Error connecting to database: {str(e)}",
            },
        )


@router.get("/tables/api", response_model=List[Dict])
async def get_tables_api(
    _: bool = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """Get information about all tables in the database (API version).

    Args:
        session: Database session

    Returns:
        JSON with table information
    """
    if MINIMAL_MODE or session is None:
        return JSONResponse(
            content=[
                {
                    "name": "minimal_mode",
                    "message": (
                        "Running in minimal mode - database features are disabled"
                    ),
                }
            ]
        )

    try:
        return JSONResponse(content=get_tables_info(session))
    except Exception as e:
        logger.error(f"Error in tables API: {str(e)}")
        return JSONResponse(content=[{"name": "error", "error": str(e)}])


@router.get("/tables/{table_name}", response_class=HTMLResponse)
async def get_table_details(
    request: Request,
    table_name: str,
    _: bool = Depends(require_admin),
    session: Session = Depends(get_session),
    templates: Jinja2Templates = Depends(get_templates),
):
    """Get detailed information about a specific table.

    Args:
        request: FastAPI request
        table_name: Table name
        session: Database session
        templates: Jinja2 templates

    Returns:
        HTML response with table details
    """
    if MINIMAL_MODE or session is None:
        # Return a template with a message that we're in minimal mode
        return templates.TemplateResponse(
            "table_details.html",
            {
                "request": request,
                "table_name": table_name,
                "columns": [],
                "row_count": 0,
                "sample_data": [],
                "title": f"Table: {table_name} - Minimal Mode",
                "minimal_mode": True,
                "message": "Running in minimal mode - database features are disabled.",
            },
        )

    try:
        # Get table columns
        column_query = text(
            """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM
                information_schema.columns
            WHERE
                table_name = :table_name
            ORDER BY
                ordinal_position
            """
        )
        # SQLModel exec() only takes one parameter (the query) with values bound to the query
        column_query = column_query.bindparams(table_name=table_name)
        columns = session.exec(column_query).all()

        # Get row count
        count_query = text(f"SELECT COUNT(*) FROM {table_name}")
        row_count = session.exec(count_query).one()

        # Try to get sample data (first 5 rows)
        try:
            sample_query = text(f"SELECT * FROM {table_name} LIMIT 5")
            sample_data = session.exec(sample_query).all()
        except Exception:
            sample_data = []

        return templates.TemplateResponse(
            "table_details.html",
            {
                "request": request,
                "table_name": table_name,
                "columns": columns,
                "row_count": row_count,
                "sample_data": sample_data,
                "title": f"Table: {table_name}",
                "minimal_mode": False,
            },
        )
    except Exception as e:
        logger.error(f"Error fetching table details: {str(e)}")
        return templates.TemplateResponse(
            "table_details.html",
            {
                "request": request,
                "table_name": table_name,
                "columns": [],
                "row_count": 0,
                "sample_data": [],
                "title": f"Table: {table_name} - Error",
                "minimal_mode": True,
                "message": f"Error accessing table: {str(e)}",
            },
        )


@router.get("/tables/{table_name}/api")
async def get_table_details_api(
    table_name: str,
    _: bool = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """Get detailed information about a specific table (API version).

    Args:
        table_name: Table name
        session: Database session

    Returns:
        JSON with table details
    """
    if MINIMAL_MODE or session is None:
        return JSONResponse(
            content={
                "table_name": table_name,
                "error": "Running in minimal mode - database features are disabled",
            }
        )

    try:
        # Get table columns
        column_query = text(
            """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM
                information_schema.columns
            WHERE
                table_name = :table_name
            ORDER BY
                ordinal_position
            """
        )
        # SQLModel exec() only takes one parameter (the query) with values bound to the query
        column_query = column_query.bindparams(table_name=table_name)
        columns = session.exec(column_query).all()

        # Get row count
        count_query = text(f"SELECT COUNT(*) FROM {table_name}")
        row_count = session.exec(count_query).one()

        return JSONResponse(
            content={
                "table_name": table_name,
                "columns": [list(col) for col in columns],
                "row_count": row_count,
            }
        )
    except Exception as e:
        logger.error(f"Error in table details API: {str(e)}")
        # Include row_count and other expected fields in error response
        return JSONResponse(
            content={
                "table_name": table_name,
                "error": str(e),
                "row_count": 0,
                "columns": []
            }
        )


def get_tables_info(session: Session) -> List[Dict]:
    """Get information about all tables in the database.

    Args:
        session: Database session

    Returns:
        List of table information dictionaries
    """
    query = text(
        """
        SELECT
            t.table_name,
            (SELECT COUNT(*) FROM information_schema.columns
             WHERE table_name=t.table_name) as column_count,
            (SELECT pg_total_relation_size(quote_ident(t.table_name))
             ) as table_size
        FROM
            information_schema.tables t
        WHERE
            table_schema = 'public'
            AND table_type = 'BASE TABLE'
        ORDER BY
            table_name
        """
    )
    tables = session.exec(query).all()

    # For each table, get the row count
    tables_info = []
    for table in tables:
        table_name = table[0]
        column_count = table[1]
        table_size = table[2]

        # Get row count
        count_query = text(f"SELECT COUNT(*) FROM {table_name}")
        row_count = session.exec(count_query).one()
        
        # Convert row_count to int if it's a SQLAlchemy Row object
        if hasattr(row_count, "__iter__"):
            row_count = row_count[0]
        elif not isinstance(row_count, (int, float)):
            row_count = int(row_count)

        tables_info.append(
            {
                "name": table_name,
                "column_count": column_count,
                "row_count": row_count,
                "size_bytes": table_size,
                "size_readable": format_size(table_size),
            }
        )

    return tables_info


def format_size(size_bytes: int) -> str:
    """Format size in bytes to human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Human-readable size string
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024 or unit == "TB":
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
