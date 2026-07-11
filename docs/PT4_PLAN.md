# PT4 — Implementation Plan (Reference)

Project: "Agentic AI in der Produktion: Vom PoC zur Enterprise Solution —
Human-in-the-Loop Governance, MCP-Integration & Market Transferability"

This is the stable reference. Milestones and work packages below.
Status legend: [ ] open · [~] in progress · [x] done

---

## Acceptance criteria → work package mapping
- AK1 Automated validation & correction        → AP1
- AK2 Reasoning + confidence, ≥80% accepted     → AP1 + Evaluation
- AK3 Human-in-the-Loop workflow                → AP3 + AP4
- AK4 MCP integration into one workflow         → AP5
- AK5 Central dashboard                         → AP6
- AK6 Memory system                             → AP7

---

## Milestones
- [x] M0  Baseline & Scope
- [x] M1  Correction Proposal Layer (AP1)
- [x] M2  Persistence Layer (AP2)
- [x] M3  HitL Backend (AP3)
- [ ] M4  HitL Frontend (AP4)
- [ ] M5  MCP Integration (AP5)
- [ ] M6  Dashboard (AP6)
- [ ] M7  Memory System (AP7)
- [ ] M8  Evaluation & Demo (AP-E)

Critical path: AP1 → AP2 → AP3 → AP4 (demo-ready) → AP5 & AP6 → AP7.

---

## AP1 — Correction Proposal Layer  (Milestone M1)
Goal: The AI produces a reviewable **proposal** instead of auto-applying a correction.
Each proposal carries reasoning, a confidence score, status `pending_review`, and is
centrally findable. Nothing is applied. Vertical slice: error type `EMPTY_FIELD` only.

Real data structure note: the correction proposal is nested inside a wrapper
(`iteration`, `snapshot_id`, `original_error`, `error_analyzed`, `correction_proposal`).
New fields go INTO `correction_proposal`, not the wrapper.

Confidence formula:
confidence = 0.5 * llm_self_estimate      (LLM returns 0..1 in an extended prompt)
+ 0.3 * schema_valid           (1 if schema validation passed, else 0)
+ 0.2 * memory_support         (AP7; 0 for now)
Special case: action == "manual_intervention_required" → confidence = 0.0
### Sub-packages
- [ ] **AP1.1 — Extend schema**
  File: `demo/smart-planning/runtime/correction_models.py`
  Add to `CorrectionProposal` (additive, optional/defaulted):
  `confidence_score: Optional[float] = None` (validate range 0.0–1.0),
  `status: str = "pending_review"` (allowed: pending_review, approved, rejected,
  modified, applied). Backward-compatible with existing proposal JSON. Touch no other file.
  DoD: old proposal JSON still parses; confidence 1.5 raises a validation error.

- [ ] **AP1.2 — Split pipeline + stop**
  Files: `demo/agents/sp_tools_config.py`, `demo/agents/sp_agent.py`
  Split correction pipeline into `generate_proposal` (validate → identify_error_llm →
  generate_correction_llm → validate_correction_schema_llm) and `apply_after_review`
  (apply_correction → update_snapshot → validate). Stop the auto-iteration loop
  (`MAX_CORRECTION_ITERATIONS`) as soon as a proposal with status `pending_review` exists.
  DoD: pipeline halts after first proposal; nothing is applied automatically.

- [ ] **AP1.3 — Confidence computation**
  Files: `demo/smart-planning/runtime/generate_correction_llm.py` (extend prompt to
  request an LLM self-estimate 0..1), plus wherever schema validity is known.
  Implement the formula above; write `confidence_score` into the proposal.
  Enforce `manual_intervention_required → 0.0`.
  DoD: every proposal has a reproducible confidence_score.

- [ ] **AP1.4 — Central proposal record**
  Persist each proposal additionally at a central, stable location with a stable
  `proposal_id` (file-based JSON for now; DB migration happens in AP2). Keep the existing
  nested `iteration-N/llm_correction_proposal.json` untouched.
  DoD: all open proposals are findable centrally by proposal_id.

DoD (AP1 overall): a snapshot with an empty `demandId` yields exactly one proposal with a
confidence score, status `pending_review`, centrally findable — and nothing is applied.

---

## AP2 — Persistence Layer  (M2)
DB backbone (SQLite local → Azure SQL target) via SQLAlchemy + Alembic.
Tables: sessions, messages (user+assistant), agent_runs (incl. tokens/cost),
snapshots_meta, proposals, reviews (decision, final_value, comment), memory_items (empty
until AP7). New dir `demo/db/` (models, session, repository). Alembic migration.
DoD: a full run creates rows in sessions/messages/agent_runs/proposals; reviews +
memory_items tables exist.

## AP3 — HitL Backend  (M3)
Flask blueprint `demo/routes/review.py`. Endpoints:
GET /api/review/proposals, GET /api/review/proposals/<id>,
POST .../approve, POST .../reject, POST .../modify.
Apply correction (via `apply_after_review`) ONLY after approve/modify, then re-validate,
store revalidation result. Idempotent (status-check first). DoD: all 5 endpoints testable;
correction applied only after approval; reject changes nothing.

## AP4 — HitL UI  (M4)
Files: `demo/ui/review.html`, `demo/ui/scripts/review.js`, CSS in styles.css.
Before/after diff: old value red/strikethrough, suggested value green; reasoning,
confidence, evidence; buttons Approve / Modify / Reject + comment field.
DoD: full loop demoable in UI. **First point the whole chain is demo-ready.**

## AP5 — MCP Integration  (M5)
`demo/mcp/server.py`, `demo/mcp/tools.py`. Tools: get_pending_reviews,
get_review_details, approve_correction, reject_correction, modify_correction,
get_snapshot_status, get_dashboard_metrics. One end-to-end enterprise case:
Outlook/email notification with deep link on new pending review. Prototype adapter is
acceptable. DoD: pending review triggers a notification with working link; tools callable.

## AP6 — Dashboard  (M6)
`demo/routes/dashboard.py` → GET /api/dashboard/metrics. Plus `demo/ui/dashboard.html`.
KPIs: validations, proposals, approval/reject/modify rate, avg confidence,
confidence-vs-human-decision (calibration), top error types, revalidation success rate,
avg handling time, est. tokens/cost, open reviews. All derived from existing tables.
DoD: dashboard shows live KPIs incl. approval rate and calibration.

## AP7 — Memory System  (M7) — LAST
`demo/memory/{short_term,long_term,retrieval}.py`, optional consolidate_job.py.
Short-term: current session context. Long-term: historical cases from `memory_items`
(built from reviews). Retrieval = case-based reasoning: on a new error, find similar past
cases, pass top-k as evidence into proposal generation, set memory_support=1 in the
confidence formula. DoD: new error → similar past case found → better-justified proposal.

## AP-E — Evaluation & Demo  (M8)
Test catalog (missing fields, invalid refs, approve/reject/modify, a memory case).
Measure ≥80% accepted-without-modification against the M0 baseline. 11-step demo.

## Out of scope (parked)
Continuous Learning Agent + GitHub PR automation. Revisit only after M0–M8.