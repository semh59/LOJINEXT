import asyncio
import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from groq import AsyncGroq
from app.config import settings


async def test_groq():
    print("--- Groq API Diagnostic ---")
    api_key = (
        settings.GROQ_API_KEY.get_secret_value() if settings.GROQ_API_KEY else None
    )
    model_name = settings.GROQ_MODEL_NAME

    if not api_key:
        print("ERROR: GROQ_API_KEY is not set in settings.")
        return

    client = AsyncGroq(api_key=api_key)
    print(f"Testing model: {model_name}")

    # Test 1: Simple completion with current parameters
    print("\nTest 1: Standard call with reasoning_effort...")
    try:
        completion = await client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "Merhaba, nasılsın?"}],
            max_completion_tokens=100,
            reasoning_effort="medium",
        )
        print(f"SUCCESS (Test 1): {completion.choices[0].message.content[:50]}...")
    except Exception as e:
        print(f"FAILED (Test 1): {e}")

    # Test 2: Without reasoning_effort
    print("\nTest 2: Call without reasoning_effort...")
    try:
        completion = await client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "Merhaba, nasılsın?"}],
            max_completion_tokens=100,
        )
        print(f"SUCCESS (Test 2): {completion.choices[0].message.content[:50]}...")
    except Exception as e:
        print(f"FAILED (Test 2): {e}")

    # Test 3: Using max_tokens instead of max_completion_tokens
    print("\nTest 3: Using max_tokens instead of max_completion_tokens...")
    try:
        completion = await client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "Merhaba, nasılsın?"}],
            max_tokens=100,
        )
        print(f"SUCCESS (Test 3): {completion.choices[0].message.content[:50]}...")
    except Exception as e:
        print(f"FAILED (Test 3): {e}")


if __name__ == "__main__":
    asyncio.run(test_groq())
