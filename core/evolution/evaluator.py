"""Evaluator: метрики качества ответов для self-improvement loop."""
from __future__ import annotations
import re
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class Evaluator:
    """
    Оценщик качества ответов Pith.
    
    Архитектурное правило: evaluator работает с "чистыми" ответами ядра,
    без префиксов интерфейса (🎭 Viktor Vaughn:, Pith:, etc.).
    """

    # Фразы-маркеры "уклонения" ИИ (снижают оценку)
    AI_DISCLAIMER_PHRASES = [
        "как языковая модель",
        "как ии",
        "я не могу",
        "я не имею доступа",
        "я не могу предоставить",
        "as an ai",
        "i cannot",
        "i'm unable to",
    ]

    # Маркеры качественного ответа (повышают оценку)
    QUALITY_SIGNALS = [
        "пошагово", "структура", "план", "рекомендация",
        "пример", "код", "патч", "исправление",
        "причина", "следствие", "вывод", "итог",
    ]

    def __init__(self):
        self.pending: Dict[str, float] = {}

    def start_task(self, task_id: str) -> None:
        """Начинает отслеживание задачи для замера latency."""
        self.pending[task_id] = time.time()

    def record_user_feedback(
        self,
        task_id: str,
        feedback: str,
        reason: Optional[str] = None,
    ) -> None:
        """
        Записывает user feedback (positive/negative) для задачи.
        
        Args:
            task_id: ID задачи
            feedback: "positive" или "negative"
            reason: опциональное пояснение от пользователя
        """
        logger.info(
            "User feedback: task=%s feedback=%s reason=%s",
            task_id, feedback, reason
        )
        # TODO: persist to DB or metrics system for long-term learning

    def _check_ai_disclaimers(self, response_text: str) -> float:
        """
        Проверяет наличие фраз-уклонений ("как ИИ", "я не могу").
        Возвращает 0.0 если найдено, иначе 1.0.
        """
        lower = response_text.lower()
        for phrase in self.AI_DISCLAIMER_PHRASES:
            if phrase in lower:
                return 0.0
        return 1.0

    def _check_quality_signals(self, response_text: str) -> float:
        """
        Оценивает наличие маркеров качественного ответа.
        Возвращает долю найденных сигналов (0.0–1.0).
        """
        if not response_text.strip():
            return 0.0
        
        lower = response_text.lower()
        found = sum(1 for signal in self.QUALITY_SIGNALS if signal in lower)
        # Нормализуем: 3+ сигнала = 1.0, 0 сигналов = 0.3 (база)
        score = 0.3 + min(0.7, found / len(self.QUALITY_SIGNALS))
        return min(1.0, max(0.0, score))

    def _check_context_use(self, response_text: str, context: Optional[str]) -> float:
        """
        Проверяет, использовал ли ответ предоставленный контекст.
        Если контекст пуст — возвращает 1.0 (нечего использовать).
        """
        if not context or not context.strip():
            return 1.0
        
        score = 1.0
        # Если в контексте есть навыки — проверяем их упоминание
        if "[РЕЛЕВАНТНЫЕ НАВЫКИ]" in context:
            skill_names = re.findall(r"- ([^:]+):", context)
            if skill_names:
                used = any(s.lower() in response_text.lower() for s in skill_names)
                if not used:
                    score -= 0.3  # небольшой штраф за игнор навыков
        
        # Если контекст длинный, но ответ очень короткий — возможный признак игнора
        if len(context) > 500 and len(response_text) < 50:
            score -= 0.2
        
        return max(0.0, min(1.0, score))

    def _check_response_length(self, response_text: str, task_type: str = "general") -> float:
        """
        Оценивает адекватность длины ответа типу задачи.
        """
        length = len(response_text.strip())
        
        if task_type in ("coding", "debug", "patch"):
            # Для кода: ожидаем минимум 100 символов
            return 1.0 if length >= 100 else 0.5
        elif task_type in ("strategy", "analysis", "research"):
            # Для анализа: ожидаем развёрнутый ответ
            return 1.0 if length >= 300 else 0.6
        else:
            # Для общего чата: гибко
            if 20 <= length <= 2000:
                return 1.0
            elif length < 20:
                return 0.4  # слишком кратко
            else:
                return 0.9  # немного длинновато, но ок
        
    def evaluate_response(
        self,
        task_id: str,
        user_id: str,
        response: str,
        model: str,
        tokens: int,
        cost: float,
        user_feedback: Optional[str],
        context_used: Optional[str],
        task_type: str = "general",
    ) -> Dict[str, Any]:
        """
        Оценивает ответ по множеству метрик.
        
        Args:
            response: чистый текст ответа (без префиксов интерфейса!)
            task_type: тип задачи для контекстной оценки длины
        """
        start = self.pending.pop(task_id, time.time())
        latency = (time.time() - start) * 1000

        # ✅ Компоненты оценки
        disclaimer_score = self._check_ai_disclaimers(response)
        quality_score = self._check_quality_signals(response)
        context_score = self._check_context_use(response, context_used)
        length_score = self._check_response_length(response, task_type)

        # ✅ Итоговая оценка: взвешенная средняя
        weights = {
            "disclaimer": 0.3,   # критично: уклонения ИИ недопустимы
            "quality": 0.3,      # важно: сигнал/шум
            "context": 0.2,      # желательно: использование памяти
            "length": 0.2,       # полезно: адекватность объёма
        }
        final_score = (
            disclaimer_score * weights["disclaimer"] +
            quality_score * weights["quality"] +
            context_score * weights["context"] +
            length_score * weights["length"]
        )

        evaluation = {
            "task_id": task_id,
            "user_id": user_id,
            "ts": datetime.utcnow().isoformat(),
            "model": model,
            "tokens": tokens,
            "cost": cost,
            "latency_ms": latency,
            "scores": {
                "disclaimer": disclaimer_score,
                "quality": quality_score,
                "context": context_score,
                "length": length_score,
                "final": round(final_score, 3),
            },
            "user_feedback": user_feedback,
            "task_type": task_type,
        }

        # ✅ Логирование в стиле % (без f-string)
        logger.info(
            "Eval: task=%s user=%s model=%s score=%.2f tokens=%s cost=%.4f",
            task_id, user_id, model, final_score, tokens, cost
        )
        
        # ✅ Предупреждение при низкой оценке
        if final_score < 0.5:
            logger.warning(
                "Low evaluation score (%.2f) for task %s: "
                "disclaimer=%.2f, quality=%.2f, context=%.2f, length=%.2f",
                final_score, task_id, disclaimer_score, quality_score, context_score, length_score
            )

        return evaluation

    def to_episode_metadata(self, evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Преобразует результат оценки в нормализованный patch для metadata эпизода.

        Args:
            evaluation: результат evaluate_response()

        Returns:
            словарь с полями для добавления в metadata_json
        """
        scores = evaluation.get("scores", {})
        final_score = scores.get("final", 0.0)

        # Определяем outcome на основе финальной оценки
        if final_score >= 0.75:
            outcome = "success"
        elif 0.5 <= final_score < 0.75:
            outcome = "partial"
        else:
            outcome = "failure"

        return {
            "model": evaluation.get("model"),
            "tokens": evaluation.get("tokens"),
            "cost": evaluation.get("cost"),
            "latency_ms": evaluation.get("latency_ms"),
            "task_type": evaluation.get("task_type"),
            "scores": scores,
            "outcome": outcome,
        }


# ✅ Глобальный экземпляр для импорта
evaluator = Evaluator()