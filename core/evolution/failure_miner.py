"""Mining failed episodes: анализ паттернов ошибок для self-improvement loop."""
import os
import json
import hashlib
import logging
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# ✅ Конфигурируемый путь к БД (через env или относительный)
DB_PATH = os.getenv(
    "PITH_EPISODES_DB",
    str(Path(__file__).parent.parent.parent / "data" / "episodes.db")
)
MINING_OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "mining"


class EpisodeMiner:
    """
    Анализатор провальных эпизодов для выявления системных паттернов ошибок.
    
    Архитектурное правило: miner работает с "чистыми" данными ядра,
    без привязки к persona или интерфейсу.
    """

    # Порог оценки для считания эпизода "провальным"
    FAILURE_SCORE_THRESHOLD = 0.5
    
    # Паттерны ошибок по ключевым словам (расширяемые)
    ERROR_PATTERNS = {
        "openrouter_timeout": ["таймаут", "timeout", "каналы связи", "504", "502", "429"],
        "model_unavailable": ["no endpoints found", "404", "модель недоступна", "not found"],
        "auth_error": ["401", "authentication", "invalid key", "неверный ключ"],
        "syntax_error": ["синтаксис", "syntax", "indentation", "nameerror", "typeerror"],
        "logic_error": ["неправильный ответ", "логика", "ошибка в рассуждении", "wrong reasoning"],
        "knowledge_gap": ["не знаю", "не могу ответить", "не хватает информации", "i don't know"],
        "context_overflow": ["контекст", "слишком длинный", "token limit", "max length"],
        "persona_leak": ["🎭 viktor", "как ии", "языковая модель", "as an ai"],  # утечка персоны в ядро
    }

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DB_PATH
        self._ensure_output_dir()

    def _ensure_output_dir(self) -> None:
        """Создаёт директорию для результатов майнинга, если нет."""
        MINING_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def _hash_content(self, content: str, max_len: int = 500) -> str:
        """Создаёт хеш контента для дедупликации (с обрезкой для стабильности)."""
        normalized = content.strip().lower()[:max_len]
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def _detect_patterns(self, content: str, metadata: Dict[str, Any]) -> List[str]:
        """
        Детектирует паттерны ошибок по контенту и метаданным.
        Возвращает список найденных паттернов.
        """
        detected = []
        text_lower = content.lower()
        
        # 1. Поиск по ключевым словам
        for pattern_name, keywords in self.ERROR_PATTERNS.items():
            if any(kw in text_lower for kw in keywords):
                detected.append(pattern_name)
        
        # 2. Анализ компонентов оценки из evaluator
        scores = metadata.get("scores", {})
        if scores.get("disclaimer", 1.0) == 0.0:
            detected.append("ai_disclaimer_leak")
        if scores.get("context", 1.0) < 0.5:
            detected.append("context_ignored")
        if scores.get("quality", 1.0) < 0.4:
            detected.append("low_quality_signal")
        
        # 3. Анализ технических метаданных
        if metadata.get("model") == "error":
            detected.append("runtime_error")
        if metadata.get("cost", 0) > 0.01 and scores.get("final", 1.0) < 0.3:
            detected.append("expensive_failure")  # дорого и плохо
        
        # 4. ✅ Анализ goal-aware полей из metadata
        runtime_mode = str(metadata.get("runtime_mode", "")).lower()
        goal_tags = metadata.get("goal_tags") or []
        if isinstance(goal_tags, str):
            goal_tags = [goal_tags]

        if runtime_mode == "diagnostics":
            detected.append("diagnostics_case")

        if "g_tactical_self_diagnostics" in goal_tags:
            detected.append("self_diagnostics_goal")
        
        # Уникальные паттерны
        return list(set(detected))

    def get_failed_episodes(
        self,
        limit: int = 100,
        score_threshold: Optional[float] = None,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Возвращает провальные эпизоды для анализа.
        
        Args:
            limit: максимальное количество эпизодов
            score_threshold: порог evaluator.scores.final (по умолчанию FAILURE_SCORE_THRESHOLD)
            user_id: фильтр по пользователю (опционально)
        """
        threshold = score_threshold if score_threshold is not None else self.FAILURE_SCORE_THRESHOLD
        episodes = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            # Базовый запрос: ищем по метаданным (оценка или явный статус)
            query = """
                SELECT user_id, content, metadata_json, ts
                FROM episodes 
                WHERE role = 'assistant'
                AND (
                    json_extract(metadata_json, '$.scores.final') < ?
                    OR json_extract(metadata_json, '$.outcome') IN ('failure', 'partial')
                )
            """
            params = [threshold]
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            query += " ORDER BY ts DESC LIMIT ?"
            params.append(limit)
            
            c.execute(query, params)
            rows = c.fetchall()
            
            for row in rows:
                try:
                    metadata = json.loads(row["metadata_json"]) if row["metadata_json"] else {}
                    episodes.append({
                        "user_id": row["user_id"],
                        "content": row["content"],
                        "metadata": metadata,
                        "ts": row["ts"],
                        "content_hash": self._hash_content(row["content"]),
                    })
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse metadata for episode: {e}")
                    continue
                    
        except sqlite3.Error as e:
            logger.error(f"Database error while fetching failed episodes: {e}")
            return []
        finally:
            if conn:
                conn.close()
        
        # ✅ Дедупликация по хешу контента
        seen_hashes = set()
        unique_episodes = []
        for ep in episodes:
            if ep["content_hash"] not in seen_hashes:
                seen_hashes.add(ep["content_hash"])
                unique_episodes.append(ep)
        
        logger.info(f"Found {len(unique_episodes)} unique failed episodes (from {len(episodes)} raw)")
        return unique_episodes

    def cluster_by_pattern(self, episodes: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Группирует эпизоды по детектированным паттернам ошибок.
        Один эпизод может попасть в несколько кластеров.
        """
        clusters = defaultdict(list)
        
        for ep in episodes:
            patterns = self._detect_patterns(ep["content"], ep["metadata"])
            if patterns:
                for pattern in patterns:
                    clusters[pattern].append(ep)
            else:
                clusters["uncategorized"].append(ep)
        
        # Сортируем кластеры по размеру (наиболее частые ошибки первыми)
        return dict(sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True))

    def generate_report(
        self,
        episodes: Optional[List[Dict[str, Any]]] = None,
        export: bool = True,
        timestamp: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Генерирует отчёт по провальным эпизодам.
        
        Args:
            episodes: список эпизодов (если None — загрузит автоматически)
            export: сохранить отчёт в JSON-файл
            timestamp: метка времени для имени файла (по умолчанию — сейчас)
        """
        if episodes is None:
            episodes = self.get_failed_episodes(limit=200)
        
        clusters = self.cluster_by_pattern(episodes)
        ts = timestamp or datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_episodes": len(episodes),
                "unique_patterns": len(clusters),
                "top_patterns": [
                    {"pattern": name, "count": len(items)}
                    for name, items in list(clusters.items())[:10]
                ],
            },
            "clusters": {
                name: [
                    {
                        "user_id": ep["user_id"],
                        "content_preview": ep["content"][:200] + ("..." if len(ep["content"]) > 200 else ""),
                        "score": ep["metadata"].get("scores", {}).get("final"),
                        "model": ep["metadata"].get("model"),
                        "cost": ep["metadata"].get("cost"),
                    }
                    for ep in items[:5]  # первые 5 примеров на кластер
                ]
                for name, items in clusters.items()
            },
            "recommendations": self._generate_recommendations(clusters),
        }
        
        if export:
            output_path = MINING_OUTPUT_DIR / f"mining_report_{ts}.json"
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
                logger.info(f"Mining report exported to {output_path}")
            except Exception as e:
                logger.error(f"Failed to export mining report: {e}")
        
        return report

    def _generate_recommendations(self, clusters: Dict[str, List]) -> List[str]:
        """Генерирует рекомендации на основе найденных паттернов."""
        recommendations = []
        
        if "openrouter_timeout" in clusters or "model_unavailable" in clusters:
            recommendations.append(
                "Рассмотреть увеличение retry_backoff или добавление резервных моделей в free/coder пулы"
            )
        if "auth_error" in clusters:
            recommendations.append(
                "Проверить валидность OPENROUTER_KEY в secrets.py / .env"
            )
        if "ai_disclaimer_leak" in clusters:
            recommendations.append(
                "Усилить фильтрацию persona-префиксов в cognition_graph.py / planner.py"
            )
        if "context_ignored" in clusters:
            recommendations.append(
                "Проверить build_context() в memory.manager: возможно, релевантные навыки не попадают в промпт"
            )
        if "expensive_failure" in clusters:
            recommendations.append(
                "Добавить ранний выход при низкой уверенности модели для экономии бюджета"
            )
        if "knowledge_gap" in clusters:
            recommendations.append(
                "Расширить базу процедур/навыков или добавить fallback на search-агент (Tera)"
            )
        
        # ✅ Рекомендация для goal-aware diagnostics
        if "diagnostics_case" in clusters or "self_diagnostics_goal" in clusters:
            recommendations.append(
                "Проверить качество DIAGNOSTICS-ответов и связь с g_tactical_self_diagnostics."
            )
        
        if not recommendations:
            recommendations.append("Критических паттернов не обнаружено — система стабильна")
        
        return recommendations


# ✅ Глобальный экземпляр для импорта
miner = EpisodeMiner()


if __name__ == "__main__":
    import sys
    
    # Настройка логгирования для CLI-запуска
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
    
    print("🔍 Pith Episode Miner — анализ провальных эпизодов")
    print(f"   DB: {DB_PATH}")
    print(f"   Output: {MINING_OUTPUT_DIR}")
    print()
    
    # Запуск майнинга
    episodes = miner.get_failed_episodes(limit=50)
    print(f"✓ Найдено {len(episodes)} уникальных провальных эпизодов")
    
    if not episodes:
        print("   Нет данных для анализа — система работает стабильно 🎉")
        sys.exit(0)
    
    # Генерация отчёта
    report = miner.generate_report(episodes, export=True)
    
    # Краткий вывод в консоль
    print("\n📊 Топ паттернов ошибок:")
    for item in report["summary"]["top_patterns"][:5]:
        print(f"   • {item['pattern']}: {item['count']} эпизодов")
    
    print("\n💡 Рекомендации:")
    for rec in report["recommendations"]:
        print(f"   → {rec}")
    
    print(f"\n✅ Полный отчёт сохранён в {MINING_OUTPUT_DIR}")