"""Cognition Graph с агентами Plex, Tera, Hex и GitHub-интеграцией.
Архитектура: Pith = kernel, Viktor = persona mode (style only).
"""
import os
import logging
import requests
import re
import hashlib
from typing import TypedDict, Optional, Dict, Any
from langgraph.graph import StateGraph, END

from core.memory.manager import get_memory
from core.router import call_llm as router_call_llm, RouterMode
from core.governance.rollout_manager import RuntimeResolver

logger = logging.getLogger(__name__)


class CognitionState(TypedDict):
    user_id: str
    user_input: str
    enriched_prompt: str
    system_prompt: str          # runtime_directives (ядро)
    persona_directives: str     # persona_directives (стиль/тон)
    response: Optional[str]
    model_used: str
    outcome: str
    tokens_used: int
    cost_usd: float
    intent: str
    tera_results: Optional[str]
    tera_summary: Optional[str]
    hex_insights: Optional[str]
    plex_coherence: Optional[float]
    plex_suggestions: Optional[str]
    coda_patch: Optional[str]
    coda_commit: Optional[str]


def fetch_github_repo(url: str) -> dict:
    """Fetches GitHub repo metadata and key files."""
    match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
    if not match:
        return {"error": "Invalid GitHub URL"}
    owner, repo = match.groups()
    repo = repo.replace(".git", "")
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents"
    headers = {"Accept": "application/vnd.github.v3+json"}
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    try:
        resp = requests.get(api_url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return {"error": f"GitHub API error: {resp.status_code}"}
        contents = resp.json()
        files = []
        readme_content = ""
        structure = []
        for item in contents:
            if item["type"] == "file":
                files.append(item["name"])
                name_lower = item["name"].lower()
                if name_lower in ["readme.md", "pyproject.toml", "setup.py", "graph.py", "router.py", "orchestrator.py"]:
                    file_resp = requests.get(item["download_url"], timeout=15)
                    if file_resp.status_code == 200:
                        if name_lower == "readme.md":
                            readme_content = file_resp.text[:3000]
                        else:
                            structure.append(f"=== {item['name']} ===\n{file_resp.text[:2000]}")
            elif item["type"] == "dir":
                structure.append(f"[DIR] {item['name']}")
        return {
            "files": files,
            "readme": readme_content,
            "structure": "\n".join(structure),
            "owner": owner,
            "repo": repo
        }
    except Exception as e:
        return {"error": str(e)}


def resolve_persona_version(user_id: str) -> str:
    """Определяет версию персоны через RuntimeResolver (canary rollout)."""
    try:
        resolver = RuntimeResolver()
        ring = "canary" if (hash(user_id) % 100) < 5 else "full"
        version = resolver.resolve_with_fallback("persona", ring)
        return version
    except Exception as e:
        logger.warning(f"RuntimeResolver failed, using default: {e}")
        return "default"


def build_persona_directives(version: str = "default") -> str:
    """
    Возвращает persona-директивы (стиль/тон) в зависимости от версии.
    Ядро (runtime_directives) остаётся неизменным — меняется только подача.
    """
    personas = {
        "viktor": """
Style: sharp, strategic, concise, self-possessed.
Tone: elite, nocturnal, deliberate — never unserious.
Phrasing: high-signal, direct judgment, clear execution paths.
Avoid: clowning, filler, chaos, excessive explanation.
""",
        "coach": """
Style: supportive, structured, growth-oriented.
Tone: warm but precise, encouraging but honest.
Phrasing: actionable steps, reflective questions, progress markers.
Avoid: vagueness, over-praise, abstract theory without practice.
""",
        "default": """
Style: clear, grounded, technically precise.
Tone: professional, neutral, focused on utility.
Phrasing: direct answers, structured reasoning, minimal fluff.
Avoid: speculation without basis, unnecessary verbosity.
"""
    }
    return personas.get(version, personas["default"])


def build_context_node(state: CognitionState) -> CognitionState:
    memory = get_memory()
    user_id = state["user_id"]
    text = state["user_input"]
    
    # ✅ Определяем версию персоны для этого пользователя
    persona_version = resolve_persona_version(user_id)
    persona_directives = build_persona_directives(persona_version)
    
    # Строим контекст из памяти
    memory_context = memory.build_context(user_id, text) or ""
    if not memory_context:
        recent = memory.get_recent_episodes(user_id, 3)
        if recent:
            lines = ["[ПАМЯТЬ: ПОСЛЕДНИЕ ДИАЛОГИ]"]
            for ep in recent:
                lines.append(f"{ep['role']}: {ep['content'][:200]}")
            memory_context = "\n".join(lines)
    
    # Навыки/процедуры
    skills_context = ""
    procedures = memory.find_procedures(text)
    if procedures:
        lines = ["[РЕЛЕВАНТНЫЕ НАВЫКИ]"]
        for p in procedures[:2]:
            lines.append(f"- {p['name']}: {p['description'][:150]}")
        skills_context = "\n".join(lines)
    
    # Собираем enriched_prompt: контекст + вопрос
    full_context = memory_context
    if skills_context:
        full_context = f"{memory_context}\n\n{skills_context}" if memory_context else skills_context
    enriched = f"{full_context}\n\nВопрос: {text}" if full_context else text
    
    return {
        **state,
        "enriched_prompt": enriched,
        "persona_directives": persona_directives,  # ✅ Выносим persona отдельно
    }


def intent_node(state: CognitionState) -> CognitionState:
    """Classifies user intent for routing. Task-based, not persona-based."""
    text = state["user_input"].lower()
    if any(kw in text for kw in ["найди", "поищи", "что такое", "расскажи про", "актуальн", "репозиторий", "github"]):
        intent = "search"
    elif any(kw in text for kw in ["код", "исправь", "coda", "патч", "файл"]):
        intent = "code"
    elif any(kw in text for kw in ["стратег", "прогноз", "тренд", "анализ"]):
        intent = "strategy"
    else:
        intent = "general"
    logger.info(f"Intent classified: {intent}")
    return {**state, "intent": intent}


def call_llm_node(state: CognitionState) -> CognitionState:
    """
    Вызов LLM через router с разделением директив:
    - system_prompt = runtime_directives (ядро: что делать)
    - persona_directives = стиль/тон (как отвечать)
    """
    try:
        # ✅ Собираем финальный системный промпт: ядро + персона
        runtime_directives = state.get("system_prompt", "")
        persona_directives = state.get("persona_directives", "")
        
        full_system_prompt = runtime_directives
        if persona_directives.strip():
            full_system_prompt = f"{runtime_directives}\n\n[STYLE GUIDELINES]\n{persona_directives}".strip()
        
        # ✅ Вызываем router с корректной сигнатурой
        result = router_call_llm(
            prompt=state["enriched_prompt"],
            system_prompt=full_system_prompt,
            mode=RouterMode.CORE,  # можно динамически выбирать по intent
        )
        
        # ✅ Парсим ответ согласно контракту router.py
        response_text = result.get("content") or result.get("response") or str(result)
        model_used = result.get("model") or result.get("model_id") or "unknown"
        usage = result.get("usage", {})
        tokens_used = usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
        cost_usd = result.get("cost_usd", result.get("cost", 0.0))
        
        # ✅ НЕ добавляем префиксы здесь — это задача интерфейсного слоя!
        # Интерфейс (Telegram) сам решит, показывать ли "Pith:", "Viktor:", etc.
        
        return {
            **state,
            "response": response_text,  # чистый ответ, без префиксов
            "outcome": "success",
            "model_used": model_used,
            "tokens_used": tokens_used,
            "cost_usd": cost_usd,
        }
    except Exception as e:
        logger.exception("LLM node error")
        return {
            **state,
            "response": f"[sys] Ошибка связи с ядром. {str(e)[:100]}",  # без префикса персоны
            "outcome": "failure",
            "model_used": "error",
            "tokens_used": 0,
            "cost_usd": 0.0,
        }


def tera_node(state: CognitionState) -> CognitionState:
    """Tera: search & research agent with GitHub integration."""
    try:
        from core.action.tavily_tool import tavily_search
    except ImportError:
        logger.error("tavily_search not available")
        return {**state, "tera_results": "Ошибка: Tavily не установлен.", "tera_summary": ""}
    try:
        query = state["user_input"]
        results = tavily_search(query, max_results=3)
        if not results:
            return {**state, "tera_results": "Ничего не найдено.", "tera_summary": ""}
        summary = []
        full_content = []
        for r in results:
            summary.append(f"- {r['title']}: {r['url']}")
            full_content.append(r.get('content', '')[:500])
            if "github.com" in r['url']:
                repo_data = fetch_github_repo(r['url'])
                if "error" not in repo_data:
                    full_content.append(f"\n=== REPOSITORY ANALYSIS: {repo_data['owner']}/{repo_data['repo']} ===")
                    full_content.append(f"Files ({len(repo_data['files'])}): {', '.join(repo_data['files'][:20])}")
                    if repo_data['readme']:
                        full_content.append(f"README excerpt:\n{repo_data['readme'][:1500]}")
                    if repo_data['structure']:
                        full_content.append(f"Key files content:\n{repo_data['structure'][:2000]}")
                else:
                    full_content.append(f"GitHub fetch error: {repo_data['error']}")
        return {
            **state,
            "tera_results": "\n".join(full_content),
            "tera_summary": "\n".join(summary),
        }
    except Exception as e:
        logger.exception("Tera node error")
        return {**state, "tera_results": f"Ошибка поиска: {e}", "tera_summary": ""}


def hex_node(state: CognitionState) -> CognitionState:
    """Hex: strategic foresight agent."""
    try:
        prompt = f"""
Ты — стратегический аналитик Hex. Проанализируй следующие данные и выдели ключевые тренды, риски и возможности на горизонте 5-10 лет.

Запрос пользователя: {state['user_input']}
Результаты поиска Tera: {state.get('tera_results', '')}

Дай структурированный ответ:
- Тренды
- Риски
- Возможности
- Рекомендации
"""
        # ✅ Вызов с разделением директив
        persona_directives = state.get("persona_directives", "")
        full_system = f"You are a strategic foresight expert.\n\n[STYLE]\n{persona_directives}".strip()
        
        result = router_call_llm(prompt=prompt, system_prompt=full_system, mode=RouterMode.CORE)
        insights = result.get("content", "") if isinstance(result, dict) else str(result)
        return {**state, "hex_insights": insights}
    except Exception as e:
        logger.exception("Hex node error")
        return {**state, "hex_insights": f"Ошибка Hex: {e}"}


def plex_node(state: CognitionState) -> CognitionState:
    """Plex: coherence checker & response optimizer."""
    try:
        from agents.plex import PlexAgent
        agent = PlexAgent()
        coherence, suggestions = agent.analyze(
            response=state.get("response", ""),
            system_prompt=state.get("system_prompt", ""),
            user_input=state.get("user_input", "")
        )
        return {**state, "plex_coherence": coherence, "plex_suggestions": suggestions}
    except ImportError:
        logger.warning("PlexAgent not available, skipping coherence check")
        return {**state, "plex_coherence": None, "plex_suggestions": None}
    except Exception as e:
        logger.exception("Plex node error")
        return {**state, "plex_coherence": None, "plex_suggestions": str(e)}


def eval_node(state: CognitionState) -> CognitionState:
    """Evaluation & metrics collection point."""
    # Здесь можно добавить логирование, метрики, сохранение эпизода
    return state


def route_after_intent(state: CognitionState) -> str:
    """Routing based on intent (task-based, not persona-based)."""
    if state.get("intent") == "search":
        return "tera"
    return "call_llm"


def route_after_tera(state: CognitionState) -> str:
    """After search: strategy → Hex, else → direct LLM."""
    if state.get("intent") == "strategy":
        return "hex"
    return "call_llm"


def build_graph() -> StateGraph:
    workflow = StateGraph(CognitionState)
    
    # Nodes
    workflow.add_node("build_context", build_context_node)
    workflow.add_node("intent", intent_node)
    workflow.add_node("call_llm", call_llm_node)
    workflow.add_node("tera", tera_node)
    workflow.add_node("hex", hex_node)
    workflow.add_node("plex", plex_node)
    workflow.add_node("eval", eval_node)
    
    # Edges
    workflow.set_entry_point("build_context")
    workflow.add_edge("build_context", "intent")
    workflow.add_conditional_edges("intent", route_after_intent, {"tera": "tera", "call_llm": "call_llm"})
    workflow.add_edge("call_llm", "plex")
    workflow.add_conditional_edges("tera", route_after_tera, {"hex": "hex", "call_llm": "call_llm"})
    workflow.add_edge("hex", "call_llm")
    workflow.add_edge("plex", "eval")
    workflow.add_edge("eval", END)
    
    return workflow.compile()


# ✅ Экспортируем готовый граф
cognition_graph = build_graph() 