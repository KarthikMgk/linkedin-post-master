"""
Content Generation Agent
Handles LinkedIn post generation with engagement optimization
"""
from typing import Dict, List
import json
from services.claude_service import ClaudeService


class ContentGenerationAgent:
    """Agent responsible for generating optimized LinkedIn posts"""

    def __init__(self, claude_service: ClaudeService):
        """
        Initialize content generation agent

        Args:
            claude_service: Claude API service instance
        """
        self.claude = claude_service
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """
        Build comprehensive system prompt for LinkedIn post generation

        Returns:
            System prompt string
        """
        return """You are an expert LinkedIn content strategist and engagement optimization specialist. Your role is to transform raw content into highly engaging LinkedIn posts that drive meaningful interactions.

## Core Principles:

1. **Engagement Engineering**: Every element optimized for maximum engagement
2. **Authentic Voice**: Maintain natural, authentic tone (not generic AI writing)
3. **Pattern Interrupts**: Strong opening lines that stop the scroll
4. **Psychological Hooks**: Leverage curiosity gaps, social proof, controversy, storytelling

## Optimization Techniques:

### Headlines (First Line):
- Use journalism formulas: curiosity gap, surprising statistic, provocative question
- Maximum impact in first 1-2 lines (visible before "see more")
- Examples: "Everyone's wrong about X...", "I spent Y years learning Z. Here's what nobody tells you..."

### Structure:
- Hook → Context → Insight → Value → Call-to-Action
- Short paragraphs (1-3 lines each) for readability
- Use line breaks strategically for visual rhythm

### Engagement Drivers:
- Questions that invite comments
- Relatable personal experiences
- Contrarian takes (respectfully presented)
- Actionable advice
- Numbered lists for structure

### LinkedIn Best Practices:
- Length: 800-1300 characters for balanced engagement
- Hashtags: 3-5 highly specific, relevant hashtags (not generic ones like #LinkedIn, #Content, #Professional)
  - Choose hashtags directly related to the content topic (e.g., #MachineLearning, #ProductManagement, #RemoteWork)
  - Include 1-2 niche/specific hashtags that target your exact audience
  - Include 1-2 broader industry hashtags for reach
  - AVOID: Generic hashtags like #Business, #Success, #Motivation, #Monday, #Inspiration
  - PREFER: Specific hashtags like #DevOps, #UXDesign, #SalesStrategy, #StartupGrowth
- Avoid corporate jargon and buzzwords
- Natural, conversational tone

## Output Format:

Return your response as JSON with the following structure:
{
    "post_text": "The complete LinkedIn post text",
    "hashtags": ["hashtag1", "hashtag2", "hashtag3"],
    "engagement_score": 8.5,
    "hook_strength": "Strong",
    "suggestions": [
        "Specific improvement suggestion 1",
        "Specific improvement suggestion 2"
    ],
    "cta": "Call to action used"
}

## Scoring Criteria:

- **Engagement Score (0-10)**: Overall post effectiveness
  - 9-10: Viral potential, exceptional hook and value
  - 7-8: Strong engagement likely, solid structure
  - 5-6: Decent but room for improvement
  - Below 5: Needs significant optimization

- **Hook Strength**: Weak / Moderate / Strong / Exceptional
  - Exceptional: Impossible to scroll past
  - Strong: Compelling, creates curiosity
  - Moderate: Acceptable but predictable
  - Weak: Generic or uninteresting opening

Now analyze the provided content and generate an optimized LinkedIn post."""

    async def generate_post(self, processed_inputs: List[Dict]) -> Dict:
        """
        Generate optimized LinkedIn post from processed inputs

        Args:
            processed_inputs: List of processed input data

        Returns:
            Generated post with metadata
        """
        # Build user message from processed inputs
        user_message = self._format_inputs_for_generation(processed_inputs)

        # Generate content using Claude
        response = await self.claude.generate_content(
            system_prompt=self.system_prompt,
            user_message=user_message,
            max_tokens=2000,
            temperature=1.0
        )

        # Parse JSON response
        try:
            # Clean response (remove markdown code blocks if present)
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            result = json.loads(cleaned_response)

            # Clean the post text (remove any escaped newlines or extra formatting)
            if "post_text" in result:
                result["post_text"] = result["post_text"].replace("\\n", "\n").strip()

            return result
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Response was: {response[:500]}")
            # Fallback if JSON parsing fails
            return {
                "post_text": response.replace("\\n", "\n").strip(),
                "hashtags": ["LinkedIn", "Content", "Professional"],
                "engagement_score": 7.0,
                "hook_strength": "Moderate",
                "suggestions": ["Could not parse structured output"],
                "cta": "Engage with this post"
            }

    def _format_inputs_for_generation(self, processed_inputs: List[Dict]) -> str:
        """
        Format processed inputs into user message for Claude

        Args:
            processed_inputs: Processed input data

        Returns:
            Formatted user message
        """
        message_parts = ["Generate an optimized LinkedIn post from the following content:\n"]

        # Identify primary content
        primary = [inp for inp in processed_inputs if inp["priority"] == "primary"]
        supporting = [inp for inp in processed_inputs if inp["priority"] == "supporting"]

        if primary:
            message_parts.append("## PRIMARY CONTENT:")
            for inp in primary:
                message_parts.append(f"\n**Source Type:** {inp['type']}")
                message_parts.append(f"**Content:**\n{inp['content']}\n")

        if supporting:
            message_parts.append("\n## SUPPORTING CONTEXT:")
            for inp in supporting:
                message_parts.append(f"\n**Source Type:** {inp['type']}")
                message_parts.append(f"**Content:**\n{inp['content']}\n")

        message_parts.append("\nSynthesize all content above and create a compelling LinkedIn post that drives engagement.")
        message_parts.append("\nIMPORTANT FOR HASHTAGS: Analyze the specific topics, industries, and themes in this content. Generate 3-5 highly relevant, specific hashtags that directly relate to the content's subject matter. Avoid generic hashtags like #Business, #Success, #Content, #Professional, #LinkedIn. Instead, use precise industry/topic hashtags.")

        return "\n".join(message_parts)

    async def refine_post(self, post_text: str, feedback: str) -> Dict:
        """
        Refine existing post based on conversational feedback

        Args:
            post_text: Current post text
            feedback: User feedback for refinement

        Returns:
            Refined post with metadata
        """
        conversation = [
            {
                "role": "user",
                "content": f"Here's my current LinkedIn post:\n\n{post_text}\n\nI want to refine it based on feedback: {feedback}\n\nPlease apply the requested changes and return the improved post in the EXACT same JSON format you used initially, with these fields:\n- post_text: the refined post content\n- hashtags: array of relevant hashtags\n- engagement_score: score from 0-10\n- hook_strength: Weak/Moderate/Strong/Exceptional\n- suggestions: array of further improvement suggestions\n\nReturn ONLY the JSON, no other text."
            }
        ]

        response = await self.claude.generate_with_conversation(
            system_prompt=self.system_prompt,
            conversation_history=conversation,
            max_tokens=2000,
            temperature=1.0
        )

        # Parse JSON response (same cleaning as generate_post)
        try:
            # Clean response (remove markdown code blocks if present)
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            result = json.loads(cleaned_response)

            # Clean the post text (remove any escaped newlines or extra formatting)
            if "post_text" in result:
                result["post_text"] = result["post_text"].replace("\\n", "\n").strip()

            result["changes"] = [feedback]  # Track what was requested
            return result
        except json.JSONDecodeError as e:
            print(f"Refine JSON parsing error: {e}")
            print(f"Response was: {response[:500]}")
            return {
                "post_text": response.replace("\\n", "\n").strip(),
                "hashtags": [],
                "engagement_score": 7.0,
                "hook_strength": "Moderate",
                "suggestions": ["Could not parse structured output"],
                "changes": [feedback]
            }
