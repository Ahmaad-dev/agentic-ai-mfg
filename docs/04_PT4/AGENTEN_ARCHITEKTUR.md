# Agenten-Architektur, Human-in-the-Loop und Gedächtnis

**Stand: 15.08.2026.** Dieses Dokument beschreibt, wie die Agenten zusammenarbeiten, was
zwischen dem 13. und 15.08.2026 geändert wurde und **warum** — und beantwortet die drei
Fragen, die sich beim Umschalten zwischen betreutem und automatischem Betrieb stellen.

Chronologische Einzelheiten stehen in `PROJECT_LOG.md`. Dieses Dokument ist die
Zusammenfassung des **aktuellen Stands**.

---

## 1. Der Aufbau in einem Satz

Ein **Orchestrator** nimmt jede Anfrage entgegen, wählt einen Fachagenten
(**SP**, **Chat**, **RAG**, **E-Mail**) und liefert die Antwort zurück. Der Nutzer redet
ausschliesslich mit dem Orchestrator. Dieses Muster heisst *Supervisor* bzw.
*Agents-as-Tools* und ist für diesen Zuschnitt die richtige Wahl — es wurde am 15.08.2026
bewertet und bestätigt, nicht ersetzt.

### Wer formuliert die Antwort?

Das ist die eine Stelle, an der sich am 15.08. etwas Grundsätzliches geändert hat.

| Pfad | Wer antwortet | Warum |
|---|---|---|
| **Chat** | der Chat-Agent selbst | Er hat **mehr** Kontext als der Orchestrator |
| **RAG** | der RAG-Agent selbst | dito; Belege sollen bei ihrer Aussage bleiben |
| **E-Mail** | der E-Mail-Agent selbst | Entwürfe sind Freigabe-Artefakte, kein Wort darf sich still ändern |
| **SP** | der **Orchestrator** | Der SP-Agent wählt nur das Werkzeug; die Antwort entsteht erst aus dem Werkzeugergebnis |

**Begründung — gemessen, nicht geschätzt.** Bis zum 15.08. formulierte der Orchestrator
*jede* Antwort noch einmal um. Der Gedanke dahinter war, dass er ergänzen könne, was der
Fachagent nicht wusste. Tatsächlich war es umgekehrt:

| | Chat-Agent | Nachformulierung |
|---|---|---|
| Gesprächsverlauf | 10 Nachrichten × 1000 Zeichen | 3 Nachrichten × 200 Zeichen |
| Snapshot-Zustand | ja (frisch gelesen) | nein |
| Review-Entscheidungen | ja | nein |
| Offene Vorschläge | ja | nein |

Die Schicht sah **ein Sechzehntel** des Verlaufs und **keine** der drei Wissensquellen. Sie
konnte nichts hinzufügen — nur weglassen oder dazuerfinden. Genau dort entstanden am
14.08.2026 zwei Falschaussagen (siehe Abschnitt 3).

Für den SP-Pfad gilt das ausdrücklich **nicht**: dort gibt es keine fertige Antwort, die
erhalten bleiben müsste, sondern ein strukturiertes Werkzeugergebnis, aus dem erst Text
entstehen muss. Die Schicht bleibt dort.

**Voraussetzung, die vorher erfüllt werden musste:** Chat- und RAG-Prompt sagten wörtlich
„Deine Antworten werden vom Orchestrator aufbereitet" und enthielten weder die Wahrheits-
noch die Pfad-Regel. Diese Regeln wurden **zuerst** umgezogen, dann wurde die Schicht
abgeschaltet — andernfalls wäre die Optimierung ein Rückschritt gewesen.

### Kosten pro Anfrage

Vorher drei LLM-Aufrufe, jetzt zwei:

| | vorher | jetzt |
|---|---|---|
| Chat-Antwort | Planung + Chat + Nachformulierung | Planung + Chat |
| SP-Werkzeug | Planung + Intent-Analyse + Auswertung | Planung + Auswertung* |

\* Der Planer benennt sein Ziel bereits in `action` („download_snapshot",
„full_correction Pipeline"). `_intent_from_plan()` liest es dort ab, statt es ein zweites
Mal per LLM herzuleiten. Verglichen wird gegen die bekannten Namen aus `SP_TOOLS` und
`SP_PIPELINES`; **nur bei genau einem Treffer** gilt das Ziel als eindeutig, sonst läuft die
bisherige Analyse. Eine gesparte Sekunde ist keine falsche Pipeline wert.

---

## 2. Was jeder Agent weiss

Alle Agenten lesen **dieselbe** Unterhaltung (eine Historie je Sitzung, in der Datenbank,
nach einem Neustart wieder geladen). Isolierte Antworten gibt es nicht.

### Herkunft jeder früheren Aussage

Seit 15.08. trägt jeder Beitrag im Verlauf ein Etikett:

```
user      | welche fehler?
assistant | [Werkzeug-Ergebnis] 3 Fehler, 5 Warnungen
assistant | [Gespräch] alles bestens
assistant | ohne herkunft          ← unbekannt: bewusst KEIN Etikett
```

**Warum:** `add_message(..., agent_name=...)` schrieb die Herkunft seit jeher in die
Datenbank — `get_history()` baute den Verlauf aber nur aus `role` und `content` wieder auf.
Die Herkunft wurde geschrieben und nie gelesen. Für einen Agenten sah ein gemessenes
Werkzeugergebnis damit genauso aus wie ein dahingesagter Satz, und eine falsche Entwarnung
konnte sich über Runden fortpflanzen.

Umgesetzt in `short_term.as_llm_messages()` — genau dort, wo der Verlauf in einen LLM-Aufruf
übergeht, weil dort ohnehin das Feld `agent_name` entfernt werden muss (die
Chat-Completions-Schnittstelle weist unbekannte Felder zurück). Dazu die Regel in allen
Prompts: **ein `[Gespräch]`-Satz belegt nichts**, auch wenn der Agent ihn selbst geschrieben
hat; bei Widerspruch gilt das aktuelle Ergebnis.

### Zusätzliches Wissen je Anfrage

| Was | Woher | Wer bekommt es |
|---|---|---|
| Snapshot-Zustand | **frisch** von der Ablage, bei jeder Frage | Chat |
| Review-Entscheidungen inkl. Nachvalidierung | Datenbank | Chat **und** SP-Auswertung |
| Offene Vorschläge | Datenbank, auf den Sitzungs-Snapshot begrenzt | Chat **und** SP-Auswertung |

Der **Sitzungs-Snapshot** („Fokus") ist neu. Vorher hielt der Orchestrator ein einziges
Attribut `last_snapshot_metadata` für den gesamten Prozess — und weil er ein Modul-Global
ist, teilten sich **alle** Sitzungen diesen Wert: wer einen Snapshot lud, schob ihn jeder
anderen laufenden Unterhaltung in den Systemprompt, in der Cloud auch anderen Nutzern.
Jetzt hängt der Bezug an der Sitzung, und gespeichert wird **nur die ID** — eine ID veraltet
nicht, der Zustand dazu wird jedes Mal neu gelesen. `short_term.clear()` nimmt den Fokus mit.

Gefunden wird der Snapshot in dieser Reihenfolge: aktuelle Nachricht → Verlauf →
Sitzungs-Fokus. Der letzte Schritt fängt den Fall ab, dass die UUID aus dem gekürzten
Verlauf herausgefallen ist.

---

## 3. Wahrheitspflicht

Am 14.08.2026 behauptete der Agent dreimal etwas Falsches: „Alle kritischen Fehler wurden
behoben" (es war ein Vorschlag für **einen von drei**), „Der Snapshot ist jetzt valide und
vom Server akzeptiert" (es wurde **nichts** geschrieben) und nach einer Freigabe
„vollständig fehlerfrei und einsatzbereit" (die Freigabe selbst meldete `3 → 2 Fehler`).

**Ursache war kein Prompt-Problem, sondern ein Datenproblem** — das formulierende Modell
bekam die entscheidenden Tatsachen gar nicht:

* Für `analyze_only` stand im Kontext nur „Status: success" und die Schrittnamen.
  `final_validation` wird ausschliesslich für `full_correction`/`correction_from_validation`
  berechnet — und genau die werden unter HitL auf `analyze_only` umgebogen. Es gab also
  strukturell nie eine Zahl.
* `get_decisions_for_snapshot()` verschluckte die Spalte `revalidation_result`. Die Zeile in
  der Datenbank enthielt wörtlich `errors_before=3, errors_after=2` samt den offenen
  Meldungen.

**Behoben an der Wurzel:**

1. `SPAgent._describe_analysis_scope()` meldet, was ein Lauf wirklich abgedeckt hat:
   gefundene Fehler, der eine behandelte, die namentlich unberührten,
   `snapshot_written=False`, `uploaded_to_server=False`.
2. `get_decisions_for_snapshot()` liefert `revalidation` (vorher/nachher/offene Fehler).
3. `BASE_INTERPRETATION_RULES` und die Chat-/RAG-Prompts tragen eine oberste Regel:
   „alle Fehler behoben", „valide", „einsatzbereit" sind **nur** erlaubt, wenn eine
   Validierung mit ERROR-Anzahl 0 vorliegt; ein Vorschlag ist keine Änderung; deckt ein Lauf
   nur einen von mehreren Fehlern ab, ist das **ungefragt** zu sagen.
4. **Zahlen kommen aus dem Code, nicht aus dem Modell.** `_facts_block()` rendert die harten
   Zahlen deterministisch und hängt sie an die Antwort:

   ```
   ---
   **Gemessen:**
   - Gefundene Fehler: **2** — Vorschlag erzeugt für **1** davon, **1** unberührt
   - Am Snapshot wurde **nichts** geändert und nichts hochgeladen
   ```

   Er ersetzt die Prosa nicht, er verankert sie. Fehlen belastbare Zahlen, entfällt er
   ersatzlos — lieber keine Angabe als eine erfundene.

### Wahrheitspflicht ist nicht Formzwang (Ergänzung vom Abend des 15.08.2026)

Auf den Einwand, das System wirke erzwungen statt authentisch, wurden die Prompts getrennt
nach Art der Regel überarbeitet:

* **Formregeln entfernt.** Eine Frageliste am Ende des Auswertungs-Prompts („Was ist das
  Ergebnis? / Bei Erfolg: … / Bei Fehler: …") war als Erinnerung gemeint und wirkte als
  Vorlage — das Modell beantwortete jede Frage als eigenen Abschnitt. Dazu ein Widerspruch:
  der Chat-Prompt verlangte „DETAILLIERTE, ausführliche Antworten", der Auswertungs-Prompt
  „2-3 Sätze". Unerfüllbar; das Modell löste es jedes Mal gleich auf.
* **Neu: Abschnitt „Deine Stimme"** in allen drei Prompts. Keine Pflichtgliederung, keine
  Längenvorgabe, Register des Nutzers übernehmen, aufeinanderfolgende Antworten dürfen
  verschieden aussehen, keine rituellen Schlussfloskeln.
* **Wahrheitsregeln blieben**, verdichtet zum Abschnitt „Was du nicht behaupten darfst". Sie
  schreiben nicht vor, WIE geantwortet wird, sondern nur, was ohne Beleg nicht behauptet
  werden darf.

Gemessen an vier identischen Anfragen vorher/nachher: 24–45 % kürzer, rituelle
Schlussfloskeln von 3 auf 0. Die *Vielfalt* selbst ist damit nicht belegt — dafür sind vier
Anfragen zu wenig.

### Links gehören in die Daten, nicht in eine Bauanleitung

Vier Stellen erzeugten Review-Links als reine Pfade (`/review.html?proposal=…`). Im Chat kam
nie ein vollständiger Link an; auf die Bitte darum wiederholte das Modell denselben Pfad —
es **konnte** nicht mehr liefern, weil es den Host nicht kennt.
`APP_BASE_URL` in `core/agent_config.py` ist jetzt die einzige Quelle (mit Normalisierung
gegen ein doppeltes Schema), und jeder offene Vorschlag trägt ein Feld `review_url` mit dem
fertigen Link. Das Modell kopiert ihn, statt ihn zu bauen.

---

## 4. Ein Fehler pro Lauf — und was das je nach Betriebsart heisst

`identify_error_llm` bekommt **alle** Fehler, priorisiert sie und wählt **einen** aus.
`generate_correction_llm` baut genau dafür einen Vorschlag. Ein Vorschlag darf dabei
**mehrere Felder** ändern (`additional_updates`) — „ein Fehler" ist nicht „ein Feld".

### Automatischer Betrieb (`HUMAN_IN_THE_LOOP=false`)

`full_correction` durchläuft: `validate → identify → generate → schema-check → apply →
upload → re-validate`. Danach greift die Schleife in `execute_pipeline`:

```
Iteration 1 → 1 Fehler behoben → neu validieren → noch Fehler? → Iteration 2 → …
```

Abbruch bei **0 verbleibenden Fehlern** oder nach **5 Iterationen**
(`MAX_CORRECTION_ITERATIONS`). Das ist das bestätigte Verhalten: **ein Fehler pro Iteration,
Iteration für Iteration, bis alles behoben ist.**

### Betreuter Betrieb (`HUMAN_IN_THE_LOOP=true`, Voreinstellung)

`full_correction` und `correction_from_validation` werden auf `analyze_only` umgebogen.
`analyze_only` steht **nicht** in der Liste der Korrektur-Pipelines, also läuft die Schleife
nicht — und zwar zwangsläufig: sie bräuchte einen neuen Datenstand, um den nächsten Fehler
zu finden, und den gibt es erst nach dem Anwenden. Ohne Freigabe wird nichts angewendet.

**Ein Lauf = ein Vorschlag = eine Entscheidung.** Nach der Freigabe muss der nächste Lauf
angestossen werden.

### Die Sperre gegen doppelte offene Vorschläge

> **Bestätigt: Die Sperre greift AUSSCHLIESSLICH bei `HUMAN_IN_THE_LOOP=true`.**
> Ist der Schalter aus, verhält sich alles unverändert wie bisher — die automatische
> Pipeline läuft Iteration für Iteration durch, ohne jede Sperre.

Geprüft an zwei Stellen, beide mit `if not HUMAN_IN_THE_LOOP: return None` bzw.
`and HUMAN_IN_THE_LOOP`:

* `generate_correction_llm.open_proposal_blocking()` — greift auch beim direkten
  Werkzeugaufruf
* `SPAgent.execute_pipeline()` — dieselbe Frage **vor** dem ersten Schritt, damit nicht
  erst nach `identify_error_llm` (einem LLM-Aufruf) abgebrochen wird. Gemessen: 0,04 s
  statt ~6 s.

**Warum die Sperre nötig ist.** Ein Vorschlag ist eine Frage an den Menschen; eine zweite zu
stellen, bevor die erste beantwortet ist, ergibt nur Sinn, wenn beide unabhängig wären — sie
sind es nicht. Dazu kommt: `apply_correction.py` nimmt keine Vorschlags-ID entgegen, sondern
greift **immer die höchste Iteration**. Ein älterer Vorschlag ist deshalb ohnehin nicht
anwendbar; der Wächter `check_iteration_is_latest` sperrt ihn — bis 15.08. allerdings erst
beim Anwenden, also nachdem der Prüfer ihn bereits gelesen und beurteilt hatte.

**Warum sie ohne HitL schaden würde.** Der Status wird nur im Review-Pfad auf `applied`
gesetzt (`routes/review.py`). Im automatischen Betrieb bleibt er dauerhaft
`pending_review` — eine bedingungslose Sperre hätte die Automatik nach dem ersten Durchgang
stillgelegt.

**Verhalten bei aktiver Sperre:** Exit-Code 3 („wartet auf Entscheidung", kein Fehler). Die
Pipeline wiederholt nicht (ein zweiter Versuch ändert nichts, nur ein Mensch tut das) und
meldet keinen Fehlschlag; der Orchestrator antwortet ohne LLM-Aufruf mit Verweis auf den
offenen Vorschlag.

### Überholte Vorschläge sind sichtbar

Liste und Detailansicht liefern `applicable` und `not_applicable_reason`. In der Oberfläche:
Abzeichen **„überholt"**, gedimmte Karte, in der Detailansicht ein Warnkasten — und
**„Genehmigen"/„Wert ändern" sind entfernt**. „Ablehnen" bleibt: ein überholter Vorschlag
muss vom Tisch können.

---

## 5. Profitiert der automatische Betrieb vom gesammelten Feedback?

**Ja — vollständig. Das Gedächtnis ist vom HitL-Schalter unabhängig.**

Das ist die wichtigste Antwort in diesem Dokument, deshalb im Detail belegt.

### Geschrieben wird nur durch Menschen

`memory_items` wächst ausschliesslich über `long_term.record_case_safe(proposal_id)`, und das
wird **nur** aus `routes/review.py` aufgerufen — also nach einer menschlichen Entscheidung
(genehmigt, geändert **oder** abgelehnt). Kein anderer Pfad schreibt hinein. Jeder Eintrag
hält fest: Fehlerart, Objektmuster, Objekt-ID, **vorgeschlagener** Wert, **angewendeter**
Wert, Entscheidung, Kommentar und ob die Nachvalidierung besser wurde.

Aktueller Bestand: **12 Einträge** (6× genehmigt, 5× geändert, 1× verworfen).

### Gelesen wird immer

Im Generator ist `HUMAN_IN_THE_LOOP` **nur** an der neuen Sperre beteiligt. Der
Gedächtnis-Abruf steht davor und ist an keine Bedingung geknüpft:

* `find_similar_cases()` holt frühere Fälle zur selben Fehlerart, gleiche Objekte zuerst
* `format_cases_for_prompt()` legt sie dem Modell als **Belege** in den Prompt
* `same_entity_confirmed_value()` **überschreibt** den Modellwert, wenn ein Mensch für
  *dasselbe Objekt* schon einen anderen Wert bestätigt hat
* `compute_memory_support()` fliesst mit Gewicht 0.2 in die Konfidenz ein und hebt sie auf
  mindestens 0.9, wenn ein Mensch genau diesen Wert bestätigt hat

### Was das praktisch heisst

> Schaltest du HitL ab, **wiederholt das System deine korrigierten Fehler nicht.** Es
> schlägt beim ersten Lauf den Wert vor, den du vorher angewendet hast — für dasselbe
> Objekt sogar zwingend, weil der Gedächtnis-Override den Modellwert ersetzt.

Zwei Einschränkungen, die dazugehören:

1. **Gedächtnis ist objektbezogen.** Ein bestätigter Wert greift zwingend nur beim
   *gleichen Objekt*. Für ein anderes Objekt derselben Fehlerart ist der frühere Fall ein
   **Methoden-Hinweis**, kein Wert-Präzedenzfall — er stützt die Konfidenz (0.5), erzwingt
   aber nichts. Das ist Absicht: derselbe Wert wäre für ein anderes Objekt oft schlicht
   falsch.
2. **Das Modell darf begründet abweichen.** Trägt es `memory_dissent_reason` ein, bleibt sein
   Wert stehen — die Konfidenz sinkt dann aber von selbst (`memory_support` fällt auf 0.5,
   die 0.9-Untergrenze greift nicht), und der Vorschlag ist als Abweichung gekennzeichnet.

**Empfehlung für dein Vorgehen:** Feedback im betreuten Betrieb sammeln ist genau richtig
und geht nicht verloren. Je mehr Fälle in `memory_items` stehen, desto besser trifft der
automatische Betrieb — und zwar ab dem ersten Lauf, nicht erst nach einer Lernphase.

---

## 6. Was NICHT geändert wurde

* **Der Architekturstil.** Supervisor mit Fachagenten bleibt; keine Handoffs, kein Swarm.
* **Ein Fehler pro Lauf.** Bleibt so — der Agent sagt es jetzt nur ehrlich dazu.
* **Die vier Wächter beim Anwenden.** Unverändert; die neue Kennzeichnung zeigt einen davon
  nur früher an.
* **Automatischer Betrieb.** Verhält sich exakt wie vorher.
* **Die Frage Graph-Architektur statt monolithischer Prompts.** Gehört in die
  Bachelorarbeit, nicht in PT4.

## 7. Offene Punkte

* Nach einer Freigabe wird der nächste Fehler **nicht** automatisch angeboten; der nächste
  Lauf muss angestossen werden. Ob das so bleiben soll, ist eine offene Entscheidung.
* Bei einem 429 (Kontingent erschöpft) wartet die Wiederholung nur 1 Sekunde und der Fehler
  wird nicht als solcher erkannt — der Nutzer sieht eine unspezifische Fehlermeldung. Der
  Vorfall vom 15.08. ist durch Erhöhung des Kontingents gelöst, die Behandlung nicht.
* Ein Lauf von `generate_correction_llm` kostet rund 55.000 Token; das Kontingent muss
  deutlich darüber liegen.
* Eine reine Formatierungsfrage („gib mir den vollständigen Link") liess den Planer erneut
  `download_snapshot` wählen. Unnötig, aber harmlos — das entscheidet der Planer.
* `localhost` löst zuerst nach `::1` auf, der Entwicklungsserver lauscht nur auf IPv4: rund
  **2 Sekunden pro Anfrage**, auch für statische Dateien (`127.0.0.1` → 17 ms). Über
  `DEV_SERVER_HOST` einstellbar; die Voreinstellung bleibt aus Sicherheitsgründen der reine
  Loopback, weil ein dualstack-fähiges `::` zusammen mit `debug=True` auf allen
  Netzwerkschnittstellen lauschen würde. Die Frontend-Konfiguration zeigt fest auf
  `localhost` — ein Umstieg auf `127.0.0.1` im Browser müsste dort mitgezogen werden.

---

## Verwandte Dokumente

* **[`BEFUNDE_UND_LEHREN.md`](BEFUNDE_UND_LEHREN.md)** — die 16 Befunde vom 14./15.08.2026,
  auf sechs wiederkehrende Muster verdichtet, samt der Regeln, die daraus folgen. Wer wissen
  will, WARUM das System so gebaut ist, findet dort die Belege.
* **[`KONFIDENZ.md`](KONFIDENZ.md)** — Herkunft und Berechnung des Konfidenz-Scores.
* **`PROJECT_LOG.md`** — chronologisch, Eintrag für Eintrag.

---

## Geprüft mit

| Datei | Prüft |
|---|---|
| `app/eval/test_agent_truthfulness.py` | Keine Erfolgsmeldung ohne Beleg; Reichweite wird genannt |
| `app/eval/test_agent_context_access.py` | Sitzungstrennung, frischer Zustand, Entscheidungen, offene Vorschläge |
| `app/eval/test_agent_architektur.py` | Herkunft, Direktantwort, Intent-Abkürzung, Fakten-Block |

Alle drei laufen gegen das echte System und das echte Modell.
