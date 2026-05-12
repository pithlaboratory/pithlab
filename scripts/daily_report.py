from __future__ import annotations
import sqlite3
import os
from textwrap import shorten
import httpx
from datetime import datetime, timezone

DB_PATH = "/root/pith_v5/data/episodes.db"
TELEGRAM_TOKEN = os.environ["TG_TOKEN"]
OWNER_CHAT_ID = os.environ.get("OWNER_CHAT_ID", "191175045")

def fetch_llm_stats(conn):
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(cost),0), COALESCE(SUM(tokens_prompt+tokens_completion),0), COUNT(*) FROM llm_calls WHERE ts >= datetime('now','-1 day')")
    total_cost, total_tokens, total_calls = cur.fetchone()
    cur.execute("SELECT model_name, SUM(cost) c, SUM(tokens_prompt+tokens_completion) t, COUNT(*) n FROM llm_calls WHERE ts >= datetime('now','-1 day') GROUP BY model_name ORDER BY c DESC LIMIT 3")
    top_models = cur.fetchall()
    cur.execute("SELECT user_id, SUM(cost) c, SUM(tokens_prompt+tokens_completion) t, COUNT(*) n FROM llm_calls WHERE ts >= datetime('now','-1 day') GROUP BY user_id ORDER BY c DESC LIMIT 3")
    top_users = cur.fetchall()
    cur.execute("SELECT ts, user_id, model_name, cost, tokens_prompt+tokens_completion, task_type FROM llm_calls WHERE ts >= datetime('now','-1 day') ORDER BY cost DESC LIMIT 3")
    top_calls = cur.fetchall()
    return {
        "total_cost": float(total_cost or 0),
        "total_tokens": int(total_tokens or 0),
        "total_calls": int(total_calls or 0),
        "top_models": top_models,
        "top_users": top_users,
        "top_calls": top_calls,
    }

def fetch_quality_stats(conn):
    cur = conn.cursor()
    cur.execute("SELECT AVG(CAST(json_extract(metadata,'$.eval.persona_coherence') AS REAL)), AVG(CAST(json_extract(metadata,'$.eval.context_use') AS REAL)), COUNT(*), SUM(CASE WHEN CAST(json_extract(metadata,'$.eval.persona_coherence') AS REAL) < 0.5 THEN 1 ELSE 0 END) FROM episodes WHERE role='assistant' AND ts >= datetime('now','-1 day')")
    avg_p, avg_c, total_ans, broken = cur.fetchone()
    cur.execute("SELECT ts, user_id, content, CAST(json_extract(metadata,'$.eval.persona_coherence') AS REAL) AS score FROM episodes WHERE role='assistant' AND ts >= datetime('now','-1 day') AND json_extract(metadata,'$.eval.persona_coherence') IS NOT NULL ORDER BY score ASC LIMIT 3")
    worst = cur.fetchall()
    return {
        "avg_persona": float(avg_p or 0),
        "avg_context": float(avg_c or 0),
        "total_answers": int(total_ans or 0),
        "broken_persona": int(broken or 0),
        "worst_persona": worst,
    }

def build_report(llm, qa):
    lines = [f"📊 Pith Daily Report ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')})", ""]
    lines.append(f"💰 Cost: ${llm['total_cost']:.4f} | Tokens: {llm['total_tokens']} | Calls: {llm['total_calls']}")
    if llm["top_models"]:
        lines.append("- Top models:")
        for name, c, t, n in llm["top_models"]:
            lines.append(f"  • {name}: ${c:.4f}, {t} tok, {n} calls")
    lines.append("")
    lines.append(f"🎭 Quality: Persona={qa['avg_persona']:.2f} Context={qa['avg_context']:.2f} | Answers: {qa['total_answers']} (broken: {qa['broken_persona']})")
    if qa["worst_persona"]:
        lines.append("- Worst persona:")
        for ts, uid, content, score in qa["worst_persona"]:
            preview = shorten(content.replace("\n", " "), width=100, placeholder="…")
            lines.append(f"  • {ts} | {uid} | {score:.2f}: {preview}")
    if llm["top_calls"]:
        lines.append("")
        lines.append("🔥 Most expensive:")
        for ts, uid, model, cost, tokens, task in llm["top_calls"]:
            lines.append(f"  • {ts} | {uid} | {model} | ${cost:.4f} | {tokens} tok | {task}")
    return "\n".join(lines)

def send(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": OWNER_CHAT_ID, "text": text[:4000]}
    httpx.post(url, json=payload, timeout=15)

def main():
    conn = sqlite3.connect(DB_PATH)
    llm = fetch_llm_stats(conn)
    qa = fetch_quality_stats(conn)
    conn.close()
    report = build_report(llm, qa)
    send(report)

if __name__ == "__main__":
    main()
