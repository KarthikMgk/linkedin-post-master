"""
LinkedIn Post Generator - FastAPI Backend
Main application entry point
"""

import os
import time
from typing import Any, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from agents.content_agent import ContentGenerationAgent
from auth.allowlist import is_allowed
from auth.google_auth import verify_google_token
from auth.jwt_handler import create_jwt
from middleware.auth_middleware import require_auth
from services.claude_service import ClaudeService
from services.input_processor import InputProcessor
from utils.exceptions import InvalidFileError, RateLimitError, ServiceUnavailableError
from utils.logger import get_logger

# Load environment variables
load_dotenv()

logger = get_logger(__name__)

# Warn loudly at startup if required auth env vars are missing
_REQUIRED_AUTH_VARS = ["GOOGLE_CLIENT_ID", "ALLOWED_EMAILS", "JWT_SECRET"]
for _var in _REQUIRED_AUTH_VARS:
    if not os.getenv(_var, "").strip():
        logger.warning("Auth env var %s is not set — login will fail until configured.", _var)

app = FastAPI(
    title="LinkedIn Post Generator API",
    description="AI-powered LinkedIn post generation with multi-input synthesis",
    version="0.1.0",
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — FRONTEND_URL is a comma-separated list so both the Vercel production
# domain and localhost can be allowed simultaneously without wildcards.
# Fall back to localhost if env var is unset or empty.
_allowed_origins = [
    url.strip() for url in os.getenv("FRONTEND_URL", "").split(",") if url.strip()
] or ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Initialize services
claude_service = ClaudeService(api_key=os.getenv("ANTHROPIC_API_KEY") or "")
input_processor = InputProcessor()
content_agent = ContentGenerationAgent(claude_service)


class GoogleAuthRequest(BaseModel):
    token: str


# ---------------------------------------------------------------------------
# Centralised error response helper
# ---------------------------------------------------------------------------


def _error_response(
    status_code: int, code: str, message: str, retry_after: Optional[int] = None
) -> JSONResponse:
    body: dict[str, Any] = {"success": False, "error": {"code": code, "message": message}}
    if retry_after is not None:
        body["error"]["retryAfter"] = retry_after
    return JSONResponse(status_code=status_code, content=body)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        422: "VALIDATION_ERROR",
        500: "INTERNAL_ERROR",
        503: "SERVICE_UNAVAILABLE",
    }
    code = code_map.get(exc.status_code, "ERROR")
    return _error_response(exc.status_code, code, exc.detail)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return _error_response(422, "VALIDATION_ERROR", str(exc))


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/")
async def root():
    return {"status": "running", "service": "LinkedIn Post Generator API", "version": "0.1.0"}


@app.get("/api/health")
async def health_check():
    """Public health check — no auth required."""
    try:
        api_status = await claude_service.test_connection()
        if not api_status:
            return JSONResponse(
                status_code=503, content={"status": "unhealthy", "claude_api": "error"}
            )
        return {"status": "healthy", "claude_api": "connected"}
    except Exception:
        logger.exception("Health check failed while testing Claude API connection")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": "Internal server error"},
        )


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------


@app.post("/api/auth/google")
@limiter.limit("10/minute")
async def auth_google(request: Request, body: GoogleAuthRequest):
    """
    Exchange a Google id_token for an application JWT.
    Rate limited to 10 requests/minute per IP.
    """
    try:
        payload = verify_google_token(body.token)
    except ValueError as exc:
        # Log the real reason so it shows in backend logs
        logger.warning("Google token verification failed: %s", exc)
        return _error_response(401, "INVALID_TOKEN", str(exc))

    email = payload.get("email", "")
    if not is_allowed(email):
        logger.info("Access denied for email: %s", email)
        return _error_response(403, "ACCESS_DENIED", "Access denied. This app is invite-only.")

    try:
        token = create_jwt(
            email=email,
            name=payload.get("name", ""),
            picture=payload.get("picture", ""),
        )
    except RuntimeError as exc:
        logger.error("JWT creation failed: %s", exc)
        return _error_response(500, "SERVER_ERROR", str(exc))

    logger.info("Auth success: %s", email)
    return {
        "success": True,
        "token": token,
        "user": {
            "email": email,
            "name": payload.get("name", ""),
            "picture": payload.get("picture", ""),
        },
    }


@app.get("/api/auth/me")
async def auth_me(email: str = Depends(require_auth)):
    """Return current user info. Quota info added in Story 5.3."""
    return {"success": True, "email": email}


# ---------------------------------------------------------------------------
# Generation endpoints (auth required)
# ---------------------------------------------------------------------------


@app.post("/api/generate")
async def generate_post(
    email: str = Depends(require_auth),
    text_input: Optional[str] = Form(default=None),
    pdf_file: Optional[UploadFile] = File(default=None),
    image_files: list[UploadFile] = File(default=[]),
    url_input: Optional[str] = Form(default=None),
):
    """
    Generate optimized LinkedIn post from multiple input sources.
    Requires a valid JWT (issued by /api/auth/google).
    """
    start_time = time.monotonic()
    try:
        has_text = text_input and text_input.strip()
        has_url = url_input and url_input.strip()

        if not any([has_text, pdf_file, image_files, has_url]):
            raise HTTPException(
                status_code=400,
                detail="At least one input source required (text, PDF, image, or URL)",
            )

        processed_inputs = await input_processor.process_inputs(
            text=text_input,
            pdf=pdf_file,
            images=image_files if image_files else None,
            url=url_input,
        )

        variants = await content_agent.generate_variants(processed_inputs)

        if not variants:
            raise HTTPException(status_code=500, detail="Content generation returned no variants")

        first_variant = variants[0]

        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        logger.info(
            "POST /api/generate - user: %s, inputs: %d, time: %dms, score: %s",
            email,
            len(processed_inputs),
            elapsed_ms,
            first_variant.get("engagement_score", "n/a"),
        )

        return {
            "success": True,
            "post": first_variant.get("post", ""),
            "hashtags": first_variant.get("hashtags", []),
            "engagement_score": first_variant.get("engagement_score", 0),
            "hook_strength": first_variant.get("hook_strength", ""),
            "suggestions": first_variant.get("suggestions", []),
            "cta": first_variant.get("cta", ""),
            "image_alt_text": first_variant.get("image_alt_text", ""),
            "variants": variants,
            "metadata": {
                "inputs_processed": len(processed_inputs),
                "primary_source": processed_inputs[0]["type"] if processed_inputs else None,
            },
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
            503,
            "RATE_LIMIT_EXCEEDED",
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
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}") from e


@app.post("/api/refine")
async def refine_post(
    email: str = Depends(require_auth),
    post_text: str = Form(...),
    feedback: str = Form(...),
    variant_id: Optional[str] = Form(default=None),
    personality: Optional[str] = Form(default=None),
    label: Optional[str] = Form(default=None),
):
    """
    Refine existing post based on conversational feedback.
    Supports variant-specific refinement (Story 2.1 AC3).
    Requires a valid JWT.
    """
    _VALID_PERSONALITIES = {"bold", "structured", "provocative"}
    if personality and personality not in _VALID_PERSONALITIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid personality '{personality}'. Must be one of: {', '.join(sorted(_VALID_PERSONALITIES))}.",
        )

    start_time = time.monotonic()
    try:
        if personality:
            refined_result = await content_agent.refine_variant(
                post_text, feedback, personality, label
            )
        else:
            refined_result = await content_agent.refine_post(post_text, feedback)

        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        logger.info(
            "POST /api/refine - user: %s, time: %dms, score: %s, personality: %s",
            email,
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

        if personality:
            response["personality"] = refined_result.get("personality", personality)
            response["label"] = refined_result.get("label", label)

        return response

    except RateLimitError as e:
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        logger.error("Rate limit in refine request (%dms): %s", elapsed_ms, str(e), exc_info=True)
        return _error_response(
            503,
            "RATE_LIMIT_EXCEEDED",
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
        raise HTTPException(status_code=500, detail=f"Refinement failed: {str(e)}") from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "True") == "True",
    )
