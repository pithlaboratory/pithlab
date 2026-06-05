"""Orchestrator: safe bridge-layer for agent execution in Pith production."""
import asyncio
import logging
from typing import Any, Dict, List, Tuple


logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Безопасный orchestrator для production-режима:
    - запускает агентов параллельно;
    - не ломается от падения отдельных агентов;
    - не показывает пользователю сырые внутренние ответы;
    - выбирает лучший пригодный ответ, а не склеивает всё подряд.
    """

    AGENT_TIMEOUT_SEC = 25.0

    INTERNAL_LEAK_MARKERS = [
        "Current task context:",
        "Recent conversation:",
        "TaskState.",
        "TaskState:",
        "Как отвечать:",
        "Строгие запреты:",
        "Что реально работает сейчас:",
        "Что НЕ надо выдавать за production:",
        "---",
        "Status: TaskState",
        "user:",
        "assistant:",
        "system prompt",
    ]

    LOW_QUALITY_PREFIXES = [
        "🔍 Ничего не найдено",
        "Ничего не найдено",
        "Ошибка:",
        "LLM error:",
        "Не удалось выполнить через orchestrator:",
    ]

    PRIORITY_ORDER = ["CODA", "HEX", "PLEX", "TERA"]

    def __init__(self) -> None:
        from agents import tera, plex, hex, coda
        self.agents = [tera, plex, hex, coda]

    def _agent_name(self, agent: Any) -> str:
        return (
            getattr(agent, "name", None)
            or getattr(agent, "AGENT_NAME", None)
            or getattr(agent, "__name__", "UNKNOWN").split(".")[-1].upper()
        )

    async def _run_agent(self, agent: Any, query: str) -> str:
        if hasattr(agent, "process_async"):
            return await asyncio.wait_for(agent.process_async(query), timeout=self.AGENT_TIMEOUT_SEC)

        if hasattr(agent, "process"):
            return await asyncio.wait_for(
                asyncio.to_thread(agent.process, query),
                timeout=self.AGENT_TIMEOUT_SEC,
            )

        raise AttributeError(
            "Agent %s has no process_async/process method" % self._agent_name(agent)
        )

    async def run_async(self, query: str) -> Dict[str, str]:
        logger.info("Orchestrator starting %s agents", len(self.agents))

        tasks: List[asyncio.Future] = []
        names: List[str] = []

        for agent in self.agents:
            agent_name = self._agent_name(agent)
            names.append(agent_name)
            logger.info("Agent %s started", agent_name)
            tasks.append(self._run_agent(agent, query))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        output: Dict[str, str] = {}
        for agent_name, res in zip(names, results):
            if isinstance(res, Exception):
                output[agent_name] = "Ошибка: %s" % str(res)
                logger.error("Agent %s failed: %s", agent_name, res)
            else:
                output[agent_name] = str(res).strip()
                logger.info("Agent %s finished", agent_name)

        return output

    def _normalize_text(self, text: str) -> str:
        text = (text or "").strip()

        for prefix in ("[TERA]", "[PLEX]", "[HEX]", "[CODA]"):
            if text.startswith(prefix):
                text = text[len(prefix):].lstrip()

        return text.strip()

    def _is_internal_leak(self, text: str) -> bool:
        lowered = text.lower()
        return any(marker.lower() in lowered for marker in self.INTERNAL_LEAK_MARKERS)

    def _is_low_quality(self, text: str) -> bool:
        stripped = text.strip()
        if not stripped:
            return True
        return any(stripped.startswith(prefix) for prefix in self.LOW_QUALITY_PREFIXES)

    def _score_output(self, name: str, text: str) -> int:
        score = 0
        text_len = len(text)

        if name in self.PRIORITY_ORDER:
            score += max(0, 20 - self.PRIORITY_ORDER.index(name) * 3)

        if 200 <= text_len <= 4000:
            score += 20
        elif 80 <= text_len < 200:
            score += 10
        elif text_len > 4000:
            score -= 5
        else:
            score -= 10

        if self._is_internal_leak(text):
            score -= 100

        if self._is_low_quality(text):
            score -= 80

        if "```" in text:
            score += 3

        if "\n- " in text or "\n1." in text:
            score += 4

        return score

    def _rank_outputs(self, agent_outputs: Dict[str, str]) -> List[Tuple[str, str, int]]:
        ranked: List[Tuple[str, str, int]] = []

        for name, raw in agent_outputs.items():
            text = self._normalize_text(str(raw))
            score = self._score_output(name, text)
            ranked.append((name, text, score))

        ranked.sort(key=lambda item: item[2], reverse=True)
        return ranked

    def synthesize(self, agent_outputs: Dict[str, str]) -> str:
        ranked = self._rank_outputs(agent_outputs)

        for name, text, score in ranked:
            if score > 0 and not self._is_internal_leak(text) and not self._is_low_quality(text):
                logger.info("Orchestrator selected agent %s with score %s", name, score)
                return text

        for name, text, score in ranked:
            if text and not self._is_internal_leak(text):
                logger.warning(
                    "Orchestrator fallback selected weak output from %s with score %s",
                    name,
                    score,
                )
                return text

        logger.warning("Orchestrator could not synthesize a safe response")
        return (
            "Не удалось собрать корректный ответ через multi-agent слой. "
            "Нужен fallback на прямой LLM-ответ."
        )


orchestrator = Orchestrator()