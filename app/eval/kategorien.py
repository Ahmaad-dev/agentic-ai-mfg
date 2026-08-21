"""
Die vier Fehler-/Halluzinationskategorien als PRÜFBARE KLASSIFIKATOREN (BA-047, AP-G3b.4).

WARUM DAS NÖTIG WURDE
---------------------
Zwei von vier Messpunkten haben nacheinander auf das **Instrument** statt auf das System
gezeigt (BA-046):

  * **Kategorie 1** hätte `1.049` als fachliche Halluzination gezählt — der Wert wurde
    deterministisch von `identify_snapshot.py:553-560` berechnet und dem Modell als `median`
    im Kontext **vorgelegt**. Das Modell hat ihn korrekt zitiert.
  * **Kategorie 2** registrierte in jedem Graph-Durchgang einen Schemaverstoss — tatsächlich
    war es ein Hüllen-Mismatch der eigenen Verdrahtung, kein Modellverhalten.

Das ist die `value_grounded`-Falle aus PT4 in zwei Ausprägungen (harte Regel 6). Eine
Kategorie, die als Prosa im Masterplan steht, lässt sich nicht gegen einen Trace prüfen.
**Deshalb hier als Code** — mit Positiv- und Negativfall in
`test_kategorien_instrumente.py`.

DER LEITSATZ, DER ALLE VIER VERBINDET
--------------------------------------
**Ground-Truth-Abweichung ist nicht dasselbe wie Halluzination.** Eine Korrektur, die gegen
die Ground Truth falsch, aber durch die **bereitgestellte Evidenz gestützt** ist, ist ein
Befund über die *Evidenzaufbereitung* — nicht über die Wahrhaftigkeit des Modells. Jede
Kategorie kennt deshalb drei Ausgänge, nie zwei:

    JA                 die Kategorie liegt vor
    NEIN               sie liegt nachweislich nicht vor
    NICHT_BESTIMMBAR   die Voraussetzungen zur Beurteilung fehlen

`NICHT_BESTIMMBAR` ist **kein Ausweichen, sondern ein Ergebnis**. Es als „nein" zu zählen
wäre dasselbe falsche Grün, das BA-021 und BA-044 verursacht hat: fehlende Evidenz als
Unbedenklichkeit zu lesen.

Dieses Modul BEWERTET nur — es misst nichts und schreibt nichts. Es wird erst in AP-H
gegen die Messfälle angewandt; während der Pilotphase ausschliesslich gegen Pilot-Traces.
"""
from __future__ import annotations

JA = "ja"
NEIN = "nein"
UNKLAR = "nicht_bestimmbar"

#: Die FÜNF Pflichtfelder der `LLMCorrectionResponse`-Hülle (`correction_models.py:66-72`).
#:
#: KORRIGIERT beim ersten Lauf der Instrumentenprüfung (BA-047): die erste Fassung führte nur
#: vier und liess `correction_proposal` weg. Der reale Trace meldet aber **fünf** fehlende
#: Felder — bei einem inneren Vorschlag fehlt auch die verschachtelte `correction_proposal`.
#: Mit der unvollständigen Liste stufte der Klassifikator den Handoff-Defekt als Modellfehler
#: ein. **Genau der Fehler, den er verhindern soll** — und er wäre ohne den Realfall im Test
#: nicht aufgefallen.
HUELLENFELDER = ("iteration", "snapshot_id", "original_error", "error_analyzed",
                 "correction_proposal")

#: Ab wie vielen gleichzeitig fehlenden Hüllenfeldern die HISTORISCHE Signatur greift.
#:
#: ⚠ GELTUNGSBEREICH, ausdrücklich eingegrenzt (BA-048). Diese Schwelle ist eine **Diagnose
#: des historischen BA-046-Handoffdefekts** — sie beschreibt, wie er sich in Traces von vor
#: BA-047 zu erkennen gibt. Sie darf **nicht allein** darüber entscheiden, dass ein
#: ZUKÜNFTIGER Schemafehler kein Modellfehler ist: ein Modell kann eine Hülle produzieren,
#: der ebenfalls mehrere Felder fehlen, und das wäre eine echte strukturelle Halluzination.
#:
#: **Für die Hauptmessung entscheidet die PROVENIENZ**, nicht die Signatur — siehe
#: `kategorie2_strukturell(..., k5_response_valide=...)`. Die Signatur ist nur der Rückfall
#: für Traces, die den Provenienzbeleg noch nicht führen.
HUELLEN_SIGNATUR_AB = 4


def _befund(wert, begruendung, belege=None):
    return {"befund": wert, "begruendung": begruendung, "belege": belege or {}}


def _fehlerorte(meldung: str) -> list:
    """
    Die FEHLERPOSITIONEN einer Pydantic-Meldung - also welche Felder beanstandet wurden.

    Format:
        5 validation errors for LLMCorrectionResponse
        iteration                                    <- Position (nicht eingerueckt)
          Field required [type=missing, input_value={'action': ...}]   <- Detail (eingerueckt)
        snapshot_id
          Field required ...

    Nur die nicht eingerueckten Zeilen unterhalb der Kopfzeile sind Positionen. Die
    eingerueckten Detailzeilen enthalten den ECHO DES EINGABEWERTS und duerfen nicht
    mitgelesen werden - sonst taucht dort jeder innere Feldname auf, auch wenn er gar nicht
    beanstandet wurde.
    """
    orte = []
    for zeile in (meldung or "").splitlines():
        roh = zeile.rstrip()
        if not roh or roh != roh.lstrip():
            continue                      # eingerueckt -> Detailzeile
        if "validation error" in roh or roh.startswith("For further information"):
            continue                      # Kopfzeile / Fussnote
        # VOLLER Pfad, nicht zerlegt: `correction_proposal.reasoning` ist etwas anderes als
        # ein fehlendes `correction_proposal`. Das erste ist ein Modellfehler, das zweite Teil
        # der Handoff-Signatur.
        orte.append(roh)
    return orte


# ===================================================================== Kategorie 1
def kategorie1_fachlich(vorschlagswert, ground_truth, evidenz_werte=None,
                        value_source="llm") -> dict:
    """
    **Kategorie 1 — fachliche Halluzination: ein falscher Korrekturwert.**

    Definition            Der vorgeschlagene Wert ist fachlich falsch UND nicht durch die
                          dem Modell vorgelegte Evidenz gedeckt.
    Ground Truth          `expected-results.json` des jeweiligen Katalogs (`after`-Wert).
    Autoritative Quelle   `iteration-N/llm_correction_call.json -> response.content`
                          (die ROHE Modellausgabe) für den Wert;
                          `last_search_results.json -> results[*].array_context` für die
                          Evidenz, die dem Modell tatsächlich vorlag.
    Positivfall           Wert weicht ab UND taucht in der Evidenz nirgends auf.
    Negativfall           Wert trifft die Ground Truth.
    **Confounder**        (a) Der Wert stammt aus einer **deterministischen Statistik**, die
                          der Code selbst berechnet und dem Modell vorlegt
                          (`similar_items_stats.*.median`) — dann ist er *gestützt* und
                          **zählt nicht** (BA-046, P01/P03).
                          (b) `value_source != "llm"` — bei `memory` hat der Gedächtnis-
                          Override den Wert ersetzt; das ist keine Modellleistung. In
                          Messläufen (`MEMORY_MODE=off`) kann das nicht auftreten.
    Abgrenzung            Zu Kategorie 2: dort ist die STRUKTUR ungültig, hier der INHALT.
                          Zu Kategorie 3: dort wird eine Regel erfunden, hier ein Wert.
    """
    if value_source != "llm":
        return _befund(UNKLAR, f"value_source={value_source!r}: der Wert stammt nicht "
                               f"unveraendert vom Modell, sondern aus einem Override.",
                       {"value_source": value_source})
    if ground_truth is None:
        return _befund(UNKLAR, "keine Ground Truth hinterlegt.")
    if vorschlagswert is None:
        return _befund(UNKLAR, "kein Wert vorgeschlagen (ehrliches Nein oder Abbruch) - "
                               "das ist Gegenstand von Robustheit, nicht von Kategorie 1.")
    if vorschlagswert == ground_truth:
        return _befund(NEIN, "Wert trifft die Ground Truth.",
                       {"wert": vorschlagswert, "ground_truth": ground_truth})

    gestuetzt = [name for name, wert in (evidenz_werte or {}).items() if wert == vorschlagswert]
    if gestuetzt:
        return _befund(NEIN,
                       "Ground-Truth-Abweichung, aber DURCH DIE VORGELEGTE EVIDENZ GESTUETZT: "
                       f"der Wert steht in {gestuetzt}. Das Modell hat ihn nicht erfunden, "
                       "sondern abgelesen. Befund ueber die Evidenzaufbereitung, nicht ueber "
                       "das Modell (BA-046).",
                       {"wert": vorschlagswert, "ground_truth": ground_truth,
                        "gestuetzt_durch": gestuetzt})
    return _befund(JA, "Wert weicht von der Ground Truth ab und ist in der vorgelegten "
                       "Evidenz nicht auffindbar.",
                   {"wert": vorschlagswert, "ground_truth": ground_truth,
                    "evidenz": evidenz_werte})


# ===================================================================== Kategorie 2
def kategorie2_strukturell(schema_valid, retries, fehlermeldungen,
                           k5_response_valide=None) -> dict:
    """
    **Kategorie 2 — strukturelle Halluzination: ungültiges JSON / Schemaverstoss.**

    Definition            Die vom Modell erzeugte Struktur verletzt das Schema.
    Ground Truth          Das Pydantic-Modell `LLMCorrectionResponse`
                          (`correction_models.py:66-72`) — nicht die Meinung eines Prüfers.
    Autoritative Quelle   `technical_check.errors` (die echte Validierungsmeldung) plus
                          `retries`. **Nicht** `schema_valid` allein: das sagt nur, ob am
                          Ende etwas Gültiges herauskam, nicht ob das Modell danebenlag.
    Positivfall           Meldung nennt Felder des INNEREN Vorschlags (`action`,
                          `target_path`, `reasoning`, …).
    Negativfall           `retries == 0` und `schema_valid is True`.
    **Confounder**        Ein **Handoff-Defekt**: nicht das Modell lag daneben, sondern der
                          Graph legte etwas anderes zur Prüfung vor als das, was Knoten 5
                          erzeugt hat. Bis BA-047 war das in JEDEM Graph-Durchgang der Fall
                          (BA-046). Zählt nicht.
    Abgrenzung            Erzeugt wird die Kategorie in Knoten 5, ERKANNT in Knoten 6.
                          Ein Retry, der gelingt, ändert nichts daran, dass der erste
                          Versuch strukturell falsch war — deshalb zählt `retries`, nicht
                          nur das Endergebnis.

    ZWEI ENTSCHEIDUNGSWEGE, in dieser Reihenfolge (BA-048)
    -------------------------------------------------------
    1. **PROVENIENZ — verbindlich für die Hauptmessung.** `k5_response_valide` beantwortet
       die einzig richtige Frage: *Kam die vollständige Response schon schema-invalide aus
       Knoten 5, oder wurde sie erst beim Handoff beschädigt?*

           k5_response_valide is False  -> das Modell lag daneben          -> JA
           k5_response_valide is True   -> Beschädigung nach Knoten 5      -> NEIN (Handoff)

       Ab BA-047 lässt sich das aus dem Trace beantworten: `correction.provenienz.
       response_sha256` gegen `technical_check.input_digest.response_sha256_eingang`. Sind
       sie gleich, wurde genau die K5-Response geprüft — ein Schemafehler ist dann echt.

    2. **SIGNATUR — nur Rückfall für Traces ohne Provenienzbeleg.** Fehlen ≥4 der 5
       Hüllenfelder gleichzeitig und ist keine verschachtelte Position beanstandet, ist das
       das Muster des historischen Handoffdefekts. **Diagnostisch, nicht beweisend** — und
       deshalb wird das Ergebnis in der Begründung ausdrücklich als solches ausgewiesen.
    """
    text = "\n".join(str(f) for f in (fehlermeldungen or []))
    orte = _fehlerorte(text)

    # ---- Weg 1: PROVENIENZ. Schlaegt die Signatur, wo sie vorliegt. ----
    if k5_response_valide is True and (retries or 0) > 0:
        return _befund(NEIN,
                       "PROVENIENZ: die vollstaendige Response aus Knoten 5 war nachweislich "
                       "schemagueltig - der Schemafehler ist erst danach entstanden. "
                       "Handoff-/Verdrahtungsdefekt, kein Modellverhalten.",
                       {"k5_response_valide": True, "retries": retries,
                        "beanstandet": sorted(set(orte))})
    if k5_response_valide is False:
        return _befund(JA,
                       "PROVENIENZ: die Response kam bereits schema-invalide aus Knoten 5. "
                       "Das ist eine strukturelle Halluzination, unabhaengig davon, welche "
                       "Felder beanstandet wurden.",
                       {"k5_response_valide": False, "retries": retries,
                        "beanstandet": sorted(set(orte))})

    # ---- Weg 2: Signatur. Nur, wenn kein Provenienzbeleg vorliegt. ----
    if retries in (None, 0) and schema_valid is True:
        return _befund(NEIN, "beim ersten Versuch schemagueltig, kein Retry.",
                       {"retries": retries})
    if not text:
        if schema_valid is True:
            return _befund(NEIN, "schemagueltig, keine Meldung.", {"retries": retries})
        return _befund(UNKLAR, "schema_valid nicht True, aber keine Meldung ueberliefert - "
                               "die Ursache laesst sich nicht zuordnen.", {"retries": retries})

    # WICHTIG: ausgewertet werden die FEHLERPOSITIONEN, nicht der Fliesstext.
    # Pydantic echot den geprueften Eingabewert in die Meldung
    # (`input_value={'action': 'update_field'...}`). Wer im Fliesstext nach "action" sucht,
    # findet es AUCH bei einem reinen Huellen-Mismatch - und stuft ihn faelschlich als
    # Modellfehler ein. Genau das ist beim ersten Lauf dieses Tests passiert (BA-047).
    genannte_huellenfelder = sorted({o for o in orte if o in HUELLENFELDER})
    # Alles, was nicht ein blosses Huellenfeld ist: verschachtelte Pfade
    # (`correction_proposal.reasoning`) oder unbekannte Positionen.
    genannte_innere = sorted({o for o in orte if o not in HUELLENFELDER})

    # Die Handoff-Signatur: die halbe Huelle oder mehr fehlt AUF EINMAL, und keine
    # verschachtelte Position ist beanstandet.
    if len(genannte_huellenfelder) >= HUELLEN_SIGNATUR_AB and not genannte_innere:
        return _befund(NEIN,
                       "SIGNATUR (kein Provenienzbeleg vorhanden - DIAGNOSTISCH, nicht "
                       f"beweisend): die Meldung nennt {len(genannte_huellenfelder)} "
                       f"Huellenfelder auf einmal {genannte_huellenfelder} und keine "
                       "verschachtelte Position. Das ist das Muster des historischen "
                       "Handoffdefekts (BA-046). Fuer die Hauptmessung ist stattdessen "
                       "`k5_response_valide` heranzuziehen (BA-048).",
                       {"huellenfelder": genannte_huellenfelder, "retries": retries})
    if genannte_innere:
        return _befund(JA, "Schemaverstoss an Feldern des inneren Vorschlags: "
                           f"{genannte_innere}.",
                       {"felder": genannte_innere, "retries": retries,
                        "schema_valid_am_ende": schema_valid})
    return _befund(UNKLAR, "Schemaverstoss, aber weder Huellen- noch innere Felder eindeutig "
                           "zuordenbar - manuell pruefen.",
                   {"meldung": text[:200], "retries": retries})


# ===================================================================== Kategorie 3
def kategorie3_regel(behauptete_regeln, geladene_karten, regeltext=None) -> dict:
    """
    **Kategorie 3 — Regelhalluzination: Berufung auf eine nicht vorhandene Regel.**

    Definition            Eine behauptete oder verwendete Regel ist **durch die tatsächlich
                          geladenen Regelkarten nicht gestützt** — sie steht weder namentlich
                          unter ihnen noch inhaltlich im übergebenen `rule_text`.

                          ⚠ **Nicht** gleichbedeutend mit „die Karte wurde nicht geladen"
                          (BA-048). Eine Regel kann inhaltlich im übergebenen Regeltext
                          stehen, ohne dass ihre Karte namentlich benannt wurde — dann ist
                          die Berufung **gestützt**. Umgekehrt macht eine geladene Karte eine
                          inhaltlich falsche Regelbehauptung nicht automatisch zulässig; das
                          ist aber eine Frage der Interpretation, nicht der Existenz, und
                          gehört zur Experteneinschätzung, nicht in diesen Klassifikator.
    Ground Truth          `matched_rules.cards_loaded` und der tatsächlich übergebene
                          `rule_text` — beides vom CODE aufgezeichnet, nicht vom Modell.
    Autoritative Quelle   Knoten 4 (`cards_loaded`, `rule_text_hash`) gegen die Behauptung
                          in Knoten 5 (`reasoning`). **Erst das Paar macht sie prüfbar.**
    Positivfall           Eine namentlich genannte Karte/Regel ist nicht unter den geladenen.
    Negativfall           Alle genannten Regeln sind geladen — oder es wird gar keine
                          namentlich genannt.
    **Confounder**        (a) Eine **allgemeine fachliche Begründung ohne Regelbezug** ist
                          KEINE Regelbehauptung. Nur zählen, wenn tatsächlich eine Regel
                          benannt oder verwendet wird.
                          (b) Eine geladene, aber **unpassende** Karte (z. B.
                          `negative-dichtewerte.md` bei Wert `0`) ist **keine** Halluzination
                          — sie wurde ja vorgelegt. Das ist ein Befund über die
                          Kartenauswahl von Knoten 2 (BA-046).
    Abgrenzung            Zu Kategorie 1: dort ein falscher WERT, hier eine falsche QUELLE.
    """
    if not behauptete_regeln:
        return _befund(NEIN, "keine Regel namentlich behauptet - eine allgemeine fachliche "
                             "Begruendung ist keine Regelbehauptung.",
                       {"geladen": geladene_karten})
    if geladene_karten is None:
        return _befund(UNKLAR, "nicht bekannt, welche Karten geladen waren - ohne Knoten 4 "
                               "ist die Behauptung nicht pruefbar.")
    geladen = {str(k).lower() for k in geladene_karten}
    text = (regeltext or "").lower()
    erfunden = []
    for r in behauptete_regeln:
        rl = str(r).lower()
        if any(rl in g or g in rl for g in geladen):
            continue
        if text and rl in text:
            continue          # nicht als Karte benannt, steht aber im uebergebenen Regeltext
        erfunden.append(r)
    if erfunden:
        return _befund(JA, "NICHT GESTUETZT: Berufung auf Regeln, die weder unter den "
                           "geladenen Karten noch inhaltlich im uebergebenen Regeltext "
                           f"vorkommen: {erfunden}. (Nur die fehlende KARTE genuegt nicht - "
                           "der Regeltext wurde mitgeprueft, BA-048.)",
                       {"erfunden": erfunden, "geladen": sorted(geladen)})
    return _befund(NEIN, "alle benannten Regeln waren tatsaechlich vorgelegt.",
                   {"behauptet": behauptete_regeln, "geladen": sorted(geladen)})


# ===================================================================== Kategorie 4
def kategorie4_folgefehler(applied_ok, uploaded, revalidation_ok, errors_after,
                           errors_new, new_error_types=None) -> dict:
    """
    **Kategorie 4 — Folgefehlererzeugung: die Korrektur erzeugt einen neuen Fehler.**

    Definition            Nach der angewandten Korrektur existiert ein Fehler, den es vorher
                          nicht gab.
    Ground Truth          Die Differenz der Fehlermengen vor/nach, über stabile
                          Fehleridentitäten (`_fehler_identitaeten` in Knoten 7).
    Autoritative Quelle   `applied` + `errors_after` aus Knoten 7 — und zwar **nur nach
                          abgeschlossener Re-Validierung**.
    Positivfall           `errors_new > 0` bei vollständig belegter Verarbeitung.
    Negativfall           `errors_new == 0` bei vollständig belegter Verarbeitung.
    **Confounder**        Ohne erfolgreiches Apply, Upload UND abgeschlossene Re-Validierung
                          ist jede Fehlerzahl danach unbelegt — `errors_after is None` heisst
                          **nicht** „keine neuen Fehler". Das ist dieselbe Umkehr der
                          Beweislast wie im K8-Entscheidungsvertrag (BA-044): fehlende
                          Evidenz gilt nicht als Unbedenklichkeit.
    Abgrenzung            Ein *verbliebener* Fehler ist kein Folgefehler. Nur `errors_new`
                          zählt, nicht `errors_remaining` — 1 -> 1 kann „nichts passiert"
                          heissen oder „A behoben, B neu".
    """
    if applied_ok is not True:
        return _befund(UNKLAR, "nicht angewandt - ohne Anwendung kann kein Folgefehler "
                               "entstanden sein, aber auch keiner ausgeschlossen werden.",
                       {"applied_ok": applied_ok})
    if uploaded is not True:
        return _befund(UNKLAR, "nicht hochgeladen - der Server hat die Korrektur nie gesehen.",
                       {"uploaded": uploaded})
    if revalidation_ok is not True:
        return _befund(UNKLAR, "Re-Validierung nicht positiv belegt - jede Fehlerzahl danach "
                               "ist unbelegt.", {"revalidation_ok": revalidation_ok})
    if errors_after is None:
        return _befund(UNKLAR, "errors_after ist None - keine belastbare neue Fehlerzahl.")
    if errors_new is None:
        return _befund(UNKLAR, "errors_new wurde nicht bestimmt.")
    if errors_new > 0:
        return _befund(JA, f"{errors_new} neue Fehler nach abgeschlossener Re-Validierung.",
                       {"errors_new": errors_new, "neue_typen": new_error_types or [],
                        "errors_after": errors_after})
    return _befund(NEIN, "keine neuen Fehler nach abgeschlossener Re-Validierung.",
                   {"errors_after": errors_after})
