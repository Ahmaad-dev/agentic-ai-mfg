"""
AP3.3a — Preparing an approved/modified proposal for later application.

This module contains the two safety/preparation steps that must happen BEFORE
`apply_correction.py` is ever invoked. It applies NOTHING itself — no snapshot data
is written here. The actual application (apply_and_upload pipeline, re-validation,
status `applied`) is AP3.3b.

Why a separate module and not `review.py`:
`review.py` is the HTTP layer (Flask blueprint, request/response, status codes). The
logic here is snapshot-file manipulation and needs the runtime storage backend, which
in turn requires a sys.path entry for `demo/smart-planning/runtime/`. Keeping that out
of the blueprint keeps the HTTP layer free of runtime imports and lets these functions
be tested without a Flask app.

Hard rule honoured here: runtime tools under `demo/smart-planning/runtime/` are NOT
modified — neither signature nor behaviour. We only write DATA files, and only through
the existing StorageManager (LOCAL/AZURE), never via bare open().
"""
from __future__ import annotations

import re
import sys as _sys
from pathlib import Path
from typing import Any, Optional, Tuple

# The runtime storage helper lives next to the runtime tools; import it the same way
# sp_agent.py does, without importing (or touching) any tool itself.
_runtime_dir = str(Path(__file__).parent.parent / "smart-planning" / "runtime")
if _runtime_dir not in _sys.path:
    _sys.path.insert(0, _runtime_dir)

from runtime_storage import get_storage, get_latest_iteration_number  # noqa: E402

#: The file `apply_correction.py` reads the value to apply from.
PROPOSAL_FILE = "llm_correction_proposal.json"

#: Untouched copy of the AI's original proposal, written before a human `modify`
#: overwrites `new_value`, so the file-level audit trail keeps the AI value.
AI_ORIGINAL_FILE = "llm_correction_proposal.ai_original.json"

#: proposal_id scheme from AP1.4: {snapshot_id}__iteration-{N}
_PROPOSAL_ID_RE = re.compile(r"^(?P<snapshot_id>.+)__iteration-(?P<iteration>\d+)$")


def parse_proposal_id(proposal_id: str) -> Tuple[str, int]:
    """Split `{snapshot_id}__iteration-{N}` into its parts. Raises ValueError if malformed."""
    match = _PROPOSAL_ID_RE.match(proposal_id or "")
    if not match:
        raise ValueError(
            f"Malformed proposal_id {proposal_id!r}; expected '{{snapshot_id}}__iteration-{{N}}'"
        )
    return match.group("snapshot_id"), int(match.group("iteration"))


def _proposal_path(snapshot_id: str, iteration: int, filename: str) -> str:
    return f"{snapshot_id}/iteration-{iteration}/{filename}"


# --------------------------------------------------------------------------- #
# Function 1 — iteration guard
# --------------------------------------------------------------------------- #
def check_iteration_is_latest(proposal_id: str) -> Tuple[bool, str]:
    """
    Guard: may the proposal behind `proposal_id` be applied at all?

    `apply_correction.py` does not take a proposal id — it always resolves the HIGHEST
    iteration that contains a `llm_correction_proposal.json` and applies that one. If a
    newer iteration exists, applying the reviewed proposal would silently apply a
    DIFFERENT correction than the one the human approved.

    Returns (True, "") if the iteration encoded in `proposal_id` is the latest one,
    otherwise (False, "<message naming both iteration numbers>").
    """
    try:
        snapshot_id, iteration = parse_proposal_id(proposal_id)
    except ValueError as exc:
        return False, str(exc)

    # Same lookup apply_correction.get_latest_iteration_number() performs, so the guard
    # sees exactly what the tool would pick.
    latest = get_latest_iteration_number(snapshot_id, require_file=PROPOSAL_FILE)

    if latest is None:
        return False, (
            f"No iteration with {PROPOSAL_FILE} found for snapshot {snapshot_id}; "
            "nothing could be applied"
        )

    if iteration != latest:
        return False, (
            f"Proposal iteration {iteration} is not the latest (latest: {latest}); "
            "applying it would apply a different correction than the one reviewed"
        )

    return True, ""


# --------------------------------------------------------------------------- #
# AP3.5b — identity guard
# --------------------------------------------------------------------------- #
def check_identity_guard(proposal_id: str) -> Tuple[bool, str, dict]:
    """
    Guard: does the object at the target position still match the one the proposal was
    generated for? Protects against silently correcting the wrong object after the array
    was reordered between generation and apply.

    Uses the AP3.5a fields anchored in the proposal (`correction_kind`,
    `target_entity_type`, `target_entity_id`, `identity_check_supported`).

    Returns (ok, message, info):
      - ok=True  → proceed (guard passed OR intentionally skipped). `message` is a non-empty
                   skip/notice string when the check was not enforced, "" on a real pass.
      - ok=False → BLOCK (identity mismatch / target position gone / field no longer empty).
      - info: structured detail for logging/response (`guard` key names the outcome).

    Skips (pass-through, never block): legacy proposals without the AP3.5a fields,
    unsupported entities (equipment/worker*/packaging), KIND_UNKNOWN, and KIND_ADD_OBJECT
    (position check not applicable — flagged add_object_guard_verified=False).
    """
    try:
        snapshot_id, iteration = parse_proposal_id(proposal_id)
    except ValueError as exc:
        return False, str(exc), {"guard": "error_bad_proposal_id"}

    storage = get_storage()
    document = storage.load_json(_proposal_path(snapshot_id, iteration, PROPOSAL_FILE))
    if document is None or not isinstance(document.get("correction_proposal"), dict):
        return False, (
            f"{PROPOSAL_FILE} missing or malformed for {proposal_id}; cannot verify identity"
        ), {"guard": "error_no_proposal_file"}

    cp = document["correction_proposal"]

    # Legacy proposal (generated before AP3.5a): the guard fields are absent. Skip, pass —
    # blocking a legitimate old proposal would be wrong.
    if "correction_kind" not in cp:
        return True, (
            "identity guard skipped: legacy proposal without AP3.5a fields"
        ), {"guard": "skipped_legacy"}

    kind = cp.get("correction_kind")
    entity_type = cp.get("target_entity_type")
    target_id = cp.get("target_entity_id")
    supported = cp.get("identity_check_supported")
    target_path = cp.get("target_path")

    if kind == "KIND_ADD_OBJECT":
        return True, (
            "identity guard skipped: KIND_ADD_OBJECT (object not yet at an index)"
        ), {"guard": "skipped_add_object", "add_object_guard_verified": False}

    if kind == "KIND_UNKNOWN" or not supported:
        return True, (
            f"identity guard skipped: not supported for entity/kind ({entity_type}/{kind})"
        ), {"guard": "skipped_unsupported"}

    # From here: KIND_MODIFY_EXISTING or KIND_FILL_IDENTITY on a supported entity.
    from generate_correction_llm import ENTITY_IDENTITY_FIELD  # lazy: keep apply_prep light

    snapshot_data = storage.load_json(f"{snapshot_id}/snapshot-data.json")
    if not isinstance(snapshot_data, dict):
        return False, (
            f"snapshot-data.json unreadable for {snapshot_id}; cannot verify identity"
        ), {"guard": "error_no_snapshot_data"}

    if kind == "KIND_FILL_IDENTITY":
        # No soll-identity (it is what gets filled). Optional check: the target field must
        # still be empty — if a value appeared since approval, the situation changed.
        m = re.match(r"^(\w+)\[(\d+)\]\.(\w+)", target_path or "")
        if not m:
            return True, (
                f"identity guard skipped: FILL_IDENTITY target_path unparsable ({target_path})"
            ), {"guard": "skipped_fill_unparsable"}
        array_name, index, field = m.group(1), int(m.group(2)), m.group(3)
        arr = snapshot_data.get(array_name)
        if not isinstance(arr, list) or index >= len(arr) or not isinstance(arr[index], dict):
            return False, (
                f"Identity mismatch: position {array_name}[{index}] no longer exists"
            ), {"guard": "blocked_position_gone"}
        current = arr[index].get(field)
        if current not in ("", None):
            return False, (
                f"Field {array_name}[{index}].{field} is no longer empty (now {current!r}); "
                "situation changed since approval"
            ), {"guard": "blocked_field_not_empty", "current_value": current}
        return True, "", {"guard": "passed_fill_still_empty"}

    # KIND_MODIFY_EXISTING with a non-null soll-identity.
    if target_id is None:
        return True, (
            "identity guard skipped: MODIFY_EXISTING without a target_entity_id"
        ), {"guard": "skipped_no_target_id"}

    m = re.match(r"^(\w+)\[(\d+)\]", target_path or "")
    if not m:
        return True, (
            f"identity guard skipped: target_path without an index ({target_path})"
        ), {"guard": "skipped_no_index"}
    array_name, index = m.group(1), int(m.group(2))
    id_field = ENTITY_IDENTITY_FIELD.get(entity_type)
    arr = snapshot_data.get(array_name)
    if not isinstance(arr, list) or index >= len(arr) or not isinstance(arr[index], dict):
        length = len(arr) if isinstance(arr, list) else "n/a"
        return False, (
            f"Identity mismatch: position {entity_type}[{index}] no longer exists "
            f"(array length {length}); proposal was generated for {target_id}"
        ), {"guard": "blocked_position_gone"}

    current_id = arr[index].get(id_field)
    if str(current_id) != str(target_id):
        return False, (
            f"Identity mismatch: position {entity_type}[{index}] now holds {current_id!r}, "
            f"proposal was generated for {target_id!r}"
        ), {"guard": "blocked_identity_mismatch", "current_id": current_id, "expected_id": target_id}

    return True, "", {"guard": "passed", "verified_id": current_id}


# --------------------------------------------------------------------------- #
# Function 2 — prepare the proposal file for application
# --------------------------------------------------------------------------- #
def prepare_proposal_for_apply(
    proposal_id: str,
    decision: str,
    final_value: Any = None,
) -> dict:
    """
    Make `llm_correction_proposal.json` carry the value that should actually be applied.

    approve → the file already holds the AI value; `new_value` is left untouched.
    modify  → the AI original is copied aside first, then `new_value` is replaced by the
              human `final_value`.

    Applies nothing to snapshot data. Returns a dict describing exactly what happened
    (never a silent no-op).
    """
    if decision not in ("approve", "modify"):
        raise ValueError(f"decision must be 'approve' or 'modify', got {decision!r}")
    if decision == "modify" and final_value is None:
        raise ValueError("decision 'modify' requires a final_value")

    snapshot_id, iteration = parse_proposal_id(proposal_id)
    storage = get_storage()

    proposal_path = _proposal_path(snapshot_id, iteration, PROPOSAL_FILE)
    original_path = _proposal_path(snapshot_id, iteration, AI_ORIGINAL_FILE)

    document = storage.load_json(proposal_path)
    if document is None:
        raise FileNotFoundError(f"{PROPOSAL_FILE} not found at {proposal_path}")

    correction_proposal = document.get("correction_proposal")
    if not isinstance(correction_proposal, dict):
        raise ValueError(f"{proposal_path} has no 'correction_proposal' object")

    ai_value = correction_proposal.get("new_value")
    result = {
        "proposal_id": proposal_id,
        "snapshot_id": snapshot_id,
        "iteration": iteration,
        "decision": decision,
        "ai_value": ai_value,
        "ai_original_written": False,
        "changed_files": [],
    }

    if decision == "approve":
        # Nothing to change about the value — the AI suggestion IS what gets applied.
        # Only the provenance marker is stamped, so the file states on its own which
        # value the human signed off on.
        correction_proposal["value_source"] = "ai_suggested"
        result["value_source"] = "ai_suggested"
        result["value_to_apply"] = ai_value
        result["value_changed"] = False
    else:
        # The FIRST AI state is the authoritative one: never overwrite an existing copy
        # (a second modify must not clobber the original with an already-modified file).
        if not storage.exists(original_path):
            storage.save_json(original_path, document)
            result["ai_original_written"] = True
            result["changed_files"].append(original_path)

        # Only the MAIN value is replaced. `additional_updates` keep the values the AI
        # proposed — one confidence score and one approval cover the whole proposal
        # (PT4 scope guardrail), so there is no per-update human override.
        correction_proposal["new_value"] = final_value
        correction_proposal["value_source"] = "human_modify"
        result["value_source"] = "human_modify"
        result["value_to_apply"] = final_value
        result["value_changed"] = True

    storage.save_json(proposal_path, document)
    result["changed_files"].append(proposal_path)
    return result
