"""Main FastAPI application for Local Newsifier."""

import logging
import os
import pathlib
from typing import Dict
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from fastapi_injectable import register_app

# Import models to ensure they're registered with SQLModel.metadata before creating tables
import local_newsifier.models
from local_newsifier.api.dependencies import get_templates
from local_newsifier.api.routers import auth, system, tasks
from local_newsifier.celery_app import app as celery_app
from local_newsifier.config.settings import get_settings, settings
from local_newsifier.database.engine import create_db_and_tables
from local_newsifier.fastapi_injectable_adapter import lifespan_with_injectable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application.
    
    Handles startup and shutdown events.
    """
    # Startup logic
    logger.info("Application startup initiated")
    try:
        # Initialize database tables
        create_db_and_tables()
        logger.info("Database initialization completed")
        
        # Initialize fastapi-injectable
        logger.info("Initializing fastapi-injectable")
        await register_app(app)
        logger.info("fastapi-injectable initialization completed")
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
    
    logger.info("Application startup complete")
    
    yield  # This is where FastAPI serves requests
    
    # Shutdown logic
    logger.info("Application shutdown initiated")
    logger.info("Application shutdown complete")


app = FastAPI(
    title="Local Newsifier API",
    description="API for Local Newsifier",
    version="0.1.0",
    lifespan=lifespan,
)

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Include routers
app.include_router(auth.router)
app.include_router(system.router)
app.include_router(tasks.router)

# Include injectable test router
try:
    from local_newsifier.api.injectable_test import router as injectable_router
    app.include_router(injectable_router)
    logger.info("Injectable test router registered successfully")
except Exception as e:
    logger.error(f"Error registering injectable test router: {str(e)}")



@app.get("/", response_class=HTMLResponse)
async def root(request: Request, templates=Depends(get_templates)):
    """Root endpoint serving home page."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Local Newsifier",
        },
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "API is running"}


@app.get("/config")
async def get_config():
    """Get application configuration."""
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
    """Handle 404 errors."""
    templates = get_templates()  # Get the templates directly
    
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=404,
            content={"detail": "Not found"},
        )
    return templates.TemplateResponse(
        "404.html", {"request": request, "title": "Not Found"}, status_code=404
    )
