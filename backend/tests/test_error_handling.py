"""
Tests for Story 1.2: Structured Error Handling & Logging.

Covers:
  AC1 - Rate limit → HTTP 503 with retryAfter
  AC2 - Service unavailable → HTTP 503
  AC3 - Corrupt PDF → HTTP 400 with PDF-specific message
  AC4 - Structured log format (via logger.py)
  AC5 - Input sanitizer strips injection vectors
"""
import logging
import pytest
import anthropic
from unittest.mock import AsyncMock, MagicMock, patch

from utils.exceptions import InvalidFileError, RateLimitError, ServiceUnavailableError
from utils.sanitizer import sanitize_input
from utils.logger import get_logger, _LOG_FORMAT


# ---------------------------------------------------------------------------
# AC1 + AC2 — /api/generate rate-limit and service-unavailable handling
# ---------------------------------------------------------------------------

def test_generate_rate_limit_returns_503(client):
    """AC1: Claude rate limit → HTTP 503 with RATE_LIMIT_EXCEEDED code."""
    with patch("main.content_agent.generate_post", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = RateLimitError(retry_after=60)
        response = client.post("/api/generate", data={"text_input": "Some text"})

    assert response.status_code == 503
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    assert data["error"]["retryAfter"] == 60
    assert "60 seconds" in data["error"]["message"]


def test_generate_service_unavailable_returns_503(client):
    """AC2: Claude API unavailable → HTTP 503 with SERVICE_UNAVAILABLE code."""
    with patch("main.content_agent.generate_post", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = ServiceUnavailableError("Claude API unavailable: connection refused")
        response = client.post("/api/generate", data={"text_input": "Some text"})

    assert response.status_code == 503
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert len(data["error"]["message"]) > 0


def test_generate_service_unavailable_no_unhandled_exception(client):
    """AC2: No unhandled exception propagates — always returns structured response."""
    with patch("main.content_agent.generate_post", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = ServiceUnavailableError("timeout")
        response = client.post("/api/generate", data={"text_input": "Some text"})

    # Must be a parseable JSON response, not a raw 500 crash
    assert response.status_code in (503, 500)
    data = response.json()
    assert "error" in data or "detail" in data


def test_refine_rate_limit_returns_503(client):
    """AC1: Rate limit on /api/refine also returns 503."""
    with patch("main.content_agent.refine_post", new_callable=AsyncMock) as mock_ref:
        mock_ref.side_effect = RateLimitError(retry_after=60)
        response = client.post(
            "/api/refine",
            data={"post_text": "Post", "feedback": "punchy"}
        )

    assert response.status_code == 503
    data = response.json()
    assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    assert data["error"]["retryAfter"] == 60


def test_refine_service_unavailable_returns_503(client):
    """AC2: Service unavailable on /api/refine returns 503."""
    with patch("main.content_agent.refine_post", new_callable=AsyncMock) as mock_ref:
        mock_ref.side_effect = ServiceUnavailableError("timeout")
        response = client.post(
            "/api/refine",
            data={"post_text": "Post", "feedback": "punchy"}
        )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"


# ---------------------------------------------------------------------------
# AC1 — structured error format on 400
# ---------------------------------------------------------------------------

def test_generate_400_uses_structured_error_format(client):
    """400 (no inputs) response has success:false and error.code."""
    response = client.post("/api/generate", data={})
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "BAD_REQUEST"


# ---------------------------------------------------------------------------
# AC3 — corrupt PDF → HTTP 400
# ---------------------------------------------------------------------------

def test_corrupt_pdf_returns_400(client):
    """AC3: Corrupt PDF file → HTTP 400 with INVALID_FILE code."""
    with patch("services.input_processor.PyPDF2.PdfReader", side_effect=Exception("Invalid PDF")):
        response = client.post(
            "/api/generate",
            files={"pdf_file": ("test.pdf", b"not a real pdf", "application/pdf")},
        )

    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_FILE"


def test_corrupt_pdf_error_message_mentions_pdf(client):
    """AC3: 400 error message specifically identifies the PDF as the problem."""
    with patch("services.input_processor.PyPDF2.PdfReader", side_effect=Exception("bad file")):
        response = client.post(
            "/api/generate",
            files={"pdf_file": ("doc.pdf", b"corrupt", "application/pdf")},
        )

    msg = response.json()["error"]["message"].lower()
    assert "pdf" in msg


def test_corrupt_pdf_with_valid_text_returns_400_not_500(client):
    """AC3: Text + corrupt PDF → 400 (PDF-specific), not 500 server error."""
    with patch("services.input_processor.PyPDF2.PdfReader", side_effect=Exception("bad file")):
        response = client.post(
            "/api/generate",
            data={"text_input": "Valid text idea"},
            files={"pdf_file": ("doc.pdf", b"corrupt", "application/pdf")},
        )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_FILE"


# ---------------------------------------------------------------------------
# AC3 — ClaudeService raises correct exception types
# ---------------------------------------------------------------------------

async def test_generate_content_raises_rate_limit_error():
    """AC1: anthropic.RateLimitError from SDK → RateLimitError (generate_content)."""
    with patch("anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.messages.create.side_effect = anthropic.RateLimitError(
            message="rate limited", response=MagicMock(status_code=429), body={}
        )
        from services.claude_service import ClaudeService
        svc = ClaudeService(api_key="test-key")
        with pytest.raises(RateLimitError):
            await svc.generate_content("sys", "user")


async def test_generate_content_raises_service_unavailable_on_connection_error():
    """AC2: anthropic.APIConnectionError → ServiceUnavailableError (generate_content)."""
    with patch("anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.messages.create.side_effect = anthropic.APIConnectionError(
            request=MagicMock()
        )
        from services.claude_service import ClaudeService
        svc = ClaudeService(api_key="test-key")
        with pytest.raises(ServiceUnavailableError):
            await svc.generate_content("sys", "user")


async def test_generate_with_conversation_raises_rate_limit_error():
    """AC1: anthropic.RateLimitError → RateLimitError (generate_with_conversation)."""
    with patch("anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.messages.create.side_effect = anthropic.RateLimitError(
            message="rate limited", response=MagicMock(status_code=429), body={}
        )
        from services.claude_service import ClaudeService
        svc = ClaudeService(api_key="test-key")
        with pytest.raises(RateLimitError):
            await svc.generate_with_conversation("sys", [{"role": "user", "content": "hi"}])


async def test_generate_with_conversation_raises_service_unavailable():
    """AC2: anthropic.APIConnectionError → ServiceUnavailableError (generate_with_conversation)."""
    with patch("anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.messages.create.side_effect = anthropic.APIConnectionError(
            request=MagicMock()
        )
        from services.claude_service import ClaudeService
        svc = ClaudeService(api_key="test-key")
        with pytest.raises(ServiceUnavailableError):
            await svc.generate_with_conversation("sys", [{"role": "user", "content": "hi"}])


# ---------------------------------------------------------------------------
# AC4 — Logger format
# ---------------------------------------------------------------------------

def test_logger_format_contains_required_fields():
    """AC4: Logger format string contains asctime, levelname, name, message."""
    assert "%(asctime)s" in _LOG_FORMAT
    assert "%(levelname)s" in _LOG_FORMAT
    assert "%(name)s" in _LOG_FORMAT
    assert "%(message)s" in _LOG_FORMAT


def test_get_logger_returns_logger_with_handler():
    """AC4: get_logger returns a Logger with at least one StreamHandler."""
    logger = get_logger("test.story12")
    assert len(logger.handlers) > 0
    assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)


def test_get_logger_idempotent():
    """AC4: Calling get_logger twice with same name does not duplicate handlers."""
    name = "test.idempotent.story12"
    logger1 = get_logger(name)
    handler_count = len(logger1.handlers)
    logger2 = get_logger(name)
    assert len(logger2.handlers) == handler_count


# ---------------------------------------------------------------------------
# AC5 — Input sanitizer
# ---------------------------------------------------------------------------

def test_sanitizer_removes_script_tags():
    """AC5: <script> injection is stripped from input."""
    dirty = 'Hello <script>alert("xss")</script> World'
    clean = sanitize_input(dirty)
    assert "<script>" not in clean
    assert "alert" not in clean
    assert "Hello" in clean
    assert "World" in clean


def test_sanitizer_removes_html_tags():
    """AC5: Generic HTML tags are stripped."""
    dirty = "My <b>bold</b> idea about <em>AI</em>"
    clean = sanitize_input(dirty)
    assert "<b>" not in clean
    assert "<em>" not in clean
    assert "bold" in clean
    assert "AI" in clean


def test_sanitizer_removes_sql_union_select():
    """AC5: UNION SELECT SQL injection pattern is stripped."""
    dirty = "Topic idea UNION SELECT * FROM users"
    clean = sanitize_input(dirty)
    assert "UNION SELECT" not in clean.upper()


def test_sanitizer_removes_drop_table():
    """AC5: DROP TABLE SQL injection pattern is stripped."""
    dirty = "Idea about DROP TABLE users cascade"
    clean = sanitize_input(dirty)
    assert "DROP TABLE" not in clean.upper()


def test_sanitizer_removes_sql_comment():
    """AC5: SQL comment separator (--) is stripped."""
    dirty = "content -- injected comment"
    clean = sanitize_input(dirty)
    assert "--" not in clean


def test_sanitizer_preserves_normal_text():
    """AC5: Sanitizer does not corrupt legitimate content."""
    normal = "AI agents are transforming enterprise software in 2024."
    assert sanitize_input(normal) == normal


def test_sanitizer_strips_surrounding_whitespace():
    """sanitize_input strips leading/trailing whitespace."""
    assert sanitize_input("  hello  ") == "hello"


def test_sanitizer_applied_to_text_input(client, mock_gen_result):
    """AC5: Text with <script> tag does not propagate into generation call."""
    with patch("main.content_agent.generate_post", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_gen_result
        client.post(
            "/api/generate",
            data={"text_input": 'Good idea <script>alert(1)</script> more text'}
        )

    call_args = mock_gen.call_args[0][0]  # processed_inputs list
    text_item = next((i for i in call_args if i["type"] == "text"), None)
    assert text_item is not None
    assert "<script>" not in text_item["content"]
    assert "alert" not in text_item["content"]
