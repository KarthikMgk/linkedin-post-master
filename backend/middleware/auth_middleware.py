"""FastAPI auth and quota dependency injection."""
import logging
import os

import jwt as pyjwt
import redis as redis_lib
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from auth.allowlist import is_allowed
from auth.jwt_handler import verify_jwt
from services import quota_service

logger = logging.getLogger(__name__)

# tokenUrl is used only for OpenAPI docs — not the actual auth endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/google")


async def require_auth(token: str = Depends(oauth2_scheme)) -> str:
    """
    FastAPI dependency: validates JWT and checks allowlist.
    Returns the authenticated user's email.
    Raises 401 if token is invalid/expired.
    Raises 403 if email is not on allowlist.
    """
    try:
        payload = verify_jwt(token)
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")
    except pyjwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Authentication required.")

    email = payload.get("email", "")
    if not is_allowed(email):
        raise HTTPException(status_code=403, detail="Access denied. This app is invite-only.")

    return email


async def require_quota(email: str = Depends(require_auth)) -> str:
    """
    FastAPI dependency: checks daily quota before allowing generation.
    Chains on require_auth — auth must succeed first.
    Returns the authenticated user's email.
    Raises 429 if quota exhausted.
    Raises 503 if Redis is unreachable.
    """
    try:
        remaining = quota_service.get_remaining(email)
    except redis_lib.RedisError as e:
        logger.error("Redis unavailable in quota check: %s", str(e))
        raise HTTPException(
            status_code=503,
            detail="Quota service temporarily unavailable. Please try again.",
        )

    if remaining <= 0:
        limit = int(os.getenv("DAILY_QUOTA_LIMIT", "10"))
        raise HTTPException(
            status_code=429,
            detail=(
                f"Daily quota exceeded. You've used all {limit} generations "
                "for today. Try again tomorrow."
            ),
        )

    return email
