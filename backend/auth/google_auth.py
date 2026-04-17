"""Google OAuth2 token verification."""
import os

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token


def verify_google_token(token: str) -> dict:
    """
    Verify a Google id_token and return the payload.
    Raises ValueError on invalid or expired token.
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    request = google_requests.Request()
    # verify_oauth2_token checks signature, expiry, AND audience (client_id)
    payload = id_token.verify_oauth2_token(token, request, client_id)
    return payload
