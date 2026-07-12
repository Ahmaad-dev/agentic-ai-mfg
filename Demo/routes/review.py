"""
AP3.1 / AP3.2 / AP3.3b — HitL Review Blueprint.

Routes under /api/review:
    GET  /api/review/proposals              — list all pending_review proposals (newest first)
    GET  /api/review/proposals/<id>         — full detail for one proposal (404 if unknown)
    POST /api/review/proposals/<id>/approve — accept the AI suggestion, then apply it
    POST /api/review/proposals/<id>/reject  — discard it for good (comment required)
    POST /api/review/proposals/<id>/modify  — replace it with a human value, then apply it

The database is the single source of truth; _proposals/*.json files are NOT read here.

=============================================================================
GOVERNANCE — READ BEFORE CHANGING `_apply_after_review`
=============================================================================
This module is the ONLY place in the system that legitimately writes snapshot data.

Everywhere else, auto-apply is closed by the `HUMAN_IN_THE_LOOP` toggle, which lives in
`orchestration_agent._execute_sp_agent` (it remaps correction pipelines to `analyze_only`
and blocks `apply_correction` / `apply_and_upload`). Calling `SPAgent` directly — as we
do here — bypasses that toggle, because the toggle sits in the orchestrator, not in the
agent.

That bypass is intentional: the human approval recorded in the `reviews` table IS the
authorisation the toggle exists to demand. To stop this from becoming an unguarded back
door, `_apply_after_review` re-derives that authorisation from the DB before it writes:

    1. the proposal must be in status `approved` or `modified`  (not pending/rejected/applied)
    2. there must be at least one `reviews` row for it          (a human really decided)
    3. the AP3.3a iteration guard must pass                     (the reviewed proposal is
                                                                 the one apply_correction
                                                                 would actually pick)

Any new caller of the apply path must go through `_apply_after_review`, never straight to
`SPAgent.execute_pipeline`.
=============================================================================
"""
import copy
import datetime as _dt
import json
import logging
import re
from pathlib import Path

from flask import Blueprint, jsonify, request
from requests.exceptions import ConnectionError, Timeout

from db import repository as repo
from memory import long_term  # AP7.1: every completed review becomes an episodic case
from memory import retrieval  # AP7.3: show the reviewer the past cases behind memory_support
from routes.apply_prep import (
    ProposalApplyBlockedError,
    check_identity_guard,
    check_iteration_is_latest,
    get_storage,
    prepare_proposal_for_apply,
)
from routes.server_validation import trigger_server_validation

logger = logging.getLogger(__name__)

review_bp = Blueprint("review", __name__, url_prefix="/api/review")

# PT4 has no authentication layer (Azure AD is explicitly out of scope), so there is
# no authenticated principal to attribute a decision to. Every review is therefore
# recorded under this fixed reviewer. The `reviews.reviewer_ref` column already holds
# a real user reference once an auth layer exists.
REVIEWER_REF = "demo_reviewer"

#: Only these statuses may trigger an application (see governance block above).
APPLICABLE_STATUS = ("approved", "modified")

#: Existing pipeline: apply_correction -> update_snapshot -> validate_snapshot.
#: Not classified as a correction pipeline, so it runs WITHOUT the auto-iteration loop.
APPLY_PIPELINE = "apply_and_upload"

_sp_agent = None


def _get_sp_agent():
    """
    Lazy module singleton.

    `web_server.py` imports this blueprint and builds its own SPAgent, so importing
    `web_server` from here would be circular. Building our own instance is cheap:
    `BaseAgent.__init__` only assigns attributes — no Azure client, no LLM, no state.
    """
    global _sp_agent
    if _sp_agent is None:
        from agents.sp_agent import SPAgent  # imported late, keeps module import light

        runtime_dir = Path(__file__).parent.parent / "smart-planning" / "runtime"
        _sp_agent = SPAgent(runtime_dir=runtime_dir)
    return _sp_agent

# PT4 has no authentication layer (Azure AD is explicitly out of scope), so there is
# no authenticated principal to attribute a decision to. Every review is therefore
# recorded under this fixed reviewer. The `reviews.reviewer_ref` column already holds
# a real user reference once an auth layer exists.
REVIEWER_REF = "demo_reviewer"


@review_bp.get("/proposals")
def list_proposals():
    """Return all open (pending_review) proposals, newest first.

    Fields returned: proposal_id, snapshot_id, error_type, target_path,
                     confidence_score, status, created_at.
    """
    proposals = repo.list_open_proposals_as_dicts()
    return jsonify(proposals), 200


@review_bp.get("/proposals/<proposal_id>")
def get_proposal(proposal_id: str):
    """Return full detail for a single proposal.

    Returns HTTP 404 with a JSON error body if the proposal_id is unknown.
    """
    proposal = repo.get_proposal_as_dict(proposal_id)
    if proposal is None:
        return jsonify({"error": "Proposal not found", "proposal_id": proposal_id}), 404
    return jsonify(proposal), 200


#: Wie viele Zeilen vor/nach der Fehlerstelle gezeigt werden.
_CONTEXT_LINES = 7


@review_bp.get("/proposals/<proposal_id>/context")
def get_proposal_context(proposal_id: str):
    """
    AP4.7: Die betroffene Stelle 1:1 aus `snapshot-data.json`, mit echten Zeilennummern.

    Warum das nötig ist: Der Reviewer sieht bisher nur `target_path` und den alten Wert. Um
    eine Korrektur wirklich beurteilen zu können, muss er den Datensatz IM ORIGINAL sehen —
    also den umgebenden JSON-Ausschnitt, so wie er auf der Platte steht.

    Wie die Zeilennummern exakt werden: Der Zielwert wird in einer Kopie durch eine
    eindeutige Marke ersetzt und das GANZE Dokument gedumpt. Alles VOR dem Ziel ist in beiden
    Dumps zeichengleich, die Zeile der Marke ist damit exakt die Zeile des Zielfelds im
    echten Dump. (Einfach mitzählen ginge nicht: derselbe Schlüsselname kommt tausendfach vor.)
    """
    proposal = repo.get_proposal_as_dict(proposal_id)
    if proposal is None:
        return jsonify({"error": "Proposal not found", "proposal_id": proposal_id}), 404

    snapshot_id = proposal["snapshot_id"]
    target_path = proposal.get("target_path") or ""

    m = re.match(r"^(\w+)\[(\d+)\]\.(\w+)", target_path)
    if not m:
        return jsonify({
            "error": "Kein auswertbarer target_path",
            "target_path": target_path,
        }), 422
    array_name, index, field = m.group(1), int(m.group(2)), m.group(3)

    data = get_storage().load_json(f"{snapshot_id}/snapshot-data.json")
    if not isinstance(data, dict):
        return jsonify({"error": "snapshot-data.json nicht lesbar",
                        "snapshot_id": snapshot_id}), 404

    arr = data.get(array_name)
    if not isinstance(arr, list) or index >= len(arr) or not isinstance(arr[index], dict):
        return jsonify({"error": f"Position {array_name}[{index}] existiert nicht"}), 404
    if field not in arr[index]:
        return jsonify({"error": f"Feld {field!r} fehlt in {array_name}[{index}]"}), 404

    dump = lambda d: json.dumps(d, indent=2, ensure_ascii=False).splitlines()
    original_lines = dump(data)

    marker = "__PT4_TARGET_a7f3__"
    probe = copy.deepcopy(data)
    probe[array_name][index][field] = marker
    probe_lines = dump(probe)

    hit = next((i for i, line in enumerate(probe_lines) if marker in line), None)
    if hit is None:
        return jsonify({"error": "Zielzeile nicht auffindbar"}), 500

    # Der Wert kann mehrzeilig sein (Array/Objekt) -> die ganze Spanne markieren.
    end = hit
    opener = original_lines[hit].rstrip()
    if opener.endswith("[") or opener.endswith("{"):
        depth = 0
        for i in range(hit, len(original_lines)):
            depth += original_lines[i].count("[") + original_lines[i].count("{")
            depth -= original_lines[i].count("]") + original_lines[i].count("}")
            if depth <= 0:
                end = i
                break

    start = max(0, hit - _CONTEXT_LINES)
    stop = min(len(original_lines), end + 1 + _CONTEXT_LINES)

    # Sehr lange Wertblöcke (z. B. 13 workItemConfigs) nicht ungebremst ausrollen.
    MAX_SPAN = 40
    truncated = False
    if end - hit > MAX_SPAN:
        end = hit + MAX_SPAN
        stop = end + 1
        truncated = True

    return jsonify({
        "file": "snapshot-data.json",
        "snapshot_id": snapshot_id,
        "target_path": target_path,
        "error_line": hit + 1,
        "lines": [
            {"n": i + 1, "text": original_lines[i], "highlight": hit <= i <= end}
            for i in range(start, stop)
        ],
        "truncated": truncated,
        "total_lines": len(original_lines),
    }), 200


@review_bp.get("/proposals/<proposal_id>/memory")
def get_proposal_memory(proposal_id: str):
    """
    AP7.3: What did humans decide on THIS kind of error before?

    Without this, the memory effect is only a number (`memory_support`) inside the confidence
    score — the reviewer cannot see what the system learned from. Here it becomes evidence he
    can check: the past cases, what the AI proposed then, what the human made of it, and why.

    Matched by entity pattern, not error_type — see memory/retrieval.py for the reason.
    """
    proposal = repo.get_proposal_as_dict(proposal_id)
    if proposal is None:
        return jsonify({"error": "Proposal not found", "proposal_id": proposal_id}), 404

    cases = retrieval.find_similar_cases(
        proposal.get("target_path"), proposal.get("error_type"), top_k=5
    )
    # A case built from THIS proposal is not evidence for it — hide the self-reference.
    cases = [c for c in cases if c.get("source_proposal_id") != proposal_id]

    return jsonify({
        "proposal_id": proposal_id,
        "pattern": retrieval.entity_pattern(proposal.get("target_path")),
        "count": len(cases),
        "approved": sum(1 for c in cases if c.get("decision") == "approve"),
        "modified": sum(1 for c in cases if c.get("decision") == "modify"),
        "rejected": sum(1 for c in cases if c.get("decision") == "reject"),
        "memory_support": proposal.get("memory_support"),
        "memory_support_reason": proposal.get("memory_support_reason"),
        "cases": cases,
    }), 200


# --------------------------------------------------------------------------- #
# AP3.2 — decision endpoints
# --------------------------------------------------------------------------- #
def _request_body() -> dict:
    """Parsed JSON body, tolerating a missing body or a missing content-type."""
    return request.get_json(silent=True) or {}


def _validate_now(agent, snapshot_id):
    """
    Get the TRUE server-side validation state for a snapshot.

    Triggers the validation job and waits for it (server clears messages on upload and does
    not recompute on its own — AP3.3d), then refreshes the local snapshot-validation.json by
    running the `validate_snapshot` tool, whose `_run_tool` special-case already parses the
    structured result. Returns (validation_dict_or_None, trigger_dict).
    """
    trigger = trigger_server_validation(snapshot_id)
    tool = agent.execute_tool("validate_snapshot", [snapshot_id])
    validation = tool.get("validation")
    return validation, trigger


def _apply_after_review(proposal_id: str, decision: str, final_value=None, comment=None):
    """
    Apply a reviewed correction to the real snapshot data. Returns (apply_dict, http_status).

    THIS IS THE ONLY WRITE PATH TO SNAPSHOT DATA — see the governance block at the top of
    this module. The authorisation is re-derived from the DB here, not taken on trust from
    the caller, so the checks below hold even if a future caller reaches this function by
    another route.

    Synchronous by design: the reviewer sees the re-validation result in the same response.
    Cost of that choice: `_run_tool` allows 90 s per tool and `_execute_pipeline` retries a
    failing step up to 3 times, so this call can in the worst case block for roughly
    3 tools x 3 attempts x 90 s. In practice a healthy run is seconds. If the UI ever needs
    a fast ack, this is the piece to move to a background job.
    """
    state = repo.get_decision_state(proposal_id)
    if state is None:
        return {"error": "Proposal not found", "proposal_id": proposal_id}, 404

    # Guard 1+2: a human decision must exist in the DB, and it must be an applicable one.
    if state["status"] not in APPLICABLE_STATUS or state["review_count"] < 1:
        return (
            {
                "error": "Proposal is not in an applicable state",
                "proposal_id": proposal_id,
                "status": state["status"],
                "review_count": state["review_count"],
                "hint": (
                    "Only a proposal with status 'approved' or 'modified' and at least one "
                    "review row may be applied."
                ),
            },
            409,
        )

    # Guard 3 (AP3.3a): apply_correction.py resolves the HIGHEST iteration itself, so a
    # newer iteration would silently apply a different correction than the reviewed one.
    # Note: filesystem is read here, decision lives in the DB — a new iteration appearing
    # between this check and the subprocess call is a theoretical TOCTOU race, accepted
    # for the single-user demo.
    iteration_ok, guard_message = check_iteration_is_latest(proposal_id)
    if not iteration_ok:
        return (
            {
                "error": "Proposal cannot be applied",
                "proposal_id": proposal_id,
                "reason": guard_message,
                "status": state["status"],
            },
            409,
        )

    # Guard 4 (AP3.5b): the object at the target position must still be the one this
    # proposal was generated for — protection against silently correcting the wrong object
    # after the array was reordered. Skips FILL_IDENTITY / unsupported entities / UNKNOWN /
    # add_object / legacy proposals (no soll-identity to compare); those pass through.
    identity_ok, identity_msg, identity_info = check_identity_guard(proposal_id)
    if identity_msg:
        logger.info("[review] AP3.5b %s (proposal=%s)", identity_msg, proposal_id)
    if not identity_ok:
        return (
            {
                "error": "Proposal cannot be applied",
                "proposal_id": proposal_id,
                "reason": identity_msg,
                "guard": identity_info.get("guard"),
                "status": state["status"],
            },
            409,
        )

    snapshot_id = state["snapshot_id"]
    agent = _get_sp_agent()

    # errors_before: the server clears validation on upload and does not recompute on its
    # own (AP3.3d finding), so a plain read is a false green. Trigger the job and read the
    # PRE-apply state here — without this baseline we cannot show the correction did anything.
    try:
        before_validation, _ = _validate_now(agent, snapshot_id)
    except (ConnectionError, Timeout) as exc:
        revalidation_result = {
            "pipeline": APPLY_PIPELINE,
            "pipeline_success": False,
            "value_source": None,
            "value_applied": None,
            "errors_before": None,
            "errors_after": None,
            "validation": None,
            "validation_trigger": None,
            "failed_at": "pre_apply_validation",
            "error": str(exc),
        }
        repo.set_latest_review_revalidation(proposal_id, revalidation_result)
        logger.error("[review] Pre-apply validation failed for %s: %s", proposal_id, exc)
        return (
            {
                "error": "Apply pipeline failed",
                "proposal_id": proposal_id,
                "status": state["status"],
                "applied": False,
                "failed_at": revalidation_result["failed_at"],
                "detail": revalidation_result["error"],
                "revalidation_result": revalidation_result,
            },
            502,
        )
    errors_before = before_validation.get("errors") if before_validation else None

    try:
        preparation = prepare_proposal_for_apply(proposal_id, decision, final_value, comment)
    except ProposalApplyBlockedError as exc:
        logger.warning("[review] Apply blocked for %s: %s", proposal_id, exc)
        return (
            {
                "error": "Proposal cannot be applied",
                "proposal_id": proposal_id,
                "status": state["status"],
                "applied": False,
                "action": exc.action,
                "reason": str(exc),
            },
            422,
        )

    logger.warning(
        "[review] APPLYING reviewed correction to snapshot %s (proposal=%s, decision=%s, "
        "value_source=%s) — human approval on record, HUMAN_IN_THE_LOOP toggle bypassed "
        "by design",
        snapshot_id,
        proposal_id,
        decision,
        preparation["value_source"],
    )
    pipeline = agent.execute_pipeline(APPLY_PIPELINE, snapshot_id)
    pipeline_ok = bool(pipeline.get("success"))

    # The pipeline's own final validate_snapshot reads an empty list (the upload cleared the
    # server messages), so it is a false green. Trigger the validation job, wait for it, then
    # read — this is the real post-apply state. See routes/server_validation.py.
    validation = None
    trigger = None
    if pipeline_ok:
        try:
            validation, trigger = _validate_now(agent, snapshot_id)
        except (ConnectionError, Timeout) as exc:
            revalidation_result = {
                "pipeline": APPLY_PIPELINE,
                "pipeline_success": pipeline_ok,
                "value_source": preparation["value_source"],
                "value_applied": preparation["value_to_apply"],
                "errors_before": errors_before,
                "errors_after": None,
                "validation": None,
                "validation_trigger": None,
                "failed_at": "post_apply_validation",
                "error": str(exc),
            }
            repo.set_latest_review_revalidation(proposal_id, revalidation_result)
            logger.error("[review] Post-apply validation failed for %s: %s", proposal_id, exc)
            return (
                {
                    "error": "Apply pipeline failed",
                    "proposal_id": proposal_id,
                    "status": state["status"],
                    "applied": False,
                    "failed_at": revalidation_result["failed_at"],
                    "detail": revalidation_result["error"],
                    "revalidation_result": revalidation_result,
                },
                502,
            )

    revalidation_result = {
        "pipeline": APPLY_PIPELINE,
        "pipeline_success": pipeline_ok,
        "value_source": preparation["value_source"],
        "value_applied": preparation["value_to_apply"],
        "errors_before": errors_before,
        "errors_after": validation.get("errors") if validation else None,
        "validation": validation,
        "validation_trigger": trigger,
        "failed_at": pipeline.get("failed_at"),
        "error": pipeline.get("error"),
    }
    # Recorded on failure too, so the audit trail shows what the attempt did.
    repo.set_latest_review_revalidation(proposal_id, revalidation_result)

    if not pipeline_ok:
        # Status stays approved/modified — the human can trigger the apply again.
        logger.error(
            "[review] Apply pipeline failed for %s at step %s: %s",
            proposal_id,
            pipeline.get("failed_at"),
            pipeline.get("error"),
        )
        return (
            {
                "error": "Apply pipeline failed",
                "proposal_id": proposal_id,
                "status": state["status"],
                "applied": False,
                "failed_at": pipeline.get("failed_at"),
                "detail": pipeline.get("error"),
                "revalidation_result": revalidation_result,
            },
            502,
        )

    if validation:
        repo.upsert_snapshot_meta(
            snapshot_id,
            errors_before=errors_before,
            warnings_before=before_validation.get("warnings") if before_validation else None,
            errors_after=validation.get("errors"),
            warnings_after=validation.get("warnings"),
            last_validated_at=_dt.datetime.now(_dt.timezone.utc),
        )

    repo.set_proposal_status(proposal_id, "applied")
    return (
        {
            "applied": True,
            "status": "applied",
            "value_source": preparation["value_source"],
            "value_applied": preparation["value_to_apply"],
            "revalidation_result": revalidation_result,
        },
        200,
    )


def _decide(proposal_id: str, decision: str, final_value=None, comment=None):
    """Persist one decision and, for approve/modify, apply it. Returns an HTTP response."""
    result = repo.decide_proposal(
        proposal_id=proposal_id,
        decision=decision,
        final_value=final_value,
        comment=comment,
        reviewer_ref=REVIEWER_REF,
    )

    if result["outcome"] == "not_found":
        return jsonify({"error": "Proposal not found", "proposal_id": proposal_id}), 404

    if result["outcome"] == "already_decided":
        return (
            jsonify(
                {
                    "error": "Proposal has already been decided",
                    "proposal_id": proposal_id,
                    "status": result["status"],
                    "hint": "Only a proposal with status 'pending_review' can be decided.",
                }
            ),
            409,
        )

    body = {k: v for k, v in result.items() if k != "outcome"}

    if decision == "reject":
        # A rejection is final and applies nothing. It is still a case worth remembering:
        # "the AI proposed X and a human threw it out" (AP7.1).
        body["applied"] = False
        long_term.record_case_safe(proposal_id)
        return jsonify(body), 200

    # approve / modify: the decision is committed; now actually apply it. If the apply
    # fails or is blocked, the decision stands and the proposal keeps its decided status.
    apply_result, apply_status = _apply_after_review(proposal_id, decision, final_value, comment)
    body.update(apply_result)
    # AP7.1: record the case AFTER the apply, so the revalidation outcome is already on the
    # review row. record_case_safe never raises — memory must not break a human decision.
    long_term.record_case_safe(proposal_id)
    return jsonify(body), apply_status


@review_bp.post("/proposals/<proposal_id>/approve")
def approve_proposal(proposal_id: str):
    """Accept the AI suggestion as-is, then apply it. Body: {"comment": optional}."""
    comment = _request_body().get("comment")
    return _decide(proposal_id, "approve", comment=comment)


@review_bp.post("/proposals/<proposal_id>/reject")
def reject_proposal(proposal_id: str):
    """Discard the proposal for good. Body: {"comment": required}.

    Final: no automatic regeneration, no retry. Nothing is applied.
    The comment is mandatory because a rejection is the one decision that yields no
    value — the reasoning is the only thing it leaves behind (and AP7 learns from it).
    """
    comment = _request_body().get("comment")
    if not isinstance(comment, str) or not comment.strip():
        return (
            jsonify(
                {
                    "error": "A non-empty 'comment' is required to reject a proposal",
                    "proposal_id": proposal_id,
                }
            ),
            400,
        )
    return _decide(proposal_id, "reject", comment=comment)


@review_bp.post("/proposals/<proposal_id>/modify")
def modify_proposal(proposal_id: str):
    """Replace the AI value with a human one, then apply it.

    Body: {"final_value": required, "comment": optional}. The AI suggestion stays untouched
    in proposals.suggested_value (and in llm_correction_proposal.ai_original.json) as
    history; the human value is stored in reviews.final_value and is what gets applied.
    """
    body = _request_body()
    if "final_value" not in body or body["final_value"] is None:
        return (
            jsonify(
                {
                    "error": "'final_value' is required to modify a proposal",
                    "proposal_id": proposal_id,
                }
            ),
            400,
        )
    return _decide(
        proposal_id,
        "modify",
        final_value=body["final_value"],
        comment=body.get("comment"),
    )
