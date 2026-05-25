# PITH Capabilities Model

> PITH is a long-lived AI operating system layer built on top of runtime orchestration, memory, tasks, agents, tools, observability, and multiple user-facing interfaces.[1][2][3]

## Purpose

This document defines the capability model for PITH: what the system must be able to do, which inputs and outputs each capability owns, which infrastructure powers it, and how each capability is observed and evaluated.[1][2]

The goal is to prevent architectural drift. PITH should evolve as one coherent system rather than as a collection of disconnected features spread across Telegram, web UI, API endpoints, agents, and scripts.[1][3]

## Capability map

| Capability | What it means | Main inputs | Main outputs | Core building blocks |
|---|---|---|---|---|
| Conversational interaction | Understand and respond through chat interfaces while preserving context and mode awareness.[1] | User text, session context, workspace context.[1] | Replies, status messages, follow-up prompts, feedback actions.[1] | Telegram interface, runtime mode detection, response normalization, loading UX.[1] |
| Voice interaction | Support speech-based interaction on top of the same runtime and memory model.[1] | Audio input, transcribed utterances, conversational context.[1] | Spoken or text responses, hands-free task operations. | Voice mode policy, multimodal interface layer, runtime response formatting.[1] |
| Task orchestration | Convert requests into tracked tasks with lifecycle state and execution metadata.[1][2] | User request, workspace ID, trace ID, task metadata.[1] | Task records, status transitions, execution results, failures.[1][2] | TaskService, planner, task states, task API endpoints.[1][2] |
| Planning and decomposition | Decide how a request should be handled and whether tools, agents, or direct response paths are needed.[1] | User intent, runtime mode, memory, policies.[1] | Execution plan, selected workflow, response path, goal tags.[1] | RuntimePlanner, router, runtime modes, tool plane hooks.[1] |
| Memory management | Store and retrieve episodes, metadata, and workspace-aware context across interactions.[1] | Messages, task metadata, feedback, workspace scope.[1] | Retrieved context, saved episodes, updated metadata, continuity across sessions.[1] | Memory manager, episodes persistence, metadata enrichment.[1] |
| Web and internet research | Search the web and extract useful external knowledge for current tasks.[1] | Search query, depth, workspace, active task.[1] | Search results, summaries, links, retrieved facts. | Tool registry, search command flow, web tools integration.[1] |
| Repository and code understanding | Read repositories, scripts, configs, APIs, and architecture artifacts to build actionable system understanding.[1][2][3] | Local files, remote repositories, code structure, docs. | Architecture summaries, implementation changes, diagnostics, recommendations. | Code/file readers, repo ingestion workflows, capability-specific agents. |
| Agent factory and specialization | Create, configure, and manage reusable agents with explicit roles, models, capabilities, and tags.[2] | Agent definitions, prompts, models, tags, configs.[2] | Agent records, reusable workers, specialized execution endpoints.[2] | Agent API, agent schemas, worker configuration, model routing.[2] |
| Tool and skill acquisition | Extend the system with new tools, skills, and agent capabilities that improve task coverage.[1][2] | Capability gaps, user needs, new integrations, external tool definitions. | Registered tools, available skills, improved workflows. | Tool registry, skills layer, agent capabilities, governance policies.[1][2] |
| Observability and tracing | Make every meaningful operation inspectable, correlated, and measurable across runtime and interfaces.[1] | Trace IDs, task IDs, workspace IDs, model/cost metadata, events.[1] | Traces, metrics, logs, dashboards, failure visibility.[1] | Trace service, capture events, execution metadata, episodes metadata.[1] |
| Evaluation and feedback | Measure answer quality, capture human feedback, and feed results back into system improvement.[1] | Responses, token/cost data, user votes, task metadata.[1] | Eval blobs, feedback records, failure classes, quality signals.[1] | Evaluator, feedback handlers, eval metadata, inspect scripts.[1] |
| Governance and safety | Enforce boundaries around dangerous actions, prompt leakage, data exfiltration, and workspace isolation.[1] | Raw user input, policy patterns, workspace context.[1] | Refusals, governance traces, blocked actions, safer system behavior.[1] | Governance guards, refusal paths, trace logging, isolation patterns.[1] |
| Product shell and experience | Present PITH as a coherent product through landing pages, API explorer, dashboards, and future workspace UX.[3] | Brand system, product structure, API metadata, roadmap content.[3] | Landing pages, explorers, demos, dashboards, product trust. | Web shell, explorer UI, swagger embed, visual design layer.[3] |

## Capability layers

PITH should be understood as five stacked layers rather than one monolithic bot. The current artifacts already show a runtime layer, an interface layer, an API control layer, and an emerging product shell.[1][2][3]

1. **Interface layer** — Telegram, future voice, web chat, later desktop/mobile.[1]
2. **Cognition layer** — planner, routing, mode detection, goal selection, decomposition.[1]
3. **Execution layer** — tasks, agents, tools, workflows, queue-backed processing.[1][2]
4. **State layer** — memory, episodes, workspace context, artifacts, metadata.[1]
5. **Control layer** — observability, eval, governance, cost control, dashboards.[1][2]

## Capability contracts

Each major capability should have a stable contract so it can evolve without breaking the whole system.[1][2]

| Capability | Required contract |
|---|---|
| Conversational interaction | Must accept user input plus workspace/session context and return a safe user-visible response plus metadata.[1] |
| Task orchestration | Must create a task record with status, trace correlation, and execution result attachment.[1][2] |
| Memory | Must support write, retrieve, enrich metadata, and workspace isolation.[1] |
| Agents | Must expose identity, type, model, config, and lifecycle operations.[2] |
| Tools/skills | Must declare invocation rules, parameters, safety constraints, and observability hooks.[1] |
| Observability | Must correlate events via task/trace/workspace identifiers and capture model, token, latency, and failure data.[1] |
| Eval | Must attach quality signals to concrete tasks or episodes rather than store detached scores.[1] |

## Capability priorities

Not all capabilities are equally important right now. The current system suggests a practical order of importance based on what already exists and what still appears to be forming.[1][2][3]

### Tier 1

These are foundational and should be treated as non-negotiable:

- Conversational interaction.[1]
- Task orchestration.[1][2]
- Memory management.[1]
- Observability and tracing.[1]
- Governance and safety.[1]

### Tier 2

These drive system leverage and scale once the foundation is stable:

- Planning and decomposition.[1]
- Web and internet research.[1]
- Repository and code understanding.[1][3]
- Evaluation and feedback.[1]
- Agent factory and specialization.[2]

### Tier 3

These shape the long-term product and differentiation:

- Voice interaction.[1]
- Tool and skill acquisition.[1][2]
- Product shell and experience.[3]
- Company/workspace operating layer built on top of the same runtime principles.[1][3]

## Evolution rules

PITH should not grow by randomly adding features. Every new feature should map to one or more named capabilities in this document, otherwise it likely belongs in experimental space rather than in the core system.[1][2]

A capability should be considered mature only when it has all four of the following:

- A clear contract.
- A runtime implementation.
- Observability hooks.
- Eval or smoke-test coverage.[1]

This rule is especially important for internet access, repository reading, and skill acquisition. Those capabilities are strategically important, but they become dangerous or noisy if they are not bounded by governance, workspace isolation, and traceable execution.[1]

## Relationship to other docs

This document should sit beside the system vision and the master plan, not replace them.[1][3]

| Document | Role |
|---|---|
| `docs/PITH_SYSTEM_VISION.md` | Defines what PITH is becoming as a system and product. |
| `docs/PITH_CAPABILITIES_MODEL.md` | Defines the capability inventory and the contracts between layers. |
| `PITH_MASTER_PLAN.md` | Defines execution order, milestones, and concrete implementation work. |
| Observability / eval docs | Define operating standards for quality and inspection around specific subsystems.[1] |

## Immediate recommendations

The next useful step is to align repository structure, scripts, and roadmap items to this capability model so that each major workstream is attached to a named system capability rather than an ad hoc implementation detail.[1]

A minimal operating rule for the repo is:

- Every new subsystem should name its owning capability.
- Every capability should have at least one smoke check or eval path.
- Every externally visible feature should connect back to memory, task lifecycle, and observability where relevant.[1]