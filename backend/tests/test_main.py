"""
Integration tests for FastAPI endpoints.

Uses TestClient (sync) which handles async endpoint execution internally.
Patches content_agent and claude_service methods to avoid real API calls.
"""

from unittest.mock import AsyncMock, patch

import pytest

# ---------------------------------------------------------------------------
# POST /api/generate
# ---------------------------------------------------------------------------


def test_generate_success_with_text_input(client, mock_variants_result):
    """AC2: Valid text input returns 200 with all required fields."""
    with patch("main.content_agent.generate_variants", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_variants_result

        response = client.post(
            "/api/generate",
            data={"text_input": "AI agents in enterprise software are changing everything"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "post" in data
    assert "hashtags" in data
    assert "engagement_score" in data
    assert "hook_strength" in data
    assert "suggestions" in data
    # P-18: verify exactly 3 variants returned (Story 2.1 AC1)
    assert "variants" in data
    assert len(data["variants"]) == 3


def test_generate_response_maps_fields_correctly(client, mock_variants_result):
    """AC2: Response fields map correctly from content_agent result."""
    with patch("main.content_agent.generate_variants", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_variants_result

        response = client.post("/api/generate", data={"text_input": "Test content"})

    data = response.json()
    assert data["post"] == mock_variants_result[0]["post"]
    assert data["hashtags"] == mock_variants_result[0]["hashtags"]
    assert data["engagement_score"] == mock_variants_result[0]["engagement_score"]
    assert data["hook_strength"] == mock_variants_result[0]["hook_strength"]
    assert data["suggestions"] == mock_variants_result[0]["suggestions"]


def test_generate_empty_body_returns_400(client):
    """AC3: No inputs provided → HTTP 400."""
    response = client.post("/api/generate", data={})
    assert response.status_code == 400


def test_generate_whitespace_only_text_returns_400(client):
    """AC3: Whitespace-only text is treated as no input → HTTP 400."""
    response = client.post("/api/generate", data={"text_input": "   "})
    assert response.status_code == 400


def test_generate_400_includes_error_message(client):
    """AC3: 400 response uses structured error format with message field."""
    response = client.post("/api/generate", data={})
    data = response.json()
    assert "error" in data
    assert "message" in data["error"]
    assert len(data["error"]["message"]) > 0


def test_generate_with_url_input_succeeds(client, mock_variants_result):
    """URL-only input is accepted (FR4)."""
    with patch("main.content_agent.generate_variants", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_variants_result

        response = client.post("/api/generate", data={"url_input": "https://example.com/article"})

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_generate_includes_metadata(client, mock_variants_result):
    """Response includes metadata with inputs_processed count."""
    with patch("main.content_agent.generate_variants", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_variants_result

        response = client.post("/api/generate", data={"text_input": "Test input"})

    data = response.json()
    assert "metadata" in data
    assert "inputs_processed" in data["metadata"]


def test_generate_agent_exception_returns_500(client):
    """Unhandled exception from content_agent → HTTP 500."""
    with patch("main.content_agent.generate_variants", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = Exception("Claude API unexpectedly unavailable")

        response = client.post("/api/generate", data={"text_input": "Test input"})

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# POST /api/refine
# ---------------------------------------------------------------------------


def test_refine_success(client, mock_refine_result):
    """AC6: Valid refine request returns 200 with refined_post."""
    with patch("main.content_agent.refine_post", new_callable=AsyncMock) as mock_refine:
        mock_refine.return_value = mock_refine_result

        response = client.post(
            "/api/refine",
            data={
                "post_text": "Original post content about AI agents",
                "feedback": "make it punchier",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "refined_post" in data
    assert data["refined_post"] == mock_refine_result["post_text"]


def test_refine_returns_engagement_score(client, mock_refine_result):
    """AC6: Refine response includes updated engagement_score."""
    with patch("main.content_agent.refine_post", new_callable=AsyncMock) as mock_refine:
        mock_refine.return_value = mock_refine_result

        response = client.post(
            "/api/refine", data={"post_text": "Post text", "feedback": "add more energy"}
        )

    assert "engagement_score" in response.json()


def test_refine_missing_post_text_returns_422(client):
    """Missing required post_text → HTTP 422 (FastAPI validation)."""
    response = client.post("/api/refine", data={"feedback": "make it better"})
    assert response.status_code == 422


def test_refine_missing_feedback_returns_422(client):
    """Missing required feedback → HTTP 422 (FastAPI validation)."""
    response = client.post("/api/refine", data={"post_text": "Some post content"})
    assert response.status_code == 422


def test_refine_calls_agent_with_correct_args(client, mock_refine_result):
    """Refine endpoint passes post_text and feedback to content_agent."""
    with patch("main.content_agent.refine_post", new_callable=AsyncMock) as mock_refine:
        mock_refine.return_value = mock_refine_result

        client.post(
            "/api/refine", data={"post_text": "Original post", "feedback": "make it punchier"}
        )

    mock_refine.assert_called_once_with("Original post", "make it punchier")


# ---------------------------------------------------------------------------
# GET /api/health
# ---------------------------------------------------------------------------


def test_health_returns_200(client):
    """Health endpoint returns HTTP 200."""
    with patch("main.claude_service.test_connection", new_callable=AsyncMock) as mock_health:
        mock_health.return_value = True
        response = client.get("/api/health")

    assert response.status_code == 200


def test_health_shows_claude_connected(client):
    """Health endpoint shows claude_api: connected when connection succeeds."""
    with patch("main.claude_service.test_connection", new_callable=AsyncMock) as mock_health:
        mock_health.return_value = True
        response = client.get("/api/health")

    data = response.json()
    assert data["claude_api"] == "connected"


def test_health_shows_error_when_connection_fails(client):
    """Health endpoint shows claude_api: error when connection fails."""
    with patch("main.claude_service.test_connection", new_callable=AsyncMock) as mock_health:
        mock_health.return_value = False
        response = client.get("/api/health")

    data = response.json()
    assert data["claude_api"] == "error"


def test_root_returns_running_status(client):
    """Root endpoint returns status: running."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"


# ---------------------------------------------------------------------------
# Image generation integration — Story 4.1
# ---------------------------------------------------------------------------

_MOCK_IMAGE = {
    "url": "https://fal.media/files/generated.jpg",
    "alt_text": "Developer at terminal.",
    "prompt_used": "High-contrast professional photo of a developer.",
}


def test_generate_includes_image_in_each_variant(client, mock_variants_result):
    """AC1: Each variant in /api/generate response contains an image object."""
    with (
        patch("main.content_agent.generate_variants", new_callable=AsyncMock) as mock_gen,
        patch("main.image_service.generate", new_callable=AsyncMock) as mock_img,
    ):
        mock_gen.return_value = mock_variants_result
        mock_img.return_value = _MOCK_IMAGE

        response = client.post("/api/generate", data={"text_input": "Test content"})

    assert response.status_code == 200
    data = response.json()
    for variant in data["variants"]:
        assert "image" in variant
        assert variant["image"]["url"] == _MOCK_IMAGE["url"]
        assert variant["image"]["alt_text"] == _MOCK_IMAGE["alt_text"]
        assert variant["image"]["prompt_used"] == _MOCK_IMAGE["prompt_used"]


def test_generate_image_called_for_all_three_variants(client, mock_variants_result):
    """AC1: image_service.generate() is called once per variant (3 total)."""
    with (
        patch("main.content_agent.generate_variants", new_callable=AsyncMock) as mock_gen,
        patch("main.image_service.generate", new_callable=AsyncMock) as mock_img,
    ):
        mock_gen.return_value = mock_variants_result
        mock_img.return_value = _MOCK_IMAGE

        client.post("/api/generate", data={"text_input": "Test content"})

    assert mock_img.call_count == 3


def test_generate_graceful_image_failure_returns_200(client, mock_variants_result):
    """AC3: If image generation fails for all variants, response is still HTTP 200."""
    with (
        patch("main.content_agent.generate_variants", new_callable=AsyncMock) as mock_gen,
        patch("main.image_service.generate", new_callable=AsyncMock) as mock_img,
    ):
        mock_gen.return_value = mock_variants_result
        mock_img.return_value = None  # graceful failure

        response = client.post("/api/generate", data={"text_input": "Test content"})

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_generate_graceful_failure_sets_image_null(client, mock_variants_result):
    """AC3: When image=None, each variant has image: null in response."""
    with (
        patch("main.content_agent.generate_variants", new_callable=AsyncMock) as mock_gen,
        patch("main.image_service.generate", new_callable=AsyncMock) as mock_img,
    ):
        mock_gen.return_value = mock_variants_result
        mock_img.return_value = None

        response = client.post("/api/generate", data={"text_input": "Test content"})

    data = response.json()
    for variant in data["variants"]:
        assert variant["image"] is None


def test_generate_graceful_failure_adds_image_suggestion(client, mock_variants_result):
    """AC3: When image=None, each variant's intelligence gains image_suggestion."""
    with (
        patch("main.content_agent.generate_variants", new_callable=AsyncMock) as mock_gen,
        patch("main.image_service.generate", new_callable=AsyncMock) as mock_img,
    ):
        mock_gen.return_value = mock_variants_result
        mock_img.return_value = None

        response = client.post("/api/generate", data={"text_input": "Test content"})

    data = response.json()
    for variant in data["variants"]:
        assert "image_suggestion" in variant["intelligence"]
        assert len(variant["intelligence"]["image_suggestion"]) > 0


def test_refine_includes_image_in_response(client, mock_refine_result):
    """AC4: /api/refine response includes an image key."""
    with (
        patch("main.content_agent.refine_post", new_callable=AsyncMock) as mock_refine,
        patch("main.image_service.generate", new_callable=AsyncMock) as mock_img,
    ):
        mock_refine.return_value = mock_refine_result
        mock_img.return_value = _MOCK_IMAGE

        response = client.post(
            "/api/refine",
            data={"post_text": "Original post", "feedback": "make it punchier"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "image" in data
    assert data["image"]["url"] == _MOCK_IMAGE["url"]


def test_refine_graceful_image_failure_still_returns_200(client, mock_refine_result):
    """AC4 + AC3: /api/refine still returns 200 even when image generation fails."""
    with (
        patch("main.content_agent.refine_post", new_callable=AsyncMock) as mock_refine,
        patch("main.image_service.generate", new_callable=AsyncMock) as mock_img,
    ):
        mock_refine.return_value = mock_refine_result
        mock_img.return_value = None

        response = client.post(
            "/api/refine",
            data={"post_text": "Original post", "feedback": "make it punchier"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["image"] is None
    # AC3: intelligence.image_suggestion must be a non-empty string when image is null
    assert "image_suggestion" in data["intelligence"]
    assert len(data["intelligence"]["image_suggestion"]) > 0


# ---------------------------------------------------------------------------
# image_visual_rationale — Story 4.2
# ---------------------------------------------------------------------------


def test_generate_variants_include_image_visual_rationale(client, mock_variants_result):
    """AC1/AC2: Each variant's intelligence includes image_visual_rationale."""
    with (
        patch("main.content_agent.generate_variants", new_callable=AsyncMock) as mock_gen,
        patch("main.image_service.generate", new_callable=AsyncMock) as mock_img,
    ):
        mock_gen.return_value = mock_variants_result
        mock_img.return_value = None

        response = client.post("/api/generate", data={"text_input": "Test content"})

    assert response.status_code == 200
    data = response.json()
    for variant in data["variants"]:
        assert "image_visual_rationale" in variant["intelligence"]


def test_refine_response_includes_image_visual_rationale(client, mock_refine_result):
    """AC3: Refine response intelligence includes image_visual_rationale."""
    with (
        patch("main.content_agent.refine_post", new_callable=AsyncMock) as mock_refine,
        patch("main.image_service.generate", new_callable=AsyncMock) as mock_img,
    ):
        mock_refine.return_value = mock_refine_result
        mock_img.return_value = None

        response = client.post(
            "/api/refine",
            data={"post_text": "Original post", "feedback": "make it punchier"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "image_visual_rationale" in data["intelligence"]


# ---------------------------------------------------------------------------
# /api/regenerate-image — Story 4.2 (AC4)
# ---------------------------------------------------------------------------


def test_regenerate_image_returns_image_on_success(client):
    """AC4: /api/regenerate-image returns image dict on successful generation."""
    with patch("main.image_service.generate", new_callable=AsyncMock) as mock_img:
        mock_img.return_value = _MOCK_IMAGE

        response = client.post(
            "/api/regenerate-image",
            json={"image_description": "High-contrast developer photo.", "alt_text": "Developer."},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["image"]["url"] == _MOCK_IMAGE["url"]


def test_regenerate_image_with_custom_direction_prepends_it(client):
    """AC4: custom_direction is prepended to image_description before generation."""
    with patch("main.image_service.generate", new_callable=AsyncMock) as mock_img:
        mock_img.return_value = _MOCK_IMAGE

        client.post(
            "/api/regenerate-image",
            json={
                "image_description": "High-contrast developer photo.",
                "custom_direction": "Make it darker and more dramatic",
            },
        )

    called_prompt = mock_img.call_args[0][0]
    assert called_prompt.startswith("Make it darker and more dramatic")
    assert "High-contrast developer photo." in called_prompt


def test_regenerate_image_returns_null_on_failure(client):
    """AC4: When image generation fails, response is still 200 with image=null and image_suggestion set."""
    with patch("main.image_service.generate", new_callable=AsyncMock) as mock_img:
        mock_img.return_value = None

        response = client.post(
            "/api/regenerate-image",
            json={"image_description": "A vivid professional photo.", "alt_text": "Photo."},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["image"] is None
    assert "image_suggestion" in data
    assert len(data["image_suggestion"]) > 0


def test_regenerate_image_requires_auth():
    """AC4: /api/regenerate-image returns 401 when no auth token provided."""
    from fastapi.testclient import TestClient
    from main import app as _app

    # Use a fresh client without auth override
    with TestClient(_app) as unauthed_client:
        response = unauthed_client.post(
            "/api/regenerate-image",
            json={"image_description": "Test."},
        )
    assert response.status_code == 401
