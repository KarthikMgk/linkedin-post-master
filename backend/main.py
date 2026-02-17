"""
LinkedIn Post Generator - FastAPI Backend
Main application entry point
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List
import os
from dotenv import load_dotenv

from services.claude_service import ClaudeService
from services.input_processor import InputProcessor
from agents.content_agent import ContentGenerationAgent

# Load environment variables
load_dotenv()

app = FastAPI(
    title="LinkedIn Post Generator API",
    description="AI-powered LinkedIn post generation with multi-input synthesis",
    version="0.1.0"
)

# CORS configuration for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
claude_service = ClaudeService(api_key=os.getenv("ANTHROPIC_API_KEY"))
input_processor = InputProcessor()
content_agent = ContentGenerationAgent(claude_service)


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
        # Test Claude API connectivity
        api_status = await claude_service.test_connection()
        return {
            "status": "healthy",
            "claude_api": "connected" if api_status else "error"
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
    Generate optimized LinkedIn post from multiple input sources

    Args:
        text_input: Plain text content
        pdf_file: PDF document upload
        image_files: Image files (JPG, PNG)
        url_input: URL for content extraction

    Returns:
        Generated LinkedIn post with engagement optimization
    """
    try:
        # Log incoming request
        print(f"Received request - text: {bool(text_input and text_input.strip())}, pdf: {bool(pdf_file)}, images: {len(image_files)}, url: {bool(url_input and url_input.strip())}")

        # Validate at least one input provided (handle empty strings)
        has_text = text_input and text_input.strip()
        has_url = url_input and url_input.strip()

        if not any([has_text, pdf_file, image_files, has_url]):
            raise HTTPException(
                status_code=400,
                detail="At least one input source required (text, PDF, image, or URL)"
            )

        # Process all inputs
        processed_inputs = await input_processor.process_inputs(
            text=text_input,
            pdf=pdf_file,
            images=image_files if image_files else None,
            url=url_input
        )

        print(f"Processed {len(processed_inputs)} inputs")

        # Generate LinkedIn post using content agent
        result = await content_agent.generate_post(processed_inputs)

        return {
            "success": True,
            "post": result["post_text"],
            "hashtags": result["hashtags"],
            "engagement_score": result["engagement_score"],
            "hook_strength": result["hook_strength"],
            "suggestions": result["suggestions"],
            "metadata": {
                "inputs_processed": len(processed_inputs),
                "primary_source": processed_inputs[0]["type"] if processed_inputs else None
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in generate_post: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.post("/api/refine")
async def refine_post(
    post_text: str = Form(...),
    feedback: str = Form(...),
):
    """
    Refine existing post based on conversational feedback

    Args:
        post_text: Current post text
        feedback: User feedback (e.g., "make it punchier", "add a question")

    Returns:
        Refined post with improvements
    """
    try:
        refined_result = await content_agent.refine_post(post_text, feedback)

        return {
            "success": True,
            "refined_post": refined_result["post_text"],
            "changes_made": refined_result["changes"],
            "engagement_score": refined_result["engagement_score"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refinement failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "True") == "True"
    )
