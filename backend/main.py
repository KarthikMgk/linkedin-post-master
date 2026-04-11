"""
LinkedIn Post Generator - FastAPI Backend
Main application entry point
"""
import time
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List
import os
from dotenv import load_dotenv

from services.claude_service import ClaudeService
from services.input_processor import InputProcessor
from agents.content_agent import ContentGenerationAgent
from utils.exceptions import InvalidFileError, RateLimitError, ServiceUnavailableError
from utils.logger import get_logger

# Load environment variables
load_dotenv()

logger = get_logger(__name__)

app = FastAPI(
    title="LinkedIn Post Generator API",
    description="AI-powered LinkedIn post generation with multi-input synthesis",
    version="0.1.0"
)

# CORS — FRONTEND_URL is a comma-separated list so both the Vercel production
# domain and localhost can be allowed simultaneously without wildcards.
# P-6: fall back to localhost if env var is unset or empty.
_allowed_origins = [
    url.strip()
    for url in os.getenv("FRONTEND_URL", "").split(",")
    if url.strip()
] or ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize services
claude_service = ClaudeService(api_key=os.getenv("ANTHROPIC_API_KEY"))
input_processor = InputProcessor()
content_agent = ContentGenerationAgent(claude_service)


# ---------------------------------------------------------------------------
# Centralised error response helpers
# ---------------------------------------------------------------------------

def _error_response(status_code: int, code: str, message: str, retry_after: int = None) -> JSONResponse:
    body = {"success": False, "error": {"code": code, "message": message}}
    if retry_after is not None:
        body["error"]["retryAfter"] = retry_after
    return JSONResponse(status_code=status_code, content=body)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    code_map = {400: "BAD_REQUEST", 401: "UNAUTHORIZED", 403: "FORBIDDEN",
                404: "NOT_FOUND", 422: "VALIDATION_ERROR", 500: "INTERNAL_ERROR",
                503: "SERVICE_UNAVAILABLE"}
    code = code_map.get(exc.status_code, "ERROR")
    return _error_response(exc.status_code, code, exc.detail)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return _error_response(422, "VALIDATION_ERROR", str(exc))


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "LinkedIn Post Generator API",
        "version": "0.1.0"
    }


@app.get("/api/health")
async def health_check():
    """Detailed health check with API connectivity"""
    try:
        api_status = await claude_service.test_connection()
        if not api_status:
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "claude_api": "error"}
            )
        return {
            "status": "healthy",
            "claude_api": "connected"
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.post("/api/generate")
async def generate_post(
    text_input: Optional[str] = Form(default=None),
    pdf_file: Optional[UploadFile] = File(default=None),
    image_files: List[UploadFile] = File(default=[]),
    url_input: Optional[str] = Form(default=None),
):
    """
    Generate optimized LinkedIn post from multiple input sources.
    """
    start_time = time.monotonic()
    try:
        has_text = text_input and text_input.strip()
        has_url = url_input and url_input.strip()

        if not any([has_text, pdf_file, image_files, has_url]):
            raise HTTPException(
                status_code=400,
                detail="At least one input source required (text, PDF, image, or URL)"
            )

        processed_inputs = await input_processor.process_inputs(
            text=text_input,
            pdf=pdf_file,
            images=image_files if image_files else None,
            url=url_input
        )

        # Generate 3 variants (Story 2.1)
        variants = await content_agent.generate_variants(processed_inputs)

        if not variants:
            raise HTTPException(status_code=500, detail="Content generation returned no variants")

        # Get first variant for backward compatibility (single-variant consumers)
        first_variant = variants[0]

        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        logger.info(
            "POST /api/generate - inputs: %d, time: %dms, score: %s",
            len(processed_inputs),
            elapsed_ms,
            first_variant.get("engagement_score", "n/a"),
        )

        return {
            "success": True,
            # Backward compatibility: top-level fields from first variant
            "post": first_variant.get("post", ""),
            "hashtags": first_variant.get("hashtags", []),
            "engagement_score": first_variant.get("engagement_score", 0),
            "hook_strength": first_variant.get("hook_strength", ""),
            "suggestions": first_variant.get("suggestions", []),
            "cta": first_variant.get("cta", ""),
            "image_alt_text": first_variant.get("image_alt_text", ""),
            # Story 2.1: new variants array
            "variants": variants,
            "metadata": {
                "inputs_processed": len(processed_inputs),
                "primary_source": processed_inputs[0]["type"] if processed_inputs else None
            }
        }

    except HTTPException:
        raise
    except InvalidFileError as e:
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        logger.error("Invalid file in generate request (%dms): %s", elapsed_ms, str(e), exc_info=True)
        return _error_response(400, "INVALID_FILE", str(e))
    except RateLimitError as e:
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        logger.error("Rate limit in generate request (%dms): %s", elapsed_ms, str(e), exc_info=True)
        return _error_response(
            503, "RATE_LIMIT_EXCEEDED",
            "AI service rate limit reached. Please try again in 60 seconds.",
            retry_after=e.retry_after,
        )
    except ServiceUnavailableError as e:
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        logger.error("Service unavailable in generate request (%dms): %s", elapsed_ms, str(e), exc_info=True)
        return _error_response(503, "SERVICE_UNAVAILABLE", str(e))
    except Exception as e:
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        logger.error("Unhandled error in generate request (%dms): %s", elapsed_ms, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.post("/api/refine")
async def refine_post(
    post_text: str = Form(...),
    feedback: str = Form(...),
    variant_id: Optional[str] = Form(default=None),
    personality: Optional[str] = Form(default=None),
    label: Optional[str] = Form(default=None),
):
    """
    Refine existing post based on conversational feedback.
    Supports variant-specific refinement (Story 2.1 AC3).
    """
    # P-14: validate personality against allowed values
    _VALID_PERSONALITIES = {"bold", "structured", "provocative"}
    if personality and personality not in _VALID_PERSONALITIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid personality '{personality}'. Must be one of: {', '.join(sorted(_VALID_PERSONALITIES))}."
        )

    start_time = time.monotonic()
    try:
        # If personality provided, use variant-specific refinement (Story 2.1)
        if personality:
            refined_result = await content_agent.refine_variant(
                post_text, feedback, personality, label
            )
        else:
            refined_result = await content_agent.refine_post(post_text, feedback)

        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        logger.info(
            "POST /api/refine - time: %dms, score: %s, personality: %s",
            elapsed_ms,
            refined_result.get("engagement_score", "n/a"),
            refined_result.get("personality", "default"),
        )

        response = {
            "success": True,
            "refined_post": refined_result["post_text"],
            "changes_made": refined_result.get("changes", []),
            "engagement_score": refined_result["engagement_score"],
            "hook_strength": refined_result.get("hook_strength", ""),
            "hashtags": refined_result.get("hashtags", []),
            "suggestions": refined_result.get("suggestions", []),
            "cta": refined_result.get("cta", ""),
        }

        # Story 2.1 AC3: preserve personality and label
        if personality:
            response["personality"] = refined_result.get("personality", personality)
            response["label"] = refined_result.get("label", label)

        return response

    except RateLimitError as e:
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        logger.error("Rate limit in refine request (%dms): %s", elapsed_ms, str(e), exc_info=True)
        return _error_response(
            503, "RATE_LIMIT_EXCEEDED",
            "AI service rate limit reached. Please try again in 60 seconds.",
            retry_after=e.retry_after,
        )
    except ServiceUnavailableError as e:
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        logger.error("Service unavailable in refine request (%dms): %s", elapsed_ms, str(e), exc_info=True)
        return _error_response(503, "SERVICE_UNAVAILABLE", str(e))
    except Exception as e:
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        logger.error("Unhandled error in refine request (%dms): %s", elapsed_ms, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Refinement failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "True") == "True"
    )
