# Umsetzungsplan Bachelorarbeit — Graph-basierte Systemarchitektur vs. monolithische Systemprompt-Struktur

**Autor der Arbeit:** Ahmad Alsayad · **Betreuer:** Dipl.-Ing. Michael Macher · **HS St. Pölten, Smart Engineering**
**Dieses Dokument:** Umsetzungs- und Durchführungsplan für den praktischen und empirischen Teil.
**Stand:** 2026-07-14. Erstellt auf Basis des Exposés V2 und des realen Codestands im Repository.

> **Wozu dieses Dokument.** Es übersetzt das Exposé in eine konkrete, wissenschaftlich belastbare
> Umsetzung: Was gebaut werden muss, was gemessen wird, unter welchen Kontrollbedingungen, mit
> welchen Instrumenten, in welcher Reihenfolge — und wo die Fallstricke liegen, die einer
> Bachelorarbeit die Note kosten. Es ist bewusst als durchgehender Fließtext geschrieben, damit du
> es dir als Podcast anhören kannst. Jeder Abschnitt beginnt mit dem Kerngedanken in einem Satz.

---

## 0. Die eine Sache, die du zuerst verstehen musst: Das ist NICHT PT4

**Kerngedanke:** Diese Arbeit ist ein anderes Projekt als das, an dem wir zuletzt gearbeitet haben.

Wir haben in den letzten Sitzungen an **PT4** gebaut: Human-in-the-Loop-Governance, ein
Confidence-Scoring, MCP-Integration, ein Dashboard und ein Memory-System. Das ist eine Enterprise-
Weiterentwicklung des bestehenden Systems.

Deine **Bachelorarbeit** stellt eine ganz andere Frage. Sie vergleicht **zwei Architekturvarianten
desselben Korrekturprozesses**: die bestehende **monolithische Systemprompt-Struktur** gegen eine neu
zu bauende **graph-basierte Systemarchitektur** — gemessen an drei Dimensionen: **Halluzinationsrate,
Nachvollziehbarkeit, Robustheit**.

Das ist wichtig, weil es bestimmt, was in die Arbeit gehört und was nicht. Human-in-the-Loop,
Dashboard, MCP, Memory — all das ist **nicht** Gegenstand der Bachelorarbeit. Es darf die Arbeit
nicht „verwässern". Umgekehrt braucht die Arbeit etwas, das in PT4 gar nicht existiert: eine echte
**graph-basierte Implementierung** und ein **kontrolliertes Vergleichsexperiment**.

Es gibt genau **drei Brücken** zwischen PT4 und der Arbeit — mehr nicht (Details in Kapitel 6):
1. Die Methode, Fehler in Snapshot-Kopien zu **injizieren** und so eine **Ground Truth** zu erzeugen.
2. Der `RULEBOOK_MODE`-Schalter (monolith ↔ cards) als **Teilbaustein und Pilotergebnis** — aber
   ausdrücklich **nicht** die Graph-Architektur selbst.
3. Der Ansatz der **deterministischen technischen Prüfung** (belegbar vs. erfunden).

Alles andere aus PT4 bleibt außen vor.

---

## 1. Die Forschungsfrage, übersetzt in Bau- und Messaufträge

**Kerngedanke:** Die Forschungsfrage ist komparativ — du gewinnst sie nicht durch ein gutes System,
sondern durch einen sauberen *Vergleich* zweier Systeme unter identischen Bedingungen.

**Hauptforschungsfrage (aus dem Exposé):**
> Inwiefern unterscheidet sich eine graph-basierte Systemarchitektur von einer monolithischen
> Systemprompt-Struktur hinsichtlich Halluzinationsrate, Nachvollziehbarkeit und Robustheit bei der
> automatisierten Validierung und Korrektur strukturierter JSON-Daten in einem produktionskritischen
> Umfeld?

Daraus folgen drei Bauaufträge und drei Messaufträge. Die drei **Unterfragen** ordnen sich diesen zu:

- **UF1 (Halluzination + Messbarkeit):** Reduziert die Modularisierung die Halluzinationen — und wie
  macht man das überhaupt messbar? → *Bauauftrag:* Graph-Variante. *Messauftrag:* Halluzinationsrate
  mit einem eigens entwickelten Messansatz (weil RAGAS für JSON-Korrekturen nicht reicht). **UF1 ist
  gleichzeitig der methodische Beitrag deiner Arbeit** — die Entwicklung des Messansatzes ist selbst
  ein Ergebnis, nicht nur ein Werkzeug.
- **UF2 (Konsistenz/Stabilität):** Führt die Zerlegung zu stabileren Entscheidungen bei variierenden
  Eingaben? → *Messauftrag:* Wiederholungstests (identische Eingabe, mehrfach) + Grenzfall-Tests.
- **UF3 (Debugging/Wartbarkeit/Fehlertoleranz):** Ermöglicht der Graph gezieltere Fehleranalyse und
  wartungsfreundlichere Weiterentwicklung in iterativen Schleifen? → *Messauftrag:* qualitativ, über
  dokumentierte Debugging-Szenarien und Expertenbewertung.

**Konsequenz für die Umsetzung:** Alles, was du baust und misst, muss *diesem Vergleich* dienen. Ein
beeindruckendes Feature, das nur eine Variante hat, ist für die Arbeit wertlos. Die Leitfrage bei
jeder Entscheidung lautet: *„Macht das den Vergleich sauberer oder aussagekräftiger?"*

---

## 2. Die zentrale Designentscheidung: Was genau ist „monolithisch", was ist „Graph"?

**Kerngedanke:** Dies ist die wichtigste und riskanteste Entscheidung der ganzen Arbeit. Wenn die
Baseline ein Strohmann ist, ist das Ergebnis wertlos — egal wie gut der Graph funktioniert.

### 2.1 Das Strohmann-Risiko, das du unbedingt vermeiden musst

Das Exposé beschreibt den monolithischen Ansatz als einen einzigen 425-Zeilen-Systemprompt, der
„alles auf einmal" verarbeitet. Das klingt sauber. Aber **im realen Code ist die Korrektur-Pipeline
schon heute in mehrere getrennte LLM-Aufrufe zerlegt**:

- `identify_error_llm.py` — wählt und klassifiziert den Fehler
- `identify_snapshot.py` — extrahiert den relevanten Kontext
- `generate_correction_llm.py` — erzeugt den Korrekturvorschlag
- `validate_correction_schema_llm.py` — prüft das Schema

Das heißt: Der Ist-Zustand ist **kein reiner Monolith**, sondern bereits eine Kette diskreter
Schritte, die per Subprozess verkettet sind. **Wenn du als „monolithische Baseline" etwas baust, das
künstlich schlechter ist als das, was real läuft, betreibst du einen Strohmann-Vergleich** — und ein
Gutachter wird das sofort sehen und die gesamte Empirie anzweifeln.

Du musst also präzise definieren, *worin* sich Monolith und Graph unterscheiden. Ich sehe drei
saubere Optionen. Du musst dich für eine entscheiden und sie im Methodenkapitel explizit begründen.

**Option A — Prompt-Bündelung als Unterscheidungsmerkmal (empfohlen, am ehrlichsten).**
Der Monolith ist der *reale* Ist-Zustand: Jeder einzelne LLM-Schritt bekommt einen großen,
gebündelten Prompt — konkret lädt z. B. `generate_correction_llm` das **komplette** Regelwerk
(936 Zeilen) plus Kontext plus Formatvorgaben in *einen* Prompt und macht „alles in einem Schuss".
Der Graph zerlegt genau diesen Schritt weiter in fokussierte Knoten mit **explizitem, sichtbarem
Zustand** und **kontrollierten Übergängen**, orchestriert über LangGraph statt über Subprozess-
Verkettung. Der Unterschied ist dann nicht „ein Prompt vs. mehrere", sondern **impliziter,
verschmolzener Kontext vs. explizite, geprüfte Zwischenzustände**. Das deckt sich exakt mit den drei
Designprinzipien im Exposé (Trennung der Verantwortlichkeiten, Sichtbarmachung von
Zwischenzuständen, Kontrollierbarkeit von Übergängen).

**Option B — Orchestrierung als Unterscheidungsmerkmal.**
Der Monolith überlässt die Ablaufsteuerung dem LLM (der Smart-Planning-Agent „entscheidet selbst",
was als Nächstes zu tun ist, über seinen 425-Zeilen-Prompt). Der Graph ersetzt diese implizite,
LLM-getriebene Steuerung durch einen **deterministisch definierten Kontrollfluss** (LangGraph-
Knoten und -Kanten). Der Unterschied liegt in der *Kontrolle über den Ablauf*.

**Option C — Wissensbündelung als Unterscheidungsmerkmal.**
Der Monolith lädt das gesamte Regelwerk in jeden Prompt; die Graph-Variante lädt pro Knoten nur die
relevanten Regeln (das ist im Kern der `RULEBOOK_MODE=cards`-Mechanismus aus PT4). **Achtung:** Das
allein ist *zu wenig* für die Arbeit. Es ist eine einzelne Dimension (Kontextlast) und liefert
keine expl, sichtbaren Zwischenzustände — genau das, worauf die Arbeit für Nachvollziehbarkeit
abzielt. Option C kann ein *Baustein* von A oder B sein, aber nicht die ganze Graph-Definition.

**Meine klare Empfehlung: Option A, angereichert um B.** Das ist der ehrlichste und wissenschaftlich
verteidigbarste Schnitt. Die Baseline ist dann der *reale* Ist-Zustand (kein Strohmann), und der
Graph unterscheidet sich durch genau die drei Eigenschaften, die die Arbeit theoretisch begründet.
Du musst diese Definition in Kapitel 4 (Konzeption) und Kapitel 5 (Methodik) **wortwörtlich fixieren**
und in jeder Ergebnisdiskussion darauf zurückverweisen.

### 2.2 Präzisierung, die im Text stehen muss

Schreibe im Methodenkapitel einen Absatz, der ungefähr so lautet — und der die Ehrlichkeit sichert:

> „Als monolithische Baseline dient nicht ein künstlich vereinfachtes System, sondern der reale,
> produktiv eingesetzte Ist-Zustand des Smart-Planning-Agenten. Dessen Korrekturschritt verarbeitet
> Regelwerk, Kontext und Ausgabeformat in einem gebündelten Prompt-Kontext ohne explizite, extern
> prüfbare Zwischenzustände. Die graph-basierte Variante zerlegt exakt diesen Prozess in diskrete
> Knoten mit dokumentiertem Zwischenergebnis und deterministisch definierten Übergängen. Modell,
> Modellparameter, Kontextextraktion und Testfälle bleiben identisch, sodass beobachtbare
> Unterschiede auf die Architektur und nicht auf konfundierende Faktoren zurückführbar sind."

---

## 3. Die Graph-Architektur konkret bauen

**Kerngedanke:** Der Graph ist kein Diagramm, sondern lauffähiger Code mit acht Knoten, einem
expliziten Zustandsobjekt und kontrollierten Kanten — implementiert in LangGraph.

### 3.1 Die acht Knoten (aus Tabelle 3 der Arbeit)

Deine Arbeit definiert bereits die Knoten. Hier mit konkretem Ein-/Ausgang und der Zuordnung zum
bestehenden Code, den du wiederverwenden kannst:

| # | Knoten | Eingang | Ausgang | Wiederverwendbar aus |
|---|---|---|---|---|
| 1 | **Eingabeanalyse** | Nutzeranfrage/Snapshot-ID | strukturierte Aufgabenbeschreibung | Orchestrator-Logik |
| 2 | **Fehlerklassifikation** | Validierungsergebnis | priorisierte Fehlerliste (`[validate_*]`-Tag) | `identify_error_llm.py` |
| 3 | **Kontextsuche** | ausgewählter Fehler | Kontextfenster (1.000–4.000 Zeilen) | `identify_snapshot.py` |
| 4 | **Regelzuordnung** | klassifizierter Fehler | relevante Regeln (natürlichsprachlich) | RAG-Agent / Rulebook-Loader |
| 5 | **Korrekturgenerierung** | Kontext + Regeln | JSON-Korrekturvorschlag + Begründung | `generate_correction_llm.py` |
| 6 | **Technische Prüfung** | Korrekturvorschlag | Validierungsstatus | `validate_correction_schema_llm.py` |
| 7 | **Ergebnisbewertung** | Validierungsstatus | Entscheidung: weiter/abschließen | Iterationslogik `sp_agent.py` |
| 8 | **Antwortformulierung** | finaler Zustand | Audit-Report + Systemnachricht | `generate_audit_report.py` |

**Das ist die zentrale gute Nachricht für deinen Zeitplan:** Sieben der acht Knoten existieren im
Kern bereits als Skripte. Die Arbeit besteht **nicht** darin, sie neu zu erfinden, sondern sie in
einen expliziten, zustandsbehafteten Graphen zu *überführen* und ihre Zwischenzustände sichtbar zu
machen. Das ist deutlich weniger Risiko als „von null".

### 3.2 Der explizite Zustand — das Herzstück für „Nachvollziehbarkeit"

Der entscheidende architektonische Unterschied zum Monolith ist ein **zentrales State-Objekt**, das
durch alle Knoten wandert und bei jedem Übergang aktualisiert und protokolliert wird. Genau dieses
sichtbare Zwischenergebnis ist es, das die Arbeit als Vorteil postuliert. Der State sollte mindestens
enthalten:

```
GraphState = {
  snapshot_id, iteration,
  validation_result,           # Rohergebnis der Validierungs-Engine
  classified_error,            # Ausgang Knoten 2 (Tag, Priorität, Begründung)
  extracted_context,           # Ausgang Knoten 3 (welche Zeilen, warum)
  matched_rules,               # Ausgang Knoten 4 (welche Regel, Quelle)
  correction_proposal,         # Ausgang Knoten 5 (Wert + Begründung)
  technical_check,             # Ausgang Knoten 6 (valide? welche Prüfung?)
  decision,                    # Ausgang Knoten 7 (weiter/abschließen + warum)
  trace                        # chronologische Liste aller Knoten-Ausgänge
}
```

Das `trace`-Feld ist dein wichtigstes Messinstrument für die Dimension **Nachvollziehbarkeit**: Es
ist der *rekonstruierbare Entscheidungspfad*, den der Monolith per Definition nicht hat. Jeder Knoten
schreibt „was habe ich entschieden und aufgrund welcher Eingabe" hinein.

### 3.3 Die Kanten und die iterative Schleife

Die Kanten sind teils sequenziell, teils bedingt. Die entscheidende **bedingte Kante**: Ergibt die
Technische Prüfung (Knoten 6), dass der Vorschlag nicht valide ist, geht es **nicht** weiter zur
Antwortformulierung, sondern **zurück zu Knoten 2 (Fehlerklassifikation)** — mit dem aktualisierten
Validierungsergebnis. Das ist der bestehende iterative Korrekturzyklus, aber als **explizite,
sichtbare Kante im Graphen** statt als versteckte Schleife im Subprozess-Code. Genau diese
Sichtbarmachung ist der Untersuchungsgegenstand von UF3 (iterative Korrekturschleifen).

Ein Abbruch erfolgt bei „valide" **oder** bei Überschreiten der Maximaliterationen. Wichtig für
Robustheit (UF2): Ein guter Graph erzwingt im Grenzfall **keine** Korrektur, sondern kann einen
Knoten haben, der „Unsicherheit transparent ausweist" (das Exposé nennt das explizit als
Qualitätsmerkmal). Das ist im bestehenden System die `manual_intervention_required`-Ausgabe.

### 3.4 Technischer Umsetzungshinweis — LangGraph fehlt noch

**Verifiziert am 2026-07-14: LangGraph und LangChain sind im Projekt nicht installiert.** Die Arbeit
nennt LangGraph als Framework für die Graph-Variante. Du musst also:
1. `langgraph` (und ggf. `langchain-core`) der Umgebung hinzufügen und pinnen.
2. Entscheiden, ob die LangGraph-Knoten die bestehenden Runtime-Skripte per Funktionsaufruf kapseln
   (empfohlen — minimiert Neucode und hält die Logik identisch) oder neu implementieren (mehr
   Risiko, mehr Freiheitsgrade).
3. Den bestehenden Azure-OpenAI-Client wiederverwenden, damit **Modell und Parameter garantiert
   identisch** zur Baseline sind (siehe Kapitel 5).

> **Alternative, falls LangGraph zeitlich zu riskant wird:** Ein Graph lässt sich auch ohne
> LangGraph als expliziter State-Machine-Loop in Python bauen (Knoten = Funktionen, State = Dict,
> Übergänge = return-Werte). Das ist wissenschaftlich völlig zulässig — der Untersuchungsgegenstand
> ist die *Architektur* (explizite Knoten/Zustände/Übergänge), nicht das konkrete Framework. Nenne
> es dann „graph-basierte Architektur, implementiert als expliziter Zustandsautomat" und begründe
> die Framework-Wahl. Das nimmt dir Abhängigkeits- und Einarbeitungsrisiko aus dem Zeitplan.

---

## 4. Die Kontrollbedingungen des Experiments — hier entscheidet sich die Validität

**Kerngedanke:** Ein Vergleich ist nur so viel wert wie die Dinge, die zwischen beiden Varianten
*konstant* gehalten werden. Jede Abweichung ist ein konfundierender Faktor, der dein Ergebnis
angreifbar macht.

Was **identisch** sein muss (das schreibt das Exposé selbst vor):

1. **Modell.** Beide Varianten nutzen dasselbe Deployment. **ACHTUNG — hier ist ein realer Konflikt:
   Das Exposé nennt GPT-4.1, im Code ist aber überall `gpt-4o` deployt** (`AZURE_OPENAI_DEPLOYMENT=gpt-4o`,
   API-Version `2025-01-01-preview`, verifiziert am 2026-07-14). Das musst du auflösen: Entweder du
   ziehst das Deployment tatsächlich auf GPT-4.1 hoch **und** dokumentierst das, oder du korrigierst
   die Angabe im Exposé/in der Arbeit auf GPT-4o. Was du **nicht** tun darfst: in der Arbeit „GPT-4.1"
   schreiben, während die Messungen auf 4o laufen. Das ist ein Reproduzierbarkeits- und
   Ehrlichkeitsdefekt, der bei genauem Hinsehen sofort auffällt.
2. **Modellparameter.** Temperatur, top_p, max_tokens, seed (falls unterstützt) — bei *beiden*
   Varianten identisch und **dokumentiert**. Für Robustheits-Wiederholungstests brauchst du eine
   bewusst gewählte, konstante Temperatur (nicht 0, sonst misst du keine Variabilität; aber für
   beide gleich). Dokumentiere den exakten Wert.
3. **Kontextextraktion.** Beide Varianten sehen denselben extrahierten Snapshot-Ausschnitt
   (1.000–4.000 Zeilen). Wenn der Graph anders extrahiert als der Monolith, misst du die Extraktion
   mit, nicht die Architektur. Halte Knoten 3 identisch zur Baseline-Extraktion.
4. **Testfälle.** Exakt dieselben Snapshots, exakt dieselben injizierten Fehler.
5. **Ausführungsreihenfolge randomisiert.** Das Exposé fordert es — verhindert Reihenfolge-/Drift-
   Effekte (z. B. API-Latenz, Tageszeit). Praktisch: Mische die Reihenfolge (Fall, Variante) und
   protokolliere Zeitstempel.

Was sich **unterscheiden darf** (und nur das): die interne Verarbeitungsarchitektur des
Smart-Planning-Agenten. Orchestrator, RAG-Agent und Chat-Agent bleiben unverändert.

> **Reproduzierbarkeit:** Lege für jeden Lauf ein Protokoll ab mit: Zeitstempel, Variante, Fall-ID,
> Modell+Version, Parametern, vollem Prompt (oder Hash), voller Antwort, Trace. Diese Rohdaten sind
> der Anhang deiner Arbeit und die Grundlage jeder Zahl. Ohne sie ist keine Aussage belastbar.

---

## 5. Der Testfallkatalog — und warum du hier schon einen großen Vorsprung hast

**Kerngedanke:** Der Katalog ist das Rückgrat der Empirie. Und du hast das Kernproblem, das das
Exposé selbst als offene methodische Herausforderung benennt, in PT4 bereits gelöst.

### 5.1 Das Ground-Truth-Problem ist gelöst — nutze das offensiv

Das Exposé sagt an mehreren Stellen: „Da keine automatisierte Ground-Truth-Validierung existiert,
erfordert die Beurteilung Expertenwissen." Das stimmt für *beliebige* Produktionsfehler. Aber du hast
in PT4 eine Methode gebaut, die genau dieses Problem umgeht: **Fehler gezielt in Snapshot-Kopien
injizieren, den Originalwert als Ground Truth festhalten** (`app/eval/build_test_catalog.py`). Damit
ist für die injizierten Fälle objektiv messbar, ob eine Korrektur *richtig* ist — nicht nur „valide".

Das ist ein **methodischer Beitrag deiner Arbeit** und beantwortet UF1 („wie überhaupt messbar
machen") teilweise direkt. Schreibe das so: Für Standardfälle mit eindeutiger Ground Truth ist
Korrektheit objektiv per Vergleich messbar; für Komplexfälle ohne eindeutige Wahrheit ergänzt die
Expertenbewertung. Diese **Kombination** ist der Kern deines Evaluierungsrahmens.

**Wichtige Ehrlichkeit fürs Methodenkapitel:** Injizierte Fehler sind *konstruierter Input*. Das ist
zulässig und gängige Praxis — die *Ground Truth* bleibt objektiv (der Originalwert). Was du **nie**
tun darfst, ist Bewertungen oder Experten-Urteile zu erfinden. Trenne im Text sauber: konstruierter
Input ja, konstruierte Ergebnisse nein.

### 5.2 Aufbau des Katalogs

Das Exposé gliedert nach Komplexität. Konkretisiere so:

**Standardfälle (Basis für die Halluzinationsmessung unter kontrollierten Bedingungen):**
Klar definierte Einzelfehler mit eindeutiger Regelzuordnung und bekannter Ground Truth. Aus dem
realen System kennst du die relevanten Fehlerklassen (`[validate_*]`-Tags):
- leere Pflicht-ID (`UNIQUE_IDS`, leer)
- doppelte ID (`UNIQUE_IDS`, Duplikat)
- ungültige Referenz / Typo (`DEMAND_ARTICLE_IDS`)
- ungültiger Zahlenwert (`DENSITY_VALUES`)
- fehlendes Array-Element (`WORK_ITEM_CONFIGS_COMPLETENESS`)

**Komplexfälle (für Robustheit und die eigentliche These):**
Mehrere gleichzeitige Fehler, verschachtelte Abhängigkeiten, Kaskadeneffekte (eine Korrektur deckt
den nächsten Fehler auf), widersprüchliche Feldinhalte. **Das sind die Fälle, bei denen die These
einen Vorteil des Graphen erwartet** — bei einfachen Fällen erwartet das Exposé selbst *keinen*
relevanten Unterschied. Investiere hier die meiste Sorgfalt.

**Robustheits-/Grenzfälle:**
Fehlende Pflichtfelder, unbekannte Feldwerte, strukturell abweichende Snapshots — Fälle, in denen die
richtige Antwort sein kann, *keine* Korrektur zu erzwingen, sondern Unsicherheit auszuweisen.

### 5.3 Umfang und die Statistik-Falle

**Kerngedanke, den du dir merken musst:** Kleine Fallzahlen erlauben keine belastbaren Raten.

Wir wissen aus PT4, dass Aussagen bei n < 10 statistisch nicht tragen (das Dashboard führt dafür
sogar einen eigenen `SMALL_SAMPLE`-Flag). Für die Bachelorarbeit heißt das:
- Plane **pro Fehlerklasse mehrere Instanzen** (nicht ein Fall pro Typ), damit die Halluzinationsrate
  je Klasse überhaupt eine Zahl mit Bedeutung ergibt.
- Plane **Wiederholungen** (für UF2 mehrfach denselben Fall, z. B. 5× pro Fall) — Robustheit *ist*
  die Streuung über Wiederholungen.
- Rechne ehrlich: Bei realistischem Aufwand wirst du keine große Stichprobe schaffen. Das ist für
  eine Bachelorarbeit **völlig in Ordnung** — aber du musst es als Limitation benennen und deine
  Aussagen entsprechend vorsichtig formulieren („deskriptiver Vergleich" statt „statistisch
  signifikant", solange n klein ist). Ein Gutachter verzeiht kleine n; er verzeiht keine
  Überinterpretation kleiner n.

Konkreter Startwert: Wenn du 10 Fälle vorbereitest (dein Vorschlag) plus Wiederholungen (z. B. 3–5×)
pro Fall pro Variante, hast du eine ordentliche deskriptive Basis. Ziel-Größenordnung für belastbare
Rate: eher 15–30 distinkte Fälle über die Klassen verteilt, falls die Zeit reicht.

---

## 6. Was aus dem bestehenden System / aus PT4 wiederverwendbar ist — und was nicht

**Kerngedanke:** Vieles ist wiederverwendbar, aber du musst sauber trennen, was *Thesis-Arbeit* ist
und was *bestehende Infrastruktur*.

**Direkt wiederverwendbar (spart Zeit, ist keine Thesis-Leistung an sich):**
- Die sieben Runtime-Skripte als Knoten-Bausteine (siehe 3.1).
- Der Azure-OpenAI-Client und die Kontextextraktion (sichert identische Kontrollbedingungen).
- Die Smart-Planning-Validierungs-Engine als Ground-Truth-Prüfer für die technische Ebene.
- Der Snapshot-Speicher (LOCAL/AZURE über `StorageManager`).

**Methodisch wertvoll und in die Arbeit übernehmbar (mit Begründung):**
- Der **Testkatalog-Builder** mit Fehlerinjektion und dokumentierter Ground Truth
  (`app/eval/build_test_catalog.py`). Das ist dein Lösungsansatz für das Ground-Truth-Problem.
- Die **deterministische technische Prüfung** (belegbar vs. erfunden) als ein Baustein der
  Halluzinationsmessung auf technischer Ebene.
- Der **`RULEBOOK_MODE`-Schalter** (monolith ↔ cards): brauchbar als *Teilaspekt* der Graph-Variante
  (die selektive Regelzuordnung, Knoten 4) und als **Pilotergebnis** (−16 % Tokens bei identischem
  Vorschlag, gemessen über 3 Snapshots). **Aber ausdrücklich nicht** als „die Graph-Architektur" —
  das wäre Option C aus Kapitel 2 und allein zu dünn.

**NICHT Teil der Arbeit (bewusst weglassen, sonst Scope-Verwässerung):**
- Human-in-the-Loop / Review-Board, das Approval-Gate.
- Das MCP-Toolset und der E-Mail-Agent.
- Das Management-Dashboard.
- Das episodische Memory-System (Retrieval, `memory_support`).
- Das Confidence-Scoring als Governance-Feature.

Diese PT4-Bestandteile sind eine *andere* Weiterentwicklung. Sie können in einem Nebensatz als
„paralleler Ausbaupfad des Systems" erwähnt werden, gehören aber nicht in den Architekturvergleich.

> Eine **Notiz zur Ehrlichkeit**, die du im Kopf behalten musst: Der `RULEBOOK_MODE`-Pilotlauf hat
> die Regelkarten *nach* dem Sehen des Ergebnisses einmal korrigiert (die Prozessreihenfolge-Regel).
> Falls du diese Zahl in der Arbeit zitierst, weise das als Nachmessung aus. Für die eigentliche
> Thesis-Evaluation gilt strikt: erst Protokoll festlegen, dann messen, nichts nachträglich anpassen.

---

## 7. Die drei Messdimensionen operationalisieren

**Kerngedanke:** „Halluzinationsrate", „Nachvollziehbarkeit" und „Robustheit" sind erst dann
Wissenschaft, wenn jede eine konkrete, wiederholbare Messvorschrift hat.

### 7.1 Halluzinationsrate

**Definition (aus dem Exposé):** Anteil der Ausgaben mit fachlich inkorrekten, nicht belegbaren oder
regelwidrigen Korrekturen — unabhängig von syntaktischer Gültigkeit.

**Vier Kategorien**, die du pro Fall vergibst:
1. **Fachliche Halluzination** — falscher Korrekturwert (messbar gegen Ground Truth).
2. **Strukturelle Halluzination** — ungültiges JSON / Schema-Verstoß (technisch messbar).
3. **Regelhalluzination** — Berufung auf eine nicht existente/falsch interpretierte Regel (prüfbar
   gegen das reale Regelwerk; hier ist der explizite `matched_rules`-State des Graphen Gold wert).
4. **Folgefehlererzeugung** — die Korrektur erzeugt einen neuen Fehler (messbar über die
   Re-Validierung: `errors_after` > 0 oder neuer Fehlertyp).

**Messvorschrift:**
- *Technische Ebene (automatisch):* Kategorien 2 und 4 vollständig automatisierbar (Schema-Check +
  Re-Validierung durch die Engine). Kategorie 1 automatisierbar **für die injizierten Standardfälle**
  (Vergleich mit Ground Truth).
- *Fachliche Ebene (Experten):* Kategorien 1 und 3 für Komplexfälle ohne eindeutige Ground Truth.
- *Rate* = Anteil halluzinierter Ausgaben pro Variante, aufgeschlüsselt nach Kategorie und nach
  Komplexität (Standard vs. Komplex). Die Aufschlüsselung ist wichtig: Die These erwartet den Effekt
  *nur* bei Komplexfällen.

### 7.2 Nachvollziehbarkeit

**Definition:** Ausmaß, in dem der Weg von Eingabe zu Ausgabe rekonstruierbar ist. Eine Begründung
zählt nur, wenn sie den *realen* Entscheidungsprozess abbildet — nicht bloß nachträglich plausibel
klingt.

**Messvorschrift:**
- *Struktureller Nachweis (automatisch/deskriptiv):* Existiert ein rekonstruierbarer Pfad? Der Graph
  hat per Konstruktion das `trace`-Feld (jeder Knoten dokumentiert Eingang→Entscheidung). Der
  Monolith hat es nicht. Das ist der qualitative Kernunterschied — belege ihn mit konkreten
  Gegenüberstellungen (ein Fall, beide Varianten, „was kann ich über den Weg sagen").
- *Experten-Rating (quantitativ):* Skala (z. B. 1–5) pro Ausgabe: „Wie gut kann ich nachvollziehen,
  welcher Fehler erkannt, welche Regel angewandt, welche Daten herangezogen wurden?"
- *Der harte Test — „echte vs. plausible Begründung":* Für Fälle, in denen die Korrektur *falsch* ist:
  Kann man erkennen, *wo* der Prozess abbog? Beim Monolith praktisch nie (Blindflug), beim Graph über
  den Trace lokalisierbar. Das ist der stärkste Beleg für UF3.

### 7.3 Robustheit

**Definition:** Fähigkeit, bei variierenden/fehlerhaften Eingaben konsistente und fachlich
angemessene Ausgaben zu erzeugen — inklusive der Fähigkeit, Unsicherheit auszuweisen statt eine
unbelegte Korrektur zu erzwingen.

**Messvorschrift:**
- *Konsistenz (quantitativ):* Wiederholungstest — identische Eingabe, N Läufe (z. B. 5). Miss die
  Streuung der *fachlichen* Korrektur (nicht der Formulierung!). Metrik: Anteil identischer fachlicher
  Ergebnisse, oder Anzahl distinkter Korrekturwerte pro Fall. **Wichtige Unterscheidung, die das
  Exposé selbst betont:** sprachliche Variabilität (unvermeidbar, stochastisch) vs. *inhaltliche*
  Instabilität (dieselben Symptome → verschiedene fachliche Korrekturen). Nur die zweite ist das
  Problem. Miss die zweite.
- *Grenzfall-Verhalten (qualitativ + Kategorien):* Bei strukturell abweichenden Snapshots — erkennt
  die Variante den Grenzfall? Weist sie Unsicherheit aus (`manual_intervention_required`) oder
  halluziniert sie eine scheinbar plausible Korrektur? Ein „ehrliches Nein" ist hier die bessere
  Antwort und muss positiv gewertet werden.

---

## 8. Das Evaluierungsinstrumentarium — Experten, SUS, UEQ, RAGAS

**Kerngedanke:** Die technische Messung liefert die harten Zahlen, aber Halluzination und
Nachvollziehbarkeit bei Komplexfällen brauchen menschliches Urteil. Das muss sauber und blind sein.

### 8.1 Expertenbewertung (primäre qualitative Quelle)

- **Wer:** 2–4 Personen aus dem Projekt-/Kundenumfeld mit Domänenwissen.
- **Was:** einheitliches Bewertungsraster über: fachliche Korrektheit, Regelkonformität,
  Nachvollziehbarkeit der Begründung, technische Verwendbarkeit, Risiko von Folgefehlern.
- **Wie — blind:** Die Bewertenden dürfen **nicht** wissen, welche Variante eine Ausgabe erzeugt hat.
  **Achtung, echter Fallstrick:** Die Graph-Variante erzeugt eventuell strukturell anders aussehende
  Ausgaben (mehr Zwischenzustände, anderes Format). Wenn man die Variante am Aussehen erraten kann,
  ist die Blindung gebrochen. **Gegenmaßnahme:** Präsentiere den Experten nur das *fachliche
  Endergebnis* (Korrekturvorschlag + Begründung) in einem **einheitlichen, variantenneutralen
  Format**, nicht den Rohtrace. Den Trace nutzt du separat für die Nachvollziehbarkeits-Analyse (die
  ohnehin nicht blind sein kann, weil der Trace die Variante verrät).
- **Protokollierung:** Alle Reviews und Gespräche protokollieren — das ist deine qualitative
  Datenquelle für die Diskussion (wiederkehrende Kritikpunkte, Praxishinweise).

### 8.2 SUS und UEQ (ergänzende Nutzerperspektive)

- **SUS** (System Usability Scale, 10 Items) → ein Gesamtscore zur wahrgenommenen
  Gebrauchstauglichkeit.
- **UEQ** (User Experience Questionnaire) → differenzierter: u. a. wahrgenommene Nachvollziehbarkeit,
  Effizienz, Verlässlichkeit.
- **Mindestens 5 Teilnehmende**, aus dem Projektkontext und außerhalb.
- **Ehrliche Einordnung:** Bei n = 5 sind das *Indikatoren*, keine signifikanten Ergebnisse. Nenne sie
  „ergänzend" (so steht es auch im Exposé) und ziehe daraus keine Hauptaussage.

### 8.3 RAGAS (nur für den RAG-Teil)

RAGAS (Faithfulness, Context Precision) passt **nur** dort, wo eine klassische RAG-Situation
vorliegt — also beim RAG-Agenten, der natürlichsprachliche Antworten aus abgerufenem Kontext erzeugt.
Für JSON-Korrekturen, Tool-Ausgaben und operative Entscheidungen ist RAGAS **nicht** geeignet — das
sagt dein Exposé selbst, und es ist korrekt. Setze RAGAS punktuell für die Regelzuordnungs-/
Kontextqualität ein, nicht als Bewertung der Korrektur.

### 8.4 Was du NICHT einsetzt

BLEU/ROUGE (sprachliche Ähnlichkeit) sind für JSON-Korrekturen ungeeignet und stehen im Exposé
korrekt als „nicht eingesetzt". Erwähne kurz *warum* (misst Wortüberlappung, nicht fachliche
Korrektheit) — das zeigt methodisches Urteilsvermögen.

---

## 9. Auswertung und Entscheidungslogik

**Kerngedanke:** Am Ende musst du eine differenzierte, ehrliche Aussage treffen — nicht „Graph
gewinnt", sondern „Graph gewinnt *wo*, verliert *wo*, ist neutral *wo*".

Das Exposé definiert die Entscheidungslogik: Der Graph gilt als vorteilhaft, wenn er (a) weniger
fachlich falsche/unbelegte Korrekturen erzeugt, (b) weniger Folgefehler, (c) stabilere Ergebnisse bei
Wiederholung/Variation, (d) von Experten als nachvollziehbarer bewertet wird.

**Die wissenschaftlich starke Haltung** (und die, die das Exposé selbst einnimmt): **kein vorab
festgelegtes Ergebnis.** Es ist ausdrücklich erlaubt und sogar erwartet, dass der Graph nicht überall
gewinnt — z. B. Nachvollziehbarkeit deutlich besser, Halluzination nur bei Komplexfällen besser,
Robustheit moderat, technische Komplexität höher. Diese **differenzierte** Aussage ist wertvoller als
ein pauschales „besser".

**Auswertungsraster** (empfohlene Struktur für Kapitel 7):
- Pro Dimension eine Tabelle: Monolith vs. Graph, aufgeschlüsselt nach Standard-/Komplexfällen.
- Deskriptive Statistik (Raten, Streuungen). Bei ausreichendem n und wenn sinnvoll: einfacher
  Signifikanztest — aber nur, wenn die Voraussetzungen halten. Sonst ehrlich deskriptiv bleiben.
- Für Nachvollziehbarkeit und UF3: qualitative Fallgegenüberstellungen (der stärkste Teil, weil hier
  der strukturelle Unterschied am greifbarsten ist).

---

## 10. Wissenschaftliche Gütekriterien und die Fallstricke, die zählen

**Kerngedanke:** Eine Bachelorarbeit fällt selten an fehlender Leistung — sie fällt an angreifbaren
Behauptungen. Adressiere die Bedrohungen der Validität *proaktiv* im Text.

1. **Strohmann-Baseline** (Kapitel 2) — die größte Bedrohung. Baseline = realer Ist-Zustand, nicht
   künstlich verschlechtert. Explizit begründen.
2. **Konfundierende Faktoren** (Kapitel 4) — Modell, Parameter, Extraktion, Testfälle identisch. Die
   GPT-4.1-vs-4o-Frage auflösen.
3. **Gebrochene Blindung** (Kapitel 8) — variantenneutrales Format für die Experten.
4. **Kleine Stichprobe** (Kapitel 5) — als Limitation benennen, Aussagen entsprechend vorsichtig.
5. **Zirkuläre Messung / „das eigene Werkzeug messen"** — ein Fehlertyp, den wir in PT4 real erlebt
   haben: Ein Metrik-Term (`value_grounded`) zeigte für eine ganze Fehlerklasse falsch herum, weil er
   die falsche Frage stellte. **Lehre für die Arbeit:** Prüfe *bevor* du misst, ob dein Messansatz für
   *alle* Fehlerklassen das Richtige misst — sonst misst du einen Defekt deines Messinstruments statt
   die Architektur. Das ist ein methodischer Reflexionspunkt, den du sogar aktiv erwähnen kannst
   (zeigt Reife).
6. **Reproduzierbarkeit** — vollständige Rohdaten-Protokolle im Anhang.
7. **Forscher-Bias** — du bist der Entwickler beider Varianten. Das ist unvermeidbar (und im Exposé
   offengelegt), aber du musst gegensteuern: Blindung bei den Experten, deterministische Metriken wo
   möglich, keine nachträglichen Anpassungen nach dem Sehen der Ergebnisse.
8. **Ethik/Daten** — anonymisierte/freigegebene Snapshot-Daten. Das System darf keine echten
   Produktionsdaten löschen oder zurückspielen (das ist auch in PT4 als bewusste Designentscheidung
   festgehalten). Testläufe auf der Testinstanz, nicht produktiv.

---

## 11. Zeitplan-Realität (Stand 2026-07-14)

**Kerngedanke:** Du bist mitten in der heißen Phase. Der kritische Pfad ist jetzt: Graph bauen →
Katalog fertig → messen → schreiben.

Der Exposé-Zeitplan sieht so aus (und wo du heute stehst):
- **Phase 1** (14.06.–30.06.) Theorie + Konzeption — *sollte abgeschlossen sein.* Die Kapitel 1–5 der
  Arbeit existieren bereits als Entwurf, das passt.
- **Phase 2** (01.07.–21.07.) Prototypische Implementierung — **hier bist du gerade.** Der Graph muss
  jetzt lauffähig werden. Kritisch: LangGraph-Entscheidung (Kapitel 3.4).
- **Phase 3** (15.07.–04.08.) Evaluation + Datenerhebung — **überschneidet sich, beginnt fast jetzt.**
- **Phase 4** (29.07.–15.08.) Auswertung + Verschriftlichung.
- **Phase 5** (16.08.–15.09.) Feedback + Finalisierung. **Vollständige Fassung an den Betreuer bis
  15.08.**, finale Abgabe **15.09.**

**Ehrliche Einschätzung:** Die Implementierung des Graphen ist der Engpass, und die Uhr läuft. Die
gute Nachricht: Sieben der acht Knoten existieren als Skripte. Der realistische kritische Pfad ist:

1. **Jetzt:** Monolith/Graph-Definition fixieren (Kapitel 2) + LangGraph-Entscheidung (3.4). Das sind
   *Entscheidungen*, keine Wochen Arbeit — aber sie blockieren alles Weitere.
2. **Diese Woche:** Graph lauffähig bekommen (Knoten kapseln, State, Kanten, iterative Schleife).
3. **Parallel:** Katalog auf ausreichende Größe bringen (10 Fälle + Wiederholungen; du bereitest
   gerade real wirkende Fälle vor).
4. **Dann:** A/B-Läufe unter Kontrollbedingungen, Rohdaten protokollieren.
5. **Parallel ab sofort:** Schreiben. Kapitel 3–6 sind fertig; Kapitel 7 (Ergebnisse) wächst mit den
   Läufen, Kapitel 8 (Diskussion) und 9 (Fazit/Designrichtlinien) danach.

> **Priorität, wenn die Zeit knapp wird:** Lieber **wenige Fälle sauber und ehrlich** als viele
> schlampig. Lieber die **Nachvollziehbarkeits-Dimension** stark (dort ist der Graph-Vorteil am
> greifbarsten und am wenigsten von großen n abhängig) als alle drei Dimensionen halb. Ein klar
> belegter Teilbefund schlägt eine überdehnte Gesamtaussage.

---

## 12. Konkrete nächste Schritte (To-do, in Reihenfolge)

1. **Modellfrage klären.** GPT-4.1 (Exposé) vs. `gpt-4o` (Code) — Deployment hochziehen *oder* Arbeit
   korrigieren. Nicht offenlassen.
2. **Monolith/Graph-Definition schriftlich fixieren** (Option A+B, Kapitel 2.2). Das ist die
   Grundlage von allem.
3. **LangGraph-Entscheidung treffen:** echtes LangGraph installieren *oder* expliziter
   Zustandsautomat in Python (Kapitel 3.4). Beides ist verteidigbar; entscheide nach Zeitbudget.
4. **Graph implementieren:** acht Knoten, `GraphState` mit `trace`, iterative Rück-Kante von Knoten 6
   zu Knoten 2. Bestehende Skripte kapseln.
5. **Kontrollbedingungen einfrieren:** Modell, Parameter (Temperatur dokumentieren), Extraktion —
   identisch für beide Varianten. Protokoll-Format festlegen (Kapitel 4).
6. **Testkatalog fertigstellen:** Standard-, Komplex-, Grenzfälle mit dokumentierter Ground Truth;
   ausreichend Instanzen + Wiederholungen (Kapitel 5).
7. **Messinstrumente vorbereiten:** Experten-Raster (variantenneutrales Format!), SUS/UEQ-Fragebögen,
   RAGAS nur für RAG-Teil.
8. **A/B-Läufe fahren:** randomisierte Reihenfolge, Rohdaten + Traces vollständig ablegen.
9. **Auswerten:** pro Dimension, aufgeschlüsselt nach Komplexität; differenzierte Aussage.
10. **Schreiben:** Kapitel 7–9; Limitationen ehrlich; Designrichtlinien ableiten.

---

## 13. Kapitelstruktur der schriftlichen Arbeit (Soll-Zustand)

Kapitel 1–6 existieren im Entwurf. Zur Vollständigkeit die Zielgliederung (neun Kapitel laut Arbeit):

1. **Einleitung** — Problem, Praxiskontext, Forschungsfrage, Thesen, Abgrenzung. *(vorhanden)*
2. **Theoretische Grundlagen** — LLMs/Prompt Engineering, monolithische Prompts, graph-basierte
   Architekturen, Graph-of-Thoughts, Halluzinationen, LLM-Evaluation. *(vorhanden)*
3. **Das bestehende System** — Unternehmenskontext, Smart Planning, Vier-Agenten-System, Pipeline,
   Grenzen des Monolithen (empirische Baseline). *(vorhanden)*
4. **Konzeption der Graph-Architektur** — Designprinzipien, Knoten/Kanten, Abgrenzung zum Monolith,
   Einbettung. *(vorhanden — ergänzen um die präzise Monolith/Graph-Definition aus Kapitel 2 hier)*
5. **Forschungsdesign und Methodik** — Untersuchungsaufbau, Kontrollbedingungen, Bewertungsmethoden.
   *(vorhanden — ergänzen um GPT-Modellklärung und die Ground-Truth-Injektionsmethode)*
6. **Evaluierungsdesign** — Operationalisierung der drei Dimensionen, Testfallkatalog,
   Bewertungsverfahren, Entscheidungslogik. *(vorhanden — konkretisieren mit Kapitel 5+7 dieses Plans)*
7. **Ergebnisse** — die Messungen, aufgeschlüsselt nach Dimension und Komplexität. *(zu schreiben)*
8. **Diskussion** — kritischer Rückbezug auf Forschungsfrage und Literatur, Limitationen. *(zu schreiben)*
9. **Fazit und Ausblick** — Kernerkenntnisse, Designrichtlinien, Weiterentwicklung. *(zu schreiben)*

---

## 14. Die drei Sätze, die alles zusammenfassen

1. **Bau den Graphen als echte Zerlegung mit sichtbarem Zustand — und miss ihn gegen den *realen*
   Ist-Zustand, nicht gegen einen Strohmann.** Sonst ist die Empirie wertlos.
2. **Nutze die Fehlerinjektion als Ground Truth — das löst genau das Messproblem, das dein Exposé als
   offen benennt, und ist selbst ein methodischer Beitrag.** Trenne dabei strikt: konstruierter Input
   ja, konstruierte Bewertungen nie.
3. **Sei ehrlich über kleine Fallzahlen und differenziert im Ergebnis — „der Graph gewinnt *wo*" ist
   wissenschaftlich stärker als „der Graph gewinnt".** Und kläre die zwei realen Defekte zuerst:
   GPT-4.1-vs-4o und das fehlende LangGraph.
