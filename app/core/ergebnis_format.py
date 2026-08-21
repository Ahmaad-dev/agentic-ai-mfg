"""
Variantenneutrales Endergebnis-Format fuer A, B und C.

WOZU (BA-031, 20.08.2026)
-------------------------
Knoten 9 erzeugte bis heute einen LLM-Audit-Report. Das war ein **vierter** Modellaufruf, den
die Monolith-Pipeline nicht macht (`full_correction` hat sieben Schritte und enthaelt
`generate_audit_report` **nicht**) — also eine Faehigkeit, die nur Bedingung C hatte. Sie
haette Zeit- und Tokenvergleiche verzerrt, ein Artefakt erzeugt, das A und B fehlt, und bei der
Expertenbewertung die Blindung gebrochen (CLAUDE.md, Bauregel B).

Diese Datei ist die Antwort darauf: **eine deterministische Funktion, die aus den fachlich
relevanten Enddaten aller drei Bedingungen dasselbe Schema erzeugt.**

  * **Kein LLM.** Kein Netzwerk. Gleiche Eingabe -> gleiche Ausgabe, bitgleich.
  * **Keine Fachlogik, keine Bewertung.** Es wird nichts abgeleitet, gerechnet oder beurteilt —
    nur umgeformt. Jeder Wert stammt unveraendert aus dem, was die Pipeline erzeugt hat.
  * **C** benutzt sie in Knoten 9. **A und B** benutzen sie ausschliesslich fuer die
    Evaluierungsdarstellung, NICHT in ihrer Pipeline — deren Ablauf bleibt unangetastet
    (harte Regel 1).
  * `generate_audit_report()` bleibt unveraendert als optionale, nachgelagerte
    Produktfunktion bestehen. Sie ist **nicht** Bestandteil der A/B/C-Hauptmessung.

WARUM DAS FUER DIE BLINDUNG NOETIG IST (Kap. 16)
------------------------------------------------
Die Varianten erzeugen strukturell verschiedene Ausgaben. Den Experten wird nur das
**fachliche Endergebnis** vorgelegt, in einem Format, das nicht verraet, aus welcher
Architektur es stammt. Genau dieses Format steht hier — und zwar **einmal**, damit es fuer alle
drei Bedingungen nachweislich dasselbe ist.
"""
from __future__ import annotations

#: Version des Schemas. Aendert es sich nach dem Einfrieren (AP-G5), sind frueher erzeugte
#: Darstellungen nicht mehr vergleichbar - deshalb hier sichtbar und nicht implizit.
SCHEMA_VERSION = "1.0"

#: Die Schluessel des neutralen Formats, in fester Reihenfolge. Feste Reihenfolge, weil das
#: Format Experten vorgelegt wird: eine wechselnde Anordnung waere selbst ein Hinweis auf die
#: Variante.
FELDER = (
    "schema_version",
    "snapshot_id",
    "fehler_vorher",
    "fehler_nachher",
    "revalidierung_abgeschlossen",
    "ergebnis",
    "korrektur_vorhanden",
    "korrektur_aktion",
    "korrektur_feld",
    "korrektur_wert",
    "korrektur_begruendung",
    "schema_gueltig",
    "schema_versuche",
    "angewendet",
    "hochgeladen",
    "iterationen",
    "manuelle_pruefung_noetig",
)

#: WAS DEN EXPERTEN GEZEIGT WIRD - eine echte Teilmenge von FELDER.
#:
#: Befund aus AP-F5 (20.08.2026, zweiter Durchgang): `schema_gueltig` und `schema_versuche`
#: gibt es NUR in Bedingung C. `validate_correction_schema_llm` persistiert sein Ergebnis
#: naemlich nirgends - es steht nur in stdout und im Exit-Code; erst Knoten 6 schreibt es als
#: `technical_check` in den Zustand. Wuerde die Vorlage diese Felder zeigen, staende bei C
#: "gueltig=True nach 0 Versuch(en)" und bei A "nicht protokolliert" - **das allein wuerde die
#: Bedingung verraten**. Deshalb enthaelt die Vorlage ausschliesslich Felder, die in ALLEN
#: Armen aus Artefakten belegbar sind.
#:
#: Die uebrigen Felder bleiben im Datensatz - fuer die Auswertung, nicht fuer die Vorlage.
#: Dass C sie hat und A nicht, ist selbst ein UF3-Befund und wird dort ausgewertet, nicht
#: verschwiegen.
VORLAGE_FELDER = (
    "snapshot_id",          # wird durch das Pseudonym ersetzt
    "fehler_vorher",
    "fehler_nachher",
    "ergebnis",
    "korrektur_vorhanden",
    "korrektur_aktion",
    "korrektur_feld",
    "korrektur_wert",
    "korrektur_begruendung",
    "angewendet",
    "hochgeladen",
    "iterationen",
    "manuelle_pruefung_noetig",
)

#: Uebersetzung der internen Entscheidungen in eine variantenneutrale Ergebnisangabe.
#: `decision["action"]` gibt es nur im Graphen; A und B werden ueber dieselbe Tabelle
#: abgebildet, damit die Formulierung nicht verraet, woher sie stammt.
_ERGEBNIS = {
    "stop_valid": "korrigiert und nachweislich fehlerfrei",
    "stop_max_iter": "abgebrochen: Iterationsgrenze erreicht",
    "stop_uncertain": "keine belastbare Aussage moeglich",
    "continue": "laufend",
}


def _ergebnis_text(entscheidung, fehler_nachher, revalidierung_ok) -> str:
    """
    Eine Zeile Klartext. **Keine Bewertung** - nur eine Abbildung vorhandener Werte.

    DIE ZAHLEN SIND AUTORITATIV, NICHT DIE ENTSCHEIDUNG (korrigiert 20.08.2026).
    Der erste Entwurf las zuerst `decision["action"]` und haette bei
    `stop_valid` zusammen mit `fehler_nachher=1` geschrieben "nachweislich fehlerfrei" -
    direkt unter der Zeile, die 1 Fehler ausweist. Genau das falsche Gruen, das an anderer
    Stelle heute beseitigt wurde. Massgeblich ist deshalb die Fehlerzahl aus der
    abgeschlossenen Re-Validierung; die Entscheidung liefert nur, was die Zahlen nicht
    ausdruecken koennen (Iterationsgrenze, laufender Durchgang).

    A und B liefern keine `decision`. Fuer sie entsteht dieselbe Aussage aus denselben
    Zahlen - deshalb steht in beiden Faellen dasselbe da, wenn dasselbe passiert ist.
    """
    if entscheidung == "continue":
        return _ERGEBNIS["continue"]
    # Ohne belastbare Re-Validierung wird KEINE Aussage ueber Validitaet gemacht.
    if revalidierung_ok is False or fehler_nachher is None:
        return _ERGEBNIS["stop_uncertain"]
    if fehler_nachher == 0:
        return _ERGEBNIS["stop_valid"]
    # Ab hier: es sind noch Fehler da.
    if entscheidung == "stop_max_iter":
        return f"abgebrochen: Iterationsgrenze erreicht, es verbleiben {fehler_nachher} Fehler"
    if entscheidung == "stop_valid":
        # Widerspruch zwischen Entscheidung und Zahlen - nicht glaetten, sondern zeigen.
        return (f"widerspruechlich: als fehlerfrei entschieden, gemessen wurden aber "
                f"{fehler_nachher} Fehler")
    return f"korrigiert, es verbleiben {fehler_nachher} Fehler"


def neutrales_ergebnis(*, snapshot_id, fehler_vorher=None, fehler_nachher=None,
                       revalidierung_ok=None, korrektur=None, schema=None,
                       angewendet=None, hochgeladen=None, iterationen=None,
                       entscheidung=None, manuelle_pruefung=False) -> dict:
    """
    Baut das neutrale Endergebnis. Rein umformend, deterministisch, ohne Seiteneffekte.

    Alle Parameter sind Schluesselwortparameter: der Aufrufer muss benennen, was er uebergibt.
    Bei einem so breiten Datensatz waere eine Positionsliste eine Fehlerquelle.

    `korrektur`: der Vorschlag als dict (`action`, `target_path`, `new_value`, `reasoning`).
    `schema`:    dict mit `schema_valid` und `retries`.
    """
    k = korrektur or {}
    s = schema or {}
    aus = {
        "schema_version": SCHEMA_VERSION,
        "snapshot_id": snapshot_id,
        "fehler_vorher": fehler_vorher,
        "fehler_nachher": fehler_nachher,
        # None heisst "keine belastbare Angabe", nicht "nein" (Kap. 7.1.2).
        "revalidierung_abgeschlossen": revalidierung_ok,
        "ergebnis": _ergebnis_text(entscheidung, fehler_nachher, revalidierung_ok),
        "korrektur_vorhanden": bool(k),
        "korrektur_aktion": k.get("action"),
        "korrektur_feld": k.get("target_path"),
        "korrektur_wert": k.get("new_value"),
        "korrektur_begruendung": k.get("reasoning"),
        "schema_gueltig": s.get("schema_valid"),
        "schema_versuche": s.get("retries"),
        "angewendet": angewendet,
        "hochgeladen": hochgeladen,
        "iterationen": iterationen,
        "manuelle_pruefung_noetig": bool(manuelle_pruefung),
    }
    # Feste Reihenfolge - siehe FELDER.
    return {f: aus[f] for f in FELDER}


def aus_graph_state(zustand: dict) -> dict:
    """Bedingung C: aus dem `GraphState`. Liest nur, veraendert nichts."""
    return neutrales_ergebnis(
        snapshot_id=zustand.get("snapshot_id"),
        fehler_vorher=zustand.get("errors_before"),
        fehler_nachher=zustand.get("errors_after"),
        revalidierung_ok=((zustand.get("applied") or {}).get("revalidation") or {}).get("ok"),
        korrektur=zustand.get("correction_proposal"),
        schema=zustand.get("technical_check"),
        angewendet=(zustand.get("applied") or {}).get("applied_ok"),
        hochgeladen=(zustand.get("applied") or {}).get("uploaded"),
        iterationen=zustand.get("iteration"),
        entscheidung=(zustand.get("decision") or {}).get("action"),
        manuelle_pruefung=zustand.get("manual_intervention_required", False),
    )


def aus_pipeline_ergebnis(rueckgabe: dict, *, snapshot_id, korrektur=None,
                          fehler_vorher=None, schema=None) -> dict:
    """
    Bedingungen A und B: aus der Rueckgabe von `SPAgent.execute_pipeline()` plus den
    Artefakten, die die Pipeline ohnehin schreibt.

    **Wird NICHT in der Pipeline aufgerufen**, sondern erst bei der Auswertung. Der Ablauf von
    A und B bleibt dadurch unveraendert.
    """
    fv = rueckgabe.get("final_validation") or {}
    return neutrales_ergebnis(
        snapshot_id=snapshot_id,
        fehler_vorher=fehler_vorher,
        fehler_nachher=fv.get("errors") if rueckgabe.get("final_validation") else None,
        revalidierung_ok=fv.get("revalidation_ok") if rueckgabe.get("final_validation") else None,
        korrektur=korrektur,
        schema=schema,
        # A und B fuehren keinen expliziten Zustand darueber; `success` der Pipeline setzt
        # beides voraus. Bewusst NICHT geraten, wenn die Pipeline gescheitert ist.
        angewendet=True if rueckgabe.get("success") else None,
        hochgeladen=True if rueckgabe.get("success") else None,
        iterationen=rueckgabe.get("total_iterations"),
        entscheidung=None,
        manuelle_pruefung=bool(rueckgabe.get("waiting_for_decision")),
    )


def als_text(neutral: dict, pseudonym: str | None = None) -> str:
    """
    **Vorlageform fuer die verblindete Evaluation.** Zeigt ausschliesslich `VORLAGE_FELDER`.

    `pseudonym` ERSETZT die Snapshot-ID und ist hier **Pflicht** (siehe unten). Fuer den
    PRODUKTBETRIEB gilt das nicht - dort darf und soll der Report reale Angaben tragen; dafuer
    ist `generate_audit_report()` zustaendig, nicht diese Funktion.

    ZWEI BEFUNDE AUS AP-F5, die beide die Blindung gebrochen haetten:

    1. **Die Snapshot-ID.** Jede Bedingung laeuft auf einem eigenen frischen Snapshot, also
       stand in jeder Vorlage eine andere UUID. Wer die Zuordnung Snapshot->Bedingung kennt -
       und das Protokoll enthaelt sie zwangslaeufig -, ordnet jede Vorlage zu, ohne sie zu
       lesen. Die Zuordnungstabelle Pseudonym->Snapshot gehoert in eine getrennte Datei, die
       die Bewerter nicht sehen (Kap. 16).
    2. **Felder, die es nur in einem Arm gibt.** `schema_gueltig`/`schema_versuche` stammen aus
       `technical_check` und existieren nur in C. Ihre blosse Anwesenheit haette die Variante
       verraten. Sie sind deshalb nicht Teil der Vorlage.

    Die Strukturpruefung allein haette beides nicht gefunden: sie suchte nach
    Architekturbegriffen, nicht nach **Zuordenbarkeit**. Genau davor warnt harte Regel 6.
    """
    if not pseudonym:
        # Kein stiller Rueckfall auf die echte ID - das war der Befund.
        raise ValueError("Fuer die Evaluierungsvorlage ist ein Pseudonym Pflicht (AP-F5). "
                         "Fuer den Produktbetrieb `generate_audit_report()` verwenden.")
    z = ["ERGEBNIS DER AUTOMATISCHEN PRUEFUNG UND KORREKTUR",
         "=" * 52,
         f"Datensatz            {pseudonym}",
         f"Fehler vorher        {neutral['fehler_vorher']}",
         f"Fehler nachher       {neutral['fehler_nachher']}"
         f"{'  (nicht belastbar ermittelt)' if neutral['fehler_nachher'] is None else ''}",
         f"Ergebnis             {neutral['ergebnis']}",
         ""]
    if neutral["korrektur_vorhanden"]:
        z += ["VORGESCHLAGENE KORREKTUR",
              f"  Aktion             {neutral['korrektur_aktion']}",
              f"  Feld               {neutral['korrektur_feld']}",
              f"  Neuer Wert         {neutral['korrektur_wert']}",
              f"  Begruendung        {neutral['korrektur_begruendung']}"]
    else:
        z += ["VORGESCHLAGENE KORREKTUR", "  keine"]
    z += ["",
          f"Angewendet           {neutral['angewendet']}",
          f"Hochgeladen          {neutral['hochgeladen']}",
          f"Durchgaenge          {neutral['iterationen']}"]
    if neutral["manuelle_pruefung_noetig"]:
        z.append("Hinweis              manuelle Pruefung erforderlich")
    return chr(10).join(z)
