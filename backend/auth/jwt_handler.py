"""JWT creation and validation."""
import os
from datetime import datetime, timedelta, timezone

import jwt


def create_jwt(email: str, name: str, picture: str) -> str:
    """Issue a signed JWT for an authenticated user."""
    secret = os.getenv("JWT_SECRET", "").strip()
    if not secret:
        raise RuntimeError("JWT_SECRET environment variable is not set.")

    expiry_hours = int(os.getenv("JWT_EXPIRY_HOURS", "24"))
    payload = {
        "email": email,
        "name": name,
        "picture": picture,
        "exp": datetime.now(timezone.utc) + timedelta(hours=expiry_hours),
    }
    # PyJWT v2.x encode() returns str — no .decode() needed
    return jwt.encode(payload, secret, algorithm="HS256")


def verify_jwt(token: str) -> dict:
    """
    Decode and verify a JWT.
    Raises jwt.PyJWTError on invalid or expired token.
    Returns the payload dict.
    """
    secret = os.getenv("JWT_SECRET", "").strip()
    # algorithms list is REQUIRED in PyJWT v2.x
    return jwt.decode(token, secret, algorithms=["HS256"])
