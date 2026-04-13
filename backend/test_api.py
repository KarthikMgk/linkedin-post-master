"""
Simple test script to verify API setup
Run this after setting up backend to test Claude API integration
"""

import asyncio
import os

from dotenv import load_dotenv

from services.claude_service import ClaudeService

# Load environment variables
load_dotenv()


async def test_claude_connection():
    """Test Claude API connection"""
    print("=" * 50)
    print("Testing Claude API Connection...")
    print("=" * 50)

    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY not found in .env file")
        print("\nPlease:")
        print("1. Copy .env.example to .env")
        print("2. Add your API key to .env file")
        return False

    if api_key == "your_api_key_here":
        print("❌ ERROR: Please replace placeholder API key with real key")
        return False

    try:
        claude = ClaudeService(api_key=api_key)
        print("\n✅ Claude service initialized successfully")

        print("\n🔄 Testing API connection...")
        connected = await claude.test_connection()

        if connected:
            print("✅ Claude API connection successful!")

            print("\n🔄 Testing content generation...")
            response = await claude.generate_content(
                system_prompt="You are a helpful assistant.",
                user_message="Say 'Hello, LinkedIn Post Generator is ready!' in a friendly way.",
                max_tokens=100,
            )

            print("\n📝 Test Response:")
            print(response)
            print("\n" + "=" * 50)
            print("✅ All tests passed! Your setup is ready.")
            print("=" * 50)
            return True
        else:
            print("❌ Claude API connection failed")
            print("Please check your API key and internet connection")
            return False

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nTroubleshooting:")
        print("- Check your API key is correct")
        print("- Verify you have internet connection")
        print("- Ensure your Anthropic account has API access")
        return False


if __name__ == "__main__":
    print("\nLinkedIn Post Generator - API Test\n")
    result = asyncio.run(test_claude_connection())

    if result:
        print("\n✅ Ready to start the server!")
        print("\nRun: python main.py")
    else:
        print("\n❌ Setup incomplete. Fix the errors above and try again.")
