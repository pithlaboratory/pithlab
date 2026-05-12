from dataclasses import dataclass, field
from typing import Any, Dict, List

@dataclass
class MemoryContext:
    """Контейнер для всех типов памяти пользователя"""
    user_id: str
    profile: Dict[str, Any] = field(default_factory=dict)
    episodic: List[Dict[str, Any]] = field(default_factory=list)  # Последние диалоги
    semantic: List[str] = field(default_factory=list)             # Похожие контексты
    procedural: List[Dict[str, Any]] = field(default_factory=list) # Известные процедуры

    def to_prompt_block(self, max_items: int = 5) -> str:
        """Форматирование в текстовый блок для LLM"""
        parts = []

        # Профиль пользователя
        if self.profile:
            lines = [f"- {k}: {v}" for k, v in self.profile.items() if v][:max_items]
            if lines:
                parts.append("[ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ]\n" + "\n".join(lines))

        # Последние диалоги
        if self.episodic:
            lines = []
            for ep in self.episodic[:max_items]:
                role = ep.get('role', 'unknown')
                content = ep.get('content', '')[:200]
                lines.append(f"{role}: {content}")
            if lines:
                parts.append("[ПОСЛЕДНИЕ ДИАЛОГИ]\n" + "\n".join(lines))

        # Похожие контексты
        if self.semantic:
            lines = [f"- {s[:300]}" for s in self.semantic[:max_items]]
            if lines:
                parts.append("[ПОХОЖИЕ КОНТЕКСТЫ]\n" + "\n".join(lines))

        # Известные процедуры
        if self.procedural:
            lines = [f"- {p['name']}: {p['description']}" for p in self.procedural[:max_items]]
            if lines:
                parts.append("[ИЗВЕСТНЫЕ ПРОЦЕДУРЫ]\n" + "\n".join(lines))

        return "\n\n".join(parts) if parts else ""

    def is_empty(self) -> bool:
        return not (self.profile or self.episodic or self.semantic or self.procedural)
