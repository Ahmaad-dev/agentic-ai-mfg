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

### 2026-07-11 — AP4.1 Review Board UI (list) + AP3.5 field exposure
- **Status:** done
- **Changed files:** new `demo/ui/review.html`, `demo/ui/scripts/review.js`; edited `demo/ui/css/styles.css` (additive), `demo/ui/staticwebapp.config.json` (additive routing). Backend exposure (user-approved additive extension): `demo/db/models.py`, `demo/db/repository.py`, new Alembic migration `alembic/versions/ebda716a41f7_ap4_1_add_ap3_5_guard_fields_to_.py`. Runtime tools untouched.
- **Backend gap found + fixed (flagged before building):** `GET /api/review/proposals` did not expose the AP3.5 fields — `correction_kind`/`target_entity_type`/`target_entity_id`/`identity_check_supported` lived only in the proposal JSON, never mapped to the DB (AP3.5a touched only `generate_correction_llm.py`). Per user decision, extended additively: 4 nullable columns on `proposals` (+ Alembic migration, `alembic upgrade head` applied to local SQLite), `save_proposal()` now maps them (target_entity_id stored as str), and both `list_open_proposals_as_dicts()` / `get_proposal_as_dict()` return them. Re-populated the demo proposal `…__iteration-5` from its central record so the columns are filled (no LLM run needed). Stays DB-as-single-source (AP3.1) — the endpoint still never reads JSON files.
- **UI:** `review.html` reuses the exact index.html shell (same fonts/favicon/`css/styles.css`), a sticky header "Review Board" with a "Zurück zum Chat" link to index.html, and a main list area. `review.js` reuses `config.js` (`API_CONFIG.baseURL`) and mirrors chat.js's fetch/error shape (AbortController timeout; explicit 5xx / non-ok / non-JSON / network branches). It `GET`s `/api/review/proposals` on load and renders each proposal as a card: shortened snapshot id (full id in tooltip), error_type, confidence as a coloured bar + %, status badge, created_at, plus the AP3.5 chips (`correction_kind`, `target_entity_type: target_entity_id`) shown only when present. Empty state → "Keine offenen Vorschläge"; error state → clear message. CSS is additive (new `.review-*`/`.rb-*` classes, `body.review-page` overrides the chat's overflow-hidden/centered layout; existing chat styles untouched). `staticwebapp.config.json`: added an explicit `/review.html` route + `navigationFallback.exclude` for `/review.html`, `/css/*`, `/scripts/*` so SWA serves it in production instead of rewriting to index.html.
- **Verification (server `python web_server.py`, port 8000, then stopped):**
  - `GET /api/review/proposals` → HTTP 200, one proposal with `error_type=WORK_ITEM_CONFIGS_COMPLETENESS, confidence_score=0.775, status=pending_review, correction_kind=KIND_MODIFY_EXISTING, target_entity_type=articles, target_entity_id=124211, identity_check_supported=true`.
  - `/review.html` → HTTP 200 (title "Review Board", nav link, config.js+review.js includes); `/css/styles.css` and `/scripts/review.js` → 200.
  - Rendered DOM (review.js render helpers run against the live API via node): card shows `WORK_ITEM_CONFIGS_COMPLETENESS`, status badge `pending_review`, snapshot `ec96832c…` (full id in title), path `articles[312].workItemConfigs`, confidence bar at **78%** (0.775) in the "high" colour, created `10.07.2026, 21:55`, and the two AP3.5 chips **`KIND_MODIFY_EXISTING`** and **`articles: 124211`**.
  - Empty state renders "Keine offenen Vorschläge"; error state renders "Keine Verbindung zum Backend. Läuft der Server (web_server.py)?" — both confirmed via the actual render functions.
- **Addendum (2026-07-11):** snapshot id now shown in FULL (untruncated, `user-select: all` so one click selects it) with a small copy button (`content_copy` → `navigator.clipboard.writeText`, briefly flips to a check on success; the id stays selectable if the clipboard API is blocked). The snapshot field spans the full card width so the long id wraps without breaking the layout. Removed the now-dead `shortSnapshotId()` helper. Changed files: `demo/ui/scripts/review.js` + minimal `demo/ui/css/styles.css` (`.rb-field-wide`/`.rb-snapshot`/`.rb-selectable`/`.rb-copy`). Verified via rendered DOM against the live API: field shows `ec96832c-1573-4ad4-995a-77d541b258f7` in full, copy button carries the full id, no ellipsis.
- **Open / next:** AP4.2 — proposal detail view (before/after diff, reasoning, evidence, confidence) and the decision buttons (Approve / Modify / Reject + comment) wired to the AP3.2/AP3.3 endpoints. The demo proposal `…__iteration-5` remains `pending_review` for that step.

---

### 2026-07-11 — AP4.2 Review detail view (before/after diff, read-only)
- **Status:** done
- **Changed files:** `demo/ui/review.html`, `demo/ui/scripts/review.js`, `demo/ui/css/styles.css` (all additive). No backend, no decision buttons, no runtime tools. (The `staticwebapp.config.json` M in the tree is from AP4.1.)
- **Design choice:** in-page view swap (list `#listView` ↔ detail `#detailView`, toggled via `hidden`) rather than a modal — the workItemConfig diff is a 13-row × 4-column table that wants full width and normal page scroll; a modal would be cramped and need focus-trap handling. "Zurück zur Liste" button restores the list.
- **What was done:** clicking a card (or Enter/Space on a focused card) fetches `GET /api/review/proposals/<id>` and renders a read-only detail. The diff dispatches on the type of `suggested_value`: **Fall A** scalar → old struck-through red / new green; **Fall B** array-of-objects → before/after; **fallback** array-of-scalars → red/green lists (no crash on other shapes). For Fall B the "Vorher" side shows `(leer) — 0 Einträge` for an empty `old_value=[]` (not a struck-through empty), and the "Nachher" side is a table with a header count. Columns for workItemConfig objects use a FIXED order `workItemKey, rampUpTime, netTimeFactor, sequence` (not `Object.keys`); missing `sequence` renders as an empty cell (never "undefined"); non-workItem object arrays fall back to the union of keys in first-seen order. Detail also shows: context chips (error_type, correction_kind, `target_entity_type: target_entity_id`, status), target_path, the full copyable snapshot id (reused AP4.1 block), confidence bar, the reasoning text block, `evidence` only when non-empty (empty `[]` omitted), and a non-functional AP4.3 placeholder. CSS additive (`.rb-detail-*`, `.rb-diff*`, colour convention old=red/struck, new=green); chat + list styles untouched.
- **Verification (server on 8000, then stopped; render fns run against the live detail API via node):** for `ec96832c-…__iteration-5`:
  - Context: chips `WORK_ITEM_CONFIGS_COMPLETENESS`, `KIND_MODIFY_EXISTING`, **`articles: 124211`**, status `pending_review`; full snapshot id + copy button; confidence **78%**.
  - Before: **"(leer) — 0 Einträge"**; no struck-through empty scalar.
  - After: header **"Nachher — 13 neue Einträge"**; column order exactly `workItemKey | rampUpTime | netTimeFactor | sequence`; **13 rows**. `BA01` → `[BA01, 30, 1, HP]` (only row with a sequence); `WART01` → `[WART01, 1, 0, ""]` (sequence cell empty). **No "undefined" anywhere in the table.**
  - Reasoning block present; evidence block omitted (`evidence=[]`); AP4.3 placeholder shown with **no active Approve/Modify/Reject buttons**.
  - "Zurück zur Liste" wired (toggles `hidden`); only the three review UI files changed.
- **Open / next:** AP4.3 — wire the decision buttons (Approve / Modify / Reject + comment) in the placeholder to the AP3.2 endpoints, and reflect the applied result (AP3.3) in the UI. Demo proposal `…__iteration-5` stays `pending_review`.

---

### 2026-07-11 — AP4.3.0 Contract-Check der Decision-Endpunkte (read-only)
- **Status:** done (Analyse only — kein Code geändert; nur dieser Log-Eintrag)
- **Gelesen:** `demo/routes/review.py`, `demo/db/repository.py` (`decide_proposal`, `get_decision_state`, `get_proposal_as_dict`, `list_open_proposals_as_dicts`), `demo/routes/apply_prep.py` (Guard-Codes). Der Vertrag unten ist aus dem Code abgeleitet, nicht aus der Erinnerung.

#### Grundstruktur aller drei Endpunkte
Alle drei laufen durch `_decide()`. Ablauf: `repo.decide_proposal()` schreibt Review-Zeile + neuen Status in EINER Transaktion → bei `approve`/`modify` folgt direkt `_apply_after_review()` (synchron, echtes Anwenden + zwei Server-Validierungsjobs). Der Response-Body ist die **Vereinigung** aus Decide-Feldern und Apply-Feldern (`body.update(apply_result)`), d. h. bei `approve`/`modify` überschreibt das Apply-Ergebnis u. a. `status`.

**Decide-Basisfelder** (immer in jedem 200er-Body): `proposal_id`, `status`, `decision`, `final_value`, `suggested_value`, `comment`, `reviewer_ref` (immer `"demo_reviewer"`), `review_id`.

#### 1) `POST /api/review/proposals/<id>/approve`
- **Request-Body:** `{"comment": <string, OPTIONAL>}`. Body darf ganz fehlen (`get_json(silent=True) or {}`). Kein `final_value` — es wird `proposals.suggested_value` als `reviews.final_value` gespeichert.
- **200 (Erfolg = entschieden UND angewendet):** Decide-Basisfelder mit `decision="approve"`, plus aus dem Apply: `applied=true`, **`status="applied"`** (überschreibt das `"approved"` aus dem Decide-Schritt!), `value_source="ai_suggested"`, `value_applied`, `revalidation_result`.
- **`revalidation_result`** (identisch für approve/modify): `{pipeline: "apply_and_upload", pipeline_success: bool, value_source, value_applied, errors_before: int|null, errors_after: int|null, validation: {is_valid, errors, warnings, …}|null, validation_trigger: {ok, job_id, status, waited_s}|null, failed_at, error}`. → **Ja: `errors_before` → `errors_after` und der neue Status kommen in der Antwort zurück.**

#### 2) `POST /api/review/proposals/<id>/reject`
- **Request-Body:** `{"comment": <string, PFLICHT, nicht leer/whitespace>}`. Fehlt er → **400** `{"error": "A non-empty 'comment' is required to reject a proposal", "proposal_id"}`.
- **200:** Decide-Basisfelder mit `decision="reject"`, `status="rejected"`, `final_value=null`, plus `applied=false`. **Kein** `revalidation_result` — es wird nichts angewendet, kein Validierungsjob läuft.

#### 3) `POST /api/review/proposals/<id>/modify`
- **Request-Body:** `{"final_value": <PFLICHT>, "comment": <OPTIONAL>}`. Feldname ist **`final_value`** (nicht `new_value`/`value`). Fehlt es oder ist es `null` → **400** `{"error": "'final_value' is required to modify a proposal", "proposal_id"}`.
- **Typ von `final_value`:** beliebiges JSON — Skalar ODER Array/Objekt. Für den Demo-Vorschlag `…__iteration-5` wäre es die **Liste der 13 workItemConfig-Objekte**, kein String. Die UI braucht dafür einen strukturierten Editor oder ein JSON-Textfeld, kein einzeiliges Input.
- **200:** wie approve, aber `decision="modify"`, `value_source="human_modify"`, `final_value` = Menschenwert, `suggested_value` = unveränderter KI-Wert (Historie), `status="applied"`.

#### Fehler-Shapes
| Code | Wann | Body |
|---|---|---|
| **400** | reject ohne Kommentar; modify ohne `final_value` | `{error, proposal_id}` |
| **404** | unbekannte `proposal_id` | `{error: "Proposal not found", proposal_id}` |
| **409-A** | Vorschlag war schon entschieden (nicht mehr `pending_review`) | `{error: "Proposal has already been decided", proposal_id, status, hint}` — **Entscheidung wurde NICHT geschrieben**, Apply nie erreicht |
| **409-B** | Apply-Guard blockiert (nur approve/modify) | Decide-Basisfelder **+** `{error: "Proposal cannot be applied" \| "Proposal is not in an applicable state", reason, guard, status}` — **Entscheidung IST geschrieben** (Status `approved`/`modified`), aber **nichts angewendet** |
| **502** | Apply-Pipeline fehlgeschlagen | Decide-Basisfelder **+** `{error: "Apply pipeline failed", applied: false, status: "approved"\|"modified", failed_at, detail, revalidation_result}` — Entscheidung steht, Anwendung fehlgeschlagen |

- **`guard`-Codes (nur 409-B, aus `apply_prep.check_identity_guard`):** `blocked_identity_mismatch`, `blocked_position_gone`, `blocked_field_not_empty`, `error_bad_proposal_id`, `error_no_proposal_file`, `error_no_snapshot_data`. (Die `skipped_*`/`passed_*`-Codes blockieren nicht und tauchen im HTTP-Response nicht auf.) Der Iterations-Guard (AP3.3a) liefert 409-B **ohne** `guard`-Key, nur mit `reason`.
- **Kritisch für die UI:** 409-A und 409-B sehen beide wie „409" aus, bedeuten aber Gegensätzliches. Unterscheidbar am `error`-Text bzw. daran, dass 409-B die Decide-Basisfelder (`review_id`, `decision`) mitführt. Die UI muss bei 409-B sagen: *„Entscheidung gespeichert, aber Anwenden blockiert"* — nicht „fehlgeschlagen".

#### Benannte Lücken (offen, NICHT in AP4.3.0 behoben)
1. **Kein Retry-Pfad für entschieden-aber-nicht-angewendet.** `_apply_after_review` dokumentiert „the human can trigger again" (bei 502 bleibt der Status `approved`/`modified`) — aber es existiert **keine Route dafür**: ein erneutes `POST /approve` läuft in `decide_proposal` → `already_decided` → **409-A**, `_apply_after_review` wird nie wieder erreicht. Nach einem 502 oder 409-B ist der Vorschlag aus der UI heraus **nicht mehr anwendbar**. Ein separater `POST .../apply`-Endpunkt (oder ein Force-Flag) wäre nötig — Scope-Entscheidung für AP4.3.2+.
2. **Entschiedene Vorschläge verschwinden aus der Liste.** `GET /api/review/proposals` filtert hart auf `status == "pending_review"`. Nach jeder Entscheidung fällt der Vorschlag aus der Liste — die UI kann keine Historie zeigen und einen 502/409-B-Fall nicht wiederfinden.
3. **Detail-Endpunkt liefert kein Review-Ergebnis.** `get_proposal_as_dict()` gibt keine `reviews`-Daten zurück (kein `decision`, `comment`, `final_value`, `revalidation_result`). Nach einem Reload zeigt die Detailansicht nur den Proposal-Status, nicht *was* der Mensch entschieden hat oder was das Anwenden bewirkt hat.
4. **`final_value=""` (leerer String) passiert die Validierung** — geprüft wird nur `not in body or is None`. Ein leerer Modify-Wert wäre erlaubt; die UI sollte das clientseitig abfangen.
5. **Antwortzeit:** approve/modify sind synchron und triggern zwei Server-Validierungsjobs (~3–4 s je) plus die Pipeline; Worst Case laut Docstring 3 Tools × 3 Versuche × 90 s. Die UI braucht einen Ladezustand und ein großzügiges Fetch-Timeout (das AP4.1-Muster nutzt einen AbortController) — der Default-Timeout aus `chat.js` ist dafür evtl. zu kurz.
- **Open / next:** AP4.3.1 — Approve + Reject verdrahten (noch kein Modify), Test an einem Wegwerf-Vorschlag; `…__iteration-5` bleibt `pending_review`.

---

### 2026-07-11 — AP4.3.1 Approve + Reject verdrahtet
- **Status:** done
- **Changed files:** `demo/ui/scripts/review.js`, `demo/ui/css/styles.css` (beide additiv). `review.html` **nicht** geändert (der AP4.2-Platzhalter wurde in JS gerendert, nicht im HTML). Kein Backend, keine Runtime-Tools, kein DB-Schema.
- **Was gebaut wurde:** Der AP4.2-Platzhalter ist durch ein echtes Entscheidungs-Panel ersetzt: Kommentar-Textarea + **Genehmigen & anwenden** + **Ablehnen** + ein **deaktivierter** „Ändern"-Button (AP4.3.2). `submitDecision()` POSTet gegen die AP3.2-Endpunkte, `baseURL` aus `config.js`, Fetch-/Fehler-Shape wie AP4.1/4.2 (AbortController). Eigener `DECISION_TIMEOUT = 180 s` (statt 30 s), weil approve synchron anwendet und zwei Server-Validierungsjobs auslöst (AP4.3.0, Lücke 5).
- **Gegen den AP4.3.0-Vertrag gebaut, nicht gegen Erinnerung:**
  - Der Kommentar geht als `{"comment": …}` mit; leerer/whitespace-Kommentar bei Reject wird **clientseitig** abgefangen (Backend würde 400 liefern).
  - **Die zwei 409er werden unterschieden** (der Kernpunkt aus AP4.3.0): 409-A („already decided", ohne `review_id`/`decision`) → *„bereits entschieden, nichts geändert"*; 409-B (Apply-Guard, **mit** den Decide-Feldern) → *„Entscheidung **gespeichert**, aber Anwenden **blockiert**"* + `guard`-Code + `reason`. Ein 502 meldet analog „Entscheidung gespeichert, Anwenden fehlgeschlagen" inkl. `failed_at`.
  - Erfolg zeigt den neuen Status und — sofern vorhanden — die echte Zeile `errors_before → errors_after` aus `revalidation_result`.
  - Nach jeder aufgezeichneten Entscheidung: Buttons + Textarea gesperrt (kein Doppelklick-Zweitversuch, der nur 409-A ergäbe), und die Liste wird beim Zurückgehen neu geladen (der Vorschlag ist nicht mehr `pending_review` und fällt aus `GET /proposals`).
  - Ein bereits entschiedener Vorschlag bekommt gar keine Buttons mehr, sondern einen Hinweis mit dem Status.
- **Verifikation (echter Flask-Server auf 8000 + echte `review.js`-Funktionen in node gegen die Live-API; jsdom war nicht installierbar — npm im Temp-Verzeichnis vom OS blockiert —, daher ein expliziter DOM-Shim, der `config.js` + `review.js` **unverändert** lädt und die echten Buttons klickt). Getestet an zwei **Wegwerf-Vorschlägen** (`ap431-reject__iteration-1`, `ap431-approve__iteration-1`, Fake-Snapshots), **nicht** an `…__iteration-5`:
  - **(a) Panel-Rendering:** `approveBtn`, `rejectBtn`, `rbComment`, `decisionStatus` vorhanden; Modify-Button gerendert und `disabled`.
  - **(b) Reject ohne Kommentar:** Statuszeile `[error] Für eine Ablehnung ist ein Kommentar erforderlich.`, Buttons bleiben aktiv, **kein Request** abgesetzt.
  - **(c) Reject mit Kommentar → DoD erfüllt:** HTTP 200-Zweig; UI: *„Vorschlag **abgelehnt**. Neuer Status: **rejected**. Es wurde nichts angewendet."*; Buttons + Textarea gesperrt. DB: `status=rejected`, `reviews`-Zeile mit `decision=reject, final_value=null, comment="AP4.3.1 UI-Test: Ablehnung via Button.", revalidation_result=NULL` → **nichts angewendet**.
  - **(d) Approve → Anwenden ausgelöst:** HTTP 409-B-Zweig; UI: *„Entscheidung **gespeichert** (Status: **approved**), aber das Anwenden wurde **blockiert**: No iteration with llm_correction_proposal.json found for snapshot ap431-approve; nothing could be applied — an den Snapshot-Daten wurde nichts geändert."* DB: `status=approved` + `reviews`-Zeile mit dem KI-Wert. **Beweis, dass der Apply-Pfad tatsächlich betreten wurde:** diese Meldung stammt aus `check_iteration_is_latest()`, das **ausschließlich innerhalb von `_apply_after_review`** läuft (hinter Guard 1+2). Der Wegwerf-Snapshot hat keine Proposal-Datei, daher blockt der Iterations-Guard — genau wie vorgesehen.
  - **(e) Bereits entschieden:** Detail erneut geöffnet → kein `approveBtn` mehr, stattdessen *„Dieser Vorschlag ist bereits entschieden (Status: rejected)"*.
  - **(f) Liste:** nach den Entscheidungen enthält `GET /api/review/proposals` nur noch `ec96832c-…__iteration-5` — die entschiedenen Wegwerf-Vorschläge sind herausgefallen.
- **Bewusst NICHT getan (ehrlich benannt):** ein echter `applied=true`-Durchstich über die UI wurde **nicht** gefahren. Dafür bräuchte es einen realen Snapshot mit Proposal-Datei auf der **höchsten** Iteration — d. h. eine neue `iteration-6` auf `ec96832c`. Das würde `iteration-5` aus der „latest"-Position werfen und den AP3.3a-Guard für die noch offene **echte** Entscheidung des Nutzers auslösen (der Demo-Vorschlag wäre nicht mehr anwendbar) und zusätzlich per VPN echte Snapshot-Daten auf dem Server verändern. Der vollständige Apply-Pfad inkl. `errors_before → errors_after` ist bereits in **AP3.3b** und **AP3.3d** auf API-Ebene nachgewiesen; AP4.3.1 verdrahtet ihn nur. Der Erfolgs-Zweig der UI (`applied=true` + Revalidierungs-Zeile) wird beim echten Approve von `…__iteration-5` das erste Mal live sichtbar.
- **Sauberkeit:** beide Wegwerf-Vorschläge inkl. ihrer `reviews`-Zeilen wieder gelöscht. Endzustand DB = die 4 echten Proposals + 4 echten Reviews wie vorher; **`ec96832c-…__iteration-5` unverändert `pending_review`**. `snapshot-data.json` von `ec96832c` SHA-256 = `7174a169…` (identisch mit dem in AP3.5b protokollierten Stand) → nichts angewendet. Nur die zwei genannten UI-Dateien geändert.
- **Open / next:** AP4.3.2 — Modify verdrahten. Achtung (aus AP4.3.0): `final_value` ist **beliebiges JSON**; für `…__iteration-5` wäre es die Liste der 13 workItemConfig-Objekte, ein einzeiliges Textfeld reicht nicht. Danach: die echte Fallentscheidung zu `…__iteration-5`.

---

### 2026-07-11 — AP4.3.2a Contract-Check Modify-Apply-Pfad (read-only)
- **Status:** done (Analyse only — kein Code geändert; nur dieser Log-Eintrag). **Kein Stop nötig: der Menschenwert landet nachweislich in den echten Daten** — für die relevante Action `update_field`. Einschränkungen für andere Actions siehe unten.
- **Gelesen:** `demo/routes/review.py`, `demo/routes/apply_prep.py`, `demo/smart-planning/runtime/apply_correction.py`, `demo/smart-planning/runtime/update_snapshot.py`, `demo/smart-planning/runtime/correction_models.py`.

#### Antwort auf die Leitfrage
**`prepare_proposal_for_apply` schreibt den Menschenwert in genau die Datei, die `apply_correction.py` anschließend liest.** Es wird NICHT die KI-Proposal von der Platte angewendet — sie wird vorher überschrieben (und vorher weggesichert). Die Kette, lückenlos:

1. **`review.modify_proposal`** → `_decide(…, final_value=body["final_value"])` → `repo.decide_proposal()` schreibt `reviews.final_value` = Menschenwert; `proposals.suggested_value` bleibt der KI-Wert (Historie). Status → `modified`.
2. **`_apply_after_review(proposal_id, "modify", final_value)`** reicht denselben `final_value` weiter (aus dem Request, nicht aus der DB nachgelesen — kann nicht divergieren, es ist derselbe Aufruf).
3. **`prepare_proposal_for_apply` (apply_prep.py:276-291)**: sichert das unveränderte Dokument einmalig nach `iteration-N/llm_correction_proposal.ai_original.json` (nie überschrieben), setzt dann **`correction_proposal["new_value"] = final_value`** und `value_source="human_modify"`, und speichert `iteration-N/llm_correction_proposal.json` über den `StorageManager` zurück. Rückgabe: `value_to_apply = final_value`.
4. **`apply_correction.main()`** (Pipeline-Schritt 1 von `apply_and_upload`): `get_latest_iteration_number(snapshot_id)` → dieselbe Iteration N (der AP3.3a-Iterations-Guard hat vorher sichergestellt, dass N die höchste ist) → `load_correction_proposal()` liest **exakt die eben geschriebene Datei** → `validate_proposal_schema()` (Pydantic).
5. **`apply_correction()` (Zeile 339-351)**: `action == "update_field"` → **`new_value = proposal.get("new_value")` aus dem ROHEN dict** (nicht aus dem validierten Modell) → `apply_single_update()` → **`data[array][index][field] = new_value`** → `storage.save_json(f"{snapshot_id}/snapshot-data.json", data)`.
6. **`update_snapshot.py`** (Pipeline-Schritt 2) lädt genau diese `snapshot-data.json` (Zeile 249) und schickt sie per **`PUT /snapshots/{id}`** an den Server.

→ **Beleg erbracht: `value_applied` (= `preparation["value_to_apply"]` = `final_value`) ist genau der Wert, der in `snapshot-data.json` geschrieben und hochgeladen wird.** Für `…__iteration-5` (`action=update_field`, `target_path=articles[312].workItemConfigs`) heißt das: das gepostete 13er-Array landet 1:1 unter `articles[312].workItemConfigs`.
- **Schema hält:** `CorrectionProposal.new_value` ist `Optional[Union[str,int,float,bool,None,dict,list]]` (correction_models.py:20) — eine Liste von 13 Objekten ist gültig, `validate_proposal_schema()` bricht also nicht ab. (Umkehrschluss unten in Lücke 2.)

#### Geflaggte Lücken / Fallstricke (NICHT behoben — Analyse)
1. **Modify wirkt NUR bei `action == "update_field"` und `add_to_array`.** `apply_correction` liest den Menschenwert aus `new_value`. Aber: bei **`remove_from_array`** liest es `proposal.get("current_value")` (Zeile 361) — `new_value` wird ignoriert, ein menschlicher Modify-Wert würde also **stillschweigend verpuffen**. Bei **`manual_intervention_required`** wird gar nichts angewendet (Zeile 330-337), die Snapshot-Daten bleiben unverändert — die Antwort meldete trotzdem `applied=true`. Bei **`add_to_array`** muss `new_value` ein **dict** sein, sonst `TypeError` → Pipeline-Fehler → 502. **Für PT4 aktuell folgenlos:** alle 21 realen Proposals haben `action=update_field` (AP3.5a Teil 0). Aber `prepare_proposal_for_apply` prüft die Action **nicht** — sobald ein `remove_from_array`-Vorschlag auftaucht, ist Modify dort eine stille Fehlfunktion. → Backlog.
2. **Das Schema fängt keinen semantischen Unsinn.** `new_value` akzeptiert **jeden** JSON-Typ. Ein Mensch könnte für `articles[312].workItemConfigs` einen String oder eine Zahl eintragen — Schema-Validierung passiert, und `apply_single_update` schreibt den Wert stumpf an die Zielposition. Es gibt **keinen** Typ-Abgleich gegen das Zielfeld. Die einzige clientseitige Sicherung wird die JSON-Validierung in AP4.3.2b sein (fängt Syntaxfehler, nicht falsche Typen).
3. **Auto-Parse von JSON-Strings** (apply_correction.py:157-164): ist `new_value` ein **String**, der mit `[` oder `{` beginnt, wird er per `json.loads` in eine Struktur umgewandelt. Für uns unkritisch (die UI postet echtes JSON, also eine echte Liste) — aber es bedeutet: ein skalarer Textwert, der zufällig mit `[`/`{` beginnt, würde umgedeutet. Wichtig für 4.3.2b: **das geparste Array posten, nicht den Textarea-String** (funktionierte zwar zufällig auch, wäre aber Verlass auf einen Runtime-Workaround).
4. **`current_value` wird beim Modify NICHT mitgezogen.** Nach einem Modify steht in der Datei der neue `new_value`, aber `current_value` bleibt die Sicht der KI. Für `update_field` ungenutzt → harmlos; für `remove_from_array` genau der Grund für Lücke 1.
5. **`additional_updates` bleiben KI-Werte** (bewusst, PT4-Guardrail: eine Konfidenz, eine Freigabe pro Proposal) — und sie **werden mitangewendet** (Zeile 370-384). Ein Modify überschreibt also nur den Hauptwert. Für `…__iteration-5` irrelevant (`additional_updates=[]`), bei künftigen Vorschlägen mit Zusatz-Updates aber eine bewusste Asymmetrie, die die UI benennen sollte.
6. **Keine Rücklese-Verifikation.** `value_applied` in der HTTP-Antwort ist das, was *geschrieben werden sollte*, nicht ein Re-Read aus `snapshot-data.json`. Der Pfad ist deterministisch (Punkt 3→5 oben), aber es gibt keinen Nachweis *nach* dem Schreiben. Für den Nutzer bleibt der echte Beleg die Zeile `errors_before → errors_after`.
- **Audit-Trail beim Modify (positiv):** der KI-Wert überlebt an **drei** Stellen — `proposals.suggested_value` (DB), `reviews.final_value` (Menschenwert daneben) und `llm_correction_proposal.ai_original.json` (Datei, nie überschrieben).
- **Open / next:** AP4.3.2b — Modify-Editor (JSON-Textarea, vorbefüllt mit pretty-printed `suggested_value`, clientseitige `JSON.parse`-Validierung, **das geparste Array** als `final_value` posten). Test am Wegwerf-Vorschlag; `…__iteration-5` bleibt `pending_review`.

---

### 2026-07-11 — AP4.3.2b Modify-Editor (JSON-Textarea)
- **Status:** done
- **Changed files:** `demo/ui/scripts/review.js`, `demo/ui/css/styles.css` (beide additiv). Kein Backend, kein Runtime-Tool, kein DB-Schema; `review.html` unverändert.
- **Was gebaut wurde:** Der „Ändern"-Button ist scharf und klappt einen **JSON-Editor** auf: Textarea, per `.value` (nicht `innerHTML`) mit `JSON.stringify(suggested_value, null, 2)` vorbefüllt — für `…__iteration-5` also die 13 workItemConfig-Objekte, pretty-printed, in place editierbar. Darunter eine **Live-Hinweiszeile**, dazu „Übernehmen & anwenden" / „Abbrechen". Beim Absenden wird der Text `JSON.parse`t und **der geparste Wert** als `final_value` gepostet — nie der Rohstring (bewusst kein Verlass auf den Auto-Parse in `apply_correction.py:157`, siehe AP4.3.2a Fallstrick 3).
- **Clientseitige Validierung (blockiert vor dem Request):** Syntaxfehler (`JSON.parse`-Meldung wird angezeigt), leeres Feld, und **`null` bzw. `""`** — Letzteres ist **AP4.3.0 Lücke 4**: das Backend prüft nur `not in body or is None`, ein leerer String würde sonst wortwörtlich in die Snapshot-Daten geschrieben. **Nicht blockiert, aber sichtbar gemacht:** ein abweichender Top-Level-Typ (z. B. Array → String) erzeugt eine gelbe Warnung „…Typ weicht vom KI-Vorschlag ab… Wird so angewendet", weil das Backend-Schema jeden JSON-Typ akzeptiert und ihn stumpf schreiben würde (AP4.3.2a Lücke 2). Zusätzlich weist der Editor darauf hin, wenn `additional_updates` vorhanden sind — die bleiben KI-Werte (PT4-Guardrail, AP4.3.2a Lücke 5).
- **AP4.3.2c fiel dabei an (keine Extra-Arbeit):** Modify läuft durch **dasselbe** `submitDecision()` wie Approve/Reject — 409-A/409-B/502/Timeout-Behandlung, Button-Sperre und die `errors_before → errors_after`-Zeile sind unverändert wiederverwendet, nur der Erfolgstext unterscheidet („Geänderter Wert übernommen und angewendet"). Kein zweiter Antwortpfad.
- **Verifikation (echter Flask-Server, echte `review.js`-Funktionen in node gegen die Live-API, echte Button-Klicks; der Harness umschließt `fetch`, um den tatsächlichen POST-Body zu inspizieren). Wegwerf-Vorschlag `ap432-modify__iteration-1` mit dem **echten** 13er-Wert aus `…__iteration-5` kopiert (Fake-Snapshot-ID), `…__iteration-5` selbst nur gelesen:**
  - **(a) Editor:** „Ändern"-Button aktiv, Editor initial `hidden`, nach Klick offen; Textarea enthält gültiges JSON mit **13 Objekten**, pretty-printed; BA01 steht dort als `{"netTimeFactor":1,"rampUpTime":30,"sequence":"HP","workItemKey":"BA01"}`; Hint: *„Gültiges JSON — Array mit 13 Einträgen."*
  - **(b) Validierung blockt (kein Request abgesetzt, je geprüft):** kaputtes JSON (Trailing Comma) → *„Kein gültiges JSON: Expected double-quoted property name…"*; leeres Feld → *„Kein Wert eingegeben."*; `""` → *„Leerer Wert (null bzw. \"\") wird nicht angewendet."* In allen drei Fällen wurde **kein** POST gesendet.
  - **(c) Echter Edit + Absenden:** BA01 `rampUpTime 30→45`, `netTimeFactor 1→2`. Der abgefangene Request an `POST /api/review/proposals/ap432-modify__iteration-1/modify` trägt **`final_value` als echtes Array mit 13 Objekten** (nicht als String!), BA01 darin `{"netTimeFactor":2,"rampUpTime":45,"sequence":"HP","workItemKey":"BA01"}`, plus den Kommentar. **DB-Durchstich:** `proposals.status=modified`, `reviews.decision=modify`, **`reviews.final_value` = Liste mit 13 Objekten, BA01 mit 45/2** — der Menschenwert ist in der Persistenz angekommen.
  - **(d) Antwort-Wiederverwendung (409-B):** der Apply-Pfad wurde betreten und vom Iterations-Guard blockiert (Wegwerf-Snapshot hat keine Proposal-Datei) → UI rendert den 4.3.1-Zweig *„Entscheidung **gespeichert** (Status: **modified**), aber das Anwenden wurde **blockiert** … an den Snapshot-Daten wurde nichts geändert"*; alle vier Buttons gesperrt.
- **Weiterhin nicht live gefahren:** ein echter `applied=true`-Modify (gleiche Begründung wie AP4.3.1 — bräuchte eine reale `iteration-6` auf `ec96832c` und würde `iteration-5` aus der „latest"-Position werfen). Dass der Menschenwert von dort bis in `snapshot-data.json` durchschlägt, ist in **AP4.3.2a** aus dem Code belegt und in **AP3.3b (b)** schon einmal real nachgewiesen worden.
- **Sauberkeit:** Wegwerf-Vorschlag + Review-Zeile gelöscht. DB-Endzustand = die 4 echten Proposals + 4 echten Reviews wie zuvor; **`ec96832c-…__iteration-5` unverändert `pending_review`**; `snapshot-data.json` SHA-256 `7174a169…` (unverändert) → nichts angewendet. Nur die zwei genannten UI-Dateien geändert.
- **Open / next:** AP4.3 ist damit funktional komplett (Approve / Reject / Modify verdrahtet, Ergebnis-Rendering geteilt). Offen bleibt die **echte Fallentscheidung** zu `…__iteration-5` — beim Approve/Modify dort wird der Erfolgs-Zweig (`applied=true` + `errors_before → errors_after`) das erste Mal live sichtbar. Neuer Backlog-Punkt aus AP4.3.2a: `prepare_proposal_for_apply` prüft die `action` nicht — bei `remove_from_array` würde ein Modify-Wert still verpuffen.

---

### 2026-07-12 — AP4.7 Layout-Fixes + Code-Kontext der Fehlerstelle im Review Board
- **Status:** done. Drei Befunde des Nutzers nach dem ersten Blick auf die neue Shell.
- **Changed files:** `demo/ui/css/styles.css`, `demo/ui/scripts/chat.js`, `demo/ui/scripts/review.js`, `demo/routes/review.py`. Kein Schema, keine Migration.

#### 1. Chat war nicht zentriert (Regression aus AP4.6)
`.input-area` ist `position: fixed` mit `left: 0; width: 100%` — sie richtete sich also am **Viewport** aus, nicht am Inhaltsbereich. Seit die Sidebar existiert, saß sie deshalb um deren halbe Breite zu weit links (der Willkommenstext daneben war korrekt, weil er in `.app-main` liegt — genau daher der schiefe Eindruck). Neu: CSS-Variable `--sidebar-w` (264 px, im Mobile-Breakpoint 60 px); die Eingabezeile nutzt `left: var(--sidebar-w); width: calc(100% - var(--sidebar-w))` und die Sidebar dieselbe Variable — beides kann nicht mehr auseinanderlaufen.

#### 2. Eingabefeld blieb einzeilig
`autoResize()` existierte seit jeher, wurde aber **ausschließlich aus der Spracherkennung** aufgerufen — beim **Tippen** feuerte nichts, das Feld blieb auf den CSS-Werten `height: 24px` stehen. Neu: `userInput.addEventListener('input', …)`. Dazu `max-height` im CSS von 200 px auf **150 px** korrigiert (identisch zum Deckel in `autoResize`, sonst wächst der Rahmen weiter, während der Text schon scrollt) und `overflow-y: auto`; `.input-wrapper` auf `align-items: flex-end`, damit Mikro-/Senden-Button beim mehrzeiligen Feld unten bleiben.

#### 3. NEU: Fehlerstelle 1:1 aus `snapshot-data.json` (Diff-Hunk-Optik)
Der Reviewer sah bisher nur `target_path` + alten Wert — zu wenig, um eine Korrektur wirklich zu beurteilen. Neuer Endpunkt **`GET /api/review/proposals/<id>/context`** liefert den Original-JSON-Ausschnitt mit **echten Zeilennummern**, 7 Zeilen davor/danach, die betroffene(n) Zeile(n) markiert.
- **Der Kniff für exakte Zeilennummern:** einfaches Mitzählen scheidet aus (`"articleId"` kommt tausendfach vor). Stattdessen wird der Zielwert in einer **Kopie** durch eine eindeutige Marke ersetzt und das **ganze** Dokument gedumpt. Alles **vor** dem Ziel ist in beiden Dumps zeichengleich → die Zeile der Marke **ist** exakt die Zeile des Zielfelds im echten Dump. Mehrzeilige Werte (Array/Objekt) werden über Klammer-Zählung als ganze Spanne markiert, sehr lange Blöcke bei 40 Zeilen gekappt.
- **UI:** neuer Abschnitt „Fehlerstelle im Original", Zeilennummern-Spalte, rote Hinterlegung + linker Balken wie in einem GitHub-Diff. Lädt asynchron nach; schlägt der Abruf fehl, bleibt der Block einfach aus (die Detailansicht funktioniert weiter).
- **Kein Fremd-Framework:** bewusst selbst gebaut statt Highlight.js/Prism einzuziehen — die eigentliche Leistung ist das **JSON-pfad-genaue Auffinden der Stelle** (das kann keine Syntax-Highlighting-Bibliothek); die Darstellung selbst sind ~50 Zeilen CSS. Keine neue Abhängigkeit in der SWA-Deployment-Kette.
- **Verifikation (Live-Server, alle 3 offenen Vorschläge):**
  - `demands[386].articleId` (sdfsdf) → **Zeile 138295 von 165282**, 15 Zeilen Kontext, 1 Zeile rot. Direkt über der Fehlerzeile steht `"demandId": "D122873_001"` — **genau der Beleg, aus dem die KI ihren Wert 122873 ableitet.**
  - `articles[312].workItemConfigs` (leeres Array) → Zeile 32969; im Kontext sichtbar: `"articleId": "124211"`, `"articleName": "Himbeer-Grundstoff"`.
  - `demands[350].articleId` (manual_intervention) → Zeile 137863, 1 Zeile markiert.
  - DOM: Abschnitt sichtbar, 15 Zeilen gerendert, 1 als `err`, Kopfzeile „snapshot-data.json · Zeile 138295 von 165282".
  - Keine Regression: `/`, `/review.html`, `/scripts/shell.js` → HTTP 200.
- **Open / next:** Der Endpunkt deckt `array[i].field`-Pfade ab; verschachtelte Pfade (`equipment[i].predecessors[0]`) liefern 422 und der Block bleibt aus — nachrüsten, wenn reale Fälle auftreten.

---

### 2026-07-12 — AP4.6 Chat-Sessions aus der DB + App-Shell (Sidebar)
- **Status:** done. Auslöser: der Nutzer verlor bei jedem Wechsel ins Review Board seinen Chat-Verlauf, und die UI hatte keine Navigation.
- **Changed files:** `demo/db/repository.py`, `demo/web_server.py`, neu `demo/ui/scripts/shell.js`, `demo/ui/scripts/chat.js`, `demo/ui/index.html`, `demo/ui/review.html`, `demo/ui/css/styles.css`. **Kein DB-Schema, keine Migration** — die Tabellen `sessions`/`messages` gibt es seit AP2.

#### Die Ursache (Contract-Check)
`chat.js:10` lautete `const sessionId = 'session_' + Date.now();` — **bei jedem Seitenaufruf eine neue Session.** Dazu lag die Historie serverseitig nur in einem In-Memory-Dict (`chat_sessions`), das jeder Neustart leerte. **Die Nachrichten selbst waren nie weg:** `web_server.chat()` schreibt seit AP2 jede User- und Assistant-Nachricht in `messages` — sie wurden nur **nie zurückgelesen**. Es fehlten also nur Lese-Endpunkte und die Anbindung.

#### Backend (additiv)
- `repository.list_sessions_as_dicts()` (Titel = erste Nutzernachricht, gekürzt — **kein LLM-Call, keine neue Spalte**; leere Sessions werden übersprungen, weil jeder alte Seitenaufruf eine erzeugt hat), `get_messages_as_dicts()`, `session_exists()`.
- Endpunkte: `GET /api/sessions`, `POST /api/sessions`, `GET /api/sessions/<id>/messages`.
- `_get_db_session_id()` akzeptiert jetzt die **DB-Id** direkt (numerisch + existiert → wird verwendet); die alte Lazy-Create-Logik bleibt als Fallback (`'default'`, alte `session_<timestamp>`-Ids funktionieren weiter).
- **`get_session_history()` lädt die Historie bei Bedarf aus der DB nach** — der In-Memory-Cache ist nicht mehr die Quelle der Wahrheit. Damit hat der Agent auch nach einem Serverneustart wieder Kontext.

#### Frontend — App-Shell
Neue `scripts/shell.js` injiziert eine gemeinsame **Sidebar** auf **beiden** Seiten (bewusst als Skript statt als kopiertes Markup, sonst laufen die Seiten auseinander): Marke, **„Neuer Chat"**, Navigation (**Chat** / **Review Board** mit Badge „offene Vorschläge" / **Dashboard** als „bald"), darunter der **Verlauf** aus der DB. Klick auf eine Session wechselt auf der Chat-Seite **ohne Reload**, vom Review Board aus per Deep-Link.
`chat.js`: `sessionId` ist jetzt die DB-Id, ermittelt aus `?session=<id>` → `localStorage` → sonst neue Session; Verlauf wird beim Laden gerendert; Session-Id bleibt in der URL (Reload zeigt denselben Chat). Nach jeder Antwort wird die Sidebar aufgefrischt (ein neuer Chat bekommt so erst seinen Titel).
`review.html` verliert seinen eigenen Header (Marke + „Zurück zum Chat" stehen jetzt in der Sidebar), behält aber den Seitentitel. CSS: `body` wird zur Shell (row), der bisherige Body-Job (column/zentriert) wandert in `.app-main` — **auf den vorhandenen Design-Tokens, kein Framework** (Nutzer-Entscheidung: bestehendes Design-System + Standard-App-Shell statt Tailwind/Template, weil ein Framework-Wechsel das getestete Review-Board-CSS komplett neu schreiben müsste).

#### Verifikation
- **Endpunkte (Live-Server):** `GET /api/sessions` → **16 bestehende Sessions mit Inhalt** (die Nachrichten lagen die ganze Zeit in der DB, u. a. die „was war die Lösung?"-Unterhaltung). `POST /api/sessions` → HTTP 201 mit neuer Id. `GET /api/sessions/<id>/messages` → vollständiger Verlauf.
- **Kerntest — Verlauf überlebt einen echten Serverneustart:** In Session 52 „mein Lieblingssnapshot ist 1ef11903" gespeichert → **Server hart neu gestartet** (In-Memory-Cache leer) → Frage „Welchen Lieblingssnapshot hatte ich genannt?" → Antwort: *„Dein Lieblingssnapshot ist die ID `1ef11903`."* Die Historie kam nachweislich aus der DB.
- **UI (echte `shell.js`+`chat.js` gegen die Live-API):** Sidebar injiziert; **17 Sessions** mit Titeln in der Liste; Badge zeigt **3** offene Vorschläge; Startzustand legt eine neue Session an und merkt sie im `localStorage`; **Wechsel in eine alte Session lädt 6 Nachrichten zurück** und setzt `chat-started`.
- **Keine Regression:** `/`, `/review.html`, `/scripts/shell.js`, `/css/styles.css` → alle HTTP 200; Review-Board-Deep-Link öffnet weiterhin die Detailansicht mit Entscheidungs-Panel.
- **Open / next:** Umbenennen/Löschen von Sessions und LLM-Titel wurden bewusst **nicht** gebaut (Nutzer-Entscheidung: nur Liste + Neu + Wechseln). Der Dashboard-Eintrag in der Sidebar ist bewusst deaktiviert („bald") und wartet auf AP6.

---

### 2026-07-11 — Baseline-Messung (AK2): Plan + Entscheidungen festgehalten, **Durchführung vertagt**
- **Status:** **nicht durchgeführt** (Nutzer-Entscheidung: keine Test-Snapshots auf dem Server erzeugen). Kein Code geschrieben, nichts angelegt, nichts gemessen. Dieser Eintrag hält den fertigen Plan fest, damit die Messung später nur noch ausgeführt werden muss.
- **Warum sie noch aussteht:** Sie ist der **letzte AK2-Blocker**. Ohne sie gibt es keine belastbare Grundlage für den ≥ 80 %-Nachweis — und die vorhandene Phase-3-Zahl (85 %) ist wegen des Validierungs-Bugs (AP3.3d) nicht zitierfähig.

#### Die zentrale Erkenntnis für das Messdesign
**„Validator grün" ≠ „korrekt gefixt".** Zweimal live belegt: beim BA01-Fall (2 → 0 Fehler, Werte trotzdem fachlich fragwürdig) und beim Duplikat-Fall (die KI schlug `D210446_003` vor — die Validierung wäre grün gewesen, der Wert war trotzdem falsch; der Mensch setzte `D210451_001`). Wer die Baseline nur an der Server-Validierung misst, misst **Key-Vollständigkeit, nicht Wert-Korrektheit** — und schreibt denselben Fehler fest wie die alten 85 %.
**Lösung:** die Fehler **selbst injizieren**. Dann ist der ursprüngliche Wert die **Ground Truth**, und Korrektheit wird objektiv messbar.

#### Entscheidungen des Nutzers (bereits getroffen)
- **Kriterium: hybrid je Fehlerklasse.**
  - Fehler mit **eindeutiger** Lösung (leeres Feld, kaputte Artikel-Referenz, ungültige Dichte, fehlende `workItemConfigs`): *korrekt = angewendeter Wert **entspricht exakt dem Originalwert***.
  - Fehler mit **mehreren gültigen** Lösungen (doppelte `demandId` — jede eindeutige ID wäre legitim): *korrekt = Validator grün **und** kein neues Duplikat erzeugt*.
- **Umfang: 10 Fälle** (5 Fehlerarten × 2), schlanke Variante. Bewusst akzeptiert: jede Fehlentscheidung verschiebt die Quote um 10 Prozentpunkte.

#### Ablauf je Fall (fertig entworfen, noch nicht gefahren)
1. `create_snapshot` → frischer, **sauberer** Server-Snapshot (der Crawler zieht echte Stammdaten; Daten lassen sich erst danach ändern).
2. `download_snapshot` → die sauberen Daten sind die **Ground Truth**.
3. **Genau einen** Fehler injizieren, `update_snapshot` (PUT) → Server-Snapshot ist kaputt.
4. Validierungsjob (AP3.3d) → echte `errors_before`.
5. `identify_error_llm` → `generate_correction_llm` → Vorschlag + `confidence_score` + `value_grounded` festhalten (**noch nichts angewendet**).
6. `apply_correction` → `update_snapshot` → Validierungsjob → das **alte Verhalten** (Auto-Apply, entspricht `HUMAN_IN_THE_LOOP=false`).
7. Bewertung nach dem Hybrid-Kriterium.

**Fehlerkatalog (5 × 2):** `EMPTY_FIELD` (demandId leeren) · `DEMAND_ARTICLE_IDS` (articleId kaputt) · `DENSITY_VALUES` (relDensityMin negativ) · `UNIQUE_IDS` (demandId duplizieren, **nicht** ground-truth-bewertet) · `WORK_ITEM_CONFIGS_COMPLETENESS` (workItemConfigs leeren).

#### Wichtige Einsicht zum Ergebnis (vorab, damit sie nicht überrascht)
Baseline-Auto-Fix-Rate und die AK2-Quote „Vorschläge ohne Änderung angenommen" sind **dieselbe Zahl** — das alte System wendete genau den Vorschlag an, den PT4 dem Menschen vorlegt. **PT4 verbessert nicht die Qualität des Vorschlags, sondern das Ergebnis:** falsche Werte landen nicht mehr still in den Daten, und der Mensch bekommt mit `confidence_score`/`value_grounded` ein Signal, wo er hinschauen muss. Derselbe Messlauf liefert damit dreierlei: die Auto-Fix-Rate, die AK2-Quote und die **Kalibrierungskurve** (Konfidenz vs. tatsächliche Korrektheit) — Letztere ist erst seit AP4.5 überhaupt aussagekräftig.

#### Kosten / Nebenwirkung (der Grund für die Vertagung)
Es gibt **kein Lösch-Tool** (nur create/rename) — jeder Messfall hinterlässt einen **dauerhaften** Snapshot auf dem Testserver (11 Stück inkl. Referenz-Snapshot). Dazu ~20–30 LLM-Läufe. Der Nutzer hat entschieden, das vorerst **nicht** zu tun.
- **Open / next:** Messung ausführen, sobald Test-Snapshots auf dem Server in Ordnung sind (oder ein Lösch-/Aufräumweg existiert). Der Plan oben ist vollständig; es fehlt nur die Ausführung.

---

### 2026-07-11 — AP4.5 Konfidenz mit Trennschärfe (`value_grounded` ersetzt `schema_valid`)
- **Status:** done. **AK2-Blocker geschlossen.** Nutzer-Entscheidung: den toten `schema_valid`-Term durch ein deterministisches Groundedness-Signal ersetzen.
- **Changed files:** `demo/smart-planning/runtime/generate_correction_llm.py` (additiv), `demo/db/models.py`, `demo/db/repository.py`, neue Alembic-Migration `1aeb3778e9cb`, `demo/ui/scripts/review.js`, `demo/ui/css/styles.css`, `docs/PT4_PLAN.md` (Formel).
- **Neue Formel:** `0.5·llm_confidence + 0.3·value_grounded + 0.2·memory_support`.
  `value_grounded` (neu, `compute_value_grounded`) beantwortet **deterministisch**: *ist der vorgeschlagene Wert aus den Daten belegbar oder erfunden?* Drei Fälle:
  - **Identitätsfeld** (`demands[i].demandId`, `articles[i].articleId`): der Wert **muss** neu/eindeutig sein, ist also grundsätzlich **nicht** belegbar → `0`. Existiert er bereits woanders → **KOLLISION** (der Vorschlag würde ein *neues* Duplikat erzeugen) → `0` mit explizitem Warnhinweis.
  - **Referenzfeld** (`demands[i].articleId` → `articles[]`): `1`, wenn das referenzierte Objekt existiert; sonst `0`.
  - **Sonstige Felder**: `1`, wenn derselbe Wert/dieselbe Struktur bereits auf demselben Feld eines vergleichbaren Datensatzes liegt (z. B. ein `workItemConfigs`-Array aus einem Nachbarartikel); sonst `0`.
  Konservativ: alles, was nicht verifizierbar ist, zählt als **nicht** belegt — ein unbelegbarer Wert kann den Score nie aufblähen.
- **Warum überhaupt:** Die Prompt-Rubrik aus AP4.4 allein reichte nicht. Gemessen: das LLM stufte eine **selbst erfundene** (hochgezählte) ID als „Band A / 0.9" ein — ausgerechnet im Fall, in dem es falsch lag. Eine Selbsteinschätzung kann „ich habe den Wert abgelesen" nicht von „ich habe ihn erfunden" unterscheiden; diese Prüfung kann es.
- **Eigener Logikfehler, im Test gefunden und behoben (wichtig):** Die erste Fassung belohnte „Wert existiert bereits im selben Feld" pauschal mit `grounded=1` — bei einem **Eindeutigkeits**-Feld ist das genau falsch herum. Der Testlauf zeigte es sofort: die KI schlug `D210451_002` vor, ein Wert, der **schon auf `demands[768]` lag**; mein Signal gab dafür `1.0`. Das hätte einen Vorschlag belohnt, der ein *neues* Duplikat erzeugt. Sonderbehandlung für Identitätsfelder ergänzt (siehe oben).
- **Messung (4 echte LLM-Läufe auf Wegwerf-Kopien, Demo-Vorschläge unberührt):**

  | Fall | new_value | llm | grounded | **score** | Begründung |
  |---|---|---|---|---|---|
  | Duplicate-ID (**KI lag falsch**) | `D210451_002` | 0.90 | **0** | **0.45** | KOLLISION: `demands[768].demandId` trägt bereits diesen Wert |
  | `sdfsdf` → `122873` | `122873` | 0.95 | **1** | **0.775** | Referenz belegt: `articles.articleId=122873` existiert |
  | workItemConfigs 124211 | 13 Objekte | 0.88 | **1** | **0.74** | identische Struktur auf `articles[23]` |
  | erfundene `articleId` | `null` | 0.0 | 0 | **0.0** | `manual_intervention_required` |

  **Vorher:** 0.775 in 7 von 8 Proposals. **Jetzt:** 0.0 / 0.45 / 0.74 / 0.775 — und der Fall, in dem die KI falsch lag, ist der **niedrigste** von null verschiedene. Genau das war die Anforderung aus AK2.
- **Sichtbar gemacht (sonst ist die Zahl nicht überprüfbar):** 3 additive Spalten auf `proposals` (`value_grounded`, `value_grounded_reason`, `confidence_rationale`) + Alembic-Migration (auf SQLite angewendet); beide Endpunkte liefern sie; die Detailansicht zeigt einen neuen Block **„Woher kommt die Konfidenz?"** — grün „Wert ist in den Daten belegt" bzw. **gelb „Wert ist NICHT in den Daten belegt — bitte genau prüfen"** samt Klartext-Begründung, darunter die Selbsteinschätzung der KI (Band + Beleg).
- **Verifikation (Live-Server):** die 3 Board-Vorschläge neu erzeugt → `GET /api/review/proposals` liefert `confidence_score` 0.775 / 0.75 / 0.0 mit `value_grounded` 1 / 1 / 0; Detail-Endpunkt liefert z. B. `value_grounded_reason="Referenz belegt: articles.articleId=122873 existiert"` und `confidence_rationale="Band A: Die articleId '122873' ist direkt aus der Demand-ID 'D122873_001' ableitbar…"`. Deep-Link öffnet die Detailansicht mit dem neuen Block. Nichts entschieden, nichts angewendet.
- **Spec:** `docs/PT4_PLAN.md` trägt die neue Formel samt Begründung.
- **Open / next:** Damit ist der Weg zur **Baseline-Messung** (letzter AK2-Blocker) frei. Offen bleibt: `value_grounded` deckt `add_to_array`/verschachtelte Pfade (`equipment[i].predecessors[0]`) noch nicht ab — dort greift Regel (c) und liefert konservativ `0`; bei realen Fällen nachschärfen.

---

### 2026-07-11 — AP4.4 Behebung aller Befunde aus dem ersten Nutzer-Review
- **Status:** done (4 von 5 Punkten vollständig gelöst; die Konfidenz-Trennschärfe **teilweise** — ehrlicher Restbefund unten).
- **Changed files:** `demo/routes/apply_prep.py`, `demo/routes/review.py`, `demo/db/repository.py`, `demo/agents/orchestration_agent.py`, `demo/agents/chat_agent.py`, `demo/smart-planning/runtime/generate_correction_llm.py` (nur Prompt, additiv), `demo/ui/scripts/review.js`, `demo/ui/review.html`, `demo/ui/css/styles.css`.

#### 1. BUG 1 gelöst — das System nennt jetzt die MENSCHLICHE Lösung, nicht die verworfene KI-Lösung
Zwei Ursachen, beide behoben:
- **Artefakt-Ebene:** `prepare_proposal_for_apply` schreibt beim Modify jetzt auch das `reasoning` um (neu: `_human_override_reasoning`): *„[MENSCHLICHE KORREKTUR] Der Reviewer hat den KI-Vorschlag 'X' verworfen und stattdessen 'Y' angewendet. Begründung des Reviewers: …"*. Die KI-Begründung bleibt vollständig erhalten (neues Feld `ai_reasoning` + `ai_original.json`); der Reviewer-Kommentar landet in `human_comment`. `review.py` reicht den Kommentar bis dorthin durch. Damit sind `metadata.txt`, Audit-Report und jeder künftige Konsument (AP6/AP7) konsistent.
- **Chat-Ebene (die eigentliche Ursache):** Der Chat-Agent kannte Review-Entscheidungen **überhaupt nicht** — er sah nur die Chat-History, in der der KI-*Vorschlag* stand; die Entscheidung fällt aber im Review Board, außerhalb des Chats. Neu: `repository.get_decisions_for_snapshot()` (Join `reviews`×`proposals`), `orchestration_agent._get_review_decisions()` (Snapshot-ID aus aktueller Nachricht **oder** History; DB-Fehler brechen den Chat nie) und ein neuer Kontextblock im `chat_agent` mit expliziter Regel: `applied_value` ist die Lösung, `ai_value` bei `decision=modify` **verworfen** und darf nicht als Lösung genannt werden.
- **Verifikation (echter Chat-Endpunkt, dieselbe Frage wie der Nutzer):** *„was war die Lösung?"* → **„Die Lösung bestand darin, den Wert `D210451_001` anzuwenden. Ursprünglich hatte die KI `D210446_003` vorgeschlagen, dieser wurde jedoch von einer Person überprüft und ersetzt."** Vorher nannte der Chat `D210446_003` als Lösung. Zusätzlich: `get_decisions_for_snapshot` liefert `applied_value='D210451_001'` / `ai_value='D210446_003'`; der `reasoning`-Rewrite wurde an einem Wegwerf-Snapshot geprüft (Menschenwert genannt, KI-Wert als verworfen markiert, `ai_reasoning` erhalten).

#### 2. BUG 2 gelöst — keine veraltete Meldung mehr, dafür ein Deep-Link
Die hartkodierte Falschaussage *„die Freigabe-Funktion folgt in einem späteren Schritt / AP3"* ist aus `orchestration_agent.py` **entfernt** (an beiden Stellen). Neu: `_review_board_hint()` erzeugt einen Wegweiser mit **Deep-Link auf den konkreten Vorschlag** — und er wird jetzt auch **nach jeder erfolgreichen `analyze_only`-Pipeline** angehängt, also genau dort, wo der Nutzer bisher ohne Hinweis dastand. Beispielausgabe: *„Dein Korrekturvorschlag wartet auf eine Entscheidung: [Im Review Board öffnen](/review.html?proposal=7ab03beb-…__iteration-1) — DEMAND_ARTICLE_IDS, Konfidenz 78 %."* Fällt ohne offenen Vorschlag sauber auf den Listen-Link zurück. Der Chat rendert Markdown (`marked.parse`), der Link ist also klickbar.
`review.js` wertet `?proposal=<id>` aus und öffnet die Detailansicht direkt. **Verifiziert:** Deep-Link → Detail offen, Ziel-Pfad `demands[386].articleId`, Entscheidungs-Panel vorhanden.

#### 3. Sprache gelöst — Begründungen auf Deutsch
Der Prompt in `generate_correction_llm.py` enthält jetzt eine explizite Sprachvorgabe (`reasoning` und das neue `confidence_rationale` auf Deutsch). **Zwischenfehler unterwegs, sofort gefixt:** die erste Fassung stellte die Anweisung *in* den JSON-Beispielwert — das LLM kopierte sie wörtlich („Begruendung auf DEUTSCH: …"). Anweisung raus aus dem Beispiel, Platzhalter rein. **Verifiziert:** alle drei offenen Vorschläge tragen jetzt natürliches Deutsch.

#### 4. UX gelöst — Snapshot-Filter im Review Board
Das Board listet systemweit; deshalb sah der Nutzer den `sdfsdf`-Vorschlag eines **fremden** Snapshots. Neu: eine Filterleiste (erscheint nur, wenn mehrere Snapshots offene Vorschläge haben) mit Anzahl je Snapshot, clientseitig, per `?snapshot=<id>` vorbelegbar. **Verifiziert:** „Alle Snapshots (3)" → Auswahl `1ef11903…` → genau 1 Karte, ausschließlich dieser Snapshot.

#### 5. Konfidenz — TEILWEISE gelöst (ehrlicher Restbefund)
Der Prompt hat jetzt eine **Kalibrierungs-Rubrik** (Bänder A–D mit Beispielen), harte Regeln („eine erfundene/hochgezählte ID ist Band C, max. 0.69"; „eine falsche Antwort mit hoher Konfidenz ist das schlechteste Ergebnis") und ein neues Feld `confidence_rationale` (Band + Beleg).
- **Messung an 4 Wegwerf-Kopien (echte LLM-Läufe, die Demo-Vorschläge unberührt):** vorher `llm_confidence` = **0.95 in 7 von 8** Fällen. Nachher: **0.0 / 0.9 / 0.95** → der Score **variiert**. Die drei neu erzeugten Board-Vorschläge tragen `confidence_score` **0.75 / 0.775 / 0.0** (vorher: 0.775 / 0.775 / 0.0).
- **Restbefund, nicht schöngeredet:** Im Duplicate-ID-Fall — genau dem, in dem die KI **falsch** lag — stuft sich das LLM trotz der harten Regel selbst als **„Band A" mit 0.9** ein, obwohl es die ID **hochgezählt und erfunden** hat (das wäre Band C, ≤ 0.69). **Prompt-Kalibrierung allein reicht nicht.** Für echte Trennschärfe braucht es ein **deterministisches** Signal (z. B. „ist `new_value` in den Daten belegbar oder erfunden?"). Das ändert die Konfidenz-**Formel** aus `PT4_PLAN.md` (0.5·llm + 0.3·schema + 0.2·memory) — und `schema_valid` ist ohnehin **immer 1** (das Proposal wird direkt nach dem Bau validiert), der 0.3-Term ist also totes Gewicht. Diese Formeländerung ist eine **Spec-Entscheidung des Nutzers**, deshalb hier NICHT eigenmächtig vorgenommen. → Backlog, muss vor AK2 fallen.

#### Zwei gemeldete Punkte waren Missverständnisse (siehe Audit-Eintrag unten)
„4 statt 1 Vorschlag" (die 4 stammen aus dem Erzeugungslauf davor) und „sdfsdf ist verschwunden" (nein — verschwunden ist der vom Nutzer entschiedene `1e3667d9`; `7ab03beb` ist weiterhin `pending_review`).

- **Eigener Fehler unterwegs (transparent):** Beim Neu-Generieren der drei Vorschläge nahm ich an, es entstünde eine `iteration-2`. Falsch: `generate_correction_llm` schreibt in die **höchste Iteration mit `llm_identify_response.json`** — also wieder in `iteration-1`. Mein anschließendes „Aufräumen" der alten `iteration-1`-Zeilen löschte damit die soeben erzeugten Zeilen. Sofort bemerkt und durch erneutes Generieren behoben; Endstand geprüft.
- **Endstand:** 3 offene Vorschläge, alle `pending_review`, deutsche Begründungen, Konfidenz 0.75 / 0.775 / 0.0. `ec96832c`/`iteration-5` unverändert; nichts entschieden, nichts angewendet.
- **Open / next:** Backlog: (a) deterministisches Konfidenz-Signal + Formelentscheidung (blockiert AK2); (b) `confidence_rationale` in DB/Board sichtbar machen (aktuell nur in der Proposal-JSON).

---

### 2026-07-11 — Audit nach dem ersten manuellen Review durch den Nutzer (read-only) → **2 echte Bugs**
- **Status:** done (Analyse, **kein Code geändert**). Anlass: der Nutzer hat im Review Board eigenständig einen Modify auf `1e3667d9…__iteration-1` (duplicate `demandId`) durchgeführt und danach 7 Auffälligkeiten gemeldet. Ergebnis: **2 echte Bugs**, 1 echte Schwäche, 2 UX-Mängel, 2 Missverständnisse.

#### ✅ Kernfrage zuerst: der Menschenwert WURDE korrekt angewendet
Der Nutzer ersetzte den KI-Vorschlag `D210446_003` durch `D210451_001`. Nachgeprüft:
`reviews.final_value = "D210451_001"` · `proposals.suggested_value = "D210446_003"` (KI-Historie) · `snapshot-data.json: demands[767].demandId = "D210451_001"` · **keine doppelten demandIds mehr** · `ai_original.json` hält `D210446_003` · `metadata.txt`: `New Value: D210451_001`. **Die Modify-Kette funktioniert.**

#### 🐞 BUG 1 (neu, mittelschwer): `reasoning`/`current_value` bleiben nach einem Modify die KI-Version → nachgelagerte Konsumenten erzählen die FALSCHE Lösung
`prepare_proposal_for_apply` ersetzt beim Modify **ausschließlich `new_value`** (apply_prep.py:287). Die Felder **`reasoning`** und **`current_value`** bleiben unverändert die KI-Sicht. Folge: das `reasoning` im angewendeten Proposal lautet weiterhin *„…I assigned a new unique ID **'D210446_003'**…"*, obwohl `D210451_001` in den Daten steht. Alles, was `reasoning` liest, erzählt die falsche Geschichte:
- **Der Chat-Agent** antwortete dem Nutzer auf „was war die Lösung?" wortwörtlich mit der **KI-Version** (`D210446_003`, inkl. der KI-Herleitung) — obwohl der Mensch das überstimmt hatte.
- **`metadata.txt` ist in sich widersprüchlich:** `New Value: D210451_001` (korrekt), direkt darunter `Reasoning: …assigned 'D210446_003'…` (falsch).
- Betrifft ebenso `generate_audit_report.py` und jeden künftigen Dashboard-/Memory-Konsumenten (AP6/AP7).
- In **AP4.3.2a Fallstrick 4** war `current_value` bereits als „für update_field harmlos" eingestuft — **das war zu kurz gedacht:** die Tragweite liegt bei `reasoning`, nicht bei `current_value`.
- **Fix-Richtung (nicht gebaut):** beim Modify `reasoning` additiv um einen Human-Override-Vermerk ergänzen (KI-Begründung erhalten, aber als überstimmt markieren) und/oder `value_source` von den Konsumenten auswerten lassen. Der Chat-Agent kennt die `reviews`-Tabelle überhaupt nicht — er liest Dateien.

#### 🐞 BUG 2 (neu, kosmetisch aber demo-relevant): veraltete Chat-Meldung, kein Deep-Link
`orchestration_agent.py:662–668` und `:720–726` melden hartkodiert: *„Die Korrektur kann erst nach ausdrücklicher Freigabe übernommen werden (die Freigabe-Funktion folgt in einem späteren Schritt / **AP3**)."* Das ist seit AP3/AP4 **falsch** — die Freigabe existiert. Der Nutzer wurde nicht ins Review Board geleitet und musste selbst dorthin navigieren. **Kein Deep-Link** auf `/review.html` (bzw. auf den konkreten `proposal_id`). Gehört fachlich zu AP5 (Benachrichtigung mit Deep-Link), die falsche Wortwahl ist aber schon jetzt ein Bug.

#### ⚠️ SCHWÄCHE (bestätigt, der Nutzer hatte recht): der `confidence_score` hat KEINE Trennschärfe
Gemessen über alle 8 erzeugten Proposals: **`llm_confidence` ist in 7 von 8 Fällen exakt `0.95`** (einmal `1.0`), `schema_valid` ist **immer** `True`, `memory_support` ist per Definition `0` (AP7 fehlt) → `0.5·0.95 + 0.3·1 + 0.2·0 = **0.775**` in **7 von 8** Fällen. Die einzige Varianz stammt aus dem Sonderfall `manual_intervention_required → 0.0`.
→ Der Score unterscheidet faktisch nur **„Vorschlag vorhanden" (0.775) vs. „KI kapituliert" (0.0)** — er misst **keine Qualität**. Beleg aus genau diesem Review: der falsche Vorschlag `D210446_003` hatte **78 %**. **Das ist ein Problem für AK2** („Konfidenz vs. menschliche Entscheidung / Kalibrierung"): mit einem quasi-konstanten Score ist keine Kalibrierungskurve darstellbar. → Backlog, muss vor der Evaluation adressiert werden.

#### 🌐 UX 1: Begründungen auf Englisch
Der Prompt in `generate_correction_llm.py` (Zeilen ~318/411/437) ist vollständig englisch und enthält **keine Sprachvorgabe** → das LLM antwortet englisch. Die UI ist deutsch. Fix wäre additiv (eine Sprachanweisung im Prompt).

#### 🌐 UX 2: das Review Board ist NICHT auf den Snapshot gefiltert
`GET /api/review/proposals` liefert **alle** offenen Vorschläge systemweit. Deshalb sah der Nutzer im Board neben „seinem" Fall auch den `sdfsdf → 122873`-Vorschlag, der zu einem **anderen** Snapshot (`7ab03beb`) gehört — verständlicherweise irritierend („sdfsdf existiert in diesem Snapshot gar nicht"). Kein Bug, aber es fehlt ein Snapshot-Filter / eine Snapshot-Spalte-als-Kontext im Board.

#### ✅ Zwei Missverständnisse (kein Defekt)
- **„4 Einträge statt 1":** korrekt so — die 4 Vorschläge stammen aus dem unmittelbar zuvor gefahrenen Erzeugungslauf (4 Fehler-Snapshots, siehe vorheriger Eintrag).
- **„Der sdfsdf-Vorschlag ist ohne Zutun verschwunden":** nein. DB-Stand: `7ab03beb…` ist weiterhin **`pending_review`** und auch auf dem letzten Screenshot sichtbar. Verschwunden ist `1e3667d9…` — **der Vorschlag, den der Nutzer gerade entschieden hat** (entschiedene Vorschläge fallen aus der Liste, die hart auf `pending_review` filtert).

#### 💡 Bemerkenswert (fürs Paper): die KI hat sich selbst widersprochen, der Mensch hat es gefangen
Die KI-Begründung lautet: *„…the pattern is `D{articleId}_{sequence}`. Since the articleId for the second occurrence is **'210451'**, the sequence number was incremented to '003'"* — und schlug dann **`D210446_003`** vor. Nach ihrem **eigenen** Muster hätte `D210451_001` herauskommen müssen. **Genau das hat der Mensch eingesetzt.** Ein Lehrbuch-Beispiel für den Nutzen von Human-in-the-Loop: hohe Konfidenz (78 %), plausible Begründung, trotzdem falscher Wert.
- **Open / next:** Priorisierung durch den Nutzer. Kandidaten: (1) BUG 1 (falsche Lösung in Chat/metadata/Audit) — **inhaltlich der gravierendste**, verfälscht die Nachvollziehbarkeit; (2) Konfidenz-Trennschärfe (blockiert AK2); (3) BUG 2 + Deep-Link (AP5); (4) Sprache; (5) Snapshot-Filter im Board.

---

### 2026-07-11 — Vorschlagserzeugung Schritte 1–3: 4 frische `pending_review`-Vorschläge + Rezept
- **Status:** done. **Nichts entschieden, nichts angewendet** — alle vier Vorschläge stehen auf `pending_review`. `ec96832c/snapshot-data.json` SHA-256 durchgehend **`62279f61…`**, `iteration-5` unberührt.
- **Changed files:** **kein Produktivcode.** Erzeugte Daten-Artefakte: 4 Snapshot-Ordner (`download_snapshot`), je `iteration-1/llm_correction_proposal.json`, je ein `_proposals/<id>__iteration-1.json`, je eine `proposals`-DB-Zeile.
- **Vorbedingung (nach dem STOPP aus Schritt 0):** Der Nutzer hat **drei neue Fehler-Snapshots auf dem Server** angelegt (gezielt manipulierte Daten). Damit existieren vier verwertbare Fehler-Snapshots mit **drei verschiedenen Fehlerarten** — vorher war es genau einer.

#### SCHRITT 3 — Das Rezept (reproduzierbar, wendet nichts an)
Aus `demo/` mit dem venv, je Snapshot **in dieser Reihenfolge**:
```
python smart-planning/runtime/download_snapshot.py <snapshot_id>          # 0. ID ist POSITIONAL
python -c "from routes.server_validation import trigger_server_validation; \
           print(trigger_server_validation('<snapshot_id>'))"             # 1. AP3.3d-Trigger
python smart-planning/runtime/validate_snapshot.py     --snapshot-id <id> # 2.
python smart-planning/runtime/identify_error_llm.py    --snapshot-id <id> # 3.
python smart-planning/runtime/generate_correction_llm.py --snapshot-id <id> # 4.
```
**Warum diese Reihenfolge zwingend ist (jeweils aus dem Code belegt):**
- **0.** `identify_snapshot` (Zeile 40) und `generate_correction_llm` (Zeile 494) laden `{id}/snapshot-data.json` **lokal**. Ein nur serverseitig existierender Snapshot reicht nicht → `download_snapshot` muss zuerst laufen (nimmt die ID als **positionales** Argument, nicht `--snapshot-id`).
- **1.** `validate_snapshot.py` macht **nur den `GET`**. Ohne vorher angestoßenen Job liefert der Server eine leere/veraltete Meldungsliste (AP3.3d) → identify fände nichts.
- **2. → 3.** `identify_error_llm` bricht ohne `{id}/snapshot-validation.json` ab.
- **3. → 4.** `generate_correction_llm` bricht ohne `last_search_results.json` **und** ohne die höchste Iteration mit `llm_identify_response.json` ab.
- **Ergebnis je Lauf:** **genau ein** Vorschlag (identify wählt einen `selected_error`), `status=pending_review` in der DB, zentraler Record unter `_proposals/`. Die Pipeline `analyze_only` enthält dieselben Schritte 2–4 (plus `validate_correction_schema_llm`), setzt aber den Download und den Trigger voraus.

#### SCHRITTE 1+2 — Ergebnis (Nachweis über `GET /api/review/proposals`, HTTP 200, **4 Einträge**)
| Snapshot | eingebauter Fehler | proposal_id | error_type | target_path | confidence | pending_review |
|---|---|---|---|---|---|---|
| `1e3667d9` | doppelte `demandId D210446_002` | `1e3667d9…__iteration-1` | `UNIQUE_IDS` | `demands[767].demandId` | **0.775** | **ja** |
| `7ab03beb` | `articleId "sdfsdf"` bei `D122873_001` | `7ab03beb…__iteration-1` | `DEMAND_ARTICLE_IDS` | `demands[386].articleId` | **0.775** | **ja** |
| `1d45ddff` | `articleId 122123600` + `relDensity -2/-6` + `equipmentKey` | `1d45ddff…__iteration-1` | `DEMAND_ARTICLE_IDS` | `demands[350].articleId` | **0.0** | **ja** |
| `1ef11903` | (Alt) 124211 ohne `workItemConfigs` | `1ef11903…__iteration-1` | `WORK_ITEM_CONFIGS_COMPLETENESS` | `articles[312].workItemConfigs` | **0.775** | **ja** |

- **`error_type` ist bei allen vier korrekt** (tag-basiert seit AP3.6b-2) — kein `DUPLICATE_ID`-Mislabel mehr.
- **Der 0.0-Fall ist echt und richtig, kein Fehler:** Bei `1d45ddff` liefert die KI `action=manual_intervention_required` mit `llm_confidence=0.0` → per AP1.3-Sonderregel `confidence_score=0.0`, `new_value=null`, `correction_kind=KIND_UNKNOWN`. Begründung der KI: für die erfundene `articleId 122123600` existiert **kein** belegbarer Ersatz in den Daten. **Das ist genau das gewünschte Verhalten** — das System rät nicht, sondern eskaliert an den Menschen. Ein wertvoller Demo-Fall (niedrige Konfidenz, roter Balken im Board).
- **Beobachtung zu `1d45ddff` (ehrlich):** Von den drei eingebauten Manipulationen erzeugte die `equipmentKey`-Änderung (`BPU01` → `BPAU021123`) **keinen** ERROR; der Server meldete nur 2 ERRORs (fehlender Artikel + negative Dichte). `identify_error_llm` wählte davon einen (`DEMAND_ARTICLE_IDS`) — die negative Dichte bleibt in diesem Snapshot unbehandelt (ein Vorschlag pro Lauf, so gewollt).
- **Verifikation:** `GET /api/review/proposals` → HTTP 200, **4** Vorschläge, alle `pending_review` (Tabelle oben). Je ein zentraler Record in `_proposals/`. Guard-SHA `62279f61…` vor und nach **jedem** der vier Läufe unverändert.
- **Open / next:** DoD erfüllt (N=4 frische `pending_review`-Vorschläge, Rezept geloggt, `ec96832c`/`iteration-5` unberührt). Damit sind sowohl die **Demo** (4 Fälle, darunter ein 0.0-Konfidenz-Eskalationsfall) als auch die **Baseline** (3 verschiedene Fehlerarten) versorgt. Die Baseline-Messung selbst (AK2, `HUMAN_IN_THE_LOOP=false`) ist ein eigener Schritt.

---

### 2026-07-11 — Vorschlagserzeugung Schritt 0: Contract-Check + Bestandsaufnahme → **STOPP**
- **Status:** done (read-only). **Kette bestätigt, aber die Datenlage weicht ab → gestoppt, nichts gebaut, nichts erzeugt, nichts entschieden.**
- **Changed files:** keine (nur dieser Log-Eintrag). `ec96832c/snapshot-data.json` SHA-256 vor **und** nach dem Check: **`62279f61…`** — unverändert.

#### A — Tool-Kette (belegt aus dem Code, KEINE Abweichung)
Die vorkonfigurierte Pipeline **`analyze_only`** (`sp_tools_config.SP_PIPELINES`) ist genau die Erzeugungskette und wendet nichts an:
`validate_snapshot → identify_error_llm → generate_correction_llm → validate_correction_schema_llm`.
Abhängigkeiten und Eingaben, aus den Tools selbst:
1. **`trigger_server_validation(snapshot_id)`** (`routes/server_validation.py`, AP3.3d) — **muss vorgeschaltet werden.** `validate_snapshot.py` macht nur den `GET`; ohne vorher angestoßenen Job liefert der Server eine leere/veraltete Meldungsliste (der Upload löscht sie und rechnet nicht von selbst neu).
2. **`validate_snapshot.py --snapshot-id <id>`** → schreibt `{id}/snapshot-validation.json`.
3. **`identify_error_llm.py --snapshot-id <id>`** → benötigt `{id}/snapshot-validation.json` (sonst „not found"); triggert `identify_snapshot` → schreibt `{id}/last_search_results.json` + `iteration-N/llm_identify_response.json`.
4. **`generate_correction_llm.py --snapshot-id <id>`** → benötigt `last_search_results.json` **und** die höchste Iteration mit `llm_identify_response.json`; schreibt `iteration-N/llm_correction_proposal.json`, den zentralen Record `_proposals/{proposal_id}.json` und die DB-Zeile `proposals` mit **`status=pending_review`** (AP2.3).
- Ergebnis: **genau ein** Vorschlag je Lauf (identify wählt einen `selected_error`).

#### B — Bestandsaufnahme (6 lokale Snapshots, Serverabgleich + echter Validierungsjob)
| Snapshot | Server | ERROR | WARN | Fehlerart |
|---|---|---|---|---|
| `1ef11903-…` | **ok** | **2** | 5 | `work_item_configs_completeness`, `start_end_operation_existence` (Artikel 124211) |
| `ec96832c-…` | ok | **0** | 5 | — (durch die Live-Entscheidung bereinigt) |
| `2b5ee9f9-…` | **404** | — | — | nicht mehr auf dem Server |
| `496e1514-…` | **404** | — | — | nicht mehr auf dem Server |
| `69f3d1bf-…` | **404** | — | — | nicht mehr auf dem Server |
| `c6bdde43-…` | **404** | — | — | nicht mehr auf dem Server |

#### C — Die Abweichung (Grund für den STOPP)
Der Auftrag geht von **mehreren** „vorhandenen Fehler-Snapshots" aus. Real existiert **genau einer**:
- **4 der 6 Snapshots sind serverseitig weg (404)** — reine Altartefakte (bestätigt die AP3.3b-Notiz zu `2b5ee9f9`). Ohne Server kein Validierungsjob, kein Upload, keine Re-Validierung. Ihre **lokalen** `snapshot-validation.json` (vom 2026-02-21 / 2026-03-10) enthalten zudem **0 ERROR** (nur je 2 Meldungen) — daraus ließe sich also nicht einmal offline ein Vorschlag erzeugen.
- **`ec96832c` hat 0 Fehler** — genau das war das Ergebnis der Live-Entscheidung.
- **Bleibt `1ef11903`** mit 2 ERROR — und das ist **derselbe Fall** (Artikel 124211, fehlende `workItemConfigs`), den wir gerade entschieden haben; es ist offenbar ein Geschwister-Snapshot desselben Standes.
→ **N = 1**, nicht N > 1. Und dieses eine N ist inhaltlich ein Duplikat des bereits demonstrierten Falls. Für die **Demo** reicht das; für eine **Baseline** über „mehrere Snapshots / mehrere Fehlerarten" (AK2) reicht es **nicht**.
- **Open / next:** Entscheidung des Nutzers nötig (Schritt 1 NICHT gestartet). Optionen: (a) mit `1ef11903` einen frischen `pending_review`-Vorschlag erzeugen (Demo-Bedarf gedeckt, N=1); (b) für die Baseline neue Fehler-Snapshots **auf dem Server anlegen** (`create_snapshot`) — Nebenwirkung: es gibt **kein** Lösch-Tool, die Snapshots bleiben dort; (c) beides.

---

### 2026-07-11 — LIVE-ENTSCHEIDUNG: `ec96832c-…__iteration-5` MODIFY + angewendet (2 → 0 Fehler)
- **Status:** done — **die erste echte Human-in-the-Loop-Entscheidung des Projekts.** Ein realer LLM-Vorschlag wurde fachlich geprüft, vom Menschen **korrigiert** und über den regulären Endpunkt auf die echten Snapshot-Daten angewendet. Kein Code geändert; VPN aktiv.
- **Vorschlag:** `WORK_ITEM_CONFIGS_COMPLETENESS`, `articles[312].workItemConfigs` (Artikel **124211 = „Himbeer-Grundstoff"**), leer → 13 workItemConfig-Objekte, Konfidenz 0.775.
- **Readiness-Check vorab (nichts angewendet):** Guards würden passieren (Iteration ok; Identität `passed`, `verified_id=124211`), VPN erreichbar, Validierungsjob `FINISHED` (3,8 s) → echter Ausgangsstand **2 ERROR / 5 WARNING**, beide ERRORs auf 124211 (`work_item_configs_completeness` + `start_end_operation_existence` für HE01).
- **Fachliche Prüfung — die ursprüngliche Nutzer-Hypothese wurde durch die Daten widerlegt:**
  - Ausgangsthese war: BA01 auf `rampUpTime=0, netTimeFactor=0, ohne sequence`, analog zum „nächsten vergleichbaren Artikel" **100005**. Faktisch korrekt daran: 100005 hat wirklich `0/0` ohne `sequence`; `HP` ist wirklich nur **29/356** in der Abteilung (Modus: `P`, 153); 124211 fehlt wirklich in `new-snapshot.json`; und **12 der 13** Keys des KI-Vorschlags sind identisch mit 100005.
  - **Aber 100005 ist kein Zwilling:** 100005 heißt **„Entschäumer"** (Hilfsstoff), 124211 ist ein **Grundstoff**. Die 12 übereinstimmenden Keys sind **abteilungsweit konstant** und haben damit **null Trennschärfe** — ausgerechnet im einzigen variierenden Feld (BA01) gehört 100005 zu einer 3 %-Minderheit. Ebenso trägt `workPlanId 'SP10 SP01'` nichts bei: **alle 1697 Artikel** haben denselben Arbeitsplan (konstant, nicht selektiv).
  - **Gemessene Kohorten (Abteilung `AfG (Homo/Past)`, aus `new-snapshot.json`):** BA01 `30/1` = **345/356 (97 %)** vs. `0/0` = 11 (3 %). Unter den 274 „Grundstoff"-Artikeln: 266 × `30/1`, 8 × `0/0`. Unter den **16 weiteren Himbeer-Grundstoffen: 16/16 = `30/1`, kein einziger `0/0`.** Die `0/0`-Gruppe besteht überwiegend aus Hilfsstoffen (Entschäumer, Aroma).
  - **`sequence`:** hier hatte die Kritik am KI-Wert recht — unter den 16 Himbeer-Grundstoffen ist `P` = **11×**, `PH` = 2×, `HP` = 2×, `HHP` = 1×. Der KI-Wert `HP` ist eine gültige, aber schwach belegte Minderheit; `P` ist der Modus.
- **Getroffene Entscheidung (Nutzer, nach Vorlage der Zahlen): MODIFY mit BA01 = `rampUpTime=30, netTimeFactor=1, sequence="P"`.** Die übrigen 12 workItemConfigs unverändert vom KI-Vorschlag (abteilungsweit konstant, identisch mit den Referenzartikeln).
- **Durchführung über den regulären Endpunkt** `POST /api/review/proposals/…__iteration-5/modify` (derselbe Pfad, den der AP4.3.2b-UI-Button geht), mit dem 13er-Array als `final_value` und der Begründung als `comment`.
- **Ergebnis (HTTP 200):** `applied=true`, `status=applied`, `value_source=human_modify`, **`errors_before=2 → errors_after=0`**, Validierungsjob `38246600-…` `FINISHED` nach 3,4 s. `is_valid=true`, 0 Fehler, Warnungen unverändert.
  - **In den Daten:** `articles[312].workItemConfigs` = 13 Objekte; **BA01 = `{"workItemKey":"BA01","rampUpTime":30,"netTimeFactor":1,"sequence":"P"}`** — der **Menschenwert**, nicht der KI-Wert. `snapshot-data.json` SHA-256 `7174a169…` → **`62279f61…`** (erste echte Änderung an diesem Snapshot seit AP3.3d).
  - **Audit-Trail vollständig:** `llm_correction_proposal.ai_original.json` hält weiterhin den KI-Wert `BA01 = 30.0/1.0/"HP"`; `proposals.suggested_value` (DB) ebenfalls; `reviews.final_value` (id=5) trägt das komplette 13er-Array mit dem Menschenwert samt Begründungstext.
  - **Liste:** `GET /api/review/proposals` liefert jetzt **0** offene Vorschläge.
- **Damit erstmals live nachgewiesen:** der Erfolgs-Zweig der UI (`applied=true` + echte `errors_before → errors_after`), die Modify-Kette Mensch → `reviews.final_value` → `prepare_proposal_for_apply` → `apply_correction` → `update_snapshot` (PUT) → echte Re-Validierung, und die AP3.3d-Trigger-Logik unter Realbedingungen. **AK3 (Human-in-the-Loop) ist damit end-to-end demonstriert.**
- **Offener fachlicher Vorbehalt (unverändert):** die Validierung belegt nur **Key-Vollständigkeit**, nicht die Richtigkeit der BA01-**Werte**. `2 → 0` heißt „alle 13 Keys da", nicht „30/1/P ist korrekt". Bei Stammdatenzugriff gegenprüfen. → Backlog.
- **Konsequenz für die Demo:** es existiert **kein `pending_review`-Vorschlag mehr**. Für eine Vorführung des Review Boards muss ein frischer Vorschlag erzeugt werden (identify → generate auf einem Snapshot mit echten Fehlern).

---

### 2026-07-11 — AP4.3.2b-Ergänzung: Pro-Objekt-Key-Warnung im Modify-Editor
- **Status:** done
- **Changed files:** `demo/ui/scripts/review.js` (nur diese eine Datei — `styles.css` brauchte nichts, die Warn-Klasse `.rb-json-hint.warn` existiert seit AP4.3.2b). Additiv, kein Backend.
- **Was gebaut wurde:** Neue Funktion `checkObjectKeys(parsed, aiValue)`, aufgerufen aus `validateJsonInput()`. Ist `final_value` ein Array von Objekten, wird **je Element** geprüft: (1) unbekannte/vertippte Keys, (2) fehlende Keys, (3) geänderte Objekt-Anzahl. Erwartete Keys kommen aus dem KI-Vorschlag selbst (`columnsFor()` — für workItemConfigs also `workItemKey, rampUpTime, netTimeFactor, sequence`). **Warnt nur, blockiert nie** — ein Reviewer darf bewusst abweichen; analog zur bestehenden Top-Level-Typ-Warnung (gelbe Hint-Zeile, Absenden weiterhin möglich).
- **Kniff gegen Rauschen:** `sequence` ist in den echten Daten **echt optional** (nur BA01 hat es). Ein fehlender Key wird deshalb nur gemeldet, wenn das **KI-Objekt an derselben Position** ihn hatte — sonst würde jede der 12 sequenzlosen Zeilen warnen und die Warnung wäre wertlos.
- **Verifikation (echter Server, echte `review.js`-Funktionen in node, Wegwerf-Vorschlag mit dem realen 13er-Wert; `…__iteration-5` nur gelesen):**
  - **(1) Unverändert:** `[ok] Gültiges JSON — Array mit 13 Einträgen.` — keine Fehlalarme.
  - **(2) Tippfehler `netTimeFactor` → `netTimeFacotr` in BA01 (Objekt #7):** `[warn] … Achtung: unbekannter Key "netTimeFacotr" in Objekt #7 (Tippfehler?); fehlender Key "netTimeFactor" in Objekt #7. Wird so angewendet.` — genau der Fall, den die Ergänzung abfangen soll.
  - **(3) Key gelöscht (`rampUpTime` in Objekt #0):** `[warn] … fehlender Key "rampUpTime" in Objekt #0.`
  - **(4) Objekt entfernt (13 → 12):** `[warn] … Anzahl geändert: 13 → 12 Objekte.` — und der Klick auf „Übernehmen & anwenden" **setzt den Request trotzdem ab** (`final_value` = Array mit 12 Objekten): die Warnung blockiert nachweislich nicht.
  - **(5) Kein `sequence`-Rauschen:** die 12 Objekte ohne `sequence` erzeugen keine „fehlender Key"-Meldung.
- **Grenze (unverändert):** die Prüfung vergleicht Keys, **nicht Werttypen oder Wertebereiche**. Ein `rampUpTime: "dreißig"` bliebe unbeanstandet — das Backend-Schema akzeptiert jeden JSON-Typ (AP4.3.2a, Lücke 2).
- **Sauberkeit:** Wegwerf-Vorschlag + Review-Zeile gelöscht; DB-Endzustand = 4 echte Proposals + 4 echte Reviews; **`…__iteration-5` unverändert `pending_review`**; `snapshot-data.json` SHA-256 `7174a169…` unverändert.

---

### 2026-07-11 — Recovery-Verfahren (Lücke 1): „entschieden aber nicht angewendet"
- **Status:** done (Analyse + Verifikation am Wegwerf-Fall; **kein Feature gebaut**, kein Produktivcode geändert — nur dieser Log-Eintrag). Der Recovery-Ablauf ist damit belegt und einmal durchgespielt.
- **Das Problem, hart belegt:** Nach einem 409-B (Guard) oder 502 (Pipeline) steht ein Vorschlag in `approved`/`modified` **mit** `reviews`-Zeile, ist aber nicht angewendet. Ein zweites reguläres `POST …/modify` wurde am Wegwerf-Fall gefahren und liefert exakt: **HTTP 409** `{"error": "Proposal has already been decided", "status": "modified", "hint": "Only a proposal with status 'pending_review' can be decided."}` — `decide_proposal()` bricht in `_is_still_undecided()` ab, `_apply_after_review` wird **nie wieder erreicht**. Es gibt keinen Retry-Endpunkt.

#### Empfohlener Weg: **B — Apply erneut auslösen, Entscheidung nicht anfassen**
`_apply_after_review(proposal_id, decision, final_value)` leitet seine Autorisierung **selbst aus der DB** ab (Status ∈ `approved`/`modified` **und** ≥ 1 `reviews`-Zeile) — das ist **genau der Steckenbleiber-Zustand**. Die Funktion ist also ohne jede DB-Manipulation direkt wieder aufrufbar; sie durchläuft dieselben Guards wie im Normalbetrieb und schreibt **keine** neue Entscheidung.

Ablauf (aus `demo/` mit dem venv, nachdem die **Blockade-Ursache beseitigt** ist — z. B. die neuere Iteration entfernt oder die Identitäts-Abweichung geklärt):
```python
from db import repository as repo, models
from db.session import get_sessionmaker
from routes.review import _apply_after_review

db = get_sessionmaker()()
review = (db.query(models.Review).filter(models.Review.proposal_id == PID)
            .order_by(models.Review.decided_at.desc(), models.Review.id.desc()).first())
decision = review.decision
final_value = review.final_value if decision == "modify" else None   # <- Menschenwert aus der DB
result, status = _apply_after_review(PID, decision, final_value)
```
**Entscheidend:** `final_value` wird aus **`reviews.final_value`** gelesen, nicht aus `proposals.suggested_value`. Damit kann ein Recovery den Menschenwert **nicht** auf den KI-Wert zurücksetzen. (Bei `approve` ist `reviews.final_value` ohnehin der KI-Wert — AP3.2.)

#### Nicht empfohlener Weg: **A — DB-Reset auf `pending_review`**
Technisch möglich, aber teuer: `_is_still_undecided()` verlangt `status == "pending_review"` **UND keine** `reviews`-Zeile. Ein Reset erfordert also **beides**: `UPDATE proposals SET status='pending_review'` **und** `DELETE FROM reviews WHERE proposal_id=…`. Das **zerstört den Audit-Trail** und — schlimmer — beim `modify` den gespeicherten `final_value`: der Mensch müsste seinen Wert neu eintippen, und ein versehentliches Approve danach würde den **KI-Wert** anwenden. `ai_original.json` bliebe zwar liegen, aber die DB-Historie wäre weg. **Weg A nur, wenn die Entscheidung selbst revidiert werden soll** (dann ist es kein Recovery, sondern eine Neubewertung).

#### Verifikation (Wegwerf-Snapshot `ap43rec`, rein lokal; `ec96832c`/`iteration-5` nur gelesen)
Aufbau: lokaler Snapshot mit `demands[0].demandId = ""`, KI-Vorschlag `AI_D999` in `iteration-1`, dazu eine **Dummy-`iteration-2`**, damit der AP3.3a-Iterations-Guard reproduzierbar blockt.
- **(a) Steckenbleiber erzeugt:** `POST …/modify` mit `final_value="HUMAN_D42"` → **409-B**. Danach: `proposals.status=modified`, 1 `reviews`-Zeile (`final_value="HUMAN_D42"`), `snapshot-data.demandId` weiterhin `""`, Proposal-Datei unverändert beim KI-Wert, **kein** `ai_original.json` (der 409-B blockt **vor** `prepare_proposal_for_apply`).
- **(b) Sackgasse bewiesen:** zweiter `POST …/modify` → **409-A** (Wortlaut oben).
- **(c) Ursache beseitigt:** `iteration-2` entfernt → `iteration-1` ist wieder die höchste.
- **(d) Recovery gefahren** (Weg B, echter `_apply_after_review`-Aufruf): Autorisierung `status=modified` + `review_count=1` → **True**; Iterations-Guard **ok**; Identitäts-Guard **ok** (`passed_fill_still_empty`). Der Aufruf lief bis **`review.py:214`** durch, also **hinter allen vier Guards** — der Recovery-Pfad ist damit nachweislich autorisiert.
- **(e) Menschenwert schlägt durch:** `prepare_proposal_for_apply` → `value_source=human_modify`, `value_to_apply="HUMAN_D42"`, `ai_original_written=True`. Danach `apply_correction.py` (unverändertes Runtime-Tool, exit=0) → **`snapshot-data.demands[0].demandId = "HUMAN_D42"`**; Proposal-Datei `new_value="HUMAN_D42"`; **`ai_original.json` hält weiterhin `"AI_D999"`** → der KI-Wert bleibt als Historie erhalten, der Menschenwert wird angewendet. **Keine zweite `reviews`-Zeile** (Anzahl 1, gleiche id 5).
- **Grenze der Verifikation (ehrlich):** Der **Netzanteil** (`_validate_now` → `POST /validate`, `update_snapshot` → `PUT`) konnte **nicht** laufen — **das VPN war nicht verbunden** (`getaddrinfo failed` für den Keycloak-Host). Verifiziert ist damit alles bis einschließlich des lokalen Apply; der Upload + die echte Re-Validierung sind in AP3.3b/AP3.3d bereits real nachgewiesen und stehen im Recovery an derselben Stelle wie im Normalbetrieb.

#### **NEUER Befund (Robustheits-Lücke, nicht gefixt): ein VPN-Abriss erzeugt ein 500 UND einen Steckenbleiber**
`_apply_after_review` umschließt `_validate_now()` mit **keinem** `try/except`. Fällt das Netz aus, wirft `trigger_server_validation` → `validate_snapshot.SmartPlanningAPI.authenticate()` eine ungefangene `requests.ConnectionError`, die durch `_decide` bis in die Flask-Route durchschlägt → **HTTP 500** statt eines sauberen 502. Fatal daran: `decide_proposal()` hat zu diesem Zeitpunkt **schon committed** — die Entscheidung steht, nichts ist angewendet, `reviews.revalidation_result` bleibt leer (der 502-Zweig, der den Versuch protokollieren würde, wird nie erreicht). **Das ist der wahrscheinlichste reale Weg in Lücke 1** und trifft ebenso die UI (die zeigt dann nur „Server-Fehler (500)"). Fix-Vorschlag (eigener AP): `_validate_now` defensiv kapseln → bei Netzfehler `errors_before=None`, geordneter 502 mit `revalidation_result`. → Backlog.

- **Sauberkeit:** Wegwerf-Snapshot `ap43rec` + DB-Zeilen restlos entfernt. DB-Endzustand = die 4 echten Proposals + 4 echten Reviews wie zuvor; **`ec96832c-…__iteration-5` unverändert `pending_review`**; `snapshot-data.json` von `ec96832c` SHA-256 `7174a169…` (unverändert). **Kein Produktivcode geändert.**
- **Konsequenz für die Live-Entscheidung zu `…__iteration-5`:** Das Verfahren steht. Bei einem 409-B/502/500 gilt: Ursache beseitigen → Weg B fahren → der Menschenwert bleibt erhalten. **Voraussetzung: VPN muss verbunden sein** — ohne VPN scheitert die Entscheidung mit 500 und landet direkt im Recovery-Fall.

---

### 2026-07-12 — AP6.1 Metrik-Backend (`GET /api/dashboard/metrics`)
- **Status:** done. Erstes Sub-Paket von AP6. **Read-only** — das Modul schreibt nichts, es aggregiert nur, was AP2/AP3 bereits persistiert haben. Kein Schema, keine Migration, keine neue Datenquelle.
- **Changed files:** neu `demo/routes/dashboard.py`; `demo/db/repository.py` (eine additive Funktion `fetch_metrics_data()`); `demo/web_server.py` (drei Zeilen Blueprint-Registrierung). Kein Runtime-Tool angefasst, kein bestehender Endpunkt geändert.
- **Schichtung:** `repository.fetch_metrics_data()` ist bewusst nur ein **Datenabzug** (alle Zeilen in EINEM Session-Scope zu Dicts materialisiert, Muster wie `list_open_proposals_as_dicts`); **jede KPI-Definition** — und jeder Ehrlichkeitsvorbehalt daran — liegt in `dashboard.py`, damit sie an einer Stelle nachlesbar ist. `fetch_metrics_data` liefert je Vorschlag nur das **jüngste** Review: `decide_proposal()` verhindert heute eine Zweitentscheidung, aber eine Kennzahl, die bei einer künftigen Änderung still doppelt zählt, wäre eine schlechte Kennzahl.

#### Die Entwurfsentscheidung: `data_quality` statt stiller Filter (Nutzer-Entscheidung)
Die DB enthält eine **Mischung aus echten Läufen und Test-Fixtures**, und zwei Spalten haben mitten im Projekt ihre Bedeutung geändert. Ein Dashboard, das darüber stillschweigend mittelt, produziert selbstbewusst aussehende falsche Zahlen — genau das Versagen, gegen das dieses Projekt antritt. Deshalb: **alles wird aus ALLEN Daten berechnet, nichts wird still gefiltert**, und jeder Vorbehalt kommt als expliziter Flag mit heraus, den die UI zeigen muss. Alle Flags sind **aus den Daten selbst** abgeleitet, nie aus einem hartkodierten Stichtag:
  - **`REVALIDATION_PRE_AP33D`** — erkannt am **Fehlen des `errors_before`-Keys** (den AP3.3d eingeführt hat). Damit ist der Backlog-Punkt „AP6-Notiz: Läufe vor AP3.3d ausschließen/markieren" erledigt. Diese Einträge sind aus der Quote **ausgenommen** und separat ausgewiesen (`revalidation_untrusted`).
  - **`CONFIDENCE_LEGACY_FORMULA`** — erkannt an `value_grounded IS NULL` (vor AP4.5).
  - **`ERROR_TYPE_LEGACY_HEURISTIC`** — erkannt am Vokabular der Zähl-Heuristik `{DUPLICATE_ID, SINGLE_MATCH, NO_RESULTS_FOUND}` (AP3.6a: diese Labels sagen, wie oft ein Wert vorkam, nicht was falsch war). Betroffene Balken tragen `legacy_label: true`.
  - **`HANDLING_TIME_FIXTURES`**, **`SMALL_SAMPLE`**, **`COST_IS_ESTIMATE`**, **`TOKENS_INCOMPLETE`**, **`VALIDATION_COUNT_PARTIAL`** — siehe unten.
- **Nenner-Definitionen (die eigentliche Arbeit):**
  - **Revalidation-Quote:** Nenner sind **nur Anwende-Versuche**. Ein `reject` wendet per Definition nichts an — es als gescheiterte Re-Validierung zu zählen wäre gelogen. Erfolg = `pipeline_success` **und** `errors_after < errors_before` (echte Fehlerreduktion, nicht „Validator grün").
  - **AK2-Quote (`accepted_unchanged_rate`):** nur `approve` zählt als „KI lag richtig". `modify` heißt, der Mensch **musste** korrigieren; `reject` heißt unbrauchbar.
  - **Bearbeitungszeit:** `proposal.created_at → review.decided_at`. Entscheidungen unter **60 s** sind Skript-Fixtures (kein Mensch liest in 0,06 s einen Diff) und werden **getrennt** ausgewiesen statt den Mittelwert auf ~0 zu ziehen. **Ehrliche Grenze, im Flag benannt:** ein Fixture, das per Skript Tage nach der Erzeugung entschieden wurde (`2b5ee9f9`), ist so **nicht** von einer echten Entscheidung zu trennen. Median wird neben dem Mittelwert ausgewiesen, weil bei n=3 ein Ausreißer alles dominiert.
- **Verifikation (echter Flask-Routing-Stack gegen die echte SQLite-DB, `GET /api/dashboard/metrics` → HTTP 200):** Jede Zahl gegen die DB per Hand gegengerechnet.
  - **Entscheidungen:** 6 gesamt = 2 approve / 1 reject / 3 modify → **Approval 33,3 % · Modify 50 % · Reject 16,7 %**. `proposals_total=9`, `proposals_open=3`.
  - **`avg_confidence=0.6944`** = (0.775+0.8+0.8+0.8+0.775+0.775+0.775+0.0+0.75)/9 — formelgenau.
  - **Revalidation:** `attempts=2, success=2, rate=1.0, untrusted=2` — die zwei belastbaren Läufe sind genau die mit echten Zahlen (2→0 und 1→0); die zwei Pre-AP3.3d-Fälle sind ausgenommen; die zwei Reviews ganz ohne `revalidation_result` (approve vor der Apply-Verdrahtung + reject) tauchen korrekt **gar nicht** im Nenner auf.
  - **Tokens/Kosten:** 1 089 583 Prompt + 24 115 Completion = **1 113 698 Tokens**, **$5,5685** über 69 `agent_runs` — Summen stimmen mit der Gruppierung direkt auf der DB überein.
  - **Fehlerarten:** EMPTY_FIELD 3 · DEMAND_ARTICLE_IDS 2 · WORK_ITEM_CONFIGS_COMPLETENESS 2 · UNIQUE_IDS 1 · **DUPLICATE_ID 1 mit `legacy_label: true`** — das ist exakt der bekannte AP3.6-Mislabel (`2b5ee9f9`, zielt auf `relDensityMin`). Der Flag greift also am realen Fall.
  - **Konfidenz-Verteilung:** 1 / 0 / 0 / 5 / 3 über die fünf Bänder (Summe 9 ✓).
  - **Kalibrierung — der wichtige, unbequeme Befund:** Band 0.6–0.8 → 3 Entscheidungen, Accept-Rate **33 %**; Band 0.8–1.0 → 3 Entscheidungen, Accept-Rate **33 %**. Die Kurve ist **flach**: eine hohe Konfidenz sagt derzeit **nichts** darüber voraus, ob der Mensch den Wert unverändert übernimmt. Das ist **kein Messergebnis, sondern konstruktionsbedingt** — 5 der 6 entschiedenen Vorschläge tragen die alte Formel (Mittelterm `schema_valid` ≡ 1, Score kollabiert auf ~0,775), und **`value_grounded` ist bei ALLEN entschiedenen Zeilen `NULL`**. Die Trennschärfe, die AP4.5 hergestellt hat, existiert bislang in **keiner einzigen entschiedenen** Zeile — sie steckt nur in den 3 offenen Vorschlägen (0.775 / 0.75 / 0.0).
  - **Konsistenz + Regression:** `proposals_open` (3) = Länge von `open_reviews` (3) = Länge von `GET /api/review/proposals` (3). Der Review-Endpunkt antwortet unverändert HTTP 200. Payload ist valides UTF-8 (5 593 Bytes); Umlaute und Gedankenstriche überstehen den Round-Trip.
- **Konsequenz für die DoD von M6 (ehrlich):** Die Kalibrierung ist **technisch vollständig implementiert und live berechnet**, aber **inhaltlich noch nicht aussagekräftig** — nicht wegen eines Fehlers im Dashboard, sondern weil es noch keine entschiedenen Vorschläge mit der neuen Formel gibt. Sie wird in dem Moment aussagekräftig, in dem Entscheidungen auf AP4.5-bewerteten Vorschlägen fallen (die 3 offenen liefern die erste Streuung) bzw. mit der **Baseline-Messung** (AK2), die ohnehin die Kalibrierungskurve als Nebenprodukt abwirft.
- **Open / next:** **AP6.2** — Dashboard-UI (`demo/ui/dashboard.html`, `ui/scripts/dashboard.js`, CSS): KPI-Karten, zwei selbstgebaute SVG-Diagramme (Fehlerarten + Konfidenz-Verteilung), Tabelle der offenen Reviews mit Deep-Link ins Board, Warnbanner aus `data_quality`. Dazu: den Sidebar-Eintrag „Dashboard" von „bald" auf aktiv schalten (`shell.js`) und **`ui/staticwebapp.config.json` um eine `/dashboard.html`-Route ergänzen** — sonst schluckt der SWA-Fallback die Seite. **Chart-Entscheidung des Nutzers: selbstgebautes SVG, keine neue Abhängigkeit** — zusätzlich technisch bestätigt, denn die CSP in `web_server.py` (`script-src 'self'`) würde ein CDN-Chart.js ohnehin blocken. Danach **AP6.3** (getrennte Input-/Output-Preise im Kostenmodell).

---

### 2026-07-12 — AP6.2 Dashboard-UI (Seite, Charts, Sidebar, SWA-Route)
- **Status:** done. Zweites Sub-Paket von AP6. Rein additiv, kein Backend angefasst (AP6.1 liefert bereits alles), kein Schema, keine Migration.
- **Changed files:** neu `demo/ui/dashboard.html`, neu `demo/ui/scripts/dashboard.js`; `demo/ui/css/styles.css` (+203 Zeilen, `db-`-Präfix, ans Ende angehängt); `demo/ui/scripts/shell.js` (Dashboard-Eintrag von „bald" auf aktiv, `PAGE`-Erkennung erweitert); `demo/ui/staticwebapp.config.json` (Route + Fallback-Ausnahme für `/dashboard.html`).
- **`staticwebapp.config.json` war nicht optional:** ohne eigene Route **und** ohne Eintrag in `navigationFallback.exclude` hätte der SWA-Fallback `/dashboard.html` auf `index.html` umgeschrieben — die Seite wäre lokal gelaufen und im Azure-Deployment still verschwunden. Beides ergänzt.

#### Charts: selbst gebautes SVG (Nutzer-Entscheidung, technisch bestätigt)
Alle drei Diagramme sind **einserieg** (Magnitude je Kategorie) — sie brauchen genau **eine** Farbe, keine Legende und keine Kategorial-Palette. Chart.js hätte ~200 KB Abhängigkeit für Funktionen gebracht, von denen hier keine gebraucht wird. **Zusätzlich technisch bestätigt:** die CSP in `web_server.py` (`script-src 'self'`) hätte ein CDN-Chart.js ohnehin geblockt — die Entscheidung war also nicht nur Geschmack. Präzedenzfall: AP4.7 (bewusst kein Highlight.js).
- **Farben nachgerechnet, nicht geschätzt** (Kontrast gegen die Kartenfläche `#171922`): Balken `#818cf8` → **5,87:1**, Status „Alt-Label" `#eab308` → **9,14:1** (Marken brauchen ≥ 3:1); Gitter `#2e3036` → 1,33:1, was so gewollt ist (ein Gitter soll zurücktreten).
- **Gelb trägt nie allein Bedeutung:** der Alt-Label-Balken bekommt zusätzlich die Textmarke „⚠ Alt-Label (Zähl-Heuristik)". Farbe allein ist für Farbfehlsichtige kein Kanal.
- **Leere Kalibrierungs-Bänder bekommen KEINEN Nullbalken**, sondern eine Grundlinien-Marke plus sichtbares `n=0`. „Keine Daten" und „0 % angenommen" sind verschiedene Aussagen; ein Nullbalken würde sie verwechselbar machen.

#### Aufbau der Seite (Ehrlichkeit vor Optik)
1. **„Belastbarkeit der Zahlen" steht GANZ OBEN und ausgeklappt** — alle 4 Warnungen sichtbar, die 4 Info-Hinweise eingeklappt. Begründung im Code: eine Kennzahl mit einem Vorbehalt, den man erst aufklappen muss, wird als Kennzahl **ohne** Vorbehalt gelesen.
2. **Heldenzahl + Meter: die AK2-Quote gegen ihre Zielmarke** (≥ 80 %). Genau eine Heldenzahl pro Ansicht — es ist die Zahl, an der das Projekt gemessen wird. Aktuell **33,3 %**, Zielmarke sichtbar **nicht erreicht**.
3. **9 KPI-Kacheln.** Die Vorbehalte stehen **an der jeweiligen Kennzahl**, nicht nur unten: die Revalidierungs-Kachel nennt „2 ausgenommen", die Bearbeitungszeit-Kachel „3 Fixture(s) ausgenommen".
4. **Entscheidungsquoten**, **Fehlerarten**, **Konfidenz-Verteilung**, **Kalibrierung**, **Tabelle offener Reviews** mit Deep-Link in die Board-Detailansicht.
5. **Die Flach-Warnung an der Kalibrierungskurve wird automatisch erkannt** (`calibrationWarning`): streuen die belegten Bänder um < 5 Prozentpunkte, erscheint der Hinweis, dass die Kurve konstruktionsbedingt flach ist. Sie verschwindet von selbst, sobald echte Streuung da ist — sie ist kein hartkodierter Text.

#### Verifikation (kein Headless-Browser vorhanden → wie in AP4.3.2b: die ECHTE `dashboard.js` in Node gegen die ECHTE API-Antwort)
- **DOM-Prüfung, 16/16 bestanden:** Heldenzahl rendert `33.3 %` (= approve 2/6, formelgenau); Zielmarke als `below` / „nicht erreicht" markiert; 4 Warnungen ausgeklappt + 4 Infos eingeklappt; 15 Balkengruppen (5+5+5); Alt-Label als **Textmarke** UND in Status-Gelb; Flach-Warnung automatisch gegriffen; 3 leere Bänder als `n=0` statt Nullbalken; 3 Deep-Links ins Board; `value_grounded=0` als „nicht belegt" ausgewiesen.
- **Geometrie-Prüfung, 15/15 bestanden** (das, was ein DOM-Test NICHT sieht): kein `<text>` läuft links/rechts/unten aus der viewBox, kein Balken mit negativer Koordinate, alle Zähl-Ticks ganzzahlig, Prozentachse 0–100 %.
- **Zwei echte Layoutfehler dabei gefunden und behoben** — beide hätte kein DOM-Test gefangen:
  1. **Label-Überlauf:** `WORK_ITEM_CONFIGS_COMPLETENESS` sind 29 Zeichen ≈ 210 px bei 12 px Schrift, die linke Beschriftungsspalte bot aber nur 198 px — das Label wäre aus dem SVG gelaufen. **Behoben durch die richtige Form**, nicht durch Kürzen: das Label steht jetzt **über** dem Balken. Ein Label, das nicht passt, wird nicht abgeschnitten; es bekommt eine Form, in der es passt.
  2. **Halbe Vorschläge auf der Achse:** bei Maximum 3 erzeugte die Achse die Ticks `0 / 1.5 / 3`. Neu `niceMaxCount()` — rundet auf gerade Zahlen (3 → 4, Ticks 0/2/4), damit der Mittel-Tick ganzzahlig ist.
  3. (klein) Der `0`-Tick saß mittig auf `x=2` und ragte 1 px links aus der viewBox → `padL = 6`.
- **Ein echter Syntaxfehler gefunden**, weil die echte Datei ausgeführt wurde statt nachgebaut: eine überzählige Klammer im verschachtelten Template-Literal der Kalibrierungs-Karte. Behoben, indem der Callout in eine eigene Funktion `calibrationWarning()` gezogen wurde (kein verschachteltes Template mehr).
- **Live gegen den echten Flask-Server (Port 8000):** `/`, `/review.html`, **`/dashboard.html`**, `/scripts/dashboard.js`, `/scripts/shell.js`, `/css/styles.css`, `/api/dashboard/metrics`, `/api/review/proposals` → **alle HTTP 200**. Die Dashboard-Seite lädt `dashboard.js`; `shell.js` liefert `href="dashboard.html"` und **kein** `sb-soon` mehr; das ausgelieferte CSS enthält den `db-`-Block; die API liefert `accepted_unchanged_rate=0.3333`, 3 offene Reviews, 8 Flags. **Keine Regression** an Chat und Review Board.
- **Open / next:** **AP6.3** — Kostenmodell mit getrennten Input-/Output-Preisen (die pauschale `_COST_PER_1K_TOKENS = 0.005` überschätzt die Kosten grob um Faktor 2, weil 950k der 1,08 Mio. Tokens Prompt-Tokens sind). Danach ist AP6 abgeschlossen; für die M6-DoD bleibt der inhaltliche (nicht technische) Vorbehalt zur Kalibrierung bestehen — siehe AP6.1.

---

### 2026-07-12 — AP6.3 Kostenmodell (Input/Output getrennt) — **AP6 code-seitig abgeschlossen**
- **Status:** done. Drittes und letztes Sub-Paket von AP6.
- **Changed files:** neu `demo/cost_model.py`; `demo/web_server.py` (Pauschal-Konstante raus, `estimate_cost` rein); `demo/smart-planning/runtime/generate_correction_llm.py` (dieselbe Umstellung); `demo/routes/dashboard.py` (Kosten werden abgeleitet statt aufsummiert, `pricing`-Block in der Antwort); `demo/ui/scripts/dashboard.js` (Preise auf der Kosten-Kachel). **Datenkorrektur:** 63 von 69 `agent_runs`-Zeilen bekamen `cost_estimate` neu berechnet (siehe unten).
- **Der Fehler, der behoben wurde:** AP2.5 verrechnete **einen** Mischpreis pro 1K Tokens für Input und Output gleichermaßen (`_COST_PER_1K_TOKENS = 0.005`). LLM-Anbieter berechnen Output aber ein Vielfaches des Inputs (gpt-4o: **$0,0025/1K Input, $0,010/1K Output — Faktor 4**), und der Token-Mix dieses Systems ist extrem input-lastig: **950k von 1,08 Mio. Tokens sind Prompt-Tokens**, weil `generate_correction_llm` ganze Snapshot-Ausschnitte in den Prompt schiebt. Die Pauschale bepreiste also genau die billigen Tokens zu teuer.
- **Gemessene Auswirkung:** Gesamtkosten **$5,5685 → $2,9651**. Die Pauschale hat um **Faktor 1,88** überschätzt — die in AP6.1 vorhergesagte Größenordnung („grob Faktor 2") bestätigt sich an den echten Daten.
- **Und erst jetzt ist die Zahl aussagekräftig:** `generate_correction_llm` = **$2,5122 von $2,9651 = 85 % der Gesamtkosten** (35 Läufe, 950 090 Input- / 13 694 Output-Tokens). Das ist der Hebel, falls je optimiert werden muss — die Pauschale hat diese Verteilung verdeckt, weil sie den Output künstlich aufgewertet hat.
- **Entwurfsentscheidungen:**
  - **Eine Quelle der Wahrheit.** `cost_model.estimate_cost()` ist die einzige Stelle, die Kosten rechnet; beide bisherigen Rechenstellen rufen sie auf. Die alte Konstante existiert im Code nicht mehr (nur noch als Doku im Docstring).
  - **Preise sind eine ANNAHME, keine Abrechnung** — Listenpreise, ohne Azure-Rabatte, Batch-Preise oder Cached-Input. Im Modul-Docstring und im `COST_IS_ESTIMATE`-Flag ausdrücklich so benannt. Aussagekräftig für den Vergleich („welcher Agent verbrennt das Budget?"), nicht für die Buchhaltung.
  - **Ohne Codeänderung überschreibbar:** `COST_PER_1K_INPUT` / `COST_PER_1K_OUTPUT` als Env-Variablen, **pro Richtung** — wer nur den Output-Preis setzt, behält den Input-Preis aus der Tabelle.
  - **Unbekanntes Modell kostet nicht still 0:** Fallback auf gpt-4o-Preise **plus** `known_model: false` in der Antwort, damit die Annahme sichtbar wird.
  - **„Keine Tokens" ist nicht „$0.00":** `estimate_cost(None, None)` liefert `None`. Die 6 Läufe ohne Token-Zahlen (vor AP2.5) bleiben auf `NULL` und werden nicht als kostenlos ausgewiesen.
  - **Das Dashboard LEITET die Kosten aus den Tokens ab**, statt die Spalte `cost_estimate` aufzusummieren. Tokens sind die Rohtatsache; Kosten sind immer nur eine Interpretation davon. Würde man die gespeicherte Spalte summieren, mischte man Zeilen, die unter verschiedenen Preisannahmen geschrieben wurden — die Gesamtsumme hinge dann still davon ab, **wann** eine Zeile entstand.
  - **Die Preise stehen in der API-Antwort (`pricing`) und auf der Kosten-Kachel.** Eine Kostenzahl, deren Preise nicht dabeistehen, ist für den Leser nicht überprüfbar — und eine ungeprüfte Kostenzahl wird geglaubt.
- **Datenkorrektur (kein Raten):** Die 63 Zeilen mit gespeicherten Tokens wurden neu bepreist; `tokens_prompt`/`tokens_completion` blieben unangetastet. Weil die Tokens die Rohdaten sind, ist die Neuberechnung **exakt und reproduzierbar**, keine Schätzung. Vorher als Dry-Run gefahren und gegengerechnet, dann angewendet. DB-Summe danach: **$2,9651** über 69 Läufe, 6 davon weiterhin `NULL`.
- **Verifikation:**
  - **Einheitentest `cost_model`:** 1000 Input → $0,0025 · 1000 Output → $0,0100 (Faktor 4, genau der Punkt) · 1000+1000 → $0,0125 · keine Tokens → `None` (nicht $0.00) · Env-Override nur für Output lässt den Input-Preis aus der Tabelle stehen · unbekanntes Modell → Fallback **und** `known_model=False`.
  - **Endpunkt:** `cost_estimate_usd = 2.9651`, `pricing = {model: gpt-4o, input: 0.0025, output: 0.01, known_model: true, overridden_by_env: false}`.
  - **Importpfade:** `web_server` importiert `cost_model` sauber; das **Runtime-Tool erreicht `cost_model` auf demselben `sys.path`, den es schon für `from db import repository` nutzt** (im Subprozess geprüft, nicht angenommen).
  - **Keine UI-Regression:** 16/16 DOM- und 15/15 Geometrie-Prüfungen weiterhin grün; die Kosten-Kachel zeigt jetzt „gpt-4o: $0.0025 in / $0.0100 out je 1K".
- **Damit ist AP6 code-seitig abgeschlossen** (AP6.1 Metrik-Backend · AP6.2 Dashboard-UI · AP6.3 Kostenmodell). Für die **M6-DoD** bleibt der inhaltliche — nicht technische — Vorbehalt zur **Kalibrierung** bestehen: sie wird live berechnet und angezeigt, ist aber flach, weil alle 6 entschiedenen Vorschläge noch die alte Konfidenz-Formel tragen (siehe AP6.1).
- **Open / next:** **AP6.4** — Überarbeitung des Dashboards nach dem ersten Nutzer-Review (Reihenfolge/Erstblick, Zeitfilter mit Navigation, Balkendiagramm „wann wurde korrigiert", Vorbehalte an die Kennzahl statt als Textblock oben). Vom Nutzer angefordert; wird separat geschnitten.

---

### 2026-07-12 — AP6.4 Dashboard-Überarbeitung nach dem ersten Nutzer-Review (Zeitfilter, Reihenfolge, Zeitreihe)
- **Status:** done (AP6.4a Backend + AP6.4b Frontend).
- **Changed files:** `demo/routes/dashboard.py` (Zeitfilter, Zeitreihe, `range`-Block), `demo/db/repository.py` (`created_at` auf den Agent-Läufen im Datenabzug — eine Zeile), `demo/ui/scripts/dashboard.js` (neu geschrieben), `demo/ui/css/styles.css` (+144 Zeilen). Kein Schema, keine Migration.
- **Auslöser (Nutzer, nach dem ersten Blick auf die Seite):** (1) „nicht mit dieser Belastbarkeit-Zahlen starten — zu viel Text für den ersten Blick", (2) Zeitfilter mit Voreinstellungen (Woche/Monat/Jahr) und Vor-/Zurück-Navigation, der **für die ganze Seite** gilt, (3) ein Balkendiagramm, das zeigt, **wann** korrigiert wurde, mit dem Tag am Balken.

#### AP6.4a — Backend: die Unterscheidung, an der der ganze Filter hängt: **FLUSS vs. BESTAND**
Der Filter darf nicht auf alles wirken. **Fluss** sind Ereignisse *in* einem Zeitraum (erzeugte Vorschläge, Entscheidungen, Tokens, Kosten, Validierungen) — die werden gefiltert. **Bestand** ist der Zustand *jetzt* (welche Vorschläge offen sind) — der wird **nicht** gefiltert. Filterte man den Bestand mit, zeigte „letzte Woche" plötzlich **0 offene Reviews**, während drei Vorschläge auf einen Menschen warten. Ein Rückstand hört nicht auf zu existieren, weil man den Datumsfilter verengt. Genau dieser Fall ist als Test verankert.
- **Jede Entität wird nach ihrem EIGENEN Zeitstempel gefiltert** (Vorschlag → `created_at`, Entscheidung → `decided_at`, Lauf → `created_at`). Alles andere wäre mehrdeutig: ein im Juni erzeugter, im Juli entschiedener Vorschlag fiele sonst je nach Kennzahl mal rein und mal raus.
- **`GET /api/dashboard/metrics`** nimmt jetzt `?preset=week|month|year|all`, `?from=&to=` (`to` inklusive) und `?granularity=day|week|month`. Default: letzte 30 Tage, Tagesraster.
- **`preset=all` wird aus den DATEN aufgelöst**, nicht aus der Unix-Epoche. Erste Fassung startete bei 1970 → 55 Jahre Spanne → Auto-Vergröberung → **vier Tage echter Daten in EINEM Monatsbalken**. Behoben: `earliest_timestamp(data)` liefert den ältesten Datensatz; „alles" spannt jetzt 08.–12.07. über fünf Tagesbalken.
- **Auto-Vergröberung statt unlesbarer Charts:** über `MAX_BUCKETS = 92` wird `day → week → month` vergröbert — und **sagt es** (`GRANULARITY_COARSENED`). Ein Jahr in Tagen wären 365 Balken à 2 px.
- **Leere Buckets werden erzeugt**, nicht übersprungen: ein Tag ohne Entscheidung muss als Lücke sichtbar sein, sonst sieht die Aktivität durchgehend aus.
- **Müllwerte führen nie zu HTTP 500:** ungültiges Datum/Preset/Granularität fällt auf den Default zurück und meldet das via `RANGE_INPUT_IGNORED`; verdrehte Grenzen werden getauscht statt ein leeres Fenster zu liefern.
- **`RANGE_EXCLUDES_DATA`** nennt die Zahl der Datensätze außerhalb des Fensters — ein enger Filter kann so nie mit einem leeren System verwechselt werden.

#### AP6.4b — Frontend
- **Neue Reihenfolge:** Filterleiste → **Zahlen** (Heldenzahl + 9 Kacheln) → Charts → offene Reviews → **Belastbarkeit ganz unten, eingeklappt**. Die Vorbehalte sind nicht verschwunden: sie hängen jetzt als **Warnsymbol an der Kennzahl, die sie betreffen**, und öffnen sich per Klick. Das ist auch die ehrlichere Stelle — die Warnung steht dort, wo die Zahl gelesen wird, statt in einem Textblock, den niemand liest.
- **Filterleiste:** eine Reihe über allem, was sie einschränkt (nie ein Filter pro Chart). Vor-/Zurück verschiebt das Fenster um **seine eigene Länge** und macht daraus ein konkretes Fenster — sonst spränge „Woche" nach einem Klick auf „zurück" wieder auf „die letzten 7 Tage ab heute" und nichts bewegte sich. **Der Filter lebt in der URL**, ein Reload oder ein geteilter Link behält den Zeitraum. Angezeigt wird der vom **Server aufgelöste** Zeitraum, nicht der angefragte — wenn der Server vergröbert oder korrigiert hat, steht hier, was wirklich gerechnet wurde.
- **Neue Zeitreihe „Wann wurde entschieden?":** gestapelte Säulen je Tag/Woche/Monat, aufgeteilt nach Entscheidungstyp. Verankert auf `decided_at` — gefragt ist, wann der **Mensch** gehandelt hat, nicht wann die KI den Vorschlag erzeugte.
- **Erste kategoriale Palette des Projekts (3 Serien) — validiert, nicht geschätzt:** Die naheliegenden Board-Farben (`#22c55e`/`#818cf8`/`#ef4444`) **fielen durch** das Helligkeitsband für dunkle Flächen (L 0,72 bzw. 0,68 > Obergrenze 0,67) — Grün hätte lauter geschrien als Rot. Auf dunklere Stufen **derselben Farbfamilien** gesnappt: **`#16a34a` freigegeben · `#6366f1` korrigiert · `#ef4444` verworfen** → alle vier Prüfungen PASS (Helligkeitsband, Chroma, CVD-Trennung ΔE 95 bei Ziel ≥ 12, Kontrast ≥ 3:1). Die Farb**familien** bleiben die des Review Boards, wer dort „grün = freigegeben" gelernt hat, liest das Chart sofort; nur die Helligkeit ist an die Rolle angepasst (im Board sind es Textfarben auf getönter Fläche, hier Vollflächen). Legende ist ab 2 Serien Pflicht und vorhanden.
- **2 px Flächen-Lücke zwischen den Stapelsegmenten** (nie eine Kontur drumherum); nur das oberste Segment trägt das gerundete Datenende.

#### Verifikation
- **Backend, 18/18** (echter Flask-Stack, echte DB): Default = letzte 30 Tage · **der kritische Fall: Fenster „nur 12.07." → 0 Entscheidungen, 0 Vorschläge (Fluss), aber weiterhin 3 offene Reviews und 3 Tabellenzeilen (Bestand)** · Zeitreihe trifft die Realität (10.07.: 2 approve + 1 modify + 1 reject; 11.07.: 2 modify; 12.07.: leerer, aber vorhandener Balken) und summiert auf alle 6 Entscheidungen · alle 4 Presets · Jahr+Tage wird vergröbert und meldet es · Müllwerte → HTTP 200 mit Meldung · Kosten folgen dem Filter.
- **Frontend, 21/21** (echte `dashboard.js` in Node gegen den **echten laufenden Server**): Reihenfolge belegt (Filter < Heldenzahl < Kacheln < Belastbarkeit) · Belastbarkeits-Block ist ein `<details>` · **11 Vorbehalt-Symbole an den Kennzahlen** · alle Filterelemente vorhanden und aktives Preset markiert · Filter steht in der URL · Legende + validierte Farben im Chart · **Tag steht als Beschriftung am Balken** und im Tooltip.
- **Geometrie, 20/20 in ALLEN vier Zeiträumen** (Woche 8 Balken · Monat 31 · Jahr vergröbert · Alles 5): kein Label läuft aus der viewBox, kein negativer Balken, Zähl-Ticks ganzzahlig — **plus neu: keine Überlappung benachbarter Datumsbeschriftungen** (der Risikofall bei 31 Tagesbalken; Beschriftung wird ausgedünnt, der Wert bleibt am Balken und im Tooltip lesbar).
- **Ein Testfehler dabei gefunden und behoben (im Test, nicht im Produkt):** die Prüfung „Zähl-Ticks müssen ganzzahlig sein" hielt die Datumsbeschriftung `05.07.` für die Zahl `05.07`. Regex geschärft.
- **Keine Regression:** `/`, `/review.html`, `/dashboard.html`, alle Skripte, `/api/review/proposals`, `/api/dashboard/metrics` (auch mit `preset=all` und mit Müllparametern) → alle HTTP 200.
- **Open / next:** Der Zeitfilter deckt Presets + Vor/Zurück + Granularität ab; ein freier Datumswähler (Kalender-Popup) ist bewusst **nicht** gebaut — `?from=&to=` wird vom Backend bereits unterstützt, die UI reicht sie nur noch nicht ein. Nachrüsten, wenn der Bedarf real wird.

---

## Open Items / Backlog (Stand: 2026-07-11 - 13:33)

### Erledigt seit letzter Aktualisierung
- **[erledigt]** AP3.6 — Fehler-Klassifizierung: Ursache war die Zähl-Heuristik in `identify_snapshot.py` (NICHT `identify_error_llm`; value-Modus + >1 Treffer → fälschlich DUPLICATE_ID). Behoben: tag-basierter `error_type` aus dem `[validate_*]`-Tag. Siehe Log **AP3.6a** (Diagnose), **AP3.6b-1** (`tag_error_type` additiv erzeugt), **AP3.6b-2** (als maßgeblicher `error_type` verankert, `legacy_error_type` daneben behalten).
- **[erledigt]** AP3.5 — Identitäts-Guard: Metadaten verankert (**AP3.5a**: `correction_kind`, `target_entity_type`, `target_entity_id`, `identity_check_supported`; Soll-Identität aus `snapshot-data` gelesen) und Guard im Anwenden-Pfad scharf (**AP3.5b**: Block bei Identitäts-Abweichung/verschwundener Position, HTTP 409, nichts angewendet). **AP3.5c-Inhalte (Altdaten-Behandlung, Sonderentitäten-Skip) sind in AP3.5b miterledigt** — Nachweise (c) Sonderentität übersprungen und (d) Altdaten ohne AP3.5a-Felder übersprungen.
- **[erledigt]** AP3.3c — echter LLM-Vorschlag erzeugt (Log **AP3.3c**, in **AP3.6b-2** durch korrekt etikettierten `iteration-5` abgelöst). Nur die Fallentscheidung bleibt offen (siehe unten).
- **[geschlossen/hinfällig]** Modellvergleich (GPT-4o-mini vs. stärkeres Modell): entfällt in dieser Form — verifiziert, dass bereits **gpt-4o** läuft (`.env AZURE_OPENAI_DEPLOYMENT=gpt-4o`, `response.model=gpt-4o-2024-11-20`), nicht 4o-mini. Ein A/B gegen 4o-mini war die falsche Prämisse.

## Open Items / Backlog (Stand: 2026-07-11)

**Status Phase 1 (AP1–AP4):** Code-seitig abgeschlossen; AK3 (Human-in-the-Loop) am
2026-07-11 end-to-end live nachgewiesen (siehe Log LIVE-ENTSCHEIDUNG). Robustheits-Audit
(Codex-Fixes) durch. Es bleiben **2 echte Blocker** bis zum sauberen Phase-1-Abschluss:
frische Vorschläge reproduzierbar erzeugen → Baseline messen (AK2 ≥80 %). Alles Übrige ist
Tech-Debt (tracken, nicht blockierend) oder Phase 2 (AP5–AP7 + Evaluation).

### Erledigt seit letzter Aktualisierung
- **[erledigt]** AP3.6 — Fehler-Klassifizierung: Ursache war die Zähl-Heuristik in `identify_snapshot.py` (NICHT `identify_error_llm`; value-Modus + >1 Treffer → fälschlich DUPLICATE_ID). Behoben: tag-basierter `error_type` aus dem `[validate_*]`-Tag. Siehe Log **AP3.6a/AP3.6b-1/AP3.6b-2** (`legacy_error_type` daneben behalten).
- **[erledigt]** AP3.5 — Identitäts-Guard: Metadaten verankert (**AP3.5a**: `correction_kind`, `target_entity_type`, `target_entity_id`, `identity_check_supported`) und Guard im Anwenden-Pfad scharf (**AP3.5b**: Block bei Identitäts-Abweichung/verschwundener Position, HTTP 409). AP3.5c-Inhalte (Altdaten-/Sonderentitäten-Skip) in AP3.5b miterledigt.
- **[erledigt]** AP3.3c — echter LLM-Vorschlag erzeugt (in AP3.6b-2 durch korrekt etikettierten `iteration-5` abgelöst).
- **[erledigt]** Fallentscheidung Proposal **ec96832c-…__iteration-5**: am 2026-07-11 als **MODIFY** entschieden und angewendet (BA01 = 30/1/`P`), `errors_before=2 → errors_after=0`. Erste echte HitL-Entscheidung. Siehe Log **LIVE-ENTSCHEIDUNG**.
- **[erledigt]** Fall C der Diff-Ansicht (AP4.2) — `additional_updates` als eigener „Zusatz-Updates"-Diff in der Detailansicht. **Korrektur der früheren Annahme:** die Originalstruktur je Eintrag (`target_path`, `current_value`, `new_value`) kommt byte-/strukturgetreu übers `evidence`-Alias an — kein Backend-/Schema-Eingriff nötig, nur `review.js`. Bei `evidence=[]` kein Block. Verifiziert am Wegwerf + echtem Detail-Endpunkt.
- **[erledigt]** `_validate_now` gegen Netzfehler gekapselt — ConnectionError/Timeout an beiden Validierungsstellen liefern jetzt geordneten HTTP 502 mit persistiertem `revalidation_result` (`errors_before=None`) statt HTTP 500; Entscheidung bleibt committed, kein Retry. Verifiziert am Wegwerf (approve/ConnectionError + modify/Timeout). Nur `review.py`.
- **[erledigt]** action-Guard in `prepare_proposal_for_apply` — Modify nur für `update_field`/`add_to_array`; `remove_from_array` + Modify und `manual_intervention_required` werden mit HTTP 422 (`applied=false`) blockiert, bevor Daten mutiert werden. Verhindert stilles Verpuffen des Menschenwerts bzw. falsches `applied=true`. Verifiziert am Wegwerf. `apply_prep.py` + `review.py`.
- **[geschlossen/hinfällig]** Modellvergleich (GPT-4o-mini vs. stärkeres Modell): entfällt — verifiziert, dass bereits **gpt-4o** läuft (`response.model=gpt-4o-2024-11-20`), nicht 4o-mini.

### Offen — Phase-1-Blocker (bis zum sauberen Abschluss)
- **[erledigt]** ~~Kein `pending_review`-Vorschlag mehr~~ — Rezept hergestellt und gefahren: aktuell **3 offene Vorschläge** (`7ab03beb`, `1d45ddff`, `1ef11903`), drei verschiedene Fehlerarten, deutsche Begründungen. Siehe Log „Vorschlagserzeugung Schritte 1–3" (Rezept) und „AP4.4".
- **[erledigt]** ~~Deterministisches Konfidenz-Signal~~ — **AP4.5**: `schema_valid` (immer 1, totes Gewicht) durch `value_grounded` ersetzt (deterministisch: ist der Wert aus den Daten belegbar oder erfunden?). Score streut jetzt 0.0 / 0.45 / 0.74 / 0.775; der Fall, in dem die KI falsch lag, ist der niedrigste. Inkl. KOLLISIONS-Erkennung, DB-Spalten + Anzeige im Board. Formel in `PT4_PLAN.md` aktualisiert.
- **[BLOCKER, AK2 — vertagt, Plan steht]** Baseline-Messung. **Design und Entscheidungen sind fertig** (siehe Log-Eintrag „Baseline-Messung (AK2)"): Fehler **selbst injizieren** → Originalwert = Ground Truth → Korrektheit objektiv messbar (nicht nur „Validator grün", was nachweislich ein False-Green-Kriterium ist). **Kriterium: hybrid** (eindeutige Fehler → exakter Ground-Truth-Vergleich; `UNIQUE_IDS` → Validator grün + kein neues Duplikat). **Umfang: 10 Fälle** (5 Fehlerarten × 2). **Blockiert durch:** es gibt kein Lösch-Tool — jeder Fall hinterlässt einen dauerhaften Snapshot auf dem Testserver (11 Stück). Nutzer hat die Ausführung deshalb vorerst gestoppt. Zum Fahren fehlt nur die Freigabe bzw. ein Aufräumweg.

### Offen — Tech-Debt (nicht blockierend)
- **[offen, fachlich]** BA01-Werte für Artikel 124211 bei **Stammdatenzugriff gegenprüfen**: die Server-Validierung belegt nur Key-Vollständigkeit (2 → 0), nicht die Richtigkeit von `rampUpTime=30 / netTimeFactor=1 / sequence="P"`. Herleitung war statistisch (16/16 Himbeer-Grundstoffe der Abteilung = 30/1; `P` Modus mit 11/16), nicht aus dem Stammsatz.
- **[erledigt]** ~~`confidence_rationale` nur in der JSON~~ — in AP4.5 zusammen mit `value_grounded`/`value_grounded_reason` in die DB (Migration `1aeb3778e9cb`) und in die Detailansicht („Woher kommt die Konfidenz?") gebracht.
- **[offen, klein]** `value_grounded` deckt `add_to_array` und verschachtelte Pfade (`equipment[i].predecessors[0]`) noch nicht gezielt ab — dort greift die generische Regel und liefert konservativ `0` (drückt die Konfidenz, blockiert aber nichts). Bei realen Fällen nachschärfen.
- **[offen, UI, klein]** `review.js` kennt HTTP **422** noch nicht (action-nicht-modify-fähig, neu aus dem action-Guard). Kann aktuell nicht eintreten (alle realen Proposals sind `update_field`), daher rein vorsorglich: 422 als eigene Klartext-Meldung behandeln, sonst generischer Fehlerzweig. Analog zur 409-A/409-B/502/500-Unterscheidung.
- **[offen, an Baseline gekoppelt]** AP3.6c (neu gefasst — alte Prämisse „tote Heuristik löschen" widerlegt): die Zähl-Heuristik in `identify_snapshot.py` lebt weiter als `legacy_error_type` UND als **Fallback bei fehlendem `[validate_*]`-Tag** (`generate_correction_llm.py:513`). Offene Frage ist das Fallback-Verhalten, keine Löschung: Wie oft fehlt das Tag real? Im Rahmen der Baseline-Messung verifizieren; falls das Tag zuverlässig da ist, die falsche `DUPLICATE_ID`-Rateheuristik durch neutrales `UNKNOWN` ersetzen. `legacy_error_type` als Audit-Feld erhalten. Nicht vor der Messung entscheiden.
- **[offen]** Volle Identitäts-Guard-Abdeckung für Sonderentitäten (`equipment` duale ID, `worker*` unter `worker.workerId`, `packaging`) und `KIND_ADD_OBJECT` — erst wenn reale Fälle existieren; aktuell bewusst guard-skipped.
- **[offen]** Phase-3-Kennzahlen fragwürdig: Die 85-%-Auto-Fix-Rate aus der Phase-3-Doku beruht evtl. auf dem Validierungs-Bug (falsches „0 Fehler"). Nicht ungeprüft zitieren.
- **[offen, kosmetisch]** action-Semantik: Vorschlag nutzt `action: "update_field"` für eine ganze Array-Befüllung (leer → 13 Objekte); semantisch eher `add_to_array`/Array-Replace. Prüfen, ob relevant.
- **[offen]** AP6-Notiz: `revalidation_result`-Einträge aus Läufen VOR AP3.3d beim Dashboard ausschließen/markieren (falsche `errors_after=0`).

### Später — Phase 2
- **[später]** AP5 MCP, AP6 Dashboard, AP7 Memory, AP-E Evaluation — nach dem Phase-1-Abschluss (frische Vorschläge + Baseline).
- **[später, nach Baseline]** `llm-validation-fix-rules.md` überarbeiten. Bekannte Schwächen: PACKAGING-EQUIPMENT-Block ~3× dupliziert (~Z.124–203); keine Struktur-Hierarchie (Identifikation / array_context / Actions vermischt); keine Regel für „workItemConfigs vollständig, einzelnes Feld nicht ableitbar → nächstem belegbaren Nachbarn folgen" (aus 124211-Fall). NICHT vor der Baseline ändern (verschiebt sonst die AK2-Grundlinie). Als messbares Vorher/Nachher gegen Baseline durchführen.
- **[später, nach AP6]** Reload-Historie in der Review-Detailansicht. Aktuell liefert `get_proposal_as_dict()` keine `reviews`-Daten — nach einem Reload zeigt das Detail nur den Proposal-Status, nicht *was* entschieden wurde. Fix: `reviews` additiv in den Detail-Endpunkt joinen (analog AP4.1). Gehört zur Audit-/Historien-Sicht (AP6). Kein Loop-Breaker: Ergebnis ist nach dem Klick inline sichtbar.

---

### 2026-07-12 — AP5.1 MCP-Tool-Schicht über bestehender Review-Logik
- **Status:** done
- **Changed files:** `demo/mcp_connections/__init__.py`, `demo/mcp_connections/tools.py`, `demo/mcp_connections/server.py`, `demo/mcp_connections/README.md`, `demo/requirements.txt`, `docs/PROJECT_LOG.md`
- **What was done:** Sieben Repository-gestützte Tools (`get_pending_reviews`, Details, drei Entscheidungen, Snapshot-Status, Dashboard-Kennzahlen) als direkt aufrufbarer Adapter und als registrierte FastMCP-Tools umgesetzt. Entscheidungen verwenden nach Nutzerfreigabe `decide_proposal()` statt des ungeeigneten `create_review()` (dieses würde nur eine Review-Zeile schreiben und den Proposal-Status offen lassen); die MCP-Entscheidung zeichnet bewusst nur die Entscheidung auf und startet nicht die bestehende Apply-Pipeline. Snapshot-Status aggregiert die vorhandenen Repository-Reads `list_open_proposals_as_dicts()` und `get_decisions_for_snapshot()`; kein neuer DB-Code. Token-Validierung ist konzeptionell dokumentiert und für PT4 out-of-scope.
- **Verification:** Python MCP SDK 1.28.1 installiert/importiert; alle sieben erwarteten Toolnamen im FastMCP-Server registriert. Isolierte Temp-DB: Pending/Details/Approve/Reject/Modify/Snapshot/Metriken durchgestochen, danach restlos gelöscht. Read-only gegen die reale DB: `get_pending_reviews()` liefert die drei bestehenden offenen Vorschläge (`7ab03beb`, `1d45ddff`, `1ef11903`).
- **Open / next:** Kein produktiver MCP-Client und keine Tool-Authentifizierung in PT4; der Server nutzt lokal stdio. M5 hängt noch am echten ACS-Zustellnachweis aus AP5.2.

---

### 2026-07-12 — AP5.2 ACS-Notification mit Review-Deep-Link
- **Status:** partial (Implementierung und Provider-Grenze verifiziert; echter ACS-Versand mangels Konfiguration noch offen)
- **Changed files:** `demo/mcp_connections/notifier.py`, `demo/mcp_connections/README.md`, `demo/smart-planning/runtime/generate_correction_llm.py`, `demo/ui/scripts/review.js`, `demo/requirements-azure.txt`, `docs/PROJECT_LOG.md`
- **What was done:** `send_proposal_notification()` unterstützt ACS und SendGrid per lazy import; ausgewählt ist ACS. Secrets/Adressen kommen ausschließlich aus Environment/`.env`; ohne `NOTIFICATION_CHANNEL` wird mit der geforderten Info-Meldung übersprungen. `save_central_proposal_record()` ruft den Notifier direkt nach dem ersten erfolgreichen DB-Insert eines neuen `pending_review`-Proposals defensiv auf; Fehler können die Speicherung nicht abbrechen, eine idempotente Regeneration sendet nicht erneut. Mail enthält Plaintext + HTML, geforderten Betreff und `{APP_BASE_URL}/review.html?id={proposal_id}`. Die UI akzeptiert `?id=` additiv neben dem bereits vorhandenen `?proposal=`-Deep-Link.
- **Verification:** (a) echter Generator-Speicherpfad mit unset Channel: Proposal in isolierter DB gespeichert, Log `Notification skipped: NOTIFICATION_CHANNEL not set`, kein Fehler. (b) Generator-Speicherpfad mit `NOTIFICATION_CHANNEL=acs` und ACS-Testdouble: Output `Notification sent`, Empfänger/Betreff/Plaintext/HTML/Deep-Link exakt geprüft; zweiter Lauf derselben Proposal-ID erzeugt keinen zweiten Versand. (c) `?id=` lädt und rendert den angeforderten Review im echten `review.js`. Alle DB-/Datei-Fixtures gelöscht; ACS SDK 1.1.0 installiert/importiert.
- **Open / next:** Für den bindenden End-to-End-Zustellnachweis fehlen lokal noch `NOTIFICATION_CHANNEL=acs`, `ACS_CONNECTION_STRING`, `ACS_SENDER_EMAIL` und `NOTIFICATION_RECIPIENT_EMAIL` in `demo/.env` (optional `APP_BASE_URL`). Erst nach einer real zugestellten Mail mit geöffnetem Link ist AP5.2 `done` und M5 erreicht.

---

### 2026-07-12 — AP5.2-Ergänzung: realer ACS-Versand
- **Status:** partial (ACS hat den Versand erfolgreich abgeschlossen; Empfängerbestätigung des Mail-/Link-Eingangs noch offen)
- **Changed files:** `docs/PROJECT_LOG.md` (Konfiguration nur lokal in `demo/.env`, keine Secrets protokolliert)
- **What was done:** Nach vollständigem read-only Konfigurationscheck wurde genau eine reale ACS-Benachrichtigung für den weiterhin offenen Vorschlag `1ef11903-…__iteration-1` (`WORK_ITEM_CONFIGS_COMPLETENESS`) gesendet. Es wurde keine Review-Entscheidung geschrieben und kein Snapshot verändert.
- **Verification:** Der ACS-Poller endete erfolgreich mit `sent=true`, Channel `acs` und vorhandener Message-ID. Danach weiterhin 3 offene Reviews; der benachrichtigte Vorschlag bleibt `pending_review`. `ec96832c`-`snapshot-data.json` SHA-256 weiterhin `62279f61…`, iteration-5 bytegleich.
- **Open / next:** Empfänger bestätigt, dass die Mail angekommen ist und der Deep-Link den Review `1ef11903-…__iteration-1` öffnet; danach AP5.2 auf `done` und M5 auf erreicht setzen.

---

### 2026-07-12 — AP5.2 abgeschlossen / M5 erreicht
- **Status:** done
- **Changed files:** `docs/PT4_PLAN.md`, `docs/PROJECT_LOG.md`
- **What was done:** Der Nutzer hat den Eingang der real über Azure Communication Services versendeten E-Mail und den funktionierenden Deep-Link bestätigt. Der Link öffnete direkt den benachrichtigten Vorschlag `1ef11903-…__iteration-1` im Review Board; damit ist der bindende Enterprise-Fall von neuem offenen Review bis zur erreichbaren menschlichen Detailansicht end-to-end belegt. M5 wurde im Referenzplan als abgeschlossen markiert.
- **Verification:** Sichtnachweis des Nutzers: korrekter Betreff `Offener Review: 1ef11903-… / WORK_ITEM_CONFIGS_COMPLETENESS`, Snapshot und Fehlertyp im Mail-Body sowie geöffnete Review-Detailansicht mit Status `PENDING_REVIEW` und passendem Snapshot/Zielpfad. Zuvor hatte der ACS-Poller den Versand mit vorhandener Message-ID erfolgreich abgeschlossen.
- **Open / next:** AP5 ist abgeschlossen. Produktiver MCP-Client und Token-Validierung bleiben wie geplant außerhalb des PT4-Scopes.

---

### 2026-07-12 — AP5.3 Konversationeller E-Mail-Agent
- **Status:** done
- **Changed files:** `demo/agent_config.py`, `demo/agents/__init__.py`, `demo/agents/email_agent.py`, `demo/agents/orchestration_agent.py`, `demo/alembic/versions/7c4e2d9a8f10_ap5_3_add_email_drafts.py`, `demo/db/__init__.py`, `demo/db/models.py`, `demo/db/repository.py`, `demo/mcp_connections/notifier.py`, `demo/mcp_connections/server.py`, `demo/mcp_connections/tools.py`, `demo/mcp_connections/README.md`, `demo/ui/index.html`, `demo/ui/scripts/chat.js`, `demo/ui/css/styles.css`, `demo/web_server.py`, `docs/PT4_PLAN.md`, `docs/PROJECT_LOG.md`
- **What was done:** Ein dedizierter E-Mail-Agent ist als vierter Orchestrator-Agent integriert. Das Plus-Menü kann ihn explizit auswählen; natürliche E-Mail-Aufträge werden ebenfalls geroutet. Der Agent erstellt einen persistenten, sichtbaren Entwurf, übernimmt allgemeine Chat-Inhalte oder auf ausdrücklichen Fallbezug verifizierte Review-/Snapshot-Fakten samt Deep-Link, verarbeitet Änderungswünsche versioniert und sendet den exakt angezeigten Stand erst bei `Bitte absenden`. Fünf MCP-Tools kapseln Create/Get/Revise/Send/Cancel; der Versand nutzt den bestehenden ACS-/SendGrid-Adapter für einen frei angegebenen Empfänger. Freigabe-Gate, Negativbefehl und Idempotenz verhindern unbeabsichtigten bzw. doppelten Versand. Token-Validierung bleibt wie geplant out-of-scope.
- **Verification:** Alembic-Migration isoliert und anschließend lokal bis Head `7c4e2d9a8f10` erfolgreich; reale DB danach `email_drafts=0`, bestehend `proposals=9`, `reviews=6`. Wegwerf-DB mit Fake-LLM/ACS: Entwurf v1 → `Ja, passt` ohne Versand → Änderung v2 → explizites Absenden übergibt exakt v2 → zweiter Send idempotent; `Bitte nicht absenden` verwirft und sendet nicht. UI-VM-Test: Plus-Auswahl setzt `selected_tool=email`, hält den Modus während des Entwurfs und löscht ihn erst nach `sent`. Snapshot-Kontext wurde separat mit Wegwerf-Proposal auf Problem, Begründung, Vorschlag und funktionalen Review-Link geprüft; alle Fixtures gelöscht.
- **Open / next:** Ein realer manueller Chat-Dialog mit frei gewähltem Empfänger ist der verbleibende Abnahmeschritt; die technische Versandgrenze ist mit dem bereits real bestätigten ACS-Kanal verbunden.

---

### 2026-07-12 — AP7 Redefinition + AP7.0 Rulebook-Split & A/B-Schalter
- **Status:** done
- **Changed files:** `docs/PT4_PLAN.md` (AP7 neu definiert), `docs/AP7-0_rule_inventory.md` (neu), `demo/skills/_core.md`, `demo/skills/unique-ids.md`, `demo/skills/references.md`, `demo/skills/work-item-configs.md`, `demo/skills/density-values.md` (alle neu), `demo/rulebook_loader.py` (neu), `demo/agent_config.py`, `demo/smart-planning/runtime/{identify_error_llm,generate_correction_llm,validate_correction_schema_llm}.py`. Der Monolith `llm-validation-fix-rules.md` ist **unverändert**.
- **What was done:** **(1) AP7 neu definiert.** Auslöser waren drei Befunde: Short-term Memory existiert bereits seit AP2 (Session-Historie in `messages`, DB-Reload, Sliding Window, `chat_history` in jedem Agent-Call) und wird nicht neu gebaut; episodisches Gedächtnis allein hat ein Kaltstart-Problem (gemessen: `proposals=9`, `reviews=6`, `memory_items=0`); und die Review-Kommentare enthalten fertige Domänenregeln (Review #5 ist eine vollständige Regel in Prosa). AP7 baut daher Long-term Memory in **zwei Schichten** — Rulebook-Karten (bessere Vorschläge, AK2 ≥80 %) und episodische Fälle (ehrliche Confidence). `memory_support` ist verbindlich **nur** aus der episodischen Schicht abzuleiten und abgestuft (0 / 0.5 / 1.0); aus den Karten abgeleitet wäre er konstant 1 und würde jeden Score um +0.2 anheben (0.775 → 0.975) — derselbe Fehler wie `schema_valid`. Ein **Scope Guard** schließt Graphen, neue Metrikdimensionen und eine Markdown-Auflösung von `agent_config.py` explizit aus (Graph-vs-Monolith ist Gegenstand einer separaten Bachelorarbeit). **(2) AP7.0 gebaut.** Regel-Inventar (22 Regeln R1–R22) VOR dem Split erstellt. Dabei ein Konstruktionsfehler der ersten AP7-Fassung gefunden: der maßgebliche `error_type` ist `tag_error_type` (der `[validate_*]`-Tag, seit AP3.6b-1), also der **Validator-Name** — `validate_unique_ids` feuert denselben Tag `UNIQUE_IDS` für Duplikate *und* leere Felder. Der geplante Schnitt `empty-field.md` / `duplicate-id.md` wäre zur Laufzeit nicht auswählbar gewesen. Karten keyen daher 1:1 auf den Validator-Tag. 13 Validator-Tags existieren, der Monolith deckt 5 davon ab; Tags ohne Karte fallen auf `_core.md` zurück (verlustfrei — der Monolith hat für sie ebenfalls keine spezifischen Regeln). `RULEBOOK_MODE = os.getenv("RULEBOOK_MODE", "monolith")` in `agent_config.py`, Muster wie `HUMAN_IN_THE_LOOP`; Tag→Karte über `RULEBOOK_CARDS`. Die dreifach duplizierte Ladefunktion wurde zu einem gemeinsamen `rulebook_loader.py` zusammengeführt.
- **Verification:** **(a) Kein Regelverlust:** 22/22 Regeln über charakteristische Textmarker in genau der Zielkarte nachgewiesen (Marker musste zusätzlich im Original existieren). Die beiden wortgleich duplizierten Packaging-Blöcke (Zeilen 124–158 ⊂ 160–203) sind entfernt, der Inhalt existiert genau einmal. **(b) Monolith-Modus byte-identisch** zur Originaldatei (Assertion). **(c) Live-A/B auf Snapshot `7ab03beb` (1 Fehler, `[validate_demand_article_ids]`), beide Modi vollständig durch identify → generate → schema-validate:** monolith 34.899 Zeichen Regeln / **14.310 Prompt-Tokens** / 0,0381 $ — cards 22.783 Zeichen / **10.570 Prompt-Tokens** / 0,0289 $ (**−26 % Tokens, −24 % Kosten**). **Beide Modi erzeugen denselben Vorschlag** (`update_field`, `demands[386].articleId` → `122873`, confidence 0.775) und bestehen die Schema-Validierung. Keine Qualitätsregression in diesem Fall. Größter Einzelgewinn: `identify_error_llm` lädt im cards-Modus nur noch `_core.md` (9.870 statt 34.899 Zeichen, −72 %) — dieser Schritt *wählt* den Fehler erst aus, der Tag existiert dort noch nicht, und er las bisher 936 Zeilen Korrekturstrategien, die er nie brauchte.
- **Open / next:** AP7.1 — episodischer Schreibpfad: jeder abgeschlossene Review wird als Fall in `memory_items` geschrieben (Fehlersignatur, KI-Vorschlag, menschliche Entscheidung, finaler Wert, Kommentar), inkl. einmaligem Backfill der 6 bestehenden Reviews. Hinweis: Ein einzelner A/B-Fall zeigt die Mechanik, keine Statistik — vor AP-E ist ein Seeding-Lauf nötig.

---

### 2026-07-12 — AP7.1 Episodischer Schreibpfad (memory_items aus reviews)
- **Status:** done
- **Changed files:** `demo/memory/__init__.py`, `demo/memory/long_term.py` (beide neu), `demo/db/repository.py` (additiv: `get_latest_review_as_dict`, `memory_item_exists`, `list_reviewed_proposal_ids`, `count_memory_items`, `list_memory_items_as_dicts`, `set_memory_item_error_type`), `demo/routes/review.py` (Hook in `_decide`).
- **What was done:** Jeder abgeschlossene Review wird zu **genau einem** Fall in `memory_items`: Fehlersignatur (`error_type`, `affected_entity_pattern`), KI-Vorschlag, menschliche Entscheidung, finaler Wert, Kommentar, `revalidation_ok`. Der Hook sitzt in `_decide()` — dem einzigen Commit-Pfad — und feuert für approve/modify **nach** dem Apply (damit das Revalidierungsergebnis schon auf der Review-Zeile steht) und für reject sofort. `record_case_safe()` wirft nie: ein Memory-Fehler darf eine menschliche Entscheidung niemals blockieren (gleiches defensives Muster wie die DB-Writes in `web_server.chat()`). Idempotent über `source_proposal_id` — ein Fall pro Proposal. **Retrieval-Schlüssel:** `affected_entity_pattern` normalisiert den Array-Index weg (`demands[386].articleId` → `demands[].articleId`), denn der konkrete Index eines Snapshots ist Rauschen; erst dadurch wird ein Altfall gegen einen neuen Fehler matchbar. **Gelernt wird ausschließlich aus `reviews`, nie aus dem Chat** — approve/reject/modify und die Begründung stehen dort; die Chat-Historie enthält nur den KI-*Vorschlag* (genau deshalb existiert der `_get_review_decisions()`-Workaround). Aus Proposals zu lernen hieße, dem System die eigenen Halluzinationen beizubringen.
- **Verification:** **(a) Backfill:** 6 bestehende Reviews → 6 Fälle; zweiter Lauf schreibt 0 und überspringt 6 (Idempotenz bewiesen). **(b) Live-Hook:** echter `POST /api/review/proposals/{id}/reject` über den Flask-Testclient auf das Proposal aus dem AP7.0-A/B-Lauf: HTTP 200, `applied=false` (keine Snapshot-Daten verändert), `memory_items` 6 → **7**, neuer Fall korrekt mit `error_type=DEMAND_ARTICLE_IDS`, `affected_entity_pattern=demands[].articleId`, `decision=reject`, `suggested_value=122873`, `final_value=None`. **(c) Datenqualitäts-Fund + Reparatur:** Die Altbestände tragen einen **Mix aus alten Heuristik-Labels und neuen Tags**, weil sie vor AP3.6b-2 entstanden. `repair_legacy_error_types()` leitet den maßgeblichen Tag **deterministisch aus dem Lauf-Artefakt** (`llm_identify_response.json` → `selected_error.message` → `[validate_*]`) neu ab, statt zu raten. Ergebnis: Fall #2 `DUPLICATE_ID` → **`DENSITY_VALUES`** korrigiert — damit ist der AP3.6a-Fehlklassifizierungsbug erstmals in echten Daten nachgewiesen (Heuristik: value-Modus + >1 Treffer → fälschlich DUPLICATE_ID).
- **Open / next:** **(1) Drei Fälle (#3–#5) behalten das Legacy-Label `EMPTY_FIELD`** — ihre Iterationen (`ec96832c` iteration-1/2/3) besitzen **gar kein** `llm_identify_response.json` (synthetische AP3-Testfixtures, Kommentare „AI guessed wrong." o.ä.). Der echte Tag ist nicht rekonstruierbar; es wurde bewusst **nichts geraten**. **(2) Konsequenz für AP7.2:** Retrieval darf **nicht primär auf `error_type`** keyen — ein neuer leerer `demandId` bekommt heute `UNIQUE_IDS` und würde die drei `EMPTY_FIELD`-Fälle verfehlen, die genau davon handeln. `affected_entity_pattern` ist der robuste Schlüssel: `demands[].demandId` vereint #1, #3, #4, #5 korrekt, **unabhängig** vom Label-Chaos. Empfehlung: Pattern primär, `error_type` als sekundäres Signal. **(3)** Die `proposals`-Tabelle trägt weiterhin die Legacy-Labels (nur `memory_items` wurde repariert) — Hinweis für AP6 (Fehlerarten-Diagramm).

---

### 2026-07-12 — AP7.2 Retrieval + ehrliche Confidence (memory_support)
- **Status:** done
- **Changed files:** `demo/memory/retrieval.py` (neu), `demo/smart-planning/runtime/generate_correction_llm.py`, `demo/db/models.py` (+`memory_support`, `memory_support_reason`, `formula_version` auf `proposals`), `demo/db/repository.py` (persistiert sie), `demo/alembic/versions/2f47c4554ece_*.py` (neu). `correction_models.py` bewusst **nicht** angefasst: abgeleitete Felder liegen dort schon seit AP4.5 (`value_grounded`) außerhalb des Pydantic-Modells, das Modell ist nicht `extra="forbid"`.
- **What was done:** Bei einem neuen Fehler werden vergangene, **von Menschen entschiedene** Fälle abgerufen und als Evidenz in den Korrektur-Prompt gegeben; daraus wird `memory_support` abgeleitet. **Retrieval-Schlüssel ist `affected_entity_pattern`, NICHT `error_type`** — begründet in AP7.1: die Fallbasis mischt Legacy-Labels (`EMPTY_FIELD`) mit Tags (`UNIQUE_IDS`), ein Retrieval über `error_type` würde genau die relevanten Altfälle verfehlen. Der Zielpfad ist bereits vor der Generierung bekannt (`last_search_results.results[0].path`), der Schlüssel also zur Retrieval-Zeit verfügbar. Ranking: Pattern-Match (Pflicht) + gleicher `error_type` (Bonus) + Revalidierung bestanden (Bonus). **`memory_support` ist abgestuft und deterministisch** (wie `value_grounded`, nie eine Modell-Meinung): `0.0` kein Fall · `0.0` **negativer Präzedenzfall** (genau dieser Wert wurde schon vorgeschlagen und von einem Menschen verworfen/wegkorrigiert → die KI wiederholt einen bekannten Fehler) · `0.5` Präzedenz für die Fehler**art**, aber kein Wert-Präzedenzfall · `1.0` ein Mensch hat genau diesen Wert bestätigt. Jeder Score trägt zusätzlich `memory_support_reason` im Klartext, damit ein Reviewer sieht, **warum** das Gedächtnis die Confidence gehoben oder gesenkt hat. `formula_version` ("v2") wird auf jedes Proposal gestempelt; "v1" war die Generation mit hart verdrahtetem `memory_support=0` (Score bei 0.8 gedeckelt). Alle Memory-Zugriffe sind defensiv: ein Ausfall degradiert zu „keine Evidenz", die Pipeline bricht nie.
- **Verification:** **(a) Alle drei Stufen deterministisch geprüft:** kein Fall → 0.0 · Fall ohne Wert-Präzedenz → 0.5 · Mensch bestätigte den Wert → 1.0 · Mensch verwarf/korrigierte den Wert weg → 0.0 mit Warnung. **(b) Retrieval gegen die echte DB:** `demands[].demandId` → **3 Fälle (#1, #4, #5)**. Fall #1 trägt `UNIQUE_IDS`, #4/#5 tragen `EMPTY_FIELD` — der Pattern-Schlüssel vereint sie **trotz** des Label-Chaos. Das ist der empirische Beleg für die Schlüsselwahl; ein `error_type`-Retrieval hätte 2 von 3 verfehlt. **(c) Live-Lauf** auf Snapshot `7ab03beb` (cards-Modus, echtes Azure OpenAI): Gedächtnis fand Fall #7, die KI schlug denselben Wert `122873` erneut vor, der **negative Präzedenzfall feuerte** → `memory_support=0.0` mit Klartext-Warnung, `confidence_score` **0.75** statt bisher konstant 0.775, gestempelt `formula v2`. **Der Score bewegt sich erstmals aufgrund des Gedächtnisses.** Alembic-Migration `7c4e2d9a8f10 → 2f47c4554ece` sauber angewendet; `proposals=11`, `memory_items=7`.
- **Open / next:** **(1) WICHTIG — Testdaten im Gedächtnis:** Fall #7 stammt aus dem AP7.1-Hook-Test, in dem ich den Wert `122873` künstlich per `reject` verworfen habe. Der Wert ist aber **nachweislich korrekt** (`value_grounded=1.0`, `articles.articleId=122873` existiert). Das Gedächtnis unterdrückt damit dauerhaft einen richtigen Vorschlag. Empfehlung: Review + Fall #7 löschen, bevor Kennzahlen erhoben werden. **Genereller Befund für die Ausarbeitung: das Gedächtnis verstärkt jede menschliche Entscheidung — auch eine falsche.** Das ist korrektes HitL-Verhalten (der Mensch hat Vorrang), aber es heißt, dass Fehlentscheidungen des Reviewers persistent werden. **(2)** Die 9 Altproposals tragen `formula_version=NULL` (Generation v1, Deckel 0.8) — AP6 muss danach filtern oder neu berechnen, sonst mischt die Kalibrierungskurve zwei Formelgenerationen. **(3)** Nächstes Paket: AP7.3 (ähnliche Fälle im Review-UI sichtbar machen).

---

### 2026-07-12 — AP7.3 Gedächtnis im Review-UI + Bereinigung (Testfall, formula_version)
- **Status:** done
- **Changed files:** `demo/routes/review.py` (neuer Endpunkt `GET /api/review/proposals/<id>/memory`), `demo/db/repository.py` (`get_proposal_as_dict` liefert `memory_support`, `memory_support_reason`, `formula_version`), `demo/ui/scripts/review.js` (Memory-Sektion + `memory_support` in der Konfidenz-Aufschlüsselung), `demo/ui/css/styles.css`.
- **What was done:** **(1) AP7.3.** Der Reviewer sieht in der Detailansicht jetzt „Was wurde bei ähnlichen Fehlern früher entschieden?": Anzahl ähnlicher Fälle mit Aufschlüsselung (bestätigt / korrigiert / verworfen), und je Fall was die KI damals vorschlug, was der Mensch daraus machte **und dessen Begründung im Klartext**. Damit ist `memory_support` nicht länger eine Zahl, die man glauben muss, sondern ein **überprüfbarer Beleg**. Geladen wird asynchron nach dem Muster von `loadCodeContext` (AP4.7); gibt es keinen Fall, bleibt die Sektion aus (kein leerer Kasten). Zusätzlich zeigt „Woher kommt die Konfidenz?" jetzt den dritten Term — aber **nur wenn er berechnet wurde**: bei v0/v1-Vorschlägen ist `memory_support` NULL und der Block bleibt weg, denn eine angezeigte „0" wäre ein Messwert statt einer Leerstelle. `memory_support = 0` wird rot dargestellt (fehlender ODER negativer Präzedenzfall ist eine Warnung, kein neutraler Zustand). **(2) Bereinigung Testfall:** Review + Memory-Fall #7 gelöscht und Proposal-Status auf `pending_review` zurückgesetzt. Begründung siehe AP7.2: der Wert `122873` war per `reject` künstlich verworfen worden, ist aber nachweislich korrekt (`value_grounded=1.0`) — das Gedächtnis hätte einen richtigen Vorschlag dauerhaft unterdrückt. Zurück auf `reviews=6`, `memory_items=6`. **(3) `formula_version` rückwirkend gestempelt** — und zwar **nach dem tatsächlichen Dateninhalt statt pauschal:** Die Prüfung ergab **drei** Generationen, nicht zwei. `v0` = 6 Proposals ohne `value_grounded` (alte `schema_valid`-Formel), `v1` = 5 Proposals mit `value_grounded`, aber `memory_support` hart 0 (AP4.5-Formel, Deckel 0.8), `v2` = AP7.2. Keine Confidence wurde neu berechnet — Vergangenheit wird nicht umgeschrieben, nur korrekt etikettiert.
- **Verification:** Endpunkt gegen echte Daten: `1ef11903__iteration-1` (offener `WORK_ITEM_CONFIGS_COMPLETENESS`-Fehler) → **1 ähnlicher Fall** (`articles[].workItemConfigs`, 1× korrigiert), nämlich Fall #6 mit der vollständigen menschlichen Begründung („BA01 rampUpTime=30 … 124211 ist ein Himbeer-Grundstoff …"). `memory_support` bleibt dort korrekt `None` (v1-Proposal) → Konfidenz-Block wird nicht gezeigt, Fall-Liste schon. **Konsistenzfehler gefunden und behoben:** Das Proposal `7ab03beb__iteration-4` trug nach der Löschung von Fall #7 noch die eingefrorene Begründung „WARNUNG … Fall #7", während die Live-Fallliste 0 zeigte — das UI hätte sich selbst widersprochen. Neu generiert gegen das bereinigte Gedächtnis: jetzt konsistent `0 Fälle` / `memory_support=0.0` („Kein vergleichbarer Fall") / `confidence 0.775` / `formula v2`. **Merke:** `memory_support` ist wie `confidence_score` ein **Generierungszeit-Wert**; ändert sich die Fallbasis, wird er stale. Für AP-E relevant.
- **Open / next:** AP7.4 (Short-term Memory nur benennen, nicht neu bauen; `_get_review_decisions()`-Workaround entfernen). Vor Kennzahlen: Seeding-Lauf. Offen aus AP7.1: die drei Fälle #3–#5 tragen weiterhin das Legacy-Label `EMPTY_FIELD` (Artefakte fehlen, bewusst nicht geraten) — für das Retrieval unschädlich, da über `affected_entity_pattern` gematcht wird.

---

### 2026-07-12 — AP7.4 Short-term Memory: benannt, nicht neu gebaut
- **Status:** done
- **Changed files:** `demo/memory/short_term.py` (neu), `demo/web_server.py`, `demo/main.py`, `docs/PT4_PLAN.md` (AP7.4-Korrektur). `demo/agents/orchestration_agent.py` **bewusst NICHT angefasst** — siehe unten.
- **What was done:** Der Session-Kontext hat jetzt **einen** Besitzer. Bisher lag er verstreut: `chat_sessions`, `db_session_ids`, `_get_db_session_id`, `get_session_history`, `get_recent_messages` in `web_server.py` — und `get_recent_messages` zusätzlich **byte-identisch dupliziert** in `main.py` (dasselbe Muster wie beim dreifachen Rulebook-Loader in AP7.0). Alles nach `memory/short_term.py` gezogen: In-Memory-Cache, DB-Reload bei kaltem Cache (AP4.6), Sliding Window, Session-Id-Mapping. `web_server` delegiert, `main` importiert. **Keine neue Fähigkeit, kein Verhaltenswechsel** — Short-term Memory existierte seit AP2 vollständig, sie hatte nur keinen Namen. Das Modul dokumentiert außerdem explizit, was Short-term Memory NICHT ist (die Review-Entscheidungen), damit die Abgrenzung zur episodischen Schicht im Code steht und nicht nur im Plan.
- **Verification:** **(a)** `main.get_recent_messages is web_server.get_recent_messages is short_term.get_recent_messages` → True (Duplikat eliminiert). **(b)** Sliding-Window-Verhalten gegen die alte Implementierung für `max_pairs` 0..11 durchgeprüft → identisch. **(c)** Kein Alt-Zustand mehr in `web_server` (`chat_sessions`, `db_session_ids`, `_get_db_session_id` entfernt, kein toter Code). **(d)** **Live-Chat gegen Azure OpenAI:** neue Session → „Merke dir bitte die Zahl 47." → „Welche Zahl hast du dir gemerkt?" (die Zahl steht NICHT in der zweiten Frage) → der Agent antwortet mit **„die Zahl 47"**; er kann sie nur aus der Historie haben. 4 Nachrichten in `short_term`, 4 in der DB. Der Kontext fließt korrekt durch die neue Fassade.
- **WICHTIGE KORREKTUR am eigenen Plan:** Die AP7.4-Definition verlangte, den `_get_review_decisions()`-„Workaround" zu entfernen, weil AP7.1 die Review-Ergebnisse strukturell verfügbar mache. **Das war falsch.** Die Funktion ist **kein** Workaround für fehlendes Gedächtnis: Sie liest die Entscheidungen bereits aus der DB (`repo.get_decisions_for_snapshot`) und nutzt die Chat-Historie **nur**, um die Snapshot-ID zu finden. Sie ist die Brücke zwischen Review Board und Chat — genau der Fix für BUG 1 (Chat antwortete auf „was war die Lösung?" mit dem KI-Vorschlag, obwohl der Mensch ihn überstimmt hatte). AP7.1 macht sie nicht überflüssig; sie zu entfernen hätte den Bug wieder aufgerissen. Sie bleibt unverändert. `PT4_PLAN.md` wurde entsprechend korrigiert.
- **Open / next:** **AP7 ist damit vollständig** (7.0 Rulebook-Split + A/B-Schalter · 7.1 episodischer Schreibpfad · 7.2 Retrieval + abgestuftes `memory_support` · 7.3 Gedächtnis im Review-UI · 7.4 Short-term benannt). Vor AP-E: **Seeding-Lauf** (mit 6 Fällen ist die Mechanik gezeigt, aber keine Statistik möglich) und die A/B-Messung `monolith` vs. `cards` über mehrere Snapshots. Offen: AP6 muss nach `formula_version` filtern (v0/v1/v2), sonst mischt die Kalibrierungskurve drei Formelgenerationen.

---

### 2026-07-12 — A/B-Messung (monolith vs. cards) + AP6 formula_version-Filter
- **Status:** done (A/B + Dashboard-Filter) · **BLOCKIERT:** Seeding-Lauf (siehe unten)
- **Changed files:** `demo/skills/work-item-configs.md` (Regression-Fix), `demo/db/repository.py` (`fetch_metrics_data` liefert `memory_support` + `formula_version`), `demo/routes/dashboard.py` (Filter `?formula_version=`, neuer Flag `CONFIDENCE_MIXED_FORMULA_VERSIONS`, Legacy-Flag jetzt exakt statt heuristisch).
- **A/B-Ergebnis (3 Snapshots mit Fehlern, beide Modi je komplett durch identify → generate):**

  | Snapshot | Fehlertyp | Tokens monolith | Tokens cards | Delta | Vorschlag |
  |---|---|---|---|---|---|
  | 7ab03beb | DEMAND_ARTICLE_IDS | 14.355 | 10.576 | −26 % | identisch |
  | 1d45ddff | DEMAND_ARTICLE_IDS | 14.367 | 10.587 | −26 % | identisch (beide `manual_intervention_required`) |
  | 1ef11903 | WORK_ITEM_CONFIGS_COMPLETENESS | 53.240 | 47.757 | −10 % | identisch (**nach** Fix, siehe unten) |
  | **Gesamt** | | **81.962** | **68.920** | **−16 %** | |

  Kosten: 0,2166 $ → 0,1839 $. Memory ist in beiden Modi identisch aktiv (Retrieval hängt nicht am `RULEBOOK_MODE`) und während des Laufs konstant, weil keine Reviews entstehen — der Vergleich bleibt sauber.
- **REGRESSION GEFUNDEN UND BEHOBEN (der eigentliche Wert dieses Laufs):** Im ERSTEN Durchlauf wich `1ef11903` ab: Beide Modi schlugen dieselben 13 `workItemConfig`-Keys vor, aber `cards` sortierte das Array **alphabetisch** (`ABF01, BA01, HE01, …`), während `monolith` es 1:1 aus einem vergleichbaren Artikel übernahm (`VOAR01 → VOPU01 → WART01 → HE01 → … → ABF01`). Das ist die **Prozessreihenfolge** der Fertigung; alphabetisch sortiert ist sie fachlich falsch. Folge: `value_grounded` fiel von **1.0 auf 0.0** („konstruiert/erfunden"), `confidence_score` von **0.75 auf 0.45**. → **Die Confidence-Mechanik hat ihre eigene Regression gefangen** — ein starker empirischer Beleg für das AP4.5-Design (`value_grounded` statt `schema_valid`). **Ursache:** KEIN verlorenes Regel-Item (das Inventar war je Regel vollständig), sondern ein verlorener **Übertragungseffekt**: Der Monolith lieferte dem `workItemConfigs`-Fall beiläufig die „funktionale Kohärenz / Sequenz"-Intelligenz aus dem *Referenzen*-Abschnitt mit; der Kartenschnitt schnitt das ab. Die Karte sagte „kopiere Struktur vom ähnlichsten Objekt", verbot aber das Umsortieren nicht. **Fix:** `work-item-configs.md` macht explizit, was der Monolith nur zufällig transportierte („Reihenfolge ist Prozessreihenfolge, NIEMALS alphabetisch sortieren, Array 1:1 vom ähnlichsten Artikel übernehmen"). Nachmessung: `value_grounded=1.0`, `confidence=0.75` — identisch zum Monolith, bei −10 % Tokens. **Offenlegung: Die Karte wurde NACH dem Sehen des Messergebnisses angepasst.** Der Wert für `1ef11903` in der Tabelle oben ist eine Nachmessung. Das ist zulässig, weil ein echter Defekt behoben wurde und nicht das Experiment geschönt — muss aber in der Auswertung so ausgewiesen werden. **Lehre für die Modularisierung: nicht nur Regeln inventarisieren, sondern auch die impliziten Querbezüge zwischen Abschnitten.**
- **AP6 formula_version:** `fetch_metrics_data` liefert jetzt `formula_version` und `memory_support`. Der bestehende Flag `CONFIDENCE_LEGACY_FORMULA` erkennt Legacy-Zeilen jetzt **exakt** über `formula_version` statt heuristisch über `value_grounded IS NULL` (das trennte nur v0). Neuer Flag `CONFIDENCE_MIXED_FORMULA_VERSIONS`: warnt, sobald entschiedene Vorschläge aus MEHREREN Generationen stammen — die Scores liegen dann nicht auf derselben Skala (v0 quasi-konstant, v1 bei 0.8 gedeckelt, erst v2 voller Bereich). Neuer Query-Param `?formula_version=v0|v1|v2` pinnt eine Generation; die Reviews herausgefilterter Proposals fallen mit weg, sonst zählte man eine Entscheidung ohne zugehörigen Vorschlag. **Verifikation:** `?formula_version=v2` blendet die Legacy-Flags korrekt aus. Der MIXED-Flag feuert derzeit NICHT — korrekt, denn alle 6 entschiedenen Vorschläge sind v0; es existiert genuin nur eine Generation unter den Entscheidungen. Er greift, sobald ein v2-Vorschlag entschieden wird.
- **BLOCKIERT — Seeding-Lauf:** Proposals über mehrere Snapshots zu erzeugen ist mechanisch und kann automatisiert werden. Ein Fall im Gedächtnis entsteht aber erst durch eine **menschliche Review-Entscheidung**, und die darf NICHT fabriziert werden: `memory_items` ist per Definition die Ground Truth. Genau daran ist Fall #7 aufgelaufen (erfundenes `reject` → korrekter Vorschlag wurde dauerhaft unterdrückt). Das im großen Stil zu wiederholen würde die Fallbasis wertlos machen. **Die Approve/Reject/Modify-Entscheidungen muss ein Mensch treffen.** Nächster Schritt: Vorschläge für den Seeding-Lauf vorbereiten, dann durch die Review-UI klicken lassen.

---

### 2026-07-12 — AP-E Testkatalog gebaut + KRITISCHER BEFUND: value_grounded ist für ID-Fehler invertiert
- **Status:** Katalog done · **BLOCKER gefunden** (Confidence-Formel)
- **Changed files:** `demo/eval/build_test_catalog.py` (neu). DB-Bereinigung: 10 Duplikat-Proposals aus meinen Testläufen gelöscht (13 offene Vorschläge waren nur 3 distinkte Fehler); je distinktem Fehler blieb der neueste v2-Vorschlag stehen.
- **Testkatalog (Smart-Planning TESTINSTANZ `vm-t-…-test02…`, cca-dev.com — vom Nutzer freigegeben, Einträge heißen `PT4-TEST-*`):** 4 Snapshots mit gezielt injizierten, bekannten Fehlern; Ground Truth in `metadata.txt`. **Abgrenzung: der INPUT ist konstruiert, die GROUND TRUTH bleibt beim Menschen** — es wurden KEINE Review-Entscheidungen fabriziert (Lehre aus Fall #7). Jeder injizierte Fehler wurde vom **echten serverseitigen Validator** bestätigt:

  | # | Snapshot | Injektion | Validator | Ground Truth |
  |---|---|---|---|---|
  | 01 | `e92b3ee2` | leere `demandId` | `[validate_unique_ids] must not be empty` | `D100079_001` |
  | 02 | `7d2de27d` | doppelte `demandId` | `[validate_unique_ids] Duplicates: D100099_001` | `D100099_002` |
  | 03 | `17a7c1e3` | Typo in `articleId` | `[validate_demand_article_ids] Missing: 100112X` | `100112` |
  | 04 | `84f5af97` | negative `relDensityMin` | `[validate_density_values] invalid: -2` | `1.017` |

  Damit sind erstmals **alle vier Regelkarten abgedeckt** (`UNIQUE_IDS` und `DENSITY_VALUES` kamen in den vorhandenen Snapshots gar nicht vor).
- **Zwei Fallen beim Bauen (beide dokumentiert, damit sie niemand erneut tritt):** **(1) Falsches Grün.** `validate_snapshot.py` HOLT nur die Nachrichtenliste und TRIGGERT den Validierungs-Job nicht — der erste injizierte Fehler wurde als „0 Fehler, Snapshot ist valide" gemeldet. Erst `trigger_server_validation` (AP3.3d) liefert die Wahrheit. Genau der `REVALIDATION_PRE_AP33D`-Effekt aus dem Dashboard-Flag; ein Katalog, der darauf hereinfällt, evaluiert leere Snapshots. **(2) Prioritäts-Kollision.** Jeder frisch gecrawlte Snapshot bringt einen echten Datenfehler mit (Artikel 124211 ohne `workItemConfigs`). Der Priorisierer stuft ihn als Root Cause über Duplikat und Dichte — bei 2 von 4 Snapshots wurde deshalb NICHT der injizierte Fehler bearbeitet. Behoben, indem die Basisdaten repariert wurden — **mit den Werten, die ein Mensch in Memory-Fall #6 bereits bestätigt hat** (keine erfundenen Werte). Danach trägt jeder Testsnapshot genau EINEN Fehler. Nebenbei der erste praktische Nutzen des Gedächtnisses: es hat die Testdaten repariert.
- **KRITISCHER BEFUND — `value_grounded` ist für die ID-Klasse strukturell invertiert:**

  | # | Fehlertyp | KI-Vorschlag | Ground Truth | korrekt? | `value_grounded` | **confidence** |
  |---|---|---|---|---|---|---|
  | 01 | UNIQUE_IDS (leer) | `D100079_001` | `D100079_001` | **JA, exakt** | 0.0 | **0.44** |
  | 02 | UNIQUE_IDS (Duplikat) | `D100099_002` | `D100099_002` | **JA, exakt** | 0.0 | **0.44** |
  | 03 | DEMAND_ARTICLE_IDS | `100112` | `100112` | JA, exakt | 1.0 | 0.775 |
  | 04 | DENSITY_VALUES | `1.14` | `1.017` | **NEIN** | 1.0 | **0.75** |

  **Der Score ist auf dieser Stichprobe ANTI-korreliert mit der Richtigkeit.** Die beiden exakt richtigen ID-Vorschläge erhalten 0.44, der falsche Dichtewert 0.75. Ursache steht wörtlich in der vom System selbst erzeugten Begründung: *„Identitätsfeld: 'D100079_001' muss neu/eindeutig sein und ist daher grundsätzlich nicht aus den Daten belegbar."* — `compute_value_grounded` **erkennt den Fall und bestraft ihn trotzdem mit 0**. Eine neue eindeutige ID DARF per Definition nicht in den Daten stehen; täte sie es, wäre sie ein Duplikat. Der 0.3-Term ist für die gesamte ID-Generierungsklasse **unerfüllbar** — und das ist ausgerechnet der vertikale Slice von PT4. Umgekehrt bei #04: die KI hat `1.14` vom Nachbarartikel abgeschrieben — „belegt" (1.0) und trotzdem falsch. **Belegt ≠ richtig.** Das ist derselbe Fehlertyp wie damals `schema_valid`, nur schwerwiegender: der Term trägt nicht bloß keine Information, er ist für eine ganze Fehlerklasse invertiert. **Für AK2 (≥80 % akzeptiert UND Kalibrierung) ist das ein Blocker — er muss VOR der Evaluation entschieden werden.**
  **Lösungsrichtung (nicht gebaut, Nutzerentscheidung):** `value_grounded` klassenabhängig machen. `compute_value_grounded` erkennt den Identitätsfall bereits — statt 0 zurückzugeben, müsste es dort ein passendes Kriterium prüfen: *folgt der Wert dem erkannten ID-Pattern UND ist er im Zielarray eindeutig?* Das ist genauso deterministisch wie der heutige Test und für diese Klasse das sachlich richtige Kriterium.
- **Open / next:** **7 offene Vorschläge warten auf menschliche Reviews** (4 aus dem Katalog + 3 bestehende) — das ist der Seeding-Stapel. Erst danach sind Kalibrierung und Approval-Rate messbar. Empfehlung: den `value_grounded`-Blocker VOR dem Seeding entscheiden, sonst reviewst du gegen eine Confidence, von der wir bereits wissen, dass sie für zwei der vier Fehlerarten falsch herum zeigt.

---

### 2026-07-12 — AP7.5 Drop-in-Regelkarten (Skills-Ordner wird gescannt statt nachgeschlagen)
- **Status:** done
- **Changed files:** `demo/rulebook_loader.py` (scannt jetzt den Ordner), `demo/agent_config.py` (`RULEBOOK_CARDS` entfernt), die vier Karten in `demo/skills/` (YAML-Frontmatter ergänzt).
- **Warum:** Der Loader schaute bis jetzt in ein hartkodiertes Dictionary (`RULEBOOK_CARDS`) in `agent_config.py`. Eine neue Markdown-Datei in `demo/skills/` wäre damit **unsichtbar** geblieben — sie hätte zusätzlich einen Python-Change gebraucht. Das untergräbt den Zweck des Skills-Ordners: Fachleute sollen Regeln pflegen können, **ohne Entwickler**. (Nutzeranforderung, wörtlich: „ich will einfach eine neue MD-Datei in Skills erstellen und den Umgang mit einem Problem beschreiben, dann fertig — wie wenn ich ganz normal einen System-Prompt erweitern würde".)
- **What was done:** Karten beschreiben sich jetzt **selbst**. Der Loader scannt `demo/skills/*.md` und baut die Zuordnung zur Laufzeit. Regeln: `_core.md` wird immer geladen (Dateien mit führendem `_` sind nie Karten); eine optionale YAML-Frontmatter (`applies_to: [TAG, …]`) nennt die zuständigen `[validate_*]`-Tags; **ohne** Frontmatter gilt die Konvention **Dateiname → Tag** (`work-plan-ids.md` → `WORK_PLAN_IDS`), für den einfachen Fall reicht also die Datei allein; **mehrere Karten dürfen denselben Tag bedienen** — sie werden alle geladen, alphabetisch nach Dateiname, so ergänzt man einen Sonderfall ohne die bestehende Karte anzufassen; kein Treffer → `_core.md` allein (verlustfrei wie bisher). Die Frontmatter ist Metadaten und wird aus dem Prompt-Text entfernt. Mini-Parser statt PyYAML (nicht installiert; für `key: value` und `key: [a, b]` wäre eine neue Abhängigkeit unangemessen). `RULEBOOK_MODE` bleibt unverändert.
- **Verification:** **(a) Scan:** alle 4 Karten mit korrekten Tags gefunden, Frontmatter im Prompt nicht sichtbar, geladene Zeichenzahlen identisch zur Dictionary-Version (12.067 / 22.782 / 17.475 / 13.703; unbekannter Tag → 9.870 = nur `_core`). **(b) Drop-in, ohne eine Zeile Code:** `work-plan-ids.md` (nur Datei, keine Frontmatter) wird für die NEUE Fehlerart `WORK_PLAN_IDS` geladen (9.870 → 9.988 Zeichen); `unique-ids-kundenauftrag.md` (Frontmatter `applies_to: [UNIQUE_IDS]`) wird ZUSÄTZLICH zur bestehenden `unique-ids.md` geladen, beide Regeltexte sind im Prompt (12.067 → 12.193). Testdateien danach entfernt. **(c) Regression:** echter Lauf auf Katalog-Snapshot 01 unverändert (`UNIQUE_IDS`, 12.067 Zeichen, Vorschlag `D100079_001` = Ground Truth).
- **Bedeutung für AP-X:** Damit ist die Voraussetzung für den Tages-Agenten gelegt — er kann eine Regelkarte als Datei vorschlagen/anlegen, ohne `agent_config.py` zu editieren.
- **Open / next:** Unverändert offen: der **`value_grounded`-Blocker** (für die ID-Klasse strukturell invertiert — zwei exakt richtige Vorschläge mit 0.44, ein falscher mit 0.75) und danach der **Seeding-Lauf** über die 7 offenen Vorschläge.

---

### 2026-07-12 — AP7.5b Agent waehlt Regelkarten selbst + Cloud-Storage + Vorlage
- **Status:** done
- **Changed files:** `demo/rulebook_loader.py`, `demo/smart-planning/runtime/identify_error_llm.py`, `demo/smart-planning/runtime/generate_correction_llm.py`, `demo/skills/_VORLAGE.md` (neu), `demo/skills/umgang-mit-zwei-falsche-nummern.md` (Nutzer-Karte, Frontmatter ergaenzt — Regeltext unveraendert).
- **Auslöser (Nutzeranforderung, wörtlich):** *„der Agent soll immer jederzeit Zugriff auf alles haben und er soll entscheiden, und zwar intelligent. Ich will einfach solche Beschreibungen hinzufügen, ganz easy in meiner einfachen Sprache, und erwarte, dass sie berücksichtigt werden."* — Der Nutzer legte `umgang-mit-zwei-falsche-nummern.md` an. Sie wurde **nie geladen**: die Dateiname→Tag-Konvention leitete daraus `UMGANG_MIT_ZWEI_FALSCHE_NUMMERN` ab, ein Tag, den es nicht gibt. **Das war ein Designfehler von mir** — eine Falle derselben Klasse wie der stille Regelverlust, gegen den AP7.0 mit dem Inventar antrat: eine Karte, die stumm nichts tut.
- **What was done:** **(1) Der Agent waehlt selbst.** Der Identifikationsschritt (laeuft ohnehin, kostet also KEINEN zusaetzlichen LLM-Call) bekommt jetzt ein **Inhaltsverzeichnis ALLER Karten** — Dateiname plus Klartext-`description` — und gibt in `relevant_cards` zurueck, welche zum Fehler passen (plus Begruendung). `generate_correction_llm` laedt genau diese. Damit hat der Agent **jederzeit Zugriff auf den gesamten Regelbestand**, laedt aber nur, was er braucht — statt alles in jeden Prompt zu kippen (das waere wieder der Monolith und skaliert bei 30 Karten nicht). **(2) Dateiname→Tag-Konvention ENTFERNT** (die Falle). `applies_to` ist jetzt eine optionale Abkuerzung fuer den garantierten Treffer; ohne sie entscheidet der Agent ueber die Beschreibung. Ohne `description` faellt der Loader auf die erste Textzeile zurueck. **(3) Cloud.** Der Kartenzugriff laeuft ueber den `StorageManager` — derselbe Code fuer `STORAGE_MODE=LOCAL` (`demo/skills/`) und `STORAGE_MODE=AZURE` (Blob-Prefix `skills/` im Container, ueber `RULEBOOK_SKILLS_PREFIX` ueberschreibbar). Fachanwender koennen die Regeln im Storage Account pflegen, **ohne Redeployment**. **(4) `_VORLAGE.md`** erklaert das Muster (Dateien mit `_` sind nie Karten). **(5) `check_cards()`** meldet `applies_to`-Tippfehler.
- **Verification (echter Lauf, Katalog-Snapshot 84f5af97, Fehler `relDensityMin: -2`):** Der Index zeigt alle 5 Karten. Der Agent waehlte **von selbst** `['density-values.md', 'umgang-mit-zwei-falsche-nummern.md']` mit Begruendung — **die Nutzer-Karte wurde gefunden, obwohl der Nutzer keinen Validator-Tag kennt.** Der Vorschlag aenderte sich dadurch von `1.14` (Median aus Nachbarartikeln, bisherige Regel) auf `2` (Vorzeichen umgedreht, neue Regel). **Die Nutzer-Karte hat die bestehende Karte ueberstimmt.**
- **WICHTIGER BEFUND — eine neue Karte kann bestehendes Verhalten ueberstimmen:** Genau das ist hier passiert. Im Testsnapshot ist die Ground Truth `1.017`, die neue Regel liefert `2`. Das heisst NICHT, dass die Regel falsch ist — mein Testfall passt nicht zu ihr: ich hatte `1.017` durch `-2` **ueberschrieben**, das war nie ein Vorzeichenfehler. Bei einem echten Vorzeichenfehler waere der Originalwert `2` gewesen. **Die Lehre bleibt:** eine drop-in-Karte kann etablierte Regeln aushebeln, ohne dass jemand Code reviewt. Das ist das staerkste Argument dafuer, dass der AP-X-Tagesagent Kartenaenderungen **nie ohne menschliche Freigabe** schreiben darf — und ein Grund, spaeter eine Konfliktpruefung zwischen Karten vorzusehen (im Plan bereits als Risiko notiert: „Widerspruch zwischen neuer und bestehender Regel").
- **Open / next:** Unveraendert: der **`value_grounded`-Blocker** (fuer die ID-Klasse invertiert) und danach der **Seeding-Lauf**. Neu auf der Liste: Konfliktpruefung zwischen Regelkarten (Backlog, nicht blockierend).

---

### 2026-07-12 — AP5.4 Automatische Review-E-Mails deaktiviert
- **Status:** done
- **Changed files:** `demo/mcp_connections/notifier.py`, `demo/mcp_connections/README.md`, `docs/PT4_PLAN.md`, `docs/PROJECT_LOG.md`
- **What was done:** Auf ausdrückliche Nutzerentscheidung sendet die Proposal-/Korrekturpipeline keine E-Mail mehr. Der bestehende Runtime-Hook bleibt wegen der Runtime-Hard-Rule kompatibel aufrufbar, endet im Adapter aber immer als dokumentierter Skip und kann ACS/SendGrid nicht erreichen. Der separate Chat-Pfad bleibt unverändert: E-Mail-Versand ist nur über einen persistenten Entwurf und `send_email_draft(..., confirmed=True)` beziehungsweise die ausdrückliche Chat-Anweisung `Bitte absenden` möglich. Der nicht mehr verwendete automatische Review-Mail-Builder wurde entfernt; Secrets wurden nicht angefasst.
- **Verification:** Wegwerf-DB bei aktivem `NOTIFICATION_CHANNEL=acs` und Provider-Testdouble: neuer Proposal-Hook → 0 Provider-Aufrufe; unbestätigter Chat-Draft → HTTP-ähnlich 409 und 0 Aufrufe; bestätigter Chat-Draft → genau 1 ACS-Aufruf; erneutes Senden → idempotent, weiterhin genau 1. Fixture restlos gelöscht. Kein Runtime-Tool geändert.
- **Open / next:** Keiner für diese Verhaltensänderung; `NOTIFICATION_RECIPIENT_EMAIL` darf in `.env` verbleiben, wird vom deaktivierten Automatikpfad aber nicht mehr gelesen.

---

### 2026-07-12 — AP7 ABGESCHLOSSEN (M7) — Verifikation, Default-Umstellung, Aufräumen
- **Status:** AP7 done — Milestone M7 abgehakt
- **Changed files:** `demo/agent_config.py` (Default `RULEBOOK_MODE` → `cards`), `docs/PT4_PLAN.md` (AP7.0–7.5 abgehakt, AP7.5 nachgetragen, M7 = [x], Handover-Abschnitt an AP-E). DB-Bereinigung: 5 veraltete/doppelte Vorschläge entfernt.
- **Verifikation aller DoDs gegen den LIVE-Code (nicht behauptet, geprüft):**
  - **AP7.0** `monolith` byte-identisch zum Original (34.899 Zeichen, Assertion). `cards` lädt selektiv: 9.870 (nur `_core`) bis 22.782 Zeichen. `check_cards()` meldet keine Tippfehler.
  - **AP7.1** `memory_items = 6`, `reviews = 6`, Backfill idempotent.
  - **AP7.2** Retrieval `demands[].demandId` → 3 Fälle; `memory_support` liefert 0.0 / 0.5 / 1.0; **12 Proposals mit `formula_version = v2`**; DB-Verteilung v0=6, v2=12.
  - **AP7.3** 7 offene Vorschläge, davon zeigen 8 (vor der Bereinigung) Altfälle inkl. menschlicher Begründung im Review-UI.
  - **AP7.4** `get_recent_messages` in `main`, `web_server`, `short_term` **dieselbe Funktion**; Alt-Zustand aus `web_server` entfernt.
  - **AP7.5** Nutzer-Karte wurde vom Agenten selbst gewählt und hat das Ergebnis verändert (1.14 → 2).
  - **AP6-Filter** `?formula_version=v2` blendet die Legacy-Flags korrekt aus.
- **ENTSCHEIDUNG — Default `RULEBOOK_MODE` von `monolith` auf `cards` umgestellt (Nutzerfreigabe).** Begründung: Mit `monolith` als Default ist der **gesamte Skills-Ordner im Normalbetrieb wirkungslos** — jede Regelkarte, die ein Fachanwender schreibt, wäre tot. Die A/B-Messung über 3 Snapshots zeigt: `cards` liefert **identische Vorschläge bei −16 % Prompt-Tokens**. Die Rückfallebene bleibt vollständig erhalten: `RULEBOOK_MODE=monolith` liefert weiterhin die byte-identische Originaldatei (verifiziert), die A/B-Messung für AP-E ist jederzeit möglich.
- **Aufgeräumt:** 5 Vorschläge entfernt — teils Duplikate meiner Testläufe, teils **veraltet** (`WORK_ITEM_CONFIGS`-Vorschläge für Fehler, die es nach der Basis-Reparatur der Katalog-Snapshots nicht mehr gibt). Bereinigt anhand der AKTUELLEN Validierung je Snapshot, nicht nach Gefühl. Stand: **7 offene Vorschläge, genau einer je Snapshot** — der Seeding-Stapel, alle vier Fehlerarten abgedeckt.
- **Was AP7 an AP-E übergibt (steht jetzt auch im Plan):** (1) **BLOCKER `value_grounded`** — gehört zur Confidence-Formel (AP1/AP4.5), NICHT zu AP7, muss aber vor AP-E entschieden werden; für die ID-Klasse strukturell invertiert (zwei exakt richtige ID-Vorschläge → 0.44, ein falscher Dichtewert → 0.75). (2) **Seeding-Lauf** — 7 Vorschläge warten auf MENSCHLICHE Entscheidungen; die dürfen nie fabriziert werden. (3) **Testkatalog** steht (`demo/eval/build_test_catalog.py`, 4 Snapshots auf der SP-Testinstanz mit dokumentierter Ground Truth). (4) **Backlog:** Konfliktprüfung zwischen Regelkarten; drei Memory-Items tragen weiter das Legacy-Label `EMPTY_FIELD` (unschädlich, Retrieval matcht über `affected_entity_pattern`).

---

### 2026-07-12 — GESAMTSTAND: was ist wirklich noch offen? (Bestandsaufnahme)
Vollständige Durchsicht von `PT4_PLAN.md`, `PROJECT_LOG.md` und dem Code. Der Backlog-Block vom
2026-07-11 ist teilweise überholt — hier der aktuelle Stand.

**Meilensteine — nur Buchhaltung, keine offene Arbeit:**
`M4 (AP4 HitL-Frontend)` und `M6 (AP6 Dashboard)` standen noch auf `[ ]`, obwohl beide **code-seitig
abgeschlossen und lauffähig** sind (verifiziert: Review-Board liefert 7 offene Vorschläge; Dashboard
liefert alle KPIs inkl. der 8 Ehrlichkeits-Flags). Auch AP1.1–AP1.4 waren nie abgehakt, obwohl M1
`[x]` ist. → Checkboxen nachgezogen, keine echte Restarbeit.

**Durch AP7 erledigt (Backlog-Einträge streichen):**
- *„`llm-validation-fix-rules.md` überarbeiten"* — durch **AP7.0** erledigt: die ~3× duplizierten
  PACKAGING-Blöcke sind raus, die Struktur ist hergestellt (Identifikation / array_context / Actions
  getrennt in `_core.md` + Karten), und die im 124211-Fall vermisste Regel („Reihenfolge = Prozess-
  reihenfolge, Array 1:1 vom ähnlichsten Artikel") ist ergänzt.
  **ACHTUNG, der alte Vorbehalt war berechtigt:** „NICHT vor der Baseline ändern (verschiebt die
  AK2-Grundlinie)". Wir HABEN vor der Baseline geändert. Deshalb ist zwingend: der Monolith bleibt
  byte-identisch erhalten (verifiziert) und **die Baseline-Messung muss den `RULEBOOK_MODE`
  festnageln** — sonst misst man gegen eine verschobene Grundlinie. Genau dafür existiert der
  A/B-Schalter.
- *„AP6-Notiz: `revalidation_result` aus Läufen VOR AP3.3d markieren"* — erledigt, das Dashboard
  führt den Flag `REVALIDATION_PRE_AP33D` (verifiziert).
- *„[später] AP5 MCP, AP6 Dashboard, AP7 Memory"* — alle drei erledigt. Nur AP-E bleibt.

**NEUER OFFENER PUNKT (von mir verursacht) — Snapshots auf dem Testserver:**
Der Log-Eintrag vom 2026-07-11 hielt fest: *„Blockiert durch: es gibt kein Lösch-Tool — jeder Fall
hinterlässt einen dauerhaften Snapshot auf dem Testserver (11 Stück). Nutzer hat die Ausführung
deshalb vorerst gestoppt."* **Das war mir nicht bekannt.** Beim Bau des AP-E-Testkatalogs habe ich
heute **4 weitere Snapshots** angelegt (`PT4-TEST-01`…`04`) — Stand jetzt **13**. Die Freigabe des
Nutzers deckte das ab, aber der ursprüngliche Grund für den Stopp besteht unverändert: **es fehlt
ein Lösch-/Aufräumweg für Testsnapshots.** Das ist die Vorbedingung dafür, den Katalog künftig
gefahrlos zu erweitern (die Baseline sah 10 Fälle vor). → Neuer Backlog-Punkt.

**Gehört fachlich in AP-E.0 (nicht separat führen):**
- `value_grounded` deckt `add_to_array` und verschachtelte Pfade (`equipment[i].predecessors[0]`)
  nicht gezielt ab und liefert dort konservativ `0`. **Dasselbe Grundproblem wie der ID-Blocker** —
  in einem Fix erledigen.

**Echte Tech-Debt, weiterhin offen (nicht blockierend):**
1. **BA01-Werte für Artikel 124211 nie am Stammsatz gegengeprüft** (statistisch hergeleitet:
   16/16 Himbeer-Grundstoffe = 30/1, `P` als Modus 11/16). **Neue Tragweite:** genau mit diesen
   Werten wurden die Basisdaten der **vier Testkatalog-Snapshots** repariert. Sind sie falsch, ist
   die Katalog-Basis falsch. Vor der Evaluation am Stammsatz verifizieren.
2. **AP3.6c** — Fallback-Verhalten, wenn das `[validate_*]`-Tag fehlt (`generate_correction_llm`
   fällt dann auf die widerlegte Zähl-Heuristik zurück). Im Rahmen der Baseline messen, wie oft das
   real passiert; falls nie → durch neutrales `UNKNOWN` ersetzen.
3. **`review.js` kennt HTTP 422 nicht** (action-Guard). Kann aktuell nicht eintreten, rein
   vorsorglich.
4. **Identitäts-Guard** für Sonderentitäten (`equipment` duale ID, `worker*`, `packaging`) und
   `KIND_ADD_OBJECT` — bewusst guard-skipped, bis reale Fälle existieren.
5. **Phase-3-Kennzahl (85 % Auto-Fix-Rate) ist fragwürdig** — beruht vermutlich auf dem False-Green-
   Validierungsbug. **Nicht ungeprüft in der Ausarbeitung zitieren.**
6. **Reload-Historie in der Review-Detailansicht** — `get_proposal_as_dict()` liefert keine
   `reviews`-Daten; nach einem Reload sieht man den Status, aber nicht *was* entschieden wurde.
7. **action-Semantik (kosmetisch)** — `update_field` für eine ganze Array-Befüllung.
8. **Konfliktprüfung zwischen Regelkarten** (neu aus AP7.5) — eine Drop-in-Karte kann eine
   bestehende Regel überstimmen, ohne dass jemand Code reviewt.

**Fazit:** Außer den AP-E-Punkten (AP-E.0 Blocker, AP-E.2 Seeding, AP-E.3 A/B, AP-E.4 Messung/Demo)
ist **nichts Blockierendes offen**. Alles Übrige ist Tech-Debt oder Buchhaltung. Die einzigen zwei
Punkte, die vor der Evaluation wirklich angefasst werden sollten, sind der **`value_grounded`-Fix
(AP-E.0)** und die **Verifikation der BA01-Werte** (weil die Testkatalog-Basis darauf steht).

---

### 2026-07-12 — AP5/AP6-Gesamtdokumentation als Markdown
- **Status:** done
- **Changed files:** `docs/AP5_AP6_DOCUMENTATION.md` (neu), `docs/PROJECT_LOG.md`
- **What was done:** Die zuvor gelieferte detaillierte Gesamtübersicht zu AP5/MCP und AP6/Dashboard wurde 1:1 als eigenständige Markdown-Dokumentation übernommen. Enthalten sind 34 nummerierte Abschnitte, Status, Architekturen, alle MCP-Tools, ACS/SendGrid, konversationeller E-Mail-Agent, Persistenz, Dashboard-API, KPI- und Datenqualitätsdefinitionen, Kostenmodell, UI/Charts, Nachweise, Grenzen, nächste Schritte und Dateiverweise.
- **Verification:** Datei als UTF-8 gelesen; 1.813 Zeilen / 42.881 Zeichen; Abschnitte 1–34 vollständig; 120 Markdown-Code-Fence-Marker paarig; `git diff --check` ohne Whitespace-Fehler. Keine Runtime-Datei und keine Produktdaten geändert.
- **Open / next:** Keiner; die Datei ist die ausformulierte AP5/AP6-Referenzdokumentation.

---

### 2026-07-12 — Tech-Debt abgearbeitet (AP3.6c, Reload-Historie, HTTP 422) + Grundsatzentscheidungen
- **Status:** done
- **Changed files:** `demo/smart-planning/runtime/generate_correction_llm.py` (AP3.6c), `demo/db/repository.py` (`get_proposal_as_dict` liefert die Entscheidung), `demo/ui/scripts/review.js` (entschiedener Zustand + HTTP 422), `demo/ui/css/styles.css`.

**GRUNDSATZENTSCHEIDUNG — das System darf NIE Snapshots löschen (Nutzerentscheidung).**
Das fehlende Lösch-Tool ist damit **kein offener Punkt, sondern gewollt**. Begründung (fürs Protokoll,
weil es ein Governance-Argument für die Ausarbeitung ist): Ein Agent, der Planungsdaten löschen kann,
ist ein Agent, der Planungsdaten löschen wird. Der Preis ist, dass Testsnapshots auf der Testinstanz
dauerhaft liegen bleiben (aktuell 13). Das ist bewusst akzeptiert. **Konsequenz für AP-E:** die
Katalog-Erweiterung (geplant waren 10 Fälle) muss mit diesem Wachstum leben — kein Blocker mehr.

**BESTÄTIGT — der Monolith ist unangetastet, mitsamt seinen Schwächen.**
Nachgemessen: `llm-validation-fix-rules.md` enthält weiterhin **3×** den duplizierten
„Domain-Intelligence"-Block und **2×** den PACKAGING-Block, und die Prozessreihenfolge-Regel fehlt
dort. Alle Korrekturen leben **ausschließlich** in `demo/skills/`. Damit ist der Monolith der saubere
„Vorher"-Arm der A/B-Messung — genau die Trennung, die der Nutzer gefordert hat.

**AP3.6c — Fallback bei fehlendem `[validate_*]`-Tag: gemessen und geschlossen.**
Messung über **alle 41** vorhandenen Identify-Artefakte: das Tag ist in **41 von 41** Fällen
vorhanden — es fehlt nie. Der Fallback auf die Zähl-Heuristik war damit toter Code mit scharfer
Kante: auf dem einen Pfad, auf dem er feuern *würde*, liefert er einen Wert, den wir als falsch
kennen (`DUPLICATE_ID` bei >1 Treffer), und dieser Wert flösse in die Regelkarten-Auswahl, die
Memory-Signatur und das Dashboard. **Ein falsches Label ist schlimmer als kein Label** → Fallback ist
jetzt neutrales `UNKNOWN` plus Warnung. `legacy_error_type` bleibt als Audit-Feld erhalten.
*Verifiziert:* neuer Lauf auf `e92b3ee2` → `error_type=UNKNOWN` feuert nicht, Tag greift (`UNIQUE_IDS`).

**Reload-Historie in der Review-Detailansicht — geschlossen.**
`get_proposal_as_dict()` liefert jetzt additiv die **letzte Entscheidung** (`decision`, `final_value`,
`comment`, `reviewer_ref`, `decided_at`, `revalidation_result`); die Detailansicht zeigt sie im
Entscheidungs-Panel an. Bisher stand dort nach einem Reload nur „Status: approved" — **was** entschieden
wurde (finaler Wert, menschliche Begründung) war unsichtbar. Das war ein Loch in der Audit-Sicht: der
ganze Sinn von HitL ist, dass die menschliche Entscheidung festgehalten ist.
*Verifiziert:* entschiedener Vorschlag liefert `decision=approve`, `final_value=0.965`, Kommentar und
Zeitstempel; offener Vorschlag liefert korrekt `decision=None`.

**HTTP 422 im Review-UI — geschlossen.** Der Action-Guard blockt Modify auf `remove_from_array` /
`manual_intervention_required` mit 422, **bevor** etwas geschrieben wird. Das UI zeigte dafür einen
generischen Fehler. Jetzt: Klartext-Meldung inkl. der unzulässigen Action und dem ausdrücklichen
Hinweis „Es wurde nichts gespeichert und nichts angewendet"; das Panel bleibt offen, der Reviewer kann
eine andere Aktion wählen. Kann aktuell nicht eintreten (alle realen Proposals sind `update_field`) —
reine Vorsorge, analog zur bestehenden 409-A/409-B/502-Unterscheidung.

**WIDERSPRUCH zum Nutzervorschlag — Identitäts-Guard gehört NICHT in eine Lernkarte.**
Der Nutzer schlug vor, den Identitäts-Guard für Sonderentitäten als Regelkarte umzusetzen.
**Das geht nicht und wäre gefährlich.** Der Guard ist keine Heuristik für die KI, sondern eine
**deterministische Sperre im Apply-Pfad**: Er läuft NACH der menschlichen Freigabe, in Python, ohne
jedes LLM, vergleicht die Identität des Zielobjekts mit der im Vorschlag verankerten und **blockiert
den Schreibvorgang mit HTTP 409** bei Abweichung. Regelkarten landen ausschliesslich im *Prompt der
Vorschlagserzeugung* — sie können im Apply-Pfad gar nicht wirken. Und selbst wenn: aus einer harten
Sperre würde ein Hinweis, dem das Modell folgen kann oder auch nicht. Das widerspricht dem Scope Guard
im Plan („deterministische Config und Logik bleiben Code; nur Domänen-Heuristiken wandern in Karten").
→ Guard bleibt Code, bleibt offen bis reale Sonderentitäten-Fälle existieren.

**Verbleibende Tech-Debt (mit Nutzerentscheidung):**
- **BA01-Werte für Artikel 124211 am Stammsatz gegenprüfen** → *nach AP-E besprechen* (Nutzer).
  Achtung: der AP-E-Testkatalog steht auf diesen Werten.
- **Phase-3-Kennzahl (85 % Auto-Fix-Rate) fragwürdig** → *nach AP-E besprechen* (Nutzer).
  Bis dahin: **nicht ungeprüft zitieren.**
- **Identitäts-Guard für Sonderentitäten** → bleibt offen bis reale Fälle (siehe Widerspruch oben).
- **Konfliktprüfung zwischen Regelkarten** → **out of scope für PT4, verschoben nach AP-X** (Nutzer).
- **`action`-Semantik** (`update_field` für eine ganze Array-Befüllung statt Array-Replace) → **später**
  (Nutzer). Kosmetisch; ein Eingriff dort berührt den Apply-Pfad, Risiko ohne aktuellen Nutzen.

---

### 2026-07-12 — Repo-Housekeeping als Aufgabe erfasst (AP-E.5)
- **Status:** Bestandsaufnahme done, Ausführung offen (steht als **AP-E.5** im Plan)
- **Changed files:** `docs/PT4_PLAN.md` (neues Sub-Paket AP-E.5)
- **Befund — und der ist anders als erwartet:** **Das Repo ist NICHT vermüllt.** Kein toter Testcode,
  keine Wegwerf-Skripte, kein `zArchive`, keine verwaisten Fixtures. Alle temporären Dateien, die ich
  während der Arbeit erzeugt habe, lagen im Scratchpad ausserhalb des Repos. Es gibt sehr wenig echten
  Abfall.
- **Das eigentliche Hygieneproblem ist ein anderes: nichts ist committet.** 16 geänderte Dateien +
  7 unversionierte Pfade — die **gesamte AP7-Arbeit** liegt uncommittet auf der Platte
  (`demo/skills/`, `demo/memory/`, `demo/eval/`, `demo/rulebook_loader.py`, die Alembic-Migration,
  `docs/AP7-0_rule_inventory.md`). Ein Rechnerausfall kostet alles. Das ist dringender als jedes
  Löschen.
- **Echter Abfall (sicher):** `demo/__pycache__/` (9 Verzeichnisse im Projektcode, regenerierbar),
  `demo/config/` (**leeres Verzeichnis**), `demo/logs/` (35 Logdateien Jan–Jul, gitignored, werden
  von nichts gelesen).
- **Zu klären:** `docs/Zwischenstand-Abschluss-AP2.md` (Statusbild vom 08.07., überholt durch
  PROJECT_LOG + Plan) und `docs/AP5_AP6_DOCUMENTATION.md` (unversioniert, überschneidet sich mit dem
  Log — eigenständiges Abgabedokument oder Dublette?).
- **FINGER-WEG-LISTE (der wichtigste Teil dieses Eintrags).** Beim Aufräumen ist die Gefahr nicht der
  Müll, sondern das, was wie Müll AUSSIEHT:
  1. **`llm-validation-fix-rules.md`** — die alte 936-Zeilen-Datei mit den bekannten Schwächen. Sieht
     aus wie ein Überbleibsel, ist aber der **„Vorher"-Arm der A/B-Messung**. **Wer sie löscht,
     vernichtet die Baseline.** Byte-Identität ist Teil der DoD von AP7.0.
  2. **`smart-planning/Snapshots/`** — gitignored, aber der Audit-Trail: die
     `iteration-*/llm_identify_response.json` werden von der Memory-Legacy-Reparatur gelesen, und die
     Ground Truth des AP-E-Testkatalogs steht in den `metadata.txt`. (Zudem gilt die
     Grundsatzentscheidung: das System darf nie Snapshots löschen.)
  3. **`demo/main.py`** — sieht nach totem CLI aus, wird aber von `agents/rag_agent.py` importiert
     (`main.LOGGING_CONFIG`).
  4. **`identify_snapshot.py`** — sein `error_type` ist tot (AP3.6a), die Datei macht aber die
     eigentliche Suche.
  5. **`alembic/versions/`** (5 Migrationen) — DB-Historie, nie aufräumen.
- **Open / next:** AP-E.5 ausführen (A: committen · B: löschen · C: entscheiden · D: nachweislich
  unangetastet lassen). Reihenfolge: **erst committen, dann löschen** — sonst ist ein Fehlgriff
  nicht rückholbar.

---

### 2026-07-12 — AP-E.0 BLOCKER behoben: `value_grounded` ist jetzt klassenabhängig (Formel v3)
- **Status:** done — der einzige echte Blocker von AP-E ist weg
- **Changed files:** `demo/smart-planning/runtime/generate_correction_llm.py` (`compute_value_grounded` + zwei neue Helfer `_id_shape` / `_dominant_id_shape` + `_grounded_for_identity` / `_grounded_for_new_object`, `CONFIDENCE_FORMULA_VERSION` → `v3`), `docs/PT4_PLAN.md` (Formel + AP-E.0 abgehakt). DB: die 7 offenen Vorschläge neu bewertet.
- **Der Defekt.** `value_grounded` stellte für JEDES Feld dieselbe Frage: *„steht dieser Wert schon in den Daten?"* Für ein **Identitätsfeld** ist das nicht bloss schwer, es ist **verkehrt herum**: Eine neue eindeutige ID DARF nicht in den Daten stehen — täte sie es, wäre sie ein Duplikat, also falsch. Der 0.3-Term war damit für die gesamte ID-Generierungsklasse **strukturell unerfüllbar** — ausgerechnet den vertikalen Slice von PT4.
- **Der Fix — die Frage hängt jetzt an der Feldklasse (alle vier gleich deterministisch wie vorher):**
  - **Identitätsfeld** → ist der Wert im Array **eindeutig** UND folgt er der **ID-Konvention** des Arrays? Die Konvention wird nicht hart kodiert, sondern aus den Daten abgeleitet: `_id_shape()` bildet eine Strukturform (Ziffern→`9`, Grossbuchstaben→`A`, …), `_dominant_id_shape()` nimmt die Mehrheitsform. `D100079_001` → `A999999_999`. Eine **Kollision** bleibt 0.0 und ist nicht nur „unbelegt", sondern nachweislich falsch.
  - **Referenzfeld** → existiert das referenzierte Objekt? (unverändert)
  - **Wertfeld** → sitzt derselbe Wert auf demselben Feld eines vergleichbaren Objekts? (unverändert)
  - **`add_to_array`** → dieselben Prüfungen auf das NEUE Objekt (Identität eindeutig+konventionell, alle Referenzfelder belegt). *Vorher gar nicht abgedeckt.*
  - **Verschachtelte Listenpfade** (`equipment[i].predecessors[0]`) → Mitgliedschaftsprüfung statt Skalar-gegen-Liste-Vergleich. *Vorher lieferte das **immer** „erfunden".*
  (Die letzten beiden waren als eigene Tech-Debt-Punkte geführt; sie gehören fachlich hierher und sind mit erledigt.)
- **Verifikation gegen die Ground Truth des Testkatalogs — die Anti-Korrelation ist umgedreht:**

  | Fall | KI-Vorschlag | Ground Truth | korrekt? | conf. **vorher** | conf. **jetzt** |
  |---|---|---|---|---|---|
  | `e92b3ee2` UNIQUE_IDS (leer) | `D100079_001` | `D100079_001` | **JA, exakt** | 0.445 | **0.745** |
  | `7d2de27d` UNIQUE_IDS (Duplikat) | `D100099_002` | `D100099_002` | **JA, exakt** | 0.44 | **0.74** |
  | `17a7c1e3` DEMAND_ARTICLE_IDS | `100112` | `100112` | JA, exakt | 0.775 | 0.775 |
  | `84f5af97` DENSITY_VALUES | `2` | `1.017` | **NEIN** | 0.475 | **0.475** |

  Richtige Vorschläge liegen jetzt bei **0.74–0.775**, der falsche bei **0.475**. Die Begründung bleibt lesbar: *„Identitätsfeld belegt: `D100079_001` ist im Array eindeutig UND folgt der Konvention `A999999_999` (1394 von 1394)"*.
  Zusätzlich unit-getestet: `add_to_array` (konventionell+Referenz belegt → 1.0; Kollision → 0.0; tote Referenz → 0.0), verschachtelte Liste (belegtes Element → 1.0; unbekannter Wert → 0.0), Konventionsbruch (`NEUE_ID_XYZ` → 0.0).
- **Formel-Generation auf `v3` erhöht.** Die **Gewichte** sind unverändert, aber die **Semantik** des 0.3-Terms hat sich geändert — v2- und v3-Scores sind **nicht vergleichbar**. Die 7 offenen Vorschläge wurden **neu bewertet, nicht neu generiert** (kein LLM-Call, kein Vorschlags-Drift): DB-Stand jetzt `v0=6` (historisch, entschieden), `v3=7`. AP6 muss weiterhin eine Generation pinnen (`?formula_version=v3`).
- **VERBLEIBENDE GRENZE, ehrlich benannt:** Für **Wertfelder** misst `value_grounded` weiterhin *Herkunft*, nicht *Korrektheit*. Ein Wert, den die KI vom **falschen Nachbarn** abgeschrieben hat, ist „belegt" (1.0) und trotzdem falsch — genau so passiert, als die KI `1.14` statt `1.017` vorschlug. Das ist keine Regression, sondern die Natur des Signals: es trennt „aus den Daten abgeleitet" von „erfunden", nicht „richtig" von „falsch". Für die ID-Klasse ist es jetzt sehr wohl ein Korrektheits-Signal (eindeutig + konventionell ist dort fast hinreichend). In der Auswertung so ausweisen.
- **Open / next:** AP-E.2 Seeding — der Nutzer bereitet **10 Snapshots mit möglichst realen Fehlern** vor (Spezifikation besprochen: **Wiederholungen desselben Musters statt 10 verschiedener Typen**, sonst lässt sich das Gedächtnis nicht demonstrieren; Ground Truth je Fall notieren; ein Fehler pro Snapshot). Zusammen mit den 7 bestehenden ergibt das **17 Entscheidungen** → der `SMALL_SAMPLE`-Flag (n<10) fällt, Kalibrierungskurve wird möglich.
