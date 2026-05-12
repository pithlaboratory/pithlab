import sys
sys.path.insert(0, '/root/pith_v5')

from core.context_assembler import ModeDetector, RuntimeMode

# Тестовый запрос, который должен активировать DIAGNOSTICS режим
test_query = "сломалось что-то в системе, ошибка при выполнении"
recent_history = []

# Создаем детектор режима
detector = ModeDetector()

# Определяем режим
mode = detector.detect(test_query, recent_history)

print(f"Запрос: {test_query}")
print(f"Определенный режим: {mode}")
print(f"Режим DIAGNOSTICS: {mode == RuntimeMode.DIAGNOSTICS}")

# Проверим, какие слова активируют DIAGNOSTICS
diagnostics_signals = [
    "сломалось", "не работает", "ошибка", "traceback", "stacktrace",
    "баг", "bug", "fix", "починить", "почини", "опять", "падает",
    "error", "exception", "failed", "failure",
]

found_signals = []
for signal in diagnostics_signals:
    if signal in test_query.lower():
        found_signals.append(signal)

print(f"Найденные сигналы DIAGNOSTICS: {found_signals}")