"""
AP6.1 — Dashboard metrics blueprint.

Routes under /api/dashboard:
    GET /api/dashboard/metrics   — all KPIs, chart series, open reviews, data-quality flags

Read-only. This module never writes; it aggregates what AP2/AP3 already persisted
(`proposals`, `reviews`, `agent_runs`, `snapshots_meta`). No new data source, no schema
change, no migration.

=============================================================================
WHY THIS FILE CARRIES A `data_quality` BLOCK
=============================================================================
The DB holds a MIX of genuine runs and test fixtures, and two of its columns changed
meaning mid-project. A dashboard that quietly averages over all of it would produce
confident-looking numbers that are wrong — which is exactly the failure mode this whole
project exists to prevent. So every KPI is computed from ALL data (nothing is silently
filtered), and anything that makes a number less than trustworthy is emitted as an
explicit flag the UI must show:

  1. REVALIDATION_PRE_AP33D — before AP3.3d, `validate_snapshot` read the server's message
     list WITHOUT triggering the validation job first, so it always reported "0 errors"
     (a false green). Those `revalidation_result` entries are recognisable by the ABSENCE
     of the `errors_before` key, which AP3.3d introduced. Detected from the data, not from
     a hardcoded cutoff date.
  2. CONFIDENCE_LEGACY_FORMULA — before AP4.5 the middle term of the confidence formula was
     `schema_valid`, which is ALWAYS 1, so the score collapsed to a near-constant ~0.775.
     Those rows are recognisable by `value_grounded IS NULL`. Their confidence carries no
     information, which is why the calibration curve is currently flat.
  3. ERROR_TYPE_LEGACY_HEURISTIC — before AP3.6b, `error_type` came from a hit-count
     heuristic in `identify_snapshot.py` (>1 match => "DUPLICATE_ID"), not from an error
     classification. Its vocabulary is {DUPLICATE_ID, SINGLE_MATCH, NO_RESULTS_FOUND};
     those labels describe how often a value occurred, not what was wrong.
  4. HANDLING_TIME_FIXTURES — several reviews are scripted test fixtures decided in the
     same second the proposal was created. A sub-minute decision cannot be a human reading
     a diff, so it is reported separately instead of dragging the average to zero.
  5. SMALL_SAMPLE — with n < 10 decisions, no rate here is statistically meaningful.

If a flag ever disappears because the underlying data got clean, that is the signal that
the KPI became trustworthy. Do not suppress a flag to make the dashboard look better.
=============================================================================
"""
from __future__ import annotations

import datetime as _dt
import logging
from typing import Any, Optional

from flask import Blueprint, jsonify, request

from cost_model import describe_prices, estimate_cost
from db import repository as repo

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")

#: Vocabulary of the pre-AP3.6b hit-count heuristic. These are not error classes:
#: they say how often the searched value occurred (see AP3.6a in PROJECT_LOG.md).
LEGACY_ERROR_LABELS = frozenset({"DUPLICATE_ID", "SINGLE_MATCH", "NO_RESULTS_FOUND"})

#: A decision faster than this cannot be a human reading a before/after diff.
#: Used ONLY to separate scripted fixtures from real decisions, never to delete data.
MIN_HUMAN_DECISION_SECONDS = 60

#: Below this many decisions, every rate on this page is anecdote, not statistics.
SMALL_SAMPLE_THRESHOLD = 10

#: Confidence axis for both the distribution and the calibration curve.
CONFIDENCE_BUCKETS = [(0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)]

#: A decision counts as "AI was right" only if the human took the value UNCHANGED.
#: `modify` means the human had to correct it; `reject` means it was unusable.
#: This is the AK2 metric (">= 80% accepted without modification").
ACCEPTED_UNCHANGED = "approve"


def _as_naive_utc(value: Any) -> Optional[_dt.datetime]:
    """
    Normalise a timestamp for arithmetic.

    SQLite hands back naive datetimes even for `DateTime(timezone=True)` columns, while
    the ORM defaults write aware ones. Subtracting the two raises TypeError, so both are
    flattened to naive UTC here.
    """
    if not isinstance(value, _dt.datetime):
        return None
    if value.tzinfo is not None:
        return value.astimezone(_dt.timezone.utc).replace(tzinfo=None)
    return value


def _rate(part: int, whole: int) -> Optional[float]:
    """Share of `part` in `whole`, rounded; None when there is nothing to divide by."""
    if not whole:
        return None
    return round(part / whole, 4)


def _bucket_label(low: float, high: float) -> str:
    return f"{low:.1f}–{high:.1f}"


def _bucket_index(score: float) -> int:
    """Index of the confidence bucket holding `score` (1.0 belongs to the last bucket)."""
    for i, (low, high) in enumerate(CONFIDENCE_BUCKETS):
        if low <= score < high:
            return i
    return len(CONFIDENCE_BUCKETS) - 1


def _median(values: list[float]) -> Optional[float]:
    """Median — reported next to the mean because single outliers dominate a small n."""
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def _revalidation_is_trustworthy(result: Any) -> bool:
    """
    True only for re-validations recorded AFTER AP3.3d.

    The marker is the `errors_before` key: AP3.3d added it together with the validation-job
    trigger that made the numbers real. An entry without it comes from the era where the
    server was asked for its message list before it had recomputed one — it reports
    `errors_after: 0` for every run, successful or not.
    """
    return isinstance(result, dict) and "errors_before" in result


# =========================================================================== #
# AP6.4a — time range
#
# FLOW vs STOCK — the distinction the whole filter hinges on.
#   FLOW  = events that happened IN a period: proposals created, decisions taken, tokens
#           burnt, validations run. These are filtered by the range.
#   STOCK = the state right NOW: which proposals are still open. This is NOT filtered.
# Filtering the stock would be a lie: selecting "last week" would report "0 open reviews"
# while three proposals sit there waiting for a human. A backlog does not stop existing
# because you narrowed the date picker.
#
# Each entity is filtered by ITS OWN timestamp (proposal → created_at, review → decided_at,
# run → created_at). Anything else is ambiguous: a proposal created in June and decided in
# July would otherwise drop in and out depending on which KPI you look at.
# =========================================================================== #

#: preset -> days back from today. "all" is handled separately.
RANGE_PRESETS = {"week": 7, "month": 30, "year": 365}

#: Above this many buckets a bar chart stops being readable (365 daily bars in one card
#: is 2px per bar). The range is then automatically coarsened and SAYS SO — better than
#: rendering an unreadable chart or silently truncating the range.
MAX_BUCKETS = 92

#: Order to coarsen through when a range produces too many buckets.
GRANULARITY_ORDER = ["day", "week", "month"]


def _bucket_key(dt: _dt.datetime, granularity: str) -> str:
    """The bucket a timestamp falls into. Weeks start Monday (ISO)."""
    if granularity == "month":
        return dt.strftime("%Y-%m")
    if granularity == "week":
        return (dt - _dt.timedelta(days=dt.weekday())).strftime("%Y-%m-%d")
    return dt.strftime("%Y-%m-%d")


def _bucket_starts(start: _dt.datetime, end: _dt.datetime, granularity: str) -> list[str]:
    """
    Every bucket in [start, end] — INCLUDING the empty ones.

    Empty buckets are the point: a day with no decisions must show as a gap, not be
    silently skipped. A chart that omits quiet days makes activity look continuous.
    """
    keys: list[str] = []
    if granularity == "month":
        cur = start.replace(day=1)
        while cur <= end:
            keys.append(cur.strftime("%Y-%m"))
            cur = (cur.replace(day=28) + _dt.timedelta(days=4)).replace(day=1)
        return keys
    step = _dt.timedelta(days=7 if granularity == "week" else 1)
    cur = start - _dt.timedelta(days=start.weekday()) if granularity == "week" else start
    cur = cur.replace(hour=0, minute=0, second=0, microsecond=0)
    while cur <= end:
        keys.append(cur.strftime("%Y-%m-%d"))
        cur += step
    return keys


def resolve_range(args, earliest_record: Optional[_dt.datetime] = None) -> dict:
    """
    Turn the query string into a concrete window.

    Accepts either a preset (`?preset=week|month|year|all`) or an explicit window
    (`?from=YYYY-MM-DD&to=YYYY-MM-DD`), plus `?granularity=day|week|month`.
    `to` is INCLUSIVE — a user picking 12.07. means "up to and including the 12th",
    so the window internally runs to 23:59:59 of that day.

    `earliest_record` is what makes `preset=all` mean something. Without it, "all" would
    start at the Unix epoch, the span would be 55 years, the auto-coarsening would kick in,
    and four days of real data would collapse into ONE monthly bar. "All" must mean "from
    the first thing that ever happened", which only the data can say.

    Falls back to the last 30 days. Invalid input never 500s: it falls back and says so
    via `invalid_input`, because a dashboard that dies on a malformed URL is worse than one
    that shows a default.
    """
    today = _dt.datetime.now(_dt.timezone.utc).replace(tzinfo=None)
    end_of_today = today.replace(hour=23, minute=59, second=59, microsecond=999999)
    midnight = {"hour": 0, "minute": 0, "second": 0, "microsecond": 0}
    invalid = []

    preset = (args.get("preset") or "").strip().lower()
    raw_from, raw_to = args.get("from"), args.get("to")

    if raw_from or raw_to:
        preset = "custom"
        try:
            start = (
                _dt.datetime.strptime(raw_from, "%Y-%m-%d") if raw_from
                else (today - _dt.timedelta(days=30)).replace(**midnight)
            )
            end = (
                _dt.datetime.strptime(raw_to, "%Y-%m-%d").replace(
                    hour=23, minute=59, second=59, microsecond=999999)
                if raw_to else end_of_today
            )
        except (ValueError, TypeError):
            invalid.append("from/to must be YYYY-MM-DD")
            preset = "month"
            start, end = (today - _dt.timedelta(days=30)).replace(**midnight), end_of_today
        if start > end:                      # swap rather than hand back an empty window
            start, end = (
                end.replace(**midnight),
                start.replace(hour=23, minute=59, second=59, microsecond=999999),
            )
            invalid.append("from was after to — swapped")
    elif preset == "all":
        start = (earliest_record or today).replace(**midnight)
        end = end_of_today
    elif preset in RANGE_PRESETS:
        start = (today - _dt.timedelta(days=RANGE_PRESETS[preset])).replace(**midnight)
        end = end_of_today
    else:
        if preset:
            invalid.append(f"unknown preset '{preset}'")
        preset = "month"
        start = (today - _dt.timedelta(days=30)).replace(**midnight)
        end = end_of_today

    granularity = (args.get("granularity") or "day").strip().lower()
    if granularity not in GRANULARITY_ORDER:
        invalid.append(f"unknown granularity '{granularity}'")
        granularity = "day"

    # Auto-coarsen rather than render 365 unreadable 2px bars.
    adjusted_from = None
    while len(_bucket_starts(start, end, granularity)) > MAX_BUCKETS:
        idx = GRANULARITY_ORDER.index(granularity)
        if idx == len(GRANULARITY_ORDER) - 1:
            break
        adjusted_from = adjusted_from or granularity
        granularity = GRANULARITY_ORDER[idx + 1]

    return {
        "from": start,
        "to": end,
        "granularity": granularity,
        "granularity_adjusted_from": adjusted_from,
        "preset": preset,
        "invalid_input": invalid,
    }


def earliest_timestamp(data: dict) -> Optional[_dt.datetime]:
    """The oldest thing in the DB — the only honest start for `preset=all`."""
    stamps = [
        _as_naive_utc(p["created_at"]) for p in data["proposals"]
    ] + [
        _as_naive_utc(r["decided_at"]) for r in data["reviews"]
    ] + [
        _as_naive_utc(r["created_at"]) for r in data["agent_runs"]
    ]
    known = [s for s in stamps if s is not None]
    return min(known) if known else None


def _in_range(value: Any, rng: dict) -> bool:
    """Is this timestamp inside the window? Rows without a timestamp are excluded."""
    dt = _as_naive_utc(value)
    return dt is not None and rng["from"] <= dt <= rng["to"]


def compute_metrics(data: dict, rng: dict) -> dict:
    """Turn the raw rows from `repository.fetch_metrics_data()` into the API payload."""
    all_proposals: list[dict] = data["proposals"]
    all_reviews: list[dict] = data["reviews"]
    all_runs: list[dict] = data["agent_runs"]

    # FLOW — filtered by each entity's own timestamp (see the block comment above).
    proposals = [p for p in all_proposals if _in_range(p["created_at"], rng)]
    reviews = [r for r in all_reviews if _in_range(r["decided_at"], rng)]
    runs = [r for r in all_runs if _in_range(r["created_at"], rng)]

    # STOCK — the current backlog. Deliberately NOT filtered.
    open_proposals = [p for p in all_proposals if p["status"] == "pending_review"]

    by_id = {p["proposal_id"]: p for p in all_proposals}   # reviews may point outside the window
    flags: list[dict] = []

    # Say plainly how much data the window hides, so a narrow filter can never be mistaken
    # for an empty system.
    hidden = (
        (len(all_proposals) - len(proposals))
        + (len(all_reviews) - len(reviews))
        + (len(all_runs) - len(runs))
    )
    if hidden:
        flags.append(
            {
                "code": "RANGE_EXCLUDES_DATA",
                "severity": "info",
                "affects": ["range"],
                "message": (
                    f"{hidden} Datensätze liegen außerhalb des gewählten Zeitraums und sind hier "
                    "nicht mitgezählt (Vorschläge, Entscheidungen und Agent-Läufe je nach eigenem "
                    "Zeitstempel). Die Kachel „Offene Reviews“ ist bewusst NICHT gefiltert — ein "
                    "offener Vorschlag hört nicht auf zu existieren, weil man den Zeitraum "
                    "verengt."
                ),
            }
        )
    if rng["invalid_input"]:
        flags.append(
            {
                "code": "RANGE_INPUT_IGNORED",
                "severity": "warning",
                "affects": ["range"],
                "message": (
                    "Teile des Zeitfilters waren ungültig und wurden ersetzt: "
                    + "; ".join(rng["invalid_input"]) + "."
                ),
            }
        )
    if rng["granularity_adjusted_from"]:
        flags.append(
            {
                "code": "GRANULARITY_COARSENED",
                "severity": "info",
                "affects": ["timeline"],
                "message": (
                    f"Der gewählte Zeitraum hätte bei „{rng['granularity_adjusted_from']}“ mehr als "
                    f"{MAX_BUCKETS} Balken ergeben — zu fein, um noch lesbar zu sein. Die "
                    f"Granularität wurde automatisch auf „{rng['granularity']}“ vergröbert."
                ),
            }
        )

    # ---------------------------------------------------------------- proposals
    # (`open_proposals` is the STOCK and was resolved above — do NOT re-derive it from the
    #  range-filtered list, that is exactly the bug this distinction exists to prevent.)
    scored = [p for p in proposals if p["confidence_score"] is not None]
    avg_confidence = (
        round(sum(p["confidence_score"] for p in scored) / len(scored), 4) if scored else None
    )

    # ---------------------------------------------------------------- decisions
    decisions = {"approve": 0, "reject": 0, "modify": 0}
    for rv in reviews:
        if rv["decision"] in decisions:
            decisions[rv["decision"]] += 1
    total_decisions = sum(decisions.values())

    # ---------------------------------------------------------------- calibration
    # Does a HIGH confidence score actually predict that the human took the value unchanged?
    # That is the one question that tells us whether the number is worth anything.
    calibration = []
    for i, (low, high) in enumerate(CONFIDENCE_BUCKETS):
        in_bucket = [
            rv
            for rv in reviews
            if (p := by_id.get(rv["proposal_id"])) is not None
            and p["confidence_score"] is not None
            and _bucket_index(p["confidence_score"]) == i
        ]
        accepted = sum(1 for rv in in_bucket if rv["decision"] == ACCEPTED_UNCHANGED)
        calibration.append(
            {
                "bucket": _bucket_label(low, high),
                "decisions": len(in_bucket),
                "accepted_unchanged": accepted,
                "accept_rate": _rate(accepted, len(in_bucket)),
            }
        )

    # AP7.2: `formula_version` is now the EXACT discriminator (v0/v1/v2); the old
    # `value_grounded IS NULL` heuristic only ever separated v0. Three generations exist:
    #   v0 — middle term `schema_valid` (always 1) -> score a near-constant ~0.775
    #   v1 — AP4.5: `value_grounded` real, but `memory_support` hard-wired to 0 -> capped at 0.8
    #   v2 — AP7.2: `memory_support` graded from the episodic case base -> full 0..1 range
    # Mixing them in ONE calibration curve compares scores that are not on the same scale.
    decided_by_version: dict[str, int] = {}
    for rv in reviews:
        p = by_id.get(rv["proposal_id"])
        if p is not None:
            v = p.get("formula_version") or "unknown"
            decided_by_version[v] = decided_by_version.get(v, 0) + 1

    legacy_confidence_decided = sum(
        n for v, n in decided_by_version.items() if v in ("v0", "unknown")
    )
    if legacy_confidence_decided:
        flags.append(
            {
                "code": "CONFIDENCE_LEGACY_FORMULA",
                "severity": "warning",
                "affects": ["calibration", "avg_confidence", "confidence_distribution"],
                "message": (
                    f"{legacy_confidence_decided} von {total_decisions} entschiedenen Vorschlägen "
                    "wurden mit der alten Konfidenz-Formel bewertet (vor AP4.5, Mittelterm "
                    "`schema_valid` = immer 1). Ihr Score ist praktisch konstant (~0.775) und "
                    "trägt keine Information — die Kalibrierungskurve ist deshalb flach, "
                    "und zwar konstruktionsbedingt, nicht als Messergebnis."
                ),
            }
        )

    if len([v for v in decided_by_version if v != "unknown"]) > 1 or (
        decided_by_version.get("unknown") and len(decided_by_version) > 1
    ):
        spread = ", ".join(f"{v}: {n}" for v, n in sorted(decided_by_version.items()))
        flags.append(
            {
                "code": "CONFIDENCE_MIXED_FORMULA_VERSIONS",
                "severity": "warning",
                "affects": ["calibration", "avg_confidence", "confidence_distribution"],
                "message": (
                    f"Die entschiedenen Vorschläge stammen aus MEHREREN Konfidenz-Generationen "
                    f"({spread}). Die Scores liegen damit nicht auf derselben Skala: v0 ist "
                    "quasi-konstant, v1 ist bei 0.8 gedeckelt (memory_support fest 0), erst v2 "
                    "nutzt den vollen Bereich 0..1. Eine gemeinsame Kalibrierungskurve über "
                    "diese Generationen vergleicht Ungleiches — vor der Auswertung nach "
                    "`formula_version` filtern (?formula_version=v2)."
                ),
            }
        )

    # ---------------------------------------------------------------- error types
    error_counts: dict[str, int] = {}
    for p in proposals:
        label = p["error_type"] or "UNKNOWN"
        error_counts[label] = error_counts.get(label, 0) + 1
    error_types = sorted(
        (
            {"error_type": k, "count": v, "legacy_label": k in LEGACY_ERROR_LABELS}
            for k, v in error_counts.items()
        ),
        key=lambda e: (-e["count"], e["error_type"]),
    )
    legacy_labelled = sum(e["count"] for e in error_types if e["legacy_label"])
    if legacy_labelled:
        flags.append(
            {
                "code": "ERROR_TYPE_LEGACY_HEURISTIC",
                "severity": "warning",
                "affects": ["error_types"],
                "message": (
                    f"{legacy_labelled} Vorschlag/Vorschläge tragen ein Label aus der alten "
                    "Zähl-Heuristik ({}). ".format(", ".join(sorted(LEGACY_ERROR_LABELS)))
                    + "Diese Labels sagen aus, wie oft ein Wert im Snapshot vorkam — nicht, was "
                    "falsch war (siehe AP3.6a). Seit AP3.6b kommt der Fehlertyp aus dem "
                    "`[validate_*]`-Tag und ist korrekt."
                ),
            }
        )

    # ---------------------------------------------------------------- timeline
    # "When were corrections actually made?" — one bucket per day/week/month, stacked by
    # decision type. Anchored on `decided_at`: the question is when the HUMAN acted, not
    # when the AI produced the proposal.
    buckets = _bucket_starts(rng["from"], rng["to"], rng["granularity"])
    empty = {"approve": 0, "reject": 0, "modify": 0}
    tally: dict[str, dict[str, int]] = {b: dict(empty) for b in buckets}
    for rv in reviews:
        dt = _as_naive_utc(rv["decided_at"])
        if dt is None:
            continue
        key = _bucket_key(dt, rng["granularity"])
        if key in tally and rv["decision"] in tally[key]:
            tally[key][rv["decision"]] += 1
    timeline = [
        {
            "bucket": b,
            "approve": tally[b]["approve"],
            "reject": tally[b]["reject"],
            "modify": tally[b]["modify"],
            "total": sum(tally[b].values()),
        }
        for b in buckets
    ]

    # ---------------------------------------------------------------- confidence distribution
    distribution = []
    for i, (low, high) in enumerate(CONFIDENCE_BUCKETS):
        distribution.append(
            {
                "bucket": _bucket_label(low, high),
                "count": sum(1 for p in scored if _bucket_index(p["confidence_score"]) == i),
            }
        )

    # ---------------------------------------------------------------- revalidation
    # Denominator = apply attempts only. A `reject` applies nothing by design, so counting
    # it as a failed re-validation would be a lie.
    attempts = [rv for rv in reviews if rv["revalidation_result"] is not None]
    trusted = [rv for rv in attempts if _revalidation_is_trustworthy(rv["revalidation_result"])]
    untrusted = len(attempts) - len(trusted)

    reval_success = 0
    for rv in trusted:
        res = rv["revalidation_result"]
        before, after = res.get("errors_before"), res.get("errors_after")
        # Success = the pipeline ran AND the snapshot really has fewer errors than before.
        if res.get("pipeline_success") and isinstance(after, int) and isinstance(before, int):
            if after < before:
                reval_success += 1

    if untrusted:
        flags.append(
            {
                "code": "REVALIDATION_PRE_AP33D",
                "severity": "warning",
                "affects": ["revalidation_success_rate"],
                "message": (
                    f"{untrusted} Re-Validierung(en) stammen aus der Zeit vor AP3.3d und sind "
                    "nicht belastbar: `validate_snapshot` las die Meldungsliste des Servers, "
                    "ohne den Validierungsjob vorher anzustoßen — das Ergebnis war immer "
                    "„0 Fehler“ (falsches Grün). Sie sind aus der Quote ausgenommen und hier "
                    "nur ausgewiesen."
                ),
            }
        )

    # ---------------------------------------------------------------- handling time
    # proposal.created_at -> review.decided_at. Fixtures decided in the same second are
    # separated out rather than averaged in; they would otherwise pull the mean to ~0.
    all_durations: list[float] = []
    human_durations: list[float] = []
    for rv in reviews:
        p = by_id.get(rv["proposal_id"])
        created = _as_naive_utc(p["created_at"]) if p else None
        decided = _as_naive_utc(rv["decided_at"])
        if not created or not decided:
            continue
        seconds = (decided - created).total_seconds()
        if seconds < 0:
            continue
        all_durations.append(seconds)
        if seconds >= MIN_HUMAN_DECISION_SECONDS:
            human_durations.append(seconds)

    fixture_count = len(all_durations) - len(human_durations)
    if fixture_count:
        flags.append(
            {
                "code": "HANDLING_TIME_FIXTURES",
                "severity": "info",
                "affects": ["handling_time"],
                "message": (
                    f"{fixture_count} Entscheidung(en) fielen in unter "
                    f"{MIN_HUMAN_DECISION_SECONDS} Sekunden nach Erzeugung des Vorschlags — das "
                    "sind Skript-Fixtures aus den Tests, kein Mensch, der einen Diff liest. Die "
                    "Bearbeitungszeit wird deshalb zusätzlich ohne sie ausgewiesen. Grenze der "
                    "Erkennung: ein per Skript entschiedenes Fixture, das Tage nach der "
                    "Erzeugung lief, ist so nicht von einer echten Entscheidung zu trennen."
                ),
            }
        )

    # ---------------------------------------------------------------- tokens / cost
    tokens_prompt = sum(r["tokens_prompt"] or 0 for r in runs)
    tokens_completion = sum(r["tokens_completion"] or 0 for r in runs)
    runs_with_tokens = sum(1 for r in runs if r["tokens_prompt"] is not None)
    validation_runs = sum(1 for r in runs if r["tool_name"] == "validate_snapshot")

    # AP6.3: cost is DERIVED from the stored tokens with the CURRENT price model, not summed
    # from each row's `cost_estimate`. Tokens are the raw fact; a cost is always an
    # interpretation of them. Summing the stored column would mix rows priced under different
    # assumptions, so the total would silently depend on WHEN a row was written.
    cost = sum(
        estimate_cost(r["tokens_prompt"], r["tokens_completion"]) or 0.0 for r in runs
    )
    pricing = describe_prices()

    flags.append(
        {
            "code": "COST_IS_ESTIMATE",
            "severity": "info",
            "affects": ["cost"],
            "message": (
                f"Die Kosten sind eine Schätzung, keine Abrechnung: Listenpreise für "
                f"{pricing['model']} (Input ${pricing['input_per_1k_usd']:.4f} / 1K, Output "
                f"${pricing['output_per_1k_usd']:.4f} / 1K), gerechnet aus den gespeicherten "
                "Tokens. Rabatte, Batch-Preise und Cached-Input sind nicht berücksichtigt. "
                "Aussagekräftig für den Vergleich („welcher Agent verbrennt das Budget?“), "
                "nicht für die Buchhaltung."
                + ("" if pricing["known_model"] else
                   f" ACHTUNG: für das Modell „{pricing['model']}“ liegt kein Preis vor — "
                   "es wird mit den gpt-4o-Preisen gerechnet.")
            ),
        }
    )

    if runs_with_tokens < len(runs):
        flags.append(
            {
                "code": "TOKENS_INCOMPLETE",
                "severity": "info",
                "affects": ["tokens", "cost"],
                "message": (
                    f"{len(runs) - runs_with_tokens} von {len(runs)} Agent-Läufen haben keine "
                    "Token-Zahlen (Läufe vor AP2.5, das Token-Tracking kam erst dort dazu). "
                    "Summe und Kosten sind entsprechend eine Untergrenze."
                ),
            }
        )

    # Server-side validation JOBS (AP3.3d) run through `trigger_server_validation`, which does
    # not write an agent_runs row. The count below therefore only sees the `validate_snapshot`
    # TOOL calls and undercounts the true number of validations.
    flags.append(
        {
            "code": "VALIDATION_COUNT_PARTIAL",
            "severity": "info",
            "affects": ["validations"],
            "message": (
                "Gezählt werden die `validate_snapshot`-Toolaufrufe. Die serverseitigen "
                "Validierungsjobs, die seit AP3.3d vor jedem Anwenden angestoßen werden, "
                "schreiben keine `agent_runs`-Zeile und fehlen in dieser Zahl."
            ),
        }
    )

    if total_decisions < SMALL_SAMPLE_THRESHOLD:
        flags.append(
            {
                "code": "SMALL_SAMPLE",
                "severity": "warning",
                "affects": ["approval_rate", "calibration", "revalidation_success_rate"],
                "message": (
                    f"Nur {total_decisions} Entscheidungen insgesamt. Jede einzelne verschiebt "
                    "jede Quote hier um zweistellige Prozentpunkte — das sind Einzelfälle, keine "
                    "Statistik. Belastbare Quoten liefert erst die Baseline-Messung (AK2)."
                ),
            }
        )

    # ---------------------------------------------------------------- payload
    return {
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "kpis": {
            "validations": validation_runs,
            "snapshots_tracked": data["snapshot_count"],
            "proposals_total": len(proposals),
            "proposals_open": len(open_proposals),
            "decisions_total": total_decisions,
            "approve_count": decisions["approve"],
            "reject_count": decisions["reject"],
            "modify_count": decisions["modify"],
            "approval_rate": _rate(decisions["approve"], total_decisions),
            "reject_rate": _rate(decisions["reject"], total_decisions),
            "modify_rate": _rate(decisions["modify"], total_decisions),
            # AK2: the share the acceptance criterion (>= 80%) is measured against.
            "accepted_unchanged_rate": _rate(decisions["approve"], total_decisions),
            "avg_confidence": avg_confidence,
            "revalidation_attempts": len(trusted),
            "revalidation_success": reval_success,
            "revalidation_success_rate": _rate(reval_success, len(trusted)),
            "revalidation_untrusted": untrusted,
            "handling_time_median_s": _median(human_durations),
            "handling_time_mean_s": (
                round(sum(human_durations) / len(human_durations), 1) if human_durations else None
            ),
            "handling_time_n": len(human_durations),
            "handling_time_excluded_fixtures": fixture_count,
            "tokens_prompt": tokens_prompt,
            "tokens_completion": tokens_completion,
            "tokens_total": tokens_prompt + tokens_completion,
            "cost_estimate_usd": round(cost, 4),
            "agent_runs": len(runs),
        },
        # The prices behind every cost above. A cost figure whose rates are not stated
        # cannot be checked by the reader, and an unchecked cost figure gets believed.
        "pricing": pricing,
        "charts": {
            "timeline": timeline,
            "error_types": error_types,
            "confidence_distribution": distribution,
            "calibration": calibration,
        },
        # The window every FLOW number above was computed in. `open_reviews` below is STOCK
        # and ignores it — stated here so the reader is never left guessing which is which.
        "range": {
            "from": rng["from"].strftime("%Y-%m-%d"),
            "to": rng["to"].strftime("%Y-%m-%d"),
            "granularity": rng["granularity"],
            "preset": rng["preset"],
            "granularity_adjusted_from": rng["granularity_adjusted_from"],
        },
        "open_reviews": sorted(
            (
                {
                    "proposal_id": p["proposal_id"],
                    "snapshot_id": p["snapshot_id"],
                    "error_type": p["error_type"],
                    "target_path": p["target_path"],
                    "confidence_score": p["confidence_score"],
                    "value_grounded": p["value_grounded"],
                    "created_at": p["created_at"].isoformat() if p["created_at"] else None,
                }
                for p in open_proposals
            ),
            key=lambda p: p["created_at"] or "",
            reverse=True,
        ),
        "data_quality": flags,
    }


@dashboard_bp.route("/metrics", methods=["GET"])
def get_metrics():
    """
    All dashboard KPIs in one call. Read-only.

    Query params (all optional):
        preset=week|month|year|all      — relative window; default `month` (last 30 days)
        from=YYYY-MM-DD&to=YYYY-MM-DD   — explicit window (`to` inclusive); overrides preset
        granularity=day|week|month      — timeline bucket size; auto-coarsened if too fine
        formula_version=v0|v1|v2        — AP7.2: restrict to ONE confidence generation

    The window scopes every FLOW metric. It deliberately does NOT scope `open_reviews` /
    `proposals_open` — see the FLOW vs STOCK block above.

    `formula_version` exists because the three generations are not on the same scale (v0 is
    quasi-constant, v1 is capped at 0.8, only v2 uses the full range). For a calibration
    curve that means something, pin ONE generation — `?formula_version=v2`.
    """
    try:
        data = repo.fetch_metrics_data()

        # AP7.2: pin one confidence generation. Reviews of filtered-out proposals go too,
        # otherwise a decision would be counted whose proposal no longer exists in the set.
        wanted = (request.args.get("formula_version") or "").strip().lower()
        if wanted:
            keep = {
                p["proposal_id"] for p in data["proposals"]
                if (p.get("formula_version") or "unknown") == wanted
            }
            data = {
                **data,
                "proposals": [p for p in data["proposals"] if p["proposal_id"] in keep],
                "reviews": [r for r in data["reviews"] if r["proposal_id"] in keep],
            }

        # The data is pulled BEFORE the range is resolved, because `preset=all` can only be
        # answered by the data itself (see resolve_range).
        rng = resolve_range(request.args, earliest_record=earliest_timestamp(data))
        payload = compute_metrics(data, rng)
        payload["formula_version_filter"] = wanted or None
        return jsonify(payload), 200
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Dashboard metrics failed")
        return jsonify({"error": "Metrics could not be computed", "detail": str(exc)}), 500
