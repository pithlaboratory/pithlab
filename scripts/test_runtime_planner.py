import asyncio
import logging

from core.memory.manager import get_memory
from core.runtime.planner import RuntimePlanner
import yaml
from pathlib import Path


logging.basicConfig(level=logging.INFO)

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

SYSTEM_PROMPT = config.get("persona", {}).get("system_prompt", "")


async def main():
    mm = get_memory()
    planner = RuntimePlanner(memory_manager=mm, system_prompt=SYSTEM_PROMPT)
    user_id = "smoke_test_user"

    tests = [
        ("direct_general", "Объясни кратко, что такое контекстное окно модели"),
        ("direct_coder", "Исправь traceback в python коде и предложи patch"),
        ("orchestrator", "Спланируй архитектуру AI-платформы с агентами, памятью и роутингом"),
    ]

    for name, text in tests:
        print(f"\n=== TEST: {name} ===")
        result = await planner.plan_and_answer(user_id=user_id, text=text)

        print("model_id:", result.get("model_id"))
        print("model_name:", result.get("model_name"))
        print("used_orchestrator:", result.get("used_orchestrator"))
        print("tokens_prompt:", result.get("tokens_prompt"))
        print("tokens_completion:", result.get("tokens_completion"))
        print("cost:", result.get("cost"))
        print("response:", (result.get("response") or "")[:300].replace("\n", " "))


if __name__ == "__main__":
    asyncio.run(main())