#!/usr/bin/env python3
"""Test MCP search with environment variables from testenvar.1.log"""

import asyncio
import os
import sys

# Set environment variables (use /v1 endpoint for API)
os.environ["GROK_API_URL"] = "https://api.gptacg.top/v1"
os.environ["GROK_API_KEY"] = "sk-DWhtbZw1G7jn1lgeTLgI8wz9P8zPYYTXeqqcNhFtlli8ak5y"
os.environ["GROK_SEARCH_MCP_MODEL"] = "gemini-3-flash-preview"
os.environ["GROK_DEBUG"] = "true"

# Add src to path
sys.path.insert(0, "src")

import httpx
from grok_search.providers.grok import GrokSearchProvider
from grok_search.config import config


async def test_chat_completions():
    """Test the chat completions endpoint directly"""
    print(f"Testing with model: {config.grok_model}")
    print(f"API URL: {config.grok_api_url}")
    print()
    
    headers = {
        "Authorization": f"Bearer {config.grok_api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": config.grok_model,
        "messages": [
            {"role": "user", "content": "What is the Model Context Protocol? Keep it brief."}
        ],
        "stream": False,
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{config.grok_api_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:2000]}")
            
            if response.status_code == 200:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0].get("message", {}).get("content", "")
                    print()
                    print("=" * 50)
                    print("RESPONSE CONTENT:")
                    print("=" * 50)
                    print(content)
                    return True
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
    
    return False


async def test_search():
    """Test the search functionality"""
    print()
    print("=" * 50)
    print("TESTING SEARCH FUNCTIONALITY")
    print("=" * 50)
    
    provider = GrokSearchProvider(config.grok_api_url, config.grok_api_key, config.grok_model)
    
    try:
        result = await provider.search("What is MCP protocol", max_results=2)
        print()
        print("SEARCH RESULT:")
        print("=" * 50)
        print(result if result else "(empty result)")
    except Exception as e:
        print(f"Search error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


async def main():
    print("=" * 50)
    print("MCP Environment Variable Test")
    print("=" * 50)
    print()
    
    # First test basic chat completion
    success = await test_chat_completions()
    
    # Then test search if basic chat works
    if success:
        await test_search()
    else:
        print()
        print("Basic chat completion failed, skipping search test")


if __name__ == "__main__":
    asyncio.run(main())
