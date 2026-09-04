"""
Level 3 building block: a single web_search tool the LLM can decide to call.
Uses Tavily if TAVILY_API_KEY is set, otherwise returns clearly-labeled mock
results so the tool-calling flow can still be demoed end-to-end.
"""
import os

import requests

WEB_SEARCH_TOOL = {
    "name": "web_search",
    "description": (
        "Search the live web for current events, recent news, or any "
        "information that may have changed since the model's training "
        "cutoff. Only call this when the answer truly requires up-to-date "
        "or external information."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to run.",
            }
        },
        "required": ["query"],
    },
}


def web_search(query: str) -> dict:
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return {
            "query": query,
            "mocked": True,
            "results": [
                {
                    "title": f"[Mocked result] Overview relevant to: {query}",
                    "content": (
                        "This is a simulated search result because no "
                        "TAVILY_API_KEY was configured. Set TAVILY_API_KEY "
                        "in your .env file to use real web search."
                    ),
                    "url": "https://example.com/mock-result",
                }
            ],
        }

    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "max_results": 5,
                "search_depth": "basic",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "query": query,
            "mocked": False,
            "results": [
                {
                    "title": r.get("title", ""),
                    "content": r.get("content", ""),
                    "url": r.get("url", ""),
                }
                for r in data.get("results", [])
            ],
        }
    except Exception as exc:
        return {
            "query": query,
            "mocked": True,
            "error": str(exc),
            "results": [],
        }
