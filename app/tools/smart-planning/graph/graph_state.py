"""
GraphState — das zentrale Zustandsobjekt der graph-basierten Variante.

Referenz: BA_MASTERPLAN.md Kapitel 10 (Feldliste), Kapitel 9 (Knoten), Kapitel 11 (Kanten).

WARUM DIESES OBJEKT DER KERN DER ARBEIT IST
-------------------------------------------
Der Monolith hat bereits Zwischenartefakte — `llm_identify_response.json`,
`last_search_results.json`, `llm_correction_proposal.json`, `snapshot-validation.json`.
Der Unterschied ist deshalb NICHT "Zustand vorhanden gegen nicht vorhanden", sondern
graduell (Masterplan Kap. 3.7 und 15.2):

    verstreut  -> ein Objekt
    untypisiert -> TypedDict
    ohne Reihenfolge -> `trace` in Ausfuehrungsreihenfolge
    ohne Zeitstempel -> je Eintrag `timestamp_utc` und `duration_ms`
    OHNE REGELPROVENIENZ -> `matched_rules` haelt fest, welche Karten wirklich geladen wurden

Der letzte Punkt ist der einzige, den der Monolith gar nicht hat: dort steht die
Kartenauswahl nur in einem `print()` in generate_correction_llm.py und verschwindet im
stdout des Subprozesses.

WICHTIG FUER DIE MESSUNG (Kap. 15.2)
------------------------------------
Alles hier wird VOM CODE aufgezeichnet, nicht VOM MODELL erzaehlt. `matched_rules` ist das,
was der Loader tatsaechlich geladen hat; `technical_check` das, was der Validator tatsaechlich
zurueckgab. Das ist die Antwort auf Turpin et al. (2023, L11): Modellbegruendungen koennen den
echten Entscheidungsweg falsch darstellen — Beobachtungen koennen es nicht.
"""
from typing import Literal, Optional, TypedDict


class GraphState(TypedDict, total=False):
    """
    Wandert durch alle neun Knoten. Jeder Knoten schreibt genau sein Feld und haengt einen
    Eintrag an `trace` an.

    `total=False`, weil der Zustand waehrend eines Laufs schrittweise gefuellt wird — beim
    Eintritt in Knoten 1 existieren die spaeteren Felder noch nicht.
    """

    # --- Identitaet und Lauf-Metadaten ---
    snapshot_id: str
    iteration: int
    #: Der tatsaechlich von der Runtime angelegte `iteration-N`-Ordner (BA-043).
    #: STRIKT GETRENNT von `iteration`: das ist der fachliche Durchgang, dies hier der
    #: Artefaktpfad. Sie stimmen nur zufaellig ueberein und duerfen nie gleichgesetzt
    #: werden. Im Graph-Pfad ist `None` ein UNGUELTIGER Zustand - kein Fallback.
    artifact_iteration_number: Optional[int]
    max_iterations: int
    architecture_mode: Literal["graph"]   # zur eindeutigen Kennzeichnung in den Rohdaten
    started_at: str                        # ISO-8601 UTC
    finished_at: Optional[str]

    # --- Fehlerzustand ---
    errors_before: int
    errors_after: Optional[int]
    # STATE-SCHNITT (20.08.2026). Vorher trug EIN Feld `validation_result` zwei Bedeutungen
    # und zwei Formen: Knoten 1 legte den Vor-Zustand als Dict ab, Knoten 7 ueberschrieb ihn
    # mit der rohen Nach-Meldungsliste. Inhaltlich war beides richtig, aber ein Feld mit zwei
    # Formen ist eine Falle - beim ersten AP-D-Gesamtsmoke bin ich selbst darauf
    # hereingefallen (BA-026). Jetzt getrennt und eindeutig:
    initial_validation: Optional[dict]      # Knoten 1: {quelle, meldungen, errors, warnings,
                                           #            error_tags} - Stand BEIM EINSTIEG
    final_validation: Optional[list]        # Knoten 7: ROHE Meldungsliste NACH der
                                           #            Re-Validierung, oder None
    # `errors_before` und `errors_after` bleiben davon getrennte, ABGELEITETE Werte - sie
    # duerfen nie aus einem der beiden Felder rekonstruiert werden muessen.

    # --- Knoten-Ausgaenge (je Knoten genau ein Feld) ---
    # Knoten 2 — Fehlerklassifikation
    classified_error: Optional[dict]       # {tag, priority, reasoning, raw_message}
    # Knoten 3 — Kontextsuche. `lines_used`/`field_examples` sind die Provenienz der DATEN;
    # sie faengt Befund D ab (Vorschlag berief sich auf ein Kollektiv, das er nicht benutzt hatte).
    extracted_context: Optional[dict]      # {target_path_hint, field_examples, lines_used, search_mode}
    # Knoten 4 — Regelzuordnung. Provenienz der REGELN. Beobachtungspunkt fuer Kategorie 3
    # gemeinsam mit Knoten 5 (Kap. 15.1): hier steht, was geladen WAR, dort die Behauptung darueber.
    matched_rules: Optional[dict]          # {rulebook_mode, cards_loaded: list[str], rule_text_hash}
    # Knoten 5 — Korrekturgenerierung. Beobachtungspunkt fuer Kategorie 1 (fachlich).
    correction_proposal: Optional[dict]    # {action, target_path, new_value, reasoning, llm_confidence}
    #: Die VOLLSTAENDIGE `LLMCorrectionResponse`-Huelle, die Knoten 5 tatsaechlich erzeugt und
    #: unter `iteration-N/llm_correction_proposal.json` abgelegt hat (BA-047).
    #: STRIKT GETRENNT von `correction_proposal`, das nur den INNEREN Vorschlag traegt:
    #:     correction_response = {iteration, snapshot_id, original_error, error_analyzed,
    #:                            correction_proposal: {...}}
    #: WOZU: Knoten 6 prueft gegen `LLMCorrectionResponse` - also gegen die HUELLE. Bekam er
    #: den inneren Vorschlag, fehlten ihm vier Pflichtfelder, und es entstand ein erzwungener
    #: LLM-Retry, den A und B nicht haben (BA-046). Die Huelle wird deshalb verlustfrei
    #: durchgereicht, statt sie in Knoten 6 neu zu bauen: nur so ist der Pruefgegenstand
    #: BEWEISBAR dasselbe Objekt, das Knoten 5 erzeugt hat.
    #: Nach einem technischen Retry ist die FINALE Huelle autoritativ und wird hier ersetzt.
    correction_response: Optional[dict]
    # Knoten 6 — Technische Pruefung. Beobachtungspunkt fuer Kategorie 2 (strukturell);
    # ERZEUGT wird sie in Knoten 5, hier wird sie nur ERKANNT.
    technical_check: Optional[dict]        # {schema_valid, retries, errors: list}
    # Knoten 7 — Anwendung und Re-Validierung. Beobachtungspunkt fuer Kategorie 4 (Folgefehler).
    # Erzeugt `errors_after`; ohne diesen Knoten schliesst die Iterationsschleife nicht.
    applied: Optional[dict]                # {applied_ok, uploaded, new_error_types: list}
    # Knoten 8 — Ergebnisbewertung. BEWUSST EIN KNOTEN, KEINE KANTE (Kap. 9): eine Kante
    # hinterlaesst keinen Zwischenzustand, auf den man zeigen kann. Der Router liest danach
    # nur noch `decision["action"]` und enthaelt KEINE Fachlogik.
    decision: Optional[dict]               # {action, reasoning}
    # Knoten 9 - das variantenneutrale Endergebnis (BA-031). Deterministisch gebildet,
    # KEIN LLM. Dasselbe Schema erzeugt `core.ergebnis_format` auch fuer A und B, dort
    # aber ausserhalb der Pipeline und nur fuer die Auswertung.
    final_answer: Optional[dict]
    manual_intervention_required: bool

    # --- Nachvollziehbarkeits-Instrument (das wichtigste Feld fuer UF3) ---
    trace: list[dict]                      # je Eintrag: {node, timestamp_utc, input_digest,
                                           #              output_digest, duration_ms}


#: Erlaubte Werte von `decision["action"]` (Kap. 11, bedingte Kante B).
#: "stop_uncertain" ist KEIN Sonderfall, den wir uns ausdenken — es formalisiert real
#: beobachtetes Verhalten (`target_path=None`). Fuer UF2 ist genau das der positiv zu
#: wertende "ehrliches Nein statt halluzinierter Korrektur"-Pfad.
DECISION_ACTIONS = ("continue", "stop_valid", "stop_max_iter", "stop_uncertain")


def new_state(snapshot_id: str, errors_before: int, max_iterations: int = 5) -> GraphState:
    """Frischer Zustand fuer den Eintritt in Knoten 1."""
    from datetime import datetime, timezone
    return GraphState(
        snapshot_id=snapshot_id,
        iteration=0,
        max_iterations=max_iterations,
        architecture_mode="graph",
        started_at=datetime.now(timezone.utc).isoformat(),
        finished_at=None,
        errors_before=errors_before,
        errors_after=None,
        manual_intervention_required=False,
        trace=[],
    )
