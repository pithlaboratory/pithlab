Pith Product Doctrine
Status: ACCEPTED
File role: canonical product doctrine for Pith v5.x
Scope: identity, product framing, value axes, and explicit constraints for the continuity runtime and Agent Company OS.

Этот документ отвечает на четыре базовых вопроса:

Кто такой Pith?

Какой продукт мы строим (и для кого)?

За что пользователи на самом деле платят?

Какие рамки и ограничения мы принимаем сознательно?

1. Identity — кто такой Pith
1.1. One line
Pith is a self-improving continuity runtime / workspace-native orchestration runtime и Agent Company OS for long-running cognitive work.

Он не существует ради ответов на промпты.
Его задача — удерживать и вести работу через время, интерфейсы, артефакты и цифровые команды.

1.2. Как думать о Pith
Pith — это:

runtime поверх LLM‑моделей и данных, а не ещё один ассистент;

операционный контур для задач, workflows, артефактов, памяти, skills и policies в рамках workspace/tenant;

Agent Company OS — прикладной слой цифровых департаментов (Sales, Marketing, Research, Delivery, Support/Ops) поверх runtime;

self‑improving слой, который со временем эволюционирует своё поведение через управляемый цикл OBS → EVAL → patch.

Подробное описание идентичности: docs/IDENTITY.md.
Архитектурный контракт: docs/PITH_KERNEL.md.

2. What Pith is not
Pith не должен превращаться в:

ещё один LLM‑чат (даже "с памятью");

Telegram‑бот как сущность продукта (Telegram — лишь интерфейс поверх ядра);

zoo агентов, где продаётся количество "ролей", а не continuity и результат;

отдельную "память" без контроля над самим ходом работы;

тяжёлую закрытую enterprise‑платформу ради галочки "agentic";

"agent framework" без жёсткой связи с workspaces, memory, traces и governance.

Мы сознательно:

не строим "ChatGPT‑клон";

не становимся очередной AI‑кнопкой внутри Notion/Jira/Slack;

не позиционируемся как чистый memory‑layer.

Детали про границы: docs/IDENTITY.md, docs/AGI_POSITION.md.

3. Для кого и против чего мы играем
3.1. Текущий ландшафт
LLM‑чаты (ChatGPT/Claude и др.) решают отдельные промпты.

AI workspace‑надстройки (Notion AI, Jira AI, Slack AI) добавляют ИИ внутрь продукта, но не дают целостной agentic‑архитектуры с оркестрацией и governance.

Memory‑сервисы обеспечивают хранение и retrieval контекста, но не управляют задачами и циклами работы.

Enterprise agentic‑платформы ориентированы на крупные компании, сложны, тяжеловесны и часто закрыты.

3.2. Где место Pith
не чат, не плагин к таск‑менеджеру и не чистая память,
а workspace-native orchestration runtime и Agent Company OS для команд и проектов.

Целевая аудитория первой волны:

инженеры и тех. фаундеры, которые уже используют LLM, но упираются в отсутствие continuity;

продуктовые/ресёрч‑команды, у которых много артефактов и задач, а контекст расползается;

агентства и операционные команды, которым нужны цифровые отделы с измеримыми результатами;

power‑users, которые хотят governed agents, а не магии.

4. За что пользователи реально платят
В основе продуктовой ценности — не "агенты" как сущность, а основные оси:

Continuity

накопление контекста между сессиями, интерфейсами, моделями;

удержание картины проекта, а не отдельных ответов.

Memory (как часть continuity)

эпизодическая память (episodes, traces);

артефакты (код, планы, отчёты, выводы) как часть общей истории;

meta‑memory: ключевые решения и причинные связи.

Orchestration

связка задач, workflows, инструментов, skills, моделей и департаментов в один управляемый цикл;

runtime‑слой, который понимает, что нужно сделать, а не только "что сказать".

Execution

не только текстовые ответы, но и выполнение шагов: изменения в коде, операции с артефактами, запуск процедур;

поддержка long‑running сценариев (инциденты, ресёрч, проектная работа).

Long-running work

способность вести длительные циклы research → planning → execution → review → iteration, а не одноразовые сессии.

Observability & Evaluation

трассировка, версии runtime, rollback;

измерение качества, стоимости и бизнес‑результата каждого workflow;

возможность объяснить "почему Pith сделал именно так".

Governance & Autonomy

политики и границы автономии (L0–L4);

approvals, audit, policy engine;

controlled evolution без "тёмных ящиков".

Agent Company OS

цифровые департаменты (Sales, Marketing, Research, Delivery, Support/Ops);

workflow‑команды с общей памятью, трассировкой и governance;

монетизация через billable events (лиды, кампании, ресёрчи, релизы).

И бонусом — sandbox‑режим для экспериментов без риска для продакшена.

5. Core product criteria
Чтобы Pith оставался самим собой, вводятся несколько критериев качества:

Continuity > feature‑zoo
Лучше одна фича, которая усиливает continuity/orchestration/observability, чем 10 бессвязанных "агентов".

Observability & Evaluation by design
Каждый существенный шаг оставляет след (trace, episode, artifacts, billable event).
Любое изменение runtime должно быть версионировано и откатываемо.

Runtime‑first, интерфейсы — вторичные
Telegram/web/CLI — это только проекции одного ядра.
Никакой интерфейс не должен становиться "источником истины" вместо runtime.

Self‑evolution, но в границах
Pith может сам предлагать и применять патчи в безопасных зонах (skills, prompts, policies);
ядро, БД и критичные интеграции меняются только через управляемый процесс (PatchGate + RolloutManager).

Agent Company поверх Runtime, не вместо
Департаменты и workflows — прикладной слой.
Они не обходят Core Runtime, не хранят теневые стейты и подчиняются тем же Trace/Governance правилам.

6. Явные "NO" (Explicit NO)
Формализуем отказ от того, что нас будет размывать:

Pith не становится:

ChatGPT/Claude‑классом ассистента;

Notion AI / Miro AI / Jira AI / Slack AI‑стайл добавкой;

чистым memory‑продуктом;

"agent‑зверинцем" ради маркетинга;

системой неконтролируемой автоэволюции без governance.

Pith не идёт в:

полностью неконтролируемую auto‑evolution без governance;

обещания "AGI скоро" (см. docs/AGI_POSITION.md);

расширение автономии без подтверждённых метрик из Evaluation и Governance.

Если новая идея противоречит этим "NO", она, вероятнее всего, не наш путь.

7. Связанные документы
Эта доктрина опирается на:

docs/MANIFESTO.md — ценности и позиционирование.

docs/IDENTITY.md — формальная идентичность Pith.

docs/PITH_KERNEL.md — архитектурный контракт ядра.

docs/ARCHITECTURE_NORTH_STAR (v2).md — целевая архитектура.

docs/PITH_AGENT_COMPANY_V1.md — Agent Company OS blueprint.

docs/PITH_OBSERVABILITY_V1.md — observability контракт.

docs/PITH_EVALUATION_V1.md — evaluation контракт.

docs/PITH_GOVERNANCE_V1.md — governance контракт.

docs/AGI_POSITION.md — честная позиция по теме AGI.

docs/PITH_SELF_EVOLUTION_RUNTIME_V1.md — self‑evolution pipeline.

docs/ROADMAP_6M.md — способности на горизонте 6 месяцев.

Pith меняется, но эти документы задают рамки того, чем он может и не может становиться.