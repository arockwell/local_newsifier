"""Date parsing utilities."""

from datetime import datetime, timezone
from typing import Optional

from dateutil.parser import parse as dateutil_parse


def parse_date_safe(date_str: str) -> Optional[datetime]:
    """Safely parse various date formats.

    Args:
        date_str: Date string to parse

    Returns:
        Parsed datetime or None if parsing fails
    """
    if not date_str:
        return None

    try:
        return dateutil_parse(date_str)
    except (ValueError, TypeError):
        return None


def get_utc_now() -> datetime:
    """Get current UTC timestamp.

    Returns:
        Current datetime in UTC
    """
    return datetime.now(timezone.utc)


def to_iso_string(dt: Optional[datetime]) -> Optional[str]:
    """Convert datetime to ISO format string.

    Args:
        dt: Datetime to convert

    Returns:
        ISO formatted string or None if dt is None
    """
    return dt.isoformat() if dt else None


def from_iso_string(date_str: str) -> Optional[datetime]:
    """Parse ISO format datetime string.

    Args:
        date_str: ISO format string

    Returns:
        Parsed datetime or None if parsing fails
    """
    if not date_str:
        return None

    try:
        return datetime.fromisoformat(date_str)
    except (ValueError, TypeError):
        return None


def format_datetime(dt: Optional[datetime], format_type: str = "short") -> Optional[str]:
    """Format datetime with predefined formats.

    Args:
        dt: Datetime to format
        format_type: One of "short", "long", or a custom strftime format

    Returns:
        Formatted string or None if dt is None
    """
    if not dt:
        return None

    formats = {
        "short": "%Y-%m-%d %H:%M",
        "long": "%Y-%m-%d %H:%M:%S",
    }

    format_str = formats.get(format_type, format_type)

    try:
        return dt.strftime(format_str)
    except (ValueError, TypeError):
        return None
