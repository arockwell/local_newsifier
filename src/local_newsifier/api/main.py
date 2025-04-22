"""Main FastAPI application for Local Newsifier."""

import os
import logging
import traceback
from typing import Dict

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from local_newsifier.api.routers import system
from local_newsifier.config.settings import get_settings
from local_newsifier.database.engine import create_db_and_tables

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Local Newsifier API",
    description="API for Local Newsifier",
    version="0.1.0",
)

# Mount templates directory
import os
import pathlib

# Get the templates directory path - works both in development and production
if os.path.exists("src/local_newsifier/api/templates"):
    # Development environment
    templates_dir = "src/local_newsifier/api/templates"
else:
    # Production environment - use package-relative path
    templates_dir = str(pathlib.Path(__file__).parent / "templates")

templates = Jinja2Templates(directory=templates_dir)

# Include routers
app.include_router(system.router)


@app.on_event("startup")
async def startup():
    """Run startup tasks with detailed logging."""
    logger.info("Application startup initiated")
    try:
        # Create database tables
        logger.info("Initializing database tables...")
        create_db_and_tables()
        logger.info("Database initialization complete")
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        logger.error(f"Exception details: {traceback.format_exc()}")
        # Re-raise to prevent app from starting with broken DB
        raise


@app.on_event("shutdown")
async def shutdown():
    """Run shutdown tasks with detailed logging."""
    logger.info("Application shutdown initiated")
    try:
        # Add any cleanup code here
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint serving home page.

    Args:
        request: FastAPI request

    Returns:
        HTMLResponse: Home page
    """
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Local Newsifier",
        },
    )


@app.get("/health")
async def health_check():
    """Health check endpoint with logging.

    Returns:
        dict: Health status
    """
    logger.debug("Health check endpoint accessed")
    try:
        # Optional: Add more health checks here
        logger.info("Health check passed")
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}


@app.get("/config")
async def get_config():
    """Get application configuration.

    Returns:
        dict: Configuration
    """
    settings = get_settings()
    # Only return safe configuration values
    return {
        "database_host": settings.POSTGRES_HOST,
        "database_port": settings.POSTGRES_PORT,
        "database_name": settings.POSTGRES_DB,
        "log_level": settings.LOG_LEVEL,
        "environment": os.environ.get("ENVIRONMENT", "development"),
    }


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle 404 errors.

    Args:
        request: FastAPI request
        exc: Exception

    Returns:
        JSONResponse: Error response
    """
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=404,
            content={"detail": "Not found"},
        )
    return templates.TemplateResponse(
        "404.html", {"request": request, "title": "Not Found"}, status_code=404
    )
