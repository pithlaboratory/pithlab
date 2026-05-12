"""
Context Assembler — собирает контекст для LLM-вызовов в рамках Pith runtime.

Canonical alignment:
- docs/PITH_MASTER_PLAN.md
- docs/PRODUCT_DOCTRINE.md

Purpose:
- keep runtime context workspace-native,
- preserve continuity,
- keep context assembly governed and mode-aware.
"""

import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


logger = logging.getLogger(__name__)


class RuntimeMode(Enum):
    NORMAL = "normal"
    DIAGNOSTICS = "diagnostics"
    VISION = "vision"


@dataclass
class AssembledContext:
    """Собранный контекст для LLM-вызова."""

    mode: RuntimeMode
    system_prompt: str
    workspace_id: Optional[str] = None
    recent_messages: List[Dict[str, str]] = field(default_factory=list)
    summary: Optional[str] = None
    memory_context: str = ""
    artifact_context: str = ""
    task_context: str = ""

    def to_prompt_string(self) -> str:
        """
        Собирает финальный промпт согласно приоритетам контекста:
        1. System / runtime policy
        2. Workspace identity
        3. Mode instructions
        4. Summary
        5. Memory
        6. Task / artifacts
        7. Recent conversation
        """
        parts: List[str] = []

        # 1. System / runtime policy
        if self.system_prompt:
            parts.append(self.system_prompt)

        # 2. Workspace identity
        if self.workspace_id:
            parts.append(f"Workspace: {self.workspace_id}")

        # 3. Mode-specific instructions
        if self.mode == RuntimeMode.DIAGNOSTICS:
            parts.append(
                "Режим: DIAGNOSTICS\n"
                "Твоя задача — разобрать, что пошло не так, и предложить конкретные шаги фикса.\n"
                "Фокус на локальной диагностике, воспроизводимости, вероятной причине, проверках и безопасном следующем действии.\n"
                "Не уходи в общий самоанализ, философию системы или абстрактные архитектурные рассуждения без явного запроса."
            )
        elif self.mode == RuntimeMode.VISION:
            parts.append(
                "Режим: VISION\n"
                "Фокус на архитектуре Pith, roadmap, trade-offs, ограничениях, governance и следующих шагах.\n"
                "Отвечай как runtime-first architect: ясно, конкретно, без лишнего мета-комментирования и без persona-noise."
            )
        else:
            parts.append(
                "Режим: NORMAL\n"
                "Фокус на текущей задаче пользователя.\n"
                "Сохраняй continuity, но не перегружай ответ нерелевантным историческим контекстом."
            )

        # 4. Conversation summary
        if self.summary:
            parts.append(
                f"Previous conversation summary (background only):\n{self.summary}"
            )

        # 5. Memory context
        if self.memory_context:
            parts.append(f"Relevant memory:\n{self.memory_context}")

        # 6. Task / artifact context
        if self.task_context:
            parts.append(f"Current task context:\n{self.task_context}")

        if self.artifact_context:
            parts.append(f"Related artifacts / documents:\n{self.artifact_context}")

        # 7. Recent messages
        if self.recent_messages:
            history_str = "\n".join(
                f"{msg.get('role', 'unknown')}: {msg.get('content', '').strip()}"
                for msg in self.recent_messages
                if (msg.get("content") or "").strip()
            )
            if history_str.strip():
                parts.append(f"Recent conversation:\n{history_str}")

        return "\n\n---\n\n".join(parts).strip()


class ContextAssembler:
    """
    Собирает контекст для LLM согласно runtime-first логике Pith.

    Режимы:
    - NORMAL: стандартная работа, task-focus, continuity without overload
    - DIAGNOSTICS: локальная диагностика ошибок, инцидентов, регрессий
    - VISION: архитектура / roadmap / evolution именно Pith, а не любой пользовательский проект
    """

    MAX_RECENT_MESSAGES = 12
    FETCH_HISTORY_LIMIT = 18
    MEMORY_RESULTS_K = 5
    MAX_MEMORY_ITEMS = 3

    DIAGNOSTICS_KW = [
        "сломалось",
        "ошибка",
        "traceback",
        "баг",
        "fix",
        "не работает",
        "error",
        "bug",
        "broken",
        "failed",
        "failure",
        "crash",
        "stacktrace",
        "stack trace",
        "regression",
        "инцидент",
        "упало",
        "падает",
        "не запускается",
        "не стартует",
    ]

    # VISION mode должен включаться только для обсуждений самой системы Pith.
    VISION_KW = [
        "архитектура pith",
        "архитектура системы pith",
        "roadmap pith",
        "эволюция pith",
        "north star pith",
        "self-analysis pith",
        "разбери архитектуру pith",
        "что улучшить в pith",
        "pith vnext",
        "pith master plan",
        "pith kernel",
        "product doctrine pith",
    ]

    SHORT_QUERY_KW = {
        "/start",
        "start",
        "привет",
        "hi",
        "hello",
        "тут",
        "ок",
        "okay",
        "да",
        "ага",
        "давай",
    }

    # Убираем только явный persona/meta noise, не трогая нормальные архитектурные термины.
    META_NOISE_KW = {
        "философ режим",
        "парадокс режим",
        "рефлексия режим",
        "байесовский фильтр",
        "монте-карло симуляция",
        "квантификатор",
        "анти-хайп",
        "viktor vaughn phd",
    }

    def __init__(self, memory_manager, artifact_service=None, task_service=None):
        self.mm = memory_manager
        self.artifact_service = artifact_service
        self.task_service = task_service

    def build(
        self,
        query: str,
        user_id: str,
        workspace_id: Optional[str] = None,
        task_id: Optional[str] = None,
        mode: Optional[RuntimeMode] = None,
        recent_history: Optional[List[Dict[str, str]]] = None,
        system_prompt: str = "",
    ) -> AssembledContext:
        """
        Собирает контекст для planner/router/model call.
        """
        detected_mode = mode or self._detect_mode(query)

        logger.info(
            "ContextAssembler.build user=%s workspace=%s task=%s mode=%s query=%s",
            user_id,
            workspace_id,
            task_id,
            detected_mode.value,
            (query or "")[:80],
        )

        if recent_history is None:
            recent_history = self._fetch_recent_history(user_id, workspace_id)

        summary = None
        if len(recent_history) > self.MAX_RECENT_MESSAGES:
            old_messages = recent_history[:-self.MAX_RECENT_MESSAGES]
            summary = self._summarize_history(old_messages, user_id)
            recent_messages = recent_history[-self.MAX_RECENT_MESSAGES:]
        else:
            recent_messages = recent_history

        if detected_mode == RuntimeMode.DIAGNOSTICS:
            memory_ctx = self._build_diagnostic_memory(user_id, query, workspace_id)
            artifact_ctx = self._fetch_logs_and_configs(workspace_id, task_id)
            task_ctx = self._build_task_context(task_id, focus="diagnostics")

        elif detected_mode == RuntimeMode.VISION:
            memory_ctx = self._build_vision_memory(user_id, workspace_id)
            artifact_ctx = self._fetch_north_star_docs()
            task_ctx = self._build_task_context(task_id, focus="vision")

        else:
            memory_ctx = self._build_memory_context(user_id, query, workspace_id)
            artifact_ctx = self._fetch_task_artifacts(workspace_id, task_id)
            task_ctx = self._build_task_context(task_id, focus="normal")

        return AssembledContext(
            mode=detected_mode,
            system_prompt=system_prompt,
            workspace_id=workspace_id,
            recent_messages=recent_messages,
            summary=summary,
            memory_context=memory_ctx,
            artifact_context=artifact_ctx,
            task_context=task_ctx,
        )

    def _detect_mode(self, query: str) -> RuntimeMode:
        """
        Auto-detect режима на основе запроса.

        Важно:
        - diagnostics имеет приоритет над vision,
        - vision включается только при явном запросе про Pith.
        """
        lower = (query or "").strip().lower()

        if any(kw in lower for kw in self.DIAGNOSTICS_KW):
            return RuntimeMode.DIAGNOSTICS

        if any(kw in lower for kw in self.VISION_KW):
            return RuntimeMode.VISION

        return RuntimeMode.NORMAL

    def _fetch_recent_history(
        self,
        user_id: str,
        workspace_id: Optional[str],
    ) -> List[Dict[str, str]]:
        """
        Получает последние сообщения из memory manager.
        При наличии workspace isolation лучше позднее добавить фильтр по workspace_id.
        """
        try:
            episodes = self.mm.get_recent_episodes(
                user_id,
                limit=self.FETCH_HISTORY_LIMIT,
            )

            items: List[Dict[str, str]] = []
            for ep in episodes:
                content = (ep.get("content") or "").strip()
                if not content:
                    continue

                lower = content.lower()
                if any(kw in lower for kw in self.META_NOISE_KW):
                    continue

                items.append(
                    {
                        "role": ep.get("role", "unknown"),
                        "content": content,
                    }
                )

            return items[-self.FETCH_HISTORY_LIMIT :]

        except Exception as e:
            logger.warning("Failed to fetch recent history: %s", e)
            return []

    def _summarize_history(
        self,
        old_messages: List[Dict[str, str]],
        user_id: str,
    ) -> str:
        """
        Сворачивает старые сообщения в компактное summary.
        Пока безопасный stub; позже можно заменить на summarizer/tool call.
        """
        if not old_messages:
            return ""

        return (
            f"[Summary of {len(old_messages)} earlier messages — "
            f"conversation context preserved for continuity]"
        )

    def _build_memory_context(
        self,
        user_id: str,
        query: str,
        workspace_id: Optional[str],
    ) -> str:
        """
        NORMAL mode: релевантные memory records через vector search.
        Не тянем память для слишком коротких или noise-like запросов.
        """
        try:
            q = (query or "").strip().lower()
            if not q or q in self.SHORT_QUERY_KW or len(q) <= 6:
                return ""

            vector_memory = getattr(self.mm, "vector_memory", None)
            if vector_memory is None:
                return ""

            results = vector_memory.search(query, k=self.MEMORY_RESULTS_K)
            if not results:
                return ""

            parts: List[str] = []
            for r in results:
                content = (r.get("text") or "")[:220].strip()
                if not content:
                    continue

                lower = content.lower()
                if any(kw in lower for kw in self.META_NOISE_KW):
                    continue

                meta = r.get("metadata", {}) or {}
                timestamp = meta.get("timestamp", "")
                source = meta.get("source", "memory")
                line = f"[{source} {timestamp}] {content}".strip()
                parts.append(line)

            return "\n\n".join(parts[: self.MAX_MEMORY_ITEMS])

        except Exception as e:
            logger.warning("Memory search failed: %s", e)
            return ""

    def _build_diagnostic_memory(
        self,
        user_id: str,
        query: str,
        workspace_id: Optional[str],
    ) -> str:
        """
        DIAGNOSTICS mode: поиск прошлых инцидентов и похожих failure cases.
        """
        try:
            vector_memory = getattr(self.mm, "vector_memory", None)
            if vector_memory is None:
                return ""

            search_query = f"ошибка баг инцидент failure regression {query or ''}".strip()
            results = vector_memory.search(search_query, k=3)

            if not results:
                return ""

            parts: List[str] = []
            for r in results:
                content = (r.get("text") or "")[:180].strip()
                if not content:
                    continue

                meta = r.get("metadata", {}) or {}
                outcome = meta.get("outcome", "Unknown")
                lessons = meta.get("lessons", "Not documented")
                source = meta.get("source", "memory")

                parts.append(
                    f"Previous incident ({source}): {content}\n"
                    f"Outcome: {outcome}\n"
                    f"Lessons: {lessons}"
                )

            return "\n\n".join(parts)

        except Exception as e:
            logger.warning("Diagnostic memory search failed: %s", e)
            return ""

    def _build_vision_memory(
        self,
        user_id: str,
        workspace_id: Optional[str],
    ) -> str:
        """
        VISION mode: архитектурные обсуждения, roadmap, north-star decisions.
        """
        try:
            vector_memory = getattr(self.mm, "vector_memory", None)
            if vector_memory is None:
                return ""

            search_query = "pith architecture evolution roadmap kernel governance"
            results = vector_memory.search(search_query, k=5)

            if not results:
                return ""

            parts: List[str] = []
            for r in results:
                content = (r.get("text") or "")[:280].strip()
                if not content:
                    continue

                meta = r.get("metadata", {}) or {}
                timestamp = meta.get("timestamp", "")
                source = meta.get("source", "memory")

                parts.append(
                    f"[Architectural discussion {source} {timestamp}]\n{content}".strip()
                )

            return "\n\n".join(parts[: self.MAX_MEMORY_ITEMS])

        except Exception as e:
            logger.warning("Vision memory search failed: %s", e)
            return ""

    def _build_task_context(
        self,
        task_id: Optional[str],
        focus: str,
    ) -> str:
        """
        Собирает контекст текущей задачи из task_service.
        """
        if not task_id or not self.task_service:
            return ""

        try:
            task = self.task_service.get_task(task_id)
            if not task:
                return ""

            parts = [
                f"Task ID: {task_id}",
                f"Task: {getattr(task, 'input_text', 'Untitled')[:160]}",
                f"Status: {getattr(task, 'status', 'unknown')}",
            ]

            if getattr(task, "source_interface", None):
                parts.append(f"Interface: {task.source_interface}")

            if focus == "diagnostics" and getattr(task, "error_message", None):
                parts.append(f"Error: {task.error_message}")

            return "\n".join(parts)

        except Exception as e:
            logger.warning("Task context fetch failed: %s", e)
            return ""

    def _fetch_task_artifacts(
        self,
        workspace_id: Optional[str],
        task_id: Optional[str],
    ) -> str:
        """
        NORMAL mode: артефакты текущей задачи.
        Пока безопасный stub: не падает, даже если artifact service ещё не готов.
        """
        if not self.artifact_service or not task_id:
            return ""

        try:
            getter = getattr(self.artifact_service, "list_artifacts_for_task", None)
            if not callable(getter):
                return ""

            artifacts = getter(task_id) or []
            if not artifacts:
                return ""

            parts = []
            for art in artifacts[:5]:
                name = getattr(art, "name", None) or art.get("name", "artifact")
                kind = getattr(art, "artifact_type", None) or art.get("artifact_type", "unknown")
                parts.append(f"- {name} ({kind})")

            return "\n".join(parts)

        except Exception as e:
            logger.warning("Task artifacts fetch failed: %s", e)
            return ""

    def _fetch_logs_and_configs(
        self,
        workspace_id: Optional[str],
        task_id: Optional[str],
    ) -> str:
        """
        DIAGNOSTICS mode: логи и конфиги для troubleshooting.
        Сейчас безопасный stub с минимальным полезным контекстом.
        """
        parts: List[str] = []

        if workspace_id:
            parts.append(f"Workspace for diagnostics: {workspace_id}")
        if task_id:
            parts.append(f"Task under diagnostics: {task_id}")

        parts.append(
            "Diagnostics guidance: prioritize concrete failure signals, likely root cause, "
            "verification steps, and safest next fix."
        )

        return "\n".join(parts)

    def _fetch_north_star_docs(self) -> str:
        """
        VISION mode: North Star и архитектурные документы.

        Пока безопасный canonical stub.
        Позже сюда можно подключить repo/doc retrieval.
        """
        logger.debug(
            "_fetch_north_star_docs: using canonical stub until docs retrieval is connected"
        )

        return (
            "Canonical architecture notes:\n"
            "- Pith is a workspace-native orchestration runtime for continuity-driven work.\n"
            "- Pith must make complex work continuous, accumulative and governable.\n"
            "- Runtime-first: interfaces are secondary, kernel is primary.\n"
            "- Context assembly belongs to the canonical operating loop.\n"
            "- Governed autonomy grows gradually: L0 manual, L1 assisted, L2 reviewed, L3 canary auto.\n"
            "- Pith vNext extends the system toward capability accumulation and governed intelligence."
        )