"""Compatibility module for ErrorHandledArticle."""

# Re-export from article.py for backward compatibility
from local_newsifier.crud.article import CRUDArticle, article

# Legacy class name for backward compatibility
ErrorHandledCRUDArticle = CRUDArticle

# Legacy instance for backward compatibility
error_handled_article = article