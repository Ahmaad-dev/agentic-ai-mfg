# PT4 — Project Log

Append one entry per completed sub-package. Newest at the bottom.

## Entry format
[DATE] — [AP-ID] [Short title]

Status: done / partial / blocked
Changed files: ...
What was done: 1–3 sentences.
Verification: how it was checked (test/manual/API).
Open / next: what remains or what comes next.
---

### 2026-07-08 — M0 Baseline & Scope
- **Status:** done
- **Changed files:** none (analysis only) + created `.github/instructions/first.instructions.md`, `docs/PT4_PLAN.md`, `docs/PROJECT_LOG.md`
- **What was done:** Inventoried the Phase-3 codebase. Confirmed: code under `demo/`, no confidence field, no DB, Pydantic models exist in `correction_models.py`, `apply_correction.py` writes directly to snapshot data with no gate. Established PT4 plan and agent instruction files.
- **Verification:** Two independent agent analyses agreed on structure and findings.
- **Open / next:** Begin AP1.1 (extend schema). Baseline auto-fix rate still to be measured on 5–10 snapshots for later comparison.

---

### 2026-07-08 — AP1.1 Extend schema (confidence & status)
- **Status:** done
- **Changed files:** `demo/smart-planning/runtime/correction_models.py`
- **What was done:** Additively extended the existing `CorrectionProposal` Pydantic model with two optional fields: `confidence_score: Optional[float] = None` (with a `@field_validator` enforcing the `[0.0, 1.0]` range when set) and `status: Literal["pending_review","approved","rejected","modified","applied"] = "pending_review"`. Added `field_validator` (Pydantic v2) and `Literal` to imports. No behavior change; no other file touched.
- **Verification:** Ran a test with the project `.venv`: (a) an old proposal without the new fields still parses (`status=pending_review`, `confidence_score=None`); (b) `confidence_score=1.5` raises `ValidationError`. `get_errors` on the file reported no problems.
- **Open / next:** Confidence is not yet computed (comes in AP1.3). Next: AP1.2 (split pipeline into `generate_proposal` / `apply_after_review` and halt the auto-iteration loop on `pending_review`).

---

### 2026-07-08 — AP1.2 Human-in-the-Loop toggle (no auto-apply)
- **Status:** done
- **Changed files:** `demo/agent_config.py`, `demo/agents/orchestration_agent.py`
- **What was done:** Implemented a `HUMAN_IN_THE_LOOP` governance toggle instead of the plan's pipeline-split approach (the codebase has no `apply_corrections` flag or `operation=="correct"` branch — pipeline choice is made by the LLM intent analyzer). Added `HUMAN_IN_THE_LOOP = os.getenv("HUMAN_IN_THE_LOOP", "true").lower() == "true"` to `agent_config.py` (default on/safe). In `orchestration_agent._execute_sp_agent`, when the toggle is on, all four auto-apply paths are now closed: (1) `full_correction` and (2) `correction_from_validation` are remapped to `analyze_only` (proposal only); (3) the `apply_and_upload` pipeline is blocked with a user message (no remap, since it has no proposal step); (4) the single tool `apply_correction` (tool branch) is blocked with the same message. All other tools/pipelines (validate, identify, generate, download, create, rename, analyze_only, ...) run unchanged. Runtime tools under `demo/smart-planning/runtime/` were NOT touched. Additive only.
- **Covered auto-apply paths (with toggle on):** `full_correction` → analyze_only; `correction_from_validation` → analyze_only; `apply_and_upload` → blocked; single tool `apply_correction` → blocked.
- **Verification:** `get_errors` on both files reported no problems. Legacy behavior preserved when `HUMAN_IN_THE_LOOP=false` (all paths run as before).
- **Open / next:** Confidence computation (AP1.3); central proposal record (AP1.4); the approve/reject/modify path that actually applies after review comes in AP3.

---

### 2026-07-08 — AP1.3 Raw LLM self-confidence field
- **Status:** done (AP1.3a — raw field only; formula split out to AP1.3b per user request)
- **Changed files:** `demo/smart-planning/runtime/generate_correction_llm.py`
- **What was done:** Additively extended the LLM prompt in `generate_correction_with_llm` so the model returns a `llm_confidence` (0.0–1.0) self-assessment inside `correction_proposal`, with a field note (1.0 = very confident, 0.0 = very unsure; `manual_intervention_required → 0.0`). After `json.loads`, the value is taken defensively: if the model omits `llm_confidence`, it defaults to `None` (no error raised). No formula/aggregation yet, `correction_models.py` schema NOT touched (`llm_confidence` lives only in the raw proposal JSON for now), runtime tool signature/behavior unchanged.
- **Verification:** Ran `generate_correction_llm.py --snapshot-id 2b5ee9f9-...` (existing snapshot; no EMPTY_FIELD snapshot available, used an existing one as allowed). Generated `iteration-4/llm_correction_proposal.json` now contains `"llm_confidence": 0.95` in the `correction_proposal` block. `get_errors` on the file reported no problems.
- **Open / next:** AP1.3b — combine into `confidence_score` via the plan formula (0.5·llm_self + 0.3·schema_valid + 0.2·memory, `manual_intervention_required → 0.0`) and write it into the proposal. Then AP1.4 (central proposal record).

---

### 2026-07-08 — AP1.3b Combined confidence_score (formula)
- **Status:** done
- **Changed files:** `demo/smart-planning/runtime/generate_correction_llm.py`
- **What was done:** Added a module-level `compute_confidence_score(correction_proposal)` implementing the PT4 formula `0.5·llm_confidence + 0.3·schema_valid + 0.2·memory_support`, with `memory_support = 0.0` (AP7) and the special case `action == "manual_intervention_required" → 0.0`. `llm_confidence` is taken defensively (missing/invalid → 0.0, clamped to [0,1]); `schema_valid` is determined self-contained by validating the freshly built proposal against the `CorrectionProposal` Pydantic model (added `from correction_models import CorrectionProposal`). The result is written as `correction_proposal["confidence_score"]`. Kept to one file; `correction_models.py` and runtime tool signatures untouched.
- **Verification:** Re-ran `generate_correction_llm.py --snapshot-id 2b5ee9f9-...`. Generated proposal now shows `"llm_confidence": 0.95` and `"confidence_score": 0.775`, which equals `0.5·0.95 + 0.3·1.0 + 0.2·0` — reproducible per formula. `get_errors` on the file reported no problems.
- **Note:** `schema_valid` reflects validity at generation time. The later pipeline step `validate_correction_schema_llm.py` (which can retry-fix an invalid proposal) does not recompute `confidence_score`; recomputation after a schema fix is out of scope here.
- **Open / next:** AP1.4 — persist each proposal additionally at a central location with a stable `proposal_id` (file-based JSON).

---

### 2026-07-08 — AP1.4 Central proposal record
- **Status:** done
- **Changed files:** `demo/smart-planning/runtime/generate_correction_llm.py`
- **What was done:** Added `save_central_proposal_record(...)`, called from the existing `save_correction_proposal(...)`, so every generated proposal is additionally written to a central, flat store via the same `StorageManager` (LOCAL/AZURE): path `_proposals/{proposal_id}.json`, sitting next to the per-snapshot folders (not buried inside them). `proposal_id` is deterministic/stable: `{snapshot_id}__iteration-{N}` (idempotent — a re-run updates the same record and preserves `created_at`). The record carries `proposal_id`, `snapshot_id`, `iteration`, `status`, `confidence_score`, `llm_confidence`, `action`, `created_at`/`updated_at`, a `source_path` pointer, and the full nested `proposal`. The nested `iteration-N/llm_correction_proposal.json` is left untouched. One file changed; runtime tool signatures unchanged; additive.
- **Verification:** Ran `generate_correction_llm.py --snapshot-id 2b5ee9f9-...`. Created `Snapshots/_proposals/2b5ee9f9-...__iteration-4.json` with `proposal_id`, `status: pending_review`, `confidence_score: 0.775`, and the embedded proposal; the nested iteration file was still written. `get_errors` reported no problems.
- **Design notes (stated to user):** central location = `_proposals/` prefix in the existing storage backend; id scheme = deterministic `{snapshot_id}__iteration-{N}`. AP2 migrates this file-based record into the real DB; AP3 (HitL backend) reads open proposals from here.
- **Open / next:** AP1 overall DoD met (proposal with confidence, `pending_review`, centrally findable, nothing applied). Next milestone: AP2 (persistence layer / DB).

---

### 2026-07-08 — AP1.5 Make schema_valid an explicit field
- **Status:** done
- **Changed files:** `demo/smart-planning/runtime/generate_correction_llm.py`
- **What was done:** The schema-validity signal (previously only computed transiently inside the confidence formula) is now persisted as an explicit `schema_valid: bool` field in `correction_proposal`, matching the AP1 long-form spec/DoD ("Schema-Validierung fließt in den Score ein" — now also visible). Introduced a small DRY helper `_proposal_matches_schema(...)` used both for the field and inside `compute_confidence_score`. Additive; one file; runtime tool signatures unchanged; `correction_models.py` untouched (field lives in the raw proposal JSON like `llm_confidence`).
- **Verification:** Re-ran `generate_correction_llm.py --snapshot-id 2b5ee9f9-...`. Proposal now shows `"schema_valid": true` alongside `"llm_confidence": 0.95` and `"confidence_score": 0.775`. `get_errors` reported no problems.
- **Decision (recommended path A):** Deliberately did NOT rebuild the full flat CorrectionProposal schema (proposal_id/error_type/affected_entity/suggested_value/evidence/created_at) now — those exist in the central `_proposals` wrapper and will be superseded by the AP2 DB schema. The pipeline split (`generate_proposal`/`apply_after_review`) is deferred to AP3 where apply-after-approval is actually wired (avoids dead code); the current HUMAN_IN_THE_LOOP toggle already guarantees no auto-apply.
- **Open / next:** AP2 — persistence layer (SQLAlchemy + Alembic, SQLite→Azure SQL), tables incl. proposals/reviews.

---

### 2026-07-08 — AP2 Persistence Layer (M2)
- **Status:** done
- **Changed files:** new `demo/db/__init__.py`, `demo/db/models.py`, `demo/db/session.py`, `demo/db/repository.py`; new `demo/alembic/` + `demo/alembic.ini` (first revision `AP2 initial schema`); edited `demo/web_server.py`, `demo/smart-planning/runtime/generate_correction_llm.py`, `demo/requirements.txt`, `demo/requirements-azure.txt`, `demo/.env` (commented `DATABASE_URL`), `.gitignore` (ignore local sqlite).
- **What was done:**
  - **AP2.1** SQLAlchemy 2.0 ORM models for all 7 tables (`sessions`, `messages`, `agent_runs`, `snapshots_meta`, `proposals`, `reviews`, `memory_items`) + engine/session factory (`get_engine`/`get_sessionmaker`/`init_db`).
  - **AP2.2** Alembic initialized; first autogenerated revision creates all 7 tables; `alembic upgrade head` applied to local SQLite (`demo/db/pt4.sqlite3`).
  - **AP2.3** `repository.py` with transactional CRUD (`create_session`, `add_message`, `add_agent_run`, `upsert_snapshot_meta`, `save_proposal`, plus `create_review`/`add_memory_item` ready for AP3/AP7). Wired additively + defensively into `web_server.chat()` (persists user message, assistant message, agent_run per request; DB errors never break chat) and into `generate_correction_llm.save_central_proposal_record()` (persists each proposal; runs in subprocess too).
  - **AP2.4** SQLite↔Azure SQL switch purely via `DATABASE_URL` (SQLite fallback if unset; `mssql+pyodbc://…` for Azure SQL, injected from Key Vault as env in prod). `pyodbc` added to `requirements-azure.txt`; commented example added to `.env`.
- **Verification:** Two-step verification:
  1. *Scripted (initial):* Ran the exact repository calls `web_server`/`generate_correction_llm` make directly. Row counts: `sessions=1, messages=2, agent_runs=1, proposals=1, snapshots_meta=1`; `reviews`/`memory_items` tables exist (empty).
  2. *Live end-to-end (2026-07-08 ~23:00):* Started `web_server.py`, sent real `POST /api/chat` requests via PowerShell `Invoke-RestMethod`. Orchestrator routed to SP_Agent, `generate_correction_llm.py` ran as subprocess with a real Azure OpenAI call (GPT-4o, confirmed in server logs). Final DB state: `sessions=4, messages=12, agent_runs=6, snapshots_meta=1, proposals=1, reviews=0, memory_items=0`. Confirmed in server log: `[Orchestrator] SP_Agent Intent: tool - generate_correction_llm` + `"POST /api/chat HTTP/1.1" 200`. Proposal in DB: `proposal_id=2b5ee9f9-…__iteration-4, status=pending_review, confidence=0.775, schema_valid=True`. No `apply_correction` call in the log — HUMAN_IN_THE_LOOP toggle greift korrekt.
- **Notes / deviations:** Installed `SQLAlchemy 2.0.51` + `alembic 1.18.5` into the venv (were missing). `proposals.affected_entity` is currently populated from `target_path` (coarse) — can be refined later. Token/cost fields on `agent_runs` are written as `NULL` for now (structure ready for AP6). Alembic migration files ARE tracked in git; the local `.sqlite3` is gitignored.
- **Open / next:** AP3 — HitL backend (Flask blueprint `demo/routes/review.py`, approve/reject/modify endpoints, apply-after-approval via a dedicated pipeline).

---

### 2026-07-09 — AP2.5 Token & cost tracking
- **Status:** done
- **Changed files:** `demo/agents/chat_agent.py`, `demo/agents/rag_agent.py`, `demo/agents/orchestration_agent.py`, `demo/web_server.py`, `demo/smart-planning/runtime/generate_correction_llm.py`
- **What was done:**
  - **Part A (analysis):** Confirmed that `response.usage` (prompt/completion/total tokens) existed inside each agent but was never surfaced to `web_server.chat()` — the `metadata` dict returned to the server had no token fields at all. All prior `agent_runs` rows had `NULL` for every token column.
  - **Part B (wiring):** (1) `chat_agent.py` + `rag_agent.py`: added `tokens_prompt/completion/total` from `response.usage` to their returned `metadata` dict. (2) `orchestration_agent.py`: added `_track_usage(usage)` accumulator + reset at start of each `execute()` call; called after all 5 internal LLM-call sites (planning, summarization, sub-agent interpretation, SP intent, SP result interpretation); returns aggregated `tokens_prompt/completion/total` in `result["metadata"]`, merged with sub-agent tokens. (3) `web_server.py`: added `_COST_PER_1K_TOKENS = 0.005` (USD/1K, clearly marked as assumption, overridable via env var, to be refined in AP6); passes token fields + computed cost to `add_agent_run()`. (4) `generate_correction_llm.py`: reads already-written `llm_correction_call.json` in `save_central_proposal_record`, creates a synthetic session + `agent_run` row with the subprocess tokens and cost — runtime tool signature unchanged.
  - **Part C (subprocess verification):** Real `POST /api/chat` request triggered `generate_correction_llm.py` as subprocess. DB before: `proposals=1, agent_runs=6`. DB after: `proposals=1 (same, idempotent), agent_runs=9 (+3 new)`.
- **Verification (a/b/c):**
  - **(a) Chat agent_run with tokens:** `agent=Chat, prompt=3416, completion=425, cost=$0.019205`
  - **(b) Subprocess tokens captured:** `agent=generate_correction_llm, prompt=23887, completion=139, cost=$0.12013` — written from the subprocess via the `llm_correction_call.json` read path; `agent=sp, prompt=5182, completion=381, cost=$0.027815` (orchestrator aggregate)
  - **(c) Subprocess DB path:** `proposals` unchanged at 1 (idempotent), `agent_runs` 6→9 (+3 genuine new rows from the real live run). `proposal_id=2b5ee9f9-…__iteration-4, status=pending_review, confidence=0.775`.
- **Bug caught + fixed during this AP:** An `output` variable was accidentally dropped from two LLM-call sites in `orchestration_agent.py` during the initial patch (caused "cannot access local variable 'output'" on the first run). Fixed immediately; second run succeeded.
- **Cost constant:** `_COST_PER_1K_TOKENS = 0.005` — gpt-4o blended estimate; marked as assumption; overridable via `COST_PER_1K_TOKENS` env var; will be refined per-model in AP6.
- **Open / next:** AP3 — HitL backend.

---

### 2026-07-09 — AP3.1 HitL Read-only Endpoints
- **Status:** done
- **Changed files:** new `demo/routes/__init__.py`, new `demo/routes/review.py`; edited `demo/db/repository.py`, `demo/web_server.py`
- **What was done:** Created Flask Blueprint `review_bp` (prefix `/api/review`) with two read-only endpoints backed exclusively by the DB (no JSON files read). Added `list_open_proposals_as_dicts()` and `get_proposal_as_dict()` to `repository.py` — these materialise ORM objects to plain dicts **inside** the session scope, avoiding detached-object errors. Blueprint registered additively in `web_server.py`; no existing route changed. Runtime tools not touched.
- **Verification:**
  - **(a) `GET /api/review/proposals`** → HTTP 200, JSON list with `proposal_id=2b5ee9f9-…__iteration-4`, `status=pending_review`, `confidence_score=0.775`.
  - **(b) `GET /api/review/proposals/2b5ee9f9-…__iteration-4`** → HTTP 200, full detail incl. `old_value=-2`, `suggested_value=0.965`, `reasoning`, `schema_valid=true`.
  - **(c) `GET /api/review/proposals/does-not-exist`** → HTTP 404, body `{"error": "Proposal not found", "proposal_id": "does-not-exist"}`.
- **Open / next:** AP3.2 — decision endpoints (POST approve/reject/modify, write to `reviews` table, set proposal status).

---

### 2026-07-10 — AP3.2 HitL Decision Endpoints
- **Status:** done
- **Changed files:** `demo/routes/review.py`, `demo/db/repository.py` (no other file; runtime tools under `demo/smart-planning/runtime/` untouched; `web_server.py` untouched — the blueprint was already registered in AP3.1)
- **What was done:** Added the three writing endpoints `POST /api/review/proposals/<id>/{approve,reject,modify}` to the existing blueprint. `approve` stores the AI value (`proposals.suggested_value`) as `reviews.final_value` and sets status `approved`; `reject` (comment mandatory) stores no final value and sets status `rejected` — final, no regeneration/retry; `modify` stores the human-supplied value as `reviews.final_value` and sets status `modified`, while the original AI value stays untouched in `proposals.suggested_value` as history. Added `repository.decide_proposal()`, which writes the `reviews` row and the new proposal status **in one transaction**, so the decision and the status can never drift apart. The pending-check happens inside that same transaction. Existing `create_review()` signature untouched. `reviewer_ref` is the fixed value `"demo_reviewer"` (commented in code: PT4 has no auth layer — Azure AD is explicitly out of scope, so there is no authenticated principal to attribute decisions to). **Nothing is applied to snapshot data** — `applied: false` is returned explicitly in every success body.
- **Bug fixed in `save_proposal()`:** Because `proposal_id` is deterministic (`{snapshot_id}__iteration-{N}`), a repeated generation run on the same iteration used to unconditionally reset `proposals.status` back to `pending_review`, silently destroying a human decision. `save_proposal()` now only writes the status if the row is new, or if the proposal is still `pending_review` **and** has no `reviews` row (helper `_is_still_undecided()`); otherwise it keeps the decided status and logs a warning. All other fields are still updated. Behaviour for undecided proposals is unchanged.
- **Verification (all via the real Flask routing stack against the real SQLite DB):**
  - **(a) approve** on the open proposal `2b5ee9f9-…__iteration-4` → HTTP 200; `reviews` row = `decision=approve, final_value=0.965, comment="Looks correct, plausible value.", reviewer_ref=demo_reviewer`; proposal status → `approved`.
  - **(b) approve again** on the same proposal → HTTP 409 `{"error": "Proposal has already been decided", "status": "approved"}`; `reviews` row count stays **1**.
  - **(c) reject** with comment → HTTP 200, status → `rejected`, `reviews` row present with `final_value=null`.
  - **(d) modify** with `final_value="HUMAN_VALUE_42"` vs. AI value `"AI_SUGGESTED_VALUE"` → HTTP 200; side by side afterwards: `proposals.suggested_value = "AI_SUGGESTED_VALUE"` (AI, history) and `reviews.final_value = "HUMAN_VALUE_42"` (human); status → `modified`.
  - **(e) reject without comment** (and with a blank comment) on a still-open proposal → HTTP 400 both times; status stays `pending_review`, 0 `reviews` rows. Also `modify` without `final_value` → HTTP 400. Unknown `proposal_id` → HTTP 404.
  - **(f) Bug-fix proof:** after the approve, re-ran `generate_correction_llm.py --snapshot-id 2b5ee9f9-…` (real Azure OpenAI call, prompt=23887/completion=146 tokens, wrote the same `proposal_id`). DB before: `status=approved`, 1 review. DB after: **`status=approved` (NOT reset), review row intact**, other fields refreshed. Server-side warning logged.
  - **(g) Snapshot data untouched:** all six `snapshot-data.json` files under the snapshot were SHA-256-identical before/after the endpoint calls; their mtime is still `2026-03-10`, whereas the proposal JSONs were rewritten `2026-07-10 14:41`. No apply path was reached.
- **Known divergence (deliberate, flagged):** the file-based central record `Snapshots/_proposals/<proposal_id>.json` still reports `status: pending_review` after a decision — the decision endpoints write only to the DB, and updating that file would require touching a runtime tool (forbidden this step). This is consistent with AP3.1, which declared the DB the single source of truth and stopped reading `_proposals/*.json`. To be resolved (sync or retire the file record) in AP3.3 or a later cleanup.
- **Test data cleanup:** the three synthetic proposals seeded for (c)/(d)/(e) (`ap32-test-*`) and their reviews were deleted again. Remaining DB state: 1 proposal (`2b5ee9f9-…__iteration-4`, `approved`), 1 review. **There is currently no `pending_review` proposal left** — for the AP4 UI demo a fresh proposal must be generated (or that row reset to `pending_review` and its review deleted).
- **Open / next:** AP3.3 — apply after review: `apply_after_review` pipeline (apply_correction → update_snapshot → validate), triggered only for `approved`/`modified`, writing `reviews.revalidation_result` and moving the status to `applied`.

---

### 2026-07-10 — AP3.3a Apply Preparation (iteration guard + modify file prep)
- **Status:** done
- **Changed files:** new `demo/routes/apply_prep.py` (only file). No runtime tool touched, no endpoint changed, `execute_pipeline` not called. **Nothing is applied.**
- **Module choice:** own module instead of adding to `review.py`. `review.py` is the HTTP layer; this logic manipulates snapshot data files and needs a `sys.path` entry for `demo/smart-planning/runtime/` to reach `runtime_storage`. Keeping that out of the blueprint keeps the HTTP layer free of runtime imports and makes both functions testable without a Flask app. Reasoning is in the module docstring.
- **What was done:**
  - **`check_iteration_is_latest(proposal_id)`** — parses `{snapshot_id}__iteration-{N}` and compares N against `get_latest_iteration_number(snapshot_id, require_file="llm_correction_proposal.json")` (the exact lookup `apply_correction.py` performs internally). Returns `(True, "")` or `(False, msg)`. Needed because `apply_correction.py` takes no proposal id — it always resolves the *highest* iteration with a proposal file, so a newer iteration would silently apply a different correction than the reviewed one. Also returns `False` for a malformed `proposal_id` and for a snapshot with no proposal file at all.
  - **`prepare_proposal_for_apply(proposal_id, decision, final_value)`** — `approve`: leaves `new_value` untouched (the AI value *is* what gets applied) and only stamps `value_source: "ai_suggested"`; returns an explicit result dict, no silent no-op. `modify`: first copies the untouched document to `llm_correction_proposal.ai_original.json` in the same iteration folder (**never overwritten** if it already exists — the first AI state is authoritative), then replaces `correction_proposal.new_value` with the human `final_value` and stamps `value_source: "human_modify"`. `additional_updates` are deliberately left as the AI proposed them (PT4 guardrail: one confidence score and one approval per whole proposal — no per-update human override); commented in code. All file access goes through the existing `StorageManager` (LOCAL/AZURE), never bare `open()`.
- **Schema question resolved (was a blocker condition in the task):** `LLMCorrectionResponse` / `CorrectionProposal` in `correction_models.py` are plain Pydantic v2 models **without** `extra="forbid"`, so unknown keys are ignored, not rejected. The extra `value_source` field therefore does **not** trigger a `ValidationError` in `apply_correction.validate_proposal_schema()`. Verified empirically, see (d). Note: `apply_correction.apply_correction()` reads the value from the **raw dict** (`proposal.get("new_value")`), not from the validated model, so the human value is what would actually be applied. The field could be kept.
- **Verification (isolated test snapshot `ap33a-test-snapshot`, built as a copy of the real iteration-4 proposal with an injected `additional_updates` entry so "unchanged" is provable; deleted afterwards):**
  - **(a) Guard positive:** `ap33a-test-snapshot__iteration-5` (5 = highest) → `(True, "")`.
  - **(b) Guard negative:** `…__iteration-2` while 5 exists → `(False, "Proposal iteration 2 is not the latest (latest: 5); applying it would apply a different correction than the one reviewed")` — both numbers named. Additionally: malformed id → `False` with a format message; unknown snapshot → `False` with "no iteration with llm_correction_proposal.json found".
  - **(c) modify prep:** `ai_original.json` created and holds the AI value `0.965`; live `llm_correction_proposal.json` now holds `"HUMAN_VALUE_0.42"` in `correction_proposal.new_value`; `value_source="human_modify"`; `additional_updates` byte-identical to before.
  - **(c2) Idempotence of the backup:** a second `modify` returned `ai_original_written=False` and the copy still held the AI value `0.965` — the original is never clobbered.
  - **(c3) approve:** `value_changed=False`, `new_value` still `0.965`, `value_source="ai_suggested"`, and **no** `ai_original.json` written.
  - **(d) Schema compatibility:** the modified file, the approve-stamped file and the `ai_original` copy all validate against `LLMCorrectionResponse` — so `apply_correction.py` will not abort with `sys.exit(1)` later.
  - **(e) Real snapshot untouched:** all six `snapshot-data.json` of `2b5ee9f9-…` SHA-256-identical; the real `iteration-4/llm_correction_proposal.json` (the AP3.2 evidence) byte-identical; no `ai_original.json` leaked into the real snapshot.
- **Note / risk carried into AP3.3b:** the guard reads the filesystem, the decision lives in the DB — between guard check and `apply_correction` invocation a new iteration could theoretically appear (TOCTOU). Single-user demo, so accepted; worth a comment when the pipeline is wired.
- **Open / next:** AP3.3b — caller that runs `sp_agent.execute_pipeline("apply_and_upload", snapshot_id)` from the review endpoint (lazy `SPAgent` singleton in `review.py` to avoid the circular import with `web_server.py`), writes the structured re-validation result into `reviews.revalidation_result`, sets the proposal status to `applied` and updates `snapshots_meta.errors_after`. Then AP3.3c (document `_proposals/*.json` as a generation-time store without status meaning; generate a fresh `pending_review` proposal for AP4).

---

### 2026-07-10 — AP3.3b Apply after review (first real write to snapshot data)
- **Status:** done
- **Changed files:** `demo/routes/review.py`, `demo/db/repository.py`. No runtime tool touched, no new pipeline defined, `sp_agent.py` unchanged.
- **What was done:** `approve` and `modify` now trigger the actual application after the decision is committed. New `_apply_after_review()` in `review.py` runs: governance check → AP3.3a iteration guard → `prepare_proposal_for_apply()` → `sp_agent.execute_pipeline("apply_and_upload", snapshot_id)` (existing pipeline: apply_correction → update_snapshot → validate_snapshot, no auto-iteration loop) → persist re-validation → `snapshots_meta.errors_after/warnings_after/last_validated_at` → proposal status `applied`. `reject` still applies nothing. `SPAgent` is held as a lazy module singleton (`_get_sp_agent()`), avoiding the circular import with `web_server.py`; `BaseAgent.__init__` only assigns attributes, so instantiation in request context is cheap. New repository helpers: `get_decision_state()`, `set_proposal_status()`, `set_latest_review_revalidation()` (existing signatures untouched).
- **Governance:** a prominent block at the top of `review.py` documents that this is the ONLY place in the system that legitimately writes snapshot data, that it bypasses the `HUMAN_IN_THE_LOOP` toggle (which sits in `orchestration_agent`, not in `SPAgent`), and why that is intended. `_apply_after_review` re-derives the authorisation from the DB rather than trusting its caller: status must be `approved`/`modified` **and** at least one `reviews` row must exist, otherwise HTTP 409. Iteration guard failure → HTTP 409. Both leave the decision standing and apply nothing.
- **Error handling:** a failing pipeline step leaves the status at `approved`/`modified` (never `applied`), returns HTTP 502, and the outcome is written into `reviews.revalidation_result` anyway, so the audit trail records the attempt. The human can trigger again.
- **Deviation from the task (verified, not assumed):** step 5 of the assignment assumed `result["validation"]` comes out of the pipeline. It does not — `_execute_pipeline` keeps only `stdout` per step, and fills `final_validation` **only** for `full_correction`/`correction_from_validation`, so for `apply_and_upload` it stays `None`. Instead of changing `sp_agent.py` (out of scope, would alter existing agent behaviour), the structured result is read after the run via `agent._read_validation_data(snapshot_id)` — the same parser `_run_tool` applies to a direct `validate_snapshot` call. Commented in code.
- **Timeout boundary (documented in the docstring):** the call is synchronous by design. `_run_tool` allows 90 s per tool and `_execute_pipeline` retries a failing step up to 3 times → worst case ≈ 3 tools × 3 attempts × 90 s. A healthy run takes seconds. Moving this to a background job is the lever if AP4 needs a fast ack.
- **Test-data situation (important):** the old snapshot `2b5ee9f9-…` **no longer exists on the server** (HTTP 404 on the validation endpoint) — it is a stale local artifact. On a freshly created snapshot `ec96832c-1573-4ad4-995a-77d541b258f7` the validation endpoint returned zero messages, so `identify_error_llm` found nothing and `generate_correction_llm` aborted ("No iteration folders with llm_identify_response.json"). An LLM-generated proposal was therefore not obtainable. Since AP3.3b verifies the **apply path**, not proposal generation, the proposal files + DB rows were constructed by hand (schema-valid, targeting the real, genuinely empty `demands[0].demandId` — the PT4 vertical-slice error type). `apply_correction`, `update_snapshot` (real PUT) and `validate_snapshot` (real OAuth+GET) all ran for real against the server via VPN. **The "zero messages" observation was later explained — see the defect entry below; it is NOT true that the snapshot had no errors.**
- **Verification (snapshot `ec96832c-…`, VPN active; endpoints driven through the real Flask routing stack):**
  - **(c) reject applies nothing:** HTTP 200, status `rejected`, `applied=false`; `snapshot-data.json` SHA-256 identical, `demandId` still `""`.
  - **(a) approve applies the AI value:** before `demandId=""` → HTTP 200, `applied=true`, `status=applied`, `value_source=ai_suggested` → after `demandId="D100005_001"`. `reviews.revalidation_result` filled (`pipeline_success: true`, `validation: {is_valid: true, errors: 0, warnings: 0}`), `snapshots_meta` updated to `errors_after=0, warnings_after=0, last_validated_at=2026-07-10 14:07:50`.
  - **(b) modify applies the HUMAN value:** AI value `"AI_GUESS_999"`, human `final_value="D100005_001"`. After apply: `snapshot-data.json` holds `"D100005_001"` (the human value); `proposals.suggested_value` still `"AI_GUESS_999"` (AI history); `reviews.final_value="D100005_001"`; `llm_correction_proposal.ai_original.json` still carries `"AI_GUESS_999"`. `value_source=human_modify`.
  - **(d) governance blocks a pending proposal:** `_apply_after_review()` called directly on a `pending_review` proposal (no decision) → HTTP 409, `review_count=0`, `snapshot-data.json` SHA-256 unchanged.
  - **(e) iteration guard blocks a stale decision:** decision recorded on iteration 4, then iteration 5 created → HTTP 409, reason *"Proposal iteration 4 is not the latest (latest: 5); applying it would apply a different correction than the one reviewed"*; `snapshot-data.json` unchanged.
  - **AP3.2 evidence intact:** `2b5ee9f9-…__iteration-4` still `approved`, untouched.
- **CORRECTION to the caveat above (investigated 2026-07-10, after the snapshot UI showed errors):** the claim "the server reports no errors" was **wrong** — it was an artefact of how server-side validation is triggered. Findings, all measured:
  1. `PUT .../snapshots/{id}` (`update_snapshot.py`) **clears** the snapshot's validation messages. `GET .../validation-messages` then returns `[]` and **stays** empty — polled for 150 s, nothing appeared. It is not a timing/latency effect.
  2. Validation is an explicit async job: `POST .../snapshots/{id}/validate` returns `{"type":"VALIDATE","status":"QUEUED"}` and the messages appear within seconds. `GET .../validate` → 405, i.e. POST-only. Opening the "Validierung" tab in the web UI triggers exactly this — which is why the messages were visible there but not to our tooling.
  3. `validate_snapshot.py` only performs the `GET`; it never triggers the job. **Consequence: the re-validation step of `apply_and_upload` (and of `full_correction`/`correction_from_validation`) systematically reads an empty list right after an upload and reports `is_valid=true, errors=0` — a false green.** The `revalidation_result` and `snapshots_meta.errors_after=0` recorded by the AP3.3b run above are therefore not meaningful; the plumbing is proven, the numbers are not.
  4. Causal proof with an explicit trigger, on the same snapshot: `demandId=""` → upload → `POST /validate` → **8 messages, 3 ERROR**, including `[validate_unique_ids] Demand IDs must not be empty`. Then `demandId="D100005_001"` → upload → `POST /validate` → **7 messages, 2 ERROR**, that error gone. So the correction applied in (a)/(b) really did clear a server-flagged ERROR; the true numbers are `errors_before=3, errors_after=2`. The two remaining ERRORs (Article 124211 missing `work_item_configs`) are pre-existing and unrelated.
- **Resulting defect (open, not fixed in this package):** the re-validation is not trustworthy until the validate job is triggered before reading the messages. A fix must not modify `validate_snapshot.py` (runtime tool, hard rule). Cleanest option: trigger the job from our own code before the pipeline's `validate_snapshot` step (or before reading the result), reusing `validate_snapshot.SmartPlanningAPI` by **import** (importing does not change the tool). This also affects the pre-existing Phase-3 pipelines and the AP-E baseline measurement.
- **Test-fixture cleanup:** the (d)/(e) fixtures (`…__iteration-4`, `…__iteration-5`, incl. their `reviews` rows and iteration folders) were removed. Remaining: iteration-1 `rejected`, iteration-2 `applied`, iteration-3 `applied` — the genuine evidence. `demands[0].demandId` is back to the correct `"D100005_001"` and uploaded. **No `pending_review` proposal exists** — AP3.3c still owes AP4 a fresh one.
- **Open / next:** (1) Fix the re-validation trigger (see defect above) — proposed as **AP3.3d**, since it changes apply behaviour and must not be smuggled into AP3.3c. (2) AP3.3c — document `_proposals/*.json` as a generation-time store without status meaning (not synced, not read), and produce a fresh `pending_review` proposal for the AP4 UI. The earlier blocker is lifted: after a `POST /validate` the snapshot reports 2 real ERRORs, so `identify_error_llm` → `generate_correction_llm` can now produce a genuine LLM proposal.

---

### 2026-07-10 — AP3.3d Re-validation trigger (fix the false green)
- **Status:** done
- **Changed files:** new `demo/routes/server_validation.py`; edited `demo/routes/review.py`. No runtime tool modified (`validate_snapshot.SmartPlanningAPI` is imported, not changed); `repository.py` unchanged (`upsert_snapshot_meta(**fields)` already accepts the before-columns).
- **What was done:** `trigger_server_validation(snapshot_id, timeout_s=60)` fires `POST .../snapshots/{id}/validate` and waits for completion, then reports `{ok, job_id, status, waited_s}`. Wired into `_apply_after_review` via a small `_validate_now(agent, snapshot_id)` helper (trigger → wait → refresh the local file with the `validate_snapshot` tool → return its structured `validation`). It is now called **twice**: once before applying to capture the real `errors_before`, once after applying for the real `errors_after`. `revalidation_result` gained `errors_before`, `errors_after`, `validation_trigger`; `snapshots_meta` now gets `errors_before/warnings_before` too. The pipeline's own final `validate_snapshot` step is left in place but its result is no longer trusted (documented in code).
- **Completion signal (no job-status endpoint exists):** probed `/jobs/{id}`, `/snapshots/{id}/jobs`, `/solver-jobs/{id}`, `/snapshots/{id}/validation-status` → all 404. The reliable signal is the snapshot object itself: `GET .../snapshots/{id}` lists the job under `solverJobs`, where it transitions `QUEUED → FINISHED` with a `finishedAt`. `_job_status()` polls that job by id. This cleanly separates "job still running" (keep waiting) from "job finished, snapshot genuinely has no messages" (empty list is the real answer) — no fragile heuristic needed. Terminal non-success states (`FAILED`/`ERROR`/`CANCELLED`) end the wait too; a real timeout returns `ok=False` with a clear error rather than a silent empty result.
- **Verification (through the review endpoint, snapshot `ec96832c-…`, VPN active):** broke `demands[0].demandId` → uploaded → seeded a `pending_review` proposal at iteration-4 (latest, passes the AP3.3a guard) → `POST /api/review/proposals/<id>/approve` → HTTP 200, `applied=true`. Results: `revalidation_result.errors_before=3, errors_after=2`; `validation_trigger={ok: true, status: FINISHED, waited_s: 3.4}`; `snapshots_meta=(errors_before=3, warnings_before=5, errors_after=2, warnings_after=5)`; `reviews.revalidation_result` in the DB carries `3/2`; local `demandId` restored to `"D100005_001"`; the `Demand IDs must not be empty` message is **gone** afterwards (7 messages, 2 ERROR — the two pre-existing Article-124211 errors remain). This is the AP3.3b false green fixed: real numbers, not `errors_after=0`.
- **Note:** each apply now costs two validation jobs (~3–4 s each observed) on top of the pipeline, still well inside the synchronous-call budget. Test fixture (iteration-4 + its DB rows) removed afterwards; remaining genuine evidence unchanged (iteration-1 rejected, 2/3 applied). Still **no `pending_review` proposal** for AP4 — that is AP3.3c.
- **Open / next:** AP3.3c — document `_proposals/*.json` as a generation-time store without status meaning; produce a fresh `pending_review` proposal for the AP4 UI (now genuinely possible via `identify_error_llm` → `generate_correction_llm` once a validation job has run).

---

### 2026-07-10 — AP3.3c Central-record doc + first real LLM proposal for AP4
- **Status:** done
- **Changed files:** `demo/smart-planning/runtime/generate_correction_llm.py` (comment only — additive, permitted under the new rule; no behaviour change). Data artifacts produced by the real run (not code): `iteration-4/llm_correction_proposal.json` + `_proposals/…__iteration-4.json` + one `proposals` DB row. No other code touched; nothing applied to snapshot data.
- **Part 1 — `_proposals/*.json` divergence resolved documentarily (not by syncing):** added a comment at the write site in `save_central_proposal_record()` stating that the file is a generation-time record whose `status` is frozen at `pending_review` and is deliberately NOT synced with review decisions; the DB (`proposals.status`) is the single authoritative status source (AP3.1). Nothing synced, nothing removed. Rationale: one authoritative source + one explicitly non-authoritative record avoids the two-writers-for-one-state bug that syncing would create.
- **Part 2 — real, LLM-generated proposal on `ec96832c-…` (no seeding, no constructed error):**
  - **(a) Validation state before generation:** triggered the job (AP3.3d), then read: **2 ERROR, 5 WARNING**. ERROR wording verbatim: `[validate_work_item_configs_completeness] Article 124211 is missing work_item_configs for: ABF01, BA01, HE01, QS01, QS02, RF01, RF02, VOAR01, VOPU01, WART01, WART02, WART03, WART04. Cannot process article.` and `[validate_start_end_operation_existence] Article 124211 is missing work_item_config for HE01. Cannot process article.`
  - **(b) Full `correction_proposal` block (real LLM, gpt-4o, 53 377 tokens):** `action=update_field`, `target_path=articles[312].workItemConfigs`, `current_value=[]` (empty), `new_value`= a list of **13** workItemConfig objects (ABF01…WART04, each with rampUpTime/netTimeFactor, BA01 also `sequence:"HP"`), `additional_updates=[]`, `llm_confidence=0.95`, `schema_valid=true`, `confidence_score=0.775` (= 0.5·0.95 + 0.3·1.0 + 0.2·0, formula-exact), `status` not in the raw file (DB carries it). `reasoning`: the article is missing mandatory workItemConfigs; similar articles in the same department (AfG - Homo/Past) and workPlan (SP10 SP01) consistently carry these configs, so it fills them in for completeness. **Outcome = a plausible correction (a genuine demo case), not `manual_intervention_required`** — so the AP1.3 zero-confidence special case does not apply here. Whether the 13 filled-in values are domain-correct is for the human reviewer; not beautified.
  - **(c) In DB as `pending_review`, retrievable via the endpoint:** `GET /api/review/proposals` → HTTP 200, list contains `…__iteration-4` with `status=pending_review, confidence_score=0.775, target_path=articles[312].workItemConfigs`. `GET /api/review/proposals/<id>` → HTTP 200, `status=pending_review`.
  - **(d) Nothing applied:** `snapshot-data.json` SHA-256 identical before and after (`7174a169…`).
- **Honest anomaly (pre-existing runtime-tool bug, NOT fixed here):** `error_analyzed.error_type` in the wrapper — and therefore `proposals.error_type` in the DB and the endpoint response — reads **`DUPLICATE_ID`**, which is wrong: the real error is missing work_item_configs. `identify_error_llm`'s own `llm_analysis` had the correct description and its search was right (`search_mode=value, search_value=124211`), and the correction targets the correct path — so this is a mislabel in one metadata field, not a wrong correction. It lives in a runtime tool's construction of `error_analyzed`; fixing it is out of scope for AP3.3c (which is additive-comment + generation only). Flagged for a later runtime-tool cleanup. Also: `identify_error_llm` stdout printed `Error Type: DUPLICATE_ID` and its search block many times (loop over messages), noisy but not fatal.
- **State for AP4:** exactly one `pending_review` proposal now exists (`ec96832c-…__iteration-4`), real and LLM-generated — the UI has something genuine to display. Other rows unchanged (iteration-1 rejected, 2/3 applied; `2b5ee9f9` approved).
- **Open / next:** AP3 (HitL) is functionally complete end-to-end (read → decide → apply → real re-validation, with a live demo proposal). Candidate follow-ups: **AP3.3e** runtime-tool cleanup for the `error_type` mislabel + `identify` stdout noise (additive); then AP4 (HitL UI) — first fully demo-ready milestone.

---

### 2026-07-10 — AP3.6a Diagnosis: error-classification chain (measure only)
- **Status:** done (diagnosis only — no code changed, nothing repaired)
- **Changed files:** none (read + run + log). One throwaway snapshot `ap36a-emptyfield-test` was created for one EMPTY_FIELD identify run and deleted again; real snapshots untouched.
- **Root cause found — it is NOT `identify_error_llm`, and it IS systematic.** `error_type` is set in TWO places, and the wrong one wins:
  - **`identify_error_llm.py`** asks the LLM for `error_type` as a free-text "brief description" (prompt line 168). This value is **correct in 6/6 cases** (see table) and lands in `iteration-N/llm_identify_response.json` → `llm_analysis.error_type`. This tool is CLEAN.
  - **`identify_snapshot.py`** (the tool `identify_error_llm` triggers) then OVERWRITES the concept with a hardcoded heuristic (lines 925–931): `empty_field → "EMPTY_FIELD"`; `value` mode → `"DUPLICATE_ID" if len(results) > 1 else "SINGLE_MATCH"`; `0 hits → "NO_RESULTS_FOUND"`. This label is written to `last_search_results.json`. **This is the bug's origin.**
  - **`generate_correction_llm.py`** (lines 406–410) copies `error_type` + `results_count` verbatim from `last_search_results.json` into the proposal's `error_analyzed`, which is what reaches the DB (`proposals.error_type`). It is a PROPAGATOR, not the origin.
  - **`validate_correction_schema_llm.py`**: unrelated (schema validation only). CLEAN.
- **A — how `error_type` is determined:** not an enum, not regex on the message, not a real classifier. The authoritative label is a **hit-count heuristic** on the search value: value-mode + more than one occurrence ⇒ `DUPLICATE_ID`, regardless of the true error. "missing work_item_configs" ends up `DUPLICATE_ID` because the search value `124211` occurs 8× (1 article + 7 demand references), i.e. `len(results)=8 > 1`.
- **B — `results_count` / `search_mode` / `search_value`:** `search_mode` (value|empty_field) and `search_value` (the ID or field name) are chosen by the LLM. `results_count = len(results)` = **number of occurrences of the search value in the snapshot** (`identify_snapshot.py` line 1013), NOT the number of missing/affected items. So `results_count: 8` for `124211` is correct for what it measures (8 occurrences of "124211"); it is unrelated to the 13 missing workItems. Not a counting bug — it counts a different quantity than one might expect.
- **C — empirical run over error types** (5 cases from existing data, no new cost + 1 fresh EMPTY_FIELD run on a throwaway snapshot):

  | # | Real error (message) | LLM free-text error_type | mode | **authoritative error_type (→DB)** | count | correct? |
  |---|---|---|---|---|---|---|
  | 1 | Demand IDs must not be empty (vertical slice) | "Empty demand IDs" | empty_field | **EMPTY_FIELD** | 1 | ✅ |
  | 2 | Article 124211 missing work_item_configs | "Missing work_item_configs…" | value | **DUPLICATE_ID** | 8 | ❌ |
  | 3 | Demand IDs must be unique — duplicates D250015_002 | "Duplicate Demand ID" | value | **DUPLICATE_ID** | 3 | ✅ |
  | 4 | Article 100265 invalid rel_density_min -2.0 | "Invalid value for rel_density_min" | value | **DUPLICATE_ID** | 7 | ❌ |
  | 5 | Missing work plans for IDs: SP10 DP01 | "Missing work plans…" | value | **SINGLE_MATCH** | 1 | ❌ |
  | 6 | Equipment references non-existent predecessor ADC01 | "Invalid equipment predecessor reference" | value | **SINGLE_MATCH** | 1 | ❌ |

  LLM free-text error_type: **6/6 correct**. Authoritative (heuristic) error_type: **correct only for EMPTY_FIELD and genuine duplicates (2/6)**; wrong for invalid-value, missing-field, missing-reference, dangling-reference.
- **D — assessment (honest, not dramatized):** The mislabel is **systematic, not sporadic**: it fires deterministically whenever a value-mode search returns a hit count that does not coincide with a real duplicate. `DUPLICATE_ID` really means "value appears >1×"; `SINGLE_MATCH` really means "value appears once" — neither is an error classification. It is correct only when the underlying error genuinely is a duplicate-ID. **BUT: no evidence it produced a wrong correction.** In case 2 the generation LLM still filled the workItemConfigs correctly despite the `DUPLICATE_ID` label, because it reads the raw error message + search results, not just the label. So the demonstrated harm is **wrong metadata** (DB `proposals.error_type`, anything a reviewer/dashboard reads, any future logic that branches on `error_type`), with a latent risk of misleading generation on harder cases — not a proven wrong-fix. Clean tools: `identify_error_llm`, `validate_correction_schema_llm`. Buggy: `identify_snapshot` (origin). Passive carrier: `generate_correction_llm`.
- **Recommendation (NOT implemented):** the pipeline already computes a correct label — `identify_error_llm`'s `llm_analysis.error_type` — and then discards it in favour of the heuristic. Cheapest robust fix: carry the LLM's free-text/normalised error_type through to `error_analyzed` instead of the hit-count heuristic, or derive `error_type` from the `[validate_*]` validator tag in the message. To be scoped as **AP3.6b** (additive; would also subsume the earlier AP3.3e note).
- **Reliable vs not:** the chain's error_type is **reliable for EMPTY_FIELD and true duplicate-ID errors**; **unreliable for every other value-mode error** (invalid value, missing field/config, missing/dangling reference). `search_mode`/`search_value` and the LLM's own analysis are reliable across the board.
- **Open / next:** decide whether to schedule AP3.6b (fix) now or after AP4; update the backlog AP3.6 item with this diagnosis.

---

### 2026-07-10 — AP3.6b-1 Tag-derived error_type (additive, side channel)
- **Status:** done
- **Changed files:** `demo/smart-planning/runtime/identify_error_llm.py` (only). `identify_snapshot.py` and `generate_correction_llm.py` deliberately untouched — the authoritative `error_type` in the data flow is NOT switched over yet (that is AP3.6b-2).
- **What was done:** Added `derive_error_type_from_message(message)` — regex-extracts the leading `[validate_<name>]` tag and returns `<NAME>` upper-cased (`validate_` stripped), or `None` if no tag is present (defensive, no raise). In `analyze_validation_with_llm`, right after `selected_error` is resolved, the derived value is attached additively as a new field `llm_response["tag_error_type"]` — so it flows into `iteration-N/llm_identify_response.json` (`llm_analysis.tag_error_type`). The existing free-text `error_type`, `search_mode`, `search_value` and all other fields are unchanged; nothing is overwritten. Written always (as `null` when no tag) for a consistent structure.
- **Verification (offline, pure text — no LLM cost):**

  | input message | tag_error_type | expected | ok |
  |---|---|---|---|
  | `[validate_work_item_configs_completeness] Article 124211 …` | WORK_ITEM_CONFIGS_COMPLETENESS | same | ✅ |
  | `[validate_unique_ids] Demand IDs must be unique …` | UNIQUE_IDS | same | ✅ |
  | `[validate_density_values] Article 100265 … invalid rel_density_min …` | DENSITY_VALUES | same | ✅ |
  | `[validate_start_end_operation_existence] Article 124211 missing work_item_config for HE01 …` | START_END_OPERATION_EXISTENCE | same | ✅ |
  | `No tag here, just a plain message …` | None | None | ✅ |

  Edge cases also pass: `None`→`None`, `""`→`None`, leading whitespace before the tag is tolerated (`   [validate_foo_bar] x`→`FOO_BAR`). Only `identify_error_llm.py` changed (git: 1 file, +28/-1; the `generate_correction_llm.py` M in the tree is from AP3.3c).
- **Note:** For the 124211 demo case this now yields the correct `tag_error_type=WORK_ITEM_CONFIGS_COMPLETENESS` alongside the still-wrong heuristic `error_type=DUPLICATE_ID`; the two coexist until AP3.6b-2 promotes the tag value to the authoritative `error_type` consumed by `generate_correction_llm.error_analyzed` and the DB.
- **Open / next:** AP3.6b-2 — make `tag_error_type` the source for `error_analyzed.error_type` (and thereby `proposals.error_type`), keeping the heuristic label only as a fallback / secondary field. Then re-check the AP3.6a table end-to-end.

---

### 2026-07-10 — AP3.6b-2 Promote tag_error_type to authoritative error_type
- **Status:** done
- **Changed files:** `demo/smart-planning/runtime/generate_correction_llm.py` (only this step). `identify_snapshot.py` intentionally untouched — confirmed no diff; its hit-count heuristic now feeds only the retained `legacy_error_type` (dead as the authoritative value; cleanup is a separate backlog item).
- **What was done:** In `main()`'s `error_analyzed` construction, `error_type` now comes from `identify_response["llm_analysis"]["tag_error_type"]` (the reliable `[validate_*]`-tag value from AP3.6b-1). Fallback to the old `search_results.get("error_type")` when the tag is missing/`null` (message without a tag) — old behaviour preserved for those cases. The old heuristic value is kept additively as `legacy_error_type`; `search_mode`, `search_value`, `results_count` unchanged. `identify_response` was already loaded before this point (line ~385), so no load had to be moved; the lookup is defensive (`(identify_response.get("llm_analysis") or {}).get(...)`), so a missing/odd response falls back instead of crashing.
- **Verification (2 real LLM runs on `ec96832c` + 1 throwaway EMPTY_FIELD case; DB durchstich each):**
  - **(a) 124211 work_item_configs — the core fix:** re-ran identify (→ iteration-5, `tag_error_type=WORK_ITEM_CONFIGS_COMPLETENESS`) + generate. `error_analyzed` now: `error_type="WORK_ITEM_CONFIGS_COMPLETENESS"`, `legacy_error_type="DUPLICATE_ID"`, `search_mode=value, search_value=124211, results_count=8`. **The DUPLICATE_ID mislabel is gone from the authoritative field.**
  - **(b) EMPTY_FIELD (empty demandId, throwaway snapshot):** `error_analyzed.error_type="UNIQUE_IDS"` (tag of `[validate_unique_ids]`), `legacy_error_type="EMPTY_FIELD"`. The tag value is the validator source-of-truth and is not worse than before (both are meaningful; the tag is now consistent system-wide).
  - **(c) DB durchstich:** `proposals.error_type` = `WORK_ITEM_CONFIGS_COMPLETENESS` for iteration-5 and `UNIQUE_IDS` for the throwaway — the new value reaches the DB, not just the JSON file.
  - **(d) Scope:** only `generate_correction_llm.py` edited this step; `identify_snapshot.py` unchanged (git: no diff). `snapshot-data.json` SHA-256 unchanged (`7174a169…`) — nothing applied.
- **Demo-state change (deliberate, flagged):** running generate created a fresh, correctly-labelled proposal `ec96832c-…__iteration-5` (pending_review, `WORK_ITEM_CONFIGS_COMPLETENESS`). The old `iteration-4` proposal (pending, mislabelled `DUPLICATE_ID`) was stale — no longer the latest iteration, so it would fail the AP3.3a guard anyway — so its DB row was removed (folder kept as history). **The single pending demo proposal for AP4 is now `ec96832c-…__iteration-5`** (the backlog "iteration-4" reference is superseded by iteration-5). Throwaway snapshot + its DB rows deleted.
- **Note:** existing DB rows written before this fix still carry the old labels (e.g. `2b5ee9f9-…__iteration-4` = `DUPLICATE_ID`, and the applied EMPTY_FIELD rows). Not back-filled — historical record. New proposals are correct from here on.
- **Open / next:** optional AP3.6c — remove the dead heuristic in `identify_snapshot.py` (or make it emit the tag directly), and optionally drop `legacy_error_type` once confidence is established. Otherwise AP3.6 (error-classification) is functionally resolved: authoritative `error_type` is now tag-sourced and correct across the tested error types.

---

### 2026-07-11 — AP3.5a Anchor guard metadata (KIND + target identity)
- **Status:** done (Teil 0 diagnosis + user decision + Teil 1 build)
- **Changed files:** `demo/smart-planning/runtime/generate_correction_llm.py` (only this step; `identify_snapshot.py` untouched). No behaviour change to existing pipelines; additive fields only.
- **Teil 0 findings (real data, 21 existing proposals across 5 snapshots):**
  - **action distribution: 21/21 `update_field`.** Zero `add_to_array`, `remove_from_array`, `manual_intervention_required`. → **KIND_ADD_OBJECT has NO empirical case** (the "100020 missing article" example does not exist in the data); that branch cannot be verified against real data.
  - **KIND derivation is possible but needs the entity→identity-field map**, not `action`/`search_mode` alone. `update_field` + target field == entity identity field + `current_value==""` → FILL_IDENTITY; otherwise MODIFY_EXISTING. Subtlety: `demands[20].demandId` (duplicate, current_value non-empty) targets the identity field but is MODIFY_EXISTING, not FILL_IDENTITY — so emptiness of current_value (not search_mode) is the discriminator, combined with knowing which field is the identity.
  - **CRITICAL: the proposed `target_entity_id` source (error message / `search_value`) is unreliable — wrong in 2 of 4 real MODIFY cases (50%).** Measured `search_value` vs the identity of the object actually at the target index:
    | target_path | search_value | target object's real id | match |
    |---|---|---|---|
    | articles[1].workPlanId | "SP10 DP01" | articleId=**240019** | ❌ |
    | equipment[339].predecessors[0] | "ADC01" | equipmentKey=**ZTO01** | ❌ |
    | articles[0].relDensityMin | "100265" | articleId=100265 | ✅ |
    | articles[312].workItemConfigs | "124211" | articleId=124211 | ✅ |
    For **reference-type errors** (missing workplan ref, dangling predecessor) the message/`search_value` names the *referenced/missing* entity, NOT the object being corrected — so using it as the guard's soll-identity would compare against the wrong entity.
  - **Reliable alternative found:** reading the identity field of the object currently at `target_path[index]` from `snapshot-data.json` at generation time gives the correct soll-value in **4/4** cases. This requires an additive load of `snapshot-data.json` in `generate_correction_llm.py` (it currently does not load it). This is exactly the guard's intended semantic: "the identity that sat at this position when the proposal was generated".
- **User decision:** `target_entity_id` is read from `snapshot-data.json` at the target position (not from message/search_value). Rationale above.
- **Teil 1 built (additive):** `ENTITY_IDENTITY_FIELD` map (articles→articleId, demands→demandId, workPlans→workPlanId; special entities absent by design), `_parse_target_entity(target_path)`, and `derive_correction_identity(correction_proposal, snapshot_data)` returning `correction_kind`, `target_entity_type`, `target_entity_id`, `identity_check_supported`. Injected into `correction_proposal` in `main()` after generation; `snapshot-data.json` is loaded defensively (any failure → id stays None, no crash). KIND rule: `add_to_array`→ADD_OBJECT; `update_field` + target field == identity field + empty current_value → FILL_IDENTITY; other `update_field` → MODIFY_EXISTING; `manual_intervention_required`/`remove_from_array`/unparsable → UNKNOWN. `target_entity_id`: MODIFY reads `data[array][index][id_field]`; ADD reads `new_value[id_field]`; FILL/UNKNOWN → None.
- **Verification:**
  - **(a) MODIFY_EXISTING — real regenerated proposal file (ec96832c iteration-5, 1 real LLM run, overwrote same iteration):** `correction_kind=KIND_MODIFY_EXISTING, target_entity_type=articles, target_entity_id=124211, identity_check_supported=True`. End-to-end wiring proven.
  - **(b) FILL_IDENTITY — empty demandId (deterministic function on real data):** `KIND_FILL_IDENTITY, demands, target_entity_id=None, supported=True`.
  - **(c) ADD_OBJECT — constructed (no real add_to_array case exists in ANY snapshot):** `KIND_ADD_OBJECT, articles, target_entity_id=100020` (from new_value), `supported=True`. Branch works but remains empirically unexercised until a real add_to_array proposal occurs.
  - **(extra) reference error proves the decision:** `articles[1].workPlanId` (search_value="SP10 DP01") → `target_entity_id=100079` = the article's own articleId at that index, NOT the search_value. Confirms the data-read source is correct where message/search_value would have been wrong.
  - **(d) special entity:** `equipment[339].predecessors[0]` → `identity_check_supported=False, target_entity_id=None` (equipment's dual id is not guessed).
  - **No breakage:** regenerated proposal still `schema_valid=True`, `confidence_score=0.775` (extra fields ignored by the Pydantic model, no `extra="forbid"`); demo proposal still `pending_review`; `snapshot-data.json` SHA-256 unchanged (`7174a169…`, nothing applied); only `generate_correction_llm.py` changed this step.
- **Open / next:** AP3.5b — the actual identity guard in the apply path (`apply_prep`/review): before applying, for `identity_check_supported` proposals with a non-null `target_entity_id`, re-read `data[target_entity_type][index][id_field]` and block (HTTP 409) on mismatch. FILL_IDENTITY and unsupported/UNKNOWN proposals skip the guard (no soll-value). KIND_ADD_OBJECT needs its own handling (object not yet at an index).

---

### 2026-07-11 — AP3.5b Identity guard in the apply path
- **Status:** done
- **Changed files:** `demo/routes/apply_prep.py` (new `check_identity_guard`), `demo/routes/review.py` (wired as Guard 4 in `_apply_after_review`). No runtime tool touched; nothing applied to snapshot data during tests.
- **What was done:** `check_identity_guard(proposal_id)` runs after the AP3.3a iteration guard and before `prepare_proposal_for_apply` / the pipeline call. It reads the AP3.5a fields from the proposal and the current `snapshot-data.json`, and returns `(ok, message, info)`:
  - **KIND_MODIFY_EXISTING, supported, target_entity_id≠null:** reads `data[target_entity_type][index][id_field]` (index from `target_path`, `id_field` from `generate_correction_llm.ENTITY_IDENTITY_FIELD`, lazily imported) and compares to `target_entity_id`. Mismatch → **block (409)**; index gone (array shorter) → **block (409)**; match → pass.
  - **KIND_FILL_IDENTITY:** no soll-identity to compare (skips the identity check), but enforces the optional "field still empty" check — if the target field now holds a value, the situation changed since approval → **block**. Field still empty → pass.
  - **identity_check_supported=False (equipment/worker*/packaging) or KIND_UNKNOWN:** skipped with a log line, pass.
  - **KIND_ADD_OBJECT:** position check N/A (object not yet at an index) → pass, flagged `add_object_guard_verified=False`.
  - **Legacy proposals without the AP3.5a fields:** skipped with a log line, pass (never block a legitimate pre-AP3.5a proposal).
  On block, `_apply_after_review` returns HTTP 409 with the guard message and `guard` code; skips are logged at INFO and pass through.
- **Verification (guard tested in isolation; iteration-5 NOT applied — reserved for the UI decision; all snapshot-data mutations were byte-restored, final SHA == start):**
  - **(a) POSITIVE — iteration-5 (124211, MODIFY_EXISTING):** `ok=True, guard=passed, verified_id=124211` (articles[312] still holds 124211).
  - **(b) NEGATIVE — identity mismatch:** set `articles[312].articleId` → `999999` in a working copy → **blocked**, `guard=blocked_identity_mismatch`, message *"Identity mismatch: position articles[312] now holds '999999', proposal was generated for '124211'"*. snapshot-data byte-restored.
  - **(b2) NEGATIVE — position gone:** truncated `articles` to length 100 → **blocked**, `guard=blocked_position_gone`, *"position articles[312] no longer exists (array length 100)…"*.
  - **(c) SKIP/behaviour:** unsupported equipment → `skipped_unsupported` (pass); FILL_IDENTITY with the target field still empty → `passed_fill_still_empty` (pass); FILL_IDENTITY where the field is now non-empty → **blocked** `blocked_field_not_empty` (the optional check).
  - **(d) LEGACY — proposal without AP3.5a fields:** `skipped_legacy` (pass, not blocked).
  - No breakage: demo proposal `ec96832c-…__iteration-5` still `pending_review`; iterations 1–5 intact (throwaway iterations 90/91/92 removed); `snapshot-data.json` SHA-256 == start (`7174a169…`), nothing applied; only `apply_prep.py` + `review.py` changed this step.
- **Guard chain now:** (1) applicable-state/decision check → (2) AP3.3a iteration-is-latest → (3) AP3.5b identity → then prepare + apply. All are preconditions; any failure returns 409 and applies nothing.
- **Open / next:** AP3.5b enforces identity only for the clean-entity MODIFY case (the demo path). Special entities (equipment dual id, worker* nested, packaging) and KIND_ADD_OBJECT remain guard-skipped by design — a later AP could extend coverage (nested/dual-id lookups, add_object identity from new_value) once real cases exist. The TOCTOU note from AP3.3a still applies (filesystem read vs. subprocess apply).

---

## Open Items / Backlog (Stand: 2026-07-11 - 09:16)

### Erledigt seit letzter Aktualisierung
- **[erledigt]** AP3.6 — Fehler-Klassifizierung: Ursache war die Zähl-Heuristik in `identify_snapshot.py` (NICHT `identify_error_llm`; value-Modus + >1 Treffer → fälschlich DUPLICATE_ID). Behoben: tag-basierter `error_type` aus dem `[validate_*]`-Tag. Siehe Log **AP3.6a** (Diagnose), **AP3.6b-1** (`tag_error_type` additiv erzeugt), **AP3.6b-2** (als maßgeblicher `error_type` verankert, `legacy_error_type` daneben behalten).
- **[erledigt]** AP3.5 — Identitäts-Guard: Metadaten verankert (**AP3.5a**: `correction_kind`, `target_entity_type`, `target_entity_id`, `identity_check_supported`; Soll-Identität aus `snapshot-data` gelesen) und Guard im Anwenden-Pfad scharf (**AP3.5b**: Block bei Identitäts-Abweichung/verschwundener Position, HTTP 409, nichts angewendet). **AP3.5c-Inhalte (Altdaten-Behandlung, Sonderentitäten-Skip) sind in AP3.5b miterledigt** — Nachweise (c) Sonderentität übersprungen und (d) Altdaten ohne AP3.5a-Felder übersprungen.
- **[erledigt]** AP3.3c — echter LLM-Vorschlag erzeugt (Log **AP3.3c**, in **AP3.6b-2** durch korrekt etikettierten `iteration-5` abgelöst). Nur die Fallentscheidung bleibt offen (siehe unten).
- **[geschlossen/hinfällig]** Modellvergleich (GPT-4o-mini vs. stärkeres Modell): entfällt in dieser Form — verifiziert, dass bereits **gpt-4o** läuft (`.env AZURE_OPENAI_DEPLOYMENT=gpt-4o`, `response.model=gpt-4o-2024-11-20`), nicht 4o-mini. Ein A/B gegen 4o-mini war die falsche Prämisse.

### Offen
- **[offen → AP4]** Fallentscheidung Proposal **ec96832c-…__iteration-5** (workItemConfigs Artikel 124211): reject oder modify — bewusst auf **AP4** (UI-Fallentscheidung) terminiert, benötigt fachlichen Vergleich mit Referenzartikeln. (Ersetzt den früheren `iteration-4`-Verweis; `iteration-4` wurde in AP3.6b-2 durch den frisch erzeugten, korrekt etikettierten `iteration-5` abgelöst.)
- **[offen]** AP3.6c — tote Zähl-Heuristik in `identify_snapshot.py` entfernen (oder direkt den Tag emittieren); optional `legacy_error_type` droppen, sobald der tag-basierte Wert etabliert ist.
- **[offen]** Volle Identitäts-Guard-Abdeckung für Sonderentitäten (`equipment` duale ID, `worker*` verschachtelt unter `worker.workerId`, `packaging`) und `KIND_ADD_OBJECT` — erst wenn reale Fälle existieren; aktuell bewusst guard-skipped.
- **[offen]** Baseline-Messung (Schuld seit M0): Auto-Fix-Rate des Alt-Verhaltens über mehrere Snapshots, mit HUMAN_IN_THE_LOOP=false, ZWINGEND nach dem Validierungs-Fix (AP3.3d). Grundlage für den ≥80 %-Nachweis (AK2).
- **[offen]** Phase-3-Kennzahlen fragwürdig: Die 85-%-Auto-Fix-Rate aus der Phase-3-Doku beruht evtl. auf dem Validierungs-Bug (falsches „0 Fehler"). Nicht ungeprüft zitieren.
- **[offen, kosmetisch]** action-Semantik: Vorschlag nutzt `action: "update_field"` für eine ganze Array-Befüllung (leer → 13 Objekte); semantisch eher add_to_array/Array-Replace. Prüfen, ob relevant.
- **[offen]** AP6-Notiz: `revalidation_result`-Einträge aus Läufen VOR AP3.3d beim Dashboard ausschließen/markieren (falsche `errors_after=0`).
- **[später]** AP4 UI, AP5 MCP, AP6 Dashboard, AP7 Memory — nach Abschluss des Robustheits-Audits.