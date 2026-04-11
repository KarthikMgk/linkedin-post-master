"""
Unit tests for ContentGenerationAgent.

All MiniMax API calls are mocked via AsyncMock on a mock MiniMaxService instance.
Tests validate JSON parsing, fallback behavior, and method delegation.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from agents.content_agent import ContentGenerationAgent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_claude_service():
    """Mock ClaudeService with async stubs."""
    service = MagicMock()
    service.generate_content = AsyncMock()
    service.generate_with_conversation = AsyncMock()
    return service


@pytest.fixture
def agent(mock_claude_service):
    return ContentGenerationAgent(mock_claude_service)


# Sample valid Claude API JSON response
VALID_RESPONSE_PAYLOAD = {
    "post_text": "AI agents in enterprise are transforming how we work.",
    "hashtags": ["AIAgents", "EnterpriseTech", "FutureOfWork"],
    "engagement_score": 8.5,
    "hook_strength": "Strong",
    "suggestions": ["Add a specific data point", "End with a question"],
    "cta": "What's your experience with AI agents?",
}

SAMPLE_PROCESSED_INPUTS = [
    {
        "type": "text",
        "content": "AI agents in enterprise software",
        "priority": "primary",
    }
]


# ---------------------------------------------------------------------------
# generate_post() tests  (AC4)
# ---------------------------------------------------------------------------

async def test_generate_post_returns_dict(agent, mock_claude_service):
    """generate_post returns a dict on valid JSON response."""
    mock_claude_service.generate_content.return_value = json.dumps(VALID_RESPONSE_PAYLOAD)
    result = await agent.generate_post(SAMPLE_PROCESSED_INPUTS)
    assert isinstance(result, dict)


async def test_generate_post_calls_minimax_generate_content(agent, mock_claude_service):
    """generate_post delegates to minimax_service.generate_content exactly once."""
    mock_claude_service.generate_content.return_value = json.dumps(VALID_RESPONSE_PAYLOAD)
    await agent.generate_post(SAMPLE_PROCESSED_INPUTS)
    mock_claude_service.generate_content.assert_called_once()


async def test_generate_post_parses_all_fields(agent, mock_claude_service):
    """AC4: All JSON fields are correctly parsed from Claude response."""
    mock_claude_service.generate_content.return_value = json.dumps(VALID_RESPONSE_PAYLOAD)
    result = await agent.generate_post(SAMPLE_PROCESSED_INPUTS)

    assert result["post_text"] == VALID_RESPONSE_PAYLOAD["post_text"]
    assert result["hashtags"] == VALID_RESPONSE_PAYLOAD["hashtags"]
    assert result["engagement_score"] == VALID_RESPONSE_PAYLOAD["engagement_score"]
    assert result["hook_strength"] == VALID_RESPONSE_PAYLOAD["hook_strength"]
    assert result["suggestions"] == VALID_RESPONSE_PAYLOAD["suggestions"]
    assert result["cta"] == VALID_RESPONSE_PAYLOAD["cta"]


async def test_generate_post_handles_markdown_wrapped_json(agent, mock_claude_service):
    """AC4: Handles ```json ... ``` wrapping that Claude sometimes returns."""
    wrapped = f"```json\n{json.dumps(VALID_RESPONSE_PAYLOAD)}\n```"
    mock_claude_service.generate_content.return_value = wrapped
    result = await agent.generate_post(SAMPLE_PROCESSED_INPUTS)
    assert result["post_text"] == VALID_RESPONSE_PAYLOAD["post_text"]


async def test_generate_post_handles_plain_backtick_wrapping(agent, mock_claude_service):
    """Handles ``` ... ``` wrapping (no json tag)."""
    wrapped = f"```\n{json.dumps(VALID_RESPONSE_PAYLOAD)}\n```"
    mock_claude_service.generate_content.return_value = wrapped
    result = await agent.generate_post(SAMPLE_PROCESSED_INPUTS)
    assert result["engagement_score"] == VALID_RESPONSE_PAYLOAD["engagement_score"]


async def test_generate_post_cleans_escaped_newlines(agent, mock_claude_service):
    """Post text with escaped \\n sequences is cleaned to real newlines."""
    payload = VALID_RESPONSE_PAYLOAD.copy()
    payload["post_text"] = "Line 1\\nLine 2\\nLine 3"
    mock_claude_service.generate_content.return_value = json.dumps(payload)
    result = await agent.generate_post(SAMPLE_PROCESSED_INPUTS)
    assert "\n" in result["post_text"]
    assert "\\n" not in result["post_text"]


async def test_generate_post_fallback_on_invalid_json(agent, mock_claude_service):
    """AC4: Falls back gracefully when JSON parsing fails — no exception raised."""
    mock_claude_service.generate_content.return_value = "This is not JSON at all"
    result = await agent.generate_post(SAMPLE_PROCESSED_INPUTS)
    assert isinstance(result, dict)
    assert "post_text" in result
    assert "engagement_score" in result
    assert "hook_strength" in result


async def test_generate_post_passes_system_prompt_to_claude(agent, mock_claude_service):
    """generate_post passes the system_prompt to claude_service."""
    mock_claude_service.generate_content.return_value = json.dumps(VALID_RESPONSE_PAYLOAD)
    await agent.generate_post(SAMPLE_PROCESSED_INPUTS)
    call_kwargs = mock_claude_service.generate_content.call_args
    assert call_kwargs is not None
    # system_prompt should be passed as first positional or keyword arg
    args, kwargs = call_kwargs
    system_prompt_passed = args[0] if args else kwargs.get("system_prompt", "")
    assert "LinkedIn" in system_prompt_passed


async def test_generate_post_formats_primary_content_in_message(agent, mock_claude_service):
    """generate_post includes PRIMARY CONTENT label in user message."""
    mock_claude_service.generate_content.return_value = json.dumps(VALID_RESPONSE_PAYLOAD)
    await agent.generate_post(SAMPLE_PROCESSED_INPUTS)
    _, kwargs = mock_claude_service.generate_content.call_args if mock_claude_service.generate_content.call_args[1] else (mock_claude_service.generate_content.call_args[0], {})
    call_args = mock_claude_service.generate_content.call_args
    user_message = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("user_message", "")
    assert "PRIMARY CONTENT" in user_message


# ---------------------------------------------------------------------------
# refine_post() tests  (AC4)
# ---------------------------------------------------------------------------

VALID_REFINE_PAYLOAD = {
    "post_text": "Punchier: AI agents aren't just tools. They're your new colleagues.",
    "hashtags": ["AIAgents", "Innovation"],
    "engagement_score": 9.0,
    "hook_strength": "Exceptional",
    "suggestions": ["Near perfect!"],
}


async def test_refine_post_returns_dict_with_changes(agent, mock_claude_service):
    """refine_post returns dict that always includes 'changes' key."""
    mock_claude_service.generate_with_conversation.return_value = json.dumps(VALID_REFINE_PAYLOAD)
    result = await agent.refine_post("Original post", "make it punchier")
    assert isinstance(result, dict)
    assert "changes" in result
    assert result["changes"] == ["make it punchier"]


async def test_refine_post_calls_generate_with_conversation(agent, mock_claude_service):
    """refine_post delegates to claude_service.generate_with_conversation."""
    mock_claude_service.generate_with_conversation.return_value = json.dumps(VALID_REFINE_PAYLOAD)
    await agent.refine_post("Post text", "feedback here")
    mock_claude_service.generate_with_conversation.assert_called_once()


async def test_refine_post_parses_post_text(agent, mock_claude_service):
    """refine_post correctly parses refined post_text from response."""
    mock_claude_service.generate_with_conversation.return_value = json.dumps(VALID_REFINE_PAYLOAD)
    result = await agent.refine_post("Original", "punchy")
    assert result["post_text"] == VALID_REFINE_PAYLOAD["post_text"]


async def test_refine_post_fallback_on_invalid_json(agent, mock_claude_service):
    """refine_post falls back gracefully when JSON parsing fails."""
    mock_claude_service.generate_with_conversation.return_value = "Not valid JSON"
    result = await agent.refine_post("Post", "feedback")
    assert isinstance(result, dict)
    assert "changes" in result


async def test_refine_post_handles_markdown_wrapped_json(agent, mock_claude_service):
    """refine_post handles ```json ... ``` wrapping."""
    wrapped = f"```json\n{json.dumps(VALID_REFINE_PAYLOAD)}\n```"
    mock_claude_service.generate_with_conversation.return_value = wrapped
    result = await agent.refine_post("Post", "feedback")
    assert result["post_text"] == VALID_REFINE_PAYLOAD["post_text"]


async def test_refine_post_tracks_requested_feedback_in_changes(agent, mock_claude_service):
    """changes field captures the exact feedback string that was requested."""
    mock_claude_service.generate_with_conversation.return_value = json.dumps(VALID_REFINE_PAYLOAD)
    feedback = "add a provocative opening question"
    result = await agent.refine_post("Post", feedback)
    assert feedback in result["changes"]


# ---------------------------------------------------------------------------
# generate_variants() tests  (Story 2.1 AC1, AC2)
# ---------------------------------------------------------------------------

VALID_VARIANTS_RESPONSE = {
    "variants": [
        {
            "id": "var-001",
            "personality": "bold",
            "label": "Bold Approach",
            "post": "Everyone is wrong about AI in the workplace. Here's why.",
            "hashtags": ["AIAgents", "FutureOfWork"],
            "engagement_score": 8.5,
            "hook_strength": "Strong",
            "suggestions": ["Add data"],
            "cta": "What's your take?"
        },
        {
            "id": "var-002",
            "personality": "structured",
            "label": "Structured Approach",
            "post": "3 lessons about AI in enterprise software:\n\n1. It's about productivity\n2. It's about collaboration\n3. It's about the future",
            "hashtags": ["AIAgents", "EnterpriseTech"],
            "engagement_score": 8.2,
            "hook_strength": "Strong",
            "suggestions": ["Great structure"],
            "cta": "Share your lessons"
        },
        {
            "id": "var-003",
            "personality": "provocative",
            "label": "Provocative Approach",
            "post": "What if AI actually makes us MORE human at work?",
            "hashtags": ["AIAgents", "Innovation"],
            "engagement_score": 8.8,
            "hook_strength": "Exceptional",
            "suggestions": ["Powerful hook"],
            "cta": "Tell me I'm wrong"
        }
    ]
}


async def test_generate_variants_returns_list(agent, mock_claude_service):
    """generate_variants returns a list of variant dicts."""
    mock_claude_service.generate_content.return_value = json.dumps(VALID_VARIANTS_RESPONSE)
    result = await agent.generate_variants(SAMPLE_PROCESSED_INPUTS)
    assert isinstance(result, list)


async def test_generate_variants_returns_exactly_3(agent, mock_claude_service):
    """AC1: generate_variants returns exactly 3 variants."""
    mock_claude_service.generate_content.return_value = json.dumps(VALID_VARIANTS_RESPONSE)
    result = await agent.generate_variants(SAMPLE_PROCESSED_INPUTS)
    assert len(result) == 3


async def test_generate_variants_has_required_fields(agent, mock_claude_service):
    """AC1: Each variant has id, personality, label, post, hashtags, engagement_score, hook_strength, suggestions."""
    mock_claude_service.generate_content.return_value = json.dumps(VALID_VARIANTS_RESPONSE)
    result = await agent.generate_variants(SAMPLE_PROCESSED_INPUTS)

    for variant in result:
        assert "id" in variant
        assert "personality" in variant
        assert "label" in variant
        assert "post" in variant
        assert "hashtags" in variant
        assert "engagement_score" in variant
        assert "hook_strength" in variant
        assert "suggestions" in variant


async def test_generate_variants_has_correct_personalities(agent, mock_claude_service):
    """AC1: Variants have correct personality values."""
    mock_claude_service.generate_content.return_value = json.dumps(VALID_VARIANTS_RESPONSE)
    result = await agent.generate_variants(SAMPLE_PROCESSED_INPUTS)

    personalities = {v["personality"] for v in result}
    assert personalities == {"bold", "structured", "provocative"}


async def test_generate_variants_adds_ids_if_missing(agent, mock_claude_service):
    """Variants without ids get auto-generated UUIDs."""
    response = {"variants": [{"personality": "bold", "post": "Test"}]}
    mock_claude_service.generate_content.return_value = json.dumps(response)
    result = await agent.generate_variants(SAMPLE_PROCESSED_INPUTS)

    for variant in result:
        assert "id" in variant
        assert len(variant["id"]) > 0


async def test_generate_variants_fallback_on_invalid_json(agent, mock_claude_service):
    """AC2: Falls back gracefully when JSON parsing fails."""
    mock_claude_service.generate_content.return_value = "Not valid JSON"
    result = await agent.generate_variants(SAMPLE_PROCESSED_INPUTS)
    assert isinstance(result, list)
    assert len(result) == 3  # Fallback generates 3 variants


async def test_generate_variants_cleans_escaped_newlines(agent, mock_claude_service):
    """Post text with escaped \\n sequences is cleaned to real newlines."""
    response = {
        "variants": [
            {"personality": "bold", "label": "Bold", "post": "Line1\\nLine2", "hashtags": [], "engagement_score": 7, "hook_strength": "Moderate", "suggestions": []}
        ]
    }
    mock_claude_service.generate_content.return_value = json.dumps(response)
    result = await agent.generate_variants(SAMPLE_PROCESSED_INPUTS)
    assert "\n" in result[0]["post"]
    assert "\\n" not in result[0]["post"]


# ---------------------------------------------------------------------------
# refine_variant() tests  (Story 2.1 AC3)
# ---------------------------------------------------------------------------

VALID_VARIANT_REFINE_PAYLOAD = {
    "post_text": "Refined bold: Everyone is wrong about X. Here's why Y matters.",
    "hashtags": ["Tech", "Innovation"],
    "engagement_score": 9.2,
    "hook_strength": "Exceptional",
    "suggestions": ["Perfect!"],
}


async def test_refine_variant_preserves_personality(agent, mock_claude_service):
    """AC3: refine_variant preserves and returns the personality field."""
    mock_claude_service.generate_with_conversation.return_value = json.dumps(VALID_VARIANT_REFINE_PAYLOAD)
    result = await agent.refine_variant("Original", "make it bolder", "bold", "Bold Approach")

    assert "personality" in result
    assert result["personality"] == "bold"


async def test_refine_variant_preserves_label(agent, mock_claude_service):
    """AC3: refine_variant preserves and returns the label field."""
    mock_claude_service.generate_with_conversation.return_value = json.dumps(VALID_VARIANT_REFINE_PAYLOAD)
    result = await agent.refine_variant("Original", "more structured", "structured", "Structured Approach")

    assert "label" in result
    assert result["label"] == "Structured Approach"


async def test_refine_variant_returns_changes(agent, mock_claude_service):
    """refine_variant includes the changes field."""
    mock_claude_service.generate_with_conversation.return_value = json.dumps(VALID_VARIANT_REFINE_PAYLOAD)
    result = await agent.refine_variant("Post", "feedback", "provocative")

    assert "changes" in result
    assert "feedback" in result["changes"]


async def test_refine_variant_without_personality_works(agent, mock_claude_service):
    """refine_variant works without personality (backward compat)."""
    mock_claude_service.generate_with_conversation.return_value = json.dumps(VALID_VARIANT_REFINE_PAYLOAD)
    result = await agent.refine_variant("Original", "feedback")

    assert "post_text" in result
    assert "engagement_score" in result
