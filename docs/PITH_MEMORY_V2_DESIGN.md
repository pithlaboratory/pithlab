# PITH_MEMORY_V2_DESIGN.md

Status: Draft v0.1  
Applies to: Pith v5.4+  
Related: docs/PITH_MASTER_PLAN.md §7, §8, §9, §11, §22; docs/PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md; docs/PITH_OBSERVABILITY_V1.md; docs/PITH_EVALUATION_V1.md

---

## 1. Purpose & Scope

Pith Memory v2 описывает, **как Pith хранит, использует и забывает информацию** на уровне платформы, а не конкретных фич.  
Цель — обеспечить управляемую continuity между задачами, эпизодами, артефактами и навыками, сохраняя жёсткие границы по workspace/tenant и соблюдая guardrails Master Plan. [file:46][cite:5]

В этом документе фиксируются:

- уровни памяти и их назначение (short / episodic / semantic / profiles);  
- namespace‑изоляция и политики доступа;  
- иерархическая суммаризация и “loss‑aware” подход;  
- политика забывания и архивации;  
- связь памяти с TraceStore, Artifact System и Self‑Improvement Loop;  
- минимальные API/контракты для RuntimePlanner, MemoryManager и Evaluator. [file:46]

---

## 2. Memory Taxonomy

Базовая таксономия Memory v2 берётся из Master Plan §7.1 и фиксируется как платформенный инвариант. [file:46]

### 2.1 Memory types

- **Short‑term memory**  
  - Purpose: текущий диалог, локальный контекст задачи.  
  - Storage: in‑memory / session state Orchestrator’а.  
  - Scope: один trace / один task.  
  - Lifetime: живёт пока активен episode / trace, не считается “persisted memory”.

- **Episodic memory**  
  - Purpose: история запросов/ответов и метрик на уровне эпизодов.  
  - Storage: `episodes.db` / EpisodeStore (SQLite или аналоги).  
  - Scope: workspace + канал (Telegram, API, и т.п.).  
  - Lifetime: управляется политиками retention/archival, но по умолчанию — “long enough for audit & eval”. [file:46]

- **Semantic memory**  
  - Purpose: проверенные факты, фрагменты репозитория, KB, “workspace‑aware knowledge” (а не сырые галлюцинации).  
  - Storage: вектор‑хранилище + файловая система (индексированные фрагменты).  
  - Scope: workspace (строгая изоляция), опционально department‑scoped.  
  - Lifetime: управляется отдельной политикой для знаний (дольше, чем эпизоды). [file:46]

- **Profiles**  
  - Purpose: предпочтения, ограничения, роли, разрешённая автономия (для пользователей, workspace, агентов, департаментов).  
  - Storage: профильная БД (SQLite/JSON в v5.x).  
  - Scope: user / workspace / department / agent.  
  - Lifetime: пока живёт соответствующая сущность + offboarding‑политики. [file:46]

### 2.2 Namespace isolation

Memory v2 **строго** соблюдает namespace‑границы:

- Жёсткая изоляция по tenant/workspace: никаких неявных cross‑tenant запросов.  
- Cross‑workspace sharing — только опционально, явно, под политикой и аудитом.  
- Для каждого workspace — отдельное логическое пространство: episodes, semantic index, artifacts, skills. [file:46][cite:5]

---

## 3. Hierarchical Summarization

Summarization в Memory v2 — многоступенчатая и “loss‑aware”: каждая ступень **понимает, что теряет**, и оставляет ссылку на сырой контент. [file:46]

### 3.1 Levels of summarization

- **Raw turns**  
  - Полные сообщения/ответы + метаданные (trace_id, task_id, runtime_config_ver, cost, eval).  
  - Хранятся в TraceStore/Episodes.

- **Session summaries**  
  - Краткое представление серии запросов/ответов (episode‑level).  
  - Содержат ссылки на raw turns (trace/episode IDs).  
  - Используются для быстрого восстановления контекста без полной истории.

- **Workspace/topic summaries (semantic)**  
  - Обобщения по темам/проектам (например, “SupportOps for Client X — последние N инцидентов”).  
  - Сшивают несколько эпизодов, артефакты и KB в осмысленные куски.  
  - Содержат ссылки на session summaries, артефакты, навыки. [file:46]

### 3.2 Loss-aware semantics

Каждый уровень обязан:

- Явно указывать, какие аспекты были отброшены (например, “опущены low‑signal chit‑chat сообщения”).  
- Держать обратные ссылки (trace/episode IDs, artifact IDs) для восстановления деталей.  
- Участвовать в ContextRetriever с приоритетом: **profiles → semantic → episodic → short‑term**, чтобы не раздувать контекст мусором. [file:46]

---

## 4. Forgetting & Archival Policy

Политика забывания Memory v2 зафиксирована в Master Plan §7.4 и уточняется здесь. [file:46]

### 4.1 Categories and retention

Для каждой категории данных задаются:

- Retention window (N дней/месяцев);  
- Действие по истечении: `archive` или `delete`;  
- Обязанность по ссылкам: при `delete` нужно обнулить/обезличить ссылки в других слоях.

Пример (логическая таблица):

- Short‑term: живёт в пределах одного trace, далее уничтожается.  
- Episodic: архив через N дней, delete в рамках offboarding или compliance‑требований.  
- Semantic: долгоживущая, delete только при ревизии знаний или контрактных ограничениях.  
- Profiles: пока активен субъект + политика offboarding. [file:46]

### 4.2 Archive vs delete

- **Archive**  
  - Убирается из “горячего” контекста (ContextRetriever по умолчанию не трогает).  
  - Остаётся доступным для аудита/ретроспектив, может быть возвращён в hot‑set по запросу.  

- **Delete**  
  - Жёсткое удаление содержимого (с учётом юридических требований).  
  - Ссылки в TraceStore/Episodes/Artifacts либо аннулируются, либо анонимизируются.  
  - Процесс должен быть трассируемым (Governance + Offboarding §17.7). [file:46]

---

## 5. Memory & Runtime Context Protocol

Memory v2 подчиняется `PITH_RUNTIME_CONTEXT_PROTOCOL_V1` и расширяет его на уровне:

- как контекст формируется для задачи;  
- как runtime записывает результаты в память;  
- как trace/eval связаны с памятью. [cite:29][file:46]

### 5.1 Context envelope

Для каждого `task` RuntimePlanner/Orchestrator формирует **context envelope**, включающий:

- identity (user, workspace, department, agent categories);  
- scoped memory slices:  
  - profiles (user/workspace/department);  
  - релевантные semantic фрагменты (по workflow_id, topic, repo‑контексту);  
  - свежие episodic summaries;  
- governance constraints (autonomy tier, risk class, allowed tools, data scopes). [file:46]

Envelope не содержит “сырых” cross‑tenant данных и не смешивает данные workspace’ов.

### 5.2 Write‑path

После выполнения task:

- **Episodes**  
  - записывается новый episode/turn с полным запросом/ответом и метаданными (model, cost, eval).  

- **Semantic memory**  
  - по решению Evaluator/FailureMiner/PatchPlanner могут извлекаться устойчивые факты или полезные паттерны и записываться как semantic entries. [file:46]

- **Profiles**  
  - по явным сигналам (user preference change, workspace setting, autonomy change) обновляются профильные записи, а не сырая история. [file:46]

---

## 6. Memory & Self-Improvement Loop

Memory v2 — главный топливо‑слой для Self‑Improvement Loop (§9): Evaluator, FailureMiner, PatchPlanner, SkillCompiler. [file:46][cite:230]

### 6.1 Evaluator

- Использует episodes + artifacts для вычисления метрик: task success, quality, cost, policy adherence, human override rate. [file:46]  
- Сохраняет EvaluationRecord v1 в `episodes.metadata.eval`, ссылаясь на `trace_id`, `task_id`, `workflow_type`, `runtime_mode`.  

### 6.2 FailureMiner

- Читает **кластеризованные failure episodes** и связанные с ними semantic entries/skills.  
- Находит общие паттерны: “этот тип запросов для SupportOps системно даёт wrong KB snippet”. [file:46]  

### 6.3 PatchPlanner & SkillCompiler

- PatchPlanner использует Memory v2, чтобы **менять стратегии памяти** (промпты, retrieval policies, weights for episodic vs semantic). [file:46]  
- SkillCompiler превращает повторяющиеся успешные решения в formal skills, используя semantic memory + artifacts как исходники и фиксируя lineage.  

### 6.4 Evolution artifacts

Вся эволюция памяти сама по себе становится частью Memory v2:

- PITH_CHANGELOG.md, skills, logs, ADR — считаются evolution artifacts и индексируются в semantic memory и Context Graph. [file:46]

---

## 7. Memory & Artifact / Context Graph

Memory v2 тесно связана с Artifact System и Context Graph (§11). [file:46]

### 7.1 Artifact lineage

Каждый артефакт (reports, plans, patches, dashboards, datasets, prompt packs, workflow manifests, incident summaries) несёт:

- `created_by`, `derived_from`, `input_sources`;  
- `approved_by`, `runtime_version`, `skill_version`, `trace_ids`. [file:46]

Memory v2 должна:

- уметь находить артефакты по семантике и lineage;  
- использовать артефакты как первичный источник “ground truth” для последующих задач внутри workspace.

### 7.2 Context Graph

Context Graph (nodes: repos, docs, tasks, workflows, traces, approvals, artifacts, departments, skills) используется как “надстройка” над памятью: [file:46]

- Memory v2 предоставляет базовые хранилища (episodes, semantic, profiles).  
- Context Graph сочетает их в единый граф: `depends_on`, `derived_from`, `approved_by`, `belongs_to_workspace`, `generated_by`.  
- Retrieval идёт через ContextRetriever (§8.3), который уважает guardrails и namespace isolation. [file:46]

---

## 8. Implementation Notes (v5.4 baseline)

### 8.1 Minimal implementation targets

Для v5.4/v5.5 достаточно:

- Episodic: надёжный EpisodeStore с привязкой к TraceStore (по trace_id/task_id).  
- Semantic: workspace‑scoped индекс (например, файловые фрагменты репо, KB, ключевые документы).  
- Profiles: простые структуры для user/workspace/department/agent.  
- Summarization:  
  - auto session summaries для длинных диалогов/эпизодов;  
  - ручные/полуавтоматические workspace/topic summaries для пилотных клиентов. [file:46]

### 8.2 Non-goals for this phase

До стабилизации Support/Ops Desk wedge и Observability/Eval v1 **не делаем**: [file:46]

- глобальные cross‑workspace knowledge graphs;  
- агрессивные, полностью автоматические ретро‑обучения модели;  
- сложные кросс‑департаментные memory‑sharing схемы (это уже Agent Company OS vNext).

---

## 9. Governance & Safety

Memory v2 подчиняется guardrails Master Plan §22. [file:46][cite:5]

Ключевые принципы:

- Reversibility by design: можно откатить memory‑политику, выключить ретривер, отозвать skills.  
- Attribution before autonomy: каждая “памятная” операция трассируема к config/prompt/policy.  
- Workspace/tenant isolation: никакого скрытого data mixing.  
- Eval‑gated evolution: любые автоматические изменения политик памяти/контекста проходят через eval‑гейты и PatchGate. [file:46]

---

## 10. Open Questions & Next Steps

Открытые вопросы для v5.4→v5.5:

- Где проходит граница между episodic и semantic для Support/Ops Desk кейсов (например, тикеты: как быстро они уходят в semantic vs архив)?  
- Какая минимальная метрика “memory quality” должна войти в Business Usefulness Scorecard для пилотов?  
- Какой формат использовать для workspace/topic summaries (Markdown vs JSON manifests) для лучшей интеграции с Artifact System и skills? [file:46]

Next steps:

1. Утвердить этот док как v0.1 и добавить ссылку в `PITH_DOCS_INDEX.md` и `PITH_MASTER_PLAN.md §7`.  
2. Определить минимальный API для MemoryManager/ContextRetriever под Support/Ops Desk workflows.  
3. Добавить 2–3 golden‑кейса, которые явно проверяют работу Memory v2 (retrieval + summarization + forgetting). [file:46]