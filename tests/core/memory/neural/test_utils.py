"""Tests for neural memory utility functions."""

from datetime import datetime, timezone

from kagura.core.memory.neural.utils import (
    IMPORTANCE_FREQUENCY_WEIGHT,
    IMPORTANCE_STORED_WEIGHT,
    LOG_FREQUENCY_REFERENCE_COUNT,
    SECONDS_PER_DAY,
    get_current_utc_time,
)


class TestGetCurrentUtcTime:
    """Test suite for get_current_utc_time()."""

    def test_returns_datetime(self):
        """Test returns datetime object."""
        result = get_current_utc_time()
        assert isinstance(result, datetime)

    def test_returns_utc_timezone(self):
        """Test returned datetime is UTC aware."""
        result = get_current_utc_time()
        assert result.tzinfo == timezone.utc

    def test_returns_current_time(self):
        """Test returns approximately current time."""
        before = datetime.now(timezone.utc)
        result = get_current_utc_time()
        after = datetime.now(timezone.utc)

        assert before <= result <= after


class TestConstants:
    """Test suite for module constants."""

    def test_log_frequency_reference_count(self):
        """Test LOG_FREQUENCY_REFERENCE_COUNT is correct."""
        assert LOG_FREQUENCY_REFERENCE_COUNT == 100
        assert isinstance(LOG_FREQUENCY_REFERENCE_COUNT, int)

    def test_importance_weights(self):
        """Test importance weight constants."""
        assert IMPORTANCE_STORED_WEIGHT == 0.7
        assert IMPORTANCE_FREQUENCY_WEIGHT == 0.3
        assert IMPORTANCE_STORED_WEIGHT + IMPORTANCE_FREQUENCY_WEIGHT == 1.0

    def test_seconds_per_day(self):
        """Test SECONDS_PER_DAY constant."""
        assert SECONDS_PER_DAY == 86400
        assert SECONDS_PER_DAY == 24 * 60 * 60
