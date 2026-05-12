import asyncio
import json
from core.memory.manager import get_memory
from core.runtime.planner import RuntimePlanner

async def main():
    # Создаем memory manager и planner
    memory = get_memory()
    planner = RuntimePlanner(memory_manager=memory, system_prompt="Вы - Pith, операционный ИИ.")
    
    # Создаем тестовый запрос, который активирует DIAGNOSTICS режим
    test_query = "сломалось что-то в системе, ошибка при выполнении"
    user_id = "test_user_diagnostics"
    
    # Вызываем planner с запросом, который активирует DIAGNOSTICS режим
    result = await planner.plan_and_answer(user_id=user_id, text=test_query)
    
    # Сохраняем результат в файл
    with open("diagnostics_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print("Результат сохранен в diagnostics_result.json")
    print("Наличие goal_model:", "goal_model" in result)

if __name__ == "__main__":
    asyncio.run(main())