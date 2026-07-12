"""
Long-term (episodic) memory — the read path (PT4 / AP7.2).

Case-based reasoning: on a new error, find what humans decided on similar errors before, hand
those cases to the LLM as evidence, and turn the outcome into `memory_support` for the
confidence score.

Retrieval key — why `affected_entity_pattern` and NOT `error_type`:
`error_type` is not consistent across the case base. Cases built from pre-AP3.6b proposals carry
the old heuristic labels (EMPTY_FIELD, DUPLICATE_ID) while new ones carry the authoritative
[validate_*] tag (UNIQUE_IDS, ...). A new empty demandId is tagged UNIQUE_IDS today and would
MISS the EMPTY_FIELD cases that are about exactly that. The entity pattern is stable across both
worlds: `demands[].demandId` unites them correctly. So the pattern decides the match, and
error_type only ranks it higher.
"""
from typing import Any, Optional

from db import repository as repo
from memory.long_term import entity_pattern

#: Only decisions a human actually made carry evidence.
_DECIDED = ("approve", "modify", "reject")


def find_similar_cases(
    target_path: Optional[str],
    error_type: Optional[str] = None,
    top_k: int = 3,
) -> list[dict]:
    """
    Past cases for the same kind of error, best first.

    A case matches when its entity pattern equals the current one. Cases with the same
    `error_type` on top of that rank higher, and a case whose correction survived
    revalidation ranks above one that did not.
    """
    pattern = entity_pattern(target_path)
    if not pattern:
        return []

    matches = []
    for case in repo.list_memory_items_as_dicts():
        if case.get("affected_entity_pattern") != pattern:
            continue
        if case.get("decision") not in _DECIDED:
            continue
        score = 1
        if error_type and case.get("error_type") == error_type:
            score += 1
        if case.get("revalidation_ok") is True:
            score += 1
        matches.append((score, case["id"], case))

    matches.sort(key=lambda m: (-m[0], -m[1]))  # best score, then most recent
    return [case for _, _, case in matches[:top_k]]


def compute_memory_support(proposed_value: Any, cases: list[dict]) -> tuple[float, str]:
    """
    Graded, deterministic — like `value_grounded`, never a model opinion.

        0.0  no similar case at all              -> the agent is on its own
        0.0  NEGATIVE precedent: this exact value was already proposed and a human
             rejected it or corrected it away    -> the agent is repeating a known mistake
        0.5  precedent for this KIND of error, but no value precedent either way
        1.0  a human CONFIRMED this exact value in a similar case

    Returns (score, rationale) — the rationale goes into the proposal so a reviewer can see
    WHY memory raised or lowered the confidence.
    """
    if not cases:
        return 0.0, "Kein vergleichbarer Fall im Gedächtnis."

    confirmed = [
        c for c in cases
        if c.get("decision") in ("approve", "modify")
        and c.get("final_value") is not None
        and c.get("final_value") == proposed_value
    ]
    if confirmed:
        src = confirmed[0]
        return 1.0, (
            f"Ein Mensch hat genau diesen Wert bereits bestätigt "
            f"(Fall #{src['id']}, Entscheidung: {src['decision']})."
        )

    # Negative precedent: the AI already proposed this value and a human threw it out.
    overruled = [
        c for c in cases
        if c.get("suggested_value") == proposed_value
        and (
            c.get("decision") == "reject"
            or (c.get("decision") == "modify" and c.get("final_value") != proposed_value)
        )
    ]
    if overruled:
        src = overruled[0]
        return 0.0, (
            f"WARNUNG: Dieser Wert wurde schon einmal vorgeschlagen und von einem Menschen "
            f"verworfen (Fall #{src['id']}, Entscheidung: {src['decision']})."
        )

    return 0.5, (
        f"{len(cases)} vergleichbare(r) Fall/Fälle vorhanden, aber kein Präzedenzfall "
        f"für genau diesen Wert."
    )


def format_cases_for_prompt(cases: list[dict]) -> str:
    """Render the retrieved cases as evidence for the correction prompt."""
    if not cases:
        return "Keine vergleichbaren Fälle im Gedächtnis. Entscheide allein aus Regeln und Daten."

    lines = [
        "Für diesen Fehlertyp gibt es frühere Fälle, die ein MENSCH entschieden hat.",
        "Diese Entscheidungen sind verbindlicher als deine eigene Einschätzung — ein Mensch hat",
        "sie geprüft. Weiche nur mit expliziter Begründung davon ab.",
        "",
    ]
    for case in cases:
        lines.append(f"FALL #{case['id']} ({case.get('error_type')}, {case.get('affected_entity_pattern')})")
        lines.append(f"  KI hatte vorgeschlagen: {case.get('suggested_value')!r}")
        lines.append(f"  Mensch entschied:       {case.get('decision')}")
        if case.get("decision") != "reject":
            lines.append(f"  Angewendeter Wert:      {case.get('final_value')!r}")
        if case.get("comment"):
            lines.append(f"  Begründung des Menschen: {case['comment']}")
        lines.append("")
    return "\n".join(lines)
