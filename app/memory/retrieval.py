"""
Long-term (episodic) memory — the read path (PT4 / AP7.2, entity-precise since 2026-07-31).

Case-based reasoning: on a new error, find what humans decided on similar errors before, hand
those cases to the LLM as evidence, and turn the outcome into `memory_support` for the
confidence score.

Two keys, in order of authority:
  1. `affected_entity_pattern` (index-normalised path, e.g. `articles[].relDensityMin`) — decides
     which cases are the SAME KIND of error. (Not `error_type`: the case base mixes legacy labels
     like EMPTY_FIELD with the authoritative [validate_*] tags; the pattern unites them.)
  2. `affected_entity_id` (e.g. `articles:100005`) — decides whether a past VALUE is authoritative
     for THIS object. A corrected value is object-specific: article 100005's density (1.017) is NOT
     the truth for a different article, even though both share the pattern `articles[].relDensityMin`.
     So a value counts as a precedent ONLY for the SAME entity. Same-pattern-but-other-entity cases
     are shown to the model as a METHOD hint, never as a value to copy — otherwise the memory would
     itself introduce a hallucination (one article's constant leaking onto another).
"""
from typing import Any, Optional

from core.agent_config import MEMORY_MODE
from db import repository as repo
from memory.long_term import entity_pattern, entity_key

#: Only decisions a human actually made carry evidence.
_DECIDED = ("approve", "modify", "reject")

#: Array name -> its identity field, to resolve the current error's entity from search results.
ENTITY_IDENTITY_FIELD = {
    "articles": "articleId",
    "demands": "demandId",
    "workPlans": "workPlanId",
    # MUST stay identical to generate_correction_llm.ENTITY_IDENTITY_FIELD (#7): the memory key
    # built here (read path) has to match the target_entity_id the guard records (write path).
    "equipment": "equipmentId",
    "workerAvailability": "workerId",
    "workerQualifications": "workerId",
    "packagingEquipmentCompatibility": "packaging",
}


def current_entity_key(target_path: Optional[str], original_object: Optional[dict]) -> Optional[str]:
    """Canonical entity key for the CURRENT error, from the search result's original object."""
    if not target_path or not isinstance(original_object, dict):
        return None
    array = target_path.split("[")[0]
    id_field = ENTITY_IDENTITY_FIELD.get(array)
    if not id_field:
        return None
    val = original_object.get(id_field)
    return entity_key(array, val) if val not in (None, "") else None


def find_similar_cases(
    target_path: Optional[str],
    error_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    top_k: int = 3,
) -> list[dict]:
    """
    Past cases for the same KIND of error, best first. Each returned case carries a
    `same_entity` flag (its affected_entity_id equals the current one).

    Ranking: same entity first, then same error_type, then a correction that survived
    revalidation, then recency.

    MEMORY_MODE="off" (BA measurement runs) short-circuits here — ONE place, so every consumer
    degrades on its own: `same_entity_confirmed_value([])` -> None (no override),
    `compute_memory_support(v, [])` -> 0.0, `format_cases_for_prompt([])` -> the neutral
    "no comparable case" line. Callers stay unaware, exactly like RULEBOOK_MODE.
    """
    if MEMORY_MODE == "off":
        return []

    pattern = entity_pattern(target_path)
    if not pattern:
        return []

    matches = []
    for case in repo.list_memory_items_as_dicts():
        if case.get("affected_entity_pattern") != pattern:
            continue
        if case.get("decision") not in _DECIDED:
            continue
        same_entity = bool(entity_id) and case.get("affected_entity_id") == entity_id
        case = {**case, "same_entity": same_entity}
        score = 1
        if same_entity:
            score += 10  # dominates the ranking — same-object precedent is the strongest signal
        if error_type and case.get("error_type") == error_type:
            score += 1
        if case.get("revalidation_ok") is True:
            score += 1
        matches.append((score, case["id"], case))

    matches.sort(key=lambda m: (-m[0], -m[1]))
    return [case for _, _, case in matches[:top_k]]


def same_entity_confirmed_value(cases: list[dict]) -> Optional[dict]:
    """
    The authoritative past HUMAN decision for the SAME object, if any: the most relevant
    same-entity case that a human approved or modified to a concrete final value.

    This is what the deterministic memory override uses — a value a human already decided for
    THIS exact object beats a fresh estimate. Returns the case (with 'id', 'final_value',
    'decision') or None. `cases` must already be ranked (same-entity first, recent first).
    """
    for c in cases:
        if (
            c.get("same_entity")
            and c.get("decision") in ("approve", "modify")
            and c.get("final_value") is not None
        ):
            return c
    return None


def compute_memory_support(proposed_value: Any, cases: list[dict]) -> tuple[float, str]:
    """
    Graded, deterministic — like `value_grounded`, never a model opinion.

        0.0  no similar case at all
        0.0  NEGATIVE precedent on the SAME entity: this exact value was already proposed here
             and a human rejected/corrected it away -> the agent is repeating a known mistake
        0.5  precedent for this KIND of error exists, but no SAME-ENTITY value precedent
        1.0  a human CONFIRMED this exact value for the SAME entity

    Authoritative value precedents (1.0 / negative-0.0) require the SAME entity. A confirmed value
    on a DIFFERENT entity of the same pattern is not authoritative here (object-specific), so it
    only sustains the 0.5 "kind-of-error precedent" level.
    """
    if not cases:
        return 0.0, "Kein vergleichbarer Fall im Gedächtnis."

    same = [c for c in cases if c.get("same_entity")]

    confirmed = [
        c for c in same
        if c.get("decision") in ("approve", "modify")
        and c.get("final_value") is not None
        and c.get("final_value") == proposed_value
    ]
    if confirmed:
        src = confirmed[0]
        return 1.0, (
            f"Ein Mensch hat genau diesen Wert für DIESES Objekt bereits bestätigt "
            f"(Fall #{src['id']}, Entscheidung: {src['decision']})."
        )

    overruled = [
        c for c in same
        if c.get("suggested_value") == proposed_value
        and (
            c.get("decision") == "reject"
            or (c.get("decision") == "modify" and c.get("final_value") != proposed_value)
        )
    ]
    if overruled:
        src = overruled[0]
        return 0.0, (
            f"WARNUNG: Dieser Wert wurde für DIESES Objekt schon einmal vorgeschlagen und von "
            f"einem Menschen verworfen (Fall #{src['id']}, Entscheidung: {src['decision']})."
        )

    n_same = len(same)
    if n_same:
        return 0.5, (
            f"{n_same} frühere Entscheidung(en) für DIESES Objekt vorhanden, aber kein "
            f"Präzedenzfall für genau diesen Wert."
        )
    return 0.5, (
        f"{len(cases)} vergleichbare(r) Fall/Fälle (anderes Objekt, gleicher Fehlertyp) — "
        f"nur Methoden-Hinweis, kein Wert-Präzedenzfall für dieses Objekt."
    )


def format_cases_for_prompt(cases: list[dict]) -> str:
    """
    Render the retrieved cases as evidence. SAME-entity cases say 'use this value'; other-entity
    cases say 'method hint only — values are object-specific, do NOT copy the value'.
    """
    if not cases:
        return "Keine vergleichbaren Fälle im Gedächtnis. Entscheide allein aus Regeln und Daten."

    lines = [
        "Frühere Fälle, die ein MENSCH entschieden hat. Beachte die Kennzeichnung:",
        "- [GLEICHES OBJEKT]: verbindlich. Übernimm den vom Menschen angewendeten Wert, außer du",
        "  hast einen expliziten, belegten Grund dagegen.",
        "- [ANDERES OBJEKT]: nur METHODEN-Hinweis. Die Werte sind objektspezifisch (z. B. eine",
        "  Dichte gilt nur für genau ihren Artikel) — übernimm NICHT den Wert, nur das Vorgehen.",
        "",
    ]
    for case in cases:
        tag = "[GLEICHES OBJEKT]" if case.get("same_entity") else "[ANDERES OBJEKT]"
        ent = case.get("affected_entity_id") or case.get("affected_entity_pattern")
        lines.append(f"FALL #{case['id']} {tag} ({case.get('error_type')}, {ent})")
        lines.append(f"  KI hatte vorgeschlagen: {case.get('suggested_value')!r}")
        lines.append(f"  Mensch entschied:       {case.get('decision')}")
        if case.get("decision") != "reject":
            lines.append(f"  Angewendeter Wert:      {case.get('final_value')!r}")
        if case.get("comment"):
            lines.append(f"  Begründung des Menschen: {case['comment']}")
        lines.append("")
    return "\n".join(lines)
