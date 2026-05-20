"""
Redis-backed JWT token blacklist for logout.

When a user logs out, their JWT is added to this blacklist with a TTL
equal to the remaining token lifetime. require_auth checks this blacklist
before allowing access.
"""
import logging
import os
from datetime import datetime, timezone

import jwt as pyjwt
import redis as redis_lib

logger = logging.getLogger(__name__)

_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

try:
    _redis = redis_lib.from_url(_REDIS_URL, decode_responses=True)
    _redis.ping()
    logger.info("Blacklist Redis connected: %s", _REDIS_URL)
except Exception as e:
    _redis = None
    logger.warning("Redis unavailable at blacklist startup: %s", str(e))


def _key_for(token_jti: str) -> str:
    return f"blacklist:{token_jti}"


def blacklist_token(token: str) -> bool:
    """
    Add a token to the blacklist. Returns True if added, False if skipped
    (e.g. Redis unavailable).
    """
    if _redis is None:
        logger.warning("Redis unavailable — blacklist skipped for token")
        return False

    try:
        payload = pyjwt.decode(token, options={"verify_signature": False})
    except Exception:
        return False

    jti = payload.get("jti") or payload.get("sub") or payload.get("email", "")
    exp = payload.get("exp")
    if not exp:
        return False

    now = datetime.now(timezone.utc).timestamp()
    ttl = max(int(exp - now), 1)

    key = _key_for(jti)
    _redis.setex(key, ttl, "1")
    logger.info("Token blacklisted: jti=%s ttl=%ds", jti, ttl)
    return True


def is_blacklisted(token: str) -> bool:
    """Return True if the token is in the blacklist."""
    if _redis is None:
        return False

    try:
        payload = pyjwt.decode(token, options={"verify_signature": False})
    except Exception:
        return False

    jti = payload.get("jti") or payload.get("sub") or payload.get("email", "")
    key = _key_for(jti)
    return _redis.exists(key) > 0
