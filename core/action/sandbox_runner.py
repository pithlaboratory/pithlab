"""Безопасный запуск кода в Docker-песочнице."""
import subprocess
import tempfile
import os
from pathlib import Path

class SandboxRunner:
    def __init__(self, image: str = "python:3.12-slim", timeout: int = 30):
        self.image = image
        self.timeout = timeout

    def run_code(self, code: str) -> tuple[bool, str, str]:
        """
        Запускает код в Docker-контейнере.
        Возвращает (успех, stdout, stderr).
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            tmp_path = f.name

        try:
            cmd = [
                "docker", "run", "--rm",
                "--memory", "256m",
                "--cpus", "0.5",
                "--network", "none",
                "-v", f"{tmp_path}:/code.py:ro",
                self.image,
                "python", "/code.py"
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            return (result.returncode == 0, result.stdout, result.stderr)
        except subprocess.TimeoutExpired:
            return (False, "", f"Timeout after {self.timeout}s")
        finally:
            os.unlink(tmp_path)

    def test_patch(self, original_code: str, patched_code: str) -> tuple[bool, str]:
        """
        Проверяет, что патч не ломает синтаксис и базовое исполнение.
        """
        # 1. Проверка синтаксиса
        try:
            compile(patched_code, "<patch>", "exec")
        except SyntaxError as e:
            return (False, f"Syntax error: {e}")

        # 2. Прогон в песочнице
        success, stdout, stderr = self.run_code(patched_code)
        if not success:
            return (False, f"Runtime error:\n{stderr}")

        return (True, stdout)

    def test_patch(self, original_code: str, patched_code: str) -> tuple[bool, str]:
        """Проверяет, что патч не ломает синтаксис и базовое исполнение."""
        # 1. Проверка синтаксиса
        try:
            compile(patched_code, "<patch>", "exec")
        except SyntaxError as e:
            return (False, f"Syntax error: {e}")

        # 2. Прогон в песочнице
        success, stdout, stderr = self.run_code(patched_code)
        if not success:
            return (False, f"Runtime error:\n{stderr}")

        return (True, stdout)
