"""Skill Compiler — превращает markdown-навыки в исполнимые JSON-playbooks."""
import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
import yaml

logger = logging.getLogger(__name__)


class SkillCompiler:
    """
    Компилятор навыков: сканирует *.md с YAML-фронтматтером,
    извлекает метаданные и сохраняет индекс в JSON для быстрого поиска.
    """

    def __init__(
        self,
        skills_dir: Optional[str] = None,
        output_index: Optional[str] = None,
        max_body_length: int = 5000,
    ):
        # Пути относительно корня проекта
        project_root = Path(__file__).parent.parent.parent
        self.skills_dir = Path(skills_dir) if skills_dir else project_root / "skills" / "mined"
        self.output_index = Path(output_index) if output_index else project_root / "skills" / "index.json"
        self.max_body_length = max_body_length
        self.skills: List[Dict] = []

    def extract_yaml_frontmatter(self, content: str) -> Tuple[Optional[Dict], str]:
        """Извлекает YAML-фронтматтер из markdown."""
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
        if match:
            try:
                frontmatter = yaml.safe_load(match.group(1))
                if not isinstance(frontmatter, dict):
                    logger.warning("Frontmatter is not a valid dictionary, treating as plain markdown")
                    return None, content
                return frontmatter, match.group(2)
            except yaml.YAMLError as e:
                logger.warning(f"YAML parsing error in frontmatter: {e}")
            except Exception as e:
                logger.warning(f"Unexpected error parsing frontmatter: {e}")
        return None, content

    def generate_triggers_from_filename(self, filename: str) -> List[str]:
        """Генерирует триггеры из имени файла с дедупликацией."""
        name = Path(filename).stem.lower()
        triggers = [name]
        parts = re.split(r'[_-]', name)
        triggers.extend([p for p in parts if len(p) > 2])
        # Удаляем дубликаты, сохраняя порядок
        return list(dict.fromkeys(triggers))

    def compile_skill(self, filepath: Path) -> Dict:
        """Компилирует один навык в playbook."""
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        frontmatter, body = self.extract_yaml_frontmatter(content)

        if frontmatter:
            name = frontmatter.get("name", filepath.stem)
            description = str(frontmatter.get("description", "")).strip()
            triggers = frontmatter.get("triggers", [])
            if not triggers:
                triggers = self.generate_triggers_from_filename(filepath.name)
        else:
            name = filepath.stem
            # Берём первое предложение/абзац как описание
            description = body[:200].strip().replace("\n", " ")
            triggers = self.generate_triggers_from_filename(filepath.name)

        # Тринкация тела с логированием
        if len(body) > self.max_body_length:
            logger.debug(f"Skill '{name}' body truncated from {len(body)} to {self.max_body_length} chars")
            body = body[: self.max_body_length]

        return {
            "id": filepath.stem,
            "name": str(name),
            "description": description,
            "triggers": triggers,
            "source_file": str(filepath.resolve()),
            "body": body,
            "compiled_at": None,
        }

    def compile_all(self) -> List[Dict]:
        """Компилирует все навыки из директории."""
        self.skills = []
        if not self.skills_dir.exists():
            logger.warning(f"Skills directory not found: {self.skills_dir}. Creating empty directory.")
            self.skills_dir.mkdir(parents=True, exist_ok=True)
            return self.skills

        for md_file in self.skills_dir.glob("*.md"):
            try:
                skill = self.compile_skill(md_file)
                self.skills.append(skill)
                logger.debug(f"Compiled skill: {skill['name']}")
            except Exception as e:
                logger.error(f"Failed to compile {md_file}: {e}")

        logger.info(f"Compiled {len(self.skills)} skills from {self.skills_dir}")
        return self.skills

    def save_index(self) -> None:
        """Сохраняет индекс всех навыков в JSON."""
        now = datetime.now(timezone.utc).isoformat()
        for skill in self.skills:
            skill["compiled_at"] = now

        self.output_index.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_index, "w", encoding="utf-8") as f:
            json.dump(self.skills, f, indent=2, ensure_ascii=False)
        logger.info(f"Index saved to {self.output_index} ({len(self.skills)} skills)")

    def load_index(self) -> List[Dict]:
        """Загружает индекс навыков и обновляет внутреннее состояние."""
        if not self.output_index.exists():
            logger.info("No index file found")
            return []

        try:
            with open(self.output_index, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                self.skills = data
                logger.info(f"Loaded {len(data)} skills from index")
                return data
            else:
                logger.warning("Index file format is invalid (expected list)")
                return []
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in index file: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return []


# ✅ Глобальный экземпляр для импорта
skill_compiler = SkillCompiler()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    compiler = SkillCompiler()
    compiler.compile_all()
    compiler.save_index()