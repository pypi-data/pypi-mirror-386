"""Brave Search integration for Kagura AI."""

from __future__ import annotations

import json
import logging
from typing import Literal

from kagura import tool
from kagura.config.env import (
    get_brave_search_api_key,
    get_search_cache_enabled,
    get_search_cache_ttl,
)
from kagura.mcp.builtin.cache import SearchCache

# Setup logger
logger = logging.getLogger(__name__)

# Global search cache instance
_search_cache: SearchCache | None = None


def _get_cache() -> SearchCache | None:
    """Get or create search cache instance based on environment config

    Returns:
        SearchCache instance if caching is enabled, None otherwise
    """
    global _search_cache

    if not get_search_cache_enabled():
        return None

    if _search_cache is None:
        _search_cache = SearchCache(
            default_ttl=get_search_cache_ttl(),
            max_size=1000,
        )

    return _search_cache


@tool
async def brave_web_search(query: str, count: int = 5) -> str:
    """Search the web using Brave Search API.

    Use this tool when:
    - User asks for current/latest/recent information
    - Information may have changed since knowledge cutoff
    - Real-time data is needed (news, prices, events)
    - Verification of facts is requested
    - User explicitly asks to "search" or "look up" something

    Do NOT use for:
    - General knowledge questions answerable from training data
    - Historical facts that don't change
    - Stable information (definitions, concepts)
    - Mathematical calculations
    - Code generation or debugging

    Automatically handles all languages. Returns formatted text results.
    Results are cached (if enabled) to reduce API calls and improve response times.

    Args:
        query: Search query in any language. Keep it concise (1-6 words recommended)
        count: Number of results to return (default: 5, max: 20)

    Returns:
        Formatted text with search results

    Example:
        # Latest information
        query="Python 3.13 release date", count=3

        # Event search (any language)
        query="熊本 イベント 今週", count=5

        # Price check
        query="Bitcoin price", count=3

    Note:
        Caching can be controlled via environment variables:
        - ENABLE_SEARCH_CACHE: Enable/disable caching (default: true)
        - SEARCH_CACHE_TTL: Cache TTL in seconds (default: 3600)
    """
    # Ensure count is int (LLM might pass as string)
    if isinstance(count, str):
        try:
            count = int(count)
        except ValueError:
            count = 5  # Default fallback

    # Check cache first (if enabled)
    cache = _get_cache()
    if cache:
        logger.debug(f"Cache enabled, checking for query: '{query}' (count={count})")
        cached_result = await cache.get(query, count)
        if cached_result:
            # Cache hit - return instantly
            logger.info(f"Cache HIT for query: '{query}' (count={count})")
            try:
                from rich.console import Console

                console = Console()
                console.print("[green]✓ Cache hit (instant) - No API call needed[/]")
            except ImportError:
                pass

            # Add cache indicator for debugging/transparency
            return f"[CACHED SEARCH RESULT - Retrieved instantly]\n\n{cached_result}"
        else:
            logger.info(f"Cache MISS for query: '{query}' (count={count})")

    # Cache miss or disabled - proceed with API call
    # Use fixed params (US, en) - API auto-detects query language
    country = "US"
    search_lang = "en"
    try:
        from brave_search_python_client import (  # type: ignore[import-untyped]
            BraveSearch,
            WebSearchRequest,
        )
    except ImportError:
        return json.dumps(
            {
                "error": "brave-search-python-client is required",
                "install": "uv add brave-search-python-client",
            },
            indent=2,
        )

    # Check API key
    api_key = get_brave_search_api_key()
    if not api_key:
        return json.dumps(
            {
                "error": "BRAVE_SEARCH_API_KEY environment variable not set",
                "help": "Get API key from https://brave.com/search/api/",
            },
            indent=2,
        )

    try:
        # Create client
        client = BraveSearch(api_key=api_key)

        # Create search request
        request = WebSearchRequest(  # type: ignore[call-arg,arg-type]
            q=query,
            count=min(count, 20),
            country=country,  # type: ignore[arg-type]
            search_lang=search_lang,
        )

        # Execute search
        response = await client.web(request)  # type: ignore[arg-type]

        # Extract results
        results = []
        if hasattr(response, "web") and hasattr(response.web, "results"):
            for item in response.web.results[:count]:  # type: ignore[union-attr]
                results.append(
                    {
                        "title": getattr(item, "title", ""),
                        "url": getattr(item, "url", ""),
                        "description": getattr(item, "description", ""),
                    }
                )

        # Format as readable text instead of JSON
        if not results:
            return f"No results found for: {query}"

        formatted = [f"Search results for: {query}\n"]
        for i, result in enumerate(results, 1):
            formatted.append(f"{i}. {result['title']}")
            formatted.append(f"   {result['url']}")
            formatted.append(f"   {result['description']}\n")

        # Add instruction to LLM
        formatted.append("---")
        formatted.append(
            "IMPORTANT: These are the web search results. "
            "Use this information to answer the user's question. "
            "Do NOT perform additional searches unless the user explicitly "
            "asks for more or different information."
        )

        result = "\n".join(formatted)

        # Store in cache (if enabled)
        if cache:
            logger.info(f"Caching search result for query: '{query}' (count={count})")
            await cache.set(query, result, count)
            logger.debug(f"Cache stats: {cache.stats()}")

        return result

    except Exception as e:
        error_msg = f"Search failed: {str(e)}"
        logger.error(f"Search error for query '{query}': {str(e)}")
        # Don't cache errors
        return error_msg


@tool
async def brave_news_search(
    query: str,
    count: int = 5,
    country: str = "US",
    search_lang: str = "en",
    freshness: Literal["pd", "pw", "pm", "py"] | None = None,
) -> str:
    """Search recent news articles using Brave Search API.

    Use this tool specifically for:
    - Breaking news and current events
    - Recent developments in specific topics
    - Time-sensitive information from news sources
    - User explicitly asks for "news" or "latest news"

    Supports filtering by:
    - Country (US, JP, UK, etc.)
    - Language (en, ja, etc.)
    - Freshness (last 24h, week, month, year)

    Args:
        query: Search query for news articles
        count: Number of results (default: 5, max: 20)
        country: Country code (default: "US", "JP" for Japan, "GB" for UK)
        search_lang: Search language (default: "en", "ja" for Japanese)
        freshness: Time filter:
            - "pd" (past day / 24 hours)
            - "pw" (past week)
            - "pm" (past month)
            - "py" (past year)
            - None (all time)

    Returns:
        JSON string with news results including title, URL, description, and age

    Example:
        # Breaking news (last 24 hours)
        query="AI regulation", freshness="pd", count=5

        # Weekly tech news
        query="tech industry", freshness="pw", country="US"

        # Japanese news
        query="東京オリンピック", country="JP", search_lang="ja"
    """
    # Ensure count is int (LLM might pass as string)
    if isinstance(count, str):
        try:
            count = int(count)
        except ValueError:
            count = 5  # Default fallback

    try:
        from brave_search_python_client import (  # type: ignore[import-untyped]
            BraveSearch,
            NewsSearchRequest,
        )
    except ImportError:
        return json.dumps(
            {
                "error": "brave-search-python-client is required",
                "install": "uv add brave-search-python-client",
            },
            indent=2,
        )

    # Check API key
    api_key = get_brave_search_api_key()
    if not api_key:
        return json.dumps(
            {
                "error": "BRAVE_SEARCH_API_KEY environment variable not set",
                "help": "Get API key from https://brave.com/search/api/",
            },
            indent=2,
        )

    try:
        # Create client
        client = BraveSearch(api_key=api_key)

        # Create search request
        kwargs = {
            "q": query,
            "count": min(count, 20),
            "country": country,
            "search_lang": search_lang,
        }
        if freshness:
            kwargs["freshness"] = freshness

        request = NewsSearchRequest(**kwargs)  # type: ignore[arg-type]

        # Execute search
        response = await client.news(request)

        # Extract results
        results = []
        if hasattr(response, "results"):
            for item in response.results[:count]:
                results.append(
                    {
                        "title": str(getattr(item, "title", "")),
                        "url": str(getattr(item, "url", "")),  # Convert HttpUrl to str
                        "description": str(getattr(item, "description", "")),
                        "age": str(getattr(item, "age", "")),
                    }
                )

        return json.dumps(results, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": f"News search failed: {str(e)}"}, indent=2)
