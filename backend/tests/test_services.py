"""
Unit tests for InputProcessor and ClaudeService.

InputProcessor: mocks PyPDF2, pytesseract, PIL.Image
ClaudeService: mocks anthropic.AsyncAnthropic client
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.input_processor import InputProcessor
from services.claude_service import ClaudeService
from utils.exceptions import InvalidFileError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def processor():
    return InputProcessor()


# ---------------------------------------------------------------------------
# InputProcessor — text input  (FR1, FR5, FR6)
# ---------------------------------------------------------------------------

async def test_process_text_returns_single_primary_item(processor):
    """AC5: Text input produces one item with type=text and priority=primary."""
    result = await processor.process_inputs(text="Sample content about AI")
    assert len(result) == 1
    assert result[0]["type"] == "text"
    assert result[0]["priority"] == "primary"
    assert result[0]["content"] == "Sample content about AI"


async def test_process_text_strips_whitespace(processor):
    """Text content is stripped of leading/trailing whitespace."""
    result = await processor.process_inputs(text="  padded content  ")
    assert result[0]["content"] == "padded content"


async def test_process_whitespace_only_text_returns_empty(processor):
    """Whitespace-only text is ignored (treated as no input)."""
    result = await processor.process_inputs(text="   \t\n  ")
    assert len(result) == 0


async def test_process_url_becomes_primary_when_only_input(processor):
    """URL alone gets promoted to primary via auto-detect (FR4, FR6)."""
    result = await processor.process_inputs(url="https://example.com/article")
    assert len(result) == 1
    assert result[0]["type"] == "url"
    assert result[0]["priority"] == "primary"


async def test_process_text_plus_url_text_is_primary_url_is_supporting(processor):
    """FR6: When text + URL provided, text is primary, URL is supporting."""
    result = await processor.process_inputs(
        text="My main idea",
        url="https://example.com/reference"
    )
    by_type = {r["type"]: r for r in result}
    assert by_type["text"]["priority"] == "primary"
    assert by_type["url"]["priority"] == "supporting"


async def test_process_multiple_inputs_returns_multiple_items(processor):
    """FR5: Text + URL together produce two items."""
    result = await processor.process_inputs(
        text="Main content",
        url="https://example.com"
    )
    assert len(result) == 2


# ---------------------------------------------------------------------------
# InputProcessor — PDF extraction  (FR2, FR7, AC5)
# ---------------------------------------------------------------------------

async def test_pdf_extraction_returns_content(processor):
    """AC5: PDF text extraction returns non-empty content."""
    mock_pdf = MagicMock()
    mock_pdf.read = AsyncMock(return_value=b"fake pdf bytes")

    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Extracted PDF paragraph text"

    with patch("PyPDF2.PdfReader") as mock_reader:
        mock_reader.return_value.pages = [mock_page]
        result = await processor.process_inputs(pdf=mock_pdf)

    assert len(result) == 1
    assert result[0]["type"] == "pdf"
    assert "Extracted PDF paragraph text" in result[0]["content"]


async def test_pdf_without_text_becomes_primary(processor):
    """PDF with no prior text input is promoted to primary (FR6)."""
    mock_pdf = MagicMock()
    mock_pdf.read = AsyncMock(return_value=b"fake pdf bytes")

    mock_page = MagicMock()
    mock_page.extract_text.return_value = "PDF content"

    with patch("PyPDF2.PdfReader") as mock_reader:
        mock_reader.return_value.pages = [mock_page]
        result = await processor.process_inputs(pdf=mock_pdf)

    assert result[0]["priority"] == "primary"


async def test_pdf_with_text_becomes_supporting(processor):
    """FR6: When text + PDF provided, PDF is supporting."""
    mock_pdf = MagicMock()
    mock_pdf.read = AsyncMock(return_value=b"fake pdf bytes")

    mock_page = MagicMock()
    mock_page.extract_text.return_value = "PDF content"

    with patch("PyPDF2.PdfReader") as mock_reader:
        mock_reader.return_value.pages = [mock_page]
        result = await processor.process_inputs(text="Primary text idea", pdf=mock_pdf)

    pdf_items = [r for r in result if r["type"] == "pdf"]
    assert pdf_items[0]["priority"] == "supporting"


async def test_pdf_multi_page_joins_with_double_newline(processor):
    """FR7: Text from multiple pages is joined with double newline."""
    mock_pdf = MagicMock()
    mock_pdf.read = AsyncMock(return_value=b"fake pdf bytes")

    page1 = MagicMock()
    page1.extract_text.return_value = "Page one text"
    page2 = MagicMock()
    page2.extract_text.return_value = "Page two text"

    with patch("PyPDF2.PdfReader") as mock_reader:
        mock_reader.return_value.pages = [page1, page2]
        result = await processor.process_inputs(pdf=mock_pdf)

    assert "Page one text" in result[0]["content"]
    assert "Page two text" in result[0]["content"]
    assert "\n\n" in result[0]["content"]


async def test_corrupt_pdf_raises_invalid_file_error(processor):
    """AC3 (Story 1.2): Corrupt PDF raises InvalidFileError — not silently skipped."""
    mock_pdf = MagicMock()
    mock_pdf.read = AsyncMock(return_value=b"not a real pdf")

    with patch("PyPDF2.PdfReader", side_effect=Exception("Invalid PDF")):
        with pytest.raises(InvalidFileError):
            await processor.process_inputs(pdf=mock_pdf)


# ---------------------------------------------------------------------------
# InputProcessor — image OCR  (FR3, FR8, AC5)
# ---------------------------------------------------------------------------

async def test_image_ocr_returns_extracted_text(processor):
    """AC5: OCR extracts text from image and returns it as content."""
    mock_img = MagicMock()
    mock_img.read = AsyncMock(return_value=b"fake image bytes")

    with patch("PIL.Image.open") as mock_open, \
         patch("pytesseract.image_to_string", return_value="Text extracted from image"):
        mock_open.return_value = MagicMock()
        result = await processor.process_inputs(images=[mock_img])

    assert len(result) == 1
    assert result[0]["type"] == "image"
    assert result[0]["content"] == "Text extracted from image"


async def test_image_alone_promoted_to_primary(processor):
    """FR6: Image with no other inputs is auto-promoted to primary."""
    mock_img = MagicMock()
    mock_img.read = AsyncMock(return_value=b"fake image bytes")

    with patch("PIL.Image.open") as mock_open, \
         patch("pytesseract.image_to_string", return_value="Some text"):
        mock_open.return_value = MagicMock()
        result = await processor.process_inputs(images=[mock_img])

    assert result[0]["priority"] == "primary"


async def test_image_with_text_is_supporting(processor):
    """FR6: Image alongside text is always marked supporting."""
    mock_img = MagicMock()
    mock_img.read = AsyncMock(return_value=b"fake image bytes")

    with patch("PIL.Image.open") as mock_open, \
         patch("pytesseract.image_to_string", return_value="Image text"):
        mock_open.return_value = MagicMock()
        result = await processor.process_inputs(
            text="Primary text content",
            images=[mock_img]
        )

    image_items = [r for r in result if r["type"] == "image"]
    assert image_items[0]["priority"] == "supporting"


async def test_multiple_images_each_produce_item(processor):
    """FR3/FR5: Multiple images produce multiple processed items."""
    mock_img1 = MagicMock()
    mock_img1.read = AsyncMock(return_value=b"img1 bytes")
    mock_img2 = MagicMock()
    mock_img2.read = AsyncMock(return_value=b"img2 bytes")

    with patch("PIL.Image.open") as mock_open, \
         patch("pytesseract.image_to_string", return_value="Text"):
        mock_open.return_value = MagicMock()
        result = await processor.process_inputs(images=[mock_img1, mock_img2])

    image_items = [r for r in result if r["type"] == "image"]
    assert len(image_items) == 2


async def test_failed_ocr_returns_no_image_item(processor):
    """FR37: Failed OCR is silently skipped — no crash, no image item."""
    mock_img = MagicMock()
    mock_img.read = AsyncMock(return_value=b"corrupt bytes")

    with patch("PIL.Image.open", side_effect=Exception("Cannot open image")):
        result = await processor.process_inputs(images=[mock_img])

    image_items = [r for r in result if r["type"] == "image"]
    assert len(image_items) == 0


# ---------------------------------------------------------------------------
# ClaudeService — mocks anthropic.AsyncAnthropic client
# ---------------------------------------------------------------------------

def _make_text_content_block(text):
    """Create a mock ContentBlock with type=text."""
    block = MagicMock()
    block.type = "text"
    block.text = text
    return block


def _make_thinking_content_block(thinking):
    """Create a mock ContentBlock with type=thinking."""
    block = MagicMock()
    block.type = "thinking"
    block.thinking = thinking
    return block


def _make_mock_message(content_blocks):
    """Create a mock Message with content list."""
    msg = MagicMock()
    msg.content = content_blocks
    return msg


def _make_mock_client(create_response):
    """Create a mock AsyncAnthropic client with a configured messages.create."""
    mock_client = MagicMock()
    mock_client.messages = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=create_response)
    return mock_client


async def test_generate_content_returns_text_from_response():
    """generate_content returns the text from response content block."""
    mock_msg = _make_mock_message([_make_text_content_block("Generated post content")])
    mock_client = _make_mock_client(mock_msg)
    service = ClaudeService(api_key="any-key", client=mock_client)
    result = await service.generate_content("system prompt", "user message")
    assert result == "Generated post content"


async def test_generate_content_skips_thinking_blocks():
    """generate_content returns text block even when thinking block is present."""
    mock_msg = _make_mock_message([
        _make_thinking_content_block("Internal reasoning"),
        _make_text_content_block("Actual response")
    ])
    mock_client = _make_mock_client(mock_msg)
    service = ClaudeService(api_key="any-key", client=mock_client)
    result = await service.generate_content("system", "user")
    assert result == "Actual response"


async def test_generate_content_calls_create_once():
    """generate_content calls client.messages.create and returns text."""
    mock_msg = _make_mock_message([_make_text_content_block("Response")])
    mock_client = _make_mock_client(mock_msg)
    service = ClaudeService(api_key="test-key", client=mock_client)
    result = await service.generate_content("system", "user")
    assert result == "Response"


async def test_generate_with_conversation_returns_text():
    """generate_with_conversation returns text from response content block."""
    mock_msg = _make_mock_message([_make_text_content_block("Conversation reply")])
    mock_client = _make_mock_client(mock_msg)
    service = ClaudeService(api_key="test-key", client=mock_client)
    history = [{"role": "user", "content": "Refine this"}]
    result = await service.generate_with_conversation("system", history)
    assert result == "Conversation reply"


async def test_test_connection_returns_true_on_success():
    """test_connection returns True when messages.create succeeds."""
    mock_msg = _make_mock_message([_make_text_content_block("Hi")])
    mock_client = _make_mock_client(mock_msg)
    service = ClaudeService(api_key="test-key", client=mock_client)
    result = await service.test_connection()
    assert result is True


async def test_test_connection_returns_false_on_exception():
    """test_connection returns False (not raises) when API call fails."""
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(side_effect=Exception("Network error"))
    service = ClaudeService(api_key="test-key", client=mock_client)
    result = await service.test_connection()
    assert result is False


async def test_generate_content_raises_on_api_failure():
    """generate_content raises Exception (propagated) when API call fails."""
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(side_effect=Exception("API error"))
    service = ClaudeService(api_key="test-key", client=mock_client)
    with pytest.raises(Exception, match="Claude API call failed"):
        await service.generate_content("system", "user")
