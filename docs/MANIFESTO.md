# Pith Manifesto

## One line

Pith is a **self-improving continuity runtime / workspace-native orchestration runtime и Agent Company OS** for long-running cognitive work.

Он существует не для того, чтобы отвечать на промпты, а чтобы удерживать и вести работу через время, интерфейсы, артефакты и цифровые команды.

---

## Problem

Современный стек выглядит так:

- проекты разбросаны по репозиториям, таск-менеджерам, Notion/Confluence, локальным файлам и чатам;
- чаты статичны: каждый диалог живёт сам по себе, история плохо связывается с кодом, задачами и решениями;
- AI-инструменты либо "сидят" внутри отдельного продукта (Notion AI, Jira AI, GitHub Copilot), либо живут как отдельный чат, который всё время нужно заново обучать контексту.

Даже сильные модели решают **промпт здесь и сейчас**, но не:

- удерживают целостную картину проекта;
- помнят решения и их причины;
- управляют долгим циклом `research → planning → execution → review → iteration`;
- дают наблюдаемость и управляемую автономию;
- организуют работу в виде слаженных цифровых команд и департаментов.

Итог: человек остаётся "оркестратором по умолчанию" и постоянно тратит внимание на сбор контекста, повторения и ручное связывание частичных результатов.

---

## Core Promise

**Pith must make complex work continuous, accumulative, governable and observable.**

- **Continuous** — работа не обнуляется между сессиями, интерфейсами и моделями; контекст не нужно объяснять заново каждый день.
- **Accumulative** — каждая задача добавляет системе знание или способность: артефакт, процедуру, skill, улучшенную политику.
- **Governable** — поведение системы наблюдаемо, контролируемо и безопасно: есть трассировка, версии, политики, approvals, rollback, понятные границы автономии (L0–L4).
- **Observable** — видно не только "что получилось", но и "как прошли решения": planner, orchestrator, департаменты, tools, память, стоимость, ошибки.

Pith — это не один ассистент, а **операционный контур**, в котором разумные агенты и инструменты действуют по правилам и в общем состоянии.

Поверх этого контура строится **Agent Company OS** — цифровая компания из специализированных департаментов (Sales, Marketing, Research, Delivery, Support/Ops), которые работают на общей памяти, runtime и governance.

---

## What Pith is not

Pith **не** должен становиться:

- ещё одним LLM chat, даже "с хорошей памятью";
- Telegram-ботом как сущностью продукта (Telegram — только интерфейс поверх ядра);
- zoo агентов, где главная ценность — количество "ролей", а не результат, continuity и управляемость;
- "магической самопереписывающейся системой" без контроля, версий и трассировки;
- ещё одной "AI надстройкой" к существующему workspace (типа Notion AI/Slack AI), где ИИ — просто дополнительная кнопка.

Pith — это **ядро**, вокруг которого могут жить боты, UI, API, интеграции и цифровые департаменты. Не наоборот.

---

## Pith vs current AI tools

Сегодня:

- ChatGPT/Claude и другие ассистенты решают отдельные задачи и промпты.
- AI workspace tools добавляют ИИ в существующие документы/таски, но не строят целостную agentic‑архитектуру с оркестрацией, памятью и governance.
- Memory‑инфраструктуры дают слой памяти, но не управляют самим ходом работы и задачами.
- Enterprise agentic‑платформы концентрируются на процессах и автономии, но часто закрыты, тяжёлые и заточены под крупные организации.

Pith занимает другое место:

> **не** чат, не плагин к таск-менеджеру и не отдельная память,  
> а **workspace-native orchestration runtime и Agent Company OS**, который связывает задачи, контекст, память, навыки, департаменты, модели и действия в один управляемый, наблюдаемый и эволюционирующий цикл.

---

## System Layers (кратко)

Pith строится из нескольких слоёв:

- **Core Runtime** — planner, orchestrator, memory, evaluator, policy engine.
- **State Layer** — tenant, workspace, task, workflow, artifact, trace, memory, runtime config.
- **Capability Layer** — model plane, tool plane, skills, repo/web intelligence.
- **Agent Company Layer** — департаменты, агентные команды, billable events.
- **Governance Layer** — observability, evaluation, approvals, autonomy tiers, rollback.
- **Interface Layer** — Telegram, API, dashboard, CLI.

Подробно: `PITH_KERNEL.md`, `ARCHITECTURE_NORTH_STAR (v2).md`, `PITH_AGENT_COMPANY_V1.md`.

---

## One-line formula

**Chat solves prompts. Pith solves continuity.**  
**Agent tools do actions. Pith runs the company of agents around your workspaces.**

Или иначе:

> **Чат отвечает. Pith ведёт.**

---

## Честность про AGI

Мы не обещаем AGI и не притворяемся "магическим интеллектом".  
Мы строим честный self‑improving runtime поверх внешних моделей.  
Наша цель — прозрачность, эволюция и управляемость, а не хайп.

Расширенная позиция по теме AGI и автономии: `docs/AGI_POSITION.md`.
