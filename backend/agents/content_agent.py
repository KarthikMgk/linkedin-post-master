"""
Content Generation Agent
Handles LinkedIn post generation with engagement optimization
"""
from typing import Dict, List, Optional
import uuid
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
    "cta": "Call to action used",
    "image_alt_text": "Brief description of an ideal complementary image (1-2 sentences)"
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

    def _build_variant_system_prompt(self) -> str:
        """
        Build system prompt for multi-variant generation.
        Generates 3 distinct personalities: Bold, Structured, Provocative.

        Returns:
            System prompt for variant generation
        """
        return """You are an expert LinkedIn content strategist specializing in multi-variant content generation. Your task is to create THREE distinct versions of a LinkedIn post from the same source content, each with a unique personality and approach.

## VARIANT PERSONALITIES:

### 1. BOLD Approach
- **Voice:** Confident, opinionated, challenges conventional wisdom
- **Opening:** Lead with a strong opinion or provocative challenge
- **Structure:** Direct, no hedging, powerful statements
- **Example opening:** "Everyone is wrong about X...", "Here's the uncomfortable truth about Y..."

### 2. STRUCTURED Approach
- **Voice:** Professional, methodical, credibility-focused
- **Opening:** Clear value proposition or numbered insight
- **Structure:** Use numbered lists (1, 2, 3), clear sections, scannable format
- **Example opening:** "3 lessons from X...", "Here's what the data shows about Y..."

### 3. PROVOCATIVE Approach
- **Voice:** Surprising, contrarian, disrupts expectations
- **Opening:** Start with a counter-intuitive or shocking statement
- **Structure:** Build tension, reveal contradiction, then pivot to insight
- **Example opening:** "What if X is actually wrong?", "The opposite of what everyone believes about Y..."

## OUTPUT REQUIREMENTS:

Return your response as JSON with the following structure containing ALL THREE variants:
{
    "variants": [
        {
            "id": "unique-id-1",
            "personality": "bold",
            "label": "Bold Approach",
            "post": "The complete LinkedIn post text",
            "hashtags": ["hashtag1", "hashtag2", "hashtag3"],
            "engagement_score": 8.5,
            "hook_strength": "Strong",
            "suggestions": ["Specific improvement suggestion 1", "Specific improvement suggestion 2"],
            "cta": "Call to action used"
        },
        {
            "id": "unique-id-2",
            "personality": "structured",
            "label": "Structured Approach",
            "post": "...",
            "hashtags": ["hashtag1", "hashtag2", "hashtag3"],
            "engagement_score": 8.2,
            "hook_strength": "Strong",
            "suggestions": ["..."],
            "cta": "..."
        },
        {
            "id": "unique-id-3",
            "personality": "provocative",
            "label": "Provocative Approach",
            "post": "...",
            "hashtags": ["hashtag1", "hashtag2", "hashtag3"],
            "engagement_score": 8.8,
            "hook_strength": "Exceptional",
            "suggestions": ["..."],
            "cta": "..."
        }
    ]
}

## SCORING CRITERIA (per variant):

- **Engagement Score (0-10)**: Overall post effectiveness for that personality
- **Hook Strength**: Weak / Moderate / Strong / Exceptional
- Each variant should score HIGH for its specific personality (a Bold post that resonates with bold readers scores higher than a safe, vanilla post)

## GUIDELINES:

1. Each variant must be GENUINELY DIFFERENT — not just word reordering
2. Bold should feel Bold (confident, opinionated) — not just enthusiastic
3. Structured should use clear numbering or section headers
4. Provocative should challenge assumptions — not just be controversial for shock value
5. Keep all variants under 3000 characters (LinkedIn limit)
6. Each variant gets 3-5 specific, relevant hashtags

Now generate all three variants from the provided content."""

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
                "cta": "Engage with this post",
                "image_alt_text": ""
            }

    async def generate_variants(self, processed_inputs: List[Dict]) -> List[Dict]:
        """
        Generate 3 distinct post variants in a single API call.

        Args:
            processed_inputs: List of processed input data

        Returns:
            List of 3 variant dictionaries with id, personality, label, post, etc.
        """
        # Build user message from processed inputs
        user_message = self._format_inputs_for_generation(processed_inputs)

        # Generate all 3 variants in a single call for speed (30s SLA)
        response = await self.claude.generate_content(
            system_prompt=self._build_variant_system_prompt(),
            user_message=user_message,
            max_tokens=4000,
            temperature=1.0
        )

        # Parse JSON response
        try:
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            result = json.loads(cleaned_response)
            variants = result.get("variants", [])

            # Add unique IDs if not present
            for variant in variants:
                if "id" not in variant:
                    variant["id"] = str(uuid.uuid4())[:8]
                # Normalize personality field
                if "personality" not in variant:
                    variant["personality"] = "unknown"
                # Normalize label
                if "label" not in variant:
                    personality = variant.get("personality", "unknown")
                    variant["label"] = f"{personality.capitalize()} Approach"
                # Clean post text
                if "post" in variant:
                    variant["post"] = variant["post"].replace("\\n", "\n").strip()
                elif "post_text" in variant:
                    variant["post"] = variant["post_text"].replace("\\n", "\n").strip()
                    del variant["post_text"]

            # Ensure we have exactly 3 variants
            if len(variants) != 3:
                print(f"Warning: Expected 3 variants, got {len(variants)}")

            return variants[:3]  # Return max 3

        except json.JSONDecodeError as e:
            print(f"Variant JSON parsing error: {e}")
            print(f"Response was: {response[:500]}")
            # Return fallback variants
            return self._fallback_variants(response)

    def _fallback_variants(self, raw_response: str) -> List[Dict]:
        """Generate fallback variants when JSON parsing fails."""
        personalities = [
            {"personality": "bold", "label": "Bold Approach"},
            {"personality": "structured", "label": "Structured Approach"},
            {"personality": "provocative", "label": "Provocative Approach"},
        ]
        variants = []
        for i, p in enumerate(personalities):
            variants.append({
                "id": str(uuid.uuid4())[:8],
                "personality": p["personality"],
                "label": p["label"],
                "post": raw_response.replace("\\n", "\n").strip()[:2000],
                "hashtags": ["LinkedIn", "Content", "Professional"],
                "engagement_score": 7.0,
                "hook_strength": "Moderate",
                "suggestions": ["Could not parse structured output"],
                "cta": "Engage with this post"
            })
        return variants

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

    async def refine_variant(
        self,
        post_text: str,
        feedback: str,
        personality: Optional[str] = None,
        label: Optional[str] = None
    ) -> Dict:
        """
        Refine a specific variant while preserving its personality.

        Args:
            post_text: Current post text
            feedback: User feedback for refinement
            personality: The variant personality (bold, structured, provocative)
            label: The variant label

        Returns:
            Refined post with metadata, preserving personality + label
        """
        # Build personality context to preserve in refinement
        personality_context = ""
        if personality:
            personality_context = self._get_personality_context(personality)

        conversation = [
            {
                "role": "user",
                "content": f"""Here's my current LinkedIn post ({personality or 'default'} style):

{post_text}

I want to refine it based on feedback: {feedback}

{personality_context}

Please apply the requested changes while maintaining the {personality or 'original'} personality and style. Return the improved post in JSON format:
- post_text: the refined post content
- hashtags: array of relevant hashtags
- engagement_score: score from 0-10
- hook_strength: Weak/Moderate/Strong/Exceptional
- suggestions: array of further improvement suggestions

Return ONLY the JSON, no other text."""
            }
        ]

        response = await self.claude.generate_with_conversation(
            system_prompt=self.system_prompt,
            conversation_history=conversation,
            max_tokens=2000,
            temperature=1.0
        )

        # Parse JSON response
        try:
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            result = json.loads(cleaned_response)

            if "post_text" in result:
                result["post_text"] = result["post_text"].replace("\\n", "\n").strip()

            result["changes"] = [feedback]
            # Preserve personality and label
            result["personality"] = personality or "unknown"
            result["label"] = label or f"{(personality or 'Default').capitalize()} Approach"

            return result
        except json.JSONDecodeError as e:
            print(f"Refine variant JSON parsing error: {e}")
            return {
                "post_text": response.replace("\\n", "\n").strip(),
                "hashtags": [],
                "engagement_score": 7.0,
                "hook_strength": "Moderate",
                "suggestions": ["Could not parse structured output"],
                "changes": [feedback],
                "personality": personality or "unknown",
                "label": label or "Approach"
            }

    def _get_personality_context(self, personality: str) -> str:
        """Get the personality-specific context for refinement."""
        contexts = {
            "bold": """
## BOLD Personality Requirements:
- Maintain the confident, opinionated voice
- Keep strong statements and direct challenges
- Don't hedge or soften the message
- Preserve the bold opening approach""",
            "structured": """
## STRUCTURED Personality Requirements:
- Maintain clear structure with numbered lists or sections
- Keep professional, methodical tone
- Preserve the organized formatting
- Keep the credibility-focused approach""",
            "provocative": """
## PROVOCATIVE Personality Requirements:
- Maintain the surprising, contrarian angle
- Keep the element of surprise or disruption
- Preserve the tension-and-reveal structure
- Don't make it too comfortable or safe"""
        }
        return contexts.get(personality, "")
