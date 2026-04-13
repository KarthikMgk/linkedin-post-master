"""
Custom exception classes for structured error handling.
"""

  

class RateLimitError(Exception):
    """Raised when the Claude API returns a 429 rate limit response."""

    def __init__(self, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after}s.")


class ServiceUnavailableError(Exception):
    """Raised when the Claude API is unreachable or times out."""


class InvalidFileError(Exception):
    """Raised when an uploaded file (PDF, image) cannot be processed."""
