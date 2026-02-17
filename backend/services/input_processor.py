"""
Input Processing Service
Handles multi-format input processing (text, PDF, images, URLs)
"""
import io
import PyPDF2
import pytesseract
from PIL import Image
from typing import List, Dict, Optional
from fastapi import UploadFile


class InputProcessor:
    """Service for processing multiple input types"""

    async def process_inputs(
        self,
        text: Optional[str] = None,
        pdf: Optional[UploadFile] = None,
        images: Optional[List[UploadFile]] = None,
        url: Optional[str] = None
    ) -> List[Dict]:
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

        # Process text input
        if text and text.strip():
            processed.append({
                "type": "text",
                "content": text.strip(),
                "priority": "primary"
            })

        # Process PDF
        if pdf:
            pdf_content = await self._extract_pdf_text(pdf)
            if pdf_content:
                processed.append({
                    "type": "pdf",
                    "content": pdf_content,
                    "priority": "primary" if not text else "supporting"
                })

        # Process images
        if images:
            for img in images:
                img_text = await self._extract_image_text(img)
                if img_text:
                    processed.append({
                        "type": "image",
                        "content": img_text,
                        "priority": "supporting"
                    })

        # Process URL (placeholder for now)
        if url:
            processed.append({
                "type": "url",
                "content": f"URL provided: {url} (URL extraction coming in Phase 2)",
                "priority": "supporting"
            })

        # Auto-detect primary content if not explicitly set
        if processed and not any(p["priority"] == "primary" for p in processed):
            processed[0]["priority"] = "primary"

        return processed

    async def _extract_pdf_text(self, pdf_file: UploadFile) -> str:
        """
        Extract text content from PDF

        Args:
            pdf_file: Uploaded PDF file

        Returns:
            Extracted text content
        """
        try:
            # Read PDF file
            content = await pdf_file.read()
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))

            # Extract text from all pages
            text_parts = []
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

            return "\n\n".join(text_parts)

        except Exception as e:
            print(f"PDF extraction error: {e}")
            return ""

    async def _extract_image_text(self, image_file: UploadFile) -> str:
        """
        Extract text from image using OCR

        Args:
            image_file: Uploaded image file

        Returns:
            Extracted text content
        """
        try:
            # Read image file
            content = await image_file.read()
            image = Image.open(io.BytesIO(content))

            # Perform OCR
            text = pytesseract.image_to_string(image)

            return text.strip()

        except Exception as e:
            print(f"Image OCR error: {e}")
            return ""
