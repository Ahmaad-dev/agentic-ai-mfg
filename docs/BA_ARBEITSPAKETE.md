# Arbeitspakete — Umsetzung Bachelorarbeit

**Stand 2026-08-18.** Zum Abhaken. Fachliche Begründung jeweils im `BA_MASTERPLAN.md`
(Kapitelverweise in Klammern) — hier steht **nur**, was zu tun ist, wovon es abhängt und woran
man erkennt, dass es fertig ist.

> **Regel für dieses Dokument:** Ein Paket ist fertig, wenn sein **DoD** (Definition of Done)
> erfüllt und ein Protokolleintrag in `BA_PROJECT_LOG.md` geschrieben ist — nicht, wenn der Code
> läuft. Ohne Eintrag ist die Arbeit später nicht verwertbar (Regel 11 in `CLAUDE.md`).

---

## Überblick

| AP | Titel | Abhängig von | Aufwand | Status |
|---|---|---|---|---|
| **A** | Umgebung final machen | — | ~1,5 T | ☐ |
| **B** | Monolith-Baseline | **A vollständig** | ~1 T | ☐ |
| **C** | Schalter und Gerüst | A | ~0,5 T | ☐ |
| **D** | Knoten extrahieren | C | ~4–5 T | ☐ |
| **E** | Graph verdrahten | D | ~2 T | ☐ |
| **F** | Vertikaler Durchstich | E, B | ~2 T | ☐ |
| **G** | Pilotphase + Einfrieren | F | ~3 T *(kürzbar)* | ☐ |
| **H** | Messen | **G eingefroren** | ~4 T | ☐ |
| **I** | Auswerten und schreiben | H | ~3 T | ☐ |
| **X** | Menschen *(läuft parallel)* | — | kalenderabhängig | ☐ |

**Summe technisch ≈ 20 Arbeitstage.** AP-X läuft daneben und ist nicht durch Fleiss zu
beschleunigen.

### Der kritische Pfad

```
A ──▶ B ──────────────────┐
 └──▶ C ──▶ D ──▶ E ──▶ F ──▶ G ──▶ H ──▶ I
                                 (einfrieren)
X ═══════════════════════════════════════▶  (parallel, extern)
```

**B und C/D/E können parallel laufen** — die Baseline braucht den Graphen nicht. Wer allein
arbeitet, macht B zuerst: er ist kurz und liefert die Referenzzahlen.

---

## ⚠ AP-A vor AP-B — eine Korrektur

**Die Umgebung muss final sein, BEVOR die Baseline gemessen wird.** Grund: `langgraph` zieht
`langchain-core`, das eigene `pydantic`-Anforderungen hat. `pydantic` liegt über
`correction_models.py` **im gemessenen Pfad** (Schemaprüfung, Knoten 6).

Wird die Baseline vor der Installation gefahren und der Graph danach, laufen die beiden Varianten
unter **verschiedenen Bibliotheksversionen** — ein konfundierender Faktor, der genau das kaputt
macht, was Kapitel 7 des Masterplans schützt.

> **Merksatz: erst Umgebung einfrieren, dann messen.** Auch wenn die Installation am Ende
> scheitert und auf den Zustandsautomaten zurückgefallen wird — **du musst es vor der Baseline
> wissen.**

---

# AP-A — Umgebung final machen  ~1,5 Tage

**Ziel:** Eine Umgebung, in der beide Varianten laufen werden, dokumentiert und unveränderlich.

### A1 — `MEMORY_MODE`-Schalter *(Masterplan Kap. 7.2)*
- [ ] **A1.1** `MEMORY_MODE = os.getenv("MEMORY_MODE", "on").lower()` in `app/core/agent_config.py`
- [ ] **A1.2** Guard an den drei Wirkstellen in `generate_correction_llm.py`:
      Abruf (`:886-902`), Override (`:936-975`), `memory_support` (`:1017-1027`)
- [ ] **A1.3** Gegenprobe: mit `off` kein Abruf und `memory_support = 0.0`; mit `on` Verhalten
      **unverändert**
- **DoD:** Ein Lauf mit `MEMORY_MODE=off` zeigt im stdout keinen Gedächtnis-Abruf; ein Lauf mit
  `on` verhält sich wie vorher. Default bleibt `on`, damit Produktion unberührt bleibt.

### A2 — Abhängigkeiten auflösen *(Kap. 4.9, 12.1)*
- [ ] **A2.1** Ist-Stand sichern: `pip freeze` archivieren (**vor** jeder Änderung)
- [ ] **A2.2** Konflikt klären: `requirements.txt` pinnt `openai>=1.6.0,<2.0.0`, installiert ist
      **2.14.0**. Pin anheben oder Paket downgraden — **Entscheidung begründen und festhalten**
- [ ] **A2.3** `langgraph` + `langchain-core`: aktuelle stabile Versionen auf PyPI prüfen,
      installieren, **exakt pinnen**
- [ ] **A2.4** `pydantic`-Verträglichkeit prüfen (installiert 2.12.4) — **der wahrscheinlichste
      Konfliktpunkt**, und er liegt im Messpfad
- **DoD:** `pip check` ohne Fehler; `requirements.txt` spiegelt die tatsächliche Umgebung.

### A3 — Smoke-Test und Einfrieren
- [ ] **A3.1** Ein **vollständiger** Monolith-Lauf (`full_correction`) auf einem bekannten Fall —
      läuft er unverändert durch?
- [ ] **A3.2** `pip freeze` der finalen Umgebung als Baseline-Artefakt archivieren
- [ ] **A3.3** **Falls A2 scheitert:** Rückfall auf expliziten Zustandsautomaten entscheiden und
      in Masterplan Kap. 5.1 vermerken — nicht still umschwenken
- **DoD:** Monolith läuft in der finalen Umgebung; Versionsliste archiviert; Protokolleintrag mit
  beiden `pip freeze`-Ständen.

---

# AP-B — Monolith-Baseline  ~1 Tag

**Abhängig von: AP-A vollständig.** *(Masterplan Kap. 8)*

### B1 — Regressionstest
- [ ] **B1.1** Einen bekannten Fall (Vorschlag: **I03**, Dichte) über den Monolith-Pfad fahren
- [ ] **B1.2** Ergebnis gegen `pt4-eval-results.json` stellen. **Abweichungen sind zu erwarten**
      (`MEMORY_MODE=off`, evtl. andere Bibliotheksversionen) — sie müssen **erklärt**, nicht
      wegerklärt werden
- **DoD:** Abweichungen benannt und ursächlich zugeordnet. Trennt Modell-/Umgebungseffekt vom
  späteren Architektureffekt.

### B2 — Der Baseline-Lauf
- [ ] **B2.1** Bedingungen setzen: `RULEBOOK_MODE=monolith`, `MEMORY_MODE=off`, HitL-Behandlung
      festgelegt und für beide Varianten gleich
- [ ] **B2.2** Alle **17 distinkten Fälle** (10 isoliert + 7 echte Mehrfehlerfälle; die
      kombinierten 01–03 sind Dubletten, Kap. 13.1)
- [ ] **B2.3** Protokoll je Lauf vollständig nach Kap. 17
- **DoD:** Ergebnisdatei **mit** Lauf-Metadaten; Protokolleintrag mit Rohdatenpfad. Das ist die
  Zahl, gegen die alles Weitere verglichen wird.

### B3 — Artefakte archivieren *(Kap. 8.2)*
- [ ] **B3.1** `llm-validation-fix-rules.md`: Hash **und** Kopie
- [ ] **B3.2** Prompt-Aufbau zum Messzeitpunkt
- [ ] **B3.3** Alle Umgebungswerte: `RULEBOOK_MODE`, `MEMORY_MODE`, `SP_ARCHITECTURE_MODE`,
      `HUMAN_IN_THE_LOOP`, `AZURE_OPENAI_DEPLOYMENT`, API-Version, Temperatur
- **DoD:** Ein Dritter könnte den Lauf allein aus dem Archiv rekonstruieren.

---

# AP-C — Schalter und Gerüst  ~0,5 Tage

*(Masterplan Kap. 6, 10, 12.3)*

- [ ] **C1** `SP_ARCHITECTURE_MODE` in `agent_config.py`, Default `"monolith"`
- [ ] **C2** Verzweigung in `sp_agent.py:626`, **eine** Zeile am Methodenanfang
- [ ] **C3** `GRAPH_ENABLED_PIPELINES = {"full_correction", "correction_from_validation"}`
- [ ] **C4** Verzeichnis `app/tools/smart-planning/graph/` + `graph_state.py` (Kap. 10)
- **DoD:** Monolith verhält sich **unverändert** (Regressionstest B1 erneut grün);
  `SP_ARCHITECTURE_MODE=graph` gibt eine saubere „noch nicht implementiert"-Meldung statt eines
  Absturzes.

---

# AP-D — Knoten extrahieren  ~4–5 Tage

**Muster überall gleich** *(Kap. 12.2)*: neue aufrufbare Funktion, `main()` ruft sie auf,
**CLI-Verhalten unverändert**. Reihenfolge nach Aufwand, nicht nach Knotennummer.

| | Teilpaket | Datei | Aufwand |
|---|---|---|---|
| ☐ | **D1** Knoten 6 Technische Prüfung | `validate_correction_schema_llm.py` | klein — **Muster festigen** |
| ☐ | **D2** Knoten 5 Korrekturgenerierung | `generate_correction_llm.py` | mittel — **der wichtigste** |
| ☐ | **D3** Knoten 7 Anwendung & Re-Validierung | `apply_correction.py`, `update_snapshot.py`, `validate_snapshot.py` | mittel — **erzeugt `errors_after`** |
| ☐ | **D4** Knoten 4 Regelzuordnung + Knoten 8 Ergebnisbewertung | Neucode in `graph/nodes/` | klein — keine Extraktion |
| ☐ | **D5** Knoten 9 Antwortformulierung | `generate_audit_report.py` | klein |
| ☐ | **D6** Knoten 2 Fehlerklassifikation | `identify_error_llm.py` | mittel — inkl. MVP-Entscheidung Kartenauswahl |
| ☐ | **D7** Knoten 3 Kontextsuche | `identify_snapshot.py` | **gross — ~300 Zeilen Ablaufsteuerung in `main()`** |

**DoD je Teilpaket:** Die Funktion ist direkt importierbar **und** das Skript verhält sich über
CLI unverändert (Argumente, stdout, Exit-Codes, erzeugte Dateien). Für D3 zusätzlich: derselbe
Suchlauf liefert dasselbe `last_search_results.json` wie vorher.

> **D3 ist der Risikoposten des ganzen Blocks.** Wenn er sich als zu verwoben erweist: Knoten 3
> und 4 zusammenlegen (Kap. 9.1) — die Entscheidung gehört in AP-F, nicht hierher.

---

# AP-E — Graph verdrahten  ~2 Tage

*(Masterplan Kap. 11, 12.3, 12.4)*

- [ ] **E1** `correction_graph.py`: neun Knoten registrieren, sequenzielle Kanten 1→…→6
- [ ] **E2** Bedingte Kante **A** nach Knoten 6 (Schema gültig? Retries übrig?)
- [ ] **E3** Bedingte Kante **B** nach Knoten 8 — der Router liest **nur** `decision.action`,
      enthält **keine** Fachlogik; inkl. Rückkante 8→2
- [ ] **E4** `_execute_pipeline_graph()` in `sp_agent.py` — **identische Rückgabestruktur** wie
      `_execute_pipeline()` (`success`, `final_validation`, `total_iterations`, `completed_steps`)
- [ ] **E5** Trace-Persistenz: vollständiger `GraphState` je Lauf als JSON in die
      Iterationsordner-Struktur (Kap. 12.4)
- [ ] **E6** `get_graph().draw_mermaid()` einmal ausführen, Ausgabe für Kapitel 4 sichern
- **DoD:** Ein bekannter Fall läuft im `graph`-Modus End-to-End durch; Orchestrator und Eval-Skripte
  merken **nichts** von der Umstellung.

---

# AP-F — Vertikaler Durchstich  ~2 Tage

**Abhängig von: AP-E und AP-B.** *(Masterplan Kap. 20, 9.1, 7.3)*
Der ehrliche Entscheidungspunkt — hier wird bestätigt oder korrigiert, was bisher Hypothese war.

- [ ] **F1** Ein bekannter Einzelfehler-Fall durch **beide** Varianten, gegenübergestellt
- [ ] **F2** Lesbare Trace-Kette gebaut (Kap. 12.5) — Debugging-Werkzeug **und**
      Kapitel-7-Abbildung
- [ ] **F3** **Entscheidung Knotenzahl:** bleibt es bei neun? (Kap. 9.1) → **im Masterplan
      vermerken**, nicht still treffen
- [ ] **F4** **Entscheidung Provenienz-Granularität:** reicht Kartenebene, oder braucht es
      Regelebene? (Kap. 7.3) → ebenfalls vermerken
- [ ] **F5** **Messinstrument testen:** das Experten-Raster an **diesem einen Fall** durchspielen.
      Ist das variantenneutrale Format wirklich neutral? Werden die Fragen verstanden?
- **DoD:** Gegenüberstellung dokumentiert; beide Entscheidungen im Masterplan festgehalten;
  Raster einmal in der Praxis erprobt.

> **F5 ist Regel 6 in der Praxis.** In PT4 hat ein defekter Messterm (`value_grounded`) eine ganze
> Fehlerklasse verdorben. Eine Stunde hier spart später eine Woche.

---

# AP-G — Pilotphase und Einfrieren  ~3 Tage *(kürzbar)*

*(Masterplan Kap. 8.3)*

- [ ] **G1** **Pilotfälle bauen** — eigene Snapshots mit **anderen Entitäten** als der
      Messkatalog. Nicht nur andere Snapshot-IDs: auch andere `articleId`/`demandId`, weil das
      Gedächtnis objektbezogen ist
- [ ] **G2** Nachweis führen, dass **keine Überschneidung** mit den 17 Messfällen besteht
- [ ] **G3** Pilotläufe fahren (~10), Regeldefekte über den Trace lokalisieren, Regelkarten
      präzisieren
- [ ] **G4** Je Änderung protokollieren als **`Status: pilot`**: welche Regel, **warum**,
      **auslösender Trace**, Hash vorher/nachher
- [ ] **G5** ██ **EINFRIEREN** ██ — Regelwerk, Graphstruktur, Prompts, Parameter, Umgebung.
      Hashes festhalten
- **DoD:** Einfrierzeitpunkt mit allen Hashes dokumentiert. **Ab hier ist jede Änderung eine
  Nachmessung.**

> **Kürzbar auf ~1 Tag**, indem G3 auf zwei bis drei Fälle reduziert wird. **Nicht kürzbar ist
> G5** — ohne dokumentiertes Einfrieren ist die anschliessende Messung wertlos.

---

# AP-H — Messen  ~4 Tage

**Abhängig von: AP-G eingefroren.** *(Masterplan Kap. 13, 17)*

- [ ] **H1** **HitL-Blocker lösen:** `open_proposal_blocking()` bricht mit Exit-Code 3 ab, solange
      ein Vorschlag offen ist — der Wiederholungs-Wrapper läuft sonst ab Durchgang 2 ins Leere.
      Lösung für **beide** Varianten identisch und dokumentiert
- [ ] **H2** Wiederholungs-Wrapper für UF2: derselbe Fall 3–5×, Vergleich der **fachlichen**
      Korrekturwerte, nicht der Formulierung
- [ ] **H3** Grenzfälle ergänzen — Fälle, bei denen „keine Korrektur erzwingen, sondern
      Unsicherheit ausweisen" die **richtige** Antwort ist
- [ ] **H4** Randomisierter A/B-Runner: mischt (Fall × Variante), protokolliert nach Kap. 17
- [ ] **H5** Vollständige Läufe: beide Kataloge × beide Varianten × Wiederholungen + Grenzfälle
- **DoD:** Rohdaten vollständig nach Kap. 17 — je Lauf Zeitstempel, Variante, Fall-ID, Modell,
  Parameter, alle Modus-Schalter, Prompt (oder Hash), Antwort, Trace, Rohdatenpfad.

---

# AP-I — Auswerten und schreiben  ~3 Tage

*(Masterplan Kap. 15, 18, 19)*

- [ ] **I1** Halluzinationen kategorisieren — vier Kategorien, je Fall, aus L08 abgeleitet
- [ ] **I2** Tabellen je Dimension: Monolith vs. Graph, aufgeschlüsselt Standard/Komplex
- [ ] **I3** Validitäts-Checkliste (Kap. 19) durchgehen — **alle** Punkte, auch die
      unangenehmen
- [ ] **I4** **Optimierungsschleife demonstrieren** an 1–2 Fällen, als **Nachmessung**
      gekennzeichnet — der praktische Beitrag F9
- [ ] **I5** Kapitel 7 (Ergebnisse), 8 (Diskussion), 9 (Fazit) schreiben — Einstieg über das
      **Kapitelregister** im Protokoll, nicht über die Chronologie
- **DoD:** Jede Zahl in Kapitel 7 ist bis zu ihrem Lauf und ihren Rohdaten zurückverfolgbar.

---

# AP-X — Menschen  *(läuft parallel, nicht durch Fleiss beschleunigbar)*

*(Masterplan Kap. 16)*

- [ ] **X1** Experten-Bewertungsraster: fachliche Korrektheit, Regelkonformität,
      Nachvollziehbarkeit, technische Verwendbarkeit, Folgefehler-Risiko
- [ ] **X2** **Variantenneutrales Präsentationsformat** — nur das fachliche Endergebnis, **nie**
      der Rohtrace (der verrät sofort die Variante)
- [ ] **X3** SUS/UEQ-Fragebögen vorbereiten — dazu die offene Entscheidung: Vollerhebung oder nur
      die UEQ-Skalen *Durchschaubarkeit* und *Steuerbarkeit* auf die Ausgaben
- [ ] **X4** Termine 2–4 Experten und ≥5 Teilnehmende
- **DoD:** Raster in AP-F/F5 einmal erprobt; Termine stehen.

---

## Offene Entscheidungen — hier sichtbar halten

| Entscheidung | Fällig in | Referenz |
|---|---|---|
| Knotenzahl bindend festlegen | **AP-F** (F3) | Kap. 9.1 |
| Provenienz: Kartenebene oder Regelebene | **AP-F** (F4) | Kap. 7.3 |
| SUS/UEQ: Vollerhebung oder nur zwei UEQ-Skalen | **AP-X** (X3) | Kap. 16.2 |
| Knoten 2: Kartenauswahl auftrennen oder MVP | **AP-D** (D6) | Kap. 9 |
| Rückfall Zustandsautomat, falls Installation scheitert | **AP-A** (A3.3) | Kap. 5.1 |
| Umfang der Pilotphase | **AP-G** (G3) | Kap. 8.3 |
