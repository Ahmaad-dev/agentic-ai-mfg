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
  Memory. Liefert die Baseline und den Kontext. Alles dazu liegt in `docs/04_PT4/`.
* **Bachelorarbeit** (aktuell) — der Architekturvergleich.

**Sie müssen sauber getrennt bleiben** — auch wegen des Eigenplagiats-Risikos. PT4-Inhalte
gehören nicht in den Architekturvergleich; sie dürfen als „paralleler Ausbaupfad" in einem
Nebensatz vorkommen.

Es gibt genau **drei Brücken** von PT4 in die Arbeit:
1. Die Fehlerinjektion als **Ground-Truth-Methode** — die *Methode*, nicht ein bestimmtes
   Skript. `app/eval/build_test_catalog.py` hat nur **drei aktive** Katalogeinträge und legt
   Snapshots live über die API an; die 10+10 Fälle auf Platte stammen aus PowerShell-Skripten
   mit Ground Truth in `expected-results.json`. **Zwei Mechanismen nebeneinander** — für neue
   Fälle einen wählen und durchhalten (Masterplan Kap. 14).
2. Das **Kartensystem** (`RULEBOOK_MODE=cards`, PT4/AP7.0) — es wird als **eigener
   Kontrollarm B** im Dreiarm-Design **mitgeführt** (Masterplan Kap. 7.1), nicht als „die
   Graph-Architektur". **Die Entwicklung wird nicht als BA-Leistung beansprucht**, die Werte
   werden unter den Kontrollbedingungen dieser Arbeit **neu erhoben**. PT4-Zahlen (−16 % Tokens)
   dürfen nie als BA-Ergebnis auftreten.
3. Die **deterministische technische Prüfung** (belegbar vs. erfunden).

## Referenzdokumente — vor jeder Arbeitseinheit lesen

1. **`docs/BA_MASTERPLAN.md`** — die **einzige verbindliche Referenz** für Methodik, Bau und
   Messung. Kapitel 23 ist die Master-Checkliste; sie definiert die Reihenfolge.
   *(Vereinigt seit 16.08.2026 die drei Vorgänger `BACHELORARBEIT_UMSETZUNGSPLAN.md`,
   `Graph-Architektur-Masterplan_fable.md` und `Doku-Claude-Chat.md`. Existieren diese noch,
   sind sie **überholt** und nicht mehr zu verwenden.)*
2. **Das Exposé** — ausschliesslich das PDF
   `docs/03_Expose-extern/260322_BSE-Exposé_se231310_Ahmad-Alsayad.pdf`. Bei Widerspruch zwischen
   Plan und Exposé gilt das Exposé, oder der Widerspruch wird ausdrücklich aufgelöst und
   dokumentiert. Es rendert nicht als Bild, ist aber mit `pypdf` direkt auslesbar (Masterplan Kap. 0).
   **`docs/03_Expose-extern/source-2/` wird ignoriert** — es stammt von einem Kollegen ohne
   Projektkenntnis und ist nicht massgeblich. `source-1/` (die vier zitierten Papers) bleibt.
3. **`docs/BA_PROJECT_LOG.md`** — was seit Projektstart passiert ist, inkl. aller Messläufe.
   **Zugleich das Rohmaterial, aus dem die Arbeit später verfasst wird** — siehe Regel 11.
4. **`docs/BA_ARBEITSPAKETE.md`** — die abhakbare Umsetzungsspur (AP-A bis AP-I plus AP-X),
   mit Teilpaketen, Abhängigkeiten, Aufwand und DoD je Paket. Bei Widerspruch zum Masterplan
   gilt der Masterplan.
5. **`docs/BA_LITERATUR.md`** — die 16 Kernquellen, sortiert nach Verwendungsstelle. Beim
   Begründen einer These hier nachsehen, statt eine Quelle zu erfinden.

Kein Scope erfinden, der dort nicht steht.

## Wissen aus PT4 — nachschlagen ja, übernehmen nein

`docs/04_PT4/` ist der Wissensspeicher des Praxisprojekts. Er ist **Sachwissen über das
bestehende System**, nicht **Scope für den Vergleich**. Diese Unterscheidung ist der ganze
Punkt: Kapitel 3 der Arbeit heisst „Das bestehende System" — dafür ist dieser Ordner das
Rohmaterial. Der Architekturvergleich dagegen darf aus PT4 nichts erben.

**Nachschlagen erwünscht:**
* `docs/04_PT4/AGENTEN_ARCHITEKTUR.md` — wie die vier Agenten zusammenarbeiten, was jeder von
  ihnen weiss, wie betreuter und automatischer Betrieb sich unterscheiden. **Das ist die
  Beschreibung der Baseline.** Wer sie nicht kennt, baut versehentlich einen Strohmann.
* `docs/04_PT4/ARCHITEKTURDIAGRAMME_PROJEKTBERICHT.md` — zitierfähige Architektur- und
  Ablaufdokumentation des realen Systems.
* `docs/04_PT4/AP7-0_rule_inventory.md` — die 936 Zeilen des Regelwerks, auf Karten aufgeteilt.
  Grundlage für Knoten 4 (Regelzuordnung) und für die Unterscheidung „gebündelter vs.
  selektiver Regelzugriff".
* `docs/04_PT4/BEFUNDE_UND_LEHREN.md` — sechs wiederkehrende Fehlermuster aus dem realen Betrieb.
  Darin der `value_grounded`-Fall: ein Messterm, der für eine ganze Fehlerklasse verkehrt
  herum zeigte. Genau die Falle, vor der Regel 6 warnt.
* `docs/04_PT4/KONFIDENZ.md` — relevant ist daraus **nur** `value_grounded`, die deterministische
  technische Prüfung (Brücke 3). Das Confidence-Scoring als Ganzes ist es nicht.

**Nicht in die Arbeit übernehmen** — das sind PT4-Nachweise und PT4-Scope:
`docs/04_PT4/PT4_BELEGE.md`, `AP1_AP7_APE_BELEGE.md`, `AP5_AP6_DOCUMENTATION.md`, `PT4_PLAN.md`
sowie `docs/04_PT4/work-environment/` (die archivierten Arbeitsdateien und das PT4-Protokoll).

**Faustregel:** Aus `docs/04_PT4/` darf **Wissen über das System** kommen, nie **Scope für den
Vergleich** — und keine Zahl. Wer eine PT4-Messung in der Arbeit verwenden will, muss sie
unter den Kontrollbedingungen dieser Arbeit **neu erheben**. Eine PT4-Zahl zu zitieren wäre
Eigenplagiat und ausserdem nicht vergleichbar, weil die Bedingungen andere waren.

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
3. **Kontrollbedingungen sind heilig.** Das Design hat **zwei Architekturen in drei
   Messbedingungen** (Masterplan Kap. 7.1): **A** Monolith-Pipeline + `RULEBOOK_MODE=monolith`
   (Ausgangszustand) · **B** Monolith-Pipeline + `cards` (**realer Ist-Zustand**, Kontrollarm;
   Bestandteil von **UF1 und UF2**; für UF2 ebenfalls **fünf Wiederholungen je Messfall**) ·
   **C** Graph + `cards`. Hauptvergleich ist **A gegen C**, und
   die Intervention ist ausdrücklich ein **Gesamtpaket** — ein Effekt darf **nicht** dem
   `GraphState` allein zugeschrieben werden.
   Modell, Parameter, Kontextextraktion, Testfälle, Umgebung und **`MEMORY_MODE=off`** sind in
   **allen drei** identisch. Alle drei laufen **nach demselben Einfrieren**.
4. **Nie Messergebnisse erfinden.** Konstruierter **Input** ist zulässig und gängige Praxis
   (Fehlerinjektion). Konstruierte **Ergebnisse, Bewertungen oder Experten-Urteile** sind es
   nie. Wenn eine Zahl nicht gemessen wurde, wird sie nicht genannt.
5. **Erst Protokoll, dann messen.** Messvorschrift und Kategorien stehen vor dem ersten Lauf
   fest. Nach dem Sehen der Ergebnisse wird nichts nachjustiert. Fällt doch etwas auf, wird
   es als **Nachmessung** ausgewiesen.
   **Vor** der Messung ist Optimieren dagegen erlaubt — das ist die **Pilotphase**
   (Masterplan Kap. 8.3). Zwei Bedingungen: Pilotfälle dürfen sich **nicht** mit Messfällen
   überschneiden (auch nicht in den Entitäten, wegen des Gedächtnisses), und Pilotläufe werden
   als `Status: pilot` protokolliert — sie sind **nie** Ergebnisse. Ab dem Einfrierzeitpunkt
   ändert sich an Regelwerk, Graphstruktur, Prompts und Parametern nichts mehr.
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
11. **Das Protokoll ist das Rohmaterial der Arbeit — schreibe jeden Eintrag für den Tag, an
    dem daraus ein Absatz wird.** Der Nutzer setzt jetzt um und verfasst die Bachelorarbeit
    später **aus diesen Einträgen**. Daraus folgen vier Pflichten je Eintrag:
    * **Stabile Kennung** `[BA-nnn]`, fortlaufend. Sie ändert sich nie, damit ein Kapitel sie
      zitieren kann.
    * **`Kapitelbezug:`** — welches Kapitel der Arbeit der Eintrag speist (K3–K9, auch mehrere,
      „—" bei reiner Hausarbeit). Danach **das Kapitelregister** oben in der Datei nachziehen;
      ein Register, das hinterherhinkt, ist schlimmer als keins.
    * **`Literatur:`** — die L-Nummern aus `docs/BA_LITERATUR.md`, wenn der Eintrag eine These
      stützt oder ihr widerspricht. Passt keine Quelle, ist das selbst ein Befund: dann
      **ausdrücklich vermerken**, dass eine Fundstelle fehlt.
    * **`Was NICHT funktioniert hat:`** — Sackgassen, verworfene Annahmen, Fehlschläge.
      **Das ist beim Schreiben mehr wert als das Gelungene**: Kapitel 8 und die Limitationen
      leben davon, und es lässt sich später nicht rekonstruieren.

    **Belege statt Behauptungen.** Nenne im Eintrag die konkrete Fundstelle (Datei + Zeile,
    Commit, Rohdatenpfad, Zeitstempel) — nicht „geprüft", sondern **womit**. Eine Zahl ohne
    Rohdatenpfad ist beim Schreiben wertlos, weil sich nichts nachrechnen lässt.

## Zwei Regeln für den Bau — sie schützen den Vergleich

Beide sind aus konkreten Fehlern entstanden (BA-021) und gelten dauerhaft.

**A — Keine Optimierung auf Geschwindigkeit zulasten der Vergleichbarkeit.**
Könnte eine Extraktion die **fachliche Semantik**, den **LLM-Input**, die
**Kontrollbedingungen** oder die **Messbarkeit** berühren, dann **zuerst stoppen, prüfen,
dokumentieren** — danach ändern. **Keine Annahmen über APIs, Artefakte oder Prozessverhalten:
am echten Code oder an einem echten Lauf verifizieren.**
Gleichwertigkeit wird **empirisch** belegt — SHA-256 des tatsächlichen Prompts, Hash des
injizierten Regeltexts, Exit-Codes und Artefakte des CLI-Pfads. **Nicht** über Näherungen wie
Tokenzahl oder Zeichenlänge.

**B — Ein neuer Graph-Knoten darf nicht einfach nur funktionieren.**
Nachzuweisen ist zweierlei: Er übernimmt **genau** die im Forschungsdesign vorgesehene
Verantwortung (Masterplan Kap. 9 und 9.0) — und er führt **keine zusätzliche Verbesserung ein,
die nur Bedingung C erhält**.
Jede Fähigkeit, die es nur in C gibt — ein behobener Fehler, ein besserer Retry, eine
zusätzliche Prüfung, ein geänderter Prompt — erscheint später als Architektureffekt, obwohl sie
keiner ist. **Ist es eine Reparatur, gehört sie in die gemeinsame Runtime, damit A, B und C sie
gleichermassen bekommen.** Genau das war beim fehlenden Re-Validierungs-Trigger der Fall.

## Bekannte Fallen

*Alle am 16.08.2026 gegen den Code verifiziert. Details im Masterplan Kap. 4.*

* **Das episodische Gedächtnis liegt im gemessenen Pfad und ist unbedingt aktiv.** Die
  **wichtigste Falle überhaupt.** `generate_correction_llm.py` holt frühere menschliche
  Entscheidungen in den Prompt (`:886-902`) und **überschreibt bei Objektgleichheit den
  Modellwert** (`:936-975`). Bestand: 20 Einträge, wachsend — und sie enthalten **objektgenau
  die Sollwerte des Testkatalogs**. Belegt: am 31.07. korrigierte ein Mensch um 20:25 den
  Fall I03 auf `1.017`; der Lauf um 23:01 traf ihn mit `memory_support: 1.0`.
  **Für Messläufe `MEMORY_MODE=off` in beiden Varianten** — sonst misst du das Gedächtnis,
  nicht die Architektur.
* **`RULEBOOK_MODE` steht im Code auf `"cards"`, nicht auf `"monolith"`**
  (`app/core/agent_config.py:40`). Ein Baseline-Lauf ohne ausdrückliches
  `RULEBOOK_MODE=monolith` misst **nicht** den Monolithen. Bei jedem Baseline-Lauf ausdrücklich
  setzen und im Protokoll festhalten. **Achtung:** der Kopfkommentar von
  `app/core/rulebook_loader.py:6` behauptet fälschlich `"monolith" (default)` — er widerspricht
  dem Code.
* **`HUMAN_IN_THE_LOOP` ist `true` als Default** und blockiert Wiederholungsläufe:
  `open_proposal_blocking()` bricht mit **Exit-Code 3** ab, solange für denselben Snapshot ein
  Vorschlag offen ist. Der UF2-Wiederholungs-Wrapper läuft sonst ab Durchgang 2 ins Leere.
* **`langgraph` ist nicht installiert.** Framework-Entscheidung steht (LangGraph, 16.08.), ist
  aber nicht umgesetzt. **Zuerst** den bestehenden Konflikt lösen: `requirements.txt` pinnt
  `openai>=1.6.0,<2.0.0`, installiert ist **2.14.0**. Zulässiger Rückfall bleibt ein expliziter
  Zustandsautomat — dann im Methodenteil so benennen und im Masterplan vermerken.
* **Das Modell-Deployment steht auf `gpt-4.1`**, API `2025-01-01-preview`, `temperature=0.3` —
  deckt sich mit dem Exposé. Nicht unbemerkt ändern; jede Änderung macht frühere Messungen
  unvergleichbar.
* **Bestehende Ergebnisdateien sind keine Rohdaten.** `pt4-eval-results.json` und
  `pt4-combined-results.json` enthalten weder Zeitstempel noch Modell, Temperatur oder Modus.
  Alle bisherigen Läufe entstanden unter `cards` (alle drei Eval-Skripte erzwingen ihn hart).
  **Kein Lauf im Repository entstand je unter `monolith`.**
* **Blindung bricht am Format.** Die Graph-Variante erzeugt strukturell andere Ausgaben. Den
  Experten wird nur das **fachliche Endergebnis** in einem variantenneutralen Format
  vorgelegt, nie der Rohtrace.
* **Knoten und Kanten sind NICHT vorgegeben.** Das Exposé nennt sechs Schritte mit dem Wort
  „**etwa**" — Beispiele, keine abschliessende Liste — und **kein Framework** (Volltextsuche
  nach LangGraph/LangChain: null Treffer). Anzahl und Schnitt sind eine **Designentscheidung
  der Arbeit** und in Kapitel 4 zu **begründen**, nicht als gegeben darzustellen. Der Plan
  entscheidet sich für **neun** Knoten nach dem Kriterium: *eine Grenze dort, wo ein eigener
  Fehlermodus beobachtbar wird* (Masterplan Kap. 5.2 und 9). Bindend wird die Zahl erst vor
  dem ersten gemessenen Graph-Lauf (Kap. 9.1).
* **„Graph" heisst hier ausschliesslich Programmablauf, nie Datenstruktur.** Snapshot, Regel-
  karten, Datenbank und Stammdaten werden **nicht** in Graphen umgewandelt — zum Graphen wird
  der Ablauf. Wer „welche Regel führte zu Entscheidung X" wissen will, braucht **Provenienz**
  (ein Feld im Zustand), keinen Regelwerk-Graphen. **Das Regelwerk ist eine Kontrollbedingung
  und wird nicht umgebaut** (Masterplan Kap. 3.4 und 7.3).
* **Neun Knoten sind nicht neun LLM-Aufrufe.** Drei Knoten rufen das Modell, genau wie der
  Monolith heute. Die Graph-Variante ist nicht „KI-lastiger" — sie macht sichtbar, was
  zwischen denselben Aufrufen passiert (Kap. 3.6).

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

## Berichten — immer sagen, was tatsächlich getan wurde

**In jeder Antwort steht, was konkret getan wurde** — nicht nur das Ergebnis oder die Empfehlung.
Welche Dateien angelegt oder geändert, welche Befehle und Prüfungen gelaufen sind, was dabei
herauskam. Auch, was **nicht** getan wurde: übersprungen, blockiert, bewusst nicht angefasst.
Und ausdrücklich unterscheiden zwischen **„geprüft, indem …"** und **„angenommen"**.

Grund: Der Nutzer setzt jetzt um und verfasst die Arbeit später aus `BA_PROJECT_LOG.md`. Eine
Antwort, die nur die Schlussfolgerung trägt, verliert den Schritt, der sie erzeugt hat — und
später ist nicht mehr unterscheidbar, was gemessen und was vermutet war.

**Trotzdem kurz halten** — keine vollständigen Diffs, keine ganzen Dateien:
1. Ein Satz je Änderung: was + welche Datei(en), nur Namen.
2. Das funktionale Ergebnis, das belegt, dass es wirkt.
3. Bestätigung, dass nur die vereinbarten Dateien angefasst wurden.

Einen Code-Ausschnitt nur, wenn ausdrücklich verlangt — oder wenn du BLOCKIERT bist und die
konkreten Zeilen zeigen musst, um das Problem zu erklären.
Hat eine Runde nichts verändert, sag auch das.
