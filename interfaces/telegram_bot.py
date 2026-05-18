"""
Pith v5 — Telegram Interface
Author: Pith Lab
License: MIT
Status: L0/L1 autonomy enforced | Kernel-compliant | Trace-ready | Workspace-aware (Phase 1.1)
"""

# === ENV LOADING: MUST BE FIRST (before any core imports) ===
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    _env_path = Path(__file__).resolve().parent.parent / ".env"
    if _env_path.exists():
        with open(_env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())
except Exception:
    pass

# === UNICODE HOTFIX ===
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ.setdefault("LANG", "ru_RU.UTF-8")
os.environ.setdefault("LC_ALL", "ru_RU.UTF-8")

import sys
import inspect
import uuid
import re  # ✅ Added for governance regex guards

try:
    enc_out = getattr(sys.stdout, "encoding", None)
    if isinstance(enc_out, str) and enc_out.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    enc_err = getattr(sys.stderr, "encoding", None)
    if isinstance(enc_err, str) and enc_err.lower() != "utf-8":
        sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, UnicodeError):
    pass

import asyncio
import contextlib
import logging
import time
from typing import Any, Dict, List, Optional

import yaml
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.error import Conflict, NetworkError, TimedOut
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.request import HTTPXRequest

# --- PATHS / IMPORTS ---
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.memory.manager import get_memory
from core.runtime.planner import RuntimePlanner, RuntimeMode
from core.evolution.evaluator import evaluator
from core.secrets import TG_TOKEN
from core.schemas import TaskState
from core.services.task_service import TaskService
from core.services.artifact_service import ArtifactService

# Optional trace service
try:
    from core.governance.trace_service import TraceService
    trace_service = TraceService()
except ImportError:
    trace_service = None
except Exception:
    trace_service = None

# Optional tool registry
try:
    from core.tool_plane import ToolRegistry
except ImportError:
    ToolRegistry = None

# Budget check via router (correct import)
try:
    from core.cognition.router import get_router
    router_available = True
except ImportError:
    router_available = False

# === CONSTANTS ===
MAX_INPUT_CHARS_DEFAULT = 8000

# === LOGGING ===
logging_kwargs = {
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "level": logging.INFO,
}
if sys.version_info >= (3, 9):
    logging_kwargs["encoding"] = "utf-8"

logging.basicConfig(**logging_kwargs)
logger = logging.getLogger(__name__)

if trace_service is None:
    logger.warning("TraceService not found — tracing disabled (non-critical)")

# === CONFIG ===
CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f) or {}

INTERFACE_CFG = config.get("interface", {}) or {}
PERSONA_CFG = config.get("persona", {}) or {}
SYSTEM_MSG_CFG = INTERFACE_CFG.get("system_messages", {}) or {}
GOVERNANCE_CFG = config.get("governance", {}) or {}
BUDGET_CFG = GOVERNANCE_CFG.get("cognitive_budget", {}) or {}

MAX_INPUT_CHARS = BUDGET_CFG.get("max_input_chars", MAX_INPUT_CHARS_DEFAULT)

SHOW_PREFIX = INTERFACE_CFG.get("show_prefix", True)
PREFIX_TEXT = INTERFACE_CFG.get("prefix_text", PERSONA_CFG.get("name", "Pith"))
SYSTEM_PROMPT = PERSONA_CFG.get("system_prompt", "")

KNOWN_PREFIXES = INTERFACE_CFG.get(
    "known_prefixes_to_strip",
    ["🎭 Viktor Vaughn:", "Viktor Vaughn:", "Pith:", "pith:", "PITH:"],
)

VOICE_MODE = INTERFACE_CFG.get("voice_mode", "runtime")
RUNTIME_ONLY_PREFIXES = ["🎭 Viktor Vaughn:", "Viktor Vaughn:", "Pith:", "pith:", "PITH:"]

TOKEN = TG_TOKEN

# === LOADING LOOP CONFIG ===
DEFAULT_LOADING_STATES = [
    "pith is in flow…",
    "mapping context…",
    "shaping response…",
    "locking final output…",
]
DEFAULT_LOADING_STEP_DELAYS = [2.4, 5.8, 9.5]
DEFAULT_TYPING_PULSE_SEC = 3.5

_loading_profile = INTERFACE_CFG.get("loading_profile", "default")
_loading_states_cfg = INTERFACE_CFG.get("loading_states", {}) or {}

PITH_LOADING_STATES = _loading_states_cfg.get(
    _loading_profile,
    _loading_states_cfg.get("default", DEFAULT_LOADING_STATES),
)
PITH_LOADING_STEP_DELAYS = INTERFACE_CFG.get(
    "loading_step_delays",
    DEFAULT_LOADING_STEP_DELAYS,
)
PITH_TYPING_PULSE_SEC = float(
    INTERFACE_CFG.get("typing_pulse_sec", DEFAULT_TYPING_PULSE_SEC)
)

if len(PITH_LOADING_STATES) < 2:
    logger.warning("Invalid loading states config, using defaults")
    PITH_LOADING_STATES = DEFAULT_LOADING_STATES[:]

if len(PITH_LOADING_STEP_DELAYS) != len(PITH_LOADING_STATES) - 1:
    logger.warning(
        "PITH_LOADING_STEP_DELAYS should be len(states)-1, got %d vs %d",
        len(PITH_LOADING_STEP_DELAYS),
        len(PITH_LOADING_STATES) - 1,
    )
    needed = max(0, len(PITH_LOADING_STATES) - 1)
    PITH_LOADING_STEP_DELAYS = (
        DEFAULT_LOADING_STEP_DELAYS * (needed // 3 + 1)
    )[:needed]

# === SYSTEM MESSAGES ===
def _fmt_sys(text: str) -> str:
    if SHOW_PREFIX and PREFIX_TEXT:
        return f"{PREFIX_TEXT}: {text}"
    return text


MSG_START = _fmt_sys(
    SYSTEM_MSG_CFG.get(
        "start",
        "Pith active.\n\nSend a task, idea, log, or code fragment.",
    )
)
MSG_EMPTY = _fmt_sys(
    SYSTEM_MSG_CFG.get(
        "empty",
        "No input received.\n\nSend a task, idea, log, or code fragment.",
    )
)
MSG_MODEL_UNAVAILABLE = _fmt_sys(
    SYSTEM_MSG_CFG.get(
        "model_unavailable",
        "Model access unavailable.\n\nCheck runtime configuration.",
    )
)
MSG_ORCHESTRATION_FAILED = _fmt_sys(
    SYSTEM_MSG_CFG.get(
        "orchestration_failed",
        "Execution failed at orchestration stage.\n\nReview agent configuration.",
    )
)
MSG_REQUEST_FAILED = _fmt_sys(
    SYSTEM_MSG_CFG.get(
        "request_failed",
        "Pith could not complete this request. The runtime will review logs and improve.\n\nTry rephrasing or sending a smaller fragment.",
    )
)
MSG_SEARCH_USAGE = _fmt_sys(
    SYSTEM_MSG_CFG.get(
        "search_usage",
        "Pith search:\n/search [basic|advanced] <query>",
    )
)
MSG_SEARCH_FAILED = _fmt_sys(
    SYSTEM_MSG_CFG.get(
        "search_failed",
        "Search failed.\n\nReview runtime logs.",
    )
)
MSG_ABOUT = _fmt_sys(
    SYSTEM_MSG_CFG.get(
        "about",
        "Pith is an operational AI runtime.\n\n"
        "It works across architecture, code, analysis, planning, and experiments.\n"
        "Use it to move real work forward, not just to chat.",
    )
)
MSG_BUDGET_WARNING = _fmt_sys(
    "⚠️ Budget warning: spending limit approaching. Switching to cost-optimized models."
)

# === TELEGRAM GOVERNANCE GUARDS ===
TELEGRAM_DANGEROUS_DELETE_REPLY = _fmt_sys(
    "Я не могу удалить все ваши задачи, данные или историю диалогов через Telegram.\n\n"
    "Такие действия требуют отдельного подтверждения и безопасного интерфейса с более высоким уровнем доступа.\n\n"
    "Я могу помочь безопасно:\n"
    "• уточнить, что именно вы хотите удалить или изменить;\n"
    "• подготовить список на удаление для подтверждения;\n"
    "• подсказать, где это делается через подходящий интерфейс."
)

TELEGRAM_DANGEROUS_DELETE_PATTERNS = [
    re.compile(r"\bудали\b.*\b(все|всё)\b.*\b(задач\w*|данн\w*|истори\w*|диалог\w*)\b", re.IGNORECASE),
    re.compile(r"\bудали\b.*\b(истори\w*|диалог\w*|данн\w*)\b", re.IGNORECASE),
    re.compile(r"\bсотри\b.*\b(все|всё)\b.*\b(задач\w*|данн\w*|истори\w*|диалог\w*)\b", re.IGNORECASE),
    re.compile(r"\bочисти\b.*\b(все|всё)\b.*\b(задач\w*|данн\w*|истори\w*|диалог\w*)\b", re.IGNORECASE),
    re.compile(r"\bdelete\b.*\b(all|everything|tasks?|data|history)\b", re.IGNORECASE),
    re.compile(r"\berase\b.*\b(all|everything|tasks?|data|history)\b", re.IGNORECASE),
    re.compile(r"\bremove\b.*\b(all|everything|tasks?|data|history)\b", re.IGNORECASE),
]


def is_telegram_dangerous_delete_request(text: str) -> bool:
    if not text:
        return False

    normalized = " ".join(str(text).split()).strip()
    if not normalized:
        return False

    return any(pattern.search(normalized) for pattern in TELEGRAM_DANGEROUS_DELETE_PATTERNS)


async def maybe_handle_governance_refusal(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
) -> bool:
    if not update.message or not update.effective_user or not update.effective_chat:
        return False

    if not is_telegram_dangerous_delete_request(text):
        return False

    user_id = str(update.effective_user.id)
    chat_id = update.effective_chat.id

    logger.warning(
        "GOVERNANCE_REFUSAL telegram dangerous_delete user=%s chat=%s text=%r",
        user_id,
        chat_id,
        text[:500],
    )

    await send_typing_safe(context, chat_id)
    await safe_reply(update.message, TELEGRAM_DANGEROUS_DELETE_REPLY)
    return True


# === CORE RUNTIME BINDINGS ===
memory = get_memory()
artifact_service = ArtifactService()

try:
    sig = inspect.signature(TaskService.__init__)
    if "memory_manager" in sig.parameters and "artifact_service" in sig.parameters:
        task_service = TaskService(memory_manager=memory, artifact_service=artifact_service)
    else:
        logger.warning("TaskService uses legacy signature — initializing without services")
        task_service = TaskService()
except Exception as e:
    logger.error(f"TaskService init failed: {e}")
    task_service = TaskService()

planner = RuntimePlanner(
    memory_manager=memory,
    system_prompt=SYSTEM_PROMPT,
    artifact_service=artifact_service,
    task_service=task_service,
)


def get_default_workspace_id_for_user(user_id: str) -> str:
    return f"ws_tg_{user_id}"


def enforce_voice_mode(text: str) -> str:
    if VOICE_MODE != "runtime":
        return text
    for prefix in RUNTIME_ONLY_PREFIXES:
        if text.startswith(prefix):
            return text[len(prefix):].lstrip()
    return text


def format_response_with_prefix(text: str, strip_known_prefixes: bool = True) -> str:
    if not text:
        return text
    if strip_known_prefixes or VOICE_MODE == "runtime":
        for known in KNOWN_PREFIXES:
            if text.startswith(known):
                text = text[len(known):].lstrip()
                break
    return enforce_voice_mode(text) if VOICE_MODE == "runtime" else text


# ✅ NEW: Filter internal runtime markers from user-visible output
INTERNAL_RUNTIME_PREFIXES = (
    "SKIP:",
    "TOOL_SKIP:",
    "ROUTER_SKIP:",
    "SEARCH_SKIP:",
    "MEMORY_SKIP:",
)


def strip_internal_runtime_lines(text: str) -> str:
    """Remove internal orchestration/debug lines from user-facing response."""
    if not text:
        return text

    cleaned_lines: List[str] = []
    for line in str(text).splitlines():
        stripped = line.strip()
        if any(stripped.startswith(prefix) for prefix in INTERNAL_RUNTIME_PREFIXES):
            logger.warning("Dropping internal runtime line from Telegram output: %s", stripped)
            continue
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def normalize_user_visible_response(text: str) -> str:
    """Apply all user-facing normalizations: prefix strip + internal marker filter."""
    text = format_response_with_prefix(text, strip_known_prefixes=True)
    text = strip_internal_runtime_lines(text)
    return text.strip()


def detect_runtime_mode_ui(text: str) -> RuntimeMode:
    text_lower = text.lower()
    meta_keywords = {
        "архитектура", "эволюция", "roadmap", "self-analysis",
        "план развития", "как нам приблизиться", "твои мысли",
    }
    if any(k in text_lower for k in meta_keywords):
        return RuntimeMode.VISION
    diagnostic_keywords = {
        "сломалось", "баг", "ошибка", "фикс", "traceback",
        "не работает", "падает", "исправить", "debug",
    }
    if any(k in text_lower for k in diagnostic_keywords):
        return RuntimeMode.DIAGNOSTICS
    return RuntimeMode.NORMAL


def compute_goal_tags(runtime_mode: RuntimeMode) -> List[str]:
    goal_tags: List[str] = []
    if runtime_mode == RuntimeMode.DIAGNOSTICS:
        goal_tags.append("g_tactical_self_diagnostics")
    return goal_tags


def feedback_keyboard(task_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("👍", callback_data=f"fb:{task_id}:up"),
            InlineKeyboardButton("👎", callback_data=f"fb:{task_id}:down"),
        ]]
    )


def fmt_loading(text: str) -> str:
    return f"⋯ {text}"


async def send_typing_safe(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    except Exception as e:
        logger.debug("Failed to send typing action: %s", e)


async def safe_reply(message, text, reply_markup=None, retries: int = 3):
    try:
        text = str(text).encode("utf-8", errors="replace").decode("utf-8")
    except Exception:
        text = str(text)
    for attempt in range(retries):
        try:
            return await message.reply_text(text, reply_markup=reply_markup)
        except (NetworkError, TimedOut) as e:
            if attempt == retries - 1:
                raise
            logger.warning("Reply failed (attempt %d/%d): %s", attempt + 1, retries, e)
            await asyncio.sleep(2 ** attempt)
        except UnicodeEncodeError as e:
            logger.error("Unicode error in reply: %s", e)
            text = text.encode("ascii", errors="replace").decode("ascii")
            return await message.reply_text(text, reply_markup=reply_markup)
    return None


async def safe_callback_reply(query, text, reply_markup=None, retries: int = 3):
    if not query or not query.message:
        return None
    try:
        text = str(text).encode("utf-8", errors="replace").decode("utf-8")
    except Exception:
        text = str(text)
    for attempt in range(retries):
        try:
            return await query.message.reply_text(text, reply_markup=reply_markup)
        except (NetworkError, TimedOut) as e:
            if attempt == retries - 1:
                raise
            logger.warning("Callback reply failed (attempt %d/%d): %s", attempt + 1, retries, e)
            await asyncio.sleep(2 ** attempt)
        except UnicodeEncodeError as e:
            logger.error("Unicode error in callback reply: %s", e)
            text = text.encode("ascii", errors="replace").decode("ascii")
            return await query.message.reply_text(text, reply_markup=reply_markup)
    return None


async def send_loading_placeholder(message, text: str):
    try:
        return await safe_reply(message, fmt_loading(text))
    except Exception as e:
        logger.debug("Failed to send loading placeholder: %s", e)
        return None


async def edit_loading_placeholder(msg, text: str) -> bool:
    if not msg:
        return False
    try:
        await msg.edit_text(fmt_loading(text))
        return True
    except Exception as e:
        logger.debug("Failed to edit loading placeholder: %s", e)
        return False


async def pith_loading_loop(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    loading_msg,
    stop_event: asyncio.Event,
):
    started = asyncio.get_running_loop().time()
    next_typing_at = started + PITH_TYPING_PULSE_SEC
    phase_index = 1
    while not stop_event.is_set():
        now = asyncio.get_running_loop().time()
        elapsed = now - started
        if phase_index < len(PITH_LOADING_STATES):
            trigger_at = PITH_LOADING_STEP_DELAYS[phase_index - 1]
            if elapsed >= trigger_at:
                await edit_loading_placeholder(loading_msg, PITH_LOADING_STATES[phase_index])
                phase_index += 1
        if now >= next_typing_at:
            await send_typing_safe(context, chat_id)
            next_typing_at = now + PITH_TYPING_PULSE_SEC
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=0.35)
        except asyncio.TimeoutError:
            continue


# === GLOBAL ERROR HANDLER ===
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    err = context.error
    if isinstance(err, Conflict):
        logger.error(
            "Telegram polling conflict: another bot instance is using getUpdates. Ensure only one process runs with this token.",
            exc_info=err,
        )
        return
    if isinstance(err, TimedOut):
        logger.warning("Telegram timeout, likely transient network issue", exc_info=err)
        return
    try:
        logger.error("Unhandled exception in Telegram handler", exc_info=err)
    except UnicodeEncodeError:
        logger.error(
            "Unhandled exception (ASCII fallback): %s",
            str(err).encode("ascii", errors="replace").decode("ascii"),
        )
    try:
        if isinstance(update, Update) and update.effective_message:
            await safe_reply(
                update.effective_message,
                format_response_with_prefix(MSG_REQUEST_FAILED, strip_known_prefixes=False),
            )
    except Exception as e:
        logger.debug("Failed to send error notification to user: %s", e)


# === HANDLERS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    await send_typing_safe(context, update.effective_chat.id)
    await safe_reply(update.message, MSG_START)


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    await send_typing_safe(context, update.effective_chat.id)
    await safe_reply(update.message, MSG_ABOUT)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return

    user_id = str(update.effective_user.id)
    text = (update.message.text or "").strip()

    if not text:
        await safe_reply(update.message, MSG_EMPTY)
        return

    # ✅ Governance guard: block dangerous delete requests via Telegram
    if await maybe_handle_governance_refusal(update, context, text):
        return

    if len(text) > MAX_INPUT_CHARS:
        await safe_reply(
            update.message,
            format_response_with_prefix(
                f"Input is too long ({len(text)} chars). Please send up to {MAX_INPUT_CHARS} characters or split it into parts.",
                strip_known_prefixes=False,
            ),
        )
        return

    workspace_id = get_default_workspace_id_for_user(user_id)
    session_id = f"tg_{update.effective_chat.id}"
    trace_id = str(uuid.uuid4())

    # 🔍 TRACE_DEBUG: log generated trace_id
    logger.info(
        "TRACE_DEBUG: generated trace_id=%s for user=%s chat=%s",
        trace_id,
        user_id,
        update.effective_chat.id if update.effective_chat else None,
    )

    if router_available:
        try:
            router = get_router()
            metrics = getattr(router, "metrics", None)
            if metrics and hasattr(metrics, "check_budget"):
                budget_status = metrics.check_budget()
                if isinstance(budget_status, dict) and budget_status.get("status") == "warning":
                    await safe_reply(update.message, MSG_BUDGET_WARNING)
        except Exception as e:
            logger.debug("Budget check skipped: %s", e)

    # 🔍 TRACE_DEBUG: log before calling create_task
    logger.info(
        "TRACE_DEBUG: calling create_task with trace_id=%s (task_service=%r)",
        trace_id,
        task_service,
    )

    # ✅ FIX: Pass trace_id to TaskService for correlation
    task = task_service.create_task(
        workspace_id=workspace_id,
        user_id=user_id,
        source_interface="telegram",
        input_text=text,
        trace_id=trace_id,
    )
    task_id = task.task_id

    logger.info(
        "📩 %s (task %s, trace %s, ws %s): %s",
        user_id,
        task_id,
        trace_id,
        workspace_id,
        text[:100],
    )

    # ✅ trace_id only in metadata, not as separate kwarg (MemoryManager compatibility)
    memory.save_episode(
        user_id=user_id,
        role="user",
        content=text,
        workspace_id=workspace_id,
        metadata={
            "task_id": task_id,
            "trace_id": trace_id,
            "channel": "telegram",
            "workspace_id": workspace_id,
        },
    )

    task_service.update_status(task_id, TaskState.executing)

    chat_id = update.effective_chat.id
    await send_typing_safe(context, chat_id)
    loading_msg = await send_loading_placeholder(update.message, PITH_LOADING_STATES[0])

    stop_loading = asyncio.Event()
    loading_task = asyncio.create_task(
        pith_loading_loop(context, chat_id, loading_msg, stop_loading)
    )

    try:
        start_ts = time.perf_counter()

        ui_mode_hint = detect_runtime_mode_ui(text)

        # ✅ FIX: Pass trace_id to Planner for correlation
        result = await planner.plan_and_answer(
            user_id=user_id,
            text=text,
            workspace_id=workspace_id,
            task_id=task_id,
            session_id=session_id,
            trace_id=trace_id,
        )

        if not isinstance(result, dict):
            raise TypeError(
                f"planner.plan_and_answer must return dict, got {type(result).__name__}"
            )

        trace_id = result.get("trace_id") or trace_id

        latency_ms = int((time.perf_counter() - start_ts) * 1000)
        runtime_mode_str = result.get("runtime_mode", ui_mode_hint.value)
        task_type = result.get("task_type", "general")
        goal_tags = result.get("goal_tags", compute_goal_tags(ui_mode_hint))

        logger.debug(
            "Planner result: task=%s, trace=%s, model=%s, cost=%.4f, latency=%dms, mode=%s, task_type=%s",
            task_id,
            trace_id,
            result.get("model_id", "unknown"),
            result.get("cost", 0.0),
            latency_ms,
            runtime_mode_str,
            task_type,
        )

        if trace_service is not None:
            try:
                trace_service.record(
                    task_id=task_id,
                    workspace_id=workspace_id,
                    semantic=f"User query → planner(mode={runtime_mode_str}, task_type={task_type}) → response ({latency_ms}ms)",
                    raw={
                        "trace_id": trace_id,
                        "model_id": result.get("model_id"),
                        "model_name": result.get("model_name"),
                        "tokens_prompt": result.get("tokens_prompt", 0),
                        "tokens_completion": result.get("tokens_completion", 0),
                        "cost_usd": result.get("cost", 0.0),
                        "context_used": result.get("context_used"),
                        "used_orchestrator": result.get("used_orchestrator", False),
                        "runtime_mode": runtime_mode_str,
                        "task_type": task_type,
                        "goal_tags": goal_tags,
                    },
                    event_type="task_completed",
                )
            except Exception as e:
                logger.debug("Trace recording skipped: %s", e)

    except Exception as e:
        logger.exception("Planner failed")
        task_service.update_status(task_id, TaskState.failed, error_message=str(e))

        if trace_service is not None:
            try:
                trace_service.record(
                    task_id=task_id,
                    workspace_id=workspace_id,
                    semantic=f"Task failed: {type(e).__name__}",
                    raw={
                        "trace_id": trace_id,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                    event_type="task_failed",
                )
            except Exception as te:
                logger.debug("Error trace recording skipped: %s", te)

        msg = str(e).lower()
        if "authentication" in msg or "401" in msg or "missing authentication" in msg:
            error_text = MSG_MODEL_UNAVAILABLE
        elif "orchestrator" in msg or "agents." in msg or "tera" in msg:
            error_text = MSG_ORCHESTRATION_FAILED
        else:
            error_text = MSG_REQUEST_FAILED

        edited_err = False
        if loading_msg:
            with contextlib.suppress(Exception):
                await loading_msg.edit_text(error_text)
                edited_err = True

        if not edited_err:
            await safe_reply(update.message, error_text)
        return

    finally:
        stop_loading.set()
        loading_task.cancel()
        try:
            await loading_task
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.debug("Loading task cleanup error: %s", e)

    # ✅ FIXED: Filter internal runtime markers from user-visible response
    raw_response = result.get("response", "")
    prefixed_response = format_response_with_prefix(raw_response, strip_known_prefixes=True)
    response = normalize_user_visible_response(raw_response)
    internal_markers_stripped = response != prefixed_response
    final_text = (response or MSG_REQUEST_FAILED)[:4000]

    edited = False
    if loading_msg:
        with contextlib.suppress(Exception):
            await loading_msg.edit_text(
                final_text,
                reply_markup=feedback_keyboard(task_id),
            )
            edited = True

    if not edited:
        await safe_reply(
            update.message,
            final_text,
            reply_markup=feedback_keyboard(task_id),
        )

    try:
        # ✅ FIXED: removed execution_path (not in evaluator signature)
        eval_kwargs = {
            "task_id": task_id,
            "user_id": user_id,
            "response": raw_response,
            "model": result.get("model_id", "unknown"),
            "tokens": result.get("tokens_prompt", 0) + result.get("tokens_completion", 0),
            "cost": result.get("cost", 0.0),
            "user_feedback": None,
            "context_used": result.get("context_used"),
        }

        sig = inspect.signature(evaluator.evaluate_response)
        if "task_type" in sig.parameters:
            eval_kwargs["task_type"] = task_type

        eval_result = evaluator.evaluate_response(**eval_kwargs)

        # ✅ Enrich eval blob to full EvaluationRecord v1 traceability contract
        eval_result["trace_id"] = trace_id
        eval_result["workspace_id"] = workspace_id
        eval_result["task_id"] = task_id
        eval_result["cost_per_workflow"] = result.get("cost", 0.0)
        eval_result["failure_class"] = eval_result.get("failure_class")
        eval_result["runtime_mode"] = runtime_mode_str
        eval_result["task_type"] = task_type
        eval_result["workflow_type"] = eval_result.get("workflow_type") or task_type

        # ✅ trace_id only in metadata, not as separate kwarg (MemoryManager compatibility)
        memory.save_episode(
            user_id=user_id,
            role="assistant",
            content=raw_response,  # keep raw for diagnostics
            workspace_id=workspace_id,
            metadata={
                "workspace_id": workspace_id,
                "task_id": task_id,
                "trace_id": trace_id,
                "channel": "telegram",
                "model_id": result.get("model_id"),
                "model_name": result.get("model_name"),
                "tokens_prompt": result.get("tokens_prompt"),
                "tokens_completion": result.get("tokens_completion"),
                "cost": result.get("cost"),
                "used_orchestrator": result.get("used_orchestrator", False),
                "context_used": result.get("context_used"),
                "execution_path": result.get("execution_path", "direct"),
                "eval": eval_result,
                "runtime_mode": runtime_mode_str,
                "task_type": task_type,
                "goal_tags": goal_tags,
                "internal_markers_stripped": internal_markers_stripped,  # ✅ observability flag
            },
        )
    except Exception as e:
        logger.warning("Non-critical error in eval/memory: %s", e, exc_info=True)

    # ✅ CORRECT ORDER: attach_execution_result BEFORE update_status(completed)
    task_service.attach_execution_result(
        task_id=task_id,
        model_id=result.get("model_id"),
        model_name=result.get("model_name"),
        model_lane=None,
        cost_usd=result.get("cost", 0.0),
        tokens_prompt=result.get("tokens_prompt", 0),
        tokens_completion=result.get("tokens_completion", 0),
        latency_ms=latency_ms,
        trace_id=trace_id,  # ✅ Added for full consistency
    )
    task_service.update_status(task_id, TaskState.completed)


async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик фидбека (👍/👎) — тихое подтверждение, лог для наблюдаемости."""
    query = update.callback_query
    if not query or not query.data:
        return
    
    await query.answer()
    
    parts = query.data.split(":")
    if len(parts) != 3 or parts[0] != "fb":
        return
    _, task_id, vote = parts
    if not update.effective_user:
        return
    
    user_id = str(update.effective_user.id)
    feedback_value = "positive" if vote == "up" else "negative"
    
    try:
        evaluator.record_user_feedback(
            task_id=task_id,
            feedback=feedback_value,
            reason=None,
        )
    except Exception as e:
        logger.warning("Non-critical error in feedback/evaluator: %s", e, exc_info=True)
    
    try:
        finder = getattr(memory, "find_episode_by_task_id", None)
        if callable(finder):
            episode = finder(user_id, task_id, role="assistant")
            if episode:
                metadata = episode.get("metadata", {}) or {}
                eval_data = metadata.get("eval", {}) or {}

                # ✅ Обновляем user_feedback
                eval_data["user_feedback"] = feedback_value

                # ✅ Синхронизируем human_override для EvaluationRecord v1
                if feedback_value == "negative":
                    eval_data["human_override"] = "minor_correction"
                else:
                    eval_data["human_override"] = "none"

                metadata["eval"] = eval_data
                memory.update_episode_metadata(episode["id"], metadata)
    except Exception as e:
        logger.debug("Fallback memory update failed: %s", e)
    
    with contextlib.suppress(Exception):
        await query.edit_message_reply_markup(reply_markup=None)
    
    logger.info("👍👎 Feedback recorded: %s (task %s, user %s)", feedback_value, task_id, user_id)


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not context.args:
        await safe_reply(update.message, MSG_SEARCH_USAGE)
        return
    args = list(context.args)
    depth = "basic"
    if args and args[0].lower() in ("basic", "advanced"):
        depth = args.pop(0).lower()
    if not args:
        await safe_reply(update.message, MSG_SEARCH_USAGE)
        return
    query = " ".join(args)
    await send_typing_safe(context, update.effective_chat.id)
    try:
        if ToolRegistry is not None:
            results = await ToolRegistry.execute(
                tool_name="web_search",
                params={"query": query, "search_depth": depth},
                workspace_id=get_default_workspace_id_for_user(str(update.effective_user.id)),
            )
            reply = results.get("formatted", str(results)) if isinstance(results, dict) else str(results)
        else:
            reply = "Search tool not available in this build."
        await safe_reply(
            update.message,
            format_response_with_prefix(reply, strip_known_prefixes=False)[:4000],
        )
    except Exception:
        logger.exception("Search command failed")
        await safe_reply(update.message, MSG_SEARCH_FAILED)


# === CONFIG VALIDATION ===
def _validate_interface_config() -> bool:
    if not isinstance(SHOW_PREFIX, bool):
        logger.error("interface.show_prefix must be boolean")
        return False
    if PREFIX_TEXT is not None and not isinstance(PREFIX_TEXT, str):
        logger.error("interface.prefix_text must be string or null")
        return False
    if not isinstance(KNOWN_PREFIXES, list) or not all(isinstance(p, str) for p in KNOWN_PREFIXES):
        logger.error("interface.known_prefixes_to_strip must be list of strings")
        return False
    if SYSTEM_MSG_CFG and not isinstance(SYSTEM_MSG_CFG, dict):
        logger.error("interface.system_messages must be a mapping")
        return False
    loading_states = INTERFACE_CFG.get("loading_states", {})
    if loading_states and not isinstance(loading_states, dict):
        logger.error("interface.loading_states must be a mapping")
        return False
    if VOICE_MODE not in ("runtime", "persona"):
        logger.error("interface.voice_mode must be 'runtime' or 'persona'")
        return False
    return True


# === ENTRY POINT ===
def build_application() -> Application:
    request = HTTPXRequest(
        connect_timeout=15.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=15.0,
    )
    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .request(request)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CallbackQueryHandler(handle_feedback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    return app


if __name__ == "__main__":
    if not _validate_interface_config():
        logger.error("Interface config validation failed. Exiting.")
        sys.exit(1)
    app = build_application()
    logger.info(
        "Pith runtime initialized. Interface prefix: '%s', loading profile: '%s', voice_mode: '%s'",
        PREFIX_TEXT if SHOW_PREFIX else "disabled",
        _loading_profile,
        VOICE_MODE,
    )
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=["message", "callback_query"],
    )
