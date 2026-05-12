"""Реестр инструментов, доступных агентам."""
from typing import Dict, Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}

    def register(self, name: str, func: Callable):
        self._tools[name] = func
        logger.info(f"Tool registered: {name}")

    def call(self, name: str, **kwargs) -> Optional[Any]:
        if name not in self._tools:
            logger.error(f"Tool '{name}' not found")
            return None
        try:
            return self._tools[name](**kwargs)
        except Exception as e:
            logger.error(f"Tool '{name}' failed: {e}")
            return None

    def list_tools(self) -> list:
        return list(self._tools.keys())

# Глобальный экземпляр
registry = ToolRegistry()

# Регистрируем Tavily search
from core.action.tavily_tool import search as tavily_search
registry.register("web_search", tavily_search)
