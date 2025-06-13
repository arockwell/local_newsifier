"""URL parsing utilities."""

from urllib.parse import urlparse


def extract_source_from_url(url: str) -> str:
    """Extract source domain from URL.

    Args:
        url: URL to parse

    Returns:
        Domain name or "Unknown Source" if parsing fails
    """
    if not url:
        return "Unknown Source"

    try:
        parsed = urlparse(url)
        return parsed.netloc or "Unknown Source"
    except Exception:
        return "Unknown Source"
