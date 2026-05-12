# Pith Runtime Context Protocol v1

> **Purpose:** Defines how Pith assembles context for LLM calls at runtime: sources, order, priority, and mode‑dependent rules.  
> **Alignment:** Implements **Pith Architecture North Star v2** at the runtime behavior level.  
> **Status:** `ACTIVE`  
> **Last updated:** 2026-04-28  
> **Owner:** Core Runtime Engineering

---

## 1. Purpose & Link to North Star

Этот протокол описывает, как Pith собирает контекст для LLM‑вызовов в рантайме: из каких источников, в каком порядке и в зависимости от режима работы.

**Цели:**
- Сделать поведение Pith стабильным, предсказуемым и контролируемым.
- Уменьшить persona drift и лишнюю саморефлексию в рабочих сценариях.
- Эффективно использовать контекстное окно (история, summary, память, артефакты).
- Гарантировать, что каждый вызов соответствует North Star v2: continuity, governability, task‑focus.

---

## 2. Источники контекста

Для каждого вызова Planner’а доступны пять типов контекста:

| # | Источник | Назначение |
|---|----------|-----------|
| 1 | **System / Runtime Policy** | North Star v2, правила стиля, ограничения автономии, budget‑политики, anti‑goals |
| 2 | **Short‑Term Conversation** | Последние `N` сообщений (обычно 8–12 пар user/assistant). «Рабочее окно» текущей задачи |
| 3 | **Conversation Summary** | Компактное резюме старой истории. Обновляется инкрементально |
| 4 | **Memory Records** | Эпизодическая/семантическая память: прошлые задачи, решения, ошибки, lessons learned |
| 5 | **Task / Artifact / Knowledge Context** | Код, документы, логи, репозитории, внешние источники (подмешиваются через RAG/tools) |

---

## 3. Режимы рантайма

Planner всегда работает в одном из трёх режимов. **Режим определяется RuntimePlanner** (на основе текущего запроса, ключевых слов и истории сообщений; в будущем может быть вынесен в отдельный `ModeDetector`).

| Режим | Триггер | Цель |
|-------|---------|------|
| `NORMAL` | По умолчанию | Ответы, выполнение задач, планирование, стандартный рабочий поток |
| `DIAGNOSTICS` | Сигналы в последних `K` сообщениях: `сломалось`, `ошибка`, `traceback`, `баг`, `fix`, `не работает` | Локальная диагностика, конкретные шаги фикса, структурированный troubleshooting |
| `VISION / META` | Явный запрос пользователя: `архитектура`, `roadmap`, `эволюция`, `чего не хватает системе`, `self‑analysis` | Длинные архитектурные ответы, стратегическое планирование, допустимый deep self‑analysis |

---

## 4. Сбор контекста по режимам

### 4.1. NORMAL
1. **System / Runtime Policy** → Role, North Star, anti‑goals, стиль, ограничения автономии.
2. **Последние `N` сообщений** → Полный текст (по токен‑лимиту).
3. **Conversation Summary** → Добавляется только при длинной истории. Формат: `Previous conversation summary (background only): ...`
4. **Memory Records** → Top‑M релевантных эпизодов (format: `Past case → Outcome → Lessons`).
5. **Task/Artifact Context** → По запросу Planner’а или через tools/RAG.
6. **Ограничение:** В NORMAL режиме Planner **не инициирует** длинные AGI‑манифесты или глубокий self‑analysis без прямого запроса.

### 4.2. DIAGNOSTICS
1. **System / Policy + Mode Block** → Инструкции: `«Твоя задача — разобрать, что пошло не так, и предложить конкретные шаги фикса. Не уходи в общий самоанализ.»`
2. **Последние сообщения** → Логи/ошибки включаются целиком. Старые архитектурные обсуждения агрессивно урезаются.
3. **Summary** → Только если относится к предыдущим сбоям.
4. **Memory** → Только прошлые инциденты того же класса (`Previous incident → Root cause → Fix`).
5. **Artifacts** → Логи, конфиги, схемы.
6. **Запреты:** Нет длинных списков «чего не хватает системе», нет переразгона в AGI‑roadmap вместо локальной диагностики.

### 4.3. VISION / META
1. **System / Policy + `mode=vision`**.
2. **Summary архитектурных обсуждений** Pith.
3. **Memory** → Только records с тегами `projects.pith.*` (philosophy, roadmap, governance, model stack).
4. **Артефакты** → North Star, roadmaps, схемы, ADR, `MASTER_PLAN.md`.
5. **Допустимо:** Длинные структурированные ответы, списки улучшений, системный self‑analysis (только по явному запросу).

---

## 5. Приоритеты источников и разрешение конфликтов

При построении контекста Planner соблюдает строгий приоритет:

1. `System / Runtime Policy` (North Star, safety, anti‑goals)
2. `Текущий режим` (normal / diagnostics / vision)
3. `Последние сообщения` (short‑term context)
4. `Явные инструкции пользователя` в текущем запросе
5. `Conversation Summary`
6. `Memory Records / прошлые задачи`
7. `Дополнительные знания` (RAG/tools)

**При конфликте:**  
Выигрывают сначала Policy и режим, затем текущий запрос, затем всё остальное. Память **не имеет права** перезаписывать system policy или текущие ограничения.

---

## 6. Политика саморефлексии

Чтобы не превращаться в «болтливую AGI‑персону», Pith придерживается правил:

- 🔹 **Один большой self‑analysis на сессию**, только в `mode=vision` и только по запросу.
- 🔹 В `normal` и `diagnostics` самоанализ ограничен: максимум 2–3 коротких пункта «что улучшить», только если спросили.
- 🔹 Старые self‑анализы могут учитываться в summary/memory как фон, но **не превращаются** в явные инструкции к текущему ответу, если конфликтуют с текущими policy.
- 🔹 Любая попытка модели развернуть манифест в обычном режиме фиксируется `Evaluator` как `persona_drift`.

---

## 7. Обновление summary и памяти

После значимого шага или завершения задачи:

1. **Обновление summary** → На основе последних сообщений пересобирается краткое резюме (в идеале до нескольких абзацев).
2. **Создание/обновление Memory Records** → Пишем только для: успешных/провальных задач, решений, паттернов, финальных артефактов. Тэгируем по `workspace`, `task_type`, `risk_level`.
3. **Trace / Governance** → Каждый важный шаг фиксирует `Trace` и, при необходимости, `PolicyDecision` / `RuntimeVersion` для воспроизводимости и отката.

---

## 8. Привязка к коду (Implementation Contract)

Модуль `RuntimePlanner` использует сервис `ContextAssembler` со следующей сигнатурой:

```python
context = context_assembler.build(
    mode=RuntimeMode.NORMAL | DIAGNOSTICS | VISION,
    workspace_id=workspace_id,
    user_id=user_id,
    task_id=task_id,
    query=user_query,
    recent_history=history_slice,
)