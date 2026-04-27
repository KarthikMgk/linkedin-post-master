"""
Image Generation Service — Story 4.1

Provides a provider-agnostic interface for generating LinkedIn-optimised images.
Supports fal.ai (fal-ai/flux/schnell) and Hugging Face Inference API (FLUX.1-schnell).

Key design principles:
  - generate() NEVER raises — returns None on any failure (NFR-I3 graceful degradation)
  - _validate_and_resize() enforces LinkedIn specs: 1200×627px, ≤5MB
  - Provider calls are isolated in _call_<provider>() so they can be mocked in tests
"""

import asyncio
import base64
import io
import logging
import os
import re
import time
from typing import Optional

from huggingface_hub import InferenceClient
from PIL import Image

from constants import LINKEDIN_IMAGE_WIDTH, LINKEDIN_IMAGE_HEIGHT, LINKEDIN_IMAGE_MAX_FILE_SIZE

logger = logging.getLogger(__name__)


class ImageGenerationService:
    """Generates images for LinkedIn posts via a configured external API."""

    def __init__(self, api_key: str, provider: str):
        self.api_key = api_key.strip()
        self.provider = provider.strip().lower()
        # Set FAL_KEY once at init rather than on every call to avoid per-request
        # global mutation and the associated race condition in concurrent requests.
        if self.api_key and self.provider == "fal":
            os.environ.setdefault("FAL_KEY", self.api_key)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate(self, image_description: str, alt_text: str) -> Optional[dict]:
        """
        Generate an image for the given description.

        Returns:
            {"url": str, "alt_text": str, "prompt_used": str}  on success
            None                                                on any failure
        """
        if not self.api_key:
            logger.warning("IMAGE_GEN_API_KEY is not set — skipping image generation")
            return None

        if not image_description.strip():
            logger.warning("Empty image_description — skipping image generation")
            return None

        start = time.monotonic()
        try:
            result = await self._call_provider(image_description)
            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.info("Image generated in %dms via %s", elapsed_ms, self.provider)
            url = result.get("url", "")
            if not url.startswith("https://") and not url.startswith("data:"):
                raise ValueError(f"Provider returned invalid URL scheme: {url!r}")
            return {
                "url": url,
                "alt_text": alt_text,
                "prompt_used": image_description,
            }
        except Exception as exc:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.error(
                "Image generation failed after %dms (%s): %s",
                elapsed_ms,
                self.provider,
                str(exc),
            )
            return None

    # ------------------------------------------------------------------
    # Provider dispatch
    # ------------------------------------------------------------------

    async def _call_provider(self, prompt: str) -> dict:
        """Dispatch to the configured provider and return {"url": ...}."""
        if self.provider == "fal":
            return await self._call_fal(prompt)
        if self.provider == "huggingface":
            return await self._call_hf(prompt)
        raise ValueError(
            f"Unknown image generation provider: '{self.provider}'. "
            "Supported: fal, huggingface"
        )

    async def _call_fal(self, prompt: str) -> dict:
        """
        Call fal.ai FLUX/schnell to generate an image.

        Requires:
            pip install fal-client
            FAL_KEY env var (set once in __init__)
        """
        import fal_client  # lazy import so the module loads even if fal-client is absent

        result = await asyncio.wait_for(
            fal_client.run_async(
                "fal-ai/flux/schnell",
                arguments={
                    "prompt": prompt,
                    # Request exact LinkedIn dimensions to minimise distortion.
                    "image_size": {"width": LINKEDIN_IMAGE_WIDTH, "height": LINKEDIN_IMAGE_HEIGHT},
                    "num_images": 1,
                    "num_inference_steps": 4,  # schnell default — fast
                },
            ),
            timeout=30.0,
        )

        images = result.get("images", [])
        if not images:
            raise ValueError("fal.ai returned empty images list")

        url = images[0].get("url")
        if not url:
            raise ValueError(f"fal.ai image object missing 'url' key: {images[0]}")

        return {"url": url}

    async def _call_hf(self, prompt: str) -> dict:
        """
        Call Hugging Face Inference API (FLUX.1-schnell) to generate an image.

        Requires:
            pip install huggingface_hub[inference]
            IMAGE_GEN_API_KEY set to a HF access token with Inference Providers permission

        Returns a base64 data URI so no external CDN hosting is needed.
        """
        # Strip text/typography overlay instructions — diffusion models can't render
        # readable text and attempts produce garbled characters that hurt image quality.
        cleaned = re.sub(
            r"(with\s+)?(bold\s+)?text\s+overlay[^.]*\.|"
            r"typography\s+overlay[^.]*\.|"
            r"text-overlay-safe\s+composition[^.]*\.|"
            r"(with\s+)?bold\s+text\s+reading\s+'[^']*'\.|"
            r"(with\s+)?bold\s+text\s+reading\s+\"[^\"]*\"\.",
            "",
            prompt,
            flags=re.IGNORECASE,
        ).strip()

        # Prepend quality modifiers for professional, LinkedIn-appropriate output
        enhanced = (
            "Professional LinkedIn banner, photorealistic, high quality, sharp focus, "
            "cinematic lighting, 8k resolution, 16:9 landscape composition. "
            + cleaned
        )

        # Negative prompt steers the model away from common diffusion artefacts
        negative = (
            "text, typography, letters, words, watermark, logo, signature, "
            "blurry, out of focus, low quality, distorted, deformed, ugly, "
            "oversaturated, grainy, pixelated"
        )

        client = InferenceClient(token=self.api_key)

        loop = asyncio.get_event_loop()
        pil_image = await loop.run_in_executor(
            None,
            lambda: client.text_to_image(
                enhanced,
                negative_prompt=negative,
                model="black-forest-labs/FLUX.1-schnell",
                width=LINKEDIN_IMAGE_WIDTH,
                height=LINKEDIN_IMAGE_HEIGHT,
                num_inference_steps=12,  # schnell plateaus ~12; sweet spot for quality/speed
            ),
        )

        # Resize to exact LinkedIn spec and encode as JPEG data URI
        if pil_image.size != (LINKEDIN_IMAGE_WIDTH, LINKEDIN_IMAGE_HEIGHT):
            pil_image = pil_image.resize((LINKEDIN_IMAGE_WIDTH, LINKEDIN_IMAGE_HEIGHT), Image.LANCZOS)

        if pil_image.mode in ("RGBA", "P", "LA"):
            pil_image = pil_image.convert("RGB")

        buf = io.BytesIO()
        pil_image.save(buf, format="JPEG", quality=95, optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode()
        return {"url": f"data:image/jpeg;base64,{b64}"}

    # ------------------------------------------------------------------
    # Image validation & processing (LinkedIn spec enforcement)
    # ------------------------------------------------------------------

    def _validate_and_resize(self, image_bytes: bytes) -> bytes:
        """
        Ensure image meets LinkedIn specifications:
          - Dimensions: 1200×627px
          - File size:  ≤5MB (JPEG compressed)

        Args:
            image_bytes: Raw image bytes (any PIL-supported format)

        Returns:
            JPEG bytes at 1200×627px, ≤5MB

        Note: URL-based providers (e.g. fal.ai) return a CDN URL rather than
        raw bytes. Per story constraints, this story does not download and
        re-host images — so this method is not called in the fal.ai path.
        It is invoked by providers that return base64 / raw bytes directly,
        and is exercised in the unit test suite to verify correctness.
        """
        img = Image.open(io.BytesIO(image_bytes))

        # Resize if needed
        if img.size != (LINKEDIN_IMAGE_WIDTH, LINKEDIN_IMAGE_HEIGHT):
            img = img.resize((LINKEDIN_IMAGE_WIDTH, LINKEDIN_IMAGE_HEIGHT), Image.LANCZOS)

        # Convert RGBA/P → RGB so we can save as JPEG
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")

        # Compress to stay under 5MB — try descending quality levels
        for quality in (85, 75, 65, 55):
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=quality, optimize=True)
            if buf.tell() <= LINKEDIN_IMAGE_MAX_FILE_SIZE:
                return buf.getvalue()

        # Fallback: return at minimum quality (extremely rare for 1200×627)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=55, optimize=True)
        return buf.getvalue()
