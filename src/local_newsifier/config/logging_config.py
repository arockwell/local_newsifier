"""Logging configuration for Local Newsifier."""

import logging
import logging.config
import os
import sys
from typing import Dict, Any

# Import settings to access log level configuration
from local_newsifier.config.settings import settings

def configure_logging() -> None:
    """Configure logging for the application.
    
    Sets up logging with appropriate handlers and formatters.
    """
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Determine log level from settings
    log_level = settings.LOG_LEVEL.upper()
    
    # Basic configuration for the root logger
    logging.basicConfig(
        level=log_level,
        format=settings.LOG_FORMAT,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Set specific loggers to DEBUG level for detailed diagnostics
    logging.getLogger("local_newsifier.tools.rss_parser").setLevel(logging.DEBUG)
    logging.getLogger("local_newsifier.tasks").setLevel(logging.DEBUG)
    logging.getLogger("local_newsifier.services.article_service").setLevel(logging.DEBUG)
    logging.getLogger("local_newsifier.database.engine").setLevel(logging.DEBUG)
    
    # Create a file handler for debug logs
    file_handler = logging.FileHandler("logs/debug.log")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    
    # Add the file handler to the root logger
    logging.getLogger().addHandler(file_handler)
    
    # Configure Celery and other third-party loggers
    logging.getLogger("celery").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

def get_detailed_logging_config() -> Dict[str, Any]:
    """Get a dictionary-based logging configuration.
    
    This can be used with logging.config.dictConfig() for more complex setups.
    
    Returns:
        Dict containing logging configuration
    """
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": settings.LOG_FORMAT,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - [%(pathname)s:%(lineno)d] - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "standard",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.FileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": "logs/debug.log",
                "mode": "a",
            },
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console", "file"],
                "level": settings.LOG_LEVEL,
                "propagate": True,
            },
            "local_newsifier": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "local_newsifier.tools.rss_parser": {
                "level": "DEBUG",
                "propagate": True,
            },
            "local_newsifier.tasks": {
                "level": "DEBUG",
                "propagate": True,
            },
            "celery": {
                "level": "INFO",
                "propagate": True,
            },
            "sqlalchemy.engine": {
                "level": "WARNING",
                "propagate": True,
            },
        },
    }
