# Graph-Architektur — Vollständiger Umsetzungsplan

> **Erstellt von: Fable (claude-fable-5), Session vom 2026-08-02.**
> Diese Datei ist bewusst neu und eigenständig geschrieben — sie ersetzt keinen älteren Plan, sondern
> ist die einzige verbindliche Referenz für die Umsetzung der graph-basierten Systemarchitektur aus
> deiner Bachelorarbeit. Jede Aussage zum "Ist-Zustand" in diesem Dokument wurde am 2026-08-02 direkt
> gegen den echten Code im Repository verifiziert (Dateipfade, Zeilennummern, Funktionsnamen — keine
> Vermutungen).

---

## 0. Wie du dieses Dokument benutzt

Dieses Dokument ist so aufgebaut, dass du es **von oben nach unten abarbeiten kannst**. Jeder
Abschnitt liefert entweder (a) eine Tatsache über den bestehenden Code, (b) eine Entscheidung, die
fixiert ist, oder (c) einen konkreten Bauauftrag. Kapitel 23 ist die **Master-Checkliste** — wenn du
nur eine Sache aus diesem Dokument offen halten willst, ist es diese.

**Die eine unumstößliche Rahmenbedingung, die alles andere prägt:**
Das bestehende monolithische System wird **nicht ersetzt, nicht gelöscht, nicht umgebaut** — es bleibt
byte-identisch erhalten und lauffähig. Es entsteht ein **Schalter**, der zwischen "altes System" und
"neues Graph-System" umschaltet. Beide müssen danach mit identischen Eingaben gegeneinander gefahren
werden können. Dieses Prinzip zieht sich durch jede einzelne Entscheidung in diesem Plan.

---

## 1. Ausgangslage — was deine Bachelorarbeit fordert

Deine Forschungsfrage (aus dem Exposé, Kapitel 2.1):

> Inwiefern unterscheidet sich eine graph-basierte Systemarchitektur von einer monolithischen
> Systemprompt-Struktur hinsichtlich Halluzinationsrate, Nachvollziehbarkeit und Robustheit bei der
> automatisierten Validierung und Korrektur strukturierter JSON-Daten in einem produktionskritischen
> Umfeld?

Das ist eine **komparative** Frage. Du gewinnst sie nicht dadurch, dass du ein gutes Graph-System
baust, sondern dadurch, dass du **zwei Systeme unter identischen Bedingungen gegeneinander misst** und
ehrlich berichtest, wo welches gewinnt. Drei Unterfragen (UF1–UF3) operationalisieren das:

- **UF1** — Halluzination + Messbarkeit (auch ein methodischer Beitrag: wie misst man das überhaupt?)
- **UF2** — Konsistenz/Stabilität bei Wiederholung und Grenzfällen
- **UF3** — Debugging/Wartbarkeit/Fehlertoleranz bei iterativen Korrekturschleifen

**Abgrenzung laut Exposé (bindend für den Scope):** Modell identisch in beiden Varianten, Fokus auf
Systemstruktur/Entscheidungsfluss (nicht Prompt-Wortlaut-Optimierung), Vergleichsgegenstand ist
ausschließlich der Validierungs-/Korrekturschritt des Smart-Planning-Agenten — nicht Orchestrator,
RAG-Agent oder Chat-Agent, die unverändert bleiben.

---

## 2. Terminologie — was "Monolith" und was "Graph" in DIESEM Repository konkret bedeutet

Das ist die wichtigste und riskanteste Definitionsentscheidung der ganzen Arbeit. Ein Gutachter prüft
zuerst: Ist die Baseline echt, oder ein Strohmann?

**Der reale Ist-Zustand (verifiziert, siehe Kapitel 4) ist bereits eine Kette von sieben eigenständigen
Skripten**, die per Subprocess verkettet werden (`SPAgent._run_tool()`, `demo/agents/sp_agent.py:62-138`).
Das ist **kein reiner Monolith** im trivialen Sinn "ein Prompt für alles". Der monolithische Charakter
liegt an zwei anderen Stellen:

1. **Der Korrekturgenerierungs-Schritt selbst ist monolithisch.** `generate_correction_llm.py` baut in
   einem einzigen Prompt (Promptaufbau `generate_correction_llm.py:599-718`, API-Call `:721-729`) das
   komplette Regelwerk + Kontext + Ausgabeformat zusammen und lässt das LLM "alles auf einmal"
   entscheiden.
2. **Der Kontrollfluss zwischen den Skripten ist implizit und nicht inspizierbar.** Es gibt kein
   einheitliches Zustandsobjekt, das durch die Kette wandert — nur lose `dict`-Rückgaben, die in
   `SPAgent._execute_pipeline()` (`sp_agent.py:248-375`) verarbeitet werden. Es gibt kein `trace`-Feld,
   keinen rekonstruierbaren Entscheidungspfad. Die Iterationslogik (`sp_agent.py:450-503`) ist reiner
   `while True`-Python-Code mit einem Zähler — keine sichtbare, dokumentierte Zustandsmaschine.

**Damit ist die präzise, ehrliche Definition für deine Arbeit:**

> Der Unterschied zwischen Monolith und Graph liegt **nicht** darin, dass der Monolith weniger
> Verarbeitungsschritte hätte — er hat bereits sieben. Der Unterschied liegt darin, dass der Monolith
> (a) Regelwerk, Kontext und Ausgabeformat im zentralen Korrekturschritt ungefiltert bündelt und
> (b) keinen expliziten, extern prüfbaren Zwischenzustand zwischen den Schritten führt. Die
> graph-basierte Variante ersetzt genau diese zwei Eigenschaften: Knoten 4 lädt gezielt nur die
> passenden Regeln (statt des vollständigen Regelwerks), und ein zentrales `GraphState`-Objekt macht
> jeden Zwischenschritt sichtbar, protokolliert und prüfbar — orchestriert über LangGraph statt über
> eine Python-`while`-Schleife mit Subprocess-Aufrufen.

**Das musst du in Kapitel 4/5 deiner Arbeit wortwörtlich so (oder sinngemäß) festschreiben und in jeder
Ergebnisdiskussion referenzieren.** Ohne diesen Absatz ist jeder Vergleich angreifbar.

**Wichtiger Nebeneffekt dieser Definition:** Sie bedeutet, dass der Graph gegenüber dem Monolith **zwei**
gleichzeitige Unterschiede hat — bündelnder vs. selektiver Regelzugriff **und** impliziter vs. expliziter
Zustand. Das ist kein Konfundierungsfehler, wenn du es offen benennst: Beide Eigenschaften sind
Bestandteil der Graph-Definition selbst (Knoten 4 = selektive Regelzuordnung ist explizit einer der acht
Knoten). Schreibe im Methodenkapitel ausdrücklich, dass die Graph-Architektur **beide** Eigenschaften
gemeinsam umfasst, und ordne beobachtete Effekte nicht vorschnell einer einzelnen Ursache zu.

---

## 3. Grundsatzentscheidungen — bereits getroffen, hier fixiert

Diese zwei Entscheidungen wurden von dir am 2026-08-01 getroffen. Sie sind ab jetzt bindend für die
gesamte Umsetzung; wenn du sie später revidierst, muss dieses Dokument entsprechend angepasst werden.

### 3.1 LangGraph als echtes Framework (nicht Eigenbau-State-Machine)

Begründung: 1:1-Deckung mit dem, was das Exposé nennt. Konsequenz: `langgraph` und `langchain-core` sind
neue, zu pinnende Abhängigkeiten (siehe Kapitel 10.1). Es gibt aktuell **keine** Zeile LangGraph- oder
State-Machine-Code im Repository — verifiziert per Volltextsuche über `StateGraph|GraphState|langgraph|
state_machine|pipeline_state`, einziger Treffer ist die (jetzt zu ignorierende) alte Planungsdatei.

### 3.2 GPT-4.1-Deployment hochziehen (statt Exposé zu korrigieren)

Begründung: Exposé bleibt unverändert korrekt. Konsequenz: Es muss ein neues Azure-OpenAI-Deployment für
GPT-4.1 angelegt und **nur** in den Korrektur-Pipeline-Skripten verwendet werden (siehe Kapitel 11 für
das genaue Vorgehen und die genaue Abgrenzung, welche der vier bestehenden Deployments betroffen sind).

### 3.3 Das Rad nicht neu erfinden — bestehende Frameworks und Implementierungsmuster

Du musst nichts von dem, was unten beschrieben ist, selbst erfinden. Für jeden zentralen Baustein des
Plans gibt es entweder ein echtes, zitierfähiges Open-Source-Framework oder ein offiziell dokumentiertes
Implementierungsmuster. Das ist zugleich wissenschaftlich wertvoll (belastbare Zitate statt
Eigenkonstruktion) und spart Umsetzungszeit.

**3.3.1 Graph of Thoughts (Besta et al., 2024) — Referenzimplementierung existiert, ist aber nicht die
richtige Wahl für den Korrekturpfad.**
Das Exposé zitiert Besta et al. bereits theoretisch; es gibt dazu ein echtes, quelloffenes Framework:
`https://github.com/spcl/graph-of-thoughts` mit einer modularen Architektur aus Prompter, Parser,
Scoring-Modul und Controller (der intern eine statische "Graph of Operations" und einen dynamischen
"Graph Reasoning State" führt — letzterer ist konzeptionell fast identisch zu unserem `GraphState`,
Kapitel 8). Die Operationen-API (`Generate(k)`, `Aggregate(k)`, `Score(k)`, `KeepBestN(N)`,
`ValidateAndImprove(t)`) ist explizit dafür gebaut, **mehrere gleichartige LLM-Ausgaben zu erzeugen und
zusammenzuführen** (z. B. beim Sortieren: Teillisten parallel sortieren, dann mergen). Das passt gut auf
Aufgaben, bei denen derselbe Operationstyp wiederholt und aggregiert wird — passt aber **strukturell
schlecht** auf unsere Korrektur-Pipeline, deren acht Knoten heterogene, werkzeugaufrufende Schritte sind
(API-Calls, Schema-Validierung, Dateisystem-Operationen), nicht Varianten derselben Denkoperation.
**Konsequenz für dich:** Du zitierst Besta et al. weiterhin als theoretische Grundlage (wie im Exposé
vorgesehen) und begründest im Methodenkapitel explizit, warum du **nicht** das GoT-Referenzframework,
sondern LangGraph einsetzt — mit genau diesem strukturellen Argument (heterogene, werkzeuggebundene
Schritte statt homogener, aggregierbarer "Thoughts"). Das ist eine saubere, verteidigbare
Methodenentscheidung, keine Ausrede.

**3.3.2 MindMap (Wen, Wang & Sun, 2024, ACL) — zwei direkt wiederverwendbare Ideen.**
Ebenfalls schon im Exposé zitiert, mit echtem Code unter `https://github.com/wyl-willing/MindMap`. Für
dich relevant sind nicht die KG-Retrieval-Mechanismen (die brauchst du nicht — dein "Wissensgraph" ist
das Regelwerk, nicht extern), sondern zwei methodische Bausteine:
- **Das "Mind Map"-Format als Vorbild für die Trace-Darstellung.** MindMap lässt das LLM seinen
  Schlussfolgerungspfad explizit als Kette ausgeben (`Pfad-Evidenz 1('Entität'->'Relation'->'Entität')
  -> ... -> Ergebnis`) und rendert daraus eine für Menschen lesbare Grafik. Das ist ein direkt
  übertragbares Vorbild dafür, wie du dein `trace`-Feld (Kapitel 8) für die Experten-Bewertung
  aufbereitest — nicht als rohes JSON, sondern als lesbare Kette "Knoten → Eingabe → Entscheidung →
  nächster Knoten". Zitierbar als Präzedenzfall für "graph-basierte Nachvollziehbarkeitsdarstellung".
- **Die GPT-4-Rater-Pairwise-Vergleichsmethode als optionales Zusatzinstrument.** MindMap nutzt GPT-4
  als automatisierten Gutachter für paarweise Vergleiche (Prompt-Vorlage im Paper, Tabelle 12: "welche
  Ausgabe passt besser zur Referenz, gib 0/1/2 aus"). Das ersetzt **nicht** die geforderte menschliche
  Expertenbewertung (Kapitel 16) — aber als **zusätzliches, günstiges, automatisiertes Signal** zur
  Triangulierung (viele Fälle schnell grob vorsortieren, bevor Experten die wichtigsten/uneindeutigen
  Fälle vertieft bewerten) ist es eine zeitsparende Ergänzung, falls die Zeit für ausreichend viele
  Experten-Reviews knapp wird. Explizit als "automatisiertes Zusatzsignal, kein Ersatz" im Methodenkapitel
  kennzeichnen.

**3.3.3 Der iterative Rück-Kanten-Loop (Knoten 6→2) ist ein etabliertes Muster, keine Eigenerfindung.**
Sowohl die akademische Literatur als auch die offizielle LangGraph-Dokumentation kennen dieses Muster
unter eigenem Namen:
- **Self-Refine** (Madaan et al., 2023), **Reflexion** (Shinn et al., 2023) und **REFINER** (Paul et al.,
  2023) — alle drei werden in Besta et al. (2024, Abschnitt "Self-Reflection & Self-Evaluation") als
  etablierte Vorarbeiten zum iterativen "generiere → kritisiere → verbessere"-Zyklus genannt. Zitiere sie
  im Theoriekapitel als Grundlage für deine Rückkante — das ist kein Sonderfall, den du erfindest, sondern
  ein benanntes Muster ("Generator-Critic-Loop" / "Reflection Pattern").
- **LangGraph selbst dokumentiert exakt dieses Muster** als Standard-Implementierungsweg für
  Retry-/Selbstkorrektur-Schleifen: eine bedingte Kante ("Router") liest `state["error"]` und
  `state["iterations"]`; ist ein Fehler vorhanden und das Iterationslimit nicht erreicht, geht es zurück
  zum vorherigen Knoten, sonst weiter oder Abbruch. Das ist **strukturell identisch** mit der in Kapitel 9
  beschriebenen Kante — du implementierst kein neues Muster, sondern das offizielle LangGraph-Standardmuster
  für "extract, check, feed back the error, retry".

**3.3.4 Human-in-the-Loop — LangGraph hat dafür bereits einen eingebauten Mechanismus.**
Falls du (über den Kern-Vergleich hinaus, siehe Abgrenzung Kapitel 1) irgendwann den Graph-Pfad mit
echter menschlicher Freigabe statt Eval-Direct-Apply laufen lassen willst: LangGraph bringt dafür die
Funktion `interrupt()` mit — sie pausiert die Graph-Ausführung an einem Knoten, ein Mensch prüft/ändert/
bestätigt, und die Ausführung wird über `Command(resume=...)` mit demselben `thread_id` fortgesetzt,
inklusive eingebautem Checkpointing (kein eigener Persistenz-Code nötig). Das ist relevant, weil es
bedeutet: Du müsstest den bestehenden `HUMAN_IN_THE_LOOP`-Gate-Mechanismus (Kapitel 5.4) für den
Graph-Pfad nicht nachbauen, sondern könntest ihn — falls gewünscht, außerhalb des reinen
Bachelorarbeit-Vergleichs — auf das native LangGraph-Muster abbilden.

**3.3.5 Konkrete, aktuell zu pinnende Paketversionen (Stand 02.08.2026, vor Installation erneut prüfen):**
`langgraph==1.2.10`, `langchain-core==1.5.3`. Diese Versionsangabe ersetzt den Platzhalter in Kapitel
10.1 — trotzdem unmittelbar vor der Installation auf PyPI verifizieren, ob es zwischenzeitlich eine
neuere stabile Version gibt.

---

## 4. Ist-Zustand des Systems — vollständige, verifizierte Bestandsaufnahme

Alle Angaben unten wurden am 2026-08-02 gegen den echten Code geprüft (nicht aus alten Dokumenten
übernommen).

### 4.1 Die Agenten

| Agent | Datei | Zeilen | Rolle |
|---|---|---|---|
| `BaseAgent` | `demo/agents/base_agent.py` | 74 | gemeinsame Basis (`execute()`, `_get_chat_history()`) |
| `ChatAgent` | `demo/agents/chat_agent.py` | 135 | freies Gespräch, kein Retrieval |
| `RAGAgent` | `demo/agents/rag_agent.py` | 246 | Azure AI Search (`VectorizedQuery`) |
| `OrchestrationAgent` | `demo/agents/orchestration_agent.py` | 1101 | Router + Multi-Step-Planer + Interpreter |
| `SPAgent` (Smart-Planning-Agent) | `demo/agents/sp_agent.py` | 504 | **reiner Executor, macht selbst KEINE LLM-Calls** |
| `EmailAgent` | `demo/agents/email_agent.py` | 288 | fünfter Agent, **nicht** einer der "vier" aus dem Exposé — out of scope |

Die Systemprompts liegen zentral in `demo/agent_config.py` (598 Zeilen): `DEFAULT_CHAT_SYSTEM_PROMPT`
(Z. 64), `DEFAULT_RAG_SYSTEM_PROMPT` (Z. 99), `DEFAULT_ORCHESTRATOR_SYSTEM_PROMPT` + sechs
Orchestrator-Sub-Prompts (Z. 125 ff.). **Wichtig:** `SPAgent` hat gar keinen eigenen Systemprompt in
diesem Sinn — er ist reiner Werkzeug-Ausführer; die LLM-Intelligenz der Korrektur-Pipeline steckt in den
`runtime/*.py`-Skripten (siehe 4.2), nicht im Agenten selbst.

**Kein Semantic Kernel, kein bestehendes Agent-Framework** — das ist ein handgebautes System.
`demo/main.py` (227 Z.) und `demo/web_server.py` (385 Z.) bauen drei getrennte `AzureOpenAI`-Clients
(Chat/RAG/Orchestrierung) und verdrahten die Agenten manuell.

### 4.2 Die "425-Zeilen"-Aussage aus dem Exposé — verifiziert und mit einer wichtigen Korrektur

Die im Exposé genannten "425 Zeilen / 20.284 Zeichen" beziehen sich **nicht** auf einen
Python-String, sondern auf eine externe Markdown-Datei:

```
demo/smart-planning/runtime/runtime-files/llm-validation-fix-rules.md
```

**Diese Datei hat heute (2026-08-02) 936 Zeilen / 36.165 Byte** — mehr als doppelt so groß wie im
Exposé beschrieben. Sie ist seit dem PT4-Commit `cd3d7fc` kontinuierlich gewachsen. **Das musst du in
der Arbeit korrigieren oder neu vermessen** (siehe Kapitel 6.2) — die Exposé-Zahl ist ein veralteter
Schnappschuss, kein aktueller Fakt.

Diese Datei wird nicht direkt gelesen, sondern über `rulebook_loader.load_rulebook()` geladen (siehe
4.4) und als `{fix_rules}` in den Korrektur-Prompt injiziert
(`demo/smart-planning/runtime/generate_correction_llm.py:599-718`).

### 4.3 Die Korrektur-Pipeline im Detail

| Skript | Umfang | Rolle |
|---|---|---|
| `create_snapshot.py` | 254 Z. | Snapshot über Smart-Planning-API anlegen |
| `download_snapshot.py` | — | Snapshot herunterladen |
| `validate_snapshot.py` | 212 Z. | Validierungsnachrichten abholen (löst Validierung NICHT selbst aus) |
| `identify_snapshot.py` | 1130 Z. | Kontextsuche im Snapshot (Feldbeispiele, Formatmuster, verwandte Entitäten) |
| `identify_error_llm.py` | 423 Z. | LLM analysiert Rohfehler, wählt Suchmodus/-wert **und** Regelkarten, ruft `identify_snapshot.py` intern auf |
| `generate_correction_llm.py` | 964 Z. | LLM generiert `llm_correction_proposal.json` (Action/Pfad/Wert/Begründung/Confidence) |
| `validate_correction_schema_llm.py` | 251 Z. | Pydantic-Schemaprüfung, bis zu 3 LLM-Retries bei Schemafehlern |
| `apply_correction.py` | 465+ Z. | wendet geprüften Vorschlag auf `snapshot-data.json` an, mit Backup |
| `update_snapshot.py` | 214+ Z. | schreibt korrigierte Daten zurück an den Server |
| `generate_audit_report.py` | 13.361 B | erzeugt deutschsprachigen Audit-Report aus `metadata.txt` |
| `correction_models.py` | 3.671 B | Pydantic-Modelle (`CorrectionProposal`, `AdditionalUpdate`) |
| `runtime_storage.py` | 125 Z. | Storage-Abstraktion (LOCAL/AZURE) |

**Aufrufmuster:** Jedes Skript ist ein eigenständiges CLI (`argparse`, `if __name__ == "__main__":
main()`) und wird **ausschließlich per `subprocess.run`** aufgerufen — niemals direkt importiert für die
Ausführung. Der Aufrufer ist `SPAgent._run_tool()` (`sp_agent.py:62-138`):

```python
cmd = [_sys.executable, str(script_path)]
result = subprocess.run(cmd, cwd=str(self.runtime_dir), capture_output=True, text=True, timeout=90)
```

**Die Pipeline-Definition** liegt in `demo/agents/sp_tools_config.py` (`SP_PIPELINES`, Z. 105-128):

```
full_correction:            validate_snapshot → identify_error_llm → generate_correction_llm
                             → validate_correction_schema_llm → apply_correction → update_snapshot
                             → validate_snapshot (Re-Validierung)
correction_from_validation:  wie oben, ohne den initialen validate_snapshot-Schritt
```

### 4.4 Der bestehende Iterations-Loop (WICHTIG — zwei getrennte Implementierungen)

**Produktions-Loop** — `SPAgent.execute_pipeline()`, `sp_agent.py:450-503`:

```python
MAX_CORRECTION_ITERATIONS = 5
iteration = 0
while True:
    iteration += 1
    last_result = self._execute_pipeline(pipeline_name, snapshot_id)   # ein Durchlauf der 7 Schritte
    if not is_correction_pipeline or not last_result.get("success"):
        break
    remaining_errors = last_result["final_validation"].get("errors", 0)
    if remaining_errors == 0:
        break                          # Erfolg
    if iteration >= MAX_CORRECTION_ITERATIONS:
        break                          # Abbruch
```

**Governance-Gate davor:** `HUMAN_IN_THE_LOOP` (`agent_config.py:10`) wird in
`orchestration_agent.py:710-738` geprüft — ist es `True`, werden `full_correction`/
`correction_from_validation` **vor** dem Aufruf still auf `analyze_only` umgeschrieben, sodass
`apply_correction`/`update_snapshot` nie ohne menschliche Freigabe laufen.

**Eval-Loop** (separat, nur für Messungen) — `demo/eval/run_iterative.py`: eigene
`for rnd in range(1, args.max+1)`-Schleife, umgeht `sp_agent.py`/`HUMAN_IN_THE_LOOP` bewusst und wendet
direkt an (explizit als Eval-Ausnahme dokumentiert, siehe 4.6).

**Fazit:** Heute entscheidet reiner Python-Kontrollfluss ("identify → generate → validate → apply →
weiter oder stopp"), gesteuert von einer statischen Schrittliste plus Iterationszähler — **keine**
Zustandsmaschine, kein einheitliches, typisiertes Zustandsobjekt.

### 4.5 Das bestehende `RULEBOOK_MODE`-Muster — dein Vorbild für den neuen Schalter

Datei: `demo/rulebook_loader.py` (290 Zeilen). Mechanismus:

- Env-Var wird **einmal, zentral** gelesen: `demo/agent_config.py:21` —
  `RULEBOOK_MODE = os.getenv("RULEBOOK_MODE", "cards").lower()`.
  **Wichtig, weil es dich direkt betrifft (siehe Kapitel 6.1): Der Default ist heute `"cards"`, nicht
  `"monolith"`.**
- Die gesamte Verzweigung ist in **einer** Funktion gekapselt — `load_rulebook()`,
  `rulebook_loader.py:227-275`:
  ```python
  def load_rulebook(error_type=None, extra_cards=None) -> str:
      if RULEBOOK_MODE != "cards":
          return MONOLITH_FILE.read_text(encoding="utf-8")     # "monolith"-Zweig
      # "cards"-Zweig: _core.md + tag-passende Karten + agentenspezifische Karten zusammensetzen
  ```
- Aufrufer (`identify_error_llm.py`, `generate_correction_llm.py`, `validate_correction_schema_llm.py`)
  kennen den Modus selbst nicht — sie rufen nur `load_rulebook(...)` auf.

Das ist **exakt das Muster**, das du für `SP_ARCHITECTURE_MODE` (Kapitel 5) übernehmen solltest: ein
Env-Var, eine Stelle, die verzweigt, alle Aufrufer bleiben unwissend.

### 4.6 Bereits vorhandene Eval-/Testkatalog-Infrastruktur

Du hast hier bereits einen erheblichen Vorsprung — nutze ihn.

| Skript | Zweck | Ergebnis-Datei |
|---|---|---|
| `demo/eval/build_test_catalog.py` (178 Z.) | injiziert je einen bekannten Fehler in echte Snapshots, Ground Truth in `metadata.txt.injected_error` | — |
| `demo/eval/run_isolated_suite.py` | fährt 10 Snapshots mit je einem chirurgischen Fehler, bewertet auf 5 Kriterien | `.../isolated-error-snapshots/pt4-eval-results.json` |
| `demo/eval/run_combined_suite.py` | 10 Snapshots mit mehreren gleichzeitigen Fehlern, testet u.a. Gedächtnis-Wiedererkennung | `.../kombinierte-fehler-snapshots/pt4-combined-results.json` |
| `demo/eval/run_iterative.py` (83 Z.) | Eval-only Multi-Fehler-Loop bis "valide", **erzwingt `RULEBOOK_MODE="cards"` explizit** (Zeile 31-35), wendet ohne Review direkt an | Konsolen-Trail |

Testkataloge auf Platte: `demo/smart-planning/Snapshots/pt4-manipulated_snapshots/
isolated-error-snapshots/` (10 Fälle) und `.../kombinierte-fehler-snapshots/` (10 Fälle), plus
`ok-snapshot.json` als Referenz.

**Bisherige Ergebnisse (aus `docs/PROJECT_LOG.md`, 31.07.–01.08.):** Isoliert 10/10 Erkennung, 4/10 exakter
Wert; kombiniert 18/20 erkannt; iterativer Multi-Fehler-Lauf bis "valide" bewiesen inkl. eines
Gedächtnis-Override mitten im Lauf.

### 4.7 Abweichungen / Lücken zum Exposé, die du kennen musst

- **Kein Terraform im Repository.** Das Exposé (Kapitel 1.2) behauptet, die Infrastruktur sei "über
  Terraform als Infrastructure-as-Code verwaltet". Eine Volltextsuche nach `*.tf`/`*.bicep` und
  Verzeichnissen `terraform|infra|infrastructure|iac` liefert **keinen Treffer**. Es existieren nur ein
  `Dockerfile` und `gunicorn.conf.py`. Für dich heißt das: Das neue GPT-4.1-Deployment (Kapitel 11) legst
  du direkt im Azure-Portal/per `az`-CLI an, nicht per Terraform-Apply — und du solltest diese
  Diskrepanz entweder im Methodenkapitel richtigstellen oder (falls Zeit reicht) tatsächlich ein
  minimales Terraform-Grundgerüst nachziehen. Letzteres ist **nicht** notwendig für die Kernthese, nur
  für die Konsistenz der Infrastruktur-Aussage im Exposé.
- **Der 425-Zeilen-Wert ist veraltet** (siehe 4.2) — heute 936 Zeilen.
- **`RULEBOOK_MODE` steht heute standardmäßig auf `"cards"`, nicht `"monolith"`** — das ist die
  wichtigste Einzelfalle des ganzen Plans, siehe Kapitel 6.1.

---

## 5. Die zentrale Architekturentscheidung: Umschalten statt Ersetzen

### 5.1 Das Koexistenz-Prinzip

Kein bestehendes Skript unter `demo/smart-planning/runtime/` wird gelöscht, umbenannt oder in seinem
CLI-Verhalten verändert. Der Monolith-Pfad (heutiges `SPAgent.execute_pipeline()`,
`sp_agent.py:248-503`) bleibt **byte-identisch** bestehen und ist nach Abschluss der Arbeit weiterhin
die produktive Standardvariante.

### 5.2 Der neue Schalter: `SP_ARCHITECTURE_MODE`

Neue Env-Var, exakt nach dem Vorbild von `RULEBOOK_MODE` (Kapitel 4.5):

```python
# demo/agents/sp_agent.py, ganz oben, analog zu RULEBOOK_MODE in agent_config.py
SP_ARCHITECTURE_MODE = os.getenv("SP_ARCHITECTURE_MODE", "monolith").lower()  # "monolith" | "graph"
```

**Default ist `"monolith"`** — bewusst so gewählt, dass ohne explizites Setzen der Variable **niemand**,
auch nicht bestehende Deployments/Tests, ein verändertes Verhalten sieht. Das ist die technische
Umsetzung deiner Vorgabe "nicht wegschmeißen, nur umschalten".

### 5.3 Wo genau geschaltet wird

**Einziger Verzweigungspunkt:** `SPAgent.execute_pipeline()`, `sp_agent.py:450-503`, ganz am Anfang der
Methode:

```python
def execute_pipeline(self, pipeline_name: str, snapshot_id: str, ...):
    if SP_ARCHITECTURE_MODE == "graph" and pipeline_name in GRAPH_ENABLED_PIPELINES:
        return self._execute_pipeline_graph(pipeline_name, snapshot_id, ...)   # NEU, siehe Kapitel 10
    # -------- ab hier: bestehender Code, UNVERÄNDERT --------
    MAX_CORRECTION_ITERATIONS = 5
    iteration = 0
    while True:
        ...
```

`GRAPH_ENABLED_PIPELINES = {"full_correction", "correction_from_validation"}` — nur die beiden
Korrektur-Pipelines sind vom Schalter betroffen, alle anderen SP-Pipelines (falls vorhanden) laufen
immer über den bestehenden Pfad.

`_execute_pipeline_graph()` ist eine **neue** Methode, die den LangGraph-Aufruf kapselt (Details
Kapitel 10). Sie gibt exakt dieselbe Rückgabestruktur zurück wie `_execute_pipeline()` (gleiche Keys:
`success`, `final_validation`, `total_iterations`, …), damit alles, was `execute_pipeline()`
aufruft (Orchestrator, Web-UI, Eval-Skripte), **nichts** von der internen Umstellung merkt.

### 5.4 Was NICHT angefasst werden darf

- `identify_error_llm.py`, `identify_snapshot.py`, `generate_correction_llm.py`,
  `validate_correction_schema_llm.py`, `apply_correction.py`, `update_snapshot.py`,
  `generate_audit_report.py` — deren CLI-Verhalten (Argumente, stdout, Exit-Codes, erzeugte Dateien)
  bleibt exakt wie heute. Sie werden **additiv erweitert** (siehe 10.2), nie ersetzt.
- `rulebook_loader.py` / `RULEBOOK_MODE` — bleibt unabhängig vom neuen Schalter bestehen; beide Schalter
  sind orthogonal (siehe Kapitel 12 für die Kombination in den Kontrollbedingungen).
- `HUMAN_IN_THE_LOOP`-Gate in `orchestration_agent.py:710-738` — gilt für **beide** Architektur-Modi in
  Produktion gleichermaßen. Nur die Eval-Läufe (analog zum bestehenden `run_iterative.py`-Präzedenzfall)
  dürfen es für Messzwecke explizit und dokumentiert umgehen.

---

## 6. Monolith-Baseline exakt einfrieren — BEVOR der Graph gebaut wird

### 6.1 Die `RULEBOOK_MODE`-Falle (wichtigster Einzelpunkt in diesem Dokument)

**Der Default von `RULEBOOK_MODE` ist heute `"cards"`, nicht `"monolith"`.** Das bedeutet:

- Jeder bisherige Eval-Lauf, der `RULEBOOK_MODE` nicht explizit auf `"monolith"` gesetzt hat, lief
  faktisch bereits im **selektiven Kartenmodus** — nicht gegen die echte Monolith-Baseline.
- `run_iterative.py` **erzwingt nachweislich** `RULEBOOK_MODE="cards"` (Zeile 31-35 im Skript).
- Für `run_isolated_suite.py` und `run_combined_suite.py` ist **nicht verifiziert**, welcher Modus beim
  bisherigen Lauf aktiv war (kein expliziter Override im Code gefunden, das heißt sie liefen vermutlich
  ebenfalls unter dem Default `"cards"`).

**Konsequenz — bevor du irgendeine bestehende Ergebnisdatei (`pt4-eval-results.json`,
`pt4-combined-results.json`) als "Monolith-Baseline" in die Arbeit übernimmst:**

1. Prüfe/dokumentiere, unter welchem `RULEBOOK_MODE` jede vorhandene Ergebnisdatei erzeugt wurde
   (Umgebungsvariable zum Zeitpunkt des Laufs war nicht protokolliert — du musst das ggf. anhand von
   Cardnamen im Trace oder durch einen sauberen Re-Run klären).
2. Fahre **einen echten, sauberen Baseline-Lauf** mit explizit `RULEBOOK_MODE=monolith` über beide
   bestehenden Kataloge (isoliert + kombiniert), **bevor** du den Graphen zum ersten Mal misst. Das ist
   dein tatsächlicher Monolith-Referenzwert.
3. Für die Graph-Variante: `RULEBOOK_MODE=cards` ist die korrekte, architektonisch begründete Einstellung
   (siehe Kapitel 2, letzter Absatz — Knoten 4 IST die selektive Regelzuordnung).

### 6.2 Die Baseline neu vermessen (936 statt 425 Zeilen)

Dokumentiere für den Stand zum Zeitpunkt deiner Messung: exakte Zeilen-/Zeichenzahl von
`llm-validation-fix-rules.md`, Modell, Temperatur/Parameter (aus `generate_correction_llm.py`
auslesen, nicht schätzen), API-Version. Diese Werte gehören als Fußnote oder Tabelle ins
Methodenkapitel — sie werden sich vermutlich noch einmal ändern, bis du tatsächlich misst.

### 6.3 Was als Baseline-Artefakt archiviert werden muss

Für Reproduzierbarkeit (Kapitel 17): vollständiger Text von `llm-validation-fix-rules.md` zum
Messzeitpunkt (Hash + Kopie), exakter Prompt-Aufbau aus `generate_correction_llm.py:599-718` zum
Messzeitpunkt, verwendetes Deployment + API-Version, alle Umgebungsvariablen-Werte
(`RULEBOOK_MODE`, `SP_ARCHITECTURE_MODE`, `AZURE_OPENAI_DEPLOYMENT`).

---

## 7. Die Graph-Architektur — die acht Knoten

Ehrliche Zuordnung zu bestehendem Code — inklusive der Stellen, an denen die Grenze heute **nicht**
sauber verläuft und explizit gezogen werden muss.

| # | Knoten | Ein-/Ausgang | Bestehender Code | Zu tun |
|---|---|---|---|---|
| 1 | **Eingabeanalyse** | Snapshot-ID/Anfrage → strukturierte Aufgabenbeschreibung | kein dedizierter Code — heute implizit in `OrchestrationAgent._execute_sp_agent` (`orchestration_agent.py:740, 825`) | dünner neuer Wrapper (Graph-Entry-Point), kein LLM-Call nötig |
| 2 | **Fehlerklassifikation** | Validierungsergebnis → Tag/Priorität/Begründung | `identify_error_llm.py` — **macht heute mehr** (wählt zusätzlich Suchmodus UND Regelkarten) | additiv: Klassifikations-Teilfunktion aus dem Skript herausziehen (siehe 10.2), Kartenauswahl wandert zu Knoten 4 |
| 3 | **Kontextsuche** | Fehler → Kontextfenster (Feldbeispiele, Formatmuster) | `identify_snapshot.py` (1130 Z.) — **1:1 wiederverwendbar**, wird heute schon von Knoten 2 aufgerufen | Funktions-Wrapper, keine Logikänderung |
| 4 | **Regelzuordnung** | klassifizierter Fehler → relevante Regeln | `rulebook_loader.load_rulebook(error_type=...)` im `cards`-Modus — **1:1 wiederverwendbar**, aber heute intern in Knoten 2/5 versteckt statt eigener sichtbarer Schritt | als eigenen, geloggten Graph-Schritt exponieren (welche Karten geladen wurden ins `GraphState`) |
| 5 | **Korrekturgenerierung** | Kontext + Regeln → JSON-Vorschlag + Begründung | `generate_correction_llm.py` (964 Z.) — **der zentrale LLM-Call bleibt inhaltlich ein Call**, wird aber zum expliziten, isolierten, geloggten Knoten statt Teil einer impliziten Subprocess-Kette | additiv: aufrufbare Funktion extrahieren (10.2) |
| 6 | **Technische Prüfung** | Vorschlag → Validierungsstatus | `validate_correction_schema_llm.py` (251 Z.) — **1:1 wiederverwendbar** | Funktions-Wrapper |
| 7 | **Ergebnisbewertung** | Validierungsstatus → weiter/abschließen/unsicher | heute reine `if/else`-Logik in `sp_agent.py:450-503`, **kein eigener Code-Block** | wird zur bedingten LangGraph-Kante selbst (Kapitel 9) |
| 8 | **Antwortformulierung** | finaler Zustand → Audit-Report | `generate_audit_report.py` — **1:1 wiederverwendbar** | Funktions-Wrapper |

**Pragmatische Entscheidung für die erste lauffähige Version (MVP):** Knoten 2 sauber von seiner
heutigen Kartenauswahl-Nebenfunktion zu trennen ist ein echter Eingriff in `identify_error_llm.py`. Baue
für die erste Version den Graphen so, dass Knoten 2 das bestehende Skript unverändert **als Ganzes**
aufruft (inkl. seiner heutigen Kartenauswahl) und dokumentiere das als bewusste Vereinfachung — das ist
kein Strohmann, weil es derselbe, unveränderte Code ist, nur (noch) nicht granular genug aufgeteilt.
Wenn die Zeit reicht, verfeinere in einer zweiten Iteration (additiv, siehe 10.2).

---

## 8. `GraphState` — vollständige Feldliste

```python
from typing import TypedDict, Literal, Optional

class GraphState(TypedDict):
    # Identität und Lauf-Metadaten
    snapshot_id: str
    iteration: int
    max_iterations: int
    architecture_mode: Literal["graph"]        # zur eindeutigen Kennzeichnung in Logs
    started_at: str                              # ISO-8601 UTC
    finished_at: Optional[str]

    # Fehlerzustand
    errors_before: int
    errors_after: Optional[int]
    validation_result: Optional[dict]            # Rohergebnis der Validierungs-Engine

    # Knoten-Ausgänge (jeder Knoten schreibt genau sein Feld)
    classified_error: Optional[dict]              # {tag, priority, reasoning, raw_message}
    extracted_context: Optional[dict]              # {target_path_hint, field_examples, lines_used, search_mode}
    matched_rules: Optional[dict]                  # {rulebook_mode, cards_loaded: list[str], rule_text_hash}
    correction_proposal: Optional[dict]             # {action, target_path, new_value, reasoning, llm_confidence, confidence_score}
    technical_check: Optional[dict]                 # {schema_valid, retries, errors: list}
    decision: Optional[dict]                        # {action: "continue"|"stop_valid"|"stop_max_iter"|"stop_uncertain", reasoning}

    # Nachvollziehbarkeits-Instrument (das wichtigste Feld für UF3/Nachvollziehbarkeit)
    trace: list[dict]   # je Eintrag: {node, timestamp_utc, input_digest, output_digest, duration_ms}
```

**Warum `trace` das Kernstück ist:** Es ist der rekonstruierbare Entscheidungspfad, den der Monolith
per Definition nicht hat (Kapitel 2). Jeder Knoten hängt seinen Eintrag an — das ist dein primäres
Beweismittel für UF3 im Nachvollziehbarkeits-Kapitel.

---

## 9. Kanten und Kontrollfluss

```
START → [1 Eingabeanalyse] → [2 Fehlerklassifikation] → [3 Kontextsuche] → [4 Regelzuordnung]
      → [5 Korrekturgenerierung] → [6 Technische Prüfung] → bedingte Kante (Knoten 7)
```

**Bedingte Kante nach Knoten 6 (das ist Knoten 7, als Kante modelliert):**

| Bedingung | Ziel |
|---|---|
| `technical_check.schema_valid == False` und Retries übrig | zurück zu [5 Korrekturgenerierung] |
| `technical_check.schema_valid == True` und `errors_after == 0` | weiter zu [8 Antwortformulierung] → `decision.action = "stop_valid"` |
| `technical_check.schema_valid == True`, `errors_after > 0`, `iteration < max_iterations` | zurück zu [2 Fehlerklassifikation] mit aktualisiertem `validation_result` |
| `iteration >= max_iterations` | weiter zu [8], `decision.action = "stop_max_iter"`, `manual_intervention_required = True` |
| Knoten 2/5 liefert kein `target_path` (bekannte Fähigkeitslücke, siehe PROJECT_LOG I09/I10) | weiter zu [8], `decision.action = "stop_uncertain"` |

Der letzte Fall ist **kein Sonderfall, den du dir ausdenkst** — er ist die exakte Formalisierung eines
bereits real beobachteten Verhaltens (`target_path=None`-Fälle aus den bisherigen Eval-Läufen, siehe
`docs/PROJECT_LOG.md`, 31.07.). Für die Robustheits-Dimension (UF2) ist genau das der positiv zu
wertende "ehrliches Nein statt halluzinierter Korrektur"-Pfad.

---

## 10. Technische Umsetzung — Schritt für Schritt

### 10.1 Dependencies

Zu `demo/requirements.txt` (und/oder `requirements-azure.txt`, je nachdem wo die anderen
LLM-Abhängigkeiten stehen) hinzufügen und **pinnen** (exakte Version, kein `>=`):

```
langgraph==1.2.10
langchain-core==1.5.3
```
(Stand 02.08.2026, siehe Kapitel 3.3.5 — unmittelbar vor der Installation auf PyPI erneut verifizieren.)

Direkt danach: `pip install -r requirements.txt` in einer sauberen virtuellen Umgebung, dann
**Smoke-Test** — bestehende Test-Suite (falls vorhanden) und mindestens einen manuellen
Monolith-Pipeline-Lauf durchführen, um sicherzustellen, dass die neuen Pakete keine bestehenden
Abhängigkeiten (z. B. `openai`, `pydantic`-Version) brechen. `pydantic` ist bereits im Projekt aktiv
(`correction_models.py`) — LangChain/LangGraph haben eigene Pydantic-Versionsanforderungen; das ist der
wahrscheinlichste Konfliktpunkt und muss zuerst geprüft werden.

### 10.2 Node-Kapselungsstrategie: additive Funktionsextraktion

Jedes wiederzuverwendende Skript bekommt **eine neue, zusätzliche** aufrufbare Funktion, ohne die
bestehende CLI-`main()` zu verändern. Muster (Beispiel `generate_correction_llm.py`):

```python
# VORHER (unverändert stehen lassen):
def main():
    args = parser.parse_args()
    ... # baut Prompt, ruft API auf, schreibt Datei

if __name__ == "__main__":
    main()

# NEU, additiv ergänzt — main() ruft diese Funktion jetzt auf, Verhalten bleibt identisch:
def run_correction_generation(snapshot_id: str, target_context: dict, rules_text: str, ...) -> dict:
    """Kernlogik, aufrufbar sowohl von main() (CLI/Subprocess) als auch vom Graph-Knoten (Direktaufruf)."""
    ... # exakt dieselbe Logik wie bisher in main(), nur parametrisiert statt aus argparse gelesen
    return proposal_dict

def main():
    args = parser.parse_args()
    result = run_correction_generation(args.snapshot_id, ...)
    # Datei schreiben, stdout ausgeben — wie bisher
```

**Warum das der richtige Weg ist:** Es gibt danach nur noch **eine** Implementierung der Kernlogik (kein
Drift-Risiko zwischen "CLI-Version" und "Graph-Version"), und der Monolith-Pfad (`main()` via
Subprocess) ist von der Umstellung **null** betroffen — er ruft intern nur eine Ebene tiefer.

Führe diese Extraktion für: `identify_error_llm.py`, `identify_snapshot.py` (ggf. bereits
importierbar — prüfen), `generate_correction_llm.py`, `validate_correction_schema_llm.py`,
`generate_audit_report.py`.

**Reihenfolge-Empfehlung:** Fange mit `generate_correction_llm.py` (Knoten 5) an — das ist der
LLM-lastigste und wichtigste Knoten. Danach `validate_correction_schema_llm.py` (Knoten 6, am
einfachsten, guter zweiter Schritt zum Muster-Festigen). Dann `identify_error_llm.py`/
`identify_snapshot.py` (Knoten 2/3/4, am meisten Entflechtungsaufwand wegen der Kartenauswahl-Vermischung,
siehe Kapitel 7).

### 10.3 Dateilayout für den neuen Graph-Code

Neues Verzeichnis, komplett additiv, nichts Bestehendes wird verschoben:

```
demo/smart-planning/graph/
    __init__.py
    graph_state.py          # GraphState-Definition (Kapitel 8)
    correction_graph.py      # StateGraph-Aufbau, Knoten-Registrierung, Kanten (Kapitel 9)
    nodes/
        __init__.py
        input_analysis.py    # Knoten 1
        classification.py    # Knoten 2 (ruft identify_error_llm.run_...())
        context_search.py    # Knoten 3 (ruft identify_snapshot.run_...())
        rule_matching.py      # Knoten 4 (ruft rulebook_loader.load_rulebook())
        correction.py         # Knoten 5 (ruft generate_correction_llm.run_correction_generation())
        technical_check.py    # Knoten 6 (ruft validate_correction_schema_llm.run_...())
        answer.py             # Knoten 8 (ruft generate_audit_report.run_...())
```

### 10.4 Azure-Client-Wiederverwendung

**Nicht** einen neuen Azure-OpenAI-Client für den Graphen bauen. Die bestehenden Runtime-Skripte lesen
bereits `AZURE_OPENAI_DEPLOYMENT`/`AZURE_OPENAI_API_KEY`/`AZURE_OPENAI_API_VERSION`/
`AZURE_OPENAI_ENDPOINT` (z. B. `generate_correction_llm.py:592-595`). Die extrahierten Funktionen
(10.2) nutzen exakt denselben Client-Aufbau wie die bestehende `main()` — dadurch ist Modell und
Parameter-Gleichheit zwischen Monolith- und Graph-Pfad **strukturell garantiert**, nicht nur
dokumentiert.

### 10.5 Logging/Trace-Persistenz

Jeder Knoten hängt einen Eintrag an `state["trace"]` (Kapitel 8). Zusätzlich: nach jedem vollständigen
Graph-Lauf den kompletten `GraphState` (minus evtl. sehr große Rohdaten) als JSON in die
Iterationsordner-Struktur schreiben, analog zu `metadata.txt` im Monolith-Pfad — das ist deine
Rohdatenbasis für Kapitel 17 (Reproduzierbarkeit).

---

## 11. GPT-4.1-Deployment — Schritt für Schritt

**Scope-Klarstellung zuerst:** Von den vier bestehenden Deployment-Konfigurationen
(`AZURE_OPENAI_CHAT_DEPLOYMENT`, `AZURE_OPENAI_RAG_DEPLOYMENT`, `AZURE_OPENAI_ORCHESTRATION_DEPLOYMENT`,
und der generischen `AZURE_OPENAI_DEPLOYMENT` für die Korrektur-Pipeline) betrifft deine
Forschungsfrage **ausschließlich die letzte** — `AZURE_OPENAI_DEPLOYMENT`, verwendet in
`identify_error_llm.py`, `generate_correction_llm.py`, `validate_correction_schema_llm.py`. Chat/RAG/
Orchestrierung sind laut Exposé-Abgrenzung nicht Vergleichsgegenstand. Du **kannst** sie aus
Konsistenzgründen mit hochziehen, musst es aber nicht — das spart Kosten und Zeit, wenn du dich aufs
Nötige beschränkst.

**Schritte:**

1. Im Azure-Portal (oder per `az cognitiveservices account deployment create`) ein neues Deployment im
   selben Azure-OpenAI-Resource wie das bestehende `gpt-4o`-Deployment anlegen: Modell `gpt-4.1`,
   gleiche Region prüfen (Modellverfügbarkeit ist regional unterschiedlich — vor dem Anlegen in der
   Azure-Doku/Portal-UI verifizieren, ob GPT-4.1 in deiner Region verfügbar ist), Quota/Kapazität nach
   erwartetem Testvolumen (Kapitel 13) dimensionieren.
2. Neuen Deployment-Namen wählen (z. B. `gpt-4.1` oder `gpt-41-correction`) und in `demo/.env` als
   Wert für `AZURE_OPENAI_DEPLOYMENT` eintragen. **Empfehlung:** Lege dir zusätzlich eine zweite Variable
   `AZURE_OPENAI_DEPLOYMENT_LEGACY_4O` mit dem alten Wert an (nicht im Code verwendet, nur als
   Dokumentations-/Rollback-Anker), falls du für einen Vergleichslauf kurzfristig zurückschalten willst.
3. API-Version prüfen: GPT-4.1 kann eine neuere `AZURE_OPENAI_API_VERSION` voraussetzen als die aktuell
   verwendete `2025-01-01-preview` — in der Azure-Dokumentation zum Modell-Release nachsehen und ggf.
   anpassen (betrifft dann ebenfalls nur die drei genannten Skripte, da sie ihre eigene, von Chat/RAG/
   Orchestrierung unabhängige Env-Var-Gruppe lesen, siehe Kapitel 4.1 in der ursprünglichen Bestandsaufnahme).
4. **Regressionstest vor jeder weiteren Arbeit:** Einen bekannten, bereits vermessenen Testfall (z. B.
   den Dichte-Fall aus der isolierten Suite) einmal unverändert über den bestehenden Monolith-Pfad mit
   dem neuen GPT-4.1-Deployment laufen lassen. Damit trennst du sauber "Modellwechsel-Effekt" von
   "Architektur-Effekt" — beide dürfen sich in deiner späteren Messung nicht vermischen.
5. Kein Terraform vorhanden (Kapitel 4.7) — die Deployment-Erstellung bleibt manuell/per CLI-Skript,
   nicht per IaC-Apply. Dokumentiere die exakten Anlage-Parameter (Modellversion, Region, Kapazität,
   Zeitpunkt) trotzdem schriftlich, damit die Arbeit reproduzierbar bleibt.

---

## 12. Kontrollbedingungen für den fairen Vergleich — eingefroren

Was zwischen Monolith- und Graph-Lauf **identisch** sein muss:

| Bedingung | Wert / Vorgehen |
|---|---|
| Modell | GPT-4.1, beide Varianten (nach Kapitel 11) |
| Modellparameter | Temperatur/top_p/max_tokens exakt aus dem Code auslesen (`generate_correction_llm.py`) und für beide Varianten fixieren und dokumentieren — nicht raten |
| Kontextextraktion | `identify_snapshot.py` unverändert, für beide Pfade identisch aufgerufen |
| `RULEBOOK_MODE` | **`monolith`** für die Monolith-Variante, **`cards`** für die Graph-Variante (das ist architektonisch begründet, siehe Kapitel 2 — kein Konfundierungsfehler, wenn im Text explizit benannt) |
| `SP_ARCHITECTURE_MODE` | `monolith` bzw. `graph` — der einzige bewusst variierte Faktor |
| Testfälle | identisch, aus den bestehenden Katalogen (Kapitel 4.6) |
| Ausführungsreihenfolge | randomisiert (Fall, Variante) — kleines Skript, das die Paare mischt und Zeitstempel protokolliert |
| `HUMAN_IN_THE_LOOP` | für Messzwecke bei beiden Varianten identisch behandeln (entweder beide eval-only direkt-anwenden wie `run_iterative.py`, oder beide über echtes Review — nicht mischen) |

---

## 13. Testfallkatalog — Stand, Lücken, Zielgröße

**Vorhanden:** 10 isolierte Einzelfehler-Fälle, 10 kombinierte Mehrfehler-Fälle, mit dokumentierter
Ground Truth (Kapitel 4.6). Das ist eine solide Basis für UF1 (Halluzination unter kontrollierten
Bedingungen).

**Fehlt noch:**
- **Wiederholungsläufe** für UF2 (Robustheit): Aktuell läuft jeder Katalog-Fall genau **einmal**. Für die
  Konsistenzmessung brauchst du denselben Fall 3–5× mit identischer Eingabe, für **beide** Varianten,
  um sprachliche Variabilität von inhaltlicher Instabilität zu trennen (siehe Kapitel 15.3). Baue dafür
  einen dünnen Wiederholungs-Wrapper um `run_isolated_suite.py`/`run_combined_suite.py` (oder ein neues
  Skript `run_repeated_suite.py`), der denselben Fall N-mal fährt und die *fachlichen* Korrekturwerte
  (nicht die Formulierung) vergleicht.
- **Grenzfälle** (fehlende Pflichtfelder, unbekannte Feldwerte, strukturell abweichende Snapshots) —
  aktuell nicht im Katalog. Für UF2/Robustheit brauchst du mindestens eine Handvoll solcher Fälle, bei
  denen "keine Korrektur erzwingen, sondern Unsicherheit ausweisen" die richtige Antwort ist.
- **Zielgröße:** 15–30 distinkte Fälle über die Fehlerklassen verteilt, falls die Zeit reicht — bei
  aktuell 20 Fällen (10+10) bist du schon über der Hälfte.

---

## 14. Ground-Truth-/Fehlerinjektionsmethodik

Deine Methode (`build_test_catalog.py` — bekannter Originalwert wird vor der Injektion als Ground Truth
in `metadata.txt` festgehalten) ist selbst ein methodischer Beitrag, weil das Exposé (Kapitel 1.3) genau
dieses Messproblem als offen benennt ("Da keine automatisierte Ground-Truth-Validierung existiert…").
Schreibe explizit im Methodenkapitel: konstruierter Input ist zulässige, gängige Praxis; die Ground
Truth selbst bleibt objektiv (der echte Originalwert), du erfindest **nie** Bewertungen oder
Experten-Urteile.

---

## 15. Die drei Messdimensionen — Operationalisierung

### 15.1 Halluzinationsrate

Vier Kategorien, pro Testfall zu vergeben:

1. **Fachliche Halluzination** — falscher Korrekturwert (automatisch messbar für injizierte
   Standardfälle: Vergleich mit Ground Truth aus `build_test_catalog.py`).
2. **Strukturelle Halluzination** — ungültiges JSON/Schema-Verstoß (automatisch messbar: Knoten 6 /
   `validate_correction_schema_llm.py`).
3. **Regelhalluzination** — Berufung auf nicht existente/falsch interpretierte Regel (prüfbar gegen das
   reale Regelwerk; im Graphen ist `matched_rules` — Knoten 4 — dafür Gold wert, weil dort exakt
   protokolliert ist, welche Karte geladen wurde).
4. **Folgefehlererzeugung** — Korrektur erzeugt neuen Fehler (automatisch messbar: Re-Validierung,
   `errors_after > 0` oder neuer Fehlertyp).

Aufschlüsseln nach Standard- vs. Komplexfällen — die These erwartet den Effekt primär bei Komplexfällen.

### 15.2 Nachvollziehbarkeit

- **Struktureller Nachweis:** Graph hat per Konstruktion das `trace`-Feld, Monolith hat es nicht — das
  ist der qualitative Kernunterschied, belegt an konkreten Fallgegenüberstellungen.
- **Experten-Rating:** Skala 1–5, "wie gut kann ich nachvollziehen, welcher Fehler erkannt, welche Regel
  angewandt, welche Daten herangezogen wurden?"
- **Der harte Test:** bei *falschen* Korrekturen — kann man erkennen, wo der Prozess abbog? Beim
  Monolith praktisch nie, beim Graph über `trace` lokalisierbar. Stärkster Beleg für UF3.

### 15.3 Robustheit

- **Konsistenz (quantitativ):** Wiederholungstest (Kapitel 13), identische Eingabe, N Läufe. Miss die
  Streuung der *fachlichen* Korrektur, nicht der Formulierung. Metrik: Anteil identischer fachlicher
  Ergebnisse.
- **Grenzfallverhalten (qualitativ):** Erkennt die Variante den Grenzfall? Weist sie Unsicherheit aus
  (`decision.action == "stop_uncertain"`, Kapitel 9) statt eine unbelegte Korrektur zu erzwingen? Ein
  "ehrliches Nein" ist die bessere Antwort und muss positiv gewertet werden.

---

## 16. Messinstrumentarium

- **Experten-Bewertung** (primäre qualitative Quelle): 2–4 Personen aus Projekt-/Kundenumfeld,
  einheitliches Raster (fachliche Korrektheit, Regelkonformität, Nachvollziehbarkeit, technische
  Verwendbarkeit, Folgefehler-Risiko). **Blind:** Präsentiere nur das fachliche Endergebnis
  (Korrekturvorschlag + Begründung) in einem variantenneutralen Format — nie den Rohtrace (der verrät
  sofort die Variante).
- **SUS + UEQ:** mindestens 5 Teilnehmende, ergänzende Nutzerperspektive, explizit als "Indikatoren",
  keine signifikanten Ergebnisse bei so kleinem n.
- **RAGAS:** nur für den RAG-Agenten-Teilaspekt (Regelzuordnungs-/Kontextqualität), nicht für
  JSON-Korrekturen selbst.
- **Bewusst nicht eingesetzt:** BLEU/ROUGE — messen Wortüberlappung, nicht fachliche Korrektheit.

---

## 17. A/B-Experimentdesign & Reproduzierbarkeitsprotokoll

Für jeden Lauf protokollieren: Zeitstempel, Variante (`SP_ARCHITECTURE_MODE`), Fall-ID, Modell+Version,
Parameter, `RULEBOOK_MODE`, voller Prompt (oder Hash), volle Antwort, `trace` (bei Graph) bzw.
äquivalente Subprocess-Log-Kette (bei Monolith). Ausführungsreihenfolge randomisieren (kleines
Runner-Skript, das (Fall, Variante)-Paare mischt). Diese Rohdaten sind der Anhang deiner Arbeit — ohne
sie ist keine Zahl belastbar.

---

## 18. Entscheidungslogik / Auswertungsraster

Der Graph gilt als vorteilhaft, wenn er (a) weniger fachlich falsche/unbelegte Korrekturen erzeugt,
(b) weniger Folgefehler, (c) stabilere Ergebnisse bei Wiederholung, (d) von Experten als nachvollziehbarer
bewertet wird. **Kein vorab festgelegtes Ergebnis** — eine differenzierte Aussage ("Graph gewinnt *wo*,
verliert *wo*, neutral *wo*") ist wissenschaftlich stärker als ein pauschales "besser". Pro Dimension
eine Tabelle Monolith vs. Graph, aufgeschlüsselt nach Standard-/Komplexfällen; deskriptive Statistik,
Signifikanztest nur wenn n und Voraussetzungen es zulassen.

---

## 19. Bedrohungen der Validität — Checkliste

- [ ] **Strohmann-Baseline** — Baseline ist der reale Ist-Zustand (Kapitel 2), nicht künstlich
      verschlechtert.
- [ ] **`RULEBOOK_MODE`-Kontamination** — jede Ergebnisdatei ist eindeutig einem Modus zugeordnet
      (Kapitel 6.1), kein unbeabsichtigtes Mischen.
- [ ] **Modell-Konsistenz** — GPT-4.1 in beiden Varianten, Regressionstest gegen bekannten Fall
      durchgeführt (Kapitel 11, Schritt 4).
- [ ] **Konfundierende Faktoren** — Parameter/Extraktion/Testfälle identisch, `RULEBOOK_MODE`-Unterschied
      explizit als Teil der Graph-Definition benannt, nicht verschwiegen.
- [ ] **Gebrochene Blindung** — Experten sehen nur variantenneutrales Format, nie den Rohtrace.
- [ ] **Kleine Stichprobe** — als Limitation benannt, Aussagen "deskriptiv" statt "signifikant" solange
      n klein.
- [ ] **Zirkuläre Messung** — vor der Messung geprüft, ob das Messinstrument für ALLE Fehlerklassen das
      Richtige misst (bekanntes reales Beispiel aus PT4: ein `value_grounded`-Term zeigte für eine ganze
      Fehlerklasse falsch herum).
- [ ] **Reproduzierbarkeit** — vollständige Rohdaten-Protokolle im Anhang (Kapitel 17).
- [ ] **Forscher-Bias** — Blindung bei Experten, deterministische Metriken wo möglich, keine
      nachträglichen Anpassungen nach Sehen der Ergebnisse.

---

## 20. Ethik & Daten

Anonymisierte/freigegebene Snapshot-Daten, keine echten Produktionsdaten löschen oder unautorisiert
zurückspielen. Testläufe ausschließlich auf der SP-Testinstanz, nicht produktiv — konsistent mit der
bestehenden Praxis (siehe Nutzer-Freigabe-Vermerke in `docs/PROJECT_LOG.md`).

---

## 21. Zeitplan, realistisch ab heute

Der Exposé-Zeitplan sah Phase 2 (Implementierung) bis 21.07. und Phase 3 (Evaluation) bis 04.08. vor.
**Heute existiert noch keine Zeile Graph-Code** — das ist Fakt, kein Vorwurf. Realistischer, kritischer
Pfad ab jetzt:

1. **Sofort:** Kapitel 3 fixieren (bereits erledigt), Kapitel 6.1 auflösen (RULEBOOK_MODE-Klarheit
   herstellen), GPT-4.1-Deployment anlegen (Kapitel 11).
2. **Als Nächstes:** `SP_ARCHITECTURE_MODE`-Schalter einbauen (Kapitel 5) — das ist eine kleine, risikoarme
   Änderung und schafft sofort die geforderte Koexistenz-Struktur.
3. **Danach:** Node-Extraktion Skript für Skript (Kapitel 10.2), beginnend mit Knoten 5/6 (am wichtigsten,
   am wenigsten Entflechtungsaufwand), dann Knoten 2/3/4.
4. **Parallel:** Wiederholungs- und Grenzfall-Erweiterung des Testkatalogs (Kapitel 13).
5. **Dann:** sauberer Monolith-Baseline-Lauf (Kapitel 6.1, Schritt 2) — **bevor** der erste Graph-Vergleich
   gezogen wird.
6. **Dann:** A/B-Läufe, Rohdaten protokollieren, auswerten, schreiben.

**Priorität, wenn die Zeit eng wird:** Die Nachvollziehbarkeits-Dimension ist am wenigsten von großer
Fallzahl abhängig und am greifbarsten (`trace`-Feld existiert oder nicht — das ist ein harter,
sofort sichtbarer Unterschied). Ein sauber belegter Teilbefund schlägt eine überdehnte Gesamtaussage.

---

## 22. Kapitelstruktur der schriftlichen Arbeit (Referenz)

1. Einleitung — Problem, Praxiskontext, Forschungsfrage, Thesen, Abgrenzung
2. Theoretische Grundlagen — LLMs/Prompt Engineering, monolithische Prompts, graph-basierte
   Architekturen, Graph-of-Thoughts, Halluzinationen, LLM-Evaluation
3. Das bestehende System — Vier-Agenten-Architektur, Pipeline, Grenzen des Monolithen (Kapitel 4 dieses
   Dokuments als Rohmaterial)
4. Konzeption der Graph-Architektur — Designprinzipien, Knoten/Kanten, präzise Monolith/Graph-Definition
   (Kapitel 2 und 7–9 dieses Dokuments als Rohmaterial)
5. Forschungsdesign und Methodik — Kontrollbedingungen, Bewertungsmethoden (Kapitel 11–12, 17)
6. Evaluierungsdesign — Operationalisierung, Testfallkatalog, Bewertungsverfahren (Kapitel 13–16)
7. Ergebnisse — Messungen nach Dimension und Komplexität
8. Diskussion — kritischer Rückbezug, Limitationen (Kapitel 19)
9. Fazit und Ausblick — Designrichtlinien, Weiterentwicklung

---

## 23. MASTER-CHECKLISTE — alles in Umsetzungsreihenfolge

- [ ] **GPT-4.1-Deployment** in Azure anlegen, `.env` (`AZURE_OPENAI_DEPLOYMENT`) umstellen, API-Version
      geprüft, Regressionstest gegen bekannten Fall auf dem Monolith-Pfad gefahren (Kap. 11)
- [ ] **`RULEBOOK_MODE`-Historie geklärt**: für jede bestehende Ergebnisdatei den tatsächlichen Modus
      verifiziert oder als unbekannt markiert (Kap. 6.1)
- [ ] **Sauberer Monolith-Baseline-Lauf** mit `RULEBOOK_MODE=monolith` + GPT-4.1 über beide Kataloge
      gefahren und archiviert (Kap. 6.1, 6.3)
- [ ] **`langgraph`/`langchain-core`** installiert und gepinnt, Abhängigkeitskonflikte geprüft (Kap. 10.1)
- [ ] **`SP_ARCHITECTURE_MODE`-Schalter** in `sp_agent.py` eingebaut, Default `"monolith"`, bestehender
      Pfad unverändert lauffähig (Kap. 5)
- [ ] **Node-Funktionsextraktion** für `generate_correction_llm.py` (Knoten 5) — additiv, CLI unverändert
      (Kap. 10.2)
- [ ] **Node-Funktionsextraktion** für `validate_correction_schema_llm.py` (Knoten 6) (Kap. 10.2)
- [ ] **Node-Funktionsextraktion** für `identify_error_llm.py`/`identify_snapshot.py` (Knoten 2/3/4),
      inkl. Entscheidung MVP vs. volle Auftrennung der Kartenauswahl (Kap. 7)
- [ ] **Node-Funktionsextraktion** für `generate_audit_report.py` (Knoten 8) (Kap. 10.2)
- [ ] **`GraphState`** implementiert (Kap. 8), **`correction_graph.py`** mit StateGraph, Knoten, Kanten
      inkl. bedingter Rück-Kante (Kap. 9)
- [ ] **`_execute_pipeline_graph()`** in `sp_agent.py` gebaut, liefert identische Rückgabestruktur wie
      `_execute_pipeline()` (Kap. 5.3)
- [ ] Erster Ende-zu-Ende-Testlauf Graph-Pfad auf einem bekannten Einzelfehler-Fall — Ergebnis mit
      Monolith-Baseline auf demselben Fall verglichen
- [ ] **Wiederholungs-Wrapper** für UF2 gebaut (Kap. 13)
- [ ] **Grenzfall-Testfälle** ergänzt (Kap. 13)
- [ ] **Randomisierter A/B-Runner** gebaut (mischt Fall×Variante, protokolliert Rohdaten) (Kap. 17)
- [ ] Vollständige A/B-Läufe über beide Kataloge + Wiederholungen + Grenzfälle gefahren
- [ ] **Experten-Bewertungsraster** vorbereitet, blindes/variantenneutrales Präsentationsformat gebaut
      (Kap. 16)
- [ ] SUS/UEQ-Fragebögen vorbereitet, ≥5 Teilnehmende organisiert (Kap. 16)
- [ ] Auswertung je Dimension (Kap. 15) durchgeführt, Validitäts-Checkliste (Kap. 19) durchgegangen
- [ ] Kapitel 7–9 der Arbeit geschrieben (Kap. 22)
- [ ] Terraform-Diskrepanz (Kap. 4.7) entweder im Text korrigiert oder Infrastruktur nachgezogen

---

## 24. Literatur / Quellen zu Kapitel 3.3 (für dein Literaturverzeichnis)

- Besta, M. et al. (2024). *Graph of Thoughts: Solving Elaborate Problems with Large Language Models.*
  AAAI. Code: https://github.com/spcl/graph-of-thoughts
- Wen, Y., Wang, Z., Sun, J. (2024). *MindMap: Knowledge Graph Prompting Sparks Graph of Thoughts in
  Large Language Models.* ACL. Code: https://github.com/wyl-willing/MindMap
- Madaan, A. et al. (2023). *Self-Refine: Iterative Refinement with Self-Feedback.* arXiv:2303.17651.
- Shinn, N., Labash, B., Gopinath, A. (2023). *Reflexion: Language Agents with Verbal Reinforcement
  Learning.* arXiv:2303.11366.
- Paul, D. et al. (2023). *REFINER: Reasoning Feedback on Intermediate Representations.*
  arXiv:2304.01904.
- LangGraph-Dokumentation: offizielle Muster für bedingte Retry-Kanten (`state["error"]`/
  `state["iterations"]`-Router) und `interrupt()`/`Command(resume=...)` für Human-in-the-Loop —
  aktuelle Version zum Zitierzeitpunkt in `reference.langchain.com/python/langgraph` prüfen.
