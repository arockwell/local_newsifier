"""Main FastAPI application for Local Newsifier."""

import logging
import os
from datetime import datetime, timedelta

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

# Import models to ensure they're registered with SQLModel.metadata before creating tables
import local_newsifier.models  # noqa: F401
from local_newsifier.api.dependencies import get_templates
from local_newsifier.api.routers import auth, system, tasks, webhooks
from local_newsifier.config.settings import get_settings, settings
from local_newsifier.database.engine import get_engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Create app without lifespan (sync-only)
app = FastAPI(
    title="Local Newsifier API",
    description="API for Local Newsifier",
    version="0.1.0",
)

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)


# Startup logging
@app.on_event("startup")
def startup_event():
    """Handle application startup."""
    logger.info("Application startup initiated")
    try:
        # Verify database connection
        engine = get_engine()
        if engine:
            logger.info("Database connection verified")
        else:
            logger.warning("Database connection could not be established")

        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")


@app.on_event("shutdown")
def shutdown_event():
    """Handle application shutdown."""
    logger.info("Application shutdown initiated")
    logger.info("Application shutdown complete")


# Include routers
app.include_router(auth.router)
app.include_router(system.router)
app.include_router(tasks.router)
app.include_router(webhooks.router)


@app.get("/", response_class=HTMLResponse)
def root(request: Request, templates: Jinja2Templates = Depends(get_templates)):
    """Root endpoint serving home page with recent headlines."""
    # Get recent articles from the last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    recent_articles_data = []
    try:
        # Use a synchronous session to avoid event loop issues
        from local_newsifier.crud.article import article as article_crud_instance
        from local_newsifier.database.engine import SessionManager

        with SessionManager() as session:
            articles = article_crud_instance.get_by_date_range(
                session, start_date=start_date, end_date=end_date
            )

            # Order by published date (newest first) and limit to 20 articles
            articles = sorted(articles, key=lambda x: x.published_at, reverse=True)[:20]

            # Convert SQLModel objects to dictionaries to avoid detached instance errors
            for article in articles:
                article_dict = {
                    "id": article.id,
                    "title": article.title,
                    "url": article.url,
                    "source": article.source,
                    "published_at": article.published_at,
                    "status": article.status,
                }
                recent_articles_data.append(article_dict)
    except Exception as e:
        logger.error(f"Error fetching recent articles: {str(e)}")

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Local Newsifier", "recent_articles": recent_articles_data},
    )


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "API is running"}


@app.get("/config")
def get_config():
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
def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
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
