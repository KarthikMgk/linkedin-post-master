"""
Input Processing Service
Handles multi-format input processing (text, PDF, images, URLs)
"""

import asyncio
import atexit
import io
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import PyPDF2
import pytesseract
from fastapi import UploadFile
from PIL import Image

from utils.exceptions import InvalidFileError
from utils.logger import get_logger
from utils.sanitizer import sanitize_input

logger = get_logger(__name__)

# Thread pool for running blocking OCR without blocking the event loop
_ocr_executor = ThreadPoolExecutor(max_workers=4)
atexit.register(_ocr_executor.shutdown, wait=False)


class InputProcessor:
    """Service for processing multiple input types"""

    async def process_inputs(
        self,
        text: Optional[str] = None,
        pdf: Optional[UploadFile] = None,
        images: Optional[list[UploadFile]] = None,
        url: Optional[str] = None,
    ) -> list[dict]:
        """
        Process all input sources and return structured data

        Args:
            text: Plain text input
            pdf: PDF file upload
            images: List of image uploads
            url: URL for content extraction

        Returns:
            List of processed inputs with metadata
        """
        processed = []

        # Process text input — sanitize before storing
        if text and text.strip():
            processed.append(
                {"type": "text", "content": sanitize_input(text.strip()), "priority": "primary"}
            )

        # Process PDF — raises InvalidFileError on corrupt input
        if pdf:
            pdf_content = await self._extract_pdf_text(pdf)
            if pdf_content:
                processed.append(
                    {
                        "type": "pdf",
                        "content": sanitize_input(pdf_content),
                        "priority": "primary" if not text else "supporting",
                    }
                )

        # Process images
        if images:
            for img in images:
                img_text = await self._extract_image_text(img)
                if img_text:
                    processed.append(
                        {
                            "type": "image",
                            "content": sanitize_input(img_text),
                            "priority": "supporting",
                        }
                    )

        # Process URL (placeholder for now)
        if url:
            processed.append(
                {
                    "type": "url",
                    "content": f"URL provided: {url} (URL extraction coming in Phase 2)",
                    "priority": "supporting",
                }
            )

        # Auto-detect primary content if not explicitly set
        if processed and not any(p["priority"] == "primary" for p in processed):
            processed[0]["priority"] = "primary"

        return processed

    # P-4: max file sizes enforced before reading into memory
    _MAX_PDF_BYTES = 10 * 1024 * 1024  # 10 MB
    _MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB

    # P-17: allowed MIME types
    _ALLOWED_PDF_TYPES = {"application/pdf"}
    _ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif"}

    async def _extract_pdf_text(self, pdf_file: UploadFile) -> str:
        """
        Extract text content from PDF.

        Raises:
            InvalidFileError: If the PDF cannot be read, parsed, or exceeds size/type limits.

        Returns:
            Extracted text content.
        """
        try:
            # P-17: validate MIME type when content_type is explicitly provided as a string
            if (
                isinstance(pdf_file.content_type, str)
                and pdf_file.content_type not in self._ALLOWED_PDF_TYPES
            ):
                raise InvalidFileError(
                    f"Unsupported file type '{pdf_file.content_type}'. Only PDF files are accepted."
                )

            content = await pdf_file.read()

            # P-4: enforce file size limit after read (UploadFile.size is not always populated)
            if len(content) > self._MAX_PDF_BYTES:
                raise InvalidFileError(
                    f"PDF file exceeds the 10 MB limit ({len(content) // (1024 * 1024)} MB uploaded)."
                )

            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))

            text_parts = []
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

            return "\n\n".join(text_parts)

        except InvalidFileError:
            raise
        except Exception as e:
            logger.error("PDF extraction error: %s", str(e), exc_info=True)
            raise InvalidFileError(f"PDF file is corrupt or unreadable: {str(e)}") from e

    async def _extract_image_text(self, image_file: UploadFile) -> str:
        """
        Extract text from image using OCR.

        Returns:
            Extracted text content, or empty string on failure (silently skipped).
        """
        try:
            # P-17: validate MIME type when content_type is explicitly provided as a string
            if (
                isinstance(image_file.content_type, str)
                and image_file.content_type not in self._ALLOWED_IMAGE_TYPES
            ):
                logger.warning(
                    "Image OCR skipped: unsupported type '%s' for file '%s'",
                    image_file.content_type,
                    image_file.filename,
                )
                return ""

            content = await image_file.read()

            # P-4: enforce file size limit
            if len(content) > self._MAX_IMAGE_BYTES:
                logger.warning(
                    "Image OCR skipped: file '%s' exceeds 5 MB limit",
                    image_file.filename,
                )
                return ""
            image = Image.open(io.BytesIO(content))

            # Run blocking OCR in thread pool to avoid blocking the event loop
            loop = asyncio.get_running_loop()
            text = await loop.run_in_executor(_ocr_executor, pytesseract.image_to_string, image)
            return text.strip()

        except Exception as e:
            logger.error("Image OCR error: %s", str(e), exc_info=True)
            return ""
