"""
Unit tests for services/quota_service.py — Story 5.3

Uses patch.object to replace the module-level _redis client so tests
run without a real Redis instance.
"""
from unittest.mock import MagicMock, patch

import pytest
import redis as redis_lib

from services import quota_service


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_redis(get_val=None):
    """Return a MagicMock that looks like a Redis client."""
    m = MagicMock()
    m.get.return_value = get_val
    return m


def _mock_pipeline(get_val, incr_val):
    """Return a MagicMock pipeline whose execute() returns [get_val, incr_val]."""
    pipe = MagicMock()
    pipe.execute.return_value = [get_val, incr_val]
    return pipe


# ---------------------------------------------------------------------------
# get_remaining
# ---------------------------------------------------------------------------

class TestGetRemaining:
    def test_returns_full_limit_when_no_key(self):
        """No Redis key → user hasn't generated today → full quota available."""
        m = _mock_redis(get_val=None)
        with patch.object(quota_service, '_redis', m), \
             patch.object(quota_service, 'DAILY_LIMIT', 10):
            assert quota_service.get_remaining("a@b.com") == 10

    def test_subtracts_used_count(self):
        m = _mock_redis(get_val="3")
        with patch.object(quota_service, '_redis', m), \
             patch.object(quota_service, 'DAILY_LIMIT', 10):
            assert quota_service.get_remaining("a@b.com") == 7

    def test_returns_zero_at_limit(self):
        m = _mock_redis(get_val="10")
        with patch.object(quota_service, '_redis', m), \
             patch.object(quota_service, 'DAILY_LIMIT', 10):
            assert quota_service.get_remaining("a@b.com") == 0

    def test_never_returns_negative(self):
        """Guard against Redis containing a value above the limit."""
        m = _mock_redis(get_val="15")
        with patch.object(quota_service, '_redis', m), \
             patch.object(quota_service, 'DAILY_LIMIT', 10):
            assert quota_service.get_remaining("a@b.com") == 0

    def test_raises_redis_error_when_client_is_none(self):
        with patch.object(quota_service, '_redis', None):
            with pytest.raises(redis_lib.RedisError):
                quota_service.get_remaining("a@b.com")


# ---------------------------------------------------------------------------
# check_and_increment
# ---------------------------------------------------------------------------

class TestCheckAndIncrement:
    def test_returns_remaining_after_increment(self):
        m = _mock_redis()
        m.pipeline.return_value = _mock_pipeline("4", 5)
        with patch.object(quota_service, '_redis', m), \
             patch.object(quota_service, 'DAILY_LIMIT', 10):
            remaining = quota_service.check_and_increment("a@b.com")
        assert remaining == 5  # 10 - 5

    def test_sets_ttl_on_first_generation(self):
        """First use today (new_count == 1) must set a TTL for midnight reset."""
        m = _mock_redis()
        m.pipeline.return_value = _mock_pipeline(None, 1)
        with patch.object(quota_service, '_redis', m), \
             patch.object(quota_service, 'DAILY_LIMIT', 10):
            quota_service.check_and_increment("a@b.com")
        assert m.expire.called

    def test_no_ttl_on_subsequent_generations(self):
        """TTL is only set on the first generation of the day, not on every call."""
        m = _mock_redis()
        m.pipeline.return_value = _mock_pipeline("4", 5)
        with patch.object(quota_service, '_redis', m), \
             patch.object(quota_service, 'DAILY_LIMIT', 10):
            quota_service.check_and_increment("a@b.com")
        assert not m.expire.called

    def test_returns_zero_at_last_allowed_generation(self):
        """Using the last quota slot returns 0 remaining."""
        m = _mock_redis()
        m.pipeline.return_value = _mock_pipeline("9", 10)
        with patch.object(quota_service, '_redis', m), \
             patch.object(quota_service, 'DAILY_LIMIT', 10):
            assert quota_service.check_and_increment("a@b.com") == 0

    def test_raises_value_error_when_quota_already_exhausted(self):
        """Race guard: if count was already at limit, ValueError is raised."""
        m = _mock_redis()
        m.pipeline.return_value = _mock_pipeline("10", 11)
        with patch.object(quota_service, '_redis', m), \
             patch.object(quota_service, 'DAILY_LIMIT', 10):
            with pytest.raises(ValueError, match="Quota already exhausted"):
                quota_service.check_and_increment("a@b.com")

    def test_decrements_back_on_quota_exhausted(self):
        """When quota is exhausted, the INCR must be rolled back with DECR."""
        m = _mock_redis()
        m.pipeline.return_value = _mock_pipeline("10", 11)
        with patch.object(quota_service, '_redis', m), \
             patch.object(quota_service, 'DAILY_LIMIT', 10):
            with pytest.raises(ValueError):
                quota_service.check_and_increment("a@b.com")
        m.decr.assert_called_once()

    def test_raises_redis_error_when_client_is_none(self):
        with patch.object(quota_service, '_redis', None):
            with pytest.raises(redis_lib.RedisError):
                quota_service.check_and_increment("a@b.com")
