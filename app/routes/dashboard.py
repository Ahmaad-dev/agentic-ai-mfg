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

  1. REVALIDATION_UNVERIFIED — before AP3.3d, `validate_snapshot` read the server's message
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

from core.cost_model import describe_prices, estimate_cost
from db import repository as repo

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")

#: Vocabulary of the pre-AP3.6b hit-count heuristic. These are not error classes:
#: they say how often the searched value occurred (see AP3.6a in PROJECT_LOG.md).

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



def _latest_formula_version(proposals: list[dict]) -> Optional[str]:
    """Die hoechste vorkommende Konfidenz-Generation (`v0`, `v3`, `v12`, ...).

    Sortiert NUMERISCH nach der Ziffernfolge, nicht alphabetisch — `"v10" < "v9"` waere als
    Zeichenkette wahr und wuerde die neueste Generation ausgerechnet dann verwerfen, wenn es
    zweistellig wird. Werte ohne dieses Muster (`None`, `"unknown"`) zaehlen nicht mit; gibt
    es gar keine, ist das Ergebnis `None` und die Kurve bleibt leer, statt stillschweigend
    auf alle Generationen zurueckzufallen.
    """
    best: Optional[tuple[int, str]] = None
    for p in proposals:
        raw = (p.get("formula_version") or "").strip().lower()
        if len(raw) > 1 and raw[0] == "v" and raw[1:].isdigit():
            cand = (int(raw[1:]), raw)
            if best is None or cand[0] > best[0]:
                best = cand
    return best[1] if best else None

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
    #
    # NUR die aktuelle Generation (13.08.2026). Die Formel wurde mehrfach geaendert, und
    # ihre Werte liegen zwischen den Generationen NICHT auf derselben Skala — eine frueher
    # quasi-konstante Formel liefert Scores um 0.775 unabhaengig vom Fall. Eine Kurve ueber
    # alle Generationen hinweg mittelt daher Ungleiches und sieht flach aus, ohne dass das
    # etwas ueber die Vorhersagekraft aussagt. Genau dieser Trugschluss war es, den bisher
    # ein Warntext erklaeren musste; jetzt entsteht er gar nicht erst.
    #
    # Welche Generation die aktuelle ist, wird NICHT als Textkonstante hinterlegt: der
    # Generator erhoeht `CONFIDENCE_FORMULA_VERSION` bei jeder Aenderung der Formel, und
    # eine Kopie davon wuerde hier stillschweigend veralten. Massgeblich ist die hoechste
    # Generation, die IM BESTAND vorkommt — das ist bauartbedingt die, die das System
    # heute schreibt. Bezugsmenge sind alle Vorschlaege, nicht die des Zeitfensters:
    # sonst waere „aktuell" beim Blaettern in die Vergangenheit etwas anderes.
    current_formula = _latest_formula_version(all_proposals)
    cal_reviews = [
        rv
        for rv in reviews
        if (q := by_id.get(rv["proposal_id"])) is not None
        and (q.get("formula_version") or None) == current_formula
    ]

    calibration = []
    for i, (low, high) in enumerate(CONFIDENCE_BUCKETS):
        in_bucket = [
            rv
            for rv in cal_reviews
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

    # ENTFERNT am 13.08.2026: die Vorbehalte CONFIDENCE_LEGACY_FORMULA und
    # CONFIDENCE_MIXED_FORMULA_VERSIONS. Beide erklärten dem Betrachter die
    # Entwicklungsgeschichte der eigenen Konfidenz-Formel (v0/v1/v2). Im laufenden Betrieb
    # ist das keine Aussage über die Daten, sondern über das Projekt — und damit an dieser
    # Stelle nur Lärm.
    # Die SACHE dahinter ist seither erledigt, nicht nur der Text: die Kalibrierungskurve
    # rechnet nur noch auf der aktuellen Generation (siehe `current_formula` weiter oben).
    # Kennzahl „Mittlere Konfidenz" und die Konfidenz-Verteilung laufen bewusst WEITER
    # ueber alle Generationen: sie beschreiben, was tatsaechlich erzeugt wurde, und stellen
    # anders als die Kurve keine Behauptung ueber Vorhersagekraft auf.

    # ---------------------------------------------------------------- error types
    error_counts: dict[str, int] = {}
    for p in proposals:
        label = p["error_type"] or "UNKNOWN"
        error_counts[label] = error_counts.get(label, 0) + 1
    error_types = sorted(
        (
            {"error_type": k, "count": v}
            for k, v in error_counts.items()
        ),
        key=lambda e: (-e["count"], e["error_type"]),
    )
    # ENTFERNT am 13.08.2026: der Vorbehalt ERROR_TYPE_LEGACY_HEURISTIC samt der
    # Sondereinfärbung im Diagramm. Er erklärte, dass einzelne Altdatensätze ein Label aus
    # einer abgelösten Zähl-Heuristik tragen — Entwicklungsgeschichte, kein Betriebshinweis.

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
                "code": "REVALIDATION_UNVERIFIED",
                "severity": "warning",
                "affects": ["revalidation_success_rate"],
                "message": (
                    f"{untrusted} Re-Validierung(en) stammen aus der Zeit vor der Umstellung der "
                    "Prüfreihenfolge und sind nicht belastbar: die Prüfung las die "
                    "Meldungsliste des Servers, ohne den Validierungsjob vorher anzustoßen — "
                    "das Ergebnis war immer „0 Fehler“ (falsches Grün). Diese Fälle sind aus "
                    "der Quote ausgenommen und hier nur nachrichtlich ausgewiesen."
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
                    f"{MIN_HUMAN_DECISION_SECONDS} Sekunden nach Erzeugung des Vorschlags. In dieser "
                    "Zeit lässt sich kein Wertevergleich prüfen — es handelt sich um "
                    "automatisiert erzeugte Testdaten. Die Bearbeitungszeit wird deshalb "
                    "zusätzlich ohne sie ausgewiesen. Grenze der Erkennung: ein automatisiert "
                    "entschiedener Fall, der erst Tage nach der Erzeugung lief, ist so nicht "
                    "von einer echten Entscheidung zu unterscheiden."
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
                "Aussagekräftig für den Vergleich zwischen Agenten, nicht für die Buchhaltung. "
                "Zu beachten: die Preise werden RÜCKWIRKEND auf alle Läufe angewandt, "
                "auch auf solche, die tatsächlich auf einem anderen Modell liefen. Nach "
                "einem Modellwechsel ändert sich diese Zahl deshalb auch für längst "
                "abgeschlossene Läufe."
                + ("" if pricing["known_model"] else
                   f" ACHTUNG: für das Modell „{pricing['model']}“ liegt kein Preis vor — "
                   "es wird mit den Preisen des aktiven Modells gerechnet.")
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
                    "Token-Zahlen — sie stammen aus der Zeit vor der Einführung der Token-Erfassung. "
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
                "Gezählt werden die Validierungs-Toolaufrufe des Agenten. Die serverseitigen "
                "Validierungsjobs, die vor jedem Anwenden angestoßen werden, schreiben "
                "keinen eigenen Lauf-Eintrag und fehlen in dieser Zahl."
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
                    "Statistik. Belastbare Quoten ergeben sich erst mit einer deutlich größeren "
                    "Zahl an Entscheidungen."
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
            # Woraus die Kurve gerechnet wurde. Die Oberflaeche braucht das, um bei einer
            # leeren Kurve zwischen „noch nichts entschieden" und „nichts auf der
            # aktuellen Formel entschieden" unterscheiden zu koennen.
            "calibration_scope": {
                "formula_version": current_formula,
                "decisions": len(cal_reviews),
                "decisions_excluded": total_decisions - len(cal_reviews),
            },
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
        formula_version=vN              — restrict EVERYTHING to one confidence generation

    The window scopes every FLOW metric. It deliberately does NOT scope `open_reviews` /
    `proposals_open` — see the FLOW vs STOCK block above.

    `formula_version` exists because the generations are not on the same scale — an early
    formula was quasi-constant, a later one capped. It pins EVERY metric to one generation.
    Note that the calibration curve no longer needs it: since 13.08.2026 it restricts
    itself to the current generation. The parameter remains for the other way round —
    inspecting an OLDER generation on purpose.
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
