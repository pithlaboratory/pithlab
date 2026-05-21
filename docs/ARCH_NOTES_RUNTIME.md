# Pith v5 — Runtime Architecture Notes (Runtime Core)

Status: aligned with runtime protocol v1, TraceStore v1.1, Phase 1.5 cleanup  
Scope: ModelRegistry/Router → RuntimePlanner → ContextAssembler  
Sources:
- `docs/PITH_ARCHITECTURE_NORTH_STAR_V2.md`
- `docs/PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md`
- `docs/PITH_OBSERVABILITY_V1.md`
- `docs/PITH_EVALUATION_V1.md`
- `docs/PITH_MASTER_PLAN.md` (v5.4, §§4–5–9–13)
- Claude/Perplexity runtime architecture review (Pith v5 – Runtime Architecture Review)

---

## 1. Current Runtime Core State

### 1.1 Model Plane / Router

- `model_registry.json` acts as SSOT for models, lanes, pricing, and routing hints. [file:14]
- Router is registry-first: it resolves models and pricing exclusively via ModelRegistry.
- Router owns:
  - lane selection (free / paid / premium),
  - budget and hard limit enforcement (per workspace/mode),
  - fallback behaviour when a lane/model is unavailable. [file:14]
- No automatic policy updates: routing behaviour changes only via explicit registry edits and code changes (no hidden auto‑learning). [file:14]
- Budget & routing are expected to feed into economics metrics (`cost_per_task`, `cost_per_useful_call`) as described in Master Plan §13. [file:14]

### 1.2 RuntimePlanner

- `RuntimePlanner` is Phase 1.5:
  - heuristic task type detection (keyword-based),
  - heuristic complexity gating (simple vs complex),
  - branch selection:
    - simple → direct LLM via Router,
    - complex → orchestrator (multi-agent / multi-step flow).
- `RuntimePlanner` has explicit boundaries:
  - owns execution branching only,
  - does not claim to be SSOT for task taxonomy or routing policy,
  - treats its task type mapping as Phase 1 heuristic, not a permanent contract.
- Mode alignment:
  - `RuntimeMode` from ContextAssembler (NORMAL / DIAGNOSTICS / VISION / operational modes for desks) can steer router mode in a safe, explicit way (e.g. diagnostics → coder lane). [file:14]
- Planner is responsible for tagging each run with `execution_path: "direct" | "orchestrated"` so observability/eval can compare marginal value. [file:14]

### 1.3 ContextAssembler

- `ContextAssembler` builds layered prompt context:
  - workspace identity,
  - runtime mode instructions,
  - current request,
  - current task context,
  - compressed conversation summary,
  - relevant memory (vector search),
  - relevant artifacts/documents,
  - recent conversation (noise-filtered). [file:14]
- System prompt is **not** дублируется внутри assembled prompt и передаётся отдельно как system message.
- Mode-dependent behaviour:
  - NORMAL: generic memory and task artifacts.
  - DIAGNOSTICS: incident-like memory and diagnostics guidance.
  - VISION / long-term: архитектура/roadmap память и North Star docs (ограниченно, с защитой от “vision‑mode everywhere”). [file:14]
- History and memory filters remove persona/meta noise; голос Pith — runtime‑voice (см. `IDENTITY.md`, `AGI_POSITION.md`). [file:14]

---

## 2. Confirmed Design Decisions

### 2.1 Separation of Concerns

- ModelRegistry + Router:
  - single source of truth for models, lanes, prices, and high-level routing hints,
  - responsible for budget, limits, and fallbacks. [file:14]
- RuntimePlanner:
  - responsible for execution branching only (direct vs orchestrated, lane choice hints),
  - не хранит canonical task taxonomy или модельное знание. [file:14]
- ContextAssembler:
  - responsible for structured, layered context assembly,
  - соблюдает порядок из Runtime Context Protocol и не смешивает system/user/assistant слои. [file:14]

### 2.2 Phase 1.5 Heuristics are Explicitly Temporary

- Task detection and complexity heuristics:
  - задокументированы как Phase 1.5,
  - помечены как кандидаты для замены Intents/registry-driven routing, [file:14]
  - реализованы так, чтобы их можно было делегировать будущему classifier/registry‑decision без ломки контракта Planner’а.

### 2.3 Layered Context is the Default

- Prompt assembly follows a fixed, protocol-aligned order:
  1. Workspace identity
  2. Mode instructions
  3. Current request
  4. Current task context
  5. Conversation summary
  6. Relevant memory
  7. Relevant artifacts/documents
  8. Recent conversation
- Это каноническая структура runtime v1; любые отклонения должны быть явными и задокументированными (например, для спец‑workflow’ов). [file:14]

---

## 3. Runtime Risk Profile (from architecture review)

### 3.1 Priority 1 — Registry Drift / Stale Routing

Risk:

- ModelRegistry — SSOT, но статичный по отношению к внешним провайдерам.
- Провайдеры могут менять цены, качество и доступность моделей асинхронно.
- Без feedback/обзора Router может слать трафик на подешевевшие/подорожавшие/деградировавшие модели, не замечая этого. [file:14]

Impact:

- Тихая деградация качества и cost‑эффективности на routing‑слое.
- Сложные ретроспективы (“почему в марте вырос cost?”) без версиирования и метрик.

### 3.2 Priority 2 — Context Poisoning via Layered Assembly

Risk:

- Layered context собирается без явной валидации.
- Разные слои могут вносить конфликтующие инструкции (workspace просит краткость, mode — полное обоснование, history — примеры с другой манерой/политикой). [file:14]
- LLM получает противоречивые сигналы без явных приоритетов → нестабильное поведение.

Impact:

- Непредсказуемые ответы, brittle behaviour, дрейф стиля и policy‑enforcement.
- Трудная отладка: конфликт размазан по нескольким слоям, а не сидит в одном месте.

### 3.3 Priority 3 — Orchestrator Without Marginal Value Measurement

Risk:

- RuntimePlanner отправляет запросы в orchestrator по эвристикам (длина, ключевые слова, количество вопросов).
- Нет систематического измерения: действительно ли orchestrated‑путь лучше direct по качеству/стоимости.
- Orchestrator может “по умолчанию” подхватывать “сложные” задачи и в 2–3 раза увеличивать cost без существенного выигрыша. [file:14]

Impact:

- Хронический перерасход на orchestration там, где он не окупается.
- Невозможность честно ответить “где нам реально нужны многоагентные сценарии”.

---

## 4. Guardrails and Metrics

### 4.1 Model Plane / Router Guardrails

Рекомендации:

- **Safe-gating для новых моделей:**
  - добавлять модели с `dev_only: true` в registry;
  - пускать трафик только из owner/internal workspaces;
  - минимум 48 часов наблюдать:
    - error_rate,
    - average latency,
    - eval‑based `avg_score`. [file:14]

- **Версионирование registry:**
  - не перезаписывать записи при изменении цены/поведения;
  - создавать `{model_id}_v2` с `supersedes` и хранить историю для “почему изменилось X?”. [file:14]

- **RoutingReviewJob (человек‑в‑цикле):**
  - периодический отчёт:
    - топ lanes/models по cost и score,
    - сравнение с прошлым интервалом,
    - флаги деградации (cost spike, error/score‑shift);
  - без автоматических патчей; изменения идут через Code + Changelog. [file:14]

Ключевые метрики (per lane/model):

- `cost_per_useful_call` — главный экономический сигнал (стыкуется с Master Plan §13.2–13.3). [file:14]
- `error_rate` — сигнал деградации провайдера.
- `fallback_rate` — индикатор проблем с доступностью/подбором модели.
- `avg_score` — evaluator‑based качество. [file:14]

Вторичные:

- latency p95/p99,
- сырой токен‑каунт (производный от cost).

### 4.2 Planner / Orchestrator Metrics

В дополнение к TraceStore v1.1 и EvaluationRecord v1: [file:14]

- `execution_path: "direct" | "orchestrated"`
- `agent_count` (если есть многоагентный сценарий)
- `steps_actual` / `steps_planned` (для сложных workflows)
- `cost_usd` (task-level, из TaskService/TraceStore)
- `task_type`, `runtime_mode`, `workflow_type`
- `score_final`, `task_success`, `failure_class` (из eval) [file:14]

Signals:

- Orchestrator wandering:
  - `steps_actual > steps_planned * 1.5`
- Orchestrator instability:
  - `error_rate(orchestrated) > 2x error_rate(direct)`
- Negative marginal value:
  - `avg_score(orchestrated) ≤ avg_score(direct) - ε`
  - при этом `cost(orchestrated) ≥ 2x cost(direct)`

Эти сигналы должны попадать в eval/observability отчёты и в decision‑процессы (где orchestration оставляем, где режем). [file:14]

### 4.3 ContextAssembler / Context Engineering

Pitfalls:

- **Order effects:**
  - начало/конец prompt’а тяжелее всего; критичные инструкции не должны теряться в середине.

- **Silent contradictions:**
  - workspace/mode/history/memory могут давать разные требования без явных приоритетов.

- **Memory flooding:**
  - vector similarity ≠ полезность; старые/шумные эпизоды могут засорять контекст.

- **Persona noise:**
  - экспериментальные personae/стиль в history/memory ломают runtime‑identity (особенно важно после постмортема по голосу).

Boundary‑риск:

- граница между summary (session background) и memory (episodic, past tasks) должна быть чётко маркирована, иначе LLM путает “текущее” и “фоновое”.

Guardrails:

- relevance floor + token budget на memory (см. 5.2 ниже);
- явные заголовки/маркировка секций (`CURRENT MODE`, `CURRENT TASK`, `BACKGROUND`, `PAST CONTEXT`);
- запрет на personae в боевом history/memory (runtime only).

---

## 5. Agreed Next Actions (Next 30–60 Days)

Привязано к Master Plan v5.4 (Q2 2026, §19.1–19.2). [file:14]

### 5.1 Add `execution_path` and basic episode metrics

Goal:

- Make direct vs orchestrated paths measurable end‑to‑end.

Actions:

- Расширить EvaluationRecord/episodes metadata:
  - `execution_path`,
  - `task_type`, `workflow_type`, `runtime_mode`,
  - `cost_per_workflow`, `failure_class`, `task_success`. [file:14]
- Убедиться, что RuntimePlanner помечает путь исполнения для обоих сценариев и что это попадает в `episodes.db` + `task_traces`. [file:14]
- Через 1–2 недели данных сравнить:
  - avg_score / task_success,
  - cost_per_workflow для direct vs orchestrated по ключевым workflow’ам (особенно Support/Ops Desk). [file:14]

Priority: **High (P1)**

### 5.2 Add relevance floor and token budget for memory

Goal:

- Reduce memory noise and flooding.

Actions:

- Для vector‑памяти:
  - ввести `relevance_score`‑порог (например, ≥ 0.65),
  - ввести upper bound на суммарный размер memory‑секции (например, 600–800 токенов),
  - предпочитать “нет памяти” вместо малосигнальной. [file:14]
- Реализация максимально простая (без сложных policy DSL).

Priority: **High (P1)**

### 5.3 Introduce `ContextValidator` as post-build step

Goal:

- Make layered context assembly observable and safer.

Actions:

- Добавить лёгкий `ContextValidator`, который работает после `ContextAssembler.build()` и до LLM‑вызова:
  - проверка token budget по секциям,
  - поиск дубликатов system‑инструкций,
  - простая проверка конфликтов (по ключевым словам: “always be concise” vs “give exhaustive detail” и т.п.),
  - persona‑noise check в history/memory.
- При fail:
  - логировать причину и деградировать аккуратно (например, отрезать noisy‑history или часть low‑relevance memory), не ломая весь runtime.

Priority: **Medium (P2)**

### 5.4 Explicit priority markers in prompt

Goal:

- Reduce order effects and clarify intent boundaries.

Actions:

- Добавить явные маркеры/заголовки для крупных блоков в assembled prompt:
  - `## [CURRENT MODE INSTRUCTIONS — HIGHEST PRIORITY]`,
  - `## [CURRENT TASK]`,
  - `## [SESSION BACKGROUND — lower priority]`,
  - `## [PAST CONTEXT — background only]`, и т.п.
- Не усложнять форматирование; цель — ясность, не “prompt‑art”.

Priority: **Medium (P2)**

---

## 6. Deferred Items (Later Phases)

### 6.1 Planner Heuristic Optimization

- Не оптимизировать эвристики task_type/complexity до тех пор, пока:
  - нет стабильных метрик от eval (direct vs orchestrated),
  - не понята реальная marginal value orchestration по ключевым workflow’ам. [file:14]
- Будущее направление:
  - IntentClassifier,
  - registry‑driven task‑to‑lane mapping.

### 6.2 Automatic Routing Policy Updates

- Не включать auto‑rewrites routing‑политик, пока:
  - eval‑loop не замкнут,
  - routing‑метрики не стали стабильными и доверенными. [file:14]
- Пока `RoutingReviewJob` остаётся отчётным инструментом с человеком в цикле.

### 6.3 Deep Registry Versioning and Migration

- Полноценное версионирование:
  - моделей,
  - pricing,
  - routing‑конфигураций.
- Находится в roadmap (Master Plan §5.7, §13.2–13.3), но не блокирует ближайшие 30 дней. [file:14]

---

*Last updated: 2026‑05‑21 · Pith v5 Runtime Core · Internal / Confidential*