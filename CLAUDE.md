# Claude Code Project Instructions

Bitte berücksichtige diese Projekt-Instructions immer:

---
description: Global project instructions for the Bachelor thesis (graph vs. monolith). Always loaded.
applyTo: "**"
---

# Bachelorarbeit — Agent Instructions

## Worum es jetzt geht

**Titel:** Graph-basierte Systemarchitektur vs. monolithische Systemprompt-Struktur — eine
empirische Evaluation von Halluzinationsrate, Nachvollziehbarkeit und Robustheit in
LLM-gestützten Validierungs- und Korrektursystemen im Produktionsumfeld.

**Forschungsfrage (wörtlich aus dem Exposé):**
> Inwiefern unterscheidet sich eine graph-basierte Systemarchitektur von einer monolithischen
> Systemprompt-Struktur hinsichtlich Halluzinationsrate, Nachvollziehbarkeit und Robustheit
> bei der automatisierten Validierung und Korrektur strukturierter JSON-Daten in einem
> produktionskritischen Umfeld?

Die Frage ist **komparativ**. Sie wird nicht dadurch beantwortet, dass ein gutes Graph-System
entsteht, sondern dadurch, dass **zwei Varianten unter identischen Bedingungen** gegeneinander
gemessen werden — und ehrlich berichtet wird, wo welche gewinnt. **Es gibt kein erwünschtes
Ergebnis.** „Der Graph gewinnt *wo*" ist wissenschaftlich stärker als „der Graph gewinnt".

Die Leitfrage bei jeder Entscheidung lautet: *Macht das den Vergleich sauberer oder
aussagekräftiger?* Ein beeindruckendes Feature, das nur eine Variante hat, ist wertlos.

## Zwei Projekte, ein Repository

Dieses Repository trägt **zwei getrennte Vorhaben**:

* **PT4** (Praxisprojekt, **abgeschlossen**) — Human-in-the-Loop, Confidence, MCP, Dashboard,
  Memory. Liefert die Baseline und den Kontext. Referenz: `docs/PT4_PLAN.md`,
  `docs/PROJECT_LOG.md` (beide geschlossen).
* **Bachelorarbeit** (aktuell) — der Architekturvergleich.

**Sie müssen sauber getrennt bleiben** — auch wegen des Eigenplagiats-Risikos. PT4-Inhalte
gehören nicht in den Architekturvergleich; sie dürfen als „paralleler Ausbaupfad" in einem
Nebensatz vorkommen.

Es gibt genau **drei Brücken** von PT4 in die Arbeit:
1. Die Fehlerinjektion als **Ground-Truth-Methode** (`app/eval/build_test_catalog.py`).
2. Der `RULEBOOK_MODE`-Schalter als **Teilbaustein** (Knoten 4) und Pilotergebnis — **nicht**
   als „die Graph-Architektur".
3. Die **deterministische technische Prüfung** (belegbar vs. erfunden).

## Referenzdokumente — vor jeder Arbeitseinheit lesen

1. **`docs/Graph-Architektur-Masterplan_fable.md`** — die verbindliche Bau-Referenz.
   Kapitel 23 ist die Master-Checkliste; sie definiert die Reihenfolge.
2. **`docs/BACHELORARBEIT_UMSETZUNGSPLAN.md`** — Methodik, Messvorschriften, Fallstricke.
3. **`docs/03_Expose-extern/`** — das eingereichte Exposé. Bei Widerspruch zwischen Plan und
   Exposé gilt das Exposé, oder der Widerspruch wird ausdrücklich aufgelöst und dokumentiert.

Kein Scope erfinden, der dort nicht steht.

## Harte Regeln

1. **Koexistenz statt Ersetzen.** Der Monolith-Pfad wird **nicht** gelöscht, umbenannt oder
   umgebaut. Er bleibt lauffähig und ist die Standardvariante. Umgeschaltet wird über
   `SP_ARCHITECTURE_MODE` (Default `"monolith"`), einziger Verzweigungspunkt ist
   `SPAgent.execute_pipeline()`. Die Runtime-Skripte werden **additiv** um Funktionen
   erweitert, ihr CLI-Verhalten (Argumente, stdout, Exit-Codes, erzeugte Dateien) bleibt
   unverändert.
2. **Keine Strohmann-Baseline.** Die Baseline ist der **reale** Ist-Zustand, nicht eine
   künstlich verschlechterte Fassung. Der Unterschied liegt in gebündeltem Prompt-Kontext
   und fehlendem explizitem Zwischenzustand — nicht in der Anzahl der Schritte (der
   Ist-Zustand hat bereits sieben).
3. **Kontrollbedingungen sind heilig.** Modell, Modellparameter, Kontextextraktion und
   Testfälle sind zwischen beiden Varianten **identisch**. Jede Abweichung ist ein
   konfundierender Faktor. Unterscheiden darf sich **nur** die interne Verarbeitungs-
   architektur des Smart-Planning-Agenten; Orchestrator, RAG- und Chat-Agent bleiben gleich.
4. **Nie Messergebnisse erfinden.** Konstruierter **Input** ist zulässig und gängige Praxis
   (Fehlerinjektion). Konstruierte **Ergebnisse, Bewertungen oder Experten-Urteile** sind es
   nie. Wenn eine Zahl nicht gemessen wurde, wird sie nicht genannt.
5. **Erst Protokoll, dann messen.** Messvorschrift und Kategorien stehen vor dem ersten Lauf
   fest. Nach dem Sehen der Ergebnisse wird nichts nachjustiert. Fällt doch etwas auf, wird
   es als **Nachmessung** ausgewiesen.
6. **Prüfe das Messinstrument, bevor du misst.** In PT4 zeigte ein Metrik-Term
   (`value_grounded`) für eine ganze Fehlerklasse verkehrt herum — gemessen wurde ein Defekt
   des Instruments, nicht das System. Vor jeder Messung prüfen, ob der Ansatz für **alle**
   Fehlerklassen das Richtige misst.
7. **Rohdaten vollständig ablegen.** Je Lauf: Zeitstempel, Variante, Fall-ID, Modell +
   Version, Parameter, vollständiger Prompt (oder Hash), vollständige Antwort, Trace. Ohne
   diese Protokolle ist keine Aussage belastbar; sie sind der Anhang der Arbeit.
8. **Unterscheide klar** in jeder Erklärung: implementiert / teilweise / geplant /
   konzeptionell / noch nicht. Nichts als vorhanden ausgeben, was es nicht ist.
9. **Fehlt eine Information, benenne die Annahme ausdrücklich** — nicht still raten.
10. **Nach jeder abgeschlossenen Einheit** einen Eintrag in `docs/BA_PROJECT_LOG.md` anhängen
    (Format oben in der Datei).

## Bekannte Fallen

* **`RULEBOOK_MODE` steht im Code auf `"cards"`, nicht auf `"monolith"`**
  (`app/core/agent_config.py`). Ein Baseline-Lauf ohne ausdrückliches
  `RULEBOOK_MODE=monolith` misst **nicht** den Monolithen. Das ist laut Masterplan (Kap. 6.1)
  der wichtigste Einzelpunkt — bei jedem Baseline-Lauf ausdrücklich setzen und im Protokoll
  festhalten.
* **`langgraph` ist nicht installiert.** Die Framework-Entscheidung (Masterplan 3.1) ist
  getroffen, aber noch nicht umgesetzt. Der zulässige Rückfall ist ein expliziter
  Zustandsautomat in Python — dann aber im Methodenteil so benennen und begründen.
* **Das Modell-Deployment steht auf `gpt-4.1`** und deckt sich damit mit dem Exposé. Nicht
  unbemerkt ändern; jede Änderung macht frühere Messungen unvergleichbar.
* **Blindung bricht am Format.** Die Graph-Variante erzeugt strukturell andere Ausgaben. Den
  Experten wird nur das **fachliche Endergebnis** in einem variantenneutralen Format
  vorgelegt, nie der Rohtrace.

## Was NICHT Gegenstand der Arbeit ist

Human-in-the-Loop / Review Board, das MCP-Toolset und der E-Mail-Agent, das
Management-Dashboard, das episodische Memory, das Confidence-Scoring als Governance-Feature.
Diese PT4-Bestandteile bleiben funktionsfähig, gehören aber nicht in den Vergleich.

Ebenfalls nicht: Grundlagenforschung an LLMs, die Frage nach dem besten Foundation Model,
reine Prompt-Wortlaut-Optimierung.

## Daten und Sicherheit

`app/.env` enthält Klartext-Geheimnisse. **Niemals Werte ausgeben, niemals `.env` committen.**
Testläufe ausschliesslich auf der Smart-Planning-Testinstanz, nie produktiv. Das System darf
keine Snapshots löschen. Nur anonymisierte oder freigegebene Daten verwenden.

## Berichten — kurz halten

Beim Melden einer fertigen Aufgabe **keine vollständigen Diffs, keine ganzen Dateien**:
1. Ein Satz: was geändert wurde + welche Datei(en), nur Namen.
2. Das funktionale Ergebnis, das belegt, dass es wirkt.
3. Bestätigung, dass nur die vereinbarten Dateien angefasst wurden.

Einen Code-Ausschnitt nur, wenn ausdrücklich verlangt — oder wenn du BLOCKIERT bist und die
konkreten Zeilen zeigen musst, um das Problem zu erklären.
