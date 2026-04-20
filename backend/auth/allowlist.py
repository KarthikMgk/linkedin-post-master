"""Email allowlist enforcement."""
import os


def is_allowed(email: str) -> bool:
    """Check if email is in ALLOWED_EMAILS env var (case-insensitive, comma-separated)."""
    allowed_raw = os.getenv("ALLOWED_EMAILS", "")
    allowed = {e.strip().lower() for e in allowed_raw.split(",") if e.strip()}
    return email.lower() in allowed
