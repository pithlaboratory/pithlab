"""Патч-исполнитель. Применяет изменения к файлам."""
import os
import shutil
from pathlib import Path
from datetime import datetime

class PatchExecutor:
    def __init__(self, repo_path: Path = None):
        if repo_path is None:
            repo_path = Path("/root/pith_v5")
        self.repo_path = repo_path

    def apply_patch(self, relative_path: str, new_content: str) -> tuple[bool, str]:
        """
        Применяет патч к файлу.
        Возвращает (success, commit_hash_or_error).
        """
        full_path = self.repo_path / relative_path

        # Создаём бэкап
        backup_path = full_path.with_suffix(full_path.suffix + f".bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        try:
            if full_path.exists():
                shutil.copy2(full_path, backup_path)
            else:
                full_path.parent.mkdir(parents=True, exist_ok=True)

            # Записываем новый контент
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            # Заглушка для "коммита" — возвращаем хэш на основе времени
            commit_hash = datetime.now().strftime("%Y%m%d%H%M%S")
            return True, commit_hash
        except Exception as e:
            # Пытаемся восстановить из бэкапа
            if backup_path.exists():
                shutil.copy2(backup_path, full_path)
            return False, str(e)
