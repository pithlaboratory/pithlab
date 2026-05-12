import sys
import os
sys.path.insert(0, '/root/pith_v5')

try:
    from core.memory.manager import get_memory
    from core.runtime.planner import RuntimePlanner
    print("✅ Модули успешно импортированы")
    
    # Создаем memory manager и planner
    memory = get_memory()
    print("✅ Memory manager создан")
    
    planner = RuntimePlanner(memory_manager=memory, system_prompt="Вы - Pith, операционный ИИ.")
    print("✅ Planner создан")
    
    print("✅ Тест завершен успешно")
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()