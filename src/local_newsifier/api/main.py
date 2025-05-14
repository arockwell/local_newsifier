"""Main FastAPI application for Local Newsifier."""

import logging
import os
import pathlib
from typing import Annotated, Dict
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi_injectable import register_app
from sqlmodel import Session

# Import models to ensure they're registered with SQLModel.metadata before creating tables
import local_newsifier.models
from local_newsifier.api.dependencies import get_templates
from local_newsifier.api.routers import auth, system, tasks
from local_newsifier.celery_app import app as celery_app
from local_newsifier.config.settings import get_settings, settings
from local_newsifier.database.engine import create_db_and_tables
from local_newsifier.fastapi_injectable_adapter import lifespan_with_injectable, migrate_container_services
from local_newsifier.di.providers import get_article_crud, get_session
from local_newsifier.crud.article import CRUDArticle

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
        
        # Migrate container services to fastapi-injectable
        logger.info("Migrating container services to fastapi-injectable")
        await migrate_container_services(app)
        
        logger.info("fastapi-injectable initialization completed")
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
    
    logger.info("Application startup complete")
    
    yield  # This is where FastAPI serves requests
    
    # Shutdown logic
    logger.info("Application shutdown initiated")
    logger.info("Application shutdown complete")


# Create app with our custom lifespan
app = FastAPI(
    title="Local Newsifier API",
    description="API for Local Newsifier",
    version="0.1.0",
    lifespan=lifespan,  # Set the lifespan context manager
)

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Include routers
app.include_router(auth.router)
app.include_router(system.router)
app.include_router(tasks.router)

@app.get("/", response_class=HTMLResponse)
async def root(
    request: Request,
    article_crud: Annotated[CRUDArticle, Depends(get_article_crud)],
    session: Annotated[Session, Depends(get_session)],
    templates: Jinja2Templates = Depends(get_templates)
):
    """Root endpoint serving home page with recent headlines."""
    # Get recent articles from the last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    recent_articles = []
    try:
        recent_articles = article_crud.get_by_date_range(
            session, 
            start_date=start_date, 
            end_date=end_date
        )
        
        # Order by published date (newest first) and limit to 20 articles
        recent_articles = sorted(
            recent_articles, 
            key=lambda x: x.published_at, 
            reverse=True
        )[:20]
    except Exception as e:
        logger.error(f"Error fetching recent articles: {str(e)}")
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Local Newsifier",
            "recent_articles": recent_articles
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
async def not_found_handler(
    request: Request, 
    exc: Exception
) -> JSONResponse:
    """Handle 404 errors."""
    templates = get_templates()
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=404,
            content={"detail": "Not found"},
        )
    return templates.TemplateResponse(
        "404.html", {"request": request, "title": "Not Found"}, status_code=404
    )
