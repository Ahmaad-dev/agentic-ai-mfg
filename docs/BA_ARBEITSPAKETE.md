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
| **0** | **Vorbedingungen** | — | ~0,5 T | ☑ |
| **A** | Umgebung final machen | **0** | ~1,5 T | ☑ |
| **B** | Regressionsreferenz *(+ HitL-Entscheidung)* | **A vollständig** | ~0,5 T | ☑ |
| **C** | Schalter und Gerüst | A | ~0,5 T | ☑ |
| **D** | Knoten extrahieren | C | ~4–5 T | ☑ **abgeschlossen 20.08.** |
| **E** | Graph verdrahten | D | ~2 T | ☑ **20.08. vollstaendig** (DoD 8/8) |
| **F** | Vertikaler Durchstich | E, B | ~2 T | ☑ **20.08. final** — A/B/C gefahren, F5 10/10 |
| **G** | Pilotphase + Einfrieren | F | ~3 T *(kürzbar)* | ☐ |
| **H** | Messen — **A / B / C** | **G eingefroren** | ~4 T | ☐ |
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

**B und C/D/E können parallel laufen** — die Regressionsreferenz braucht den Graphen nicht.
Wer allein arbeitet, macht B zuerst: es ist kurz und legt die HitL-Behandlung fest, die alle
spaeteren Laeufe brauchen.

> **Die Messung findet ausschliesslich in AP-H statt**, nach dem Einfrieren (G5), fuer alle drei
> Bedingungen A/B/C gemeinsam. AP-B liefert **keine** Zahlen fuer Kapitel 7.

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

# AP-0 — Vorbedingungen  ~0,5 Tage

**Ziel:** Ein Zustand, aus dem heraus jede Änderung rückgängig zu machen ist — bevor das erste
Paket installiert wird.

### 0.1 — ⚠ Virtuelle Umgebung anlegen *(die wichtigste Vorbedingung)*

**Befund 19.08.2026:** Es gibt **keine venv**. Python 3.13.3 läuft aus
`C:\Program Files\Python313` mit **106 Paketen** — dem System-Interpreter.

Warum das vor AP-A gelöst sein muss:

* **Kein Rollback.** Wenn `langgraph` `pydantic` verschiebt, gibt es kein „zurück". `pydantic`
  liegt über `correction_models.py` **im gemessenen Pfad**.
* **Das Produktivsystem hängt mit drin.** Dasselbe Python führt PT4 aus.
* **Der Code erwartet es bereits.** `sp_agent.py:81` kommentiert wörtlich
  *„sys.executable: Nutze das aktuell laufende Python (venv auf Windows…)"* — die Werkzeuge
  erben den Interpreter des Agenten. Eine venv macht die Umgebung für Agent **und** Subprozesse
  in einem Schritt konsistent.

- [x] **0.1.1** venv angelegt (`.venv/`), stand bereits in `.gitignore` — 19.08.
- [x] **0.1.2** Requirements in der venv installiert, `pip check` sauber, 9 Kernmodule importierbar — 19.08.
- [x] **0.1.3** Monolith-Lauf in der venv geprueft — **DoD angepasst 19.08.**: statt `full_correction` nur `identify_error_llm` + `generate_correction_llm`. Begruendung: `apply`/`update` schreiben auf die Testinstanz und sind fuer den Nachweis 'die Umgebung traegt' nicht noetig. Beide LLM-Schritte liefen (BA-012)
- **DoD** *(angepasst 19.08., Begruendung bei 0.1.3)*: `sys.prefix != sys.base_prefix`; **beide
  LLM-Schritte** (`identify_error_llm`, `generate_correction_llm`) laufen in der venv durch.
  **Erst danach darf AP-A2 etwas installieren.**

### 0.2 — Rückfallpunkte sichern
- [x] **0.2.1** Git-Stand sauber — geprüft 19.08.: 0 geänderte Dateien, letzter Commit `3ed63bf`
- [x] **0.2.2** `pip freeze` System-Python archiviert → `data/archive/ba-ap0-20260819/`
- [x] **0.2.3** DB-Kopie gesichert, Gegenprobe 20 `memory_items` in Original und Kopie
- **DoD:** Beide Artefakte liegen ausserhalb des Arbeitsbereichs.

### 0.3 — Erreichbarkeit prüfen
- [x] **0.3.1** Testinstanz erreichbar — 19.08. nachmittags: DNS loest auf (10.112.19.8), `authenticate()` liefert Token (1390 Zeichen). *(Vormittags noch blockiert, siehe BA-011.)*
- [x] **0.3.2** Azure OpenAI antwortet — exakte Modellversion **`gpt-4.1-2025-04-14`** (gehört ins Protokoll, Kap. 17)
- [x] **0.3.3** Kontingent geprueft: gemessener Lauf kostete **14.590 Prompt-Token** (0,0313 $),
      nicht die aus PT4 uebernommenen ~55.000 — jene Zahl hing am damaligen Fall. Kein Engpass
- **DoD:** Beides bestätigt. Scheitert später ein Smoke-Test, ist es dann **nicht** die Anbindung.

### 0.4 — Referenzfall festlegen
- [x] **0.4.1** Referenzfall festgelegt: **I03**
      (Dichte, `articles[0].relDensityMin`, Ground Truth `1.017`) — bekannt, klein, und in
      `pt4-eval-results.json` mit `value_ok: false` dokumentiert, also mit Vergleichspunkt
- **DoD:** Fall-ID im Protokoll festgehalten; wird in AP-A3.1, AP-B1 und AP-F1 derselbe sein.

---

# AP-A — Umgebung final machen  ~1,5 Tage

**Abhängig von: AP-0.**

**Ziel:** Eine Umgebung, in der beide Varianten laufen werden, dokumentiert und unveränderlich.

### A1 — `MEMORY_MODE`-Schalter *(Masterplan Kap. 7.2)*
- [x] **A1.1** `MEMORY_MODE` in `app/core/agent_config.py`, Default `"on"` — 19.08.
- [x] **A1.2** Guard **an EINER Stelle statt an dreien**: `memory/retrieval.find_similar_cases()`.
      Alle drei Verbraucher degradieren von selbst neutral (`same_entity_confirmed_value([])`->None,
      `compute_memory_support(v,[])`->0.0, `format_cases_for_prompt([])`->Neutralsatz).
      Folgt dem `RULEBOOK_MODE`-Muster; `generate_correction_llm.py` blieb **unangetastet**
- [x] **A1.3** Gegenprobe gegen die echte DB (Fall I03, `articles:100005`): `on` -> 2 Faelle, Override **1.017**, support 1.0 · `off` -> 0 Faelle, kein Override, support 0.0 · ohne Variable -> `on`
- **DoD:** Ein Lauf mit `MEMORY_MODE=off` zeigt im stdout keinen Gedächtnis-Abruf; ein Lauf mit
  `on` verhält sich wie vorher. Default bleibt `on`, damit Produktion unberührt bleibt.

### A2 — Abhängigkeiten auflösen *(Kap. 4.9, 12.1)*

**Recherchestand 19.08.2026** (an PyPI geprüft, vor der Installation erneut verifizieren):
`langgraph` **1.2.10/1.2.11**, veröffentlicht 11.08.2026 — die beiden Quellen wichen um eine
Patchversion ab. Python **>=3.10**, unterstützt bis 3.13 → **3.13.3 passt**. Mitgezogene Pakete:
`langchain-core`, `langgraph-checkpoint`, `langgraph-prebuilt`, `langgraph-sdk`, `pydantic`,
`xxhash`.

- [x] **A2.1** Konflikt **war keiner**: die venv respektiert den Pin (`openai 1.109.1`); der System-Python war abgedriftet und nie Projektumgebung. Nichts geaendert. Urspruenglich: `requirements.txt` pinnt `openai>=1.6.0,<2.0.0`, installiert ist
      **2.14.0**. Pin anheben oder Paket downgraden — **Entscheidung begründen und festhalten**
- [x] **A2.2** PyPI abgefragt: `langgraph==1.2.11` (11.08.), `langchain-core==1.5.6` (17.08.). Installiert und in `requirements.txt` gepinnt
- [x] **A2.3** Kein Konflikt: `pydantic 2.13.4` und `openai 1.109.1` **vor und nach** der Installation identisch; `pip check` sauber
- [x] **A2.4** Entscheidung: **ohne Checkpointer** starten. für den Vergleich **nicht erforderlich** (der
      `trace` wird selbst geschrieben). Ohne starten; nur nachrüsten, falls beim Debuggen von
      AP-D7 Wiederabspielen gebraucht wird. Weniger Abhängigkeiten = weniger Konfliktfläche
- **DoD:** `pip check` ohne Fehler; `requirements.txt` spiegelt die tatsächliche Umgebung;
  Versionen im Protokoll.

> ### ⚠ Was aus dem LangChain-Ökosystem NICHT verwendet wird
> Die Installation zieht mehr mit, als gebraucht wird. **Drei Dinge sind ausdrücklich tabu**,
> weil sie die Kontrollbedingungen brechen würden:
>
> * **Keine LangChain-LLM-Wrapper** (`ChatOpenAI`, `AzureChatOpenAI` o. Ä.). Die Knoten nutzen
>   den **bestehenden Azure-Client** aus den Runtime-Skripten — nur so sind Modell, Temperatur
>   und API-Version zwischen beiden Varianten **strukturell** identisch statt nur dokumentiert
>   (Kap. 7.1, 12.4). Ein Wrapper würde den Aufruf verändern.
> * **Keine Prebuilt-Agenten** (`create_react_agent` aus `langgraph-prebuilt`). Sie würden die
>   bestehende Pipeline **ersetzen** statt sie zu orchestrieren — und damit den
>   Untersuchungsgegenstand austauschen.
> * **Keine Retry-Policies auf Knotenebene.** Die Schema-Wiederholung ist bestehende Logik
>   (`validate_with_retry(..., max_retries=5)`) und muss **unverändert** bleiben; sie durch einen
>   Framework-Mechanismus zu ersetzen wäre eine Verhaltensänderung im Messpfad.
>
> **LangGraph wird ausschliesslich als Orchestrator verwendet.**

### A3 — Smoke-Test und Einfrieren
- [x] **A3.1** Smoke-Test gefahren als `identify_error_llm` + `generate_correction_llm` (beide LLM-Schritte) auf Snapshot `194f58de…` (DEMAND_ARTICLE_IDS). **Bewusst ohne `apply`/`update`** — kein Schreibzugriff auf die Testinstanz noetig, um die Umgebung zu belegen
- [x] **A3.2** `pip-freeze-venv-vor-langgraph.txt` und `-nach-langgraph.txt` archiviert
- [x] **A3.3** **Entfaellt** — A2 ist nicht gescheitert. LangGraph 1.2.11 installiert, `pydantic`
      und `openai` unveraendert, `pip check` sauber. Der Rueckfall auf den Zustandsautomaten ist
      damit gegenstandslos (BA-012)
- **DoD:** Monolith läuft in der finalen Umgebung; Versionsliste archiviert; Protokolleintrag mit
  beiden `pip freeze`-Ständen.

---

# AP-B — Regressionsreferenz  ~0,5 Tage

**Abhängig von: AP-A vollständig.** *(Masterplan Kap. 8)*

> **⚠ Umbenannt und verkürzt am 19.08.2026.** Hiess vorher „Monolith-Baseline" und galt als „die
> Zahl, gegen die alles Weitere verglichen wird". **Das war falsch:** In AP-G wird danach das
> Regelwerk optimiert — eine vorher erhobene Zahl entstand unter anderen Bedingungen.
> **AP-B beantwortet nur: „läuft das System noch wie vorher?"** Die wissenschaftlichen Zahlen
> entstehen in **AP-H**, nach dem Einfrieren, für alle drei Bedingungen gemeinsam.
> Deshalb genügt hier eine **Teilmenge** statt aller 17 Fälle.

### B0 — `HUMAN_IN_THE_LOOP` festlegen *(vorgezogen aus H1)*
- [x] **B0.1** **Entschieden 19.08.: `HUMAN_IN_THE_LOOP=false` in A, B und C.** `apply_correction`
      laeuft mit (noetig fuer Kategorie 4), das Review-Gate ist nicht Vergleichsgegenstand.
      Praezedenzfall: `run_iterative.py` seit PT4
- [x] **B0.2** **Kein Eingriff noetig — empirisch geprueft**, nicht angenommen: derselbe Snapshot
      zweimal gefahren. `HUMAN_IN_THE_LOOP=true` -> **Exit 3** (Sperre greift), `=false` -> **Exit 0**,
      Lauf geht durch. Die Sperre haengt an `if not HUMAN_IN_THE_LOOP: return None`
- **DoD:** Entscheidung im Protokoll; ein Wiederholungslauf desselben Snapshots läuft durch.
- **Warum hier und nicht in AP-H:** Schon die Regressionsreferenz braucht dieselbe
      HitL-Behandlung wie die späteren Messläufe — sonst ist sie nicht vergleichbar.

### B1 — Regressionstest
- [x] **B1.1** I03 neu erzeugt (`d14634a2…`) und unter `monolith`+`MEMORY_MODE=off` gefahren — 19.08.
- [x] **B1.2** Gegen PT4 gestellt: **keine Abweichung** (Vorschlag 1.14 = 1.14, Feld identisch, Wert weiterhin nicht exakt). Modell-/Umgebungseffekt fuer diesen Fall ausgeschlossen
- **DoD:** Abweichungen benannt und ursächlich zugeordnet. Trennt Modell-/Umgebungseffekt vom
  späteren Architektureffekt.

### B2 — Der Baseline-Lauf
- [x] **B2.1** Bedingung **A** gefahren: `RULEBOOK_MODE=monolith`, `MEMORY_MODE=off`, `HUMAN_IN_THE_LOOP=false`
- [x] **B2.2** **5 Faelle** ueber 5 Fehlerklassen: I01, I02, I05, I07, I10 (+ I03 aus B1/AP-C)
- [x] **B2.3** Ergebnisdatei + Lauf-Metadaten im Protokoll (BA-016)
- **DoD:** Ergebnisdatei **mit** Lauf-Metadaten; Protokolleintrag mit Rohdatenpfad. Das ist die
  Referenz fuer „hat sich etwas veraendert?" — **nicht** die Vergleichsbasis fuer Kapitel 7.

### B3 — Artefakte archivieren *(Kap. 8.2)*
- [x] **B3.1** Regelwerk sha256 `a3c14bd1b66cc1e3…`, 36.165 Byte, Kopie + **alle 14 Regelkarten** gehasht und kopiert
- [x] **B3.2** **Echter Prompt aus einem Lauf** archiviert (222.931 Zeichen, sha256 `fc6cbcce…`) — aussagekraeftiger als der Code, der ihn baut
- [x] **B3.3** `MANIFEST.json` mit allen Schaltern, den **drei Messbedingungen A/B/C**,
      Modellversion `gpt-4.1-2025-04-14` und den Paketversionen
- **DoD:** Ein Dritter könnte den Lauf allein aus dem Archiv rekonstruieren.

---

# AP-C — Schalter und Gerüst  ~0,5 Tage

*(Masterplan Kap. 6, 10, 12.3)*

- [x] **C1** `SP_ARCHITECTURE_MODE` in `agent_config.py`, Default `"monolith"`, **strikt geparst** (Tippfehler bricht ab) — 19.08.
- [x] **C2** Verzweigung am Anfang von `execute_pipeline()` — greift nur bei `graph` UND Korrektur-Pipeline
- [x] **C3** `GRAPH_ENABLED_PIPELINES` in `agent_config.py` (neben dem Schalter, nicht im Agenten)
- [x] **C4** `graph/` + `graph/nodes/` + `graph_state.py` mit **19 Feldern** und `new_state()`
      *(waren 18; am 20.08. wurde `validation_result` in `initial_validation` und
      `final_validation` aufgeteilt — ein Feld trug zwei Bedeutungen und zwei Formen,
      siehe BA-027)*
- **DoD:** Monolith verhält sich **unverändert** (Regressionstest B1 erneut grün);
  `SP_ARCHITECTURE_MODE=graph` gibt eine saubere „noch nicht implementiert"-Meldung statt eines
  Absturzes.

---

# AP-D — Knoten extrahieren  ~4–5 Tage

**Muster überall gleich** *(Kap. 12.2)*: neue aufrufbare Funktion, `main()` ruft sie auf,
**CLI-Verhalten unverändert**. Reihenfolge nach Aufwand, nicht nach Knotennummer.

| | Teilpaket | Datei | Aufwand |
|---|---|---|---|
| ☑ | **D1** Knoten 6 Technische Prüfung | `validate_correction_schema_llm.py` | **fertig 19.08.** |
| ☑ | **D2** Knoten 5 Korrekturgenerierung | `generate_correction_llm.py` | **fertig 19.08.** |
| ☑ | **D3** Knoten 7 Anwendung & Re-Validierung | `apply_correction.py`, `update_snapshot.py`, `validate_snapshot.py` | **fertig 19.08.** |
| ☑ | **D4** Knoten 4 Regelzuordnung + Knoten 8 Ergebnisbewertung | Neucode in `graph/nodes/` | **fertig 19.08.** |
| ☑ | **D5** Knoten 9 Antwortformulierung | `generate_audit_report.py` | **fertig 19.08.** |
| ☑ | **D6** Knoten 2 Fehlerklassifikation | `identify_error_llm.py` | **fertig 19.08.** — Prompt per SHA-256 unveraendert |
| ☑ | **D7** Knoten 3 Kontextsuche | `identify_snapshot.py` | **fertig 19.08., nachgeprüft 20.08.** — MVP: `main()` parametrisiert statt zerlegt; 8 Szenarien roh + kanonisch identisch; dabei Runtime-Defekt *veralteter Kontext* gefunden und gemeinsam repariert (BA-024) |

**DoD je Teilpaket:** Die Funktion ist direkt importierbar **und** das Skript verhält sich über
CLI unverändert (Argumente, stdout, Exit-Codes, erzeugte Dateien).
Für **D7** zusätzlich: derselbe Suchlauf liefert dasselbe `last_search_results.json` wie vorher.
*(Stand vorher fälschlich bei D3 — dort gibt es keinen Suchlauf; korrigiert 19.08.2026.)*
Für **D3** zusätzlich: die Re-Validierung wird **ausgelöst und abgewartet**, und `errors_after`
ist bei nicht abgeschlossenem Job `None`, nie `0`.

> **D7 ist der Risikoposten des ganzen Blocks.** Wenn er sich als zu verwoben erweist: Knoten 3
> und 4 zusammenlegen (Kap. 9.1) — die Entscheidung gehört in AP-F, nicht hierher.

---

> ### ✓ Vor AP-E bereinigt — Audit vom 20.08.2026 (BA-025 / BA-026)
>
> Neun Auffälligkeiten aus der Vollprüfung AP-0 bis AP-D. **Stand 20.08. abends: erledigt**
> bis auf F4 und F8, die bewusst als Auftrag an AP-H (H4a) und AP-G (G5a) verschoben
> wurden. **F4 ist mit H4a am 21.08. erledigt** (BA-051/BA-052); F8/G5a steht noch aus.
>
> | | Befund | Wirkung | wann spätestens |
> |---|---|---|---|
> | **F1** ✓ | zwei venvs | **gelöst:** Wurzel-`.venv` ist verbindliche BA-Messumgebung; `app/.venv` bleibt (nichts hängt funktional daran). Jeder Lauf protokolliert `sys.executable` + `ba_env_ok` | erledigt |
> | **F2** ✓ | Ergebnisdatei ohne Metadaten | **gelöst:** `app/core/run_metadata.py` + `--with-metadata`; B2 unter definierter Umgebung neu erhoben | erledigt |
> | **F3** ✓ | doppelte Implementierungen | **gelöst:** beide `main()` delegieren; CLI vorher/nachher verglichen | erledigt |
> | **F4** ✓ | PT4-Runner erzwingen `cards` | **bewusst NICHT verändert.** Eigener BA-Runner `run_ba_abc_suite.py` — **erledigt 21.08.** (BA-051/052) | erledigt |
> | **F5** ✓ | falscher Default-Kommentar | **korrigiert** — `cards (DEFAULT)` | erledigt |
> | **F6** ✓ | Knoten 1 fehlte | **gebaut:** `app/tools/smart-planning/graph/nodes/input_analysis.py`, kein LLM. Jetzt wirklich neun Module | erledigt |
> | **F7** ✓ | stdout `✓` → `OK` | **zurückgesetzt** (Subprozesse bekommen `PYTHONUTF8=1`, kein Grund dagegen) | erledigt |
> | **F8** → | lose Pins | **Lock-Artefakt statt Umbau** der produktiven Datei — als **G5a** verankert | AP-G |
> | **F9** ✓ | `__pycache__` im Archiv | **entfernt** | erledigt |

# AP-E — Graph verdrahten  ~2 Tage

*(Masterplan Kap. 11, 12.3, 12.4)*

- [x] **E1** `correction_graph.py`: neun Knoten, sequenzielle Kanten 1→…→6 — **20.08.**, 9 Knoten / 12 Kanten im kompilierten Graphen
- [x] **E2** Bedingte Kante **A** nach Knoten 6 — **20.08.** `schema_valid is True → [7]`, sonst `[8]`. **Nicht** nach Retries gefragt (die sind in Knoten 6 erschoepft); `None` wird wie `False` behandelt. Kante 6→5 nachweislich nicht im Graphen
- [x] **E3** Bedingte Kante **B** nach Knoten 8 — **20.08.**, `route_after_evaluation()` liest **nur** `decision.action`,
      enthält **keine** Fachlogik; inkl. Rückkante 8→2
- [x] **E4** `_execute_pipeline_graph()` in `sp_agent.py` — **20.08.**, **identische Rückgabestruktur** wie
      `_execute_pipeline()` (`success`, `final_validation`, `total_iterations`, `completed_steps`)
- [x] **E5** Trace-Persistenz — **20.08.**: `data/snapshots/<id>/iteration-N/graph_state.json`, 13 KB, 20 Felder,
      9 Trace-Einträge. Regeltext, Suchkontext, Identify-Antwort und Meldungslisten sind
      **durch ihre Hashes ersetzt** (Kap. 12.5), die Rohdaten liegen als Artefakte daneben
- [x] **E6** — **20.08.**: `docs/abbildungen/graph-korrekturablauf.mmd` (885 Zeichen)
- **DoD:** Ein bekannter Fall läuft im `graph`-Modus End-to-End durch; Orchestrator und Eval-Skripte
  merken **nichts** von der Umstellung.

---

# AP-F — Vertikaler Durchstich  ~2 Tage

**Abhängig von: AP-E und AP-B.** *(Masterplan Kap. 20, 9.1, 7.3)*
Der ehrliche Entscheidungspunkt — hier wird bestätigt oder korrigiert, was bisher Hypothese war.

- [x] **F1** — **20.08., final mit A/B/C** (BA-033). Fall **I03**, je frischer Snapshot, je
      eigener Prozess, alle drei im selben Codestand. **B einzeln gefahren**, nicht aus
      Codegleichheit abgeleitet. Fachlicher Endzustand in allen drei identisch. A und C liefern
      **denselben** Vorschlag (`update_field articles[0].relDensityMin = 1.14`, Ground Truth
      `1.017` — beide daneben); Unterschied liegt in der Nachvollziehbarkeit (7 Schrittnamen
      gegen `graph_state.json` mit 9 Trace-Eintraegen, Karten und Regel-Hash). Dabei einen
      **Berichtsfehler in `_execute_pipeline_graph()`** gefunden und behoben (BA-029)
- [x] **F2** — **20.08.**: `app/tools/smart-planning/graph/trace_lesbar.py`. Je Knoten Dauer,
      Zeitstempel und die drei Handoff-Hashes; am Ende **sieben Fragen** als UF3-Raster
      statt einer Schrittzahl (am I03-Durchstich alle sieben belegt). Weist den Anteil von
      Knoten 9 gesondert aus — siehe den strukturellen Widerspruch in BA-030
- [x] **F3** — **20.08.: es bleiben NEUN.** Im Masterplan als Kap. 3.6.1 festgehalten. Der
      einzige strukturelle Widerspruch betraf Knoten 9 als LLM-Aufruf und ist behoben
- [x] **F4** — **20.08.: Kartenebene bleibt.** Keine Regelwerk- oder Promptänderung nur zur
      Erzeugung von Rule-IDs; die tatsächlich angewandte Einzelregel ist ohne weiteren
      Eingriff nicht beobachtbar. Als **Limitation** in Kap. 3.6.1 dokumentiert
- [x] **F5** — **20.08.**: beide Bedingungen des I03-Durchstichs durch das gemeinsame Format.
      Strukturell **5/5** sauber — und **trotzdem undicht**: die `snapshot_id` im Vorlageformat
      hätte jede Vorlage ihrer Bedingung zuordnen lassen. `als_text(..., pseudonym=...)`
      ergänzt, für die Expertenvorlage Pflicht (BA-031).
      **Final am 20.08. gegen A/B/C: 10/10** (BA-033), mit Provenienz-Matrix in Masterplan
      Kap. 16.3 — 13/13 Vorlagefelder in allen drei Bedingungen aus Artefakten belegbar.
      Zwischenstand 9/9 auf A/C (BA-032). Dabei ein
      **zweiter** Blindungsbruch gefunden: `schema_gueltig`/`schema_versuche` gibt es nur in C
      — die Vorlage zeigt jetzt nur die 13 von 17 Feldern, die in allen Armen belegbar sind
- **DoD:** Gegenüberstellung dokumentiert; beide Entscheidungen im Masterplan festgehalten;
  Raster einmal in der Praxis erprobt.

> **F5 ist Regel 6 in der Praxis.** In PT4 hat ein defekter Messterm (`value_grounded`) eine ganze
> Fehlerklasse verdorben. Eine Stunde hier spart später eine Woche.

---

# AP-G — Pilotphase und Einfrieren  ~3 Tage *(kürzbar)*

*(Masterplan Kap. 8.3)*

- [x] **G1** — **20.08.**: `app/eval/build_pilot_catalog.py` erzeugt **10 Pilotfälle**
      (`data/snapshots/ba-pilot-snapshots/`), je ein **anderer Artikel**, keiner aus dem
      Messkatalog, keiner doppelt. Abgedeckte Prozesspfade: Einzelfehler · Referenz-/ID-Fehler ·
      fachlicher Korrekturwert · mehrere Fehler · Folgefehler · **Kontextsuche ohne Treffer** ·
      **Fuzzy-Fallback** · Zusatzkarten · **Grenzfall** (min/max vertauscht → `stop_uncertain`
      ist die richtige Antwort) · **Rückkante 8→2** (P10, drei Fehler)
- [x] **G2** — **20.08.**: `app/eval/check_pilot_overlap.py`, Exit 0/1.
      **Keine gemeinsamen Entitäten, keine gemeinsamen Fall-Codes** (Mess 21 Bezeichner,
      Pilot 18). Zielpfad-*Arten* sind absichtlich gleich und werden getrennt ausgewiesen.
      Rohartefakt: `data/archive/ba-g2-ueberschneidung/ueberschneidungsnachweis.json`
- [x] **G3** — **ABGESCHLOSSEN 21.08. (BA-049/BA-050)**, siehe Abschlusszeile unten. Historisch: **First Pass am 20.08. vollständig gefahren und archiviert (BA-035),
      NICHT abgeschlossen.** Befunde: **P06/P07/P09 verfehlen ihren Pfad** (Testdaten, nicht
      System → Fälle ersetzen) · **Rückkante 8→2 erstmals real durchlaufen** (P04, P10, je 3
      Iterationen) · zwei Defekte in **Knoten 7** (Handoff-Guard blockiert ab Iteration 2;
      Modell liefert `demands[?]`-Zielpfade). Regelkarten wurden **nicht** angefasst

  > ⚠ **Zwei Aussagen oben sind überholt** — sie bleiben als Beleg des Erkenntniswegs stehen:
  > *„aber aus dem falschen Grund: sie lief, weil Knoten 7 nichts anwenden konnte"* wurde in
  > **BA-036** widerlegt (in den Durchgängen 1 und 2 war `applied_ok=True`; die Rückkante ist
  > **fachlich validiert**). Die Ursache des Guard-Anschlags klärte **BA-042**: die
  > Artefakt-Iteration fror auf `1` ein.

- [x] **G3a** — **21.08.**: Iterations-/Proposal-Handoff **repariert und validiert**.
      BA-043 (vier Defekte) · **BA-044** (drei Restlöcher: K5-Fallback, K7-Disk-Zugriff vor dem
      Guard, K8-Vorbedingung `bool(applied)`) · **BA-045** (Fix + acht Regressionen grün).
      Der K8-Entscheidungsvertrag ist umgekehrt: **nur positiv belegte Verarbeitung** führt zu
      `stop_valid`/`continue`/`stop_max_iter`; `revalidation_ok` ist neu in der Kette.
      Permanente Tests: `app/eval/test_graph_handoff_regressions.py` (R1–R6),
      `test_k8_replay_ba036.py`, `test_ab_cli_isolation.py`, `test_trace_registry.py`,
      `graph_regression_harness.py`.
      Belege: R1 10/10 · R2 22/22 · R3 12/12 · R4 5/5 · R5 7/7 · R6 15/15 · R7a 10/10 ·
      Replay 12/12 · Registry 11/11 · **je einzeln mit Negativkontrolle abgesichert**.
      Rohdaten R8/R7b: `data/archive/ba-g3-pilot/pilot-firstpass-C-20260820T163515Z.json`,
      `…A-20260820T163751Z.json`

  > **B2 wurde bewusst NICHT als Regression gefahren.** B2 besteht aus I01, I02, I05, I07, I10
  > und I03 — das sind **Messfälle**, und AP-G3 verbietet ihre Ausführung während der Pilotphase.
  > Ersatz: **R7a** (AST-Erreichbarkeitsnachweis: alle Änderungen liegen unter `graph/`,
  > `run_technical_check()` hat genau einen Aufrufer, CLI ruft `validate_with_retry` direkt)
  > und **R7b** (Bedingung **A** auf dem *Pilotfall* P02: 1 → 0 Fehler, keine Graph-Artefakte).
  > **Offene Entscheidung:** ob das genügt oder B2 nach dem Einfrieren nachgeholt wird.

- [x] **G3b.1 P01/P03 — Diagnose abgeschlossen (BA-046).** **Keine Halluzination und kein
      K5-Problem.** Der Wert `1.049` wird **deterministisch in Python** berechnet
      (`identify_snapshot.py:553-560`, `sorted(werte)[len//2]` über `similar_items`, n=90,
      Abteilung 20200) und liegt als `similar_items_stats.relDensityMin.median` im
      angereicherten Kontext; das Modell hat ihn nur zitiert. Ground Truth (1.063 / 1.1) ist
      **im Kollektiv enthalten** — ein Median kann einen Einzelwert nicht rekonstruieren.
      `get_array_context()` läuft in **A, B und C** gleich → **kein Architekturunterschied**.
      `negative-dichtewerte.md` stammt aus **Knoten 2** (`relevant_cards`, nichtdeterministisch),
      nicht aus Knoten 4; ohne messbaren Effekt auf den Wert.

  > ⚠ **Folge für das Messinstrument:** Für Dichtefehler zählt ein naives Halluzinationsmass
  > einen **deterministisch erzeugten** Wert als Modellfehler. Das ist die
  > `value_grounded`-Falle aus PT4 (harte Regel 6). **Kategorie 1 ist für diese Fehlerklasse
  > so nicht messbar** und muss vor G5 neu gefasst werden.

- [x] **G3b.2 — BEHOBEN am 21.08. (BA-047, verifiziert BA-048).** Der Befund lautete:
      *C macht je Durchgang einen LLM-Retry, den A und B nicht machen* *(BA-046)*. Derselbe Fall P04: **A 0 · B 0 · C 2** Retry-Artefakte bei je 2 Durchgängen.
      Ursache: `run_correction_generation()` liefert die **innere** `correction_proposal`
      (`generate_correction_llm.py:1134`), Knoten 6 reicht sie an `run_technical_check()`, und
      `validate_correction_proposal()` prüft gegen die **Hülle** `LLMCorrectionResponse`
      (`correction_models.py:66-72`) → vier Pflichtfelder fehlen → erzwungener LLM-Retry.
      **Durch BA-043 entstanden** (vorher lud der `or`-Zweig die Hülle von Platte; P01/P03
      zeigen `retries: 0`).

  > ✅ **Erledigt.** Der A/B/C-Nachlauf auf P04 mit frischen Snapshots ergab
  > **A 0 · B 0 · C 0** Retry-Artefakte; die SHA-Invariante
  > `correction.provenienz.response_sha256 == technical_check.input_digest.response_sha256_eingang`
  > hielt in beiden Durchgängen, und die Artefakte sind unbeschädigt (BA-048).
  > Der Befundtext bleibt als Diagnose stehen — er ist der Beleg des Erkenntniswegs.

  > **Bauregel B verletzt:** C erhält eine Reparaturschleife, die A und B nicht haben — Token-
  > und Laufzeitunterschiede wären dann kein Architektureffekt. Zugleich misst **Kategorie 2**
  > derzeit einen Hüllen-Mismatch der eigenen Verdrahtung statt struktureller Halluzination.
  >
  > **Vorschlag (nicht umgesetzt, wartet auf Entscheidung):** Normalisierung in der
  > **gemeinsamen Runtime** — `run_technical_check()` ergänzt eine innere `correction_proposal`
  > zur Hülle, bevor es prüft. Danach R3 um eine **Formprüfung** erweitern und `retries=0` als
  > Regression festschreiben. **Kein G5 vor dieser Entscheidung.**

- [x] **G3b.3 — geschlossen in BA-049/BA-050.** Zwischenstand (BA-048): P06/P07/P09 sind als ungeeignete Designs **archiviert**
      (Kennungen bleiben, damit der First Pass zitierbar ist). **G2 erneut gefahren:
      überschneidungsfrei, Exit 0**, 11 Pilotfälle.

  > ⚠ **Zwei der drei Pfade sind per Fehlerinjektion NICHT konstruierbar** — am echten Code
  > und an den echten Daten belegt, nicht argumentiert:
  > * **P06 „Kontextsuche ohne Treffer":** eine Injektion schreibt den Wert IN den Snapshot;
  >   die exakte Suche findet ihn danach zwangsläufig (1 Treffer vs. 0 für einen nie
  >   injizierten Wert). Null Treffer sind so nicht herstellbar.
  > * **P07 „Fuzzy-Fallback":** `search_by_id()` fuzzt nur bei null exakten Treffern — aus
  >   demselben Grund unerreichbar. Die **Fähigkeit existiert** und ist direkt nachgewiesen.
  > * Auch „Artikel ohne Vergleichskollektiv" scheidet aus: der Datensatz kennt genau **zwei**
  >   `(departmentId, workPlanId)`-Kollektive mit **91** und **331** Artikeln.
  >
  > Beide Pfade sind auf **Knotenebene** abgedeckt: `app/eval/test_kontextsuche_pfade.py`
  > (**10/10**). Das ist eine **Reichweitengrenze der Ground-Truth-Methode** (Brücke 1) und
  > gehört in die Limitationen (K8) — kein Systemmangel.

- [x] **P11** *(Ersatz für P09, Artikel 830285)* gebaut und real gefahren (`7f447c4e…`, C).
      Erzeugt anders als P09 **nachweislich** einen `validate_unique_ids`-Fehler ✔ —
      **trifft den Grenzfall-Pfad aber NICHT**: Entscheidung `stop_valid`, Vorschlag
      `D830285_003` = exakt die Ground Truth. Grund: die beiden Demands sind inhaltlich
      identisch, aber die **Lücke in der ID-Sequenz** macht eindeutig, welche ID fehlt.
      Ich hatte nur die Feldinhalte geprüft, nicht die Sequenz. P11 bleibt als sauberer
      **Positivfall für Kategorie 1** im Katalog, unter zutreffendem Pfadetikett.

- [x] **Grenzfall-Pfad — ENTSCHIEDEN am 21.08. (BA-049/BA-050): kein vierter Versuch.**
      Zwei Aussagen, die **nicht** gleichgesetzt werden:
      * **(a)** Der `stop_uncertain` / `manual_intervention_required`-**Pfad** ist **real
        belegt** (P10 D5, BA-045) und über R2 sowie den K8-Vertrag regressionsgesichert.
      * **(b)** Ein **gezielt konstruierter fachlich mehrdeutiger Ground-Truth-Grenzfall**
        liess sich in drei Entwürfen **nicht zuverlässig herstellen** (P09, Kollektiv-Idee, P11).

      Geht als **Limitation nach K5/K8**, nicht als offener Punkt.

- [x] **P05-Zusatzfall — ENTSCHIEDEN am 21.08. (BA-049): entfällt.**
      Statt neue LLM-Pilotfälle zu würfeln, bis zufällig ein Folgefehler eintritt, wurde die
      **Messkette** nachgewiesen: `app/eval/test_kategorie4_integration.py` **19/19**, inkl.
      des kritischen Falls `1 → 1` („A behoben, B neu"), den eine Messung über die blosse
      Fehlerzahl verfehlt hätte.

  > ⚠ **Präzisierung zur früheren Formulierung** *(BA-050)*: Die Pre-Fix-Beobachtung in
  > P04 `7a9a981d…` D2 (BA-036) ist **kein regulärer Kategorie-4-Nachweis** — ihre Artefakte
  > waren vom K5→K6-Handoffdefekt betroffen und gelten als **Debugging-Befund**
  > (`WARNUNG-BESCHAEDIGTE-ARTEFAKTE.md`). Gültig ist: das **Messinstrument** ist post-fix
  > validiert; ein realer Post-Fix-Positivfall **steht aus** und wird nicht erzwungen.

- [x] **G3b.2 FIX umgesetzt (BA-047).** Die vollstaendige `LLMCorrectionResponse`-Huelle
      wandert als `GraphState.correction_response` von Knoten 5 zu Knoten 6 — **keine
      Runtime-Aenderung noetig**, `run_correction_generation()` gibt sie unter `output_data`
      bereits zurueck (bitgleich mit `llm_correction_proposal.json`). Invariante
      `K5.response_sha256 == K6.response_sha256_eingang` per SHA-256 belegt (**R9a**).
      Nach einem Retry ist die finale Huelle autoritativ, ihr innerer Vorschlag geht an K7
      (**R9b**). Knoten 7 unveraendert, R1 unberuehrt.
      ⚠ **`retries=0` ist KEINE Systeminvariante** — Schema-Retries bleiben in echten
      Pilotlaeufen legitim; geprueft wird nur, dass keiner mehr aus dem Handoff entsteht.
      **Offen:** A/B/C-Bestaetigung am laufenden System (Testinstanz zeitweise nicht
      erreichbar) und `test_trace_registry` gegen einen frischen Trace.

- [x] **G3b.4 vorgezogen und erledigt (BA-047).** Die vier Kategorien liegen als pruefbare
      Klassifikatoren in `app/eval/kategorien.py`, validiert in
      `app/eval/test_kategorien_instrumente.py` gegen **reale** Pilot-Traces (P01, P03,
      `da0cae38…`, `7a9a981d…`) plus kontrollierte Faelle. Je Kategorie **drei** Ausgaenge —
      `ja` / `nein` / `nicht_bestimmbar` — und je Kategorie Definition, Ground Truth,
      autoritative Quelle, Positiv-, Negativ- und **Confounderfall**.
      Ergebnis: **K1 8/8 · K2 5/5 · K3 7/7 · K4 7/7**.
      Belegt sind insbesondere die vier geforderten Abgrenzungen: technische Handoff-/
      Schemafehler zaehlen **nicht** als Modellhalluzination · ein Ground-Truth-falscher, aber
      **evidenzgestuetzter** Wert zaehlt **nicht** · Folgefehler nur nach Apply **und**
      abgeschlossener Revalidierung · Regelhalluzination nur bei einer **nicht vorgelegten**
      Regel.

- [x] **G3b.4 — ERLEDIGT (BA-047, vorgezogen):** jede der **vier Kategorien** einmal gegen einen echten Trace geprüft,
      ob sie misst, was sie zu messen behauptet. Zwei von vier haben in Folge auf das
      Instrument statt auf das System gezeigt (BA-046) — das ist kein Zufall mehr.

  > **⚠ Ein schlechter Pilotlauf ist KEIN Grund für eine Regeländerung.** Zuerst am Trace
  > lokalisieren, **wo** die Ursache liegt — Klassifikation (K2), Kontext (K3), Regelzuordnung
  > (K4), Korrekturgenerierung (K5) oder technische Verarbeitung (K6/K7). Eine Regelkarte nur
  > ändern, wenn der Befund tatsächlich auf einen **Regeldefekt oder eine unklare Regel**
  > zurückgeht. Trifft ein Pilotfall den vorgesehenen Prozesspfad nicht, ist **der Fall zu
  > ersetzen, nicht das Regelwerk anzupassen**.
  >
  > Je Änderung vollständig: *Pilotfall → beobachteter Fehler → lokalisierender Trace →
  > konkrete Änderung → Hash vorher/nachher → Wiederholung desselben Falls → Regression auf
  > weiteren Pilotfällen.*
  >
  > **`MEMORY_MODE=off` auch in der Pilotphase**, sonst überdecken gespeicherte Lösungen die
  > beobachteten Effekte. **Keiner der 17 Messfälle wird während G1–G4 ausgeführt oder zur
  > Optimierung angesehen.**
- [x] ██ **G3 ABGESCHLOSSEN — 21.08. (BA-049)** ██ Abschlussmatrix im Protokoll.
      **7 von 10 Pilotzielen real belegt**, 3 nicht — und zwar begründet:
      * **Kontextsuche ohne Treffer** und **Fuzzy-Fallback**: **im E2E-Korrekturworkflow nicht
        erreichbar**. Knoten 2 *extrahiert* den Suchwert aus der Validatormeldung, und die
        beanstandet einen Wert, der im Snapshot steht — in allen drei Suchmodi. Die Fähigkeit
        ist implementiert und auf Knotenebene nachgewiesen
        (`test_kontextsuche_pfade.py` **15/15**). **Offen bleibt ausdruecklich**, dass andere
        oder kuenftige Aufrufer, eine geaenderte Validatormenge oder eine Fehlklassifikation
        diese Pfade sehr wohl erreichen koennen — "toter Code" waere zu pauschal.
        → Befund über das **Bestandssystem** (K3) und **Limitation** (K8), NICHT ein Mangel
        der Pilotfallkonstruktion.
      * **Grenzfall — zwei getrennte Aussagen:** (a) der `stop_uncertain` /
        `manual_intervention_required`-**Pfad** ist **real belegt** (P10 D5, BA-045) und
        regressionsgesichert. (b) Ein **gezielt konstruierter mehrdeutiger
        Ground-Truth-Grenzfall** liess sich in **drei** Entwürfen (P09, Kollektiv-Idee, P11)
        **nicht zuverlässig herstellen**. (a) und (b) werden nicht gleichgesetzt. Kein
        vierter Versuch.
      * **Kategorie 4**: kein Post-Fix-Positivfall (alle Traces geprüft: `errors_new=0`).
        Der **Pre-Fix-Lauf `7a9a981d…` D2 ist KEIN regulärer Nachweis** — seine Artefakte
        waren vom Handoffdefekt betroffen; er bleibt Debugging-Befund. Gültig ist: das
        **Messinstrument** ist post-fix validiert, ein realer Positivfall steht aus.
        Statt neue LLM-Fälle zu würfeln, ist die **Messkette** nachgewiesen —
        `test_kategorie4_integration.py` **19/19**, inkl. des kritischen Falls `1 → 1`
        („A behoben, B neu"), den eine Messung über die blosse Fehlerzahl verfehlt hätte.
      * **Kategorien fachlich festgelegt** *(KEIN formaler Freeze — der erfolgt in G5)*:
        fachlich korrekt/falsch · evidenzgestützt/
        ungestützt · `nicht_bestimmbar` · technische/Handoff-Fehler getrennt über die
        **Provenienz**. **Ground-Truth-falsch zählt nicht automatisch als Halluzination.**
        Änderungen nur noch nach **dokumentierter Revalidierung**; **Nachmessungspflicht gilt
        ab G5**, nicht schon ab hier.

- [x] ██ **G4 ABGESCHLOSSEN — 21.08. (BA-050)** ██
      **`docs/BA_G4_PILOTPHASE_ABSCHLUSS.md`** — konsolidierter Pilotphasen-Abschluss, keine
      Optimierungsrunde. **Keine neue Inkonsistenz gefunden.**
      * **0 Promptänderungen · 0 Regelkartenänderungen · kein Messfall benutzt** — jeweils
        am Dateisystem bzw. an den BA-Markern im Code belegt, **nicht** über Zeitstempel
        (drei Runtime-Dateien tragen irreführende `mtime` aus dem Pilotzeitraum).
      * **Drei Produktänderungen** (BA-043, BA-044, BA-047), je mit Ursache, auslösendem
        Trace, **A/B/C-Wirkung** und Regressionsnachweis. Alle drei erreichen **nur C**;
        BA-047 **beseitigt** sogar eine C-Sonderleistung.
      * **199 Einzelprüfungen** über sieben Testdateien, alle grün, jeder Fix zusätzlich mit
        **Negativkontrolle**.
      * Limitationen nach Wirkungsrichtung getrennt (K3/K5/K6/K7/K8).
- [x] ██ **G5a ABGESCHLOSSEN — 21.08. (BA-053)** ██ **Messstand festhalten — bewusst schlank**
      Artefakt: `data/archive/ba-umgebung-eingefroren-20260820/{lock.json, requirements-frozen.txt}`.
      Alle sechs Punkte belegt: Commit `3ed63bf1` auf `main` · Working Tree **38 Einträge,
      keiner unbekannt** (17 Messinstrument/Graph, 14 Produktpfad, 7 Dokumentation) ·
      **77 Pakete** · `ba_env_ok=True` · `gpt-4.1`/`2025-01-01-preview`/`T=0.3` ·
      SHA-256 der vier nicht versionierten Messartefakte + **14 Regelkarten** einzeln und gesamt.
      **Kein Datei-für-Datei-Manifest**, wie festgelegt.

  > **Kein Datei-für-Datei-Manifest.** Git identifiziert den Codestand bereits eindeutig; ein
  > zweites, handgepflegtes Verzeichnis derselben Information wäre Aufwand ohne Erkenntnis und
  > eine weitere Stelle, die veralten kann. Sechs Angaben genügen:
  >
  > 1. **Git-Commit** des Messstands
  > 2. **Working Tree sauber** zum Messbeginn — verbleibende Änderungen ausdrücklich benannt
  > 3. **`pip freeze`** der BA-`.venv`
  > 4. **`collect_run_metadata()`**-Ausgabe
  > 5. **Modell, Deployment, API-Version, Temperature** und die experimentrelevanten Schalter
  > 6. **SHA-256** von Messkatalog, Ground Truth, Regelkarten und Monolith-Regelwerk
  >
  > Punkt 6 ist die einzige Stelle, an der Einzeldateien gehasht werden — dort ist es nötig,
  > weil diese Artefakte **nicht** unter Versionskontrolle stehen (`data/` ist ignoriert) und
  > Git sie deshalb nicht abdeckt. Alles Übrige deckt der Commit ab.

- [x] ██ **G5 — VERBINDLICH EINGEFROREN am 21.08.2026, 13:24:41 +02:00** ██ *(BA-062)*

  > **Der Freeze von 13:13:41 (BA-061) ist überholt** — die laufende Sicherung der Messzeilen
  > berührt den Runner. **Unter ihm wurden keine H5-Messdaten erhoben**, also keine
  > Nachmessung. BA-061 bleibt unverändert. Geändert wurde **ausschliesslich der
  > Schreibzeitpunkt** des Rohdatensatzes: atomar nach jedem Lauf statt einmal am Ende.
  > Messplan, Reihenfolge, Seed, Schema, Kategorien, Pfadlogik und Ground Truth sind identisch
  > (Plan-SHA `4ed26d0c1baf247c5643e836…`).

- [x] ~~██ **G5 — VERBINDLICH EINGEFROREN am 21.08.2026, 13:13:41 +02:00** ██~~ *(überholt, siehe oben)*
      *(= 2026-08-21T11:13:41Z, freigegeben durch den Nutzer, dokumentiert in **BA-061**)*

  > **Ab hier keine messrelevanten Änderungen mehr** an Produktcode, Graph, Runner,
  > Evaluierungslogik, Pfadauflösung, Kategorien, Prompts, Regeln, Ground Truth, Messkatalog,
  > Modellparametern oder Umgebung. **Erlaubt** bleiben Dokumentation und reine
  > AP-I-Auswertungsschritte — solange sie die eingefrorene Bewertungssemantik **nicht
  > nachträglich verändern**. Eine Auswertung *anwenden* ist erlaubt, ihre *Definition* ändern
  > nicht; das wäre eine **Nachmessung** (harte Regel 5).

      **Stand:** messrelevanter Code `15f2a44` · HEAD `a1e018e` · Working Tree sauber ·
      Branch `ba-messstand-g5`. Die Differenz besteht **ausschliesslich** aus drei lesenden
      Prüfwerkzeugen und zwei Dokumenten — per `git diff` über alle messrelevanten Pfade belegt.

      **Messvorschrift:** 17 Fälle (10 isoliert + 7 kombiniert) · 29 Ground-Truth-Korrekturen ·
      A/B/C je **N=5** · **255 Läufe** · Seed `20260821` · 29-Feld-Schema · gemeinsame
      Kategorie-4-Auswertung · Pfadsemantik aus `pfadaufloesung.py` · `MEMORY_MODE=off` ·
      `gpt-4.1` / `2025-01-01-preview` / `T=0.3`. **n bleibt 17.**

      **Der vorherige G5 (12:39:27, BA-057) ist überholt** — der Trockenlauf fand vor der
      ersten Datenerhebung, dass nur 10 statt 17 Fälle geladen wurden. **Unter ihm wurden
      keine H5-Hauptmessdaten erhoben**, also keine Nachmessung. BA-057 bleibt unverändert.

- [x] ~~██ **G5 — EINGEFROREN am 21.08.2026, 12:39:27 +02:00** ██~~ *(überholt, siehe oben)*

  > **Kein Messwert betroffen, also KEINE Nachmessung.** Unter dem alten Freeze wurde **kein
  > einziger H5-Lauf** durchgeführt. Der Trockenlauf fand vor der ersten Datenerhebung, dass
  > `KATALOGE["mess"]` nur 10 statt 17 Fälle lud — **150 statt 255 Läufe**. Korrigiert in
  > BA-058: die 7 distinkten kombinierten Fälle `K04`–`K10` haben jetzt maschinenlesbare, per
  > Deep-Diff belegte Ground Truth. **BA-057 bleibt unverändert stehen.**

- [x] ~~██ **G5 — EINGEFROREN am 21.08.2026, 12:39:27 +02:00** ██~~ *(überholt, siehe oben)* *(= 2026-08-21T10:39:28Z,
      freigegeben durch den Nutzer, dokumentiert in **BA-057**)*

  > **Ab diesem Zeitpunkt ist jede Änderung an Regelwerk, Graphstruktur, Prompts, Parametern
  > oder Umgebung eine NACHMESSUNG** und als solche zu kennzeichnen (harte Regel 5). Das gilt
  > auch für Änderungen, die offensichtlich Verbesserungen wären.

      **Eingefroren:**
      * **Codestand** Commit `93ad674` (letzter Commit, der `app/` berührt); HEAD `beae011`,
        Working Tree sauber, Branch `ba-messstand-g5`
      * **Graphstruktur** 9 Knoten, 12 Kanten — am kompilierten Graphen nachgezählt
      * **Regelkarten** 14 Stück, Gesamt-SHA `4d380884…f658`
      * **Monolith-Regelwerk (A)** 36.165 Byte, SHA `a3c14bd1…b4b1` — identisch mit BA-016 B3.1
      * **Messkatalog** isoliert 14 Dateien `0b0a9aff…da76` · kombiniert 13 Dateien `5a237594…cedb`
      * **Modell** `gpt-4.1` · `2025-01-01-preview` · `temperature=0.3`
      * **Umgebung** Wurzel-`.venv`, 77 Pakete, `ba_env_ok=True`
      * **Prompts** unverändert — 0 Änderungen während der gesamten Pilotphase
      * Lock-Artefakt: `data/archive/ba-umgebung-eingefroren-20260821/`

      **Messvorschrift ab hier:** 17 Fälle × 3 Bedingungen × 5 Wiederholungen = **255 Läufe**,
      randomisiert mit Seed `20260821`, 29-Feld-Schema, `MEMORY_MODE=off`, eigener Prozess je
      Bedingung. **`n` bleibt 17** — die Wiederholungen sind Within-Case.

      **Nicht eingefroren:** Auswertungsschicht (AP-I), Expertenmaterialien (AP-X), Protokoll. — **ab diesem Zeitpunkt bis zum Abschluss der
      A/B/C-Hauptmessung keine messrelevanten Änderungen** an Code, Prompts, Regeln,
      Messinstrument, Testkatalog, Ground Truth, Modellkonfiguration oder Umgebung.
      **Dokumentationsänderungen bleiben erlaubt.**
      Hashes festhalten
- **DoD:** Einfrierzeitpunkt mit allen Hashes dokumentiert. **Ab hier ist jede Änderung eine
  Nachmessung.**

> **Kürzbar auf ~1 Tag**, indem G3 auf zwei bis drei Fälle reduziert wird. **Nicht kürzbar ist
> G5** — ohne dokumentiertes Einfrieren ist die anschliessende Messung wertlos.

---

# AP-H — Messen  ~4 Tage

**Abhängig von: AP-G eingefroren.** *(Masterplan Kap. 13, 17)*

- [x] **H1** **vorgezogen nach B0** (19.08.) — schon die Regressionsreferenz braucht dieselbe HitL-Behandlung. Urspruenglich: `open_proposal_blocking()` bricht mit Exit-Code 3 ab, solange
      ein Vorschlag offen ist — der Wiederholungs-Wrapper läuft sonst ab Durchgang 2 ins Leere.
      Lösung für **beide** Varianten identisch und dokumentiert
- [x] ██ **H2 ABGESCHLOSSEN — 21.08. (BA-055)** ██ Wiederholungen für UF2, **im Runner
      implementiert und vor G5 fixiert**.
      * **N = 5**, verbindlich festgelegt. Masterplan (Kap. 13.2, 15.3) und AP-H nannten
        durchgängig nur die Spanne „3–5×" bzw. „N Läufe" — **es gab keine verbindliche Zahl**;
        die Festlegung war eine offene methodische Entscheidung und wurde ausdrücklich
        getroffen, nicht abgeleitet.
      * **Alle drei Arme** werden wiederholt — **geändert am 21.08. (BA-056)**, vorher nur
        A und C. Grund: mit einem einmal laufenden B liesse sich für UF2 nur der Gesamteffekt
        **A → C** betrachten; **B → C** fehlte, und damit die Trennung von Kartenform und
        Orchestrierung. Umfang: **A 85 + B 85 + C 85 = 255 Läufe**.
      * ⚠ **Wiederholungen sind KEINE zusätzlichen Fälle.** Die Fallzahl bleibt **17**,
        ergänzt um **Within-Case-Stabilität** je Fall. Der Rohdatensatz macht das explizit:
        identische `fall`-ID, laufende `wiederholung`, plus ein Warnhinweis im Kopf.
      * Wiederholungsnummer in `lauf_metadaten` — **kein neues Schemafeld**, die 29 bleiben.
- [x] ██ **H3 GESCHLOSSEN — 21.08. (BA-055) — als Limitation, nicht durch neue Fälle** ██
      Der ursprüngliche Auftrag lautete: Grenzfälle ergänzen. **Er wird nicht ausgeführt**, und
      zwar begründet — G3 hat die Frage bereits beantwortet (BA-049/BA-050):

  > **Zwei Aussagen, die nicht gleichgesetzt werden:**
  > * **(a)** Der `stop_uncertain` / `manual_intervention_required`-**Pfad** ist **real belegt**
  >   (P10 D5, BA-045), regressionsgesichert über R2 und den K8-Entscheidungsvertrag.
  > * **(b)** Ein **gezielt konstruierter, fachlich mehrdeutiger Ground-Truth-Grenzfall** liess
  >   sich in **drei** Entwürfen **nicht zuverlässig herstellen** — P09 (min/max vertauscht
  >   erzeugt gar keinen Validierungsfehler), Kollektiv-Idee (es gibt nur zwei Kollektive mit
  >   91 und 331 Artikeln), P11 (die Lücke in der ID-Sequenz macht die fehlende ID eindeutig).
  >
  > **Kein vierter Versuch.** Drei Entwürfe haben denselben Fehler in drei Varianten
  > wiederholt: jeweils wurde *ein Teil* der Information geprüft, die dem Modell vorliegt.
  > Mehr Fleiss hilft dagegen nicht.
  >
  > **Der gehashte 17-Fälle-Katalog wird nicht verändert** — er ist in G5a fixiert
  > (14 + 13 Dateien einzeln gehasht). Neue Messfälle würden ihn brechen.

      **Geht als Limitation nach K5 und K8**, dokumentiert in
      `docs/BA_G4_PILOTPHASE_ABSCHLUSS.md` Abschnitt 3.2.
- [x] ██ **H4 ABGESCHLOSSEN — 21.08. (BA-055)** ██ Randomisierung **im finalen Runner**,
      vor G5 fixiert. `messplan()` mischt die Tripel **(Fall × Bedingung × Wiederholung)**.
      * **Seed `20260821`, vor der Hauptmessung dokumentiert.** Der Wert ist beliebig und darf
        es sein — entscheidend ist, dass er **vorher** feststeht. Einen Seed nach dem Sehen der
        Ergebnisse zu wählen wäre Nachjustieren einer Messvorschrift (harte Regel 5).
      * **Seed UND die tatsächlich erzeugte Reihenfolge** stehen im Rohdatensatz
        (`randomisierung.seed`, `randomisierung.reihenfolge`). Der Seed allein genügt nicht —
        er belegt Reproduzierbarkeit nur, solange der Planungscode unverändert bleibt.
      * **Randomisiert wird ausschliesslich die Reihenfolge.** Nicht die Zuordnung von
        Schaltern zu Bedingungen, nicht die Fälle, nichts an der A/B/C-Semantik. Jeder Lauf
        bleibt ein eigener Prozess mit frischem Snapshot, `MEMORY_MODE=off`.
      * **Wozu:** ohne Mischung liefe erst alles A, dann alles B, dann alles C — jede zeitliche
        Drift (Serverlast, Netzlatenz, Modellverhalten) fiele systematisch mit der Bedingung
        zusammen und wäre von einem Architektureffekt nicht zu trennen.
      * Geprüft in `app/eval/test_messplan.py` (**25/25**) mit **synthetischen und
        Pilot-IDs** — kein Messfall geladen. `--trockenlauf` erzeugt den Plan, ohne etwas
        auszuführen.
- [x] ██ **H4a ABGESCHLOSSEN — 21.08. (BA-051, BA-052)** ██ **Eigener BA-Runner für die
      volle Pipeline** *(verbindlich, aus Befund F4, BA-025)* — `app/eval/run_ba_abc_suite.py`
      * **Alle vier Schalter explizit**, je Bedingung ein **eigener Prozess**; der
        **effektiv geltende** Wert wird zurückgemeldet (`schalter_effektiv`).
      * **Volle Pipeline** inkl. Anwendung, Upload, Trigger und Re-Validierung — nur so ist
        Kategorie 4 überhaupt messbar.
      * **`require_ba_env()` bricht hart ab**, `collect_run_metadata()` je Lauf.
      * **Messschema final: 29 Felder** *(`errors_remaining` war die Lücke, BA-052)*, in allen
        Zeilen identisch.
      * **Kategorie 4 für A, B und C aus DERSELBEN Funktion** (`app/eval/kategorie4.py`),
        Basis sind die autoritativen Validierungsmeldungen vor/nach; der `GraphState` dient
        bei C **nur als Cross-Check** und überschreibt nichts.
      * **Keine falschen Nullen:** ohne abgeschlossene Re-Validierung bleiben alle vier
        Kategorie-4-Felder `nicht_bestimmbar`. Im Ausfall-Lauf empirisch belegt
        (`abc-pilot-20260820T213134Z.json`: `ergebnis="abgebrochen"`, `fehler_nachher=None`).
      * **Pilotvalidierung P01 über A/B/C grün** — `abc-pilot-20260820T215517Z.json`:
        je 29 Felder, `MEMORY_MODE=off`, 1 → 0 Fehler, Apply/Upload/Revalidation vollständig,
        Kategorie 4 in allen drei Armen identisch belegt, **C-Cross-Check `identisch=true`**.
      * **Kein `generate_audit_report()`**, keiner der 17 Messfälle berührt.

  > **Die PT4-Runner werden dafür NICHT umdefiniert.** `run_combined_suite.py:97` und
  > `run_iterative.py:33` erzwingen `RULEBOOK_MODE=cards` hart (`{**os.environ, "RULEBOOK_MODE":
  > "cards"}` — das Literal gewinnt gegen die Umgebung) und setzen `MEMORY_MODE` gar nicht,
  > sodass der Default `on` greift. Ein Messlauf für **Bedingung A** wäre damit unbemerkt ein
  > `cards`-Lauf **mit** Gedächtnis. Sie sind PT4-Nachweise und bleiben, wie sie sind
  > (harte Regel 1, Koexistenz statt Ersetzen).
  >
  > Der neue Runner muss:
  > * **alle** Schalter explizit setzen — `SP_ARCHITECTURE_MODE`, `RULEBOOK_MODE`,
  >   `MEMORY_MODE=off`, `HUMAN_IN_THE_LOOP=false` — und den **effektiv gueltigen** Wert
  >   zurückmelden, nicht den gesetzten (Lehre aus BA-021/BA-024: `importlib.reload()` schaltet
  >   nichts um, was aus `agent_config` importiert wurde — getrennte Prozesse je Bedingung),
  > * die **volle** Pipeline fahren: Klassifikation → Suche → Regeln → Korrektur → Schema →
  >   **Anwendung + Upload + Trigger + Re-Validierung** → Bewertung. Die isolierte Suite fährt
  >   nur `identify` + `generate` und kann Kategorie 4 (Folgefehler) gar nicht messen,
  > * je Lauf **vollständige Metadaten** schreiben — `app/core/run_metadata.py` → `collect_run_metadata()`
  >   liefert sie fertig (Zeitstempel, `sys.executable`, `sys.prefix`, Python- und
  >   Paketversionen, `ba_env_ok`, alle Schalter, Modell, Temperatur, Git-Commit),
  > * **bei `ba_env_ok == False` HART ABBRECHEN, nicht warnen.** `warn_if_wrong_env()` ist
  >   fuer Entwicklungs- und Pilotlaeufe gedacht — ein *finaler* Messlauf unter dem
  >   falschen Interpreter ist wertlos, weil `pydantic` an drei Stellen im gemessenen Pfad
  >   liegt und in Knoten 6 mitentscheidet, welcher Vorschlag als schemagültig gilt.
  >   Dafür gibt es `app/core/run_metadata.py` → `require_ba_env()`: wirft `RuntimeError`,
  >   **bevor** der erste Fall läuft. Ein halb gelaufener Messsatz unter gemischten
  >   Umgebungen wäre schlimmer als gar keiner.
- [ ] **H5** **Die eigentliche Messung.** **Katalog seit BA-058 vollständig:** 10 isolierte
      (`I01`–`I10`) + 7 distinkte kombinierte (`K04`–`K10`) = **n = 17**; `snapshot-error-01…03`
      ausgeschlossen (redundant zu I01–I03). **255 Läufe.** Alle 17 Fälle × **drei Bedingungen** (Masterplan Kap. 7.1):
      **A** Monolith-Pipeline + `RULEBOOK_MODE=monolith` · **B** Monolith-Pipeline + `cards`
      (Kontrollarm, realer Ist-Zustand) · **C** Graph + `cards`.
      **Wiederholungen (UF2) für alle drei Arme, je 5** — geändert 21.08. (BA-056), damit
      **B → C** die Orchestrierung von der Kartenform trennt. **255 Läufe**, n bleibt **17**.
      Grenzfälle: als Limitation geschlossen (H3, BA-055).
      **Alle drei nach demselben Einfrieren G5**, randomisierte Reihenfolge
- **DoD:** Rohdaten vollständig nach Kap. 17 — je Lauf Zeitstempel, Variante, Fall-ID, Modell,
  Parameter, alle Modus-Schalter, Prompt (oder Hash), Antwort, Trace, Rohdatenpfad.

---

# AP-I — Auswerten und schreiben  ~3 Tage

*(Masterplan Kap. 15, 18, 19)*

  > **Vorarbeit erledigt (BA-059):** Der Zielpfad-Vergleich steht **vor** der Messung fest —
  > `app/eval/pfadaufloesung.py` löst semantische und indexbasierte Notation auf denselben
  > kanonischen Pfad auf; Mehrdeutigkeit ergibt `nicht_bestimmbar`. Die Ground-Truth-Dateien
  > wurden **nicht** umgeschrieben.

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
- [~] **X2** **Variantenneutrales Präsentationsformat** — nur das fachliche Endergebnis, **nie**
      der Rohtrace (der verrät sofort die Variante).
      **Format gebaut und erprobt** (`app/core/ergebnis_format.py`; deterministisch, kein LLM,
      mit `als_text(neutral, pseudonym)`); in **F5** für beide Bedingungen durchgelaufen.
      **Offen:** `aus_pipeline_ergebnis()` und `als_text()` werden noch **nirgends aufgerufen** —
      die Expertenvorlage entsteht erst aus Messergebnissen (BA-057).
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
