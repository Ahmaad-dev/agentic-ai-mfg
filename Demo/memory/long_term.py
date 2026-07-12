"""
Long-term (episodic) memory — the write path (PT4 / AP7.1).

Turns a completed human review into ONE reusable case in `memory_items`.

Why reviews and not the chat: approve/reject/modify and the reasoning behind them live in
`reviews.decision` / `reviews.comment`. The chat history only ever contains the AI's PROPOSAL —
that is why `orchestration_agent._get_review_decisions()` has to patch the outcome back in.
Learning from proposals would teach the system its own mistakes; the human decision is the only
trustworthy signal.

A `modify` is the most valuable case of all: it is the explicit record that the AI was wrong and
what the correct answer was.

AP7.2 will read these cases back (retrieval by error signature) and derive `memory_support`.
"""
import re
import sys as _sys
from pathlib import Path
from typing import Optional

from db import repository as repo

# The runtime storage helper lives next to the runtime tools; import it the same way
# routes/apply_prep.py does (never a bare open()), so this works for LOCAL and AZURE storage.
_runtime_dir = str(Path(__file__).parent.parent / "smart-planning" / "runtime")
if _runtime_dir not in _sys.path:
    _sys.path.insert(0, _runtime_dir)

from runtime_storage import get_storage  # noqa: E402

# Cases are retrieved by error signature. The concrete array index of one snapshot is noise —
# "demands[386].articleId" and "demands[12].articleId" are the same KIND of error. Normalising
# the index out is what makes a past case matchable against a new one.
_INDEX_RE = re.compile(r"\[\d+\]")


def entity_pattern(target_path: Optional[str]) -> Optional[str]:
    """'demands[386].articleId' -> 'demands[].articleId'. None stays None."""
    if not target_path:
        return None
    return _INDEX_RE.sub("[]", target_path)


def _revalidation_ok(revalidation_result) -> Optional[bool]:
    """
    Did the correction actually hold up against the validator?

    None when nothing was applied (a reject) or no result was recorded.
    Reads `validation.is_valid`, NOT `errors_after`: runs before AP3.3d wrote a wrong
    `errors_after=0` (see PROJECT_LOG), so that field cannot be trusted for old rows.
    """
    if not isinstance(revalidation_result, dict):
        return None
    if revalidation_result.get("pipeline_success") is False:
        return False
    validation = revalidation_result.get("validation")
    if isinstance(validation, dict) and "is_valid" in validation:
        return bool(validation["is_valid"])
    return None


def record_case(proposal_id: str) -> Optional[int]:
    """
    Write the memory case for one decided proposal. Returns the memory_item id, or None if
    there is nothing to record (no proposal, no review) or the case already exists.

    Idempotent: one case per proposal, so re-running this (or the backfill) never duplicates.
    """
    if repo.memory_item_exists(proposal_id):
        return None

    proposal = repo.get_proposal_as_dict(proposal_id)
    review = repo.get_latest_review_as_dict(proposal_id)
    if proposal is None or review is None:
        return None

    return repo.add_memory_item(
        error_type=proposal.get("error_type"),
        affected_entity_pattern=entity_pattern(proposal.get("target_path")),
        suggested_value=proposal.get("suggested_value"),
        final_value=review.get("final_value"),
        decision=review.get("decision"),
        comment=review.get("comment"),
        revalidation_ok=_revalidation_ok(review.get("revalidation_result")),
        source_proposal_id=proposal_id,
    )


def record_case_safe(proposal_id: str) -> Optional[int]:
    """
    Same, but never lets a memory failure break a review. Memory is an add-on; the human
    decision and its application must succeed regardless (same defensive pattern the DB writes
    in web_server.chat() use).
    """
    try:
        return record_case(proposal_id)
    except Exception as err:  # noqa: BLE001 - deliberately swallowing: memory must not block HitL
        print(f"WARN: could not record memory case for {proposal_id}: {err}")
        return None


# --------------------------------------------------------------------------- #
# Legacy label repair (one-off, for cases built from pre-AP3.6b proposals)
# --------------------------------------------------------------------------- #
# Proposals written before AP3.6b-2 carry the OLD heuristic error_type from
# identify_snapshot.py. Those labels are unreliable — AP3.6a showed the heuristic mislabels a
# density error as DUPLICATE_ID (value-mode + >1 hits). Keeping them would poison retrieval:
# a new empty demandId gets tag UNIQUE_IDS and would never match the EMPTY_FIELD cases that are
# about exactly that. The authoritative tag is recoverable, not guessable: the iteration's
# llm_identify_response.json still holds the original message with its [validate_*] tag.
_LEGACY_ERROR_TYPES = {"EMPTY_FIELD", "DUPLICATE_ID", "SINGLE_MATCH", "NO_RESULTS_FOUND"}
_TAG_RE = re.compile(r"\s*\[validate_([^\]]+)\]")
_PROPOSAL_ID_RE = re.compile(r"^(?P<snapshot>.+)__iteration-(?P<iteration>\d+)$")


def _authoritative_error_type_from_artifact(proposal_id: str) -> Optional[str]:
    """Re-derive the [validate_*] tag from the run's identify artifact. None if unavailable."""
    match = _PROPOSAL_ID_RE.match(proposal_id or "")
    if not match:
        return None
    try:
        path = (
            f"{match.group('snapshot')}/iteration-{match.group('iteration')}"
            "/llm_identify_response.json"
        )
        data = get_storage().load_json(path)
    except Exception:  # noqa: BLE001 - artifact may be gone; caller keeps the legacy label
        return None
    if not isinstance(data, dict):
        return None
    message = ((data.get("llm_analysis") or {}).get("selected_error") or {}).get("message", "")
    tag = _TAG_RE.match(message if isinstance(message, str) else "")
    return tag.group(1).strip().upper() if tag else None


def repair_legacy_error_types() -> list[dict]:
    """Replace legacy heuristic labels on existing cases with the authoritative tag."""
    repaired = []
    for item in repo.list_memory_items_as_dicts():
        if (item.get("error_type") or "").upper() not in _LEGACY_ERROR_TYPES:
            continue
        tag = _authoritative_error_type_from_artifact(item.get("source_proposal_id"))
        if not tag or tag == item.get("error_type"):
            continue
        repo.set_memory_item_error_type(item["id"], tag)
        repaired.append({"id": item["id"], "from": item["error_type"], "to": tag})
    return repaired


def backfill() -> dict:
    """One-off: turn every review that already exists into a case. Safe to run repeatedly."""
    written, skipped = [], []
    for proposal_id in repo.list_reviewed_proposal_ids():
        item_id = record_case(proposal_id)
        (written if item_id else skipped).append(proposal_id)
    return {
        "written": written,
        "skipped": skipped,
        "repaired": repair_legacy_error_types(),
        "total": repo.count_memory_items(),
    }
