"""
AP-G1 — Pilotkatalog erzeugen.

WOZU
-----
Die Pilotphase (Masterplan Kap. 8.3) ist der einzige Abschnitt, in dem noch optimiert werden
darf. Regel 5 knuepft das an eine Bedingung: **Pilotfaelle duerfen sich nicht mit Messfaellen
ueberschneiden - auch nicht in den Entitaeten.** Zwei verschiedene Snapshot-IDs genuegen nicht:
wer denselben `articleId` korrigiert, optimiert auf die Testmenge hin, und beim Gedaechtnis
laege die Loesung spaeter objektgenau vor (deshalb zusaetzlich `MEMORY_MODE=off`).

TABU-ENTITAETEN (aus dem Messkatalog erhoben, nicht angenommen)
---------------------------------------------------------------
`isolated-error-snapshots/expected-results.json` (I01-I10) und
`kombinierte-fehler-snapshots/ERROR-SNAPSHOTS.md` (10 Snapshots) drehen sich fast vollstaendig
um **articleId 100005**, dazu 100079, `D100005_001/002`, `departmentId 20100`,
`packaging 70381/71125`, `workPlanId SP10`.

Die Pilotfaelle benutzen deshalb **andere Artikel** und deren eigene Demands. Die Referenz hat
422 Artikel und 1.395 Demands - Auswahl ist reichlich vorhanden.

METHODE
--------
Dieselbe **Fehlerinjektion als Ground-Truth-Methode** wie im Messkatalog (Bruecke 1 aus
CLAUDE.md): eine vollstaendige Kopie von `ok-snapshot.json` mit gezielten Manipulationen,
und je Fall der Originalwert als Ground Truth. Nicht dasselbe Skript - der Messkatalog wurde
mit PowerShell erzeugt -, aber dieselbe Methode, und das Ergebnisformat ist bewusst gleich
(`expected-results.json`), damit der bestehende Harness es ohne Aenderung lesen kann.

Aufruf:  python eval/build_pilot_catalog.py [--force]
"""
import argparse
import copy
import json
import re
import sys
from pathlib import Path

APP = Path(__file__).resolve().parent.parent
SNAP = APP.parent / "data" / "snapshots"
OK = SNAP / "ok-snapshot.json"
ZIEL = SNAP / "ba-pilot-snapshots"

#: Die Artikel, um die der MESSKATALOG kreist. Fuer Pilotfaelle gesperrt.
TABU_ARTIKEL = {"100005", "100079"}


def _art_index(daten, article_id):
    for i, a in enumerate(daten.get("articles", [])):
        if str(a.get("articleId")) == str(article_id):
            return i
    raise KeyError(f"Artikel {article_id} nicht in der Referenz")


def _dem_indizes(daten, article_id):
    return [i for i, d in enumerate(daten.get("demands", []))
            if str(d.get("articleId")) == str(article_id)]


# ---------------------------------------------------------------- Manipulationen
# Jede gibt (aenderungen, hinweis) zurueck. `aenderungen` ist die Ground Truth:
# jsonPath, before (Originalwert), after (manipulierter Wert).

def m_doppelte_demand_id(daten, art):
    di = _dem_indizes(daten, art)
    ziel, quelle = di[1], di[0]
    vorher = daten["demands"][ziel]["demandId"]
    neu = daten["demands"][quelle]["demandId"]
    daten["demands"][ziel]["demandId"] = neu
    return [{"jsonPath": f"demands[{ziel}].demandId", "before": vorher, "after": neu}]


def m_unbekannter_artikel(daten, art):
    di = _dem_indizes(daten, art)[0]
    vorher = daten["demands"][di]["articleId"]
    neu = f"{vorher}_GIBTESNICHT"
    daten["demands"][di]["articleId"] = neu
    return [{"jsonPath": f"demands[{di}].articleId", "before": vorher, "after": neu}]


def m_dichte_null(daten, art):
    ai = _art_index(daten, art)
    vorher = daten["articles"][ai]["relDensityMin"]
    daten["articles"][ai]["relDensityMin"] = 0
    return [{"jsonPath": f"articles[{ai}].relDensityMin", "before": vorher, "after": 0}]


def m_unbekannter_arbeitsplan(daten, art):
    ai = _art_index(daten, art)
    vorher = daten["articles"][ai]["workPlanId"]
    neu = "PLAN_GIBTESNICHT"
    daten["articles"][ai]["workPlanId"] = neu
    return [{"jsonPath": f"articles[{ai}].workPlanId", "before": vorher, "after": neu}]


def m_department_leer(daten, art):
    ai = _art_index(daten, art)
    vorher = daten["articles"][ai].get("departmentId")
    daten["articles"][ai]["departmentId"] = ""
    return [{"jsonPath": f"articles[{ai}].departmentId", "before": vorher, "after": ""}]


def m_demand_id_leer(daten, art):
    di = _dem_indizes(daten, art)[0]
    vorher = daten["demands"][di]["demandId"]
    daten["demands"][di]["demandId"] = ""
    return [{"jsonPath": f"demands[{di}].demandId", "before": vorher, "after": ""}]


def m_demand_id_vertippt(daten, art):
    """Fuzzy-Pfad: die ID existiert fast - ein Zeichen daneben."""
    di = _dem_indizes(daten, art)[0]
    vorher = daten["demands"][di]["demandId"]
    neu = str(vorher)[:-1] + "9" if str(vorher)[-1] != "9" else str(vorher)[:-1] + "8"
    daten["demands"][di]["demandId"] = neu
    return [{"jsonPath": f"demands[{di}].demandId", "before": vorher, "after": neu}]


def m_dichte_umgekehrt(daten, art):
    """Grenzfall: min > max. Beide Werte sind da, welcher ist der falsche?"""
    ai = _art_index(daten, art)
    vmin = daten["articles"][ai].get("relDensityMin")
    vmax = daten["articles"][ai].get("relDensityMax")
    daten["articles"][ai]["relDensityMin"] = vmax
    daten["articles"][ai]["relDensityMax"] = vmin
    return [{"jsonPath": f"articles[{ai}].relDensityMin", "before": vmin, "after": vmax},
            {"jsonPath": f"articles[{ai}].relDensityMax", "before": vmax, "after": vmin}]


def m_ununterscheidbares_duplikat(daten, art):
    """
    ECHTE Mehrdeutigkeit (P11, Ersatz fuer P09).

    Zwei Demands desselben Artikels, die sich AUSSER in der `demandId` in KEINEM Feld
    unterscheiden - geprueft an den Daten, nicht angenommen. Wird die eine ID auf die andere
    gesetzt, entsteht ein `validate_unique_ids`-Fehler, bei dem objektiv nicht entscheidbar
    ist, welche der beiden die falsche ist: beide Datensaetze sind identisch.

    **Ein ehrliches `stop_uncertain` ist hier die RICHTIGE Antwort** (Masterplan Kap. 15.3).
    Anders als beim verworfenen P09 (min/max vertauscht - der Server beanstandet das gar
    nicht) entsteht hier nachweislich ein Validierungsfehler.
    """
    di = _dem_indizes(daten, art)
    kern = lambda d: {k: v for k, v in d.items() if k != "demandId"}
    paar = None
    for i in range(len(di)):
        for j in range(i + 1, len(di)):
            if kern(daten["demands"][di[i]]) == kern(daten["demands"][di[j]]):
                paar = (di[i], di[j])
                break
        if paar:
            break
    if paar is None:
        raise ValueError(f"Artikel {art}: kein ununterscheidbares Demand-Paar gefunden")
    quelle, ziel = paar
    vorher = daten["demands"][ziel]["demandId"]
    neu_id = daten["demands"][quelle]["demandId"]
    daten["demands"][ziel]["demandId"] = neu_id
    return [{"jsonPath": f"demands[{ziel}].demandId", "before": vorher, "after": neu_id}]


#: DER PILOTKATALOG. Je Fall ein anderer Artikel - kein Artikel doppelt, keiner aus TABU.
#: `pfad` benennt den Prozesspfad, den der Fall abdecken soll (AP-G1).
KATALOG = [
    ("P01", "100099", [m_dichte_null], "einfacher Einzelfehler",
     "Ein Fehler, klarer Korrekturwert aus dem Vergleichskollektiv."),
    ("P02", "100112", [m_unbekannter_artikel], "Referenz-/ID-Fehler",
     "Demand zeigt auf einen Artikel, den es nicht gibt."),
    ("P03", "100254", [m_dichte_null], "fachlicher Korrekturwert",
     "Zerstoerter Wert; richtig ist nur der Originalwert, nicht der Median."),
    ("P04", "106071", [m_doppelte_demand_id, m_unbekannter_arbeitsplan],
     "mehrere gleichzeitige Fehler",
     "Zwei unabhaengige Fehler in einem Snapshot."),
    ("P05", "106072", [m_doppelte_demand_id], "moeglicher Folgefehler",
     "Eine ID-Korrektur kann eine neue Kollision erzeugen, wenn der gewaehlte Wert schon existiert."),
    # P06 und P07 sind ARCHIVIERT (BA-035, Begruendung in ARCHIVIERT unten). Ihre Pfade sind
    # per Fehlerinjektion NICHT konstruierbar - am Code und an den Daten belegt (BA-048).
    # Sie bleiben als Faelle bestehen, damit die Kennungen stabil sind und der First Pass
    # zitierbar bleibt; ihr vorgesehener Pfad wird aber NICHT mehr beansprucht.
    ("P06", "106096", [m_unbekannter_arbeitsplan],
     "ARCHIVIERT (urspr.: Kontextsuche ohne Treffer)",
     "Pfad verfehlt: der injizierte Suchwert steht danach IM Snapshot, die Suche findet ihn. "
     "Nicht konstruierbar - siehe test_kontextsuche_pfade.py."),
    ("P07", "106097", [m_demand_id_vertippt],
     "ARCHIVIERT (urspr.: Fuzzy-/Fallback-Suche)",
     "Pfad verfehlt: eine um ein Zeichen geaenderte demandId erzeugt gar keinen "
     "Validierungsfehler. Nicht konstruierbar - siehe test_kontextsuche_pfade.py."),
    ("P08", "106105", [m_department_leer], "relevante Zusatzkarten",
     "Department-Fehler zieht article-departments.md zusaetzlich zur Kernkarte."),
    ("P09", "106140", [m_dichte_umgekehrt],
     "ARCHIVIERT (urspr.: Unsicherheits-/Grenzfall)",
     "Pfad verfehlt: vertauschte min/max werden vom Server nicht beanstandet - es gibt keine "
     "Regel 'min <= max'. 0 Fehler, also kein Lauf. ERSETZT DURCH P11."),
    ("P10", "106150", [m_doppelte_demand_id, m_dichte_null, m_department_leer],
     "Rueckkante 8->2 (mehrere fachliche Iterationen)",
     "Drei Fehler: die Pipeline korrigiert je Durchgang einen, es bleiben welche uebrig - "
     "Knoten 8 muss auf 'continue' entscheiden und die Rueckkante ausloesen."),
    # --- ERSATZFAELLE (BA-048) -------------------------------------------------
    ("P11", "830285", [m_ununterscheidbares_duplikat],
     "Unsicherheits-/Grenzfall mit ECHTER Mehrdeutigkeit",
     "Ersetzt P09. Zwei Demands des Artikels sind ausser in der demandId IDENTISCH - "
     "nach der Duplikat-Injektion ist objektiv nicht entscheidbar, welche die falsche ist. "
     "Anders als P09 entsteht nachweislich ein validate_unique_ids-Fehler. "
     "Ein ehrliches stop_uncertain ist die RICHTIGE Antwort."),
]

#: Warum P06, P07 und P09 nicht gleichwertig ersetzt werden koennen (BA-048).
#: Am ECHTEN Code und an den ECHTEN Daten geprueft, nicht angenommen:
#:
#:   P06 "Kontextsuche ohne Treffer" - NICHT KONSTRUIERBAR.
#:       `search_in_dict()` liefert fuer einen injizierten Wert immer >= 1 Treffer (den
#:       manipulierten Datensatz selbst); nur ein nie injizierter Wert ergibt 0. Wer einen
#:       Platzhalter einfuegt und danach nach ihm sucht, findet ihn zwangslaeufig.
#:
#:   P07 "Fuzzy-/Fallback-Suche" - NICHT DETERMINISTISCH KONSTRUIERBAR.
#:       Der Fuzzy-Pfad in `search_by_id()` greift ausschliesslich bei 0 exakten Treffern.
#:       Aus demselben Grund wie bei P06 ist das per Injektion nicht herstellbar. Der Pfad
#:       EXISTIERT und ist erreichbar (belegt: "D106097_00X" -> 5 Treffer, fuzzy=True), aber
#:       nur mit einem Suchwert ausserhalb des Dokuments - und den waehlt Knoten 2, nicht wir.
#:
#:   Beide Pfade werden deshalb auf KNOTENEBENE abgedeckt (`test_kontextsuche_pfade.py`),
#:   nicht als Pilotfall. Das ist eine Grenze der Fehlerinjektion als Ground-Truth-Methode
#:   und gehoert als solche in die Limitationen (K8).
#:
#:   Ein dritter Ersatz - "Artikel ohne Vergleichskollektiv" - waere ebenfalls interessant
#:   gewesen und ist ebenfalls nicht konstruierbar: der Datensatz kennt genau ZWEI
#:   (departmentId, workPlanId)-Kollektive, mit 91 und 331 Artikeln. Es gibt keinen Artikel
#:   ohne Vergleichsgruppe.
ARCHIVIERT = {
    "P06": "Pfad per Injektion nicht konstruierbar - abgedeckt in test_kontextsuche_pfade.py",
    "P07": "Pfad per Injektion nicht konstruierbar - abgedeckt in test_kontextsuche_pfade.py",
    "P09": "erzeugt keinen Validierungsfehler - ersetzt durch P11",
}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="vorhandenen Pilotkatalog ueberschreiben")
    args = ap.parse_args(argv)

    if ZIEL.exists() and any(ZIEL.iterdir()) and not args.force:
        print(f"FEHLER: {ZIEL} ist nicht leer. Mit --force ueberschreiben.")
        return 1
    ZIEL.mkdir(parents=True, exist_ok=True)

    ok = json.loads(OK.read_text(encoding="utf-8"))
    faelle, benutzte_artikel = [], set()

    for code, art, manips, pfad, warum in KATALOG:
        if str(art) in TABU_ARTIKEL:
            print(f"FEHLER: {code} benutzt den gesperrten Artikel {art}")
            return 1
        if art in benutzte_artikel:
            print(f"FEHLER: Artikel {art} zweimal im Pilotkatalog ({code})")
            return 1
        benutzte_artikel.add(art)

        daten = copy.deepcopy(ok)
        aenderungen = []
        for m in manips:
            aenderungen += m(daten, art)

        datei = f"pilot-{code}.json"
        (ZIEL / datei).write_text(json.dumps(daten, ensure_ascii=False), encoding="utf-8")
        faelle.append({
            "code": code, "file": datei, "title": pfad,
            "prozesspfad": pfad, "begruendung": warum,
            "ziel_artikel": art,
            "erwartete_fehler": len(aenderungen),
            "changes": aenderungen,
            "entitaeten": sorted({str(art)} | {str(c["before"]) for c in aenderungen if c["before"]}),
        })
        print(f"  {code}  Artikel {art:<8} {len(aenderungen)} Manipulation(en)  {pfad}")

    spec = {
        "zweck": "AP-G1 PILOTKATALOG - dient ausschliesslich der Pilotphase (Masterplan Kap. 8.3). "
                 "KEIN Messfall. Ueberschneidungsfreiheit zum Messkatalog wird von "
                 "eval/check_pilot_overlap.py nachgewiesen.",
        "erzeugt_von": "eval/build_pilot_catalog.py",
        "referenz": "ok-snapshot.json",
        "tabu_artikel": sorted(TABU_ARTIKEL),
        "cases": faelle,
    }
    (ZIEL / "expected-results.json").write_text(
        json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n  {len(faelle)} Pilotfaelle in {ZIEL}")
    print(f"  benutzte Artikel: {sorted(benutzte_artikel)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
