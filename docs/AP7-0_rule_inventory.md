# AP7.0 — Rule Inventory (precondition for the rulebook split)

Source: `demo/smart-planning/runtime/runtime-files/llm-validation-fix-rules.md` (936 lines).
Purpose: every rule must land in exactly one card. After the split, verify against THIS table —
not against a single snapshot run (a run only exercises the rules it happens to trigger).

Status: **DRAFT — 2 blocking questions open (see bottom). No cards written yet.**

---

## Key finding: cards cannot be keyed by "EMPTY_FIELD" / "DUPLICATE_ID"

The authoritative `error_type` is `tag_error_type`, derived from the leading `[validate_*]` tag
(`identify_error_llm.derive_error_type_from_message`, AP3.6b-1). It is the **validator name**,
uppercased — NOT a semantic category:

    [validate_unique_ids]                     -> UNIQUE_IDS
    [validate_work_item_configs_completeness] -> WORK_ITEM_CONFIGS_COMPLETENESS

`EMPTY_FIELD` / `DUPLICATE_ID` are the *legacy* heuristic values from `identify_snapshot.py`,
which AP3.6a declared unreliable and dead.

**Consequence:** `validate_unique_ids` emits the SAME tag (`UNIQUE_IDS`) for both the duplicate
case and the empty-field case. The card split proposed in PT4_PLAN (`empty-field.md` vs
`duplicate-id.md`) is therefore **not selectable** at runtime. Cards must be keyed 1:1 on the
actual validator tag, or a new sub-classifier would be needed (= new logic, out of scope).

## Validator tags that actually exist (13)

    UNIQUE_IDS                                  <- rules exist (duplicate AND empty)
    DEMAND_ARTICLE_IDS                          <- rules exist (invalid reference)
    EQUIPMENT_PREDECESSOR_REFERENCES            <- rules exist (invalid reference, arrays)
    WORK_ITEM_CONFIGS_COMPLETENESS              <- rules exist (missing array element)
    DENSITY_VALUES                              <- rules exist (array_context statistics)
    WORK_PLAN_IDS                               <- no specific rules in the monolith
    START_END_OPERATION_EXISTENCE               <- no specific rules in the monolith
    DEMAND_UNIQUENESS                           <- no specific rules in the monolith
    EQUIPMENT_CONNECTIVITY                      <- no specific rules (warning-level)
    EQUIPMENT_DEPARTMENT_PRESENCE               <- no specific rules (warning-level)
    EQUIPMENT_UNAVAILABILITY_CONSISTENCY        <- no specific rules (warning-level)
    EQUIPMENT_WORKER_QUALIFICATION_COMPATIBILITY<- no specific rules (warning-level)
    WORKER_CONSISTENCY                          <- no specific rules (warning-level)

Note: the monolith's heading "## 3. Ungültige Referenzen (validate_demand_article_ids,
**validate_references**)" names a validator `validate_references` that does not exist in the
codebase. Stale documentation — carried over as-is, not invented away.

---

## Inventory: rule -> source lines -> target card

| # | Rule | Lines | Target card |
|---|------|-------|-------------|
| R1 | Error prioritisation (root cause before symptom, dependencies, severity order) | 7–34 | `_core.md` |
| R2 | Search-mode selection (`value` vs `empty_field`) + examples | 36–91 | `_core.md` |
| R3 | Investigation decision (`should_investigate` true/false) | 93–105 | `_core.md` |
| R4 | When is `array_context` useful / not useful (JA/NEIN list) | 109–123 | `_core.md` |
| R5 | **Principle:** filter `array_context` to the same group (department, workPlan, prefix) before deriving a value; state the filter in the reasoning | extracted from 208–244 | `_core.md` |
| R6 | Packaging equipment pattern analysis (empty `predecessors`: ID-clustering, sequence-length priority, functional coherence, string distance last) | 160–203 (superset) | **OPEN — see Q2** |
| R7 | Duplicate IDs: suffix numbering `_1`/`_2`, update all affected references | 286–327 | `unique-ids.md` |
| R8 | Empty ID fields: pattern recognition, find missing sequence number, fallback naming | 331–363 | `unique-ids.md` |
| R9 | Invalid references: never create new entries, correct the typo | 369–371 | `references.md` |
| R10 | PRESERVE EXACT FORMAT (spaces, underscores, case) when copying the correct ID | 373–377 | `references.md` |
| R11 | No duplicates in arrays — 5/6-step process (identify array, find bad ID, candidates, duplicate filter, functional coherence, pick best) | 379–443 | `references.md` |
| R12 | Typo correction, universal 9-step strategy (Levenshtein + duplicate filter + functional coherence + pattern matching + exact format) | 445–467 | `references.md` |
| R13 | Worked examples 1–5 (format preservation, spacing, prefix, pattern matching LT033→LT04, functional coherence BbU01→BPU01) | 469–582 | `references.md` |
| R14 | Analysis criteria + candidate ranking (functional coherence > pattern match > string similarity; constraint: no duplicate) | 584–595 | `references.md` |
| R15 | Placeholder detection FIRST (prefix-, pattern-, context-based; 5-step detection; replace vs. add) | 605–697 | `work-item-configs.md` |
| R16 | Action format for nested arrays: `update_field` on the WHOLE parent array, not on a nested index | 699–712 | `work-item-configs.md` |
| R17 | Standard strategy when no placeholder (copy structure/typical values from similar objects) | 714–770 | `work-item-configs.md` |
| R18 | Action catalogue: `update_field` (format + example) | 776–801 | `_core.md` |
| R19 | Action catalogue: `add_to_array` (format, rules, example) | 805–855 | `_core.md` |
| R20 | Action catalogue: `remove_from_array` (by index / by matching) | 859–908 | `_core.md` |
| R21 | Which action when? (prefer `update_field`, avoid `add_to_array`, avoid `remove_from_array`) | 912–937 | `_core.md` |
| R22 | Article-array statistical filtering — full worked examples (relDensityMin, dept/workPlan filtering, good vs. bad usage) | 208–282 | `density-values.md` |

**Deliberately dropped (duplicates, not rules):** lines 124–158 and the heading at 208 duplicate
the block at 160–203. Lines 124–158 are a strict subset of 160–203 (which additionally contains
the "ERGEBNIS für 70409" resolution). Only the superset is carried over. Nothing else is dropped.

---

## Proposed card set (keyed 1:1 on `tag_error_type`)

    _core.md                 always loaded          R1–R5, R18–R21
    unique-ids.md            UNIQUE_IDS             R7, R8
    references.md            DEMAND_ARTICLE_IDS, EQUIPMENT_PREDECESSOR_REFERENCES   R9–R14 (+R6?)
    work-item-configs.md     WORK_ITEM_CONFIGS_COMPLETENESS                          R15–R17
    density-values.md        DENSITY_VALUES                                          R22

Fallback for any tag without a card (WORK_PLAN_IDS, EQUIPMENT_CONNECTIVITY, …) and for an
untagged message: load `_core.md` only. **This loses nothing** — the monolith contains no
specific rules for those validators either; they are served by the generic action guidance.

---

## Open questions (blocking — do not split before these are answered)

**Q1 — Card granularity.** Key cards on the validator tag (`unique-ids.md` holding BOTH duplicate
and empty rules), or introduce a sub-classifier that separates empty vs. duplicate inside
`UNIQUE_IDS`? Recommendation: **validator tag**. It uses the existing, reliable, deterministic
signal and adds zero new logic — the sub-classifier would be exactly the "new architecture" the
AP7 scope guard forbids. Cost: `unique-ids.md` carries ~80 lines instead of ~40.

**Q2 — Where does R6 (packaging equipment pattern) belong?** The monolith states the problem as
"Leere predecessors in packagingEquipmentCompatibility" but never names the emitting validator.
Candidates: `EQUIPMENT_PREDECESSOR_REFERENCES` (references card) or `EQUIPMENT_CONNECTIVITY`
(no card today). Guessing wrong means the rule is never loaded in `cards` mode = silent rule loss,
the exact failure this inventory exists to prevent. Options: (a) put R6 in `references.md`,
(b) give it its own card mapped to both tags, (c) put it in `_core.md` (always loaded — safest,
costs tokens). Recommendation: **(a)**, with the option to move it once we see a real
packaging-predecessor error in the wild.
