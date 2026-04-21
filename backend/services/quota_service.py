"""
Redis-based per-user daily quota tracking.

Key pattern : quota:{email}:{YYYY-MM-DD}  (UTC date)
TTL         : seconds until midnight UTC  (auto-resets daily — no cron needed)
"""
import logging
import os
from datetime import datetime, timedelta, timezone

import redis as redis_lib

logger = logging.getLogger(__name__)

_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DAILY_LIMIT = int(os.getenv("DAILY_QUOTA_LIMIT", "10"))

# Module-level client — shared across requests (thread-safe)
try:
    _redis = redis_lib.from_url(_REDIS_URL, decode_responses=True)
    _redis.ping()
    logger.info("Redis connected: %s", _REDIS_URL)
except Exception as e:
    _redis = None
    logger.warning("Redis unavailable at startup: %s", str(e))


def _today_key(email: str) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"quota:{email}:{today}"


def _seconds_until_midnight() -> int:
    now = datetime.now(timezone.utc)
    midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return max(int((midnight - now).total_seconds()), 1)


def get_remaining(email: str) -> int:
    """
    Returns remaining quota for today without modifying any counter.
    Raises redis_lib.RedisError if Redis is unavailable.
    """
    if _redis is None:
        raise redis_lib.RedisError("Redis client not initialized")
    val = _redis.get(_today_key(email))
    used = int(val) if val else 0
    return max(DAILY_LIMIT - used, 0)


def check_and_increment(email: str) -> int:
    """
    Atomically increments the quota counter after a successful generation.
    Returns remaining count AFTER increment.
    Raises ValueError if quota was already exhausted (race condition guard).
    Raises redis_lib.RedisError if Redis is unavailable.
    """
    if _redis is None:
        raise redis_lib.RedisError("Redis client not initialized")

    key = _today_key(email)

    # Pipeline: GET current value, then INCR — executed together
    pipe = _redis.pipeline()
    pipe.get(key)
    pipe.incr(key)
    results = pipe.execute()

    current_before = int(results[0]) if results[0] else 0
    new_count = int(results[1])

    if current_before >= DAILY_LIMIT:
        # Race: two requests passed require_quota simultaneously — roll back
        _redis.decr(key)
        raise ValueError(f"Quota already exhausted for {email}")

    # First generation today — set TTL so key auto-deletes at midnight UTC
    if new_count == 1:
        _redis.expire(key, _seconds_until_midnight())

    remaining = max(DAILY_LIMIT - new_count, 0)
    logger.info("Quota: %s used=%d remaining=%d", email, new_count, remaining)
    return remaining
