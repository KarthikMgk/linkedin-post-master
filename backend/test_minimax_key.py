"""Quick script to test MiniMax API key validity."""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")
model = os.getenv("MINIMAX_MODEL", "MiniMax-M2.7")
base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.minimax.io/anthropic")

print(
    f"ANTHROPIC_API_KEY: {'SET' if api_key else 'NOT SET'}"
    f"{f' (length={len(api_key)})' if api_key else ''}"
)
print(f"ANTHROPIC_BASE_URL: {base_url}")
print(f"MINIMAX_MODEL: {model}")
print("-" * 50)

if not api_key:
    print("ERROR: No ANTHROPIC_API_KEY found in .env")
    sys.exit(1)

try:
    import anthropic

    # Use no args - SDK reads from env vars
    client = anthropic.Anthropic()
    print("Sending test request via Anthropic SDK (no args)...")
    response = client.messages.create(
        model=model, max_tokens=10, messages=[{"role": "user", "content": "Hi"}]
    )
    print(f"SUCCESS! Response: {response.content[0].text if response.content else '(empty)'}")
except Exception as e:
    print(f"Failed: {type(e).__name__}: {e}")
