"""TERA: safe web search & research agent for explicit external-info tasks."""
import asyncio
import logging
import re
from typing import List

from core.action.tavily_tool import tavily_search

AGENT_NAME = "TERA"
logger = logging.getLogger(__name__)

MAX_QUERY_LEN = 300

SEARCH_INTENT_MARKERS = [
    "найди",
    "поиск",
    "search",
    "web",
    "веб",
    "источники",
    "ссылки",
    "research",
    "исследуй",
    "погугли",
    "поищи",
    "в интернете",
    "в сети",
    "latest",
    "новости",
]

INTERNAL_LEAK_MARKERS = [
    "Current task context:",
    "Recent conversation:",
    "TaskState",
    "Как отвечать:",
    "Строгие запреты:",
    "Что реально работает сейчас:",
    "Что НЕ надо выдавать за production:",
]

STOP_PHRASES = [
    "вопрос:",
    "current task context:",
    "recent conversation:",
    "status:",
    "task:",
]


def _contains_search_intent(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in SEARCH_INTENT_MARKERS)


def _strip_internal_sections(text: str) -> str:
    cleaned = text
    for marker in INTERNAL_LEAK_MARKERS:
        idx = cleaned.lower().find(marker.lower())
        if idx != -1:
            cleaned = cleaned[:idx]
    return cleaned.strip()


def _extract_question_tail(text: str) -> str:
    lowered = text.lower()
    idx = lowered.rfind("вопрос:")
    if idx != -1:
        return text[idx + len("вопрос:"):].strip()
    return text.strip()


def _trim_at_stop_phrases(text: str) -> str:
    lowered = text.lower()
    cut_positions = []
    for phrase in STOP_PHRASES:
        idx = lowered.find(phrase)
        if idx > 0:
            cut_positions.append(idx)
    if cut_positions:
        text = text[:min(cut_positions)]
    return text.strip()


def _collapse_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _sanitize_query(raw_query: str) -> str:
    text = raw_query or ""
    text = _strip_internal_sections(text)
    text = _extract_question_tail(text)
    text = _trim_at_stop_phrases(text)
    text = _collapse_whitespace(text)

    text = text.replace("«", '"').replace("»", '"')
    text = text.replace("—", "-")

    if len(text) > MAX_QUERY_LEN:
        text = text[:MAX_QUERY_LEN].rsplit(" ", 1)[0].strip()

    return text


def _query_too_broad_or_internal(text: str) -> bool:
    lowered = text.lower()

    if not text or len(text) < 8:
        return True

    if any(marker.lower() in lowered for marker in INTERNAL_LEAK_MARKERS):
        return True

    if lowered.count(":") > 3:
        return True

    if "user:" in lowered or "assistant:" in lowered:
        return True

    return False


def _format_sources(results: List[dict]) -> str:
    blocks = []
    for r in results[:3]:
        title = (r.get("title") or "Без названия").strip()
        raw_snippet = (r.get("snippet") or "").strip() or "Нет описания"
        snippet = raw_snippet[:180].strip()
        if len(raw_snippet) > 180:
            snippet += "..."
        url = (r.get("url") or "").strip()
        blocks.append(f"- {title}\n  {snippet}\n  {url}")
    return "\n\n".join(blocks)


async def process_async(query: str) -> str:
    """
    Выполняет web search только для явных external/research задач.
    Для нерелевантных запросов возвращает SKIP, чтобы orchestrator не выбирал TERA.
    """
    try:
        sanitized = _sanitize_query(query)

        if not _contains_search_intent(sanitized):
            logger.info("TERA skipped: no explicit search intent")
            return "SKIP: no explicit web-search intent"

        if _query_too_broad_or_internal(sanitized):
            logger.info("TERA skipped: query looks internal or too broad")
            return "SKIP: query is too broad for safe web search"

        results = await asyncio.to_thread(tavily_search, sanitized, max_results=3)

        if not results:
            return f"По веб-поиску ничего релевантного не найдено для запроса: {sanitized}"

        synthesis = (
            f"Найдены внешние источники по запросу: {sanitized}. "
            f"Всего релевантных результатов: {len(results[:3])}."
        )

        sources = _format_sources(results)
        return f"{synthesis}\n\n{sources}"

    except Exception:
        logger.exception("TERA search failed")
        return "SKIP: search failed"