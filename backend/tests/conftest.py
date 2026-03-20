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

# Add backend root to sys.path so imports like `from main import app` work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from main import app


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

MOCK_REFINE_RESULT = {
    "post_text": "AI agents aren't just tools. They're your new colleagues.\n\nHere's the truth nobody talks about.",
    "hashtags": ["AIAgents", "EnterpriseTech", "Innovation"],
    "engagement_score": 9.0,
    "hook_strength": "Exceptional",
    "suggestions": ["Near perfect!"],
    "cta": "Drop your thoughts below",
    "changes": ["make it punchier"],
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """FastAPI TestClient — handles async endpoints synchronously."""
    return TestClient(app)


@pytest.fixture
def mock_gen_result():
    return MOCK_GENERATION_RESULT.copy()


@pytest.fixture
def mock_refine_result():
    return MOCK_REFINE_RESULT.copy()
