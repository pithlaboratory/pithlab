"""Базовый класс агента."""
import asyncio
from typing import Optional, Dict, Any
from core.cognition.router import call_llm

class BaseAgent:
    def __init__(self, name: str, role_prompt: str):
        self.name = name
        self.role_prompt = role_prompt

    def process(self, query: str) -> str:
        """Синхронный вызов (для совместимости)."""
        prompt = f"{self.role_prompt}\n\nЗапрос: {query}"
        return call_llm(prompt)

    async def process_async(self, query: str) -> str:
        """Асинхронный вызов."""
        prompt = f"{self.role_prompt}\n\nЗапрос: {query}"
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, call_llm, prompt)

    def use_tool(self, tool_name: str, **kwargs) -> Optional[Any]:
        from core.action.tool_registry import registry
        return registry.call(tool_name, **kwargs)
