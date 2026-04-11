"""
Claude API Service
Handles all interactions with Anthropic's Claude API.
"""
import anthropic
from typing import Dict, List
import os

from utils.exceptions import RateLimitError, ServiceUnavailableError
from utils.logger import get_logger

logger = get_logger(__name__)


class ClaudeService:
    """Service for interacting with Anthropic's Claude API"""

    def __init__(self, api_key: str, model: str = None, client=None):
        """
        Initialize Claude service.

        Args:
            api_key: Anthropic API key
            model: Claude model to use (defaults to CLAUDE_MODEL env var or claude-sonnet-4-5-20251001)
            client: Optional AsyncAnthropic client instance (for testing)
        """
        if not api_key and client is None:
            raise ValueError("ANTHROPIC_API_KEY not provided")

        self.client = client if client is not None else anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model or os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

    async def test_connection(self) -> bool:
        """
        Test Claude API connectivity.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return response.content is not None
        except Exception as e:
            logger.error("Claude API connection test failed: %s", str(e))
            return False

    async def generate_content(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 2000,
        temperature: float = 1.0
    ) -> str:
        """
        Generate content using Claude.

        Args:
            system_prompt: System instructions
            user_message: User input/request
            max_tokens: Maximum tokens in response
            temperature: Creativity level (0.0-1.0)

        Returns:
            Generated text from Claude
        """
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )
            if not response.content:
                return ""
            for block in response.content:
                if block.type == "text":
                    return block.text
            return ""

        except anthropic.RateLimitError as e:
            logger.error("Claude API rate limit exceeded: %s", str(e), exc_info=True)
            raise RateLimitError()

        except (anthropic.APIConnectionError, anthropic.APITimeoutError) as e:
            logger.error("Claude API unavailable: %s", str(e), exc_info=True)
            raise ServiceUnavailableError(f"Claude API unavailable: {str(e)}")

        except Exception as e:
            logger.error("Claude API call failed: %s", str(e), exc_info=True)
            raise Exception(f"Claude API call failed: {str(e)}")

    async def generate_with_conversation(
        self,
        system_prompt: str,
        conversation_history: List[Dict[str, str]],
        max_tokens: int = 2000,
        temperature: float = 1.0
    ) -> str:
        """
        Generate content with conversation history for refinement.

        Args:
            system_prompt: System instructions
            conversation_history: List of {"role": "user"|"assistant", "content": "..."}
            max_tokens: Maximum tokens
            temperature: Creativity level

        Returns:
            Generated text from Claude
        """
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=conversation_history
            )
            if not response.content:
                return ""
            for block in response.content:
                if block.type == "text":
                    return block.text
            return ""

        except anthropic.RateLimitError as e:
            logger.error("Claude API rate limit exceeded: %s", str(e), exc_info=True)
            raise RateLimitError()

        except (anthropic.APIConnectionError, anthropic.APITimeoutError) as e:
            logger.error("Claude API unavailable: %s", str(e), exc_info=True)
            raise ServiceUnavailableError(f"Claude API unavailable: {str(e)}")

        except Exception as e:
            logger.error("Claude conversation API call failed: %s", str(e), exc_info=True)
            raise Exception(f"Claude conversation API call failed: {str(e)}")
