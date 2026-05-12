# PITH DEV CONTEXT

## 1. What Pith is

Pith is a **self-improving continuity runtime (Agent OS / cognitive operating layer)** for engineering and cognitive work.

It is not:
- a bot,
- a generic LLM wrapper,
- an AGI claim,
- a feature-zoo of personas.

It is a runtime layer that:

- connects strategy, memory, tools, execution and reflection into one governed loop;
- decides **how**, **when**, and **with which model lane** work is executed;
- accumulates context, artifacts and failure patterns so the system becomes more precise and more efficient over time.

Core positioning:
- **Chat solves prompts. Pith solves continuity.**

---

## 2. Current status (2026-05-07)

### Baseline
- ✅ `v1.0` baseline is stable enough to serve as the current production/runtime baseline.
- ✅ Router, config-driven model selection, Telegram/Viktor interface, Orchestrator bridge, Evaluator / FailureMiner / PatchPlanner / SkillCompiler are in place architecturally.
- ✅ Main live interface is still **Viktor in Telegram**.
- ✅ Dashboard and FastAPI remain secondary until the runtime core is more reliable.

### In progress
- 🟡 Real implementations of agents (`tera`, `hex`, `coda`) instead of thin bridge/stub behaviour.
- 🟡 TraceStore / observability expansion.
- 🟡 `PithEval v0.1` dataset.
- 🟡 CLI `pith ask/dev/incident`.

### Planned next
- 🔲 Memory v2:
  - namespace isolation,
  - consolidation,
  - hierarchical summarization,
  - forgetting policy.
- 🔲 A2A protocol.
- 🔲 Tool Contracts.
- 🔲 Governance rollout completion (PatchGate / RolloutManager / kill switch path).

### Infra
- Server: `msk-1-vm-ngf0`
- OS: Ubuntu 24.04
- Runtime process: `systemd` → `pith_v5.service`

---

## 3. Core system map

| Layer | Main components |
|------|------------------|
| **Interface** | `telegram_bot.py`, CLI, future HTTP/API/web surface |
| **Routing** | `router.py` — lane selection, fallback, budget gate, provider switching |
| **Planning** | `planner.py` / RuntimePlanner — task_type detection, direct vs orchestrated path |
| **Orchestration** | `orchestrator.py` — bridge for modular agents, parallel execution, synthesis |
| **Memory** | `manager.py`, `episodes.db`, `skills/index.json`, profile/context assembly |
| **Evaluation** | `evaluator.py` — quality/context/disclaimer scoring |
| **Evolution** | `miner.py` → `patch_planner.py` → `skill_compiler.py` |
| **Governance** | `PatchGate`, `RolloutManager`, `autonomy.yaml`, future kill switch |
| **Artifacts / future runtime substrate** | tasks, traces, manifests, candidate patches, runtime versions |

---

## 4. Current priorities (next 30 days)

1. **Stabilize real agents**
   - Turn `tera`, `hex`, `coda` into reliable modular workers.
   - Reduce dummy/stub behaviour.
   - Make outputs structured and synthesis-friendly.

2. **TraceStore + observability**
   - Full cost attribution per lane and per agent.
   - Structured logging for LLM calls and task steps.
   - Better production diagnosis.

3. **PithEval v0.1**
   - 30–50 ground-truth tasks.
   - Close the loop between generation, evaluation and patching.

4. **CLI v0.1**
   - `pith ask`
   - `pith dev`
   - `pith incident`
   - Goal: terminal-native workflow without manual copy-paste.

5. **Memory cleanup / Memory v2 design**
   - namespace isolation,
   - forgetting policy,
   - summarization hierarchy,
   - better context compression.

---

## 5. Workflow and constraints

### Dev environment
- VS Code + Remote SSH on `msk-1-vm-ngf0`
- AI assistant via OpenRouter (Continue / Cline style workflow)
- Goal: preserve context and reduce breakage during iteration

### Rules for assistants and commits
1. First analyze, then propose a plan, then change code.
2. No broad uncontrolled refactors.
3. Preserve Viktor and production runtime unless explicitly told otherwise.
4. Prefer small reversible steps.
5. Use explicit diffs and clear commit messages.
6. Any non-trivial change must be reflected in `PITH_CHANGELOG.md`.
7. Important architectural changes go to `MASTER_PLAN.md` or ADR notes.

### Runtime constraints
- Budget target: about `$30/month`
- `hard_stop: true`
- `quality_weighted_cost` matters
- Production stability beats elegance
- Avoid large UI/frontend work until runtime reliability improves

---

## 6. Identity guardrails for development

Every meaningful change should reinforce at least one of these properties:

- **continuity**
- **memory quality**
- **orchestration clarity**
- **execution reliability**
- **observability**
- **governed evolution**

Every meaningful change should avoid pushing Pith toward:

- chatbot-first UX,
- persona-first architecture,
- uncontrolled autonomy,
- feature-zoo complexity,
- memory without governance,
- orchestration without traces.

---

## 7. Canonical references

Before making major changes, align with:

- `MANIFESTO.md`
- `PRODUCTDOCTRINE.md`
- `MASTER_PLAN.md`
- `AGI_POSITION.md`
- `EVOLUTION.md`

If code, naming or direction conflicts with those files, those documents win unless explicitly revised.

---

## 8. Architectural boundaries — what is core now, what's next, what's not

### **Core now** (what holds production and defines identity)

These components are **already in place** and must remain stable:

- **Router** (`router.py`) — model lane selection, fallback, budget enforcement, provider switching
- **RuntimePlanner** (`planner.py`) — task_type detection, direct vs orchestrated path, context assembly integration
- **Task/Artifact/Trace substrate** — canonical `TaskRecord`, `ArtifactRecord`, `Trace` entities as state layer
- **Viktor production path** (`telegram_bot.py`) — the only critical live interface right now
- **Evaluator** (`evaluator.py`) — persona coherence, context use, disclaimer detection, failure scoring
- **Memory Manager** (`manager.py`) — episodes, vector memory, user profiles, `save_episode` / `get_recent_context`
- **Orchestrator bridge** (`orchestrator.py`) — modular agent dispatch, parallel execution, synthesis
- **Evolution scaffolding** — `FailureMiner`, `PatchPlanner`, `SkillCompiler` (architectural presence, not full loop yet)
- **Observability baseline** — `episodes.db`, `llm_calls`, `failure_cases` tables

These are the **non-negotiable runtime core**. Changes here must be reversible, small, and explicitly justified.

---

### **Next substrate** (30–90 day build horizon)

What we're actively building to strengthen the runtime:

1. **Real agent implementations** (`tera`, `hex`, `coda`)
   - Currently stubs/bridges. Goal: structured outputs, typed interfaces, synthesis-ready results.
   - Replace placeholder behaviour with reliable modular workers.

2. **TraceStore v1**
   - Structured traces for every LLM call, task step, agent invocation.
   - Cost attribution per lane, per agent, per workspace.
   - Production diagnosis and observability.

3. **PithEval v0.1**
   - 30–50 ground-truth tasks (code, research, planning, diagnostics).
   - Close the loop: generation → evaluation → failure mining → patch proposal.

4. **CLI v0.1**
   - `pith ask` — direct query without Telegram
   - `pith dev` — context-aware code/architecture questions
   - `pith incident` — diagnostic/postmortem workflow
   - Goal: terminal-native, preserves workspace context.

5. **Memory v2 design**
   - Namespace isolation (user/workspace/tenant boundaries)
   - Consolidation and forgetting policy
   - Hierarchical summarization (episode → session → workspace)
   - Better context compression and retrieval ranking

6. **Tool Contracts**
   - Strongly typed, versioned, schema-validated tool invocations
   - Governance: no uncontrolled side effects, approval queues for critical actions
   - Idempotency and rollback support

7. **Governance rollout completion**
   - `PatchGate` policy enforcement (whitelist/canary/block)
   - `RolloutManager` ring-based rollout (owner → canary → full)
   - Kill switch path and rollback hooks

8. **A2A protocol**
   - Agent-to-agent async delegation
   - Shared memory namespace, capability discovery
   - Governance: agents cannot spawn uncontrolled sub-agents

These are **near-term substrate work** — they strengthen the runtime without changing its identity.

---

### **Explicitly not now** (conscious no-list to avoid drift)

What we are **not building** until the runtime core is reliable:

- ❌ **Big dashboard/UI work** — Streamlit dashboard exists but is secondary. No polish, no feature expansion until traces/observability are solid.
- ❌ **Multimodal polish** — image/video/audio are future capability layer, not runtime core. No architecture work here until Memory v2 and Tool Contracts ship.
- ❌ **Persona expansion** — Viktor is the current interface voice. No new personas, no "agent zoo", no chatbot-style UX layers.
- ❌ **Uncontrolled self-modification** — runtime can propose patches via `PatchPlanner`, but **no auto-apply without governance**. L0/L1 autonomy enforced.
- ❌ **Feature-zoo surfaces** — no Slack integration, no Discord bot, no web shell, no IDE plugin until the core runtime is observably stable for 30+ days.
- ❌ **Repo reading / document intelligence / web monitoring as core features** — these are **capability layer expansions** (Phase 5: Intelligence expansion), not runtime substrate. Build them as modular tools after Tool Contracts exist.
- ❌ **FastAPI Agent Factory production rollout** — exists as prototype/research direction, but **not** a production surface until workspace substrate and governance baseline ship.

These are **future or non-core** — they do not define Pith's identity and must not steal focus from runtime reliability.

---

*Last updated: 2026-05-07 · Pith Lab · Internal / Confidential*