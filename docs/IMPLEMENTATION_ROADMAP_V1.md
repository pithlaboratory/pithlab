# Pith Implementation Roadmap v1

Scope: Pith v5 → runtime-first Pith (без B2B/multi-tenant и без ранней платформизации).

## Phase 1 — Core stabilization (2–3 недели)

- `models.py` registry: убрать хардкод, роли/lanes, budget caps.
- Secrets: `core/secrets.py`, `.env`, чистый `config.yaml`.
- Structured traces: schema для `episodes`, `llm_calls`, `task_traces`.
- Canonical task lifecycle: `states`, `transitions`, error handling.
- Runtime boundaries: чётко, что делает `router` / `planner` / `memory` / `evaluator`.

## Phase 2 — Workspace substrate (3–4 недели)

- `WorkspaceService` (CRUD + isolation).
- `TaskService` (создание, статусы, привязка к workspace).
- `ArtifactStore` (schema + API).
- Schemas: `TaskRecord`, `ArtifactRecord`, `Workspace`.
- FastAPI `/v1/workspaces`, `/v1/tasks` поверх Cognition Graph, общий runtime для TG и HTTP.

## Phase 3 — Governance baseline (2–3 недели)

- Evaluation schema (что сохраняем: scores, reasons, tags).
- Rollout tables: `runtime_versions`, `patch_candidates`, `patch_rollouts`.
- Rollback hooks и base policy.
- Budget/risk policies: лимиты по модели/задаче/дню.
- Dashboard v1 (Streamlit): tasks, workspaces, costs, failures, runtime versions.

## Phase 4 — Capability accumulation (4–6 недель)

- `SkillRegistry` (schema + API).
- `SkillBinding` (к task type / workspace / domain).
- Success/failure mining: из traces/tasks в candidate skills.
- Review pipeline: очередь, approve/reject, rollout.

## Phase 5 — Intelligence expansion (параллельно / после)

- `RepoIndexer` и basic repo map.
- `ContextRetriever` across memory + repo + artifacts + docs.
- `WebResearch` и `WebMonitor` как workspace tools.
- `DocumentIngestor` (PDF/MD/HTML → knowledge chunks).

## Out-of-scope v1

Сознательно **не** делаем в этом цикле:

- публичную multi-tenant B2B-платформу;
- сложный multi-agent zoo;
- persona-слой;
- глубокий auto-patching runtime без человека.