"""Политика безопасности для self-mod."""
from pathlib import Path

CRITICAL_FILES = [
    "interfaces/telegram_bot.py",
    "core/cognition/router.py",
    "core/memory/manager.py",
    "config.yaml",
    ".env",
]

class ChangeGuard:
    def __init__(self, repo_path: str = "/root/pith_v5"):
        self.repo_path = Path(repo_path)

    def is_critical(self, file_path: str) -> bool:
        """Проверяет, является ли файл критическим."""
        return any(file_path.endswith(cf) for cf in CRITICAL_FILES)

    def requires_approval(self, file_path: str, patch_content: str) -> bool:
        """
        Определяет, требуется ли явное одобрение человека.
        Критические файлы всегда требуют approval.
        """
        if self.is_critical(file_path):
            return True
        # Дополнительные эвристики: большой патч, удаление функций и т.д.
        if len(patch_content) > 5000:
            return True
        if "DELETE" in patch_content or "DROP" in patch_content:
            return True
        return False

    def pre_check(self, file_path: str, original: str, patched: str) -> tuple[bool, str]:
        """
        Базовая проверка перед применением патча.
        """
        # 1. Файл должен существовать
        full_path = self.repo_path / file_path
        if not full_path.exists():
            return (False, f"File {file_path} does not exist")

        # 2. Патч не должен удалять критические импорты
        critical_imports = ["from core.memory", "from core.cognition", "import yaml"]
        for imp in critical_imports:
            if imp in original and imp not in patched:
                return (False, f"Critical import removed: {imp}")

        return (True, "OK")
