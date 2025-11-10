"""Time formatting utilities for CLI output.

Provides human-readable time formatting functions for consistent
time display across Kagura CLI commands.
"""

from __future__ import annotations

from datetime import datetime, timezone


def format_relative_time(dt: datetime | str) -> str:
    """Format datetime as relative time (e.g., "2 hours ago").

    Args:
        dt: Datetime object or ISO format string

    Returns:
        Human-readable relative time string

    Example:
        >>> format_relative_time(datetime.now() - timedelta(hours=2))
        '2 hours ago'
    """
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))

    # Ensure timezone-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    delta = now - dt

    # Future times
    if delta.total_seconds() < 0:
        delta = -delta
        suffix = "from now"
    else:
        suffix = "ago"

    seconds = delta.total_seconds()

    if seconds < 60:
        return f"{int(seconds)} seconds {suffix}"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} {suffix}"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} {suffix}"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} {suffix}"
    elif seconds < 2592000:
        weeks = int(seconds / 604800)
        return f"{weeks} week{'s' if weeks != 1 else ''} {suffix}"
    else:
        months = int(seconds / 2592000)
        return f"{months} month{'s' if months != 1 else ''} {suffix}"


def format_duration(seconds: float | int) -> str:
    """Format duration in seconds as human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration (e.g., "3h 45m", "2m 30s")

    Example:
        >>> format_duration(13500)
        '3h 45m'
        >>> format_duration(90)
        '1m 30s'
    """
    if seconds < 60:
        return f"{int(seconds)}s"

    minutes = int(seconds / 60)
    remaining_seconds = int(seconds % 60)

    if minutes < 60:
        if remaining_seconds > 0:
            return f"{minutes}m {remaining_seconds}s"
        return f"{minutes}m"

    hours = int(minutes / 60)
    remaining_minutes = minutes % 60

    if remaining_minutes > 0:
        return f"{hours}h {remaining_minutes}m"
    return f"{hours}h"


def format_timestamp(
    dt: datetime | str,
    format: str = "%Y-%m-%d %H:%M:%S",
) -> str:
    """Format datetime as custom string.

    Args:
        dt: Datetime object or ISO format string
        format: strftime format string (default: YYYY-MM-DD HH:MM:SS)

    Returns:
        Formatted timestamp string

    Example:
        >>> format_timestamp(datetime.now(), "%Y-%m-%d")
        '2025-11-05'
    """
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))

    return dt.strftime(format)
