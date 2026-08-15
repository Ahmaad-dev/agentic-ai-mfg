# Exposé — Bachelorarbeit (distilled / engineering view)

> **Distillation of** `260322_BSE-Exposé_se231310_Ahmad-Alsayad.pdf` (Version 2).
> The PDF is the formal, submittable exposé. This `.md` is a structured, workable
> version for engineering planning: scope, research questions, methodology, and a
> feature/task breakdown. Key domain terms kept in German where they are the term of art.

---

## Metadata

| Field | Value |
|---|---|
| **Titel** | Graph-basierte Systemarchitektur vs. monolithische Systemprompt-Struktur: Eine empirische Evaluation von Halluzinationsrate, Nachvollziehbarkeit und Robustheit in LLM-gestützten Validierungs- und Korrektursystemen im Produktionsumfeld |
| **Studierender** | Ahmad Alsayad (Matr. 52318601) |
| **Betreuer** | Dipl.-Ing. Michael Macher, BSc, MSc |
| **Studiengang** | Smart Engineering, FH St. Pölten |
| **Industriekontext** | CANCOM Austria AG — Digital Makers (duales Studium) |
| **Modell (fix in beiden Varianten)** | Azure OpenAI GPT-4.1 |
| **Abgabe** | 15. September (Vollfassung an Betreuer: 15. August) |

---

## TL;DR

Empirischer, kontrollierter Vergleich **zweier Prompt-/Systemarchitekturen** für dasselbe
reale LLM-System (Smart-Planning JSON-Snapshot-Korrektur):

- **Baseline:** monolithischer Systemprompt (aktuell 425 Zeilen / 20.284 Zeichen).
- **Vergleichsvariante:** graph-basierte Systemarchitektur (Verarbeitungsprozess als
  gerichteter Graph aus diskreten Knoten).

Gemessen entlang **drei Dimensionen**: **Halluzinationsrate**, **Nachvollziehbarkeit**,
**Robustheit**. Modell, Parameter und Testfälle bleiben konstant, damit Unterschiede auf
die *Struktur* zurückführbar sind.

**Dreifacher Beitrag:** empirisch (Architekturvergleich) · methodisch (Evaluierungsrahmen
für strukturierte LLM-Ausgaben) · praktisch (Prototyp + Designrichtlinien).

---

## Kontext: bestehendes System

**Smart Planning** ist ein Integrationslayer zwischen ERP und Shopfloor. Es liefert
**JSON-Snapshots** mit **70.000–200.000+ Einträgen** (Produkte, Maschinen-IDs, Produkttypen,
Mitarbeiterverfügbarkeiten/-qualifikationen, Prozessparameter). Die eigene Validierungs-Engine
*erkennt* Fehler, kann sie aber nicht *korrigieren* → bisher manuell, **2–6 h pro Snapshot**.

Das im Praxisprojekt gebaute **Vier-Agenten-System** (Azure, Terraform-IaC) automatisiert das:

| Agent | Rolle |
|---|---|
| **Orchestrator** | Primäre User-Schnittstelle; kontextsensitives Routing via LLM-Call (keine if-then-Regeln); plant mehrstufige Korrekturprozesse |
| **RAG-Agent** | Azure AI Search auf Wissensbasis; Korrekturregeln **in natürlicher Sprache** (von Fachexperten pflegbar) |
| **Smart-Planning-Agent** | Operative Kernkomponente; **10 Tools + 4 Pipelines**; einziger Agent, der direkt an JSON arbeitet; Kontextextraktion 1.000–4.000 Zeilen (Snapshot zu groß fürs LLM) |
| **Chat-Agent** | Allgemeinwissen; keine Retrieval-/Systemintegration |

**Korrektur-Pipeline (iterativ):** abholen → validieren → LLM-Fehleranalyse → Korrekturvorschlag
→ anwenden → re-validieren → wiederholen bis „valide" oder Max-Iterationen. Jede Änderung
protokolliert → revisionssicherer Audit-Report. Ergebnis: **1–3 min** statt 2–6 h (**95–99 %**).

---

## Problemstellung (die 3 Dimensionen)

1. **Halluzinationen bei komplexen Validierungsaufgaben** — bei vielen verschachtelten
   Abhängigkeiten / gleichzeitigen Fehlern steigt die Rate fachlich falscher, aber syntaktisch
   valider Korrekturen. Kritisch: solche Fehler können unbemerkt ins ERP wandern. Keine
   automatisierte Ground-Truth → Bewertung braucht Domänenexperten.
2. **Fehlende Nachvollziehbarkeit** — bei Fehlern kein rekonstruierbarer Entscheidungspfad;
   Prompt-Anpassung = „Blindflug" mit Nebeneffekten (Robustheit ist kein Zustand, sondern
   muss bei jedem Eingriff neu erprobt werden).
3. **Mangelnde Robustheit** — variierende/abweichende Eingaben → instabiles Verhalten;
   identische Eingaben → mitunter unterschiedliche fachliche Korrekturen; Kaskadeneffekte.
   Zu trennen: *stochastische* Formulierungsvariabilität (unvermeidbar) vs. *inhaltliche*
   Instabilität (in Produktion inakzeptabel — Zielgröße der Arbeit).

**Wissenschaftliche Lücke:** Vorteile graph-basierter Reasoning-Strukturen sind an abstrakten
Benchmarks gezeigt (Besta 2024, Wen 2024), aber **nicht** empirisch an einem
produktionskritischen System mit **strukturierten JSON-Ausgaben** und Revisionssicherheit.
Zusätzlich fehlt ein **Evaluierungsansatz jenseits klassischer Textmetriken**.

---

## Forschungsfragen

**Hauptfrage:** Inwiefern unterscheidet sich eine graph-basierte Systemarchitektur von einer
monolithischen Systemprompt-Struktur hinsichtlich **Halluzinationsrate, Nachvollziehbarkeit
und Robustheit** bei automatisierter Validierung/Korrektur strukturierter JSON-Daten im
produktionskritischen Umfeld?

- **UF1 — Halluzination:** Einfluss der Modularisierung in graph-basierte Workflows auf die
  Halluzinationsreduktion — *und* wie dieser Effekt überhaupt messbar wird (Brücke zum
  methodischen Beitrag).
- **UF2 — Konsistenz/Robustheit:** Führt die Zerlegung in diskrete, graph-modellierte Schritte
  zu konsistenteren Entscheidungen bei variierenden Eingaben / Grenzfällen? (Architekturbedingt
  vs. stochastisch trennen.)
- **UF3 — Debugging/Wartbarkeit:** Ermöglichen explizite Zwischenzustände + Entscheidungspunkte
  gezieltere Fehleranalyse und wartungsfreundlichere Weiterentwicklung bei iterativen
  Korrekturschleifen?

---

## Abgrenzung (Scope)

- ✅ Vergleich **genau zweier** Architekturen an **einem** Anwendungsfall (Smart-Planning
  JSON-Snapshots). Graph-Variante ist **Prototyp**, keine Produktivsetzung.
- ✅ „Graph-basierte Systemarchitektur" = strukturierte Modellierung von Daten, (Teil-)Prompts,
  Regeln, Beispielen, Kontext, Tool-Ausgaben, Zwischenergebnissen als **gerichteter Graph**
  (nicht nur einzelne Prompts).
- ❌ **Keine** LLM-Grundlagenforschung; **keine** Modellauswahl — GPT-4.1 bleibt fix.
- ❌ **Keine** reine Prompt-Optimierung (Formulierungen) — Fokus auf Struktur/Entscheidungsfluss.
- ❌ **Keine** vollständige Abdeckung aller Fehlerfälle — repräsentative Testfälle.
- RAGAS nur **ergänzend** für text-/RAG-Teilaspekte, kein alleiniger Maßstab.

---

## Methodik & Forschungsdesign

Empirisch-vergleichend; **praxisnahe Fallstudie mit experimentellen Elementen**.

1. **Baseline** (F1): monolithischen Prompt systematisch analysieren (gebündelte Aufgaben).
2. **Graph-Variante** (F2): Entscheidungs-/Verarbeitungslogik in Knoten zerlegen —
   *Eingabeanalyse · Fehlerklassifikation · Kontextsuche · Regelzuordnung · Korrekturgenerierung
   · Ergebnisbewertung*; Abhängigkeiten/Kontrollflüsse als Kanten. (Fundierung: Besta 2024 GoT,
   Wen 2024 MindMap, Ji 2023 Halluzination.)
3. **Testfallkatalog** (F3): Standardfälle (Einzelfehler, eindeutige Regel) + Komplexfälle
   (mehrere Fehler, verschachtelte Abhängigkeiten, widersprüchliche Feldinhalte).
4. **Kontrollierter Vergleich:** identische Eingaben, konstantes Modell + Parameter,
   randomisierte Ausführungsreihenfolge.

---

## Evaluierungsdesign

**Ergebnisqualität ≠ Prozessqualität** — beides wird bewertet. Drei Ebenen:

| Ebene | Was | Kennzahlen / Instrument |
|---|---|---|
| **Technisch** (F5) | JSON-Schema-, Referenz-, Pflichtfeldprüfung, Re-Validierung via SP-Engine | gültige/ungültige Korrekturen, neue Folgefehler, Korrekturiterationen, Wiederholungs-Variabilität |
| **Fachlich** (F6) | 2–4 Domänenexperten, **blind** (architektur-agnostisch), einheitliches Raster | fachliche Korrektheit, Regelkonformität, Nachvollziehbarkeit, Verwendbarkeit, Folgefehler-Risiko; protokolliert |
| **Nutzerseitig** (F7) | ≥5 Teilnehmende (inkl. außerhalb Projektteam) | **SUS** (Score), **UEQ** (Nachvollziehbarkeit/Effizienz/Verlässlichkeit); RAGAS ergänzend |

**Operationalisierung der Dimensionen**
- **Halluzinationsrate:** Anteil fachlich inkorrekter / nicht belegbarer / regelwidriger
  Korrekturen (unabhängig von Syntax). Typen: *fachlich · strukturell · Regel · Folgefehler*.
- **Nachvollziehbarkeit:** Ist der Weg Eingabe→Ausgabe rekonstruierbar (welcher Fehler, welche
  Regel, welche Daten, warum)? Gilt nur, wenn Begründung den **realen** Prozess abbildet.
- **Robustheit:** konsistente, fachlich angemessene Ausgaben bei variierenden/fehlerhaften
  Eingaben — inkl. transparentes Ausweisen von Unsicherheit statt erzwungener Korrektur.

**Entscheidungslogik:** Graph-Variante gilt als vorteilhaft, wenn sie weniger falsche/unbelegte
Korrekturen + weniger Folgefehler erzeugt, stabiler bei Wiederholung/Variation ist und als
nachvollziehbarer bewertet wird. Differenziertes Urteil erlaubt (besser / gleichwertig /
bedingt vorteilhaft) — kein vorab festgelegtes Ergebnis.

---

## Features & Tasks (Was die Arbeit liefern muss)

| # | Feature / Deliverable | Tasks | Beitrag |
|---|---|---|---|
| **F1** | Baseline-Analyse monolithischer Prompt | 425-Zeilen-Prompt in Concerns zerlegen; als Baseline dokumentieren | Empirisch |
| **F2** | Graph-basierte Architektur (Prototyp) | Knoten + Kanten designen/implementieren; in 4-Agenten-System integrieren; Kontrollfluss + Fehlerbehandlung | Praktisch |
| **F3** | Testfallkatalog | Standard- + Komplexfälle: leere Pflichtfelder, ungültige Referenzen, inkonsistente Relationen, falsche Korrekturwerte, unvollständige Snapshots | Empirisch |
| **F4** | Evaluierungsrahmen (strukturierte Ausgaben) | 3 Dimensionen operationalisieren; Halluzinationstypen klassifizieren; Metriken + Raster + Wiederholungstests kombinieren | Methodisch |
| **F5** | Technische Evaluierungsschicht | Schema/Referenz/Pflichtfeld-Checks, Re-Validierung, Kennzahlen erfassen | Empirisch |
| **F6** | Fachliche Evaluierungsschicht | Expertenrating (blind, Raster), Reviews protokollieren | Methodisch |
| **F7** | Nutzertests | SUS + UEQ (≥5 TN); RAGAS ergänzend | Methodisch |
| **F8** | Vergleich + Entscheidungslogik | Head-to-head über 3 Dimensionen; differenziertes Urteil; Grenzfälle/neue Schwächen benennen | Empirisch |
| **F9** | Designrichtlinien + Empfehlung | Guidelines für Prompt-/Graph-Architekturen; Empfehlung zur Weiterentwicklung des realen Systems | Praktisch |
| **F10** | Schriftliche Arbeit | Theorie · Konzept · Implementierung · Evaluation · Ergebnisse; Draft 15.08., Abgabe 15.09. | — |

---

## Erwartete Ergebnisse

- **Halluzination:** Vorteil der Graph-Variante v.a. bei **komplexen** Snapshots (getrennte,
  validierbare Teilaufgaben); bei einfachen Fällen **kein** relevanter Unterschied erwartet.
- **Nachvollziehbarkeit:** **deutlichster** Vorteil (explizite Zwischenzustände → gezielte
  Fehlerlokalisierung).
- **Robustheit:** **moderatere** Verbesserung (Entscheidungsraum je Schritt enger, nicht
  Eliminierung der Stochastik); mögliche neue Schwächen an Knotengrenzen als Erkenntnis.

---

## Zeitplan

| Phase | Zeitraum | Inhalt |
|---|---|---|
| 1 — Grundlagen & Konzeption | 14.06.–30.06. | Literatur (Halluzination, GoT, graph-Reasoning, LLM-Eval); Baseline-Analyse; erste Knoten definieren → dokumentierte Architekturkonzeption |
| 2 — Prototypische Implementierung | 01.07.–21.07. | Graph iterativ bauen (Knoten → Kontrollfluss, Fehlerbehandlung, Integration); erste technische Tests |
| 3 — Evaluation & Datenerhebung | 15.07.–04.08. | Beide Varianten mit Testfallkatalog; Outputs/Trace-Logs dokumentieren; Expertenreviews; ggf. Nutzertests |
| 4 — Auswertung & Verschriftlichung | 29.07.–15.08. | Auswertung entlang 3 Dimensionen; Vollfassung an Betreuer |
| 5 — Feedback & Finalisierung | 16.08.–15.09. | Feedback einarbeiten; QS, Formales, Abbildungen, Quellen; **Abgabe 15.09.** |

*(Phasen überlappen; Literatur, Implementierung, Testfälle, Evaluation, Schreiben laufen parallel.)*

---

## Benötigtes Equipment

Bestehendes 4-Agenten-System · Azure (OpenAI, AI Foundry, AI Search, Storage, Dev/Deploy-Umgebung)
· Python, Git, VS Code, Logging/Monitoring · anonymisierte/freigegebene ERP- & Smart-Planning-
Snapshot-Daten · Domänenexperten (Projekt/Kunde/AI) für die fachliche Bewertung.

---

## Literatur

- **Besta, M. et al. (2024).** Graph of Thoughts: Solving Elaborate Problems with LLMs.
  *AAAI 38(16)*, 17682–17690. https://doi.org/10.1609/aaai.v38i16.29720
- **Es, S. et al. (2024).** RAGAs: Automated Evaluation of Retrieval Augmented Generation.
  *EACL: System Demonstrations*, 150–158. https://doi.org/10.18653/v1/2024.eacl-demo.16
- **Ji, Z. et al. (2023).** Survey of Hallucination in Natural Language Generation.
  *ACM Computing Surveys 55(12)*, 1–38. https://doi.org/10.1145/3571730
- **Wen, Y., Wang, Z., & Sun, J. (2024).** MindMap: Knowledge Graph Prompting Sparks Graph of
  Thoughts in LLMs. *ACL (Vol. 1: Long Papers)*, 10370–10388.
  https://doi.org/10.18653/v1/2024.acl-long.558
