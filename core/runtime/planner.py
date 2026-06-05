"""
Pith v5 — Runtime Planner
Author: Pith Lab
License: MIT
Status: L0/L1 autonomy enforced | Workspace-aware | Trace-ready | v1.1.4 Trace-Correlation

Governing docs:
- docs/PITH_ARCHITECTURE_NORTH_STAR_V2.md
- docs/PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md
"""
import asyncio
import json
import logging
import os
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime

from core.cognition.router import call_llm, normalize_router_mode
from core.orchestrator import orchestrator
from core.context_assembler import ContextAssembler, RuntimeMode
from core.goal_model import get_goal_model
from core.evolution.evaluator import Evaluator
from core.schemas import TaskState

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
        self.evaluator = Evaluator()
        self._eval_output_dir = "output/eval_runs"

    def _save_evaluation(self, result: Dict[str, Any], trace_id: str, user_id: str, original_text: str) -> Dict[str, Any]:
        """
        Run evaluator on result and save EvaluationRecord to output/eval_runs/<trace_id>.json.
        Returns result dict with "evaluation" key added. Safe — wrapped in try/except.
        """
        try:
            os.makedirs(self._eval_output_dir, exist_ok=True)
            eval_record = self.evaluator.evaluate_response(
                task_id=result.get("task_id", "unknown"),
                user_id=user_id,
                response=result.get("response", ""),
                model=result.get("model_id", "unknown"),
                tokens=result.get("tokens_prompt", 0) + result.get("tokens_completion", 0),
                cost=result.get("cost", 0.0),
                user_feedback=None,
                context_used=result.get("context_used"),
                task_type=result.get("task_type", "general"),
            )
            # Add trace_id and workspace_id (caller's responsibility per Evaluator contract)
            eval_record["trace_id"] = trace_id
            eval_record["workspace_id"] = result.get("workspace_id", "default")

            eval_path = os.path.join(self._eval_output_dir, f"{trace_id}.json")
            with open(eval_path, "w") as f:
                json.dump(eval_record, f, ensure_ascii=False, indent=2)

            result["evaluation"] = eval_record
            logger.info(
                "RuntimePlanner: saved eval record for task %s (score=%.2f) to %s",
                eval_record.get("task_id"),
                eval_record.get("quality_score", 0.0),
                eval_path,
            )
        except Exception:
            logger.exception("RuntimePlanner: evaluator failed — continuing without eval record")

        # Finalize task via TaskService (attach execution metadata + update status)
        self._apply_execution_result(result)
        return result

    def _apply_execution_result(self, result: Dict[str, Any]) -> None:
        """Attach execution metadata and mark task completed/failed in TaskService. Safe — try/except."""
        task_id = result.get("task_id")
        if not task_id or self.task_service is None:
            return
        try:
            model_id = result.get("model_id", "unknown")
            tokens_prompt = result.get("tokens_prompt", 0)
            tokens_completion = result.get("tokens_completion", 0)
            cost = result.get("cost", 0.0)
            trace_id = result.get("trace_id")

            self.task_service.attach_execution_result(
                task_id=task_id,
                model_id=model_id,
                model_name=result.get("model_name"),
                model_lane=None,
                cost_usd=cost,
                tokens_prompt=tokens_prompt,
                tokens_completion=tokens_completion,
                latency_ms=0,
                trace_id=trace_id,
            )

            # Add quality_score to metadata for score_final in trace
            eval_rec = result.get("evaluation")
            if eval_rec:
                quality_score = eval_rec.get("quality_score")
                if quality_score is not None:
                    # We access the task record directly through TaskService's internal dict
                    task = self.task_service._tasks.get(task_id)
                    if task:
                        task.metadata["quality_score"] = quality_score

            # Determine whether the task was successful or failed
            response = result.get("response", "")
            is_error = (
                result.get("model_id") == "error"
                or response.startswith("Не удалось")
                or response.startswith("LLM error")
            )
            new_status = TaskState.failed if is_error else TaskState.completed
            self.task_service.update_status(task_id, new_status)

            logger.info(
                "RuntimePlanner: finalized task %s -> %s (cost=%.6f, tokens=%d+%d)",
                task_id, new_status.value, cost, tokens_prompt, tokens_completion,
            )
        except Exception:
            logger.exception("RuntimePlanner: task finalization failed — continuing")

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
        trace_id: Optional[str] = None,  # ✅ Added for correlation
        workflow: Optional[str] = None,
        golden_id: Optional[str] = None,
        runtime_mode: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Workspace-native entry point.
        Phase 1: heuristic routing + structured context assembly.
        Phase 2: protocol-driven pruning, intent classification, agent routing.

        Args:
            user_id: User identifier.
            text: Input query text.
            workspace_id: Workspace scope.
            task_id: Optional pre-defined task ID.
            session_id: Optional session for context assembly.
            trace_id: Optional trace ID for correlation.
            workflow: Optional workflow name (e.g. 'support_resolution').
            golden_id: Optional golden test ID (e.g. 'support_ops_faq_v1').
        """
        # 0. Generate trace_id if not provided externally
        if trace_id is None:
            trace_id = uuid.uuid4().hex

        # 0a. Determine runtime_mode and task_type — prefer caller-provided values
        runtime_mode_str = runtime_mode or "normal"
        task_type_str = task_type or self._detect_task_type(text)

        # 0b. Create task in TaskService if available
        planned_task_id = task_id or uuid.uuid4().hex[:12]
        if self.task_service is not None:
            try:
                task_record = self.task_service.create_task(
                    workspace_id=workspace_id or "default",
                    user_id=user_id,
                    source_interface="system",
                    input_text=text,
                    intent_type=task_type_str,
                    trace_id=trace_id,
                    runtime_mode=runtime_mode_str,
                    task_type=task_type_str,
                    workflow=workflow,
                    golden_id=golden_id,
                )
                planned_task_id = task_record.task_id
                logger.info(
                    "RuntimePlanner: created task %s with trace_id %s",
                    planned_task_id, trace_id,
                )
            except Exception:
                logger.exception(
                    "RuntimePlanner: TaskService.create_task failed — continuing without task record",
                )

        # Store task_id, user_id, original_text, workspace_id for downstream flows
        self._current_planned_task_id = planned_task_id
        self._current_user_id = user_id
        self._current_original_text = text
        self._current_workspace_id = workspace_id or "default"
        self._current_task_type = task_type_str
        self._current_runtime_mode = runtime_mode_str

        # 1. Сборка контекста (workspace_id пробрасывается в Assembler)
        assembled = self.context_assembler.build(
            query=text,
            user_id=user_id,
            workspace_id=workspace_id,
            task_id=planned_task_id,
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
                runtime_mode=runtime_mode.value, task_type=task_type, goal_tags=goal_tags,
                trace_id=trace_id,
            )

        if is_complex:
            # Option A: keep existing signature. Phase 2 will add assembled_context here.
            return await self._run_orchestrator_flow(
                prompt, context_str, task_type=task_type, goal_tags=goal_tags,
                runtime_mode=runtime_mode.value, trace_id=trace_id,
            )

        return await self._run_direct_llm_flow(
            prompt, context_str, text, mode=router_mode,
            runtime_mode=runtime_mode.value, task_type=task_type, goal_tags=goal_tags,
            trace_id=trace_id,
        )

    async def _run_orchestrator_flow(
        self,
        prompt: str,
        context: str,
        task_type: str,
        goal_tags: List[str],
        runtime_mode: str = "normal",
        trace_id: Optional[str] = None,  # ✅ Added for correlation
    ) -> Dict[str, Any]:
        try:
            agent_results = await orchestrator.run_async(prompt)
            response = orchestrator.synthesize(agent_results)
            result = {
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
                "execution_path": "orchestrated",
                "trace_id": trace_id,  # ✅ Returned for correlation
                "task_id": self._current_planned_task_id,
                "workspace_id": self._current_workspace_id,
            }
            return self._save_evaluation(result, trace_id, self._current_user_id, self._current_original_text)
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
                "execution_path": "orchestrated",
                "trace_id": trace_id,  # ✅ Returned even on error
                "task_id": self._current_planned_task_id,
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
        trace_id: Optional[str] = None,  # ✅ Added for correlation
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
            direct_result = {
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
                "execution_path": "direct",
                "trace_id": trace_id,  # ✅ Returned for correlation
                "task_id": self._current_planned_task_id,
                "workspace_id": self._current_workspace_id,
            }
            return self._save_evaluation(direct_result, trace_id, self._current_user_id, self._current_original_text)
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
                "execution_path": "direct",
                "trace_id": trace_id,  # ✅ Returned even on error
                "task_id": self._current_planned_task_id,
            }
