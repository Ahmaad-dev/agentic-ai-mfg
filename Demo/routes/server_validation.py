"""
AP3.3d — Trigger and await server-side snapshot validation.

Why this exists
---------------
`update_snapshot.py` (PUT .../snapshots/{id}) CLEARS a snapshot's validation messages on
the server. `GET .../validation-messages` then returns `[]` and STAYS empty until a
validation job is run. The server does not recompute automatically — the web UI's
"Validierung" tab silently fires that job, which is why the UI showed errors while our
tooling saw none.

`validate_snapshot.py` only performs the GET, never the trigger. So the re-validation
step of every correction pipeline (`apply_and_upload`, `full_correction`,
`correction_from_validation`) reads an empty list right after an upload and reports
`errors=0` — a false green. This module supplies the missing trigger.

Hard rule honoured: no runtime tool is modified. `SmartPlanningAPI` is IMPORTED from
`validate_snapshot` (import does not change the tool), reused only for auth + base URI.

Completion signal
-----------------
There is no job-status endpoint (probed: `/jobs/{id}`, `/snapshots/{id}/jobs`, … all 404).
But `POST .../validate` returns a job `{"id","type":"VALIDATE","status":"QUEUED",...}` and
the same job appears in `GET .../snapshots/{id}` under `solverJobs`, where its status
transitions `QUEUED → FINISHED` with a `finishedAt` timestamp. Polling that job by id is
what lets us tell "job still running" (→ keep waiting) apart from "job finished, snapshot
genuinely has no messages" (→ empty list is the real answer, not a false green).
"""
from __future__ import annotations

import sys as _sys
import time
from pathlib import Path
from typing import Optional

# Import the runtime tool's API client without importing (or touching) the tool's CLI.
_runtime_dir = str(Path(__file__).parent.parent / "smart-planning" / "runtime")
if _runtime_dir not in _sys.path:
    _sys.path.insert(0, _runtime_dir)

import requests  # noqa: E402
from validate_snapshot import SmartPlanningAPI  # noqa: E402

#: Terminal solverJob states. FINISHED is the observed success value; the others are
#: defensive so a failed/aborted job ends the wait instead of hanging to the timeout.
_TERMINAL_STATES = {"FINISHED", "FAILED", "COMPLETED", "DONE", "ERROR", "CANCELLED"}
_SUCCESS_STATES = {"FINISHED", "COMPLETED", "DONE"}

DEFAULT_TIMEOUT_S = 60
_POLL_INTERVAL_S = 3


def trigger_server_validation(
    snapshot_id: str,
    timeout_s: int = DEFAULT_TIMEOUT_S,
) -> dict:
    """
    Start a server-side validation job and wait until it finishes.

    Returns a dict:
        {"ok": True,  "job_id", "status", "waited_s"}                     — job finished
        {"ok": False, "job_id", "status", "waited_s", "error"}            — failed/timeout

    `ok=True` means the messages on the server now reflect the current snapshot data, so a
    subsequent read is trustworthy (an empty list then genuinely means "no messages").
    Raises no exception on a slow/failed job — the caller decides what to do with `ok`.
    """
    api = SmartPlanningAPI()
    api.authenticate()
    headers = {"Authorization": f"Bearer {api.token}"}
    base = f"{api.base_uri}/esarom-be/api/v1/snapshots/{snapshot_id}"

    post = requests.post(f"{base}/validate", headers=headers, verify=False, timeout=30)
    post.raise_for_status()
    job = post.json()
    job_id = job.get("id")
    status = job.get("status")

    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if status in _TERMINAL_STATES:
            break
        time.sleep(_POLL_INTERVAL_S)
        status = _job_status(base, headers, job_id)

    waited = round(time.time() - t0, 1)

    if status in _SUCCESS_STATES:
        return {"ok": True, "job_id": job_id, "status": status, "waited_s": waited}

    if status in _TERMINAL_STATES:
        return {
            "ok": False,
            "job_id": job_id,
            "status": status,
            "waited_s": waited,
            "error": f"Validation job ended in non-success state {status!r}",
        }

    return {
        "ok": False,
        "job_id": job_id,
        "status": status,
        "waited_s": waited,
        "error": f"Validation job did not finish within {timeout_s}s (last status {status!r})",
    }


def _job_status(base: str, headers: dict, job_id: Optional[str]) -> Optional[str]:
    """Read the current status of our validate job from the snapshot's solverJobs list."""
    if not job_id:
        return None
    resp = requests.get(base, headers=headers, verify=False, timeout=30)
    resp.raise_for_status()
    for job in resp.json().get("solverJobs", []):
        if job.get("id") == job_id:
            return job.get("status")
    return None
