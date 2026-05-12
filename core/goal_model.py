"""
Pith v5 — Goal Model
Author: Pith Lab
License: MIT

Единая точка правды про цель системы Pith и её подцели.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class SubGoal:
    id: str
    title: str
    description: str
    level: str  # "operational" | "tactical" | "strategic"
    parent_id: str | None = None
    success_criteria: List[str] = field(default_factory=list)


@dataclass
class GoalModel:
    core_purpose: str
    subgoals: List[SubGoal]


def get_goal_model() -> GoalModel:
    """
    Возвращает текущую модель целей Pith.
    Это то, чем должен руководствоваться оркестратор и интерфейсы.
    """
    subgoals: List[SubGoal] = [
        SubGoal(
            id="g_operational_effective_work",
            title="Эффективное решение текущей задачи пользователя",
            level="operational",
            parent_id=None,
            description=(
                "Каждый запрос пользователя должен приводить к реальному сдвигу в его работе: "
                "код, архитектура, анализ, план, эксперимент."
            ),
            success_criteria=[
                "Ответ содержит конкретные действия, а не общие рассуждения",
                "Пользователь может сразу применить результат в своей системе/коде/решении",
            ],
        ),
        SubGoal(
            id="g_tactical_self_diagnostics",
            title="Встроенная самодиагностика и корректировка",
            level="tactical",
            parent_id="g_operational_effective_work",
            description=(
                "Pith отслеживает собственные ошибки и смещения, фиксирует их и использует "
                "для улучшения последующих решений."
            ),
            success_criteria=[
                "Есть хотя бы один модуль, который анализирует качество ответа (evaluator/PSM)",
                "Ошибки и слабые места сохраняются в память/логи и могут быть проанализированы",
            ],
        ),
        SubGoal(
            id="g_tactical_orchestration_quality",
            title="Качественная оркестрация модулей",
            level="tactical",
            parent_id="g_operational_effective_work",
            description=(
                "Оркестратор выбирает нужные модели и инструменты по задаче, бюджету и контексту, "
                "избегая лишних шагов и бессмысленных вызовов."
            ),
            success_criteria=[
                "Есть трассировка решений роутера и планировщика",
                "Бюджет учитывается при выборе модели",
            ],
        ),
        SubGoal(
            id="g_strategic_evolution",
            title="Эволюция системы на основе реальных задач",
            level="strategic",
            parent_id=None,
            description=(
                "Pith со временем меняет свою архитектуру и поведение, исходя из реальных задач, "
                "ошибок и обратной связи, а не абстрактных бенчмарков."
            ),
            success_criteria=[
                "Есть механизм фиксации эволюционных изменений (версии, changelog)",
                "Решения о модификации системы опираются на накопленные данные (логи, eval)",
            ],
        ),
    ]

    return GoalModel(
        core_purpose=(
            "Pith существует для устойчивого, проверяемого и эволюционирующего решения "
            "реальных задач пользователя, где результат важнее формы ответа."
        ),
        subgoals=subgoals,
    )


def as_dict() -> Dict[str, Any]:
    """Удобный helper, если нужно отдать модель целей в JSON-подобном виде."""
    gm = get_goal_model()
    return {
        "core_purpose": gm.core_purpose,
        "subgoals": [
            {
                "id": sg.id,
                "title": sg.title,
                "description": sg.description,
                "level": sg.level,
                "parent_id": sg.parent_id,
                "success_criteria": sg.success_criteria,
            }
            for sg in gm.subgoals
        ],
    }


def get_subgoal_by_id(subgoal_id: str) -> SubGoal | None:
    """
    Возвращает подцель по её ID или None, если не найдена.
    """
    gm = get_goal_model()
    for subgoal in gm.subgoals:
        if subgoal.id == subgoal_id:
            return subgoal
    return None


def list_subgoals_by_level(level: str) -> List[SubGoal]:
    """
    Возвращает список подцелей по указанному уровню.
    """
    gm = get_goal_model()
    return [subgoal for subgoal in gm.subgoals if subgoal.level == level]
