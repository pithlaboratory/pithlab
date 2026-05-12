#!/usr/bin/env python3
"""
Тестовый скрипт для проверки DIAGNOSTICS режима в Pith.
"""

import asyncio
import json
import sys
from pathlib import Path

# Добавляем корень проекта в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.memory.manager import get_memory
from core.runtime.planner import RuntimePlanner
from core.secrets import OPENROUTER_KEY

# Создаем memory manager и planner
memory = get_memory()
planner = RuntimePlanner(memory_manager=memory, system_prompt="Вы - Pith, операционный ИИ.")

async def test_diagnostics():
    """Тест DIAGNOSTICS режима"""
    # Создаем тестовый запрос, который активирует DIAGNOSTICS режим
    test_query = "сломалось что-то в системе, ошибка при выполнении"
    user_id = "test_user_diagnostics"
    
    print("Запуск теста DIAGNOSTICS режима...")
    print(f"Запрос: {test_query}")
    print("-" * 50)
    
    try:
        # Вызываем planner с запросом, который активирует DIAGNOSTICS режим
        result = await planner.plan_and_answer(user_id=user_id, text=test_query)
        
        print("Ответ от планировщика:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # Проверяем наличие goal_model в ответе
        if "goal_model" in result:
            print("\n" + "="*50)
            print("НАЙДЕНО goal_model в ответе:")
            print("="*50)
            goal_model = result["goal_model"]
            print(json.dumps(goal_model, ensure_ascii=False, indent=2))
        else:
            print("\n⚠️  goal_model НЕ НАЙДЕН в ответе")
            
    except Exception as e:
        print(f"Ошибка при выполнении теста: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_diagnostics())