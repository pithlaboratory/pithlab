from __future__ import annotations

import json
import os
import socket
import time
from collections import Counter, defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional

import pandas as pd
import psutil
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# === PAGE CONFIG ===
st.set_page_config(
    page_title="Pith Runtime Console",
    page_icon="◌",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# === PATHS ===
TRACE_DIR = Path("output/traces")
EVAL_DIR = Path("output/eval_runs")
SYSTEM_MAP_PATH = Path("docs/PITH_SYSTEM_MAP_V1.md")
OPENAPI_PATH = Path("openapi-2.json")

# === CONFIG ===
REFRESH_MS = 3000  # Auto-refresh interval
HISTORY_LIMIT = 60  # Keep last N samples in memory

# === UTILS ===
def parse_ts(value: str | None) -> datetime:
    if not value:
        return datetime.min
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return datetime.min

def first_non_null(values: List[Any]) -> Any:
    for value in values:
        if value is not None:
            return value
    return None

def format_bytes(num: float) -> str:
    step = 1024.0
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = float(num)
    for unit in units:
        if size < step:
            return f"{size:.1f} {unit}"
        size /= step
    return f"{size:.1f} EB"

def format_uptime(seconds: float) -> str:
    seconds = int(seconds)
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"

def status_label(value: float, warn: float, crit: float) -> str:
    if value >= crit:
        return "hot"
    if value >= warn:
        return "warning"
    return "healthy"

# === DATA LOADERS ===
def load_trace_events() -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    if not TRACE_DIR.exists():
        return grouped
    for path in sorted(TRACE_DIR.glob("*.jsonl")):
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                raw = event.get("raw") or {}
                trace_id = raw.get("trace_id") or "no-trace-id"
                grouped[trace_id].append(event)
    return grouped

def build_trace_summary(trace_id: str, events: List[Dict[str, Any]]) -> Dict[str, Any]:
    events = sorted(events, key=lambda e: parse_ts(e.get("timestamp")))
    last_event = events[-1] if events else {}
    raw_blobs = [(e.get("raw") or {}) for e in events]
    return {
        "trace_id": trace_id,
        "workspace_id": first_non_null([e.get("workspace_id") for e in events]),
        "task_id": first_non_null([e.get("task_id") for e in events]),
        "event_count": len(events),
        "final_event_type": last_event.get("event_type"),
        "workflow_type": first_non_null([raw.get("workflow_type") for raw in raw_blobs]),
        "task_type": first_non_null([raw.get("task_type") for raw in raw_blobs]),
        "autonomy_tier": first_non_null([raw.get("autonomy_tier") for raw in raw_blobs]),
        "policy_violation": first_non_null([raw.get("policy_violation") for raw in raw_blobs]),
        "quality_score": first_non_null([raw.get("quality_score") for raw in raw_blobs]),
        "cost_usd": first_non_null([raw.get("cost_usd") for raw in reversed(raw_blobs)]) or first_non_null([raw.get("cost") for raw in reversed(raw_blobs)]),
        "last_timestamp": last_event.get("timestamp"),
    }

def normalize_eval_record(payload: Dict[str, Any], source_file: str) -> Dict[str, Any]:
    eval_record = payload.get("evaluation_record")
    if isinstance(eval_record, dict):
        merged = dict(eval_record)
        merged.setdefault("workflow_type", payload.get("workflow_type"))
        merged.setdefault("autonomy_tier", payload.get("autonomy_tier"))
        merged.setdefault("department", payload.get("department"))
        merged.setdefault("golden_id", payload.get("golden_id"))
        merged["_source_file"] = source_file
        # Extract multi-turn metadata from _meta
        meta = payload.get("_meta") or {}
        merged.setdefault("multi_turn", meta.get("multi_turn", False))
        # Extract conversation_turn_count from payload.payload
        inner_payload = payload.get("payload") or {}
        merged.setdefault("conversation_turn_count", inner_payload.get("conversation_turn_count"))
        # Extract governance dimensions from scores
        scores = eval_record.get("scores") or {}
        merged.setdefault("governance_score", scores.get("governance_score"))
        merged.setdefault("explicit_refusal", scores.get("explicit_refusal"))
        merged.setdefault("no_verbatim_internal", scores.get("no_verbatim_internal"))
        merged.setdefault("no_secrets", scores.get("no_secrets"))
        merged.setdefault("no_fake_execution", scores.get("no_fake_execution"))
        merged.setdefault("user_clarity", scores.get("user_clarity"))
        return merged
    payload = dict(payload)
    payload["_source_file"] = source_file
    return payload

def load_eval_records() -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    if not EVAL_DIR.exists():
        return records
    for path in sorted(EVAL_DIR.glob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as f:
                payload = json.load(f)
            if isinstance(payload, dict):
                records.append(normalize_eval_record(payload, str(path)))
        except Exception:
            continue
    return records

def avg(values: List[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)

def load_openapi_snapshot() -> Dict[str, Any]:
    if not OPENAPI_PATH.exists():
        return {}
    try:
        with OPENAPI_PATH.open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception:
        return {}
    paths = payload.get("paths") or {}
    total_operations = 0
    for _, ops in paths.items():
        if isinstance(ops, dict):
            total_operations += sum(1 for method in ops if method.lower() in {"get", "post", "patch", "delete", "put"})
    return {
        "title": ((payload.get("info") or {}).get("title")),
        "version": ((payload.get("info") or {}).get("version")),
        "path_count": len(paths),
        "operation_count": total_operations,
        "tag_count": len(payload.get("tags") or []),
    }

def load_system_map_text() -> str:
    if SYSTEM_MAP_PATH.exists():
        return SYSTEM_MAP_PATH.read_text(encoding="utf-8")
    return "PITH_SYSTEM_MAP_V1.md not found yet. Add the canonical system map in docs/ to render architecture context here."

# === GOVERNANCE HELPERS ===
def extract_governance_events(trace_events: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for trace_id, events in trace_events.items():
        for event in events:
            if (event.get("event_type") or "") != "governance_refusal":
                continue
            raw = event.get("raw") or {}
            rows.append(
                {
                    "timestamp": event.get("timestamp"),
                    "trace_id": raw.get("trace_id") or trace_id,
                    "task_id": event.get("task_id"),
                    "workspace_id": event.get("workspace_id"),
                    "channel": raw.get("channel", "unknown"),
                    "workflow_type": raw.get("workflow_type", "unknown"),
                    "task_type": raw.get("task_type", "unknown"),
                    "refusal_reason": raw.get("refusal_reason", "unknown"),
                    "autonomy_tier": raw.get("autonomy_tier"),
                    "policy_violation": raw.get("policy_violation"),
                    "user_id": raw.get("user_id"),
                    "chat_id": raw.get("chat_id"),
                    "input_preview": raw.get("input_preview", ""),
                    "semantic": event.get("semantic"),
                }
            )
    rows.sort(key=lambda x: parse_ts(x.get("timestamp")), reverse=True)
    return rows

def summarize_governance_events(events: List[Dict[str, Any]]) -> Dict[str, pd.DataFrame]:
    if not events:
        empty = pd.DataFrame()
        return {
            "events_df": empty,
            "reason_df": empty,
            "channel_df": empty,
        }

    events_df = pd.DataFrame(events)

    reason_df = (
        events_df.groupby("refusal_reason", dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )

    channel_df = (
        events_df.groupby("channel", dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )

    return {
        "events_df": events_df,
        "reason_df": reason_df,
        "channel_df": channel_df,
    }

# === SERVER METRICS ===
def get_server_metrics() -> Dict[str, Any]:
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()
    boot_ts = psutil.boot_time()
    load_avg = os.getloadavg() if hasattr(os, "getloadavg") else (0.0, 0.0, 0.0)
    try:
        process_count = len(psutil.pids())
    except Exception:
        process_count = None
    return {
        "timestamp": datetime.now(),
        "hostname": socket.gethostname(),
        "cpu_percent": psutil.cpu_percent(interval=0.2),
        "cpu_count": psutil.cpu_count(),
        "load_1m": load_avg[0],
        "load_5m": load_avg[1],
        "load_15m": load_avg[2],
        "ram_percent": vm.percent,
        "ram_used": vm.used,
        "ram_total": vm.total,
        "disk_percent": disk.percent,
        "disk_used": disk.used,
        "disk_total": disk.total,
        "net_sent": net.bytes_sent,
        "net_recv": net.bytes_recv,
        "boot_time": datetime.fromtimestamp(boot_ts),
        "uptime_seconds": time.time() - boot_ts,
        "process_count": process_count,
    }

def get_top_processes(limit: int = 8) -> pd.DataFrame:
    rows = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            info = proc.info
            rows.append({
                "pid": info.get("pid"),
                "name": info.get("name"),
                "cpu_percent": info.get("cpu_percent") or 0.0,
                "memory_percent": round(info.get("memory_percent") or 0.0, 3),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    if not rows:
        return pd.DataFrame(columns=["pid", "name", "cpu_percent", "memory_percent"])
    df = pd.DataFrame(rows)
    return df.sort_values(["cpu_percent", "memory_percent"], ascending=False).head(limit)

# === HISTORY MANAGEMENT ===
def ensure_history() -> None:
    if "server_history" not in st.session_state:
        st.session_state.server_history = deque(maxlen=HISTORY_LIMIT)
    if "last_net_sent" not in st.session_state:
        st.session_state.last_net_sent = None
    if "last_net_recv" not in st.session_state:
        st.session_state.last_net_recv = None
    if "last_timestamp" not in st.session_state:
        st.session_state.last_timestamp = None

def update_history(metrics: Dict[str, Any]) -> pd.DataFrame:
    ensure_history()
    prev_sent = st.session_state.last_net_sent
    prev_recv = st.session_state.last_net_recv
    prev_ts = st.session_state.last_timestamp

    sent_rate = 0.0
    recv_rate = 0.0
    if prev_sent is not None and prev_recv is not None and prev_ts is not None:
        elapsed = max((metrics["timestamp"] - prev_ts).total_seconds(), 1e-6)
        sent_rate = max(metrics["net_sent"] - prev_sent, 0) / elapsed
        recv_rate = max(metrics["net_recv"] - prev_recv, 0) / elapsed

    row = {
        "timestamp": metrics["timestamp"],
        "cpu_percent": metrics["cpu_percent"],
        "ram_percent": metrics["ram_percent"],
        "disk_percent": metrics["disk_percent"],
        "load_1m": metrics["load_1m"],
        "sent_rate_kb_s": sent_rate / 1024.0,
        "recv_rate_kb_s": recv_rate / 1024.0,
    }

    st.session_state.server_history.append(row)
    st.session_state.last_net_sent = metrics["net_sent"]
    st.session_state.last_net_recv = metrics["net_recv"]
    st.session_state.last_timestamp = metrics["timestamp"]

    return pd.DataFrame(list(st.session_state.server_history))

# === MAIN APP ===
st_autorefresh(interval=REFRESH_MS, key="pith_server_refresh")

# Load data
trace_events = load_trace_events()
trace_summaries = [build_trace_summary(trace_id, events) for trace_id, events in trace_events.items()]
trace_summaries.sort(key=lambda x: parse_ts(x.get("last_timestamp")), reverse=True)
trace_df = pd.DataFrame(trace_summaries)

# ✅ NEW: Governance events extraction
governance_events = extract_governance_events(trace_events)
governance_summary = summarize_governance_events(governance_events)
governance_events_df = governance_summary["events_df"]
governance_reason_df = governance_summary["reason_df"]
governance_channel_df = governance_summary["channel_df"]

eval_records = load_eval_records()
eval_df = pd.DataFrame(eval_records)
openapi_snapshot = load_openapi_snapshot()

# ✅ FIXED: Safe quality_score parsing
quality_scores: List[float] = []
for r in eval_records:
    value = r.get("quality_score")
    if value is not None:
        try:
            quality_scores.append(float(value))
        except (TypeError, ValueError):
            # Игнорируем странные значения, чтобы не падать
            pass
avg_quality = avg(quality_scores)

human_override_count = sum(1 for r in eval_records if r.get("human_override") not in (None, "none"))
policy_violation_count = sum(1 for r in eval_records if bool(r.get("policy_violation")) is True)
governance_count = sum(1 for r in eval_records if str(r.get("workflow_type", "")).startswith("governance_"))
non_governance_count = len(eval_records) - governance_count
workflow_counter = Counter(r.get("workflow_type", "unknown") for r in eval_records)
success_counter = Counter(r.get("task_success", "unknown") for r in eval_records)

# ✅ NEW: Governance metrics
governance_refusal_count = len(governance_events)
latest_governance_reason = (
    governance_events_df.iloc[0]["refusal_reason"]
    if not governance_events_df.empty and "refusal_reason" in governance_events_df.columns
    else "n/a"
)

# Server metrics
server_metrics = get_server_metrics()
server_history_df = update_history(server_metrics)
top_processes_df = get_top_processes()

# Status indicators
cpu_state = status_label(server_metrics["cpu_percent"], 65, 85)
ram_state = status_label(server_metrics["ram_percent"], 75, 90)
disk_state = status_label(server_metrics["disk_percent"], 80, 92)

# === STYLES ===
st.markdown("""
<style>
:root {
    --bg: #f3f1ec;
    --bg2: #e8e5de;
    --bg3: #ddd9d1;
    --sage: #8aa5a3;
    --sage2: #5c8280;
    --sageLt: #bdd0ce;
    --ink: #1c1d1b;
    --muted: #7a7b77;
    --white: #fafaf8;
    --line: rgba(28,29,27,.08);
    --line2: rgba(28,29,27,.14);
    --ok: #5c8280;
    --warn: #d19900;
    --hot: #a13544;
}
.stApp {
    background: linear-gradient(180deg, var(--bg) 0%, #efede7 100%);
    color: var(--ink);
}
.block-container {
    padding-top: 1.8rem;
    padding-bottom: 3rem;
    max-width: 1340px;
}
h1, h2, h3 {
    color: var(--ink);
    letter-spacing: -0.03em;
    font-weight: 300;
}
[data-testid="stMetricValue"] {
    font-size: 2.2rem;
    font-weight: 300;
    color: var(--ink);
}
[data-testid="stMetricLabel"] {
    color: var(--muted);
    font-size: 0.92rem;
    letter-spacing: 0.03em;
}
div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.45);
    border: 1px solid var(--line);
    border-radius: 22px;
    padding: 1rem 1.1rem;
    box-shadow: 0 8px 30px rgba(28,29,27,0.04);
}
.pith-hero {
    background: linear-gradient(135deg, rgba(255,255,255,0.62) 0%, rgba(232,229,222,0.86) 100%);
    border: 1px solid var(--line);
    border-radius: 32px;
    padding: 2rem 2rem 1.6rem 2rem;
    margin-bottom: 1.25rem;
    position: relative;
    overflow: hidden;
}
.pith-hero::after {
    content: "";
    position: absolute;
    width: 340px;
    height: 340px;
    right: -80px;
    top: -120px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(138,165,163,0.18) 0%, rgba(138,165,163,0.02) 68%, transparent 72%);
}
.eyebrow {
    text-transform: uppercase;
    letter-spacing: 0.18em;
    font-size: 0.72rem;
    color: var(--sage2);
    margin-bottom: 0.9rem;
}
.hero-title {
    font-size: clamp(2.4rem, 5vw, 4.8rem);
    line-height: 1.02;
    margin: 0 0 0.8rem 0;
    position: relative;
    z-index: 2;
}
.hero-title .acc { color: var(--sage2); }
.hero-sub {
    max-width: 780px;
    color: var(--muted);
    font-size: 1.02rem;
    line-height: 1.75;
    position: relative;
    z-index: 2;
}
.micro-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0,1fr));
    gap: 0.75rem;
    margin-top: 1.15rem;
    position: relative;
    z-index: 2;
}
.micro-card {
    background: rgba(28,29,27,0.03);
    border: 1px solid rgba(28,29,27,0.06);
    border-radius: 18px;
    padding: 0.9rem 1rem;
}
.micro-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: var(--sage2);
    margin-bottom: 0.35rem;
}
.micro-value {
    font-size: 1rem;
    color: var(--ink);
}
.section-card {
    background: rgba(255,255,255,0.42);
    border: 1px solid var(--line);
    border-radius: 28px;
    padding: 1.25rem 1.25rem 1rem 1.25rem;
    margin-top: 1rem;
    box-shadow: 0 10px 30px rgba(28,29,27,0.035);
}
.section-label {
    text-transform: uppercase;
    letter-spacing: 0.18em;
    font-size: 0.72rem;
    color: var(--sage2);
    margin-bottom: 0.7rem;
}
.section-title {
    font-size: 1.55rem;
    margin-bottom: 0.35rem;
}
.section-copy {
    color: var(--muted);
    font-size: 0.97rem;
    line-height: 1.7;
    margin-bottom: 1rem;
    max-width: 760px;
}
.pill {
    display: inline-block;
    border: 1px solid rgba(138,165,163,0.34);
    color: var(--sage2);
    background: rgba(189,208,206,0.25);
    border-radius: 999px;
    padding: 0.35rem 0.75rem;
    margin-right: 0.45rem;
    margin-bottom: 0.45rem;
    font-size: 0.8rem;
}
.status-pill {
    display: inline-block;
    border-radius: 999px;
    padding: 0.38rem 0.8rem;
    font-size: 0.8rem;
    margin-right: 0.5rem;
    border: 1px solid transparent;
}
.status-healthy { background: rgba(92,130,128,.12); color: var(--ok); border-color: rgba(92,130,128,.18); }
.status-warning { background: rgba(209,153,0,.10); color: var(--warn); border-color: rgba(209,153,0,.16); }
.status-hot { background: rgba(161,53,68,.10); color: var(--hot); border-color: rgba(161,53,68,.16); }
div[data-testid="stDataFrame"] {
    border-radius: 18px;
    overflow: hidden;
    border: 1px solid var(--line);
}
div[data-testid="stCodeBlock"] pre {
    border-radius: 18px !important;
    border: 1px solid var(--line) !important;
}
@media (max-width: 980px) {
    .micro-grid { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 640px) {
    .micro-grid { grid-template-columns: 1fr; }
}
</style>
""", unsafe_allow_html=True)

# === HERO ===
st.markdown(f"""
<div class="pith-hero">
    <div class="eyebrow">Pith Runtime Console</div>
    <div class="hero-title">Observability for the <span class="acc">continuity engine</span></div>
    <div class="hero-sub">
        Internal dashboard for traces, evaluation, governance posture, architecture context, and live server health.
        The interface keeps the Pith landing language, but now includes dynamic host telemetry.
    </div>
    <div style="margin-top:1rem;">
        <span class="status-pill status-{cpu_state}">CPU {cpu_state}</span>
        <span class="status-pill status-{ram_state}">RAM {ram_state}</span>
        <span class="status-pill status-{disk_state}">Disk {disk_state}</span>
    </div>
    <div class="micro-grid">
        <div class="micro-card"><div class="micro-label">Hostname</div><div class="micro-value">{server_metrics['hostname']}</div></div>
        <div class="micro-card"><div class="micro-label">Trace files</div><div class="micro-value">{len(list(TRACE_DIR.glob('*.jsonl'))) if TRACE_DIR.exists() else 0}</div></div>
        <div class="micro-card"><div class="micro-label">Eval runs</div><div class="micro-value">{len(eval_records)}</div></div>
        <div class="micro-card"><div class="micro-label">Refresh</div><div class="micro-value">{REFRESH_MS // 1000}s live</div></div>
    </div>
</div>
""", unsafe_allow_html=True)

# === TOP METRICS ===
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total workflows", len(eval_records))
c2.metric("Avg quality", f"{avg_quality:.3f}" if avg_quality is not None else "n/a")
c3.metric("Human overrides", human_override_count)
c4.metric("Policy violations", policy_violation_count)

# === TABS ===
# ✅ UPDATED: Added Governance tab
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["Overview", "Server", "Governance", "Traces", "Eval", "Architecture"]
)

# --- TAB 1: OVERVIEW ---
with tab1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Snapshot</div><div class="section-title">Current runtime posture</div><div class="section-copy">A compact operational view across evaluation, governance mix, API surface, and server health. This remains the top-level summary layer above local evidence stores.</div>', unsafe_allow_html=True)
    a, b, c = st.columns(3)
    a.metric("Governance workflows", governance_count)
    # ✅ NEW: Governance refusals metric
    a.metric("Governance refusals", governance_refusal_count)
    b.metric("Non-governance", non_governance_count)
    b.metric("RAM", f"{server_metrics['ram_percent']:.1f}%")
    c.metric("Trace summaries", len(trace_summaries))
    c.metric("Disk", f"{server_metrics['disk_percent']:.1f}%")

    st.markdown("#### Workflow mix")
    wf_df = pd.DataFrame([{"workflow_type": k, "count": v} for k, v in workflow_counter.most_common()])
    if not wf_df.empty:
        st.dataframe(wf_df, use_container_width=True, hide_index=True)
    else:
        st.info("No evaluation workflow data found yet.")

    st.markdown("#### Success distribution")
    succ_df = pd.DataFrame([{"task_success": k, "count": v} for k, v in success_counter.most_common()])
    if not succ_df.empty:
        st.dataframe(succ_df, use_container_width=True, hide_index=True)
    else:
        st.info("No task success data found yet.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 2: SERVER ---
with tab2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Host telemetry</div><div class="section-title">Live server metrics</div><div class="section-copy">Current machine health with short in-memory history for CPU, memory, disk, and network throughput. This view is refreshed automatically.</div>', unsafe_allow_html=True)
    
    # ✅ NEW: Last refresh timestamp
    st.caption(f"Last sample: {server_metrics['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")

    # Metrics row 1
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("CPU", f"{server_metrics['cpu_percent']:.1f}%", f"{server_metrics['load_1m']:.2f} load (1m)")
    m2.metric("RAM", f"{server_metrics['ram_percent']:.1f}%", f"{format_bytes(server_metrics['ram_used'])} / {format_bytes(server_metrics['ram_total'])}")
    m3.metric("Disk /", f"{server_metrics['disk_percent']:.1f}%", f"{format_bytes(server_metrics['disk_used'])} / {format_bytes(server_metrics['disk_total'])}")
    m4.metric("Uptime", format_uptime(server_metrics["uptime_seconds"]), server_metrics["boot_time"].strftime("%Y-%m-%d %H:%M:%S"))

    # Metrics row 2
    n1, n2, n3, n4 = st.columns(4)
    n1.metric("Processes", server_metrics["process_count"] if server_metrics["process_count"] is not None else "n/a")
    n2.metric("CPU cores", server_metrics["cpu_count"])
    n3.metric("Net sent", format_bytes(server_metrics["net_sent"]))
    n4.metric("Net recv", format_bytes(server_metrics["net_recv"]))

    # ✅ FIXED: Charts with guards
    st.markdown("#### Live trend")
    chart_left, chart_right = st.columns(2)

    with chart_left:
        if not server_history_df.empty and "timestamp" in server_history_df.columns:
            st.line_chart(
                server_history_df.set_index("timestamp")[["cpu_percent", "ram_percent", "disk_percent"]],
                use_container_width=True,
                height=280,
            )
        else:
            st.info("Collecting first telemetry samples for CPU / RAM / disk…")

    with chart_right:
        if not server_history_df.empty and "timestamp" in server_history_df.columns:
            st.line_chart(
                server_history_df.set_index("timestamp")[["sent_rate_kb_s", "recv_rate_kb_s", "load_1m"]],
                use_container_width=True,
                height=280,
            )
        else:
            st.info("Collecting first telemetry samples for network / load…")

    # Top processes
    st.markdown("#### Top processes")
    if not top_processes_df.empty:
        st.dataframe(top_processes_df, use_container_width=True, hide_index=True)
    else:
        st.info("Process data unavailable.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 3: GOVERNANCE (NEW) ---
with tab3:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-label">Policy events</div>'
        '<div class="section-title">Governance refusals</div>'
        '<div class="section-copy">Structured governance events extracted from trace files. '
        'This view shows what requests were refused by policy guards, why they were refused, '
        'and through which interface they arrived.</div>',
        unsafe_allow_html=True,
    )

    g1, g2, g3 = st.columns(3)
    g1.metric("Total refusals", governance_refusal_count)
    g2.metric(
        "Unique reasons",
        int(governance_reason_df["refusal_reason"].nunique()) if not governance_reason_df.empty else 0,
    )
    g3.metric("Latest reason", latest_governance_reason)

    left, right = st.columns(2)

    with left:
        st.markdown("#### By refusal reason")
        if not governance_reason_df.empty:
            st.dataframe(governance_reason_df, use_container_width=True, hide_index=True)
        else:
            st.info("No governance refusal events found yet.")

    with right:
        st.markdown("#### By channel")
        if not governance_channel_df.empty:
            st.dataframe(governance_channel_df, use_container_width=True, hide_index=True)
        else:
            st.info("No governance channel data found yet.")

    st.markdown("#### Recent governance events")
    if not governance_events_df.empty:
        cols = [
            c for c in [
                "timestamp",
                "channel",
                "refusal_reason",
                "workflow_type",
                "task_type",
                "trace_id",
                "workspace_id",
                "input_preview",
            ]
            if c in governance_events_df.columns
        ]
        st.dataframe(
            governance_events_df[cols],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No governance events available in output/traces yet.")

    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 4: TRACES (was tab3) ---
with tab4:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Trace spine</div><div class="section-title">Trace summary</div><div class="section-copy">Grouped by trace_id from JSONL events. Intended to show how workflows resolve, what final event type they reach, and which governance or workflow metadata is present.</div>', unsafe_allow_html=True)
    if not trace_df.empty:
        cols = [c for c in ["trace_id", "task_id", "workspace_id", "event_count", "final_event_type", "workflow_type", "task_type", "autonomy_tier", "policy_violation", "quality_score", "cost_usd", "last_timestamp"] if c in trace_df.columns]
        st.dataframe(trace_df[cols], use_container_width=True, hide_index=True)
    else:
        st.info("No trace summaries found yet in output/traces.")
    recent_files = sorted([p.name for p in TRACE_DIR.glob("*.jsonl")], reverse=True)[:8] if TRACE_DIR.exists() else []
    if recent_files:
        st.markdown("#### Recent trace files")
        st.markdown("".join([f'<span class="pill">{name}</span>' for name in recent_files]), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 5: EVAL (was tab4) ---
with tab5:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Evaluation</div><div class="section-title">Eval runtime summary</div><div class="section-copy">Normalized from output/eval_runs, including evaluation_record payloads. This section tracks quality, override pressure, and workflow coverage across current golden runs.</div>', unsafe_allow_html=True)
    if not eval_df.empty:
        # Filters row: 3 columns for compact layout
        fcol1, fcol2, fcol3 = st.columns(3)
        with fcol1:
            show_multi_only = st.checkbox("Multi-turn only", value=False, key="eval_multi_filter")
        with fcol2:
            model_options = sorted(eval_df["model"].dropna().unique()) if "model" in eval_df.columns else []
            selected_models = st.multiselect("Model", options=model_options, key="eval_model_filter")
        with fcol3:
            wf_options = sorted(eval_df["workflow_type"].dropna().unique()) if "workflow_type" in eval_df.columns else []
            selected_wf = st.multiselect("Workflow type", options=wf_options, key="eval_wf_filter")

        # Apply filters in order: multi-turn → model → workflow_type
        display_df = eval_df.copy()
        if show_multi_only and "multi_turn" in display_df.columns:
            display_df = display_df[display_df["multi_turn"] == True]
        if selected_models and "model" in display_df.columns:
            display_df = display_df[display_df["model"].isin(selected_models)]
        if selected_wf and "workflow_type" in display_df.columns:
            display_df = display_df[display_df["workflow_type"].isin(selected_wf)]

        cols = [c for c in [
            "golden_id", "workflow_type", "task_type", "task_success",
            "human_override", "quality_score", "governance_score",
            "policy_violation", "multi_turn", "conversation_turn_count",
            "autonomy_tier", "eval_version", "_source_file",
        ] if c in display_df.columns]
        st.dataframe(display_df[cols], use_container_width=True, hide_index=True)
    else:
        st.info("No eval records found yet in output/eval_runs.")

    # Governance breakdown block
    st.markdown("#### Governance score breakdown")
    gov_df = eval_df[eval_df["workflow_type"].str.startswith("governance_", na=False)] if not eval_df.empty else pd.DataFrame()
    if not gov_df.empty:
        gov_cols = [c for c in [
            "golden_id", "governance_score", "explicit_refusal",
            "no_verbatim_internal", "no_secrets", "no_fake_execution",
            "user_clarity", "multi_turn", "conversation_turn_count",
        ] if c in gov_df.columns]
        st.dataframe(gov_df[gov_cols], use_container_width=True, hide_index=True)
    else:
        st.info("No governance evaluation records found yet.")

    latest_eval_files = sorted([p.name for p in EVAL_DIR.glob("*.json")], reverse=True)[:8] if EVAL_DIR.exists() else []
    if latest_eval_files:
        st.markdown("#### Recent eval files")
        st.markdown("".join([f'<span class="pill">{name}</span>' for name in latest_eval_files]), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 6: ARCHITECTURE (was tab5) ---
with tab6:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Architecture</div><div class="section-title">System map context</div><div class="section-copy">Canonical system map and request flow for the current Pith runtime. Keep this aligned with the docs version so the dashboard remains an honest reflection of the system.</div>', unsafe_allow_html=True)
    st.markdown("#### API snapshot")
    api_cols = st.columns(4)
    api_cols[0].metric("API title", openapi_snapshot.get("title", "n/a"))
    api_cols[1].metric("Version", openapi_snapshot.get("version", "n/a"))
    api_cols[2].metric("Paths", openapi_snapshot.get("path_count", 0))
    api_cols[3].metric("Operations", openapi_snapshot.get("operation_count", 0))
    st.markdown("#### System map document")
    st.code(load_system_map_text(), language="markdown")
    st.markdown('</div>', unsafe_allow_html=True)
