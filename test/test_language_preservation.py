"""
Test script to verify that GrokSearch preserves original language content.

This script tests:
1. web_search with Japanese queries returns Japanese content
2. web_fetch with Japanese URLs returns Japanese content
"""

import sys
import asyncio
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from grok_search.providers.grok import GrokSearchProvider
from grok_search.config import config


async def test_search_japanese():
    """Test that web search preserves Japanese content."""
    print("\n" + "="*60)
    print("TEST 1: Web Search with Japanese Query")
    print("="*60)

    try:
        api_url = config.grok_api_url
        api_key = config.grok_api_key
        model = config.grok_model

        print(f"API URL: {api_url}")
        print(f"Model: {model}")

        grok_provider = GrokSearchProvider(api_url, api_key, model)

        # Search for Japanese content
        query = "日本のニュース 2024"  # "Japanese news 2024"
        print(f"\nQuery: {query}")
        print("\nSearching...")

        results = await grok_provider.search(query, platform="", min_results=2, max_results=3)

        print("\nResults:")
        print(results)

        # Check if results contain Japanese characters
        if any(ord(c) > 0x3000 for c in results):
            print("\n✅ PASS: Results contain Japanese characters (preserved original language)")
        else:
            print("\n❌ FAIL: Results do not contain Japanese characters (might have been translated)")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


async def test_fetch_japanese():
    """Test that web fetch preserves Japanese content."""
    print("\n" + "="*60)
    print("TEST 2: Web Fetch with Japanese URL")
    print("="*60)

    try:
        api_url = config.grok_api_url
        api_key = config.grok_api_key
        model = config.grok_model

        grok_provider = GrokSearchProvider(api_url, api_key, model)

        # Fetch a Japanese website
        url = "https://www.yahoo.co.jp"  # Yahoo Japan
        print(f"\nURL: {url}")
        print("\nFetching...")

        content = await grok_provider.fetch(url)

        print("\nContent preview (first 500 chars):")
        print(content[:500])

        # Check if content contains Japanese characters
        if any(ord(c) > 0x3000 for c in content):
            print("\n✅ PASS: Content contains Japanese characters (preserved original language)")
        else:
            print("\n❌ FAIL: Content does not contain Japanese characters (might have been translated)")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


async def test_search_chinese():
    """Test that web search preserves Chinese content."""
    print("\n" + "="*60)
    print("TEST 3: Web Search with Chinese Query")
    print("="*60)

    try:
        api_url = config.grok_api_url
        api_key = config.grok_api_key
        model = config.grok_model

        grok_provider = GrokSearchProvider(api_url, api_key, model)

        # Search for Chinese content
        query = "中国新闻 2024"  # "Chinese news 2024"
        print(f"\nQuery: {query}")
        print("\nSearching...")

        results = await grok_provider.search(query, platform="", min_results=2, max_results=3)

        print("\nResults:")
        print(results)

        # Check if results contain Chinese characters
        if any(0x4E00 <= ord(c) <= 0x9FFF for c in results):
            print("\n✅ PASS: Results contain Chinese characters (preserved original language)")
        else:
            print("\n❌ FAIL: Results do not contain Chinese characters (might have been translated)")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("GROK SEARCH - LANGUAGE PRESERVATION TESTS")
    print("="*60)

    try:
        # Check configuration
        print(f"\nConfiguration:")
        print(f"  API URL: {config.grok_api_url}")
        print(f"  API Key: {config.grok_api_key[:8]}...{config.grok_api_key[-4:]}")
        print(f"  Model: {config.grok_model}")
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease set the following environment variables:")
        print("  - GROK_API_URL")
        print("  - GROK_API_KEY")
        return

    # Run tests
    await test_search_japanese()
    await test_fetch_japanese()
    await test_search_chinese()

    print("\n" + "="*60)
    print("TESTS COMPLETED")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
