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
- [x] M4  HitL Frontend (AP4)
- [x] M5  MCP Integration (AP5)
- [x] M6  Dashboard (AP6)
- [x] M7  Memory System (AP7)
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

Confidence formula (REVISED 2026-07-11, user decision — see PROJECT_LOG "AP4.5"):
confidence = 0.5 * llm_self_estimate      (LLM returns 0..1 in an extended prompt, calibrated
                                           against an A–D rubric)
+ 0.3 * value_grounded         (1 if the proposed value is deterministically VERIFIABLE for its
                                field class, else 0 — CLASS-AWARE since AP-E.0:
                                  identity field  -> unique in its array AND follows the array's
                                                     ID convention (majority shape)
                                  reference field -> the referenced object exists
                                  value field     -> the identical value sits on the same field
                                                     of a comparable object (or is a member of
                                                     such a list)
                                  add_to_array    -> the same checks applied to the NEW object
                                Before AP-E.0 the check asked "is the value already in the data?"
                                for EVERY field — backwards for identity fields, where a new
                                unique ID must NOT be in the data. See compute_value_grounded.)
+ 0.2 * memory_support         (0 until AP7.2; then GRADED 0 / 0.5 / 1.0 from the episodic
                                layer only — see "memory_support — binding definition" in AP7.
                                It must NOT be derived from the rulebook cards: those load on
                                every proposal, so the term would be constant 1 and repeat the
                                `schema_valid` mistake.)
Special case: action == "manual_intervention_required" → confidence = 0.0

Why the middle term changed: it used to be `schema_valid`, which is ALWAYS 1 — the proposal is
validated against the Pydantic model immediately after being built, so the term was tautological
and the score collapsed to a near-constant 0.775 (measured: 7 of 8 proposals). Worse, the LLM's
self-estimate cannot tell "I read this value from the data" from "I made it up": it rated an
INVENTED de-duplication ID at 0.9 in exactly the case where it was wrong. `value_grounded` is the
deterministic signal that separates the two. `schema_valid` is still recorded as its own field.
### Sub-packages
- [x] **AP1.1 — Extend schema**
  File: `demo/smart-planning/runtime/correction_models.py`
  Add to `CorrectionProposal` (additive, optional/defaulted):
  `confidence_score: Optional[float] = None` (validate range 0.0–1.0),
  `status: str = "pending_review"` (allowed: pending_review, approved, rejected,
  modified, applied). Backward-compatible with existing proposal JSON. Touch no other file.
  DoD: old proposal JSON still parses; confidence 1.5 raises a validation error.

- [x] **AP1.2 — Split pipeline + stop**
  Files: `demo/agents/sp_tools_config.py`, `demo/agents/sp_agent.py`
  Split correction pipeline into `generate_proposal` (validate → identify_error_llm →
  generate_correction_llm → validate_correction_schema_llm) and `apply_after_review`
  (apply_correction → update_snapshot → validate). Stop the auto-iteration loop
  (`MAX_CORRECTION_ITERATIONS`) as soon as a proposal with status `pending_review` exists.
  DoD: pipeline halts after first proposal; nothing is applied automatically.

- [x] **AP1.3 — Confidence computation**
  Files: `demo/smart-planning/runtime/generate_correction_llm.py` (extend prompt to
  request an LLM self-estimate 0..1), plus wherever schema validity is known.
  Implement the formula above; write `confidence_score` into the proposal.
  Enforce `manual_intervention_required → 0.0`.
  DoD: every proposal has a reproducible confidence_score.

- [x] **AP1.4 — Central proposal record**
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
acceptable. The automatic notification was used for the M5 acceptance proof and subsequently
disabled by user decision; proposal generation no longer sends email. The chat plus menu exposes a
dedicated email agent: it creates a
persistent preview from the user's requested context, supports conversational revisions and sends
through the configured provider only after an explicit `Bitte absenden`. Snapshot/review facts and
the deep link are included only when requested. DoD-Nachweis: the original pending-review
notification with working link was demonstrated for M5; current operation sends email exclusively
through the callable conversational draft/revise/confirm/send flow.

## AP6 — Dashboard  (M6)
Kurzbeschreibung:
`demo/routes/dashboard.py` → GET /api/dashboard/metrics. Plus `demo/ui/dashboard.html`.
KPIs: validations, proposals, approval/reject/modify rate, avg confidence,
confidence-vs-human-decision (calibration), top error types, revalidation success rate,
avg handling time, est. tokens/cost, open reviews. All derived from existing tables.
DoD: dashboard shows live KPIs incl. approval rate and calibration.
Langbeschreibung: 
AP6 — Dashboard
Langform. Eine neue Section in der bestehenden UI, die Kennzahlen aus der Datenbank berechnet und darstellt. Backend liefert eine Metrik-API, Frontend zeigt KPI-Karten und ein bis zwei Diagramme.
Technik.
Backend – demo/routes/dashboard.py:

GET /api/dashboard/metrics
Vorgeschlagene Kennzahlen (du entscheidest final beim Start des Pakets):
Anzahl Validierungen, Anzahl Vorschläge
Approval / Reject / Modify Rate
Ø Confidence Score
Confidence vs. tatsächliche menschliche Entscheidung (Kalibrierung) – wichtigste Qualitätskennzahl
Häufigste Fehlerarten
Revalidation Success Rate
Ø Bearbeitungszeit
Geschätzte Token/Kosten
Anzahl offener Reviews
Alle berechenbar aus proposals, reviews, agent_runs, snapshots_meta – keine neuen Datenquellen nötig.
Frontend – ui/dashboard.html + ui/scripts/dashboard.js:
KPI-Karten oben, darunter Balkendiagramm „Fehlerarten" und Confidence-Verteilung (Chart.js).
Tabelle offener Reviews mit Link in die Review-UI.
Definition of Done. Dashboard zeigt Live-Zahlen aus echten Durchläufen inkl. Approval-Rate und Confidence-Kalibrierung. → M6
## AP7 — Memory System  (M7) — LAST

### Redefinition 2026-07-12 (why this section was rewritten)
The original AP7 assumed a single long-term memory (episodic cases) and a `short_term.py`
still to be built. Three findings forced a rewrite:

1. **Short-term memory already exists** (built in AP2, never named as such): session history
   is persisted in `messages`, reloaded from DB on restart (`web_server.get_session_history`),
   truncated to a sliding window (`get_recent_messages`, `CHAT_HISTORY_CONFIG`) and passed as
   `chat_history` into every agent call. AP7 adds nothing here → status: **done**, only
   documented, not rebuilt.
2. **Episodic memory alone cannot carry AP7 yet — cold start.** Measured 2026-07-12:
   `proposals=9`, `reviews=6`, `memory_items=0`. Case retrieval over 6 cases will usually
   find nothing. The DoD "new error → similar past case found" is not reliably demonstrable
   on this data volume.
3. **The reviews contain more than decisions — they contain rules.** The `modify` comment of
   review #5 is a fully formed domain rule in prose ("all 16 other raspberry base materials of
   department AfG have BA01=30/1; sequence 'P' is the mode"). That is procedural knowledge, and
   it is the substrate the 936-line `llm-validation-fix-rules.md` should have been made of.

Consequence: AP7 builds **long-term memory in two layers**, both fed from `reviews`. They have
different jobs and must not be confused:
- **Rulebook layer (cards)** → makes the *proposal better*  → serves AK2 (≥80% accepted)
- **Episodic layer (cases)** → makes the *confidence honest* → serves the calibration quality
  criterion (defined in AP6). Note: AK2 literally only demands ≥80% accepted — calibration is our
  own quality criterion. Do not overclaim it as AK2.

Naming note: the rulebook layer is deliberately NOT labelled "procedural memory" in the strict
CoALA sense. The cards mix production rules ("if field empty → derive from neighbours") with
domain facts ("all 16 raspberry base materials of dept. AfG have BA01=30/1") — procedural and
semantic knowledge respectively. "Rulebook layer" is the honest, defensible term.

### SCOPE GUARD — what AP7 is NOT (2026-07-12, user decision, non-negotiable)
AP7 introduces **no new architecture**. It is (a) a refactoring of an existing file plus a config
flag, and (b) a write/read path onto an already existing DB table. Explicitly out of scope:
- **No graph structures.** No edges or dependencies between cards, no graph-based prompt assembly.
  `cards` mode = flat, selective loading: `_core.md` + the card(s) for this error. Nothing more.
  (Graph-based vs. monolithic prompt architectures are the subject of a SEPARATE bachelor thesis.
  That question must not bleed into PT4 — it would blow the project's scope.)
  *Note (AP7.5): which cards get loaded is decided by the agent from a plain-language index, but
  the cards themselves stay a FLAT set — no edges between them. Still not a graph.*
- **No new metric dimensions** (hallucination rate, traceability, robustness). PT4 is measured
  against the AKs in this document, nothing else.
- **No rewrite of `agent_config.py` into markdown.** Deterministic config and logic stay code;
  only the domain heuristics move into cards.

### memory_support — binding definition (supersedes "AP7; 0 for now" in AP1)
`memory_support` is derived from the **episodic layer only**. It must never be derived from the
procedural layer: the rulebook cards are loaded on *every* proposal, so a term derived from them
is constant 1 — the exact `schema_valid` mistake again, and worse: it would shift every score by
+0.2 (typical case 0.775 → 0.975), pushing all proposals to the ceiling and destroying calibration.
Graded, deterministic (like `value_grounded`):
- `0.0` — no similar past case found
- `0.5` — similar case(s) found, proposed action matches the pattern, but no value precedent
- `1.0` — similar case found AND the proposed value follows the pattern a human confirmed there

### Sub-packages
- [x] **AP7.0 — Rulebook split + A/B switch**  *(no LLM, no DB, lowest risk — start here)*
  **DONE 2026-07-12.** Card names differ from the draft below: the authoritative `error_type` is
  the `[validate_*]` tag (AP3.6b), and `validate_unique_ids` emits the SAME tag for the empty AND
  the duplicate case — so `empty-field.md` / `duplicate-id.md` would never have been selectable.
  Cards are keyed on the validator tag instead: `_core.md`, `unique-ids.md`, `references.md`,
  `work-item-configs.md`, `density-values.md`. The rule inventory (`docs/AP7-0_rule_inventory.md`)
  caught this BEFORE a line was cut — 22/22 rules carried over, verified per rule.
  A/B over 3 snapshots: **−16 % prompt tokens, identical proposals** (see PROJECT_LOG; one
  regression was found and fixed — the cards had lost the implicit cross-section hint that the
  workItemConfigs order is a PROCESS order).

  Files: new `demo/skills/` (`_core.md`, `empty-field.md`, `duplicate-id.md`,
  `invalid-reference.md`, `missing-array-elements.md`), `demo/agent_config.py`,
  and the three loaders `identify_error_llm.py`, `generate_correction_llm.py`,
  `validate_correction_schema_llm.py`.
  Split the 936-line `llm-validation-fix-rules.md` along `error_type`. Drop the three duplicated
  "Domain-Intelligence bei array_context" blocks (lines 124/160/208, two of them verbatim copies).
  Switch in `agent_config.py`, same pattern as `HUMAN_IN_THE_LOOP`:
  `RULEBOOK_MODE = os.getenv("RULEBOOK_MODE", "monolith")`  → `monolith` | `cards`.
  `monolith` = today's behaviour, byte-identical; the old file stays in the repo untouched.
  `cards` = load `_core.md` + the card for the identified `error_type` only.

  **Rule inventory first — mandatory.** Before cutting the file, produce an inventory:
  every rule → which `error_type` → which target card. Split against the inventory, then verify
  against it. Reason: "same snapshot runs green" only exercises the rules that one snapshot
  happens to trigger; when splitting 936 lines (including the deliberate removal of the three
  duplicated "Domain-Intelligence bei array_context" blocks, lines 124/160/208) a rule can drop
  out silently and stay unnoticed until it is needed in production.

  Open design decision to settle at the start of AP7.0: what belongs in `_core.md` (cross-cutting:
  error identification, prioritisation, search-mode selection, the action catalogue) vs. what is
  error-type specific. This is the one real design choice in this sub-package.

  DoD: (1) every rule of the inventory is present in exactly one card — nothing lost, no duplicates
  reintroduced; (2) the same snapshot runs green in both modes; (3) `cards` mode measurably reduces
  prompt tokens per run.

- [x] **AP7.1 — Episodic write path**  *(DONE 2026-07-12 — 6 reviews backfilled; every new review
  writes exactly one case; one legacy label repaired deterministically from the run artifact:
  `DUPLICATE_ID` → `DENSITY_VALUES`, the AP3.6a misclassification proven in real data)*
  Files: new `demo/memory/long_term.py`, `demo/db/repository.py`, review commit path.
  On every completed review, write one case into `memory_items`: error signature
  (`error_type`, field, entity/context), AI proposal, human decision, final value, and the
  human comment. One-off backfill of the 6 existing reviews.
  DoD: `memory_items` is non-empty; every new review adds exactly one case.

- [x] **AP7.2 — Retrieval + honest confidence**  *(DONE 2026-07-12. Retrieval keys on
  `affected_entity_pattern`, NOT on `error_type` — the case base mixes legacy labels
  (`EMPTY_FIELD`) with tags (`UNIQUE_IDS`), so an error_type lookup would miss the very cases it
  needs. Proven: `demands[].demandId` unites cases #1/#4/#5 across both label worlds.
  `memory_support` is graded 0 / 0.5 / 1.0 and includes a NEGATIVE precedent (the AI is repeating
  a value a human already threw out). `formula_version` v0/v1/v2 stamped on all proposals.)*
  Files: new `demo/memory/retrieval.py`, `generate_correction_llm.py`, proposal schema.
  On a new error: match the error signature against `memory_items`, pass top-k cases as
  evidence into the proposal prompt, compute the graded `memory_support` above.

  **Two effects to handle, or the calibration curve lies:**
  1. *Cold-start ceiling.* While `memory_support = 0`, the maximum reachable confidence is
     `0.5·1 + 0.3·1 + 0.2·0 = 0.8`. Until the seeding run, every score is capped at 0.8 and the
     system looks systematically underconfident. This is correct behaviour (no precedent → less
     certain) but it DOMINATES the AP6 calibration curve. Document it; do not hard-code bins or
     thresholds in the dashboard that assume a 0–1 spread.
  2. *Mixed formula versions.* The 9 proposals already in the DB carry a `confidence_score`
     computed under the old formula and are never recomputed (same pattern as the known issue
     where confidence is not recomputed after a schema fix). After AP7.2 the dashboard would mix
     scores from two formula generations in one curve. Fix: add `formula_version` to the proposal
     record and either filter or recompute in AP6.

  DoD: `memory_support` takes at least two distinct values across a run set; the confidence score
  is no longer near-constant; every proposal carries a `formula_version`.

- [x] **AP7.3 — Memory visible in the review UI**  *(DONE 2026-07-12 — `GET /proposals/<id>/memory`
  + a detail section showing N similar cases with the human's decision AND their reasoning in
  plain text. Verified: 8 of the open proposals surface past cases.)*
  Show the reviewer "N similar past cases, M approved" with a link. Decision support, no
  change to the confidence logic.
  DoD: the memory effect is visible in the demo, not only in a number.

- [x] **AP7.4 — Short-term memory: document, don't rebuild**  *(DONE 2026-07-12)*
  No new capability. Consolidate the existing logic under `demo/memory/short_term.py` as a
  thin, named façade over what `web_server` already does.

  **CORRECTION (2026-07-12, found while building AP7.4):** an earlier draft of this sub-package
  said to "remove the `_get_review_decisions()` workaround once AP7.1 makes review outcomes
  structurally available". **That was wrong and must not be done.** `_get_review_decisions()`
  is NOT a workaround for missing memory: it already reads the decisions from the DB
  (`repo.get_decisions_for_snapshot`) and only uses the chat history to find the SNAPSHOT ID.
  It is the bridge between the Review Board and the chat — the fix for the bug where the chat
  answered "what was the solution?" with the AI's proposal after a human had overruled it
  (PROJECT_LOG, BUG 1). AP7.1 does not make it redundant. Removing it would reopen that bug.
  It stays exactly where it is.

  DoD: session context has one named owner; behaviour unchanged.

- [x] **AP7.5 — Drop-in rule cards (added 2026-07-12, user requirement)**
  Not in the original AP7 draft. It was forced by a real defect: the user created a card in the
  skills folder and it was **silently never loaded** — routing derived the validator tag from the
  FILENAME, so `umgang-mit-zwei-falsche-nummern.md` became the tag `UMGANG_MIT_ZWEI_FALSCHE_NUMMERN`,
  which no validator emits. A rule that quietly does nothing is the worst possible outcome — the
  same failure class the AP7.0 inventory exists to prevent.

  User requirement, verbatim: *"der Agent soll immer jederzeit Zugriff auf alles haben und
  intelligent entscheiden. Ich will einfach Beschreibungen hinzufügen, in meiner einfachen
  Sprache, und erwarte, dass sie berücksichtigt werden."*

  What it does:
  * The identification step (which runs anyway → **no extra LLM call**) sees a plain-language
    **index of ALL cards** (filename + `description`) and returns `relevant_cards`. The agent
    therefore has access to the entire rulebook at all times but only loads what it needs —
    NOT everything into every prompt (that would be the monolith again and does not scale).
  * The filename→tag convention is REMOVED (it was the trap). `applies_to` is now an optional
    shortcut for a guaranteed hit; without it the agent routes on the description alone.
    **A domain expert needs no tag and no developer.**
  * Cards are read through the `StorageManager`: `STORAGE_MODE=LOCAL` → `demo/skills/`,
    `STORAGE_MODE=AZURE` → blob prefix `skills/`. Rules can be maintained in the storage account
    **without redeployment**.
  * `demo/skills/_VORLAGE.md` documents the pattern; files starting with `_` are never cards.

  Verified end-to-end: on snapshot `84f5af97` (`relDensityMin: -2`) the agent picked the user's
  card by itself and the proposal changed from `1.14` (median of neighbours) to `2` (sign flipped).
  DoD: a new .md file with a plain-language description is honoured without any code change. ✔

  **Risk this exposed:** a drop-in card can OVERRIDE established rules with nobody reviewing code.
  That is the strongest argument for AP-X never writing cards without human approval, and for a
  card-conflict check (backlog).

DoD (AP7 overall): a new error is answered with a proposal that cites human-confirmed precedent,
and its confidence score reflects whether such precedent existed. Both rulebook modes remain
switchable for the evaluation. → **MET 2026-07-12.**

### Note for AP-E (evaluation)
AP7.0 creates a clean A/B experiment — *monolithic system prompt vs. selectively loaded rule
cards* — measurable on tokens per run, approval-without-modification rate (AK2 ≥80%) and latency.
With 6 reviews this shows the *mechanism*; statistically meaningful numbers require a seeding run
(a batch of snapshots reviewed through the UI) before AP-E. This is a known, accepted gap.

### Handover to AP-E
AP7 hands four open items to AP-E. They are NOT AP7 work and do not block M7 — they are listed
as sub-packages in the AP-E section below: the `value_grounded` blocker (AP-E.0), the seeding run
(AP-E.2), the finished test catalog (AP-E.1), and the card-conflict check (backlog).

---

## AP-E — Evaluation & Demo  (M8)

Goal: measure **≥80 % accepted-without-modification** (AK2) against the M0 baseline, show a
calibrated confidence, and run the 11-step demo.

**Ground rule for this whole package: human decisions are NEVER fabricated.** `memory_items` and
`reviews` are the ground truth of the system. Constructing INPUT (injecting known errors into
snapshot copies) is legitimate and is what AP-E.1 does. Constructing an approve/reject/modify is
not. Case #7 in PROJECT_LOG is the cautionary tale: one invented `reject` made the system suppress
a demonstrably correct proposal from then on.

### Sub-packages

- [x] **AP-E.0 — BLOCKER: `value_grounded` is inverted for the ID class**  *(FIXED 2026-07-12)*
  **Result:** the two exactly-correct ID proposals moved 0.44 → 0.74 and 0.445 → 0.745; the wrong
  density value stayed at 0.475. Correlation with correctness restored. Formula generation bumped
  to **v3** (weights unchanged, but the SEMANTICS of the 0.3 term changed — v2 and v3 scores are
  NOT comparable, so AP6 must pin one generation).
  Files: `demo/smart-planning/runtime/generate_correction_llm.py` (`compute_value_grounded`).
  Belongs to the confidence formula (AP1/AP4.5), surfaced by the AP7 test catalog.

  **The defect.** `value_grounded` asks "is the proposed value provable from the data?". For a NEW
  unique ID the answer must be NO by construction — if the ID already existed in the data it would
  be a DUPLICATE, i.e. wrong. The 0.3 term is therefore structurally unsatisfiable for the whole
  ID-generation class — which is exactly PT4's vertical slice (empty `demandId`).

  **Measured on the test catalog (2026-07-12):**

  | catalog | error type | proposal | ground truth | correct? | value_grounded | confidence |
  |---|---|---|---|---|---|---|
  | 01 | UNIQUE_IDS (empty) | `D100079_001` | `D100079_001` | **YES, exact** | 0.0 | **0.44** |
  | 02 | UNIQUE_IDS (dup) | `D100099_002` | `D100099_002` | **YES, exact** | 0.0 | **0.44** |
  | 03 | DEMAND_ARTICLE_IDS | `100112` | `100112` | YES, exact | 1.0 | 0.775 |
  | 04 | DENSITY_VALUES | `1.14` | `1.017` | **NO** | 1.0 | **0.75** |

  On this sample the score is **anti-correlated with correctness**. A calibration curve built on it
  measures this defect, not the system. Same failure class as the old `schema_valid` term, but
  worse: not merely uninformative — inverted for an entire error class.

  **Direction (user decision pending).** `compute_value_grounded` ALREADY detects the case and says
  so in its own message ("Identitätsfeld: … muss neu/eindeutig sein und ist daher grundsätzlich
  nicht aus den Daten belegbar"). It just returns 0 instead of testing the criterion that is
  correct for this class: *does the value follow the detected ID pattern AND is it unique in the
  target array?* That is exactly as deterministic as today's test.
  DoD: on the test catalog, confidence correlates with correctness instead of against it.

- [x] **AP-E.1 — Test catalog**  *(DONE 2026-07-12)*
  `demo/eval/build_test_catalog.py`. Four snapshots on the Smart-Planning **TEST** instance
  (`vm-t-…-test02…`, cca-dev.com — user-approved), named `PT4-TEST-*`, each with exactly ONE
  injected error confirmed by the **real server-side validator**, ground truth recorded in
  `metadata.txt`. All four rule cards are covered (`UNIQUE_IDS` and `DENSITY_VALUES` did not occur
  in any pre-existing snapshot at all).

  | # | snapshot | injected | validator says | ground truth |
  |---|---|---|---|---|
  | 01 | `e92b3ee2` | empty `demandId` | `[validate_unique_ids] must not be empty` | `D100079_001` |
  | 02 | `7d2de27d` | duplicate `demandId` | `[validate_unique_ids] Duplicates: D100099_001` | `D100099_002` |
  | 03 | `17a7c1e3` | typo in `articleId` | `[validate_demand_article_ids] Missing: 100112X` | `100112` |
  | 04 | `84f5af97` | negative `relDensityMin` | `[validate_density_values] invalid: -2` | `1.017` |

  **Two traps documented so nobody steps in them again:** (1) `validate_snapshot.py` only FETCHES
  the message list, it does NOT trigger the validation job — it reported "0 errors, snapshot is
  valid" on a demonstrably broken snapshot (the `REVALIDATION_PRE_AP33D` false green). Always call
  `trigger_server_validation` first. (2) Every freshly crawled snapshot carries a real base error
  (article 124211 without `workItemConfigs`) that the prioritiser ranks ABOVE the injected one.
  Repaired using the values a human confirmed in memory case #6 — no invented values.

- [ ] **AP-E.2 — Seeding run (needs a HUMAN)**
  7 open proposals are queued, exactly one per snapshot, all four error types covered. A case only
  enters `memory_items` through a real human review. **Do AP-E.0 first** — otherwise you review
  against a confidence that is provably inverted for half the error types.
  DoD: enough decided cases that `SMALL_SAMPLE` (n < 10) clears and a calibration curve is possible.

- [ ] **AP-E.3 — A/B: monolithic prompt vs. rule cards**
  The `RULEBOOK_MODE` switch (AP7.0) is the experiment: same snapshot, two arms.
  First run (3 snapshots, 2026-07-12): **−16 % prompt tokens (81.962 → 68.920), identical
  proposals**, cost 0.2166 $ → 0.1839 $. It also exposed a real regression (the cards had lost the
  implicit hint that the `workItemConfigs` order is a PROCESS order) — the value of the experiment.
  **Disclosure requirement:** the card was fixed AFTER seeing that result, so the `1ef11903` figure
  is a re-measurement. Say so in the write-up.
  DoD: A/B over the test catalog + the real snapshots, reported on tokens, acceptance rate, latency.

- [ ] **AP-E.4 — Measurement + 11-step demo**
  ≥80 % accepted-without-modification vs. the M0 baseline; calibration curve pinned to ONE
  confidence generation (`?formula_version=v2` — see AP6); memory case shown live in the review UI.

- [ ] **AP-E.5 — Repo-Housekeeping** *(vor der Abgabe / dem Demo-Tag)*
  Bestandsaufnahme 2026-07-12. **Wichtig vorweg: das Repo ist NICHT vermüllt.** Kein toter Test-
  code, keine Wegwerf-Skripte, kein `zArchive`. Es gibt wenig echten Abfall — dafür ein echtes
  Hygieneproblem und, wichtiger, eine Reihe von Dateien, die man beim Aufräumen NICHT anfassen darf.

  **A) Das eigentliche Problem: nichts ist committet.**
  16 geänderte Dateien + 7 unversionierte Pfade — die **komplette AP7-Arbeit** liegt uncommittet:
  `demo/skills/`, `demo/memory/`, `demo/eval/`, `demo/rulebook_loader.py`, die Alembic-Migration
  `2f47c4554ece`, `docs/AP7-0_rule_inventory.md`. Ein Rechnerausfall kostet alles. **Das ist die
  dringendste Aufräum-Aufgabe, nicht das Löschen von Dateien.**

  **B) Echter Abfall (löschen ist sicher):**
  - `demo/__pycache__/` (9 Verzeichnisse im Projektcode) — regenerierbar, bereits gitignored.
  - `demo/config/` — **leeres Verzeichnis**.
  - `demo/logs/` — 35 Logdateien von Januar bis heute (`chat_2026*.log`, `web_2026*.log`),
    gitignored. Nichts davon wird gelesen.

  **C) Zu klären (Nutzerentscheidung, KEIN Blindlöschen):**
  - `docs/Zwischenstand-Abschluss-AP2.md` — Statusbild vom 2026-07-08, inhaltlich überholt durch
    `PROJECT_LOG.md` + diesen Plan. Löschen oder als historisches Dokument behalten?
  - `docs/AP5_AP6_DOCUMENTATION.md` — unversioniert, überschneidet sich mit dem PROJECT_LOG.
    Ist das ein eigenständiges Abgabe-Dokument? Dann behalten und committen.

  **D) FINGER WEG — sieht aus wie Müll, ist aber tragend:**
  - **`demo/smart-planning/runtime/runtime-files/llm-validation-fix-rules.md`** — die alte
    936-Zeilen-Datei mit ihren bekannten Schwächen (3× duplizierter Block usw.). Sie sieht aus wie
    ein Überbleibsel und ist **der „Vorher"-Arm der A/B-Messung** (`RULEBOOK_MODE=monolith`).
    **Wer sie löscht, vernichtet die Baseline.** Byte-Identität ist Teil der DoD.
  - **`demo/smart-planning/Snapshots/`** — 13 Snapshots. Gitignored, aber der Audit-Trail: die
    `iteration-*/llm_identify_response.json` werden von der Memory-Legacy-Reparatur gelesen, und
    die Ground Truth des AP-E-Testkatalogs steht in den `metadata.txt`.
  - **`demo/main.py`** — sieht nach totem CLI aus, wird aber von `agents/rag_agent.py` importiert
    (`main.LOGGING_CONFIG`).
  - **`demo/smart-planning/runtime/identify_snapshot.py`** — sein `error_type` ist tot (AP3.6a),
    die Datei selbst macht aber die eigentliche Suche.
  - `demo/alembic/versions/` (5 Migrationen) — die Historie der DB. Nie aufräumen.

  DoD: alles committet; B) gelöscht; C) entschieden; D) nachweislich unangetastet
  (`RULEBOOK_MODE=monolith` liefert weiterhin die byte-identische Originaldatei).

### Backlog (non-blocking)
- **Conflict check between rule cards.** A drop-in card can override an established rule with
  nobody reviewing code — it happened: the user's `umgang-mit-zwei-falsche-nummern.md` overruled
  `density-values.md` (1.14 → 2). Harmless here, but it must be visible before it bites.
- Three `memory_items` still carry the legacy label `EMPTY_FIELD` (their run artifacts are gone, so
  the real tag was deliberately NOT guessed). Harmless: retrieval matches on
  `affected_entity_pattern`, which unites them correctly across both label worlds.

## Out of scope (parked)
Continuous Learning Agent + GitHub PR automation. Revisit only after M0–M8.

**AP-X — Rule distillation agent (parked, concept fixed 2026-07-12).** A separate agent reads the
day's completed `reviews` — NOT the chat history: approve/reject/modify and the reasoning live in
`reviews.decision` / `reviews.comment`, the chat only ever contains the AI proposal (hence the
`_get_review_decisions()` workaround) — and proposes edits to the `demo/skills/` cards as a diff.
Human approval required (project rule 3); versioned via git. Prerequisites: AP7.0 (the cards must
exist before an agent can edit them) and AP7.1 (the cases must exist before rules can be distilled).
Known risks to design for: rule bloat (an agent appending daily rebuilds the monolith in small),
contradiction between new and existing rules, missing eviction. This is what turns the rulebook
from a static prompt into real procedural memory — a memory nothing ever writes to is just a prompt.
