"""
Pith v5 — Intelligent LLM Router with Caching, Fallbacks & Budget Control
Author: Pith Lab
License: MIT

Workspace-aware extensions (2026-05-07):
- workspace_id parameter for budget/policy isolation
- Per-workspace budget tracking (stub for now, full impl later)
- Per-workspace policy enforcement (stub)
- Enriched traces with workspace context via extra={}
"""
import sys
import os
import logging
from pathlib import Path

# ✅ Ранний logging только в режиме отладки роутера
if os.getenv("PITH_ROUTER_DEBUG") == "1":
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

# Добавляем корень проекта в sys.path для прямого запуска скрипта
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Безопасный импорт: позволяет запускать smoke-test без ключа
try:
    from core.secrets import OPENROUTER_KEY
except RuntimeError:
    OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")  # fallback в None

import json
import time
import hashlib
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field, asdict
from enum import Enum

import yaml
import requests
from requests.exceptions import Timeout, RequestException, HTTPError

from core.model_registry import ModelRegistry, ModelRegistryEntry

class BudgetExceededError(Exception):
    pass

from core.traces import (
    make_llm_call_trace,
    record_llm_call,
    make_router_decision_trace,
    record_router_decision,
)

logger = logging.getLogger(__name__)

# === DEFAULT_CONFIG: синхронизирован с config.yaml ===
DEFAULT_CONFIG = {
    "budget": {
        "monthly_usd": 30.0,
        "monthly_soft_limit": 22.0,
        "daily_soft_limit": 0.80,
        "daily_hard_limit": 2.50,
        "warning_threshold": 0.8,
        "hard_stop": True,
    },
    "limits": {
        "max_tokens_default": 8192,
        "max_tokens_coding": 12000,
        "max_tokens_agent": 12000,
        "max_tokens_long_context": 16000,
        "max_tokens_premium": 10000,
    },
    "temperatures": {
        "default": 0.7,
        "coding": 0.2,
        "agent": 0.5,
        "long_context": 0.2,
        "premium": 0.3,
    },
    "requests": {
        "timeout_seconds": 90,
        "max_retries": 3,
        "retry_backoff_base": 2,
    },
    "routing": {
        "default_mode": "core",
        "allow_free_fallback": True,
        "allow_premium_fallback": False,
        "premium_requires_explicit": True,
        "global_policy": {
            "prefer_free_first": False,  # ✅ FIX: стабильность важнее экономии
            "default_paid_model": "deepseek/deepseek-v4-flash",
            "max_paid_hops_per_request": 2,
            "max_premium_hops_per_day": 8,
        },
        "long_context_trigger_chars": 12000,
        "long_context_trigger_tokens_est": 8000,
        "coding_trigger_keywords": [
            "код", "code", "python", "bash", "sql", "refactor",
            "bug", "patch", "fix", "traceback", "stacktrace", "ошибка", "исправь",
        ],
        "agent_trigger_keywords": [
            "пошагово", "спланируй", "план", "strategy", "research",
            "workflow", "agent", "архитектура",
        ],
        "premium_trigger_keywords": [
            "critical", "production incident", "high stakes", "arbiter", "критично", "сложнейший",
        ],
        "task_routes": {
            "simple_chat": "free",
            "summarize": "free",
            "classification": "free",
            "reasoning": "core",
            "general": "core",
            "architecture": "core",
            "coding": "coder",
            "debug": "coder",
            "patch": "coder",
            "agent_planning": "agent",
            "research_flow": "agent",
            "long_context": "long_context",
        },
    },
    "models": {
        "free": [
            {"id": "qwen/qwen3-coder:free", "budget_weight": 0.0, "role": "free_coder_primary"},
            # ✅ FIX: удалён мёртвый endpoint qwen/qwen3-30b-a3b:free
            {"id": "meta-llama/llama-3.3-70b-instruct:free", "budget_weight": 0.0, "role": "free_reasoning_alt"},
        ],
        "core": [
            {"id": "deepseek/deepseek-v4-flash", "budget_weight": 1.0, "role": "primary_general"},
            {"id": "deepseek/deepseek-chat-v3.1", "budget_weight": 1.08, "role": "stable_general_fallback"},
            {"id": "qwen/qwen3-32b", "budget_weight": 1.12, "role": "reasoning_general_alt"},
        ],
        "coder": [
            {"id": "qwen/qwen3-coder-plus", "budget_weight": 1.0, "role": "primary_coder"},
            {"id": "deepseek/deepseek-v4-flash", "budget_weight": 1.05, "role": "fast_coder_fallback"},
            {"id": "moonshotai/kimi-k2.6", "budget_weight": 1.12, "role": "long_horizon_coder"},
            {"id": "qwen/qwen3-coder:free", "budget_weight": 0.0, "role": "free_coder_backup"},
        ],
        "agent": [
            {"id": "moonshotai/kimi-k2.6", "budget_weight": 1.0, "role": "primary_agentic"},
            {"id": "moonshotai/kimi-k2.5", "budget_weight": 1.05, "role": "agentic_fallback"},
            {"id": "deepseek/deepseek-v4-flash", "budget_weight": 1.08, "role": "general_agent_fallback"},
            # ✅ FIX: удалён мёртвый endpoint qwen/qwen3-30b-a3b:free
        ],
        "long_context": [
            {"id": "deepseek/deepseek-v4-flash", "budget_weight": 1.0, "role": "primary_long_context"},
            {"id": "deepseek/deepseek-v4-pro", "budget_weight": 1.25, "role": "high_depth_long_context"},
            {"id": "moonshotai/kimi-k2.6", "budget_weight": 1.18, "role": "long_context_agentic"},
            {"id": "qwen/qwen3-coder-plus", "budget_weight": 1.15, "role": "repo_scale_long_context"},
        ],
        "premium": [
            {"id": "anthropic/claude-sonnet-4", "budget_weight": 2.0, "role": "highest_stakes_reasoning"},
            {"id": "deepseek/deepseek-v4-pro", "budget_weight": 1.55, "role": "premium_coding_reasoning"},
            {"id": "moonshotai/kimi-k2.6", "budget_weight": 1.35, "role": "premium_agentic_alt"},
        ],
    },
    "cache": {
        "enabled": True,
        "ttl_seconds": 3600,
        "max_entries": 1000,
        "path": "data/cache/router_cache.json",
    },
    "metrics": {
        "enabled": True,
        "path": "data/metrics/router_stats.json",
        "persist_llm_calls": True,
        "persist_router_decisions": True,
    },
    # 🆕 WORKSPACE: Workspace-specific policies (stub for now)
    "workspace_policies": {
        # Example: "ws_production": {"allow_premium": False, "max_daily_usd": 5.0}
    },
}

CONFIG_PATH = Path(__file__).parent.parent.parent / "config.yaml"
REGISTRY = ModelRegistry.load()


def _pick_default_chat_model() -> ModelRegistryEntry:
    """Временная точка: базовый lane для обычного чата."""
    return REGISTRY.get_lane_model("chat_default")


def _dedupe_model_specs(specs: List["ModelSpec"]) -> List["ModelSpec"]:
    """Убирает дубликаты моделей по id, сохраняя порядок первого вхождения."""
    seen = set()
    result: List["ModelSpec"] = []
    for spec in specs:
        if spec.id in seen:
            continue
        seen.add(spec.id)
        result.append(spec)
    return result


class RouterMode(Enum):
    CORE = "core"
    CODER = "coder"
    AGENT = "agent"
    FREE = "free"
    LONG_CONTEXT = "long_context"
    PREMIUM = "premium"
    CUSTOM = "custom"


@dataclass
class ModelSpec:
    id: str
    budget_weight: float = 1.0
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    role: str = ""


@dataclass
class RouterStats:
    total_calls: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    errors: int = 0
    tokens_used: Dict[str, int] = field(default_factory=dict)
    cost_usd: float = 0.0
    last_reset: str = field(default_factory=lambda: time.strftime("%Y-%m-%d"))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RouterStats":
        return cls(**data)


@dataclass
class LLMResponse:
    content: str
    model: str
    mode: str
    cached: bool
    usage: Dict[str, int] = field(default_factory=dict)
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    error: Optional[str] = None
    attempts: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SimpleCache:
    """Lightweight LRU-like cache with TTL for router responses."""

    def __init__(self, config: Dict[str, Any]):
        self.enabled = config.get("enabled", True)
        self.ttl = config.get("ttl_seconds", 3600)
        self.max_entries = config.get("max_entries", 1000)
        self.path = Path(config.get("path", "data/cache/router_cache.json"))
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _cache_key(
        self, prompt: str, model: str, mode: str, temp: float, system_prompt: str = ""
    ) -> str:
        raw = f"{system_prompt}|{prompt}|{model}|{mode}|{temp:.2f}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _load(self):
        if not self.enabled or not self.path.exists():
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            now = time.time()
            self._cache = {
                k: v for k, v in data.items() if now - v.get("timestamp", 0) < self.ttl
            }
        except Exception as e:
            logger.warning(f"Cache load failed: {e}")
            self._cache = {}

    def _save(self):
        if not self.enabled:
            return
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Cache save failed: {e}")

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        entry = self._cache.get(key)
        if entry and time.time() - entry.get("timestamp", 0) < self.ttl:
            return entry.get("response")
        return None

    def set(self, key: str, response: Dict[str, Any]):
        if not self.enabled:
            return
        if len(self._cache) >= self.max_entries:
            oldest = min(self._cache.items(), key=lambda x: x[1].get("timestamp", 0))
            del self._cache[oldest[0]]
        self._cache[key] = {"timestamp": time.time(), "response": response}
        self._save()

    def clear(self):
        self._cache.clear()
        if self.path.exists():
            self.path.unlink()


class MetricsTracker:
    """Track router usage, costs, and performance."""

    PRICING = {
        "deepseek/deepseek-v4-flash": {"input": 0.00027, "output": 0.0011},
        "deepseek/deepseek-chat-v3.1": {"input": 0.00027, "output": 0.0011},
        "qwen/qwen3-32b": {"input": 0.000325, "output": 0.00195},
        "qwen/qwen3-coder:free": {"input": 0.0, "output": 0.0},
        "qwen/qwen3-30b-a3b:free": {"input": 0.0, "output": 0.0},
        "qwen/qwen3-coder-plus": {"input": 0.0004, "output": 0.0016},
        "moonshotai/kimi-k2.6": {"input": 0.00056, "output": 0.002},
        "moonshotai/kimi-k2.5": {"input": 0.0005, "output": 0.0018},
        "anthropic/claude-sonnet-4": {"input": 0.003, "output": 0.015},
        "deepseek/deepseek-v4-pro": {"input": 0.0012, "output": 0.005},
        "default": {"input": 0.0005, "output": 0.0015},
    }

    def __init__(self, config: Dict[str, Any]):
        self.enabled = config.get("enabled", True)
        self.path = Path(config.get("path", "data/metrics/router_stats.json"))
        self.budget_limit = config.get("budget", {}).get("monthly_usd", 30.0)
        self.warning_threshold = config.get("budget", {}).get("warning_threshold", 0.8)
        self.stats = RouterStats()
        self._load()

    def _load(self):
        if not self.enabled or not self.path.exists():
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.stats = RouterStats.from_dict(data)
        except Exception as e:
            logger.warning(f"Metrics load failed: {e}")

    def _save(self):
        if not self.enabled:
            return
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.stats.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Metrics save failed: {e}")

    def _estimate_cost(self, model: str, usage: Dict[str, int]) -> float:
        pricing = self.PRICING.get(model, self.PRICING["default"])
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        return (
            prompt_tokens / 1000 * pricing["input"]
            + completion_tokens / 1000 * pricing["output"]
        )

    def record_call(
        self,
        model: str,
        usage: Dict[str, int],
        cached: bool,
        error: Optional[str] = None,
        workspace_id: Optional[str] = None,  # 🆕 WORKSPACE
    ):
        if not self.enabled:
            return
        self.stats.total_calls += 1
        if cached:
            self.stats.cache_hits += 1
        else:
            self.stats.cache_misses += 1
        if error:
            self.stats.errors += 1
        else:
            cost = self._estimate_cost(model, usage)
            self.stats.cost_usd += cost
            self.stats.tokens_used[model] = (
                self.stats.tokens_used.get(model, 0)
                + usage.get("prompt_tokens", 0)
                + usage.get("completion_tokens", 0)
            )
            # 🆕 WORKSPACE: TODO — per-workspace budget tracking
            # if workspace_id:
            #     workspace_path = Path(f"data/metrics/workspace_{workspace_id}_stats.json")
            #     # load, increment, save
        self._save()

    def check_budget(
        self, workspace_id: Optional[str] = None  # 🆕 WORKSPACE
    ) -> Dict[str, Any]:
        if not self.enabled:
            return {"ok": True, "message": "Metrics disabled"}
        
        # 🆕 WORKSPACE: TODO — load workspace-specific budget if workspace_id provided
        # For now, use global budget
        pct = self.stats.cost_usd / self.budget_limit if self.budget_limit > 0 else 0
        status = "ok"
        if pct >= 1.0:
            status = "exceeded"
        elif pct >= self.warning_threshold:
            status = "warning"
        return {
            "ok": status == "ok",
            "status": status,
            "spent_usd": round(self.stats.cost_usd, 3),
            "limit_usd": self.budget_limit,
            "percent": round(pct * 100, 1),
            "recommendation": (
                "Switch to free-tier models"
                if status == "warning"
                else "Halt non-essential calls"
                if status == "exceeded"
                else "All systems nominal"
            ),
            "workspace_id": workspace_id,  # 🆕 WORKSPACE
        }

    def reset_stats(self):
        self.stats = RouterStats()
        self._save()


# === PUBLIC API: Registry access helpers ===


def get_registry_route(task_type: str):
    return REGISTRY.get_task_route(task_type)


def get_registry_default(role: str):
    return REGISTRY.get_default(role)


def get_registry_lane(lane: str):
    """Безопасная точка доступа к lane-based моделям."""
    return REGISTRY.get_lane_model(lane)


# === LLMRouter class ===


class LLMRouter:
    """
    Intelligent router for Pith v5:
    - Mode-based model selection
    - Smart fallback loop with 404/429 handling
    - Budget tracking and policy enforcement
    - Retry logic with exponential backoff
    - 🆕 Workspace-aware budget/policy isolation
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or CONFIG_PATH
        self.config = self._load_config()
        self.cache = SimpleCache(self.config.get("cache", {}))
        self.metrics = MetricsTracker(self.config)
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Content-Type": "application/json",
                "HTTP-Referer": "https://pith-v5.local",
                "X-Title": "Pith v5",
            }
        )

    def _load_config(self) -> Dict[str, Any]:
        cfg = json.loads(json.dumps(DEFAULT_CONFIG))
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    user_cfg = yaml.safe_load(f)
                if isinstance(user_cfg, dict):
                    self._deep_merge(cfg, user_cfg)
            except Exception as e:
                logger.error(f"Config load failed: {e}")

        metrics_cfg = cfg.setdefault("metrics", {})
        budget_cfg = cfg.get("budget", {})
        if "budget" not in metrics_cfg:
            metrics_cfg["budget"] = {
                "monthly_usd": budget_cfg.get("monthly_usd", 30.0),
                "warning_threshold": budget_cfg.get("warning_threshold", 0.8),
            }

        if not OPENROUTER_KEY:
            logger.warning(
                "⚠️ OpenRouter API key not set — router will fail on first call"
            )
        return cfg

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]):
        for k, v in override.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                self._deep_merge(base[k], v)
            else:
                base[k] = v

    def _get_models_for_mode(self, mode: str) -> List[ModelSpec]:
        models_cfg = self.config.get("models", {}).get(mode, []) or []
        if not models_cfg:
            fallback = self.config.get("models", {}).get("core", []) or []
            models_cfg = (
                fallback
                if fallback
                else [
                    {
                        "id": self.config.get("routing", {})
                        .get("global_policy", {})
                        .get("default_paid_model", "deepseek/deepseek-v4-flash")
                    }
                ]
            )
        specs: List[ModelSpec] = []
        for m in models_cfg:
            if isinstance(m, str):
                specs.append(ModelSpec(id=m))
            elif isinstance(m, dict) and "id" in m:
                specs.append(
                    ModelSpec(
                        id=m["id"],
                        budget_weight=m.get("budget_weight", 1.0),
                        max_tokens=m.get("max_tokens"),
                        temperature=m.get("temperature"),
                        role=m.get("role", ""),
                    )
                )
        return specs

    def _select_mode_by_content(self, prompt: str) -> RouterMode:
        routing = self.config.get("routing", {})
        if len(prompt) > routing.get("long_context_trigger_chars", 12000):
            return RouterMode.LONG_CONTEXT
        lower = prompt.lower()
        for kw in routing.get("coding_trigger_keywords", []):
            if kw in lower:
                return RouterMode.CODER
        for kw in routing.get("agent_trigger_keywords", []):
            if kw in lower:
                return RouterMode.AGENT
        for kw in routing.get("premium_trigger_keywords", []):
            if kw in lower:
                return RouterMode.PREMIUM
        return normalize_router_mode(routing.get("default_mode", "core"))

    # 🆕 WORKSPACE: Policy check per workspace
    def _check_workspace_policy(
        self, workspace_id: Optional[str], mode: RouterMode
    ) -> Dict[str, Any]:
        """
        Stub для workspace-specific policy enforcement.
        TODO: Реализовать полноценную policy engine когда будет WorkspaceService.
        
        Returns:
            {"ok": bool, "reason": str, "override_mode": Optional[RouterMode]}
        """
        if not workspace_id:
            return {"ok": True, "reason": "no_workspace_id"}
        
        workspace_policies = self.config.get("workspace_policies", {})
        policy = workspace_policies.get(workspace_id)
        
        if not policy:
            return {"ok": True, "reason": "no_policy_defined"}
        
        # Example policy checks:
        if mode == RouterMode.PREMIUM and not policy.get("allow_premium", True):
            logger.warning(f"Workspace {workspace_id} blocks PREMIUM mode, falling back to CORE")
            return {"ok": False, "reason": "premium_blocked", "override_mode": RouterMode.CORE}
        
        return {"ok": True, "reason": "policy_passed"}

    def _build_payload(
        self,
        model: ModelSpec,
        prompt: str,
        system_prompt: str,
        temperature: Optional[float],
        max_tokens: Optional[int],
        mode: RouterMode,
    ) -> Dict[str, Any]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        temps = self.config.get("temperatures", {})
        mode_temp_key = mode.value if mode.value in temps else "default"
        lims = self.config.get("limits", {})
        mode_lim_key = (
            f"max_tokens_{mode.value}"
            if f"max_tokens_{mode.value}" in lims
            else "max_tokens_default"
        )
        return {
            "model": model.id,
            "messages": messages,
            "temperature": (
                temperature
                if temperature is not None
                else model.temperature
                if model.temperature is not None
                else temps.get(mode_temp_key, temps["default"])
            ),
            "max_tokens": (
                max_tokens
                if max_tokens is not None
                else model.max_tokens
                if model.max_tokens is not None
                else lims[mode_lim_key]
            ),
        }

    def _call_api(
        self,
        payload: Dict[str, Any],
        timeout: float,
        max_retries: int,
        backoff_base: float,
    ) -> Dict[str, Any]:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            **self._session.headers,
        }
        for attempt in range(max_retries):
            try:
                resp = self._session.post(
                    url, json=payload, headers=headers, timeout=timeout
                )
                resp.raise_for_status()
                data = resp.json()
                if "choices" not in data or not data["choices"]:
                    raise ValueError(
                        f"Empty choices in response: {list(data.keys())}"
                    )
                return {
                    "content": data["choices"][0]["message"]["content"],
                    "usage": data.get("usage", {}),
                    "model": data.get("model", payload["model"]),
                }
            except Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1}")
            except HTTPError as e:
                status = e.response.status_code if e.response is not None else 500
                body = (e.response.text or "")[:200]
                logger.error(f"HTTP {status}: {body}")
                if status in (404, 429):
                    raise RuntimeError(f"RETRY_MODEL_{status}") from e
                if status == 401:
                    raise RuntimeError("Invalid API key") from e
                if status >= 500:
                    pass
            except RequestException as e:
                logger.error(f"Request failed: {e}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                raise ValueError("API returned malformed JSON") from e
            except Exception as e:
                logger.error(f"Unexpected: {type(e).__name__}: {e}")
                if attempt == max_retries - 1:
                    raise
            if attempt < max_retries - 1:
                sleep_time = backoff_base**attempt
                time.sleep(sleep_time)
        raise RuntimeError(f"Failed after {max_retries} attempts")

    def call(
        self,
        prompt: str,
        system_prompt: str = "",
        mode: Union[str, RouterMode, None] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        force_refresh: bool = False,
        workspace_id: Optional[str] = None,  # 🆕 WORKSPACE
        **kwargs,
    ) -> LLMResponse:
        start_time = time.time()
        mode_was_explicit = mode is not None
        if mode is None:
            mode = self._select_mode_by_content(prompt)
        else:
            mode = normalize_router_mode(mode)

        # 🆕 WORKSPACE: Policy check
        policy_result = self._check_workspace_policy(workspace_id, mode)
        if not policy_result["ok"]:
            override_mode = policy_result.get("override_mode")
            if override_mode:
                logger.info(
                    f"Workspace {workspace_id} policy override: {mode.value} → {override_mode.value}"
                )
                mode = override_mode

        if mode == RouterMode.CORE:
            try:
                lane_model = get_registry_lane("chat_default")
                logger.debug(
                    f"[lanes] CORE mode will use chat_default lane baseline: {lane_model.model_id} ({lane_model.key})"
                )
            except KeyError:
                logger.warning(
                    "[lanes] chat_default lane is not defined in model_registry.json"
                )

        budget_status = self.metrics.check_budget(workspace_id=workspace_id)  # 🆕 WORKSPACE
        policy = self.config.get("routing", {}).get("global_policy", {})
        prefer_free = policy.get("prefer_free_first", True)

        if not budget_status["ok"] and mode != RouterMode.FREE:
            logger.warning(
                f"Budget {budget_status['status']}: {budget_status['recommendation']}"
            )
            if self.config.get("budget", {}).get("hard_stop", True):
                # ✅ FIX: workspace_id через extra, не как параметр
                record_llm_call(
                    make_llm_call_trace(
                        agent=kwargs.get("agent", "unknown"),
                        session_id=kwargs.get("session_id"),
                        task_id=kwargs.get("task_id"),
                        model="",
                        mode=mode.value or "",
                        prompt=prompt,
                        system_prompt=system_prompt,
                        cached=False,
                        success=False,
                        attempts=0,
                        latency_ms=(time.time() - start_time) * 1000,
                        usage={},
                        cost_usd=0.0,
                        error=f"budget_exceeded:{budget_status['spent_usd']}/{budget_status['limit_usd']}",
                        extra={
                            "failure_stage": "budget_hard_stop",
                            "workspace_id": workspace_id,  # ✅ WORKSPACE via extra
                        },
                    )
                )
                record_router_decision(
                    make_router_decision_trace(
                        agent=kwargs.get("agent", "unknown"),
                        session_id=kwargs.get("session_id"),
                        task_id=kwargs.get("task_id"),
                        mode=mode.value,
                        explicit_mode=mode_was_explicit,
                        budget_status=budget_status.get("status", "ok"),
                        budget_spent_usd=budget_status.get("spent_usd", 0.0),
                        budget_limit_usd=budget_status.get("limit_usd", 0.0),
                        prompt=prompt,
                        system_prompt=system_prompt,
                        success=False,
                        reason="budget_hard_stop",
                        error=f"Budget exceeded: {budget_status['spent_usd']}/{budget_status['limit_usd']}",
                        extra={"workspace_id": workspace_id},  # ✅ WORKSPACE via extra
                    )
                )
                raise BudgetExceededError(
                    f"Budget exceeded: {budget_status['spent_usd']}/{budget_status['limit_usd']}"
                )
            mode = RouterMode.FREE

        # 📝 DECISION #1: Start
        record_router_decision(
            make_router_decision_trace(
                agent=kwargs.get("agent", "unknown"),
                session_id=kwargs.get("session_id"),
                task_id=kwargs.get("task_id"),
                mode=mode.value,
                explicit_mode=mode_was_explicit,
                prompt=prompt,
                system_prompt=system_prompt,
                prefer_free_first=prefer_free,
                budget_status=budget_status.get("status", "ok"),
                budget_spent_usd=budget_status.get("spent_usd", 0.0),
                budget_limit_usd=budget_status.get("limit_usd", 0.0),
                reason="router_call_started",
                extra={
                    "policy_check": policy_result,
                    "workspace_id": workspace_id,  # ✅ WORKSPACE via extra
                },
            )
        )

        if model:
            candidates = [ModelSpec(id=model)]
        else:
            candidates: List[ModelSpec] = []
            if mode == RouterMode.CORE:
                try:
                    lane_entry = _pick_default_chat_model()
                    candidates.append(
                        ModelSpec(
                            id=lane_entry.model_id,
                            budget_weight=1.0,
                            role=lane_entry.key,
                        )
                    )
                except KeyError:
                    logger.warning(
                        "[lanes] chat_default lane not found, fallback to config models for CORE"
                    )

            candidates.extend(self._get_models_for_mode(mode.value))
            if prefer_free and mode != RouterMode.FREE:
                free_pool = self._get_models_for_mode(RouterMode.FREE.value)
                candidates = free_pool + candidates
            candidates = _dedupe_model_specs(candidates)

        # 📝 DECISION #2: Candidates ready
        record_router_decision(
            make_router_decision_trace(
                agent=kwargs.get("agent", "unknown"),
                session_id=kwargs.get("session_id"),
                task_id=kwargs.get("task_id"),
                mode=mode.value,
                explicit_mode=mode_was_explicit,
                selected_models=[c.id for c in candidates],
                selected_roles=[c.role for c in candidates if c.role],
                prefer_free_first=prefer_free,
                budget_status=budget_status.get("status", "ok"),
                budget_spent_usd=budget_status.get("spent_usd", 0.0),
                budget_limit_usd=budget_status.get("limit_usd", 0.0),
                prompt=prompt,
                system_prompt=system_prompt,
                reason="candidates_ready",
                extra={"workspace_id": workspace_id},  # ✅ WORKSPACE via extra
            )
        )

        max_hops = policy.get("max_paid_hops_per_request", 2)
        hops = 0
        last_error = ""

        for attempt_idx, candidate in enumerate(candidates):
            if hops >= max_hops and candidate.budget_weight > 0:
                continue

            cache_key = self.cache._cache_key(
                prompt, candidate.id, mode.value, temperature or 0.7
            )
            if not force_refresh:
                cached = self.cache.get(cache_key)
                if cached:
                    latency = (time.time() - start_time) * 1000
                    self.metrics.record_call(
                        candidate.id, {}, cached=True, workspace_id=workspace_id
                    )
                    # ✅ FIX: workspace_id через extra
                    record_llm_call(
                        make_llm_call_trace(
                            agent=kwargs.get("agent", "unknown"),
                            session_id=kwargs.get("session_id"),
                            task_id=kwargs.get("task_id"),
                            model=cached.get("model", candidate.id),
                            mode=mode.value or "",
                            prompt=prompt,
                            system_prompt=system_prompt,
                            cached=True,
                            success=True,
                            attempts=attempt_idx + 1,
                            latency_ms=latency,
                            usage=cached.get("usage", {}),
                            cost_usd=0.0,
                            extra={
                                "source": "router_cache",
                                "workspace_id": workspace_id,  # ✅ WORKSPACE via extra
                            },
                        )
                    )
                    record_router_decision(
                        make_router_decision_trace(
                            agent=kwargs.get("agent", "unknown"),
                            session_id=kwargs.get("session_id"),
                            task_id=kwargs.get("task_id"),
                            mode=mode.value,
                            explicit_mode=mode_was_explicit,
                            selected_models=[candidate.id],
                            selected_roles=[candidate.role] if candidate.role else [],
                            prefer_free_first=prefer_free,
                            budget_status=budget_status.get("status", "ok"),
                            budget_spent_usd=budget_status.get("spent_usd", 0.0),
                            budget_limit_usd=budget_status.get("limit_usd", 0.0),
                            prompt=prompt,
                            system_prompt=system_prompt,
                            success=True,
                            final_model=cached.get("model", candidate.id),
                            hops_used=hops,
                            reason="cache_hit",
                            extra={"workspace_id": workspace_id},  # ✅ WORKSPACE via extra
                        )
                    )
                    return LLMResponse(
                        content=cached["content"],
                        model=cached["model"],
                        mode=mode.value,
                        cached=True,
                        usage=cached.get("usage", {}),
                        latency_ms=latency,
                        attempts=attempt_idx + 1,
                    )

            payload = self._build_payload(
                candidate, prompt, system_prompt, temperature, max_tokens, mode
            )
            req_cfg = self.config.get("requests", {})
            try:
                api_result = self._call_api(
                    payload,
                    req_cfg.get("timeout_seconds", 90),
                    req_cfg.get("max_retries", 3),
                    req_cfg.get("retry_backoff_base", 2),
                )
                latency = (time.time() - start_time) * 1000
                self.cache.set(
                    cache_key,
                    {
                        "content": api_result["content"],
                        "model": api_result["model"],
                        "usage": api_result["usage"],
                    },
                )
                self.metrics.record_call(
                    api_result["model"],
                    api_result["usage"],
                    cached=False,
                    workspace_id=workspace_id,
                )
                if candidate.budget_weight > 0:
                    hops += 1
                estimated_cost = self.metrics._estimate_cost(
                    api_result["model"], api_result["usage"]
                )

                # ✅ FIX: workspace_id через extra
                record_llm_call(
                    make_llm_call_trace(
                        agent=kwargs.get("agent", "unknown"),
                        session_id=kwargs.get("session_id"),
                        task_id=kwargs.get("task_id"),
                        model=api_result["model"],
                        mode=mode.value or "",
                        prompt=prompt,
                        system_prompt=system_prompt,
                        cached=False,
                        success=True,
                        attempts=attempt_idx + 1,
                        latency_ms=latency,
                        usage=api_result["usage"],
                        cost_usd=estimated_cost,
                        extra={
                            "candidate_id": candidate.id,
                            "candidate_role": candidate.role,
                            "budget_weight": candidate.budget_weight,
                            "workspace_id": workspace_id,  # ✅ WORKSPACE via extra
                        },
                    )
                )
                record_router_decision(
                    make_router_decision_trace(
                        agent=kwargs.get("agent", "unknown"),
                        session_id=kwargs.get("session_id"),
                        task_id=kwargs.get("task_id"),
                        mode=mode.value,
                        explicit_mode=mode_was_explicit,
                        selected_models=[c.id for c in candidates],
                        selected_roles=[c.role for c in candidates if c.role],
                        prefer_free_first=prefer_free,
                        budget_status=budget_status.get("status", "ok"),
                        budget_spent_usd=budget_status.get("spent_usd", 0.0),
                        budget_limit_usd=budget_status.get("limit_usd", 0.0),
                        prompt=prompt,
                        system_prompt=system_prompt,
                        success=True,
                        final_model=api_result["model"],
                        hops_used=hops,
                        reason="final_success",
                        extra={
                            "candidate_id": candidate.id,
                            "candidate_role": candidate.role,
                            "attempt": attempt_idx + 1,
                            "workspace_id": workspace_id,  # ✅ WORKSPACE via extra
                        },
                    )
                )
                return LLMResponse(
                    content=api_result["content"],
                    model=api_result["model"],
                    mode=mode.value,
                    cached=False,
                    usage=api_result["usage"],
                    cost_usd=estimated_cost,
                    latency_ms=latency,
                    attempts=attempt_idx + 1,
                )
            except RuntimeError as e:
                err_str = str(e)
                if "RETRY_MODEL_404" in err_str or "RETRY_MODEL_429" in err_str:
                    logger.warning(
                        f"Model {candidate.id} unavailable (404/429), switching to next candidate"
                    )
                    last_error = f"{candidate.id}: {err_str}"
                    if candidate.budget_weight > 0:
                        hops += 1
                    continue
                last_error = f"{candidate.id}: {err_str}"
                break
            except Exception as e:
                last_error = f"{candidate.id}: {type(e).__name__}: {e}"
                break

        latency = (time.time() - start_time) * 1000
        logger.error(f"All candidates failed. Last error: {last_error}")
        first_id = candidates[0].id if candidates else "unknown"
        self.metrics.record_call(
            first_id, {}, cached=False, error=last_error, workspace_id=workspace_id
        )

        # ✅ FIX: workspace_id через extra
        record_llm_call(
            make_llm_call_trace(
                agent=kwargs.get("agent", "unknown"),
                session_id=kwargs.get("session_id"),
                task_id=kwargs.get("task_id"),
                model=first_id,
                mode=mode.value or "",
                prompt=prompt,
                system_prompt=system_prompt,
                cached=False,
                success=False,
                attempts=len(candidates),
                latency_ms=latency,
                usage={},
                cost_usd=0.0,
                error=last_error,
                extra={
                    "failure_stage": "router_exhausted_candidates",
                    "workspace_id": workspace_id,  # ✅ WORKSPACE via extra
                },
            )
        )
        record_router_decision(
            make_router_decision_trace(
                agent=kwargs.get("agent", "unknown"),
                session_id=kwargs.get("session_id"),
                task_id=kwargs.get("task_id"),
                mode=mode.value,
                explicit_mode=mode_was_explicit,
                selected_models=[c.id for c in candidates],
                selected_roles=[c.role for c in candidates if c.role],
                prefer_free_first=prefer_free,
                budget_status=budget_status.get("status", "ok"),
                budget_spent_usd=budget_status.get("spent_usd", 0.0),
                budget_limit_usd=budget_status.get("limit_usd", 0.0),
                prompt=prompt,
                system_prompt=system_prompt,
                success=False,
                final_model=first_id,
                hops_used=hops,
                reason="final_failure",
                error=last_error,
                extra={"workspace_id": workspace_id},  # ✅ WORKSPACE via extra
            )
        )
        return LLMResponse(
            content="",
            model="",
            mode=mode.value,
            cached=False,
            error=f"All models failed. Last: {last_error}",
            latency_ms=latency,
            attempts=len(candidates),
        )

    def get_stats(self) -> Dict[str, Any]:
        return {
            "metrics": self.metrics.stats.to_dict(),
            "budget": self.metrics.check_budget(),
            "cache_size": len(self.cache._cache),
        }

    def clear_cache(self):
        self.cache.clear()
        logger.info("Router cache cleared")

    def reset_metrics(self):
        self.metrics.reset_stats()
        logger.info("Router metrics reset")


_router_instance: Optional[LLMRouter] = None


def get_router() -> LLMRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = LLMRouter()
    return _router_instance


def normalize_router_mode(mode: Union[str, RouterMode, None]) -> RouterMode:
    if isinstance(mode, RouterMode):
        return mode
    if isinstance(mode, str):
        mode_l = mode.lower()
        # алиас для старого vision-режима
        if mode_l == "vision":
            logger.warning("Alias mode 'vision' mapped to CORE")
            return RouterMode.CORE
        try:
            return RouterMode(mode_l)
        except ValueError:
            logger.warning(f"Unknown mode '{mode}', fallback to CORE")
            return RouterMode.CORE
    return RouterMode.CORE


def call_llm(
    prompt: str,
    system_prompt: str = "",
    mode: Union[str, RouterMode, None] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    workspace_id: Optional[str] = None,  # 🆕 WORKSPACE
    **kwargs,
) -> Dict[str, Any]:
    router = get_router()
    # ✅ Не ломаем implicit auto-routing: None остаётся None
    safe_mode = normalize_router_mode(mode) if mode is not None else None

    response = router.call(
        prompt=prompt,
        system_prompt=system_prompt,
        mode=safe_mode,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        workspace_id=workspace_id,  # 🆕 WORKSPACE
        force_refresh=kwargs.pop("force_refresh", False),
        **kwargs,
    )
    if response.error:
        raise RuntimeError(response.error)
    return {
        "content": response.content,
        "model": response.model,
        "usage": response.usage,
        "cached": response.cached,
        "latency_ms": response.latency_ms,
        "cost_usd": response.cost_usd,
        "mode": response.mode,
        "attempts": response.attempts,
    }


if __name__ == "__main__":
    router = LLMRouter()
    print("🔍 Budget:", router.metrics.check_budget())
    if OPENROUTER_KEY:
        res = router.call(
            "Explain quantum entanglement in one sentence.",
            mode="core",
            force_refresh=True,
            workspace_id="test_ws_001",  # 🆕 WORKSPACE: smoke test
        )
        if res.error:
            print(f"❌ {res.error}")
        else:
            print(
                f"✅ {res.model} ({res.attempts} hops): {res.content[:80]}..."
            )
    else:
        print(
            "⚠️ OPENROUTER_KEY not set. Skipping API call (syntax/config check passed)."
        )
