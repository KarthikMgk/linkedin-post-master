"""
Tests for Story 3.1: Enhanced Engagement Scoring

Covers:
  AC1 - Each variant in generate response has a fully-populated intelligence object
  AC2 - Refine response includes recalculated intelligence
  AC3 - Intelligence fields contain specific non-placeholder text (via mock)
  AC4 - Existing root fields (hook_strength string, suggestions) still present
  AC5 - char_count equals len(post) for each variant
"""
from unittest.mock import AsyncMock, patch

import pytest

from agents.content_agent import ContentGenerationAgent, DEFAULT_INTELLIGENCE


# ---------------------------------------------------------------------------
# AC1: generate response — intelligence object structure
# ---------------------------------------------------------------------------

def test_generate_variants_include_intelligence(client, mock_variants_result):
    """Each variant in the generate response must have an intelligence object."""
    with patch("main.content_agent.generate_variants", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_variants_result
        response = client.post("/api/generate", data={"text_input": "Test content"})

    assert response.status_code == 200
    variants = response.json()["variants"]
    for variant in variants:
        assert "intelligence" in variant, f"variant {variant['id']} missing intelligence"


def test_generate_intelligence_has_all_dimensions(client, mock_variants_result):
    """intelligence object must contain all four required dimensions."""
    with patch("main.content_agent.generate_variants", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_variants_result
        response = client.post("/api/generate", data={"text_input": "Test content"})

    variants = response.json()["variants"]
    for variant in variants:
        intel = variant["intelligence"]
        assert "hook_strength" in intel
        assert "cta_clarity" in intel
        assert "optimal_posting_time" in intel
        assert "length_assessment" in intel


def test_generate_intelligence_hook_strength_has_rating_and_reason(client, mock_variants_result):
    with patch("main.content_agent.generate_variants", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_variants_result
        response = client.post("/api/generate", data={"text_input": "Test"})

    intel = response.json()["variants"][0]["intelligence"]
    assert "rating" in intel["hook_strength"]
    assert "reason" in intel["hook_strength"]
    assert intel["hook_strength"]["rating"] in {"Weak", "Moderate", "Strong", "Exceptional"}


def test_generate_intelligence_cta_clarity_has_status_and_suggestion(client, mock_variants_result):
    with patch("main.content_agent.generate_variants", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_variants_result
        response = client.post("/api/generate", data={"text_input": "Test"})

    intel = response.json()["variants"][0]["intelligence"]
    assert "status" in intel["cta_clarity"]
    assert "suggestion" in intel["cta_clarity"]
    assert intel["cta_clarity"]["status"] in {"clear", "consider", "missing"}


def test_generate_intelligence_posting_time_has_time_and_reason(client, mock_variants_result):
    with patch("main.content_agent.generate_variants", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_variants_result
        response = client.post("/api/generate", data={"text_input": "Test"})

    intel = response.json()["variants"][0]["intelligence"]
    assert "time" in intel["optimal_posting_time"]
    assert "reason" in intel["optimal_posting_time"]


def test_generate_intelligence_length_assessment_has_status_and_char_count(client, mock_variants_result):
    with patch("main.content_agent.generate_variants", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_variants_result
        response = client.post("/api/generate", data={"text_input": "Test"})

    intel = response.json()["variants"][0]["intelligence"]
    assert "status" in intel["length_assessment"]
    assert "char_count" in intel["length_assessment"]
    assert intel["length_assessment"]["status"] in {"too_short", "optimal", "too_long"}


# ---------------------------------------------------------------------------
# AC4: backward compatibility — root fields unchanged
# ---------------------------------------------------------------------------

def test_generate_root_hook_strength_still_present(client, mock_variants_result):
    """Root hook_strength (plain string) must still exist alongside intelligence object."""
    with patch("main.content_agent.generate_variants", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_variants_result
        response = client.post("/api/generate", data={"text_input": "Test"})

    for variant in response.json()["variants"]:
        assert "hook_strength" in variant
        assert isinstance(variant["hook_strength"], str)


def test_generate_root_suggestions_still_present(client, mock_variants_result):
    with patch("main.content_agent.generate_variants", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_variants_result
        response = client.post("/api/generate", data={"text_input": "Test"})

    for variant in response.json()["variants"]:
        assert "suggestions" in variant
        assert isinstance(variant["suggestions"], list)


# ---------------------------------------------------------------------------
# AC2: refine response — intelligence present and recalculated
# ---------------------------------------------------------------------------

def test_refine_response_includes_intelligence(client, mock_refine_result):
    """Refine response must include an intelligence object."""
    with patch("main.content_agent.refine_post", new_callable=AsyncMock) as mock_ref:
        mock_ref.return_value = mock_refine_result
        response = client.post(
            "/api/refine",
            data={"post_text": "My post", "feedback": "make it punchier"},
        )

    assert response.status_code == 200
    assert "intelligence" in response.json()


def test_refine_intelligence_has_all_dimensions(client, mock_refine_result):
    with patch("main.content_agent.refine_post", new_callable=AsyncMock) as mock_ref:
        mock_ref.return_value = mock_refine_result
        response = client.post(
            "/api/refine",
            data={"post_text": "My post", "feedback": "punchy"},
        )

    intel = response.json()["intelligence"]
    assert "hook_strength" in intel
    assert "cta_clarity" in intel
    assert "optimal_posting_time" in intel
    assert "length_assessment" in intel


def test_refine_falls_back_to_default_intelligence_when_missing(client):
    """If refine result has no intelligence, response uses DEFAULT_INTELLIGENCE."""
    refine_without_intelligence = {
        "post_text": "My post",
        "hashtags": [],
        "engagement_score": 8.0,
        "hook_strength": "Strong",
        "suggestions": [],
        "cta": "Reply below",
        "changes": ["punchy"],
    }
    with patch("main.content_agent.refine_post", new_callable=AsyncMock) as mock_ref:
        mock_ref.return_value = refine_without_intelligence
        response = client.post(
            "/api/refine",
            data={"post_text": "My post", "feedback": "punchy"},
        )

    assert "intelligence" in response.json()
    assert response.json()["intelligence"]["hook_strength"]["rating"] == "Moderate"


# ---------------------------------------------------------------------------
# AC5: server-side char_count accuracy
# ---------------------------------------------------------------------------

def test_generate_char_count_is_present_in_response(client):
    """char_count from intelligence is passed through in the generate response."""
    post_text = "A" * 500
    variants_with_correct_char_count = [
        {
            "id": f"v-{i}",
            "personality": p,
            "label": f"{p.capitalize()} Approach",
            "post": post_text,
            "hashtags": [],
            "engagement_score": 8.0,
            "hook_strength": "Strong",
            "suggestions": [],
            "cta": "Test",
            "intelligence": {
                "hook_strength": {"rating": "Strong", "reason": "test"},
                "cta_clarity": {"status": "clear", "suggestion": "test"},
                "optimal_posting_time": {"time": "Tuesday 10am UTC", "reason": "test"},
                "length_assessment": {"status": "optimal", "char_count": 500},
            },
        }
        for i, p in enumerate(["bold", "structured", "provocative"])
    ]

    with patch("main.content_agent.generate_variants", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = variants_with_correct_char_count
        response = client.post("/api/generate", data={"text_input": "Test"})

    for variant in response.json()["variants"]:
        assert variant["intelligence"]["length_assessment"]["char_count"] == 500


# ---------------------------------------------------------------------------
# Unit tests: ContentGenerationAgent post-processing
# ---------------------------------------------------------------------------

def test_generate_variants_injects_default_intelligence_when_missing():
    """generate_variants() post-processing must add default intelligence if Claude omits it."""
    from unittest.mock import AsyncMock, MagicMock
    agent = ContentGenerationAgent(MagicMock())

    variant_without_intelligence = {
        "id": "v1",
        "personality": "bold",
        "label": "Bold Approach",
        "post": "Hello world",
        "hashtags": [],
        "engagement_score": 8.0,
        "hook_strength": "Strong",
        "suggestions": [],
        "cta": "Test",
    }

    import json
    raw_json = json.dumps({"variants": [
        variant_without_intelligence,
        {**variant_without_intelligence, "id": "v2", "personality": "structured", "label": "Structured Approach"},
        {**variant_without_intelligence, "id": "v3", "personality": "provocative", "label": "Provocative Approach"},
    ]})

    import asyncio
    agent.claude.generate_content = AsyncMock(return_value=raw_json)

    variants = asyncio.get_event_loop().run_until_complete(
        agent.generate_variants([{"type": "text", "content": "test", "priority": "primary"}])
    )

    for v in variants:
        assert "intelligence" in v
        assert "hook_strength" in v["intelligence"]


def test_generate_variants_overwrites_char_count_server_side():
    """generate_variants() must overwrite char_count with len(post) regardless of Claude's value."""
    from unittest.mock import AsyncMock, MagicMock
    agent = ContentGenerationAgent(MagicMock())

    post = "X" * 750
    variant = {
        "id": "v1", "personality": "bold", "label": "Bold Approach",
        "post": post, "hashtags": [], "engagement_score": 8.0,
        "hook_strength": "Strong", "suggestions": [], "cta": "Test",
        "intelligence": {
            "hook_strength": {"rating": "Strong", "reason": "test"},
            "cta_clarity": {"status": "clear", "suggestion": "test"},
            "optimal_posting_time": {"time": "Tuesday 10am UTC", "reason": "test"},
            "length_assessment": {"status": "optimal", "char_count": 1},  # wrong
        },
    }

    import json
    raw = json.dumps({"variants": [variant, {**variant, "id": "v2", "personality": "structured"}, {**variant, "id": "v3", "personality": "provocative"}]})
    agent.claude.generate_content = AsyncMock(return_value=raw)

    import asyncio
    variants = asyncio.get_event_loop().run_until_complete(
        agent.generate_variants([{"type": "text", "content": "test", "priority": "primary"}])
    )

    for v in variants:
        assert v["intelligence"]["length_assessment"]["char_count"] == 750
