"""Google OAuth2 token verification."""
import os

from google.auth.exceptions import GoogleAuthError, TransportError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token


def verify_google_token(token: str) -> dict:
    """
    Verify a Google id_token and return the payload.

    Raises ValueError with a descriptive message on any failure so the
    caller can always do a single `except ValueError` and return a clean
    error response to the client.
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    if not client_id:
        raise ValueError(
            "Server misconfiguration: GOOGLE_CLIENT_ID is not set. "
            "Contact the administrator."
        )

    try:
        request = google_requests.Request()
        payload = id_token.verify_oauth2_token(token, request, client_id)
        return payload
    except ValueError as exc:
        # Invalid token, expired, wrong audience, malformed JWT, etc.
        raise ValueError(f"Google token verification failed: {exc}") from exc
    except TransportError as exc:
        # Network error reaching Google's public-key endpoint
        raise ValueError(
            f"Could not reach Google authentication servers. "
            f"Check network connectivity. Detail: {exc}"
        ) from exc
    except GoogleAuthError as exc:
        raise ValueError(f"Google authentication error: {exc}") from exc
    except Exception as exc:
        # Catch-all: never let an unexpected exception become a silent 500
        raise ValueError(f"Unexpected error verifying Google token: {exc}") from exc
