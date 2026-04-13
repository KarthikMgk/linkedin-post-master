"""
Input sanitization utilities.
Strips common injection vectors before content reaches the Claude API system prompt.
"""

import re

# Remove <script> ... </script> blocks — handles optional whitespace inside tag (P-20)
_SCRIPT_RE = re.compile(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", re.IGNORECASE | re.DOTALL)

# Remove all remaining HTML/XML tags
_HTML_TAG_RE = re.compile(r"<[^>]+>")

# Remove common SQL injection patterns
_SQL_RE = re.compile(
    r"(--|;|/\*|\*/|xp_|UNION\s+SELECT|DROP\s+TABLE|INSERT\s+INTO|DELETE\s+FROM)",
    re.IGNORECASE,
)


def sanitize_input(text: str) -> str:
    """
    Remove script tags, HTML markup, and SQL injection patterns from text.

    Args:
        text: Raw user-supplied string.

    Returns:
        Sanitized string safe to embed in Claude prompts.
    """
    text = _SCRIPT_RE.sub("", text)
    text = _HTML_TAG_RE.sub("", text)
    text = _SQL_RE.sub("", text)
    return text.strip()
