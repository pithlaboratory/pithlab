import json
import time
import uuid
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, asdict, field


logger = logging.getLogger(__name__)


TRACE_DIR = Path("data/traces")
LLM_CALLS_PATH = TRACE_DIR / "llm_calls.jsonl"
ROUTER_DECISIONS_PATH = TRACE_DIR / "router_decisions.jsonl"


def _iso_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def hash_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()[:16]


def _write_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
            f.flush()
    except Exception as e:
        logger.warning(f"Trace write failed ({path}): {e}")


@dataclass
class LLMCallTrace:
    trace_id: str
    timestamp: str
    schema_version: str = "v1"
    kind: str = "llm_call"

    agent: str = "unknown"
    session_id: Optional[str] = None
    task_id: Optional[str] = None

    model: str = ""
    mode: str = ""
    provider: str = "openrouter"

    prompt_hash: str = ""
    system_prompt_hash: str = ""
    prompt_chars: int = 0
    system_prompt_chars: int = 0

    cached: bool = False
    success: bool = False
    attempts: int = 0
    latency_ms: float = 0.0

    usage: Dict[str, Any] = field(default_factory=dict)
    cost_usd: float = 0.0

    error: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RouterDecisionTrace:
    trace_id: str
    timestamp: str
    schema_version: str = "v1"
    kind: str = "router_decision"

    agent: str = "unknown"
    session_id: Optional[str] = None
    task_id: Optional[str] = None

    mode: str = ""
    explicit_mode: bool = False
    provider: str = "openrouter"

    selected_models: List[str] = field(default_factory=list)
    selected_roles: List[str] = field(default_factory=list)

    prefer_free_first: bool = True
    budget_status: str = "ok"
    budget_spent_usd: float = 0.0
    budget_limit_usd: float = 0.0

    prompt_hash: str = ""
    system_prompt_hash: str = ""
    prompt_chars: int = 0
    system_prompt_chars: int = 0

    success: bool = False
    final_model: str = ""
    hops_used: int = 0
    reason: str = ""
    error: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def make_llm_call_trace(
    *,
    agent: str = "unknown",
    session_id: Optional[str] = None,
    task_id: Optional[str] = None,
    model: str = "",
    mode: str = "",
    provider: str = "openrouter",
    prompt: str = "",
    system_prompt: str = "",
    cached: bool = False,
    success: bool = False,
    attempts: int = 0,
    latency_ms: float = 0.0,
    usage: Optional[Dict[str, Any]] = None,
    cost_usd: float = 0.0,
    error: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> LLMCallTrace:
    return LLMCallTrace(
        trace_id=str(uuid.uuid4()),
        timestamp=_iso_now(),
        agent=agent or "unknown",
        session_id=session_id,
        task_id=task_id,
        model=model,
        mode=mode,
        provider=provider,
        prompt_hash=hash_text(prompt),
        system_prompt_hash=hash_text(system_prompt),
        prompt_chars=len(prompt or ""),
        system_prompt_chars=len(system_prompt or ""),
        cached=cached,
        success=success,
        attempts=attempts,
        latency_ms=round(latency_ms, 2),
        usage=usage or {},
        cost_usd=round(cost_usd or 0.0, 6),
        error=error,
        extra=extra or {},
    )


def make_router_decision_trace(
    *,
    agent: str = "unknown",
    session_id: Optional[str] = None,
    task_id: Optional[str] = None,
    mode: str = "",
    explicit_mode: bool = False,
    provider: str = "openrouter",
    selected_models: Optional[List[str]] = None,
    selected_roles: Optional[List[str]] = None,
    prefer_free_first: bool = True,
    budget_status: str = "ok",
    budget_spent_usd: float = 0.0,
    budget_limit_usd: float = 0.0,
    prompt: str = "",
    system_prompt: str = "",
    success: bool = False,
    final_model: str = "",
    hops_used: int = 0,
    reason: str = "",
    error: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> RouterDecisionTrace:
    return RouterDecisionTrace(
        trace_id=str(uuid.uuid4()),
        timestamp=_iso_now(),
        agent=agent or "unknown",
        session_id=session_id,
        task_id=task_id,
        mode=mode,
        explicit_mode=explicit_mode,
        provider=provider,
        selected_models=selected_models or [],
        selected_roles=selected_roles or [],
        prefer_free_first=prefer_free_first,
        budget_status=budget_status,
        budget_spent_usd=round(budget_spent_usd or 0.0, 6),
        budget_limit_usd=round(budget_limit_usd or 0.0, 6),
        prompt_hash=hash_text(prompt),
        system_prompt_hash=hash_text(system_prompt),
        prompt_chars=len(prompt or ""),
        system_prompt_chars=len(system_prompt or ""),
        success=success,
        final_model=final_model,
        hops_used=hops_used,
        reason=reason,
        error=error,
        extra=extra or {},
    )


def record_trace(trace: Union[LLMCallTrace, RouterDecisionTrace], path: Optional[Path] = None) -> None:
    if path is None:
        if isinstance(trace, LLMCallTrace):
            path = LLM_CALLS_PATH
        elif isinstance(trace, RouterDecisionTrace):
            path = ROUTER_DECISIONS_PATH
        else:
            logger.warning(f"Unsupported trace type: {type(trace).__name__}")
            return
    _write_jsonl(path, trace.to_dict())


def record_llm_call(trace: LLMCallTrace, path: Path = LLM_CALLS_PATH) -> None:
    record_trace(trace, path)


def record_router_decision(trace: RouterDecisionTrace, path: Path = ROUTER_DECISIONS_PATH) -> None:
    record_trace(trace, path)