"""Инструмент для поиска через Tavily API."""
import os
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def tavily_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Выполняет поиск через Tavily API.
    Возвращает список словарей с ключами:
    - title
    - url
    - snippet
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        logger.error("TAVILY_API_KEY not set in environment")
        return []

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        response = client.search(query, max_results=max_results)

        results = []
        for r in response.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": (r.get("content", "") or "")[:500],
            })
        return results

    except ImportError:
        logger.exception("Tavily library not installed. Run: pip install tavily-python")
        return []
    except Exception as e:
        logger.exception(f"Tavily search error: {e}")
        return []


class TavilyTool:
    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")

    def search(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        return tavily_search(query, max_results)