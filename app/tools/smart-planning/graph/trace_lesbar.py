"""
AP-F2 — Die lesbare Trace-Kette.

Zwei Zwecke in einem Werkzeug (BA_MASTERPLAN Kap. 12.5):
  1. **Debugging** waehrend der Entwicklung - wo ist die Kette gerissen?
  2. **Abbildung fuer Kapitel 7** - der Beleg fuer UF3 (Nachvollziehbarkeit).

**Es wird nichts berechnet und nichts bewertet.** Dieses Modul liest ausschliesslich, was die
Knoten in den Zustand geschrieben haben, und ordnet es lesbar an. Jede Zahl hier stammt aus
`graph_state.json`; keine wird hier abgeleitet.

WAS DIE KETTE ZEIGT - UND WAS SIE NICHT ZEIGT
----------------------------------------------
Sie zeigt **welche Fragen sich aus dem Protokoll beantworten lassen**, nicht wie viele
Schritte es gab. Die blosse Schrittzahl (7 im Monolithen gegen 9 Knoten) ist **keine**
Nachvollziehbarkeitsmetrik - die beiden Zahlen zaehlen Verschiedenes, und der Graph macht
denselben Ablauf nur feiner sichtbar (Kap. 3.6).

Der Monolith hat sehr wohl Artefakte auf Platte - je Iteration `llm_identify_response.json`,
`last_search_results.json`, `llm_correction_proposal.json`, `upload-result.json` und mehr.
Der Unterschied ist, dass sie **verteilt, untypisiert und zeitlich ungeordnet** sind und
**keine Regelprovenienz** enthalten: welche Karten geladen waren, steht dort nirgends.

Aufruf:
    python graph/trace_lesbar.py <snapshot-id> [--iteration N] [--md]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(_HIER.parent / "runtime"))

#: Die sieben Fragen, an denen sich Nachvollziehbarkeit entscheidet. Sie sind der eigentliche
#: Gegenstand von UF3 - jede ist entweder aus dem Protokoll beantwortbar oder nicht.
FRAGEN = (
    ("Welcher Fehler wurde ausgewaehlt, und warum dieser?", "classification"),
    ("Welcher Kontext lag dem Modell vor?", "context_search"),
    ("Welche Regeln waren geladen?", "rule_matching"),
    ("Sah das Modell genau diese Regeln und diesen Kontext?", "correction"),
    ("War der Vorschlag schemagueltig, nach wie vielen Versuchen?", "technical_check"),
    ("Was hat die Anwendung bewirkt?", "apply_revalidate"),
    ("Warum wurde abgebrochen bzw. weitergemacht?", "evaluation"),
)


def _kurz(wert, n: int = 46) -> str:
    if wert is None:
        return "—"
    s = str(wert)
    return s if len(s) <= n else s[: n - 1] + "…"


def kette(zustand: dict) -> list[str]:
    """Baut die lesbare Kette aus einem abgelegten `graph_state.json`."""
    z: list[str] = []
    trace = zustand.get("trace") or []
    iv = zustand.get("initial_validation") or {}

    z.append("=" * 78)
    z.append(f"KORREKTURLAUF  {zustand.get('snapshot_id')}")
    z.append(f"  Architektur {zustand.get('architecture_mode')} · "
             f"Iteration {zustand.get('iteration')}/{zustand.get('max_iterations')} · "
             f"start {zustand.get('started_at')}")
    z.append(f"  Fehler vorher {zustand.get('errors_before')} → nachher {zustand.get('errors_after')}"
             f"   ({'None = keine belastbare Re-Validierung' if zustand.get('errors_after') is None else 'aus abgeschlossener Re-Validierung'})")
    z.append("=" * 78)

    gesamt_ms = 0
    for i, t in enumerate(trace, 1):
        name = t.get("node")
        ms = t.get("duration_ms") or 0
        gesamt_ms += ms
        z.append("")
        z.append(f"[{i}] {name}   {ms} ms   {t.get('timestamp_utc')}")
        ein, aus = t.get("input_digest") or {}, t.get("output_digest") or {}

        if name == "input_analysis":
            z.append(f"      Quelle    {aus.get('quelle')}")
            z.append(f"      gefunden  {aus.get('errors')} ERROR / {aus.get('warnings')} WARNING")
            z.append(f"      Tags      {aus.get('error_tags')}")
        elif name == "classification":
            z.append(f"      gewaehlt  {aus.get('tag')}  (Prioritaet {aus.get('priority_index')})")
            z.append(f"      Suche     mode={aus.get('search_mode')} value={_kurz(aus.get('search_value'))}")
            z.append(f"      Karten vorgeschlagen  {aus.get('relevant_cards_vorgeschlagen')}")
            z.append(f"      Antwort   sha256={_kurz(aus.get('identify_response_sha256'), 20)}")
        elif name == "context_search":
            # `error_type` ist die ALTE Trefferzahl-Heuristik aus `identify_snapshot.py`, nicht
            # der massgebliche Validator-Tag. Sie kann z. B. einen Dichtefehler als
            # "DUPLICATE_ID" ausweisen (bekannt und dokumentiert in
            # generate_correction_llm.py:1099). Hier ausdruecklich markiert, damit die Kette
            # nicht wie ein Widerspruch zur Klassifikation aus Knoten 2 aussieht.
            z.append(f"      Treffer   {aus.get('results_count')}   "
                     f"Typ {aus.get('error_type')} (Heuristik, nicht der Validator-Tag)")
            z.append(f"      Pfade     {_kurz(aus.get('lines_used'), 60)}")
            z.append(f"      Kontext   sha256={_kurz(aus.get('results_hash'), 20)}")
        elif name == "rule_matching":
            z.append(f"      Modus     {aus.get('rulebook_mode')}")
            z.append(f"      Karten    {aus.get('cards_loaded')}")
            z.append(f"      Regeltext {aus.get('chars')} Zeichen  sha256={_kurz(aus.get('rule_text_hash'), 20)}")
        elif name == "correction":
            z.append(f"      Vorschlag {aus.get('action')} → {_kurz(aus.get('target_path'))}")
            z.append(f"      Wert      {_kurz(aus.get('new_value'))}   Quelle {aus.get('value_source')}")
            z.append("      HANDOFFS (was das Modell WIRKLICH gesehen hat):")
            z.append(f"        Regeln  sha256={_kurz(ein.get('regeln_sha256'), 20)}  "
                     f"{'== Knoten 4' if ein.get('regeln_sha256') else 'keine'}")
            z.append(f"        Kontext sha256={_kurz(ein.get('context_input_sha256'), 20)}  "
                     f"ok={ein.get('context_handoff_ok')}")
            z.append(f"        Ident.  sha256={_kurz(ein.get('identify_input_sha256'), 20)}  "
                     f"ok={ein.get('identify_handoff_ok')}")
        elif name == "technical_check":
            z.append(f"      Schema    gueltig={aus.get('schema_valid')} nach {aus.get('retries')} Retry(s)")
            z.append(f"      Fehler    {aus.get('fehleranzahl')}")
        elif name == "apply_revalidate":
            z.append(f"      angewendet={aus.get('applied_ok')}  hochgeladen={aus.get('uploaded')}")
            z.append(f"      Re-Validierung ok={aus.get('revalidation_ok')} "
                     f"job={_kurz(aus.get('revalidation_job'), 12)} "
                     f"gewartet={aus.get('revalidation_waited_s')}s")
            z.append(f"      Fehler    vorher={aus.get('errors_before')} nachher={aus.get('errors_after')} "
                     f"(behoben {aus.get('errors_resolved')}, neu {aus.get('errors_new')})")
            if aus.get("new_error_types"):
                z.append(f"      NEUE Fehlerarten  {aus.get('new_error_types')}")
        elif name == "evaluation":
            z.append(f"      Entscheidung  {aus.get('action')}")
            z.append(f"      Begruendung   {_kurz(aus.get('reasoning'), 62)}")
        if aus.get("fehler"):
            z.append(f"      ⚠ FEHLER  {_kurz(aus.get('fehler'), 62)}")

    z.append("")
    z.append("=" * 78)
    z.append(f"Summe {gesamt_ms} ms über {len(trace)} Knoten")
    # Knoten 9 gesondert ausweisen. Bis 20.08.2026 war er ein LLM-Aufruf ohne Entsprechung
    # in der Monolith-Pipeline (45 % der Laufzeit im Durchstich I03); seit BA-031 erzeugt er
    # das Endergebnis deterministisch. Die Zeile bleibt als Kontrolle stehen: steigt sie
    # wieder ueber wenige Millisekunden, ist versehentlich ein Modellaufruf zurueckgekehrt.
    t9 = next((x for x in trace if x.get("node") == "answer"), None)
    if t9:
        ms9 = t9.get("duration_ms") or 0
        anteil = (100 * ms9 / gesamt_ms) if gesamt_ms else 0
        llm = (t9.get("output_digest") or {}).get("llm_aufruf")
        z.append(f"  davon Knoten 9 (Ausgabe/Finalisierung): {ms9} ms = {anteil:.0f} %  "
                 f"llm_aufruf={llm}"
                 + ("   ⚠ ERWARTET WIRD 0 ms UND False" if (llm is not False or ms9 > 50) else ""))
    z.append("")
    z.append("BEANTWORTBARE FRAGEN (das ist der UF3-Gegenstand, nicht die Schrittzahl)")
    for frage, knoten in FRAGEN:
        t = next((x for x in trace if x.get("node") == knoten), None)
        aus = (t or {}).get("output_digest") or {}
        ein = (t or {}).get("input_digest") or {}
        belegt = bool(t) and any(v not in (None, [], "", {}) for k, v in {**ein, **aus}.items()
                                 if k != "fehler")
        z.append(f"  [{'x' if belegt else ' '}] {frage}")
    z.append("=" * 78)
    return z


def aus_datei(snapshot_id: str, iteration: int | None = None) -> dict:
    from runtime_storage import get_storage, get_latest_iteration_number
    st = get_storage()
    n = iteration or get_latest_iteration_number(snapshot_id, require_file="graph_state.json")
    if n is None:
        raise FileNotFoundError(f"kein graph_state.json fuer {snapshot_id}")
    d = st.load_json(f"{snapshot_id}/iteration-{n}/graph_state.json")
    if d is None:
        raise FileNotFoundError(f"graph_state.json in iteration-{n} nicht lesbar")
    return d


def main(argv=None):
    a = list(sys.argv if argv is None else argv)
    if len(a) < 2:
        print(__doc__)
        return 1
    sid = a[1]
    it = int(a[a.index("--iteration") + 1]) if "--iteration" in a else None
    zeilen = kette(aus_datei(sid, it))
    if "--md" in a:
        print("```")
        print("\n".join(zeilen))
        print("```")
    else:
        print("\n".join(zeilen))
    return 0


if __name__ == "__main__":
    sys.exit(main())
