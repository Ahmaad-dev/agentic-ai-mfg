"""
LLM-based Correction Proposal Generator

Generates structured correction proposals for validation errors using Azure OpenAI.
Reads validation-fix-rules.md and last_search_results.json to create actionable corrections.
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from openai import AzureOpenAI

# Storage Manager (LOCAL / AZURE)
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from runtime_storage import get_storage, get_iteration_folders_with_file, get_latest_iteration_number

# AP7.0: rulebook loader (monolith vs. error-type cards, switched via RULEBOOK_MODE)
from rulebook_loader import load_rulebook
from agent_config import RULEBOOK_MODE

# AP7.2: episodic memory — retrieve human-decided past cases, derive memory_support
from memory import retrieval as mem_retrieval

# Pydantic model for schema-validity part of the confidence score (AP1.3b)
from correction_models import CorrectionProposal

#: Stamped on every proposal. AP6 must not mix generations in one calibration curve:
#: "v0" = middle term was `schema_valid` (always 1) -> score a near-constant ~0.775.
#: "v1" = value_grounded real, but memory_support hard-wired to 0 (score capped at 0.8).
#: "v2" = memory_support graded from the episodic case base (AP7.2).
#: "v3" = value_grounded is CLASS-AWARE (AP-E.0). The weights are unchanged, but the SEMANTICS
#:        of the 0.3 term changed: for identity fields it now asks "unique + follows the array's
#:        ID convention?" instead of "already in the data?" (which was backwards — a new unique
#:        ID must NOT be in the data). v2 and v3 scores are therefore NOT comparable.
CONFIDENCE_FORMULA_VERSION = "v3"

# Load environment variables (aus demo-Verzeichnis)
# Lade .env aus dem demo-Verzeichnis (2 Ebenen höher)
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

def load_current_snapshot_id(snapshot_id: str = None):
    """Load the current snapshot ID. Argument hat Priorität, Fallback auf current_snapshot.txt."""
    if snapshot_id:
        return snapshot_id
    current_snapshot_file = Path("runtime-files/current_snapshot.txt")
    if not current_snapshot_file.exists():
        raise FileNotFoundError("runtime-files/current_snapshot.txt not found")
    
    snapshot_id = current_snapshot_file.read_text().strip()
    if not snapshot_id:
        raise ValueError("current_snapshot.txt is empty")
    
    # Remove "snapshot_id = " prefix if present
    if snapshot_id.startswith("snapshot_id = "):
        snapshot_id = snapshot_id.replace("snapshot_id = ", "").strip()
    
    return snapshot_id

def load_validation_fix_rules(error_type: str = None, relevant_cards=None):
    """
    Load the rulebook for this correction.

    AP7.0: monolith, or _core.md + the card(s) for this error's [validate_*] tag.
    AP7.5: PLUS every card the agent itself picked during identification (`relevant_cards`).
    Das ist der Weg fuer Karten, die ein Fachanwender in normaler Sprache beschrieben hat,
    ohne einen technischen Tag zu kennen.
    """
    return load_rulebook(error_type, extra_cards=relevant_cards)

def load_search_results(snapshot_id):
    """Load the last_search_results.json from the snapshot folder"""
    storage = get_storage()
    data = storage.load_json(f"{snapshot_id}/last_search_results.json")
    if data is None:
        raise FileNotFoundError(f"last_search_results.json not found for snapshot {snapshot_id}")
    return data

def load_identify_response(snapshot_id):
    """Load llm_identify_response.json from the latest iteration folder"""
    iteration_number = get_latest_iteration_number(snapshot_id, require_file="llm_identify_response.json")
    if iteration_number is None:
        raise FileNotFoundError(f"No iteration folders with llm_identify_response.json found for {snapshot_id}")
    storage = get_storage()
    data = storage.load_json(f"{snapshot_id}/iteration-{iteration_number}/llm_identify_response.json")
    if data is None:
        raise FileNotFoundError(f"llm_identify_response.json not found in iteration-{iteration_number}")
    return data

def get_latest_iteration_number_local(snapshot_id):
    """Find the highest iteration folder that contains llm_identify_response.json"""
    num = get_latest_iteration_number(snapshot_id, require_file="llm_identify_response.json")
    if num is None:
        raise FileNotFoundError(f"No iteration folders with llm_identify_response.json found for {snapshot_id}")
    return num

def save_correction_proposal(snapshot_id, iteration_number, proposal_data, llm_call_data):
    """Save the correction proposal and LLM call details to iteration folder"""
    storage = get_storage()
    storage.save_json(f"{snapshot_id}/iteration-{iteration_number}/llm_correction_proposal.json", proposal_data)
    storage.save_json(f"{snapshot_id}/iteration-{iteration_number}/llm_correction_call.json", llm_call_data)
    print(f"Saved correction proposal: {snapshot_id}/iteration-{iteration_number}/llm_correction_proposal.json")
    print(f"Saved LLM call details:   {snapshot_id}/iteration-{iteration_number}/llm_correction_call.json")
    # AP1.4: additionally persist a central, flat proposal record (nested file stays untouched)
    save_central_proposal_record(snapshot_id, iteration_number, proposal_data)


def save_central_proposal_record(snapshot_id, iteration_number, output_data):
    """
    AP1.4: Persist each proposal additionally at a central, flat location so open
    proposals are findable without digging into per-snapshot iteration folders.

    - Central path: '_proposals/{proposal_id}.json' in the same storage backend
      (works for LOCAL and AZURE via StorageManager).
    - proposal_id is deterministic and stable: '{snapshot_id}__iteration-{N}'
      (idempotent: a re-run updates the same record, preserving created_at).
    - The nested 'iteration-N/llm_correction_proposal.json' is NOT modified here.
    """
    storage = get_storage()
    proposal_id = f"{snapshot_id}__iteration-{iteration_number}"
    central_path = f"_proposals/{proposal_id}.json"

    proposal = output_data.get("correction_proposal", {}) if isinstance(output_data, dict) else {}
    now_iso = datetime.now(timezone.utc).isoformat()

    # Preserve created_at across idempotent updates
    existing = storage.load_json(central_path)
    created_at = existing.get("created_at") if isinstance(existing, dict) else None

    # NOTE (AP3.3c): this file is a GENERATION-TIME record only. Its `status` is frozen at
    # "pending_review" and is deliberately NOT kept in sync with review decisions. The DB
    # (`proposals.status`) is the single, authoritative source of status — see AP3.1. After
    # a decision the DB reads approved/applied while this file still reads pending_review;
    # that divergence is expected. Do NOT read status from here and do NOT sync it back;
    # one authoritative source plus one explicitly non-authoritative record avoids the
    # two-writers-for-one-state bug that syncing would introduce.
    record = {
        "proposal_id": proposal_id,
        "snapshot_id": snapshot_id,
        "iteration": iteration_number,
        "status": proposal.get("status", "pending_review"),
        "confidence_score": proposal.get("confidence_score"),
        "llm_confidence": proposal.get("llm_confidence"),
        "action": proposal.get("action"),
        "created_at": created_at or now_iso,
        "updated_at": now_iso,
        "source_path": f"{snapshot_id}/iteration-{iteration_number}/llm_correction_proposal.json",
        "proposal": output_data,
    }
    storage.save_json(central_path, record)
    print(f"Saved central proposal record: {central_path} (proposal_id={proposal_id})")

    # AP2: also persist the proposal into the relational store (defensive; never break generation)
    try:
        from db import repository as _db_repo
        _is_new_proposal = _db_repo.get_proposal_as_dict(proposal_id) is None
        _db_repo.save_proposal(record)
        print(f"Saved proposal to DB: {proposal_id}")

        # AP5.2: best-effort enterprise notification. The deterministic proposal id makes
        # generation idempotent, so notify only for the first DB insert, never for a re-run.
        if _is_new_proposal and record["status"] == "pending_review":
            try:
                from mcp_connections.notifier import send_proposal_notification
                _notification = send_proposal_notification(
                    proposal_id,
                    snapshot_id,
                    (output_data.get("error_analyzed") or {}).get("error_type") or "UNKNOWN",
                )
                if _notification.get("sent"):
                    print(f"Notification sent: {proposal_id} ({_notification.get('channel')})")
            except Exception as _notif_err:
                print(f"WARN: notification failed: {_notif_err}")

        # AP2.5: Read token usage from the already-saved llm_correction_call.json
        # (runtime tool NOT changed — we read the file it already wrote)
        # AP6.3: cost now comes from the shared cost model (input and output billed at their
        # own rates). This tool is the input-heaviest caller in the system — it ships whole
        # snapshot excerpts into the prompt — so a blended rate distorted it the most.
        from cost_model import estimate_cost as _estimate_cost
        call_data = storage.load_json(
            f"{snapshot_id}/iteration-{iteration_number}/llm_correction_call.json"
        )
        if call_data:
            usage = (call_data.get("response") or {}).get("usage") or {}
            tok_p = usage.get("prompt_tokens")
            tok_c = usage.get("completion_tokens")
            cost = _estimate_cost(tok_p, tok_c)
            # Write a synthetic session to anchor the agent_run (subprocess has no web session)
            try:
                _sess_id = _db_repo.create_session(
                    snapshot_id=snapshot_id, user_ref=f"subprocess:{proposal_id}"
                )
                _db_repo.add_agent_run(
                    _sess_id,
                    agent_name="generate_correction_llm",
                    tool_name="generate_correction_llm",
                    input_summary=f"snapshot_id={snapshot_id}, iteration={iteration_number}",
                    output_summary=f"proposal_id={proposal_id}",
                    status="success",
                    tokens_prompt=tok_p,
                    tokens_completion=tok_c,
                    cost_estimate=cost,
                )
                print(f"Saved agent_run with tokens (prompt={tok_p}, completion={tok_c}, cost={cost})")
            except Exception as _run_err:
                print(f"WARN: could not persist agent_run for correction: {_run_err}")
    except Exception as _db_err:
        print(f"WARN: could not persist proposal to DB: {_db_err}")

# AP3.5a: entities with a clean, single top-level identity field (guard-checkable).
# Special entities are intentionally absent: equipment has a DUAL id (equipmentId +
# equipmentKey), worker* arrays carry the id NESTED (worker.workerId), and
# packagingEquipmentCompatibility uses a non-*Id field (packaging). For those the guard
# is marked unsupported rather than guessing.
ENTITY_IDENTITY_FIELD = {
    "articles": "articleId",
    "demands": "demandId",
    "workPlans": "workPlanId",
}


def _parse_target_entity(target_path):
    """From a target_path, return (array_name, index_or_None, first_field_or_None).

    Examples:
        'articles[312].workItemConfigs'   -> ('articles', 312, 'workItemConfigs')
        'demands[0].demandId'             -> ('demands', 0, 'demandId')
        'equipment[339].predecessors[0]'  -> ('equipment', 339, 'predecessors')
        'demands' (add_to_array root)     -> ('demands', None, None)
    """
    if not isinstance(target_path, str):
        return None, None, None
    m = re.match(r"^(\w+)(?:\[(\d+)\])?(?:\.(\w+))?", target_path)
    if not m:
        return None, None, None
    idx = int(m.group(2)) if m.group(2) is not None else None
    return m.group(1), idx, m.group(3)


def derive_correction_identity(correction_proposal, snapshot_data):
    """
    AP3.5a: additively derive the guard metadata for a proposal.

    Returns {correction_kind, target_entity_type, target_entity_id, identity_check_supported}.

    correction_kind:
        KIND_FILL_IDENTITY  – the identity field itself is empty and is being filled
                              (no soll-identity exists → target_entity_id = None)
        KIND_MODIFY_EXISTING– an existing object's field/sub-field is changed/filled
        KIND_ADD_OBJECT     – a whole object is appended to a root array (add_to_array)
        KIND_UNKNOWN        – manual_intervention_required / remove_from_array / unparsable

    target_entity_id is the soll-identity read from snapshot_data at the target position
    (decided in AP3.5a: the message/search_value is unreliable for reference errors — it
    names the referenced entity, not the corrected object). For KIND_ADD_OBJECT the object
    does not exist yet, so its identity is taken from new_value's id field if present.
    """
    action = correction_proposal.get("action")
    target_path = correction_proposal.get("target_path")
    current_value = correction_proposal.get("current_value")
    new_value = correction_proposal.get("new_value")

    array_name, index, field = _parse_target_entity(target_path)
    id_field = ENTITY_IDENTITY_FIELD.get(array_name)
    identity_check_supported = id_field is not None

    if action == "add_to_array":
        kind = "KIND_ADD_OBJECT"
    elif action == "update_field":
        # FILL_IDENTITY only when the target field IS the entity's identity field AND it is
        # currently empty. A non-empty identity field being changed (e.g. de-duplicating a
        # demandId) is MODIFY_EXISTING, not FILL. Emptiness — not search_mode — decides.
        if id_field is not None and field == id_field and current_value in ("", None):
            kind = "KIND_FILL_IDENTITY"
        else:
            kind = "KIND_MODIFY_EXISTING"
    else:
        # manual_intervention_required, remove_from_array, or unparsable path.
        kind = "KIND_UNKNOWN"

    target_entity_id = None
    if kind == "KIND_MODIFY_EXISTING" and identity_check_supported and index is not None \
            and isinstance(snapshot_data, dict):
        arr = snapshot_data.get(array_name)
        if isinstance(arr, list) and 0 <= index < len(arr) and isinstance(arr[index], dict):
            target_entity_id = arr[index].get(id_field)
    elif kind == "KIND_ADD_OBJECT" and identity_check_supported and isinstance(new_value, dict):
        target_entity_id = new_value.get(id_field)
    # KIND_FILL_IDENTITY -> None (identity is what is being filled); KIND_UNKNOWN -> None.

    return {
        "correction_kind": kind,
        "target_entity_type": array_name,
        "target_entity_id": target_entity_id,
        "identity_check_supported": identity_check_supported,
    }


def _proposal_matches_schema(correction_proposal):
    """Return True if the proposal validates against the CorrectionProposal Pydantic model."""
    try:
        CorrectionProposal(**correction_proposal)
        
        return True
    except Exception:
        return False


#: Fields that REFERENCE another entity: field -> (array holding it, its identity field).
#: Used by the groundedness check: a reference is grounded exactly if the referenced object
#: actually exists in the snapshot.
REFERENCE_FIELD_TARGET = {
    "articleId": ("articles", "articleId"),
    "workPlanId": ("workPlans", "workPlanId"),
}


def _id_shape(value):
    """
    Strukturelle Signatur einer ID: Ziffern -> '9', Grossbuchstaben -> 'A', Kleinbuchstaben ->
    'a', alles andere bleibt. 'D100079_001' -> 'A999999_999'.

    So laesst sich deterministisch pruefen, ob eine NEU gebildete ID der Konvention des Arrays
    folgt — ohne die Konvention hart zu kodieren.
    """
    out = []
    for ch in str(value):
        if ch.isdigit():
            out.append("9")
        elif ch.isalpha():
            out.append("A" if ch.isupper() else "a")
        else:
            out.append(ch)
    return "".join(out)


def _dominant_id_shape(objects, field, exclude_index=None):
    """Die haeufigste ID-Form im Array (Mehrheitskonvention) + wie eindeutig sie ist."""
    shapes = {}
    for i, o in enumerate(objects or []):
        if i == exclude_index or not isinstance(o, dict):
            continue
        v = o.get(field)
        if v in (None, ""):
            continue
        s = _id_shape(v)
        shapes[s] = shapes.get(s, 0) + 1
    if not shapes:
        return None, 0, 0
    total = sum(shapes.values())
    top, count = max(shapes.items(), key=lambda kv: kv[1])
    return top, count, total


def compute_value_grounded(correction_proposal, snapshot_data):
    """
    Deterministic answer to: **is the proposed value verifiably admissible, or invented?**

    This exists because the LLM's own `llm_confidence` is not calibratable by prompt alone.
    Measured: it rated an ID it had INVENTED as "Band A / 0.9" — in exactly the case where it
    was wrong and a human had to overrule it. A self-estimate cannot distinguish "I read this
    from the data" from "I made this up"; this check can.

    Returns (grounded: float 0.0|1.0, reason: str). Conservative: anything it cannot verify
    counts as NOT grounded, so an unverifiable value never inflates the score.

    --- AP-E.0 (2026-07-12): the check is now CLASS-AWARE. ---
    The old version asked ONE question for every field: "does this value already exist in the
    data?" For an identity field that question is not merely hard, it is BACKWARDS: a new unique
    ID must NOT exist in the data — if it did, it would be a duplicate, i.e. wrong. So the term
    was structurally unsatisfiable for the entire ID-generation class, which is PT4's vertical
    slice. Measured on the test catalog: two EXACTLY correct ID proposals scored 0.0 while a
    WRONG density value scored 1.0 — the signal was anti-correlated with correctness.

    The right question depends on the field class:
      * IDENTITY field  -> is the value UNIQUE in its array AND does it follow the array's
                           established ID convention (majority shape)?
      * REFERENCE field -> does the referenced object exist?
      * VALUE field     -> does the identical value already sit on the same field of a
                           comparable object? (For list fields: is it a member of such a list?)
      * add_to_array    -> apply the identity + reference checks to the NEW object.
    All four are exactly as deterministic as the old single test.
    """
    if correction_proposal.get("action") == "manual_intervention_required":
        return 0.0, "manual_intervention_required"

    new_value = correction_proposal.get("new_value")
    if new_value is None or new_value == "":
        return 0.0, "kein new_value"
    if not isinstance(snapshot_data, dict):
        return 0.0, "snapshot-data nicht ladbar (konservativ: nicht belegt)"

    array_name, index, field = _parse_target_entity(correction_proposal.get("target_path"))
    if not array_name:
        return 0.0, "target_path nicht auswertbar"

    # (a0) add_to_array: target_path is the bare array name and new_value is a whole object.
    # Verify the NEW object the same way: its identity must be unique + conventional, and its
    # references must exist.
    if field is None and index is None and isinstance(new_value, dict):
        return _grounded_for_new_object(array_name, new_value, snapshot_data)

    if not field:
        return 0.0, "target_path nicht auswertbar (kein Feld)"

    # (a1) IDENTITY field of its own array (demands[i].demandId, ...).
    if ENTITY_IDENTITY_FIELD.get(array_name) == field:
        return _grounded_for_identity(array_name, field, index, new_value, snapshot_data)

    # (a2) Reference field -> the referenced object must exist.
    ref = REFERENCE_FIELD_TARGET.get(field)
    if ref and ref[0] != array_name:
        ref_array, ref_id_field = ref
        objects = snapshot_data.get(ref_array)
        if not isinstance(objects, list):
            return 0.0, f"Referenz-Array '{ref_array}' fehlt"
        exists = any(
            isinstance(o, dict) and str(o.get(ref_id_field)) == str(new_value)
            for o in objects
        )
        if exists:
            return 1.0, f"Referenz belegt: {ref_array}.{ref_id_field}={new_value} existiert"
        return 0.0, f"Referenz NICHT belegt: kein {ref_array} mit {ref_id_field}={new_value}"

    # (b) Same value already used on the same field of a comparable object.
    objects = snapshot_data.get(array_name)
    if not isinstance(objects, list):
        return 0.0, f"Array '{array_name}' fehlt in snapshot-data"

    for i, o in enumerate(objects):
        if i == index or not isinstance(o, dict) or field not in o:
            continue
        other = o[field]
        if other == new_value:
            return 1.0, (
                f"Wert existiert bereits in {array_name}[{i}].{field} "
                f"— aus vergleichbarem Datensatz uebernommen"
            )
        # Nested list field (equipment[i].predecessors[0]): the proposal writes ONE element of
        # a list. Comparing the scalar against the whole list never matches — check membership.
        # (Old behaviour: always 0.0 here, i.e. every list-element fix was called "invented".)
        if isinstance(other, list) and not isinstance(new_value, (list, dict)) and new_value in other:
            return 1.0, (
                f"Wert ist belegtes Element von {array_name}[{i}].{field} "
                f"— aus vergleichbarem Datensatz uebernommen"
            )

    return 0.0, (
        f"Wert nicht in den Daten auffindbar — konstruiert/erfunden "
        f"(kein {array_name}[*].{field} mit diesem Wert)"
    )


def _grounded_for_identity(array_name, field, index, new_value, snapshot_data):
    """
    Identitaetsfeld: der Wert MUSS neu sein. „Steht er schon in den Daten?" ist hier die falsche
    Frage — die richtige ist: **ist er eindeutig UND folgt er der Konvention des Arrays?**
    """
    objects = snapshot_data.get(array_name)
    if not isinstance(objects, list):
        return 0.0, f"Array '{array_name}' fehlt in snapshot-data"

    # 1. Eindeutigkeit — eine Kollision ist nicht nur „unbelegt", sondern nachweislich FALSCH:
    #    das Anwenden wuerde ein NEUES Duplikat erzeugen. (Gemessen: die KI schlug bei einer
    #    De-Duplizierung 'D210451_002' vor — eine ID, die bereits auf demands[768] sass.)
    for i, o in enumerate(objects):
        if i != index and isinstance(o, dict) and o.get(field) == new_value:
            return 0.0, (
                f"KOLLISION: {array_name}[{i}].{field} traegt bereits {new_value!r} "
                f"— dieser Vorschlag wuerde ein neues Duplikat erzeugen"
            )

    # 2. Konvention — folgt die neue ID der Mehrheitsform der bestehenden IDs?
    shape, count, total = _dominant_id_shape(objects, field, exclude_index=index)
    if not shape:
        return 0.0, f"keine bestehenden {field}-Werte, Konvention nicht pruefbar (konservativ)"

    proposed = _id_shape(new_value)
    if proposed == shape:
        return 1.0, (
            f"Identitaetsfeld belegt: {new_value!r} ist im Array eindeutig UND folgt der "
            f"Konvention {shape} ({count} von {total} bestehenden {field} haben diese Form)"
        )
    return 0.0, (
        f"Identitaetsfeld NICHT belegt: {new_value!r} hat die Form {proposed}, die Konvention "
        f"des Arrays ist aber {shape} ({count} von {total}) — Wert weicht vom Muster ab"
    )


def _grounded_for_new_object(array_name, obj, snapshot_data):
    """add_to_array: das NEUE Objekt pruefen — Identitaet eindeutig+konventionell, Referenzen echt."""
    id_field = ENTITY_IDENTITY_FIELD.get(array_name)
    if not id_field:
        return 0.0, f"add_to_array auf '{array_name}': kein bekanntes Identitaetsfeld (konservativ)"
    if id_field not in obj:
        return 0.0, f"add_to_array: neues Objekt hat kein {id_field}"

    grounded, reason = _grounded_for_identity(
        array_name, id_field, None, obj[id_field], snapshot_data
    )
    if grounded < 1.0:
        return 0.0, f"add_to_array: {reason}"

    # Alle Referenzfelder des neuen Objekts muessen auf existierende Objekte zeigen.
    for fld, (ref_array, ref_id) in REFERENCE_FIELD_TARGET.items():
        if fld not in obj or ref_array == array_name:
            continue
        objects = snapshot_data.get(ref_array)
        if not isinstance(objects, list):
            return 0.0, f"add_to_array: Referenz-Array '{ref_array}' fehlt"
        if not any(isinstance(o, dict) and str(o.get(ref_id)) == str(obj[fld]) for o in objects):
            return 0.0, (
                f"add_to_array: Referenz NICHT belegt — kein {ref_array} mit "
                f"{ref_id}={obj[fld]}"
            )

    return 1.0, f"add_to_array: neues {id_field} ist eindeutig+konventionell, Referenzen belegt"


def compute_confidence_score(correction_proposal, snapshot_data=None):
    """
    AP1.3b / AP4.5: Combine the raw signals into one confidence_score in [0.0, 1.0].

    Formula:
        confidence = 0.5 * llm_self_estimate   (LLM self-assessment, 0..1)
                   + 0.3 * value_grounded      (1 if the value is provable from the data, else 0)
                   + 0.2 * memory_support      (AP7; 0 for now)
    Special case: action == "manual_intervention_required" -> 0.0

    CHANGE vs. the original PT4_PLAN formula (user decision, 2026-07-11): the middle term was
    `schema_valid`, which is ALWAYS 1 — the proposal is validated against the Pydantic model
    immediately after being built, so the term was tautological dead weight and the score
    collapsed to 0.5*llm + 0.3 (0.775 in 7 of 8 measured proposals). It is replaced by
    `value_grounded`, a deterministic signal that actually discriminates (see
    compute_value_grounded). `schema_valid` is still recorded as its own field.
    """
    # Special case: no automatic correction possible -> zero confidence
    if correction_proposal.get("action") == "manual_intervention_required":
        return 0.0

    # LLM self-estimate (defensive: missing/invalid -> 0.0), clamped to [0.0, 1.0]
    llm_self = correction_proposal.get("llm_confidence")
    if not isinstance(llm_self, (int, float)) or isinstance(llm_self, bool):
        llm_self = 0.0
    llm_self = max(0.0, min(1.0, float(llm_self)))

    # Groundedness: prefer an already-computed value (set in main() once snapshot-data is
    # loaded); otherwise compute it here. Without snapshot_data it is 0.0 (conservative).
    grounded = correction_proposal.get("value_grounded")
    if not isinstance(grounded, (int, float)) or isinstance(grounded, bool):
        grounded, _ = compute_value_grounded(correction_proposal, snapshot_data)
    grounded = max(0.0, min(1.0, float(grounded)))

    # AP7.2: memory_support is precomputed in main() from the episodic case base (graded
    # 0 / 0.5 / 1.0, see memory.retrieval.compute_memory_support). Defensive: if it is absent
    # (e.g. the memory lookup failed) the term stays 0.0 and the score behaves exactly as before.
    memory_support = correction_proposal.get("memory_support")
    if not isinstance(memory_support, (int, float)) or isinstance(memory_support, bool):
        memory_support = 0.0
    memory_support = max(0.0, min(1.0, float(memory_support)))

    score = 0.5 * llm_self + 0.3 * grounded + 0.2 * memory_support
    return round(score, 3)


def generate_correction_with_llm(fix_rules, identify_response, search_results, memory_evidence=""):
    """Generate correction proposal using Azure OpenAI"""

    # Initialize Azure OpenAI client
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )

    # Build prompt
    prompt = f"""You are a data correction expert for Smart Planning API snapshots.

INPUT DATA EXPLANATION:
1. VALIDATION FIX RULES: Mandatory correction strategies for different error types. Follow these rules exactly.
2. ORIGINAL ERROR: Raw validation message from the Smart Planning API validator showing what failed.
3. ERROR ANALYSIS: Interpreted error type and search parameters from the analysis tool.
4. SEARCH RESULTS: Located error with enriched context containing:
   - enriched_context.field_examples: Valid values for reference (use to understand correct formats)
   - enriched_context.format_patterns: Detected ID patterns with statistics (use to generate new IDs)
   - enriched_context.related_entities: Similar entries and all valid IDs (use to find gaps or duplicates)
   - reference_data_available: If true, reference data from a valid snapshot is available as fallback
   - reference_data: Sample entries (first 3) from reference snapshot
   - reference_data_count: Total number of entries available in reference
   - fallback_solution: If "reference_data", use reference snapshot to populate empty array

HOW TO USE THE DATA:
- PLAN A: Check field_examples to see what valid values look like (preferred)
- PLAN A: Use format_patterns to detect ID naming conventions (preferred)
- PLAN A: Use related_entities to find missing sequence numbers or similar entries (preferred)
- PLAN B: If reference_data_available=true AND fallback_solution="reference_data", propose to copy from reference
- Follow the pattern exactly when generating new values

---

VALIDATION FIX RULES:
{fix_rules}

ORIGINAL ERROR:
{json.dumps(identify_response.get('original_error', {}), indent=2, ensure_ascii=False)}

ERROR ANALYSIS:
{json.dumps(identify_response.get('llm_analysis', {}), indent=2, ensure_ascii=False)}

SEARCH RESULTS (Error Context):
{json.dumps(search_results, indent=2, ensure_ascii=False)}

MEMORY — HUMAN-DECIDED PAST CASES (AP7.2):
{memory_evidence}

---

TASK:
Analyze the error and generate a structured correction proposal following the fix rules.

CRITICAL DECISION RULES:

0. TARGET PATH EXTRACTION (MOST IMPORTANT):
   **ALWAYS extract target_path from the SEARCH RESULTS, NEVER construct it yourself!**
   - Search results contain "path" field like "articles[40].articleId" or "demands[165].demandId"
   - Use this EXACT path as base, then append the field that needs correction
   - Example: If error is about "rel_density_min" and path is "articles[40].articleId", use "articles[40].rel_density_min"
   - **NEVER use the search_value as array index** (e.g., WRONG: "articles[106270]" when search_value="106270")
   - The search_value might be an ID value (106270), but the array index is in the path field!

1. MANUAL INTERVENTION REQUIRED:
   If search_results contains "manual_intervention_required": true:
   - Use "action": "manual_intervention_required"
   - Set "target_path": to the problematic field path
   - Set "reasoning": Explain why automatic correction is not possible (include the "reason" from search_results)
   - Do NOT attempt any automatic correction
   - This happens when reference data fallback is disabled or no solution exists

2. REFERENCE DATA FALLBACK (when enabled):
   If search_results contains "fallback_solution": "reference_data":
   - Use "action": "update_field"
   - Set "new_value": "USE_REFERENCE_DATA" 
   - Add to reasoning: "Using reference snapshot as fallback (contains X entries). ⚠ Manual verification recommended."
   - This will copy all entries from the reference snapshot

OUTPUT FORMAT (JSON):
{{
  "action": "update_field" OR "manual_intervention_required",
  "target_path": "exact.path[index].field",
  "current_value": "current value",
  "new_value": "corrected value" OR null (for manual_intervention_required),
  "reasoning": "<text>",
  "llm_confidence": <number>,
  "confidence_rationale": "<text>",
  "additional_updates": [
    {{
      "target_path": "path.to.reference",
      "current_value": "old",
      "new_value": "new"
    }}
  ]
}}

LANGUAGE (important):
- The VALUES of "reasoning" and "confidence_rationale" must be written in GERMAN — the
  reviewer is German. Write natural German prose.
- Do NOT copy these instructions into the values. Write the actual content.
- All other fields (action, target_path, values) stay technical and unchanged.

FIELD NOTE - llm_confidence (BE STRICT AND HONEST — a human reviews this):
This is your calibrated estimate that the proposed VALUE IS CORRECT — not that the JSON is
well-formed. Use the FULL scale. Do not anchor on one comfortable number.

BAND A (0.90-1.00) — the correct value is DIRECTLY READABLE from the supplied data.
   Example: the articleId is invalid, but the demand's own demandId is 'D122873_001' and the
   pattern D{{articleId}}_{{sequence}} is confirmed by other records → articleId = 122873 is
   directly derivable. You can point at the evidence.
BAND B (0.70-0.89) — the value follows a pattern that SEVERAL comparable records confirm
   consistently, but the exact value itself is not in the data.
BAND C (0.40-0.69) — you INVENT or EXTRAPOLATE a value that cannot be verified in the data
   (e.g. incrementing a sequence number to make an ID unique, guessing times from neighbours),
   OR several candidates are equally plausible.
BAND D (0.10-0.39) — essentially a guess.
0.0 — action == "manual_intervention_required".

HARD RULES:
- An ID you MADE UP (counted up, constructed) and cannot find in the data is BAND C:
  llm_confidence MUST NOT exceed 0.69, no matter how plausible the pattern looks.
- Re-read your own reasoning before answering. If it contains an inconsistency (e.g. you name
  one articleId but build the ID from another), lower the confidence and fix the value.
- A WRONG value with HIGH confidence is the worst possible outcome. An honest low value
  costs nothing — a human will look at it either way.
- "confidence_rationale": start with the band letter (A/B/C/D), then name the concrete
  evidence, in German. Example: "Band A: articleId 122873 ist direkt aus der demandId
  'D122873_001' ablesbar, das Muster ist durch D122873_002/_003 bestaetigt."
"""
    
    # Make API call
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        messages=[
            {"role": "system", "content": "You are a precise data correction expert. Always respond with valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        response_format={"type": "json_object"}
    )
    
    # Parse response
    correction_proposal = json.loads(response.choices[0].message.content)

    # AP1.3a: Ensure the raw LLM self-assessment field is present (defensive default).
    if "llm_confidence" not in correction_proposal:
        correction_proposal["llm_confidence"] = None

    # AP1.5: Persist the schema-validity signal as an explicit field (also feeds the score).
    correction_proposal["schema_valid"] = _proposal_matches_schema(correction_proposal)

    # AP1.3b: Compute the combined confidence_score and write it into the proposal.
    correction_proposal["confidence_score"] = compute_confidence_score(correction_proposal)

    # Build LLM call log
    llm_call_data = {
        "request": {
            "model": os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            "temperature": 0.3,
            "messages": [
                {"role": "system", "content": "You are a precise data correction expert. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ]
        },
        "response": {
            "content": correction_proposal,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    }
    
    return correction_proposal, llm_call_data

def main():
    import argparse
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--snapshot-id", dest="snapshot_id", default=None,
                        help="Snapshot UUID (optional, Fallback auf current_snapshot.txt)")
    args, _ = parser.parse_known_args()

    print("=== LLM Correction Proposal Generator ===\n")
    
    # Load snapshot ID (Argument hat Priorität)
    snapshot_id = load_current_snapshot_id(args.snapshot_id)
    print(f"Snapshot ID: {snapshot_id}\n")
    
    # Get latest iteration number (use existing, don't create new)
    iteration_number = get_latest_iteration_number_local(snapshot_id)
    print(f"Using existing iteration: {iteration_number}\n")
    
    # Load inputs
    print("Loading inputs...")
    # AP7.0: identify_response first — it carries the authoritative tag_error_type that selects
    # the rulebook card. In monolith mode the argument is ignored.
    identify_response = load_identify_response(snapshot_id)
    _analysis = identify_response.get("llm_analysis") or {}
    rulebook_error_type = _analysis.get("tag_error_type")
    # AP7.5: die Karten, die der Agent bei der Identifikation selbst als relevant benannt hat.
    relevant_cards = _analysis.get("relevant_cards") or []
    fix_rules = load_validation_fix_rules(rulebook_error_type, relevant_cards)
    search_results = load_search_results(snapshot_id)
    print(f"- Fix rules loaded ({len(fix_rules)} chars, mode={RULEBOOK_MODE}, error_type={rulebook_error_type})")
    if relevant_cards:
        print(f"- Vom Agenten gewaehlt: {', '.join(relevant_cards)} "
              f"({_analysis.get('relevant_cards_reasoning', '')[:80]})")
    print(f"- Error analysis loaded (iteration {identify_response.get('iteration')})")
    print(f"- Search results loaded ({search_results['results_count']} results)\n")
    
    # AP7.2: retrieve past HUMAN-decided cases for this kind of error and hand them to the LLM
    # as evidence. The target path is already known here (search_results[0].path), so the entity
    # pattern — the retrieval key — can be built before the proposal exists.
    # Defensive: any memory failure degrades to "no evidence", never breaks the pipeline.
    similar_cases, memory_evidence = [], ""
    try:
        results = search_results.get("results") or []
        query_path = results[0].get("path") if results else None
        similar_cases = mem_retrieval.find_similar_cases(query_path, rulebook_error_type)
        memory_evidence = mem_retrieval.format_cases_for_prompt(similar_cases)
        print(f"- Memory: {len(similar_cases)} vergleichbare(r) Fall/Fälle "
              f"für {mem_retrieval.entity_pattern(query_path)}")
    except Exception as _mem_err:
        print(f"WARN: memory retrieval failed, continuing without evidence: {_mem_err}")
        memory_evidence = "Gedächtnis nicht verfügbar."

    # Generate correction proposal
    print("Generating correction proposal with LLM...")
    correction_proposal, llm_call_data = generate_correction_with_llm(
        fix_rules, identify_response, search_results, memory_evidence
    )

    print(f"\nProposal generated:")
    print(f"- Action: {correction_proposal.get('action')}")
    print(f"- Target: {correction_proposal.get('target_path')}")
    print(f"- New Value: {correction_proposal.get('new_value')}")
    print(f"- Additional Updates: {len(correction_proposal.get('additional_updates', []))}")

    # AP3.5a: additively anchor guard metadata (correction_kind, target_entity_type,
    # target_entity_id, identity_check_supported). Reads the target object's identity from
    # snapshot-data.json (defensive: on any load failure the id stays None, no crash).
    try:
        snapshot_data_for_identity = get_storage().load_json(f"{snapshot_id}/snapshot-data.json")
    except Exception as _sd_err:
        print(f"WARN: could not load snapshot-data.json for identity metadata: {_sd_err}")
        snapshot_data_for_identity = None
    correction_proposal.update(
        derive_correction_identity(correction_proposal, snapshot_data_for_identity)
    )
    print(f"- Correction Kind: {correction_proposal.get('correction_kind')} "
          f"(entity={correction_proposal.get('target_entity_type')}, "
          f"id={correction_proposal.get('target_entity_id')}, "
          f"guard_supported={correction_proposal.get('identity_check_supported')})")

    # AP4.5: groundedness needs snapshot-data.json, which only exists here (the score was
    # first computed inside generate_correction_with_llm without it). Compute it now and
    # RECOMPUTE confidence_score with the real signal.
    grounded, grounded_reason = compute_value_grounded(
        correction_proposal, snapshot_data_for_identity
    )
    correction_proposal["value_grounded"] = grounded
    correction_proposal["value_grounded_reason"] = grounded_reason

    # AP7.2: memory_support — graded, deterministic, from the episodic cases only. It can only
    # be scored once the proposed value exists, so it happens here, not before the LLM call.
    try:
        support, support_reason = mem_retrieval.compute_memory_support(
            correction_proposal.get("new_value"), similar_cases
        )
    except Exception as _ms_err:
        print(f"WARN: memory_support could not be computed: {_ms_err}")
        support, support_reason = 0.0, "Gedächtnis nicht verfügbar."
    correction_proposal["memory_support"] = support
    correction_proposal["memory_support_reason"] = support_reason
    correction_proposal["memory_cases_used"] = [c["id"] for c in similar_cases]
    correction_proposal["formula_version"] = CONFIDENCE_FORMULA_VERSION

    correction_proposal["confidence_score"] = compute_confidence_score(
        correction_proposal, snapshot_data_for_identity
    )
    print(f"- Value grounded: {grounded} ({grounded_reason})")
    print(f"- Memory support: {support} ({support_reason})")
    print(f"- Confidence Score: {correction_proposal['confidence_score']} "
          f"(= 0.5*{correction_proposal.get('llm_confidence')} + 0.3*{grounded} "
          f"+ 0.2*{support}) [formula {CONFIDENCE_FORMULA_VERSION}]")
    
    # AP3.6b-2: the authoritative error_type comes from the reliable [validate_*] tag
    # (tag_error_type, produced in identify_error_llm since AP3.6b-1), not from the
    # hit-count heuristic in last_search_results.json (which mislabels e.g. a missing-field
    # error as DUPLICATE_ID — see AP3.6a).
    #
    # AP3.6c (2026-07-12, measured): the tag is present in 41 of 41 identify artifacts — it never
    # goes missing. The old fallback to the hit-count heuristic is therefore dead code with a
    # sharp edge: on the one path where it WOULD fire it hands back a value we know to be wrong
    # (DUPLICATE_ID for anything with >1 hit), and that value would flow into the rulebook card
    # selection, the memory case signature and the dashboard. A wrong label is worse than no
    # label, so the fallback is now the neutral "UNKNOWN". `legacy_error_type` is still recorded
    # next to it as an audit field. identify_snapshot.py stays untouched; its heuristic is dead.
    legacy_error_type = search_results.get("error_type")
    tag_error_type = (identify_response.get("llm_analysis") or {}).get("tag_error_type")
    authoritative_error_type = tag_error_type or "UNKNOWN"
    if not tag_error_type:
        print(f"WARN: kein [validate_*]-Tag in der Fehlermeldung — error_type=UNKNOWN "
              f"(die alte Heuristik haette '{legacy_error_type}' geraten, was unzuverlaessig ist)")

    # Build final output
    output_data = {
        "iteration": iteration_number,
        "snapshot_id": snapshot_id,
        "original_error": identify_response.get("original_error", {}),
        "error_analyzed": {
            "search_mode": search_results.get("search_mode"),
            "search_value": search_results.get("search_value"),
            "error_type": authoritative_error_type,
            "legacy_error_type": legacy_error_type,
            "results_count": search_results.get("results_count")
        },
        "correction_proposal": correction_proposal
    }
    
    # Save output
    save_correction_proposal(snapshot_id, iteration_number, output_data, llm_call_data)
    
    print("\nToken Usage:")
    print(f"- Prompt: {llm_call_data['response']['usage']['prompt_tokens']}")
    print(f"- Completion: {llm_call_data['response']['usage']['completion_tokens']}")
    print(f"- Total: {llm_call_data['response']['usage']['total_tokens']}")
    
    print("\n=== Done ===")

if __name__ == "__main__":
    main()
