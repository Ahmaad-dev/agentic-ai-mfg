"""
Die zwei Suchpfade, die als PILOTFALL nicht konstruierbar sind — auf Knotenebene (BA-048).

WARUM DIESER TEST STATT ZWEIER PILOTFÄLLE
------------------------------------------
P06 („Kontextsuche ohne Treffer") und P07 („Fuzzy-/Fallback-Suche") haben ihren Prozesspfad
verfehlt (BA-035). Die Prüfung der Ersatzfälle ergab zunächst, dass beide Pfade **per
Fehlerinjektion** nicht herstellbar sind. Die weitergehende Frage — *kann Knoten 2 im realen
Korrekturworkflow überhaupt einen Suchwert erzeugen, der nicht schon im Snapshot steht?* —
führt zu einer **schärferen und unangenehmeren Antwort** (BA-049):

> **Nein — nicht auf einem regulären Weg.** Der Suchwert entsteht nicht frei, sondern wird
> vom Modell **aus der Validatormeldung extrahiert** (`identify_error_llm.py:202-210`:
> *„Extract the appropriate search_value"*). Eine Validatormeldung beanstandet einen Wert,
> der **im Snapshot steht** — sonst gäbe es den Fehler nicht. Für alle drei Suchmodi gilt
> deshalb: der gesuchte Wert ist vorhanden.

Damit sind Nulltreffer und Fuzzy-Fallback **im derzeitigen End-to-End-Korrekturworkflow nicht
erreichbar** — unabhängig davon, wie Pilotfälle konstruiert werden. Das ist **keine Frage der
Fallkonstruktion**, sondern eine Eigenschaft des Workflows:

    Modus                 Suchwert                          Nulltreffer möglich?
    value                 Wert aus der Fehlermeldung        nein - er steht im Snapshot
    empty_field           FELDNAME, normalisiert            nein - das leere Feld existiert
    equipment_workitem    fehlender Schlüssel               nein - laut Code-Kommentar
                                                            "occurs in hundreds of valid places"

Die einzige beobachtete Ausnahme ist eine **Fehlklassifikation**: in P10 D5 wählte Knoten 2
`empty_field` für `relDensityMin`, das aber den Wert `0` trug (nicht leer) — Ergebnis
0 Treffer. Das ist kein Prozesspfad, den man ansteuern kann, sondern ein Klassifikationsfehler.

**Zwei Konsequenzen, sauber getrennt:**

1. Die **Fähigkeiten sind implementiert und funktionieren** — hier direkt an Knoten 3
   nachgewiesen, ohne Pipeline, ohne LLM, ohne Server.
2. Sie sind **unter dem derzeitigen regulären E2E-Korrekturworkflow** — mit der aktuellen
   Validatormenge und der aktuellen Ableitung des `search_value` — **nicht erreichbar**.
   Für die Arbeit heisst das: der Fuzzy-Pfad darf **nicht** als Leistungsmerkmal einer
   Architektur gezählt werden und kann zwischen A, B und C unter den Messbedingungen keinen
   Unterschied erzeugen. Befund über das **Bestandssystem** (K3) und Limitation (K8) — kein
   Mangel der Pilotphase.

**Ausdrücklich offen:** andere oder künftige Aufrufer von `search_by_id()`, eine geänderte
Validatormenge, eine andere Suchwertableitung — oder eine **Fehlklassifikation durch Knoten 2**
(real beobachtet in P10 D5) — können diese Pfade grundsätzlich erreichen. Die Aussage gilt dem
*heutigen regulären Ablauf*, nicht dem Code an sich. **„Toter Code" wäre zu pauschal.**

**Kein Messlauf.** Keiner der 17 Messfälle wird gelesen oder ausgeführt.

Aufruf:  .venv/Scripts/python.exe app/eval/test_kontextsuche_pfade.py
"""
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from graph_regression_harness import APP, Pruefung, pfade_setzen  # noqa: E402

pfade_setzen()
OK = APP.parent / "data" / "snapshots" / "ok-snapshot.json"


def pruefen() -> Pruefung:
    import identify_snapshot as ids

    p = Pruefung("Kontextsuche — Null-Treffer und Fuzzy: Knotenebene UND E2E-Erreichbarkeit")
    daten = json.loads(OK.read_text(encoding="utf-8"))

    with redirect_stdout(io.StringIO()):
        # --- (1) Warum P06 nicht konstruierbar ist ---
        manipuliert = json.loads(json.dumps(daten))
        manipuliert["articles"][0]["workPlanId"] = "PLAN_GIBTESNICHT"
        treffer_injiziert = ids.search_in_dict(manipuliert, "PLAN_GIBTESNICHT")
        treffer_nie = ids.search_in_dict(daten, "KOMMT_NIRGENDS_VOR_XYZ")

        # --- (2) Der Fuzzy-Pfad, direkt nachgewiesen ---
        fuzzy = ids.search_by_id(daten, "D106097_00X")
        exakt = ids.search_by_id(daten, "D106097_001")

    # (1) Der Beleg fuer die Unmoeglichkeit
    p.gleich("injizierter Wert wird von der exakten Suche GEFUNDEN", 1, len(treffer_injiziert))
    p.gleich("nie injizierter Wert ergibt 0 Treffer", 0, len(treffer_nie))
    p.wahr("=> Null-Treffer per Injektion ist strukturell unmoeglich",
           len(treffer_injiziert) >= 1 and len(treffer_nie) == 0,
           "der manipulierte Datensatz ist immer selbst ein Treffer")

    # (2) Die Faehigkeit existiert trotzdem - hier direkt nachgewiesen
    p.wahr("Fuzzy-Pfad liefert Treffer fuer eine NICHT existierende, aehnliche ID",
           len(fuzzy) > 0, len(fuzzy))
    p.wahr("Fuzzy-Treffer sind als solche markiert",
           all(r.get("fuzzy_match") for r in fuzzy),
           [r.get("fuzzy_match") for r in fuzzy][:5])
    p.wahr("die aehnlichsten Treffer sind die tatsaechlich existierenden IDs",
           any("D106097_00" in json.dumps(r) for r in fuzzy),
           [str(r)[:40] for r in fuzzy][:2])
    # Abgrenzung: bei einem exakten Treffer darf NICHT auf Fuzzy umgeschaltet werden.
    p.wahr("bei exaktem Treffer wird NICHT gefuzzt",
           len(exakt) > 0 and not any(r.get("fuzzy_match") for r in exakt),
           [r.get("fuzzy_match") for r in exakt][:3])

    # (3) E2E-ERREICHBARKEIT: woher stammt der Suchwert? (BA-049)
    # Statisch am Prompt und an den drei Modi - kein LLM-Aufruf.
    import identify_error_llm as ident
    quelle = Path(ident.__file__).read_text(encoding="utf-8", errors="replace")
    p.wahr("Knoten 2 EXTRAHIERT den Suchwert aus der Fehlermeldung (kein freier Wert)",
           "Extract the appropriate search_value" in quelle,
           "identify_error_llm.py, Prompt-Schritt 5")
    p.wahr("value-Modus: Suchwert ist der beanstandete Wert",
           '"search_value": "the ID value to search for (value mode) OR the field name' in quelle,
           "Prompt-Schema")
    p.wahr("empty_field-Modus: Suchwert ist ein FELDNAME, kein Wert",
           "normalize_field_name(search_value)" in quelle,
           "identify_error_llm.py:320")
    p.wahr("equipment_workitem-Modus: der 'fehlende' Schluessel kommt vielfach vor",
           "occurs in hundreds of valid places" in quelle,
           "Code-Kommentar in identify_error_llm.py")
    p.wahr("=> im E2E-Workflow ist der Suchwert IMMER im Snapshot vorhanden",
           all(m in quelle for m in ("Extract the appropriate search_value",
                                     "normalize_field_name(search_value)",
                                     "occurs in hundreds of valid places")),
           "Nulltreffer/Fuzzy im REGULAEREN E2E-Ablauf nicht erreichbar - auf Knotenebene "
           "implementiert und getestet; andere Aufrufer/Fehlklassifikationen bleiben moeglich")

    # (4) Und der Grund, warum auch 'Artikel ohne Vergleichskollektiv' nicht geht
    from collections import Counter
    paare = Counter((a.get("departmentId"), a.get("workPlanId"))
                    for a in daten.get("articles") or [])
    p.gleich("Anzahl verschiedener (departmentId, workPlanId)-Kollektive", 2, len(paare))
    p.gleich("kleinstes Kollektiv im Datensatz", 91, min(paare.values()))
    p.wahr("=> kein Artikel ohne Vergleichsgruppe konstruierbar",
           min(paare.values()) > 1, dict(paare.most_common()))
    return p


def main():
    sys.path.insert(0, str(APP))
    from core.run_metadata import require_ba_env
    meta = require_ba_env("Kontextsuche-Pfadnachweis (BA-048)")
    print(f"Umgebung: {meta['umgebung']['sys_prefix']}")
    p = pruefen()
    p.drucken()
    return 0 if p.bestanden else 1


if __name__ == "__main__":
    sys.exit(main())
