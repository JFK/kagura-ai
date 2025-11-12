"""API Key usage statistics tracking with Redis.

Records and aggregates API key usage statistics over time for monitoring
and analytics purposes.
"""

from __future__ import annotations

import logging
import os
from datetime import date, datetime, timedelta
from typing import Any, Optional

import redis

logger = logging.getLogger(__name__)

# Redis key prefix for API key statistics
REDIS_PREFIX = "apikey:stats"

# Statistics retention period (days)
STATS_RETENTION_DAYS = 30


class APIKeyStatsTracker:
    """Tracks API key usage statistics using Redis.

    Records daily request counts with automatic TTL cleanup.
    """

    def __init__(self, redis_client: Optional[redis.Redis] = None) -> None:
        """Initialize stats tracker.

        Args:
            redis_client: Optional Redis client
                (default: connects to env-configured Redis)
        """
        if redis_client is None:
            # Use REDIS_URL (matches existing codebase pattern)
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.redis = redis.Redis.from_url(redis_url, decode_responses=True)
        else:
            self.redis = redis_client

    def _get_key(self, key_hash: str, day: date) -> str:
        """Generate Redis key for a specific day's stats.

        Args:
            key_hash: SHA256 hash of API key
            day: Date for the statistics

        Returns:
            Redis key string
        """
        date_str = day.isoformat()
        return f"{REDIS_PREFIX}:{key_hash}:{date_str}"

    def record_request(self, key_hash: str) -> None:
        """Record an API request for a key.

        Args:
            key_hash: SHA256 hash of API key
        """
        today = date.today()
        redis_key = self._get_key(key_hash, today)

        try:
            # Increment counter
            self.redis.incr(redis_key)

            # Set TTL to 30 days (in seconds)
            ttl_seconds = STATS_RETENTION_DAYS * 24 * 60 * 60
            self.redis.expire(redis_key, ttl_seconds)

        except Exception as e:
            # Don't fail requests if Redis is down
            logger.warning(f"Failed to record API key stats: {e}")

    def get_stats(
        self, key_hash: str, days: int = STATS_RETENTION_DAYS
    ) -> dict[str, Any]:
        """Get usage statistics for an API key.

        Args:
            key_hash: SHA256 hash of API key
            days: Number of days to retrieve (default: 30)

        Returns:
            Dictionary containing:
                - total_requests: Total request count
                - daily_stats: List of {date, count} for each day
                - period_start: Start date of statistics period
                - period_end: End date of statistics period
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        daily_stats = []
        total_requests = 0

        try:
            # Fetch stats for each day
            current_date = start_date
            while current_date <= end_date:
                redis_key = self._get_key(key_hash, current_date)
                count_str = self.redis.get(redis_key)
                count = int(count_str) if count_str else 0

                daily_stats.append(
                    {"date": current_date.isoformat(), "count": count}
                )
                total_requests += count

                current_date += timedelta(days=1)

        except Exception as e:
            logger.error(f"Failed to retrieve API key stats: {e}")
            # Return empty stats on error
            return {
                "total_requests": 0,
                "daily_stats": [],
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
            }

        return {
            "total_requests": total_requests,
            "daily_stats": daily_stats,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
        }

    def delete_stats(self, key_hash: str) -> int:
        """Delete all statistics for an API key.

        Args:
            key_hash: SHA256 hash of API key

        Returns:
            Number of keys deleted
        """
        try:
            # Find all keys for this API key
            pattern = f"{REDIS_PREFIX}:{key_hash}:*"
            keys = self.redis.keys(pattern)

            if not keys:
                return 0

            # Delete all matching keys
            return self.redis.delete(*keys)

        except Exception as e:
            logger.error(f"Failed to delete API key stats: {e}")
            return 0

    def health_check(self) -> bool:
        """Check if Redis connection is healthy.

        Returns:
            True if Redis is accessible, False otherwise
        """
        try:
            self.redis.ping()
            return True
        except Exception:
            return False


# Global stats tracker instance
_stats_tracker: Optional[APIKeyStatsTracker] = None


def get_stats_tracker() -> APIKeyStatsTracker:
    """Get or create global stats tracker instance.

    Returns:
        APIKeyStatsTracker instance
    """
    global _stats_tracker

    if _stats_tracker is None:
        _stats_tracker = APIKeyStatsTracker()

    return _stats_tracker
