"""
Claude API Service
Handles all interactions with Anthropic's Claude API
"""
import anthropic
from typing import Dict, List, Optional


class ClaudeService:
    """Service for interacting with Claude API"""

    def __init__(self, api_key: str):
        """
        Initialize Claude service

        Args:
            api_key: Anthropic API key
        """
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not provided")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-5-20250929"  # Latest Sonnet model

    async def test_connection(self) -> bool:
        """
        Test Claude API connectivity

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Simple test message
            response = self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return response.content is not None
        except Exception as e:
            print(f"Claude API connection test failed: {e}")
            return False

    async def generate_content(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 2000,
        temperature: float = 1.0
    ) -> str:
        """
        Generate content using Claude

        Args:
            system_prompt: System instructions for Claude
            user_message: User input/request
            max_tokens: Maximum tokens in response
            temperature: Creativity level (0.0-1.0)

        Returns:
            Generated text from Claude
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )

            # Extract text from response
            return response.content[0].text if response.content else ""

        except Exception as e:
            raise Exception(f"Claude API call failed: {str(e)}")

    async def generate_with_conversation(
        self,
        system_prompt: str,
        conversation_history: List[Dict[str, str]],
        max_tokens: int = 2000,
        temperature: float = 1.0
    ) -> str:
        """
        Generate content with conversation history for refinement

        Args:
            system_prompt: System instructions
            conversation_history: List of {"role": "user"|"assistant", "content": "..."}
            max_tokens: Maximum tokens
            temperature: Creativity level

        Returns:
            Generated text from Claude
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=conversation_history
            )

            return response.content[0].text if response.content else ""

        except Exception as e:
            raise Exception(f"Claude conversation API call failed: {str(e)}")
