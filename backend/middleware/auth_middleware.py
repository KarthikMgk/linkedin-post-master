"""FastAPI auth dependency injection."""
import jwt as pyjwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from auth.allowlist import is_allowed
from auth.jwt_handler import verify_jwt

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
    except pyjwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Authentication required.")

    email = payload.get("email", "")
    if not is_allowed(email):
        raise HTTPException(status_code=403, detail="Access denied. This app is invite-only.")

    return email
