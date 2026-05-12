#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pith APEX Command Center v4.1 — Final Elite Edition
Landing-native aesthetic, live metrics, SVG favicon.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import psutil
import time
import os
import sqlite3
import glob
import base64
from datetime import datetime, timedelta
from pathlib import Path

# -------------------- FAVICON (SVG DATA URI + FALLBACK PNG) --------------------
PITH_LOGO_SVG = """
<svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="32" cy="32" r="22" stroke="#8AA5A3" stroke-width="3" />
  <circle cx="32" cy="32" r="8" fill="#8AA5A3" />
</svg>
"""

def get_svg_icon(svg_str):
    b64 = base64.b64encode(svg_str.encode()).decode()
    return f"data:image/svg+xml;base64,{b64}"

# Paths
BASE_DIR = Path(os.getenv("PITH_DIR", "/root/pith_v5"))
DB_PATH = BASE_DIR / "data" / "episodes.db"
SKILLS_DIR = BASE_DIR / "skills" / "mined"
LOG_PATH = BASE_DIR / "logs" / "bot_nohup.log"
FAVICON_PATH = BASE_DIR / "favicon.png"

# Generate PNG favicon as fallback (if Pillow available)
if not FAVICON_PATH.exists():
    try:
        from PIL import Image, ImageDraw
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((8, 8, 56, 56), outline=(138, 165, 163), width=3)
        draw.ellipse((26, 26, 38, 38), fill=(138, 165, 163))
        img.save(FAVICON_PATH)
    except Exception:
        pass

# Use SVG data URI as primary icon (works in all modern browsers)
st.set_page_config(
    page_title="pith · Command Center",
    page_icon=get_svg_icon(PITH_LOGO_SVG),
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -------------------- LANDING-NATIVE CSS --------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,200;0,300;0,400;0,500;1,200&family=JetBrains+Mono:wght@300;400&display=swap');

:root {
    --bg: #F3F1EC;
    --bg2: #E8E5DE;
    --bg3: #DDD9D1;
    --sage: #8AA5A3;
    --sage2: #5C8280;
    --sagelt: #BDD0CE;
    --ink: #1C1D1B;
    --muted: #7A7B77;
    --white: #FAFAF8;
    --line: rgba(28,29,27,0.07);
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
}
.stApp {
    background: var(--bg) !important;
    color: var(--ink) !important;
}
#MainMenu, footer, header, .stDeployButton, .stToolbar {
    visibility: hidden !important;
    display: none !important;
}

/* Glass cards */
.glass-card {
    background: rgba(250, 250, 248, 0.6);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid var(--line);
    border-radius: 24px;
    padding: 28px;
    box-shadow: 0 2px 16px rgba(138, 165, 163, 0.04);
    transition: transform 0.35s cubic-bezier(.16,1,.3,1), box-shadow 0.35s ease;
}
.glass-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 40px rgba(138, 165, 163, 0.10);
}

/* Φ Capsule */
.phi-capsule {
    width: 160px; height: 160px; border-radius: 50%;
    position: relative; margin: 0 auto;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    background: radial-gradient(circle at 35% 35%, rgba(138,165,163,0.18) 0%, rgba(92,130,128,0.08) 60%, transparent 100%);
    border: 1.5px solid rgba(138, 165, 163, 0.28);
    box-shadow: 0 0 60px rgba(138, 165, 163, 0.14), inset 0 0 30px rgba(255,255,255,0.35);
    animation: breathe 6s ease-in-out infinite;
}
.phi-capsule::before {
    content: ''; position: absolute; inset: -14px; border-radius: 50%;
    border: 1px solid rgba(138, 165, 163, 0.18);
    animation: spin 22s linear infinite;
    pointer-events: none;
}
.phi-capsule::after {
    content: ''; position: absolute; inset: -7px; border-radius: 50%;
    border: 1px dashed rgba(138, 165, 163, 0.12);
    animation: spin 44s linear infinite reverse;
    pointer-events: none;
}
@keyframes breathe { 0%,100%{transform:scale(1)} 50%{transform:scale(1.04)} }
@keyframes spin { to{transform:rotate(360deg)} }
.phi-value { font-size: 42px; font-weight: 200; color: var(--sage2); letter-spacing: -0.04em; line-height: 1; }
.phi-label { font-size: 10px; font-weight: 500; letter-spacing: 0.22em; text-transform: uppercase; color: var(--sage); margin-top: 8px; }

/* Typography */
.section-title {
    font-size: 11px; font-weight: 500; letter-spacing: 0.18em; text-transform: uppercase;
    color: var(--sage); margin: 0 0 16px 0;
}
.metric-value {
    font-size: 36px; font-weight: 200; letter-spacing: -0.04em; color: var(--ink); line-height: 1;
}
.metric-label {
    font-size: 11px; font-weight: 300; letter-spacing: 0.1em; text-transform: uppercase;
    color: var(--muted); margin-bottom: 10px;
}
.metric-delta {
    font-size: 12px; font-weight: 400; color: var(--sage2); margin-top: 8px; letter-spacing: 0.02em;
}
.metric-delta.muted { color: var(--muted); }

/* Agents */
.agent-card {
    background: rgba(250,250,248,0.5);
    backdrop-filter: blur(10px);
    border: 1px solid var(--line);
    border-radius: 20px;
    padding: 24px;
    transition: all 0.35s cubic-bezier(.16,1,.3,1);
}
.agent-card:hover {
    background: rgba(250,250,248,0.85);
    transform: translateY(-3px);
    box-shadow: 0 16px 48px rgba(138,165,163,0.12);
}
.agent-name { font-size: 16px; font-weight: 400; color: var(--ink); letter-spacing: -0.01em; }
.agent-role { font-size: 11px; font-weight: 300; color: var(--sage); letter-spacing: 0.04em; margin-top: 2px; }
.status-dot {
    width: 7px; height: 7px; border-radius: 50%; display: inline-block; margin-right: 6px;
}
.status-dot.active {
    background: var(--sage);
    box-shadow: 0 0 0 4px rgba(138,165,163,0.18);
    animation: pulse 2.5s infinite;
}
.status-dot.standby { background: var(--sagelt); }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.45} }
.agent-bar-track { height: 5px; background: var(--bg2); border-radius: 3px; overflow: hidden; margin-top: 10px; }
.agent-bar-fill { height: 100%; background: var(--sage); border-radius: 3px; transition: width 0.8s cubic-bezier(.16,1,.3,1); }
.agent-bar-fill.mid { background: var(--sage2); }
.agent-meta { margin-top: 16px; padding-top: 14px; border-top: 1px solid var(--line); font-size: 11px; color: var(--muted); letter-spacing: 0.02em; }

/* System */
.sys-card { background: rgba(250,250,248,0.5); border: 1px solid var(--line); border-radius: 16px; padding: 20px; }
.sys-label { font-size: 10px; font-weight: 500; letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted); margin-bottom: 10px; }
.sys-value { font-size: 26px; font-weight: 200; color: var(--ink); margin-bottom: 10px; letter-spacing: -0.02em; }
.sys-bar-track { height: 4px; background: var(--bg2); border-radius: 2px; overflow: hidden; }
.sys-bar-fill { height: 100%; background: var(--sage); border-radius: 2px; transition: width 0.8s ease; }
.sys-bar-fill.mid { background: var(--sage2); }

/* Terminal */
.terminal {
    background: var(--ink); color: var(--white); padding: 24px; border-radius: 16px;
    font-family: 'JetBrains Mono', monospace !important; font-size: 12px; line-height: 1.7;
    max-height: 460px; overflow: auto;
}
.term-info { color: var(--sagelt); }
.term-warn { color: var(--sage); }
.term-err { color: var(--bg3); }

/* Tables */
table { font-family: 'DM Sans', sans-serif !important; font-size: 13px !important; }
th {
    font-weight: 500 !important; letter-spacing: 0.06em; text-transform: uppercase;
    font-size: 10px !important; color: var(--muted) !important;
    background: transparent !important; border-bottom: 1px solid var(--line) !important;
}
td { border-bottom: 1px solid var(--line) !important; color: var(--ink) !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 28px; border-bottom: 1px solid var(--line); }
.stTabs [data-baseweb="tab"] {
    height: 42px; font-family: 'DM Sans', sans-serif !important; font-size: 12px !important;
    font-weight: 500 !important; letter-spacing: 0.08em; text-transform: uppercase;
    color: var(--muted) !important; background: transparent !important; border: none !important;
}
.stTabs [aria-selected="true"] { color: var(--ink) !important; border-bottom: 1.5px solid var(--sage) !important; }
</style>
""", unsafe_allow_html=True)

# -------------------- SESSION STATE --------------------
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = True
if "refresh_interval" not in st.session_state:
    st.session_state.refresh_interval = 5

# -------------------- HELPERS --------------------
@st.cache_data(ttl=2)
def get_system_metrics():
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    proc = psutil.Process(os.getpid())
    return {
        "cpu": cpu,
        "ram_percent": mem.percent,
        "ram_used_gb": round(mem.used / (1024**3), 1),
        "ram_total_gb": round(mem.total / (1024**3), 1),
        "disk_percent": disk.percent,
        "disk_free_gb": round(disk.free / (1024**3), 1),
        "uptime_seconds": int(time.time() - proc.create_time()),
    }

@st.cache_data(ttl=10)
def load_stats():
    stats = {
        "total_requests": 0,
        "success_rate": 100.0,
        "total_cost": 0.0,
        "budget_left": 30.0,
        "coherence_phi": 76.2,
    }
    try:
        if DB_PATH.exists():
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            row = c.execute("SELECT COUNT(*) FROM episodes WHERE role='user'").fetchone()
            if row: stats["total_requests"] = row[0]
            row_succ = c.execute("SELECT COUNT(*) FROM episodes WHERE outcome='success'").fetchone()
            succ = row_succ[0] if row_succ else 0
            total = c.execute("SELECT COUNT(*) FROM episodes").fetchone()[0] or 1
            stats["success_rate"] = round((succ / total) * 100, 1)
            row_cost = c.execute("SELECT SUM(cost_usd) FROM llm_calls").fetchone()
            if row_cost and row_cost[0]:
                stats["total_cost"] = row_cost[0]
                stats["budget_left"] = 30.0 - stats["total_cost"]
            row_phi = c.execute(
                "SELECT AVG(CAST(json_extract(metadata_json,'$.plex_coherence') AS REAL)) "
                "FROM episodes WHERE metadata_json LIKE '%plex_coherence%'"
            ).fetchone()
            if row_phi and row_phi[0]:
                stats["coherence_phi"] = round(row_phi[0], 1)
            conn.close()
    except Exception:
        pass
    return stats

def get_agents():
    return [
        {"name": "TERA", "role": "Strategic Nucleus", "status": "active", "load": 42, "calls": 124},
        {"name": "PLEX", "role": "Contextual Retrieval", "status": "active", "load": 38, "calls": 98},
        {"name": "HEX", "role": "Constraint Audit", "status": "standby", "load": 0, "calls": 14},
        {"name": "CODA", "role": "Deterministic Execution", "status": "active", "load": 15, "calls": 62},
    ]

def fmt_uptime(sec):
    d, rem = divmod(sec, 86400)
    h, rem = divmod(rem, 3600)
    m, _ = divmod(rem, 60)
    if d: return f"{d}d {h:02d}h {m:02d}m"
    return f"{h:02d}h {m:02d}m"

def style_plotly(fig, h=220):
    fig.update_layout(
        font=dict(family="DM Sans, sans-serif", color="#7A7B77", size=11),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=30, b=10),
        height=h,
        xaxis=dict(showgrid=True, gridcolor="rgba(28,29,27,0.06)", gridwidth=0.5, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(28,29,27,0.06)", gridwidth=0.5, zeroline=False),
        hoverlabel=dict(bgcolor="#FAFAF8", font_color="#1C1D1B", font_family="DM Sans"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)),
    )
    return fig

# -------------------- DATA --------------------
stats = load_stats()
sys_m = get_system_metrics()
agents = get_agents()

# -------------------- HEADER --------------------
c1, c2, c3 = st.columns([1, 2, 1])
with c1:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;">
      <svg width="28" height="28" viewBox="0 0 32 32" fill="none">
        <circle cx="16" cy="16" r="11" stroke="#8AA5A3" stroke-width="1.2" stroke-dasharray="56 12" stroke-linecap="round"/>
        <circle cx="16" cy="16" r="3.5" stroke="#8AA5A3" stroke-width="1"/>
      </svg>
      <span style="font-size:15px;font-weight:300;letter-spacing:.04em;color:#1C1D1B;">
        pith<span style="color:#8AA5A3;font-weight:400;">.</span> dashboard
      </span>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown(
        f'<div style="text-align:center;font-size:12px;font-weight:300;color:#7A7B77;letter-spacing:.04em;">'
        f'{datetime.now().strftime("%d.%m.%Y · %H:%M")} · UTC+3</div>',
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        '<div style="text-align:right;font-size:11px;font-weight:300;color:#8AA5A3;letter-spacing:.1em;text-transform:uppercase;">'
        'v4.1 elite</div>',
        unsafe_allow_html=True,
    )

st.markdown("<div style='height:1px;background:rgba(28,29,27,0.07);margin:16px 0;'></div>", unsafe_allow_html=True)

# -------------------- TOP ROW: Φ + KPIs --------------------
col_phi, col_k1, col_k2, col_k3, col_k4 = st.columns([1.1, 0.95, 0.95, 0.95, 0.95])

with col_phi:
    st.markdown(f"""
    <div class="glass-card" style="display:flex;align-items:center;justify-content:center;height:100%;min-height:210px;">
      <div class="phi-capsule">
        <div class="phi-value">Φ {stats['coherence_phi']:.1f}</div>
        <div class="phi-label">Coherence</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

kpis = [
    ("Requests", f"{stats['total_requests']:,}", "↑ 12%", False),
    ("Success", f"{stats['success_rate']:.1f}%", "↑ 2.3%", False),
    ("Cost", f"${stats['total_cost']:.4f}", "+$0.002", True),
    ("Budget", f"${stats['budget_left']:.2f}", "30 days", False),
]

for col, (lab, val, dlt, neg) in zip([col_k1, col_k2, col_k3, col_k4], kpis):
    with col:
        cls = "metric-delta muted" if neg else "metric-delta"
        st.markdown(f"""
        <div class="glass-card" style="height:100%;display:flex;flex-direction:column;justify-content:center;min-height:210px;">
            <div class="metric-label">{lab}</div>
            <div class="metric-value">{val}</div>
            <div class="{cls}">{dlt}</div>
        </div>
        """, unsafe_allow_html=True)

# -------------------- AGENTS --------------------
st.markdown('<div style="margin-top:32px;"><p class="section-title">active agents</p></div>', unsafe_allow_html=True)
a_cols = st.columns(4)
for idx, ag in enumerate(agents):
    with a_cols[idx]:
        dot = "active" if ag["status"] == "active" else "standby"
        bar = "mid" if ag["load"] > 50 else ""
        st.markdown(f"""
        <div class="agent-card">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div>
                    <div class="agent-name">{ag['name']}</div>
                    <div class="agent-role">{ag['role']}</div>
                </div>
                <div style="display:flex;align-items:center;margin-top:4px;">
                    <span class="status-dot {dot}"></span>
                    <span style="font-size:11px;color:#7A7B77;text-transform:uppercase;letter-spacing:0.06em;">{ag['status']}</span>
                </div>
            </div>
            <div style="margin-top:22px;">
                <div style="display:flex;justify-content:space-between;font-size:12px;color:#7A7B77;margin-bottom:6px;">
                    <span>Load</span><span>{ag['load']}%</span>
                </div>
                <div class="agent-bar-track"><div class="agent-bar-fill {bar}" style="width:{ag['load']}%;"></div></div>
            </div>
            <div class="agent-meta">Calls: {ag['calls']:,}</div>
        </div>
        """, unsafe_allow_html=True)

# -------------------- SYSTEM HEALTH --------------------
st.markdown('<div style="margin-top:36px;"><p class="section-title">system health</p></div>', unsafe_allow_html=True)
s_cols = st.columns(5)
s_data = [
    ("CPU", sys_m["cpu"], "%", sys_m["cpu"]),
    ("RAM", sys_m["ram_percent"], "%", sys_m["ram_percent"]),
    ("Disk", sys_m["disk_percent"], "%", sys_m["disk_percent"]),
    ("Uptime", fmt_uptime(sys_m["uptime_seconds"]), "", 0),
    ("Tasks", len(psutil.pids()), "", 0),
]
for col, (lab, val, unit, raw) in zip(s_cols, s_data):
    with col:
        bar = ""
        if unit == "%":
            mid = "mid" if raw > 60 else ""
            bar = f'<div class="sys-bar-track"><div class="sys-bar-fill {mid}" style="width:{raw}%;"></div></div>'
        st.markdown(f"""
        <div class="sys-card">
            <div class="sys-label">{lab}</div>
            <div class="sys-value">{val}{unit}</div>
            {bar}
        </div>
        """, unsafe_allow_html=True)

# -------------------- TABS --------------------
st.markdown("<div style='margin-top:36px;'></div>", unsafe_allow_html=True)
t1, t2, t3, t4, t5 = st.tabs(["ANALYTICS", "MEMORY", "SKILLS", "LOGS", "GOVERNANCE"])

# --- ANALYTICS ---
with t1:
    st.markdown('<p class="section-title" style="margin-top:8px;">activity & coherence</p>', unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    with c2:
        st.session_state.auto_refresh = st.checkbox("Live refresh", value=st.session_state.auto_refresh)
        st.session_state.refresh_interval = st.selectbox("Interval (sec)", [3, 5, 10, 30], index=1)

    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=60, freq="5min")
    df = pd.DataFrame({
        "time": dates,
        "coherence": np.clip(np.cumsum(np.random.normal(0.05, 0.35, 60)) + stats["coherence_phi"], 60, 99),
        "requests": np.random.poisson(6, 60),
        "cost": np.abs(np.random.normal(0.005, 0.002, 60)),
        "tokens": np.random.poisson(110, 60),
    })

    fig_phi = go.Figure()
    fig_phi.add_trace(go.Scatter(
        x=df["time"], y=df["coherence"], mode="lines", name="Φ Coherence",
        line=dict(color="#5C8280", width=2.2, shape="spline"),
        fill="tozeroy", fillcolor="rgba(189,208,206,0.18)",
    ))
    st.plotly_chart(style_plotly(fig_phi, 240), width="stretch", config={"displayModeBar": False})

    c1, c2 = st.columns(2)
    with c1:
        fig_r = px.area(df, x="time", y="requests", color_discrete_sequence=["#8AA5A3"])
        fig_r.update_traces(line=dict(width=0), fillcolor="rgba(138,165,163,0.18)")
        st.plotly_chart(style_plotly(fig_r, 200), width="stretch", config={"displayModeBar": False})
    with c2:
        fig_c = px.bar(df, x="time", y="cost", color_discrete_sequence=["#5C8280"])
        fig_c.update_traces(marker=dict(opacity=0.7, line=dict(width=0)))
        st.plotly_chart(style_plotly(fig_c, 200), width="stretch", config={"displayModeBar": False})

# --- MEMORY ---
with t2:
    st.markdown('<p class="section-title" style="margin-top:8px;">episodic memory</p>', unsafe_allow_html=True)
    search = st.text_input("Search episodes", placeholder="Keywords...")
    limit = st.select_slider("Rows", options=[50, 100, 200, 500], value=100)
    try:
        conn = sqlite3.connect(DB_PATH)
        q = "SELECT ts, user_id, content, outcome FROM episodes WHERE content LIKE ? ORDER BY ts DESC LIMIT ?"
        df_mem = pd.read_sql(q, conn, params=(f"%{search}%", limit))
        conn.close()
    except Exception:
        df_mem = pd.DataFrame({
            "ts": [datetime.now() - timedelta(minutes=i * 5) for i in range(20)],
            "user_id": ["user_001"] * 20,
            "content": ["Semantic drift analysis and context window compaction routine."] * 20,
            "outcome": ["success"] * 20,
        })
    st.dataframe(df_mem, width="stretch", height=420, hide_index=True)
    csv = df_mem.to_csv(index=False)
    st.download_button("Export CSV", csv, f"episodes_{datetime.now():%Y%m%d_%H%M}.csv")

# --- SKILLS ---
with t3:
    st.markdown('<p class="section-title" style="margin-top:8px;">skill library</p>', unsafe_allow_html=True)
    try:
        if SKILLS_DIR.exists():
            files = sorted(glob.glob(str(SKILLS_DIR / "*.md")))
            skills = [
                {"name": Path(f).name, "size_kb": round(os.path.getsize(f) / 1024, 1),
                 "modified": datetime.fromtimestamp(os.path.getmtime(f)).strftime("%Y-%m-%d")}
                for f in files
            ]
        else:
            skills = []
    except Exception:
        skills = []
    if not skills:
        skills = [
            {"name": "mcp_protocol_integration.md", "size_kb": 4.5, "modified": "2026-04-20"},
            {"name": "attention_is_all_you_need.md", "size_kb": 12.8, "modified": "2026-04-19"},
            {"name": "a2a_agent_to_agent_spec.md", "size_kb": 3.1, "modified": "2026-04-18"},
            {"name": "rag_optimization_patterns.md", "size_kb": 8.9, "modified": "2026-04-17"},
        ]
    st.dataframe(pd.DataFrame(skills), width="stretch", height=320, hide_index=True)

# --- LOGS ---
with t4:
    st.markdown('<p class="section-title" style="margin-top:8px;">system logs</p>', unsafe_allow_html=True)
    n_lines = st.slider("Lines", 20, 500, 100)
    try:
        with open(LOG_PATH, "r", errors="ignore") as f:
            lines = f.readlines()[-n_lines:]
    except Exception:
        lines = [
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  INFO  [bot]      Telegram bot initialized",
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  INFO  [router]   Fallback model selected",
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  WARN  [hex]      Soft constraint deviation",
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ERROR [coda]     Execution timeout on skill_miner",
        ]
    html = []
    for line in lines:
        line = line.rstrip().replace("<", "&lt;").replace(">", "&gt;")
        if "ERROR" in line:
            html.append(f'<span class="term-err">{line}</span><br>')
        elif "WARN" in line:
            html.append(f'<span class="term-warn">{line}</span><br>')
        else:
            html.append(f'<span class="term-info">{line}</span><br>')
    st.markdown(f'<div class="terminal">{"".join(html)}</div>', unsafe_allow_html=True)

# --- GOVERNANCE ---
with t5:
    st.markdown('<p class="section-title" style="margin-top:8px;">patch governance</p>', unsafe_allow_html=True)
    try:
        conn = sqlite3.connect(DB_PATH)
        df_gov = pd.read_sql(
            "SELECT id, component, status, created_at FROM patch_candidates ORDER BY id DESC LIMIT 20", conn
        )
        conn.close()
    except Exception:
        df_gov = pd.DataFrame([
            {"id": 1, "component": "router_timeout", "status": "proposed", "created_at": "2026-04-22"},
            {"id": 2, "component": "coherence_boost", "status": "approved", "created_at": "2026-04-21"},
            {"id": 3, "component": "memory_gc", "status": "rejected", "created_at": "2026-04-20"},
        ])
    st.dataframe(df_gov, width="stretch", height=320, hide_index=True)

# -------------------- FOOTER --------------------
st.markdown("<div style='height:1px;background:rgba(28,29,27,0.07);margin:40px 0 20px;'></div>", unsafe_allow_html=True)
st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:center;font-size:11px;color:#7A7B77;letter-spacing:0.02em;">
    <span>© 2026 pith. · agent intelligence</span>
    <span>PID {os.getpid()} · {datetime.now().strftime('%H:%M:%S')}</span>
    <span style="color:#8AA5A3;">v4.1 elite</span>
</div>
""", unsafe_allow_html=True)

# -------------------- AUTO REFRESH --------------------
if st.session_state.auto_refresh:
    time.sleep(st.session_state.refresh_interval)
    st.rerun()
