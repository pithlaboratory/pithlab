# ADR: Direct LLM flow and eval signals for `specification_draft`

## Context

The `delivery_specification_draft_v1` golden checks how the system generates a functional specification for the "Saved Views for Project Dashboard" feature. Initially, the assistant responded with a short, abstract 3‑line output (“Trend / Risk / Opportunity”) instead of a structured, multi‑section specification.

At the same time, the generic `evaluation_v1` model scored this output with `quality_score ≈ 0.79` (just below the 0.8 threshold) and a very low quality subscore, because there was no clear structure, flows, data model, edge cases, or explicit constraints.[web:79][web:76]

We identified two root causes:

1. The planner was routing `specification_draft` through an orchestrator agent that ignored the detailed system prompt and produced an abstract analysis instead of a functional spec.
2. The evaluator prompt did not contain any explicit “specification” signals (like “context”, “data model”, “edge case”, “out of scope”), so well‑structured specs were undervalued.

## Decision

We made two coordinated changes:

1. **Direct LLM flow for `specification_draft`**  
   In `core/runtime/planner.py`, the `specification_draft` workflow is now forced through a direct LLM path instead of the generic orchestrator. This path uses a dedicated system prompt that instructs the model to always produce a Markdown functional specification with **exactly eight sections**:

   1. Context and goals  
   2. Out of scope  
   3. User roles and permissions  
   4. Main user flows  
   5. States and edge cases  
   6. Data model / entities (high‑level)  
   7. Non‑functional constraints  
   8. Open questions  

   Each section must be populated with concrete, implementation‑ready details (flows, tables, entities, limits, edge cases) rather than high‑level “vision” language.[web:79][web:81]

2. **Specification‑aware quality signals in the evaluator**  
   In `core/evolution/evaluator.py`, we added explicit quality signals for specification documents, including the presence of:

   - context / goals  
   - data model / entities  
   - edge cases / states  
   - out of scope  
   - open questions  
   - user flows / user roles  
   - non‑functional constraints  

   The generic evaluation model is instructed to reward answers that contain these elements in a clear, structured format. This aligns the evaluator with how we actually want specs to look.

After these changes, `delivery_specification_draft_v1` now consistently produces a full 8‑section functional spec, and its `quality_score` increased from 0.79 to ~0.92, safely above the 0.8 threshold.

## Consequences

- The `specification_draft` workflow is now stable for product / engineering use: it produces structured, implementation‑ready specs instead of abstract commentary.
- The evaluation pipeline better reflects our true notion of “quality” for specifications: documents that cover flows, data, edge cases, and constraints are rewarded accordingly.
- Future specification‑style workflows should either reuse this pattern (direct LLM flow + specification‑aware signals) or provide an explicit justification if they diverge.