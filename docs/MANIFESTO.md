Этот манифест по сути уже совпадает с PITH_MASTER_PLAN v5.4 и IDENTITY.md, но его лучше чуть выровнять под актуальный фокус: runtime‑first + Support/Ops Desk wedge, а Agent Company OS оставить как долгосрочный слой сверху, а не равноправную часть one‑liner’а.

Ниже — обновлённая версия docs/MANIFESTO.md, которую можно положить вместо текущей.

One line
Pith is a self‑improving continuity runtime / workspace‑native orchestration runtime for long‑running cognitive and operational work.

Он существует не для того, чтобы отвечать на промпты, а чтобы удерживать и вести работу через время, интерфейсы, артефакты и цифровые команды внутри workspace’ов.

Поверх этого runtime‑ядра могут подниматься цифровые департаменты и desks (начиная с Support/Ops Desk), а в долгосрочной перспективе — более широкий слой “Agent Company OS”.

Problem
Современный стек выглядит так:

проекты размазаны по репозиториям, таск‑менеджерам, Notion/Confluence, локальным файлам и чатам;

чаты статичны: каждый диалог живёт сам по себе, история плохо связывается с кодом, задачами и решениями;

AI‑инструменты либо “сидят” внутри отдельных продуктов (Notion AI, Jira AI, GitHub Copilot), либо живут как отдельный чат, который всё время нужно заново обучать контексту.

Даже сильные модели решают промпт здесь и сейчас, но не:

удерживают целостную картину проекта или операционного процесса;

помнят решения и их причины в привязке к workspace;

управляют долгим циклом intake → triage → research → planning → execution → review → iteration;

дают наблюдаемость, управляемую автономию и перевариваемые отчёты;

организуют работу в виде слаженных цифровых отделов (support, ops, back office, revenue) поверх общего контекста.

Итог: человек остаётся “оркестратором по умолчанию” и постоянно тратит внимание на сбор контекста, повторения и ручное связывание частичных результатов.

Core Promise
Pith must make complex work continuous, accumulative, governable and observable.

Continuous — работа не обнуляется между сессиями, интерфейсами и моделями; контекст не нужно объяснять заново каждый день.

Accumulative — каждая задача добавляет системе знание или способность: артефакт, процедуру, skill, улучшенную политику.

Governable — поведение системы наблюдаемо, контролируемо и безопасно: есть трассировка, версии, политики, approvals, rollback, понятные границы автономии (L0–L4).

Observable — видно не только “что получилось”, но и “как прошли решения”: planner, orchestrator, департаменты/desk’и, tools, память, стоимость, ошибки.

Pith — это не один ассистент, а операционный контур, в котором разумные агенты и инструменты действуют по правилам и в общем состоянии.

Поверх этого контура строятся цифровые департаменты / desks (Support/Ops, далее Back Office, Revenue и т.п.), а в долгосрочной перспективе — более широкий слой “Agent Company OS” поверх стабильного runtime.

What Pith is not
Pith не должен становиться:

ещё одним LLM‑чатом (даже “с хорошей памятью”);

Telegram‑ботом как сущностью продукта (Telegram/CLI/API/web — только интерфейсы поверх ядра);

зоопарком агентов, где ценность — количество “ролей”, а не результат, continuity и управляемость;

“магической самопереписывающейся системой” без контроля, версий и трассировки;

ещё одной “AI‑надстройкой” к существующему workspace (Notion/Jira/Slack с одной лишней кнопкой “Ask AI”).

Pith — это ядро, вокруг которого могут жить боты, UI, API, интеграции и цифровые департаменты. Не наоборот.

Pith vs current AI tools
Сегодня:

ChatGPT/Claude и другие ассистенты решают отдельные запросы и промпты.

AI workspace‑инструменты добавляют ИИ к документам/таскам, но редко строят целостную agentic‑архитектуру с оркестрацией, памятью и governance.

Memory‑слои дают хранение контекста, но не управляют самим ходом работы и задачами.

Enterprise agentic‑платформы концентрируются на процессах и автономии, но часто тяжёлые, закрытые и ориентированы на крупные организации.

Pith занимает другое место:

не чат, не плагин к таск‑менеджеру и не отдельная память,
а workspace‑native orchestration runtime, который связывает задачи, контекст, память, навыки, департаменты и модели в один управляемый, наблюдаемый и эволюционирующий цикл.

В v5.4 внешний продуктовый фокус конкретен: Support/Ops Desk для B2B‑команд поверх этого runtime, а не абстрактная “Agent Company OS для всего”.

System Layers (кратко)
Pith строится из нескольких слоёв (см. PITH_ARCHITECTURE_NORTH_STAR_V2.md и PITH_KERNEL.md):

Core Runtime — planner, router, orchestrator, memory, evaluator, policy engine.

State Layer — tenant, workspace, task, workflow, artifact, trace, memory, runtime config.

Capability Layer — model plane, tool plane, skills, repo/web/document intelligence.

Department / Desk Layer — департаменты и desks (Support/Ops и последующие), billable workflows, billable events.

Governance Layer — observability, evaluation, approvals, autonomy tiers, rollout/rollback, budget/risk policies.

Interface Layer — Telegram, API, dashboard/operator console, CLI, IDE/voice адаптеры.

One-line formula
Chat solves prompts. Pith solves continuity.
Agent tools do actions. Pith runs the work around your workspaces under governance.

Или иначе:

Чат отвечает. Pith ведёт и удерживает работу.

Честность про AGI
Pith не обещает AGI и не притворяется “магическим интеллектом”.
Он строится как честный self‑improving runtime поверх внешних моделей с:

прозрачностью (traces, eval, config versions),

управляемой автономией (L0–L4),

эволюцией через eval/failure_miner/patch_planner, а не через скрытую самоперепись ядра.

Расширенная позиция по теме AGI и автономии описана в docs/PITH_AGI_POSITION.md.

