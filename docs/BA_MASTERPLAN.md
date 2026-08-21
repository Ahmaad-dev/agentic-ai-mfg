# Bachelorarbeit — Masterplan

**Graph-basierte Systemarchitektur vs. monolithische Systemprompt-Struktur.**
Eine empirische Evaluation von Halluzinationsrate, Nachvollziehbarkeit und Robustheit in
LLM-gestützten Validierungs- und Korrektursystemen im Produktionsumfeld.

**Autor:** Ahmad Alsayad (Matr. 52318601) · **Betreuer:** Dipl.-Ing. Michael Macher, BSc, MSc
**Studiengang:** Smart Engineering, FH St. Pölten · **Industriekontext:** CANCOM Austria AG
**Stand dieses Dokuments:** 2026-08-16

---

> **Was dieses Dokument ist.** Die **einzige verbindliche Referenz** für den praktischen und
> empirischen Teil der Arbeit. Es ersetzt und vereinigt drei Vorgänger:
> `BACHELORARBEIT_UMSETZUNGSPLAN.md` (14.07., Methodik), `Graph-Architektur-Masterplan_fable.md`
> (02.08., Bau-Referenz) und `Doku-Claude-Chat.md` (Arbeitsweise und Risikoeinordnung).
> Jede Ist-Zustands-Aussage wurde am **2026-08-16 direkt gegen den Code geprüft** — die drei
> Vorgänger beschrieben in fast jeder Ortsangabe einen überholten Stand.
>
> **Bei Widerspruch zwischen diesem Dokument und dem Exposé gilt das Exposé** — oder der
> Widerspruch wird ausdrücklich aufgelöst und hier dokumentiert.
>
> **Das Exposé ist ausschliesslich das PDF:**
> `docs/03_Expose-extern/260322_BSE-Exposé_se231310_Ahmad-Alsayad.pdf` (20 Seiten).
> Es lässt sich nicht als Bild rendern (kein poppler installiert), aber der Text ist direkt
> auslesbar — `pypdf` ist im Projekt vorhanden:
> ```python
> from pypdf import PdfReader
> t = "\n".join(p.extract_text() or "" for p in PdfReader(PFAD).pages)   # ~62.000 Zeichen
> ```
> **Nicht** aus der Zusammenfassung im verworfenen Kollegen-Ordner zitieren (siehe Kap. 5.2).

---

## 0. Wie du dieses Dokument benutzt

Von oben nach unten abarbeitbar. Jeder Abschnitt liefert entweder **(a)** eine geprüfte Tatsache,
**(b)** eine fixierte Entscheidung oder **(c)** einen konkreten Bauauftrag.
**Kapitel 23 ist die Master-Checkliste** — wenn du nur eine Sache offen hältst, ist es die.

**Die eine Rahmenbedingung, die alles andere prägt:** Das bestehende monolithische System wird
**nicht ersetzt, nicht gelöscht, nicht umgebaut**. Es bleibt lauffähig und Standardvariante. Es
entsteht ein **Schalter**. Beide Varianten müssen danach mit identischen Eingaben gegeneinander
gefahren werden können. Dieses Prinzip zieht sich durch jede Entscheidung hier.

---

## 1. Die Forschungsfrage und was sie verlangt

> Inwiefern unterscheidet sich eine graph-basierte Systemarchitektur von einer monolithischen
> Systemprompt-Struktur hinsichtlich Halluzinationsrate, Nachvollziehbarkeit und Robustheit bei
> der automatisierten Validierung und Korrektur strukturierter JSON-Daten in einem
> produktionskritischen Umfeld?

Die Frage ist **komparativ**. Sie wird nicht dadurch gewonnen, dass ein gutes Graph-System
entsteht, sondern dadurch, dass **zwei Varianten unter identischen Bedingungen** gegeneinander
gemessen werden — und ehrlich berichtet wird, wo welche gewinnt.

**Es gibt kein erwünschtes Ergebnis.** „Der Graph gewinnt *wo*" ist wissenschaftlich stärker als
„der Graph gewinnt". Die graph-basierte Variante wird nicht gebaut, **weil** sie besser ist,
sondern **um zu prüfen, ob** sie besser ist. Diese Haltung muss in jeder Phase spürbar bleiben;
ein Gutachter achtet genau darauf.

Die Leitfrage bei jeder Entscheidung: *Macht das den Vergleich sauberer oder aussagekräftiger?*
Ein beeindruckendes Feature, das nur eine Variante hat, ist wertlos.

**Die drei Unterfragen:**

| | Frage | Bauauftrag | Messauftrag |
|---|---|---|---|
| **UF1** | Reduziert Modularisierung Halluzinationen — und wie wird das überhaupt messbar? | Graph-Variante | Halluzinationsrate, vier Kategorien (Kap. 15.1). **UF1 ist zugleich der methodische Beitrag**: die Entwicklung des Messansatzes ist selbst ein Ergebnis |
| **UF2** | Führt die Zerlegung zu konsistenteren Entscheidungen bei variierenden Eingaben und Grenzfällen? | Wiederholungs-Wrapper, Grenzfälle | Streuung über Wiederholungen; Grenzfallverhalten (Kap. 15.3) |
| **UF3** | Ermöglichen explizite Zwischenzustände gezieltere Fehleranalyse in iterativen Schleifen? | `trace`-Feld im `GraphState` | qualitativ: Fallgegenüberstellungen + Expertenrating (Kap. 15.2) |

---

## 2. Zwei Projekte, eine Codebasis

Dieses Repository trägt zwei getrennte Vorhaben:

* **PT4** (Praxisprojekt, **abgeschlossen** 15.08.2026) — Human-in-the-Loop, Confidence, MCP,
  Dashboard, Memory. Liefert Baseline und Kontext. Dokumentation in `docs/04_PT4/`.
* **Bachelorarbeit** (aktuell) — der Architekturvergleich.

**Sie müssen sauber getrennt bleiben — auch wegen des Eigenplagiats-Risikos.** PT4-Inhalte gehören
nicht in den Architekturvergleich; sie dürfen als „paralleler Ausbaupfad" in einem Nebensatz
vorkommen.

**Genau drei Brücken** führen von PT4 in die Arbeit:

1. **Die Fehlerinjektion als Ground-Truth-Methode** (Kap. 14) — die *Methode*, nicht ein
   bestimmtes Skript. Siehe die Korrektur in Kap. 14.
2. **Der `RULEBOOK_MODE`-Schalter** als *Teilbaustein* (Knoten 4) und Pilotergebnis —
   **nicht** als „die Graph-Architektur".
3. **Die deterministische technische Prüfung** (belegbar vs. erfunden).

**Nicht Gegenstand der Arbeit:** Human-in-the-Loop / Review Board, MCP-Toolset, E-Mail-Agent,
Management-Dashboard, episodisches Memory, Confidence-Scoring als Governance-Feature. Ebenfalls
nicht: Grundlagenforschung an LLMs, die Frage nach dem besten Foundation Model, reine
Prompt-Wortlaut-Optimierung.

**Faustregel für `docs/04_PT4/`:** Es darf **Wissen über das System** kommen, nie **Scope für den
Vergleich** — und **keine Zahl**. Eine PT4-Messung muss unter den Kontrollbedingungen dieser
Arbeit neu erhoben werden; sie zu zitieren wäre Eigenplagiat und ausserdem nicht vergleichbar.

**Nachschlagen erwünscht:** `04_PT4/AGENTEN_ARCHITEKTUR.md` (beschreibt die **Baseline** — wer sie
nicht kennt, baut versehentlich einen Strohmann), `ARCHITEKTURDIAGRAMME_PROJEKTBERICHT.md`,
`AP7-0_rule_inventory.md`, `BEFUNDE_UND_LEHREN.md`, aus `KONFIDENZ.md` **nur** `value_grounded`.
**Nicht übernehmen:** `PT4_BELEGE.md`, `AP1_AP7_APE_BELEGE.md`, `AP5_AP6_DOCUMENTATION.md`,
`PT4_PLAN.md`, `work-environment/`.

---

## 3. Terminologie — was „Monolith" und was „Graph" in DIESEM Repository heisst

Das ist die wichtigste und riskanteste Definitionsentscheidung der Arbeit. Ein Gutachter prüft
zuerst: **Ist die Baseline echt oder ein Strohmann?**

### 3.1 Das Strohmann-Risiko

Das Exposé beschreibt den monolithischen Ansatz als einen Systemprompt, der „alles auf einmal"
verarbeitet. **Der reale Ist-Zustand ist bereits eine Kette von sieben eigenständigen Skripten**,
per Subprozess verkettet. Wer als „monolithische Baseline" etwas baut, das künstlich schlechter
ist als das real Laufende, betreibt einen Strohmann-Vergleich — und ein Gutachter sieht das sofort.

Der monolithische Charakter liegt an **zwei anderen Stellen**:

1. **Der Korrekturgenerierungs-Schritt selbst ist monolithisch.** `generate_correction_llm.py`
   baut in *einem* Prompt das komplette Regelwerk (936 Zeilen) plus Kontext plus Ausgabeformat
   zusammen und lässt das LLM alles auf einmal entscheiden.
2. **Der Kontrollfluss ist implizit und nicht inspizierbar.** Es gibt kein einheitliches
   Zustandsobjekt, das durch die Kette wandert — nur lose `dict`-Rückgaben und Dateien auf Platte.
   Kein `trace`-Feld, kein rekonstruierbarer Entscheidungspfad. Die Iterationslogik ist reiner
   `while True`-Python-Code mit Zähler.

### 3.2 Die verbindliche Definition — wörtlich so in Kapitel 4 und 5 der Arbeit

> Der Unterschied zwischen Monolith und Graph liegt **nicht** darin, dass der Monolith weniger
> Verarbeitungsschritte hätte — er hat bereits sieben. Der Unterschied liegt darin, dass der
> Monolith **(a)** Regelwerk, Kontext und Ausgabeformat im zentralen Korrekturschritt ungefiltert
> bündelt und **(b)** keinen expliziten, extern prüfbaren Zwischenzustand zwischen den Schritten
> führt. Die graph-basierte Variante ersetzt genau diese zwei Eigenschaften: Knoten 4 lädt gezielt
> nur die passenden Regeln statt des vollständigen Regelwerks, und ein zentrales
> `GraphState`-Objekt macht jeden Zwischenschritt sichtbar, protokolliert und prüfbar —
> orchestriert über LangGraph statt über eine Python-`while`-Schleife mit Subprozess-Aufrufen.

Und der Absatz, der die Ehrlichkeit sichert (Methodenkapitel):

> „Als monolithische Baseline dient nicht ein künstlich vereinfachtes System, sondern der reale,
> produktiv eingesetzte Ist-Zustand des Smart-Planning-Agenten. Modell, Modellparameter,
> Kontextextraktion und Testfälle bleiben identisch, sodass beobachtbare Unterschiede auf die
> Architektur und nicht auf konfundierende Faktoren zurückführbar sind."

**Ohne diese zwei Absätze ist jeder Vergleich angreifbar.**

### 3.3 Zwei gleichzeitige Unterschiede — und wie sie auseinandergehalten werden

Diese Definition bedeutet: Die Graph-Variante unterscheidet sich vom Ausgangszustand in **zwei**
Eigenschaften gleichzeitig — bündelnder vs. selektiver Regelzugriff **und** impliziter vs.
expliziter Zustand.

Die frühere Fassung dieses Kapitels hielt es für ausreichend, das *offen zu benennen*. **Das
genügt nicht.** Wer zwei Dinge gleichzeitig ändert und nur eine Messung hat, kann den Effekt
nicht zuordnen — Offenheit macht das Problem sichtbar, aber nicht kleiner.

**Deshalb wird es gemessen statt eingeräumt:** Der Kontrollarm **B** (Kap. 7.1) hält die Pipeline
konstant und variiert nur die Regelquelle. Damit ist der Beitrag der selektiven Regelauswahl
empirisch abtrennbar, statt als Vorbehalt im Text zu stehen.

**Konsequenz für die Formulierung:** Die Intervention A→C ist ein **Gesamtpaket**. Ein
gemessener Effekt darf **nicht** dem `GraphState` allein zugeschrieben werden — was er wirklich
trägt, sagt erst der Vergleich mit B.

**Und eine Verschiebung, die daraus folgt:** Wenn B und C beide `cards` verwenden, leistet
Knoten 4 im Vergleich nicht mehr „weniger Regeltext", sondern **„sichtbar machen, welche Karten
geladen wurden"** — also **Provenienz statt Reduktion**. Für UF3 ist das wertvoller, für UF1
ehrlicher.

### 3.4 Was hier „Graph" heisst — und was NICHT

Das Wort wird in drei unvereinbaren Bedeutungen benutzt. Diese Arbeit meint **nur die dritte**.
Der Absatz gehört fast wörtlich in Kapitel 4 der Arbeit, weil er das häufigste Missverständnis
ausräumt, bevor es entsteht.

| Bedeutung | Beispiel | Gegenstand dieser Arbeit? |
|---|---|---|
| Graph als **Datenstruktur** | Knowledge Graph, Neo4j, „Artikel→Abteilung→Maschine" als Knotennetz | **Nein.** Kommt nicht vor |
| Graph als **Bild** | ein gezeichnetes Diagramm | **Nein** — fällt nur als Nebenprodukt an (Kap. 12.5) |
| Graph als **Programmablauf** | Verarbeitungsschritte als Knoten, Übergänge als Kanten | **Ja. Ausschliesslich das** |

> **Keine der Daten wird zu einem Graphen.** Der Snapshot bleibt JSON, die Regelkarten bleiben
> Markdown, die Datenbank bleibt SQLite, die Stammdaten werden nicht angefasst.
> **Zum Graphen wird der Ablauf, nicht das Material** — nicht das Werkstück wird umgebaut,
> sondern die Fertigungsstrasse.

### 3.5 Knoten und Kante, konkret

Ein **Knoten** ist eine Python-Funktion, die einen Zustand hereinbekommt und ihn verändert
zurückgibt. Mehr nicht:

```python
def node_rule_matching(state: GraphState) -> GraphState:
    tag   = state["classified_error"]["tag"]      # was Knoten 2 hinterlassen hat
    rules = load_rulebook(tag)                     # BESTEHENDE Funktion, unverändert
    state["matched_rules"] = {"cards_loaded": [...], "rule_text_hash": ...}
    state["trace"].append({"node": "rule_matching", "cards": [...]})
    return state
```

Eine **Kante** ist nur die Antwort auf „welcher Knoten läuft als Nächstes?" — meist fest
verdrahtet, an zwei Stellen abhängig vom Zustand (Kap. 11). Der Graph ist **gerichtet und hat
einen Zyklus** (die Rückkante 8→2); der Zyklus ist die bestehende Iterationsschleife, sichtbar
gemacht.

### 3.6 Neun Knoten sind NICHT neun LLM-Aufrufe

> **Korrigiert am 20.08.2026 (BA-031).** Die frühere Fassung zählte Knoten 9 als regulären
> LLM-Aufruf und behauptete trotzdem „genau so viele wie der Monolith". Beides zusammen war
> falsch: Knoten 9 rief `generate_audit_report_with_llm()`, und **keine** der vier
> Monolith-Pipelines (`full_correction`, `correction_from_validation`, `analyze_only`,
> `apply_and_upload`) enthält diesen Schritt. Bedingung C machte damit **vier** reguläre
> Aufrufe gegen drei in A und B — im Durchstich AP-F1 waren das 20.291 ms von 44.792 ms, also
> **45 % der Laufzeit**, plus zwei Artefakte, die A nicht hat.
>
> **Entschieden und umgesetzt:** Knoten 9 erzeugt das Endergebnis jetzt **deterministisch**
> über `app/core/ergebnis_format.py` — kein Modell, kein Netzwerk, gleiche Eingabe gleiche
> Ausgabe. `generate_audit_report()` bleibt unverändert als optionale, nachgelagerte
> Produktfunktion und ist **nicht** Bestandteil der A/B/C-Hauptmessung.

Am Code geprüft (`grep -c "chat.completions.create"`, nachgezählt 20.08.2026): Von den neun
Knoten rufen **drei** das Modell — genau so viele wie die Monolith-Pipeline.

| Knoten | LLM? | | Knoten | LLM? |
|---|---|---|---|---|
| 1 Eingabeanalyse | nein | | 6 Technische Prüfung | **bedingt** — siehe unten |
| **2 Fehlerklassifikation** | **ja** | | 7 Anwendung & Re-Validierung | nein |
| 3 Kontextsuche | nein | | 8 Ergebnisbewertung | nein |
| 4 Regelzuordnung | nein | | 9 Ausgabe/Finalisierung | **nein** (deterministisch) |
| **5 Korrekturgenerierung** | **ja** | | | |

**Die drei regulären Aufrufe:** Klassifikation (Knoten 2), Korrekturgenerierung (Knoten 5) und
die Schemaprüfung (Knoten 6). In der Monolith-Pipeline sind es dieselben drei Skripte —
`identify_error_llm`, `generate_correction_llm`, `validate_correction_schema_llm`.

**Schema-Retries sind bedingte Zusatzaufrufe, in beiden Architekturen gleich.**
`validate_with_retry(..., max_retries=5)` ruft das Modell erneut, wenn der Vorschlag das
Schema verletzt. Wie oft, hängt vom Vorschlag ab — das ist ein **Ergebnis** der jeweiligen
Architektur, kein Unterschied im Aufbau. Die Zahl steht je Lauf als `technical_check.retries`
im Zustand und ist bei Zeit- und Tokenvergleichen **getrennt auszuweisen**, nicht
wegzumitteln. Die Retry-Logik selbst ist in beiden Bedingungen dieselbe Funktion; eine
Retry-Policy auf Graphebene ist ausdrücklich ausgeschlossen (Kap. 11).

**Die Graph-Variante ist nicht „KI-lastiger".** Sie macht sichtbar, was zwischen denselben drei
Aufrufen passiert. Wer das im Methodenteil nicht klarstellt, weckt den Verdacht, der Vergleich
messe Aufwand statt Struktur.

### 3.6.1 ⚑ F3 und F4 — die beiden Entscheidungen aus AP-F, festgehalten

Beide waren als *„im Masterplan vermerken, nicht still treffen"* ausgewiesen (AP-F3/F4).
Entschieden am **20.08.2026**, nach dem vertikalen Durchstich.

**F3 — Es bleibt bei NEUN Knoten.** Der Durchstich hat den Ablauf End-to-End getragen; der
einzige aufgetretene strukturelle Widerspruch betraf **nicht** den Schnitt, sondern Knoten 9
als LLM-Aufruf — und der ist behoben (Kap. 3.6). Nach einem funktionierenden Durchstich
Knoten zusammenzulegen wäre eine Änderung ohne Anlass; das Schnittkriterium *„eine Grenze
dort, wo ein eigener Fehlermodus beobachtbar wird"* (Kap. 5.2) bleibt erfüllt. **Ab hier ist
die Zahl bindend** (Kap. 9.1).

**F4 — Provenienz bleibt auf KARTENEBENE.** `matched_rules.cards_loaded` weist aus, welche
Regelkarten geladen waren; eine feinere Zuordnung auf einzelne Unterregeln wird **nicht**
eingeführt.

> **Das ist eine Grenze, keine Bequemlichkeit — und sie gehört in die Limitationen.**
> Um Rule-IDs auf Regelebene zu bekommen, müsste das Regelwerk umgeschrieben und der Prompt
> geändert werden. Beides sind **Kontrollbedingungen** (Kap. 3.4, 7.3): eine Änderung nur zum
> Zweck feinerer Messung würde genau das verändern, was zwischen den Bedingungen gleich
> bleiben muss. Ausserdem wäre eine so gewonnene Rule-ID **nicht belastbar**: dass eine
> bestimmte Unterregel im Prompt stand, heisst nicht, dass das Modell sie benutzt hat. Ohne
> weiteren Eingriff ist die tatsächlich angewandte Einzelregel **nicht beobachtbar**.
> Kategorie 3 (Regelhalluzination) wird deshalb auf Kartenebene geprüft: *war die Karte, auf
> die sich das Modell beruft, überhaupt geladen?* Diese Einschränkung ist in Kapitel 8
> ausdrücklich zu benennen.

### 3.6.2 Die Reporting-Schicht — gemeinsam, nachgelagert, nicht Teil des Vergleichs

**Der Audit-Report ist ein wichtiges Produktartefakt, kein Nebenfeature.** Der angestrebte
Nutzungspfad lautet:

```
Snapshot korrigiert  →  Audit-Report erzeugt  →  optionaler Versand / Benachrichtigung
                                                  (z. B. E-Mail an eine verantwortliche Person)
```

Zweck: nachvollziehbar machen, **welche Fehler gefunden, welche Änderungen vorgenommen und wie
der Snapshot abschliessend validiert wurde**. Genau deshalb darf er nicht verschwinden — und
genau deshalb darf er auch nicht in den Architekturvergleich hineinragen.

#### Warum er den Vergleich nicht berührt — technisch nachgewiesen

`generate_audit_report.run_audit_report(snapshot_id)` liest ausschliesslich **Artefakte, die
alle drei Bedingungen schreiben**:

| Eingang | Fundstelle | in A | in B | in C |
|---|---|---|---|---|
| `metadata.txt` | `generate_audit_report.py:51` | ✔ | ✔ | ✔ |
| `upload-result.json` | `generate_audit_report.py:58` | ✔ | ✔ | ✔ |

Es liest **nichts** aus dem `GraphState` und nichts Graph-Spezifisches.

> **Empirisch belegt (20.08.2026, BA-032):** `run_audit_report()` wurde **unverändert auf einen
> Monolith-Snapshot** angewandt (Bedingung A, Fall I03, `e9ccf149-…`) und erzeugte einen
> vollständigen Report — 6.905 Zeichen, 6.795 Tokens, kein Fehler. Die Reporting-Schicht ist
> also bereits armneutral; sie **muss nicht integriert werden**, sie ist es schon.

```
A ─┐
B ─┼─▶  run_audit_report(snapshot_id)  ─▶  audit-report.md (+ -stats.json)  ─▶  Versand
C ─┘        gemeinsame Schicht                                                  (optional)
```

#### Bedarfsgesteuert — nicht automatisch nach einer Pipeline

**Der Report läuft ausschliesslich auf ausdrückliche Anforderung**, etwa *„Generiere einen
Report zu Snapshot X"*. Er wird **nicht** automatisch an eine Pipeline angehängt — weder heute
noch später. **Das aktuelle Verhalten ist genau das gewollte; es ist kein Zwischenstand und
kein Umbau geplant.** `SPAgent.execute_pipeline()` bleibt unangetastet, `full_correction`
behält seine sieben Schritte, und `generate_audit_report` ist in keiner Pipeline-Schrittliste
enthalten.

Warum das auch fachlich richtig ist: Ein Report, den niemand angefordert hat, kostet je Lauf
Zeit und Tokens, legt ein weiteres Artefakt ab und kann fehlschlagen — und würde damit einen
sonst gültigen Korrekturlauf ohne Not in Frage stellen. Während Pilot- und Hauptläufen
entsteht er deshalb gar nicht erst.

Der Aufrufort ist entsprechend der **Nutzer bzw. Aufrufer**, nach Abschluss und getrennt vom
Korrekturlauf — ein zweiter, eigenständiger Vorgang auf demselben Snapshot.

#### Messgrössen trennen (verbindlich ab AP-H)

| Präfix | umfasst | wofür |
|---|---|---|
| `core_*` | Klassifikation → Suche → Regeln → Korrektur → Schema → Anwendung → Re-Validierung → Bewertung → Finalisierung | **der Architekturvergleich** — UF1, UF2, UF3 |
| `report_*` | `run_audit_report()` | die gemeinsame Reporting-Schicht, **separat** ausgewiesen |
| `total_*` | beides zusammen | nur dort, wo eine Gesamtbetrachtung sinnvoll ist |

**Für UF1 und UF2 hat der Audit-Report keinen Einfluss auf die fachlichen Ergebnisse.** Er
entsteht **nach** der Korrekturentscheidung, liest sie nur und wirkt nicht auf sie zurück.
Sein LLM-Aufruf ist deshalb **kein Aufruf der Graph-Orchestrierung** und darf nicht als solcher
gezählt werden — dieselbe Funktion steht A und B nachgelagert genauso zur Verfügung.

> **Formulierung für den Methodenteil.**
> *Der Architekturvergleich bezieht sich auf den Korrektur- und Entscheidungsprozess. Die
> natürlichsprachliche Audit-Report-Generierung ist eine gemeinsame nachgelagerte
> Produktfunktion ohne Rückwirkung auf die Korrekturentscheidung und wird separat betrachtet.*

#### Produktmodus und Evaluierungsmodus

Zwei verschiedene Ausgaben mit zwei verschiedenen Anforderungen — sie dürfen nicht verwechselt
werden:

| | Produktmodus | Evaluierungsmodus |
|---|---|---|
| erzeugt von | `generate_audit_report()` | `core.ergebnis_format.als_text()` |
| Form | natürlichsprachlicher Report | variantenneutrales Kurzformat |
| Snapshot-ID | **real, erwünscht** | **ausschliesslich Pseudonym** (erzwungen) |
| Adressat | verantwortliche Person, E-Mail | verblindete Fachgutachter |
| im Vergleich | nein — `report_*` | Gegenstand von UF3 |

Die Zuordnung **Pseudonym ↔ Snapshot ↔ Bedingung** gehört in eine **getrennte Datei, die den
Bewertern nicht zugänglich ist** (Kap. 16). `als_text()` wirft ohne Pseudonym eine Ausnahme —
ein stiller Rückfall auf die echte ID war der Befund aus AP-F5.

#### E-Mail-Versand — Ausblick, nicht Messgegenstand

Der Versandkanal ist **nur ein Verbraucher** des Reports und ebenfalls ein **separater
Folgeprozess** — nicht Bestandteil des Korrektur- und erst recht nicht des A/B/C-Messpfads.
Er wird **nicht** in den experimentellen Kern gebaut. Als praktischer Nutzungspfad gehört er in den Ausblick: der
Report macht einen automatisierten Korrekturlauf gegenüber einer verantwortlichen Person
rechenschaftsfähig — das ist der betriebliche Nutzen, der über den Architekturvergleich
hinausweist.

### 3.7 Den Zustand gibt es bereits — er liegt nur verstreut

Das ist das stärkste Argument gegen den Strohmann-Vorwurf. Nach einem heutigen Lauf liegt in
einem Iterationsordner:

```
iteration-1/
    llm_identify_response.json     <- Ausgang Knoten 2
    last_search_results.json       <- Ausgang Knoten 3
    llm_correction_proposal.json   <- Ausgang Knoten 5
    snapshot-validation.json       <- Ausgang Knoten 7
```

**Das ist bereits ein Zustand.** Er ist nur (a) über acht Dateien verstreut, (b) untypisiert,
(c) ohne Reihenfolge, (d) ohne Zeitstempel — und (e) eines fehlt ganz: **welche Regelkarten
geladen wurden.** Das steht heute nur als `print()` in `generate_correction_llm.py:875` und
verschwindet im stdout des Subprozesses.

Der `GraphState` ist **dieselbe Information in einem typisierten Objekt**, in Reihenfolge, mit
Zeitstempeln, um die fehlenden Felder ergänzt. Nicht mehr, aber auch nicht weniger.

### 3.8 Was sich ändert und was nicht — die Übersicht

| Ändert sich **nicht** | Ändert sich |
|---|---|
| Die Prompts | **Wie die Schritte verbunden sind:** Subprozess + Dateien → Funktionsaufruf + Zustandsobjekt |
| Modell, Temperatur (0.3), API-Version | **Ob Zwischenzustand sichtbar ist:** nein → ja (`trace`) |
| Die Kontextsuche (`identify_snapshot`) | **Wann Regeln geladen werden:** versteckt in Schritt 2/5 → eigener sichtbarer Schritt 4 |
| Die Validierungs-Engine | **Wer die Iteration entscheidet:** `while True` in `sp_agent.py` → Knoten 8 schreibt `decision`, die Kante liest sie |
| Snapshot-Format, Regelkarten, Datenbank, Stammdaten | **Welche Regeln geladen werden:** alle 936 Zeilen → nur die passenden Karten |

**Die fachliche Logik — was ein gültiger Korrekturwert ist — ändert sich an keiner Stelle.**

### 3.9 Die ehrliche Einordnung, die den Vergleich schützt

Ein kritischer Gutachter fragt: *„Ist das nicht einfach ein Refactoring mit schönem Namen?"*
Die Antwort muss **im Text stehen, bevor er sie stellt**:

> Architektonisch ist es ein gerichteter Graph mit Zyklus. Die wissenschaftliche Behauptung ist
> **nicht** „Graphen sind besser", sondern: **expliziter Zwischenzustand plus selektiver
> Regelzugriff verändern messbare Grössen** — diese drei, in diese Richtung, in diesem Ausmass.

Wer so formuliert, ist unangreifbar. Wer „Graph-Architektur" als Zauberwort benutzt, nicht.

---

## 4. Ist-Zustand — verifiziert am 2026-08-16

Alle Angaben gegen den echten Code geprüft, nicht aus den Vorgängerdokumenten übernommen.
**Die drei Vorgängerpläne nannten durchweg `demo/`-Pfade und Zeilennummern vom 02.08. — beides ist
überholt.** Der Ordner heisst seit 02.08. `app/`, und es wurde zusätzlich tiefer umsortiert.

### 4.1 Die Agenten

| Agent | Datei | Zeilen | Rolle |
|---|---|---|---|
| `BaseAgent` | `app/agents/base_agent.py` | 79 | gemeinsame Basis |
| `ChatAgent` | `app/agents/chat_agent.py` | 164 | freies Gespräch |
| `RAGAgent` | `app/agents/rag_agent.py` | 246 | Azure AI Search |
| `OrchestrationAgent` | `app/agents/orchestration_agent.py` | 1379 | Router + Multi-Step-Planer |
| `SPAgent` | `app/agents/sp_agent.py` | 680 | **reiner Executor, macht selbst KEINE LLM-Calls** |
| `EmailAgent` | `app/agents/email_agent.py` | 288 | fünfter Agent, **out of scope** |

Systemprompts zentral in `app/core/agent_config.py` (675 Z.). **`SPAgent` hat keinen eigenen
Systemprompt** — die LLM-Intelligenz der Korrektur-Pipeline steckt in den Runtime-Skripten.

### 4.2 Die „425-Zeilen"-Aussage — korrigiert

Die Exposé-Zahl „425 Zeilen / 20.284 Zeichen" bezieht sich **nicht** auf einen Python-String,
sondern auf `app/tools/smart-planning/runtime/runtime-files/llm-validation-fix-rules.md`.

**Diese Datei hat heute 936 Zeilen / 36.165 Byte** — mehr als doppelt so viel. Die Exposé-Zahl ist
ein veralteter Schnappschuss. **Das muss in der Arbeit richtiggestellt oder neu vermessen werden.**
Geladen wird sie über `rulebook_loader.load_rulebook()` und als `{fix_rules}` in den
Korrektur-Prompt injiziert.

### 4.3 Die Korrektur-Pipeline

Alle unter `app/tools/smart-planning/runtime/`:

| Skript | Zeilen | Rolle |
|---|---|---|
| `create_snapshot.py` | 254 | Snapshot anlegen |
| `download_snapshot.py` | 330 | Snapshot herunterladen |
| `validate_snapshot.py` | 227 | Validierungsnachrichten abholen (löst Validierung NICHT aus) |
| `identify_snapshot.py` | **1186** | Kontextsuche im Snapshot |
| `identify_error_llm.py` | **450** | LLM analysiert Rohfehler, wählt Suchmodus **und** Regelkarten |
| `generate_correction_llm.py` | **1085** | LLM erzeugt den Korrekturvorschlag |
| `validate_correction_schema_llm.py` | 251 | Pydantic-Schemaprüfung mit LLM-Retries |
| `apply_correction.py` | **572** | wendet den Vorschlag auf `snapshot-data.json` an |
| `update_snapshot.py` | 324 | schreibt zurück an den Server |
| `generate_audit_report.py` | 375 | deutschsprachiger Audit-Report |
| `correction_models.py` | 4.050 B | Pydantic-Modelle |
| `runtime_storage.py` | 4.651 B | Storage-Abstraktion (LOCAL/AZURE) |

**Aufrufmuster:** Jedes Skript ist ein eigenständiges CLI und wird **ausschliesslich per
`subprocess.run`** aufgerufen — `SPAgent._run_tool()`, `app/agents/sp_agent.py:71-168`.

**Pipeline-Definition:** `app/agents/sp_tools_config.py`, `SP_PIPELINES` ab Z. 104:

```
full_correction:            validate_snapshot → identify_error_llm → generate_correction_llm
                             → validate_correction_schema_llm → apply_correction → update_snapshot
                             → validate_snapshot (Re-Validierung)
correction_from_validation:  wie oben, ohne den initialen validate_snapshot-Schritt
analyze_only:                validate → identify → generate → schema-check (keine Änderung)
```

### 4.4 Wie die Skripte Daten weiterreichen — **über Dateien**

Das ist für den Graph-Bau die wichtigste Struktureigenschaft:

```
identify_error_llm  ──schreibt──▶ iteration-N/llm_identify_response.json
        │ (Subprozess)
        ▼
identify_snapshot   ──schreibt──▶ last_search_results.json
        │
        ▼
generate_correction ──liest beide, schreibt──▶ iteration-N/llm_correction_proposal.json
                                              _proposals/{sid}__iteration-N.json
        ▼
apply_correction    ──liest Vorschlagsdatei, schreibt──▶ snapshot-data.json
```

Rückgabewerte existieren für einzelne Funktionen, **die Verkettung läuft über `runtime_storage`**.
Für den Graphen heisst das: Die Knoten müssen entweder dieselben Dateien schreiben (empfohlen —
hält die Rohdatenlage identisch) oder der `GraphState` übernimmt die Weitergabe zusätzlich.

### 4.5 Was importierbar ist — und was in `main()` steckt

Entscheidend für Kap. 12.2. Geprüft durch Lesen der Signaturen:

| Knoten | Direkt aufrufbar | In `main()` gefangen |
|---|---|---|
| 2 Klassifikation | `identify_error_llm.analyze_validation_with_llm(validation_data)` → `(analyse, first_error, call_data)` | Laden der Validierungsdaten, Iterationsordner, Speichern, `trigger_identify_tool` |
| 3 Kontextsuche | **nichts Ganzes.** Bausteine ja (`build_enriched_context`, `search_in_dict`, `find_references`) | **die gesamte Ablaufsteuerung**, `main()` Z. 888-1185 (~300 Zeilen) — der grösste Entflechtungsaufwand |
| 4 Regelzuordnung | `rulebook_loader.load_rulebook(error_type, extra_cards)` — **1:1 nutzbar** | — |
| 5 Korrektur | `generate_correction_llm.generate_correction_with_llm(fix_rules, identify_response, search_results, memory_evidence)` — **nimmt genau, was ein Knoten liefert** | Sperre, Gedächtnis, `derive_correction_identity`, Konfidenz, Speichern (~250 Z.) |
| 6 Technische Prüfung | `validate_correction_schema_llm.validate_with_retry(sid, iter, proposal, max_retries=5)` | wenig |
| — Anwenden | `apply_correction.apply_correction(sid, proposal)` | wenig |
| — Validieren | `validate_snapshot.validate_snapshot(sid)` | wenig |
| 8 Antwort | `generate_audit_report.generate_audit_report_with_llm(metadata, upload_results, sid)` | wenig |

### 4.6 Der bestehende Iterations-Loop

**Produktions-Loop** — `SPAgent.execute_pipeline()`, **`app/agents/sp_agent.py:626-679`**
(die Vorgängerpläne nannten `:450-503` — überholt):

```python
MAX_CORRECTION_ITERATIONS = 5
iteration = 0
while True:
    iteration += 1
    last_result = self._execute_pipeline(pipeline_name, snapshot_id)   # sp_agent.py:278
    if not is_correction_pipeline or not last_result.get("success"): break
    if final_validation.get("errors", 0) == 0: break        # Erfolg
    if iteration >= MAX_CORRECTION_ITERATIONS: break        # Abbruch
```

**Governance-Gate davor:** `HUMAN_IN_THE_LOOP` (`app/core/agent_config.py:10`, **Default `true`**)
wird in `orchestration_agent.py:801/824/890` geprüft; `full_correction` und
`correction_from_validation` werden **vor** dem Aufruf still auf `analyze_only` umgeschrieben.

**Fazit:** Heute entscheidet reiner Python-Kontrollfluss, gesteuert von einer statischen
Schrittliste plus Iterationszähler — **keine** Zustandsmaschine, kein typisiertes Zustandsobjekt.

### 4.7 Das `RULEBOOK_MODE`-Muster — Vorbild für den neuen Schalter

`app/core/rulebook_loader.py` (290 Z.). Env-Var **einmal, zentral** gelesen:
`app/core/agent_config.py:40` → `RULEBOOK_MODE = os.getenv("RULEBOOK_MODE", "cards").lower()`.
Die gesamte Verzweigung in **einer** Funktion, `load_rulebook()` (`:264`). Aufrufer kennen den
Modus nicht.

**Das ist exakt das Muster für `SP_ARCHITECTURE_MODE` (Kap. 6) und `MEMORY_MODE` (Kap. 7.2):
ein Env-Var, eine Stelle die verzweigt, alle Aufrufer bleiben unwissend.**

⚠ **Der Kopfkommentar von `rulebook_loader.py:6` behauptet `"monolith" (default)` — das ist
falsch.** Der Code sagt `cards`. Der Kommentar in `agent_config.py:32-40` ist korrekt. Wer den
Loader liest, setzt die Baseline verkehrt auf.

### 4.8 Bestehende Eval-Infrastruktur

| Skript | Zweck |
|---|---|
| `app/eval/build_test_catalog.py` (178 Z.) | Fehlerinjektion mit Ground Truth in `metadata.txt.injected_error` — **siehe Korrektur Kap. 14** |
| `app/eval/run_isolated_suite.py` | 10 Snapshots, je ein chirurgischer Fehler, 5 Kriterien |
| `app/eval/run_combined_suite.py` | 10 Snapshots, mehrere Fehler |
| `app/eval/run_iterative.py` (83 Z.) | Multi-Fehler-Loop bis „valide", umgeht `sp_agent.py` bewusst |

**Kataloge auf Platte:** `data/snapshots/pt4-manipulated_snapshots/isolated-error-snapshots/`
(10 Fälle) und `.../kombinierte-fehler-snapshots/` (10 Fälle).

### 4.9 Was geklärt ist — und was die Vorgängerpläne falsch hatten

| Punkt | Stand 16.08.2026 |
|---|---|
| **Modell** | **Konflikt aufgelöst.** Alle fünf Deployments auf `gpt-4.1`, API `2025-01-01-preview`, `temperature=0.3` in allen drei Korrekturskripten. Datiert belegt: `infra/terraform.tfvars:63-66` im Repo `Infra/agentic-ai-mfg-infrastructure-terraform`, Kommentar „02.08.2026 von gpt-4o auf gpt-4.1 umgestellt". Der im Umsetzungsplan Kap. 4/12 benannte Konflikt GPT-4.1 gegen `gpt-4o` existiert nicht mehr. |
| **Terraform** | **Vorhanden**, aber im **Nachbar-Repository**, nicht in diesem. Die Masterplan-Aussage „kein Terraform" war eine Frage des Suchbereichs. Das Exposé ist korrekt; die geplante Richtigstellung entfällt. *Einschränkung:* eine `azurerm_cognitive_deployment`-Ressource existiert dort nicht — Terraform verwaltet über ein Key-Vault-Secret, **welches** Deployment die Anwendung nutzt, nicht dessen Anlage. |
| **`RULEBOOK_MODE`-Historie** | **Geklärt — Masterplan lag falsch.** Er hielt es für unverifiziert. Tatsächlich erzwingen **alle drei** Eval-Skripte `cards` hart im Code: `run_isolated_suite.py:115`, `run_combined_suite.py:97`, `run_iterative.py:33`. → **Kein einziger Lauf im Repository entstand unter `monolith`.** |
| **`langgraph`** | **Nicht installiert**, kein Graph-Code, kein `SP_ARCHITECTURE_MODE`, kein `graph/`-Verzeichnis. Volltextsuche trifft nur Dokumente. |
| **Abhängigkeiten** | `app/deploy/requirements.txt` pinnt `openai>=1.6.0,<2.0.0`, **installiert ist 2.14.0**; `pydantic 2.12.4`. Die Umgebung weicht schon heute von der Pin-Datei ab — **vor** dem Hinzufügen von LangGraph zu lösen. |
| **Schema-Retries** | `validate_with_retry(..., max_retries=5)` — der Masterplan nannte 3. Das ist eine Kontrollbedingung. |
| **Ergebnisdateien** | `pt4-eval-results.json` / `pt4-combined-results.json` enthalten **keine Lauf-Metadaten**: kein Zeitstempel, kein Modell, keine Temperatur, kein `RULEBOOK_MODE`, kein Prompt, keine Antwort. Sie erfüllen weder Kap. 17 noch Regel 7. **Als Rohdaten unbrauchbar — auch für `cards`.** |

### 4.10 ⚠ Der Befund, den kein Vorgängerplan kannte: das episodische Gedächtnis

**Es liegt mitten im gemessenen Pfad und ist unbedingt aktiv.** Der Masterplan (02.08.) ist älter
als AP7.2; der Umsetzungsplan führt Memory als „nicht Teil der Arbeit" — es ist aber **im Code**:

* `generate_correction_llm.py:886-902` — holt frühere **menschliche** Entscheidungen und legt sie
  dem Modell als Belege in den Prompt. Vor dem LLM-Aufruf, an keine Bedingung geknüpft.
* `:936-975` — `same_entity_confirmed_value()` **überschreibt den Modellwert**, wenn ein Mensch
  für dasselbe Objekt und Feld bereits entschieden hat.
* `:1017-1027` — `memory_support` geht mit Gewicht 0,2 in die Konfidenz ein und hebt sie auf ≥0,9.
* Bestand: **20 Einträge** in `memory_items` (11 approve, 7 modify, 2 reject), **wachsend**.

**Die Lösungen deines Testkatalogs stehen objektgenau in der Datenbank.** Nachweisbare Kette:

| Zeit | Ereignis |
|---|---|
| 31.07., 19:06 | isolierte Suite fertig. Fall **I03**: Modell schlägt `1.14` vor, richtig ist `1.017` → `value_ok: false` |
| 31.07., 20:25:48 | ein Mensch korrigiert im Review Board auf `1.017` → `memory_items` id 11: `DENSITY_VALUES`, `articles:100005`, suggested `1.14` → final **`1.017`** |
| 31.07., 23:01 | kombinierte Suite. Fall 03, derselbe Artikel: `memory_support: 1.0`, `top_value: 1.017` — **richtig** |

Das Modell wurde nicht besser; **ihm wurde die Antwort gereicht.** Dasselbe gilt für die Einträge
9, 10, 12, 14 (alle 31.07., 20:22–20:31) und 16/18/22 — sie decken die Katalogfälle I01, I02, I04,
I05, I08, I10 mit exakt den Ground-Truth-Werten ab.

**→ Behandlung: Kapitel 7.2. Das ist genau die Falle aus Regel 6** — nur sitzt der Defekt diesmal
nicht in der Metrik, sondern in der Eingabe.

---

## 5. Fixierte Grundsatzentscheidungen

Diese Entscheidungen sind ab jetzt bindend. Werden sie revidiert, ist dieses Dokument anzupassen.

### 5.1 LangGraph als Framework *(entschieden 16.08.2026)*

**Wichtig für die Begründung im Methodenteil: Das Exposé nennt kein Framework.** Eine Volltextsuche
über das eingereichte PDF nach `LangGraph`/`LangChain` liefert **null Treffer** (geprüft
16.08.2026). Die frühere Behauptung des Vorgängerplans, LangGraph decke sich „1:1 mit dem, was das
Exposé nennt", war **falsch**. Die Framework-Wahl ist damit **frei** — sie ist zu begründen, aber
keine Variante steht im Widerspruch zum Exposé.

**Begründung:** zitierfähige offizielle Muster (bedingte Retry-Kante, `interrupt()`);
`get_graph().draw_mermaid()` erzeugt die Architekturabbildung **aus dem laufenden Code** — bei
einer Arbeit über Nachvollziehbarkeit mehr als Kosmetik; das Wort „Graph" wird wörtlich.

**Erste Aufgabe vor der Installation:** den Konflikt `openai 2.14.0` gegen den Pin `<2.0.0`
auflösen (Kap. 4.9), dann `pydantic`-Kompatibilität prüfen.

**Dokumentierter Rückfall:** Scheitert die Abhängigkeitsauflösung, ist ein expliziter
Zustandsautomat in Python zulässig (Knoten = Funktionen, State = TypedDict, Übergänge =
Rückgabewerte). Dann im Methodenteil so benennen: *„graph-basierte Architektur, implementiert als
expliziter Zustandsautomat"* — der Untersuchungsgegenstand ist die Architektur, nicht das
Framework. **Diese Entscheidung ist dann hier zu vermerken, nicht still zu treffen.**

### 5.2 Sequenzielle Kette mit Rück-Kante, keine Baumsuche *(entschieden 16.08.2026)*

Der Vergleich ist **monolithische Kette vs. graph-basierte Kette mit explizitem Zustand**.
**LATS (Zhou et al., ICML 2024) ist nicht Gegenstand dieser Arbeit.**

**Die Knoten und Kanten sind nicht vorgegeben — sie sind eine Designentscheidung dieser Arbeit.**
Am PDF geprüft (16.08.2026): Das Exposé nennt die Zerlegung in „klar definierte Schritte — **etwa**
Eingabeanalyse, Fehlerklassifikation, Kontextsuche, Regelzuordnung, Korrekturgenerierung und
Ergebnisbewertung". Das Wort **„etwa"** ist entscheidend — die sechs sind **Beispiele, keine
abschliessende Liste**. Anzahl und Schnitt sind damit frei und müssen in Kapitel 4 **begründet**
werden, nicht als gegeben dargestellt.

**Das Schnittkriterium dieser Arbeit — und zugleich ihr Designprinzip:**

> **Eine Knotengrenze gehört dorthin, wo ein eigener Fehlermodus beobachtbar und zurechenbar wird.**

Das ist kein willkürlicher Schnitt, sondern folgt direkt der Messvorschrift: Jede der vier
Halluzinationskategorien (Kap. 15.1) bekommt **genau einen** Knoten, an dem sie sichtbar wird.
Genau das kann der Monolith nicht — dort verschmelzen die Fehlermodi in einem Kontext, und bei
einer falschen Ausgabe ist nicht entscheidbar, welcher davon zugeschlagen hat. **Der Schnitt folgt
der Messvorschrift** — dieser Satz gehört in Kapitel 4 und trägt einen erheblichen Teil der
Argumentation für UF3.

Daraus folgen **neun** Knoten (Kap. 9), nicht die sechs des Exposé-Beispiels. Zwei kommen aus dem
Messbedarf (Technische Prüfung, Anwendung & Re-Validierung), einer aus dem Ablauf
(Antwortformulierung).

> **Ignoriert:** `docs/03_Expose-extern/source-2/` stammt von einem Kollegen ohne Kenntnis der
> Projektdetails und ist **nicht massgeblich** (Entscheidung 16.08.2026). Das dortige `Thesis.md`
> beschrieb ein abweichendes Zielbild (`LATS+RAG` mit Baumsuche, „needs Macher sign-off"); es ist
> gegenstandslos, ein Rückbau erübrigt sich. `exposee.md` wurde vor dem Verwerfen gegen das PDF
> geprüft und war inhaltlich korrekt — es wird trotzdem nicht mehr verwendet, weil das Exposé
> direkt lesbar ist (siehe unten). **Massgeblich ist ausschliesslich das PDF.**

**Warum nicht GoT-Referenzframework:** Die Operationen-API von `spcl/graph-of-thoughts`
(`Generate(k)`, `Aggregate(k)`, `Score(k)`, `KeepBestN(N)`) ist dafür gebaut, **mehrere
gleichartige LLM-Ausgaben zu erzeugen und zusammenzuführen**. Unsere neun Knoten sind dagegen
**heterogene, werkzeugaufrufende Schritte** (API-Calls, Schema-Validierung,
Dateisystem-Operationen), nicht Varianten derselben Denkoperation. Besta et al. bleibt
theoretische Grundlage; die Framework-Entscheidung gegen GoT wird mit genau diesem strukturellen
Argument begründet. Das ist eine saubere Methodenentscheidung, keine Ausrede.

### 5.3 Das Rad nicht neu erfinden

Für jeden zentralen Baustein existiert ein zitierfähiges Muster:

* **Die Rück-Kante (Knoten 6→2) ist ein benanntes Muster, keine Eigenerfindung** —
  *Self-Refine* (Madaan 2023), *Reflexion* (Shinn 2023), *REFINER* (Paul 2023), alle drei bei
  Besta et al. (2024) als Vorarbeiten geführt. LangGraph dokumentiert exakt dieses Muster als
  Standardweg für Retry-/Selbstkorrektur-Schleifen (Router liest `state["error"]` und
  `state["iterations"]`).
* **MindMap (Wen et al. 2024)** liefert zwei übertragbare Ideen: das Mind-Map-Format als **Vorbild
  für die Trace-Darstellung** (lesbare Kette „Knoten → Eingabe → Entscheidung → nächster Knoten"
  statt rohem JSON) und die **GPT-4-Rater-Pairwise-Methode** als *optionales, zusätzliches*
  automatisiertes Signal zur Triangulierung — **kein Ersatz** für die menschliche
  Expertenbewertung, und im Methodenteil explizit so zu kennzeichnen.
* **Human-in-the-Loop:** LangGraph bringt `interrupt()` + `Command(resume=...)` mit. Relevant nur
  ausserhalb des Kernvergleichs (Kap. 7.1).

---

## 6. Koexistenz statt Ersetzen — der Schalter

### 6.1 Das Prinzip

Kein bestehendes Skript unter `app/tools/smart-planning/runtime/` wird gelöscht, umbenannt oder in
seinem CLI-Verhalten verändert. Der Monolith-Pfad bleibt bestehen und ist nach Abschluss der Arbeit
weiterhin die produktive Standardvariante. Die Skripte werden **additiv erweitert**, nie ersetzt.

### 6.2 `SP_ARCHITECTURE_MODE`

```python
# app/core/agent_config.py, nach dem Vorbild von RULEBOOK_MODE (Z. 40)
SP_ARCHITECTURE_MODE = os.getenv("SP_ARCHITECTURE_MODE", "monolith").lower()  # "monolith" | "graph"
```

**Default `"monolith"`** — bewusst so, dass ohne explizites Setzen **niemand** ein verändertes
Verhalten sieht.

### 6.3 Wo genau geschaltet wird

**Einziger Verzweigungspunkt:** `SPAgent.execute_pipeline()`, **`app/agents/sp_agent.py:626`**,
ganz am Anfang der Methode:

```python
def execute_pipeline(self, pipeline_name, snapshot_id=None):
    if SP_ARCHITECTURE_MODE == "graph" and pipeline_name in GRAPH_ENABLED_PIPELINES:
        return self._execute_pipeline_graph(pipeline_name, snapshot_id)   # NEU
    # -------- ab hier: bestehender Code, UNVERÄNDERT --------
    MAX_CORRECTION_ITERATIONS = 5
    ...
```

`GRAPH_ENABLED_PIPELINES = {"full_correction", "correction_from_validation"}`.

`_execute_pipeline_graph()` gibt **exakt dieselbe Rückgabestruktur** zurück wie
`_execute_pipeline()` (`success`, `final_validation`, `total_iterations`, `completed_steps`), damit
Orchestrator, Web-UI und Eval-Skripte nichts von der Umstellung merken.

### 6.4 Was nicht angefasst werden darf

* Die neun Runtime-Skripte: CLI-Verhalten (Argumente, stdout, Exit-Codes, erzeugte Dateien) bleibt
  exakt wie heute.
* `rulebook_loader.py` / `RULEBOOK_MODE` — bleibt unabhängig; beide Schalter sind orthogonal.
* Das `HUMAN_IN_THE_LOOP`-Gate — gilt für **beide** Modi in Produktion gleichermassen. Nur
  Eval-Läufe dürfen es für Messzwecke explizit und dokumentiert umgehen (Präzedenzfall:
  `run_iterative.py`).

---

## 7. Kontrollbedingungen — eingefroren

### 7.1 Das Untersuchungsdesign: zwei Architekturen, drei Messbedingungen

**Entschieden am 2026-08-19**, nach externer Begutachtung des Plans. Ersetzt die frühere
Zwei-Arm-Anordnung, die sich selbst widersprach (siehe Kasten am Ende dieses Abschnitts).

| | Bedingung | Pipeline | `RULEBOOK_MODE` | Was sie im Projekt ist |
|---|---|---|---|---|
| **A** | **Ausgangszustand** | Monolith, impliziter Ablauf | `monolith` | der Zustand **bis 12.07.2026** — das System, das das Exposé beschreibt |
| **B** | **Realer Ist-Zustand** | Monolith, impliziter Ablauf | `cards` | **produktiv ausgerollt seit 12.07.2026** |
| **C** | **Neue Gesamtarchitektur** | LangGraph, `GraphState`, Provenienz | `cards` | die Vergleichsvariante dieser Arbeit |

**Hauptvergleich: A gegen C** — genau die zwei Architekturen, die das Exposé nennt
(„der bestehende monolithische Systemprompt und eine neu konzipierte graph-basierte
Systemarchitektur"). Die Intervention ist dabei ausdrücklich ein **Gesamtpaket**: expliziter
Zustand **plus** Graph-Orchestrierung **plus** selektiver Regelzugriff.

**Kontrollvergleich: B** — trennt den Beitrag der selektiven Regelauswahl von dem der
Graph-Orchestrierung. **Über alle 17 Fälle**, damit das Bild vollständig ist und keine
Teilmengen-Einschränkung in den Text muss.

> **B wird NICHT erst nach Sichtung der A/C-Ergebnisse auf Divergenzfälle eingeschränkt.**
> Das wäre eine Auswahl nach dem Sehen der Daten und damit ein Verstoss gegen Regel 5.
> Alle drei Bedingungen laufen für UF1 mindestens einmal über **dieselben vollständigen
> 17 Messfälle**, alle **nach demselben Einfrieren (G5)**.

**Die drei paarweisen Lesarten — so und nicht anders zu interpretieren:**

| Vergleich | Was er beantwortet |
|---|---|
| **A vs. C** | *Der Gesamtvergleich.* Ursprünglicher Monolith gegen Graph-Zielarchitektur — die Frage des Exposé-Titels. Intervention = **Gesamtpaket** |
| **A vs. B** | Einfluss der **Regelwerk-Modularisierung** allein (Cards), ohne Graph |
| **B vs. C** | **zusätzlicher** Einfluss der Graph-Orchestrierung **bei gleichem Regelwerk** |

Ein Effekt in A→C darf **nicht** dem `GraphState` allein zugeschrieben werden; was er wirklich
trägt, sagt erst die Zerlegung über B.

> **B ist keine dritte Architektur**, sondern dieselbe wie A mit anderer Regelkonfiguration.
> Deshalb: *„zwei Architekturen, drei Messbedingungen"*. Damit bleibt die Anordnung wörtlich
> innerhalb der Exposé-Abgrenzung.

**Drei Probleme, die dieses Design löst:**

1. **Attribution.** Bei A gegen C allein wäre nicht entscheidbar, woher ein Effekt kommt. Mit B
   ist er zerlegbar.
2. **Der Strohmann-Vorwurf entfällt beweisbar.** `cards` ist der produktiv ausgerollte Zustand
   (`app/.env` setzt nichts, Terraform-Default `cards`, nicht überschrieben — verifiziert
   19.08.2026). Mit B liegt **der reale Ist-Zustand im Vergleich**, nicht nur der historische.
   Regel 2 ist damit nicht nur behauptet, sondern belegt.
3. **Der Selbstwiderspruch ist weg** (siehe Kasten).

**Was B leistet und was nicht:** B trägt **nur zu UF1** bei. Für UF3 ist es uninteressant (es hat
dieselbe Nachvollziehbarkeit wie A), für UF2 wäre es zu teuer. **Ohne Wiederholungsläufe.**
Als Einschränkung in den Text.

**Zum Kartensystem und Eigenplagiat:** Das Kartensystem wurde im Praxisprojekt entwickelt
(AP7.0). Die Arbeit **führt es mit**, sie beansprucht seine Entwicklung nicht. Formulierung für
den Methodenteil:

> „Das im Praxisprojekt entwickelte Kartensystem wird als Zwischenstufe mitgeführt, um den
> Beitrag der Graph-Orchestrierung von dem der selektiven Regelauswahl zu trennen. Die hier
> berichteten Werte wurden unter den Kontrollbedingungen dieser Arbeit **neu erhoben**."

Die PT4-Zahlen (−16 % Tokens) dürfen **nicht** als Ergebnis dieser Arbeit auftreten.

### 7.1.1 Was zwischen ALLEN drei Bedingungen identisch sein muss

| Bedingung | Wert / Vorgehen |
|---|---|
| **Modell** | `gpt-4.1`, konkret **`gpt-4.1-2025-04-14`**, API-Version `2025-01-01-preview` |
| **Modellparameter** | `temperature=0.3` (aus dem Code ausgelesen). Bewusst **nicht 0**: für die Wiederholungstests der UF2 braucht es Variabilität |
| **Kontextextraktion** | `identify_snapshot.py` unverändert, für alle Bedingungen identisch aufgerufen |
| **Azure-Client** | **Nicht** neu bauen — dadurch ist Modell- und Parametergleichheit **strukturell garantiert**, nicht nur dokumentiert |
| **`MEMORY_MODE`** | **`off` in allen drei Bedingungen** (siehe 7.2) |
| **Testfälle** | identisch, alle 17 distinkten Fälle |
| **Ausführungsreihenfolge** | randomisiert über (Fall × Bedingung), Zeitstempel protokolliert |
| **`HUMAN_IN_THE_LOOP`** | in allen drei identisch behandeln. **Vor** dem ersten Messlauf festzulegen (AP-B), nicht erst in AP-H |
| **Schema-Retries** | `max_retries=5` |
| **Umgebung** | dieselbe venv, dieselben Paketversionen — vor der ersten Messung eingefroren (AP-A) |
| **Re-Validierung** | **ausgelöst und abgewartet** in allen drei Bedingungen (siehe 7.1.2) |
| **Zeitpunkt** | **alle drei Bedingungen nach demselben Einfrieren (G5)**, siehe 8.3 |

### 7.1.2 ⚠ Die Re-Validierung war ein falsches Grün — behoben am 19.08.2026

**Der Befund.** `update_snapshot` (PUT) **löscht** die Validierungsmeldungen auf dem Server, und
der Server rechnet **nicht von selbst neu**. `validate_snapshot` führt nur das GET aus. Ohne
einen Trigger las der Re-Validierungsschritt jeder Korrektur-Pipeline deshalb eine **leere
Liste** und meldete `errors=0` — ein **falsches Grün**.

Das war seit AP3.3d in `app/routes/server_validation.py` dokumentiert und im **Review-Pfad**
behoben, aber **nie in die Pipeline verdrahtet**: Weder `sp_agent.py` noch die Runtime-Skripte
riefen `trigger_server_validation()`. Nur die Eval-Skripte taten es.

**Warum das für den Vergleich entscheidend ist.** Die Iterationsschleife in
`execute_pipeline()` liest `final_validation.errors`, um über eine weitere Runde zu
entscheiden — auf Basis einer Zahl, die strukturell immer 0 war. Hätte ich den Trigger **nur**
in den Graph-Knoten eingebaut, dann:

* **A und B**: falsches Grün, Schleife bricht nach Iteration 1 ab
* **C**: echte Zahl, Schleife läuft korrekt

Der Graph hätte anders ausgesehen — **aus einem Grund, der nichts mit Architektur zu tun hat**.
Ein Konfundierungsfaktor, der die gesamte Kategorie 4 (Folgefehler) und die Iterationszahlen
verdorben hätte.

**Behoben an der gemeinsamen Stelle:** Der Trigger sitzt jetzt in
`SPAgent._execute_pipeline()` **und** im Graph-Knoten 7. Damit haben A, B und C dieselbe
fachliche Re-Validierungssemantik. `trigger_server_validation()` ist synchron — es pollt den
Job bis `FINISHED` und liefert `{"ok", "job_id", "status", "waited_s"}`.

> **`errors_after = None` ist NICHT `errors_after = 0`.**
> `None` = keine belastbare neue Validierung (Job offen, gescheitert, Timeout).
> `0` = Validierung nachweislich abgeschlossen **und** fehlerfrei.
> Knoten 8 entscheidet bei `None` auf `stop_uncertain` — lieber keine Zahl als eine veraltete.

**Für Kategorie 4 reicht die Anzahl nicht.** `1 → 1` kann „nichts passiert" heissen oder
„A behoben, B neu erzeugt". Knoten 7 leitet deshalb zusätzlich ab: `errors_resolved`,
`errors_remaining`, `errors_new` und `new_error_types`. Die Fehleridentität ist eine
**Näherung** (Validator-Tag + Hash der Meldung), weil der Server keine Fehler-ID liefert —
als solche im Code ausgewiesen.

### 7.1.3 ⚠ Der Suchkontext konnte veralten — behoben am 20.08.2026

Die zweite gemeinsame Reparatur, gefunden bei der D7-Nachprüfung (BA-024).

`identify_snapshot.py` schrieb die Leerergebnis-Datei nur, **wenn noch keine existierte**.
Fand eine spätere Suche nichts, blieb `last_search_results.json` der **vorigen** Suche stehen
und wurde vom nächsten Schritt als aktueller Kontext gelesen. Nachgestellt: Suche A → 16
Treffer, `results_hash 6d538551…`; danach Suche B ohne Treffer → **derselbe Hash**.

**Betroffen sind alle drei Bedingungen.** `SPAgent.execute_pipeline()` iteriert
(`while True`, `MAX_CORRECTION_ITERATIONS`), und `identify_error_llm.py:504` stösst je
Iteration eine neue Suche an. Ab Iteration 2 hätte das Modell in **A, B und C** den Kontext
der Iteration davor bekommen — und ihn für aktuell gehalten. Für UF1 wäre das eine
Halluzination, die das System nicht verschuldet hat; das Messinstrument hätte den falschen
Gegenstand gemessen (harte Regel 6).

**Behoben in der gemeinsamen Runtime**, nicht im Knoten — Bauregel B. Eine Abfangung im
Knoten hätte nur C geholfen und später wie ein Architektureffekt ausgesehen.
`last_search_results.json` bedeutet jetzt ausnahmslos *Ergebnis der zuletzt ausgeführten
Suche*; die Leerdatei landet zusätzlich im Iterationsordner, wie in den beiden anderen
Zweigen längst üblich.

**Gegenprobe, dass sonst nichts anders wurde:** 8 Suchszenarien über alle drei Suchmodi,
roh- und kanonisch gehasht gegen die Fassung davor — **0 Abweichungen**.

**Anschliessend geschlossen: die Kontextprovenienz.** Knoten 5 lud die Datei ein zweites Mal
von Platte, statt das Objekt aus Knoten 3 zu übernehmen — `results_hash` war damit eine
Behauptung über einen früheren Dateizustand, keine Zusicherung über den Modelleingang.
Jetzt reicht Knoten 3 das Objekt durch, und beide Knoten hashen über **dieselbe** Funktion
`identify_snapshot.context_sha256()`. Dass daraus kein C-Vorteil entsteht, ist per
Prompt-Hash belegt: Nachladen und Durchreichen ergeben denselben Prompt
(205.573 Zeichen, `a4b55f4d…`).

**Was sich unterscheiden darf:** ausschliesslich Pipeline-Architektur und Regelquelle, in der
oben definierten Kombination. Orchestrator, RAG- und Chat-Agent bleiben unverändert.

> ### ⚠ Was hier vorher falsch stand (korrigiert 19.08.2026)
> Die frühere Fassung dieser Tabelle nannte in **einer Zeile** `RULEBOOK_MODE` als zwischen den
> Varianten variiert und in der **nächsten** `SP_ARCHITECTURE_MODE` als „den einzigen bewusst
> variierten Faktor". Das war ein **Selbstwiderspruch**: variiert wurden zwei Dinge gleichzeitig.
>
> Ausserdem war die Zuordnung sachlich falsch: `RULEBOOK_MODE=monolith` als „realer Ist-Zustand"
> zu bezeichnen widerspricht Regel 2, denn produktiv läuft seit dem 12.07.2026 `cards`.
> Eine Baseline mit dem Monolith-Regelwerk wäre der Zustand **davor** gewesen — also genau der
> Strohmann, den Regel 2 verbietet.
>
> Beides ist mit dem Dreiarm-Design behoben: A **ist** der Ausgangszustand und wird als solcher
> benannt, B **ist** der Ist-Zustand, und die Intervention A→C ist ausdrücklich ein Paket.

### 7.2 Das Gedächtnis wird für Messläufe abgeschaltet *(entschieden 16.08.2026)*

**Entscheidung:** Ein neuer Schalter nach dem `RULEBOOK_MODE`-Muster, **in beiden Varianten
identisch auf `off`**.

```python
# app/core/agent_config.py
MEMORY_MODE = os.getenv("MEMORY_MODE", "on").lower()   # "on" | "off" — Default aendert nichts
```

Geprüft an den drei Stellen in `generate_correction_llm.py`, an denen das Gedächtnis heute wirkt
(Abruf `:886-902`, Override `:936-975`, `memory_support` `:1017-1027`). Bei `off`: kein Abruf, kein
Override, `memory_support = 0.0`. **Der Produktionspfad bleibt bei `on` unverändert.**

**Begründung (so in den Methodenteil):**

> Das episodische Gedächtnis wurde in **beiden** Varianten deaktiviert. Es speist frühere
> menschliche Korrekturentscheidungen als Belege in den Prompt und überschreibt bei
> Objektgleichheit den Modellwert deterministisch. Da der Bestand zum Messzeitpunkt objektgenau
> die Sollwerte des Testkatalogs enthält, würde er die Halluzinationsrate beider Varianten gegen
> null drücken und den zu messenden Architekturunterschied überdecken. Das Gedächtnis ist
> ausserdem ein paralleler Ausbaupfad des Systems und nicht Bestandteil der verglichenen
> Architekturen.

**Warum nicht „einfrieren":** Einfrieren entfernt die Kontamination nicht, es verteilt sie
**gleichmässig**. Beide Varianten bekämen die richtige Antwort gereicht, beide Halluzinationsraten
wanderten gegen null — man verliert nicht die Fairness, sondern die **Auflösung**. UF1 wäre
faktisch nicht mehr messbar.

**Optional, falls die Zeit reicht:** ein kleiner Kontrolllauf mit eingefrorenem Bestand als
eigener Nebenbefund („wie stark überdeckt ein Gedächtnis den Architektureffekt?"). Ausdrücklich
als Zusatzmessung kennzeichnen, nicht als Hauptergebnis.

### 7.3 Das Regelwerk bleibt unangetastet — Provenienz statt Umbau

**Die Frage, die dahintersteckt** (Nutzerfrage 18.08.2026): *„Muss ich nicht auch das Regelwerk
in Graphen umwandeln, um später zu sehen, welche Regeln zu Entscheidung X geführt haben — damit
ich sie gezielt optimieren kann?"*

**Das Ziel ist richtig, der Weg wäre falsch.** Dein eigener Betrieb belegt den Bedarf: In
`04_PT4/BEFUNDE_UND_LEHREN.md`, Befund D, berief sich ein Vorschlag auf Artikel „aus demselben
Department (20100)" — alle drei zitierten lagen in **20200**; es waren die Array-Nachbarn.
Gefunden hat das ein Mensch beim Nachrechnen, **weil das System nicht protokollierte, welches
Vergleichskollektiv tatsächlich benutzt wurde**.

**Was du dafür brauchst, ist Provenienz, kein Graph:**

```python
state["matched_rules"]     = {"cards_loaded": [...], "rule_text_hash": ...}   # Knoten 4
state["extracted_context"] = {"lines_used": [...], "field_examples": [...]}   # Knoten 3
```

Zwei Felder im Zustandsobjekt. Ein Graph über dem Regelwerk (Regel→Regel, Regel→Feld,
Regel→Fehlerklasse) wäre eine **eigene, zweite Arbeit** und liefert für diese Frage nichts, was
`matched_rules` nicht auch liefert.

> **Merksatz:** Der Graph beantwortet *„welchen Weg nahm der Prozess?"* — die Provenienz
> beantwortet *„worauf stützte sich Schritt N?"*. Für die zweite Frage genügt ein Feld.

**Die offene Teilfrage: Granularität.** `density-values.md` hat 99 Zeilen und enthält mindestens
fünf unterscheidbare Regeln (Evidenzreihenfolge, Positivitätsbedingung, `min <= max`,
Erfindungsverbot bei < 2 Vergleichbaren, Gruppenfilter).

* **Kartenebene** sagt: *„`density-values.md` war geladen."*
* **Regelebene** sagt: *„Das Modell nahm Evidenzstufe 3 (Median), obwohl Stufe 1 verfügbar war."*

Nur das Zweite trägt gezielte Optimierung. **Teilweise vorhanden:** `04_PT4/AP7-0_rule_inventory.md`
führt **22 Regel-IDs** (R1–R22), aber **nur 4 von 14 Kartendateien** verweisen darauf, und das
Inventar ist als DRAFT gekennzeichnet.

> ### ⚠ Die Falle: das Regelwerk ist eine Kontrollbedingung
>
> Baust du die Karten um, damit feiner protokolliert werden kann, hast du **einen dritten
> Unterschied** zwischen den Varianten — neben Architektur und `RULEBOOK_MODE`. Der Gutachter
> fragt zu Recht: *„Ist der Graph besser, oder hat er nur die besser strukturierten Regeln
> bekommen?"*
>
> Schlimmer: Karten editieren heisst, **den Text zu ändern, den das Modell liest**. Sclar et al.
> (L09) zeigen bis zu 76 Punkte Unterschied durch **bedeutungserhaltende** Formatänderungen.

**Entscheidung (18.08.2026):**

| | Was | Wann |
|---|---|---|
| ✅ | Knoten 4 protokolliert Kartennamen + Hash; Knoten 3 protokolliert das benutzte Vergleichskollektiv | vor dem Baseline-Lauf |
| ❌ | Karten umbauen, Regelwerk-Graph, Regeln umformulieren | gar nicht |
| ⚠ | R-IDs **ausschliesslich ins Frontmatter**, das vor der Prompt-Injektion entfernt wird — **nur mit Nachweis, dass der injizierte Prompt byte-identisch bleibt** (Hash vorher/nachher). Ohne diesen Nachweis: nicht anfassen | optional, vor dem Einfrieren, für **beide** Varianten identisch |

Start mit **Kartenebene**. Ob sie reicht, hängt davon ab, wie oft mehrere Regeln *derselben* Karte
in Frage kommen — das siehst du erst am ersten Trace. Nach dem Durchstich entscheiden.

---

## 8. Regressionsreferenz und Einfrieren

> ### ⚠ Was AP-B ist — und was es NICHT ist (korrigiert 19.08.2026)
> Die frühere Fassung nannte den Baseline-Lauf „die Zahl, gegen die alles Weitere verglichen
> wird". **Das war ein Konstruktionsfehler.** In AP-G wird danach das Regelwerk optimiert; eine
> vor dieser Optimierung erhobene Zahl ist unter **anderen** Bedingungen entstanden und taugt
> nicht als Vergleichsbasis.
>
> **Richtig ist:**
> * **AP-B ist die Regressionsreferenz.** Sie beantwortet *„läuft das System noch wie vorher,
>   hat der Umgebungswechsel etwas verändert?"* — nicht *„wie gut ist der Monolith?"*.
>   Deshalb kann AP-B **kurz** gehalten werden.
> * **Die wissenschaftlichen Zahlen für Kapitel 7 entstehen ausschliesslich in AP-H**, nach dem
>   Einfrieren (G5), für **alle drei Bedingungen A, B und C gemeinsam** und unter identischen
>   Bedingungen.
>
> Wer diese Trennung nicht macht, vergleicht Messungen aus zwei verschiedenen Systemzuständen.

### 8.1 Die `RULEBOOK_MODE`-Falle

**Der Default ist `"cards"`, nicht `"monolith"`.** Ein Baseline-Lauf ohne ausdrückliches
`RULEBOOK_MODE=monolith` misst **nicht** den Monolithen. Laut Kap. 4.9 lief bisher **jeder**
Eval-Lauf unter `cards`.

**Vorgehen:**

1. ✅ **Erledigt (16.08.):** Für jede bestehende Ergebnisdatei ist der Modus verifiziert — alle
   `cards`, alle drei Eval-Skripte erzwingen ihn hart im Code.
2. **Offen:** Einen sauberen Baseline-Lauf mit explizit `RULEBOOK_MODE=monolith`, `MEMORY_MODE=off`
   und GPT-4.1 über beide Kataloge fahren, **bevor** der Graph zum ersten Mal gemessen wird. Das
   ist der tatsächliche Monolith-Referenzwert.
3. Für die Graph-Variante ist `RULEBOOK_MODE=cards` die korrekte, architektonisch begründete
   Einstellung (Knoten 4 **ist** die selektive Regelzuordnung).

### 8.2 Was als Baseline-Artefakt archiviert werden muss

Zum Messzeitpunkt festhalten: vollständiger Text von `llm-validation-fix-rules.md` (Hash + Kopie),
exakter Prompt-Aufbau aus `generate_correction_llm.py`, Deployment + API-Version, sowie **alle**
Umgebungsvariablen-Werte: `RULEBOOK_MODE`, `SP_ARCHITECTURE_MODE`, `MEMORY_MODE`,
`HUMAN_IN_THE_LOOP`, `AZURE_OPENAI_DEPLOYMENT`.

Ebenfalls dokumentieren: exakte Zeilen-/Zeichenzahl des Regelwerks (heute 936 / 36.165), Modell,
Temperatur, API-Version. Diese Werte gehören als Tabelle ins Methodenkapitel.

### 8.3 Die Pilotphase — kalibrieren, dann einfrieren, dann messen

**Entscheidung 18.08.2026.** Regel 5 verbietet Änderungen *während* und *nach* der Messung.
**Vor** der Messung sind sie schlicht Entwicklung. Das ist saubere empirische Praxis und heisst
Pilot- oder Kalibrierungsphase.

```
Pilotläufe → optimieren → Pilotläufe → optimieren → ██ EINFRIEREN ██ → messen
                                                       ↑
                                ab hier ändert sich am Regelwerk nichts mehr,
                                und beide Varianten bekommen dieselbe Fassung
```

#### ⚠ Die Falle: nicht auf dem Messkatalog optimieren

Wer mit denselben 17 Fällen optimiert, mit denen er später misst, hat **auf die Testmenge hin
trainiert**. Die Halluzinationsrate misst dann nicht die Architektur, sondern die Anpassungsgüte
an genau diese Fälle. Ein Gutachter mit ML-Hintergrund sieht das sofort.

**Lösung, und sie kostet fast nichts:** Auf **anderen Fällen** optimieren. `build_test_catalog.py`
legt Snapshots live über die API an — für die Pilotphase frische Fälle mit **anderen Entitäten**
bauen. Die 17 Messfälle bleiben unberührt.

> **Faustregel: Ein Snapshot, den die Pilotphase gesehen hat, ist als Messfall verbrannt.**

Zu beachten: Das Gedächtnis ist objektbezogen — Pilotfälle müssen auch **andere `articleId`/
`demandId`** verwenden, nicht nur andere Snapshot-IDs, sonst wirkt der Bestand in die Messung
hinein (Kap. 4.10).

#### Der Nebeneffekt, der in die Diskussion gehört

Kontraintuitiv, aber real: **Die Pilotphase lässt den Graphen in der Messung schwächer
aussehen.** Sie erntet seinen Hauptnutzen vorab. Wird über den Trace erkannt „Knoten 5 wählt
systematisch die falsche Evidenzstufe" und die Regelkarte entsprechend präzisiert, profitieren
danach **beide** Varianten — der bei UF1 messbare Unterschied schrumpft.

Kein Grund, es zu lassen. Aber es gehört in Kapitel 8, und zwar so:

> „Die vorgelagerte Kalibrierungsphase behob N Regeldefekte, die über den Graph-Trace lokalisiert
> wurden. Beide Varianten profitierten davon gleichermassen; der gemessene
> Halluzinationsunterschied ist dadurch **konservativ**."

Das ist ein starker Satz — er zeigt, dass der Effekt verstanden wurde, und macht den Befund
glaubwürdiger statt schwächer.

#### Was protokolliert werden muss

Pilotläufe sind **keine Ergebnisse** und dürfen nie als solche berichtet werden. Für Kapitel 9
sind sie trotzdem wertvoll. Eigene Protokollkategorie **`Status: pilot`**, je Änderung:

* welche Regel geändert wurde, **warum**, und **welcher Trace** es gezeigt hat
* Fassung des Regelwerks vorher/nachher (**Hash**)
* auf welchem Pilotfall — mit dem Nachweis, dass er **nicht** im Messkatalog ist

#### Der Ertrag: das ist Kapitel 9

Die Optimierungsschleife ist nicht nur zulässig, sie ist der **praktische Beitrag** (F9). Nach der
Hauptmessung an ein bis zwei dokumentierten Fällen demonstrieren:

> „Der Trace zeigte in 4 von 7 Komplexfällen, dass Knoten 5 Evidenzstufe 3 wählte, obwohl Stufe 1
> verfügbar war. Eine gezielte Präzisierung von R22 behob das im Nachlauf. Beim Monolithen wäre
> diese Lokalisierung nicht möglich gewesen."

Das belegt UF3 **praktisch** statt nur strukturell — als **Nachmessung gekennzeichnet**.

---

## 9. Die neun Knoten

Der Schnitt folgt dem Kriterium aus Kap. 5.2: **eine Grenze dort, wo ein eigener Fehlermodus
beobachtbar wird.** Spalte „macht messbar" ist die Begründung — sie gehört so in Kapitel 4.

| # | Knoten | Ein-/Ausgang | macht messbar | Bestehender Code | Zu tun |
|---|---|---|---|---|---|
| 1 | **Eingabeanalyse** | Snapshot-ID → Aufgabenbeschreibung | — (Einstieg) | kein dedizierter Code | dünner Wrapper, **kein LLM-Call** |
| 2 | **Fehlerklassifikation** | Validierungsergebnis → Tag/Priorität/Begründung | *falscher Fehler priorisiert* — bei mehreren Fehlern zurechenbar | `identify_error_llm.py` — **macht heute mehr** (wählt zusätzlich Suchmodus UND Regelkarten) | `analyze_validation_with_llm()` ist bereits aufrufbar; Kartenauswahl wandert konzeptionell zu Knoten 4 |
| 3 | **Kontextsuche** | Fehler → Kontextfenster | *leerer/falscher Kontext* — real beobachtet (fehlende `last_search_results.json`) | `identify_snapshot.py` (1186 Z.), **ohne Gesamt-Einstiegsfunktion** | **grösster Entflechtungsaufwand**: Funktion aus `main()` (Z. 888-1185) herausziehen |
| 4 | **Regelzuordnung** | klassifizierter Fehler → relevante Regeln | **Regelhalluzination (Kat. 3)** — nur hier zurechenbar, weil `matched_rules` festhält, welche Karte geladen wurde | `rulebook_loader.load_rulebook()` im `cards`-Modus — **1:1 nutzbar**, heute in Knoten 2/5 versteckt | als eigenen, **geloggten** Schritt exponieren |
| 5 | **Korrekturgenerierung** | Kontext + Regeln → JSON-Vorschlag | **Fachliche Halluzination (Kat. 1)** | `generate_correction_with_llm(...)` — **bereits aufrufbar, nimmt genau die Knoten-Eingänge** | Wrapper; Gedächtnis per `MEMORY_MODE` aus |
| 6 | **Technische Prüfung** | Vorschlag → Schemastatus | **Strukturelle Halluzination (Kat. 2)** | `validate_with_retry(...)` — **1:1 nutzbar** | Funktions-Wrapper |
| 7 | **Anwendung & Re-Validierung** | geprüfter Vorschlag → `errors_after` | **Folgefehlererzeugung (Kat. 4)** | `apply_correction()`, `update_snapshot`, `validate_snapshot()` — alle aufrufbar | Wrapper; erzeugt den Wert, den Knoten 8 braucht |
| 8 | **Ergebnisbewertung** | `errors_after` + Schemastatus → `decision` | **UF2-Grenzfallverhalten** (`stop_uncertain` statt erzwungener Korrektur) | heute reine `if/else`-Logik in `sp_agent.py:626-679` | **echter Knoten**, der `decision` in den State schreibt — siehe Kasten unten |
| 9 | **Ausgabe / Finalisierung** | finaler Zustand → variantenneutrales Endergebnis | — (Ausgabe) | **kein** bestehender Schritt — `generate_audit_report` ist in **keiner** Monolith-Pipeline | **deterministisch** über `app/core/ergebnis_format.py`, **kein LLM** (geändert 20.08.2026, BA-031) |

> **Zwei bewusste Abweichungen vom Vorgängerplan — beide mit Grund.**
>
> **(a) Knoten 7 ist neu.** Der Altplan kannte acht Knoten, die beim Korrekturvorschlag endeten —
> aber seine bedingte Kante fragte nach `errors_after`, **das niemand erzeugte**. Ohne Anwendung
> und Re-Validierung gibt es diesen Wert nicht, und damit weder die Iterationsschleife noch die
> Messung der Folgefehler (Kategorie 4). Das war ein Loch, kein Detail.
>
> **(b) Knoten 8 ist ein Knoten, keine Kante.** Der Altplan modellierte die Ergebnisbewertung als
> die bedingte Kante selbst. Für eine Arbeit über **Nachvollziehbarkeit** ist das die schlechtere
> Wahl: Eine Kante hinterlässt keinen Zwischenzustand, auf den man zeigen kann. Als Knoten
> schreibt sie `decision` samt Begründung in den `GraphState`, und der Router liest nur noch
> `state["decision"]["action"]`. Damit ist die Entscheidung **selbst** ein prüfbares
> Zwischenergebnis — genau das, was der Monolith nicht hat.

**Die gute Nachricht für den Zeitplan:** Acht der neun Knoten existieren im Kern bereits als
aufrufbarer Code. Die Arbeit besteht **nicht** darin, sie neu zu erfinden, sondern sie in einen
expliziten, zustandsbehafteten Graphen zu überführen und ihre Zwischenzustände sichtbar zu machen.

**Falls die Zeit knapp wird**, ist der Schnitt reduzierbar: Knoten 3 und 4 lassen sich
zusammenlegen (beide deterministisch), Knoten 9 kann entfallen. **Nicht reduzierbar sind 4, 5, 6
und 7** — an ihnen hängt je eine Halluzinationskategorie. Eine Reduktion ist im Methodenteil
auszuweisen.

### 9.0 Verantwortungsschnitt Knoten 2 / 3 / 4 *(festgelegt 19.08.2026, vor AP-D6)*

**Befund am Code.** `identify_error_llm.py` erledigt heute die Aufgaben von **drei** Knoten.
Sein LLM-Aufruf liefert in **einer** Antwort:

| Feld | gehört fachlich zu |
|---|---|
| `selected_error_index`, `selected_error`, `prioritization_reasoning` | **Knoten 2** — Klassifikation und Priorisierung |
| `search_mode`, `search_value`, `should_investigate` | **Knoten 3** — Suchstrategie |
| **`relevant_cards`, `relevant_cards_reasoning`** | **Knoten 4** — Regelzuordnung |

Zusätzlich ruft `main()` über `trigger_identify_tool()` direkt `identify_snapshot.py` auf —
**Knoten 2 führt heute also auch Knoten 3 aus.**

**Der festgelegte Schnitt:**

* **Knoten 2 (D6)** — ruft `analyze_validation_with_llm()` mit **unverändertem Prompt** auf und
  schreibt das Ergebnis in `classified_error`, einschliesslich `search_mode`, `search_value` und
  `relevant_cards`. **Er führt die Suche NICHT mehr aus.**
* **Knoten 3 (D7)** — nimmt `search_mode`/`search_value` aus dem State und führt die Suche aus.
  Schreibt `extracted_context` samt benutztem Vergleichskollektiv (fängt Befund D ab).
* **Knoten 4** — **die einzige Stelle, die Karten auflöst und protokolliert.**
  `select_cards(tag, extra_cards=classified_error["relevant_cards"])`.

> **Damit wählen Knoten 2 und 4 NICHT unabhängig voneinander Karten aus.**
> Genau formuliert:
>
> * **Knoten 2 schlägt zusätzliche Karten vor** (`relevant_cards`, in Fachsprache und ohne
>   Tag-Kenntnis — dafür war das Feld in AP7.5 gedacht). Er lädt nichts und protokolliert nichts.
> * **Knoten 4 löst diese Vorschläge zusammen mit der deterministischen Tag-Zuordnung zum
>   tatsächlich verwendeten Kartensatz auf, lädt ihn und protokolliert ihn** (`matched_rules`
>   mit `cards_loaded`, `rule_text`, `rule_text_hash`).
>
> Beide Wege laufen in **`select_cards()`** zusammen — genau eine Auflösungsstelle. Was das
> Modell in Knoten 5 zu sehen bekommt, ist ausschliesslich das, was Knoten 4 aufgelöst hat.

> ### ⚠ Der Prompt von Knoten 2 wird NICHT geändert — und das ist eine bewusste Entscheidung
> Architektonisch sauberer wäre, `relevant_cards` aus dem Prompt zu entfernen und die Auswahl
> allein Knoten 4 zu überlassen. **Das wird nicht getan.**
>
> Grund: Der Prompt von Knoten 2 ist in **A, B und C identisch** — er ist Teil der
> Kontrollbedingungen (Kap. 7.1.1). Ihn nur für C zu ändern, hiesse, die Varianten in etwas zu
> unterscheiden, das **nicht** die Orchestrierung ist. Der gemessene Unterschied wäre dann
> teilweise ein Prompt-Unterschied — und L09 (Sclar et al.) zeigt, wie gross solche Effekte
> werden können.
>
> **Die Trennung ist eine Zuständigkeits-, keine Prompt-Änderung.** Falls der Prompt später
> doch angepasst werden soll, ist das eine **Architekturänderung** und gehört vorher hierher —
> nicht still in einen Commit.

### 9.1 Wann die Knotenzahl entschieden wird — drei Zeitpunkte

Nur der letzte ist bindend.

| Zeitpunkt | Was gilt |
|---|---|
| **Jetzt** | Neun Knoten als **Arbeitshypothese**, mit dokumentiertem Kriterium (Kap. 5.2) |
| **Nach dem vertikalen Durchstich** | **Der ehrliche Entscheidungspunkt.** Erst wenn ein Fall einmal komplett durchgelaufen ist, weisst du, ob der Schnitt trägt |
| **Vor dem ersten gemessenen Graph-Lauf** | **Einfrieren.** Die Struktur danach zu ändern hiesse, alles neu zu messen |

Was am Durchstich realistisch zu einer Änderung zwingen könnte:

* **Knoten 3** (`identify_snapshot`, ~300 Zeilen Ablaufsteuerung in `main()`) erweist sich als zu
  verwoben → 3 und 4 zusammenlegen
* **Knoten 2** lässt sich nicht sinnvoll von seiner Kartenauswahl trennen → MVP-Variante,
  dokumentiert
* **Knoten 9** erweist sich als für den Vergleich irrelevant → streichen

Jede Abweichung von den neun wird **hier im Plan vermerkt**, bevor sie umgesetzt wird — nicht
still getroffen.

**Pragmatische MVP-Entscheidung:** Knoten 2 sauber von seiner heutigen Kartenauswahl zu trennen ist
ein echter Eingriff. Baue die erste Version so, dass Knoten 2 das bestehende Skript **als Ganzes**
aufruft (inkl. heutiger Kartenauswahl) und dokumentiere das als **bewusste Vereinfachung** — das ist
kein Strohmann, weil es derselbe unveränderte Code ist, nur noch nicht granular aufgeteilt.
Verfeinerung in einer zweiten Iteration, falls die Zeit reicht.

---

## 10. `GraphState`

```python
from typing import TypedDict, Literal, Optional

class GraphState(TypedDict):
    # Identität und Lauf-Metadaten
    snapshot_id: str
    iteration: int
    max_iterations: int
    architecture_mode: Literal["graph"]
    started_at: str                    # ISO-8601 UTC
    finished_at: Optional[str]

    # Fehlerzustand
    errors_before: int
    errors_after: Optional[int]
    validation_result: Optional[dict]

    # Knoten-Ausgänge (jeder Knoten schreibt genau sein Feld)
    classified_error: Optional[dict]      # {tag, priority, reasoning, raw_message}
    extracted_context: Optional[dict]     # {target_path_hint, field_examples, lines_used, search_mode}
    matched_rules: Optional[dict]         # {rulebook_mode, cards_loaded: list[str], rule_text_hash}
    correction_proposal: Optional[dict]   # {action, target_path, new_value, reasoning, llm_confidence}
    technical_check: Optional[dict]       # {schema_valid, retries, errors: list}
    applied: Optional[dict]               # Knoten 7: {applied_ok, uploaded, new_error_types: list}
    decision: Optional[dict]              # Knoten 8: {action: "continue"|"stop_valid"|"stop_max_iter"|"stop_uncertain", reasoning}
    manual_intervention_required: bool

    # Nachvollziehbarkeits-Instrument — das wichtigste Feld für UF3
    trace: list[dict]   # je Eintrag: {node, timestamp_utc, input_digest, output_digest, duration_ms}
```

**Warum `trace` das Kernstück ist:** Es ist der rekonstruierbare Entscheidungspfad, den der
Monolith per Definition nicht hat. Jeder Knoten hängt seinen Eintrag an — das ist dein **primäres
Beweismittel für UF3**.

**Darstellung für die Bewertung:** nicht als rohes JSON, sondern nach MindMap-Vorbild als lesbare
Kette „Knoten → Eingabe → Entscheidung → nächster Knoten" (Kap. 5.3).

---

## 11. Kanten und Kontrollfluss

```
START → [1 Eingabeanalyse] → [2 Fehlerklassifikation] → [3 Kontextsuche] → [4 Regelzuordnung]
      → [5 Korrekturgenerierung] → [6 Technische Prüfung]
                                     (Schema-Retries laufen INNERHALB des Knotens)
                                          │
                          schema_valid?   ├── nein ──▶ [8] ──▶ "stop_uncertain" ──▶ [9]
                                          │
                                          ja
                                          ▼
      [7 Anwendung & Re-Validierung] → [8 Ergebnisbewertung] → Router liest decision.action
                    ▲                                                   │
                    └── (über [2]) ─── "continue" ──────────────────────┤
                                                                        ▼
                                                              [9 Antwortformulierung] → END
```

**Zwei bedingte Kanten statt einer:**

**(A) nach Knoten 6** — rein technisch, ohne Zustandsbewertung:

| Bedingung | Ziel |
|---|---|
| `technical_check.schema_valid == True` | weiter zu **[7]** |
| `technical_check.schema_valid == False` | weiter zu **[8]** → `"stop_uncertain"` |

> ### ⚠ Es gibt KEINE Rückkante 6→5 (korrigiert 19.08.2026)
> Die frühere Fassung sah vor: *„`schema_valid == False` und **Retries übrig** → zurück zu [5]"*.
> **Das war ein Konstruktionsfehler.**
>
> `validate_with_retry(..., max_retries=5)` führt die technischen Schema-Retries **vollständig
> innerhalb von Knoten 6** aus — inklusive erneutem LLM-Aufruf mit dem Schemafehler. Eine
> zusätzliche Graph-Kante 6→5 wäre eine **zweite Retry-Schicht** über der bestehenden: bis zu
> 5 interne × N Graph-Durchläufe. Der Graph verhielte sich damit **anders als der Monolith**,
> und zwar in einer Dimension, die gar nicht Gegenstand des Vergleichs ist. Ein
> Konfundierungsfaktor, den niemand bemerkt hätte.
>
> **Die verbindliche Aufteilung der Verantwortung:**
>
> | Ebene | Zuständig | Wofür |
> |---|---|---|
> | **innerhalb Knoten 6** | `validate_with_retry` | **technische** Schemafehler — bis zu `max_retries` LLM-Korrekturversuche |
> | **Kante 8→2** | Router | **fachliche** Korrekturiteration, erst **nach** Re-Validierung des Snapshots (`errors_after > 0`) |
>
> Knoten 6 gibt nach erschöpften Retries schlicht `schema_valid=False` zurück; der Graph geht
> dann über Knoten 8 auf `stop_uncertain`. **Die Rückkante 8→2 existiert ausschliesslich für
> eine neue fachliche Iteration** — nie für denselben Schemafehler.
>
> **`retries` im `technical_check` bedeutet:** *Zusatzversuche **nach** dem ersten*, also die Zahl
> der tatsächlich ausgeführten LLM-Retries. `0` = beim ersten Versuch gültig; die Obergrenze ist
> `max_retries`. *(Der Zähler meldete anfangs um eins zu hoch, weil `retry_count` vor der
> Schranke erhöht wird — am 19.08. korrigiert und geprüft.)*

**(B) nach Knoten 8** — der Router liest nur noch das, was Knoten 8 in den State geschrieben hat:

| `decision.action` | gesetzt von Knoten 8, wenn … | Ziel |
|---|---|---|
| `"stop_valid"` | `errors_after == 0` | **[9]** |
| `"continue"` | `errors_after > 0` und `iteration < max_iterations` | zurück zu **[2]** mit aktualisiertem `validation_result` |
| `"stop_max_iter"` | `iteration >= max_iterations` | **[9]**, `manual_intervention_required = True` |
| `"stop_uncertain"` | Knoten 2/5 lieferte kein `target_path`, oder Schemaprüfung endgültig gescheitert | **[9]** |

**Warum die Trennung wichtig ist:** Der Router enthält **keine** Fachlogik — er ist ein
`switch` über ein Feld, das ein sichtbarer Knoten gesetzt hat. Damit ist jede Verzweigung im
`trace` begründet nachlesbar. Ein Router mit eingebauter `if/else`-Kette wäre wieder genau der
implizite Kontrollfluss, den die Arbeit dem Monolithen vorwirft.

Der Fall `stop_uncertain` ist **kein ausgedachter Sonderfall** — er formalisiert real beobachtetes
Verhalten (`target_path=None`-Fälle aus den bisherigen Läufen). **Für UF2 ist genau das der positiv
zu wertende „ehrliches Nein statt halluzinierter Korrektur"-Pfad.**

**Fehlerbehandlung an jedem Knoten:** Definiere, was bei unerwarteter oder unsicherer Eingabe
passiert. Die fachlich saubere Antwort ist häufig, **Unsicherheit transparent auszuweisen statt
eine scheinbar plausible Korrektur zu erzwingen** — das Exposé nennt das ausdrücklich als
Qualitätsmerkmal.

---

## 12. Technische Umsetzung — Schritt für Schritt

### 12.1 Dependencies

**Zuerst** den bestehenden Konflikt lösen: `app/deploy/requirements.txt` pinnt
`openai>=1.6.0,<2.0.0`, installiert ist `2.14.0`. Erst danach ergänzen und **pinnen**:

```
langgraph==<version>
langchain-core==<version>
```

Versionen unmittelbar vor der Installation auf PyPI verifizieren (die Angaben der Vorgängerpläne
sind vom 02.08. und nicht mehr belastbar). Danach `pip install`, dann **Smoke-Test**: mindestens
ein vollständiger Monolith-Pipeline-Lauf, um sicherzustellen, dass nichts bricht. `pydantic 2.12.4`
ist der wahrscheinlichste Konfliktpunkt und zuerst zu prüfen.

### 12.2 Node-Kapselung: additive Funktionsextraktion

Jedes wiederzuverwendende Skript bekommt **eine neue, zusätzliche** aufrufbare Funktion, ohne die
bestehende CLI-`main()` zu verändern:

```python
# NEU, additiv — main() ruft diese Funktion jetzt auf, Verhalten bleibt identisch:
def run_correction_generation(snapshot_id, target_context, rules_text, ...) -> dict:
    """Kernlogik, aufrufbar von main() (CLI/Subprocess) UND vom Graph-Knoten (Direktaufruf)."""
    ...
    return proposal_dict

def main():
    args = parser.parse_args()
    result = run_correction_generation(args.snapshot_id, ...)
    # Datei schreiben, stdout ausgeben — wie bisher
```

**Warum das der richtige Weg ist:** Danach existiert nur **eine** Implementierung der Kernlogik
(kein Drift zwischen „CLI-Version" und „Graph-Version"), und der Monolith-Pfad ist von der
Umstellung **null** betroffen — er ruft intern nur eine Ebene tiefer.

**Reihenfolge** (nach tatsächlichem Aufwand, siehe Kap. 4.5):

1. **Knoten 6** — `validate_correction_schema_llm` ist schon aufrufbar. Einfachster Einstieg, gut
   zum Muster-Festigen.
2. **Knoten 5** — `generate_correction_with_llm()` ist schon aufrufbar und nimmt genau die
   Knoten-Eingänge. Der wichtigste Knoten.
3. **Knoten 7** — `apply_correction()` und `validate_snapshot()` sind beide aufrufbar; nur
   `update_snapshot` braucht einen Wrapper. Früh dran, weil erst danach `errors_after` existiert
   und die Schleife überhaupt geschlossen werden kann.
4. **Knoten 4 und 8** — reiner Neucode, kein Extraktionsaufwand: `load_rulebook()` aufrufen und
   protokollieren bzw. die `if/else`-Logik aus `sp_agent.py:626-679` in eine Funktion überführen,
   die `decision` schreibt.
5. **Knoten 9** — `generate_audit_report_with_llm()`, aufrufbar.
6. **Knoten 2** — `analyze_validation_with_llm()` aufrufbar; Persistenz aus `main()` lösen.
7. **Knoten 3** — `identify_snapshot.py`. **Der eigentliche Aufwand.** ~300 Zeilen
   Ablaufsteuerung in `main()`, keine Gesamt-Einstiegsfunktion.

### 12.3 Dateilayout

Neues Verzeichnis, komplett additiv:

```
app/tools/smart-planning/graph/
    __init__.py
    graph_state.py           # Kapitel 10
    correction_graph.py      # StateGraph, Knoten-Registrierung, Kanten (Kapitel 11)
    nodes/
        __init__.py
        input_analysis.py    # Knoten 1
        classification.py    # Knoten 2
        context_search.py    # Knoten 3
        rule_matching.py     # Knoten 4
        correction.py        # Knoten 5
        technical_check.py   # Knoten 6
        apply_revalidate.py  # Knoten 7
        evaluation.py        # Knoten 8 — schreibt decision, entscheidet NICHT im Router
        answer.py            # Knoten 9
```

### 12.4 Trace-Persistenz

Jeder Knoten hängt einen Eintrag an `state["trace"]`. Nach jedem vollständigen Graph-Lauf den
kompletten `GraphState` als JSON in die Iterationsordner-Struktur schreiben, analog zu
`metadata.txt` im Monolith-Pfad. **Das ist deine Rohdatenbasis für Kapitel 17.**

Zusätzlich: `graph.get_graph().draw_mermaid()` einmal ausführen und die Ausgabe als
Architekturabbildung in Kapitel 4 der Arbeit übernehmen — eine Abbildung, die beweisbar den echten
Kontrollfluss zeigt.

### 12.5 Visualisierung, State-Tracking und Debuggen

Vier Darstellungen, drei davon geschenkt.

| Was | Wozu | Aufwand |
|---|---|---|
| **Struktur (statisch)** — `get_graph().draw_mermaid()` | Architekturabbildung für Kapitel 4, **erzeugt aus dem kompilierten Graphen** statt nachgezeichnet | eine Zeile |
| **Zustand je Knoten (live)** — LangGraph gibt den Zustand nach jedem Knoten heraus statt nur das Endergebnis | Beim Debuggen zusehen, wie sich `matched_rules`, `correction_proposal`, `decision` füllen | eine Zeile |
| **Wiederabspielen** — Checkpointing | Einen Lauf an einem Knoten anhalten und von dort neu starten. Nützlich, wenn ein Fall reproduzierbar an derselben Stelle abbiegt | Konfiguration |
| **Lesbare Trace-Kette** — selbst gebaut | **Das wertvollste Artefakt der Arbeit.** Siehe unten | ein Nachmittag |

> Die genauen Signaturen bei der Installation prüfen — LangGraph 1.x ist jung. Dass die
> Fähigkeiten existieren, ist sicher; wie die Methoden heissen, an der gepinnten Version
> verifizieren.

#### Die lesbare Trace-Kette

Nach dem MindMap-Vorbild (L02) — nicht rohes JSON, sondern:

```
Fehler [validate_density_values] articles[0].relDensityMin
  -> Knoten 2  klassifiziert als DENSITY_VALUES         (0.9 s)
  -> Knoten 3  Kontext: 331 Artikel Department 20100    (1.2 s)
  -> Knoten 4  Regeln: _core.md + density-values.md     (0.0 s)
  -> Knoten 5  Vorschlag 1.14 · Evidenzstufe 3 (Median)
  -> Knoten 6  Schema gültig
  -> Knoten 7  errors_after = 0
  -> Knoten 8  stop_valid
```

Zahlt dreifach: **Debugging-Werkzeug**, **Abbildung in Kapitel 7**, und das **Artefakt, an dem der
Nachvollziehbarkeitsunterschied gezeigt wird**.

#### Debuggen — der konkrete Unterschied (das ist der UF3-Befund)

Realer Fall aus `04_PT4/BEFUNDE_UND_LEHREN.md`, Muster 1: `identify_error_llm` meldete Erfolg,
obwohl die Suche nichts erzeugt hatte. Der Absturz kam **zwei Schritte später** in
`generate_correction_llm` („`last_search_results.json` fehlt"), und die Fehlermeldung riet dem
Nutzer, einen Schritt nachzuholen, der gerade gelaufen war.

| | Monolith | Graph |
|---|---|---|
| Was man sieht | Absturz in Schritt 3 | `node_context_search -> results_count=0` |
| Wie man die Ursache findet | stdout dreier Subprozesse zusammensuchen, Iterationsordner durchsehen, raten | im `trace` ablesen |
| Was das System tut | zwei Schritte später abstürzen | als `stop_uncertain` sauber beenden |

**Das ist die Messvorschrift für UF3**, nicht ein Gefühl: Kann bei einer falschen Korrektur der
Abzweig lokalisiert werden? Monolith praktisch nie, Graph über den `trace`.

#### ⚠ Externe Tracing-Dienste: nein

Für LangGraph existieren kommerzielle Tracing-Dienste (LangSmith und Ähnliche). Die senden
**Prompts und Daten an einen externen Anbieter**. Bei Smart-Planning-Snapshots ist das eine
Datenschutzfrage, keine Komfortfrage — Kapitel 24 erlaubt nur anonymisierte oder freigegebene
Daten. **Lokales Tracing ins Dateisystem reicht für alles Genannte.**

---

## 13. Testfallkatalog — Stand, Lücken, Zielgrösse

### 13.1 Was vorhanden ist — genauer gezählt als „10+10"

| Katalog | Fälle | Tatsächlich |
|---|---|---|
| `isolated-error-snapshots/` | 10 | 10 Einzelfehler, **10 verschiedene Validatoren** (I01–I10) |
| `kombinierte-fehler-snapshots/` | 10 | **01–03 sind Einzelfehler** und wiederholen die Klassen von I01–I03; wirklich mehrfehlerhaft sind nur **04–10** (7 Fälle mit 2–3 Fehlern) |

**→ 17 distinkte Fälle, davon 3 redundant.** Die Vorgängerpläne rechneten mit 20.

**Fehlerklassen (`[validate_*]`-Tags):** `unique_ids`, `demand_article_ids`, `density_values`,
`work_plan_ids`, `article_department_presence`, `article_equipment_department_consistency`,
`work_item_configs_completeness`, `start_end_operation_existence`,
`work_item_equipment_availability`, `packaging_references`, `equipment_predecessor_references`,
`equipment_worker_qualification_compatibility`, `packaging_equipment_compatibility_references`.

### 13.2 Was fehlt

* **Wiederholungsläufe für UF2.** Aktuell läuft jeder Fall genau **einmal**. Für die
  Konsistenzmessung braucht es denselben Fall **3–5×** mit identischer Eingabe, für **beide**
  Varianten. Dafür ein Skript `run_repeated_suite.py`, das die **fachlichen** Korrekturwerte
  vergleicht, nicht die Formulierung.

  ⚠ **Blocker, der vorher zu lösen ist:** `HUMAN_IN_THE_LOOP` ist `true` als Default, und
  `generate_correction_llm.open_proposal_blocking()` bricht mit **Exit-Code 3** ab, solange für
  denselben Snapshot ein Vorschlag offen ist. **Ab Durchgang 2 desselben Falls läuft der Wrapper
  sonst ins Leere.** Lösung in beiden Varianten identisch und dokumentiert.

* **Grenzfälle.** Aktuell **keine**. Für UF2 braucht es mindestens eine Handvoll Fälle, bei denen
  „keine Korrektur erzwingen, sondern Unsicherheit ausweisen" die richtige Antwort ist: fehlende
  Pflichtfelder, unbekannte Feldwerte, strukturell abweichende Snapshots.

* **Zielgrösse:** 15–30 distinkte Fälle über die Klassen verteilt. Bei 17 bist du im unteren
  Bereich — die Lücke liegt genau bei den UF2-Fällen.

### 13.3 Die Statistik-Falle

Kleine Fallzahlen erlauben keine belastbaren Raten. Aus PT4 ist bekannt, dass Aussagen bei n < 10
statistisch nicht tragen. Für die Arbeit heisst das:

* Pro Fehlerklasse **mehrere Instanzen**, nicht eine.
* **Wiederholungen** einplanen — Robustheit *ist* die Streuung über Wiederholungen.
* **Ehrlich rechnen:** Eine grosse Stichprobe ist nicht zu schaffen. Das ist für eine
  Bachelorarbeit völlig in Ordnung — aber es muss als **Limitation** benannt und die Formulierung
  angepasst werden: „deskriptiver Vergleich" statt „statistisch signifikant".
  **Ein Gutachter verzeiht kleine n; er verzeiht keine Überinterpretation kleiner n.**

---

## 14. Ground-Truth-Methodik

**Die Methode:** Fehler gezielt in Snapshot-Kopien injizieren, den Originalwert als Ground Truth
festhalten. Damit ist für injizierte Fälle objektiv messbar, ob eine Korrektur *richtig* ist —
nicht nur „valide". Das Exposé benennt genau dieses Messproblem als offen („Da keine automatisierte
Ground-Truth-Validierung existiert…"), **also ist die Methode selbst ein methodischer Beitrag** und
beantwortet UF1 teilweise direkt.

> ⚠ **Korrektur gegenüber den Vorgängerplänen.** Beide nennen `app/eval/build_test_catalog.py` als
> *das* Werkzeug. Tatsächlich:
> * Es enthält vier Injektoren, von denen nur **drei** in `CATALOG` aktiv sind
>   (`inject_empty_demand_id` ist definiert, aber nicht eingetragen), und es legt Snapshots
>   **live über die API** an.
> * Die 10+10 Fälle auf Platte stammen aus **PowerShell-Skripten**
>   (`generate-isolated-error-snapshots.ps1`, `generate-error-snapshots.ps1`); ihre Ground Truth
>   liegt in `expected-results.json` bzw. `ERROR-SNAPSHOTS.md`, **nicht** in
>   `metadata.txt.injected_error`.
>
> **Es gibt also zwei Ground-Truth-Mechanismen nebeneinander.** Das Methodenkapitel muss den
> beschreiben, der tatsächlich verwendet wird. Für neue Fälle (Grenzfälle, Wiederholungen) ist
> **einer** davon zu wählen und durchzuhalten.

**Ehrlichkeit fürs Methodenkapitel:** Injizierte Fehler sind *konstruierter Input*. Das ist
zulässig und gängige Praxis; die Ground Truth bleibt objektiv (der Originalwert). Was **nie**
zulässig ist: Bewertungen oder Experten-Urteile zu erfinden. **Konstruierter Input ja,
konstruierte Ergebnisse nie.**

---

## 15. Die drei Messdimensionen operationalisieren

**Vor der Messung muss exakt feststehen, wie jede Dimension gemessen wird.** Nach dem Sehen der
Ergebnisse wird nichts nachjustiert; fällt doch etwas auf, wird es als **Nachmessung** ausgewiesen.

### 15.1 Halluzinationsrate

**Definition:** Anteil der Ausgaben mit fachlich inkorrekten, nicht belegbaren oder regelwidrigen
Korrekturen — **unabhängig von syntaktischer Gültigkeit**.

**Vier Kategorien, pro Testfall zu vergeben:**

Für jede Kategorie existiert im `GraphState` ein **definierter Beobachtungs- und
Validierungspunkt**. Beachte die Spaltenüberschrift: **wo sie sichtbar wird**, nicht wo sie
entsteht — das ist nicht dasselbe.

| # | Kategorie | Messbar wie | **Beobachtungspunkt** |
|---|---|---|---|
| 1 | **Fachliche Halluzination** — falscher Korrekturwert | automatisch für injizierte Fälle (Vergleich mit Ground Truth); sonst Experten | **5** — `correction_proposal` |
| 2 | **Strukturelle Halluzination** — ungültiges JSON / Schemaverstoss | automatisch | **6** — `technical_check` *(erzeugt wird sie in Knoten 5, **erkannt** in 6)* |
| 3 | **Regelhalluzination** — Berufung auf nicht existente / falsch interpretierte Regel | Abgleich der Behauptung aus Knoten 5 gegen `matched_rules` | **4 + 5 gemeinsam** — Knoten 4 belegt, *welche* Karten geladen waren; die falsche Berufung entsteht in Knoten 5. **Erst das Paar macht sie prüfbar** |
| 4 | **Folgefehlererzeugung** — die Korrektur erzeugt einen neuen Fehler | automatisch (Re-Validierung: `errors_after > 0` oder neuer Fehlertyp) | **7** — `applied`, `errors_after` |

**Das ist die Begründung des Knotenschnitts (Kap. 5.2), von der Messseite gelesen:** Jede
Kategorie hat im Graphen einen definierten Punkt, an dem sie **prüfbar** wird. Beim Monolithen
liegen alle vier hinter einer einzigen Ausgabe — man sieht *dass* etwas falsch ist, nicht
*welcher* Fehlermodus zugeschlagen hat. **Genau diese Zurechenbarkeit ist der zu messende
Unterschied** — und Kategorie 3 zeigt, warum „ein Knoten pro Kategorie" zu einfach gedacht war:
Regelhalluzination braucht **zwei** Zustände, den geladenen Regelsatz und die Behauptung darüber.

**Aufschlüsseln nach Standard- vs. Komplexfällen.** Die These erwartet den Effekt **primär bei
Komplexfällen**; bei einfachen Fällen erwartet das Exposé selbst *keinen* Unterschied.

### 15.2 Nachvollziehbarkeit

**Definition:** Ausmass, in dem der Weg von Eingabe zu Ausgabe rekonstruierbar ist. **Eine
Begründung zählt nur, wenn sie den *realen* Entscheidungsprozess abbildet** — nicht, wenn sie
nachträglich bloss plausibel klingt. Diese Unterscheidung ist subtil und muss den Bewertenden
ausdrücklich vermittelt werden.

> ### ⚠ Nicht so messen: „Graph hat einen Trace, Monolith nicht"
> Das wäre **durch die Konstruktion vorweggenommen** und damit wertlos. Ausserdem ist es
> **sachlich falsch**: Der Monolith schreibt sehr wohl maschinelle Zwischenartefakte —
> `llm_identify_response.json`, `last_search_results.json`, `llm_correction_proposal.json`,
> `snapshot-validation.json` (Kap. 3.7). Sie sind nur **verstreut, untypisiert, ohne Reihenfolge
> und ohne Regelprovenienz**.
>
> Der Unterschied ist also **graduell, nicht binär** — und muss entsprechend gemessen werden.
> Genau das verlangt auch L12 (Jacovi & Goldberg): *faithfulness* ist eine graduelle, keine
> binäre Eigenschaft.

**Messvorschrift — vier Grössen, jede so, dass der Graph auch verlieren kann:**

| # | Grösse | Erhebung |
|---|---|---|
| 1 | **Lokalisierung** — wird der fehlerhafte Verarbeitungsschritt **korrekt** benannt? | pro Fehlfall, gegen die tatsächliche Ursache geprüft. **Richtig / falsch / nicht bestimmbar** |
| 2 | **Rekonstruierbarkeit** — welche Regel wurde tatsächlich angewandt? Welcher Kontext tatsächlich benutzt? | je Frage: aus den Artefakten belegbar, nur vermutbar, oder gar nicht |
| 3 | **Suchaufwand** — **wie viele Artefakte** müssen dafür zusammengesucht werden? | zählbar, deskriptiv (Monolith ≈ 4 verstreute Dateien + stdout, Graph = 1 `trace`) |
| 4 | **Experten-Rating** | Skala 1–5, einheitliches Raster |

**Die Kernfrage bleibt die harte:** Kann bei einer *falschen* Korrektur der Abzweig lokalisiert
werden? Aber sie wird jetzt **beantwortet**, nicht vorausgesetzt.

> **⚠ Wer lokalisiert?** Nicht der Autor — er hat den Graphen gebaut und kennt die Antwort.
> Sonst tauschst du einen konstruktionsbedingten Vorteil gegen einen Bewerter-Bias.
> Entweder über die Domänenexperten oder über ein **vorab festgelegtes Protokoll** mit
> definierten Kriterien und dokumentierter Reihenfolge. **Vor der ersten Messung festlegen**
> (Regel 5).

### 15.3 Robustheit

**Definition:** Fähigkeit, bei variierenden oder fehlerhaften Eingaben konsistente und fachlich
angemessene Ausgaben zu erzeugen — **inklusive der Fähigkeit, Unsicherheit auszuweisen statt eine
unbelegte Korrektur zu erzwingen**.

* **Konsistenz (quantitativ):** Wiederholungstest, identische Eingabe, N Läufe. **Miss die Streuung
  der *fachlichen* Korrektur, nicht der Formulierung.** Metrik: Anteil identischer fachlicher
  Ergebnisse bzw. Anzahl distinkter Korrekturwerte pro Fall.

  > **⚠ Wiederholungen sind keine zusätzlichen Fälle.** 5 Wiederholungen von 17 Fällen ergeben
  > **nicht n=85**. Es bleiben **17 Fälle**, ergänzt um eine **Within-Case-Stabilität** je Fall.
  > Die Fallzahl für jede Aussage über Halluzinationsraten bleibt 17. Wer die Wiederholungen
  > mitzählt, überschätzt die Aussagekraft um das Fünffache — ein Fehler, den ein Gutachter mit
  > Statistikhintergrund sofort sieht.
  > **Berichte absolute Zahlen** („5 von 17"), nicht Prozente („30 %") — bei n=17 täuschen
  > Prozentangaben eine Präzision vor, die nicht existiert.
  **Die entscheidende Unterscheidung:** sprachliche Variabilität (unvermeidbar, stochastisch) vs.
  **inhaltliche Instabilität** (dieselben Symptome → verschiedene fachliche Korrekturen). **Nur die
  zweite ist das Problem. Miss die zweite.**
* **Grenzfallverhalten (qualitativ):** Erkennt die Variante den Grenzfall? Weist sie Unsicherheit
  aus (`decision.action == "stop_uncertain"` bzw. `manual_intervention_required`) statt eine
  unbelegte Korrektur zu erzwingen? **Ein „ehrliches Nein" ist die bessere Antwort und muss positiv
  gewertet werden.**

---

## 16. Messinstrumentarium

### 16.1 Expertenbewertung — primäre qualitative Quelle

* **Wer:** 2–4 Personen aus Projekt-/Kundenumfeld mit Domänenwissen.
* **Was:** einheitliches Raster über fachliche Korrektheit, Regelkonformität, Nachvollziehbarkeit
  der Begründung, technische Verwendbarkeit, Risiko von Folgefehlern.
* **Wie — blind:** Die Bewertenden dürfen **nicht** wissen, welche Variante eine Ausgabe erzeugt
  hat.

  ⚠ **Echter Fallstrick: Die Blindung bricht am Format.** Die Graph-Variante erzeugt strukturell
  andere Ausgaben. **Gegenmassnahme:** Den Experten wird nur das *fachliche Endergebnis*
  (Korrekturvorschlag + Begründung) in einem **einheitlichen, variantenneutralen Format** vorgelegt
  — **nie der Rohtrace**, der verrät sofort die Variante. Den Trace nutzt du separat für die
  Nachvollziehbarkeits-Analyse, die ohnehin nicht blind sein kann.
* **Protokollierung:** Alle Reviews und Gespräche protokollieren — qualitative Datenquelle für die
  Diskussion.
* **Übereinstimmungsmass — nicht vorschnell Cohens κ.** Cohens κ ist für **zwei** Bewertende und
  **nominale** Kategorien gebaut. Hier stehen **3–4** Personen auf einer **ordinalen** 1–5-Skala.
  Passend wären je nach endgültigem Design **Fleiss' κ** (mehrere Rater, nominal),
  **gewichtetes κ** (zwei Rater, ordinal) oder **Krippendorffs α** (beliebig viele Rater,
  ordinal, verträgt fehlende Werte — die flexibelste Wahl).
  **Festzulegen, sobald das Raster steht — und vor der ersten Bewertung** (Regel 5).
  *Präzedenzfall für Trace-Annotation mit κ: MAST (NeurIPS 2025) berichtet κ = 0,88 über 150
  annotierte Traces.*

### 16.2 SUS und UEQ — ergänzend

**SUS** (10 Items, ein Gesamtscore) und **UEQ** (differenzierter: Nachvollziehbarkeit, Effizienz,
Verlässlichkeit), **mindestens 5 Teilnehmende**, aus dem Projektkontext und ausserhalb.
**Ehrliche Einordnung:** Bei n = 5 sind das **Indikatoren**, keine signifikanten Ergebnisse. Als
„ergänzend" bezeichnen (so steht es auch im Exposé) und keine Hauptaussage daraus ziehen.

### 16.3 Provenienz-Matrix der verblindeten Ergebnisvorlage

Die Vorlage für die Fachgutachter enthält **13 Felder**. Grundsatz: **ein Wert darf nur in die
Vorlage, wenn er in A, B und C aus einem tatsächlichen Artefakt belegbar ist.** Keine
konstruierten Vorgaben, keine erfundenen Ersatzwerte — ein Feld, das nur ein Arm liefern kann,
verrät den Arm.

Am Durchstich I03 (20.08.2026) für jedes Feld am realen Artefaktbestand geprüft:

| Feld | Quelle A | Quelle B | Quelle C |
|---|---|---|---|
| `snapshot_id` | Laufmetadaten — **wird durch Pseudonym ersetzt** | dito | dito |
| `fehler_vorher` | `data/snapshots/<id>/iteration-1/snapshot-validation.json` | dito | dito |
| `fehler_nachher` | `snapshot-validation.json` (nach Re-Validierung) | dito | dito |
| `ergebnis` | abgeleitet aus `fehler_nachher` + `revalidierung_ok` | dito | dito |
| `korrektur_vorhanden` | `data/snapshots/<id>/iteration-1/llm_correction_proposal.json` | dito | dito |
| `korrektur_aktion` | dieselbe Datei → `correction_proposal.action` | dito | dito |
| `korrektur_feld` | dieselbe Datei → `.target_path` | dito | dito |
| `korrektur_wert` | dieselbe Datei → `.new_value` | dito | dito |
| `korrektur_begruendung` | dieselbe Datei → `.reasoning` | dito | dito |
| `angewendet` | `snapshot-data.json` am Zielpfad gegengeprüft | dito | dito |
| `hochgeladen` | `upload-result.json` → `success` | dito | dito |
| `iterationen` | Anzahl der `iteration-*/`-Ordner | dito | dito |
| `manuelle_pruefung_noetig` | `_proposals/` (leer = keine HitL-Sperre) | dito | dito |

**13 von 13 in allen drei Bedingungen belegbar.** `angewendet` wird ausdrücklich **nicht** aus
`success` abgeleitet, sondern am Zielpfad in `snapshot-data.json` nachgesehen — ob der Wert
wirklich dort steht.

#### Die vier Felder ausserhalb der Vorlage — sie bleiben UF3-Material

| Feld | A | B | C | warum ausserhalb |
|---|---|---|---|---|
| `schema_gueltig` | — | — | ✔ | `validate_correction_schema_llm` persistiert sein Ergebnis nicht; nur Knoten 6 legt es als `technical_check` ab |
| `schema_versuche` | — | — | ✔ | dito |
| `revalidierung_abgeschlossen` | (nur zur Laufzeit) | (nur zur Laufzeit) | ✔ | der Trigger-Ausgang ist nur in C persistiert (`graph_state.applied.revalidation`); in A/B steht er ausschliesslich in der Rückgabe im Arbeitsspeicher |
| `schema_version` | ✔ | ✔ | ✔ | Konstante des Formats, kein Datenfeld |

> **Sie werden NICHT verworfen.** Dass die technische Schemaprüfung und der Ausgang der
> Re-Validierung in C **explizit persistiert** sind und in A/B nur flüchtig existieren, ist
> **kein Störfaktor, sondern genau der Gegenstand von UF3**. Die Frage lautet nicht „wie viele
> Schritte gab es", sondern **„was lässt sich hinterher aus den Artefakten rekonstruieren"**.
> Diese Felder gehören deshalb in die Nachvollziehbarkeitsanalyse in Kapitel 7 — nur eben nicht
> in die verblindete Vorlage, wo ihre blosse Anwesenheit den Arm verraten würde.

#### Was die Vorlage nicht dicht bekommt

`korrektur_begruendung` ist Modellprosa und unterscheidet sich zwischen den Läufen in Länge und
Stil, obwohl das Argument dasselbe ist (im Durchstich: Median 1.14 über 330 Vergleichsartikel).
Das ist **Systemausgabe, kein Formatfehler** — aber es ist ein Restrisiko für die Blindung und
gehört als solches in Kapitel 8.

### 16.4 RAGAS — nur für den RAG-Teil

RAGAS (Faithfulness, Context Precision) passt **nur** dort, wo eine klassische RAG-Situation
vorliegt. Für JSON-Korrekturen, Tool-Ausgaben und operative Entscheidungen ist es **nicht**
geeignet — das sagt das Exposé selbst, und es ist korrekt. Punktuell für Regelzuordnungs-/
Kontextqualität einsetzen, nicht als Bewertung der Korrektur.

### 16.5 Was bewusst nicht eingesetzt wird

**BLEU/ROUGE** — sie messen Wortüberlappung, nicht fachliche Korrektheit. Das kurz zu begründen
zeigt methodisches Urteilsvermögen.

---

## 17. Reproduzierbarkeitsprotokoll

**Für jeden Lauf zu protokollieren:** Zeitstempel · Variante (`SP_ARCHITECTURE_MODE`) · Fall-ID ·
Modell + API-Version · Temperatur und übrige Parameter · `RULEBOOK_MODE` · `MEMORY_MODE` ·
`HUMAN_IN_THE_LOOP` · vollständiger Prompt (oder Hash) · vollständige Antwort · `trace` (Graph)
bzw. die äquivalente Subprozess-Log-Kette (Monolith) · Wiederholungsnummer · Pfad der Rohdaten.

**Ausführungsreihenfolge randomisieren:** kleines Runner-Skript, das (Fall × Variante)-Paare mischt
und Zeitstempel protokolliert.

**Diese Rohdaten sind der Anhang der Arbeit — ohne sie ist keine Zahl belastbar.**

⚠ Die bestehenden Ergebnisdateien erfüllen das **nicht** (Kap. 4.9). Sie sind kein Vorbild.

---

## 18. Auswertung und Entscheidungslogik

Der Graph gilt als vorteilhaft, wenn er **(a)** weniger fachlich falsche/unbelegte Korrekturen
erzeugt, **(b)** weniger Folgefehler, **(c)** stabilere Ergebnisse bei Wiederholung/Variation
liefert, **(d)** von Experten als nachvollziehbarer bewertet wird.

**Kein vorab festgelegtes Ergebnis.** Es ist ausdrücklich erlaubt und erwartet, dass der Graph
nicht überall gewinnt — etwa Nachvollziehbarkeit deutlich besser, Halluzination nur bei
Komplexfällen besser, Robustheit moderat, technische Komplexität höher. **Diese differenzierte
Aussage ist wertvoller als ein pauschales „besser".**

**Auswertungsraster für Kapitel 7:**
* Pro Dimension eine Tabelle **A / B / C**, aufgeschlüsselt nach Standard-/Komplexfällen.
  *(B nur bei UF1 — siehe Kap. 7.1.)*
* **Absolute Zahlen, nicht Prozente.** Bei n=17 ist „5 von 17" ehrlich, „30 %" nicht.
* Deskriptive Statistik. Signifikanztest **nur**, wenn n und Voraussetzungen es zulassen —
  bei 17 Fällen wird das in aller Regel **nicht** der Fall sein.

**Wie das Ergebnis zu formulieren ist — Muster:**

> Die vollständige graph-basierte Variante (C) korrigierte *x von 17* Fällen fachlich falsch,
> gegenüber *y von 17* im ursprünglichen monolithischen Ausgangszustand (A). Der
> Kontrollvergleich zeigt, dass der aktuelle Produktivzustand (B — selektive Regelauswahl ohne
> Graph) bereits *z von 17* erreichte. Das Muster ist damit **vereinbar**, dass ein Teil der
> Verbesserung auf die Modularisierung des Regelkontexts zurückgeht und nicht auf die
> Graph-Orchestrierung; **bei dieser Fallzahl ist die Aufteilung deskriptiv und nicht
> statistisch belastbar**. Unabhängig davon zeigten sich die Vorteile von C bei
> Nachvollziehbarkeit und Fehlerlokalisierung.

**Warum diese Formulierung stärker ist als „der Graph gewinnt":** Sie zeigt, dass dem eigenen
Befund nicht mehr zugetraut wird, als er hergibt. Das ist der Unterschied zwischen einer Arbeit,
die verteidigt werden kann, und einer, die auseinandergenommen wird.
* Für Nachvollziehbarkeit und UF3: qualitative Fallgegenüberstellungen — der stärkste Teil, weil
  der strukturelle Unterschied dort am greifbarsten ist.

**Erwartete Ergebnisse laut Exposé** (als Erwartung, nicht als Ziel): Halluzination — Vorteil v. a.
bei komplexen Snapshots, bei einfachen kein relevanter Unterschied. Nachvollziehbarkeit —
**deutlichster** Vorteil. Robustheit — **moderatere** Verbesserung; mögliche neue Schwächen an
Knotengrenzen sind selbst eine Erkenntnis.

---

## 19. Bedrohungen der Validität — Checkliste

- [ ] **Strohmann-Baseline** — Baseline ist der reale Ist-Zustand (Kap. 3), nicht künstlich
      verschlechtert. Explizit begründet.
- [ ] **`RULEBOOK_MODE`-Kontamination** — jede Ergebnisdatei eindeutig einem Modus zugeordnet,
      kein unbeabsichtigtes Mischen.
- [ ] **Gedächtnis-Kontamination** — `MEMORY_MODE=off` in beiden Varianten, im Text begründet
      (Kap. 7.2).
- [ ] **Modell-Konsistenz** — `gpt-4.1` in beiden Varianten, Regressionstest gegen einen bekannten
      Fall durchgeführt.
- [ ] **Konfundierende Faktoren** — Parameter, Extraktion, Testfälle identisch;
      `RULEBOOK_MODE`-Unterschied explizit als Teil der Graph-Definition benannt, nicht verschwiegen.
- [ ] **Gebrochene Blindung** — Experten sehen nur das variantenneutrale Format, nie den Rohtrace.
- [ ] **Kleine Stichprobe** — als Limitation benannt, Aussagen „deskriptiv" statt „signifikant".
- [ ] **Zirkuläre Messung** — vor der Messung geprüft, ob das Messinstrument für **alle**
      Fehlerklassen das Richtige misst. *(Reales PT4-Beispiel: ein `value_grounded`-Term zeigte für
      eine ganze Fehlerklasse verkehrt herum — gemessen wurde ein Defekt des Instruments.)*
- [ ] **Überanpassung an den Messkatalog** — kein Pilotfall überschneidet sich mit einem Messfall,
      weder in der Snapshot-ID noch in den Entitäten (Kap. 8.3). Der konservative Effekt der
      Kalibrierung ist in Kapitel 8 benannt
- [ ] **Regelwerk als Kontrollbedingung** — die Karten wurden zwischen den Varianten **nicht**
      unterschiedlich verändert; falls Metadaten ergänzt wurden, liegt der Byte-Gleichheitsnachweis
      des injizierten Prompts vor (Kap. 7.3)
- [ ] **Reproduzierbarkeit** — vollständige Rohdaten-Protokolle im Anhang (Kap. 17).
- [ ] **Forscher-Bias** — du bist Entwickler beider Varianten. Unvermeidbar und im Exposé
      offengelegt, aber gegenzusteuern: Blindung, deterministische Metriken wo möglich, **keine
      nachträglichen Anpassungen nach dem Sehen der Ergebnisse**.

---

## 20. Arbeitsweise

**Vertikaler Durchstich.** Zuerst die **gesamte Vergleichskette für einen einzigen Fehlertyp**
vollständig zum Laufen bringen: ein Testfall durch den Monolithen, derselbe durch den Graphen,
beide Ausgaben durch die technische Prüfung, beide in ein vergleichbares Protokoll. **Erst wenn
dieser Durchstich steht, wird in die Breite gegangen.** Grund: So wird das Vergleichsverfahren
selbst früh getestet, bevor Zeit in Daten fliesst, die sich am Ende nicht sauber vergleichen lassen.

**Durchgehende Protokollierung.** Jede Ausführung erzeugt einen strukturierten Datensatz (Kap. 17).
Diese Protokolle sind die eigentliche Datengrundlage; ihre Qualität entscheidet über die
Auswertbarkeit.

**Schreiben läuft mit, nicht danach.** Frühe Verschriftlichung macht Denkfehler früh sichtbar.

**Nach jeder abgeschlossenen Einheit ein Eintrag in `docs/BA_PROJECT_LOG.md`** (Format oben in der
Datei). Bei Messläufen zusätzlich die Lauf-Metadaten. Zwei Regeln aus PT4, weil sie dort Zeit
gekostet haben: **(1)** Was gemessen wurde, wird notiert — auch wenn es nicht gefällt. **(2)**
Vermutungen werden als solche benannt.

---

## 21. Zeitplan und kritischer Pfad — ehrlich

**Stand 16.08.2026: Die Vollfassung an den Betreuer war der 15.08. Bis zur Abgabe am 15.09. bleiben
30 Tage. Es existiert noch keine Zeile Graph-Code.** Das ist ein Fakt, kein Vorwurf — aber die
Zeitpläne der drei Vorgängerdokumente (14.07.: „du bist in Phase 2"; 02.08.: „realistischer Pfad ab
jetzt") rechnen mit einem Budget, das es nicht mehr gibt.

### 21.1 Der kritische Pfad ist **nicht** die Implementierung

Acht der neun Knoten existieren als aufrufbarer Code. **Der Engpass sind die Menschen:** Die fachliche
Expertenbewertung (2–4 Personen) und die Nutzertests (≥5 Personen) hängen von der Verfügbarkeit
Dritter ab, sind blind vorzubereiten und lassen sich nicht komprimieren. **Wenn hier etwas rutscht,
rutscht die ganze Arbeit.**

**Praktische Konsequenz: Expertentermine und Teilnehmende JETZT fix vereinbaren**, nicht erst wenn
die Läufe fertig sind. Testfallkatalog, technische Prüfautomatik und Bewertungsraster müssen früh
stehen, damit die Menschen-Phase so früh wie möglich starten kann.

### 21.2 Reihenfolge ab heute

1. **Zuerst, weil es allem vorgelagert ist:** `MEMORY_MODE`-Schalter bauen und die Entscheidung
   festhalten. Ein Baseline-Lauf mit aktivem Override ist unbrauchbar, und Regel 5 verbietet, das
   nachträglich zu korrigieren.
2. Regressionstest gegen einen bekannten Fall auf dem Monolith-Pfad (trennt Modellwechsel-Effekt
   von Architektur-Effekt).
3. **Sauberer Monolith-Baseline-Lauf** (`RULEBOOK_MODE=monolith`, `MEMORY_MODE=off`) über beide
   Kataloge, vollständig protokolliert und archiviert.
4. Parallel: Expertentermine vereinbaren, Bewertungsraster und variantenneutrales
   Präsentationsformat bauen.
5. `langgraph` auflösen und pinnen; `SP_ARCHITECTURE_MODE`-Schalter einbauen.
6. Node-Extraktion in der Reihenfolge aus Kap. 12.2; `GraphState`, Kanten, Rück-Kante.
7. **Vertikaler Durchstich** an einem bekannten Einzelfehler-Fall, gegen die Baseline verglichen.
8. Wiederholungs-Wrapper (inkl. HitL-Blocker aus Kap. 13.2) und Grenzfälle.
9. Randomisierter A/B-Runner, volle Läufe, Rohdaten.
10. Auswertung, Validitäts-Checkliste, Kapitel 7–9.

### 21.3 Priorität, wenn es eng wird

**Die Nachvollziehbarkeits-Dimension zuerst.** Begründung — nach Aufwand und Ertrag:

| Dimension | Aufwand | Ertrag | Risiko |
|---|---|---|---|
| **Nachvollziehbarkeit (UF3)** | am kleinsten: Graph läuft, wenige Fälle in beiden Varianten, Fallgegenüberstellungen | **am sichersten** — der `trace` existiert oder nicht. Eine Demonstration, keine Statistik; n≈5 genügt | gering — steht auch dann, wenn der Graph bei Halluzination verliert |
| **Halluzination (UF1)** | mittel-hoch: ≥34 Läufe über beide Kataloge, Kategorisierung in vier Typen | die Schlagzeile, aber bei 17 Fällen **deskriptiv** | mittel — der grösste Teil der Fallzahl liegt bei Standardfällen, wo das Exposé selbst keinen Unterschied erwartet |
| **Robustheit (UF2)** | **am grössten**: 100–170 Läufe, plus fehlende Grenzfälle, plus HitL-Blocker | wertvoll, teuer erkauft | **am höchsten** — die meiste fehlende Infrastruktur |

**Ein klar belegter Teilbefund schlägt eine überdehnte Gesamtaussage.** Lieber wenige Fälle sauber
und ehrlich als viele schlampig.

---

## 22. Kapitelstruktur der Arbeit

1. **Einleitung** — Problem, Praxiskontext, Forschungsfrage, Thesen, Abgrenzung *(vorhanden)*
2. **Theoretische Grundlagen** — LLMs/Prompt Engineering, monolithische Prompts, graph-basierte
   Architekturen, Graph-of-Thoughts, Halluzinationen, LLM-Evaluation *(vorhanden)*
3. **Das bestehende System** — Vier-Agenten-Architektur, Pipeline, Grenzen des Monolithen.
   **Rohmaterial: Kapitel 4 dieses Dokuments und `docs/04_PT4/AGENTEN_ARCHITEKTUR.md`**
4. **Konzeption der Graph-Architektur** — Designprinzipien, Knoten/Kanten, **die präzise
   Monolith/Graph-Definition aus Kap. 3.2 wörtlich**. Rohmaterial: Kap. 9–11
5. **Forschungsdesign und Methodik** — Kontrollbedingungen (Kap. 7), Ground-Truth-Methode (Kap. 14),
   Reproduzierbarkeit (Kap. 17)
6. **Evaluierungsdesign** — Operationalisierung (Kap. 15), Testfallkatalog (Kap. 13),
   Bewertungsverfahren (Kap. 16)
7. **Ergebnisse** — nach Dimension und Komplexität *(zu schreiben)*
8. **Diskussion** — kritischer Rückbezug, Limitationen (Kap. 19) *(zu schreiben)*
9. **Fazit und Ausblick** — Designrichtlinien, Weiterentwicklung *(zu schreiben)*

**Anhang:** A Testfallkatalog + Fehlertaxonomie · B beide Prompts + Graph-Definition + Configs ·
C Experten-Raster + variantenneutrales Format · D Rohdaten, Traces · E SUS/UEQ.

---

## 23. MASTER-CHECKLISTE — in Umsetzungsreihenfolge

> **Abhakbare Fassung mit Arbeits- und Teilpaketen, Abhängigkeiten, Aufwand und DoD:
> `docs/BA_ARBEITSPAKETE.md`.** Diese Liste hier ist die fachliche Referenz, jene die
> Umsetzungsspur. Bei Widerspruch gilt diese hier.

> ### ⚠ Reihenfolgekorrektur (18.08.2026)
> **Die Umgebung muss final sein, BEVOR die Baseline gemessen wird** — die frühere Fassung dieser
> Checkliste hatte den Baseline-Lauf vor der `langgraph`-Installation. Das war falsch:
> `langgraph` zieht `langchain-core`, das eigene `pydantic`-Anforderungen hat, und `pydantic`
> liegt über `correction_models.py` **im gemessenen Pfad** (Schemaprüfung, Knoten 6). Baseline
> vor und Graph nach der Installation hiesse: zwei Varianten unter **verschiedenen
> Bibliotheksversionen** — genau der konfundierende Faktor, den Kapitel 7 ausschliesst.
> **Auch wenn die Installation scheitert und auf den Zustandsautomaten zurückgefallen wird: du
> musst es vor der Baseline wissen.**

**Vorgelagert (blockiert alles Weitere):**
- [x] **`RULEBOOK_MODE`-Historie geklärt** — alle bestehenden Läufe unter `cards`, verifiziert
      16.08. (Kap. 4.9)
- [x] **GPT-4.1-Deployment** steht, `.env` gesetzt, API-Version geprüft (Kap. 4.9)
- [ ] **`MEMORY_MODE`-Schalter** gebaut, Default `on`, für Messläufe `off`, Entscheidung im
      Protokoll festgehalten (Kap. 7.2)
- [ ] **Abhängigkeitskonflikt** `openai 2.14.0` gegen Pin `<2.0.0` aufgelöst (Kap. 4.9)
- [ ] **`langgraph`/`langchain-core`** installiert und gepinnt, `pydantic`-Verträglichkeit geprüft,
      **Smoke-Test: vollständiger Monolith-Lauf** (Kap. 12.1)
- [ ] **Umgebung eingefroren und dokumentiert** — `pip freeze` vor und nach der Änderung archiviert
- [ ] **Regressionstest** gegen einen bekannten Fall auf dem Monolith-Pfad gefahren

**Baseline (in der finalen Umgebung):**
- [ ] **Sauberer Monolith-Baseline-Lauf** mit `RULEBOOK_MODE=monolith`, `MEMORY_MODE=off`,
      GPT-4.1 über beide Kataloge — vollständig nach Kap. 17 protokolliert und archiviert
- [ ] **Baseline-Artefakte** archiviert: Regelwerk-Hash + Kopie, Prompt-Aufbau, alle Env-Werte
      (Kap. 8.2)

**Menschen — parallel ab sofort, nicht später:**
- [ ] **Expertentermine** (2–4 Personen) fix vereinbart
- [ ] **Experten-Bewertungsraster** + blindes, variantenneutrales Präsentationsformat gebaut
      (Kap. 16.1)
- [ ] **SUS/UEQ-Fragebögen** vorbereitet, ≥5 Teilnehmende organisiert

**Graph bauen:**
- [ ] **`SP_ARCHITECTURE_MODE`-Schalter** in `sp_agent.py:626` eingebaut, Default `"monolith"`,
      bestehender Pfad unverändert lauffähig (Kap. 6)
- [ ] **Knotenschnitt in Kapitel 4 der Arbeit begründet** — „der Schnitt folgt der Messvorschrift",
      inkl. der Tabelle Kategorie↔Knoten (Kap. 5.2, 15.1)
- [ ] **Node-Extraktion Knoten 6** `validate_correction_schema_llm` — additiv, CLI unverändert
- [ ] **Node-Extraktion Knoten 5** `generate_correction_llm`
- [ ] **Node-Extraktion Knoten 7** `apply_correction` + `update_snapshot` + `validate_snapshot` —
      **erzeugt `errors_after`, ohne das die Schleife nicht schliesst**
- [ ] **Knoten 4 und 8** neu gebaut (kein Extraktionsaufwand): Regelzuordnung protokolliert die
      geladenen Karten; Ergebnisbewertung schreibt `decision`, der Router entscheidet **nicht** selbst
- [ ] **Node-Extraktion Knoten 9** `generate_audit_report`
- [ ] **Node-Extraktion Knoten 2** `identify_error_llm`, inkl. MVP-Entscheidung zur Kartenauswahl
- [ ] **Node-Extraktion Knoten 3** `identify_snapshot` — **grösster Aufwand** (Kap. 4.5)
- [ ] **`GraphState`** implementiert (Kap. 10), **`correction_graph.py`** mit StateGraph, neun
      Knoten und **beiden** bedingten Kanten (Kap. 11)
- [ ] **`_execute_pipeline_graph()`** gebaut, liefert identische Rückgabestruktur (Kap. 6.3)
- [ ] **Mermaid-Abbildung** aus `draw_mermaid()` erzeugt und in Kapitel 4 übernommen

**Durchstich und Kalibrierung:**
- [ ] **Vertikaler Durchstich**: ein bekannter Einzelfehler-Fall durch beide Varianten, verglichen
- [ ] **Lesbare Trace-Kette** gebaut (Kap. 12.5) — Debugging-Werkzeug und Kapitel-7-Abbildung
- [ ] **Entscheidung Knotenzahl bestätigt oder angepasst** und hier vermerkt (Kap. 9.1)
- [ ] **Entscheidung Provenienz-Granularität**: bleibt es bei Kartenebene? (Kap. 7.3)
- [ ] **Pilotfälle gebaut** — eigene Snapshots mit **anderen Entitäten** als der Messkatalog
      (Kap. 8.3). Nachweis, dass keine Überschneidung besteht
- [ ] **Pilotläufe + Regeloptimierung** gefahren, je Änderung als `Status: pilot` protokolliert
      (Regel, Grund, auslösender Trace, Hash vorher/nachher)
- [ ] ██ **EINFRIEREN** ██ — Regelwerk, Graphstruktur, Prompts, Parameter. Ab hier keine
      Änderung mehr; jede spätere ist eine **Nachmessung**

**Messen:**
- [ ] **HitL-Blocker** für Wiederholungsläufe gelöst (Kap. 13.2)
- [ ] **Wiederholungs-Wrapper** für UF2 gebaut
- [ ] **Grenzfall-Testfälle** ergänzt (Kap. 13.2)
- [ ] **Randomisierter A/B-Runner** gebaut, protokolliert nach Kap. 17
- [ ] **Vollständige A/B-Läufe** über beide Kataloge + Wiederholungen + Grenzfälle

**Auswerten und schreiben:**
- [ ] **Auswertung je Dimension** (Kap. 15), Validitäts-Checkliste (Kap. 19) durchgegangen
- [ ] **Optimierungsschleife demonstriert** an 1–2 Fällen, als **Nachmessung** gekennzeichnet —
      der praktische Beitrag F9 (Kap. 8.3)
- [ ] **Kapitel 7–9** geschrieben

---

## 24. Ethik und Daten

`app/.env` enthält Klartext-Geheimnisse. **Niemals Werte ausgeben, niemals `.env` committen.**
Testläufe **ausschliesslich auf der Smart-Planning-Testinstanz**, nie produktiv. Das System darf
keine Snapshots löschen und keine echten Produktionsdaten unautorisiert zurückspielen. Nur
anonymisierte oder freigegebene Daten verwenden.

---

## 25. Literatur

> **Vollständige, nach Verwendungsstelle sortierte Literaturbasis: `docs/BA_LITERATUR.md`**
> (29 Quellen, Stand 16.08.2026, einzeln gegen die Primärquelle geprüft). Dort stehen auch die
> Gegenbefunde, die in Kapitel 8 diskutiert werden müssen, und die Abgrenzung zu Wu et al. (2022),
> der nächstverwandten Vorarbeit. Unten nur der Kern.

**Theoretische Grundlage**
* Besta, M. et al. (2024). *Graph of Thoughts: Solving Elaborate Problems with LLMs.* AAAI 38(16),
  17682–17690. Code: `github.com/spcl/graph-of-thoughts`
* Wen, Y., Wang, Z., Sun, J. (2024). *MindMap: Knowledge Graph Prompting Sparks Graph of Thoughts
  in LLMs.* ACL. Code: `github.com/wyl-willing/MindMap`
* Ji, Z. et al. (2023). *Survey of Hallucination in Natural Language Generation.* ACM Computing
  Surveys 55(12), 1–38.

**Das Rück-Kanten-Muster (Generator-Critic-Loop)**
* Madaan, A. et al. (2023). *Self-Refine: Iterative Refinement with Self-Feedback.* arXiv:2303.17651
* Shinn, N., Labash, B., Gopinath, A. (2023). *Reflexion: Language Agents with Verbal Reinforcement
  Learning.* arXiv:2303.11366
* Paul, D. et al. (2023). *REFINER: Reasoning Feedback on Intermediate Representations.*
  arXiv:2304.01904

**Evaluation**
* Es, S. et al. (2024). *RAGAs: Automated Evaluation of Retrieval Augmented Generation.* EACL
* Brooke, J. (1996). *SUS: A Quick and Dirty Usability Scale.*
* Laugwitz, B., Held, T., Schrepp, M. (2008). *Construction and Evaluation of a UEQ.* USAB, LNCS 5298

**Framework**
* LangGraph-Dokumentation — offizielle Muster für bedingte Retry-Kanten
  (`state["error"]`/`state["iterations"]`-Router) und `interrupt()`/`Command(resume=...)`.
  Version zum Zitierzeitpunkt prüfen.

**Nicht Gegenstand dieser Arbeit, für §11.2 Future Work**
* Zhou, A. et al. (2024). *Language Agent Tree Search (LATS).* ICML
