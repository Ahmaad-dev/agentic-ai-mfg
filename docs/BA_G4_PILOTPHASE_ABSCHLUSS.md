# AP-G4 — Konsolidierter Abschluss der Pilotphase

**Status: `pilot`. Kein Messergebnis.** Erstellt 21.08.2026, Grundlage BA-035 bis BA-049.

> **Wozu dieses Dokument.** Regel 5 erlaubt Optimierung ausschliesslich in der Pilotphase und
> verlangt, dass **jede** Änderung protokolliert wird: was, warum, ausgelöst wodurch, mit
> welcher Wirkung. Erst wenn das lückenlos vorliegt, ist der Einfrierzeitpunkt (G5) belastbar.
>
> **G4 ist ausdrücklich keine weitere Optimierungsrunde.** Es wird nichts geändert, nichts
> nachgebessert, nichts nachgemessen — es wird zusammengetragen und geprüft, ob die
> Vergleichbarkeit über alle Änderungen hinweg erhalten geblieben ist.

---

## 0 — Die sieben Feststellungen, die G5 tragen

| # | Feststellung | Beleg |
|---|---|---|
| 1 | **0 Promptänderungen** während der Pilotphase | kein Runtime-Modul trägt einen BA-047/048/049-Marker; jüngster Marker in `validate_correction_schema_llm.py` ist **BA-043** |
| 2 | **0 Änderungen an Regelkarten** während der Pilotphase | `find app/skills -name "*.md" -newermt "2026-08-20"` → **leer** |
| 3 | **Keiner der 17 Messfälle** wurde ausgeführt oder zur Optimierung angesehen | alle Läufe über `run_pilot_suite.py` auf `ba-pilot-snapshots`; G2 belegt Entitätentrennung (Exit 0) |
| 4 | Vom Handoffdefekt betroffene Artefakte sind **nur Debugging-Material** | `data/archive/ba-g3-pilot/WARNUNG-BESCHAEDIGTE-ARTEFAKTE.md` |
| 5 | **P06/P07 sind im aktuellen regulären E2E-Workflow nicht erreichbar** | `test_kontextsuche_pfade.py` 15/15 |
| 6 | Ein **gezielt konstruierter mehrdeutiger Grenzfall** wurde **nicht** hergestellt | drei Entwürfe: P09, Kollektiv-Idee, P11 |
| 7 | **Kategorie-4-Messung post-fix per Integration validiert** | `test_kategorie4_integration.py` 19/19 |

Zu (1) und (2) die genaue Abgrenzung: **geändert wurde die Zustandsführung des Graphen und
eine Funktion der gemeinsamen Runtime — nicht das, was das Modell zu lesen bekommt.** Regeltext,
Systemprompts und Kartenauswahl sind unangetastet. Das ist der Unterschied zwischen „am
Kontrollfluss repariert" und „auf die Testmenge hin optimiert".

---

## 1 — Sämtliche Änderungen während G3

Reihenfolge chronologisch. **A/B/C-Wirkung** ist die entscheidende Spalte: eine Änderung, die
nur C erreicht, wäre nach Bauregel B ein Kandidat für einen Scheineffekt und muss begründet
werden.

### 1.1 BA-043 — Iterations-/Proposal-Handoff, vier Defekte in einem Zug

| | |
|---|---|
| **Ursache** | Die Artefakt-Iteration fror auf `1` ein: Knoten 6 las sie aus seiner **eigenen vorigen Ausgabe** (Zirkelbezug, `technical_check.py:31`). Ab Durchgang 2 arbeiteten K5, K6 und K7 auf **drei verschiedenen Ordnern**. |
| **Auslösender Trace** | P04 `7a9a981d…`, P10 `f48a8d8d…` — ab D2 `proposal_identisch=False`, in D3 `applied_ok=False` (BA-035, diagnostiziert BA-042) |
| **Geändert** | `graph_state.py` (+`artifact_iteration_number`), `nodes/{classification,correction,technical_check,apply_revalidate}.py`, **`runtime/validate_correction_schema_llm.py`** (`run_technical_check`: `or` → vier getrennte Fälle; `proposal_sha256_before/_after`) |
| **A/B/C-Wirkung** | **nur C.** `run_technical_check()` hat **genau einen** Aufrufer, und der liegt im Graphen — AST-belegt in `test_ab_cli_isolation.py`. Der CLI-Pfad ruft `validate_with_retry` **direkt**. |
| **Regression** | R3 (Vier-Kombinationen, echte Runtime) 12/12 · R4 (Hash ohne Retry) 5/5 · R5 (Retry) 7/7 · R6 (D1→1, D2→2, D3→3) 15/15 |

### 1.2 BA-044 — drei Restlöcher desselben Defekts

| | |
|---|---|
| **Ursache** | BA-043 setzte den Guard an **einer** Stelle und übersah drei mit derselben Annahme: K5 reichte die Nummer ungeprüft durch (Latest-Resolver + LLM-Aufruf auf falschem Ordner), K7 griff **vor** seinem Guard auf Platte zu, K8 hängte seinen gesamten Sicherheitsblock an `k7_gelaufen = bool(applied)`. |
| **Auslösender Trace** | Regression 2 (Missing-Artifact), 8/10 FAIL |
| **Geändert** | `nodes/{correction,apply_revalidate,evaluation}.py`, `graph/trace_keys.py` (required/conditional/unknown) |
| **A/B/C-Wirkung** | **nur C** — alle vier Dateien liegen unter `graph/`; einziger Importeur ausserhalb ist `sp_agent`, dort hinter `SP_ARCHITECTURE_MODE == "graph"`. Die Legacy-Defaults der Runtime (`iteration_number=None`) stehen unverändert. |
| **Fachliche Folge** | **Umkehr der Beweislast in Knoten 8**: nur vollständig positiv belegte Verarbeitung führt zu `stop_valid`/`continue`/`stop_max_iter`. `revalidation_ok` ist neu in der Kette. |
| **Regression** | R1 10/10 · R2 22/22 · **Replay P04/P10 gegen BA-036: 12/12 identisch** |

> **Der Replay ist hier der wichtigste Nachweis.** Er belegt, dass der umgekehrte
> Entscheidungsvertrag an keiner **bereits belegten** Entscheidung etwas ändert — sonst wäre
> BA-036 („die Rückkante ist fachlich validiert") wieder offen gewesen.

### 1.3 BA-047 — Hülle statt innerem Vorschlag an Knoten 6

| | |
|---|---|
| **Ursache** | `run_correction_generation()` gibt unter `"proposal"` den **inneren** Vorschlag zurück; die Hülle steht daneben in `output_data`. Knoten 6 prüfte den inneren gegen `LLMCorrectionResponse` → fünf Pflichtfelder fehlten → **erzwungener LLM-Retry je Durchgang**, den A und B nicht hatten. Der Retry überschrieb zudem `llm_correction_proposal.json` mit **vom Modell geratenen** Hüllenfeldern. |
| **Auslösender Trace** | `retries=1` in allen zehn technischen Prüfungen von R8; A/B/C-Vergleich P04: **A 0 · B 0 · C 4** |
| **Geändert** | `graph_state.py` (+`correction_response`), `nodes/{correction,technical_check}.py`, `graph/trace_keys.py`. **Keine Runtime-Änderung nötig** — die Hülle wird bereits zurückgegeben. |
| **A/B/C-Wirkung** | **nur C**, und die Änderung **beseitigt** eine C-eigene Zusatzleistung. Sie stellt Vergleichbarkeit **her**, statt sie zu gefährden. |
| **Invariante** | `correction.provenienz.response_sha256 == technical_check.input_digest.response_sha256_eingang` — am realen Trace `b51c5b1c…` in beiden Durchgängen erfüllt |
| **Regression** | R9a 13/13 · R9b 16/16 · A/B/C-Wiederholung **A 0 · B 0 · C 0** · Registry gegen den frischen Trace **PASS** |

### 1.4 Instrumentierung — kein Produktcode

| Artefakt | Zweck |
|---|---|
| `graph/trace_keys.py` | zentrale Registry der Trace-Schlüssel, `TraceLeser`, required/conditional/unknown — Ende von vier Auswertungen am falschen Schlüssel (BA-025, 033, 040, 042) |
| `app/eval/kategorien.py` | die vier Kategorien als **prüfbare Klassifikatoren** mit drei Ausgängen |
| `app/eval/graph_regression_harness.py` + 7 Testdateien | **199 Einzelprüfungen**, permanent, wiederholbar |
| `app/eval/report_retry_ursachen.py` | A/B/C-Vergleich der Retry-**Ursachen**, nicht nur der Anzahl |
| `WARNUNG-BESCHAEDIGTE-ARTEFAKTE.md` | Kennzeichnung der Debugging-Artefakte |

**Diese Schicht berührt den gemessenen Pfad nicht.** Sie liest Artefakte und ruft Knoten in
Testfixtures; kein Produktionsablauf importiert sie.

---

## 2 — Warum die Vergleichbarkeit erhalten bleibt

Vier Argumente, jedes einzeln belegt:

1. **Alle Graph-Änderungen liegen unter `graph/`** und sind für A, B und CLI mechanisch
   unerreichbar. AST-Nachweis (nicht Textsuche): einziger Importeur ausserhalb ist `sp_agent`,
   dort hinter dem Modusschalter. `test_ab_cli_isolation.py` 10/10.
2. **Die einzige berührte Runtime-Funktion hat genau einen Aufrufer**, und der liegt im
   Graphen. Der CLI-Pfad ruft `validate_with_retry` direkt; die drei Legacy-Defaults
   (`iteration_number=None`) stehen unverändert.
3. **Empirisch bestätigt, nicht nur statisch:** Bedingung A auf Pilotfall P02 (1 → 0 Fehler,
   `karten=None`, `decision=None`, keine Graph-Artefakte) und der A/B/C-Dreiervergleich auf
   P04 — alle drei konvergieren auf 0 Fehler, **jetzt mit gleichem Aufwand**.
4. **Die einzige gefundene C-Sonderleistung wurde entfernt, nicht hinzugefügt.** Der erzwungene
   Retry (BA-046) war ein Verstoss gegen Bauregel B; BA-047 hat ihn beseitigt.

> **B2 wurde bewusst nicht als Entwicklungsregression gefahren** — es besteht aus I01, I02,
> I05, I07, I10 und I03, also aus **Messfällen**. Ersatz: R7a (statisch) und R7b (Bedingung A
> auf dem *Pilotfall* P02).

---

## 3 — Verbleibende Limitationen

Nach Wirkungsrichtung getrennt, weil sie in der Arbeit an verschiedene Stellen gehören.

### 3.1 Zwei Suchpfade sind im aktuellen Ablauf nicht erreichbar → **K3 und K8**

Knoten 2 **extrahiert** den `search_value` aus der Validatormeldung
(`identify_error_llm.py:202-210`). Eine Validatormeldung beanstandet einen Wert, der **im
Snapshot steht** — sonst gäbe es den Fehler nicht. Das gilt für alle drei Suchmodi
(`value`, `empty_field`, `equipment_workitem`).

**Folge:** Nulltreffer und Fuzzy-Fallback sind **unter dem derzeitigen regulären
E2E-Korrekturworkflow, mit der aktuellen Validatormenge und Suchwertableitung, nicht
erreichbar**. Auf **Knotenebene sind sie implementiert und getestet** (15/15).

**Ausdrücklich offen:** andere oder künftige Aufrufer, eine geänderte Validatormenge, eine
andere Suchwertableitung — oder eine **Fehlklassifikation durch Knoten 2** (real beobachtet:
P10 D5) — können diese Pfade grundsätzlich erreichen. **„Toter Code" wäre zu pauschal.**

**Für den Vergleich:** der Pfad darf in keinem Arm als Leistungsmerkmal zählen und kann unter
den Messbedingungen zwischen A, B und C keinen Unterschied erzeugen.

### 3.2 Der mehrdeutige Grenzfall wurde nicht konstruiert → **K5 und K8**

**Zwei Aussagen, die nicht gleichgesetzt werden:**

* **(a)** Der `stop_uncertain` / `manual_intervention_required`-**Pfad** ist **real belegt**
  (P10 D5) und regressionsgesichert.
* **(b)** Ein **gezielt konstruierter, fachlich mehrdeutiger Ground-Truth-Grenzfall** liess
  sich **nicht zuverlässig herstellen**.

Drei Entwürfe, drei Ursachen — jedes Mal hatte ich *einen Teil* der Information geprüft, die
dem Modell vorliegt: die Validatorregeln (**P09**: min/max vertauscht wird nicht beanstandet),
die Kollektivgrössen (**Zwischenidee**: es gibt nur zwei Kollektive, 91 und 331 Artikel), die
ID-Sequenz (**P11**: die Lücke macht die fehlende ID eindeutig).

### 3.3 Kategorie 4 hat noch keinen realen Post-Fix-Positivfall → **K6 und K7**

Alle Post-Fix-Traces geprüft (`b51c5b1c…` 2 Durchgänge, `7f447c4e…` 1 Durchgang):
durchgehend `errors_new = 0`.

Der Pre-Fix-Lauf `7a9a981d…` D2 **wird nicht als regulärer Nachweis geführt** — seine
Artefakte waren vom Handoffdefekt betroffen; er bleibt **Debugging-Befund**.

**Gültiger Stand:** das **Messinstrument** ist post-fix validiert (19/19, inklusive des
kritischen Falls `1 → 1` „A behoben, B neu"). Ein realer Positivfall wird sich in AP-H ergeben
oder nicht — **erzwungen wird keiner**.

### 3.4 Die Kategorien sind fachlich festgelegt, aber noch nicht formal eingefroren

Verbindlich ab jetzt: fachlich korrekt/falsch · evidenzgestützt/ungestützt ·
`nicht_bestimmbar` als gleichrangiger Ausgang · technische und Handoff-Fehler getrennt über die
**Provenienz** (`k5_response_valide`), nicht über die Feldsignatur. **Ground-Truth-falsch zählt
nicht automatisch als Halluzination** (P01/P03: der Median 1.049 wurde deterministisch von
`identify_snapshot.py:553-560` berechnet und dem Modell vorgelegt).

Änderungen nur nach **dokumentierter Revalidierung**. **Der formale Gesamtfreeze erfolgt in
G5**; erst ab dort ist jede Änderung eine Nachmessung.

### 3.5 Weitere offene Punkte

* **`sorted[len//2]`** heisst im Code `median`, ist bei geradem n aber der **obere** Median
  (1.049 statt 1.0485). **Nicht geändert** — gemeinsame Runtime, eine Änderung verschöbe A, B
  und C gleichzeitig. Als Beschreibung des Bestandssystems nach K3.
* **Die Kartenauswahl von Knoten 2 ist nichtdeterministisch** — P01 erhielt
  `negative-dichtewerte.md`, P03 bei gleichem Tag nicht. Ohne messbaren Effekt auf den Wert in
  diesen beiden Fällen. Für UF3 relevant, nicht für den Fix.
* **Alle Pilotläufe sind Einzelläufe.** Aussagen über Streuung sind daraus nicht ableitbar;
  Wiederholungen gehören nach AP-H (Robustheit).

---

## 4 — Regressionsnachweise, Gesamtstand

| Datei | Gegenstand | Prüfungen |
|---|---|---|
| `test_graph_handoff_regressions.py` | R1–R6, R9a/b (inkl. 12 `ECHTHEIT`-Assertions) | **100** |
| `test_kategorien_instrumente.py` | die vier Kategorien, je Positiv-/Negativ-/Confounderfall | **32** |
| `test_kategorie4_integration.py` | Kategorie-4-Messkette am echten Knoten 7 | **19** |
| `test_kontextsuche_pfade.py` | Suchpfade auf Knotenebene + E2E-Erreichbarkeit | **15** |
| `test_k8_replay_ba036.py` | P04/P10 gegen den neuen K8-Vertrag | **12** |
| `test_trace_registry.py` | Registry-Selbstprüfung, PASS/FAIL/**PENDING** | **11** |
| `test_ab_cli_isolation.py` | A/B/CLI-Erreichbarkeit, AST | **10** |
| | **Gesamt** | **199** |

Alle in der Wurzel-`.venv`, `require_ba_env()` bricht sonst hart ab.

**Jeder Fix wurde mit einer Negativkontrolle abgesichert** — der jeweilige Defekt wurde
zurückgebaut und geprüft, dass die Regression anschlägt. Ohne diesen Schritt wären die grünen
Tests wertlos.

---

## 5 — Ergebnis von G4

**Keine neue Inkonsistenz gefunden.** Alle während G3 vorgenommenen Änderungen sind
zugeordnet, begründet, in ihrer A/B/C-Wirkung bestimmt und regressionsgesichert. Die
Kontrollbedingungen sind unverletzt: kein Prompt, keine Regelkarte, kein Messfall.

**Bereit für G5a (Lock-Artefakt) und G5 (Einfrieren).**
