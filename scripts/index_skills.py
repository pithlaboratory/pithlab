#!/usr/bin/env python3
"""Индексация скиллов из mined/*.md напрямую в Chroma."""
import sys
import json
import re
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from core.memory.manager import get_memory

memory = get_memory()
skills_dir = Path(__file__).parent.parent / "skills" / "mined"

count = 0
for md_file in skills_dir.glob("*.md"):
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Извлекаем YAML-заголовок между --- и ---
        match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not match:
            continue
            
        yaml_block = match.group(1)
        body = content[match.end():].strip()
        
        # Простейший парсинг YAML (без библиотеки)
        name = ""
        description = ""
        triggers = []
        for line in yaml_block.split('\n'):
            if line.startswith('name:'):
                name = line.replace('name:', '').strip()
            elif line.startswith('description:'):
                description = line.replace('description:', '').strip()
            elif line.startswith('triggers:'):
                triggers_str = line.replace('triggers:', '').strip()
                triggers = [t.strip() for t in triggers_str.strip('[]').split(',') if t.strip()]
        
        if not name:
            name = md_file.stem
            
        # Формируем процедуру
        procedure = {
            "id": md_file.stem,
            "name": name,
            "description": description or body[:200],
            "triggers": triggers,
            "source_file": str(md_file),
            "body": body[:2000]  # ограничим для эмбеддинга
        }
        
        memory.add_procedure(procedure)
        count += 1
        if count % 50 == 0:
            print(f"Indexed {count} skills...")
            
    except Exception as e:
        print(f"❌ Error {md_file.name}: {e}")

print(f"✅ Successfully indexed {count} skills into Chroma")
