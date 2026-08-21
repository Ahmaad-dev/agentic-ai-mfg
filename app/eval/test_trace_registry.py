"""
Selbstprüfung des Messinstruments: stimmen `graph/trace_keys.py` und der echte Trace überein?

WARUM DIESER TEST EXISTIERT
---------------------------
Vier Auswertungen in Folge scheiterten am falschen Trace-Schlüssel (BA-025, BA-033, BA-040,
BA-042) und meldeten daraufhin je einen Defekt, den es nicht gab. Die Registry in
`trace_keys.py` soll das beenden — aber eine Registry, die still veraltet, ist schlimmer als
keine: sie sieht aus wie eine Zusicherung.

Harte Regel 6 verlangt, das Instrument VOR der Messung zu prüfen. Genau das tut dieser Test.

DREI GELTUNGSGRADE (BA-044)
---------------------------
    PFLICHT     fehlt im Trace -> Abweichung
    BEDINGT     darf fehlen (nur ein Zweig schreibt ihn) -> keine Abweichung
    UNBEKANNT   steht nicht in der Registry -> harter Fehler

Der Test prüft **beide Richtungen**: dass ein echter Trace sauber durchgeht, UND dass die
Prüfung überhaupt anschlägt (Negativkontrolle mit einem erfundenen Schlüssel). Ein Prüfer,
der nie anschlägt, belegt nichts.

WICHTIG — ALTE TRACES SIND KEIN MASSSTAB
-----------------------------------------
Traces von vor BA-043 tragen bei Knoten 6 noch `iteration` statt `artifact_iteration_number`
und bei Knoten 8 weder `k7_hat_belegt` noch `revalidation_ok`; Traces von vor BA-047 führen
`response_sha256_eingang` nicht. Dass die Registry dort anschlägt, ist RICHTIG — sie
beschreibt den heutigen Code.

DREI ZUSTÄNDE, NICHT ZWEI (BA-048)
-----------------------------------
    PASS      der jüngste Trace stammt nachweislich aus der aktuellen Codefassung
              und deckt sich mit der Registry
    FAIL      **Produktregression** — ein aktueller Trace weicht von der Registry ab
    PENDING   der jüngste Trace ist ÄLTER als die letzte Registry-Änderung. Es gibt
              schlicht noch keinen Trace, gegen den sich prüfen liesse.

`PENDING` ist **kein Fehlschlag und kein Erfolg** — es ist eine Wartesituation und wird mit
Exit-Code 2 ausgewiesen (0 = PASS, 1 = FAIL). Der Unterschied ist nicht kosmetisch: ein FAIL
verlangt, den Code zu untersuchen; ein PENDING verlangt einen Lauf. Sie zu vermischen hiesse,
eine fehlende Beobachtung als Befund auszugeben — derselbe Fehler, den BA-044 im
K8-Entscheidungsvertrag beseitigt hat.

Aufruf:  .venv/Scripts/python.exe app/eval/test_trace_registry.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from graph_regression_harness import APP, Pruefung, pfade_setzen  # noqa: E402

pfade_setzen()
SNAP = APP.parent / "data" / "snapshots"


#: Zeitpunkt der letzten Registry-Änderung. Ein Trace, der älter ist, kann die Registry
#: nicht erfüllen — er entstand unter einer anderen Codefassung.
REGISTRY = (APP / "tools" / "smart-planning" / "graph" / "trace_keys.py")


def _juengster_trace():
    """Der zuletzt geschriebene `graph_state.json` im Snapshot-Verzeichnis."""
    kandidaten = sorted(SNAP.glob("*/iteration-*/graph_state.json"),
                        key=lambda f: f.stat().st_mtime, reverse=True)
    if not kandidaten:
        return None, None
    f = kandidaten[0]
    return f, json.loads(f.read_text(encoding="utf-8"))


def _trace_ist_aelter_als_registry(datei) -> bool:
    """Stammt der Trace aus der Zeit VOR der letzten Registry-Änderung?"""
    return datei.stat().st_mtime < REGISTRY.stat().st_mtime


def pruefen() -> Pruefung:
    from graph.trace_keys import (BEDINGT, BEDINGTE_EBENEN, DIGEST, TraceLeser,
                                  ist_pflicht, pruefe_registry)

    p = Pruefung("Trace-Registry gegen den echten Trace")

    # --- Registry-Selbstkonsistenz: nichts Bedingtes ohne Basiseintrag ---
    verwaist = [f"{k}.{e}.{s}" for k, eb in BEDINGT.items() for e, ks in eb.items()
                for s in ks if s not in DIGEST.get(k, {}).get(e, ())]
    p.gleich("BEDINGT verweist nur auf bekannte Schluessel", [], verwaist)
    verwaiste_ebenen = [f"{k}.{e}" for k, es in BEDINGTE_EBENEN.items() for e in es
                        if e not in DIGEST.get(k, {})]
    p.gleich("BEDINGTE_EBENEN verweist nur auf bekannte Ebenen", [], verwaiste_ebenen)
    p.gleich("`fehler` bei Knoten 6 ist BEDINGT, nicht PFLICHT",
             False, ist_pflicht("technical_check", "fehler"))
    p.gleich("`schema_valid` bei Knoten 6 ist PFLICHT",
             True, ist_pflicht("technical_check", "schema_valid"))

    # --- Der Leser wirft bei unbekannten Namen, liefert bei bekannten ---
    leer = TraceLeser({"trace": []})
    for knoten, schluessel in (("technical_check", "iteration_number"),   # BA-042-Falle
                               ("apply_revalidate", "proposal_sha256_after"),
                               ("evaluation", "erfundener_schluessel")):
        try:
            leer.hole(knoten, schluessel)
            p.wahr(f"hole({knoten!r}, {schluessel!r}) wirft", False, "kein Fehler geworfen")
        except KeyError:
            p.wahr(f"hole({knoten!r}, {schluessel!r}) wirft", True, "KeyError")

    # --- Negativkontrolle: schlaegt die Pruefung ueberhaupt an? ---
    kaputt = {"trace": [{"node": "evaluation", "timestamp_utc": "x", "duration_ms": 0,
                         "input_digest": {"erfunden": 1}, "output_digest": {}}]}
    abw = pruefe_registry(kaputt)
    p.wahr("Negativkontrolle: unbekannter Schluessel wird gemeldet",
           any("erfunden" in a for a in abw), abw[:3])
    p.wahr("Negativkontrolle: fehlende PFLICHT-Schluessel werden gemeldet",
           any("PFLICHT" in a for a in abw), [a for a in abw if "PFLICHT" in a][:3])

    # --- Der echte, juengste Trace ---
    datei, zustand = _juengster_trace()
    if zustand is None:
        p.wahr("ein graph_state.json ist vorhanden", False, str(SNAP))
        return p
    if _trace_ist_aelter_als_registry(datei):
        p.zeilen.append({"pruefung": "juengster Trace vs. Registry",
                         "erwartet": "Trace aus der aktuellen Codefassung",
                         "beobachtet": f"PENDING - juengster Trace "
                                       f"({datei.parent.parent.name[:8]}/{datei.parent.name}) "
                                       f"ist aelter als trace_keys.py",
                         "ok": True, "pending": True})
        return p
    abweichungen = pruefe_registry(zustand)
    p.gleich(f"juengster Trace sauber ({datei.parent.parent.name[:8]}/{datei.parent.name})",
             [], abweichungen)
    leser = TraceLeser(zustand)
    p.wahr("TraceLeser findet mindestens einen Durchgang", leser.durchgaenge() >= 1,
           leser.durchgaenge())
    return p


def main():
    sys.path.insert(0, str(APP))
    from core.run_metadata import require_ba_env
    meta = require_ba_env("Trace-Registry-Selbstpruefung (BA-044)")
    print(f"Umgebung: {meta['umgebung']['sys_prefix']}")
    p = pruefen()
    p.drucken()
    if not p.bestanden:
        return 1                                   # echte Produktregression
    if any(z.get("pending") for z in p.zeilen):
        print("\n  STATUS: PENDING - es fehlt ein Trace aus der aktuellen Codefassung. "
              "Das ist KEINE Produktregression; ein Lauf nach dem letzten Fix loest es auf.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
