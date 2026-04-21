"""
Pytest configuration and shared fixtures for the LinkedIn Post Generator backend tests.

Sets up environment variables BEFORE importing the app to prevent
ClaudeService from failing due to missing ANTHROPIC_API_KEY.
"""







import os
import sys

# Set test environment variables BEFORE any app module imports
os.environ.setdefault("ANTHROPIC_API_KEY", "test-api-key-for-testing")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")
# Auth vars — dummy values so startup warnings are suppressed and jwt_handler doesn't crash
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
os.environ.setdefault("ALLOWED_EMAILS", "test@example.com")
os.environ.setdefault("JWT_SECRET", "test-secret-for-testing-only")

# Add backend root to sys.path so imports like `from main import app` work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import copy
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from main import app
from middleware.auth_middleware import require_auth, require_quota

# ---------------------------------------------------------------------------
# Shared mock payloads
# ---------------------------------------------------------------------------

MOCK_GENERATION_RESULT = {
    "post_text": (
        "AI agents in enterprise are transforming how we work.\n\n"
        "Here's what most people miss about the adoption challenge..."
    ),
    "hashtags": ["AIAgents", "EnterpriseTech", "FutureOfWork"],
    "engagement_score": 8.5,
    "hook_strength": "Strong",
    "suggestions": ["Add a specific data point", "End with a question"],
    "cta": "What's your experience with AI agents?",
}

_MOCK_INTELLIGENCE = {
    "hook_strength": {"rating": "Strong", "reason": "Opens with a challenge to conventional wisdom"},
    "cta_clarity": {"status": "clear", "suggestion": "Direct question invites comments effectively"},
    "optimal_posting_time": {"time": "Tuesday 10am UTC", "reason": "B2B tech content peaks mid-morning"},
    "length_assessment": {"status": "optimal", "char_count": 100},
}

# Mock result for generate_variants (list of 3 variant dicts)
MOCK_VARIANTS_RESULT = [
    {
        "id": "variant-001",
        "personality": "bold",
        "label": "Bold Approach",
        "post": (
            "AI agents in enterprise are transforming how we work.\n\n"
            "Here's what most people miss about the adoption challenge..."
        ),
        "hashtags": ["AIAgents", "EnterpriseTech", "FutureOfWork"],
        "engagement_score": 8.5,
        "hook_strength": "Strong",
        "suggestions": ["Add a specific data point", "End with a question"],
        "cta": "What's your experience with AI agents?",
        "intelligence": _MOCK_INTELLIGENCE,
    },
    {
        "id": "variant-002",
        "personality": "structured",
        "label": "Structured Approach",
        "post": (
            "AI agents are reshaping enterprise software.\n\n"
            "Key insight: adoption challenges differ from traditional tools..."
        ),
        "hashtags": ["AIAgents", "EnterpriseTech", "FutureOfWork"],
        "engagement_score": 8.2,
        "hook_strength": "Strong",
        "suggestions": ["Add data points"],
        "cta": "Share your thoughts below",
        "intelligence": _MOCK_INTELLIGENCE,
    },
    {
        "id": "variant-003",
        "personality": "provocative",
        "label": "Provocative Approach",
        "post": (
            "Everyone's talking about AI agents.\n\n"
            "Almost nobody is actually deploying them successfully..."
        ),
        "hashtags": ["AIAgents", "EnterpriseTech", "FutureOfWork"],
        "engagement_score": 8.8,
        "hook_strength": "Exceptional",
        "suggestions": ["Consider the timing"],
        "cta": "Drop your experiences below",
        "intelligence": _MOCK_INTELLIGENCE,
    },
]

MOCK_REFINE_RESULT = {
    "post_text": "AI agents aren't just tools. They're your new colleagues.\n\nHere's the truth nobody talks about.",
    "hashtags": ["AIAgents", "EnterpriseTech", "Innovation"],
    "engagement_score": 9.0,
    "hook_strength": "Exceptional",
    "suggestions": ["Near perfect!"],
    "cta": "Drop your thoughts below",
    "changes": ["make it punchier"],
    "intelligence": {
        "hook_strength": {"rating": "Exceptional", "reason": "Reframes AI as colleagues — deeply relatable"},
        "cta_clarity": {"status": "clear", "suggestion": "Invites sharing — strong community engagement signal"},
        "optimal_posting_time": {"time": "Tuesday 10am UTC", "reason": "B2B tech content peaks mid-morning"},
        "length_assessment": {"status": "optimal", "char_count": 87},
    },
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    """
    FastAPI TestClient with auth and quota dependencies overridden.
    Bypasses JWT validation and Redis quota checks so tests focus on business logic.
    """
    app.dependency_overrides[require_auth] = lambda: "test@example.com"
    app.dependency_overrides[require_quota] = lambda: "test@example.com"
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def mock_gen_result():
    # deepcopy so nested lists (hashtags, suggestions) are not shared between tests (P-15)
    return copy.deepcopy(MOCK_GENERATION_RESULT)


@pytest.fixture
def mock_variants_result():
    return copy.deepcopy(MOCK_VARIANTS_RESULT)


@pytest.fixture
def mock_refine_result():
    return copy.deepcopy(MOCK_REFINE_RESULT)
