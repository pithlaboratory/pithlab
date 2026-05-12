"""
Pith v5 — Runtime Planner
Author: Pith Lab
License: MIT
Status: L0/L1 autonomy enforced | Workspace-aware | Trace-ready | v1.1.2 Phase 1.5 Final

Governing docs:
- docs/PITH_ARCHITECTURE_NORTH_STAR_V2.md
- docs/PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md
"""
import asyncio
import logging
from typing import Optional, Dict, Any, List

from core.cognition.router import call_llm, normalize_router_mode
from core.orchestrator import orchestrator
from core.context_assembler import ContextAssembler, RuntimeMode
from core.goal_model import get_goal_model

logger = logging.getLogger(__name__)


class RuntimePlanner:
    """
    Планировщик выполнения запросов:
    - Простые запросы → прямой вызов LLM через router
    - Сложные запросы → orchestrator с multi-agent flow
    - Режимы: NORMAL, DIAGNOSTICS, VISION (управляют сборкой контекста)
    - Workspace-aware: изоляция контекста, метаданных, бюджетов
    
    Architecture notes:
    - Phase 1: heuristic routing + structured context assembly.
    - Phase 2: protocol-driven pruning, IntentClassifier, registry-driven routing.
    - Planner owns execution branching, NOT task taxonomy SSOT.
    """

    # Phase 1 heuristic complexity markers.
    # TODO (Phase 2): replace with classifier- or policy-driven complexity gating.
    COMPLEX_MARKERS = [
        "проанализируй", "стратегия", "архитектура", "спрогнозируй",
        "план", "исследование", "многошаговый", "агент", "orchestrator",
    ]

    # Phase 1 heuristic task classification keywords.
    # TODO (Phase 2): Replace with IntentClassifier / registry-driven taxonomy.
    TASK_KEYWORDS = {
        "coding": ["код", "code", "python", "bash", "sql", "traceback", "stacktrace", "ошибка", "исправь", "патч", "рефактор"],
        "debug": ["баг", "багфикс", "дебаг", "отладка", "почини", "не работает"],
        "agent_planning": ["пошагово", "спланируй", "план действий", "workflow", "агент"],
        "research_flow": ["исследуй", "найди информацию", "анализ источников", "факты"],
        "long_context": ["длинный текст", "документ", "файл", "репозиторий", "анализ кода"],
        "reasoning": ["почему", "объясни", "логика", "причина", "анализ"],
    }

    # Phase 1 heuristic mapping: task_type → router_mode.
    # TODO (Phase 2): Move to model_registry.json or router config as single source of truth.
    TASK_TYPE_TO_ROUTER_MODE = {
        "simple_chat": None, "summarize": None, "classification": None,
        "reasoning": "core", "general": None, "architecture": "core",
        "coding": "coder", "debug": "coder", "patch": "coder",
        "agent_planning": "agent", "research_flow": "agent",
        "long_context": "long_context",
    }

    def __init__(
        self,
        memory_manager,
        system_prompt: str,
        artifact_service=None,
        task_service=None,
    ):
        self.mm = memory_manager
        self.system_prompt = system_prompt
        self.artifact_service = artifact_service
        self.task_service = task_service
        self.context_assembler = ContextAssembler(
            memory_manager=memory_manager,
            artifact_service=artifact_service,
            task_service=task_service,
        )
        self.goal_model = get_goal_model()

    def _ensure_router_mode(self, mode: Optional[str], text: str) -> str:
        if mode is not None:
            return mode
        task_type = self._detect_task_type(text)
        return self._route_mode_for_task(task_type) or "core"

    def _goal_summary(self) -> str:
        core = self.goal_model.core_purpose
        subgoal_titles = [sg.title for sg in self.goal_model.subgoals[:3]]
        subgoals_text = "; ".join(subgoal_titles)
        return f"Core purpose: {core}\nKey subgoals: {subgoals_text}"

    # Phase 1 heuristic classifier.
    # TODO (Phase 2): Replace with IntentClassifier / registry-driven routing.
    def _detect_task_type(self, text: str) -> str:
        text_lower = text.lower()
        for task_type, keywords in self.TASK_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                return task_type
        return "general"

    def _route_mode_for_task(self, task_type: str) -> Optional[str]:
        # Phase 1: reads from local mapping. Phase 2: delegate to REGISTRY.get_mode_for_task()
        return self.TASK_TYPE_TO_ROUTER_MODE.get(task_type)

    def _is_complex_request(self, text: str) -> bool:
        markers_found = sum(1 for m in self.COMPLEX_MARKERS if m in text.lower())
        has_multiple_questions = text.count("?") > 1 or text.count("\n") > 2
        return markers_found >= 2 or len(text) > 300 or has_multiple_questions

    async def plan_and_answer(
        self,
        user_id: str,
        text: str,
        workspace_id: Optional[str] = None,
        task_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Workspace-native entry point.
        Phase 1: heuristic routing + structured context assembly.
        Phase 2: protocol-driven pruning, intent classification, agent routing.
        """
        # 1. Сборка контекста (workspace_id пробрасывается в Assembler)
        assembled = self.context_assembler.build(
            query=text,
            user_id=user_id,
            workspace_id=workspace_id,
            task_id=task_id,
            session_id=session_id,
            system_prompt=self.system_prompt,
        )

        context_str = assembled.to_prompt_string()
        prompt = f"{context_str}\n\nВопрос: {text}" if context_str else text

        # 2. Определение режима и тегов
        runtime_mode = assembled.mode
        # Phase 1: keyword heuristics. Replace with IntentClassifier in Phase 2.
        task_type = self._detect_task_type(text)
        router_mode = self._route_mode_for_task(task_type)
        router_mode = self._ensure_router_mode(router_mode, text)

        # ✅ Explicit runtime_mode → router_mode alignment (prevent drift)
        if runtime_mode == RuntimeMode.VISION and router_mode not in ("core", "agent", "long_context"):
            logger.debug(f"VISION mode override: router_mode '{router_mode}' → 'core'")
            router_mode = "core"
        elif runtime_mode == RuntimeMode.DIAGNOSTICS and router_mode not in ("coder", "core"):
            logger.debug(f"DIAGNOSTICS mode override: router_mode '{router_mode}' → 'coder'")
            router_mode = "coder"

        # 3. Формируем goal_tags для трейсов и eval
        goal_tags: List[str] = []
        if runtime_mode == RuntimeMode.DIAGNOSTICS:
            goal_tags.append("g_tactical_self_diagnostics")
        elif runtime_mode == RuntimeMode.VISION:
            goal_tags.append("g_strategic_evolution")
        # Phase 2: use goal_tags for agent routing/policy enforcement

        # 4. Маршрутизация потоков
        is_complex = self._is_complex_request(text)

        # FIX: allow VISION/DIAGNOSTICS to use orchestrator for complex tasks
        if runtime_mode in (RuntimeMode.DIAGNOSTICS, RuntimeMode.VISION) and not is_complex:
            return await self._run_direct_llm_flow(
                prompt, context_str, text, mode=router_mode,
                runtime_mode=runtime_mode.value, task_type=task_type, goal_tags=goal_tags
            )

        if is_complex:
            # Option A: keep existing signature. Phase 2 will add assembled_context here.
            return await self._run_orchestrator_flow(
                prompt, context_str, task_type=task_type, goal_tags=goal_tags,
                runtime_mode=runtime_mode.value,
            )

        return await self._run_direct_llm_flow(
            prompt, context_str, text, mode=router_mode,
            runtime_mode=runtime_mode.value, task_type=task_type, goal_tags=goal_tags
        )

    async def _run_orchestrator_flow(
        self,
        prompt: str,
        context: str,
        task_type: str,
        goal_tags: List[str],
        runtime_mode: str = "normal",
    ) -> Dict[str, Any]:
        try:
            agent_results = await orchestrator.run_async(prompt)
            response = orchestrator.synthesize(agent_results)
            return {
                "response": response,
                "model_id": "orchestrator",
                "model_name": "Orchestrator",
                "tokens_prompt": 0,
                "tokens_completion": 0,
                "cost": 0.0,
                "used_orchestrator": True,
                "context_used": context,
                "mode": runtime_mode,
                "runtime_mode": runtime_mode,
                "task_type": task_type,
                "goal_tags": goal_tags,
            }
        except Exception as e:
            logger.exception("Orchestrator flow failed")
            return {
                "response": f"Не удалось выполнить через orchestrator: {str(e)[:100]}",
                "model_id": "error",
                "model_name": "Error",
                "tokens_prompt": 0,
                "tokens_completion": 0,
                "cost": 0.0,
                "used_orchestrator": False,
                "context_used": context,
                "mode": "error",
                "runtime_mode": runtime_mode,
                "task_type": task_type,
                "goal_tags": goal_tags,
            }

    async def _run_direct_llm_flow(
        self,
        prompt: str,
        context: str,
        original_text: str,
        mode: Optional[str] = None,
        runtime_mode: str = "normal",
        task_type: str = "general",
        goal_tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        try:
            if mode is None:
                mode = self._ensure_router_mode(None, original_text)
            safe_mode = normalize_router_mode(mode) if mode is not None else None

            # DIAGNOSTICS enrichment
            if runtime_mode == "diagnostics":
                goal_context = self._goal_summary()
                prompt = f"{goal_context}\n\n{prompt}"

            result = await asyncio.to_thread(
                call_llm,
                prompt=prompt,
                system_prompt=self.system_prompt,
                mode=safe_mode,
            )

            usage = result.get("usage", {}) or {}
            return {
                "response": result.get("content", ""),
                "model_id": result.get("model", "unknown"),
                "model_name": result.get("model", "unknown"),
                "tokens_prompt": usage.get("prompt_tokens", 0),
                "tokens_completion": usage.get("completion_tokens", 0),
                "cost": result.get("cost_usd", 0.0),
                "used_orchestrator": False,
                "context_used": context,
                "mode": safe_mode.value if safe_mode else "core",
                "runtime_mode": runtime_mode,
                "task_type": task_type,
                "goal_tags": goal_tags or [],
            }
        except Exception as e:
            logger.exception("Direct LLM flow failed")
            return {
                "response": f"LLM error: {str(e)[:100]}",
                "model_id": "error",
                "model_name": "Error",
                "tokens_prompt": 0,
                "tokens_completion": 0,
                "cost": 0.0,
                "used_orchestrator": False,
                "context_used": context,
                "mode": "core",
                "runtime_mode": runtime_mode,
                "task_type": task_type,
                "goal_tags": goal_tags or [],
            }
