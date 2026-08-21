"""
Zentrale Definition der Trace-Digest-Schluessel — und ein typisierter Leser.

WARUM ES DIESE DATEI GIBT
--------------------------
Vier Analysen in Folge lasen den falschen Schluessel oder die falsche Digest-Ebene:

  * BA-025  Exit-Codes ueber Textvorkommen gezaehlt statt ueber den AST
  * BA-033  Provenienz-Sonde las die Pipeline-Rueckgabe statt ein Artefakt
  * BA-040  `proposal_sha256` im `output_digest` gesucht - es steht im `input_digest`
  * BA-042  `iteration_number` bei Knoten 6 abgefragt - der Schluessel heisst `iteration`

Jedes Mal wurde daraufhin ein Defekt gemeldet, den es nicht gab. **Das ist inzwischen ein
Risiko fuer die Messinstrumente selbst** (harte Regel 6: erst das Instrument pruefen).

Ab hier rekonstruiert Analysecode keine Schluessel mehr aus dem Gedaechtnis, sondern liest sie
hier. Wer einen Knoten-Digest aendert, aendert ihn HIER mit - und `pruefe_registry()` schlaegt
an, wenn Registry und Code auseinanderlaufen.

DREI GELTUNGSGRADE (BA-044)
---------------------------
Die erste Fassung kannte nur "bekannt" und "unbekannt". Das war zu grob und haette selbst
Fehlalarme erzeugt - genau die Sorte Befund, die schon viermal in eine falsche Defektmeldung
gemuendet ist. **Ein einzelner echter Trace ist kein universelles Pflichtschema**: Knoten
schreiben je nach Zweig unterschiedliche Teilmengen.

    PFLICHT (required)      in JEDEM Eintrag dieses Knotens vorhanden. Fehlt der Schluessel,
                            ist das eine Abweichung - der Knoten hat seinen Digest geaendert.
    BEDINGT (conditional)   darf fehlen, weil ihn nur ein bestimmter Zweig schreibt
                            (z. B. `fehler` nur im Fehlerzweig). Fehlen ist KEINE Abweichung;
                            der Schluessel ist trotzdem bekannt und darf gelesen werden.
    UNBEKANNT               steht nicht in der Registry -> **harter Fehler**, unveraendert.
                            Ein Tippfehler oder ein aus dem Gedaechtnis erfundener Name faellt
                            damit sofort auf, statt still `None` zu liefern.

Ganze EBENEN koennen ebenfalls bedingt sein: Knoten 6 schreibt `provenienz` nur, wenn er
`run_technical_check()` wirklich gerufen hat - im Guard-Zweig (fehlende Artefaktnummer,
BA-043/BA-044) fehlt die Ebene vollstaendig.
"""
from __future__ import annotations

#: Schluessel eines Trace-Eintrags, die KEINE Digest-Ebene sind.
META_SCHLUESSEL = frozenset({"node", "timestamp_utc", "duration_ms"})

#: Welcher Knoten legt welchen Wert in welche Digest-Ebene?
#: Form: knotenname -> ebene -> (schluessel, ...)
#: Das ist die VOLLSTAENDIGE Menge der bekannten Schluessel; welche davon fehlen duerfen,
#: steht in `BEDINGT`.
DIGEST = {
    "input_analysis":   {"input_digest":  ("snapshot_id",),
                         "output_digest": ("quelle", "errors", "warnings", "error_tags", "fehler")},
    "classification":   {"input_digest":  ("iteration", "meldungen"),
                         "output_digest": ("tag", "error_type", "priority_index", "search_mode",
                                           "search_value", "should_investigate",
                                           "relevant_cards_vorgeschlagen", "iteration_number",
                                           "identify_response_sha256", "fehler")},
    "context_search":   {"input_digest":  ("search_mode", "search_value", "should_investigate"),
                         "output_digest": ("results_count", "error_type", "results_hash",
                                           "lines_used", "field_examples", "fehler")},
    "rule_matching":    {"input_digest":  ("tag", "extra_cards"),
                         "output_digest": ("rulebook_mode", "cards_loaded", "chars",
                                           "rule_text_hash", "fehler")},
    # BA-044: `artifact_iteration_number` neu - belegt, AUF WELCHEM Iterationsordner
    # generiert wurde, und ist im Guard-Zweig `None`.
    "correction":       {"input_digest":  ("regeln_von_knoten4", "regeln_zeichen", "regeln_sha256",
                                           "karten", "context_input_sha256", "context_handoff_ok",
                                           "context_results_count", "identify_input_sha256",
                                           "identify_handoff_ok", "artifact_iteration_number"),
                         "provenienz":    ("response_sha256",),
                         "output_digest": ("action", "target_path", "new_value", "value_source",
                                           "confidence_score", "blockiert", "fehler")},
    # ACHTUNG: Knoten 6 nennt den Wert im APPLY-Knoten `iteration`, NICHT `iteration_number`
    # (BA-042). Hier heisst er `artifact_iteration_number`.
    "technical_check":  {"input_digest":  ("hat_vorschlag", "artifact_iteration_number",
                                           "response_sha256_eingang"),
                         "provenienz":    ("proposal_sha256_before", "proposal_sha256_after",
                                           "retry_hat_vorschlag_geaendert",
                                           "response_sha256_final"),
                         "output_digest": ("schema_valid", "retries", "fehleranzahl", "fehler")},
    # ACHTUNG: `proposal_sha256` und `proposal_identisch` stehen im INPUT-Digest (BA-040).
    "apply_revalidate": {"input_digest":  ("schema_valid", "iteration", "proposal_sha256",
                                           "proposal_identisch", "proposal_aus_state"),
                         "output_digest": ("applied_ok", "uploaded", "revalidation_ok",
                                           "revalidation_job", "revalidation_waited_s",
                                           "errors_before", "errors_after", "errors_resolved",
                                           "errors_remaining", "errors_new", "new_error_types",
                                           "fehler")},
    # BA-044: `k7_hat_belegt` und `revalidation_ok` neu - ohne sie laesst sich im Trace nicht
    # nachlesen, WELCHE Stufe des Entscheidungsvertrags gegriffen hat.
    "evaluation":       {"input_digest":  ("schema_valid", "hat_target_path", "k7_hat_belegt",
                                           "applied_ok", "uploaded", "revalidation_ok",
                                           "errors_after", "iteration", "max_iterations"),
                         "output_digest": ("action", "reasoning")},
    "answer":           {"input_digest":  ("decision",),
                         "output_digest": ("schema_version", "ergebnis", "llm_aufruf", "fehler")},
}

#: Schluessel, die FEHLEN DUERFEN - je Knoten und Ebene. Alles in `DIGEST`, was hier nicht
#: steht, ist PFLICHT.
#:
#: Begruendung je Eintrag, damit spaeter niemand raten muss, warum etwas bedingt ist:
#:   `fehler`  - schreiben die Knoten nur im Fehlerzweig bzw. als leere Liste; ein Knoten,
#:               der sauber durchlaeuft, fuehrt ihn teils gar nicht.
#:   Knoten 6 `provenienz` - siehe `BEDINGTE_EBENEN`; die einzelnen Schluessel sind innerhalb
#:               der Ebene Pflicht, wenn die Ebene ueberhaupt da ist.
BEDINGT = {
    "input_analysis":   {"output_digest": ("fehler",)},
    "classification":   {"output_digest": ("fehler",)},
    "context_search":   {"output_digest": ("fehler",)},
    "rule_matching":    {"output_digest": ("fehler",)},
    "correction":       {"output_digest": ("fehler",)},
    "technical_check":  {"output_digest": ("fehler",)},
    "apply_revalidate": {"output_digest": ("fehler",)},
    "answer":           {"output_digest": ("fehler",)},
}

#: Ganze Ebenen, die in einem Eintrag fehlen duerfen.
#: Knoten 6 schreibt `provenienz` nur, wenn `run_technical_check()` wirklich gerufen wurde -
#: im Guard-Zweig bei fehlender `artifact_iteration_number` gibt es keine Hashes, ueber die
#: sich etwas aussagen liesse (BA-043/BA-044).
BEDINGTE_EBENEN = {
    "technical_check": ("provenienz",),
    # BA-047: Knoten 5 fuehrt `provenienz` nur, wenn er wirklich generiert hat. Im
    # Guard-Zweig (fehlende Artefaktnummer) gibt es keine Huelle, ueber die sich etwas
    # aussagen liesse.
    "correction": ("provenienz",),
}


def ist_bekannt(knoten: str, schluessel: str) -> bool:
    """Steht der Schluessel ueberhaupt in der Registry - egal auf welcher Ebene?"""
    return any(schluessel in ks for ks in DIGEST.get(knoten, {}).values())


def ebene_von(knoten: str, schluessel: str):
    """Auf welcher Digest-Ebene steht der Schluessel? `None`, wenn unbekannt."""
    for ebene, ks in DIGEST.get(knoten, {}).items():
        if schluessel in ks:
            return ebene
    return None


def ist_pflicht(knoten: str, schluessel: str) -> bool:
    """PFLICHT heisst: in jedem Eintrag dieses Knotens vorhanden, sonst Abweichung."""
    ebene = ebene_von(knoten, schluessel)
    if ebene is None:
        raise KeyError(f"{knoten!r} kennt keinen Schluessel {schluessel!r}")
    return schluessel not in BEDINGT.get(knoten, {}).get(ebene, ())


def pflichtschluessel(knoten: str, ebene: str) -> set:
    bedingt = set(BEDINGT.get(knoten, {}).get(ebene, ()))
    return set(DIGEST[knoten][ebene]) - bedingt


class TraceLeser:
    """
    Typisierter Zugriff auf einen `graph_state.json`-Trace.

    `hole()` wirft bei einem UNBEKANNTEN Schluessel — ein Tippfehler oder ein aus dem
    Gedaechtnis erfundener Name faellt damit SOFORT auf, statt still `None` zu liefern.
    Genau das war die Fehlerquelle der letzten vier Analysen.

    Ein BEDINGTER Schluessel, der in diesem konkreten Eintrag fehlt, liefert dagegen `None` —
    das ist kein Fehler, sondern der andere Zweig. Wer strenger pruefen will, nimmt
    `hole_pflicht()`.
    """

    def __init__(self, zustand: dict):
        self.zustand = zustand
        self.trace = zustand.get("trace") or []

    def eintraege(self, knoten: str) -> list:
        if knoten not in DIGEST:
            raise KeyError(f"Unbekannter Knoten {knoten!r}. Bekannt: {sorted(DIGEST)}")
        return [t for t in self.trace if t.get("node") == knoten]

    def hole(self, knoten: str, schluessel: str, durchgang: int = 0):
        """Ein Wert aus der richtigen Digest-Ebene. `durchgang` ist 0-basiert."""
        if knoten not in DIGEST:
            raise KeyError(f"Unbekannter Knoten {knoten!r}. Bekannt: {sorted(DIGEST)}")
        ebene = ebene_von(knoten, schluessel)
        if ebene is None:
            raise KeyError(
                f"{knoten!r} hat keinen Schluessel {schluessel!r}. Vorhanden: "
                f"{ {e: list(ks) for e, ks in DIGEST[knoten].items()} }")
        eintr = self.eintraege(knoten)
        if durchgang >= len(eintr):
            return None
        return (eintr[durchgang].get(ebene) or {}).get(schluessel)

    def hole_pflicht(self, knoten: str, schluessel: str, durchgang: int = 0):
        """
        Wie `hole()`, wirft aber zusaetzlich, wenn ein PFLICHT-Schluessel im konkreten
        Eintrag fehlt. Fuer Regressionen, die einen bestimmten Wert wirklich erwarten —
        ein `None` aus einem fehlenden Schluessel sieht sonst aus wie ein `None` als Wert.
        """
        if not ist_pflicht(knoten, schluessel):
            return self.hole(knoten, schluessel, durchgang)
        eintr = self.eintraege(knoten)
        if durchgang >= len(eintr):
            raise IndexError(f"{knoten!r} hat keinen Durchgang {durchgang} "
                             f"(vorhanden: {len(eintr)})")
        ebene = ebene_von(knoten, schluessel)
        digest = eintr[durchgang].get(ebene)
        if digest is None or schluessel not in digest:
            raise KeyError(f"PFLICHT-Schluessel {knoten}.{ebene}.{schluessel} fehlt in "
                           f"Durchgang {durchgang}. Registry und Code laufen auseinander.")
        return digest[schluessel]

    def durchgaenge(self) -> int:
        """Anzahl fachlicher Durchgaenge = Anzahl der Klassifikationen."""
        return len(self.eintraege("classification"))


def pruefe_registry(zustand: dict) -> list:
    """
    Vergleicht die Registry mit einem echten Trace. Gibt Abweichungen zurueck (leer = sauber).

    Drei Arten von Abweichung:
      * unbekannter Knoten oder unbekannte EBENE   -> harter Fehler
      * unbekannter SCHLUESSEL im Trace            -> harter Fehler
      * fehlender PFLICHT-Schluessel               -> Abweichung
    Ein fehlender BEDINGTER Schluessel oder eine fehlende BEDINGTE EBENE ist KEINE Abweichung.
    """
    abweichungen = []
    for i, t in enumerate(zustand.get("trace") or []):
        n = t.get("node")
        if n not in DIGEST:
            abweichungen.append(f"[{i}] Knoten {n!r} fehlt in der Registry")
            continue

        echte_ebenen = set(t) - META_SCHLUESSEL
        for unbekannt in sorted(echte_ebenen - set(DIGEST[n])):
            abweichungen.append(f"[{i}] {n}: Ebene {unbekannt!r} im Trace, nicht in der Registry")

        for ebene, bekannt in DIGEST[n].items():
            if ebene not in t:
                if ebene not in BEDINGTE_EBENEN.get(n, ()):
                    abweichungen.append(f"[{i}] {n}: Pflicht-Ebene {ebene!r} fehlt im Trace")
                continue
            echt = set((t.get(ebene) or {}).keys())
            for unbekannt in sorted(echt - set(bekannt)):
                abweichungen.append(
                    f"[{i}] {n}.{ebene}: {unbekannt!r} im Trace, nicht in der Registry")
            for fehlt in sorted(pflichtschluessel(n, ebene) - echt):
                abweichungen.append(
                    f"[{i}] {n}.{ebene}: PFLICHT-Schluessel {fehlt!r} fehlt im Trace")
    return abweichungen
