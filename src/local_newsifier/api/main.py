"""Main FastAPI application for Local Newsifier."""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi_injectable import register_app

# Import models to ensure they're registered with SQLModel.metadata before creating tables
import local_newsifier.models
from local_newsifier.api.dependencies import get_templates
from local_newsifier.api.routers import auth, system, tasks
from local_newsifier.config.settings import get_settings, settings
from local_newsifier.database.engine import create_db_and_tables
from local_newsifier.di.providers import get_background_task_manager

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
    manager = get_background_task_manager()
    try:
        # Initialize database tables
        create_db_and_tables()
        logger.info("Database initialization completed")
        
        # Initialize fastapi-injectable
        logger.info("Initializing fastapi-injectable")
        await register_app(app)

        logger.info("fastapi-injectable initialization completed")

        if hasattr(manager, "restore_tasks"):
            await manager.restore_tasks()
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
    
    logger.info("Application startup complete")
    
    yield  # This is where FastAPI serves requests
    
    # Shutdown logic
    logger.info("Application shutdown initiated")
    if hasattr(manager, "save_tasks"):
        await manager.save_tasks()
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
    templates: Jinja2Templates = Depends(get_templates)
):
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
