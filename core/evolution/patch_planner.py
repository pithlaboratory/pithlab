"""Patch Planner: генерация гипотез патчей на основе кластеров сбоев."""
import sys
import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Добавляем корень проекта в path для импортов
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.cognition.router import call_llm as router_call_llm, RouterMode
from core.memory.manager import get_memory

logger = logging.getLogger(__name__)

# Директория для сохранения сгенерированных патчей
PATCH_OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "patches" / "pending"


def _extract_json_from_response(text: str) -> Optional[Dict[str, Any]]:
    """
    Извлекает валидный JSON из ответа LLM.
    Поддерживает: чистый JSON, JSON в ```json ... ```, JSON с преамбулой.
    """
    text = text.strip()
    
    # 1. Пробуем распарсить как есть
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # 2. Ищем код-блок ```json ... ``` или ``` ... ```
    code_block_match = re.search(r'```(?:json)?\s*(.*?)```', text, re.DOTALL)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1).strip())
        except json.JSONDecodeError:
            pass
    
    # 3. Ищем первую { и последнюю } в тексте (грубый, но рабочий fallback)
    brace_match = re.search(r'(\{.*\})', text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # 4. Не удалось извлечь
    logger.warning(f"Failed to extract JSON from LLM response. Preview: {text[:200]}...")
    return None


def _validate_hypothesis(h: Dict[str, Any], cluster_id: str) -> List[str]:
    """
    Проверяет гипотезу на наличие обязательных полей.
    Возвращает список предупреждений (пустой = всё ок).
    """
    warnings = []
    required_fields = ["summary", "root_cause", "component", "patch_type", "patch", "confidence", "test_plan"]
    
    for field in required_fields:
        if field not in h:
            warnings.append(f"Missing required field: {field}")
        elif field == "confidence" and not (0.0 <= h[field] <= 1.0):
            warnings.append(f"confidence must be in [0.0, 1.0], got {h[field]}")
    
    if h.get("patch_type") not in ("prompt", "config", "code", "router_policy", "memory_policy"):
        warnings.append(f"Unknown patch_type: {h.get('patch_type')}")
    
    if not h.get("patch") or len(str(h["patch"]).strip()) < 10:
        warnings.append("Patch content seems too short or empty")
    
    if warnings:
        logger.warning(f"Hypothesis validation warnings for cluster '{cluster_id}': {warnings}")
    
    return warnings


def _find_relevant_context(cluster_id: str, examples: List[Dict[str, Any]]) -> str:
    """
    Собирает релевантный контекст для генерации патча:
    - навыки по ключевым словам из cluster_id
    - примеры провалов (сокращённые)
    """
    memory = get_memory()
    parts = []
    
    # 1. Ищем навыки по ключевым словам из имени кластера
    # (напр. "openrouter_timeout" → ищем "timeout", "connection", "retry")
    keywords = re.findall(r'[a-z_]+', cluster_id.lower())
    skills = []
    for kw in keywords:
        if len(kw) > 3:  # игнорируем слишком короткие
            found = memory.find_procedures(kw)
            skills.extend(found)
    
    # Уникализируем по имени
    seen = set()
    unique_skills = []
    for s in skills:
        name = s.get("name", "")
        if name and name not in seen:
            seen.add(name)
            unique_skills.append(s)
    
    if unique_skills:
        lines = ["[RELEVANT PATTERNS FROM SKILL LIBRARY]"]
        for s in unique_skills[:3]:
            lines.append(f"- {s['name']}: {s['description'][:150]}")
        parts.append("\n".join(lines))
    
    # 2. Добавляем примеры провалов (короткие превью)
    if examples:
        lines = ["[FAILURE EXAMPLES]"]
        for i, ex in enumerate(examples[:3], 1):
            query = ex.get("user_input", ex.get("content", ""))[:100]
            response = ex.get("response", "")[:150]
            score = ex.get("metadata", {}).get("scores", {}).get("final", "N/A")
            lines.append(f"{i}. Q: {query}... | A: {response}... | score: {score}")
        parts.append("\n".join(lines))
    
    return "\n\n".join(parts) if parts else ""


def generate_hypothesis(
    failure_cluster_id: str,
    examples: List[Dict[str, Any]],
    export: bool = True,
    mode: Optional[str] = "core",  # router mode для генерации
) -> Dict[str, Any]:
    """
    Генерирует структурированную гипотезу патча для заданного кластера сбоев.
    
    Args:
        failure_cluster_id: имя кластера из miner (напр. "openrouter_timeout")
        examples: список эпизодов-примеров из этого кластера
        export: сохранить гипотезу в файл для review
        mode: router mode для вызова LLM (по умолчанию "core")
    
    Returns:
        Dict с полями:
            - summary, root_cause, component, patch_type, patch, confidence, test_plan
            - failure_cluster_id, generated_at, validation_warnings
    """
    # 1. Собираем контекст
    context = _find_relevant_context(failure_cluster_id, examples)
    
    # 2. Формируем промпт с жёсткой инструкцией по формату
    prompt = f"""{context}

Task: Analyze failure cluster '{failure_cluster_id}' and propose a structured patch hypothesis.

Instructions:
1. Identify the root cause of these failures.
2. Propose a concrete, actionable patch.
3. Return ONLY valid JSON with the following schema:

{{
  "summary": "One-sentence description of the patch",
  "root_cause": "Why these failures happen (technical explanation)",
  "component": "Which component to patch: persona | router_policy | memory_policy | orchestrator | interface | other",
  "patch_type": "prompt | config | code | router_policy | memory_policy",
  "patch": "The actual patch content (e.g., updated prompt text, YAML snippet, or code diff)",
  "confidence": 0.0-1.0 (your certainty in this hypothesis),
  "test_plan": "How to validate this patch (specific steps or test cases)"
}}

Output rules:
- Return ONLY the JSON object, no other text.
- Use double quotes for strings.
- Escape special characters properly.
- Do not include markdown code fences.
"""
    
    system_prompt = "You are an expert AI system architect specializing in self-improving systems. Focus on actionable, minimal, high-impact patches."
    
    try:
        # 3. Вызов LLM через router с корректной сигнатурой
        result = router_call_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            mode=mode,
        )
        
        response_text = result.get("content", "")
        model_used = result.get("model", "unknown")
        usage = result.get("usage", {})
        cost = result.get("cost_usd", 0.0)
        
    except Exception as e:
        logger.exception(f"LLM call failed for patch generation: {e}")
        # Возвращаем минимальную заглушку с информацией об ошибке
        return {
            "summary": f"Patch generation failed: {str(e)[:100]}",
            "root_cause": "LLM invocation error",
            "component": "patch_planner",
            "patch_type": "code",
            "patch": f"# Fix LLM call in patch_planner.py\n# Error: {e}",
            "confidence": 0.0,
            "test_plan": "Verify router connectivity and API key",
            "failure_cluster_id": failure_cluster_id,
            "generated_at": datetime.utcnow().isoformat(),
            "error": str(e),
            "validation_warnings": ["Generated from error fallback"],
        }
    
    # 4. Парсим JSON из ответа
    hypothesis = _extract_json_from_response(response_text)
    
    if not hypothesis:
        logger.error(f"Failed to parse hypothesis JSON for cluster '{failure_cluster_id}'")
        return {
            "summary": "JSON parsing failed",
            "root_cause": "LLM response format mismatch",
            "component": "patch_planner",
            "patch_type": "prompt",
            "patch": f"# Raw LLM response:\n{response_text[:500]}",
            "confidence": 0.0,
            "test_plan": "Improve prompt instructions or try different model",
            "failure_cluster_id": failure_cluster_id,
            "generated_at": datetime.utcnow().isoformat(),
            "raw_response_preview": response_text[:300],
            "validation_warnings": ["JSON parsing failed"],
        }
    
    # 5. Добавляем метаданные
    hypothesis["failure_cluster_id"] = failure_cluster_id
    hypothesis["generated_at"] = datetime.utcnow().isoformat()
    hypothesis["model_used"] = model_used
    hypothesis["tokens_used"] = usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
    hypothesis["cost_usd"] = cost
    
    # 6. Валидация
    warnings = _validate_hypothesis(hypothesis, failure_cluster_id)
    hypothesis["validation_warnings"] = warnings
    
    # 7. Экспорт в файл для review (опционально)
    if export:
        try:
            PATCH_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            safe_cluster_id = re.sub(r'[^a-z0-9_]', '_', failure_cluster_id.lower())
            filename = f"patch_{safe_cluster_id}_{timestamp}.json"
            output_path = PATCH_OUTPUT_DIR / filename
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(hypothesis, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Patch hypothesis exported to {output_path}")
            hypothesis["export_path"] = str(output_path)
            
        except Exception as e:
            logger.warning(f"Failed to export patch hypothesis: {e}")
    
    # 8. Итоговое логирование
    logger.info(
        f"Patch hypothesis generated for '{failure_cluster_id}': "
        f"component={hypothesis.get('component')}, type={hypothesis.get('patch_type')}, "
        f"confidence={hypothesis.get('confidence')}, warnings={len(warnings)}"
    )
    
    return hypothesis


def review_pending_patches() -> List[Dict[str, Any]]:
    """
    Возвращает список ожидающих review патчей из data/patches/pending/.
    """
    pending = []
    if not PATCH_OUTPUT_DIR.exists():
        return pending
    
    for path in PATCH_OUTPUT_DIR.glob("*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                patch = json.load(f)
                patch["_source_file"] = str(path)
                pending.append(patch)
        except Exception as e:
            logger.warning(f"Failed to load patch file {path}: {e}")
    
    # Сортируем по времени генерации (новые первыми)
    pending.sort(key=lambda x: x.get("generated_at", ""), reverse=True)
    return pending


if __name__ == "__main__":
    import sys
    
    # Настройка логгирования для CLI
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
    
    print("🔧 Pith Patch Planner — генерация гипотез патчей")
    print(f"   Output: {PATCH_OUTPUT_DIR}")
    print()
    
    # Демонстрация на тестовом кластере
    test_cluster = "openrouter_timeout"
    test_examples = [
        {
            "user_input": "Найди информацию про API лимиты",
            "response": "Ошибка: каналы связи недоступны (429)",
            "metadata": {"scores": {"final": 0.2}, "model": "error"},
        },
        {
            "user_input": "Почему не работает поиск?",
            "response": "Timeout при подключении к провайдеру",
            "metadata": {"scores": {"final": 0.3}, "model": "error"},
        },
    ]
    
    print(f"🧪 Генерация гипотезы для кластера: {test_cluster}")
    hypothesis = generate_hypothesis(test_cluster, test_examples, export=True)
    
    print(f"\n📋 Hypothesis summary:")
    print(f"   • {hypothesis.get('summary')}")
    print(f"   • Component: {hypothesis.get('component')}")
    print(f"   • Type: {hypothesis.get('patch_type')}")
    print(f"   • Confidence: {hypothesis.get('confidence')}")
    print(f"   • Warnings: {len(hypothesis.get('validation_warnings', []))}")
    
    if "export_path" in hypothesis:
        print(f"\n💾 Exported to: {hypothesis['export_path']}")
    
    print(f"\n✅ Patch planner ready for integration with miner loop")