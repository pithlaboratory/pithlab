"""
Context Assembler — assembles runtime context for LLM calls in Pith.

Canonical alignment:
- docs/PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md
- docs/PITH_ARCHITECTURE_NORTH_STAR_V2.md
- docs/PITH_MASTER_PLAN.md

Purpose:
- keep runtime context workspace-native,
- preserve continuity without overload,
- keep context assembly governed, mode-aware, and protocol-aligned.
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
    """Structured runtime context for a single LLM call."""

    mode: RuntimeMode
    system_prompt: str
    workspace_id: Optional[str] = None
    request_context: str = ""
    recent_messages: List[Dict[str, str]] = field(default_factory=list)
    summary: Optional[str] = None
    task_context: str = ""
    memory_context: str = ""
    artifact_context: str = ""

    def to_prompt_string(self) -> str:
        """
        Build user-context payload only.

        Important:
        - system_prompt is passed separately as a true system message,
          so it must NOT be duplicated inside the assembled prompt.
        - Context order follows runtime protocol priorities.
        """
        parts: List[str] = []

        # 1. Workspace identity
        if self.workspace_id:
            parts.append(f"Workspace: {self.workspace_id}")

        # 2. Mode-specific instructions
        if self.mode == RuntimeMode.DIAGNOSTICS:
            parts.append(
                "Mode: DIAGNOSTICS\n"
                "Focus on concrete failure signals, likely root cause, reproducibility, "
                "verification steps, and the safest next fix."
            )
        elif self.mode == RuntimeMode.VISION:
            parts.append(
                "Mode: VISION\n"
                "Focus on Pith architecture, roadmap, trade-offs, constraints, governance, "
                "and concrete next steps."
            )
        else:
            parts.append(
                "Mode: NORMAL\n"
                "Focus on the user's current task. Preserve continuity, but avoid irrelevant history."
            )

        # 3. Current request
        if self.request_context:
            parts.append(f"Current request:\n{self.request_context}")

        # 4. Current task context
        if self.task_context:
            parts.append(f"Current task context:\n{self.task_context}")

        # 5. Conversation summary
        if self.summary:
            parts.append(f"Conversation summary:\n{self.summary}")

        # 6. Relevant memory
        if self.memory_context:
            parts.append(f"Relevant memory:\n{self.memory_context}")

        # 7. Related artifacts / documents
        if self.artifact_context:
            parts.append(f"Relevant artifacts / documents:\n{self.artifact_context}")

        # 8. Recent messages
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
    Builds runtime context according to Pith runtime-first rules.

    Modes:
    - NORMAL: standard task-focused execution with continuity
    - DIAGNOSTICS: troubleshooting, regressions, failures, local root-cause analysis
    - VISION: Pith architecture, roadmap, kernel, doctrine, north-star evolution
    """

    MAX_RECENT_MESSAGES = 10
    FETCH_HISTORY_LIMIT = 18
    MEMORY_RESULTS_K = 5
    MAX_MEMORY_ITEMS = 3

    DIAGNOSTICS_KW = [
        "сломалось", "ошибка", "traceback", "баг", "fix", "не работает",
        "error", "bug", "broken", "failed", "failure", "crash",
        "stacktrace", "stack trace", "regression", "инцидент",
        "упало", "падает", "не запускается", "не стартует",
    ]

    VISION_CORE_KW = [
        "архитектура", "roadmap", "эволюция", "north star",
        "kernel", "master plan", "product doctrine", "governance",
    ]

    SHORT_QUERY_KW = {
        "/start", "start", "привет", "hi", "hello", "тут",
        "ок", "okay", "да", "ага", "давай",
    }

    # Persona/meta noise to strip from history & memory.
    META_NOISE_KW = {
        "философ режим", "парадокс режим", "рефлексия режим",
        "байесовский фильтр", "монте-карло симуляция",
        "квантификатор", "анти-хайп", "viktor vaughn phd",
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
        **kwargs: Any,
    ) -> AssembledContext:
        """
        Build context for planner/router/model calls.

        **kwargs kept for soft compatibility with existing call-sites.
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

        request_context = (query or "").strip()

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
            request_context=request_context,
            recent_messages=recent_messages,
            summary=summary,
            task_context=task_ctx,
            memory_context=memory_ctx,
            artifact_context=artifact_ctx,
        )

    def _detect_mode(self, query: str) -> RuntimeMode:
        """
        Auto-detect runtime mode based on query.

        - DIAGNOSTICS has priority over VISION
        - VISION only triggers for explicit Pith architecture/roadmap discussion
        """
        lower = (query or "").strip().lower()

        if any(kw in lower for kw in self.DIAGNOSTICS_KW):
            return RuntimeMode.DIAGNOSTICS

        if "pith" in lower and any(kw in lower for kw in self.VISION_CORE_KW):
            return RuntimeMode.VISION

        return RuntimeMode.NORMAL

    def _fetch_recent_history(
        self,
        user_id: str,
        workspace_id: Optional[str],
    ) -> List[Dict[str, str]]:
        """
        Fetch recent messages from memory manager.

        TODO: add workspace_id filtering when workspace isolation is ready.
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

            return items[-self.FETCH_HISTORY_LIMIT:]
        except Exception as e:
            logger.warning("Failed to fetch recent history: %s", e)
            return []

    def _summarize_history(
        self,
        old_messages: List[Dict[str, str]],
        user_id: str,
    ) -> str:
        """
        Compress older messages into a compact summary.

        Stub for now; can be replaced with summarizer/tool call later.
        """
        if not old_messages:
            return ""

        first = old_messages[0].get("content", "")[:120].strip()
        last = old_messages[-1].get("content", "")[:120].strip()
        return (
            f"Earliest relevant point: {first}\n"
            f"Latest prior point: {last}\n"
            f"Compressed {len(old_messages)} earlier messages for continuity."
        )

    def _build_memory_context(
        self,
        user_id: str,
        query: str,
        workspace_id: Optional[str],
    ) -> str:
        """
        NORMAL mode: relevant memory records via vector search.

        Skip memory for too-short or noise-like queries.
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
                parts.append(f"[{source} {timestamp}] {content}".strip())

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
        DIAGNOSTICS mode: search for past incidents and similar failure cases.
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

            return "\n\n".join(parts[: self.MAX_MEMORY_ITEMS])
        except Exception as e:
            logger.warning("Diagnostic memory search failed: %s", e)
            return ""

    def _build_vision_memory(
        self,
        user_id: str,
        workspace_id: Optional[str],
    ) -> str:
        """
        VISION mode: architectural discussions, roadmap, north-star decisions.
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
        Build current task context from task_service.
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
        NORMAL mode: artifacts of the current task.

        Safe stub for now; does nothing if artifact service is not ready.
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
        DIAGNOSTICS mode: logs and configs for troubleshooting.

        Safe canonical stub for now.
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
        VISION mode: North Star and architecture docs.

        Canonical stub until repo/doc retrieval is connected.
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
