"""
A/B/C-Vergleich der technischen Retries — **Ursache, nicht nur Anzahl** (BA-048).

WARUM DIE ANZAHL NICHT GENÜGT
------------------------------
BA-046 hat den Unterschied über Zählwerte gefunden (A 0 · B 0 · C 2) und wäre damit fast bei
der falschen Schlussfolgerung stehen geblieben. Erst die **Fehlermeldung** zeigte, dass die
Retries in C nicht vom Modell verursacht waren, sondern vom Graph-Handoff: es fehlten die
fünf Hüllenfelder.

Nach BA-047 ist die Erwartung deshalb **nicht** `retries == 0`. Ein Schema-Retry bleibt
legitim, wenn der tatsächliche K5-Modelloutput schema-invalide war — das ist Kategorie 2 und
gehört gemessen. Unzulässig ist nur noch die eine Ursache: **Retry wegen fehlender
Hüllenfelder allein aufgrund des Handoffs.**

WAS DIESES SKRIPT AUSWERTET
----------------------------
Je Arm und Durchgang:
  * die Anzahl der Retries (`technical_check.retries`)
  * die **beanstandeten Felder** der ersten Validierungsmeldung
  * die daraus abgeleitete **Ursachenklasse** über `kategorien.kategorie2_strukturell()`
  * für C zusätzlich die **SHA-Invariante** aus BA-047

Für A und B gibt es keinen `graph_state.json` — dort werden die Retries über die Artefakte
`llm_correction_proposal_retry_*.json` gezählt. Das ist der einzige Weg, der in allen drei
Armen dieselbe Frage beantwortet, und er wird als solcher ausgewiesen.

Aufruf:  .venv/Scripts/python.exe app/eval/report_retry_ursachen.py [--fall P04]
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from graph_regression_harness import APP, pfade_setzen  # noqa: E402
from kategorien import kategorie2_strukturell, _fehlerorte  # noqa: E402

pfade_setzen()
SNAP = APP.parent / "data" / "snapshots"
ARCHIV = APP.parent / "data" / "archive" / "ba-g3-pilot"


def _neueste_laeufe(fall: str) -> dict:
    """Je Bedingung der jüngste archivierte Lauf, der diesen Fall enthält."""
    raus = {}
    for datei in sorted(ARCHIV.glob("pilot-firstpass-*.json"), key=lambda f: f.stat().st_mtime):
        d = json.loads(datei.read_text(encoding="utf-8"))
        for e in d.get("ergebnisse") or []:
            if e.get("code") == fall and not e.get("fehlgeschlagen"):
                raus[d["bedingung"]] = {"snapshot_id": e["snapshot_id"], "quelle": datei.name,
                                        "schalter": e.get("schalter_effektiv")}
    return raus


def _retry_artefakte(sid: str) -> dict:
    """Retries je Iterationsordner, aus den Dateien — funktioniert in ALLEN drei Armen."""
    d = SNAP / sid
    raus = {}
    for ordner in sorted(d.glob("iteration-*"), key=lambda f: int(f.name.split("-")[1])):
        dateien = sorted(p.name for p in ordner.glob("llm_correction_proposal_retry_*.json"))
        raus[ordner.name] = dateien
    return raus


def _graph_befunde(sid: str) -> list:
    """Je Durchgang: Retries, beanstandete Felder, Ursachenklasse, SHA-Invariante."""
    d = SNAP / sid
    kandidaten = sorted(d.glob("iteration-*/graph_state.json"),
                        key=lambda f: int(f.parent.name.split("-")[1]))
    if not kandidaten:
        return []
    z = json.loads(kandidaten[-1].read_text(encoding="utf-8"))
    tc = [t for t in z["trace"] if t["node"] == "technical_check"]
    k5 = [t for t in z["trace"] if t["node"] == "correction"]
    fehler = (z.get("technical_check") or {}).get("errors") or []

    raus = []
    for i, t in enumerate(tc):
        eingang = (t.get("input_digest") or {}).get("response_sha256_eingang")
        erzeugt = ((k5[i].get("provenienz") or {}).get("response_sha256")
                   if i < len(k5) else None)
        retries = (t.get("output_digest") or {}).get("retries")
        # Die Meldung liegt nur fuer den LETZTEN Durchgang im State; fuer frueherere ist sie
        # nicht ueberliefert. Ehrlich ausweisen statt raten.
        meldung = fehler if i == len(tc) - 1 else None
        befund = (kategorie2_strukturell((t.get("output_digest") or {}).get("schema_valid"),
                                         retries, meldung)
                  if meldung is not None else None)
        raus.append({
            "durchgang": i + 1,
            "retries": retries,
            "beanstandet": sorted(set(_fehlerorte("\n".join(str(f) for f in (meldung or []))))),
            "ursache": (befund or {}).get("befund"),
            "begruendung": (befund or {}).get("begruendung"),
            "sha_k5_erzeugt": erzeugt,
            "sha_k6_eingang": eingang,
            "invariante_haelt": (erzeugt is not None and erzeugt == eingang),
        })
    return raus


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--fall", default="P04")
    args = ap.parse_args(argv)

    laeufe = _neueste_laeufe(args.fall)
    if not laeufe:
        print(f"Keine archivierten Laeufe fuer {args.fall} gefunden.")
        return 1

    print(f"=== Retry-Ursachen je Arm — Fall {args.fall} ===\n")
    zusammen = {}
    for arm in ("A", "B", "C"):
        if arm not in laeufe:
            print(f"  {arm}: kein Lauf vorhanden\n")
            continue
        sid = laeufe[arm]["snapshot_id"]
        art = _retry_artefakte(sid)
        gesamt = sum(len(v) for v in art.values())
        zusammen[arm] = gesamt
        print(f"  {arm}  snapshot={sid[:8]}  ({laeufe[arm]['quelle']})")
        print(f"      Schalter: {laeufe[arm]['schalter']}")
        print(f"      Retry-Artefakte gesamt: {gesamt}")
        for ordner, dateien in art.items():
            if dateien:
                print(f"        {ordner}: {dateien}")
        if arm == "C":
            for b in _graph_befunde(sid):
                print(f"      D{b['durchgang']}: retries={b['retries']} "
                      f"beanstandet={b['beanstandet'] or '-'}")
                print(f"           SHA K5={str(b['sha_k5_erzeugt'])[:16]} "
                      f"K6={str(b['sha_k6_eingang'])[:16]} "
                      f"INVARIANTE={'HAELT' if b['invariante_haelt'] else 'VERLETZT/fehlt'}")
                if b["ursache"]:
                    print(f"           Ursachenklasse: {b['ursache']} - {b['begruendung'][:110]}")
        print()

    print("=== Bewertung ===")
    if zusammen.get("C") is None:
        print("  C fehlt - keine Aussage moeglich.")
        return 1
    print(f"  Retries: A={zusammen.get('A')} B={zusammen.get('B')} C={zusammen.get('C')}")
    print("  ENTSCHEIDEND ist nicht die Zahl, sondern ob in C ein Retry auf FEHLENDE")
    print("  HUELLENFELDER zurueckgeht. Ein Retry auf innere Felder ist legitim (Kategorie 2).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
