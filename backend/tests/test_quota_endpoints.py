"""
Integration tests for quota behaviour in FastAPI endpoints — Story 5.3

Two fixtures:
  client          — overrides both require_auth AND require_quota (from conftest)
  client_quota    — overrides require_auth only, letting require_quota run for real

The second fixture is used to test 429 / 503 responses from the quota check itself.
"""
from unittest.mock import AsyncMock, patch

import pytest
import redis as redis_lib
from fastapi.testclient import TestClient

from main import app
from middleware.auth_middleware import require_auth, require_quota
from services import quota_service


# ---------------------------------------------------------------------------
# Extra fixture: auth bypassed but real require_quota runs
# ---------------------------------------------------------------------------

@pytest.fixture
def client_quota():
    """
    Bypasses JWT validation (require_auth override) but runs the real
    require_quota dependency so quota-blocking behaviour can be tested.
    """
    app.dependency_overrides[require_auth] = lambda: "test@example.com"
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# AC6: 429 when quota exhausted
# ---------------------------------------------------------------------------

def test_generate_returns_429_when_quota_exhausted(client_quota):
    """require_quota must block the request and return 429 before Claude is called."""
    with patch.object(quota_service, 'get_remaining', return_value=0):
        response = client_quota.post("/api/generate", data={"text_input": "anything"})
    assert response.status_code == 429


def test_generate_429_has_quota_exceeded_code(client_quota):
    with patch.object(quota_service, 'get_remaining', return_value=0):
        response = client_quota.post("/api/generate", data={"text_input": "anything"})
    assert response.json()["error"]["code"] == "QUOTA_EXCEEDED"


def test_generate_429_has_quota_headers(client_quota):
    """AC5 + AC6: 429 response must include X-Quota-Remaining: 0 and X-Quota-Limit."""
    with patch.object(quota_service, 'get_remaining', return_value=0):
        response = client_quota.post("/api/generate", data={"text_input": "anything"})
    assert response.headers.get("x-quota-remaining") == "0"
    assert response.headers.get("x-quota-limit") is not None


def test_refine_returns_429_when_quota_exhausted(client_quota):
    with patch.object(quota_service, 'get_remaining', return_value=0):
        response = client_quota.post(
            "/api/refine",
            data={"post_text": "My post", "feedback": "Make it punchier"},
        )
    assert response.status_code == 429


# ---------------------------------------------------------------------------
# AC10: 503 when Redis is unavailable
# ---------------------------------------------------------------------------

def test_generate_returns_503_when_redis_unavailable(client_quota):
    """Redis down → require_quota must return 503, not crash."""
    with patch.object(
        quota_service, 'get_remaining',
        side_effect=redis_lib.RedisError("connection refused")
    ):
        response = client_quota.post("/api/generate", data={"text_input": "anything"})
    assert response.status_code == 503


def test_generate_503_has_structured_error(client_quota):
    with patch.object(
        quota_service, 'get_remaining',
        side_effect=redis_lib.RedisError("timeout")
    ):
        response = client_quota.post("/api/generate", data={"text_input": "anything"})
    data = response.json()
    assert data["success"] is False
    assert "error" in data


# ---------------------------------------------------------------------------
# AC5: quota headers on successful generate / refine
# ---------------------------------------------------------------------------

def test_generate_success_includes_quota_remaining_header(client, mock_variants_result):
    """Successful generation response must carry X-Quota-Remaining header."""
    with patch("main.content_agent.generate_variants", new_callable=AsyncMock) as mock_gen, \
         patch.object(quota_service, 'check_and_increment', return_value=7):
        mock_gen.return_value = mock_variants_result
        response = client.post("/api/generate", data={"text_input": "Test"})

    assert response.status_code == 200
    assert response.headers.get("x-quota-remaining") == "7"


def test_generate_success_includes_quota_limit_header(client, mock_variants_result):
    with patch("main.content_agent.generate_variants", new_callable=AsyncMock) as mock_gen, \
         patch.object(quota_service, 'check_and_increment', return_value=7):
        mock_gen.return_value = mock_variants_result
        response = client.post("/api/generate", data={"text_input": "Test"})

    assert response.headers.get("x-quota-limit") is not None


def test_refine_success_includes_quota_headers(client, mock_refine_result):
    """Successful refinement response must carry quota headers."""
    with patch("main.content_agent.refine_post", new_callable=AsyncMock) as mock_ref, \
         patch.object(quota_service, 'check_and_increment', return_value=6):
        mock_ref.return_value = mock_refine_result
        response = client.post(
            "/api/refine",
            data={"post_text": "My post", "feedback": "punchier"},
        )

    assert response.status_code == 200
    assert response.headers.get("x-quota-remaining") == "6"


def test_generate_quota_not_counted_on_bad_request(client_quota):
    """AC3: quota increment must NOT run when request is rejected at validation."""
    with patch.object(quota_service, 'get_remaining', return_value=5), \
         patch.object(quota_service, 'check_and_increment') as mock_incr:
        # No inputs → 400
        client_quota.post("/api/generate", data={})
    mock_incr.assert_not_called()
