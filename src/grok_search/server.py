import sys
from pathlib import Path

# Support direct execution: add src directory to Python path
src_dir = Path(__file__).parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from fastmcp import FastMCP, Context

# Try using absolute imports (supports mcp run)
try:
    from grok_search.providers.grok import GrokSearchProvider
    from grok_search.utils import format_search_results
    from grok_search.logger import log_info
    from grok_search.config import config
except ImportError:
    # Fallback to relative imports (after pip install -e .)
    from .providers.grok import GrokSearchProvider
    from .utils import format_search_results
    from .logger import log_info
    from .config import config

import asyncio

mcp = FastMCP("grok-search")

@mcp.tool(
    name="web_search",
    description="""
    Performs a third-party web search based on the given query and returns the results
    as a JSON string.

    The `query` should be a clear, self-contained natural-language search query.
    When helpful, include constraints such as topic, time range, language, or domain.

    The `platform` should be the platforms which you should focus on searching, such as "Twitter", "GitHub", "Reddit", etc.

    The `min_results` and `max_results` should be the minimum and maximum number of results to return.

    Returns
    -------
    str
        A JSON-encoded string representing a list of search results. Each result
        includes at least:
        - `url`: the link to the result
        - `title`: a short title
        - `summary`: a brief description or snippet of the page content.
    """
)
async def web_search(query: str, platform: str = "", min_results: int = 3, max_results: int = 10, ctx: Context = None) -> str:
    try:
        api_url = config.grok_api_url
        api_key = config.grok_api_key
        model = config.grok_model
    except ValueError as e:
        error_msg = str(e)
        if ctx:
            await ctx.report_progress(error_msg)
        return f"Configuration error: {error_msg}"

    grok_provider = GrokSearchProvider(api_url, api_key, model)

    await log_info(ctx, f"Begin Search: {query}", config.debug_enabled)
    results = await grok_provider.search(query, platform, min_results, max_results, ctx)
    await log_info(ctx, "Search Finished!", config.debug_enabled)
    return results


@mcp.tool(
    name="web_fetch",
    description="""
    Fetches and extracts the complete content from a specified URL and returns it
    as a structured Markdown document.
    The `url` should be a valid HTTP/HTTPS web address pointing to the target page.
    Ensure the URL is complete and accessible (not behind authentication or paywalls).
    The function will:
    - Retrieve the full HTML content from the URL
    - Parse and extract all meaningful content (text, images, links, tables, code blocks)
    - Convert the HTML structure to well-formatted Markdown
    - Preserve the original content hierarchy and formatting
    - Remove scripts, styles, and other non-content elements
    Returns
    -------
    str
        A Markdown-formatted string containing:
        - Metadata header (source URL, title, fetch timestamp)
        - Table of Contents (if applicable)
        - Complete page content with preserved structure
        - All text, links, images, tables, and code blocks from the original page
        
        The output maintains 100% content fidelity with the source page and is
        ready for documentation, analysis, or further processing.
    Notes
    -----
    - Does NOT summarize or modify content - returns complete original text
    - Handles special characters, encoding (UTF-8), and nested structures
    - May not capture dynamically loaded content requiring JavaScript execution
    - Respects the original language without translation
    """
)
async def web_fetch(url: str, ctx: Context = None) -> str:
    try:
        api_url = config.grok_api_url
        api_key = config.grok_api_key
        model = config.grok_model
    except ValueError as e:
        error_msg = str(e)
        if ctx:
            await ctx.report_progress(error_msg)
        return f"Configuration error: {error_msg}"
    await log_info(ctx, f"Begin Fetch: {url}", config.debug_enabled)
    grok_provider = GrokSearchProvider(api_url, api_key, model)
    results = await grok_provider.fetch(url, ctx)
    await log_info(ctx, "Fetch Finished!", config.debug_enabled)
    return results


@mcp.tool(
    name="get_config_info",
    description="""
    Returns the current Grok Search MCP server configuration information and tests the connection.

    This tool is useful for:
    - Verifying that environment variables are correctly configured
    - Testing API connectivity by sending a request to /models endpoint
    - Debugging configuration issues
    - Checking the current API endpoint and settings

    Returns
    -------
    str
        A JSON-encoded string containing configuration details:
        - `api_url`: The configured Grok API endpoint
        - `api_key`: The API key (masked for security, showing only first and last 4 characters)
        - `model`: The currently selected model for search and fetch operations
        - `debug_enabled`: Whether debug mode is enabled
        - `log_level`: Current logging level
        - `log_dir`: Directory where logs are stored
        - `config_status`: Overall configuration status (✅ complete or ❌ error)
        - `connection_test`: Result of testing API connectivity to /models endpoint
          - `status`: Connection status
          - `message`: Status message with model count
          - `response_time_ms`: API response time in milliseconds
          - `available_models`: List of available model IDs (only present on successful connection)

    Notes
    -----
    - API keys are automatically masked for security
    - This tool does not require any parameters
    - Useful for troubleshooting before making actual search requests
    - Automatically tests API connectivity during execution
    """
)
async def get_config_info() -> str:
    import json
    import httpx

    config_info = config.get_config_info()

    # Add connection test
    test_result = {
        "status": "Not tested",
        "message": "",
        "response_time_ms": 0
    }

    try:
        api_url = config.grok_api_url
        api_key = config.grok_api_key

        # Build /models endpoint URL
        models_url = f"{api_url.rstrip('/')}/models"

        # Send test request
        import time
        start_time = time.time()

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                models_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
            )

            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds

            if response.status_code == 200:
                test_result["status"] = "✅ Connection successful"
                test_result["message"] = f"Successfully retrieved model list (HTTP {response.status_code})"
                test_result["response_time_ms"] = round(response_time, 2)

                # Try to parse returned model list
                try:
                    models_data = response.json()
                    if "data" in models_data and isinstance(models_data["data"], list):
                        model_count = len(models_data["data"])
                        test_result["message"] += f", total {model_count} models"

                        # Extract all model IDs/names
                        model_names = []
                        for model in models_data["data"]:
                            if isinstance(model, dict) and "id" in model:
                                model_names.append(model["id"])

                        if model_names:
                            test_result["available_models"] = model_names
                except:
                    pass
            else:
                test_result["status"] = "⚠️ Connection abnormal"
                test_result["message"] = f"HTTP {response.status_code}: {response.text[:100]}"
                test_result["response_time_ms"] = round(response_time, 2)

    except httpx.TimeoutException:
        test_result["status"] = "❌ Connection timeout"
        test_result["message"] = "Request timeout (10 seconds), please check network connection or API URL"
    except httpx.RequestError as e:
        test_result["status"] = "❌ Connection failed"
        test_result["message"] = f"Network error: {str(e)}"
    except ValueError as e:
        test_result["status"] = "❌ Configuration error"
        test_result["message"] = str(e)
    except Exception as e:
        test_result["status"] = "❌ Test failed"
        test_result["message"] = f"Unknown error: {str(e)}"

    config_info["connection_test"] = test_result

    return json.dumps(config_info, ensure_ascii=False, indent=2)


@mcp.tool(
    name="switch_model",
    description="""
    Switches the default Grok model used for search and fetch operations, and persists the setting.

    This tool is useful for:
    - Changing the AI model used for web search and content fetching
    - Testing different models for performance or quality comparison
    - Persisting model preference across sessions

    Parameters
    ----------
    model : str
        The model ID to switch to (e.g., "grok-4-fast", "grok-2-latest", "grok-vision-beta")

    Returns
    -------
    str
        A JSON-encoded string containing:
        - `status`: Success or error status
        - `previous_model`: The model that was being used before
        - `current_model`: The newly selected model
        - `message`: Status message
        - `config_file`: Path where the model preference is saved

    Notes
    -----
    - The model setting is persisted to ~/.config/grok-search/config.json
    - This setting will be used for all future search and fetch operations
    - You can verify available models using the get_config_info tool
    """
)
async def switch_model(model: str) -> str:
    import json

    try:
        previous_model = config.grok_model
        config.set_model(model)
        current_model = config.grok_model

        result = {
            "status": "✅ Success",
            "previous_model": previous_model,
            "current_model": current_model,
            "message": f"Model switched from {previous_model} to {current_model}",
            "config_file": str(config.config_file)
        }

        return json.dumps(result, ensure_ascii=False, indent=2)

    except ValueError as e:
        result = {
            "status": "❌ Failed",
            "message": f"Failed to switch model: {str(e)}"
        }
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        result = {
            "status": "❌ Failed",
            "message": f"Unknown error: {str(e)}"
        }
        return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(
    name="toggle_builtin_tools",
    description="""
    Toggle Claude Code's built-in WebSearch and WebFetch tools on/off.

    Parameters: action - "on" (block built-in), "off" (allow built-in), "status" (check)
    Returns: JSON with current status and deny list
    """
)
async def toggle_builtin_tools(action: str = "status") -> str:
    import json

    # Locate project root
    root = Path.cwd()
    while root != root.parent and not (root / ".git").exists():
        root = root.parent

    settings_path = root / ".claude" / "settings.json"
    tools = ["WebFetch", "WebSearch"]

    # Load or initialize
    if settings_path.exists():
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
    else:
        settings = {"permissions": {"deny": []}}

    deny = settings.setdefault("permissions", {}).setdefault("deny", [])
    blocked = all(t in deny for t in tools)

    # Execute action
    if action in ["on", "enable"]:
        for t in tools:
            if t not in deny:
                deny.append(t)
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        msg = "Built-in tools disabled"
        blocked = True
    elif action in ["off", "disable"]:
        deny[:] = [t for t in deny if t not in tools]
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        msg = "Built-in tools enabled"
        blocked = False
    else:
        msg = f"Built-in tools currently {'disabled' if blocked else 'enabled'}"

    return json.dumps({
        "blocked": blocked,
        "deny_list": deny,
        "file": str(settings_path),
        "message": msg
    }, ensure_ascii=False, indent=2)


def main():
    import signal
    import os
    import threading

    # Signal handling (main thread only)
    if threading.current_thread() is threading.main_thread():
        def handle_shutdown(signum, frame):
            os._exit(0)
        signal.signal(signal.SIGINT, handle_shutdown)
        if sys.platform != 'win32':
            signal.signal(signal.SIGTERM, handle_shutdown)

    # Windows parent process monitoring
    if sys.platform == 'win32':
        import time
        import ctypes
        parent_pid = os.getppid()

        def is_parent_alive(pid):
            """Check if process is alive on Windows"""
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            STILL_ACTIVE = 259
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if not handle:
                return False
            exit_code = ctypes.c_ulong()
            result = kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
            kernel32.CloseHandle(handle)
            return result and exit_code.value == STILL_ACTIVE

        def monitor_parent():
            while True:
                if not is_parent_alive(parent_pid):
                    os._exit(0)
                time.sleep(2)

        threading.Thread(target=monitor_parent, daemon=True).start()

    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        pass
    finally:
        os._exit(0)


if __name__ == "__main__":
    main()
