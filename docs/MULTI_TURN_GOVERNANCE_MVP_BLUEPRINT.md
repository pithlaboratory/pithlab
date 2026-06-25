# Multi-Turn Governance MVP — Implementation Blueprint

> Design-level patch plan. No code, no diff, no repo changes.
> Date: 2026-06-24
> Status: Draft for review before implementation

---

## 1. Recommendation

**Recommended: Variant A — history in system_prompt.**

Rationale in one sentence: Variant A changes exactly one file (the runner), touches zero lines in the router or evaluator, and preserves 100% backward compatibility for all existing single-turn goldens.

Variant B is architecturally cleaner for a full multi-turn runtime, but for an **MVP whose sole purpose is governance eval of the final dangerous turn**, the extra risk of touching the router's `_build_payload()` and `call_llm()` API surface is not justified.

---

## 2. Variant Comparison

| Criterion | Variant A — history in system_prompt | Variant B — explicit messages array |
|---|---|---|
| **Files changed** | 1 (runner only) | 3+ (runner + router._build_payload + router.call + call_llm public API) |
| **Risk to single-turn pipeline** | Negligible — system_prompt is already appended conditionally; existing golden path untouched | Medium — touching `_build_payload()` and `call_llm()` signature. Every existing caller uses the `prompt`/`system_prompt` API; changing it introduces regression surface |
| **LLM sees structured conversation?** | No — history is flat text prepended to system_prompt | Yes — messages array with `role: user/assistant` is standard OpenAI/OpenRouter format |
| **Quality of multi-turn simulation** | Sufficient for governance eval MVP. Models can understand conversation context from serialized text. The final turn is what matters, and the model has full context. | Better — model sees exact turn structure. But the question is: does this improve governance refusal accuracy? Unknown for MVP, can be measured later. |
| **Future evolution** | Limited. To move to proper messages array later, will need Variant B changes anyway. But Variant A can be a stepping stone without breaking anything. | Direct path to full multi-turn. No migration needed later. |
| **MVP fit for governance eval** | **Excellent.** Minimal risk, fast to implement, proves the concept. Governance eval only needs to see if the final response refuses correctly given context. | Over-engineered for MVP. The router's internal message construction should not be changed until we know the full requirements for multi-turn runtime. |

### Detailed risk analysis for Variant A:

The runner currently does:
```python
call_llm(prompt=user_query, system_prompt=context_prompt)
```

Variant A changes this to:
```python
history_text = serialize_conversation(golden.get("inputs", {}).get("conversation", []))
call_llm(prompt=user_query, system_prompt=history_text + "\n" + context_prompt)
```

This is a **localized, conditional change in one file**. If `conversation` is absent (all existing goldens), `history_text` is empty string and the call is identical to today. Zero regression risk.

### Detailed risk analysis for Variant B:

Requires:
1. Adding `messages: Optional[List[Dict]]` to `router.call()` — but `call()` has 12 parameters already and uses `**kwargs`. Adding an optional param that changes how payload is built creates internal branching.
2. Changing `_build_payload()` to handle two modes (prompt-based vs messages-based).
3. Changing `call_llm()` signature.
4. Changing all existing callers? No — they keep using `prompt`/`system_prompt` and the new param defaults to None. But the internal branching in `_build_payload()` is fragile.
5. The cache key in `SimpleCache._cache_key` would need to incorporate the messages array — cache invalidation complexity.

**Verdict:** Variant B is the right long-term architecture. Variant A is the right MVP.

---

## 3. Patch Plan

### Files

| File | Change type | Required for MVP | Notes |
|---|---|---|---|
| `eval/golden/golden_workflow_schema.json` | Schema extension | Yes | Add optional `conversation` property to `inputs`. Keep `user_query` required. No breaking changes. |
| `scripts/run_single_golden_runtime.py` | Branching logic + helper extraction | Yes | Add a `build_conversation_history()` helper. Branch in `run_golden_through_runtime()`: if `conversation` present, serialize it into system_prompt. The `via_planner` path needs same treatment. |
| `core/cognition/router.py` | No change | No | Not touched for MVP. Variant A means router stays unaware of multi-turn. |
| `core/evolution/governance_evaluator.py` | No change | No | Not touched for MVP. Evaluator still receives `response` string + `context_used`. Context now includes conversation history, but evaluator doesn't care about format. |
| `core/evolution/evaluator.py` | No change | No | Not touched. |
| Existing single-turn golden YAMLs | No change | No | They have no `conversation` field → runner behaves identically to today. |

### Change details per file

#### `golden_workflow_schema.json`

- **What:** Add optional `conversation` array to `inputs.properties`
- **Type:** Schema extension (additive, non-breaking)
- **Key constraint:** `conversation` must NOT be added to `inputs.required`. Must NOT be added to `inputs.additionalProperties` (but since `additionalProperties: false`, we must explicitly add the property).
- **Backward compatibility:** `validate(instance=golden, schema=schema)` — existing YAMLs lack `conversation` → pass because it's not required. New multi-turn YAMLs include it → pass because it's a valid property.

#### `scripts/run_single_golden_runtime.py`

- **What:** Add helper `build_conversation_history(golden) → str`. Modify two points in `run_golden_through_runtime()` where system_prompt is constructed (around line 127) and where dry-run displays context. Same modification in `run_through_planner()`.
- **Type:** Branching logic + helper extraction
- **Key constraint:** If `conversation` is missing or empty, the new helper returns `""` and the pipeline is byte-identical to today.
- **The runner's output artifact** should be augmented with:
  - `payload.conversation_turn_count: int` (0 for single-turn)
  - `payload.conversation_roles: List[str]` (e.g., `["user", "assistant", "user"]`)
  - `_meta.multi_turn: bool`
  - These are metadata-only additions, no structural changes to evaluation record.

### Files NOT changed (explicitly excluded for MVP)

- `core/cognition/router.py` — no change per Variant A decision
- `core/evolution/governance_evaluator.py` — no change; evaluates final response only
- `core/evolution/evaluator.py` — no change
- Any existing golden YAML — no change
- Any CI/CD or report scripts — no change for MVP

---

## 4. Schema Delta

### Current state (simplified `inputs` section)

```json
"inputs": {
  "type": "object",
  "required": ["description", "user_query"],
  "additionalProperties": false,
  "properties": {
    "description": { "type": "string" },
    "user_query": { "type": "string" },
    "initial_context": { "type": "array", ... }
  }
}
```

### After MVP extension

```json
"inputs": {
  "type": "object",
  "required": ["description", "user_query"],
  "additionalProperties": false,
  "properties": {
    "description": { "type": "string" },
    "user_query": { "type": "string" },
    "initial_context": { "type": "array", ... },
    "conversation": {
      "type": "array",
      "description": "Optional prior conversation turns providing multi-turn context. The final turn is always user_query.",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["role", "content"],
        "additionalProperties": false,
        "properties": {
          "role": {
            "type": "string",
            "enum": ["user", "assistant"],
            "description": "Speaker role. 'user' for human messages, 'assistant' for system responses."
          },
          "content": {
            "type": "string",
            "description": "Message content of this turn."
          }
        }
      }
    }
  }
}
```

### Key design decisions

| Decision | Choice | Reasoning |
|---|---|---|
| Does `user_query` stay required? | **Yes** | Backward compatibility. All existing golden YAMLs have it. Multi-turn YAMLs also have it — it represents the final adversarial turn. |
| Role enum | `["user", "assistant"]` | `system` is excluded — system-level context goes into `initial_context` or is built from it. Mixing system messages into `conversation` would confuse the history serialization. |
| `minItems` for `conversation` | **Yes, = 1** | A conversation with 0 items is equivalent to no conversation. If present, should have at least 1 prior turn. |
| Turn alternation enforced? | **No** | Schema check is not the right place for runtime invariants. The runner should validate alternation at runtime and log a warning. The schema accepts any sequence of user/assistant roles. |
| Max conversation length? | **No schema constraint** | Defer to runner: truncate at a reasonable threshold (e.g., 20 turns or 8000 tokens) and log a warning. Not a schema concern. |
| Final turn redundancy | `user_query` should match `conversation[-1].content` if `conversation[-1].role == "user"`. But **not enforced by schema** — runner can optionally validate at runtime. | This is a documentation convention, not a schema invariant for MVP. |

### Alternative considered: conversation IS the turns (no user_query)

Not chosen for MVP because:
- Breaks `required: ["user_query"]` in schema
- Breaks all existing golden parsers that expect `inputs.user_query`
- Would force branching in the runner's core extraction logic
- Would require changes in planner path that constructs task from user_query

---

## 5. Execution Semantics

### Step-by-step (Variant A — MVP)

### 1. How the first user turn is processed

If `inputs.conversation` is present and non-empty:
- The runner extracts ALL messages from `conversation` array
- It serializes them into a single text block:
  ```
  [CONVERSATION HISTORY]
  User: {first message}
  Assistant: {first response}
  User: {second message}
  ...
  [/CONVERSATION HISTORY]
  ```
- This text block is prepended to the existing system_prompt (which still includes `initial_context` entries)
- The final `inputs.user_query` (the actual adversarial prompt) is sent as `prompt` to `call_llm()`

If `inputs.conversation` is absent:
- The runner behaves exactly as today — no history, no change

### 2. How assistant responses are used

**Key MVP decision: assistant turns from YAML are context/documentation only.**

They are NOT fed to the LLM as runtime input. They are NOT re-generated by the LLM. They serve as:
- Part of the conversation history context (serialized into system_prompt)
- Optional ground truth for future multi-turn eval comparison (not used in MVP)

Rationale:
- We don't trust the LLM to regenerate intermediate assistant responses correctly
- We don't need LLM calls for intermediate turns — the scenario is defined by the YAML author
- The only thing we need to evaluate is: "given this full conversation context, does the system correctly refuse the final adversarial query?"
- No extra cost, no extra latency, no variability

### 3. How the next user turn arrives

For MVP, there is NO sequential turn execution. All turns are static in the YAML `conversation` array. The runner does not:
- Wait for a real user to type
- Call the LLM iteratively
- Collect intermediate responses

All user turns are pre-written in the YAML. All assistant responses are pre-written in the YAML. The runner serializes them and presents the full context to the LLM in a single call with the final `user_query`.

### 4. Assistant turns from YAML

See point 2 above. Explicit documentation of the decision:

> **For MVP: YAML assistant turns are conversation history context only.**
> They are part of the scenario definition. They help the LLM understand what happened before the final turn. They are NOT regenerated, NOT verified, NOT used as expected output for intermediate steps.

This can change in a future phase when we add full turn-by-turn eval, but for MVP it is the correct simplification.

### 5. What goes to the evaluator

The evaluator (GovernanceEvaluator v1) receives exactly the same inputs as today:
- `response`: the LLM's response to the final `user_query`
- `context_used`: the full system_prompt (which now includes conversation history)
- `task_type`: unchanged from golden (e.g., `governance_refusal`)
- All other parameters (task_id, model, tokens, cost, etc.) unchanged

The evaluator does NOT:
- Receive the conversation history as a separate field
- Know whether the test was multi-turn or single-turn
- Need any changes

**This is the key architectural property of the MVP: the evaluator is completely unaware of multi-turn.**

### 6. Final eval record

Same structure as today's single-turn record, with two additive metadata changes in `payload` and `_meta`:

```json
{
  "golden_id": "governance_social_engineering_multi_v1",
  "payload": {
    "trace_id": "...",
    "task_id": "...",
    "user_query": "final adversarial query text",
    "conversation_turn_count": 5,
    "conversation_roles": ["user", "assistant", "user", "assistant", "user"],
    "initial_context_count": 2
  },
  "assistant_answer": "LLM response to final turn",
  "evaluation_record": {
    "task_success": "success",
    "quality_score": 0.85,
    "policy_violation": false,
    "trace_id": "...",
    "workspace_id": "eval_single_golden"
  },
  "_meta": {
    "multi_turn": true,
    "turn_count": 5,
    "conversation_used_in_context": true,
    "passed": true,
    "model_used": "...",
    "tokens_total": 1234,
    "notes": "MVP multi-turn: conversation history injected into system_prompt, only final turn evaluated"
  }
}
```

### 7. Logging and reporting

- The runner logs:
  ```
  INFO: Multi-turn golden 'governance_social_engineering_v1' — conversation has 5 turns, injecting into system_prompt
  ```
- If conversation is very long (>20 turns or >8000 chars), log a warning about truncation
- The output JSON is written to the same `output/eval_runs/<golden_id>.json` path pattern
- Existing report scripts (`eval_runtime_gate.py`, `eval_runtime_summary.py`) continue to work because the evaluation record structure is unchanged
- The `_meta.multi_turn` field can be used by future reporting to filter or compare multi-turn vs single-turn results

---

## 6. Open Questions / Guardrails

### Open questions to resolve before implementation

| Question | Options | Recommendation |
|---|---|---|
| Max conversation length before truncation? | (a) 10 turns, (b) 20 turns, (c) 8000 chars, (d) no limit | **20 turns or 8000 chars**, whichever is hit first. Log truncation warning. |
| Should the runner validate user/assistant alternation? | (a) yes with warning, (b) yes with error, (c) no | **Yes with warning.** If two consecutive user turns found, log warning and continue. Schema doesn't enforce this. |
| `conversation[-1].role` must be `user`? | (a) yes, it's the penultimate turn, (b) no restriction | **Document as convention, don't enforce.** The runner's serialization is role-agnostic. |
| Should the runner verify `conversation[-1].content` matches `user_query`? | (a) warn if mismatch, (b) ignore, (c) error | **Ignore for MVP.** This is a YAML authoring concern. Can add validation in a later phase. |
| `via_planner` path: same treatment? | (a) yes, (b) no — restrict MVP to direct path | **Yes, same treatment.** The planner path already has its own system_prompt construction. Apply the same conversation serialization there. |
| Should we add a `run_single_golden_runtime.py --multi-turn` flag? | (a) yes, (b) no — auto-detect from YAML | **Auto-detect from YAML.** If `conversation` present → multi-turn mode. No new CLI flags. |

### Guardrails (must NOT break)

1. **Single-turn goldens must continue to work without changes.**
   - All existing YAMLs lack `conversation` → `build_conversation_history()` returns `""` → pipeline identical.
   - Verify by running existing goldens after changes: `python scripts/run_single_golden_runtime.py eval/golden/support_ops_faq_v1.yaml --dry-run` should show no system_prompt change.

2. **Current output format must not change for single-turn cases.**
   - `payload.conversation_turn_count: 0` and `_meta.multi_turn: false` are additive. No existing field changes value.
   - Any downstream script that parses the output JSON must continue to work. Check `eval_runtime_gate.py`, `eval_runtime_summary.py`, `inspect_eval.py`.

3. **Evaluator must not be modified.**
   - `governance_evaluator.py` and `evaluator.py` are not touched. They receive the same `response` and `context_used` as before. The fact that `context_used` now includes conversation history is invisible to them.

4. **No new CLI flags for MVP.**
   - The runner auto-detects multi-turn from YAML content. No `--multi-turn` flag. Simpler UX, less code, less testing surface.

5. **No changes to the CI/CD pipeline (`evals.yml`).**
   - CI runs existing goldens via `run_single_golden_runtime.py`. If those are unchanged and the runner doesn't break, CI passes. Multi-turn goldens can be added to CI in a separate PR after MVP validation.

6. **Cost and token tracking must remain accurate.**
   - The conversation history text adds tokens to the prompt. `tokens_prompt` from the API response will reflect this. No changes needed to token tracking. The `_meta.tokens_total` already captures the real count.

7. **No changes to `workflow_type` schema constraint.**
   - `workflow_type` remains a free string. No enum validation added.

### Sequence recommendation for implementation

1. **Schema extension** — add `conversation` to `golden_workflow_schema.json` (5 minute change)
2. **Helper extraction** — add `build_conversation_history()` to `run_single_golden_runtime.py` (10 minutes)
3. **Branching logic** — modify system_prompt construction in `run_golden_through_runtime()` and `run_through_planner()` (15 minutes)
4. **Output augmentation** — add multi_turn metadata to output artifact (5 minutes)
5. **Dry-run update** — display conversation history in dry-run mode (5 minutes)
6. **Validation** — run dry-mode on existing single-turn goldens to confirm no change
7. **Test with a multi-turn golden** — create a test YAML with 3-turn conversation, run and verify output

**Total estimated implementation time: ~40-45 minutes of focused work.**