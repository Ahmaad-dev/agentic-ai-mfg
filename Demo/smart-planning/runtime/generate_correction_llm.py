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

# Pydantic model for schema-validity part of the confidence score (AP1.3b)
from correction_models import CorrectionProposal

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

def load_validation_fix_rules():
    """Load the validation fix rules document"""
    rules_file = Path("runtime-files/llm-validation-fix-rules.md")
    if not rules_file.exists():
        raise FileNotFoundError("llm-validation-fix-rules.md not found")
    
    return rules_file.read_text(encoding='utf-8')

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
        _db_repo.save_proposal(record)
        print(f"Saved proposal to DB: {proposal_id}")

        # AP2.5: Read token usage from the already-saved llm_correction_call.json
        # (runtime tool NOT changed — we read the file it already wrote)
        # Cost constant mirrors web_server.py assumption; will be refined in AP6.
        _COST_PER_1K_TOKENS = 0.005  # USD / 1K tokens — assumption, not model-specific (AP6 refines this)
        call_data = storage.load_json(
            f"{snapshot_id}/iteration-{iteration_number}/llm_correction_call.json"
        )
        if call_data:
            usage = (call_data.get("response") or {}).get("usage") or {}
            tok_p = usage.get("prompt_tokens")
            tok_c = usage.get("completion_tokens")
            tok_t = usage.get("total_tokens")
            cost = round((tok_t / 1000.0) * _COST_PER_1K_TOKENS, 6) if tok_t else None
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


def compute_value_grounded(correction_proposal, snapshot_data):
    """
    Deterministic answer to: **is the proposed value provable from the data, or invented?**

    This exists because the LLM's own `llm_confidence` is not calibratable by prompt alone.
    Measured: it rated an ID it had INVENTED (counted a sequence number up) as "Band A / 0.9"
    — in exactly the case where it was wrong and the human had to overrule it. A self-estimate
    cannot distinguish "I read this from the data" from "I made this up"; this check can.

    Returns (grounded: float 0.0|1.0, reason: str). Conservative: anything it cannot verify
    counts as NOT grounded, so an unverifiable value never inflates the score.

    Grounded (1.0) means one of:
      a) the value is a REFERENCE and the referenced object exists (e.g. demands[i].articleId
         set to 122873 and articles[] really contains articleId 122873), or
      b) the identical value/structure already exists on the SAME field of another object of
         the same array (e.g. a workItemConfigs array copied from a comparable article).
    Not grounded (0.0) means the value cannot be found anywhere — it was constructed. The
    classic case is de-duplicating an ID by incrementing a counter: the new ID must be unique,
    so by definition it is NOT in the data. That is precisely a value a human should look at.
    """
    if correction_proposal.get("action") == "manual_intervention_required":
        return 0.0, "manual_intervention_required"

    new_value = correction_proposal.get("new_value")
    if new_value is None or new_value == "":
        return 0.0, "kein new_value"
    if not isinstance(snapshot_data, dict):
        return 0.0, "snapshot-data nicht ladbar (konservativ: nicht belegt)"

    array_name, index, field = _parse_target_entity(correction_proposal.get("target_path"))
    if not array_name or not field:
        return 0.0, "target_path nicht auswertbar"

    # (a0) IDENTITY field of its own array (demands[i].demandId, articles[i].articleId, ...).
    # Such a value must be UNIQUE, so it can never be "read from the data" — it is always
    # constructed. Grounded is therefore 0 by definition. And if the proposed value DOES
    # already exist elsewhere, the proposal is not merely unproven, it is provably wrong:
    # applying it would create a NEW duplicate. (Measured: the LLM proposed 'D210451_002'
    # for a de-duplication — an ID that already sat on demands[768].)
    if ENTITY_IDENTITY_FIELD.get(array_name) == field:
        objects = snapshot_data.get(array_name)
        if isinstance(objects, list):
            for i, o in enumerate(objects):
                if i != index and isinstance(o, dict) and o.get(field) == new_value:
                    return 0.0, (
                        f"KOLLISION: {array_name}[{i}].{field} traegt bereits {new_value!r} "
                        f"— dieser Vorschlag wuerde ein neues Duplikat erzeugen"
                    )
        return 0.0, (
            f"Identitaetsfeld: {new_value!r} muss neu/eindeutig sein und ist daher "
            f"grundsaetzlich nicht aus den Daten belegbar (konstruiert)"
        )

    # (a) Reference field -> the referenced object must exist.
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
        if i == index or not isinstance(o, dict):
            continue
        if field in o and o[field] == new_value:
            return 1.0, (
                f"Wert existiert bereits in {array_name}[{i}].{field} "
                f"— aus vergleichbarem Datensatz uebernommen"
            )

    return 0.0, (
        f"Wert nicht in den Daten auffindbar — konstruiert/erfunden "
        f"(kein {array_name}[*].{field} mit diesem Wert)"
    )


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

    # Memory support arrives in AP7
    memory_support = 0.0

    score = 0.5 * llm_self + 0.3 * grounded + 0.2 * memory_support
    return round(score, 3)


def generate_correction_with_llm(fix_rules, identify_response, search_results):
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
    fix_rules = load_validation_fix_rules()
    identify_response = load_identify_response(snapshot_id)
    search_results = load_search_results(snapshot_id)
    print(f"- Fix rules loaded ({len(fix_rules)} chars)")
    print(f"- Error analysis loaded (iteration {identify_response.get('iteration')})")
    print(f"- Search results loaded ({search_results['results_count']} results)\n")
    
    # Generate correction proposal
    print("Generating correction proposal with LLM...")
    correction_proposal, llm_call_data = generate_correction_with_llm(fix_rules, identify_response, search_results)
    
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
    correction_proposal["confidence_score"] = compute_confidence_score(
        correction_proposal, snapshot_data_for_identity
    )
    print(f"- Value grounded: {grounded} ({grounded_reason})")
    print(f"- Confidence Score: {correction_proposal['confidence_score']} "
          f"(= 0.5*{correction_proposal.get('llm_confidence')} + 0.3*{grounded} + 0.2*0)")
    
    # AP3.6b-2: the authoritative error_type comes from the reliable [validate_*] tag
    # (tag_error_type, produced in identify_error_llm since AP3.6b-1), not from the
    # hit-count heuristic in last_search_results.json (which mislabels e.g. a missing-field
    # error as DUPLICATE_ID — see AP3.6a). Fallback to the old heuristic value if the tag is
    # missing/null (message without a tag), so behaviour is preserved for those cases. The
    # old value is kept additively as legacy_error_type for traceability/comparison.
    # identify_snapshot.py is intentionally left as-is; its heuristic error_type is now dead.
    legacy_error_type = search_results.get("error_type")
    tag_error_type = (identify_response.get("llm_analysis") or {}).get("tag_error_type")
    authoritative_error_type = tag_error_type if tag_error_type else legacy_error_type

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
