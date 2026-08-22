# Bachelorarbeit — Projektprotokoll

Graph-basierte Systemarchitektur vs. monolithische Systemprompt-Struktur.
Ein Eintrag je abgeschlossener Einheit, **neueste unten**.

> Vorgänger: `PROJECT_LOG.md` (PT4, abgeschlossen 2026-08-15). Bewusst getrennt — siehe die
> Begründung dort. PT4 ist Nachweis für das Praxisprojekt, dieses Protokoll für die Arbeit.

---

## Dieses Protokoll ist das Rohmaterial der Arbeit

**Die Arbeit wird später aus diesen Einträgen geschrieben.** Das ist der ausdrückliche Zweck
(Nutzerentscheidung 16.08.2026), und er bestimmt, wie ein Eintrag auszusehen hat: Er wird nicht
für morgen geschrieben, sondern für den Moment in vier Wochen, in dem daraus ein Absatz in
Kapitel 5, 7 oder 8 werden muss.

Drei Dinge folgen daraus, und sie sind der Grund für die Felder unten:

1. **Ein Eintrag muss zitierbar sein.** Deshalb trägt jeder eine stabile Kennung `[BA-nnn]`.
   Sie ändert sich nie, auch wenn der Eintrag später ergänzt wird.
2. **Ein Eintrag muss wissen, wohin er gehört.** Chronologie ist die richtige Ordnung für ein
   Protokoll, aber die falsche für eine Arbeit. Das Feld **Kapitelbezug** löst das: Beim
   Schreiben von Kapitel 7 filtert man auf `K7` statt 40 Einträge zu lesen.
3. **Was nicht funktioniert hat, ist beim Schreiben so viel wert wie was funktioniert hat.**
   Kapitel 8 (Diskussion) und die Limitationen leben davon. Fehlschläge, Sackgassen und
   revidierte Annahmen gehören deshalb ausdrücklich hinein — sie sind später **nicht**
   rekonstruierbar.

---

## Eintragsformat

```
### [BA-nnn] JJJJ-MM-TT — [Kurztitel]
- **Status:** done / partial / blocked
- **Kapitelbezug:** K3 / K4 / K5 / K6 / K7 / K8 / K9  (auch mehrere; "—" wenn reine Hausarbeit)
- **Literatur:** L-Nummern aus `BA_LITERATUR.md`, sofern der Eintrag eine These stützt
- **Changed files:** ...
- **Was getan wurde:** 1–3 Sätze.
- **Verifikation:** wie geprüft (Testlauf, Messung, manuell) — mit dem tatsächlichen Ergebnis.
- **Was NICHT funktioniert hat:** Sackgassen, verworfene Annahmen, Fehlschläge. Nur weglassen,
  wenn es wirklich nichts gab.
- **Offen / nächstes:** was bleibt.
```

**Bei Messläufen zusätzlich verpflichtend**, sonst ist die Zahl später wertlos:

```
- **Lauf-Metadaten:** Variante (monolith/graph) · RULEBOOK_MODE · MEMORY_MODE ·
  HUMAN_IN_THE_LOOP · Modell + API-Version · Temperatur und übrige Parameter · Fall-IDs ·
  Wiederholungen · Zeitstempel · **Pfad der Rohdaten**
```

> **Die Zahl im Protokoll ersetzt die Rohdaten nicht.** Sie zeigt auf sie. Ein Eintrag ohne
> Rohdatenpfad ist beim Schreiben wertlos, weil sich nichts nachrechnen lässt.

---

## Was dieses Protokoll leisten muss

Es ist die **Rückverfolgbarkeit** der Arbeit. Jede Zahl, die später in Kapitel 7 steht, muss
sich hier bis zu ihrem Lauf zurückverfolgen lassen: welche Variante, welche Bedingungen,
welche Rohdaten. Ohne diese Kette ist eine Aussage nicht belastbar — und ein Gutachter fragt
genau danach.

Zwei Regeln, die aus PT4 mitgenommen werden, weil sie dort Geld und Zeit gekostet haben:

1. **Was gemessen wurde, wird notiert — auch wenn es nicht gefällt.** Ein Lauf, der gegen die
   Erwartung ausfällt, gehört genauso ins Protokoll wie ein bestätigender. Nachträgliches
   Anpassen nach dem Sehen der Ergebnisse ist ausgeschlossen; fällt doch etwas auf, wird es
   ausdrücklich als **Nachmessung** gekennzeichnet.
2. **Vermutungen werden als solche benannt.** „Vermutlich lag es an X" ist ein zulässiger
   Eintrag. „Es lag an X" ohne Beleg ist es nicht.

---

## Kapitelregister — Einstieg beim Schreiben

> **Für die Synthese: `docs/BA_METHODISCHE_BEFUNDE.md`** (BA-060). Dort stehen die Befunde
> aus BA-035 bis BA-059 **nach Kapitel sortiert**, jeder mit Verweis hierher — inklusive der
> acht wiederkehrenden Arbeitsmuster für Kapitel 8. Dieses Register bleibt der Einstieg in die
> Einträge selbst.

Beim Verfassen eines Kapitels hier beginnen, nicht oben im Protokoll.
**Bei jedem neuen Eintrag mitpflegen.**

| Kapitel der Arbeit | Einträge |
|---|---|
| **K3** Das bestehende System | BA-004, **BA-030** *(Artefakte des Monolithen)*, **BA-032**, **BA-033** *(Reporting-Schicht, B-Durchstich)*, **BA-046** *(Domaenenheuristik `similar_items`, Median aus Python)*, **BA-049** *(Fuzzy-Fallback im aktuellen Korrekturworkflow nicht erreichbar)* |
| **K4** Konzeption der Graph-Architektur | BA-005 … BA-015, BA-017 … BA-023, **BA-026** *(Knoten 1)*, **BA-027** *(State-Schnitt)*, **BA-028** *(Graphstruktur)*, **BA-029** *(Durchstich)*, **BA-031**, **BA-043** *(Iterations-/Proposal-Handoff)*, **BA-044**, **BA-045** *(Knotenvertraege, Guards, K8-Entscheidungsvertrag)*, **BA-047** *(Huellen-Handoff K5->K6)* |
| **K5** Forschungsdesign und Methodik | BA-004 … BA-016, BA-021 … **BA-035**, **BA-063** *(technischer Abbruch vs. fachliches Nullergebnis; Fortsetzung eines unterbrochenen Messlaufs)* |
| **K6** Evaluierungsdesign | BA-004, BA-007, **BA-014**, BA-017 … BA-021, **BA-023**, **BA-024** *(Datenprovenienz, Kontext-Handoff)*, **BA-025** *(Rohdatenluecke, Umgebungskontrolle)*, **BA-026** *(Lauf-Metadaten, Handoff-Smoke)*, **BA-027** *(Identify-Handoff)*, **BA-028** *(Trace-Persistenz)*, **BA-029** *(UF3-Beleg)*, **BA-030** *(autoritative Validitaet, UF3-Raster)*, **BA-031**, **BA-032** *(Blindungsbrueche)*, **BA-033** *(Provenienz-Matrix)*, **BA-034** *(Pilotkatalog)*, **BA-035** … **BA-052** *(First Pass, Rueckkante, Iterationsfuehrung, Handoff-Fix, Regressionen R1-R9, Trace-Registry, Kategorien-Instrumente, AP-G3-Abschlussmatrix, AP-G4-Pilotphasenabschluss, BA-Runner, gemeinsame Kategorie-4-Auswertung)*, **BA-051** *(Kategorie-4-Messgleichheit)*, **BA-063** *(Fortsetzungsmechanik, Vorpruefung `verify_fortsetzung.py`)*, **BA-064** *(Cross-Check als Kontrollmechanismus; 25 Messinkonsistenzen restlos geklaert)* |
| **K7** Ergebnisse | BA-013, BA-016 *(Regressionsreferenz)*, **BA-033** *(Durchstichmaterial)*, **BA-045** *(P04/P10 nach dem Fix — PILOT, kein Messwert)*, **BA-063** *(**die Hauptmessung: 255 Positionen, `abc-mess-20260822T141347Z.json`** — Auswertung in AP-I)*, **BA-064** *(Datensatz auditiert, sha256 `db867a26…`)* |
| **K8** Diskussion und Limitationen | BA-004 … BA-009, BA-013, **BA-014**, **BA-016** *(I10)*, **BA-021** *(falsches Gruen)*, **BA-024** *(veralteter Kontext)*, **BA-025** *(zwei venvs, fehlende Lauf-Metadaten)*, **BA-026** *(Restrisiken)*, **BA-027** *(Server-Teil offen)*, **BA-042** *(vier Auswertungsfehler in Folge)*, **BA-044** *(fehlende Evidenz als Unbedenklichkeit gelesen)*, **BA-045** *(Suite einzeln gruen / gesamt kaputt, schwache Negativkontrolle)*, **BA-046** *(zwei Messpunkte zeigen aufs Instrument; C-eigener Zusatz-LLM-Aufruf)*, **BA-047** *(ungueltige Test-Huelle, K2-Klassifikator zweimal daneben)*, **BA-048** *(zwei Pilotpfade nicht konstruierbar, P11-Pfad verfehlt)*, **BA-049** *(drei Pilotziele nicht belegbar; Guard fing den eigenen Testaufbau)*, **BA-050** *(vier ueberdehnte Formulierungen; Zeitstempel sind kein Aenderungsnachweis)*, **BA-052** *(fuenfte Formatannahme; Cross-Check fing sie)*, **BA-053** *(falscher FAIL durch Textsuche; git-porcelain-Parsing)*, **BA-063** *(Korrelation als Ursache gelesen; blinder Monitor; zweimal ungepruefte Kennzahl gemeldet; Instrumentendefekt `_schreibe_aggregat`; geteilter Runnerstand)*, **BA-064** *(GraphState misst nur die letzte Iteration; ueberdehnte Regel durch Negativkontrolle verhindert)* |
| **K9** Fazit und Ausblick | BA-006, BA-009, **BA-032** *(E-Mail-Nutzungspfad)* |
| *(ohne Kapitelbezug — Hausarbeit)* | BA-001, BA-002, BA-003 |

---

### [BA-001] 2026-08-15 — Start Bachelorarbeit: Arbeitsumgebung umgestellt
- **Status:** done
- **Changed files:** `CLAUDE.md`, `.github/instructions/instructions.md`, `docs/PT4_PLAN.md`,
  `docs/PROJECT_LOG.md`, `docs/BA_PROJECT_LOG.md` (neu)
- **Was getan wurde:** PT4 abgeschlossen und die Arbeitsumgebung auf die Bachelorarbeit
  umgestellt. Die Agenten-Instruktionen (`CLAUDE.md` und die daraus abgeleitete
  `instructions.md`) verweisen jetzt auf Exposé, Masterplan und Umsetzungsplan statt auf den
  PT4-Plan und tragen die Regeln, die den Vergleich schützen: Koexistenz statt Ersetzen, keine
  Strohmann-Baseline, eingefrorene Kontrollbedingungen, keine erfundenen Messergebnisse, erst
  Protokoll dann messen. `PT4_PLAN.md` und `PROJECT_LOG.md` sind als abgeschlossen
  gekennzeichnet und bleiben als Nachweis erhalten.
- **Verifikation:** Beide Instruktionsdateien enthalten keinen `demo/`-Pfad mehr (die alte
  `instructions.md` verwies noch auf den vor dem 02.08. gültigen Ordnernamen) und sind
  inhaltsgleich, weil die zweite aus der ersten abgeleitet wird — zwei abweichende Fassungen
  wären zwei Wahrheiten.
- **Drei Befunde beim Prüfen des Ist-Stands** (gegen den Code, nicht aus den Plänen
  abgeschrieben):
  * `RULEBOOK_MODE` steht in `app/core/agent_config.py` auf **`"cards"`**, nicht auf
    `"monolith"`. Ein Baseline-Lauf ohne ausdrückliches Setzen misst damit **nicht** den
    Monolithen. Der Masterplan nennt das seinen wichtigsten Einzelpunkt (Kap. 6.1); es steht
    jetzt als Falle in `CLAUDE.md`.
  * **`langgraph` ist nicht installiert**, und es existiert keine Zeile Graph-Code
    (Volltextsuche nach `StateGraph|GraphState|SP_ARCHITECTURE_MODE`: kein Treffer). Die
    Framework-Entscheidung ist getroffen, aber nicht umgesetzt.
  * **Das Modell-Deployment steht auf `gpt-4.1`** und deckt sich damit mit dem Exposé. Der im
    Umsetzungsplan (Kap. 4/12) benannte Konflikt GPT-4.1 gegen `gpt-4o` ist damit
    **aufgelöst** — die Pläne beschreiben hier einen überholten Stand.
- **Offen / nächstes:** Nach Masterplan Kap. 23, in dieser Reihenfolge: `RULEBOOK_MODE`-Historie
  der bestehenden Ergebnisdateien klären, sauberer Monolith-Baseline-Lauf mit
  `RULEBOOK_MODE=monolith`, dann `langgraph` pinnen und den `SP_ARCHITECTURE_MODE`-Schalter
  einbauen.

---

### [BA-002] 2026-08-15 — Link-Prüfer für die Doku-Umstrukturierung
- **Status:** done
- **Changed files:** `app/eval/check_doku_links.py` (neu), `docs/PROJECT_LOG.md`,
  `app/README-PT4.md` (je Verweise nachgezogen)
- **Was getan wurde:** Beim Umsortieren nach `docs/04_PT4/` sind fünf Verweise ins Leere
  gelaufen (drei in `PROJECT_LOG.md`, zwei in `README-PT4.md`) — lautlos, wie immer bei
  Markdown. Die fünf sind gezogen; dazu ein wiederholbarer Prüflauf, der jeden lokalen
  Verweis auflöst.
- **Verifikation:** Lauf über alle Markdown-Dateien des Repositories. Die vier heute
  umgestellten Dateien (`CLAUDE.md`, `instructions.md`, `PT4_PLAN.md`, `BA_PROJECT_LOG.md`)
  sind sauber.
- **Zweimal nachgeschärft, weil eine Prüfung mit Fehlalarmen wertlos ist:**
  1. Erste Fassung: 1672 Treffer, fast alle falsch. Ein blosser Dateiname in Backticks
     (`short_term.py`) ist eine ERWÄHNUNG im Fliesstext, keine Ortsangabe. Jetzt zählt nur,
     was einen Schrägstrich enthält.
  2. Zweite Fassung: 836 Treffer, davon 690 aus den Protokollen. Deren `demo/`-Pfade sind
     GESCHICHTE — sie waren am Eintragsdatum richtig, der Ordner heisst erst seit dem 02.08.
     `app/`. Sie nachträglich umzuschreiben wäre Geschichtsfälschung. In Protokollen werden
     jetzt nur noch die klickbaren Links geprüft.
- **Verbleibend: 149 Verweise**, davon **98 veraltete `demo/`-Pfade** in PT4-Dokumenten, die
  ebenfalls historisch sind, sowie Verweise auf Dateien, die es nie gab oder die mit dem
  Umbau verschwunden sind (`docs/HANDOVER.md`, `docs/Zwischenstand-Abschluss-AP2.md`).
  **Bewusst nicht angefasst** — das sind PT4-Dokumente, und ihre Bereinigung ist eine
  inhaltliche Entscheidung des Nutzers, keine technische.
- **Offen / nächstes:** Nach Abschluss der Doku-Umstrukturierung erneut laufen lassen; er
  meldet dann genau die Verweise, die der Umbau gebrochen hat.

---

### [BA-003] 2026-08-15 — PT4-Wissensspeicher in die Instruktionen aufgenommen — mit Grenze
- **Status:** done
- **Changed files:** `CLAUDE.md`, `.github/instructions/instructions.md`
- **Was getan wurde:** `docs/04_PT4/` ist jetzt in den Instruktionen benannt, aber **nicht
  pauschal**. Der neue Abschnitt trennt zwei Rollen: Sachwissen über das bestehende System
  (nachschlagen erwünscht) gegen PT4-Nachweise und PT4-Scope (nicht übernehmen).
  Fünf Dokumente sind namentlich als Nachschlagequelle freigegeben — allen voran
  `AGENTEN_ARCHITEKTUR.md`, weil es die **Baseline beschreibt**: wer sie nicht kennt, baut
  versehentlich einen Strohmann, und das ist laut Umsetzungsplan die grösste Bedrohung der
  Validität. Vier weitere sind ausdrücklich ausgenommen (`PT4_BELEGE.md`,
  `AP1_AP7_APE_BELEGE.md`, `AP5_AP6_DOCUMENTATION.md`, `PT4_PLAN.md`, `work-environment/`).
  Faustregel im Text: Wissen ja, Scope nein, **Zahlen nie** — eine PT4-Messung muss unter den
  Kontrollbedingungen dieser Arbeit neu erhoben werden.
- **Verifikation:** `app/eval/check_doku_links.py` — alle Verweise in beiden Dateien treffen.
  Der Prüflauf hat dabei einen eigenen Fehler von mir gefunden: die Pfade standen als
  `04_PT4/…` relativ zu `docs/`, `CLAUDE.md` liegt aber im Wurzelverzeichnis. Acht Stück
  korrigiert.
- **Zwei Befunde aus dem laufenden Umbau:**
  * `PT4_PLAN.md` und `PROJECT_LOG.md` sind inzwischen nach `docs/04_PT4/` gewandert. Die
    Verweise darauf in `CLAUDE.md` zeigten damit ins Leere und wurden ersetzt.
  * In `docs/04_PT4/work-environment/` liegen **zwei** Fassungen des PT4-Protokolls:
    `PROJECT_LOG.md` (mit Abschlusseintrag) und `PROJECT_LOG copy.md` (2411 Zeichen kürzer,
    ohne Abschluss — also der ältere Stand). Zwei Fassungen desselben Nachweises sind ein
    Risiko: irgendwann zitiert jemand die falsche. **Nicht angefasst** — welche bleibt, ist
    eine Entscheidung des Nutzers.
- **Offen / nächstes:** Die doppelte Protokollfassung auflösen; danach den Link-Prüfer erneut
  über das fertig sortierte `docs/` laufen lassen.

---

### [BA-004] 2026-08-16 — Lagebericht: Pläne gegen den echten Code geprüft
- **Status:** done (reine Bestandsaufnahme — **kein** Code, **keine** Konfiguration geändert;
  einzige berührte Datei ist dieses Protokoll)
- **Changed files:** `docs/BA_PROJECT_LOG.md`
- **Was getan wurde:** Exposé (`03_Expose-extern/source-2/exposee.md`), Masterplan (02.08.),
  Umsetzungsplan (14.07.), dieses Protokoll sowie `04_PT4/AGENTEN_ARCHITEKTUR.md` und
  `04_PT4/BEFUNDE_UND_LEHREN.md` gelesen; anschliessend **jede** Ist-Zustands-Aussage der
  beiden Pläne gegen den echten Code geprüft statt sie zu übernehmen. Ergebnis: die Pläne
  sind in Substanz und Methodik tragfähig, in fast jeder **Ortsangabe** und in **zwei
  inhaltlichen Punkten** überholt. Ein bisher nirgends benannter konfundierender Faktor ist
  dabei aufgefallen (Befund 4).
- **Verifikation:** Volltextsuchen, Datei-/Zeilenzählungen, `pip list`, SQLite-Abfrage auf
  `app/db/pt4.sqlite3`, Lesen der Ergebnis- und Katalogdateien. Aus `app/.env` wurden
  ausschliesslich Nicht-Geheimnisse gelesen (Deployment-Namen, API-Version, Modus-Schalter);
  keine Schlüssel ausgegeben.

**Bestätigt (Pläne haben recht):**

| Aussage | Befund |
|---|---|
| `RULEBOOK_MODE`-Default ist `"cards"` | bestätigt, `app/core/agent_config.py:40` |
| `langgraph`/`langchain` nicht installiert | bestätigt, `pip list` — kein Treffer |
| Keine Zeile Graph-Code | bestätigt, Suche `StateGraph\|GraphState\|SP_ARCHITECTURE_MODE` trifft nur Dokumente; kein `graph/`-Verzeichnis |
| Regelwerk 936 Zeilen / 36.165 Byte (nicht 425) | bestätigt, unverändert seit 02.08. |
| Datenweitergabe der Runtime-Skripte | bestätigt: **über Dateien**, nicht über Rückgabewerte |

**Neun Abweichungen zwischen Plan und Wirklichkeit:**

1. **Sämtliche Pfad- und Zeilenangaben des Masterplans sind überholt.** Der Ordner heisst
   seit 02.08. `app/`, und es wurde zusätzlich tiefer umsortiert:
   `demo/agent_config.py` → `app/core/agent_config.py`, `demo/rulebook_loader.py` →
   `app/core/rulebook_loader.py`, `demo/smart-planning/runtime/` →
   `app/tools/smart-planning/runtime/`, `demo/eval/` → `app/eval/`, die Testkataloge nach
   `data/snapshots/pt4-manipulated_snapshots/`, `requirements.txt` nach `app/deploy/`.
2. **Die Skripte sind seit dem 02.08. gewachsen; jede Zeilennummer im Masterplan ist falsch.**
   `generate_correction_llm.py` 964 → **1085**, `identify_snapshot.py` 1130 → **1186**,
   `identify_error_llm.py` 423 → **450**, `apply_correction.py` 465 → **572**,
   `sp_agent.py` 504 → **680**, `orchestration_agent.py` 1101 → **1379**.
   Konkret für den Bauauftrag: der einzige Verzweigungspunkt `execute_pipeline()` liegt bei
   **`sp_agent.py:626-679`**, nicht bei `:450-503`.
3. **Der Modellkonflikt GPT-4.1 vs. `gpt-4o` existiert nicht mehr.** Alle fünf
   Deployment-Variablen stehen auf `gpt-4.1`, API-Version `2025-01-01-preview`. Der
   Umsetzungsplan (Kap. 4.1/12.1) und Masterplan Kap. 11 beschreiben einen überholten Stand.
   Die Umstellung ist **datiert belegt**: `infra/terraform.tfvars:63-66` im Nachbar-Repository
   `Infra/agentic-ai-mfg-infrastructure-terraform` trägt den Kommentar „02.08.2026 von gpt-4o
   auf gpt-4.1 umgestellt".
4. **Neu und wichtig: das episodische Gedächtnis ist im gemessenen Pfad aktiv — unbedingt.**
   Kein Plan erwähnt das; der Masterplan (02.08.) ist älter als AP7.2, der Umsetzungsplan
   führt Memory als „nicht Teil der Arbeit" — es liegt aber **mitten im Korrekturschritt**:
   * `generate_correction_llm.py:886-902` holt frühere **menschliche** Entscheidungen und legt
     sie dem Modell als Belege in den Prompt — vor dem LLM-Aufruf, an keine Bedingung geknüpft.
   * `:936-975` — `same_entity_confirmed_value()` **überschreibt** den Modellwert, wenn ein
     Mensch für dasselbe Objekt schon anders entschieden hat.
   * `:1017-1027` — `memory_support` geht mit Gewicht 0,2 in die Konfidenz ein und hebt sie
     auf mindestens 0,9.
   * Bestand heute: **20 Einträge** in `memory_items` (11 approve, 7 modify, 2 reject) — am
     15.08. waren es laut `AGENTEN_ARCHITEKTUR.md` noch 12. Der Bestand **wächst weiter**.
   * Dass das bereits gemessen hat, ist belegt: `pt4-combined-results.json` schreibt für
     **7 von 10** Fällen `memory_support: 1.0`.

   Drei Folgen für die Arbeit: (a) der Faktor wirkt in **beiden** Varianten, ist also kein
   Vorteil einer Seite, verfälscht aber die Halluzinationsrate nach unten; (b) er ist
   **reihenfolge- und laufzahlabhängig**, was der geforderten randomisierten
   Ausführungsreihenfolge (Exposé, Masterplan Kap. 12) direkt widerspricht; (c) das
   Gedächtnis ist objektbezogen, und der Katalog benutzt dieselben Objekte mehrfach
   (`demands[1].demandId` → `D100005_002` in isoliert I01 **und** kombiniert 01/04) — ein
   „richtiger" Wert kann also aus dem Gedächtnis stammen statt aus der Architektur.
   **Das ist genau der Fall, vor dem Regel 6 warnt** (Messinstrument vor der Messung prüfen).
   Zu entscheiden **vor** dem Baseline-Lauf: Gedächtnis für Messläufe einfrieren oder
   abschalten — in beiden Varianten identisch und dokumentiert.
5. **Die `RULEBOOK_MODE`-Historie ist klärbar, und der Masterplan liegt hier falsch.**
   Kap. 6.1 sagt, für `run_isolated_suite.py`/`run_combined_suite.py` sei „nicht verifiziert",
   welcher Modus lief. Tatsächlich erzwingen **alle drei** Eval-Skripte `cards` hart im Code:
   `run_isolated_suite.py:115`, `run_combined_suite.py:97`, `run_iterative.py:33`.
   → **Sämtliche bestehenden Ergebnisse entstanden unter `cards`. Im Repository existiert
   kein einziger Lauf unter `monolith`.** Damit ist Checklistenpunkt 2 beantwortet.
6. **Die bestehenden Ergebnisdateien taugen auch für `cards` nicht als Rohdaten.**
   `pt4-eval-results.json` und `pt4-combined-results.json` enthalten **keine** Lauf-Metadaten:
   kein Zeitstempel, kein Modell, keine Temperatur, kein `RULEBOOK_MODE`, kein Prompt, keine
   Antwort. Sie erfüllen weder Masterplan Kap. 17 noch Regel 7 aus `CLAUDE.md`. Jede Zahl der
   Arbeit muss neu erhoben werden — was ohnehin galt (keine PT4-Zahlen), hier aber zusätzlich
   technisch erzwungen ist.
7. **`build_test_catalog.py` hat den bestehenden Katalog nicht erzeugt, und es ist kleiner
   als die Pläne annehmen.** Es enthält vier Injektoren, von denen nur **drei** in `CATALOG`
   aktiv sind (`inject_empty_demand_id` ist definiert, aber nicht eingetragen), und es legt
   Snapshots **live über die API** an. Die 10+10 Fälle auf Platte stammen aus zwei
   **PowerShell**-Skripten (`generate-isolated-error-snapshots.ps1`,
   `generate-error-snapshots.ps1`); ihre Ground Truth liegt in `expected-results.json` bzw.
   `ERROR-SNAPSHOTS.md`, nicht in `metadata.txt.injected_error`. Es gibt also **zwei**
   Ground-Truth-Mechanismen nebeneinander. Brücke 1 aus `CLAUDE.md` ist damit präziser zu
   fassen: die *Methode* ist übernommen, das benannte Skript ist nicht das verwendete Werkzeug.
8. **Der Katalog ist kleiner und schiefer, als „10+10" nahelegt.** Isoliert: 10 Fälle, je
   1 Fehler, 10 verschiedene Validatoren. Kombiniert: 10 Fälle — aber **01–03 sind
   Einzelfehler** und wiederholen die Klassen von I01–I03; wirklich mehrfehlerhaft sind nur
   **04–10** (7 Fälle mit 2–3 Fehlern). Macht **17 distinkte Fälle**, 3 redundante.
   **Wiederholungen: keine. Grenzfälle: keine** — kein einziger Fall, bei dem „keine Korrektur
   erzwingen, sondern Unsicherheit ausweisen" die richtige Antwort wäre. Damit fehlt genau
   das Material für UF2 (Robustheit).
9. **Kleinigkeiten, die einen Baseline-Lauf trotzdem kippen können:**
   * `app/core/rulebook_loader.py:6` behauptet im Kopfkommentar `"monolith" (default)` — der
     Code sagt `cards`. Wer den Loader liest, setzt die Baseline falsch auf. Der Kommentar in
     `agent_config.py` ist korrekt; die beiden widersprechen sich.
   * `validate_correction_schema_llm.validate_with_retry(..., max_retries=5)` — der Masterplan
     (Kap. 4.3) nennt 3. Das ist eine Kontrollbedingung und gehört richtig dokumentiert.
   * `HUMAN_IN_THE_LOOP` ist **`true`** als Default und in `app/.env` nicht gesetzt.
     `generate_correction_llm.open_proposal_blocking()` bricht mit Exit-Code 3 ab, solange für
     denselben Snapshot ein Vorschlag offen ist. Der geplante **Wiederholungs-Wrapper für UF2
     läuft damit ab Durchgang 2 desselben Falls ins Leere** — vor dem Bau zu lösen.
   * `requirements.txt` pinnt `openai>=1.6.0,<2.0.0`, installiert ist **2.14.0**. Die Umgebung
     weicht schon heute von der Pin-Datei ab; das ist beim Nachziehen von `langgraph` zu
     berücksichtigen.
   * Masterplan Kap. 4.7 „kein Terraform im Repository" stimmt für *dieses* Repository, ist
     als Aussage über das Projekt aber irreführend: die Infrastruktur liegt als Terraform im
     Nachbar-Repository `Infra/agentic-ai-mfg-infrastructure-terraform`. Das Exposé ist damit
     korrekt, die geplante Richtigstellung entfällt. **Einschränkung:** eine
     `azurerm_cognitive_deployment`-Ressource findet sich dort nicht — Terraform verwaltet,
     *welches* Deployment die Anwendung benutzt (über ein Key-Vault-Secret), nicht dessen
     Anlage.

- **Stand der Master-Checkliste (Masterplan Kap. 23):** erledigt sind der GPT-4.1-Teil von
  Punkt 1 (Deployment steht, `.env` gesetzt, API-Version geprüft — der geforderte
  **Regressionstest** gegen einen bekannten Fall fehlt) und Punkt 2 (Modus-Historie geklärt,
  siehe Befund 5). **Alle übrigen 19 Punkte sind offen**, beginnend mit dem sauberen
  Monolith-Baseline-Lauf.
- **Offen / nächstes:** Vor jedem Messlauf ist die Gedächtnisfrage (Befund 4) zu entscheiden
  und schriftlich festzuhalten — sie ist dem Baseline-Lauf **vorgelagert**, weil ein Lauf mit
  aktivem Override die Baseline unbrauchbar macht und Regel 5 ein Nachjustieren verbietet.
  Danach Masterplan Kap. 23 in Reihenfolge: Regressionstest, Baseline-Lauf mit ausdrücklich
  `RULEBOOK_MODE=monolith`, dann `langgraph` und der `SP_ARCHITECTURE_MODE`-Schalter.
- **Unsicherheiten, ausdrücklich als solche benannt:**
  * Ob im Cloud-Betrieb auch die generische `AZURE_OPENAI_DEPLOYMENT` der Korrektur-Pipeline
    aus dem Key-Vault-Secret gespeist wird, ist **nicht geprüft**. Für lokale Messläufe
    (`STORAGE_MODE=LOCAL`, `app/.env`) ist es ohne Belang.
  * Ob die bestehenden Ergebnisdateien mit oder ohne damaligen Gedächtnisbestand entstanden
    sind, lässt sich **nicht mehr rekonstruieren** — `pt4-combined-results.json` belegt nur,
    dass Gedächtnis wirkte, nicht mit welchem Bestand.
  * Der Aufwand, `identify_snapshot.py` als Knoten 3 aufrufbar zu machen, ist **nicht
    abgeschätzt**: das Skript hat keine importierbare Gesamt-Einstiegsfunktion, die
    Ablaufsteuerung liegt in `main()` (Z. 888-1185, rund 300 Zeilen).

---

### [BA-005] 2026-08-16 — Drei Pläne zu einem zusammengeführt, drei Entscheidungen fixiert
- **Status:** done (Dokumentation und Instruktionen; **kein** Code, **keine** Konfiguration)
- **Changed files:** `docs/BA_MASTERPLAN.md` (neu), `CLAUDE.md`,
  `.github/instructions/instructions.md`, `docs/04_PT4/PT4_PLAN.md`, `docs/BA_PROJECT_LOG.md`
- **Was getan wurde:** `BACHELORARBEIT_UMSETZUNGSPLAN.md` (14.07., Methodik),
  `Graph-Architektur-Masterplan_fable.md` (02.08., Bau-Referenz) und `Doku-Claude-Chat.md`
  (Arbeitsweise, Risikoeinordnung) sind zu `docs/BA_MASTERPLAN.md` vereinigt — mit dem am
  16.08. verifizierten Ist-Zustand statt der überholten Angaben. Die drei Vorgänger werden
  vom Nutzer gelöscht. Alle Verweise darauf sind nachgezogen.
- **Was aus welchem Vorgänger übernommen wurde:** Methodik, Operationalisierung der drei
  Dimensionen, Instrumentarium und Validitätsbedrohungen aus dem Umsetzungsplan; verifizierte
  Bestandsaufnahme, Koexistenz-Prinzip, Knoten, `GraphState`, Kanten und Master-Checkliste aus
  dem Masterplan; vertikaler Durchstich, Ergebnisoffenheit und die ehrliche Einordnung
  „der kritische Pfad sind die Menschen, nicht der Code" aus `Doku-Claude-Chat.md`.

**Drei Entscheidungen, vom Nutzer nach Abwägung getroffen — ab jetzt bindend:**

1. **Zielbild: acht sequenzielle Knoten wie im Exposé.** Keine Baumsuche.
2. **Framework: LangGraph.** Rückfall auf einen expliziten Zustandsautomaten bleibt zulässig,
   ist dann aber im Masterplan zu vermerken und im Methodenteil zu begründen.
3. **`MEMORY_MODE=off` für alle Messläufe, in beiden Varianten.**

**Begründung zu 3, weil sie die Messbarkeit von UF1 entscheidet.** Das Gedächtnis wurde nicht
aus Bequemlichkeit abgeschaltet, sondern weil sein Bestand die Sollwerte des Testkatalogs
objektgenau enthält. Nachweisbare Kette aus den eigenen Daten:

| Zeit | Ereignis |
|---|---|
| 31.07., 19:06 | isolierte Suite fertig. Fall **I03**: Modell schlägt `1.14` vor, richtig ist `1.017` → `value_ok: false` |
| 31.07., 20:25:48 | ein Mensch korrigiert im Review Board auf `1.017` → `memory_items` id 11 (`DENSITY_VALUES`, `articles:100005`, suggested `1.14` → final `1.017`) |
| 31.07., 23:01 | kombinierte Suite, Fall 03, derselbe Artikel: `memory_support: 1.0`, `top_value: 1.017` — **richtig** |

Das Modell wurde nicht besser; ihm wurde die Antwort gereicht. Dasselbe gilt für die Einträge
9, 10, 12, 14 (alle 31.07., 20:22–20:31) sowie 16/18/22 — sie decken I01, I02, I04, I05, I08
und I10 mit exakt den Ground-Truth-Werten ab.
**Verworfen wurde ausdrücklich das Einfrieren des Bestands:** Einfrieren entfernt die
Kontamination nicht, es verteilt sie gleichmässig. Beide Halluzinationsraten wanderten gegen
null — verloren ginge nicht die Fairness, sondern die **Auflösung**.

**Ein Befund beim Lesen des Schreibgerüsts, den kein Plan kannte:**
`docs/03_Expose-extern/source-2/Thesis.md:11` beschreibt den Vergleich als
`monolithic RAG vs. graph-based LATS+RAG` — eine **Baumsuche** (Zhou et al., ICML 2024) mit
Wertfunktion, LLM-Judge, Budget-Controls (§7.2) und eigener Ablation (§9.6), ausdrücklich mit
dem Vermerk **„needs Macher sign-off"**. Das deckt sich weder mit dem Exposé noch mit den
Umsetzungsplänen. Mit Entscheidung 1 ist LATS **nicht** Gegenstand der Arbeit und gehört nach
§11.2 Future Work; der Rückbau von `Thesis.md` steht als Checklistenpunkt aus. Ergänzend:
`source-2/pdf/` enthält **null PDFs** — die 48-Titel-Bibliografie ist Absicht, nicht Bestand.

- **Verifikation:** `instructions.md` wird jetzt mechanisch aus `CLAUDE.md` abgeleitet
  (`tail -n +5`), Gegenprobe per `diff` ist leer — zwei abweichende Fassungen wären zwei
  Wahrheiten. Verweisprüfung über alle Markdown-Dateien mit `app/eval/check_doku_links.py`;
  kein Verweis auf die drei Vorgängerpläne bleibt ausserhalb der Protokolle stehen. Die
  `demo/`-Pfade in den PT4-Protokollen sind Geschichte und bleiben unangetastet.
- **Offen / nächstes:** Masterplan Kap. 23, vorgelagerter Block: `MEMORY_MODE`-Schalter bauen,
  Regressionstest, dann der saubere Monolith-Baseline-Lauf mit `RULEBOOK_MODE=monolith` und
  `MEMORY_MODE=off`. **Parallel und nicht später:** Expertentermine vereinbaren — laut
  Masterplan Kap. 21.1 sind die Menschen der kritische Pfad, nicht der Code.
- **Unsicherheit:** Ob der Betreuer den LATS-Rückbau mitträgt oder umgekehrt LATS freigeben
  würde, ist **nicht geklärt** — das Schreibgerüst nennt die Freigabe als ausstehend. Die
  Entscheidung vom 16.08. hält sich an das eingereichte Exposé.
  *(Nachtrag desselben Tages: hinfällig — siehe nächster Eintrag.)*

---

### [BA-006] 2026-08-16 — Kollegen-Ordner verworfen, Exposé direkt geprüft, Knotenschnitt neu begründet
- **Status:** done (Dokumentation; **kein** Code, **keine** Konfiguration)
- **Changed files:** `docs/BA_MASTERPLAN.md`, `CLAUDE.md`,
  `.github/instructions/instructions.md`, `docs/BA_PROJECT_LOG.md`
- **Was getan wurde:** Der Nutzer hat mitgeteilt, dass `docs/03_Expose-extern/source-2/` von
  einem Kollegen ohne Projektkenntnis stammt und ignoriert werden kann — und dass **Knoten und
  Kanten noch gar nicht definiert** sind, also frei wählbar nach Eignung. Beides ist eingearbeitet.

**1. Das Exposé ist jetzt direkt geprüft, nicht über eine Zusammenfassung.**
Bis dahin lief jede Exposé-Aussage über `source-2/exposee.md`, weil das PDF sich nicht rendern
liess (kein poppler). Das war ein Risiko: eine fremde Destillation als Grundlage des ganzen
Plans. **Gelöst** — `pypdf` ist im Projekt vorhanden und liest die 20 Seiten als Text
(62.183 Zeichen). Der Weg steht jetzt in Masterplan Kap. 0.
**Gegenprobe der Zusammenfassung gegen das PDF: sie war korrekt.** Forschungsfrage wörtlich
identisch, „425 Zeilen und 20.284 Zeichen", GPT-4.1, Terraform, SUS/UEQ ≥5 — alles bestätigt.
Sie wird trotzdem nicht mehr verwendet; massgeblich ist ab jetzt allein das PDF.

**2. Zwei Befunde aus dem PDF, die die Vorgängerpläne falsch hatten:**
* **Das Exposé nennt kein Framework.** Volltextsuche nach `LangGraph`/`LangChain`: **null
  Treffer**. Die Masterplan-Begründung „LangGraph deckt sich 1:1 mit dem, was das Exposé nennt"
  war schlicht **falsch**. Die Wahl ist frei — sie muss begründet werden, aber keine Variante
  widerspricht dem Exposé. Der Rückfall auf einen Zustandsautomaten braucht damit **keine
  Rechtfertigung mehr**, nur eine Benennung.
* **Die sechs Schritte im Exposé stehen unter „etwa"** („in klar definierte Schritte zerlegt —
  **etwa** Eingabeanalyse, Fehlerklassifikation, …"). Sie sind **Beispiele, keine abschliessende
  Liste**. Zusammen mit der Aussage des Nutzers heisst das: Anzahl und Schnitt sind eine
  **Designentscheidung der Arbeit** und in Kapitel 4 zu begründen.

**3. Der Knotenschnitt ist neu begründet — und dabei ein Loch im Altplan aufgefallen.**
Neues Kriterium, das zugleich das Designprinzip der Arbeit ist:
> **Eine Knotengrenze gehört dorthin, wo ein eigener Fehlermodus beobachtbar und zurechenbar wird.**

Daraus folgen **neun** statt acht Knoten. Jede der vier Halluzinationskategorien hat jetzt genau
einen Knoten, an dem sie sichtbar wird: Kat. 1 → Knoten 5, Kat. 2 → Knoten 6, Kat. 3 → Knoten 4,
Kat. 4 → Knoten 7. Beim Monolithen liegen alle vier hinter einer Ausgabe — man sieht *dass*
etwas falsch ist, nicht *welcher* Fehlermodus zugeschlagen hat. **Das ist der zu messende
Unterschied**, und der Schnitt macht ihn erst messbar.

Zwei Abweichungen vom Altplan, beide mit Grund:
* **Knoten 7 (Anwendung & Re-Validierung) ist neu.** Der Altplan endete beim Korrekturvorschlag,
  **aber seine bedingte Kante fragte nach `errors_after` — das niemand erzeugte.** Ohne Anwendung
  und Re-Validierung gibt es diesen Wert nicht, und damit weder die Iterationsschleife noch die
  Messung der Folgefehler. Das war ein Loch, kein Detail.
* **Knoten 8 (Ergebnisbewertung) ist ein Knoten, keine Kante.** Der Altplan modellierte sie als
  die bedingte Kante selbst. Für eine Arbeit über Nachvollziehbarkeit ist das die schlechtere
  Wahl: Eine Kante hinterlässt keinen Zwischenzustand, auf den man zeigen kann. Als Knoten
  schreibt sie `decision` samt Begründung in den State; der Router liest nur noch
  `state["decision"]["action"]` und enthält **keine** Fachlogik. Ein Router mit eingebauter
  `if/else`-Kette wäre wieder genau der implizite Kontrollfluss, den die Arbeit dem Monolithen
  vorwirft.

Nachgezogen: `GraphState` (`applied`, `manual_intervention_required`), Kap. 11 mit **zwei**
bedingten Kanten statt einer, Dateilayout, Extraktionsreihenfolge, Checkliste.

**4. LATS ist gegenstandslos.** Das abweichende Zielbild stand nur in `Thesis.md` aus dem
Kollegen-Ordner. Damit entfällt der geplante Rückbau, entfällt der Checklistenpunkt und entfällt
die offene Betreuer-Frage aus dem vorigen Eintrag. Das Schreibgerüst der Arbeit ist neu
aufzusetzen — diesmal gegen das Exposé.

- **Verifikation:** `instructions.md` erneut aus `CLAUDE.md` abgeleitet, `diff` leer.
  `app/eval/check_doku_links.py` fand **einen** echten Fehler in meinem eigenen Text (ein
  Verweis `source-2/exposee.md`, der relativ zu `docs/` aufgelöst ins Leere lief) — korrigiert.
  `BA_MASTERPLAN.md` und `CLAUDE.md` haben jetzt null defekte Verweise.
- **Offen / nächstes:** unverändert der vorgelagerte Block aus Masterplan Kap. 23 —
  `MEMORY_MODE`-Schalter, Regressionstest, sauberer Monolith-Baseline-Lauf. Parallel die
  Expertentermine.
- **Zu entscheiden, sobald der Graph läuft:** ob der Schnitt bei neun Knoten bleibt. Reduzierbar
  sind 3+4 (zusammenlegbar) und 9 (entbehrlich); **nicht** reduzierbar sind 4, 5, 6 und 7 — an
  ihnen hängt je eine Halluzinationskategorie. Eine Reduktion wäre im Methodenteil auszuweisen.

---

### [BA-007] 2026-08-16 — Literaturrecherche: von 4 auf 29 Quellen
- **Status:** done (Dokumentation; **kein** Code)
- **Changed files:** `docs/BA_LITERATUR.md` (neu), `docs/BA_MASTERPLAN.md` (Verweis),
  `docs/BA_PROJECT_LOG.md`
- **Was getan wurde:** Webrecherche nach zusätzlicher Literatur. Statt Masse gezielt nach den
  Lücken gesucht, die die Argumentation offen liess. Ergebnis: **29 Quellen**, sortiert nach
  Verwendungsstelle in der Arbeit, jede einzeln gegen die Primärquelle geprüft. Belastbarkeit ist
  je Eintrag markiert (✔ vollständig verifiziert / ◐ Autorenliste noch aus DOI zu ziehen) —
  **Autorennamen wurden bewusst nicht geraten**.
- **Vier Funde, die inhaltlich etwas ändern:**
  * **Wu, Terry & Cai (2022), CHI — „AI Chains".** Die **nächstverwandte Vorarbeit überhaupt**:
    20-Personen-Studie, die zeigt, dass Verkettung von LLM-Schritten Qualität **und** Transparenz
    erhöht. Fehlte bisher vollständig. Muss zitiert **und abgegrenzt** werden (sie misst
    wahrgenommene Transparenz an allgemeinen NLP-Aufgaben; diese Arbeit misst Halluzination gegen
    Ground Truth an produktionskritischem JSON). Ohne diese Abgrenzung ist die Neuheit angreifbar.
  * **Turpin et al. (2023), NeurIPS — unfaithful Chain-of-Thought.** Der stärkste denkbare
    Einwand gegen UF3: Modellbegründungen können den echten Entscheidungsweg systematisch falsch
    darstellen. **Lässt sich in einen Verstärker drehen:** Der `trace` wird vom **Code
    aufgezeichnet**, nicht vom Modell erzählt (`matched_rules` = was der Loader wirklich lud,
    `technical_check` = was der Validator wirklich zurückgab). Beobachtung statt Selbstauskunft —
    genau der Unterschied zum Monolithen. Gehört in Kapitel 4 **und** in die Diskussion.
  * **Baltes et al. (2026), Empirical Software Engineering — Leitlinien für empirische
    LLM-Studien.** Acht Berichtspflichten plus Checkliste für genau diesen Studientyp; decken sich
    weitgehend mit Masterplan Kap. 17. **Zwei Leitlinien erfüllt die Arbeit nicht** und muss sie
    als Limitation ausweisen: kein offener LLM-Vergleichslauf (Exposé fixiert GPT-4.1) und die
    Validierung gegen menschliches Urteil steht und fällt mit der Expertenrunde.
  * **Tam et al. (2024), EMNLP Industry — „Let Me Speak Freely?".** Gegenbefund: Formatzwang
    senkt die Reasoning-Leistung messbar. Trifft **beide** Varianten, aber die Graph-Variante
    erzwingt Struktur häufiger (je Knoten) — **ein möglicher systematischer Nachteil der eigenen
    Variante**, der diskutiert werden muss statt unerwähnt zu bleiben.
- **Geschlossene Lücke:** Für **UF2 (Robustheit)** gab es bisher **keine einzige** Quelle. Jetzt
  drei: Sclar et al. (ICLR 2024, Formatsensitivität bis 76 Punkte Unterschied), Wang et al.
  (ICLR 2023, Streuung über Wiederholungen als legitimes Messobjekt) und eine Arbeit zur
  Nicht-Determiniertheit auch bei `temperature=0` — letztere entkräftet den naheliegenden
  Einwand „nimm doch Temperatur 0".
- **Verifikation:** Zwei Quellen wurden zusätzlich direkt am Volltext geprüft, weil sie tragende
  Aussagen stützen: Henkel et al. (2026) — PRISMA-Übersicht, 2.341 gesichtet, 88 ausgewertet,
  **75 % TRL 4–6, 9,1 % einsatzorientierte Evidenz** — und Baltes et al. (2026), Leitlinien und
  Checkliste. Beide bestätigt.
- **Ehrlich benannt:** **Zu LLM-gestützter Korrektur strukturierter ERP-/Planungsdaten existiert
  keine begutachtete Literatur** — die Suche lieferte nur Anbieter- und Beratungsinhalte. Das ist
  kein Recherchemangel, sondern der Beitrag der Arbeit; die Lückenformulierung in Kapitel 1 ist
  entsprechend eng zu fassen (nicht „LLMs in der Industrie sind unerforscht" — das wäre durch
  Henkel et al. widerlegt).
- **Offen / nächstes:** Die ◐-Einträge über DOI/arXiv vervollständigen, BibTeX von den
  Primärquellen ziehen (nicht von Aggregatoren), Preprint-Status von drei Quellen vor Abgabe
  erneut prüfen. Am Bauplan ändert sich nichts — der vorgelagerte Block aus Masterplan Kap. 23
  (`MEMORY_MODE`, Regressionstest, Baseline-Lauf) bleibt der nächste Schritt.

---

### [BA-008] 2026-08-16 — Literatur auf 16 verdichtet, Protokoll auf Schreibbetrieb umgestellt
- **Status:** done
- **Kapitelbezug:** K5, K8 *(die Literaturauswahl selbst ist Methodik; die Protokollstruktur
  betrifft die Nachvollziehbarkeit der eigenen Arbeit)*
- **Literatur:** L05, L11, L13, L15 — die vier, die inhaltlich etwas verändert haben
- **Changed files:** `docs/BA_LITERATUR.md` (auf 16 verdichtet),
  `docs/BA_LITERATUR_ARCHIV.md` (neu), `docs/BA_PROJECT_LOG.md`, `CLAUDE.md`,
  `.github/instructions/instructions.md`
- **Was getan wurde:** Zwei Dinge. **(1)** Die 29 recherchierten Quellen auf **16 Kernquellen**
  verdichtet, nach Verwendungsstelle sortiert; die übrigen 13 nach `BA_LITERATUR_ARCHIV.md`
  archiviert statt verworfen. **(2)** Das Protokoll auf seinen eigentlichen Zweck umgestellt:
  Es ist das **Rohmaterial, aus dem die Arbeit später verfasst wird** (Nutzerentscheidung).
- **Die Auswahlregel für die 16**, damit sie nachvollziehbar bleibt: aufgenommen wurde, was
  **einen konkreten Satz der Arbeit trägt** — nicht, was thematisch passt. Vier Exposé-Quellen
  sind gesetzt; die zwölf übrigen decken je eine Stelle ab, die sonst unbelegt bliebe
  (Zerlegungswirksamkeit, Halluzinationstaxonomie, UF2-Motivation, UF2-Methodik, UF3-Einwand,
  UF3-Begrifflichkeit, Berichtspflichten, Forschungsdesign, Gegenbefund, Forschungslücke).
- **Verifikation:** Alle 16 einzeln an der Primärquelle geprüft (ACL Anthology, ACM DL,
  NeurIPS/ICLR-Proceedings, arXiv, dblp) — **Zitat-Status durchgehend ✔**. Die zwei zunächst
  nur teilgeprüften Einträge (Jacovi & Goldberg 2020; Madaan et al. 2023) wurden vor der
  Aufnahme gezielt nachrecherchiert und bestätigt. Autorennamen wurden **nirgends geraten**;
  im Archiv sind die unvollständigen als ◐ markiert.
- **Umstellung des Protokolls — was sich ändert und warum:**
  * **Stabile Kennungen `[BA-nnn]`** für alle sieben Alteinträge nachgetragen. Ohne sie kann
    kein Kapitel einen Eintrag zitieren.
  * **Neue Pflichtfelder** `Kapitelbezug:` und `Literatur:` sowie **`Was NICHT funktioniert
    hat:`** — letzteres, weil Kapitel 8 und die Limitationen davon leben und es sich später
    nicht rekonstruieren lässt.
  * **Kapitelregister** oben in der Datei: Einstieg beim Schreiben ist ab jetzt das Register,
    nicht die Chronologie.
  * **Regel 11 in `CLAUDE.md`** verankert das dauerhaft, inklusive „Belege statt Behauptungen":
    Fundstelle nennen (Datei + Zeile, Commit, Rohdatenpfad), nicht „geprüft".
- **Begründung der Struktur — die Alternative wäre schlechter gewesen:** Das Protokoll
  chronologisch zu lassen ist richtig (es ist der Prüfpfad, und Umsortieren wäre
  Geschichtsfälschung), aber Chronologie ist die **falsche Ordnung zum Schreiben**. Der
  Kapitelbezug plus Register löst beides, ohne die Chronologie anzutasten. Ein reines
  „mehr Referenzen einstreuen" hätte das Zugriffsproblem nicht gelöst.
- **Was NICHT funktioniert hat:** Der erste Zuschnitt der 16 hatte SUS und UEQ ausgeschlossen,
  um Platz für Argumentationsquellen zu schaffen. **Das war falsch** — Instrumentenbelege
  konkurrieren nicht mit Argumenten: Wer einen SUS-Score berichtet, *muss* Brooke zitieren,
  sonst ist es ein Formfehler. Aufgelöst, indem sie als eigene Kategorie ins Archiv wandern,
  mit der Bedingung „wird verpflichtend, sobald gemessen wird".
- **Offen / nächstes:** Unverändert der vorgelagerte Block aus Masterplan Kap. 23 —
  `MEMORY_MODE`-Schalter, Regressionstest, sauberer Monolith-Baseline-Lauf. Der erste Eintrag
  mit `Lauf-Metadaten` wird BA-009 oder später; er eröffnet K7 im Register.

---

### [BA-009] 2026-08-18 — Konzeptionelle Grundlagen geklärt, Pilotphase aufgenommen
- **Status:** done (Dokumentation; **kein** Code)
- **Kapitelbezug:** K4, K5, K8, K9
- **Literatur:** L02 (Trace-Darstellung), L09 (Formatsensitivität als Grund gegen Regelwerk-Umbau)
- **Changed files:** `docs/BA_MASTERPLAN.md`, `CLAUDE.md`,
  `.github/instructions/instructions.md`, `docs/BA_PROJECT_LOG.md`
- **Was getan wurde:** Ein längeres Klärungsgespräch über die Frage „was genau verwandeln wir
  eigentlich in Graphen?" hat vier Lücken im Plan sichtbar gemacht. Alle vier sind jetzt
  dokumentiert. **Der Inhalt dieses Eintrags ist weitgehend der Stoff für Kapitel 4 der Arbeit.**

**1. Was „Graph" hier heisst — und was nicht (Masterplan Kap. 3.4–3.9, neu).**
Das Wort wird in drei unvereinbaren Bedeutungen benutzt; die Arbeit meint nur die dritte
(Programmablauf), nicht Datenstruktur und nicht Bild. **Keine der Daten wird zu einem Graphen** —
Snapshot bleibt JSON, Regelkarten bleiben Markdown, Datenbank bleibt SQLite. Zum Graphen wird der
**Ablauf**. Dazu aufgenommen: was ein Knoten konkret ist (eine Funktion `state -> state`), was eine
Kante ist, und die ehrliche Einordnung gegen den Vorwurf „Refactoring mit schönem Namen".

**2. Neun Knoten sind nicht neun LLM-Aufrufe (Kap. 3.6).**
Am Code geprüft (`grep -c "chat.completions.create"` über die neun Runtime-Skripte): **drei**
Knoten rufen das Modell — 2, 5 und 9. Genau so viele wie der Monolith heute. `identify_snapshot`,
`rulebook_loader`, `apply_correction`, `validate_snapshot`, `update_snapshot` enthalten **null**
LLM-Aufrufe. Ohne diese Klarstellung im Methodenteil entsteht der Verdacht, der Vergleich messe
Aufwand statt Struktur.

**3. Der Zustand existiert bereits — er liegt verstreut (Kap. 3.7).**
Ein realer Iterationsordner (`data/snapshots/<id>/iteration-1/`) enthält heute schon die Ausgänge
der Knoten 2, 3, 5 und 7 als vier getrennte JSON-Dateien. Er ist nur untypisiert, ohne Reihenfolge,
ohne Zeitstempel — **und eines fehlt ganz: welche Regelkarten geladen wurden.** Das steht nur als
`print()` in `generate_correction_llm.py:875` und verschwindet im stdout des Subprozesses.
Der `GraphState` ist dieselbe Information in einem Objekt. **Das ist das stärkste Argument gegen
den Strohmann-Vorwurf** und gehört wörtlich in Kapitel 4.

**4. Provenienz statt Regelwerk-Umbau (Kap. 7.3, neu) — die Frage, bei der ich widersprochen habe.**
Frage war, ob nicht auch Regelwerk und entscheidungsrelevante Daten in Graphen umzuwandeln seien,
um später gezielt Regeln optimieren zu können. **Das Ziel ist berechtigt** — Befund D aus
`BEFUNDE_UND_LEHREN.md` belegt es: ein Vorschlag berief sich auf Artikel „aus Department 20100",
alle drei zitierten lagen in 20200. **Der Weg wäre aber falsch:** Was gebraucht wird, ist
Provenienz (zwei Felder im Zustand: `matched_rules`, `extracted_context`), kein Regelwerk-Graph.
**Die Falle, die das entschieden hat:** Das Regelwerk ist eine **Kontrollbedingung**. Karten
umzubauen wäre ein *dritter* Unterschied zwischen den Varianten neben Architektur und
`RULEBOOK_MODE` — und Karten zu editieren ändert den Text, den das Modell liest (L09: bis zu
76 Punkte Unterschied durch **bedeutungserhaltende** Formatänderungen).
**Entscheidung:** Kartenebene protokollieren, Regelwerk nicht anfassen. Regel-IDs nur ins
Frontmatter und nur mit Byte-Gleichheitsnachweis des injizierten Prompts.
**Offener Teilaspekt:** `AP7-0_rule_inventory.md` führt 22 Regel-IDs (R1–R22), aber nur **4 von 14**
Kartendateien verweisen darauf. Ob Kartenebene für die Optimierungsabsicht reicht, entscheidet
sich am ersten Trace — `density-values.md` allein enthält auf 99 Zeilen mindestens fünf
unterscheidbare Regeln.

**5. Die Pilotphase (Kap. 8.3, neu) — vom Nutzer vorgeschlagen, aufgenommen.**
Vorschlag war, vor der Messung ~10 Läufe zu fahren und parallel die Regeln zu optimieren.
**Das ist zulässig und gute Praxis** — Regel 5 verbietet Änderungen *während* und *nach* der
Messung, davor ist es Entwicklung. Drei Dinge musste ich ergänzen:
  * **Die Überanpassungsfalle:** Wer auf den 17 Messfällen optimiert, trainiert auf die
    Testmenge. Pilotfälle brauchen **andere Snapshots UND andere Entitäten** (letzteres wegen
    des objektbezogenen Gedächtnisses). Faustregel im Plan: *Ein Snapshot, den die Pilotphase
    gesehen hat, ist als Messfall verbrannt.*
  * **Ein kontraintuitiver Nebeneffekt:** Die Pilotphase lässt den Graphen in der Messung
    **schwächer** aussehen, weil sie seinen Hauptnutzen vorab erntet — behobene Regeldefekte
    helfen danach *beiden* Varianten. Kein Grund, es zu lassen, aber es gehört als Satz nach
    Kapitel 8: der gemessene Unterschied ist dadurch **konservativ**.
  * **Eigene Protokollkategorie `Status: pilot`** — Pilotläufe sind nie Ergebnisse.
Der Ertrag ist Kapitel 9 (F9): die Optimierungsschleife nach der Hauptmessung an 1–2 Fällen
demonstrieren, als Nachmessung gekennzeichnet. Das belegt UF3 **praktisch** statt nur strukturell.

**6. Visualisierung, State-Tracking, Debuggen (Kap. 12.5, neu).**
Vier Darstellungen, drei davon geschenkt (Mermaid aus dem kompilierten Graphen, Zustand je Knoten,
Checkpointing zum Wiederabspielen). Die vierte — die **lesbare Trace-Kette** nach MindMap-Vorbild
(L02) — ist selbst zu bauen und das wertvollste Artefakt: Debugging-Werkzeug, Kapitel-7-Abbildung
und das Objekt, an dem der Nachvollziehbarkeitsunterschied gezeigt wird.
Dazu die konkrete Debugging-Gegenüberstellung an einem **realen** Fehler (Muster 1 aus
`BEFUNDE_UND_LEHREN.md`) — das ist die Messvorschrift für UF3, kein Gefühl.
**Warnung aufgenommen:** externe Tracing-Dienste (LangSmith u. Ä.) senden Prompts und Daten an
Dritte. Bei Smart-Planning-Snapshots eine Datenschutzfrage, keine Komfortfrage. Lokales Tracing
genügt.

**7. Wann die Knotenzahl bindend wird (Kap. 9.1, neu).** Drei Zeitpunkte: jetzt Arbeitshypothese,
nach dem Durchstich echter Entscheidungspunkt, **vor dem ersten gemessenen Graph-Lauf einfrieren**.
- **Verifikation:** Alle Aussagen am Code belegt, nicht behauptet — LLM-Aufrufzählung über die
  neun Skripte, Iterationsordner-Inhalt an einem echten Snapshot, Kartengrössen
  (`wc -l app/skills/*.md`: 25–349 Zeilen), Regel-IDs im Inventar (22 Stück, 4 Karten verweisen
  darauf). `instructions.md` neu aus `CLAUDE.md` abgeleitet, `diff` leer.
- **Was NICHT funktioniert hat:** Nichts gebaut, daher keine Sackgasse. Aber ein Denkfehler von
  mir ist korrigiert worden: Ich hatte die Optimierungsschleife zunächst pauschal als Verstoss
  gegen Regel 5 eingeordnet. Falsch — Regel 5 betrifft Änderungen **während und nach** der
  Messung. Eine vorgelagerte Kalibrierungsphase ist zulässig; sie braucht nur einen definierten
  Einfrierzeitpunkt und getrennte Fälle. Der Vorschlag des Nutzers war besser als meine erste
  Einordnung.
- **Offen / nächstes:** Unverändert — `MEMORY_MODE`, Regressionstest, Baseline-Lauf. Neu in der
  Checkliste zwischen Durchstich und Messung: Pilotfälle bauen, kalibrieren, **einfrieren**.

---

### [BA-010] 2026-08-18 — Arbeitspakete angelegt, Reihenfolgefehler korrigiert
- **Status:** done (Planung; **kein** Code)
- **Kapitelbezug:** K5
- **Literatur:** —
- **Changed files:** `docs/BA_ARBEITSPAKETE.md` (neu), `docs/BA_MASTERPLAN.md` (Kap. 23),
  `CLAUDE.md`, `.github/instructions/instructions.md`, `docs/BA_PROJECT_LOG.md`
- **Was getan wurde:** Die Umsetzung als abhakbare Spur dokumentiert —
  **AP-A bis AP-I plus AP-X** (Menschen, parallel), je mit Teilpaketen, Abhängigkeiten, Aufwand
  und **DoD**. Bisher existierte nur die fachliche Checkliste in Masterplan Kap. 23; die
  Blockstruktur mit Aufwandsschätzung lebte allein im Gespräch.
- **Der korrigierte Fehler — er war ein echter Konfundierungsfehler:** Meine Blockreihenfolge
  vom Vortag hatte den **Baseline-Lauf vor der `langgraph`-Installation**. Das ist falsch.
  `langgraph` zieht `langchain-core`, das eigene `pydantic`-Anforderungen hat — und `pydantic`
  liegt über `correction_models.py` **im gemessenen Pfad** (Schemaprüfung, Knoten 6). Baseline
  vor und Graph nach der Installation hiesse: beide Varianten unter **verschiedenen
  Bibliotheksversionen**, also genau der konfundierende Faktor, den Kap. 7 ausschliesst.
  **Neue Regel: erst Umgebung einfrieren, dann messen** — auch wenn die Installation scheitert
  und auf den Zustandsautomaten zurückgefallen wird, muss das **vor** der Baseline geklärt sein.
  Masterplan Kap. 23 trägt die Korrektur jetzt als eigenen Kasten, damit sie nachvollziehbar ist
  und nicht still verschwindet.
- **Aufwandsschätzung, ausdrücklich als Schätzung:** ~20 Arbeitstage technisch (A 1,5 · B 1 ·
  C 0,5 · D 4–5 · E 2 · F 2 · G 3 · H 4 · I 3). Bei 28 Kalendertagen bis zum 15.09. ist das
  vollständig ausgelastet; AP-X läuft daneben und ist nicht durch Fleiss beschleunigbar.
  **Risikoposten ist AP-A2/A2.4** (Abhängigkeitsauflösung) und **AP-D7**
  (`identify_snapshot.py`, ~300 Zeilen Ablaufsteuerung in `main()`).
- **Verifikation:** `check_doku_links.py` — null defekte Verweise in den BA-Dokumenten.
  `instructions.md` neu aus `CLAUDE.md` abgeleitet. Die sechs offenen Entscheidungen sind in
  `BA_ARBEITSPAKETE.md` in einer eigenen Tabelle mit Fälligkeitspaket sichtbar gehalten, damit
  keine still getroffen wird.
- **Was NICHT funktioniert hat:** Der Reihenfolgefehler oben — er stand zwei Tage in der
  Checkliste und wäre bei sequenzieller Abarbeitung erst am Messtag aufgefallen, also zu spät.
  Aufgefallen ist er nur, weil nach den zu installierenden Paketen gefragt wurde. Lehre: Eine
  Checkliste in „Umsetzungsreihenfolge" prüft man **gegen die Kontrollbedingungen**, nicht nur
  gegen die fachliche Logik.
- **Offen / nächstes:** **AP-A1** — `MEMORY_MODE`-Schalter. Klein, risikoarm, blockiert alles
  Weitere. Direkt danach **AP-A2**, weil dort das Terminrisiko sitzt.

---

### [BA-011] 2026-08-19 — AP-0 Vorbedingungen: venv angelegt, drei Befunde
- **Status:** partial — 0.1, 0.2, 0.4 erledigt; **0.3.1 blockiert** (siehe unten)
- **Kapitelbezug:** K5 *(Reproduzierbarkeit, Kontrollbedingungen)*
- **Literatur:** L13 *(Baltes: „Report model versions, configurations" — erfüllt, siehe unten)*
- **Changed files:** `.venv/` (neu, gitignored),
  `data/archive/ba-ap0-20260819/` (neu: Sicherungen)

**Was getan wurde.** AP-0 abgearbeitet: Rücksprungpunkte gesichert, virtuelle Umgebung angelegt,
Erreichbarkeit geprüft. **Kein Code geändert** — bis hierher nur Umgebung.

**Verifikation und Belege:**
* **0.2 Sicherungen** unter `data/archive/ba-ap0-20260819/`: `pip freeze` des System-Python,
  Kopie von `pt4.sqlite3` (**Gegenprobe: 20 `memory_items` in Original und Kopie**),
  Umgebungsnotiz. Git-Stand war sauber (0 geänderte Dateien, Commit `3ed63bf`).
* **0.1 venv** unter `.venv/`, Python 3.13.3, `sys.prefix != sys.base_prefix` bestätigt.
  `pip install -r app/deploy/requirements.txt` durchgelaufen, **`pip check`: keine gebrochenen
  Abhängigkeiten**. Alle neun Kernmodule importierbar (`core.*`, `agents.*`, `memory.retrieval`,
  `db.models`) sowie die drei LLM-Runtime-Skripte.
* **0.4 Referenzfall:** **I03** (Dichte, `articles[0].relDensityMin`, Ground Truth `1.017`).

**Befund 1 — es gab nie eine funktionierende Projektumgebung.**
Der System-Python (`C:\Program Files\Python313`, 106 Pakete) enthält `openai`, `pydantic` und
`azure-storage-blob`, aber **weder `sqlalchemy` noch `alembic`, `flask` oder `mcp`**. Damit konnte
die Anwendung dort nie vollständig laufen — die Pakete stammen aus vereinzelten Ad-hoc-Installationen.
**Konsequenz:** Die venv ist die **erste** vollständige Umgebung des Projekts.
*Vermutung, nicht belegt:* Die Eval-Läufe vom 31.07. liefen anderswo (Docker oder anderer Rechner).
**Das ist ein weiterer Grund, warum `pt4-eval-results.json` nicht als Baseline taugt** — die
Umgebung jener Läufe ist nicht rekonstruierbar. Ergänzt den bereits bekannten Mangel fehlender
Lauf-Metadaten (BA-004).

**Befund 2 — der „Abhängigkeitskonflikt" aus AP-A2.1 löst sich auf.**
| Paket | venv | System-Python |
|---|---|---|
| `openai` | **1.109.1** | 2.14.0 |
| `pydantic` | **2.13.4** | 2.12.4 |

Die venv respektiert den Pin `openai>=1.6.0,<2.0.0` aus `app/deploy/requirements.txt`; der
System-Python war auf 2.14.0 **abgedriftet**, ohne je die Projektumgebung gewesen zu sein.
**Entscheidung: Pin bleibt, die venv ist massgeblich** — sie entspricht dem, was auch das
Container-Image baut. Der Code importiert und läuft unter 1.109.1 nachweislich.
**AP-A2.1 ist damit erledigt**, ohne dass etwas geändert werden musste.

**Befund 3 — die exakte Modellversion ist jetzt bekannt (für Kap. 17 verpflichtend).**
Minimalaufruf gegen Azure OpenAI erfolgreich: Deployment `gpt-4.1` antwortet als
**`gpt-4.1-2025-04-14`** (14 Prompt- + 2 Completion-Token). Bisher stand im Plan nur
„`gpt-4.1`" — **die konkrete Modellversion gehört ins Reproduzierbarkeitsprotokoll** und ist
genau das, was L13 (Baltes et al., Leitlinie 2) verlangt.

- **Was NICHT funktioniert hat — BLOCKER für AP-B:**
  Die **Smart-Planning-Testinstanz ist nicht erreichbar**.
  `vm-t-weu-ccadmm-idp-test02.internal.idp.cca-dev.com` löst nicht auf
  (`getaddrinfo failed`, Errno 11002). **Es ist kein Zugangsdaten-, sondern ein Netzproblem** —
  der Host liegt unter `.internal.idp.cca-dev.com`, also im Firmennetz. Vermutlich fehlt VPN.
  **Betroffen:** alles, was validiert, herunterlädt oder hochlädt — also AP-A3.1 (Smoke-Test),
  AP-B (Baseline) und der Katalogbau. **Nicht betroffen:** AP-A1 (`MEMORY_MODE`), AP-A2
  (Pakete), AP-C bis AP-E (Knoten und Graph bauen) — die brauchen die Instanz nicht.
  **Genau dafür war AP-0.3 da:** Scheitert später ein Lauf, ist jetzt belegt, dass es nicht am
  Code liegt.
- **Offen / nächstes:** **AP-A1** (`MEMORY_MODE`-Schalter) — vom Blocker unberührt.
  Parallel: VPN-Zugang klären, damit AP-A3.1 und AP-B laufen können.
  *(Nachtrag 19.08. nachmittags: Testinstanz erreichbar, DNS 10.112.19.8, `authenticate()` liefert
  Token — der Blocker ist aufgelöst.)*

---

### [BA-012] 2026-08-19 — AP-A abgeschlossen: MEMORY_MODE, LangGraph installiert, Smoke-Test grün
- **Status:** done
- **Kapitelbezug:** K4 *(Schaltermuster)*, K5 *(Kontrollbedingungen, Reproduzierbarkeit)*
- **Literatur:** L13 *(Baltes, Leitlinie 2: Modellversionen und Konfiguration berichten)*
- **Changed files:** `app/core/agent_config.py`, `app/memory/retrieval.py`,
  `app/deploy/requirements.txt`, `data/archive/ba-ap0-20260819/` (zwei weitere pip-freeze-Stände)

**A1 — `MEMORY_MODE`-Schalter.** Abweichend vom Arbeitspaket **an EINER statt an drei Stellen**
umgesetzt: der Guard sitzt in `memory/retrieval.find_similar_cases()`. Grund: Alle drei
Verbraucher degradieren bei leerer Fallliste bereits von selbst neutral
(`same_entity_confirmed_value([])` → `None`, `compute_memory_support(v, [])` → `0.0`,
`format_cases_for_prompt([])` → Neutralsatz). Damit folgt der Schalter exakt dem
`RULEBOOK_MODE`-Muster — **ein** Env-Var, **eine** verzweigende Stelle, alle Aufrufer unwissend —
und **`generate_correction_llm.py` (1085 Zeilen) blieb unangetastet**. Weniger Diff, weniger Risiko.

**Gegenprobe gegen die echte Datenbank**, Fall I03 (`articles:100005`, `relDensityMin`):

| `MEMORY_MODE` | Fälle | Override | `memory_support` (Wert 1.017) |
|---|---|---|---|
| `on` | 2 | **1.017** | 1.0 |
| `off` | 0 | — | 0.0 |
| *(nicht gesetzt)* | 2 | 1.017 | — |

**Das ist der dokumentierte Konfundierungsfaktor in Aktion:** Mit `on` bekommt das Modell die
Ground Truth von I03 (`1.017`) deterministisch vorgesetzt. Default bleibt `on`, Produktion
also unverändert.

**A2 — Abhängigkeiten.** Der im Plan seit dem 16.08. geführte „Konflikt" **war keiner**: Die venv
respektiert den Pin `openai<2.0.0` (→ 1.109.1); der System-Python war auf 2.14.0 abgedriftet, ohne
je die Projektumgebung gewesen zu sein (BA-011). **Nichts geändert.**
PyPI abgefragt statt geschätzt: `langgraph==1.2.11` (11.08.2026), `langchain-core==1.5.6`
(17.08.2026), beide `requires_python >=3.10` → 3.13.3 passt. Installiert und in
`requirements.txt` gepinnt, mit Kommentar zur Verwendungsgrenze.

**Der befürchtete `pydantic`-Konflikt trat nicht ein** — Gegenprobe über `pip freeze` vor und nach
der Installation:

| Paket | vorher | nachher |
|---|---|---|
| `openai` | 1.109.1 | **1.109.1** |
| `pydantic` | 2.13.4 | **2.13.4** |

`pip check` sauber, 7/7 Kernmodule und 3/3 LLM-Runtime-Skripte weiterhin importierbar,
`StateGraph` importierbar. **Damit ist der Rückfall auf den Zustandsautomaten (Kap. 5.1) vom
Tisch — LangGraph bleibt.**

**Datenschutz geprüft:** `langsmith 0.11.0` kam als Transitivabhängigkeit mit. Es ist **nicht
scharf** — keine der Variablen `LANGSMITH_TRACING`, `LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`,
`LANGSMITH_API_KEY`, `LANGCHAIN_ENDPOINT` ist gesetzt. Der Hinweis steht als Kommentar in
`requirements.txt`, damit es niemand versehentlich aktiviert (Masterplan Kap. 12.5).

**A3 — Smoke-Test, grün.** Snapshot `194f58de-8fe3-41ff-96d2-6f8f2af4c502`
(`[validate_demand_article_ids]`), `MEMORY_MODE=off`, `RULEBOOK_MODE=monolith`:
* `identify_error_llm` → LLM-Aufruf ok, `iteration-2` geschrieben, Suche mit `results_count=1`
* `generate_correction_llm` → Regelwerk **34.899 Zeichen im `monolith`-Modus** geladen,
  **„Memory: 0 Fälle"** (der Schalter greift im echten Lauf), Vorschlag
  `demands[0].articleId = 100005` — **das ist die Ground Truth von Fall I02** —
  `value_grounded=1.0`, `memory_support=0.0`, Konfidenz `0.8 = 0.5*1.0 + 0.3*1.0 + 0.2*0.0`
* **Tokenverbrauch gemessen: prompt=14.590, completion=266, Kosten 0,0313 $.** Die im Plan aus
  PT4 übernommene Angabe „rund 55.000 Token pro Lauf" gilt **nicht allgemein** — sie hing am
  damaligen Fall. Für die Aufwandsplanung von AP-B ist 14,6k der realistischere Anker für
  einfache Fälle.

- **Verifikation der Nebenwirkungen:** DB-Vergleich gegen die Sicherung von heute früh —
  `memory_items` **20 → 20 unverändert** (die Messgrundlage ist unberührt; sie wächst nur durch
  menschliche Review-Entscheidungen), `proposals` 26 → 27 und `agent_runs` 180 → 181 durch den
  Smoke-Test. `reviews` unverändert.
- **Was NICHT funktioniert hat / bewusst anders gemacht:**
  * **Erster Snapshot-Kandidat verworfen.** `509dd21a…` (der I03-Referenzfall aus AP-0.4) meldet
    auf dem Server **0 Fehler** — er wurde im damaligen Lauf korrigiert. Als Smoke-Test-Fall
    unbrauchbar; stattdessen ein lokaler Snapshot mit gespeichertem ERROR gewählt.
    **Konsequenz für AP-B:** Der Referenzfall I03 muss für den Baseline-Lauf **neu erzeugt**
    werden, er lässt sich nicht wiederverwenden.
  * **Kein `full_correction` gefahren**, obwohl das Arbeitspaket es so nannte. `apply_correction`
    und `update_snapshot` schreiben auf die Testinstanz; für den Nachweis „die Umgebung trägt"
    genügen die beiden LLM-Schritte. Bewusste Abweichung, hier vermerkt statt still getroffen.
  * `HUMAN_IN_THE_LOOP=false` für den Smoke-Test gesetzt, um die Sperre gegen doppelte offene
    Vorschläge zu umgehen. Für Messläufe ist die Behandlung noch festzulegen — sie muss in
    **beiden** Varianten gleich sein (Kap. 7.1).
- **Offen / nächstes:** **AP-B** (Monolith-Baseline) ist jetzt freigegeben — Umgebung final und
  dokumentiert. Erster Schritt dort: Referenzfall I03 neu erzeugen (siehe oben), dann B1
  Regressionstest.

---

### [BA-013] 2026-08-19 — MEMORY_MODE gehärtet · AP-B1 Regressionstest bestanden
- **Status:** done (A1-Nachbesserung + AP-B1); AP-B2/B3 offen
- **Kapitelbezug:** K5 *(Kontrollbedingungen, Regressionstest)*, K7 *(erster Messwert unter
  Baseline-Bedingungen)*, K8 *(Instrumentenrisiken)*
- **Literatur:** L13 *(Baltes: Konfiguration berichten)*
- **Changed files:** `app/core/agent_config.py`, `app/eval/run_isolated_suite.py`,
  `data/archive/ba-ap0-20260819/` (drei weitere Sicherungen + B1-Ergebnis)

**1. `MEMORY_MODE` gehärtet — meine eigene Umsetzung von heute früh war gefährlich.**
Die erste Fassung prüfte auf die Zeichenfolge `"off"`. Getestet mit zehn Werten: `false`, `0`,
`no`, `disabled`, `aus` und jeder Tippfehler liessen das Gedächtnis **still eingeschaltet**.
Man hält es für aus, die Baseline ist kontaminiert, und **nichts sagt es**. Dieselbe Klasse wie
Muster 1 aus `04_PT4/BEFUNDE_UND_LEHREN.md`.
Jetzt: `on|true|1|yes` bzw. `off|false|0|no`, Gross-/Kleinschreibung und Leerzeichen egal —
**jeder andere Wert bricht beim Start hart ab**. Nachgeprüft über 13 Eingaben. Default (Variable
nicht gesetzt) bleibt `on`, Produktion unverändert.

> **Gleiches Risiko bei `RULEBOOK_MODE`, noch NICHT behoben** (Befund, nicht geändert):
> `RULEBOOK_MODE=card` — ein fehlendes „s" — liefert still den **Monolithen** (34.899 statt
> 23.761 Zeichen). Für die Baseline harmlos (Zielrichtung stimmt zufällig), **für die
> Graph-Läufe nicht**: dort ist `cards` beabsichtigt, und ein Tippfehler würde unbemerkt die
> falsche Variante messen. **Vor AP-E zu härten.**

**2. Zwei Verdrahtungen in `run_isolated_suite.py` gelöst — beide additiv, Defaults unverändert.**
* Die Modi waren fest auf `cards` genagelt; damit war der Harness für die Monolith-Baseline
  unbrauchbar. Jetzt aus der Umgebung übernehmbar, Default weiterhin `cards`/`on`.
* **Beinahe-Datenverlust abgefangen:** Die Ergebnisdatei war fest auf `pt4-eval-results.json`
  verdrahtet — ein Lauf mit `--only I03` hätte den **PT4-Nachweis mit einer einzigen Zeile
  überschrieben**, unwiederbringlich, weil `data/` nicht unter Versionskontrolle steht. Vor dem
  Lauf gesichert (`pt4-eval-results.json.bak`, 10 Fälle gegengeprüft; ebenso
  `pt4-combined-results.json.bak`), danach `--out` ergänzt.

**3. AP-B1 Regressionstest — bestanden, keine Abweichung.**
Fall **I03** frisch auf der Testinstanz erzeugt (Snapshot `d14634a2-e200-4edc-b38e-b62e6791e4e9`),
gefahren unter Baseline-Bedingungen.

- **Lauf-Metadaten:** Variante `monolith` · `RULEBOOK_MODE=monolith` (34.899 Zeichen Regelwerk,
  SHA-256 `a3c14bd1b66cc1e3…`) · `MEMORY_MODE=off` · `HUMAN_IN_THE_LOOP` nicht gesetzt (Default
  `true`; die Sperre greift nicht, weil der Snapshot neu ist) · Modell `gpt-4.1`, konkret
  **`gpt-4.1-2025-04-14`**, API `2025-01-01-preview`, `temperature=0.3` · Fall-ID I03 ·
  1 Wiederholung · 2026-08-19 · Rohdaten
  `data/archive/ba-ap0-20260819/B1-regressionstest-I03.json` und
  `data/snapshots/d14634a2-e200-4edc-b38e-b62e6791e4e9/`

| Kriterium | PT4 31.07. (`cards`, Gedächtnis an) | B1 19.08. (`monolith`, Gedächtnis aus) |
|---|---|---|
| erkannt | ja | ja |
| Feld richtig | ja | ja |
| **Wert exakt** | **nein** | **nein** |
| `target_path` | `articles[0].relDensityMin` | identisch |
| Vorschlag | **1.14** | **1.14** |
| Ground Truth | 1.017 | 1.017 |

**Ergebnis: identisch.** Trotz anderer `openai`-Version, anderer Umgebung, anderem
Regelwerk-Modus und abgeschaltetem Gedächtnis schlägt das Modell denselben Wert vor.
**Damit ist der Modell-/Umgebungseffekt für diesen Fall ausgeschlossen** — was später an
Unterschieden auftaucht, ist nicht der Umzug in die venv.

**Beleg, dass der Schalter auch im vollen Lauf greift:** Der gespeicherte Vorschlag trägt
`memory_support=0.0`, `value_source=llm`, Konfidenz 0,75. Wäre das Gedächtnis an gewesen, hätte
der Override `1.017` erzwungen (der Eintrag für `articles:100005` existiert seit 31.07.) und
`value_ok` wäre `true` — der Fall gälte fälschlich als gelöst.

- **Was NICHT funktioniert hat:** Der ursprünglich als Referenz vorgesehene Snapshot
  `509dd21a…` war unbrauchbar (0 Fehler auf dem Server, damals korrigiert). Deshalb neu erzeugt.
  Ausserdem hätte mich der fest verdrahtete Ausgabepfad beinahe den PT4-Nachweis gekostet —
  gefunden, weil ich vor dem Lauf nachgesehen habe, wohin geschrieben wird, statt es laufen zu
  lassen.
- **Offen / nächstes:** **AP-B2** — der eigentliche Baseline-Lauf über alle Fälle. Vorher zu
  klären: (a) Behandlung von `HUMAN_IN_THE_LOOP` für Messläufe, in beiden Varianten gleich;
  (b) ob der Protokollumfang nach Kap. 17 (voller Prompt/Hash, volle Antwort) im Harness ergänzt
  wird — aktuell schreibt er nur die fünf Kriterien.
  *(Überholt durch BA-014: AP-B wird zur Regressionsreferenz, die Messung wandert nach AP-H.)*

---

### [BA-014] 2026-08-19 — Externe Begutachtung eingearbeitet: Dreiarm-Design A/B/C
- **Status:** done (Planung und Dokumentation; **kein** Code)
- **Kapitelbezug:** K4, K5, K6, K7, K8
- **Literatur:** L12 *(faithfulness graduell statt binär)*, L16 *(Kontext der Forschungslücke)*
- **Changed files:** `docs/BA_MASTERPLAN.md`, `docs/BA_ARBEITSPAKETE.md`,
  `docs/BA_LITERATUR.md`, `CLAUDE.md`, `.github/instructions/instructions.md`

**Anlass.** Externes Feedback zum Plan. Ich habe **jede überprüfbare Behauptung** gegen Code und
Dokumente geprüft — **sieben von sieben trafen zu**, zwei davon deckten Selbstwidersprüche auf,
die ich selbst eingebaut hatte. Der Nutzer hat daraus ein Dreiarm-Design entwickelt, das den
Kern des Problems besser löst als beide Varianten, die ich vorgeschlagen hatte.

**Die zentrale Änderung: zwei Architekturen, drei Messbedingungen** (Masterplan Kap. 7.1)

| | Bedingung | `RULEBOOK_MODE` | Rolle |
|---|---|---|---|
| **A** | Monolith-Pipeline | `monolith` | Ausgangszustand (bis 12.07.2026) |
| **B** | Monolith-Pipeline | `cards` | **realer Ist-Zustand**, Kontrollarm |
| **C** | Graph | `cards` | neue Gesamtarchitektur |

Hauptvergleich **A gegen C** (die zwei Architekturen des Exposés), Kontrollarm **B über alle
17 Fälle** — auf Wunsch des Nutzers vollständig statt auf der von mir vorgeschlagenen
Divergenz-Teilmenge. **Seine Version ist besser:** die Teilmenge hätte kaum Zeit gespart
(17 Läufe ≈ 40 min, ~0,50 $), aber im Text eine Teilmengen-Einschränkung erzwungen.

**Was das löst:**
1. **Attribution** — der Beitrag der selektiven Regelauswahl ist jetzt messbar statt eingeräumt.
2. **Der Strohmann-Vorwurf entfällt beweisbar.** Verifiziert: `app/.env` setzt `RULEBOOK_MODE`
   nicht, der Code-Default ist `cards`, und `infra/variables.tf:386` hat `default = "cards"`,
   in `terraform.tfvars` **nicht überschrieben**. → **Produktiv läuft `cards` seit 12.07.2026.**
   Damit war die bisherige Planung sachlich falsch: `RULEBOOK_MODE=monolith` als „realer
   Ist-Zustand" zu bezeichnen verstiess gegen **Regel 2**. Mit B liegt der echte Ist-Zustand
   im Vergleich.
3. **Exposé-Konformität** — am PDF geprüft: „Der Vergleich beschränkt sich auf **zwei konkrete
   Systemarchitekturen**". A und C sind diese zwei; B ist keine dritte Architektur, sondern
   dieselbe wie A mit anderer Regelquelle. Formulierung: „zwei Architekturen, drei
   Messbedingungen".

**Fünf weitere Korrekturen, alle aus dem Feedback:**

* **Kap. 7.1 widersprach sich selbst.** Eine Zeile nannte `RULEBOOK_MODE` als variiert, die
  nächste `SP_ARCHITECTURE_MODE` als „den einzigen bewusst variierten Faktor". Behoben, mit
  Kasten, der den alten Fehler benennt statt ihn zu verschweigen.
* **AP-B war als „die Zahl, gegen die alles Weitere verglichen wird" definiert** — obwohl AP-G
  danach das Regelwerk optimiert. **Konstruktionsfehler.** AP-B ist jetzt **Regressionsreferenz**
  („läuft das System noch wie vorher?"), auf 4–5 Fälle verkürzt; die Zahlen für Kapitel 7
  entstehen ausschliesslich in **AP-H nach dem Einfrieren**, für alle drei Bedingungen gemeinsam.
  **Spart Zeit.**
* **UF3 durfte nicht über „Graph hat Trace, Monolith nicht" gemessen werden** — das wäre durch
  die Konstruktion vorweggenommen **und sachlich falsch** (Kap. 3.7 listet die maschinellen
  Artefakte des Monolithen auf). Neue Messvorschrift mit vier Grössen: korrekte Lokalisierung,
  Rekonstruierbarkeit, **Anzahl zusammenzusuchender Artefakte**, Experten-Rating.
  **Der Graph kann dabei verlieren** — das ist der Punkt. Dazu die Frage „**wer** lokalisiert?":
  nicht der Autor, sonst Bewerter-Bias.
* **Halluzinationskategorien: „entsteht" ≠ „wird beobachtbar".** Strukturelle Halluzination
  *entsteht* in Knoten 5 und wird in Knoten 6 *erkannt*. Kategorie 3 braucht sogar **zwei**
  Zustände (Knoten 4 belegt die geladenen Karten, Knoten 5 macht die Behauptung). Spalte auf
  „Beobachtungspunkt" umgestellt — mein „ein Knoten pro Kategorie" war zu einfach gedacht.
* **Statusehrlichkeit in den Arbeitspaketen.** AP-0 stand auf ☑, obwohl 0.1.3 und 0.3.3 offen
  waren, und die DoD von 0.1.3 verlangte einen `full_correction`-Lauf, den ich bewusst nicht
  gefahren hatte. **DoD geändert und begründet**, statt sie stillschweigend zu unterlaufen.
  Ausserdem: `D3` → `D7` im Risiko-Kasten, A3.3 als gegenstandslos geschlossen, HitL-Blocker
  von H1 nach **B0** vorgezogen (schon die Regressionsreferenz braucht dieselbe Behandlung).

**Zwei statistische Präzisierungen:**
* **Wiederholungen sind keine zusätzlichen Fälle.** 5 × 17 ist **nicht n=85** — es bleiben
  17 Fälle plus Within-Case-Stabilität. Wer sie mitzählt, überschätzt die Aussagekraft um das
  Fünffache. **Absolute Zahlen berichten** („5 von 17"), nicht Prozente.
* **Cohens κ ist hier vermutlich das falsche Mass** — es ist für **zwei** Rater und **nominale**
  Daten gebaut; hier stehen 3–4 Personen auf einer **ordinalen** 1–5-Skala. Passend wären
  Fleiss' κ, gewichtetes κ oder **Krippendorffs α**. Festzulegen, sobald das Raster steht.

- **Was NICHT funktioniert hat — eigene Fehler, benannt:**
  * Die beiden Selbstwidersprüche (Kap. 7.1, AP-B) stammen von mir und standen seit dem 16.08.
    im Plan. Aufgefallen sind sie erst durch fremde Prüfung — ein Hinweis darauf, dass mein
    eigenes Gegenlesen hier nicht gereicht hat.
  * **Überreichweite in `BA_LITERATUR.md`:** Ich hatte behauptet, es existiere **keine**
    begutachtete Literatur zur LLM-gestützten Korrektur strukturierter Planungsdaten. Grundlage
    waren **acht Websuchen** — das ist eine explorative, keine systematische Recherche. Die
    Behauptung ist auf die belegbare Fassung abgeschwächt; ein Suchprotokoll (Datenbanken,
    Strings, Datum, Kriterien) ist als Aufgabe vor der Abgabe vermerkt.
  * **Falsche Aussage korrigiert:** „Der Monolith hat nur die Selbstauskunft" widersprach meinem
    eigenen Masterplan Kap. 3.7. Richtig: Ihm fehlen **Regelprovenienz, Reihenfolge, Zeitstempel
    und Zusammenhang** — der Unterschied ist **graduell, nicht binär**, was ohnehin besser zu
    L12 passt.
  * Meine Idee, B nur auf der Divergenz-Teilmenge zu fahren, war eine Optimierung ohne Nutzen.
    Verworfen.
- **Offen / nächstes:** **AP-B0** — `HUMAN_IN_THE_LOOP`-Behandlung für Messläufe festlegen und
  den `open_proposal_blocking()`-Blocker lösen. Danach die verkürzte Regressionsreferenz (B2).
  Parallel weiterhin **AP-X** (Menschen).
  Noch offen und vor AP-E zu erledigen: **`RULEBOOK_MODE` härten** — `RULEBOOK_MODE=card`
  (Tippfehler) liefert still den Monolithen; für die Graph-Läufe wäre das die falsche Variante.

---

### [BA-015] 2026-08-19 — RULEBOOK_MODE gehärtet · HitL entschieden · AP-C fertig
- **Status:** done
- **Kapitelbezug:** K4 *(Schalter, GraphState)*, K5 *(Kontrollbedingungen)*
- **Literatur:** L11 *(Trace als Beobachtung, nicht Selbstauskunft — im `graph_state.py` verankert)*
- **Changed files:** `app/core/agent_config.py`, `app/agents/sp_agent.py`,
  `app/tools/smart-planning/graph/` (neu: `__init__.py`, `nodes/__init__.py`, `graph_state.py`),
  `docs/BA_ARBEITSPAKETE.md`

**1. `RULEBOOK_MODE` gehärtet.** Gleiches Muster wie `MEMORY_MODE`: nur `cards` und `monolith`
sind gültig, alles andere bricht beim Start ab. Vorher lieferte jeder Tippfehler still den
**Monolithen** (`rulebook_loader` verzweigt auf `!= "cards"`) — bei Bedingung C wäre damit
unbemerkt die falsche Variante gemessen worden. Über acht Eingaben geprüft: `cards`, `monolith`,
`MONOLITH`, `" Cards "` gültig; `card`, `monolit`, `tippfehler`, leer brechen ab.

**2. `HUMAN_IN_THE_LOOP` für Messläufe entschieden** *(Nutzerentscheidung 19.08.)*:
**`false` in allen drei Bedingungen A, B und C.** `apply_correction` bleibt funktionsfähig und
läuft mit — es wird für Kategorie 4 (Folgefehler, `errors_after`) gebraucht —, aber das
Review-Gate ist nicht Gegenstand des Vergleichs. Präzedenzfall aus PT4: `run_iterative.py`
verfährt seit jeher so. **Damit ist AP-B0.1 erledigt**; der `open_proposal_blocking()`-Blocker
(B0.2) wird gegenstandslos, weil die Sperre unter `HUMAN_IN_THE_LOOP=false` gar nicht greift —
belegt in `AGENTEN_ARCHITEKTUR.md` §4 („greift AUSSCHLIESSLICH bei `HUMAN_IN_THE_LOOP=true`").

**3. AP-C — Schalter und Gerüst.**
* `SP_ARCHITECTURE_MODE` in `agent_config.py`, Default `"monolith"`, strikt geparst
  (`grph` und leer brechen ab). `GRAPH_ENABLED_PIPELINES` daneben — bewusst in der Konfiguration
  und nicht im Agenten, damit alle Schalter an **einer** Stelle stehen.
* **Der einzige Verzweigungspunkt** am Anfang von `SPAgent.execute_pipeline()`. Er greift nur,
  wenn `graph` **und** eine Korrektur-Pipeline vorliegt; sonst fällt er durch und der bestehende
  Code läuft unverändert weiter.
* `_execute_pipeline_graph()` als **sauberer Stub**: gibt eine verständliche Meldung mit
  Handlungsanweisung zurück statt eines Stacktrace. Trägt bereits alle fünf Rückgabeschlüssel
  des Monolith-Pfads (Kap. 6.3).
* `graph/graph_state.py` mit **18 Feldern** und `new_state()`. Die Kommentare halten die
  Entscheidungen fest, damit sie nicht verloren gehen: Knoten 8 ist ein **Knoten, keine Kante**;
  `matched_rules` + `correction_proposal` sind **gemeinsam** der Beobachtungspunkt für
  Kategorie 3; `extracted_context` fängt Befund D ab.

- **Verifikation:**
  * **Regressionstest wiederholt** — Fall I03, `RULEBOOK_MODE=monolith`, `MEMORY_MODE=off`,
    frischer Snapshot `0f565afe…`. Gegen den Lauf vor AP-C (BA-013, `d14634a2…`): **0 Abweichungen**
    in allen sechs Kriterien (erkannt, Feld, Wert, `target_path`, Vorschlag 1.14, Ground Truth
    1.017). **Der Monolith-Pfad ist unverändert.**
  * Ohne gesetzte Variablen: `SP_ARCHITECTURE_MODE='monolith'`, alles wie zuvor — Produktion
    unberührt.
  * 8/8 Kernmodule importieren; `SP_ARCHITECTURE_MODE=graph` liefert `success=False` mit
    Klartextmeldung statt Absturz.
- **Lauf-Metadaten (Regressionslauf):** Bedingung A · `RULEBOOK_MODE=monolith` ·
  `MEMORY_MODE=off` · `HUMAN_IN_THE_LOOP=false` · `gpt-4.1-2025-04-14`, API `2025-01-01-preview`,
  `temperature=0.3` · Fall I03 · 1 Wiederholung · 2026-08-19 · Rohdaten
  `data/archive/ba-ap0-20260819/C-regression-nach-schalter-I03.json`
- **Was NICHT funktioniert hat:** Mein eigener Prüfausdruck stürzte mit `UnicodeEncodeError`
  ab — Häkchen-Zeichen auf einer cp1252-Konsole. **Exakt Muster 5 aus `BEFUNDE_UND_LEHREN.md`**,
  und zwar im selben Repository, das die Lehre dokumentiert. Ohne Sonderzeichen wiederholt.
  Kein Schaden, aber ein Beleg dafür, wie hartnäckig dieses Muster ist.
- **Offen / nächstes:** **AP-D** — Knotenextraktion. Reihenfolge nach Aufwand: D1 Knoten 6,
  D2 Knoten 5, D3 Knoten 7, D4 Knoten 4+8, D5 Knoten 9, D6 Knoten 2, **D7 Knoten 3 (der Brocken,
  ~300 Zeilen Ablaufsteuerung in `main()`)**. Der verkürzte Regressionslauf B2 kann jederzeit
  nebenher laufen — er ist nicht mehr auf dem kritischen Pfad.

---

### [BA-016] 2026-08-19 — AP-B abgeschlossen: B0 geprüft, B2 gefahren, B3 archiviert
- **Status:** done
- **Kapitelbezug:** K5 *(Kontrollbedingungen, Reproduzierbarkeit)*, K7 *(Regressionsreferenz)*,
  K8 *(die I10-Abweichung gehört in die Diskussion)*
- **Literatur:** L13 *(Baltes: Konfiguration und Traces berichten)*, L10 *(Streuung als Messobjekt)*
- **Changed files:** `app/eval/run_isolated_suite.py` (`--only` nimmt Komma-Listen),
  `data/archive/ba-baseline-artefakte-20260819/` (neu, 18 Dateien), `docs/BA_ARBEITSPAKETE.md`

**Anlass:** Der Nutzer hat bemerkt, dass B0, B2 und B3 noch offen waren, obwohl ich B0.1 als
entschieden *berichtet* hatte. Zu Recht — „done" muss etwas bedeuten.

**B0 — HitL, jetzt belegt statt behauptet.** Entscheidung: `HUMAN_IN_THE_LOOP=false` in allen drei
Bedingungen. Ich hatte behauptet, der `open_proposal_blocking()`-Blocker werde dadurch
gegenstandslos. **Das habe ich nachgeholt und empirisch geprüft** — derselbe Snapshot zweimal:

| `HUMAN_IN_THE_LOOP` | Exit-Code | Verhalten |
|---|---|---|
| `true` | **3** | Sperre greift, kein zweiter Vorschlag |
| `false` | **0** | Wiederholungslauf geht durch |

**Damit ist die DoD von B0 erfüllt** („ein Wiederholungslauf desselben Snapshots läuft durch") —
und der UF2-Wiederholungs-Wrapper braucht **keinen** Eingriff in den Sperrmechanismus.
**Nebenbefund:** Der Wiederholungslauf lieferte erneut `1.14` — erster Datenpunkt zur
Within-Case-Stabilität, noch keine Messung.

**B2 — Regressionsreferenz, Bedingung A**, 5 Fälle über 5 Fehlerklassen.
- **Lauf-Metadaten:** Bedingung **A** · `RULEBOOK_MODE=monolith` · `MEMORY_MODE=off` ·
  `HUMAN_IN_THE_LOOP=false` · `gpt-4.1-2025-04-14`, API `2025-01-01-preview`, `temperature=0.3` ·
  Fälle I01, I02, I05, I07, I10 · je 1 Lauf · 2026-08-19 · Rohdaten
  `data/archive/ba-baseline-artefakte-20260819/B2-regressionsreferenz.json`

| | I01 | I02 | I05 | I07 | I10 |
|---|---|---|---|---|---|
| erkannt | ja | ja | ja | ja | ja |
| Feld richtig | ja | ja | ja | ja | **nein** |
| Wert exakt | ja | ja | nein | nein | ja |

Erkannt 5/5 · Feld 4/5 · Wert 3/5. **Über 5 Fälle × 3 Kriterien genau eine Abweichung zu PT4.**

**Die Abweichung — I10, und sie ist interessanter als sie aussieht.**

| | PT4 31.07. (`cards`, Gedächtnis an) | B2 19.08. (`monolith`, Gedächtnis aus) |
|---|---|---|
| `target_path` | **`None`** | `packagingEquipmentCompatibility[0]…` |
| `new_value` | **`None`** | `['ACO04']` — **richtig** |

Damals erzeugte das Modell **gar keinen Vorschlag** — das ist exakt die `target_path=None`-Lücke,
auf der im Masterplan der `stop_uncertain`-Pfad aufbaut. Jetzt erzeugt es einen, und der Wert
stimmt.

**Ursache: nicht abschliessend geklärt.** Drei Kandidaten, einer davon ausgeschlossen:
* ❌ **Gedächtnis** — ausgeschlossen. Der passende Eintrag existiert zwar (id=23,
  `packagingEquipmentCompatibility:70381` → `"ACO04"`, seit 15.08.), **aber der Lauf hatte
  `MEMORY_MODE=off`**: `memory_support=0.0`, `memory_cases_used=[]`, `value_source=llm`.
  Nachgeprüft im gespeicherten Vorschlag.
* ❓ **Regelwerk-Modus** — PT4 lief `cards`, B2 lief `monolith`. Möglich, dass das
  Monolith-Regelwerk hier etwas enthält, das die Karte nicht trägt.
* ❓ **Stochastik** — `temperature=0.3`, je **ein** Lauf. Ein `None` gegen einen Vorschlag kann
  schlicht Streuung sein.

**Mit je einem Lauf sind (2) und (3) nicht trennbar. Als Vermutung ausgewiesen, nicht als Befund.**
Das ist zugleich ein Argument für die Wiederholungsläufe (UF2): Genau solche Fälle zeigen, dass
Einzelläufe keine Ursachenzuordnung erlauben. **Für Kapitel 8 vormerken** — und I10 in AP-H
besonders beobachten.

**B3 — Artefakte archiviert** unter `data/archive/ba-baseline-artefakte-20260819/`, 18 Dateien:
* Regelwerk `llm-validation-fix-rules.md`: **sha256 `a3c14bd1b66cc1e3…`**, 36.165 Byte, Kopie
* **alle 14 Regelkarten** einzeln gehasht und kopiert (für Bedingung B und C)
* **Der echte Prompt aus einem Lauf** statt nur des Codes: 222.931 Zeichen,
  sha256 `fc6cbcce…`, mit Modell und Temperatur
* `MANIFEST.json` mit allen Schaltern, den drei Messbedingungen, Modellversion und
  Paketversionen (`langgraph 1.2.11`, `openai 1.109.1`, `pydantic 2.13.4`, Python 3.13.3)

**Ein Nebenbefund aus dem Archivieren, der in Kapitel 4 gehört:** Der Gesamtprompt umfasst
**222.931 Zeichen** — das Regelwerk (34.899) macht davon nur **16 %** aus. Der Unterschied
zwischen `monolith` und `cards` beträgt 11.138 Zeichen, also **rund 5 % des Gesamtprompts**.
Das erklärt den PT4-Pilotbefund „identische Vorschläge bei −16 % Tokens" und stützt die
Entscheidung, den Regelwerk-Modus nicht als Hauptfaktor zu behandeln.

- **Was NICHT funktioniert hat:** Ich hatte B0.1 im Gespräch als erledigt dargestellt, ohne es
  abzuhaken, und B0.2 aus der Dokumentation abgeleitet statt geprüft. Beides jetzt nachgeholt —
  der Test hat die Ableitung bestätigt, aber das war vorher nicht belegt.
- **Offen / nächstes:** **AP-D1** — Knotenextraktion, beginnend mit Knoten 6
  (`validate_correction_schema_llm`, am kleinsten, festigt das Muster).

---

### [BA-017] 2026-08-19 — AP-D1: Knoten 6 extrahiert, Muster festgelegt
- **Status:** done
- **Kapitelbezug:** K4 *(Knotenschnitt, Extraktionsmuster)*, K6 *(Beobachtungspunkt Kategorie 2)*
- **Literatur:** —
- **Changed files:** `app/tools/smart-planning/runtime/validate_correction_schema_llm.py`
  (additiv), `app/tools/smart-planning/graph/nodes/technical_check.py` (neu),
  `docs/BA_ARBEITSPAKETE.md`

**Das Muster, das ab jetzt für D2–D7 gilt.** Knoten 6 war der kleinste — bewusst zuerst, um das
Vorgehen festzuzurren:

1. **Gemeinsamer Helfer statt Doppelung.** `_load_latest_proposal()` neu; **`main()` benutzt ihn
   jetzt ebenfalls**. Vorher hätte der Graph-Knoten dieselbe Iterations- und Ladelogik ein
   zweites Mal gebraucht — genau das Drift-Risiko, das Kap. 12.2 ausschliessen will.
2. **Zwei additive Parameter an der bestehenden Kernfunktion**, Defaults = bisheriges Verhalten:
   * `exit_on_failure=True` → CLI unverändert (`sys.exit(1)`).
     **`False` für den Graphen** — siehe Kasten unten.
   * `stats=None` → füllt `{retries, errors}`. Der Graph braucht die Zahl für
     `GraphState["technical_check"]`; ohne den Parameter ändert sich nichts.
3. **Knotenfunktion `run_technical_check()`** im Runtime-Skript (nicht im Graph-Paket), damit die
   Logik dort bleibt, wo sie hingehört. Der Wrapper unter `graph/nodes/` macht nur
   Zustandsformung und `trace`.

> **Der inhaltlich wichtigste Punkt: ein Knoten darf den Prozess nicht beenden.**
> `validate_with_retry()` rief bei erschöpften Retries `sys.exit(1)`. Im Graphen wäre das fatal —
> die bedingte Kante könnte dann nie auf `stop_uncertain` entscheiden (Kap. 11), und der Lauf
> wäre weg statt dokumentiert. **Ein gescheiterter Schema-Check ist ein Zustand, kein Abbruch.**
> Das gilt für jeden weiteren Knoten in D2–D7.

- **Verifikation — beide Pfade einzeln geprüft:**
  * **CLI unverändert:** `validate_correction_schema_llm.py --snapshot-id 1d66d9f6…` →
    „Using iteration: 1", „OK Schema validation passed", **Exit-Code 0**. Ausgabe und
    Exit-Verhalten wie vorher.
  * **Als Graph-Knoten:** `schema_valid=True`, `retries=0`, `iteration=1`, dazu ein
    `trace`-Eintrag mit Zeitstempel, Dauer (2 ms) und Ein-/Ausgangs-Digest.
  * **Fehlerpfad 1** (ungültiger Vorschlag, `max_retries=0`): `schema_valid=False`, `retries=1`,
    Fehlertext gefüllt — **Prozess lebt**.
  * **Fehlerpfad 2** (kein Vorschlag vorhanden): `schema_valid=False` mit der Klartextmeldung
    „Knoten 5 hat keinen Vorschlag hinterlassen" — **Prozess lebt**.
  * **Zeilenenden erhalten:** die Datei hat CRLF; nach der Bearbeitung 290 statt 280 CRLF
    (= die zehn neuen Zeilen), keine Vermischung.
- **Was NICHT funktioniert hat:**
  * Meine erste Ersetzung schlug fehl, weil ich als Anker eine Zeile mit `\n` **innerhalb** eines
    f-Strings gewählt hatte. Die Datei blieb dabei unverändert (Assertion vor dem Schreiben).
    Mit einem Anker ohne Escape-Sequenzen ging es. **Lehre:** Ankertexte für Ersetzungen ohne
    Escapes wählen — verwandt mit Muster 5 aus `BEFUNDE_UND_LEHREN.md`.
  * Der Fehlerpfad-Test hat `llm_correction_proposal_retry_0.json` in einem **echten
    Messdaten-Ordner** (`1d66d9f6…`, Fall I10 aus B2) hinterlassen. **Entfernt**; der echte
    Vorschlag ist unversehrt (`packagingEquipmentCompatibility[0].predecessors = ['ACO04']`).
    Künftige Fehlerpfad-Tests gehören auf einen Wegwerf-Snapshot, nicht auf Messdaten.
- **Offen / nächstes:** **AP-D2** — Knoten 5 (`generate_correction_llm.py`), der wichtigste.
  `generate_correction_with_llm()` ist bereits aufrufbar und nimmt genau die Knoten-Eingänge;
  der Aufwand liegt in den rund 250 Zeilen `main()` drumherum (Sperre, Gedächtnis,
  `derive_correction_identity`, Konfidenz, Speichern).

---

### [BA-018] 2026-08-19 — AP-D2: Knoten 5 extrahiert, Regelübergabe belegt
- **Status:** done
- **Kapitelbezug:** K4 *(Knotenschnitt, Regelprovenienz)*, K6 *(Beobachtungspunkte Kat. 1 und 3)*
- **Literatur:** L11 *(`matched_rules` als Beobachtung statt Selbstauskunft)*
- **Changed files:** `app/tools/smart-planning/runtime/generate_correction_llm.py` (additiv,
  1085 → 1136 Zeilen), `app/tools/smart-planning/graph/nodes/correction.py` (neu),
  `docs/BA_ARBEITSPAKETE.md`

**Der Schnitt.** 216 Zeilen aus `main()` in `run_correction_generation()` verschoben — der Block
lag bereits auf Funktionsrumpf-Einrücktiefe, musste also nicht umgeschrieben werden. `main()`
ruft jetzt nur noch eine Ebene tiefer und behält seine CLI-Semantik (Sperrmeldung, Exit-Code 3,
Token-Ausgabe).

**Die inhaltlich wichtige Entscheidung: `fix_rules` ist ein PARAMETER, kein Ladevorgang.**
Das Laden des Regelwerks gehört zu **Knoten 4 (Regelzuordnung)** und wird dort protokolliert.
Würde Knoten 5 die Regeln selbst nachladen, könnte `matched_rules` etwas anderes ausweisen als
das, was das Modell tatsächlich gesehen hat — und damit wäre die **Regelprovenienz wertlos**.
Genau sie ist aber das, was der Monolith nicht hat (Kap. 3.7). Wird nichts übergeben, lädt die
Funktion wie bisher — der CLI-Pfad bleibt unverändert.

Dazu: `check_open_proposal` gibt den offenen Vorschlag **zurück** statt `sys.exit(3)` zu rufen —
dasselbe Prinzip wie in AP-D1. Eine Sperre ist ein Zustand, kein Abbruch.

- **Verifikation — drei Stufen:**
  1. **CLI byte-identisch.** Lauf gegen den Wegwerf-Snapshot `194f58de…`:
     Regelwerk 34.899 Zeichen, `Memory: 0 Fälle`, `demands[0].articleId = 100005`,
     `value_grounded=1.0`, Konfidenz `0.8`, **Prompt: 14.590 Token** — **exakt dieselbe
     Tokenzahl wie beim AP-A-Smoke-Test (BA-012).** Gleiche Tokenzahl heisst gleicher Prompt.
  2. **Als Graph-Knoten** mit simuliertem Knoten 4: liefert denselben Vorschlag, dazu ein
     `trace`-Eintrag mit Aktion, Zielpfad, Wert, `value_source`, Konfidenz und den geladenen
     Karten.
  3. **Der Parameter setzt sich gegen den Prozess-Default durch** — das war der eigentlich zu
     beweisende Punkt:

     | | |
     |---|---|
     | Prozess lief unter | `RULEBOOK_MODE=cards` → 23.761 Zeichen |
     | Knoten 4 übergab | Monolith → 34.899 Zeichen |
     | Gespeicherter Prompt | **14.590 Token** — identisch mit den Monolith-Läufen |

     Bei `cards` wären es rund 3.000 Token weniger gewesen. **Der übergebene Regeltext gewinnt.**
  4. 6/6 Kernmodule und 3/3 Runtime-Skripte importieren weiterhin; CRLF erhalten (1085 → 1136,
     nur die neuen Zeilen).
- **Was NICHT funktioniert hat:**
  * **Der erste Beweisversuch war untauglich.** Ich hatte `os.environ['RULEBOOK_MODE']='cards'`
    **nach** dem Import gesetzt — `RULEBOOK_MODE` wird aber beim Import gelesen. Beide Werte
    waren 34.899, das Ergebnis also nicht unterscheidbar. **Ein Test, der nicht trennen kann,
    beweist nichts** — wiederholt mit dem Modus von aussen gesetzt.
  * Der Katalog-Regressionslauf über den Harness brach ab: **Testinstanz nicht erreichbar**
    (`getaddrinfo failed`, VPN weg). Kein Codeproblem — die Prüfung lief stattdessen direkt
    gegen einen lokalen Snapshot, was denselben Code abdeckt, weil `generate_correction_llm`
    ohnehin nur lokale Dateien plus Azure OpenAI braucht.
  * Testartefakte liegen bewusst auf `194f58de…` (Wegwerf-Snapshot aus AP-A), **nicht** auf
    Messdaten — Lehre aus BA-017.
- **Offen / nächstes:** **AP-D3** — Knoten 7 (Anwendung und Re-Validierung). Erzeugt
  `errors_after`; ohne ihn schliesst die Iterationsschleife nicht. `apply_correction()`,
  `validate_snapshot()` sind bereits aufrufbar, `update_snapshot` braucht einen Wrapper.
  **Benötigt die Testinstanz** — vor dem Start VPN prüfen.

---

### [BA-019] 2026-08-19 — Nachprüfungen zu D1 und D2 nach externer Rückmeldung
- **Status:** done — D1 und D2 damit endgültig abgeschlossen
- **Kapitelbezug:** K4 *(Kanten, Retry-Verantwortung)*, K5 *(Rückwärtskompatibilität)*,
  K6 *(was die rohe LLM-Korrektur ist)*
- **Literatur:** —
- **Changed files:** `app/tools/smart-planning/runtime/validate_correction_schema_llm.py`,
  `app/tools/smart-planning/runtime/generate_correction_llm.py`,
  `app/tools/smart-planning/graph/nodes/correction.py`, `docs/BA_MASTERPLAN.md` (Kap. 11)

**Alle sieben Rückmeldungen trafen zu.** Zwei davon deckten Fehler auf, die sonst erst in der
Messung sichtbar geworden wären.

## D1

**(1) Retry-Verantwortung — ein Konstruktionsfehler in meiner Kantenbeschreibung.**
Kap. 11 sah vor: *„`schema_valid == False` und Retries übrig → zurück zu [5]"*. Aber
`validate_with_retry(max_retries=5)` führt die Schema-Retries **vollständig innerhalb von
Knoten 6** aus, inklusive erneutem LLM-Aufruf. Eine Graph-Kante 6→5 wäre eine **zweite
Retry-Schicht** gewesen: bis zu 5 interne × N Graph-Durchläufe. Der Graph hätte sich damit
anders verhalten als der Monolith — **in einer Dimension, die gar nicht Gegenstand des
Vergleichs ist.** Ein Konfundierungsfaktor, den niemand bemerkt hätte.
**Korrigiert.** Verbindliche Aufteilung, jetzt in Kap. 11 als Kasten:

| Ebene | Zuständig | Wofür |
|---|---|---|
| **innerhalb Knoten 6** | `validate_with_retry` | **technische** Schemafehler |
| **Kante 8→2** | Router | **fachliche** Iteration, erst nach Re-Validierung |

Die Rückkante 6→5 ist gestrichen; das Ablaufdiagramm ist angepasst.

**(2) `retries`-Semantik — ein Off-by-one in meiner eigenen Instrumentierung.**
`retry_count` wird **vor** der Schranke erhöht. Bei `max_retries=5` laufen 5 LLM-Retries,
gemeldet wurden **6**; bei `max_retries=0` wurden 0 ausgeführt, gemeldet **1**.
**Korrigiert** über einen eigenen Zähler `llm_retries_done`. Definition jetzt im Docstring **und**
in Kap. 11: **`retries` = Zusatzversuche NACH dem ersten**, also tatsächlich ausgeführte
LLM-Retries; `0` = beim ersten Versuch gültig; Obergrenze `max_retries`.
Gegenprobe: gültig beim ersten Versuch → `retries=0` ✓; erschöpft bei `max_retries=0` →
`retries=0` ✓ (vorher fälschlich 1).

**(3) CLI-Fehlerfall und Rückwärtskompatibilität.** Auf einem Wegwerf-Snapshot geprüft:

| Aufruf | Exit | Ausgabe / Artefakte |
|---|---|---|
| CLI, erschöpfte Retries *(CLI-Defaults, `exit_on_failure` nicht gesetzt)* | **1** | „Max retries reached", „Please check … manually.", `llm_correction_proposal_retry_0.json` geschrieben |
| CLI, Ausnahme im Retry *(fehlende `identify_response`)* | **1** | Traceback wie bisher |
| **Graph** (`run_technical_check`) | **0** | `schema_valid=False`, `retries=0`, Fehlerliste — **Prozess lebt** |

*Einschränkung, ehrlich benannt:* Der Erschöpfungspfad wurde mit `max_retries=0` erzwungen, um
nicht fünf echte LLM-Retries zu bezahlen. Getestet ist damit **die Verzweigung**, nicht das
Durchlaufen aller fünf Runden — `max_retries` beeinflusst die Verzweigungslogik nicht.

## D2

**(4) Der Tokenzahl-Beweis war zu schwach — durch SHA-256 ersetzt.**
„Gleiche Tokenzahl" ist ein Näherungsmass. Stattdessen: die Fassung **vor** der Extraktion aus
`git show HEAD` geholt, beide Fassungen auf demselben Snapshot gefahren und die tatsächlich
gesendeten Prompts verglichen:

```
ALT: 49.841 Zeichen  sha256 dc25326c9d8355069c94e410f30ef771…
NEU: 49.841 Zeichen  sha256 dc25326c9d8355069c94e410f30ef771…
Stringvergleich identisch : True
SHA-256 identisch         : True
```

Modell, Temperatur und Nachrichtenanzahl ebenfalls gleich. **Der Prompt ist byte-identisch.**

**(5) HitL-Sperre im CLI-Pfad nach der Extraktion.** `HUMAN_IN_THE_LOOP=true` mit offenem
Vorschlag → CLI meldet „ABGEBROCHEN", nennt Vorschlags-ID, Fehlerart und Review-Link,
**Exit-Code 3** wie zuvor. Derselbe Fall als Graph-Knoten → `correction_proposal=None`,
`manual_intervention_required=True`, `trace.blockiert=True`, **Exit 0**.

**(6) `is None` statt truthy — geprüft, nicht behauptet.** Alle vier Parameter
(`fix_rules`, `identify_response`, `search_results`, `iteration_number`) werden per `is None`
geprüft; kein truthy-Test im Code. **Ein leerer Regeltext löst also kein Nachladen aus.**
Zusätzlich trägt der Trace jetzt **`regeln_sha256`** — den Hash des tatsächlich an Knoten 5
übergebenen Regeltexts. Ohne ihn liesse sich später nicht beweisen, dass das Modell genau die
Regeln gesehen hat, die `matched_rules` ausweist; damit wäre die Regelprovenienz wertlos.

**(7) Echte Generierung gegen operative Hülle — dokumentiert im Docstring.**

* **Echte Generierung:** `generate_correction_with_llm()` — der einzige LLM-Aufruf.
* **Die rohe LLM-Korrektur liegt in `iteration-N/llm_correction_call.json` → `response.content`**,
  daneben `model` mit der exakten Version. Wird bei **jedem** Lauf geschrieben.
* **Operative Hülle** (verändert den Wert nicht): HitL-Sperre, Eingangsbeschaffung,
  `derive_correction_identity`, `compute_value_grounded`, `compute_memory_support`,
  `compute_confidence_score`, Persistenz.
* **Der einzige Grenzfall:** der Gedächtnis-Override ist die **einzige** Stelle ausserhalb des
  LLM-Aufrufs, die `new_value` ersetzt. Genau deshalb läuft er in Messläufen über
  `MEMORY_MODE=off` ins Leere — sonst wäre nicht entscheidbar, ob eine korrekte Korrektur vom
  Modell oder aus dem Gedächtnis kam. `value_source` unterscheidet die Fälle:
  `llm` / `memory` / `llm_dissent`.

- **Was NICHT funktioniert hat:**
  * **Ich hatte im Docstring behauptet, die rohe Modellausgabe liege in
    `llm_correction_proposal.ai_original.json`.** Falsch: Die Datei schreibt der **Review-Pfad**
    (`app/routes/apply_prep.py`), also erst bei einer menschlichen Entscheidung — in Messläufen
    existiert sie gar nicht. Am Dateisystem geprüft und korrigiert. Danach auch die Struktur von
    `response` falsch geraten (`choices` statt `content`); ebenfalls am echten Artefakt
    nachgesehen und richtiggestellt. **Zweimal geraten statt nachgesehen — in einem Docstring,
    der später die Messquelle definiert, ist das der teuerste Ort für eine Vermutung.**
    **Nachtrag, durch eine repository-weite Suche bestätigt** (die erste war nur gezielt):
    Einziger Schreiber ist `app/routes/apply_prep.py:337`; `review.py:664` erwähnt die Datei
    nur im Kommentar. Empirisch passend — sie liegt in **7 von 32** Snapshot-Ordnern, bei
    23 Reviews in der Datenbank. **Im Generierungspfad entsteht sie nie.**
  * Gegenprobe am realen Artefakt: roh `100005` = final `100005`, `value_source=llm`,
    `model=gpt-4.1-2025-04-14` — bei `MEMORY_MODE=off` erwartungsgemäss identisch.
- **Offen / nächstes:** **AP-D3** (Knoten 7). **Braucht die Testinstanz** — VPN vorher prüfen.

---

### [BA-020] 2026-08-19 — AP-D3, D4 und D5: Knoten 7, 4, 8 und 9 fertig
- **Status:** done — damit sind **6 der 9 Knoten** gebaut; offen bleiben D6 (Knoten 2) und D7 (Knoten 3)
- **Kapitelbezug:** K4 *(Knotenbau, Router ohne Fachlogik)*, K6 *(Beobachtungspunkt Kategorie 4)*
- **Literatur:** L11 *(Regelprovenienz als Beobachtung)*
- **Changed files:** `apply_correction.py`, `update_snapshot.py`, `generate_audit_report.py`,
  `app/core/rulebook_loader.py` (alle additiv), vier neue Knoten unter
  `app/tools/smart-planning/graph/nodes/`, `docs/BA_ARBEITSPAKETE.md`

**D3 — Knoten 7, Anwendung und Re-Validierung.** Zwei Extraktionen (`run_apply`, `run_upload`),
`validate_snapshot()` war bereits aufrufbar. Der Knoten verkettet vier Schritte.
**Der dritte ist der kritische:** `validate_snapshot` **holt nur ab, löst nichts aus**. Ohne
`trigger_server_validation()` meldet der Server die ALTE Bewertung — im schlimmsten Fall
„0 Fehler", obwohl nichts neu geprüft wurde. Genau dieses falsche Grün ist in PT4 schon
aufgetreten und ist im Knoten als Kommentar festgehalten.

**D4 — Knoten 4 und 8, beides Neucode.**
* **Knoten 4** ist *der Knoten, den der Monolith gar nicht hat*: Er lädt nicht nur die Regeln,
  er hält fest **welche**. `matched_rules` trägt Modus, Kartenliste, den vollen `rule_text`
  (den Knoten 5 als Parameter bekommt), dessen **sha256** und den Umfang.
  Der `trace` bekommt bewusst **nur Hash und Umfang, nicht den Volltext** — 24.000 bis 35.000
  Zeichen würden ihn unlesbar machen (Kap. 12.5).
* **Knoten 8** schreibt `decision`; **`route_after_evaluation()` enthält keine Fachlogik**,
  sondern liest nur das Feld. Ein Router mit eingebauter `if/else`-Kette wäre wieder der
  implizite Kontrollfluss, den die Arbeit dem Monolithen vorwirft.

**D5 — Knoten 9.** `run_audit_report()` extrahiert. Im Docstring festgehalten: Dies ist der
**einzige Knoten, dessen Ausfall den Vergleich nicht berührt** — der Report ist Ausgabe, kein
Messgegenstand. Deshalb darf er bei Zeitknappheit als einziger entfallen (Kap. 9).

**Eine Nebenextraktion, die nötig wurde:** Für Knoten 4 gab es keine Möglichkeit zu erfahren,
*welche* Karten `load_rulebook()` ausgewählt hat — die Auswahl stand inline. Ich hätte die Regel
im Knoten nachbauen können; das wäre genau das Drift-Risiko aus Kap. 12.2. Stattdessen
`select_cards()` additiv herausgezogen, **`load_rulebook()` benutzt sie jetzt ebenfalls**.

- **Verifikation:**
  * Syntax aller vier geänderten Dateien; `run_apply`, `run_upload`, `run_audit_report`,
    `select_cards` vorhanden.
  * **Regelwerk nach dem `select_cards`-Umbau unverändert:** `monolith` 34.899 Zeichen,
    `cards` 23.761 Zeichen — dieselben Werte wie vor dem Umbau.
  * **Knoten 4:** Modus `cards` → Karten `['_core.md', 'density-values.md']`, 16.620 Zeichen,
    Hash gesetzt, `rule_text` im State, **kein Volltext im trace**.
  * **Knoten 8, alle sechs Pfade einzeln geprüft:** Schema ungültig → `stop_uncertain` ·
    kein `target_path` → `stop_uncertain` · Anwenden gescheitert → `stop_uncertain` ·
    0 Fehler → `stop_valid` · Limit erreicht → `stop_max_iter` · sonst → `continue`.
    Router leitet nur bei `continue` zurück zu `classification`, sonst zu `answer`.
  * **Knoten 7 end-to-end** auf einem frisch erzeugten Wegwerf-Fall
    (`d352f26e…`, I01, `validate_unique_ids`):
    Korrektur angewendet (`demands[1].demandId` = `D100005_002`), `upload-result.success=True`,
    Re-Validierung **1 Fehler → 0 Fehler**. **Damit existiert `errors_after`, und die
    Iterationsschleife schliesst** — das Loch aus dem Altplan ist zu.
- **Lauf-Metadaten (Knoten-7-Test):** Bedingung A · `RULEBOOK_MODE=monolith` ·
  `MEMORY_MODE=off` · `HUMAN_IN_THE_LOOP=false` · `gpt-4.1-2025-04-14` · Fall I01 ·
  1 Lauf · 2026-08-19 · Rohdaten `data/snapshots/d352f26e-9779-411f-a612-7faab5ea45ff/`
  und `data/archive/ba-ap0-20260819/D3-testfall.json`.
  **Kein Messwert** — Wegwerf-Fall zur Funktionsprüfung vor dem Einfrieren.
- **Was NICHT funktioniert hat:**
  * Ich hatte in Knoten 4 zunächst `rulebook_loader.cards_for()` aufgerufen — **eine Funktion,
    die es nicht gibt.** Statt sie zu erfinden oder die Auswahlregel nachzubauen, `select_cards()`
    sauber extrahiert. *(Wieder ein Fall von angenommener statt geprüfter API.)*
  * Zwei Ersetzungen scheiterten erneut an `\n`-Ankern innerhalb von f-Strings; mit dem
    Editor-Werkzeug statt der Shell gelöst — Muster 5, inzwischen zum dritten Mal.
- **Offen / nächstes:** **AP-D6** (Knoten 2, `identify_error_llm`) und **AP-D7** (Knoten 3,
  `identify_snapshot` — ~300 Zeilen Ablaufsteuerung in `main()`, der Risikoposten des Blocks).
  Danach AP-E: den Graphen verdrahten.

---

### [BA-021] 2026-08-19 — Prüfrunde zu D3–D5: ein falsches Grün im Monolith-Pfad gefunden
- **Status:** done — D3, D4 und D5 sind damit abgeschlossen
- **Kapitelbezug:** K4 *(Verantwortungsschnitt)*, K5 *(Kontrollbedingungen, Re-Validierung)*,
  K6 *(Kategorie 4, Beobachtungspunkte)*, K8 *(Instrumentenfehler in der Baseline)*
- **Literatur:** L09 *(Prompt-Sensitivität als Grund gegen die Prompt-Änderung in Knoten 2)*
- **Changed files:** `app/agents/sp_agent.py`, `graph/nodes/apply_revalidate.py`,
  `graph/nodes/evaluation.py`, `graph/nodes/rule_matching.py`, `graph/nodes/answer.py`,
  `docs/BA_MASTERPLAN.md` (Kap. 7.1, 7.1.2, 9.0), `docs/BA_ARBEITSPAKETE.md`

**Zehn Prüfpunkte abgearbeitet. Vier waren bereits korrekt, sechs deckten echte Fehler auf** —
einer davon schwerwiegend, und er lag **nicht** im Graphen, sondern in der Baseline.

## Der schwerwiegende Fund: falsches Grün im Monolith-Pfad

`trigger_server_validation()` ist **bereits synchron** — es pollt den Job bis `FINISHED`,
hat Timeout und liefert `{"ok", "job_id", "status", "waited_s"}`. Die Infrastruktur war also
richtig. **Zwei Dinge waren es nicht:**

1. **Mein Knoten 7 verwarf den Rückgabewert.** Bei Timeout oder gescheitertem Job hätte er
   trotzdem `validate_snapshot()` aufgerufen und ein veraltetes Ergebnis als `errors_after`
   gemeldet. **Exakt Muster 1** aus `BEFUNDE_UND_LEHREN.md`.
2. **Der Monolith-Pfad löst gar keine Re-Validierung aus.** Weder `sp_agent.py` noch die
   Runtime-Skripte rufen `trigger_server_validation` — nur die Eval-Skripte und der Review-Pfad
   tun es. Dabei ist das Problem seit **AP3.3d** in `routes/server_validation.py` wörtlich
   dokumentiert: *„the re-validation step of every correction pipeline reads an empty list right
   after an upload and reports `errors=0` — a false green."* Es wurde nie in die Pipeline
   verdrahtet.

**Warum das den Vergleich zerstört hätte:** Die Iterationsschleife in `execute_pipeline()`
entscheidet anhand von `final_validation.errors` über eine weitere Runde — auf Basis einer Zahl,
die strukturell immer 0 war. Hätte ich den Trigger **nur** im Graph-Knoten eingebaut:
A und B mit falschem Grün und nach einer Iteration abbrechend, C mit echten Zahlen. Der Graph
hätte anders ausgesehen **aus einem Grund, der nichts mit Architektur zu tun hat** — und
Kategorie 4 samt Iterationszahlen wären verdorben gewesen.

**Behoben an der gemeinsamen Stelle:** Trigger in `SPAgent._execute_pipeline()` **und** im
Graph-Knoten. A, B und C haben jetzt dieselbe Re-Validierungssemantik (Masterplan Kap. 7.1.2).

## Die weiteren Befunde

**Proposal-Identität (Punkt 2) — bestätigt.** `run_apply()` hätte ohne Übergabe den „neuesten"
Vorschlag von Platte geladen; der State hätte X tragen, angewendet worden wäre Y. Knoten 7
übergibt jetzt den Vorschlag **aus dem State** und protokolliert dessen `proposal_sha256`.
Keine zweite Wahrheit zwischen State und Dateisystem.

**Fehlermengen (Punkt 3) — bestätigt.** Die reine Anzahl genügt nicht: `1 → 1` kann „nichts
passiert" heissen oder „A behoben, B neu erzeugt". Knoten 7 leitet jetzt `errors_resolved`,
`errors_remaining`, `errors_new` und `new_error_types` ab. Fehleridentität = Validator-Tag +
Hash der Meldung, **als Näherung ausgewiesen**, weil der Server keine Fehler-ID liefert.
**`errors_after=None` ≠ `0`** — Knoten 8 entscheidet bei `None` auf `stop_uncertain`.

**Knoten 8, Priorität (Punkt 6) — Reihenfolge festgeschrieben und geprüft.**
Stufe 1 technische/operative Unsicherheit → Stufe 2 nachweislich fehlerfrei → Stufe 3 Limit →
Stufe 4 weiter. **Stufe 1 schlägt Stufe 2:** `applied_ok=False` zusammen mit `errors_after=0`
ergibt `stop_uncertain`, nicht `stop_valid`. Acht Kombinationen einzeln geprüft, alle korrekt;
zusätzlich der Fall „Knoten 7 noch nicht gelaufen", der nicht fälschlich scheitern darf.

**`select_cards()` (Punkt 5) — per Hash bewiesen statt per Zeichenzahl.** Alte Fassung aus
`git show HEAD`. Die Extraktion hat den injizierten Regeltext nicht verändert.

> **Korrektur 20.08.2026.** Hier stand „7 Fehler-Tags × 2 Modi: 16 Vergleiche“ — das ist
> schon rechnerisch falsch (7 × 2 = 14) und die Fallzahl war zu klein. Statt die Zahl
> nachzurechnen, wurde **neu gemessen**: **21 Fälle** (19 `KNOWN_VALIDATOR_TAGS` + `None` +
> ein unbekannter Tag) **× 2 Modi = 42 Vergleiche, 0 Abweichungen.**
> Dabei fiel ein **Fehler im Prüfaufbau** auf: der Moduswechsel per `importlib.reload()`
> greift nicht, weil `RULEBOOK_MODE` aus `agent_config` stammt und nicht mitgeladen wird —
> der erste Versuch mass **zweimal `cards`**. Erst getrennte Prozesse je Modus messen
> wirklich beide. Gegenprobe, dass es diesmal wirkte: `cards` liefert **12 verschiedene
> Regeltextlängen** (selektiv), `monolith` genau **eine** (immer derselbe Volltext).

**Zwei zu starke Formulierungen von mir korrigiert:**
* *„Knoten 4 ist der Knoten, den der Monolith gar nicht hat"* — **zu stark.** Bedingung B wählt
  funktional bereits dieselben Karten. Neu ist der **eigenständige, explizite Schritt mit
  persistierter Provenienz im gemeinsamen State**; in A/B ist die Auswahl flüchtiger `print()`.
* *„Knoten 9 kann entfallen, ohne den Vergleich zu berühren"* — **zu weit.** Für UF1/UF2 stimmt
  es; der Audit-Report kann aber bei **UF3, Expertenbewertung und SUS/UEQ** Bewertungsgegenstand
  sein. Korrekt: Er darf nur entfallen, wenn er **in allen drei Bedingungen symmetrisch**
  ausgeschlossen wird.

**Verantwortungsschnitt für D6/D7 (Punkt 4) — festgelegt, Masterplan Kap. 9.0.**
`identify_error_llm` erledigt heute die Aufgaben von **drei** Knoten: Klassifikation,
Suchstrategie **und Kartenauswahl** (`relevant_cards`), und ruft über `trigger_identify_tool()`
zusätzlich `identify_snapshot.py` auf. Neuer Schnitt: Knoten 2 **schlägt** Karten vor,
**Knoten 4 ist die einzige Stelle, die auflöst und protokolliert**; die Suche wandert zu
Knoten 3.
**Der Prompt von Knoten 2 wird ausdrücklich NICHT geändert** — er ist in A, B und C identisch
und damit Kontrollbedingung. Ihn nur für C anzupassen, hiesse einen Prompt-Unterschied zu
messen statt Orchestrierung (L09).

- **Verifikation — CLI-Regressionen auf dem Wegwerf-Snapshot `d352f26e…`:**

  | CLI | Exit | Ausgabe / Artefakte |
  |---|---|---|
  | `apply_correction.py` | **0** | „Correction Applier", Iteration, Schema gültig, „Applied", „Done" |
  | `update_snapshot.py` | **0** | „UPDATE SNAPSHOT", 2.746.443 Zeichen, „SUCCESS" |
  | `generate_audit_report.py` | **0** | Report erzeugt, `audit-report.md` + `audit-report-stats.json` |

  Dazu: Syntax aller fünf geänderten Dateien, 5/5 Kernmodule importierbar, Trigger im
  Monolith-Pfad nachweislich verdrahtet.
- **Was NICHT funktioniert hat:** Der verworfene Rückgabewert in Knoten 7 war **mein** Fehler,
  und zwar genau das Muster, das dieses Repository als Muster 1 dokumentiert — begangen zwei
  Tage nachdem ich es selbst zitiert hatte. Aufgefallen ist er nur durch die externe Prüfung.
- **Offen / nächstes:** **AP-D6** und **AP-D7** nach dem Schnitt aus Kap. 9.0.
  **Vor AP-H zu klären:** Die isolierte Suite fährt nur `identify` + `generate`, also **ohne**
  apply/revalidate. Für Kategorie 4 braucht AP-H einen Runner, der die **volle** Pipeline in
  allen drei Bedingungen fährt.

---

### [BA-022] 2026-08-19 — Zwei Bauregeln verankert · AP-D6: Knoten 2 mit fünf Nachweisen
- **Status:** done — D6 abgeschlossen; offen bleibt nur noch D7
- **Kapitelbezug:** K4 *(Verantwortungsschnitt, Prompt als Kontrollbedingung)*,
  K5 *(Kontrollbedingungen)*, K6 *(Beobachtungspunkt Priorisierung)*
- **Literatur:** L09 *(Prompt-Sensitivität — Begründung, den Prompt nicht zu ändern)*
- **Changed files:** `CLAUDE.md`, `.github/instructions/instructions.md`,
  `app/tools/smart-planning/runtime/identify_error_llm.py` (additiv),
  `app/tools/smart-planning/graph/nodes/classification.py` (neu),
  `docs/BA_ARBEITSPAKETE.md`, Memory-Verzeichnis (zwei neue Notizen)

**Zwei Bauregeln dauerhaft verankert** (Nutzervorgabe, aus den Fehlern von BA-021):

* **Regel A — keine Optimierung auf Geschwindigkeit zulasten der Vergleichbarkeit.**
  Berührt eine Extraktion möglicherweise fachliche Semantik, LLM-Input, Kontrollbedingungen oder
  Messbarkeit: **erst stoppen, prüfen, dokumentieren.** Keine Annahmen über APIs, Artefakte oder
  Prozessverhalten — am echten Code oder Lauf verifizieren. Gleichwertigkeit **empirisch** über
  Hashes belegen, nicht über Näherungen wie Tokenzahl.
* **Regel B — ein Graph-Knoten darf nicht einfach nur funktionieren.** Nachzuweisen: Er
  übernimmt **genau** die vorgesehene Verantwortung **und** führt **keine Verbesserung ein, die
  nur C erhält**. Ist es eine Reparatur, gehört sie in die gemeinsame Runtime.

Beide stehen jetzt in `CLAUDE.md` (Abschnitt „Zwei Regeln für den Bau") und im Memory.

## AP-D6 — Knoten 2, die fünf geforderten Nachweise

**1. Alter CLI-Identify-Pfad fachlich identisch.** Derselbe Wegwerf-Snapshot vor und nach der
Extraktion. Alle **entscheidungsrelevanten** Felder gleich:

| Feld | ALT | NEU | gleich |
|---|---|---|---|
| `tag_error_type` | `DEMAND_ARTICLE_IDS` | `DEMAND_ARTICLE_IDS` | ✔ |
| `selected_error_index` | 0 | 0 | ✔ |
| `search_mode` | `value` | `value` | ✔ |
| `search_value` | `100005_NOT_FOUND` | `100005_NOT_FOUND` | ✔ |
| `should_investigate` | True | True | ✔ |
| `relevant_cards` | `['references.md']` | `['references.md']` | ✔ |

Abweichend **nur** die Freitextfelder `error_type` und `prioritization_reasoning` — das ist
Stochastik bei `temperature=0.3` bei byte-identischem Prompt, **kein** Code-Unterschied.
Exit-Code 0, Iterationsordner geschrieben, Suche ausgelöst — CLI-Ablauf unverändert.

> **⚠ Entwicklungsbeobachtung, KEIN Evaluierungsergebnis** (ergänzt 19.08.2026):
> Über **fünf** Läufe desselben Prompts auf demselben Snapshot schwankte `relevant_cards`
> erheblich — `['references.md','unique-ids.md','work-plan-ids.md']` → `['references.md']`
> (dreimal) → `[]`. Der `tag_error_type` blieb dabei stabil `DEMAND_ARTICLE_IDS`.
> Das ist Streuung in einem **entscheidungsrelevanten** Feld, nicht nur im Freitext.
> **Diese Zahlen sind vor dem Einfrieren entstanden, auf einem Wegwerf-Snapshot und ohne
> Messprotokoll — sie sind KEIN Befund für UF2 und dürfen in Kapitel 7 nicht auftauchen.**
> Sie sind ein Hinweis darauf, worauf der Wiederholungstest in AP-H achten sollte.

**2. Prompt-Hash vorher/nachher identisch.**

```
ALT: 38.137 Zeichen  sha256 2b65a88bdd6f9cdf9b6edefed93ea06bd65106e271ea6d1a113e10b39ebf71c6
NEU: 38.137 Zeichen  sha256 2b65a88bdd6f9cdf9b6edefed93ea06bd65106e271ea6d1a113e10b39ebf71c6
Stringvergleich: True
```

**3. LLM-Aufruf identisch.** Modell `gpt-4.1`, `temperature=0.3`,
`response_format={'type':'json_object'}`, 2 Nachrichten — alles gleich.

**4. Knoten 2 führt keine Suche mehr aus — per AST belegt, nicht per Textsuche.**
`run_classification` ruft: `analyze_validation_with_llm`, `load_validation_data`,
`save_llm_response`. **`trigger_identify_tool` ist nicht darunter.** In `main()` schon —
das CLI bleibt unverändert.

**5. Der State trägt alles Geforderte.** Klassifikation (`tag`, `error_type`, `priority_index`,
`reasoning`, `raw_message`), `search_mode`, `search_value`, `should_investigate`,
`relevant_cards`.

**Zusammenspiel mit Knoten 4 geprüft — genau eine Auflösungsstelle.**
*Präzisierung: Dies war ein **eigener, dritter LLM-Lauf** (iteration-5), nicht derselbe wie der
CLI-Vergleich oben (iteration-3 gegen iteration-4). In diesem Lauf nannte das Modell keine
Karte, deshalb `relevant_cards=[]` — kein Widerspruch zum CLI-Test, sondern ein anderer Lauf.*

Knoten 2 schlug `[]` vor, Knoten 4 löste über den Tag auf: `['_core.md', 'references.md']`,
23.761 Zeichen, Hash `f913bd6e…`.

**Genau formuliert:** Knoten 2 **schlägt zusätzliche Karten vor** — er lädt nichts und
protokolliert nichts. Knoten 4 **löst diese Vorschläge zusammen mit der deterministischen
Tag-Zuordnung zum tatsächlich verwendeten Kartensatz auf, lädt ihn und protokolliert ihn.**
Beide Wege laufen in `select_cards()` zusammen.

## Deterministischer Regressionstest — die Codeänderung isoliert

Die realen Azure-Läufe zeigen Plausibilität, trennen die Codeänderung aber **nicht** von der
Modellstochastik. Deshalb zusätzlich ein Test, der beiden Fassungen **dieselbe gespeicherte
LLM-Antwort** unterschiebt (`AzureOpenAI` wird in beiden Modulen durch einen Stub ersetzt;
ALT kommt aus `git show HEAD`):

| Feld | ALT | NEU | gleich |
|---|---|---|---|
| `tag_error_type` | `DEMAND_ARTICLE_IDS` | `DEMAND_ARTICLE_IDS` | ✔ |
| `selected_error_index` | 0 | 0 | ✔ |
| `search_mode` / `search_value` | `value` / `100005_NOT_FOUND` | identisch | ✔ |
| `should_investigate` | True | True | ✔ |
| `relevant_cards` | `['references.md']` | `['references.md']` | ✔ |

Prompt identisch (38.137 Zeichen), **0 Abweichungen**, `raw_message` korrekt durchgereicht.
**Bleibt bei identischer Modellantwort kein Unterschied, kann die Extraktion die
entscheidungsrelevanten Ausgaben nicht verändert haben.**
Testskript archiviert: `data/archive/ba-d6-vergleich/regression_deterministisch.py` —
wiederholbar, ohne Azure-Kosten.

- **Was NICHT funktioniert hat:** Mein erster Nachweis zu Punkt 4 war eine **Textsuche über den
  Quelltext** — die schlug an, weil `trigger_identify_tool` im **Docstring** erwähnt wird
  („ruft es NICHT auf"). Ein Test, der Kommentare mitzählt, beweist nichts. Mit einer
  AST-Analyse des tatsächlichen Aufrufbaums wiederholt. **Genau der Fall, vor dem Regel A
  warnt — und er ist mir in derselben Runde passiert, in der ich sie verankert habe.**
- **Offen / nächstes:** **AP-D7** — Knoten 3 (`identify_snapshot`), der Risikoposten:
  ~300 Zeilen Ablaufsteuerung in `main()`, keine Gesamt-Einstiegsfunktion. DoD dort zusätzlich:
  derselbe Suchlauf liefert dasselbe `last_search_results.json` wie vorher.

---

### [BA-023] 2026-08-19 — AP-D7: Knoten 3 · AP-D damit vollständig
- **Status:** done — **alle neun Knoten stehen**, AP-D abgeschlossen
- **Kapitelbezug:** K4 *(MVP-Entscheidung, Verantwortungsschnitt)*, K5 *(Kontrollbedingungen)*,
  K6 *(Datenprovenienz, Befund D)*
- **Literatur:** —
- **Changed files:** `app/tools/smart-planning/runtime/identify_snapshot.py` (additiv),
  `app/tools/smart-planning/graph/nodes/context_search.py` (neu),
  `data/archive/ba-d7-vergleich/` (neu: 22 Vergleichsartefakte), `docs/BA_ARBEITSPAKETE.md`

**Die Entscheidung, die den Risikoposten entschärft hat.** `main()` trägt ~295 Zeilen
Ablaufsteuerung mit drei Modi, verschachtelten Fallbacks (Referenzdaten, Fuzzy-Suche,
Kontextanreicherung) und vielen `return`-Punkten. Diese Logik zu verschieben wäre der
riskanteste Eingriff des ganzen Blocks gewesen — **und für die Forschungsfrage wertlos**:
Knoten 3 soll Kontext liefern und protokollieren, *welchen*. *Wie* die Suche intern arbeitet,
ist nicht Gegenstand des Vergleichs.

Deshalb der vom Masterplan ausdrücklich erlaubte **MVP-Weg** (Kap. 9): das bestehende Skript
**als Ganzes** aufrufen — *„kein Strohmann, weil es derselbe, unveränderte Code ist"*.
`run_context_search()` baut nur die Argumentliste und ruft `main(argv=...)`.

**Der einzige Eingriff — und er war nötig:** `main()` überschrieb `sys.argv` **global**. Beim
CLI-Aufruf harmlos, in-process hätte es **jeden weiteren Schritt im selben Lauf** betroffen.
`main(argv=None)` ist jetzt parametrisierbar; Default `None` = unverändertes CLI-Verhalten,
neun Stellen angepasst, keine globale Mutation mehr. **Nachgewiesen: nach sieben Knotenaufrufen
ist `sys.argv` unverändert.**

## Der geforderte Nachweis

Vorgehen: **erst Baselines**, dann ändern. Sieben Szenarien über **alle drei Suchmodi**, jeweils
mit und ohne Treffer, auf einem eigens angelegten Wegwerf-Snapshot. Kanonisierung:
`json.dumps(sort_keys=True, ensure_ascii=False, separators=(',',':'))`, dann SHA-256.

| Szenario | Modus | Treffer | ALT = NEU (CLI) | ALT = KNOTEN |
|---|---|---|---|---|
| `100005` | value | 16 | ✔ | ✔ |
| `GIBTESNICHT_XYZ` | value | 0 | ✔ | ✔ |
| `--empty demandId` | empty_field | 0 | ✔ | ✔ |
| `--equipment-workitem VOAR01` | equipment_workitem | 0 | ✔ | ✔ |
| `--empty packaging` | empty_field | **9** | ✔ | ✔ |
| `D100005_00` (Fuzzy) | value | **5** | ✔ | ✔ |
| `--equipment-workitem HE01` | equipment_workitem | 0 | ✔ | ✔ |
| `--equipment-workitem VOAR01` *(Nachtrag 20.08.)* | equipment_workitem | **1** | ✔ | ✔ |

**8 Szenarien × 2 Vergleiche = 16 Prüfungen, 0 Abweichungen.** Die erzeugte
`last_search_results.json` ist **byte-identisch** — sowohl über das CLI als auch über die
Knotenfunktion, gemessen gegen die Fassung **vor** der Änderung
(`data/archive/ba-d7-vergleich/identify_snapshot_ALT.py`, deckungsgleich mit `git show HEAD`).

> **Nachtrag 20.08.2026 — zwei Korrekturen an diesem Eintrag.**
> 1. Ursprünglich stand hier **7 Szenarien / 14 Prüfungen**, und für `equipment_workitem`
>    waren **nur Nulltrefferpfade** geprüft. Die Aussage „alle drei Modi mit und ohne
>    Treffer“ war damit **nicht gedeckt**. Szenario 08 schliesst die Lücke: der einzige
>    Snapshot im Repository mit einer echten `workItems`-Anomalie ist
>    `482d71b0-…`, `equipment[334].workItems[0] = 'WORK_ITEM_NOT_AVAILABLE'` (equipmentKey
>    `VAR01`) — gefunden durch Abgleich aller Snapshots gegen `VALID_WORK_ITEM_KEYS` (14 Keys).
> 2. „Byte-identisch“ war zunächst **zu stark**: verglichen wurden kanonisierte SHA-256.
>    Am 20.08. wurden zusätzlich die **Rohbytes** gehasht — alle 8 Szenarien stimmen auch
>    dort überein, erst damit ist das Wort belegt.

Abgedeckt sind damit auch die tiefen Zweige: die Kontextanreicherung (16 Treffer, 119.702
Zeichen Ausgabe), die Fuzzy-Suche, der Leerfeld-Pfad mit echten Treffern und der
Leerergebnis-Pfad, der eine kompatible Ersatzdatei schreibt.

**Was der Knoten zusätzlich leistet — Datenprovenienz.** `extracted_context` hält fest, welche
Pfade tatsächlich im Kontext lagen (`lines_used`, `field_examples`) und den `results_hash` der
vollständigen Ergebnisdatei. **Das fängt Befund D ab:** Dort berief sich ein Vorschlag auf
Artikel „aus Department 20100", während die drei zitierten in 20200 lagen — niemand konnte das
sehen, weil nirgends stand, welches Vergleichskollektiv wirklich im Kontext lag.
Geprüft: 16 Treffer, `lines_used` beginnt mit `articles[0].articleId`, `demands[0].demandId`,
`demands[0].articleId`; `field_examples` = `['articleId','demandId','tnr-ursache-dg']`.
Der **Volltext** bleibt bewusst aus dem `trace` — er kann sechsstellig viele Zeichen umfassen
(Kap. 12.5); Hash, Anzahl und Pfade genügen als Beleg.

**Verantwortungsschnitt umgesetzt:** Bis D6 führte `identify_error_llm.main()` die Suche selbst
aus. Jetzt bestimmt Knoten 2 nur `search_mode` und `search_value`, **Knoten 3 führt sie aus** —
erst dadurch bekommt der Kontext einen eigenen Beobachtungspunkt.

- **Verifikation:** 7/7 Runtime-Skripte und 3/3 Kernmodule importierbar;
  `main(argv=None)` parametrisiert; Grenzfall ohne `search_value` liefert einen Zustand
  („Kein search_value — Knoten 2 hat keinen geliefert") statt eines Absturzes, Exit 0.
- **Was NICHT funktioniert hat:** Nichts Wesentliches. Zwei Sonden lieferten anfangs
  unbrauchbare Ausgaben, weil `identify_snapshot` sehr viel nach stdout schreibt — mit
  `contextlib.redirect_stdout` wiederholt. Ausserdem hatte ich für `--empty demandId` und
  `--equipment-workitem VOAR01` zunächst nur Null-Treffer-Fälle; erst die Suche nach real
  leeren Feldern (`packaging`, 9 Treffer) und ein Fuzzy-Fall haben die tiefen Zweige abgedeckt.
  **Ein Test, der nur den flachen Pfad trifft, beweist wenig.**
- **Offen / nächstes:** **AP-E** — den Graphen verdrahten: `correction_graph.py` mit den neun
  Knoten, beiden bedingten Kanten und der Rückkante 8→2, dazu `_execute_pipeline_graph()` und
  die Mermaid-Abbildung.

---

### [BA-024] 2026-08-20 — D7-Nachprüfung: ein Runtime-Defekt und eine Beweislücke gefunden
- **Status:** done — AP-D7 endgültig geschlossen, AP-E freigegeben
- **Kapitelbezug:** K5 *(Kontrollbedingungen, gemeinsame Reparatur)*, K6 *(Messinstrument,
  Kontextprovenienz)*, K8 *(Limitationen)*
- **Literatur:** L11 *(Turpin et al. — Modellbegründungen sind nicht die Ursache; deshalb muss
  der Code aufzeichnen, welchen Kontext das Modell wirklich sah)*
- **Changed files:** `app/tools/smart-planning/runtime/identify_snapshot.py`,
  `app/tools/smart-planning/graph/nodes/correction.py`, `docs/BA_PROJECT_LOG.md`

Sechs gezielte Nachfragen zu BA-023. Zwei davon haben etwas Substanzielles zutage gefördert;
das rechtfertigt den eigenen Eintrag.

## 1 — `equipment_workitem` mit echten Treffern *(Lücke geschlossen)*

Für diesen Modus waren nur **Nulltrefferpfade** geprüft; die Aussage „alle drei Modi mit und
ohne Treffer" war nicht gedeckt. Abgleich **aller** Snapshots gegen `VALID_WORK_ITEM_KEYS`
(14 Keys) ergab **genau einen** mit echter Anomalie: `482d71b0-…`,
`equipment[334].workItems[0] = 'WORK_ITEM_NOT_AVAILABLE'`, equipmentKey `VAR01`.
Szenario 08 darauf: 1 Treffer, ALT = NEU = KNOTEN, **roh und kanonisch**. Jetzt sind alle drei
Modi mit *und* ohne Treffer belegt (16 Prüfungen statt 14).

## 2 — Prozessbeendende Pfade *(geprüft, sauber)*

`identify_snapshot.py` enthält **kein** `sys.exit`, `parser.error`, `os._exit` oder `quit()`;
`main()` verlässt sich auf `return`. Die einzige Beendigungsquelle ist **argparse**, das bei
kaputten Argumenten `SystemExit` wirft — `run_context_search()` fängt es (`:936`) und liefert
`"Suche abgebrochen (exit N)"`. Belegt an **acht feindlichen Eingaben** (fehlender Snapshot,
unbekannter `search_mode`, `None`, Leerstring, flag-artiger Suchwert `--snapshot-id`, …):
**alle acht durchlaufen, Prozess lebt, Gesamt-Exit 0.** Der flag-artige Wert löste tatsächlich
`exit 2` aus und wurde korrekt zu einem Zustand.

## 3 — Der Defekt, den dieser Test aufgedeckt hat

Bei den feindlichen Eingaben meldete eine Suche über ein **nicht existierendes Leerfeld**
`results_count: 16` und `error_type: DUPLICATE_ID` — die Werte der Suche **davor**.

Ursache in [`identify_snapshot.py:1248`](../app/tools/smart-planning/runtime/identify_snapshot.py#L1248):
die Leerergebnis-Datei wurde nur geschrieben, **wenn noch keine existierte**
(`if not results and not storage.exists(...)`). Fand eine spätere Suche nichts, blieb die Datei
der vorigen stehen — und der nächste Schritt las sie als aktuellen Kontext.

Isoliert nachgestellt: Suche A (`value 100005`) → 16 Treffer, `results_hash 6d538551…`;
danach Suche B (`empty_field gibtesnichtXY`) → **derselbe Hash**. Ohne Altdatei: 0 Treffer.

**Warum das den Vergleich zerstört hätte.** Nicht nur den Graphen: `sp_agent.execute_pipeline()`
iteriert (`:702`, `while True`, `MAX_CORRECTION_ITERATIONS`) und `identify_error_llm.py:504`
stösst **je Iteration** eine neue Suche an. Der Monolith ist also **genauso betroffen** — ab
Iteration 2 hätte das Modell den Kontext der Iteration davor bekommen und ihn für aktuell
gehalten. Für UF1 wäre das eine Halluzination, die das System gar nicht verschuldet hat.

**Deshalb Reparatur in der gemeinsamen Runtime, nicht im Knoten** (CLAUDE.md, Bauregel B:
*„Ist es eine Reparatur, gehört sie in die gemeinsame Runtime, damit A, B und C sie
gleichermassen bekommen"*). Sie im Knoten abzufangen hätte C einen Vorteil verschafft, der
später wie ein Architektureffekt ausgesehen hätte. Zweite Änderung derselben Stelle: die
Leerdatei landet jetzt auch im Iterationsordner — die beiden anderen Zweige taten das längst.
`last_search_results.json` bedeutet ab jetzt ausnahmslos *Ergebnis der zuletzt ausgeführten
Suche*.

**Beleg, dass die Reparatur nichts anderes anfasst:** alle **8 Szenarien nach der Reparatur
erneut gegen die archivierten ALT-Stände**, roh und kanonisch — **0 Abweichungen**. Und der
Defekt selbst ist weg: Suche B liefert jetzt `47a850ce…` statt `6d538551…`, `NO_RESULTS_FOUND`,
0 Treffer.

> **Eingriff in die Produktionssemantik — bitte gegenlesen.** Wer `identify_snapshot` über MCP
> mit einem falschen Suchbegriff aufruft, überschreibt jetzt den vorher gefundenen Kontext,
> statt ihn stehen zu lassen. Das ist gewollt, aber es ist eine Verhaltensänderung. Wir sind
> **vor** dem Einfrieren (AP-G), also ist der Zeitpunkt richtig; ein Veto ist bis dahin möglich.

## 4 — Die Beweislücke bei `results_hash`

Die Forderung war: `results_hash` aus Knoten 3 muss **exakt** dem Kontext entsprechen, den
Knoten 5 bekommt. Er tat es **nicht**. Knoten 5 übergab `search_results` nicht, also lud
`run_correction_generation()` die Datei **ein zweites Mal von Platte**
(`generate_correction_llm.py:930`). Der Hash beschrieb damit einen früheren Dateizustand, nicht
den Modelleingang — eine Behauptung, keine Zusicherung. Zusammen mit Defekt 3 war das
gefährlich: genau dazwischen konnte sich der Dateiinhalt ändern.

Behoben nach demselben Muster wie beim Regeltext aus Knoten 4:
* `identify_snapshot.context_sha256(obj)` — **eine** Serialisierungsstelle. Knoten 3 bildet
  damit `results_hash`, Knoten 5 `context_input_sha256`. Zwei eigene Serialisierungen hätten
  Serialisierungen statt Inhalte verglichen.
* Knoten 3 legt das geladene Objekt als `results_object` in den State.
* Knoten 5 übergibt **genau dieses** als `search_results=` und schreibt
  `context_input_sha256` sowie `context_handoff_ok` in den Trace.

**Regel-B-Nachweis, dass C dadurch nichts gewinnt:** der Modellaufruf wurde abgefangen und der
**vollständige Prompt** gehasht — Nachladen von Platte gegen Durchreichen:
`a4b55f4d…` = `a4b55f4d…`, **205.573 Zeichen, identisch**. Es ist eine Provenienzzusicherung,
keine zusätzliche Fähigkeit. Ergänzend: `load_search_results()` ist ein reines Laden ohne
Nachbearbeitung, und das durchgereichte Objekt ist tief gleich zum nachgeladenen.

## 5 — Falsche Zahl in BA-021 *(korrigiert, siehe dort)*

*„7 Fehler-Tags × 2 Modi: 16 Vergleiche"* — schon arithmetisch falsch. Statt nachzurechnen neu
gemessen: **21 Fälle × 2 Modi = 42 Vergleiche, 0 Abweichungen**. Dabei fiel ein **Fehler im
Prüfaufbau** auf, der den ursprünglichen Wert ohnehin entwertet hätte: der Moduswechsel per
`importlib.reload()` greift nicht, weil `RULEBOOK_MODE` aus `agent_config` stammt — der erste
Versuch mass **zweimal `cards`**. Erst getrennte Prozesse je Modus messen beide. Gegenprobe:
`cards` → 12 verschiedene Regeltextlängen, `monolith` → genau eine.

## 6 — Kante 6→5 *(bestätigt gestrichen)*

Keine Fundstelle sieht sie noch vor. Masterplan Kap. 11 führt sie ausdrücklich als gestrichen
(`:1131–1149`), `evaluation.py:35` verweist darauf. Verbindlich für AP-E:
`schema_valid == True → [7]`, `False → [8] → "stop_uncertain"`. Technische Retries bleiben
**vollständig** in Knoten 6 (`validate_with_retry()`); eine Graph-Kante wäre eine zweite
Retry-Schicht über der bestehenden und würde die Retry-Zahl zwischen den Bedingungen
ungleich machen.

- **Was NICHT funktioniert hat:**
  * **Der Robustheitstest war als Formsache gedacht** und hat den schwersten Fund des Tages
    geliefert. Die acht feindlichen Eingaben liefen nacheinander auf demselben Snapshot — nur
    deshalb fiel der veraltete Kontext auf. Wäre jeder Fall auf einem frischen Snapshot
    gelaufen, wäre der Defekt unentdeckt in die Messläufe gegangen. **Zustand zwischen
    Testfällen absichtlich nicht zurücksetzen** ist ein Prüfmittel, kein Schlamperei-Risiko.
  * **Zwei Ankerblöcke für Textersetzungen erneut danebengegriffen** (Muster 5): einmal, weil
    ich „für" als `fuer` geschrieben hatte, während im Code der Umlaut steht; einmal, weil
    ein Here-Doc mit Umlauten unter cp1252 dekodiert wurde. Abhilfe: `PYTHONUTF8=1` und
    `\uXXXX`-Escapes statt Umlauten im Skript.
  * **`importlib.reload()` als Weg, einen Schalter umzustellen** — funktioniert nicht, wenn der
    Schalter aus einem anderen Modul importiert wurde. Das hat schon BA-021 verdorben und wäre
    fast ein zweites Mal passiert. **Schalterabhängige Läufe gehören in getrennte Prozesse**,
    und der effektiv gültige Wert gehört mit ausgegeben.
  * Kein Nachweis erbracht, **wie häufig** der Kontext-Defekt real gegriffen hat. Er setzt
    Iteration ≥ 2 mit einer treffernlosen Folgesuche voraus; ob das in den 17 Messfällen
    vorkommt, ist unbekannt. Für K8 ehrlich als **nicht quantifiziert** führen.
- **Offen / nächstes:** **AP-E** — `correction_graph.py`: neun Knoten, zwei bedingte Kanten,
  Rückkante 8→2, `_execute_pipeline_graph()`, Mermaid-Abbildung. Dabei beachten:
  `extracted_context` trägt jetzt mit `results_object` den vollen Suchkontext; beim Ablegen der
  Rohdaten (Regel 7) muss entschieden werden, ob er in die Trace-Datei gehört oder nur sein Hash.

---

### [BA-025] 2026-08-20 — Vollaudit AP-0 bis AP-D: 9 Auffälligkeiten, davon 2 schwer
- **Status:** done — Prüfung abgeschlossen, **Befunde nicht behoben** (bewusst: erst Entscheidung)
- **Kapitelbezug:** K5 *(Kontrollbedingungen, Umgebungskontrolle)*, K6 *(Rohdaten, Messinstrument)*,
  K8 *(Limitationen)*
- **Literatur:** L11 *(Turpin et al. — was der Code aufzeichnet, zählt; nicht was er behauptet)*
- **Changed files:** nur `docs/BA_PROJECT_LOG.md`, `docs/BA_ARBEITSPAKETE.md` *(Code unangetastet)*

Vollständige Nachprüfung aller Häkchen von AP-0 bis AP-D gegen den realen Zustand. **Freigabe
vorab notiert:** Das Überschreiben von `last_search_results.json` bei einem neuen Nulltreffer ist
vom Nutzer ausdrücklich freigegeben — die Datei repräsentiert *die letzte Suche*, nicht *die
letzte erfolgreiche*. Damit ist BA-024 Punkt 3 abgeschlossen.

## Was der Prüfung standgehalten hat

| Punkt | Womit geprüft | Ergebnis |
|---|---|---|
| 0.1 venv | `sys.prefix != sys.base_prefix` | ✔ Python 3.13.3, `.venv/` in `.gitignore:2` |
| 0.1.2 | `pip check` | ✔ „No broken requirements found" |
| 0.2.2 | `data/archive/ba-ap0-20260819/` | ✔ 4 `pip freeze`-Stände, DB- und Ergebnis-Backups |
| A1 | `agent_config.py:76-86`, Guard-Suche über `app/` | ✔ strikt geparst, **genau ein** Guard (`retrieval.py:72`) |
| A2 | `pip list` gegen `requirements.txt:22-23` | ✔ `langgraph 1.2.11`, `langchain-core 1.5.6` exakt wie gepinnt |
| A2-Tabu | Volltextsuche `ChatOpenAI\|AzureChatOpenAI\|create_react_agent\|RetryPolicy\|from langchain` | ✔ **0 Treffer** im Projektcode |
| B3 | `MANIFEST.json` | ✔ Regelwerk-SHA, 14 Karten gehasht, echter Prompt (222.931 Z.), 3 Bedingungen, Modellversion, Paketversionen |
| C1/C3 | 9 Läufe, je 2 gültige + 1 Tippfehler pro Schalter | ✔ alle drei brechen mit `ValueError` ab |
| C2 | `sp_agent.py:691` | ✔ greift nur bei `graph` **und** Korrektur-Pipeline |
| C4 | `typing.get_type_hints(GraphState)` | ✔ **genau 18** Felder; `new_state()` belegt 10, die übrigen 8 sind `total=False` |
| C-DoD | `_execute_pipeline_graph()` | ✔ saubere Struktur statt Absturz |
| D1/D2/D3/D6 | AST: ruft `main()` die extrahierte Funktion? | ✔ delegiert, keine Doppelung |
| D7 | AST | ✔ Umkehrung dokumentiert (MVP) |
| Sonstiges | `git ls-files`, Volltextsuche | ✔ `.env` nicht getrackt, **kein** Snapshot-Löschcode, 3 überholte Pläne entfernt, 8/8 Knotenmodule importierbar, alle Dateien kompilieren |

**Eigene Fehlmeldung korrigiert:** Mein erster Zähler meldete für
`validate_correction_schema_llm.py` eine Abweichung bei den Exit-Codes (4→5). Falsch — er hatte
**Docstring-Erwähnungen** mitgezählt. Echte Codestellen: **4 = 4, unverändert.**

---

## F1 ⚠⚠ Es gibt ZWEI virtuelle Umgebungen mit unterschiedlichem `pydantic`

**Der schwerste Befund.** Neben `.venv/` (angelegt 19.08. 13:54) existiert
**`app/.venv/` seit dem 04.01.2026**:

| | `.venv` | `app/.venv` |
|---|---|---|
| erstellt | 19.08.2026 13:54 | **04.01.2026 16:04** |
| `pydantic` | **2.13.4** | **2.12.5** |
| `langgraph` | 1.2.11 | **fehlt** |
| `openai` | 1.109.1 | 1.109.1 |

**Damit ist die Prämisse von AP-0.1 sachlich falsch.** Dort steht: *„Befund 19.08.2026: Es gibt
keine venv."* Es gab eine — sieben Monate alt, eine Ebene tiefer.

**Warum das den Vergleich bedroht.** `pydantic` liegt an **drei** Stellen im gemessenen Pfad,
nicht an einer: `generate_correction_llm.py:29` (`CorrectionProposal`),
`validate_correction_schema_llm.py:24` (`LLMCorrectionResponse`, Knoten 6 —
`LLMCorrectionResponse(**correction_proposal)` in Zeile 35) und `apply_correction.py:23`.
Ein Versionsunterschied ändert potenziell, **welcher Vorschlag als schemagültig gilt** — also
direkt Kategorie 2. Und `sp_agent.py:81` reicht `sys.executable` an **alle** Subprozesse weiter:
welcher Interpreter den Agenten startet, entscheidet still über die gesamte Messkette.

Genau davor warnt der Kasten „AP-A vor AP-B" — *„laufen die beiden Varianten unter verschiedenen
Bibliotheksversionen — ein konfundierender Faktor"*. Die Falle war beschrieben und stand
trotzdem offen.

**Was belegt ist und was nicht.** Belegt: die Baseline-Artefakte stammen aus der Wurzel-`.venv` —
`MANIFEST.json` führt `pydantic 2.13.4` und `langgraph 1.2.11`, was nur dort zutrifft.
**Nicht belegt:** dass die *Läufe selbst* denselben Interpreter benutzten, denn keine
Ergebnisdatei hält `sys.executable` fest (siehe F2). Die Umgebung ist also plausibel, aber
**nicht nachweisbar** dieselbe.

> **Empfehlung, Entscheidung liegt beim Nutzer.** (a) In jede Lauf-Metadatenzeile
> `sys.executable`, `pydantic.VERSION` und `sys.version` aufnehmen — das schliesst die Lücke
> dauerhaft. (b) `app/.venv` vor AP-G umbenennen oder entfernen, damit sie nicht versehentlich
> greift. **(b) ist ein Löschvorgang und wird nicht ohne ausdrückliche Zustimmung ausgeführt.**

## F2 ⚠⚠ Die Regressionsreferenz hat keine Lauf-Metadaten

`data/archive/ba-baseline-artefakte-20260819/B2-regressionsreferenz.json` ist eine **blanke Liste
von 5 Bewertungszeilen**. Schlüssel je Zeile: `code`, `context`, `detected`, `frag_ok`,
`count_ok`, `target_path`, `gt_jsonpath`, `field_ok`, `new_value`, `correct_value`, `value_ok`,
`snapshot_id`. **Kein Zeitstempel, kein Modell, keine Temperatur, kein `rulebook_mode`, kein
`memory_mode`, kein Interpreter.**

Das ist wörtlich der Defekt, den CLAUDE.md als bekannte Falle führt: *„Bestehende Ergebnisdateien
sind keine Rohdaten. `pt4-eval-results.json` … enthalten weder Zeitstempel noch Modell,
Temperatur oder Modus."* **Die neue Datei wiederholt ihn.** Harte Regel 7 verlangt je Lauf
Zeitstempel, Variante, Fall-ID, Modell + Version und Parameter.

Das `MANIFEST.json` deckt die Umgebung **global** ab und ist gut gemacht — aber es steht neben
der Ergebnisdatei, nicht darin. Wer später eine Zeile prüfen will, kann sie keinem Lauf zuordnen.

> **Vor AP-H zwingend:** `run_isolated_suite.py` muss je Zeile Zeitstempel, alle drei Schalter,
> Modell + gemessene Version, Temperatur und `sys.executable` mitschreiben. Sonst sind die
> Messdaten aus AP-H genauso wenig verwertbar wie die aus PT4.

## F3 ⚠ Zwei Skripte haben doppelte Implementierungen statt Delegation

Das AP-D-Muster lautet *„neue aufrufbare Funktion, `main()` ruft sie auf"* — bei zwei von sieben
Skripten ist es nicht umgesetzt:

| Datei | `main()` | extrahierte Funktion | Beziehung |
|---|---|---|---|
| `update_snapshot.py` | 271–368 (97 Z.) | `run_upload()` 223–268 (45 Z.) | **parallel** |
| `generate_audit_report.py` | 350–400 (50 Z.) | `run_audit_report()` 321–347 (26 Z.) | **parallel** |

Beide `main()` bauen die Kernlogik selbst nach: laden, `parse_metadata()`, `SmartPlanningAPI`,
speichern. Heute verhalten sie sich gleich — aber sie sind **zwei Wege durch dieselbe Aufgabe**.

**Warum das die Forschungsfrage berührt:** A und B laufen über `main()` (Subprozess aus
`sp_agent`), C über `run_*()`. Jede spätere Änderung an einem der beiden Wege erzeugt einen
Unterschied, der in den Ergebnissen wie ein **Architektureffekt** aussieht, ohne einer zu sein —
genau der Fall, den Bauregel B verhindern soll. Masterplan Kap. 12.2 fordert *„eine
Implementierung, kein Drift"*.

> **Empfehlung:** `main()` auf `run_upload()` bzw. `run_audit_report()` umstellen und nur die
> CLI-Hülle behalten (Argumente, `current_snapshot.txt`-Fallback, Banner, Exit-Codes) — wie in
> D1/D2/D6 bereits gelöst. Danach die CLI-Gleichwertigkeit erneut belegen.

## F4 ⚠ Zwei Eval-Skripte erzwingen `cards` hart — AP-H-Blocker

* `run_combined_suite.py:97` — `e = {**os.environ, "RULEBOOK_MODE": "cards", …}`
* `run_iterative.py:33` — identisch

Das Literal steht **hinter** `os.environ` und gewinnt. Ein `RULEBOOK_MODE=monolith` von aussen
verpufft wirkungslos. Nur `run_isolated_suite.py` wurde in AP-B entschärft (Default `cards`, aber
überschreibbar).

Das trifft direkt auf einen bereits bekannten offenen Punkt: **die isolierte Suite fährt nur
`identify` + `generate`**, nicht die volle Pipeline mit Anwendung und Re-Validierung. Der Runner
für AP-H wird also einer der beiden anderen sein — und der würde **Bedingung A unbemerkt unter
`cards` messen**, also gar nicht Bedingung A. Zusätzlich setzt keines von beiden `MEMORY_MODE`;
ohne äussere Vorgabe greift der Default `on` — die als wichtigste bezeichnete Falle.

> **Vor AP-H zwingend**, zusammen mit dem ohnehin offenen Punkt „Runner für die volle Pipeline".

## F5 Der falsche Kopfkommentar steht immer noch da

`app/core/rulebook_loader.py:6` behauptet weiterhin `"monolith" (default)`. Der tatsächliche
Default ist `cards` (`agent_config.py:40`). CLAUDE.md führt genau das seit dem 16.08. als bekannte
Falle — **korrigiert wurde es nie.** Eine Zeile, aber sie steht in der Datei, die beim Einfrieren
gelesen wird.

## F6 Knoten 1 hat keine Datei — Lücke in der Paketbuchhaltung

`graph/nodes/` enthält 8 Module (2–9). Der Masterplan definiert **neun** Knoten; Knoten 1
(*Eingabeanalyse*, „dünner Wrapper, **kein LLM-Call**") hat *„kein dedizierter Code"*.
AP-D deckt ausdrücklich nur D1–D7 = Knoten 2–9 ab; **AP-E E1 setzt „neun Knoten registrieren"
voraus, ohne dass Knoten 1 irgendwo gebaut würde.** Kein Fehler, aber E1 muss ihn mit erledigen —
sonst fällt es beim Verdrahten auf.

## F7 Undokumentierte stdout-Abweichung in `apply_correction.py`

11 von 12 Ausgabezeilen sind identisch zum Stand vor AP-D. Eine hat sich geändert:
`"  ✓ Schema is valid"` → `"  OK Schema is valid"`. Plausibel wegen cp1252 auf der
Windows-Konsole, aber die AP-D-DoD nennt **stdout** ausdrücklich, und im Protokoll steht es
nicht. Der Exit-Vertrag bleibt gewahrt: neu `sys.exit(1)` in `main()` nach `run_apply()`, vorher
brach eine Ausnahme mit demselben Code ab.

## F8 `requirements.txt` pinnt nur zur Hälfte

`langgraph==1.2.11` und `langchain-core==1.5.6` sind exakt. `openai>=1.6.0,<2.0.0` und
`pydantic>=2.0.0` sind offen. Für das Einfrieren in AP-G heisst das: eine Neuinstallation kann ein
anderes `pydantic` ziehen — und das liegt laut F1 im Schemapfad von Knoten 6.

> **Empfehlung:** vor AP-G alle Pakete des gemessenen Pfads exakt pinnen (`pip freeze` als
> `requirements-frozen.txt` neben die bestehende Datei legen, damit Produktion unberührt bleibt).

## F9 Kleinigkeit

`data/archive/__pycache__/` liegt im Archivordner. Harmlos, aber ein Archiv sollte nur Artefakte
enthalten.

---

- **Was NICHT funktioniert hat:**
  * **Mein Zähler für Exit-Codes war falsch gebaut** — er zählte Docstring-Text mit und meldete
    eine Abweichung, die es nicht gibt. Erst der Blick auf die konkreten Zeilen klärte es.
    Lehre: bei Codevergleichen **AST oder Zeilennummern**, keine Vorkommenszählung.
  * Ein rekursiver Glob über das ganze Repository (`**/pt4.sqlite3`) lief in den 180-s-Timeout.
    Bei Suchen im Repo immer den Pfad einschränken.
  * Ein Volltext-Grep über `app/` traf **`app/.venv/`** mit hunderten Fremdtreffern — und genau
    dadurch fiel F1 überhaupt auf. **Ein zu breiter Suchlauf war hier der Glücksfall**, nicht der
    Fehler; ohne ihn wäre die zweite venv unbemerkt geblieben.
  * **Nicht geprüft:** ob die B2-Läufe faktisch mit der Wurzel-`.venv` liefen. Das lässt sich
    nachträglich **nicht** feststellen, weil die Ergebnisdatei den Interpreter nicht festhält
    (F2). Für K8 ehrlich als nicht rekonstruierbar führen.
  * **Nicht geprüft:** die CLI-Gleichwertigkeit von D1–D5 durch echte Läufe. Verglichen wurden
    Argumentoberfläche, Exit-Stellen und stdout-Zeilen gegen `git show HEAD` — **statisch, nicht
    dynamisch.** Für D2/D6/D7 liegen dagegen echte Laufvergleiche per SHA-256 vor.
- **Offen / nächstes:** Entscheidung über F1–F4. **F2 und F4 blockieren AP-H**, F3 sollte vor
  AP-E fallen (danach wird der Graph auf `run_*()` verdrahtet und die Doppelung zementiert).
  F5/F7/F9 sind Einzeiler. Erst danach AP-E.

---

### [BA-026] 2026-08-20 — Auditbefunde bereinigt · AP-D-Gesamtsmoke deckt zwei Kettenbrüche auf
- **Status:** done — F1, F2, F3, F5, F6, F7, F9 erledigt; F4 und F8 bewusst nach AP-H/AP-G verschoben
- **Kapitelbezug:** K4 *(Knoten 1, Verantwortungsschnitt)*, K5 *(Umgebungskontrolle, gemeinsame
  Implementierung)*, K6 *(Rohdaten, Handoff-Nachweise)*, K8 *(Limitationen)*
- **Literatur:** L11 *(Turpin et al. — der Code muss aufzeichnen, was tatsächlich geschah)*
- **Changed files:** `app/core/run_metadata.py` *(neu)*,
  `app/tools/smart-planning/graph/nodes/input_analysis.py` *(neu)*, `…/nodes/classification.py`,
  `…/nodes/apply_revalidate.py`, `…/runtime/update_snapshot.py`,
  `…/runtime/generate_audit_report.py`, `…/runtime/apply_correction.py`,
  `app/core/rulebook_loader.py`, `app/eval/run_isolated_suite.py`,
  `docs/BA_ARBEITSPAKETE.md`, `docs/BA_PROJECT_LOG.md`

---

## F1 + F2 — Zwei Umgebungen, keine Lauf-Metadaten

**Befund.** `.venv/` (Wurzel, 19.08.) und `app/.venv/` (04.01.) unterscheiden sich in
`pydantic` (2.13.4 gegen 2.12.5); `langgraph` fehlt in der zweiten. `pydantic` liegt an **drei**
Stellen im gemessenen Pfad (`generate_correction_llm.py:29`,
`validate_correction_schema_llm.py:24`, `apply_correction.py:23`) und entscheidet in Knoten 6
mit, welcher Vorschlag als schemagültig gilt. `sp_agent.py:81` vererbt `sys.executable` an alle
Subprozesse. Zugleich hielt keine Ergebnisdatei fest, unter welchem Interpreter sie entstand.

**Entscheidung.** Vor der Festlegung wurde repositoryweit geprüft, ob etwas funktional an
`app/.venv` hängt:

| Fundstelle | Art | Wirkung |
|---|---|---|
| `app/README.md:30` | Installationsanleitung (`cd app; python -m venv .venv`) | Doku |
| `app/eval/check_doku_links.py:4`, `check_doku_stimmt.py:3` | Docstring-Beispiele | Doku |
| `.claude/settings.json` | Berechtigungseinträge | keine Laufzeitwirkung |
| `app/deploy/Dockerfile` | Python 3.11-slim, **ganz ohne venv** | Produktion unberührt |
| `.github/workflows/*.yml` | kein `setup-python` | CI baut nur das Image |

Keine `launch.json`, keine `tasks.json`, kein `defaultInterpreterPath`. **Nichts hängt
funktional daran.** Die Wurzel-`.venv` ist damit die verbindliche BA-Messumgebung;
`app/.venv` bleibt als historische PT4-Entwicklungsumgebung **erhalten** (nicht gelöscht).

**Änderung.** `app/core/run_metadata.py` (neu, additiv — kein Produktionscode importiert es):
`collect_run_metadata()` liefert Zeitstempel, `sys.executable`, `sys.prefix`, `sys.base_prefix`,
Python-Version, die Versionen von `pydantic`/`openai`/`langgraph`/`langchain-core`/`requests`,
`ba_env_ok`, alle vier Schalter, Deployment, API-Version, Temperatur **mit Fundstelle**
(`generate_correction_llm.py:753`) sowie Git-Commit und Sauberkeit des Arbeitsbaums.
Geheimnisse bleiben draussen: Endpunkt und Schlüssel werden bewusst nicht aufgenommen.
`warn_if_wrong_env()` warnt sichtbar, **blockiert aber nicht** — ein Lauf soll nicht daran
scheitern, dass er dokumentiert werden will.

`run_isolated_suite.py` bekam `--with-metadata`. **Default aus**, damit jeder PT4-Aufruf
byte-gleiche Ausgaben behält (harte Regel 1); ohne den Schalter weist das Skript jetzt selbst
darauf hin, dass die Datei als BA-Rohdatum nicht verwertbar ist.

**Regression.** Dieselbe Funktion in beiden Umgebungen aufgerufen: Wurzel → `ba_env_ok: true`,
`pydantic 2.13.4`, `langgraph 1.2.11`. `app/.venv` → Warnbanner, `ba_env_ok: false`,
`pydantic 2.12.5`, `langgraph: null`. Der Mechanismus erkennt also genau den Fall, für den er
gebaut ist.

**B2 unter der festgelegten Umgebung neu erhoben.**
`data/archive/ba-b2-neu-20260820/B2-regressionsreferenz.json`, Bedingung **A**
(`RULEBOOK_MODE=monolith`, `MEMORY_MODE=off`, `HUMAN_IN_THE_LOOP=false`), fünf Fälle
I01/I02/I05/I07/I10 — dieselben wie am 19.08.

Der Metadatenkopf trägt jetzt: Zeitstempel `2026-08-20T10:05:06Z`, `ba_env_ok: true`
(`\.venv`), Python 3.13.3, `pydantic 2.13.4`, `langgraph 1.2.11`, alle vier Schalter,
`gpt-4.1` / `2025-01-01-preview` / T=0.3, Git-Commit `3ed63bf10102` samt Hinweis, dass der
Arbeitsbaum nicht sauber war (20 geänderte Dateien — die Bereinigung dieser Runde).

**Ergebnis: 5/5 erkannt, 4/5 richtiges Feld, 3/5 exakter Wert.** Gegen den Stand vom 19.08.
Fall für Fall verglichen — `detected`, `field_ok`, `value_ok` **und** der vorgeschlagene Wert:

| Fall | Tag | ggü. 19.08. | Vorschlag |
|---|---|---|---|
| I01 | `validate_unique_ids` | unverändert | `D100005_002` gleich |
| I02 | `validate_demand_article_ids` | unverändert | `100005` gleich |
| I05 | `validate_article_department_presence` | unverändert | `20200` gleich |
| I07 | `validate_work_item_configs_completeness` | unverändert | gleich |
| I10 | `validate_packaging_references` | unverändert | `['ACO04']` gleich |

**0 Abweichungen in 5 Fällen.** Die Eingriffe dieser Runde haben das fachliche Verhalten
nicht verändert — und genau das ist die Frage, die eine Regressionsreferenz beantwortet.
Die alte Datei bleibt als historischer Stand liegen; **B2 ist und bleibt Regressionsreferenz,
kein wissenschaftliches Ergebnis** (AP-B-Kasten vom 19.08.).

---

## F3 — Doppelte Implementierungen

**Befund.** In `update_snapshot.py` (main 97 Z. gegen `run_upload()` 45 Z.) und
`generate_audit_report.py` (main 50 Z. gegen `run_audit_report()` 26 Z.) war die Kernlogik
zweimal vorhanden. A/B laufen über `main()`, C über `run_*()`.

**Entscheidung.** `main()` wird zur reinen CLI-Hülle (Argumente, `current_snapshot.txt`-Fallback,
Banner, Exit-Codes). Die Fortschrittsausgaben wandern **in** die `run_*()`-Funktionen — nur so
sieht der CLI-Pfad dieselben stdout-Zeilen wie vorher **und** beide Pfade verhalten sich gleich.
`run_upload()` bekam zusätzlich strukturierte Fehlerangaben (`fehler_art`, `http_status`,
`http_text`), damit `main()` die alten Fehlermeldungen wortgleich reproduzieren kann.

**Regression.** Vier CLI-Läufe je Fassung auf einem Wegwerf-Snapshot und einer nicht
existierenden ID, stdout **und** Exit-Code verglichen:

| Skript / Fall | Ergebnis |
|---|---|
| `generate_audit_report` / vorhandener Snapshot | **identisch** |
| `generate_audit_report` / unbekannte ID | **identisch** |
| `update_snapshot` / unbekannte ID | **identisch** |
| `update_snapshot` / vorhandener Snapshot | dieselben Zeilen, **eine Umordnung** |

Die Umordnung: `save_upload_result()` läuft jetzt vor dem Fehlerbanner statt danach, weil die
CLI die Reihenfolge nicht mehr besitzt. Exit-Code (1) und erzeugtes Artefakt
(`upload-result.json`) sind gleich. Geprüft, dass das folgenlos ist: niemand parst dieses
stdout — `_read_snapshot_metadata_from_stdout()` in `sp_agent.py` gilt nur für
`rename_snapshot` und `identify_snapshot`, und `sp_agent` wertet sonst nur `returncode` aus.

**Nebenbefund beim Umbau — ein Knoten, der den Graphen töten konnte.** `run_audit_report()`
fing nur `except Exception`. `load_metadata()` (`:54`) und `load_snapshot_id()` (`:37`) rufen
aber `sys.exit(1)`, und **`SystemExit` erbt von `BaseException`, nicht von `Exception`**. Der
Docstring behauptete „Beendet den Prozess NIE" — der Code hielt es nicht ein. Ein fehlendes
`metadata.txt` hätte den gesamten Graphlauf beendet. Jetzt wird `SystemExit` mitgefangen;
belegt: Rückgabe `Abbruch aus dem Runtime-Skript (exit 1)`, Prozess lebt, zweiter Aufruf
funktioniert.

---

## F5 / F7 / F9

* **F5** `rulebook_loader.py:6` sagte seit dem 16.08. fälschlich `"monolith" (default)`. Jetzt
  `"cards" (DEFAULT)`. Der tatsächliche Default steht in `agent_config.py:40`.
* **F7** `apply_correction.py:556` sagte `OK Schema is valid` statt `✓ Schema is valid`.
  Zurückgesetzt, nachdem geprüft war, dass kein Grund dagegen spricht: `sp_agent.py:109` setzt
  für Subprozesse `PYTHONIOENCODING=utf-8` **und** `PYTHONUTF8=1`, und dieselbe Datei druckt
  `✓` an sieben weiteren Stellen.
* **F9** `data/archive/__pycache__/` entfernt.

---

## F6 — Knoten 1 gebaut

**Befund.** `graph/nodes/` enthielt acht Module. AP-D deckte die Knoten 2–9 ab; Knoten 1
(*Eingabeanalyse*) hatte laut Masterplan „kein dedizierter Code" und fiel durch die
Paketbuchhaltung. Die Aussage „alle neun Knoten stehen" aus BA-023 war damit **nicht gedeckt**.

**Änderung.** `graph/nodes/input_analysis.py`. **Kein LLM, keine neue Fachlogik.** Er liest die
Validierungsmeldungen mit **wörtlich derselben Vorrangregel** wie der Monolith
(`sp_agent.py:552`: zuerst `iteration-N/snapshot-validation.json`, sonst die Ebene darüber),
zählt ERROR und WARNING, zieht die `[validate_*]`-Tags und schreibt `validation_result` sowie
`errors_before`. Er **triggert keine Validierung** — das ist ein Pipeline-Schritt, den AP-E
genauso verdrahtet, wie der Monolith ihn heute führt; sonst hätte C eine Validierung mehr
als A und B.

**Regression.** Gegen die Zählweise des Monolithen geprüft: beide 1 ERROR, Tag
`validate_unique_ids`. Fehlt die Datei, bleibt `errors_before` auf **`None`, nicht `0`** —
dieselbe Unterscheidung wie bei `errors_after`. Die Meldungen selbst bleiben aus dem Trace.

---

## Der AP-D-Gesamtsmoke — und was er gefunden hat

Neun Knoten als Kette, **ohne LangGraph**, auf einem frisch erzeugten Testinstanz-Snapshot
(Fall I01, doppelte Demand-ID), unter `RULEBOOK_MODE=cards`, `MEMORY_MODE=off`,
`HUMAN_IN_THE_LOOP=false`. 16 Konsistenzprüfungen über State-Handoffs, Regel-Hash,
Kontext-Hash, Vorschlags-Hash, Schemaergebnis, Re-Validierung und Entscheidung.
**Entwicklungslauf, kein Messergebnis.**

**Durchgang 1: 11 von 15, zwei Abstürze.** Zwei echte Kettenbrüche:

**(1) Knoten 1 → Knoten 2, Formkollision.** Knoten 2 reichte `state["validation_result"]`
unverändert an `run_classification()` weiter — das erwartet die **rohe Meldungsliste**, bekam
aber Knoten 1s strukturiertes Dict, iterierte über dessen **Schlüssel** und brach mit
`AttributeError: 'str' object has no attribute 'get'` ab. Danach lief die ganze Kette leer
weiter: kein Tag, kein Suchmodus, kein Kontext, kein Vorschlag, `schema_valid=False`,
`stop_uncertain`. **Jeder Knoten für sich war grün.** Knoten 2 ist jetzt formtolerant (Dict aus
Knoten 1, rohe Liste von der Rückkante 8→2, oder nichts).

**(2) Knoten 6 und Knoten 7 fällten gegensätzliche Schemaurteile.** Knoten 6 meldete
`schema_valid=True`, Knoten 7 brach mit `apply: Schemaprüfung abgebrochen (exit 1)` ab —
**bei jedem Lauf**. Ursache: Knoten 7 baute die Hülle selbst als
`{"correction_proposal": vorschlag}`. `LLMCorrectionResponse` verlangt aber **fünf**
Pflichtfelder; vier fehlten (`iteration`, `snapshot_id`, `original_error`, `error_analyzed`),
einzeln nachgewiesen über `ValidationError.errors()`. `apply_correction.validate_proposal_schema()`
(`:83`) prüft genau dieses Modell und ruft bei Verstoss `sys.exit(1)`.
**Der Graph-Pfad konnte also nie anwenden** — und damit wären Kategorie 4 (Folgefehler) und
jede `errors_after`-Zahl in Bedingung C strukturell unmessbar gewesen.

Behoben so, dass C **keinen Sonderweg** bekommt: Knoten 7 lädt die vollständige Hülle über
`apply_correction.load_correction_proposal()` — dieselbe Quelle, die A und B über die CLI
benutzen — und prüft, dass ihr innerer Vorschlag mit dem State übereinstimmt
(`proposal_identisch` im Trace). Weichen sie ab, wird **nicht** angewendet. Die
Staleness-Sorge, wegen der ursprünglich aus dem State übergeben wurde, ist damit beantwortet,
ohne ein zweites Schemaverhalten einzuführen.

**Durchgang 3: 16 von 16, keine Abstürze.**

| Prüfung | Ergebnis |
|---|---|
| K1 → `errors_before` aus `snapshot-validation.json` | 1 |
| K1 → K2: Tags | `['validate_unique_ids']` |
| K2 → K3: `search_mode` durchgereicht | `value` = `value` |
| K3: Kontext-Hash = Hash des Objekts im State | `d6e23b97…` |
| K3 → K5: `context_input_sha256` = `results_hash` | gleich |
| K3 → K5: Handoff-Zusicherung | `True` |
| K4 → K5: Regel-Hash = Hash des übergebenen Texts | `1ba6a023…` |
| K4 → K5: Karten im Trace = geladene Karten | `_core.md`, `references.md`, `unique-ids.md` |
| K5: Vorschlag | `update_field demands[1].demandId` |
| K6: Schemaergebnis | `schema_valid=True`, 0 Retries |
| K7: Anwendung | `applied_ok=True`, `uploaded=True` |
| K7: `errors_after` nie stilles 0 | `0` (echte Re-Validierung) |
| K8: Entscheidung | `stop_valid`, konsistent zu `errors_after=0` |
| Trace | 9 Einträge für 9 Knoten |

Rohdaten je Durchgang in `data/archive/ba-apd-smoke/`, mit vollständigen Lauf-Metadaten.

---

## Verbleibendes Risiko

1. **`validation_result` trägt zwei Bedeutungen.** Knoten 1 schreibt den **Vor**-Zustand als
   Dict, Knoten 7 überschreibt ihn (`apply_revalidate.py:146`) mit der **rohen Nach**-Liste.
   Für die Rückkante 8→2 ist das inhaltlich richtig (neue Iteration, frische Validierung), und
   Knoten 2 verträgt jetzt beide Formen — aber ein Feld mit zwei Formen ist eine Falle.
   **In AP-E entscheiden:** vereinheitlichen oder trennen. *(Beim ersten Smoke bin ich selbst
   darauf hereingefallen und habe Knoten 1 fälschlich als fehlerhaft gemeldet, weil meine
   Prüfung den Endzustand statt des Trace-Eintrags las.)*
2. **Knoten 5 lädt die Identifikationsantwort weiterhin von Platte.**
   `run_correction_generation()` holt sie über `load_identify_response()` aus dem jüngsten
   Iterationsordner, wenn nichts übergeben wird. Scheitert Knoten 2 in Iteration 2, bekäme
   Knoten 5 die Antwort aus Iteration 1 und hielte sie für aktuell — **dieselbe Fehlerklasse
   wie der veraltete Suchkontext aus BA-024**, nur an anderer Stelle. Nicht behoben, weil es
   denselben Prompt-Gleichheitsnachweis braucht wie damals. **Vor AP-F schliessen.**
3. **`app/.venv` bleibt bestehen.** Ein Lauf aus dem falschen Interpreter wird jetzt erkannt und
   protokolliert, aber nicht verhindert. Bewusst so entschieden.
4. **Der Smoke deckt genau einen Fall ab** (I01, ein Einzelfehler, Suchmodus `value`). Kein
   Beleg für Mehrfachfehler, Leerfeld- oder Equipment-Fälle und **nicht** für die Rückkante
   8→2 — die gibt es erst mit AP-E.
5. **Die B2-Zahlen bleiben Regressionsreferenz, kein Ergebnis.** Sie beantworten „läuft das
   System noch wie vorher?", nicht Kapitel 7. Die wissenschaftlichen Zahlen entstehen in AP-H
   nach dem Einfrieren.

- **Was NICHT funktioniert hat:**
  * **Der Smoke war als Abnahme gedacht und wurde zur Fehlersuche.** Zwei Defekte, die alle
    Einzeltests von AP-D passiert hatten. Beide sassen **zwischen** Knoten — genau dort, wo
    Einzeltests blind sind. Lehre: ein Integrationslauf gehört an das **Ende jedes**
    Extraktionsblocks, nicht erst vor die Verdrahtung.
  * **Zwei eigene Prüffehler.** Erstens las die Handoff-Prüfung den Endzustand statt Knoten 1s
    Trace und meldete einen Fehler, den es nicht gab. Zweitens brach `redirect_stdout` auf ein
    `StringIO` die Knoten 7 und 9, weil Runtime-Skripte `sys.stdout.reconfigure()` aufrufen —
    ein Artefakt meines Harness, nicht des Produkts. **Beim Prüfen einer Kette gilt: erst das
    Messinstrument prüfen** (harte Regel 6).
  * **`\n` in Ersetzungsskripten zum dritten Mal danebengegangen** (Muster 5). Diesmal wurde
    das Escape beim Durchreichen aufgelöst und erzeugte eine kaputte f-String-Zeile. Endgültige
    Abhilfe: Ersatzblöcke als **Datei** schreiben und hineinspleissen, nie als Inline-Literal.
  * **Fast einen neuen F7 erzeugt:** Beim Neuschreiben von `generate_audit_report` hatte ich
    `✓` durch `OK` ersetzt — genau die Abweichung, die ich in derselben Runde zurücksetzen
    sollte. Vor dem Einspleissen aufgefallen und korrigiert.
- **Offen / nächstes:** **AP-E** — Graphverdrahtung. Vorher entscheiden: Punkt 1 und 2 aus dem
  Restrisiko. `AP-H4a` (eigener BA-Runner) und `AP-G5a` (Lock-Artefakt) sind in
  `BA_ARBEITSPAKETE.md` verankert.

---

### [BA-027] 2026-08-20 — Letzte State-/Handoff-Risiken geschlossen · AP-D abgeschlossen
- **Status:** done — AP-D endgültig geschlossen; AP-E freigegeben
- **Kapitelbezug:** K4 *(State-Schnitt)*, K5 *(Kontrollbedingungen, Umgebungszwang)*,
  K6 *(Provenienznachweise)*, K8 *(Limitationen)*
- **Literatur:** L11 *(Turpin et al. — nur was der Code festhält, ist später prüfbar)*
- **Changed files:** `…/runtime/identify_error_llm.py`, `…/graph/nodes/classification.py`,
  `…/graph/nodes/correction.py`, `…/graph/nodes/input_analysis.py`,
  `…/graph/nodes/apply_revalidate.py`, `…/graph/graph_state.py`,
  `…/runtime/update_snapshot.py`, `app/core/run_metadata.py`, `docs/BA_ARBEITSPAKETE.md`

## 1 — Identify-Handoff Knoten 2 → Knoten 5

**Befund.** Knoten 5 übergab die Identifikationsantwort nicht; `run_correction_generation()`
suchte sie über `get_latest_iteration_number()` selbst von Platte
(`generate_correction_llm.py:931`). Scheitert Knoten 2 in Iteration 2, bekäme Knoten 5 die
Antwort aus Iteration 1 und hielte sie für aktuell — dieselbe Fehlerklasse wie der veraltete
Suchkontext aus BA-024.

**Änderung.** Nach demselben Muster wie Regel- und Kontext-Handoff:
* `identify_error_llm.identify_sha256()` — **eine** Serialisierungsstelle. Zwei eigene
  Serialisierungen würden Serialisierungen statt Inhalte vergleichen.
* `save_llm_response()` gibt jetzt zusätzlich `output_data` zurück (**ein** Aufrufer, geprüft
  per Volltextsuche), `run_classification()` reicht es als `identify_response` und
  `identify_response_sha256` weiter.
* Knoten 2 hängt beides an `classified_error` — genau wie `results_object` am
  `extracted_context` hängt.
* Knoten 5 übergibt `identify_response=` und schreibt `identify_input_sha256` sowie
  `identify_handoff_ok` in den Trace.

**Regel-B-Nachweis.** Modellaufruf abgefangen, **vollständiger Prompt** gehasht:
Nachladen `52f78c6abf96d989…` gegen Durchreichen `52f78c6abf96d989…`, **567.518 Zeichen,
identisch**. Es ist eine Provenienzzusicherung, keine zusätzliche Fähigkeit.
**CLI-Fallback unverändert:** `identify_response` hat weiterhin Default `None`, der
Nachlade-Zweig steht unangetastet — geprüft über `inspect.signature` und den Quelltext.

## 2 — `validation_result` in zwei Felder getrennt

**Befund.** Ein Feld trug zwei Bedeutungen *und* zwei Formen: Knoten 1 schrieb den
Einstiegsstand als Dict, Knoten 7 überschrieb ihn mit der rohen Nach-Liste. Knoten 2 musste
raten, welche Form er bekommt — genau daran war der erste Gesamtsmoke gescheitert.

**Änderung.** `GraphState` trägt jetzt **19 statt 18 Felder**:
* `initial_validation: Optional[dict]` — Knoten 1, Stand beim Einstieg
* `final_validation: Optional[list]` — Knoten 7, rohe Meldungen nach der Re-Validierung

`errors_before` und `errors_after` bleiben ausdrücklich **getrennte abgeleitete Werte** und
werden nie aus einem der beiden Felder rekonstruiert. Knoten 2 wählt jetzt eindeutig:
`final_validation` (wenn gesetzt — Rückkante 8→2) sonst `initial_validation["meldungen"]`.
Die Typprüfung bleibt nur noch als Schutz gegen Setzen von aussen stehen, nicht als Rateweg.

**Gegenprobe über alle neun Knoten** (AST, nur Codezeilen, Kommentare ausgenommen):
`initial_validation` in `input_analysis.py` + `classification.py`; `final_validation` in
`apply_revalidate.py` + `classification.py`; **`validation_result`: 0 Codestellen.**
`AP-C4` in `BA_ARBEITSPAKETE.md` von „18 Feldern" auf 19 nachgezogen.

## 3 — `run_audit_report()` geprüft

**Kein `except BaseException` im Produktcode.** Die Umsetzung war bereits die geforderte:
`generate_audit_report.py:372` fängt gezielt `except SystemExit`, gefolgt von
`except Exception`; die CLI-Semantik steht getrennt in `main()`, das nach einem Fehler selbst
`sys.exit(1)` setzt. *(`except BaseException` steht nur in meinem Smoke-Harness im
Scratchpad — dort ist es Absicht, weil ein Prüfskript alles auffangen muss.)*

**Bei der Gelegenheit alle sieben `run_*`-Wrapper geprüft**, ob sie Code aufrufen, der
`sys.exit` macht, ohne es zu fangen:

| Wrapper | fängt `SystemExit` | ruft `sys.exit`-fähigen Code |
|---|---|---|
| `run_apply` | ja | `validate_proposal_schema` |
| `run_audit_report` | ja | `load_metadata` |
| `run_context_search` | ja | — (argparse) |
| `run_technical_check` | nein | `validate_with_retry` — **konstruktiv ausgeschlossen** |
| `run_correction_generation`, `run_upload`, `run_classification` | — | keiner |

Der scheinbare Treffer bei `run_technical_check` ist ein **Fehlalarm meines Scanners**: der
Wrapper übergibt `exit_on_failure=False`, das `sys.exit(1)` in `validate_with_retry:244` steht
hinter `if exit_on_failure:` und ist aus dem Knotenpfad nicht erreichbar. Das ist die sauberste
Form der geforderten Trennung — ein zusätzliches `except` wäre nur Rauschen.
**Grenze des Verfahrens ehrlich benannt:** die Prüfung geht **eine Aufrufebene tief**.

## 4 — `update_snapshot` stdout

**Nicht wiederhergestellt, ausdrücklich dokumentiert.** Die Reihenfolge liesse sich nur
zurückholen, indem entweder die Logik wieder dupliziert wird (genau der behobene Befund) oder
ein gemeinsamer Helfer einen Druckunterdrückungs-Schalter bekommt — beides ein Eingriff aus
rein kosmetischem Grund. `save_upload_result()` muss in `run_upload()` liegen, damit Bedingung
C dasselbe Artefakt schreibt wie A und B; die CLI besitzt die Reihenfolge deshalb nicht mehr.

Als Kommentarblock direkt an der Stelle in `update_snapshot.main()` festgehalten, mit den
Belegen: Zeilenmenge, Exit-Code (1) und `upload-result.json` unverändert; niemand parst dieses
stdout (`_read_snapshot_metadata_from_stdout()` gilt nur für `rename_snapshot` und
`identify_snapshot`).

## 5 — Harter Umgebungszwang für H4a

`app/core/run_metadata.py` → `require_ba_env()` wirft `FalscheUmgebung(RuntimeError)`,
**bevor der erste Fall läuft**, wenn `ba_env_ok` falsch ist. Die Meldung nennt erwartete und
tatsächliche Umgebung, Interpreter und Paketversionen und endet mit *„Kein Fall wurde
ausgeführt."*

Bewusste Abgrenzung: `warn_if_wrong_env()` bleibt für Entwicklungs- und Pilotläufe — dort soll
ein Lauf nicht daran scheitern, dass er dokumentiert werden will. Für einen *finalen* Messlauf
ist Warnen falsch, weil `pydantic` an drei Stellen im gemessenen Pfad liegt.
Belegt: Wurzel-`.venv` läuft durch, `app/.venv` bricht mit `FalscheUmgebung` ab.
In `BA_ARBEITSPAKETE.md` unter **H4a** verbindlich verankert.

## Abschliessender Gesamtsmoke — 18/18

Neun Knoten als Kette, ohne LangGraph, `RULEBOOK_MODE=cards`, `MEMORY_MODE=off`,
`HUMAN_IN_THE_LOOP=false`. Alle 18 Prüfungen bestanden, **0 Abstürze**, 9 Trace-Einträge.
Neu darunter und grün: `identify_input_sha256 == identify_response_sha256`,
`identify_handoff_ok == True`, und `initial_validation` ist Dict während `final_validation`
Liste ist.

> **⚠ Einschränkung, die nicht übergangen werden darf.** Während dieses Laufs war die
> Smart-Planning-Testinstanz **nicht erreichbar** — der interne IdP-Host löst nicht auf
> (`gaierror`, dieselbe Blockade wie am 19.08. vormittags, BA-011; Azure OpenAI war
> erreichbar). Der Smoke lief deshalb im neu ergänzten `--reuse`-Modus auf einem vorhandenen
> Snapshot. **Damit sind Upload, Trigger und Re-Validierung in DIESEM Lauf nicht ausgeführt
> worden** (`uploaded=False`, `errors_after=None`, folgerichtig `stop_uncertain`).
> Anwendung selbst lief lokal durch (`applied_ok=True`).
>
> Der Server-Teil war im vorangegangenen Lauf vom selben Tag vollständig grün
> (`applied_ok=True`, `uploaded=True`, `errors_after=0`, `stop_valid`), und an Knoten 7s
> Upload- und Re-Validierungscode hat sich seither **nichts** geändert — nur das Zielfeld
> heisst jetzt `final_validation`. Das Risiko ist damit klein, aber **nicht null**:
> **Vor AP-F ist ein vollständiger End-to-End-Smoke mit erreichbarer Testinstanz zu
> wiederholen.**

- **Was NICHT funktioniert hat:**
  * **`\n`-Escapes zum vierten Mal danebengegangen** (Muster 5) — diesmal in `require_ba_env()`,
    obwohl ich die Abhilfe in BA-026 selbst notiert hatte. **Ab jetzt ausnahmslos:
    Ersatzblöcke als Datei schreiben und hineinspleissen.** Die Fehlermeldung war identisch
    zum letzten Mal; ich habe sie trotzdem erst beim zweiten Hinsehen erkannt.
  * **Zwei Assertions schlugen an, weil sie meinen eigenen Erklärkommentar mitzählten**
    (`validation_result` im Text über die Umbenennung). Kein Schaden — die Skripte schreiben
    erst nach der Prüfung, es entstand kein Teilzustand. Aber: **Prüfe auf Codezeilen, nicht
    auf Vorkommen im Text.** Dieselbe Klasse Fehler wie der Exit-Code-Zähler in BA-025.
  * **Der Umgebungsausfall kam ungelegen** und lässt den Server-Teil des Abschlusssmokes offen.
    Bewusst nicht überspielt: ein Lauf, der Upload und Re-Validierung nicht ausgeführt hat,
    wird nicht als „grün inklusive Server" berichtet.
- **Offen / nächstes:** **AP-E** — Graphverdrahtung. Vorgabe: keine neue Fachlogik, nur
  Orchestrierung der geprüften Knoten, des Zustands und der festgelegten Übergänge.
  Nach Rückkehr der Testinstanz: vollständiger End-to-End-Smoke nachholen.

---

### [BA-028] 2026-08-20 — AP-E: Der Graph ist verdrahtet
- **Status:** done bis auf einen DoD-Rest (End-to-End mit erreichbarer Testinstanz)
- **Kapitelbezug:** K4 *(Graphstruktur, Abbildung)*, K5 *(Orchestrator, keine Fachlogik)*,
  K6 *(Trace-Persistenz)*
- **Literatur:** L11 *(der Code führt Protokoll, nicht das Modell)*
- **Changed files:** `app/tools/smart-planning/graph/correction_graph.py` *(neu)*,
  `app/agents/sp_agent.py`, `docs/abbildungen/graph-korrekturablauf.mmd` *(neu)*,
  `docs/BA_ARBEITSPAKETE.md`

**Vorgabe eingehalten: keine neue Fachlogik.** `correction_graph.py` registriert die neun in
AP-D geprüften Knotenfunktionen, die Kanten aus Masterplan Kap. 11 und sonst nichts. Beide
Router lesen genau ein Feld, das ein Knoten gesetzt hat.

**API vorher am installierten Paket verifiziert**, nicht angenommen (Bauregel A): `StateGraph`,
`add_node`, `add_edge`, `add_conditional_edges`, `compile`, `START`/`END` (`'__start__'` /
`'__end__'`), `get_graph().draw_mermaid()`. `route_after_evaluation()` existierte bereits aus
AP-D4 und wurde **wiederverwendet statt neu geschrieben**.

## Struktur — gegen den Plan geprüft

| | Soll (Kap. 11) | Ist |
|---|---|---|
| Knoten | 9 | 9 (+ `__start__`/`__end__`) |
| Kanten | — | 12 |
| Rückkante 8→2 | ja | `evaluation → classification` vorhanden |
| **Kante 6→5** | **nein** | **nachweislich nicht im Graphen** |

Router A (`route_after_technical_check`): `schema_valid is True → apply_revalidate`, `False →
evaluation`, **`None` ebenfalls `evaluation`** — lieber Knoten 8 entscheiden lassen als etwas
anwenden, dessen Schemastatus unbekannt ist. Ausdrücklich **nicht** nach übrigen Retries
gefragt: die sind erschöpft, wenn Knoten 6 `False` liefert.
Router B: alle vier Werte aus `DECISION_ACTIONS` geprüft — `continue → classification`, die
drei `stop_*` → `answer`.

**Was aus dem LangChain-Ökosystem NICHT benutzt wird**, im Modulkopf festgehalten: keine
LLM-Wrapper, keine Prebuilt-Agenten, **keine Retry-Policies auf Knotenebene**, kein
Checkpointer.

**`recursion_limit` bewusst gesetzt.** Der LangGraph-Standard (25) hätte bei mehreren
fachlichen Iterationen gegriffen und den Lauf mit einer Framework-Ausnahme beendet — ein
**Abbruchgrund, den der Monolith nicht hat** und der später wie ein Architektureffekt aussähe.
Grenze jetzt `max_iterations × 9 + 10`; die fachliche Obergrenze bleibt allein Knoten 8
(`stop_max_iter`).

## E4 — die Rückgabe bleibt identisch

`_execute_pipeline_graph()` liefert `success`, `pipeline`, `completed_steps`,
`final_validation`, `total_iterations` — geprüft, weil `orchestration_agent.py:1206` genau
`final_validation.get("is_valid")` und `.get("errors")` liest.

**Die Iteration gehört dem Graphen.** `execute_pipeline()` kehrt bei `graph` sofort zurück und
durchläuft seine eigene `while True`-Schleife nicht; die Wiederholung macht die Rückkante 8→2.
Liefen beide, wäre die Iterationszahl zwischen den Bedingungen nicht mehr vergleichbar.

**Kein falsches Grün:** ist `errors_after` `None`, bleibt `final_validation` **`None`** statt
`{"errors": 0}` — dieselbe Handhabung wie im Monolithen (`sp_agent.py:297`).
Belegt im Lauf: `success=False`, `total_iterations=1`, `final_validation=None`,
`error` trägt den echten Grund (`upload: ConnectionError …`).

**Monolith unberührt:** ohne gesetzte Variable ist `SP_ARCHITECTURE_MODE == 'monolith'`, und
die Verzweigung greift nur bei `graph` **und** einer Korrektur-Pipeline.

## E5 / E6

`iteration-N/graph_state.json`, 13.216 Byte, 20 Felder, 9 Trace-Einträge. Regeltext,
Suchkontext, Identify-Antwort und Meldungslisten sind **durch ihre Hashes ersetzt** —
eingebettet hätten sie die Datei unlesbar gemacht (Kap. 12.5); die Rohdaten liegen als
Artefakte daneben. Gegenprobe: `rule_text` → `<ausgelagert, 12214 Zeichen, sha256=99412443…>`,
`rule_text_hash` unverändert erhalten.
E6: `docs/abbildungen/graph-korrekturablauf.mmd`, direkt aus dem kompilierten Graphen.

- **Verifikation:** Graphlauf über LangGraph durchlaufen — Trace
  `input_analysis → classification → context_search → rule_matching → correction →
  technical_check → apply_revalidate → evaluation → answer`, `architecture_mode='graph'`,
  `finished_at` gesetzt, `initial_validation` Dict / `final_validation` Liste.
  Derselbe Lauf zusätzlich **über `SPAgent.execute_pipeline()`**.
- **Was NICHT funktioniert hat:**
  * `SPAgent()` braucht `runtime_dir` — ich hatte ihn ohne Argument konstruiert. Kleiner
    Fehler, aber wieder derselbe Reflex: **Signatur ansehen, nicht annehmen.**
  * Im Prüfausdruck der Zustandsdatei griff ich mit `[...]` auf `results_object` und
    `identify_response` zu, die in diesem Lauf **legitim fehlen** — der Snapshot hatte 0 Fehler,
    also lieferte Knoten 2 keinen Suchwert. Kein Defekt, sondern mein Zugriff. Bei
    Zustandsdateien grundsätzlich `.get()`.
  * **Der DoD ist nicht vollständig erfüllt.** Er verlangt *„ein bekannter Fall läuft im
    `graph`-Modus End-to-End durch"*. Der Lauf ging durch alle neun Knoten, aber Upload und
    Re-Validierung scheiterten an der **nicht erreichbaren Testinstanz** (siehe BA-027).
    Das wird nicht als erfüllt berichtet: **sobald die Testinstanz wieder da ist, ist ein
    vollständiger Graph-Lauf auf einem frischen Fall nachzuholen** — zusammen mit dem
    ebenfalls offenen End-to-End-Smoke aus BA-027, in einem Zug.
- **Offen / nächstes:** **AP-F** — vertikaler Durchstich. Davor die beiden nachzuholenden
  Läufe. Weiterhin offen aus BA-025: **H4a** (BA-Runner) und **G5a** (Lock-Artefakt).

---

### [BA-029] 2026-08-20 — Nachgeholte Läufe · AP-E-DoD erfüllt · AP-F1 deckt einen Berichtsfehler auf
- **Status:** done — AP-E vollständig abgeschlossen, **AP-F1 erledigt**; F2–F5 offen
- **Kapitelbezug:** K4 *(Durchstich)*, K5 *(Kontrollbedingungen)*, K6 *(UF3-Belege)*,
  K7 *(Pilotbefund, ausdrücklich kein Ergebnis)*, K8
- **Literatur:** L11 *(was der Code aufzeichnet, nicht was das Modell behauptet)*
- **Changed files:** `app/agents/sp_agent.py`, `docs/BA_ARBEITSPAKETE.md`
- **Status der Läufe:** `pilot` — **keiner dieser Werte ist ein Messergebnis** (Regel 5)

Der Netzzugang zur Smart-Planning-Testinstanz war wiederhergestellt (`10.112.19.8` löst auf,
Token über 1.385 Zeichen). Damit liessen sich die beiden aus BA-027 und BA-028 offenen Läufe
nachholen.

## 1 — Gesamtsmoke jetzt vollständig, inklusive Server

Frischer Snapshot, Fall I01, alle neun Knoten als Kette. **18/18 Prüfungen, 0 Abstürze** —
und diesmal mit dem Teil, der beim letzten Mal fehlte: `applied_ok=True`, **`uploaded=True`**,
`errors_after=0` aus einer **echten Re-Validierung**, Entscheidung `stop_valid`.
Damit ist der Vorbehalt aus BA-027 aufgelöst.

## 2 — AP-E-DoD erfüllt: 8/8

Ein bekannter Fall im `graph`-Modus über `SPAgent.execute_pipeline()`, frischer Snapshot:
`success=True`, `total_iterations=1`, alle neun Knoten in `completed_steps`,
`final_validation = {'errors': 0, 'warnings': 5, 'is_valid': True, 'server_validated': True}`,
`graph_state.json` in `iteration-1` abgelegt.
Ausdrücklich mitgeprüft, weil `orchestration_agent.py:1206` genau darauf zugreift:
`final_validation.get("is_valid")` und `.get("errors")` liefern brauchbare Werte, und
`is_valid` ist genau dann `True`, wenn `errors == 0`.

## 3 — AP-F1: der Durchstich, und was er gefunden hat

Fall **I03** (der in AP-0.4 festgelegte Referenzfall), je ein **frischer** Snapshot pro
Bedingung, jede Bedingung in einem **eigenen Prozess** — `RULEBOOK_MODE` und
`SP_ARCHITECTURE_MODE` werden beim Import aus `agent_config` gelesen, `importlib.reload()`
schaltet sie nicht um (der Fehler, der BA-021 verdorben hat). Die effektiv geltenden Werte
werden je Lauf mitprotokolliert, nicht die gesetzten.

| | A (Monolith + `monolith`) | C (Graph + `cards`) |
|---|---|---|
| Fehler vorher | 1 | 1 |
| `success` | True | True |
| Iterationen | 1 | 1 |
| Fehler nachher | 0 | 0 |
| `action` | `update_field` | `update_field` |
| `target_path` | `articles[0].relDensityMin` | `articles[0].relDensityMin` |
| `new_value` | **1.14** | **1.14** |
| protokollierte Schritte | 7 | 9 |

**Beide Architekturen kommen zum selben Vorschlag — und beide liegen daneben.** Ground Truth
ist `1.017` (`articles[articleId=100005].relDensityMin`, Klartext im Katalog:
*„wieder auf 1.017 setzen"*). Das deckt sich mit der Regressionsreferenz aus BA-016 und ist
ein nützlicher Befund für den Erwartungshaushalt: **der Architekturunterschied liegt hier
nicht im Ergebnis, sondern in dem, was hinterher nachvollziehbar ist.**

Genau das zeigt der UF3-Teil des Durchstichs:
* **A:** 7 Schrittnamen in der Rückgabe. Auf Platte liegen **sehr wohl Artefakte** — je
  Iteration `llm_identify_response.json`, `llm_identify_call.json`, `last_search_results.json`,
  `llm_correction_proposal.json`, `llm_correction_call.json`, `upload-result.json`,
  `snapshot-validation.json`. Sie sind **verteilt, uneinheitlich getypt und nicht zeitlich
  geordnet**, und die Regelprovenienz fehlt darin: welche Karten geladen waren, steht nur in
  einem `print()` im stdout des Subprozesses.
* **C:** zusätzlich `graph_state.json` — **ein** typisierter Zustand mit **einem** zeitlich
  geordneten Trace (9 Einträge, je mit `timestamp_utc` und `duration_ms`), einschliesslich
  Regel- und Kontextprovenienz: `cards_loaded = ['_core.md', 'density-values.md']`, Regeltext
  16.620 Zeichen mit `sha256=da902d152fe91062…`, `decision = stop_valid`.

> **Korrektur 20.08.2026 (auf Hinweis des Nutzers).** Hier stand zuvor, A habe *„kein Zustand
> auf Platte"* — **das ist falsch** und hätte den Monolithen zum Strohmann gemacht (harte
> Regel 2). Der Unterschied ist nicht *Artefakte gegen keine Artefakte*, sondern
> **verteilte, untypisierte Einzelartefakte ohne Regelprovenienz gegen einen einheitlichen,
> typisierten Zustand mit integriertem, zeitlich geordnetem Trace**.
>
> Ebenso ist **7 gegen 9 Schritte KEINE Nachvollziehbarkeitsmetrik.** Die Zahlen zählen
> Verschiedenes: 7 Pipeline-Schritte gegen 9 Graphknoten — der Graph macht denselben Ablauf
> feiner sichtbar (Kap. 3.6: neun Knoten sind nicht neun LLM-Aufrufe). Als Kennzahl für UF3
> taugt die Schrittzahl nicht; was zählt, ist **welche Fragen sich hinterher aus dem
> Protokoll beantworten lassen**. Das Raster dafür entsteht in AP-F2/F5.

### Der Fund: `server_validated` mass in A und C etwas anderes

Im ersten Durchgang meldete A `server_validated=False` und C `True` — **bei identischem
Korrekturvorschlag**. Ursache lag nicht in der Architektur, sondern in **meiner Übersetzung
in `_execute_pipeline_graph()`**: der Monolith liest das Serverurteil aus
`upload-result.json → server_response.isSuccessfullyValidated` (`sp_agent.py:460ff`), meine
Fassung setzte lediglich `bool(applied.uploaded)` — also „wurde hochgeladen" statt „hat der
Server es als valide angenommen".

Das ist eine **Bauregel-B-Verletzung in der Berichtsschicht**: ein Unterschied, der als
Architektureffekt gelesen worden wäre, obwohl er keiner ist. Angeglichen — der Graph-Pfad liest
jetzt dieselbe Datei auf dieselbe Weise. **Gegenprobe im Wiederholungslauf: beide Bedingungen
melden `server_validated=False`.**

Bemerkenswert ist auch der Wert selbst: `is_valid=True` bei `errors=0`, aber
`server_validated=False` — der Server hat den Upload also nicht als „erfolgreich validiert"
markiert, obwohl die Re-Validierung 0 Fehler ergab. **Das ist bisher nicht verstanden und
gehört vor AP-H geklärt**, weil `server_validated` sonst als Kennzahl untauglich ist.

- **Verifikation:** alle Läufe mit `MEMORY_MODE=off`, `HUMAN_IN_THE_LOOP=false`,
  `ba_env_ok=true` und vollständigen Lauf-Metadaten. Rohdaten:
  `data/archive/ba-apd-smoke/smoke-I01-7db95556.json`,
  `data/archive/ba-ape-dod/ape-dod-I01-05a8b055.json`,
  `data/archive/ba-f1-durchstich/f1-I03.json`.
- **Was NICHT funktioniert hat:**
  * **Meine eigene Übersetzung hat den ersten Unterschied erzeugt**, den der Durchstich
    gezeigt hat. Nicht das System, nicht die Architektur — die Berichtsschicht. Genau davor
    warnt Bauregel B, und genau dafür ist AP-F der „ehrliche Entscheidungspunkt". Hätte ich
    den Durchstich übersprungen, wäre `server_validated` als Architektureffekt in Kapitel 7
    gelandet.
  * **Ground Truth wurde still zu `None`**, weil ich `case["change"]` statt `case["changes"]`
    gelesen habe — der Katalog nennt den Schlüssel im Plural. Ein leeres Feld, das wie „keine
    Ground Truth vorhanden" aussah. Korrigiert; jetzt wird zusätzlich der Klartext
    (`correction`) mitgeführt, damit so etwas auffällt.
  * Eine der acht DoD-Prüfungen (*„Graph hat angewendet UND hochgeladen"*) war **fest auf
    `True` verdrahtet** und damit wertlos; die Aussage trägt in Wahrheit
    `final_validation.server_validated`. Beim nächsten Durchlauf ersetzen — als bestandene
    Prüfung gezählt wurde sie nicht zu Recht.
- **Offen / nächstes:** **AP-F2–F5** — lesbare Trace-Kette, Entscheidung Knotenzahl (F3),
  Entscheidung Provenienz-Granularität (F4), Messinstrument am Einzelfall erproben (F5).
  Zusätzlich vor AP-H: `server_validated`-Semantik klären; **H4a** (BA-Runner) und **G5a**
  (Lock-Artefakt) aus BA-025.

---

### [BA-030] 2026-08-20 — Validitätssemantik geklärt · F2 gebaut · ein struktureller Widerspruch zu F3
- **Status:** done — Punkte 1–3 geschlossen, **F2 fertig**; F3 braucht eine Entscheidung
- **Kapitelbezug:** K3 *(was der Monolith wirklich ablegt)*, K5 *(Kontrollbedingungen)*,
  K6 *(autoritative Validität, UF3-Raster)*, K8 *(Limitationen)*
- **Literatur:** L11
- **Changed files:** `app/agents/sp_agent.py`,
  `app/tools/smart-planning/graph/correction_graph.py`,
  `app/tools/smart-planning/graph/trace_lesbar.py` *(neu)*, `docs/BA_PROJECT_LOG.md`

## 1 — `server_validated` gegen `is_valid`: bis zur API zurückverfolgt

Drei Dinge waren vermischt. Die Kette, an den Artefakten des F1-Laufs belegt:

| | Quelle | Zeitpunkt | Bedeutung |
|---|---|---|---|
| `isSuccessfullyValidated` | **PUT-Antwort** von `/esarom-be/api/v1/snapshots/{id}` (`update_snapshot`) | **vor** der Re-Validierung | gespeicherter Snapshot-Zustand beim Upload |
| Validierungsjob | `POST …/validate`, gepollt bis Terminalzustand (`trigger_server_validation`) | dazwischen | *ob* geprüft wurde |
| `errors` / `warnings` | **GET** `…/snapshots/{id}/validation-messages` (`validate_snapshot`) | **nach** dem Job | **autoritative technische Validität** |

Beide F1-Snapshots trugen `isSuccessfullyValidated: False` bei gleichzeitig 0 Fehlern nach der
Re-Validierung. Das ist **kein Widerspruch**: das Flag beschreibt den Upload-Zustand, nicht das
Prüfergebnis. Als Validitätsmetrik war es untauglich — deshalb heisst es jetzt
**`upload_flag_at_put`** und ist im Code ausdrücklich als *keine* Validitätsmetrik markiert.

**Autoritativ ist:** `errors == 0` aus den Meldungen, geholt **nach** einem abgeschlossenen
Validierungsjob. Neu im Rückgabefeld: `revalidation_ok`.

**Dabei ein echter Defekt gefunden.** Der Monolith protokollierte bei gescheitertem Job
*„final_validation bleibt unbelegt"* — **tat es aber nicht**: `error_count` wurde unbedingt aus
`snapshot-validation.json` gelesen, also möglicherweise aus einem **veralteten** Stand. Genau
das falsche Grün, das BA-021 an anderer Stelle beseitigt hatte. Jetzt setzt der Code
`final_validation = None`, wenn der Job nicht erfolgreich war — der Code tut endlich, was sein
Log behauptet.

**In beiden Pfaden gleich** (AST-Gegenprobe): `final_validation_status` (Monolith, `:496`) und
`abschluss` (Graph, `:840`) tragen identisch
`['errors', 'warnings', 'is_valid', 'revalidation_ok', 'upload_flag_at_put']`.
Kein Verbraucher las `final_validation["server_validated"]` — per Volltextsuche geprüft, das
Umbenennen bricht nichts.

## 2 — BA-029 korrigiert: der Monolith hat sehr wohl Artefakte

Die Aussage *„A: kein Zustand auf Platte"* war **falsch** und hätte den Monolithen zum
Strohmann gemacht (harte Regel 2). Am realen A-Snapshot nachgezählt:

```
./           last_search_results.json, metadata.txt, snapshot-data.json,
             snapshot-validation.json, upload-result.json
iteration-1  last_search_results.json, llm_correction_call.json,
             llm_correction_proposal.json, llm_identify_call.json,
             llm_identify_response.json, snapshot-data.json, snapshot-validation.json
```

C legt **dieselben** ab, plus `graph_state.json` (und die Audit-Report-Dateien, siehe Punkt 4).

**Der Unterschied ist also nicht *Artefakte gegen keine Artefakte*,** sondern: verteilte,
uneinheitlich getypte Einzeldateien **ohne zeitliche Ordnung und ohne Regelprovenienz** gegen
**einen** typisierten Zustand mit **einem** zeitlich geordneten Trace, der Regel- und
Kontextprovenienz mitführt.

**„7 gegen 9 Schritte" ist ebenfalls keine Nachvollziehbarkeitsmetrik.** Die Zahlen zählen
Verschiedenes — 7 Pipeline-Schritte gegen 9 Graphknoten; der Graph macht denselben Ablauf nur
feiner sichtbar (Kap. 3.6). Beides ist in BA-029 als Korrektur eingetragen.

## 3 — 19 gegen 20 Felder aufgeklärt

Das zwanzigste war `final_validation_anzahl`, das **erst beim Ablegen** entsteht — kein
Zustandsfeld, stand aber auf derselben Ebene und sah dadurch wie ein undokumentiertes Feld aus.
Alles, was zur Ablage gehört, steht jetzt unter **`_ablage`**: `graph_state_felder` (aus
`typing.get_type_hints(GraphState)`, also selbstbeschreibend statt fest verdrahtet), die Liste
der ausgelagerten Felder und die Meldungsanzahl. Die übrigen Schlüssel sind exakt die **19**
deklarierten Zustandsfelder.

## 4 ⚠ F2 hat einen strukturellen Widerspruch aufgedeckt — betrifft F3

`app/tools/smart-planning/graph/trace_lesbar.py` rendert `graph_state.json` als lesbare Kette:
je Knoten Dauer und Zeitstempel, die drei Handoff-Hashes an Knoten 5, und am Ende die
**sieben Fragen**, an denen sich UF3 entscheidet (statt einer Schrittzahl). Am I03-Durchstich
sind alle sieben mit `[x]` belegt.

Dabei fiel auf:

| | Bedingung A (`full_correction`) | Bedingung C (Graph) |
|---|---|---|
| Schritte / Knoten | 7 | 9 |
| **LLM-Aufrufe** | identify, generate, Schema-Retry = **3** | dieselben **+ Knoten 9** = **4** |
| `generate_audit_report` | **in keiner der vier Pipelines** | Knoten 9, läuft immer |
| Artefakte | — | zusätzlich `audit-report.md`, `audit-report-stats.json` |
| Laufzeit I03 | — | 44.792 ms, **davon Knoten 9: 20.291 ms = 45 %** |

**Damit stimmt Masterplan Kap. 3.6 nicht mehr:** dort steht *„Drei Knoten rufen das Modell,
genau wie der Monolith heute."* Gebaut sind es in C **vier**. Nachgeprüft: keine der vier
Pipelines (`full_correction`, `correction_from_validation`, `analyze_only`,
`apply_and_upload`) enthält `generate_audit_report`; LLM-Aufrufstellen gezählt über
`chat.completions.create`.

**Warum das zählt:** ein Zeit- oder Tokenvergleich A gegen C wäre um diesen Aufruf verzerrt,
C erzeugt ein Artefakt, das A nicht hat, und für die Expertenbewertung (F5) hätte C ein
formuliertes Endergebnis, A nicht — das würde die Blindung brechen.

**Nicht eigenmächtig entschieden.** Vier Wege, mit Bewertung:
1. **Knoten 9 im Messlauf nicht ausführen** — C hätte dann acht aktive Knoten; die Neun bliebe
   nur strukturell.
2. **`generate_audit_report` in die Monolith-Pipeline aufnehmen** — verändert den realen
   Ist-Zustand und damit die Baseline. **Verstösst gegen Regel 2**, nicht empfohlen.
3. **Knoten 9 behalten, seinen Aufruf aus allen Zeit-/Tokenkennzahlen herausrechnen** und die
   Artefaktasymmetrie als Limitation führen. Für F5 den Experten in **beiden** Armen dasselbe
   variantenneutrale Format vorlegen, das **nicht** aus `audit-report.md` stammt.
4. Neun Knoten aufgeben und auf acht zusammenlegen — widerspricht deiner F3-Vorgabe.

**Empfehlung: Weg 3.** Er hält die neun Knoten, verfälscht keine Kennzahl und macht die
Einschränkung sichtbar, statt sie zu verstecken. Die Trace-Kette weist den Anteil von Knoten 9
seit heute gesondert aus, damit er beim Auswerten nicht untergeht.

- **Was NICHT funktioniert hat:**
  * **Ich hatte den Monolithen zum Strohmann gemacht** — nicht absichtlich, aber die Formulierung
    „kein Zustand auf Platte" tat genau das. Sie stand schon im Protokoll. **Bei jeder Aussage
    über die Baseline gilt: erst am Snapshot nachzählen, dann schreiben.**
  * Der Widerspruch aus Punkt 4 **existiert seit AP-D5** (Knoten 9) und ist mir bei drei
    Gesamtsmokes und dem AP-E-DoD nicht aufgefallen, weil alle nur C betrachteten. Erst der
    **Vergleich** zweier Artefaktbäume hat ihn gezeigt. Das ist das Argument für AP-F als
    eigenes Paket.
  * Zwei Textersetzungen scheiterten an der Einrückung (16 statt 24 Leerzeichen) und an einem
    Regex, der bei `{}` im Ausdruck abbrach. Beide Male half erst der Blick auf die echten
    Zeilen bzw. AST statt Textsuche — **dieselbe Lehre wie beim Exit-Code-Zähler in BA-025**.
- **Offen / nächstes:** **Entscheidung zu Punkt 4** (F3). Danach **F5** am I03-Durchstich.
  Weiterhin offen: **H4a** (BA-Runner), **G5a** (Lock-Artefakt).

---

### [BA-031] 2026-08-20 — Knoten 9 deterministisch · F3/F4 entschieden · F5 findet einen Blindungsbruch
- **Status:** done — **AP-F vollständig** (F1–F5); Entscheidungen im Masterplan festgehalten
- **Kapitelbezug:** K4 *(Knotenzahl, Knoten 9)*, K5 *(Kontrollbedingungen, Blindung)*,
  K6 *(Messinstrument)*, K8 *(Limitation Provenienzgranularität)*
- **Literatur:** L11
- **Changed files:** `app/core/ergebnis_format.py` *(neu)*,
  `app/tools/smart-planning/graph/nodes/answer.py`, `…/graph/graph_state.py`,
  `…/graph/trace_lesbar.py`, `docs/BA_MASTERPLAN.md`, `docs/BA_ARBEITSPAKETE.md`
- **Status der Läufe:** `pilot` — F1 und F5 sind Methodenprüfungen, **keine Ergebnisse**

## Der Widerspruch aus BA-030, behoben

Ich hatte empfohlen, Knoten 9 als LLM-Aufruf zu behalten und ihn aus den Kennzahlen
herauszurechnen. Der Nutzer hat stattdessen entschieden, ihn **deterministisch** zu machen.
**Das ist der bessere Weg**, und der Unterschied ist methodisch nicht klein: mein Vorschlag
hätte einen Konfundierungsfaktor rechnerisch behandelt, den man beseitigen kann. Man muss
nichts wegerklären, was gar nicht existiert.

**Umgesetzt.** Knoten 9 erzeugt das Endergebnis jetzt über `app/core/ergebnis_format.py` —
kein Modell, kein Netzwerk, gleiche Eingabe gleiche Ausgabe.
`generate_audit_report()` bleibt **unverändert** als optionale, nachgelagerte Produktfunktion
und ist nicht mehr Bestandteil der A/B/C-Hauptmessung.

**Gemessene Wirkung** (Fall I01, derselbe Ablauf vorher/nachher):

| | vorher | nachher |
|---|---|---|
| Knoten 9 | 20.291 ms | **0 ms** |
| Gesamtlauf | 44.792 ms | **20.787 ms** |
| Anteil Knoten 9 | 45 % | 0 % |
| reguläre LLM-Aufrufe in C | 4 | **3 — wie A und B** |
| Artefakte nur in C | `audit-report.md`, `audit-report-stats.json` | **keine** |

Alle sieben UF3-Fragen bleiben belegt; DoD-Lauf weiterhin 8/8.

### Nachweis, dass Knoten 9 nichts Fachliches verändert

Zustand mit allen fachlichen Feldern aufgebaut, tief kopiert, Knoten 9 ausgeführt, jedes Feld
per SHA-256 verglichen. Zusätzlich **sabotiert**: `openai.AzureOpenAI`,
`generate_audit_report.run_audit_report` und `…generate_audit_report_with_llm` durch Funktionen
ersetzt, die bei Aufruf eine Ausnahme werfen.

* **17 fachliche Felder unverändert, 0 verändert** — darunter `correction_proposal`,
  `final_validation`, `errors_after`, `decision`, `technical_check`, `applied`,
  `matched_rules`, `extracted_context`, `classified_error`.
* Neu im Zustand: ausschliesslich **`final_answer`**; ausserdem `finished_at` und ein
  `trace`-Eintrag mit `llm_aufruf: False`.
* Kein Modellaufruf trotz Sabotage.
* Deterministisch: zwei Läufe auf demselben Eingang, identischer SHA-256.

`GraphState` hat damit **20** deklarierte Felder (19 + `final_answer`).

### Ein Fehler in meinem eigenen Formatter, den der Test gezeigt hat

Der erste Entwurf las zuerst `decision["action"]`. Bei `stop_valid` zusammen mit
`fehler_nachher = 1` schrieb er *„korrigiert und nachweislich fehlerfrei"* — direkt unter die
Zeile, die 1 Fehler ausweist. **Genau das falsche Grün, das am selben Tag an anderer Stelle
beseitigt wurde.** Jetzt sind die Zahlen autoritativ; die Entscheidung liefert nur, was Zahlen
nicht ausdrücken können. Widersprechen sich beide, wird der Widerspruch **ausgegeben**, nicht
geglättet. Acht Kombinationen einzeln geprüft.

## Masterplan korrigiert

**Kap. 3.6** trug die falsche Aussage *„drei Knoten rufen das Modell — genau so viele wie der
Monolith"*, während die Tabelle darunter Knoten 9 als LLM-Knoten führte. Neu gefasst mit
Korrekturkasten; die drei regulären Aufrufe sind Klassifikation, Korrekturgenerierung und
Schemaprüfung — dieselben drei Skripte wie in der Monolith-Pipeline.
**Schema-Retries** sind jetzt getrennt beschrieben: bedingte Zusatzaufrufe, in beiden
Architekturen dieselbe Funktion, Anzahl je Lauf in `technical_check.retries`, bei Zeit- und
Tokenvergleichen **getrennt auszuweisen statt wegzumitteln**.
**Kap. 9, Knotentabelle Zeile 9** ebenfalls korrigiert — sie nannte
`generate_audit_report_with_llm(...)` als „1:1 nutzbar".

## F3 und F4 — entschieden und festgehalten (neues Kap. 3.6.1)

**F3: neun Knoten bleiben.** Der Durchstich trug den Ablauf End-to-End; der einzige
strukturelle Widerspruch betraf Knoten 9 als LLM-Aufruf und ist behoben. Nach einem
funktionierenden Durchstich zusammenzulegen wäre eine Änderung ohne Anlass. **Ab hier bindend.**

**F4: Provenienz bleibt auf Kartenebene** — und das ist als **Limitation** dokumentiert, nicht
als Bequemlichkeit: Rule-IDs auf Regelebene erforderten eine Änderung an Regelwerk und Prompt,
also an **Kontrollbedingungen**. Ausserdem wäre eine so gewonnene ID nicht belastbar — dass
eine Unterregel im Prompt stand, heisst nicht, dass das Modell sie benutzt hat. Kategorie 3
wird deshalb auf Kartenebene geprüft: *war die Karte, auf die sich das Modell beruft, überhaupt
geladen?*

## F5 — das Instrument geprüft, und es war undicht

Beide Bedingungen aus dem I03-Durchstich durch das gemeinsame Format geschickt und Feld für
Feld verglichen. **Strukturell 5/5 sauber:** identische Felder in identischer Reihenfolge,
keine Architekturbegriffe in Feldnamen, Werten oder Textform, keine Laufzeitangaben.

**Und trotzdem brach es die Blindung** — an der unscheinbarsten Stelle:

> **`snapshot_id` steht im Vorlageformat.** Jede Bedingung läuft auf einem **eigenen frischen
> Snapshot**, also trägt jede Vorlage eine andere UUID. Wer die Zuordnung Snapshot → Bedingung
> kennt — und das Protokoll enthält sie zwangsläufig —, ordnet jede Vorlage zu, **ohne den
> Inhalt zu lesen**.

Behoben: `als_text()` nimmt jetzt ein `pseudonym` (z. B. „Fall 07"), das die ID ersetzt; für
die Expertenvorlage ist es Pflicht, die Zuordnungstabelle gehört in eine getrennte Datei.
Gegenprobe: keine UUID mehr im Text.

**Genau dafür ist Regel 6 da.** Fünf von fünf Strukturprüfungen grün, und das Instrument war
trotzdem undicht — weil die Prüfungen nach Architekturbegriffen suchten und nicht nach
*Zuordenbarkeit*.

Die beiden anderen Unterschiede:
* `korrektur_begruendung` — unterschiedliche Modellprosa aus zwei Läufen. Inhaltlich dasselbe
  Argument (Median 1.14 über 330 Vergleichsartikel), andere Formulierung. Das ist Systemausgabe,
  kein Formatproblem — **aber Länge und Stil variieren sichtbar**, was bei einer
  Expertenvorlage auffallen kann. Für K8 als Restrisiko notieren.
* `revalidierung_abgeschlossen`: A `None`, C `True`. **Kein echter Unterschied**, sondern
  veraltete Daten: der F1-Lauf entstand **vor** der heutigen Umstellung, A's gespeichertes
  `final_validation` trägt noch den alten Schlüssel. **Vor Verwendung muss F1 neu gefahren
  werden** — dann ist der Vergleich sauber.

- **Was NICHT funktioniert hat:**
  * **Meine Empfehlung in BA-030 war die schwächere Lösung.** Ich hatte vorgeschlagen, den
    Konfundierungsfaktor herauszurechnen, statt ihn zu beseitigen. Beseitigen ist immer besser,
    wenn es ohne Eingriff in die Kontrollbedingungen geht — und hier ging es.
  * **Mein Formatter hatte dasselbe falsche Grün eingebaut**, das ich am selben Tag im
    Monolithen behoben hatte: Entscheidung über Zahlen gestellt. Der Invarianztest hat es
    gezeigt, weil ich Testdaten mit `stop_valid` **und** `fehler_nachher=1` gewählt hatte.
    **Absichtlich widersprüchliche Testdaten sind ein Prüfmittel** — mit „realistischen" Daten
    wäre es nicht aufgefallen.
  * **F5 hätte fast bestanden.** Fünf Strukturprüfungen grün, und ich hätte das Instrument für
    dicht gehalten. Erst der Blick auf die *inhaltlichen* Unterschiede zeigte die UUID. Lehre:
    eine Neutralitätsprüfung darf nicht nur nach verräterischen **Begriffen** suchen, sondern
    muss fragen, **ob sich die Vorlagen einander zuordnen lassen**.
  * **Nicht geprüft:** ob die neuen `revalidation_ok`/`upload_flag_at_put`-Felder in einem
    A-Lauf tatsächlich belegt werden — dafür fehlt ein A-Lauf nach der Umstellung.
- **Offen / nächstes:** **F1 neu fahren** (A und C unter dem heutigen Stand), damit die
  F5-Gegenüberstellung nicht auf veralteten A-Daten beruht. Danach **AP-G** (Pilotphase und
  Einfrieren). Weiterhin offen: **H4a** (BA-Runner), **G5a** (Lock-Artefakt).

---

### [BA-032] 2026-08-20 — Reporting-Schicht verankert · F1 neu · F5 grün · AP-F abgeschlossen
- **Status:** done — **AP-F vollständig**; Reporting-Schicht dokumentiert, nicht aktiviert
- **Kapitelbezug:** K3 *(Reporting als Produktartefakt)*, K5 *(Messgrössentrennung, Blindung)*,
  K6 *(Instrument)*, K8 *(Limitationen)*, K9 *(Ausblick E-Mail)*
- **Literatur:** L11
- **Changed files:** `app/agents/sp_agent.py`, `app/core/ergebnis_format.py`,
  `docs/BA_MASTERPLAN.md` *(neues Kap. 3.6.2)*, `docs/BA_ARBEITSPAKETE.md`
- **Status der Läufe:** `pilot` — F1 und F5 sind Methodenprüfungen, **keine Ergebnisse**

## Die Reporting-Schicht ist bereits gemeinsam — nachgewiesen

`generate_audit_report.run_audit_report(snapshot_id)` liest ausschliesslich `metadata.txt`
(`:51`) und `upload-result.json` (`:58`) — Artefakte, die **alle drei Bedingungen** schreiben.
Es liest nichts aus dem `GraphState`.

> **Empirisch belegt:** `run_audit_report()` **unverändert auf einen Monolith-Snapshot**
> angewandt (Bedingung A, Fall I03, `e9ccf149-…`) → vollständiger Report, **6.905 Zeichen,
> 6.795 Tokens, kein Fehler.**

**Sie muss also nicht integriert werden — sie ist es schon.** Der saubere Aufrufort ist
**nach** Abschluss der Pipeline im Aufrufer, nicht in der Pipeline; `execute_pipeline()` bleibt
unangetastet und `full_correction` behält seine sieben Schritte.

**Bewusst noch nicht automatisch aktiviert.** Ein automatischer Aufruf brächte je Fall
zusätzliche Laufzeit und Tokenkosten, ein weiteres Artefakt und einen möglichen Fehlschlag, der
einen sonst gültigen Lauf verunsichern würde. Vorschlag und Fundstellen stehen in
**Masterplan Kap. 3.6.2**; die Aktivierung ist eine eigene Entscheidung nach AP-H.

**Messgrössen getrennt (verbindlich ab AP-H):** `core_*` = Korrektur- und Entscheidungsprozess
(der Vergleichsgegenstand) · `report_*` = `run_audit_report()` · `total_*` = beides.
Der LLM-Aufruf des Reports zählt **nicht** als Aufruf der Graph-Orchestrierung, weil dieselbe
Funktion A und B nachgelagert genauso zur Verfügung steht. Die Formulierung für den
Methodenteil steht im Masterplan.

**Produkt- gegen Evaluierungsmodus** ebenfalls dort: `generate_audit_report()` darf und soll
reale Angaben tragen; `als_text()` erzwingt ein Pseudonym. Die Zuordnung
Pseudonym ↔ Snapshot ↔ Bedingung gehört in eine getrennte, den Bewertern nicht zugängliche
Datei. **E-Mail-Versand** ist als nachgelagerter Nutzungspfad dokumentiert und ausdrücklich
kein Bestandteil des Vergleichs.

## Der Fehler, den der F1-Neulauf aufgedeckt hat — und er war meiner

Der erste Neulauf lieferte in **A** `final_validation = None`, in C den vollen Datensatz.
Ursache: `_revalidation` war **nur im Ausnahmezweig** zugewiesen. Ohne Ausnahme lief der
spätere Zugriff in einen `NameError`, den der umgebende `except Exception` verschluckte —
`final_validation` wurde **still** zu `None`.

**Wie es dazu kam:** Mein Ersetzungsskript hatte drei Änderungen; die dritte Assertion schlug
fehl und brach ab, **bevor** geschrieben wurde. Zwei Änderungen gingen dadurch verloren. Ich
habe danach nur geprüft, dass die Datei **kompiliert** — und das tat sie.

> **Lehre, die über diesen Fall hinausgeht:** Nach einer Textersetzung ist zu prüfen, ob sie
> **angekommen** ist, nicht ob die Datei noch übersetzt. Ein Skript, das mittendrin abbricht,
> hinterlässt einen halben Stand, der syntaktisch fehlerfrei ist. Die AST-Abfrage „wo wird
> `_revalidation` zugewiesen?" hat es in einem Schritt gezeigt.

Behoben: drei Zuweisungen (Vorbelegung vor der Schleife, Erfolgsfall, Ausnahmefall), per AST
gegengeprüft.

## F1 neu — und `final_validation` ist jetzt in beiden Armen identisch

Fall I03, je frischer Snapshot, je eigener Prozess, effektive Schalter protokolliert.

| | A (Monolith + `monolith`) | C (Graph + `cards`) |
|---|---|---|
| Fehler vorher → nachher | 1 → 0 | 1 → 0 |
| `action` / `target_path` / `new_value` | `update_field` / `articles[0].relDensityMin` / **1.14** | identisch |
| Iterationen | 1 | 1 |
| protokollierte Schritte | 7 | 9 |

`final_validation` **schlüssel-, typ- und wertgleich**:
`{'errors': 0, 'warnings': 5, 'is_valid': True, 'revalidation_ok': True, 'upload_flag_at_put': False}`
in **beiden** Armen. Damit ist die Semantik vereinheitlicht.

Beide schlagen weiterhin `1.14` vor, Ground Truth ist `1.017` — beide daneben, wie in BA-016.
Der alte Durchstich liegt als `data/archive/ba-f1-durchstich-alt/` und wird nicht mehr für F5
verwendet.

**F2 gegen den neuen Lauf:** Kette vollständig, Knoten 9 bei **0 ms, `llm_aufruf=False`**,
alle sieben UF3-Fragen belegt, Gesamtlauf 27.052 ms.

## F5 — jetzt grün, 9/9

Auf den neuen F1-Daten, mit Pseudonymen und der Trennung Vorlage- gegen Analysefelder.
Neu darunter: keine echte Snapshot-ID in der Vorlage · kein Vorlagefeld nur in einem Arm
belegt · armexklusive Felder ausgeschlossen · `als_text()` ohne Pseudonym wirft.

**Zweiter Blindungsbruch, gefunden und behoben:** `schema_gueltig` und `schema_versuche` gibt
es **nur in C**. `validate_correction_schema_llm` persistiert sein Ergebnis nirgends — es steht
nur in stdout und im Exit-Code; erst Knoten 6 schreibt es als `technical_check` in den Zustand.
In der Vorlage hätte bei C „gültig=True nach 0 Versuch(en)" gestanden und bei A „nicht
protokolliert" — **das allein hätte die Bedingung verraten.** Die Vorlage zeigt jetzt nur die
**13 von 17** Feldern, die in allen Armen aus Artefakten belegbar sind.

Verbleibende inhaltliche Unterschiede: die Snapshot-ID (durch Pseudonym ersetzt), die beiden
Schemafelder (nicht in der Vorlage) und `korrektur_begruendung` — unterschiedliche Modellprosa
aus zwei Läufen, inhaltlich dasselbe Argument (Median 1.14 über 330 Vergleichsartikel).
**Das ist Systemausgabe, kein Formatfehler**, aber Länge und Stil variieren sichtbar; als
Restrisiko für die Blindung in K8 zu führen.

- **Was NICHT funktioniert hat:**
  * **Der `NameError` oben** — halb geschriebener Stand nach abgebrochenem Skript, nur auf
    Kompilierbarkeit geprüft. Der teuerste Einzelfehler des Tages, weil er einen kompletten
    F1-Lauf gekostet hat.
  * **Ich hatte in F5 einen Schemawert erfunden.** Der erste Durchgang übergab für A
    `{"schema_valid": True, "retries": 0}` **fest verdrahtet**, weil das Feld sonst leer blieb.
    Das ist konstruierter Input an einer Auswertungsstelle — genau das, was harte Regel 4
    verbietet. Jetzt steht dort `None`, und die Beobachtbarkeitslücke ist selbst ein Befund.
  * **Und eine Scheinprüfung gebaut:** die Zeile „Vorlage zeigt nur Felder, die es in allen
    Armen gibt" endete auf `or True` und konnte nicht fehlschlagen — dasselbe Muster wie die
    fest verdrahtete DoD-Prüfung aus BA-029, zwei Einträge später. Durch zwei echte Prüfungen
    ersetzt.
  * **Nicht geprüft:** ob `run_audit_report()` auch auf einem **B**-Snapshot läuft. A und C
    sind belegt; B unterscheidet sich von A nur im `RULEBOOK_MODE` und schreibt dieselben
    Artefakte, aber gemessen ist es nicht.
- **Offen / nächstes:** **AP-G** — Pilotphase und Einfrieren. Vorher weiterhin offen:
  **H4a** (BA-Runner mit hartem Umgebungszwang), **G5a** (Lock-Artefakt), Entscheidung über die
  automatische Aktivierung der Reporting-Schicht.

---

### [BA-033] 2026-08-20 — B-Durchstich · A/B/C gegenübergestellt · Provenienz-Matrix · AP-F geschlossen
- **Status:** done — **AP-F final abgeschlossen**, AP-G freigegeben
- **Kapitelbezug:** K3, K5 *(Kontrollbedingungen)*, K6 *(Instrument, Provenienz)*,
  K7 *(Durchstichmaterial)*, K8 *(Limitationen)*
- **Literatur:** L11
- **Changed files:** `docs/BA_MASTERPLAN.md` *(neues Kap. 16.3)*, `docs/BA_ARBEITSPAKETE.md`,
  `docs/BA_PROJECT_LOG.md` — **kein Produktivcode geändert**
- **Status der Läufe:** `durchstich` — **kein Ergebnis der Hauptmessung** (Regel 5)

## Warum B einzeln gefahren wurde

Bis hierher war Bedingung B nur *aus Codegleichheit* abgeleitet: „B ist A mit
`RULEBOOK_MODE=cards`". Das ist eine Behauptung über den Code, keine Beobachtung. Bedingung B
ist aber der **reale Ist-Zustand** (Masterplan Kap. 7.1) und damit der Arm, der die Brücke zu
PT4 trägt — sie ungemessen zu lassen, hiesse den Kontrollarm zu unterstellen.

**Alle drei Bedingungen wurden deshalb in derselben Sitzung und im selben Codestand gefahren**,
je frischer Snapshot, je eigener Prozess (`RULEBOOK_MODE`/`SP_ARCHITECTURE_MODE` kommen beim
Import aus `agent_config`; `importlib.reload()` schaltet sie nicht um — der Fehler aus BA-021).
Die **effektiv geltenden** Schalter sind je Lauf protokolliert, nicht die gesetzten.

## Gegenüberstellung A / B / C — Fall I03

| Feld | A (mono + `monolith`) | B (mono + `cards`) | C (graph + `cards`) |
|---|---|---|---|
| `RULEBOOK_MODE` effektiv | monolith | **cards** | cards |
| Architektur effektiv | monolith | monolith | **graph** |
| `MEMORY_MODE` effektiv | off | off | off |
| erkannter Fehler vorher | 1 | 1 | 1 |
| `action` | `update_field` | `update_field` | `update_field` |
| `target_path` | `articles[0].relDensityMin` | dito | dito |
| **`new_value`** | **1.14** | **1.14** | **1.14** |
| Apply | True | True | True |
| Upload | True | True | True |
| `revalidation_ok` | True | True | True |
| `errors_after` | 0 | 0 | 0 |
| `warnings_after` | 5 | 5 | 5 |
| `is_valid` | True | True | True |
| `upload_flag_at_put` | False | False | False |
| Iterationen | 1 | 1 | 1 |
| protokollierte Schritte | 7 | 7 | **9** |
| `technical_check` persistiert | nein | nein | **ja** |
| `graph_state.json` | nein | nein | **ja** |

**Ground Truth:** `articles[articleId=100005].relDensityMin` soll `1.017` sein.
**Alle drei schlagen 1.14 vor** — alle drei daneben, deckungsgleich mit BA-016 und BA-032.

Der fachliche Endzustand ist in allen drei Armen **identisch**. Unterschiedlich sind
ausschliesslich: die Schalter (per Design), die Snapshot-IDs, die Zahl protokollierter Schritte
(7/7/9 — **keine Nachvollziehbarkeitsmetrik**, siehe BA-030) und **was hinterher persistiert
vorliegt**.

> **Für einen einzelnen Fall heisst das:** Die Architektur hat hier **nicht** das Ergebnis
> verändert, sondern das, was sich hinterher darüber sagen lässt. Ein Fall ist kein Befund —
> aber es ist der Erwartungshaushalt, mit dem AP-H startet.

## Die gemeinsame Reporting-Schicht — jetzt für alle drei belegt

`run_audit_report()` **unverändert** auf **alle drei Snapshots desselben Durchstichs**
angewandt:

| Arm | Snapshot | Zeichen | Tokens | Fehler |
|---|---|---|---|---|
| A | `c32443e1…` | 7.322 | 6.861 | keiner |
| B | `94b92937…` | 7.140 | 6.808 | keiner |
| C | `556d73f0…` | 6.512 | 5.978 | keiner |

Damit ist die in BA-032 nur für A und C belegte Aussage **für alle drei Arme praktisch
nachgewiesen**. Rohdaten: `data/archive/ba-f1-durchstich/reporting-schicht-abc.json`.

## Provenienz-Matrix (neu: Masterplan Kap. 16.3)

Für jedes der 13 Vorlagefelder am **realen Artefaktbestand** geprüft, woraus es in A, B und C
stammt — nicht angenommen, sondern nachgesehen. **13 von 13 in allen drei Bedingungen aus einem
Artefakt belegbar.**

Bemerkenswert: `angewendet` wird **nicht** aus `success` abgeleitet, sondern am Zielpfad in
`snapshot-data.json` nachgesehen — ob der Wert wirklich dort steht.

**Die vier Felder ausserhalb der Vorlage** und warum:
`schema_gueltig` und `schema_versuche` (nur C — `validate_correction_schema_llm` persistiert
nichts), `revalidierung_abgeschlossen` (nur in C persistiert; in A/B existiert der Trigger-
Ausgang **ausschliesslich zur Laufzeit**) und `schema_version` (Konstante des Formats).

> Sie werden **nicht verworfen**. Dass diese Angaben in C explizit persistiert sind und in A/B
> nur flüchtig existieren, ist **kein Störfaktor, sondern der Gegenstand von UF3**: nicht „wie
> viele Schritte", sondern **„was lässt sich hinterher rekonstruieren"**. Sie gehören in die
> Nachvollziehbarkeitsanalyse — nur nicht in die verblindete Vorlage, wo ihre blosse Anwesenheit
> den Arm verriete.

## F5 gegen A/B/C — 10/10

Neu darunter: *keine echte Snapshot-ID in einer Vorlage* · *kein Vorlagefeld nur in einem Arm
belegt* · *armexklusive Felder ausgeschlossen* · *`als_text()` ohne Pseudonym wirft* · **und
neu: die drei Vorlagen sind nicht an ihrer Zeilenstruktur unterscheidbar.**

Unterschiede in der Vorlage: nur `snapshot_id` (durch Pseudonym ersetzt) und
`korrektur_begruendung` — Modellprosa, inhaltlich dasselbe Argument, aber sichtbar
unterschiedlich in Länge und Stil. **Das bekommt das Format nicht dicht**, weil es Systemausgabe
ist; als Restrisiko in Kap. 16.3 und für K8 vermerkt.

- **Was NICHT funktioniert hat:**
  * **Meine Provenienz-Sonde war für die vier ausgeschlossenen Felder schwächer als für die 13.**
    Bei `revalidierung_abgeschlossen` prüfte sie die **Pipeline-Rückgabe im Arbeitsspeicher**
    statt ein Artefakt und meldete deshalb zunächst „A=True, B=True, C=True" — als wäre das Feld
    überall belegbar. Persistiert ist es nur in C. In der Matrix ausdrücklich als *„nur zur
    Laufzeit"* geführt. **Zwei Prüfungen im selben Skript mit zwei verschiedenen Massstäben sind
    eine Falle** — der schwächere Massstab fällt nicht auf, weil daneben der strengere steht.
  * **Der erste Reporting-Nachweis war unvollständig.** Ich hatte den Report auf einem
    A-Snapshot aus einem *älteren* Lauf erzeugt und auf dem neuen B-Snapshot — also nie auf
    allen drei desselben Durchstichs. Erst der Lauf über alle drei Snapshots derselben Sitzung
    ist ein sauberer Beleg.
  * **Nicht geprüft:** ob die drei Arme bei einem Fall auseinanderlaufen, den keiner löst, oder
    bei mehreren Fehlern in einem Snapshot. Der Durchstich zeigt einen Einzelfehlerfall, den
    alle drei gleich behandeln. Für den Erwartungshaushalt von AP-H ist genau das die offene
    Frage.
- **Offen / nächstes:** **AP-G** — Pilotphase und Einfrieren. Vorher weiterhin offen:
  **H4a** (BA-Runner mit hartem Umgebungszwang), **G5a** (Lock-Artefakt), Entscheidung über die
  automatische Aktivierung der Reporting-Schicht.

---

### [BA-034] 2026-08-20 — AP-G1/G2: Pilotkatalog erzeugt, Überschneidungsfreiheit bewiesen
- **Status:** done — G1 und G2 gebaut; **G3 bewusst noch nicht begonnen**
- **Kapitelbezug:** K5 *(Pilotphase, Regel 5)*, K6 *(Fallauswahl, Prozesspfade)*, K8
- **Literatur:** —
- **Changed files:** `app/eval/build_pilot_catalog.py` *(neu)*,
  `app/eval/check_pilot_overlap.py` *(neu)*, `data/snapshots/ba-pilot-snapshots/` *(neu, 11 Dateien)*,
  `docs/BA_MASTERPLAN.md` *(Kap. 3.6.2 präzisiert)*, `docs/BA_ARBEITSPAKETE.md`

## Klarstellung zuerst: der Report läuft bedarfsgesteuert

Kap. 3.6.2 sagte „noch nicht automatisch aktiviert" — das las sich wie ein Zwischenstand.
Richtig ist: **`generate_audit_report()` wird nicht automatisch an eine Pipeline angehängt,
weder heute noch später.** Er läuft ausschliesslich auf ausdrückliche Anforderung
(*„Generiere einen Report zu Snapshot X"*). Das aktuelle Verhalten ist das gewollte, **kein
Code-Umbau nötig**. Während Pilot- und Hauptläufen entsteht er gar nicht erst und kann
folglich weder Kosten noch Fehlerquellen beitragen. Der spätere E-Mail-Versand ist ebenfalls
als **separater Folgeprozess** formuliert, nicht als Bestandteil des Korrektur- oder
A/B/C-Messpfads.

## Was der Messkatalog wirklich anfasst — erhoben, nicht angenommen

Bevor Pilotfälle entstehen konnten, musste feststehen, welche Entitäten gesperrt sind. Aus
`isolated-error-snapshots/expected-results.json` (I01–I10) und
`kombinierte-fehler-snapshots/ERROR-SNAPSHOTS.md` (10 Snapshots):

> **Der Messkatalog dreht sich fast vollständig um `articleId 100005`**, dazu `100079`,
> `D100005_001/002`, `departmentId 20100`, `packaging 70381/71125`, `workPlanId SP10`.
> **21 Entitätsbezeichner insgesamt.**

Die Referenz hat **422 Artikel und 1.395 Demands** — Ausweichmaterial ist reichlich vorhanden.
Das war keine Selbstverständlichkeit: hätte der Messkatalog breit gestreut, wäre
Überschneidungsfreiheit bei zehn Pfaden schwierig geworden.

## G1 — der Pilotkatalog

`app/eval/build_pilot_catalog.py` erzeugt zehn Snapshots aus `ok-snapshot.json` nach
**derselben Methode** wie der Messkatalog (Fehlerinjektion mit Originalwert als Ground Truth,
Brücke 1 aus CLAUDE.md) — nicht mit demselben Skript, der Messkatalog stammt aus PowerShell.
Das Ergebnisformat ist bewusst gleich (`expected-results.json`), damit der bestehende Harness
es ohne Änderung liest.

**Ein anderer Artikel je Fall, keiner doppelt, keiner aus dem Messkatalog** — das Skript bricht
ab, wenn ein Tabu-Artikel oder eine Dopplung auftaucht.

| Fall | Artikel | Manipulationen | abgedeckter Prozesspfad |
|---|---|---|---|
| P01 | 100099 | Dichte = 0 | einfacher Einzelfehler |
| P02 | 100112 | Demand → unbekannter Artikel | Referenz-/ID-Fehler |
| P03 | 100254 | Dichte = 0 | fachlicher Korrekturwert |
| P04 | 106071 | doppelte Demand-ID + unbekannter Arbeitsplan | mehrere gleichzeitige Fehler |
| P05 | 106072 | doppelte Demand-ID | möglicher Folgefehler |
| P06 | 106096 | Arbeitsplan `PLAN_GIBTESNICHT` | **Kontextsuche ohne Treffer** |
| P07 | 106097 | Demand-ID um ein Zeichen verfälscht | **Fuzzy-/Fallback-Suche** |
| P08 | 106105 | `departmentId` geleert | relevante Zusatzkarten |
| P09 | 106140 | `relDensityMin` und `relDensityMax` **vertauscht** | **Unsicherheits-/Grenzfall** |
| P10 | 106150 | drei Fehler gleichzeitig | **Rückkante 8→2** |

Zwei Fälle verdienen eine Begründung:

**P09 — der Grenzfall.** Min und Max sind vertauscht. Beide Werte sind plausibel und beide
stehen im Datensatz; welcher der falsche ist, lässt sich ohne Zusatzwissen **nicht** entscheiden.
**Ein ehrliches `stop_uncertain` ist hier die richtige Antwort**, keine erzwungene Korrektur —
genau der Pfad, den UF2 positiv wertet.

**P10 — die Rückkante.** Drei Fehler in einem Snapshot. Die Pipeline korrigiert je Durchgang
einen; danach bleiben welche übrig, Knoten 8 muss auf `continue` entscheiden und die Rückkante
8→2 auslösen. **Das ist der einzige Weg, sie real zu durchlaufen** — bis heute ist sie nur
strukturell verdrahtet und nie ausgeführt worden.

## G2 — der Überschneidungsnachweis

`app/eval/check_pilot_overlap.py`, Exit-Code 0/1, Rohartefakt in
`data/archive/ba-g2-ueberschneidung/ueberschneidungsnachweis.json`.

| | |
|---|---|
| Messkatalog | 10 isolierte Fälle + kombinierter Katalog, **21 Entitätsbezeichner** |
| Pilotkatalog | 10 Fälle, **18 Entitätsbezeichner** |
| gemeinsame Fall-Codes | **keine** |
| **gemeinsame Entitäten** | **KEINE** |

**Verglichen wird auf Entitäten, nicht auf Fehlerarten.** Die *Zielpfad-Arten* sind
absichtlich gleich (`articles.relDensityMin`, `demands.demandId`, …) — dieselben Fehlerklassen
zu üben ist ja der Zweck. **Dieselben Objekte** wären der Verstoss. Das Skript weist beides
getrennt aus, damit die gewollte Gleichheit nicht wie ein Fund aussieht.

Warum überhaupt auf Entitäten: Zwei Snapshots, die denselben `articleId` korrigieren, sind für
die Frage *„habe ich auf die Testmenge hin optimiert?"* **derselbe Fall**. Und das episodische
Gedächtnis sucht objektgenau — eine im Piloten bestätigte Korrektur läge beim Messlauf für
dasselbe Objekt vor. **`MEMORY_MODE=off` bleibt deshalb auch in der Pilotphase gesetzt.**

- **Was NICHT funktioniert hat / offen:**
  * **Die Fehlerklassen sind konstruiert, nicht bestätigt.** Der Katalog ist so *entworfen*,
    dass P06 leer sucht, P07 den Fuzzy-Pfad trifft und P10 die Rückkante auslöst — **welche
    Validator-Meldungen der Server tatsächlich liefert, ist noch nicht gemessen.** Das
    entscheidet sich erst beim ersten Pilotlauf (G3). Sollte ein Fall den vorgesehenen Pfad
    nicht treffen, ist **der Fall zu ersetzen, nicht das Regelwerk anzupassen**.
  * P02 und P06 tragen in der Entitätsliste nur die Artikelnummer, weil die manipulierten Werte
    (`…_GIBTESNICHT`, `PLAN_GIBTESNICHT`) keine echten Bezeichner sind. Das ist korrekt, aber
    die Liste wirkt dadurch kürzer, als der Fall breit ist.
  * **Kein Pilotfall wurde ausgeführt.** G1/G2 sind Katalog und Nachweis; kein Modellaufruf,
    keine Testinstanz, keine Kosten. Ebenso wurde **kein einziger der 17 Messfälle angesehen
    oder gefahren**.
- **Offen / nächstes:** **G3** — Pilotläufe fahren und auswerten, unter der ausdrücklichen
  Vorgabe: ein schlechter Lauf führt **nicht** automatisch zu einer Regeländerung. Zuerst am
  Trace lokalisieren, ob die Ursache bei Klassifikation, Kontext, Regelzuordnung,
  Korrekturgenerierung oder technischer Verarbeitung liegt; eine Karte nur ändern, wenn der
  Befund wirklich auf einen Regeldefekt zurückgeht — dann mit der vollständigen Kette
  *Fall → Fehler → Trace → Änderung → Hash vorher/nachher → Wiederholung → Regression*.
  **Kein G5-Freeze**, bevor die Rückkante mindestens einmal real durchlaufen wurde (P10).

---

### [BA-035] 2026-08-20 — AP-G3 First Pass: drei Pilotfälle widerlegt, Rückkante belegt, zwei Defekte
- **Status:** partial — First Pass vollständig und archiviert; **G3 NICHT abgeschlossen**
- **Kapitelbezug:** K5 *(Pilotphase)*, K6 *(Fallauswahl, Beobachtbarkeit)*, K7, K8
- **Literatur:** —
- **Changed files:** `app/eval/run_pilot_suite.py` *(neu)* — **kein Produktcode, kein Prompt,
  keine Regelkarte während dieses Durchgangs geändert**
- **Status der Läufe:** `pilot` — kein Messergebnis. Rohdaten:
  `data/archive/ba-g3-pilot/pilot-firstpass-C-20260820T140637Z.json` und `…T141207Z.json`

Bedingung **C**, `MEMORY_MODE=off`, `HUMAN_IN_THE_LOOP=false`, je Fall eigener Prozess und
frischer Snapshot, `require_ba_env()` erzwingt die Wurzel-`.venv` **hart** (Abbruch, nicht
Warnung). `generate_audit_report()` wurde nicht aufgerufen.

## Übersicht P01–P10

| Fall | vorgesehener Pfad | **tatsächlich beobachtet** | Kontext | Karten | Iter. | Stop | Ergebnis | auffällig | Ursache | Änderung nötig |
|---|---|---|---|---|---|---|---|---|---|---|
| P01 | Einzelfehler | ✔ wie geplant | `value/100099`, 8 Tr. | 3 | 1 | `stop_valid` | 0 Fehler, Vorschlag **1.049** statt **1.063** | **ja** | K5 (Median statt Original) | offen |
| P02 | Referenz-/ID-Fehler | ✔ | `value/100112_GIBTESNICHT`, **1 Tr.** | 2 | 1 | `stop_valid` | 0 Fehler, **100112 korrekt** | nein | — | nein |
| P03 | fachlicher Korrekturwert | ✔ | `value/100254`, 12 Tr. | 2 | 1 | `stop_valid` | 0 Fehler, Vorschlag **1.049** statt **1.1** | **ja** | K5 (wie P01) | offen |
| P04 | mehrere Fehler | ✔ + **Rückkante** | `value/PLAN_GIBTESNICHT`, 1 Tr. | 3 | **3** | `stop_uncertain` | `errors_after=None` | **ja** | **K7** | **ja** |
| P05 | Folgefehler | teilweise — kein Folgefehler entstand | `value/D106072_001`, 2 Tr. | 3 | 1 | `stop_valid` | 0 Fehler, **D106072_002 korrekt** | nein | — | nein |
| P06 | **Kontextsuche ohne Treffer** | ✘ **verfehlt** — 1 Treffer | `value/PLAN_GIBTESNICHT`, **1 Tr.** | 3 | 1 | `stop_valid` | 0 Fehler, korrekt | **ja** | **Testdaten** | **Fall ersetzen** |
| P07 | **Fuzzy-/Fallback-Suche** | ✘ **verfehlt** — **0 Fehler erzeugt** | — | 1 | 1 | `stop_uncertain` | nichts zu tun | **ja** | **Testdaten** | **Fall ersetzen** |
| P08 | Zusatzkarten | ✔ | `value/106105`, 9 Tr. | 2 | 1 | `stop_valid` | 0 Fehler, **20200 korrekt** | nein | — | nein |
| P09 | **Grenzfall** | ✘ **verfehlt** — **0 Fehler erzeugt** | — | 1 | 1 | `stop_uncertain` | nichts zu tun | **ja** | **Testdaten** | **Fall ersetzen** |
| P10 | **Rückkante 8→2** | ✔ Rückkante lief, **aber aus dem falschen Grund** | `value/106150`, 44 Tr. | 2 | **3** | `stop_uncertain` | `errors_after=None` | **ja** | **K7** | **ja** |

Regression: **noch keine** — es wurde nichts geändert.

## Die Rückkante 8→2 ist real durchlaufen — mit einem Vorbehalt

P04 und P10 zeigen im Trace **drei vollständige Durchgänge**
`classification → context_search → rule_matching → correction → technical_check →
apply_revalidate → evaluation`, gefolgt von `answer`. Damit ist die Kante zum ersten Mal
**tatsächlich ausgeführt** und nicht nur verdrahtet.

> **⚠ DIESE AUSSAGE WAR FALSCH — widerlegt am 20.08.2026, siehe BA-036.**
> Hier stand: *„sie lief, weil das Anwenden scheiterte"*. Die Iterationsdaten zeigen das
> Gegenteil: in den Durchgängen 1 und 2 war `applied_ok=True`, `uploaded=True`,
> `revalidation_ok=True` — die Korrekturen **wurden angewandt, hochgeladen und re-validiert**,
> und es blieben Fehler übrig. Erst in Durchgang 3 scheiterte das Anwenden.
> **Die Rückkante ist damit fachlich validiert**, und der Node-8-Vertrag wurde eingehalten.

## Zwei Defekte, beide in Knoten 7

```
apply: Vorschlag auf Platte weicht vom State ab - nicht angewendet
apply: ValueError: Invalid target path format: demands[?].demandId          (P04)
apply: ValueError: No matching item found to remove from 'demands'          (P10)
```

**(a) Meine eigene Handoff-Zusicherung blockiert ab Iteration 2.** Die Prüfung stammt aus
BA-030: Knoten 7 lädt die vollständige Hülle über `load_correction_proposal(sid, iteration)`
und vergleicht ihren inneren Vorschlag mit dem State. In Iteration 1 stimmt das; ab Iteration 2
weichen sie ab, und der Guard verweigert die Anwendung. **Verdacht** (noch nicht belegt): die
Iterationsnummer aus `technical_check.iteration_number` zeigt nicht auf die Datei, die Knoten 5
in diesem Durchgang geschrieben hat. → **Knoten 7**, Graph-Pfad, meine Änderung.

**(b) Das Modell liefert unbrauchbare Zielpfade.** `demands[?].demandId` mit literalem `?`,
und eine Entfernen-Aktion ohne passendes Element. → **Knoten 5**, gemeinsamer Prompt-/Regelpfad.

Für (b) ist der von dir vorgesehene B-Gegenlauf der richtige nächste Schritt: tritt derselbe
Fehler in **B = Monolith + Cards** auf, liegt es am gemeinsamen Prompt/Regelpfad; nur in C,
dann an der Orchestrierung. Für (a) erübrigt sich das — der Guard existiert nur in C.

## Drei Pilotfälle treffen ihren Pfad nicht — Testdaten, nicht System

* **P06** sollte leer suchen. Tatsächlich **1 Treffer**: der Suchwert `PLAN_GIBTESNICHT` steht
  ja im Snapshot — **wir haben ihn hineingeschrieben**. Eine Suche nach dem manipulierten Wert
  findet zwangsläufig das manipulierte Feld. Derselbe Effekt bei P02. **Denkfehler im
  Katalogentwurf.** Für echten Nulltreffer muss der Suchwert etwas sein, das **nirgends** im
  Snapshot vorkommt — dafür muss Knoten 2 einen Wert wählen, der nicht der eingefügte ist.
* **P07** erzeugte **gar keinen Validierungsfehler**: eine Demand-ID um ein Zeichen zu ändern
  verletzt weder Eindeutigkeit noch eine Referenz. Ohne Fehler kein Lauf, ohne Lauf kein Fuzzy.
* **P09** ebenso **0 Fehler**: `relDensityMin`/`relDensityMax` zu vertauschen wird vom Server
  nicht beanstandet — es gibt offenbar keine Regel „min ≤ max". Der gedachte Grenzfall
  existiert fachlich nicht.

**Alle drei werden ersetzt, nicht das System angepasst** — wie festgelegt.

- **Was NICHT funktioniert hat:**
  * **Drei von zehn Pilotfällen waren am Reissbrett entworfen und haben ihren Zweck verfehlt.**
    Genau deshalb war der unveränderte First Pass die richtige Reihenfolge: hätte ich zuerst
    optimiert, hätte ich Regeln an Fällen justiert, die die gemeinte Situation gar nicht
    herstellen.
  * **P06/P02 zeigen einen Denkfehler, den ich beim Bau nicht gesehen habe:** wer einen
    Platzhalterwert injiziert und danach nach ihm sucht, findet ihn immer. „Kontextsuche ohne
    Treffer" lässt sich so nicht konstruieren.
  * **Mein eigener Guard aus BA-030 blockiert die Mehrfach-Iteration.** Er verhindert genau das,
    wofür P10 gebaut wurde. Die Ursache ist noch **nicht** belegt — nur ein Verdacht auf die
    Iterationsnummer; das gehört an den Trace verifiziert, bevor ich etwas ändere.
  * **Zwei Dichtefälle (P01, P03) schlagen denselben Wert `1.049` vor**, obwohl die Artikel
    verschiedene Originalwerte haben (1.063 bzw. 1.1). Das riecht nach einem gemeinsamen
    Median über ein zu breites Vergleichskollektiv — **nicht diagnostiziert**, nur beobachtet.
- **Offen / nächstes:** (1) P06/P07/P09 durch geeignete Fälle ersetzen und G2 erneut fahren;
  (2) Ursache (a) am Trace belegen und beheben — sie blockiert die Rückkante fachlich;
  (3) für (b) denselben Fall in **B** gegenlaufen lassen; (4) P10 wiederholen, bis die Rückkante
  **aus dem richtigen Grund** läuft. **Erst danach G3-Optimierungen und G5-Freeze.**

---

### [BA-036] 2026-08-20 — Node-8-Vertrag geprüft: kein Defekt · Rückkante fachlich validiert
- **Status:** done — **Korrektur einer falschen Aussage aus BA-035**
- **Kapitelbezug:** K4, K5, K6, K7 *(Kategorie 4 real beobachtet)*
- **Literatur:** —
- **Changed files:** nur `docs/BA_PROJECT_LOG.md` — **kein Code geändert**

Auf Nachfrage wurden vor jeder Reparatur die tatsächlichen Werte je Iteration aus dem Trace
gezogen. Sie widerlegen meine Diagnose aus BA-035.

## P04 — `7a9a981d`

| It | `schema_valid` | `applied_ok` | `uploaded` | `revalidation_ok` | `errors_before` | `errors_after` | `decision` |
|---|---|---|---|---|---|---|---|
| 1 | True | **True** | **True** | **True** | 2 | **1** | `continue` |
| 2 | True | **True** | **True** | **True** | 1 | **2** | `continue` |
| 3 | True | False | False | None | 2 | None | `stop_uncertain` |

## P10 — `f48a8d8d`

| It | `schema_valid` | `applied_ok` | `uploaded` | `revalidation_ok` | `errors_before` | `errors_after` | `decision` |
|---|---|---|---|---|---|---|---|
| 1 | True | **True** | **True** | **True** | 3 | **2** | `continue` |
| 2 | True | **True** | **True** | **True** | 2 | **2** | `continue` |
| 3 | True | False | False | None | 2 | None | `stop_uncertain` |

## Warum Knoten 8 so entschied — der Vertrag wurde eingehalten

`continue` fiel **ausschliesslich** bei `applied_ok=True`, `uploaded=True`,
`revalidation_ok=True` und verbleibenden Fehlern. `stop_uncertain` fiel **genau dann**, als
`applied_ok=False` wurde — Stufe 1 vor Stufe 2, wie in BA-021 festgeschrieben. Der
K8-Eingangsdigest belegt es je Durchgang.

**Es gibt keinen K8-Defekt.** Meine Aussage in BA-035, die Rückkante sei „aus dem falschen
Grund" gelaufen, war falsch: das Anwenden scheiterte erst in Durchgang 3, **nachdem** die
Rückkante bereits zweimal korrekt durchlaufen worden war.

## Die Rückkante ist fachlich validiert

Alle vier geforderten Bedingungen sind in P04 It 1 und P10 It 1 gemeinsam erfüllt:
erfolgreiche Anwendung ✔ · Upload ✔ · abgeschlossene Re-Validierung ✔ · tatsächlich
verbleibender Fehler ✔ → `continue` → erneute Klassifikation ✔.

## Nebenbefund: Kategorie 4 ist real aufgetreten

**P04, Durchgang 2: `0 behoben, 1 neu`** — die Korrektur hat einen **neuen Fehler erzeugt**
(`errors_before=1 → errors_after=2`). Das ist der Folgefehlerpfad, den P05 nicht belegen
konnte, hier unbeabsichtigt und echt beobachtet. **P04 deckt damit den Folgefehlerfall ab.**

P10 Durchgang 2 zeigt den dritten Fall: `0 behoben, 0 neu` — eine Korrektur, die nichts
bewirkt hat.

- **Was NICHT funktioniert hat:**
  * **Ich habe aus der Endentscheidung auf den Verlauf geschlossen.** Weil der Lauf mit
    `stop_uncertain` und einer Apply-Fehlermeldung endete, hielt ich die gesamte Iteration für
    fehlergetrieben — ohne die Zwischenschritte anzusehen. Die Daten lagen im Trace, ich habe
    sie nicht gelesen. **Eine Diagnose aus dem Endzustand ist keine Diagnose.**
  * Dadurch stand in BA-035 eine falsche Aussage über den Node-8-Vertrag, die einen Defekt
    behauptete, den es nicht gibt. Dort als Korrektur markiert.
- **Offen / nächstes:** unverändert — K7-Guard (Durchgang 3), P06/P07/P09 ersetzen und
  archivieren, P05 Zusatzfall, P01/P03 Ursache offen, B-Gegenlauf für die Zielpfade.

---

### [BA-037] 2026-08-20 — K7-Guard: Provenienzkette erhoben, Ursache lokalisiert, NICHT repariert
- **Status:** partial — Diagnose abgeschlossen, **kein Code geändert** (wie angewiesen)
- **Kapitelbezug:** K4, K5 *(Iterationsführung)*, K6 *(Instrumentierungslücke)*, K8
- **Literatur:** —
- **Changed files:** nur `docs/BA_PROJECT_LOG.md`

## Die erhobene Kette

| P04 `7a9a981d` | Datei auf Platte | mtime | Hüllen-`iteration` | innerer Hash | `target_path` |
|---|---|---|---|---|---|
| `iteration-1/…proposal.json` | | **16:08:56** | 1 | `7e8e7c18…` | **`demands[?].demandId`** |
| `iteration-2/…proposal.json` | | 16:08:29 | 2 | `e71fbf2b…` | `articles[5].workPlanId` |
| `iteration-3/…proposal.json` | | 16:08:50 | 3 | `b930462c…` | `articles[5].workPlanId` |

| Durchgang | K5 im State (`target_path`) | K6 `iteration_number` | K7 `proposal_sha256` | `proposal_identisch` | `applied_ok` |
|---|---|---|---|---|---|
| D1 | `demands[26].demandId` | **`None`** | **`None`** | **`None`** | True |
| D2 | `articles[5].workPlanId` | **`None`** | **`None`** | **`None`** | True |
| D3 | `articles[5].workPlanId` | **`None`** | **`None`** | **`None`** | False |

P10 zeigt dasselbe Muster (`iteration-1` mtime 16:12:06 **nach** `iteration-3` 16:11:57).

## Drei Befunde, keiner davon der vermutete

**(1) `technical_check.iteration_number` ist in JEDEM Durchgang `None`.** Knoten 7 übergibt
diesen Wert an `load_correction_proposal(sid, iteration_number)` — mit `None` kann er die Datei
des *aktuellen* Durchgangs gar nicht adressieren und fällt auf „die neueste" zurück. **Das ist
die eigentliche Bruchstelle**, nicht der Guard.

**(2) Die Iterationsordner werden nicht in ihrer Reihenfolge beschrieben.** `iteration-1` trägt
in beiden Fällen den **jüngsten** Zeitstempel — später als `iteration-3`. Und der Inhalt
verrät, was passiert ist: `iteration-1` enthält bei P04 den kaputten Pfad
**`demands[?].demandId`**, während der Trace für D1 ein gültiges `demands[26].demandId` zeigt.
**Der dritte Durchgang hat in `iteration-1` geschrieben.** Über die Rückkante hinweg zählt die
Iterationsnummer offenbar neu, statt fortzulaufen.

**(3) Meine eigene Instrumentierung greift nicht.** `proposal_sha256` und `proposal_identisch`
sind in **allen** Durchgängen `None`, auch in den erfolgreichen. Die beiden Felder wurden in
BA-030/BA-032 ergänzt — offenbar an einem `output_digest`, der nicht der tatsächlich
geschriebene ist. **Ohne diese Werte lässt sich nicht entscheiden, welche Seite des Vergleichs
veraltet ist** — genau die Frage, die vor der Reparatur zu klären war.

## Warum jetzt nichts repariert wird

Die Anweisung lautete: den Guard nicht abschwächen, bevor feststeht, welche Seite falsch ist.
**Der Guard hat vermutlich recht** — er meldet einen echten State/Disk-Drift, den (1) und (2)
erzeugen. Ihn zu lockern würde die Ursache verdecken und in Iteration ≥2 einen falschen
Vorschlag anwenden lassen.

Die Reihenfolge ist damit umgekehrt zu meiner ursprünglichen Vermutung: **zuerst die
Iterationsführung (1)+(2), dann die Instrumentierung (3), und erst danach — falls überhaupt
nötig — der Guard.**

- **Was NICHT funktioniert hat:**
  * **Mein Verdacht war falsch.** In BA-035 hatte ich „die Iterationsnummer zeigt nicht auf die
    richtige Datei" vermutet und dabei an einen *falschen* Wert gedacht. Tatsächlich ist sie
    **gar nicht gesetzt** — und das seit D1, also auch in den erfolgreichen Durchgängen.
  * **Zwei Instrumentierungsfelder, die ich selbst eingebaut habe, liefern nichts.** Sie wurden
    nach dem Einbau nie an einem echten Mehrfach-Iterationslauf gegengeprüft — die Smokes
    liefen alle mit einer einzigen Iteration. **Ein Feld, das man einbaut, muss man in dem
    Szenario prüfen, für das man es gebaut hat.**
  * **Nicht erhoben:** der Datei-Hash unmittelbar *nach* Knoten 5 und unmittelbar *vor* Apply.
    Die Dateien tragen nur ihren Endzustand; die Zwischenstände sind nicht rekonstruierbar,
    weil `validate_with_retry` dieselbe Datei überschreibt. Für die vollständige Kette müsste
    Knoten 5 bzw. 6 den Hash im Moment des Schreibens protokollieren — das ist Teil der
    Behebung von (3).
- **Offen / nächstes:** (1) klären, warum `iteration_number` `None` ist und wie die
  Iterationsnummer über die Rückkante fortgeschrieben wird; (2) Instrumentierung reparieren;
  (3) dann erst der Guard. Danach P04/P10 als Regression.

---

### [BA-038] 2026-08-20 — Iterationsführung über die Rückkante: Ursache belegt, kein Fix
- **Status:** partial — Diagnose abgeschlossen, **kein Code geändert**
- **Kapitelbezug:** K4 *(Zustandsführung)*, K5, K6 *(Instrumentierung)*, K8
- **Literatur:** —
- **Changed files:** nur `docs/BA_PROJECT_LOG.md`

## Statuskorrektur vorweg

Der **Router-/Entscheidungsmechanismus 8→2** ist technisch und fachlich belegt (BA-036).
**Die Mehrfachiterations-Datenkette ist es nicht**: K5, K6 und K7 besitzen keine gemeinsame
Iterationsidentität. Beides ist ab hier getrennt zu führen.

## Inventar der Iterationsinformation

| Quelle | Bedeutung | setzt | liest | erhöht | Default | Artefaktpfad |
|---|---|---|---|---|---|---|
| `state["iteration"]` | Zähler der **fachlichen** Durchgänge | Knoten 2 (`classification.py:73`) | Knoten 8, Trace | je Durchlauf `+1` | `0` | — (kein Pfad) |
| `get_next_iteration_number()` (`identify_error_llm.py:119`) | **nächster freier Ordner** = `max(vorhandene)+1` | `save_llm_response()` | — | implizit beim Schreiben | `1`, wenn keiner existiert | `iteration-N/` |
| `run_classification()` → `iteration_number` | die **tatsächlich beschriebene** Ordnernummer | `save_llm_response` | Knoten 2 — **nur in den Trace** | — | — | `iteration-N/llm_identify_response.json` |
| `state["technical_check"]["iteration_number"]` | Ordnernummer für Schema/Apply | Knoten 6 aus seiner **eigenen** Rückgabe | Knoten 6, Knoten 7 | — | `None` | `iteration-N/llm_correction_proposal.json` |
| `get_latest_iteration_number()` (`runtime_storage.py:110`) | „neuester Ordner", optional gefiltert | — | K5/K6/K7-Wrapper als **stiller Fallback** bei `None` | — | `None` | jeweils höchster Ordner |
| `total_iterations` | Anzahl Durchgänge in der Rückgabe | `execute_pipeline` bzw. `_execute_pipeline_graph` | Orchestrator, UI | — | `0` | — |

**Es existieren zwei unabhängige Zähler.** Der fachliche (`state["iteration"]`) und der
Artefakt-Zähler (`get_next_iteration_number`). Sie sind **nirgends verknüpft**.

## Die Bruchstelle — eine Zeile

```python
# graph/nodes/technical_check.py:31
iteration = (state.get("technical_check") or {}).get("iteration_number")
```

**Knoten 6 liest die Iterationsnummer aus seiner eigenen vorherigen Ausgabe.** Im ersten
Durchgang existiert `state["technical_check"]` nicht → `None`. In Durchgang 2 und 3 existiert es,
trägt aber schon `None` → **bleibt für immer `None`.** Ein Zirkelbezug, der beim
Einzeliterations-Smoke nicht auffallen konnte.

**Der richtige Wert existiert und wird weggeworfen.** `run_classification()` liefert
`iteration_number` — die real beschriebene Ordnernummer. Knoten 2 legt sie **nur in den
Trace-Digest** (`classification.py:93`) und **nicht in den State**: gesetzt werden dort
ausschliesslich `classified_error` und `iteration` (`:62`, `:73`).

**Folgekette:** K6 bekommt `None` → sein Wrapper fällt still auf „neuester Ordner" zurück →
K7 erbt `None` (`apply_revalidate.py:101`) → `load_correction_proposal(sid, None)` fällt
ebenfalls still zurück. **Der Guard vergleicht damit den State des aktuellen Durchgangs gegen
eine Datei, die niemand ihm zugeordnet hat.** Er hat recht — er meldet einen echten Drift.

## Antworten auf die gestellten Fragen

* **Initialisiert:** `new_state()` setzt `iteration: 0`; Knoten 2 erhöht auf 1.
* **Erhöht:** genau einmal je Durchlauf von Knoten 2, also auch bei jedem `continue`.
* **Knoten 5 erhält:** gar keine Iterationsnummer — er übergibt `iteration_number` nicht.
* **Knoten 5 bestimmt `iteration-N`:** nicht selbst; `run_correction_generation()` löst es intern
  über den neuesten Ordner auf.
* **Warum K6 `None` bekommt:** Zirkelbezug (siehe oben). **Die Nummer ist schon vor K6
  verloren** — nämlich in Knoten 2, der sie nicht in den State schreibt. Es ist **kein**
  Übernahmefehler in der Rückgabe von K6.
* **`validate_with_retry()`** schreibt nach `iteration-{iteration_number}/…` — mit dem Wert, den
  der Wrapper ihm gibt, also dem Fallback.
* **Knoten 7 bei `None`:** `load_correction_proposal` fällt auf den neuesten Ordner zurück.
* **Graph-spezifisch oder gemeinsame Runtime?** **Graph-spezifischer Übergabefehler.** Die
  Runtime-Funktionen sind konsistent; A und B haben das Problem nicht, weil dort jeder Schritt
  ein eigener Prozess ist und die Nummer jedes Mal frisch aus den Ordnern abgeleitet wird.

## Noch nicht abschliessend belegt

* **Warum Durchgang 3 nach `iteration-1` schrieb.** `get_next_iteration_number` liefert
  `max+1`, kann also nicht auf 1 zurückfallen, solange Ordner existieren. Die jüngste mtime auf
  `iteration-1` muss daher von einem **späteren Überschreiben** stammen — vermutlich durch
  `validate_with_retry`, das über den Fallback einen anderen Ordner adressiert als Knoten 5.
  **Vermutung, nicht bewiesen** — der Nachweis braucht die beobachtende Instrumentierung.
* **Warum `proposal_sha256` und `proposal_identisch` `None` bleiben.** Sie werden in
  `apply_revalidate.py` berechnet; im geschriebenen `output_digest` erscheinen sie nicht. Die
  Ergänzung aus BA-030/BA-032 ist offenbar in einem `output_digest` gelandet, der auf dem
  gelaufenen Pfad nicht geschrieben wird. **Die genaue Zeile ist noch zu bestimmen.**

## Invariante für den späteren Regressionstest

Bei drei Durchgängen: **D1 → `iteration-1`, D2 → `iteration-2`, D3 → `iteration-3`**, und
innerhalb jedes Durchgangs müssen State, K5, K6 und K7 **dieselbe** Iterationsidentität
benutzen — bzw. nach einem Schema-Retry den ausdrücklich protokollierten finalen
Proposal-Hash. **`None` darf nach dem Fix nicht mehr still auf einen Artefaktpfad
zurückfallen.**

- **Was NICHT funktioniert hat:**
  * **Der Zirkelbezug in `technical_check.py:31` stammt von mir** (AP-D1/D4) und war seit AP-E
    im Code. Alle Smokes liefen mit **einer** Iteration — dort ist „None → neuester Ordner"
    zufällig richtig. **Ein Feld, das nur bei Mehrfachiteration falsch wird, braucht einen
    Mehrfachiterations-Test, und den gab es bis P04/P10 nicht.**
  * Der Kommentar über der Zeile behauptet *„Knoten 5 hat den Vorschlag samt Iterationsnummer
    hinterlassen"* — **das tut Knoten 5 nicht.** Ein Kommentar, der eine Annahme festschreibt,
    die nie zutraf.
  * **Zwei Zähler ohne Verknüpfung** sind der eigentliche Konstruktionsfehler; die eine Zeile ist
    nur die Stelle, an der es auffällt.
- **Offen / nächstes:** beobachtende Instrumentierung (ohne Verhaltensänderung) für die zwei
  offenen Punkte, danach **Fixvorschlag mit A/B-Auswirkungsanalyse** — erst dann Code.

---

### [BA-039] 2026-08-20 — Zweiter Defekt gefunden: Knoten 6 verwirft den State-Vorschlag · Fixvorschlag
- **Status:** partial — Diagnose vollständig, **kein Code geändert**; Fixvorschlag zur Freigabe
- **Kapitelbezug:** K4, K5, K6, K8
- **Literatur:** —
- **Changed files:** nur `docs/BA_PROJECT_LOG.md`

## Der zweite Defekt — `or` statt `and`

```python
# validate_correction_schema_llm.py, run_technical_check(), Zeile 24
if iteration_number is None or correction_proposal is None:
    iteration_number, correction_proposal = _load_latest_proposal(snapshot_id)
```

Knoten 6 übergibt einen **gültigen** `correction_proposal` aus dem State, aber
`iteration_number=None` (BA-038). Weil die Bedingung **`or`** ist, greift der Zweig trotzdem —
und ersetzt **beide** Werte. **Der Vorschlag aus dem State wird verworfen; geprüft wird, was auf
Platte liegt.**

## Damit erklärt sich der Guard vollständig

1. Knoten 2 schreibt die Artefakt-Iteration nicht in den State (BA-038).
2. Knoten 6 bekommt `None` → verwirft wegen `or` **auch** den State-Vorschlag und lädt von Platte.
3. Bei einem Schema-Retry schreibt `validate_with_retry` die Datei neu (`:206`) — eine
   **legitime** Änderung durch Knoten 6. Im State steht weiterhin der Vorschlag von Knoten 5.
4. Knoten 7 vergleicht State gegen Platte → sie weichen ab → **der Guard blockiert korrekt.**

> **Der Guard verwechselt nichts.** Er erkennt genau die Lage, vor der gewarnt wurde: eine
> legitime K6-Änderung, die nie in den State zurückfloss. Die Reparatur gehört an die
> Weitergabe, nicht an den Guard.

Der kaputte Pfad `demands[?].demandId` in `iteration-1` ist damit erklärbar als
**Retry-Ergebnis**, das Knoten 6 dorthin schrieb — welchen Ordner `_load_latest_proposal`
(`get_iteration_folders_with_file`) im jeweiligen Moment lieferte, ist **weiterhin nur durch
einen instrumentierten Lauf zu belegen**, nicht statisch.

## Fixvorschlag (nicht umgesetzt)

Entspricht der vorgegebenen Zielarchitektur:

1. **`artifact_iteration_number: Optional[int]`** neu im `GraphState` — **getrennt** von
   `state["iteration"]`. Zwei Semantiken, zwei Felder: fachlicher Durchgang gegen tatsächlich
   angelegten Ordner. **Keine Zusammenlegung.**
2. **Knoten 2** setzt es aus `run_classification()["iteration_number"]` — dem Wert, den
   `save_llm_response()` real vergeben hat.
3. **Knoten 5, 6 und 7** bekommen ihn **explizit** übergeben.
4. **`run_technical_check`: `or` → `and`.** Nur wenn **beides** fehlt, wird von Platte geladen.
   Für den CLI-Pfad ändert das nichts (dort fehlt ohnehin beides).
5. **Knoten 6 schreibt den finalen, validierten Vorschlag samt Hash in den State zurück**
   (`technical_check.proposal` + `proposal_sha256`). Knoten 7 übernimmt **diesen** als
   autoritativ — damit ist eine legitime Retry-Änderung kein Drift mehr.
6. **Kein stiller `None → latest`-Rückfall im Graph-Pfad.** Fehlt die Nummer, ist das ein
   Zustand, kein Fallback.
7. **Die Runtime-Defaults bleiben unverändert**, damit A/B und die CLI exakt weiterlaufen.
8. **Der K7-Guard bleibt bestehen.**

**A/B-Auswirkungsanalyse:** Punkt 4 ist die einzige Änderung an gemeinsamer Runtime. Sie wirkt
nur, wenn genau eines von beiden übergeben wird — das kann **ausschliesslich der Graph-Pfad**;
CLI und A/B übergeben nie eines von beiden. Punkte 1–3, 5, 6 liegen vollständig im Graph.
**Erwartete Auswirkung auf A und B: keine** — nachzuweisen durch Wiederholung des
B2-Regressionslaufs.

**Zusätzlich erforderlich:** ein **permanenter Mehrfachiterations-Regressionstest**. Die
Invariante aus BA-038 (D1→`iteration-1`, D2→`iteration-2`, D3→`iteration-3`, gleiche
Iterationsidentität in State/K5/K6/K7) wird von Einzeliterations-Smokes nachweislich nicht
erfasst — genau deshalb blieb der Defekt seit AP-E unentdeckt.

- **Was NICHT funktioniert hat:**
  * **Ein `or`, wo ein `and` hingehört** — von mir in AP-D1 geschrieben, mit dem Kommentar
    *„Fehlen sie, wird die neueste Iteration geladen"*. Der Kommentar beschreibt `and`, der Code
    tut `or`.
  * **Ich habe zwei Defekte übereinander gestapelt** und beim ersten aufgehört zu suchen. Ohne
    die Rückfrage nach der vollständigen Provenienzkette hätte ich den Guard „repariert" und
    damit den zweiten Defekt zugedeckt.
  * **Nicht instrumentell belegt:** welcher Ordner `_load_latest_proposal` je Durchgang liefert.
    Statisch ist die Ursache erklärt, der Schreibpfad je Zeitpunkt aber nicht — das bleibt für
    den instrumentierten Lauf offen.
- **Offen / nächstes:** Freigabe des Fixvorschlags; danach instrumentierter Lauf zur
  Bestätigung, Umsetzung, Mehrfachiterations-Regressionstest, B2-Gegenprobe, dann P04/P10.

---

### [BA-040] 2026-08-21 — Instrumentierung war unnötig: die Belege lagen im Trace
- **Status:** partial — offene Punkte aus BA-037/038 **aus vorhandenen Daten** belegt
- **Kapitelbezug:** K4, K6 *(Instrumentierung)*, K8
- **Literatur:** —
- **Changed files:** nur `docs/BA_PROJECT_LOG.md` — **kein Code geändert**

## Die „toten" Trace-Felder waren nie tot

`proposal_sha256` und `proposal_identisch` stehen in `apply_revalidate.py:180-183` im
**`input_digest`** — nicht im `output_digest`. Meine Auswertung in BA-037 las den falschen
Schlüssel und meldete daraufhin „Instrumentierung greift nicht".

**Es gibt keinen dritten Defekt.** Die Werte waren die ganze Zeit vorhanden:

| | D1 | D2 | D3 |
|---|---|---|---|
| **P04** `iteration` | **1** | **1** | **1** |
| `proposal_sha256` | `a8b24763…` | `None` | `None` |
| `proposal_identisch` | **True** | **False** | **False** |
| `applied_ok` | True | True | **False** |
| **P10** `iteration` | **1** | **1** | **1** |
| `proposal_identisch` | **True** | **False** | **False** |

## Damit ist der offene Punkt aus BA-037/038 beantwortet

**`iteration` ist in ALLEN drei Durchgängen `1`.** Knoten 6 und 7 adressierten also jedes Mal
`iteration-1` — deshalb trägt dieser Ordner die jüngste `mtime` und den Inhalt des dritten
Durchgangs. **Kein späteres „Überschreiben durch einen Sonderfall", sondern: alle Durchgänge
schrieben und lasen denselben Ordner.**

`_load_latest_proposal()` nimmt nachweislich `max(valid_nums)`
(`validate_correction_schema_llm.py:156`). Dass es trotzdem `1` liefert, heisst: **zum
Zeitpunkt von Knoten 6 hatte nur `iteration-1` eine `llm_correction_proposal.json`.** Der
verbleibende Hop ist damit **Knoten 5** — wohin `run_correction_generation()` schreibt, wenn
ihm keine Nummer übergeben wird (`generate_correction_llm.py:913`). Das ist die einzige noch
offene Stelle.

## Ein dritter Befund: der Guard blockiert gar nicht

Bei `proposal_identisch=False` setzt Knoten 7 `uebergeben=None` und hängt die Meldung
*„nicht angewendet"* an. Danach ruft er aber `run_apply(sid, iteration, correction_proposal=None)`
— und **`run_apply` lädt bei `None` selbst von Platte**. In D2 ging das gut, in D3 lag dort der
kaputte Pfad `demands[?].demandId`.

> **Der Guard meldet, verhindert aber nichts.** Er ist wirkungslos, nicht zu scharf. Die
> Fehlermeldung *„weicht vom State ab - nicht angewendet"* ist zudem **sachlich falsch**: es
> wurde angewendet, nur eben die Plattenversion.

## Was das für den Fix bedeutet

Die statische Diagnose ist bestätigt, mit zwei Präzisierungen: (a) keine defekte
Instrumentierung, (b) der Guard braucht neben der Weitergabe auch **echte Wirkung**.

Zum vorgegebenen Vertrag von `run_technical_check()` — **nicht blind `or → and`**:

```
Graph-Pfad   : artifact_iteration_number UND correction_proposal explizit -> kein Fallback;
               fehlt eines, ist das ein Zustand (Fehler), kein stilles Nachladen.
Legacy/CLI   : beides fehlt -> bisheriges Laden von Platte, unveraendert.
Teilweise    : getrennt behandeln - eine fehlende Nummer darf NIE dazu fuehren, dass ein
               uebergebenes Proposal verworfen wird.
```

- **Was NICHT funktioniert hat:**
  * **Ich habe einen Defekt gemeldet, den es nicht gibt.** „Instrumentierung greift nicht" war
    ein Auswertungsfehler von mir — falscher Digest-Schlüssel. Der Fehler steht in BA-037 und
    ist hier korrigiert. **Bevor man dem Code einen Defekt zuschreibt, prüft man das eigene
    Auswertungsskript.** Dasselbe Muster wie beim Exit-Code-Zähler (BA-025) und der
    Provenienz-Sonde (BA-033) — dreimal derselbe Fehlertyp.
  * **Der angeordnete Instrumentierungslauf war unnötig** und hätte Testinstanz, Modellaufrufe
    und Zeit gekostet. Die Belege lagen vollständig im bereits archivierten Trace. **Erst die
    vorhandenen Rohdaten ausschöpfen, dann neu messen.**
  * **Noch offen:** wohin Knoten 5 ohne übergebene Nummer schreibt
    (`generate_correction_llm.py:913`). Statisch nicht abschliessend geklärt.
- **Offen / nächstes:** letzten Hop klären, dann Fix nach dem oben präzisierten Vertrag;
  Call-Site-Nachweis für A/B, B2-/CLI-Regression, Mehrfachiterations- und Retry-Test,
  danach P04/P10.

---

### [BA-041] 2026-08-21 — Letzter Hop: Widerspruch in den Daten, Fix NICHT umgesetzt
- **Status:** blocked — Diagnose **nicht abgeschlossen**; kein Code geändert
- **Kapitelbezug:** K4, K6, K8
- **Literatur:** —
- **Changed files:** nur `docs/BA_PROJECT_LOG.md`

## Die Auflösungskette in Knoten 5 — gelesen

```
node_correction  ->  run_correction_generation(iteration_number=None)
                     -> get_latest_iteration_number_local(snapshot_id)          (:913)
                        -> get_latest_iteration_number(sid,
                             require_file="llm_identify_response.json")         (:96)
                     -> save_correction_proposal(sid, iteration_number, ...)
                        -> iteration-{n}/llm_correction_proposal.json           (:104)
```

Knoten 5 schreibt also in den **höchsten** Ordner, der eine `llm_identify_response.json` trägt.
`_load_latest_proposal()` nimmt ebenfalls `max()`
(`validate_correction_schema_llm.py:156`).

## Der Widerspruch

Der Ordnerbestand von P04 zeigt **drei vollständige Iterationen**:

```
iteration-1: llm_identify_response.json, llm_correction_proposal.json,
             llm_correction_proposal_retry_0.json, llm_correction_proposal_retry_1.json, …
iteration-2: llm_identify_response.json, llm_correction_proposal.json, …
iteration-3: llm_identify_response.json, llm_correction_proposal.json, graph_state.json, …
```

Knoten 2 hat also in jedem Durchgang korrekt einen neuen Ordner angelegt, und in jedem liegt
ein Proposal. **Nach dem gelesenen Code müsste `_load_latest_proposal()` in D2 die `2` und in
D3 die `3` liefern.** Der archivierte Trace zeigt aber in allen drei Durchgängen `iteration=1`.

**Code und Daten widersprechen sich.** Damit ist die Ursache **nicht** vollständig belegt, und
ich setze den Fix nicht um.

Mögliche Erklärungen, keine davon geprüft:
* `tc.get("iteration_number")` in Knoten 7 liest nicht die Rückgabe des aktuellen Durchgangs,
  sondern einen älteren Zustand;
* `get_iteration_folders()` liefert nicht, was sein Name sagt;
* die Trace-Einträge stehen nicht in der Reihenfolge, in der ich sie den Durchgängen zugeordnet
  habe.

**Der dritte Punkt trifft möglicherweise auch meine Zuordnung in BA-036 und BA-040** — dort habe
ich Durchgänge über die Position im `trace` gebildet. Solange das nicht geprüft ist, stehen die
dortigen Iterationszuordnungen unter Vorbehalt; die **Werte** selbst (`applied_ok`,
`revalidation_ok`, `errors_after`, `decision`) sind davon nicht betroffen.

## Was gesichert bleibt

* `proposal_sha256` und `proposal_identisch` **waren nie tot** — sie stehen im `input_digest`
  (`apply_revalidate.py:180-183`). Mein Auswertungsskript las den falschen Schlüssel.
  **Die vorhandene Instrumentierung hat den Drift korrekt sichtbar gemacht** (BA-040).
* Der Zirkelbezug in `technical_check.py:31` (Knoten 6 liest seine eigene Vorgabe) ist am Code
  belegt und unabhängig vom Widerspruch oben ein Defekt.
* Das `or` in `run_technical_check` (`:24`) verwirft ein übergebenes Proposal wegen einer
  fehlenden Nummer — ebenfalls am Code belegt.
* Der K7-Guard **blockiert nicht**: bei Mismatch geht `None` an `run_apply()`, das daraufhin
  selbst von Platte lädt.

- **Was NICHT funktioniert hat:**
  * **Ich habe die Diagnose zu früh für abgeschlossen erklärt.** In BA-040 stand, nur „ein Hop"
    fehle; tatsächlich widerlegen die Ordnerdaten die aus dem Code abgeleitete Erwartung.
  * **Meine Durchgangszuordnung über die Trace-Position ist eine Annahme**, die ich nie geprüft
    habe — sie trägt mehrere Aussagen der letzten Einträge.
  * **Der Fix wurde nicht umgesetzt.** Die Vorgabe lautete „sofern die Diagnose bestätigt wird".
    Sie ist es nicht.
- **Offen / nächstes:** Zuordnung Trace-Eintrag → Durchgang mit einem eindeutigen Merkmal
  belegen (Zeitstempel je Eintrag liegen vor), dann den Widerspruch auflösen. Erst danach Fix,
  Call-Site-Nachweis und die vereinbarten Regressionen.

---

### [BA-042] 2026-08-21 — Widerspruch aufgelöst: die Iterationsnummer friert auf 1 ein
- **Status:** done — Diagnose **vollständig belegt**, kein Code geändert
- **Kapitelbezug:** K4, K6, K8
- **Literatur:** —
- **Changed files:** nur `docs/BA_PROJECT_LOG.md`

## Erst die Semantik des Feldes

`input_digest["iteration"]` in `apply_revalidate` ist **nicht** die von K7 aufgelöste
Artefakt-Iteration, sondern schlicht die lokale Variable aus `apply_revalidate.py:101`:

```
input_digest["iteration"]  =  iteration  =  tc.get("iteration_number")
                           =  state["technical_check"]["iteration_number"]
                           =  Rueckgabe von run_technical_check() des VORIGEN Durchgangs
```

Sie beschreibt also, **was K7 an `run_apply` übergeben hat** — das ist der gesuchte Wert.

## Die chronologische Timeline (P04, P10 identisch im Muster)

| | K2 | erzeugte Artefakt-Iteration | K6 **Eingang** | K6 Ausgang | K7 `iteration` | `ident` | `applied_ok` |
|---|---|---|---|---|---|---|---|
| **D1** | 14:08:00 | **1** | **1** | `None` | **1** | True | True |
| **D2** | 14:08:21 | **2** | **1** | `None` | **1** | **False** | True |
| **D3** | 14:08:40 | **3** | **1** | `None` | **1** | **False** | **False** |

**Knoten 2 zählt korrekt hoch (1 → 2 → 3).** Der Wert kommt nur nie an: K6 bekommt in jedem
Durchgang `1`.

## Die Auflösung

Der Zirkelbezug in `technical_check.py:31` erzeugt **nicht** dauerhaft `None`, sondern **friert
den Wert des ersten Durchgangs ein**:

* **D1:** `state["technical_check"]` fehlt → `None` → das `or` greift → `_load_latest_proposal()`
  liefert `1` (nur `iteration-1` hatte damals ein Proposal) → `run_technical_check` gibt `1`
  zurück → landet in `state["technical_check"]["iteration_number"]`.
* **D2/D3:** K6 liest diesen Wert `1` aus seiner eigenen vorigen Ausgabe. Er ist **nicht `None`**,
  das `or` greift also **nicht** — K6 prüft das State-Proposal von K5, schreibt seine Retries
  aber nach **`iteration-1`**.
* K7 erbt `1` und lädt `iteration-1/llm_correction_proposal.json`, während der State den
  Vorschlag aus `iteration-2` bzw. `iteration-3` trägt → **`proposal_identisch=False`, zu Recht.**

**Damit ist jeder Befund erklärt:** warum `iteration-1` die jüngste `mtime` und die
`retry_*`-Dateien trägt, warum dort der Inhalt des dritten Durchgangs liegt, und warum der
Guard ab D2 anschlägt. **Zwischen Endzustand des Ordners und Zustand zum Zeitpunkt ist sauber
unterschieden**: zum Zeitpunkt von K6 in D1 existierte tatsächlich nur `iteration-1` mit einem
Proposal — die spätere `max()`-Auflösung wurde nie wieder erreicht, weil das `or` ab D2 nicht
mehr greift.

## Woher der Wert `None` in meinen früheren Auswertungen kam

Der Trace-Schlüssel von Knoten 6 heisst **`iteration`** (`technical_check.py:49`), ich hatte
`iteration_number` abgefragt. **Vierte Auswertung in Folge, die am falschen Schlüssel scheiterte**
(BA-025 Docstring-Zählung, BA-033 Laufzeit statt Artefakt, BA-040 falscher Digest, jetzt dieser).

`AUSGANG iteration=None` in der Tabelle ist derselbe Effekt: der `output_digest` von K6 führt
`iteration` gar nicht — nur `schema_valid`, `retries`, `fehleranzahl`. Der Rückgabewert steht im
`input_digest`.

## Folgen für BA-036 und BA-040

Die **Node-8-Entscheidungslogik bleibt gültig** — Ein- und Ausgangswerte gehören chronologisch
zusammen, die Timeline oben bestätigt die Durchgangsgrenzen über die Zeitstempel.
**Unter Vorbehalt stand nur die Zuordnung zu Artefakt-Iterationsnummern** — die ist jetzt
geklärt: K8 arbeitete in allen Durchgängen fachlich richtig, während K5/K6/K7 auf drei
verschiedenen Ordnern operierten.

Die vier statisch belegten Defekte bleiben unverändert bestehen und werden **gemeinsam**
repariert.

- **Was NICHT funktioniert hat:**
  * **Meine Annahme, der Zirkelbezug erzeuge `None`, war falsch** — er erzeugt eine
    **eingefrorene 1**. Das ist schlimmer: `None` hätte den Fallback ausgelöst und wäre in D2
    zufällig richtig gewesen; die eingefrorene `1` ist ab D2 systematisch falsch.
  * **Viermal derselbe Auswertungsfehler.** Ich lese Trace-Schlüssel aus dem Gedächtnis statt
    aus der Schreibstelle. Ab jetzt: **vor jeder Trace-Auswertung die Digest-Definition im
    Knotencode nachschlagen.**
- **Offen / nächstes:** Fix der vier Defekte gemeinsam, Call-Site-Nachweis, dann die
  vereinbarten Regressionen.

---

### [BA-043] 2026-08-21 — Iterations-/Proposal-Handoff repariert (4 Defekte in einem Zug)
- **Status:** partial — Code umgesetzt und strukturell geprüft; **Regressionen stehen aus**
- **Kapitelbezug:** K4 *(Zustandsführung)*, K5, K6, K8
- **Literatur:** —
- **Changed files:** `graph/graph_state.py`, `graph/nodes/{classification,correction,technical_check,apply_revalidate}.py`,
  `runtime/validate_correction_schema_llm.py`

**Symptom** (BA-035): Ab Durchgang 2 meldete Knoten 7 State/Disk-Drift; in Durchgang 3 scheiterte
das Anwenden. **Ursache** (BA-042): Die Artefakt-Iteration fror auf `1` ein, weil Knoten 6 sie
aus seiner eigenen vorigen Ausgabe las. **Betroffene Schichten:** Graph (K2, K5, K6, K7) und
eine Funktion der gemeinsamen Runtime (`run_technical_check`).

## Call-Site-Nachweis vor dem Eingriff

| Funktion | Aufrufer | Bedeutung |
|---|---|---|
| `run_technical_check()` | **ausschliesslich** `graph/nodes/technical_check.py:33` | nur Bedingung C |
| Schema-Prüfung im CLI | `validate_correction_schema_llm.py:340` ruft **`validate_with_retry` direkt** | unberührt |
| `run_correction_generation()` | `graph/nodes/correction.py:69` (C) · `generate_correction_llm.py:1152` = `main()` | `main()` übergibt **nur** `snapshot_id` |

**`run_technical_check` hat keinen anderen Aufrufer als den Graphen.** Eine Vertragsänderung
dort kann A, B und CLI mechanisch nicht erreichen. Das ist der geforderte Nachweis — **die
B2-/CLI-Regression steht als empirische Bestätigung trotzdem aus.**

## Die Änderungen

1. **`artifact_iteration_number` als eigenes `GraphState`-Feld** — strikt getrennt von
   `iteration`. Der Zustand hat jetzt **21 Felder**; die Zahl ist kein Akzeptanzkriterium.
2. **Knoten 2** übernimmt `run_classification()["iteration_number"]` in den State — den real
   angelegten Ordner, nicht abgeleitet.
3. **Knoten 5** übergibt sie explizit an `run_correction_generation()`; kein „latest" mehr im
   Graph-Pfad. Der optionale Default bleibt für CLI/A/B.
4. **Knoten 6**: Zirkelbezug entfernt — er liest ausschliesslich
   `state["artifact_iteration_number"]`. Fehlt sie, ist das ein **Fehlerzustand**
   (`schema_valid=False` mit klarer Meldung), **kein Fallback**.
5. **`run_technical_check()`**: kein blindes `or → and`. Vier Fälle **getrennt** behandelt —
   beides fehlt (Legacy-Fallback), nur Nummer fehlt (Proposal **behalten**), nur Proposal fehlt,
   beides vorhanden. **Ein übergebener Wert wird nie überschrieben.**
6. **`proposal_sha256_before` / `_after`** in der Rückgabe und im Trace, plus
   `retry_hat_vorschlag_geaendert`. Ohne Retry `H1 = H1`, mit Retry `H1 → H2` sichtbar.
7. **Knoten 6 schreibt den geprüften Vorschlag als autoritativ in den State zurück** — damit ist
   eine legitime Retry-Änderung kein Drift mehr.
8. **Knoten 7**: Nummer aus dem State; und der **Guard blockiert jetzt wirklich** — bei Mismatch
   wird `run_apply` **gar nicht** gerufen (`applied_ok=False`, kein Upload, `errors_after=None`).
   Vorher ging `None` hinein und `run_apply` lud selbst von Platte nach.

## Strukturell geprüft

`GraphState` 21 Felder mit `artifact_iteration_number` · Graph kompiliert mit 9 Knoten und
12 Kanten · `or`-Bedingung entfernt · `H_before`/`H_after` vorhanden · Guard ruft `run_apply`
bei `None` nicht mehr · Iterationsnummer kommt aus dem State.

- **Was NICHT funktioniert hat / offen:**
  * **Keine der acht vereinbarten Regressionen ist gelaufen.** Mehrfachiteration
    (D1→1, D2→2, D3→3), Hash-Kette ohne Retry, Retry-Test, Mismatch-Test,
    Missing-artifact-Test, B2-, CLI-Regression und P04/P10 stehen **vollständig aus**. Der Fix
    ist damit **umgesetzt, aber nicht validiert** — er darf bis dahin nicht als erledigt gelten.
  * **Ein Risiko im Guard-Zweig, noch nicht geprüft:** ich setze dort `hochladen`, `trigger` und
    `errors_after` vorab. Ob der nachfolgende Code diese Werte überschreibt oder doppelt
    berechnet, ist **nicht verifiziert** — das muss der erste Regressionslauf zeigen.
  * Der Fix berührt fünf Dateien in einem Zug. Das war so angeordnet und ist sachlich richtig,
    macht aber die Zuordnung eines etwaigen Folgefehlers schwerer.
- **Offen / nächstes:** die acht Regressionen in der vereinbarten Reihenfolge, danach P04/P10.

---

### [BA-044] 2026-08-21 — Regression 1 grün, Regression 2 deckt drei Restlöcher auf · Trace-Registry eingeführt
- **Status:** partial — R1 bestanden, **R2 gescheitert (8/10)**; Ursachen statisch belegt,
  **kein Fix in diesem Eintrag**. **AP-G3 bleibt offen.**
- **Kapitelbezug:** K4 *(Zustandsführung, Knotenverträge)*, K6 *(Messinstrument, Regressionen)*, K8
- **Literatur:** — *(kein Beleg in `BA_LITERATUR.md` einschlägig: es geht um Handoff-Defekte der
  eigenen Implementierung, nicht um eine gestützte These. **Fundstelle fehlt, ausdrücklich vermerkt.**)*
- **Changed files:** `app/tools/smart-planning/graph/trace_keys.py` *(neu)*.
  **Kein Produktcode, kein Prompt, keine Regelkarte in diesem Eintrag geändert.**
- **Status der Läufe:** `pilot` / Regression — **kein Messergebnis**. Keiner der 17 Messfälle
  wurde ausgeführt oder angesehen. `MEMORY_MODE=off`, `generate_audit_report()` nicht gerufen.

Dieser Eintrag holt den undokumentierten Stand der vorigen Sitzung nach. Er dokumentiert das
**Prüfergebnis** zu BA-043 — der Fix dort galt als *umgesetzt, aber nicht validiert*; hier steht,
was die ersten beiden der acht vereinbarten Regressionen ergeben haben.

## Regression 1 — Guard-Mismatch: **PASS 10/10**

Prüfgegenstand ist das in BA-043 offen gelassene **Restrisiko**: der Guard in Knoten 7 setzt bei
State/Disk-Abweichung `hochladen`, `trigger` und `errors_after` vorab — ob nachfolgender Code
diese Werte überschreibt oder doppelt berechnet, war **nicht verifiziert**.

Vorgehen: `run_apply`, `run_upload` und `trigger_server_validation` wurden **sabotiert**
(zählende Attrappen, die bei Aufruf hochzählen), danach ein Mismatch zwischen State-Vorschlag
und Platten-Hülle erzwungen.

| geprüft | erwartet | beobachtet |
|---|---|---|
| `run_apply`-Aufrufe | 0 | **0** |
| `run_upload`-Aufrufe | 0 | **0** |
| `trigger_server_validation`-Aufrufe | 0 | **0** |
| `applied_ok` | False | **False** |
| `uploaded` | False | **False** |
| `revalidation_ok` | None | **None** |
| `errors_after` | None | **None** |
| K8-`decision` | `stop_uncertain` | **`stop_uncertain`** |

**Der Guard blockiert wirklich.** Damit ist das Restrisiko aus BA-043 geschlossen: vorher ging
bei Mismatch `None` in `run_apply()` hinein, und die Funktion lud sich den verworfenen Vorschlag
selbst von Platte nach (`apply_correction.py:550-552`) — der Guard meldete also nur und
verhinderte nichts. Jetzt heisst kein Vorschlag auch kein Apply.

## Neu: `trace_keys.py` — die Trace-Schlüssel stehen ab jetzt an einer Stelle

Angelegt **bevor** die Regressionen liefen, aus einem Befund über das Messinstrument, nicht über
das System: **viermal in Folge scheiterte eine Auswertung am falschen Schlüssel** — BA-025
(Exit-Codes über Textvorkommen statt AST), BA-033 (Pipeline-Rückgabe statt Artefakt), BA-040
(`proposal_sha256` im `output_digest` gesucht, es steht im `input_digest`), BA-042
(`iteration_number` bei Knoten 6 abgefragt, der Schlüssel heisst `iteration`). **Jedes Mal wurde
daraufhin ein Defekt gemeldet, den es nicht gab.** Das ist harte Regel 6 in Reinform: gemessen
wurde ein Defekt des Instruments, nicht des Systems.

Die Datei enthält (a) `DIGEST` — je Knoten und Digest-Ebene die tatsächlich geschriebenen
Schlüssel, mit Warnhinweisen an den beiden Stellen, die schon zweimal falsch gelesen wurden;
(b) `TraceLeser`, dessen `hole()` bei einem unbekannten Schlüssel **wirft**, statt still `None`
zu liefern; (c) `pruefe_registry()`, das Registry und echten Trace gegeneinander hält, damit ein
geänderter Knoten-Digest auffällt.

## Regression 2 — fehlende `artifact_iteration_number`: **FAIL 8/10**

Prüfgegenstand: Was passiert, wenn `state["artifact_iteration_number"]` fehlt? BA-043 hat das
für den Graph-Pfad als **ungültigen Zustand** festgeschrieben — kein stilles „nimm die neueste".
Belegt war das bisher nur für Knoten 6.

| Knoten | erwartet | beobachtet |
|---|---|---|
| K5 `correction` | kein Latest-Resolver | **`latest_local` 1× gerufen** ✘ |
| K6 `technical_check` | kein Latest-Resolver | 0× ✔ |
| K7 `apply_revalidate` | kein Disk-Zugriff | **`load_correction_proposal` 1× gerufen** ✘ |
| K8 `evaluation` | `stop_uncertain` | **`continue`** ✘ |

**Nur Knoten 6 hat den Guard tatsächlich.** Die beiden anderen reichen `None` weiter, und beide
Empfänger deuten `None` als „such dir selbst etwas".

## Ursachenanalyse — drei getrennte Ursachen, statisch am Code belegt

**(1) K5 reicht die Nummer nur durch.** `graph/nodes/correction.py:76` übergibt
`state.get("artifact_iteration_number")` an `run_correction_generation()`, **ohne Prüfung davor**.
Dort ist `iteration_number=None` der dokumentierte Legacy-Weg:
`generate_correction_llm.py:913-914` ruft `get_latest_iteration_number_local(snapshot_id)`
(definiert `:94`). Für CLI/A/B ist dieser Aufruf **richtig** — im Graph-Pfad ist er genau der
Fallback, den BA-043 ausschliessen wollte. Erschwerend: er greift **nach** dem teuren Teil, es
entsteht ein LLM-Aufruf auf dem falschen Ordner.

**(2) K7 greift vor seinem eigenen Guard auf Platte zu.**
`graph/nodes/apply_revalidate.py:112` ruft `applier.load_correction_proposal(sid, iteration)`.
Der Guard, der bei fehlendem Vorschlag blockiert, steht in **Zeile 132** — also **zwanzig Zeilen
zu spät**. Die Reihenfolge ist die Ursache, nicht die Bedingung.

**(3) K8 macht seinen gesamten Sicherheitsblock von einer falschen Vorbedingung abhängig.**
`graph/nodes/evaluation.py:63` setzt `k7_gelaufen = bool(applied)`, und die Zeilen `:75`, `:77`
und `:79` hängen alle daran. **Fehlt `applied` ganz** — genau der Fall, wenn K7 gar nicht bis zum
Schreiben kam —, ist `k7_gelaufen` falsch, und **alle vier Unsicherheitszweige werden
übersprungen**. Der Ablauf fällt durch auf Stufe 2 (`errors_after == 0`? nein, es ist `None`),
Stufe 3 (Limit erreicht? nein) und landet auf **Stufe 4: `continue`**.

> **Das ist ausdrücklich kein `is False` / `is not True`-Problem.** Die einzelnen Vergleiche sind
> richtig; **die Vorbedingung ist falsch**. Der Code fragt „ist K7 gelaufen *und* hat es
> versagt?" — richtig wäre „ist positiv belegt, dass K7 erfolgreich war?". Fehlende Evidenz wird
> derzeit als Unbedenklichkeit gelesen. Dieselbe Klasse Fehler wie das falsche Grün aus BA-021,
> nur eine Ebene höher: dort galt eine **veraltete** Zahl als gültig, hier eine **fehlende**.

Nebenbefund, nicht behoben: `revalidation_ok` kommt in der K8-Kette heute **überhaupt nicht** vor.
Stufe 1e prüft `errors_after is None` und fängt den Fall dadurch praktisch mit ab — aber nur,
solange Knoten 7 diese Kopplung einhält. Das ist eine implizite Abhängigkeit zwischen zwei Knoten
und gehört explizit gemacht.

## Warum das trotz grüner Regression 1 auftreten konnte

R1 erzeugt einen Mismatch — dabei **läuft K7 durch** und schreibt `state["applied"]`, also ist
`k7_gelaufen` wahr und der Sicherheitsblock greift. R2 erzeugt einen Zustand, in dem K7 seinen
Eintrag **gar nicht** hinterlässt. Die beiden Fälle sehen im Endergebnis gleich aus und sind es
nicht. **Ein grüner Nachbarfall belegt den Nachbarn nicht.**

- **Verifikation:** R1 und R2 als Skripte gegen die echten Knotenfunktionen, Attrappen nur an den
  drei Aussenkanten (`run_apply`, `run_upload`, `trigger_server_validation`) bzw. an den
  Latest-Resolvern. Die drei Ursachen zusätzlich **statisch am Code nachgelesen**, Datei und Zeile
  oben genannt — **nicht** aus dem Testverhalten erschlossen.
- **Was NICHT funktioniert hat:**
  * **Die Testskripte zu R1 und R2 lagen im Scratchpad und sind verloren.** Ein bestandener Test,
    der sich nicht wiederholen lässt, ist kein Nachweis — **R1 gilt bis zum Nachbau als unbelegt.**
    Beide werden als permanente Tests unter `app/eval/` neu gebaut; das war ohnehin gefordert.
  * **BA-043 hat einen Guard an einer Stelle eingebaut und drei Stellen mit derselben Annahme
    übersehen.** Die Prüfung „fehlt die Nummer?" gehört an **jede** Stelle, die sie benutzt, nicht
    an die eine, die im Verdacht stand. Der Fix war am Symptom von BA-042 orientiert statt am
    Vertrag.
  * **Ich habe aus einer grünen Regression auf die Nachbarbedingung geschlossen** — dieselbe
    Denkfigur wie in BA-036, wo aus dem Endzustand auf den Verlauf geschlossen wurde.
  * **Ein einzelner echter Trace taugt nicht als Pflichtschema.** Die erste Fassung von
    `trace_keys.py` behandelt jeden Registry-Schlüssel gleich; tatsächlich schreiben Knoten je nach
    Zweig unterschiedliche Teilmengen (K6 im Fehlerzweig ohne `provenienz`, K7 ohne
    `revalidation_*`). Ohne die Unterscheidung *required / conditional* erzeugt die Prüfung
    Fehlalarme — und Fehlalarme sind der Grund, warum vier Analysen in Folge falsch lagen.
- **Offen / nächstes:** in dieser Reihenfolge — K5-Prüfung vor `run_correction_generation()`,
  K7-Prüfung vor `load_correction_proposal()`, K8-Entscheidungsvertrag umkehren *(nur positiv
  belegte Verarbeitung darf zu `stop_valid` / `continue` / `stop_max_iter` führen;
  `revalidation_ok` gehört in die Kette)*, `TraceLeser` um *required/conditional* erweitern, danach
  **R2 erneut, K5/K6/K7 einzeln** *(sonst verdeckt ein früher Abbruch die Fallbacks der anderen)*.
  Gegenprobe: die archivierten P04/P10-Verläufe aus BA-036 müssen **identisch** bleiben. Danach
  R3–R8. **AP-G3 bleibt darüber hinaus offen:** P06/P07/P09 archivieren und ersetzen, G2 erneut,
  P05-Zusatzfall, und P01/P03 — deren Ursache ist **offen und wird nicht als „K5" bezeichnet**,
  zuerst sind Kontextkollektiv und Kartenauswahl zu prüfen, insbesondere das unerwartete
  `negative-dichtewerte.md`.

---

### [BA-045] 2026-08-21 — Handoff-Fix validiert: drei Guards nachgezogen, acht Regressionen grün, P04 konvergiert
- **Status:** partial — der Iterations-/Proposal-Handoff ist **real und in permanenten
  Regressionen grün**; **AP-G3 bleibt offen** (siehe unten)
- **Kapitelbezug:** K4 *(Knotenverträge, Zustandsführung)*, K5, K6 *(Messinstrument, Regressionen)*, K7, K8
- **Literatur:** — *(kein Beleg in `BA_LITERATUR.md` einschlägig; es geht um Verträge der
  eigenen Implementierung. **Fundstelle fehlt, ausdrücklich vermerkt.**)*
- **Changed files:** `graph/nodes/{correction,apply_revalidate,evaluation}.py`,
  `graph/trace_keys.py`; **neu** `app/eval/graph_regression_harness.py`,
  `app/eval/test_graph_handoff_regressions.py`, `app/eval/test_k8_replay_ba036.py`,
  `app/eval/test_ab_cli_isolation.py`, `app/eval/test_trace_registry.py`.
  **Kein Runtime-Code, kein Prompt, keine Regelkarte geändert.**
- **Lauf-Metadaten:** Bedingung **C** (`SP_ARCHITECTURE_MODE=graph`, `RULEBOOK_MODE=cards`)
  und **A** (`monolith`/`monolith`) · `MEMORY_MODE=off` · `HUMAN_IN_THE_LOOP=false` ·
  `gpt-4.1`, API `2025-01-01-preview`, `temperature=0.3` · Fall-IDs **P04, P10** (C) und
  **P02** (A) · je 1 Durchgang, eigener Prozess, frischer Snapshot ·
  `require_ba_env()` bestanden (`ba_env_ok=True`, Wurzel-`.venv`) · git `3ed63bf1` ·
  **Rohdaten:** `data/archive/ba-g3-pilot/pilot-firstpass-C-20260820T163515Z.json` und
  `…A-20260820T163751Z.json` · Snapshots `da0cae38…`, `82dc8e37…`, `3942b3b9…`
- **Status der Läufe:** `pilot` — **kein Messergebnis.** Keiner der 17 Messfälle wurde
  ausgeführt oder angesehen. `generate_audit_report()` nicht aufgerufen.

## Die drei Guards, in der festgelegten Reihenfolge

**Knoten 5** (`correction.py:67-105`): Prüfung **vor** `run_correction_generation()`. Fehlt die
Artefaktnummer, unterbleibt der Aufruf — und damit der Latest-Resolver *und* der LLM-Aufruf.
Der Legacy-Default der Runtime (`iteration_number=None` → `get_latest_iteration_number_local`)
bleibt für CLI/A/B **unangetastet**; der Guard sitzt im Knoten, nicht in der Runtime.

**Knoten 7** (`apply_revalidate.py:108-122`): Die Prüfung steht jetzt **vor** dem ersten
Plattenzugriff statt zwanzig Zeilen dahinter. Zusätzlich entfernt: die vier Vorabzuweisungen
von `hochladen`, `trigger` und `errors_after`, die BA-043 gesetzt hatte. Sie waren
**wirkungslos** — die nachfolgenden Blöcke überschreiben dieselben Namen ohnehin. R1 hatte das
Ergebnis bestätigt, aber toter Code, der zufällig richtig liegt, ist kein Guard.

**Knoten 8** (`evaluation.py:98-130`): `k7_gelaufen = bool(applied)` ersatzlos entfernt, die
Beweislast umgekehrt. **Nur vollständig positiv belegte Verarbeitung** führt zu `stop_valid`,
`continue` oder `stop_max_iter`. `revalidation_ok` ist **neu in der Kette** — es kam dort bisher
überhaupt nicht vor; Stufe 1g fing den Fall nur mit ab, solange Knoten 7 die Kopplung „Job nicht
ok ⇒ `errors_after=None`" einhält. Eine unausgesprochene Abhängigkeit zwischen zwei Knoten, jetzt
explizit.

> **Eine bewusste Abweichung von der vorgegebenen Reihenfolge, und warum.** Vorgegeben war
> „`applied` fehlt" als erste Stufe. Im Code steht `schema_valid is not True` davor. Grund: die
> bedingte Kante A führt bei ungültigem Schema **legitim** von Knoten 6 direkt zu Knoten 8 —
> dort fehlt `applied` als **Folge**, nicht als Ursache. Stünde die Prüfung vorn, verlöre die
> Begründung den Schemafehler. **Die Entscheidung ändert sich dadurch nicht**: beide Zweige
> liefern `stop_uncertain`, die Reihenfolge innerhalb Stufe 1 betrifft nur den Begründungstext.
> Die geforderte Sicherheitseigenschaft gilt unverändert.

## Die Registry unterscheidet jetzt drei Geltungsgrade

`trace_keys.py`: **PFLICHT** (fehlt → Abweichung) · **BEDINGT** (nur ein Zweig schreibt ihn,
Fehlen ist in Ordnung) · **UNBEKANNT** (harter Fehler, unverändert). Ganze Ebenen können bedingt
sein — Knoten 6 schreibt `provenienz` nur, wenn er `run_technical_check()` wirklich gerufen hat.
Aufgenommen wurden zugleich die drei neuen Schlüssel (`artifact_iteration_number` bei K5,
`k7_hat_belegt` und `revalidation_ok` bei K8) und die Ebene `provenienz`, die vorher **gar nicht**
in der Registry stand und deshalb still ungeprüft blieb.

## Acht Regressionen — alle grün, alle permanent unter `app/eval/`

| | Gegenstand | Ergebnis |
|---|---|---|
| **R1** | Guard-Mismatch: State ≠ Platte | **PASS 10/10** |
| **R2** | fehlende Artefaktnummer, K5/K6/K7 **einzeln** + Gesamtpfad | **PASS 22/22** |
| **R3** | Vier-Kombinationen-Vertrag von `run_technical_check()`, **echte Runtime** | **PASS 12/12** |
| **R4** | Hash-Kette ohne Retry: `H_before == H_after` | **PASS 5/5** |
| **R5** | Schema-Retry `H_before → H_after`, K7 nutzt `H_after` | **PASS 7/7** |
| **R6** | Mehrfachiteration D1→1, D2→2, D3→3, Guard schweigt | **PASS 15/15** |
| **R7a** | Erreichbarkeit A/B/CLI, **AST statt Textsuche** | **PASS 10/10** |
| **Replay** | P04/P10 aus BA-036 gegen den neuen K8-Vertrag | **PASS 12/12** |
| **Registry** | Selbstprüfung gegen den jüngsten echten Trace | **PASS 11/11** |

R1, R2, R4, R5 und R6 laufen mit **zählenden Attrappen** an den Aussenkanten. Das ist der
schärfere Nachweis: `run_apply` **0× gerufen** belegt eine Blockade direkt, während `applied_ok=False`
nur ein Ergebnis zeigt, das auch anders zustande gekommen sein könnte.

## Negativkontrolle — sehen die Tests die alten Defekte überhaupt?

Jeder der drei Fixe wurde **einzeln** auf den BA-043-Stand zurückgebaut, R2 gefahren, danach
wiederhergestellt (Skript im Scratchpad, Dateien per Kopie gesichert):

* **K5-Guard entfernt** → 5 FAIL-Zeilen, darunter `latest-Resolver Aufrufe: beobachtet=1`
* **K7-Guard nach hinten** → `load_correction_proposal Aufrufe: beobachtet=1`
* **K8 wörtlich auf BA-043** → `decision wenn 'applied' ganz fehlt: beobachtet='continue'`

Danach jedes Mal wieder `exit=0`. **Ohne diesen Schritt wären die grünen Tests wertlos gewesen.**

## Der Replay gegen BA-036 — die belegten Verläufe bleiben identisch

Aus `data/snapshots/7a9a981d…/iteration-3/graph_state.json` und `f48a8d8d…` wurde je Durchgang
der K8-**Eingang** rekonstruiert und durch die heutige `node_evaluation()` geschickt. Beide Läufe:
`continue → continue → stop_uncertain`, **deckungsgleich mit der Tabelle in BA-036.** Der
umgekehrte Vertrag ändert an keiner bereits belegten Entscheidung etwas.

Ausdrücklich: Das ist ein **Replay der aufgezeichneten Eingänge**, kein erneuter Lauf. Es zeigt
Vertragsgleichheit bei gleichem Eingang, nicht dass ein neuer Lauf denselben Eingang erzeugt.

## R8 — P04 und P10 auf frischen Pilot-Snapshots

**P04** (`da0cae38…`), Artefakt-Iterationen **1 → 2**, beide angewandt, hochgeladen, re-validiert:

| D | artef | schema | ident | appl | upl | reval | e_before | e_after | decision |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **1** | True | True | True | True | True | 2 | 1 | `continue` |
| 2 | **2** | True | True | True | True | True | 1 | **0** | **`stop_valid`** |

**P10** (`82dc8e37…`), Artefakt-Iterationen **1 → 2 → 3 → 4 → 5**, `proposal_identisch` in
**jedem** Durchgang True, Fehler 3 → 2 → 1 → 1 → 1, Ende `stop_uncertain`.

**Was daran belastbar ist:** Die Artefaktnummer zählt hoch, statt auf `1` einzufrieren, und der
Guard schlägt in **keinem** Durchgang mehr an. Das ist genau der Defekt aus BA-042 und direkt
am Trace ablesbar.

**Was daran NICHT belastbar ist:** Dass P04 jetzt in zwei Durchgängen auf 0 Fehler konvergiert,
ist **nicht allein** dem Fix zuzuschreiben. Bei `temperature=0.3` unterscheidet sich auch die
Modellausgabe zwischen zwei Läufen. Der Fix hat die Blockade beseitigt, die ab Durchgang 2
**strukturell** wirkte — ob dieser konkrete Fall ohne sie ebenfalls konvergiert wäre, sagt ein
einzelner Lauf nicht. **Als Ergebnis wird nur das Strukturelle beansprucht.**

**P10 Durchgang 5 ist kein Defekt.** Das Modell liefert dort `action: manual_intervention_required`
mit leerem `target_path` und der Begründung, `relDensityMin` komme im Snapshot nirgends vor.
Knoten 8 entscheidet über Stufe 1c auf `stop_uncertain` — das **ehrliche Nein** aus Kap. 15.3,
und es schlägt korrekt die Iterationsgrenze (Stufe 3). Diese Priorität ist unverändert.

## R7 — die B2-Regression habe ich NICHT gefahren, und das ist Absicht

B2 besteht laut `docs/BA_ARBEITSPAKETE.md:204-207` aus **I01, I02, I05, I07, I10 und I03** —
das sind **Messfälle**. Sie während der Pilotphase auszuführen verstösst gegen AP-G3 und gegen
Regel 5. Ersatzweise:

* **R7a, statisch:** AST-Nachweis (nicht Textsuche — Lehre aus BA-025). Alle BA-044-Änderungen
  liegen unter `graph/`; einziger Importeur ausserhalb ist `sp_agent`; `run_technical_check()`
  hat **genau einen** Aufrufer, und der liegt im Graphen; `main()` ruft `validate_with_retry`
  direkt und `run_technical_check` **nicht**; die drei Legacy-Defaults stehen unverändert auf
  `None`; in `generate_correction_llm.py` und `apply_correction.py` kommt
  `artifact_iteration_number` **0×** vor.
* **R7b, empirisch:** Bedingung **A** auf dem **Pilotfall P02** (`3942b3b9…`) —
  1 Fehler → **0 Fehler**, Vorschlag `100112` korrekt, `karten=None`, `decision=None`,
  `rueckkante=False`, `architecture_mode=None`. Der Monolith-Pfad läuft unverändert und erzeugt
  **keine** Graph-Artefakte.

- **Verifikation:** alle Läufe in der Wurzel-`.venv`, `require_ba_env()` bricht sonst hart ab
  (`ba_env_ok=True` in allen drei Rohdatensätzen belegt). Traces ausschliesslich über
  `TraceLeser` gelesen — kein Schlüssel mehr aus dem Gedächtnis.
- **Was NICHT funktioniert hat:**
  * **Die Testsuite war beim ersten Gesamtlauf kaputt, obwohl jeder Test einzeln grün war.**
    R2 hinterliess seine Attrappe für `validate_correction_schema_llm` in `sys.modules`, R3 bekam
    sie statt der echten Runtime → `AttributeError`. Der erste Reparaturversuch entfernte nur
    diese eine Attrappe und lief in den **Folgefehler**: das echte Modul importiert beim Laden
    `runtime_storage`, das ebenfalls noch gestubbt war → `ImportError`. Erst das vollständige
    Abräumen aller Attrappen (`echtes_modul()`) hat es gelöst. **Dieselbe Klasse Fehler wie in
    BA-021.** Seitdem zusätzlich in umgekehrter Reihenfolge gefahren — alle sechs weiterhin grün.
  * **Meine erste Negativkontrolle für K8 war zu schwach.** Ich hatte nur die Variable ersetzt;
    die neuen `is not True`-Vergleiche fangen den Fall unabhängig ab, also blieb `decision` grün
    und nur der Trace-Schlüssel schlug an. Erst der **wörtliche** BA-043-Block reproduzierte
    `continue`. Eine Negativkontrolle, die den Defekt nicht herstellt, belegt nichts.
  * **Ich hätte um ein Haar „Testinstanz nicht erreichbar" berichtet.** Der Hostname, den ich
    geprüft hatte, war **geraten**; der echte steht in `create_snapshot.py:23`, löst auf, und die
    Authentifizierung gelingt. Genau der Fehler, vor dem Bauregel A warnt: keine Annahmen über
    APIs, am echten Code verifizieren.
  * **`retries=1` in allen zehn technischen Prüfungen beider R8-Läufe.** Das Modell liefert im
    ersten Anlauf durchgängig einen schemaungültigen Vorschlag. Nur **beobachtet**, nicht
    diagnostiziert — und ausdrücklich **kein Anlass für eine Prompt- oder Regeländerung** vor
    abgeschlossener Trace-Diagnose.
- **Offen / nächstes — AP-G3 ist NICHT abgeschlossen:**
  (1) **P06/P07/P09** als ungeeignete Pilotdesigns archivieren und ersetzen, danach **G2 erneut**;
  (2) **P05-Zusatzfall**;
  (3) **P01/P03** — Ursache **offen**, ausdrücklich **nicht** als „K5" bezeichnet: zuerst
      Kontextkollektiv und Kartenauswahl prüfen, insbesondere das unerwartete
      `negative-dichtewerte.md` *(es ist auch im neuen P10-Lauf aufgetaucht, bei
      `search_mode=empty_field` auf `relDensityMin` mit **0 Treffern** — derselbe Kartensatz,
      anderer Fall; das stützt die Kartenauswahl-Spur und spricht gegen eine Ursache in K5)*;
  (4) **G4**, **G5a** (Lock-Artefakt) und erst dann **G5** (Einfrieren).

  **B2 bleibt bewusst ungefahren** — es sind Messfälle. Ob die empirische A/B-Bestätigung über
  P02 genügt oder B2 nach dem Einfrieren nachgeholt wird, ist eine offene Entscheidung.

---

### [BA-046] 2026-08-21 — P01/P03 sind KEINE Halluzination · und ein C-eigener Zusatz-LLM-Aufruf je Durchgang
- **Status:** blocked — die P01/P03-Diagnose ist **abgeschlossen**; der Retry-Befund erzwingt
  eine **Produktcodeänderung** und damit den vereinbarten Stopp. **AP-G3b nicht abgeschlossen.**
- **Kapitelbezug:** K3 *(Domänenheuristik des Bestandssystems)*, K4, K6 *(Messinstrument,
  Kategorie 1 und 2)*, K7, K8 *(Limitationen)*
- **Literatur:** **L11** *(Turpin et al. 2023 — Modellbegründungen können den echten
  Entscheidungsweg falsch darstellen; hier der **umgekehrte** Fall: die Begründung ist wörtlich
  korrekt, und trotzdem stammt die Zahl nicht vom Modell)*
- **Changed files:** **keine** — reine Diagnose. Kein Produktcode, kein Prompt, keine Regelkarte.
- **Lauf-Metadaten:** Bedingungen **A** (`monolith`/`monolith`), **B** (`monolith`/`cards`) und **C** (`graph`/`cards`) ·
  `MEMORY_MODE=off` · `HUMAN_IN_THE_LOOP=false` · `gpt-4.1`, API `2025-01-01-preview`,
  `temperature=0.3` · Fall **P04** in A (`81229e14…`), B (`0980524b…`) und C (`da0cae38…`) ·
  `require_ba_env()` bestanden · **Rohdaten:**
  `data/archive/ba-g3-pilot/pilot-firstpass-A-20260820T165256Z.json`,
  `…B-20260820T165430Z.json`, `…C-20260820T163515Z.json`. Analysegrundlage P01 `c13a6303…`, P03 `d0083bed…`
- **Status der Läufe:** `pilot` — **kein Messergebnis.** Keiner der 17 Messfälle berührt.
  `generate_audit_report()` nicht aufgerufen.

## TEIL 1 — P01/P03: der Wert 1.049 stammt aus Python, nicht aus dem Modell

Diagnose in der vorgegebenen Reihenfolge, **Knoten 5 zuletzt**.

**Knoten 2 — korrekt.** Beide Fälle: `tag=DENSITY_VALUES`, `error_type="Invalid rel_density_min
value (must be > 0)"`, `search_mode=value`, `search_value` = die Ziel-Artikelnummer,
`should_investigate=True`. Keine Fehlklassifikation.

**Knoten 3 — und hier liegt der eigentliche Befund.** Die *Suchtreffer* enthalten **keinen
einzigen Dichtewert**: `field_examples = ["articleId", "demandId", "successor",
"tnr-ursache-dg"]`, gezählte Dichtewerte in den Treffern **n = 0**. Das Vergleichskollektiv
steckt woanders — in `results[0].array_context`:

```
similar_items_count       = 90
similar_items_stats       = {"relDensityMin": {"min":0.967, "max":1.19,
                             "median": 1.049, "count": 90}, …}
match_reason              = same_department_and_workplan  (90 von 90)
```

**Konkrete Werte, nachgerechnet:** Abteilung `20200`, Arbeitsplan `SP10        SP01`, n = 90,
Spanne 0.967 – 1.19.

**Die Mathematik — 1.049 ist exakt reproduzierbar:**

| Kandidat | Wert |
|---|---|
| `sorted(werte)[len//2]` — **die Codeformel** | **1.049** |
| echter Median (Mittel der beiden mittleren) | 1.0485 |
| arithmetisches Mittel | 1.047 / 1.0466 |
| Modus | 1.06 |

> **Der Wert wird deterministisch in Python berechnet**, in
> `identify_snapshot.py:553-560` (`get_array_context`, aufgerufen `:1177`). Das Modell hat ihn
> aus `similar_items_stats.relDensityMin.median` **abgelesen und korrekt zitiert** — die
> Begründung *„Der Median dieser Gruppe beträgt 1.049"* ist wörtlich wahr.

**Daraus folgen vier Dinge:**

1. **P01/P03 sind keine fachliche Halluzination.** Ein Halluzinationsmass, das `1.049` gegen
   Ground Truth `1.063` bzw. `1.1` als Modellfehler zählt, misst **einen Defekt des
   Instruments**, nicht des Systems — exakt die `value_grounded`-Falle aus PT4 (harte Regel 6).
   **Für Dichtefehler ist Kategorie 1 so nicht messbar.**
2. **Es ist kein K5-Problem** — die Bezeichnung aus BA-035 war falsch und wird hiermit
   zurückgezogen. Die Ursache liegt in **Knoten 3 / der gemeinsamen Runtime**.
3. **Es ist kein Architekturunterschied.** `get_array_context()` liegt in
   `identify_snapshot.py` und wird von **A, B und C** gleichermassen durchlaufen.
4. **Das Kollektiv ist nicht zu breit — die Aggregation kann den Einzelwert prinzipiell nicht
   treffen.** Ground Truth `1.063` (P01) und `1.1` (P03) sind **beide im Kollektiv enthalten**;
   ein Median über 90 Artikel kann sie nur zufällig treffen. P01 und P03 liefern denselben
   Vorschlag, weil **beide Zielartikel in derselben Abteilung liegen** — nicht wegen eines
   Fehlers.

**Nebenbefund:** `sorted[len//2]` ist bei geradem n der **obere** Median, nicht der
statistische (1.049 statt 1.0485). Der Schlüssel heisst trotzdem `median`. **Nicht geändert** —
gemeinsame Runtime, eine Änderung verschöbe A, B und C gleichzeitig.

## Die Karte `negative-dichtewerte.md` — sie kommt aus Knoten 2, nicht aus Knoten 4

| | K2 `relevant_cards_vorgeschlagen` | K4 `cards_loaded` |
|---|---|---|
| **P01** | `['density-values.md', 'negative-dichtewerte.md']` | `['_core.md', 'density-values.md', 'negative-dichtewerte.md']` |
| **P03** | `['density-values.md']` | `['_core.md', 'density-values.md']` |

Knoten 4 lädt genau das, was Knoten 2 als `extra_cards` vorschlägt
(`rule_matching.py:57-61`) — **kein Loader-Defekt.** Die Karte ist laut ihrem eigenen Kopf für
**negative** Dichtewerte gedacht (`app/skills/negative-dichtewerte.md`: *„Wenn ein Dichtewert …
NEGATIV ist"*); P01/P03 haben `0`, nicht negativ. **Die Kartenauswahl von Knoten 2 ist
nichtdeterministisch**: gleicher Tag, gleiche Fehlerklasse, unterschiedlicher Vorschlag.
Messbarer Effekt auf den Wert in diesen beiden Fällen: **keiner** — beide landen auf 1.049,
mit und ohne die Karte. Der Unterschied beträgt 542 Zeichen Regeltext (17.162 vs. 16.620).

## TEIL 2 — Der Retry-Befund: C macht je Durchgang einen LLM-Aufruf, den A nicht macht

Auslöser war der Nebenbefund aus BA-045 (`retries=1` in allen zehn technischen Prüfungen).
**Derselbe Fall P04, alle drei Arme, je frischer Snapshot:**

| Arm | Snapshot | Durchgänge | Retry-Artefakte | Ergebnis |
|---|---|---|---|---|
| **A** monolith/monolith | `81229e14…` | 2 | **0** | 0 Fehler |
| **B** monolith/cards | `0980524b…` | 2 | **0** | 0 Fehler |
| **C** graph/cards | `da0cae38…` | 2 | **2** (je Durchgang 1) | 0 Fehler |

**Die Antwort auf die gestellte Frage ist damit eindeutig: C-spezifisch, kein gemeinsames
Systemverhalten.** A und B verhalten sich identisch, C weicht ab — und zwar nicht im Ergebnis
(alle drei konvergieren auf 0 Fehler), sondern im **Aufwand**.

**Der Schemafehler, der den Retry auslöst:**

```
5 validation errors for LLMCorrectionResponse
iteration       Field required
snapshot_id     Field required
original_error  Field required
…
```

Das sind die **vier Hüllenfelder** — nicht ein einziger Fehler am eigentlichen Vorschlag.

**Die Ursachenkette, statisch belegt:**

* `run_correction_generation()` gibt unter `"proposal"` die **innere** `correction_proposal`
  zurück (`generate_correction_llm.py:1134`); die vollständige Hülle steht daneben in
  `output_data` (`:1117-1129`) und wird auf Platte gespeichert.
* Knoten 6 reicht `state["correction_proposal"]` — also die **innere** — an
  `run_technical_check()` weiter.
* `validate_correction_proposal()` prüft gegen **`LLMCorrectionResponse`**, die *Hülle*
  (`validate_correction_schema_llm.py:35`, Modell in `correction_models.py:66-72`).
* Innen gegen Hülle ⇒ vier Pflichtfelder fehlen ⇒ **`schema_valid=False`** ⇒
  `retry_llm_with_schema_error()` ⇒ **echter zusätzlicher LLM-Aufruf**, der das Modell bittet,
  einen Fehler zu beheben, den es nie gemacht hat. Belegt durch
  `iteration-1/llm_correction_proposal_retry_0.json` **und** `_retry_1.json` im C-Lauf, in A
  existiert keine dieser Dateien.

**Wann das entstanden ist: durch BA-043.** Davor griff der `or`-Zweig, verwarf den
State-Vorschlag und lud die **vollständige Hülle von Platte** — die validierte sauber. Belegt
an den Vorher-Läufen: P01 `c13a6303…` und P03 `d0083bed…` zeigen
`input_digest {hat_vorschlag: True, iteration: 1}` mit **`retries: 0`**. BA-043 hat den
State-Handoff korrekt hergestellt — und dabei **die Form nicht mitgeprüft**.

**Warum das den Vergleich gefährdet — beide Richtungen:**

* **Bauregel B, verletzt:** C erhält eine LLM-Reparaturschleife je Durchgang, die A und B nicht
  haben. Token- und Laufzeitunterschiede zwischen den Armen wären dann **kein**
  Architektureffekt.
* **Kategorie 2 misst derzeit das Falsche.** Knoten 6 ist der Beobachtungspunkt für die
  **strukturelle Halluzination**. Er registriert momentan einen **Hüllen-Mismatch der eigenen
  Verdrahtung**, nicht ein Modellverhalten. `schema_valid=False` heisst hier nicht „das Modell
  hat Unfug produziert". Zweite Instanz derselben Fallenklasse wie in Teil 1.

**Warum meine Regression R3 das nicht gefangen hat:** sie prüft, dass ein übergebener Vorschlag
**nicht überschrieben** wird — nie, welche **Form** er hat. Der Vertrag war richtig formuliert
und unvollständig gedacht.

## Vorschlag — NICHT umgesetzt, wartet auf Entscheidung

Die Reparatur gehört **in die gemeinsame Runtime**, nicht in den Graph-Knoten, sonst wäre sie
selbst wieder eine C-Sonderbehandlung: `run_technical_check()` normalisiert den Eingang, indem
es eine innere `correction_proposal` mit den vier Feldern zur Hülle ergänzt, bevor es prüft —
dieselbe Quelle wie auf Platte, gleiches Schema für alle Arme. Danach zwingend: **R3 um eine
Formprüfung erweitern**, P04 in A/B/C erneut, und die Erwartung `retries=0` als Regression
festschreiben.

- **Verifikation:** P01/P03 an den archivierten Artefakten nachgerechnet (Codeformel gegen
  `similar_items`, Treffer exakt); Retry-Kette statisch an vier Fundstellen belegt und
  empirisch über den A/C-Vergleich desselben Falls; Traces ausschliesslich über `TraceLeser`.
- **Was NICHT funktioniert hat:**
  * **„Ursache K5" in BA-035 war falsch** — und ich hatte in BA-045 noch die Kartenauswahl als
    wahrscheinliche Spur benannt. Beides daneben: die Zahl kommt aus **deterministischem
    Python in Knoten 3**. Ohne die vorgegebene Reihenfolge (K2 → K3 → Werte → Mathematik → K4
    → K5) hätte ich das nicht gefunden, sondern an Knoten 5 herumdiagnostiziert.
  * **Zwei Messpunkte in Folge zeigen auf das Instrument statt auf das System.** Kategorie 1
    bei Dichtefehlern und Kategorie 2 bei jedem Graph-Durchgang. Das ist kein Zufall mehr,
    sondern ein Muster: **vor G5 muss jede der vier Kategorien einmal gegen einen echten
    Trace geprüft werden**, ob sie misst, was sie zu messen behauptet.
  * **Mein Nebenbefund aus BA-045 war zu harmlos formuliert.** Ich hatte `retries=1` als
    Modellverhalten notiert („liefert im ersten Anlauf einen schemaungültigen Vorschlag").
    Tatsächlich war es die eigene Verdrahtung. **Aus dem Endzustand geschlossen statt die
    Fehlermeldung gelesen** — dieselbe Denkfigur wie in BA-036.
- **Offen / nächstes:** (1) **Entscheidung zur Runtime-Normalisierung** — bis dahin **kein
  G5**; (2) danach P04 in A/B/C erneut mit erwarteten `retries=0`; (3) **weiterhin offen aus G3b:** P06/P07/P09-Ersatzfälle mit neuen Kennungen, G2 erneut,
  P05-Zusatzfall.

---

### [BA-047] 2026-08-21 — Hülle statt innerem Vorschlag an Knoten 6 · vier Kategorien als prüfbare Instrumente
- **Status:** partial — Code umgesetzt und offline vollständig regressiert; **die A/B/C-Bestätigung
  am laufenden System steht aus** (Testinstanz nicht erreichbar). **G5 bleibt blockiert.**
- **Kapitelbezug:** K4 *(Zustandsführung)*, K6 *(Messinstrumente, Kategorien)*, K7, K8
- **Literatur:** **L11** *(Turpin et al. — Beobachtung schlägt Selbstauskunft; hier als
  Konstruktionsprinzip der Klassifikatoren: sie lesen ausschliesslich CODE-Aufzeichnungen)*,
  **L12** *(Jacovi & Goldberg — faithfulness ist graduell; deshalb drei Ausgänge je Kategorie
  statt zwei)*
- **Changed files:** `graph/graph_state.py`, `graph/nodes/{correction,technical_check}.py`,
  `graph/trace_keys.py`, `app/eval/{graph_regression_harness,test_graph_handoff_regressions}.py`;
  **neu** `app/eval/kategorien.py`, `app/eval/test_kategorien_instrumente.py`.
  **Kein Runtime-Code, kein Prompt, keine Regelkarte geändert.**
- **Status der Läufe:** offline, kein Messwert. Keiner der 17 Messfälle berührt.
  `generate_audit_report()` nicht aufgerufen.

## TEIL 1 — Der Fix liegt an K5→K6 und braucht null Runtime-Änderung

Die Prüfung vor der Umsetzung hat die bevorzugte Variante bestätigt — sogar deutlicher als
erwartet:

* `run_correction_generation()` **erzeugt die vollständige Hülle bereits** und gibt sie
  zurück: `output_data` (`generate_correction_llm.py:1117-1131`) enthält
  `{iteration, snapshot_id, original_error, error_analyzed, correction_proposal}`.
* **Es ist bitgleich dasselbe Objekt**, das `save_correction_proposal()` nach
  `iteration-N/llm_correction_proposal.json` schreibt (`:1104`, Argument `proposal_data`).
* Der Graph hat es schlicht ignoriert und nur `"proposal"` — den inneren Vorschlag — gelesen.
* **Call-Sites:** genau zwei. `graph/nodes/correction.py:109` und `main()` (`:1152`). `main()`
  liest weder `"proposal"` noch `"output_data"`, sondern nur `llm_call` für die Tokenausgabe.

> **Folge: A, B und der CLI-Pfad werden von diesem Fix mechanisch nicht berührt.** Es musste
> in Knoten 6 nichts nachgebaut werden — die echte Hülle wird verlustfrei durchgereicht.

**Die Änderungen, minimal:**

1. **`GraphState.correction_response`** — die vollständige Hülle, strikt getrennt von
   `correction_proposal` (innerer Vorschlag). 22 Felder; die Zahl ist kein Akzeptanzkriterium.
2. **Knoten 5** legt `ergebnis["output_data"]` dort ab und protokolliert
   `provenienz.response_sha256`.
3. **Knoten 6** prüft die **Hülle** statt des inneren Vorschlags und protokolliert
   `input_digest.response_sha256_eingang`. Fehlt die Hülle bei vorhandenem Vorschlag, ist das
   ein **Fehlerzustand** — kein Disk- und kein Neubau-Fallback (dieselbe Linie wie BA-044).
4. **Nach der Prüfung** ist die finale Hülle autoritativ: sie ersetzt
   `correction_response`, ihr innerer Vorschlag ersetzt `correction_proposal` und geht an
   Knoten 7. Zusätzlich `provenienz.response_sha256_final`.
5. **Knoten 7 unverändert.** Er bekommt weiterhin den inneren Vorschlag, lädt die Platten-Hülle
   und vergleicht — der State/Disk-Guard und R1 bleiben unangetastet.

**Die harte Invariante, im Trace nachrechenbar:**

```
correction.provenienz.response_sha256  ==  technical_check.input_digest.response_sha256_eingang
```

Beide über dieselbe kanonische Serialisierung wie `_proposal_sha256`
(`validate_correction_schema_llm.py:251-256`). In R9a als Gleichheit geprüft, nicht behauptet.

## Was der Defekt zusätzlich angerichtet hat — nachgetragen

BA-046 nannte den überflüssigen LLM-Aufruf. Am Artefakt zeigt sich mehr: `retry_0.json` (das,
was Knoten 6 hineingab) trägt die Keys `action, additional_updates, …` — der **innere**
Vorschlag, wie behauptet. Und der geglückte Retry **überschrieb**
`llm_correction_proposal.json` mit einer Hülle, deren Pflichtfelder das **Modell geraten**
hatte: in `da0cae38…/iteration-2/` steht seither `iteration: 1`. **Der Defekt hat die Rohdaten
beschädigt** — Regel 7 betroffen, nicht nur der Tokenverbrauch.

## Die zwei Regressionen — ausdrücklich als Paar

| | Gegenstand | Ergebnis |
|---|---|---|
| **R9a** | kontrolliert **schemavalide** Hülle → kein handoff-bedingter Retry; Invariante per SHA-256 | **PASS 7/7** |
| **R9b** | kontrolliert **schema-invalide** Hülle → Retry löst aus, finale Hülle autoritativ, K7 bekommt sie | **PASS 10/10** |

> **`retries=0` ist ausdrücklich KEINE Systeminvariante.** In echten Pilotläufen sind
> Schema-Retries legitim — das ist Kategorie 2. R9a prüft nur, dass ein Retry **nicht mehr
> durch den Graph-Handoff** entsteht. R9b ist der Gegenpol: ohne ihn liesse sich `retries=0`
> auch dadurch erreichen, dass gar nichts mehr geprüft wird. R9b belegt zusätzlich, dass die
> Fehlermeldung nach dem Fix **keine Hüllenfelder** mehr nennt.

**Gesamtstand:** R1 10/10 · R2 22/22 · R3 12/12 · R4 5/5 · R5 7/7 · R6 15/15 · R9a 7/7 ·
R9b 10/10 · Replay 12/12 · R7a 10/10.

## TEIL 2 — AP-G3b.4: die vier Kategorien sind jetzt Code, nicht Prosa

`app/eval/kategorien.py` — je Kategorie **drei** Ausgänge statt zwei: `ja` · `nein` ·
`nicht_bestimmbar`. Der dritte ist ein **Ergebnis**, kein Ausweichen; ihn als „nein" zu zählen
wäre dasselbe falsche Grün wie in BA-021 und BA-044.

| | Ground Truth | autoritative Quelle | **Confounder, der NICHT zählt** |
|---|---|---|---|
| **K1** fachlich | `expected-results.json` (`after`) | `llm_correction_call.json → response.content`; Evidenz aus `last_search_results.json → array_context` | Wert **durch die vorgelegte Evidenz gestützt** (P01/P03: der Median 1.049 stand im Kontext) · `value_source != "llm"` |
| **K2** strukturell | Pydantic `LLMCorrectionResponse` | `technical_check.errors` **plus** `retries` | **Hüllen-Signatur**: ≥4 der 5 Hüllenfelder fehlen gleichzeitig und keine verschachtelte Position → Handoff, kein Modellfehler |
| **K3** Regel | `matched_rules.cards_loaded` + übergebener `rule_text` | Knoten 4 gegen die Behauptung in Knoten 5 | Begründung **ohne Regelbezug** · geladene, aber **unpassende** Karte (`negative-dichtewerte.md` bei Wert 0) |
| **K4** Folgefehler | Differenz der Fehleridentitäten vor/nach | `applied` + `errors_after` **nach abgeschlossener Re-Validierung** | Apply/Upload/Revalidierung nicht positiv belegt → `nicht_bestimmbar`, **nie** „nein" · ein *verbliebener* Fehler ist kein Folgefehler |

**Geprüft gegen reale Traces, nicht nur konstruierte:** K1-Confounder an P01 (`c13a6303…`) und
P03 (`d0083bed…`); K2-Confounder am realen Hüllen-Mismatch (`da0cae38…`); K3 an den echten
geladenen Karten von P01; K4 an allen drei Durchgängen von `7a9a981d…` — Positivfall
(D2, `errors_new=1`), Negativfall (D1) und Confounder (D3, Apply gescheitert →
`nicht_bestimmbar`).

**Ergebnis: K1 8/8 · K2 5/5 · K3 7/7 · K4 7/7.**

- **Verifikation:** alles in der Wurzel-`.venv`, `require_ba_env()` bricht sonst hart ab.
  Traces ausschliesslich über `TraceLeser`. Die Kategorien-Confounder gegen **archivierte
  Realläufe**, nicht gegen Nachbauten.
- **Was NICHT funktioniert hat:**
  * **Mein `voll_huelle()` im Testgerüst war seit BA-044 nie eine gültige Hülle.**
    `original_error` und `error_analyzed` waren Strings, das Modell verlangt Objekte
    (`correction_models.py:51-62`). Aufgefallen ist es erst, als R9a/R9b die **echte**
    Pydantic-Prüfung benutzten — R1, R5 und R6 hatten den Prüfer gestubbt und konnten es nicht
    merken. **Eine Attrappe, die alles akzeptiert, prüft nichts.**
  * **Der K2-Klassifikator stufte den realen Handoff-Defekt zunächst als Modellfehler ein** —
    also genau der Fehler, den er verhindern soll. Zwei Ursachen nacheinander: (a) ich suchte
    im Fliesstext nach Feldnamen, und Pydantic **echot den Eingabewert** in die Meldung
    (`input_value={'action': …}`); (b) meine Liste der Hüllenfelder hatte **vier** statt
    **fünf** Einträge — `correction_proposal` fehlt bei einem inneren Vorschlag ebenfalls.
    Behoben durch Auswertung der **Fehlerpositionen** und eine Signaturschwelle.
    **Ohne den Realfall im Test wäre beides durchgegangen.**
  * **Die A/B/C-Bestätigung am laufenden System konnte nicht stattfinden.** Die
    Smart-Planning-Testinstanz war um 16:52 erreichbar (Auth OK, drei Läufe erfolgreich) und
    um 17:10 nicht mehr: DNS löst weiterhin auf `10.112.19.8`, TCP läuft in den
    `ConnectTimeout`. **Kein Zusammenhang mit den Änderungen** — der letzte erfolgreiche Lauf
    lag nach dem Fix an Knoten 5. Rohartefakt des Fehlversuchs:
    `data/archive/ba-g3-pilot/pilot-firstpass-C-20260820T171013Z.json`.
  * **`test_trace_registry` steht auf FAIL**, und das ist **richtig**: der jüngste vorhandene
    Trace stammt von vor dieser Änderung und führt `response_sha256_eingang` noch nicht. Es
    löst sich mit dem ersten Lauf nach dem Fix — bis dahin **nicht** als grün zählen.
- **Offen / nächstes:** (1) **A/B/C auf P04 wiederholen, sobald die Testinstanz wieder
  erreichbar ist** — erwartet: kein Retry mit Hüllenfeld-Ursache in C, und der **Grund** eines
  etwaigen Retries wird verglichen, nicht nur die Anzahl; (2) `test_trace_registry` gegen den
  frischen Trace; (3) danach erst **G3b.3** (P06/P07/P09-Ersatzfälle mit neuen Kennungen,
  G2 erneut, P05-Zusatzfall); (4) **G5 bleibt blockiert**, bis (1) und (2) grün sind.

---

### [BA-048] 2026-08-21 — Hüllen-Fix real bestätigt (C: 4 → 0 Retries) · zwei Pilotpfade als nicht konstruierbar belegt
- **Status:** partial — der K5→K6-Fix ist **real geschlossen**; G3b.3 teilweise: P11 gebaut und gefahren, Pfad verfehlt. **G5 weiterhin blockiert.**
- **Kapitelbezug:** K4, K6 *(Messinstrumente, Kategorien, Grenzen der Fehlerinjektion)*, K7, K8
- **Literatur:** **L11**, **L12** *(graduelle faithfulness — Grundlage für die drei Ausgänge je Kategorie)*
- **Changed files:** `app/eval/{kategorien,test_kategorien_instrumente,test_trace_registry,
  test_graph_handoff_regressions,build_pilot_catalog}.py`; **neu**
  `app/eval/report_retry_ursachen.py`, `app/eval/test_kontextsuche_pfade.py`,
  `data/archive/ba-g3-pilot/WARNUNG-BESCHAEDIGTE-ARTEFAKTE.md`.
  **Kein Produktcode, kein Prompt, keine Regelkarte in diesem Eintrag geändert.**
- **Lauf-Metadaten:** Bedingungen **A**, **B**, **C** · `MEMORY_MODE=off` ·
  `HUMAN_IN_THE_LOOP=false` · `gpt-4.1`, API `2025-01-01-preview`, `temperature=0.3` ·
  Fall **P04** je frischer Snapshot: A `9e7fd473…`, B `d9a23f6f…`, C `b51c5b1c…` ·
  `require_ba_env()` bestanden · **Rohdaten:**
  `data/archive/ba-g3-pilot/pilot-firstpass-{A-20260820T184854Z,B-20260820T184954Z,
  C-20260820T184744Z}.json`
- **Status der Läufe:** `pilot` — **kein Messergebnis.** Keiner der 17 Messfälle berührt.
  `generate_audit_report()` nicht aufgerufen.

## TEIL 1 — Der A/B/C-Vergleich schliesst den Fix

| Arm | Snapshot | Durchgänge | **Retry-Artefakte** | Ergebnis |
|---|---|---|---|---|
| **A** monolith/monolith | `9e7fd473…` | 2 | **0** | 0 Fehler |
| **B** monolith/cards | `d9a23f6f…` | 2 | **0** | 0 Fehler |
| **C** graph/cards | `b51c5b1c…` | 2 | **0** *(vorher 4)* | 0 Fehler, `stop_valid`, Rückkante |

**Die harte Erwartung ist erfüllt:** in C entsteht kein Retry mehr aus fehlenden Hüllenfeldern.
Vor dem Fix beanstandete die Meldung `['correction_proposal', 'error_analyzed', 'iteration',
'original_error', 'snapshot_id']` — alle fünf auf einmal; jetzt gibt es keine Meldung, weil es
keinen Retry gibt.

**Die SHA-Invariante hält am realen Trace**, beide Durchgänge:

| D | `correction.provenienz.response_sha256` | `technical_check.input_digest.response_sha256_eingang` | |
|---|---|---|---|
| 1 | `0fe7045394532136…` | `0fe7045394532136…` | **identisch** |
| 2 | `566f69a3edcf28bc…` | `566f69a3edcf28bc…` | **identisch** |

**Die Artefakte sind unbeschädigt.** `b51c5b1c…/iteration-1` trägt `iteration: 1`,
`iteration-2` trägt `iteration: 2` — vorher stand dort `1`, vom Modell geraten. Keine
`*_retry_*.json` mehr vorhanden. Die Rohdaten sind wieder Rohdaten im Sinne der Regel 7.

**`test_trace_registry` gegen genau diesen Trace: PASS** (`b51c5b1c/iteration-2`, Exit 0).

Ausgewertet mit dem neuen `app/eval/report_retry_ursachen.py`, das je Arm und Durchgang
**Retry-Anzahl, beanstandete Felder, Ursachenklasse und SHA-Invariante** ausweist — nicht nur
die Zahl. Genau die Verkürzung auf die Zahl hätte in BA-046 fast zur falschen Diagnose geführt.

## Registry: PENDING ist jetzt ein eigener Zustand

`test_trace_registry` kennt drei Ausgänge mit eigenen Exit-Codes: **0 PASS**, **1 FAIL**
(Produktregression), **2 PENDING** (der jüngste Trace ist älter als `trace_keys.py` — es gibt
noch keinen Trace, gegen den sich prüfen liesse). Ein FAIL verlangt, den Code zu untersuchen;
ein PENDING verlangt einen Lauf. Sie zu vermischen hiesse, eine fehlende Beobachtung als
Befund auszugeben — derselbe Fehler, den BA-044 im K8-Vertrag beseitigt hat.

## Beschädigte Artefakte gekennzeichnet

`data/archive/ba-g3-pilot/WARNUNG-BESCHAEDIGTE-ARTEFAKTE.md`: `da0cae38…` (P04) und
`82dc8e37…` (P10) sind **Debugging-Artefakte, keine Evaluationsbelege**. Erkennungsmerkmal,
erlaubte Restverwendung (Trace/Kontrollfluss, Server- und Runtime-Werte) und ausdrückliches
Verbot (Vorschlagsinhalt, `iteration`/`snapshot_id`, Token-/Laufzeitvergleiche, Kategorie 1
und 2) sind dort festgehalten. Die Läufe **vor** BA-043 und **alle** A/B-Läufe sind unversehrt.

## TEIL 2 — Die Kategorien: Provenienz schlägt Signatur

* **K2** entscheidet jetzt über **Provenienz**: `k5_response_valide=True` + Retry → Handoff
  (NEIN); `False` → Modellfehler (JA), **unabhängig davon, welche Felder beanstandet sind**.
  Die „≥4/5 Hüllenfelder"-Signatur ist ausdrücklich auf **Diagnose des historischen
  BA-046-Defekts** zurückgestuft und beschriftet ihr eigenes Ergebnis mit
  `SIGNATUR (… DIAGNOSTISCH, nicht beweisend)`. Testfall dafür: alle fünf Felder fehlen, aber
  `k5_response_valide=False` → **JA** — genau der Fall, den die Signatur allein falsch
  klassifiziert hätte.
* **K3** ist umformuliert auf *„durch die geladenen Regelkarten nicht gestützt"* statt
  *„Karte nicht geladen"*. Neuer Testfall: die Regel steht inhaltlich im übergebenen
  `rule_text`, ihre Karte ist nicht benannt → **NEIN**.
* **K1** (Ground-Truth-Abweichung ≠ Halluzination bei Evidenzstützung) und
  **`nicht_bestimmbar`** unverändert.

Stand: **K1 8/8 · K2 9/9 · K3 8/8 · K4 7/7**.

**Bestätigt und ab jetzt in jedem Lauf geprüft:** R9a/R9b benutzen den **echten**
Schema-Prüfpfad. Sechs `ECHTHEIT`-Assertions belegen je Lauf, dass
`validate_correction_proposal`, `validate_with_retry` und `run_technical_check` die realen
Funktionen sind und gegen das echte `LLMCorrectionResponse` prüfen; gestubbt sind nur der
LLM-Reparaturaufruf und der Plattenzugriff. R9a 13/13, R9b 16/16.

## TEIL 3 — Zwei Pilotpfade sind per Fehlerinjektion NICHT konstruierbar

Bei der Konstruktion der Ersatzfälle kam ein struktureller Befund heraus — am echten Code und
an den echten Daten geprüft, nicht angenommen:

> **Eine Fehlerinjektion schreibt den fehlerhaften Wert IN den Snapshot.** Knoten 2 liest ihn
> aus der Fehlermeldung und sucht danach. Die exakte Suche findet deshalb **immer mindestens
> den manipulierten Datensatz selbst**.

Belegt: `search_in_dict(manipuliert, "PLAN_GIBTESNICHT")` → **1 Treffer**;
`search_in_dict(original, "KOMMT_NIRGENDS_VOR_XYZ")` → **0 Treffer**.

Daraus folgt:

* **P06 „Kontextsuche ohne Treffer" — nicht konstruierbar.** Null Treffer sind per Injektion
  nicht herstellbar.
* **P07 „Fuzzy-/Fallback-Suche" — nicht deterministisch konstruierbar.** Der Fuzzy-Pfad in
  `search_by_id()` greift ausschliesslich bei null exakten Treffern. Die **Fähigkeit
  existiert** und ist direkt nachgewiesen (`"D106097_00X"` → 5 Treffer, alle
  `fuzzy_match=True`, ähnlichste sind die real existierenden IDs) — erreichbar aber nur mit
  einem Suchwert ausserhalb des Dokuments, und den wählt Knoten 2, nicht der Katalog.
* **Auch ein dritter Kandidat scheidet aus:** „Artikel ohne Vergleichskollektiv". Der
  Datensatz kennt genau **zwei** `(departmentId, workPlanId)`-Kollektive, mit **91** und
  **331** Artikeln. Es gibt keinen Artikel ohne Vergleichsgruppe.

**Konsequenz:** Beide Pfade werden auf **Knotenebene** abgedeckt
(`app/eval/test_kontextsuche_pfade.py`, **10/10**), nicht als Pilotfall. Das ist eine **Grenze
der Fehlerinjektion als Ground-Truth-Methode** (Brücke 1) und gehört als solche in die
Limitationen — kein Systemmangel.

## P11 — der eine Ersatzfall, der wirklich funktioniert

`P11`, Artikel **830285** (neue Kennung; P06/P07/P09 bleiben archiviert und behalten ihre IDs,
damit der First Pass zitierbar bleibt). Manipulation:
`m_ununterscheidbares_duplikat` — zwei Demands desselben Artikels, die sich **in keinem Feld
ausser der `demandId` unterscheiden** (an den Daten geprüft: `D830285_002` und `D830285_003`
sind identisch). Nach der Duplikat-Injektion ist **objektiv nicht entscheidbar**, welche die
falsche ist.

Anders als beim verworfenen P09 entsteht nachweislich ein `validate_unique_ids`-Fehler —
insofern ist P11 die bessere Konstruktion. **Den vorgesehenen Pfad trifft es trotzdem nicht.**

### P11 real gefahren (`7f447c4e…`, Bedingung C) — Pfad VERFEHLT, Korrektur richtig

| | |
|---|---|
| Fehler vorher | 1 (`validate_unique_ids`) ✔ — anders als P09 |
| Kontext | `value/D830285_002`, 2 Treffer |
| Karten | `_core.md`, `references.md`, `unique-ids.md` |
| Entscheidung | **`stop_valid`** — erwartet war `stop_uncertain` ✘ |
| Vorschlag | `D830285_003` = **exakt die Ground Truth** |

Die Begründung des Modells erklärt, warum meine Annahme falsch war:

> *„Das ID-Muster für demands mit articleId '830285' ist eindeutig: D830285_001, D830285_002,
> D830285_004, D830285_005, D830285_006. Die Sequenznummer '003' fehlt im Array und ist die
> einzige Lücke."*

**Ich hatte nur die Feldinhalte auf Identität geprüft, nicht die ID-Sequenz.** Die beiden
Datensätze sind inhaltlich ununterscheidbar — aber die **Lücke in der Nummernfolge** macht
eindeutig, welche ID fehlt. Es gab nie eine Mehrdeutigkeit; ich hatte nur einen Teil der
Information angesehen, die dem Modell vorliegt.

**Was P11 trotzdem wert ist:** ein sauberer **Positivfall für Kategorie 1** — Vorschlag trifft
die Ground Truth exakt, mit einer nachvollziehbaren, an den Daten überprüfbaren Begründung.
Der Fall bleibt im Katalog, aber unter dem zutreffenden Pfadetikett.

### Der Grenzfall-Pfad ist beobachtet, nicht konstruiert

`stop_uncertain` als *richtige* Antwort ist real aufgetreten — in **P10, Durchgang 5**: das
Modell lieferte `action: manual_intervention_required` mit leerem `target_path` und der
Begründung, `relDensityMin` komme im Snapshot nirgends vor (BA-045). Das ist der ehrliche
Nein-Pfad aus Kap. 15.3, **unbeabsichtigt und echt**. Als Beleg zulässig: es geht um
Kontrollfluss und die Entscheidung von Knoten 8, was die Artefakt-Warnung für `82dc8e37…`
ausdrücklich erlaubt.

**Damit gilt für den Grenzfall dasselbe wie für P06 und P07: die Fähigkeit ist belegt, der
gezielte Testfall ist es nicht.** Ob dafür weiter Aufwand investiert wird, ist eine offene
Entscheidung — nach drei verfehlten Reissbrett-Entwürfen in Folge würde ich einen vierten
Versuch nicht ohne neue Idee starten.

**G2 erneut gefahren: überschneidungsfrei**, Exit 0. 11 Pilotfälle, keine gemeinsamen
Entitäten mit dem Messkatalog; `830285` ist neu und kollidiert mit keinem anderen Pilotfall.
Rohartefakt: `data/archive/ba-g2-ueberschneidung/ueberschneidungsnachweis.json`.

- **Verifikation:** alle Läufe in der Wurzel-`.venv` (`require_ba_env()`). Traces
  ausschliesslich über `TraceLeser`. Die Unmöglichkeitsbefunde durch **direkten Aufruf der
  echten Suchfunktionen**, nicht durch Argumentation.
- **Was NICHT funktioniert hat:**
  * **Der Bash-Heredoc hat `\n` in einem Patch-Skript zu echten Zeilenumbrüchen aufgelöst**
    und die Testdatei mit einem `SyntaxError` zerschossen. Repariert; für Patches mit
    Escape-Sequenzen ab jetzt ausschliesslich die Datei-Route, nicht der Heredoc.
  * **Ein Suchtext war um ein Zeichen daneben** (`Verdrahtungsdefekts` statt
    `Verdrahtungsdefekt`) und liess einen Patch scheitern. Harmlos, weil die Assertion vor dem
    Schreiben steht — genau dafür ist sie da.
  * **Mein erster Ersatzentwurf für P06 war wieder am Reissbrett gedacht** („Artikel ohne
    Vergleichskollektiv"). Erst die Prüfung an den Daten zeigte, dass es im gesamten Datensatz
    nur zwei Kollektive gibt. **Zweimal derselbe Fehler in derselben Sache** — deshalb wurde
    diesmal jede Annahme vor dem Bau am echten Code und an den echten Daten geprüft.
  * **P11 hat seinen Pfad ebenfalls verfehlt** — der dritte Reissbrett-Entwurf in Folge. Ich
    hatte die Feldinhalte auf Identität geprüft und die **ID-Sequenz übersehen**, aus der das
    Modell die Lücke ableitet. Immerhin erzeugt P11 anders als P09 einen echten Fehler und
    liefert eine korrekte Korrektur; als Grenzfall taugt es nicht.
  * **Zwei von drei Ersatzfällen liessen sich nicht bauen, der dritte traf daneben.** Das ist kein Rückschlag, sondern
    das eigentliche Ergebnis dieses Abschnitts: die Ground-Truth-Methode hat eine benennbare
    Reichweitengrenze.
- **Offen / nächstes:** (1) **Entscheidung zum Grenzfall-Pfad** — beobachtet (P10 D5), aber
  nicht gezielt konstruierbar; ein vierter Entwurfsversuch braucht eine neue Idee, nicht mehr
  Fleiss; (2) **P05-Zusatzfall** — Kategorie 4 ist durch P04 bereits real belegt (BA-036), der
  Zusatzfall dient nur der Reproduzierbarkeit und darf das Testdesign nicht verbiegen;
  (3) **G4** (Änderungsprotokoll), **G5a** (Lock-Artefakt), dann **G5**.
  **G5 bleibt blockiert**, bis P11 und der P05-Zusatzfall entschieden sind.

---

### [BA-049] 2026-08-21 — AP-G3 ABGESCHLOSSEN · Nulltreffer/Fuzzy im aktuellen Workflow nicht erreichbar · Kategorien fachlich festgelegt
- **Status:** done — **AP-G3 geschlossen.** Weiter mit G4. **G5 weiterhin blockiert** (G4, G5a stehen aus)
- **Kapitelbezug:** K3 *(Befund über das Bestandssystem)*, K5, K6 *(Messinstrumente)*, K7, K8 *(Limitationen)*
- **Literatur:** **L11**, **L12**
- **Changed files:** `app/eval/test_kontextsuche_pfade.py`; **neu**
  `app/eval/test_kategorie4_integration.py`.
  **Kein Produktcode, kein Prompt, keine Regelkarte geändert. Kein LLM-Lauf in diesem Eintrag.**
- **Status der Läufe:** rein statisch bzw. offline. Keiner der 17 Messfälle berührt.
  `generate_audit_report()` nicht aufgerufen.

## 1 — Nulltreffer und Fuzzy: im aktuellen Workflow nicht erreichbar

Die Frage war schärfer gestellt als bisher beantwortet: *Kann Knoten 2 im realen
Korrekturworkflow überhaupt einen Suchwert erzeugen, der nicht schon im Snapshot vorkommt?*

**Antwort: nein — auf keinem regulären Weg.** Der Suchwert entsteht nicht frei; das Modell
**extrahiert** ihn aus der Validatormeldung (`identify_error_llm.py:202-210`, Prompt-Schritt 5:
*„Extract the appropriate search_value"*). Eine Validatormeldung beanstandet aber einen Wert,
der **im Snapshot steht** — sonst gäbe es den Fehler nicht.

| Suchmodus | Suchwert | Nulltreffer möglich? |
|---|---|---|
| `value` | der beanstandete Wert aus der Fehlermeldung | **nein** — er steht im Snapshot |
| `empty_field` | ein **Feldname**, über `normalize_field_name()` (`:320`) | **nein** — das leere Feld existiert |
| `equipment_workitem` | der „fehlende" Schlüssel | **nein** — laut Code-Kommentar *„occurs in hundreds of valid places"* |

Der Fuzzy-Zweig sitzt in `search_by_id()` und greift **ausschliesslich bei null exakten
Treffern**; im `empty_field`-Pfad ist er gar nicht verdrahtet (dort läuft `search_empty_field()`).

> **Das ist ausdrücklich KEIN Problem der Pilotfallkonstruktion.**
>
> **Genaue Formulierung — sie trägt die Einschränkung mit:** Der Nulltreffer- und der
> Fuzzy-Pfad sind **unter dem derzeitigen regulären E2E-Korrekturworkflow, mit der aktuellen
> Validatormenge und der aktuellen Ableitung des `search_value`, nicht erreichbar**. Auf
> **Knotenebene sind sie implementiert und getestet**.
>
> **Was damit ausdrücklich offen bleibt:** Andere oder künftige Aufrufer von
> `search_by_id()`, eine geänderte Validatormenge, eine andere Ableitung des Suchwerts —
> oder eine **Fehlklassifikation durch Knoten 2** — können diese Pfade grundsätzlich sehr
> wohl erreichen. Die Aussage gilt für den *heutigen regulären* Ablauf, nicht für den Code
> an sich. **„Toter Code" wäre deshalb zu pauschal und wird nicht behauptet.**

**Direkt nachgewiesen** (`test_kontextsuche_pfade.py`, **15/15**): `search_by_id(daten,
"D106097_00X")` → 5 Treffer, alle `fuzzy_match=True`, die ähnlichsten sind die real
existierenden IDs; bei einem exakten Treffer wird **nicht** gefuzzt.

Die einzige beobachtete Nulltreffer-Situation ist eine **Fehlklassifikation**: in P10 D5 wählte
Knoten 2 `empty_field` für `relDensityMin`, das den Wert `0` trug (nicht leer) → 0 Treffer. Kein
*ansteuerbarer* Prozesspfad — aber **der Beleg dafür, dass der Zustand real vorkommen kann**.
Genau deshalb bleibt die Aussage auf den regulären Ablauf beschränkt.

**Zwei Konsequenzen für die Arbeit, sauber getrennt:**
1. **K3 (Bestandssystem):** Der Fuzzy-Fallback ist eine Fähigkeit, die im heutigen
   Korrekturworkflow regulär nicht zum Zug kommt. Das gehört in die Beschreibung des
   Ist-Zustands — als Eigenschaft des Ablaufs, nicht als Urteil über den Code.
2. **K8 (Limitationen):** Der Pfad darf in **keinem** Arm als Leistungsmerkmal gezählt werden
   und kann zwischen A, B und C unter den Messbedingungen keinen Unterschied erzeugen.

## 2 — Grenzfall: kein vierter Versuch

**Zwei Aussagen, die auseinandergehalten werden müssen — sie sind NICHT dasselbe:**

| | Aussage | Status |
|---|---|---|
| **(a)** | Der `stop_uncertain` / `manual_intervention_required`-**Pfad** funktioniert und wird real durchlaufen | **real belegt** (P10 D5) |
| **(b)** | Ein **gezielt konstruierter, fachlich mehrdeutiger Ground-Truth-Grenzfall** | **nicht zuverlässig herstellbar** (3 Entwürfe) |

(a) sagt nichts über (b) und umgekehrt. Wer beides gleichsetzt, behauptet entweder einen
Testfall, den es nicht gibt, oder eine Fähigkeitslücke, die es nicht gibt.

**Zu (a) — der Unsicherheitspfad ist real beobachtet** — P10, Durchgang 5: `action:
manual_intervention_required`, leerer `target_path`, Begründung *„keine Instanz von
relDensityMin gefunden"* → Knoten 8 entschied über Stufe 1c auf `stop_uncertain` (BA-045). Als
Beleg zulässig, weil es um Kontrollfluss und die Entscheidung von Knoten 8 geht — was die
Artefakt-Warnung für `82dc8e37…` ausdrücklich erlaubt. Zusätzlich ist der Pfad in R2 und im
K8-Vertrag mehrfach regressionsgesichert.

**Zu (b) — ein gezielt konstruierter, fachlich mehrdeutiger Ground-Truth-Fall liess sich in
drei Entwürfen nicht erzeugen:**

| Entwurf | Idee | Warum gescheitert |
|---|---|---|
| **P09** | `relDensityMin`/`Max` vertauschen | Der Server beanstandet das gar nicht — es gibt keine Regel „min ≤ max". **0 Fehler, kein Lauf.** |
| *(Zwischenidee)* | Artikel ohne Vergleichskollektiv | Der Datensatz kennt genau **zwei** Kollektive (91 und 331 Artikel). Existiert nicht. |
| **P11** | zwei inhaltlich identische Demands, eine ID dupliziert | Die **Lücke in der ID-Sequenz** macht eindeutig, welche ID fehlt. Das Modell schloss korrekt auf `D830285_003` — die Ground Truth. Keine Mehrdeutigkeit. |

**Kein vierter Versuch.** Drei Entwürfe haben denselben Fehler in drei Varianten wiederholt:
Ich habe jeweils *einen Teil* der Information geprüft, die dem Modell vorliegt, und die
übrigen übersehen — die Validatorregeln (P09), die Kollektivgrössen (Zwischenidee), die
ID-Sequenz (P11). Mehr Fleiss hilft dagegen nicht.

## 3 — Kategorie 4: kein Post-Fix-Positivfall, deshalb Integrationsnachweis

**Alle Post-Fix-Pilottraces geprüft** — `b51c5b1c…` (2 Durchgänge) und `7f447c4e…`
(1 Durchgang):

| Snapshot | D | applied | uploaded | reval | vor | nach | behoben | **neu** | Typen |
|---|---|---|---|---|---|---|---|---|---|
| `b51c5b1c` | 1 | True | True | True | 2 | 1 | 1 | **0** | `[]` |
| `b51c5b1c` | 2 | True | True | True | 1 | 0 | 1 | **0** | `[]` |
| `7f447c4e` | 1 | True | True | True | 1 | 0 | 1 | **0** | `[]` |

**Kein Post-Fix-Positivfall.**

> **Der Pre-Fix-Lauf `7a9a981d…` D2 (BA-036) wird NICHT als regulärer positiver Nachweis
> geführt.** Seine Artefakte waren vom damaligen K5→K6-Handoffdefekt betroffen
> (`WARNUNG-BESCHAEDIGTE-ARTEFAKTE.md`); er bleibt ein **Debugging-Befund**. Dass dort ein
> Folgefehler beobachtet wurde, zeigt, dass das Phänomen auftritt — es ist aber **kein
> Messbeleg** unter den geltenden Bedingungen.
>
> **Der gültige Stand ist deshalb:** Das **Kategorie-4-Messinstrument ist post-fix validiert**,
> und zwar durch den Integrationsnachweis unten (**19/19**). Ein realer Positivfall unter
> Post-Fix-Bedingungen **steht noch aus** und wird sich in AP-H ergeben oder nicht.

Statt neue LLM-Pilotfälle zu würfeln, bis zufällig ein Folgefehler eintritt, wurde die
**Messkette selbst** nachgewiesen: `app/eval/test_kategorie4_integration.py`, **19/19**. Echter
Knoten 7, kontrollierte Serverantworten, gestubbt sind nur die Aussenkanten.

| Fall | vorher → nachher | `errors_after` | behoben | neu | **Kategorie 4** |
|---|---|---|---|---|---|
| 1 | A → ∅ | 0 | 1 | 0 | **nein** |
| 2 | A → B | **1 (unverändert!)** | 1 | **1** | **JA** |
| 3 | A → A | 1 | 0 | 0 | **nein** *(wirkungslos ≠ Folgefehler)* |
| 4 | A → B, C | 2 | 1 | **2** | **JA** |
| 5 | Verarbeitung unvollständig | — | — | — | **nicht_bestimmbar** |

**Fall 2 ist der eigentliche Nachweis:** die Fehlerzahl bleibt `1 → 1`. Nur über die stabilen
Fehleridentitäten ist erkennbar, dass ein Fehler behoben **und** ein neuer erzeugt wurde. Eine
Messung über die blosse Fehlerzahl hätte hier „nichts passiert" gemeldet.

## 4 — Die Kategorien sind fachlich festgelegt (noch KEIN formaler Freeze)

Die validierte Trennung gilt ab hier unverändert:

* **fachlich korrekt / falsch** — gegen die Ground Truth
* **evidenzgestützt / ungestützt** — ein Ground-Truth-falscher Wert, der aus der **vorgelegten
  Evidenz** stammt, ist **keine Halluzination** (P01/P03: der Median 1.049 wurde von
  `identify_snapshot.py:553-560` deterministisch berechnet und dem Modell vorgelegt)
* **`nicht_bestimmbar`** als eigener, gleichrangiger Ausgang
* **technische / Handoff-Fehler getrennt** — über die **Provenienz** (`k5_response_valide`),
  nicht über die Feldsignatur

> **Abgrenzung, ausdrücklich:** Das ist eine **fachliche Festlegung**, **kein formaler
> Freeze**. Die Definitionen dürfen ab hier nur nach **dokumentierter Revalidierung** geändert
> werden — also: Änderung begründen, die Klassifikatoren erneut gegen reale und kontrollierte
> Traces prüfen, Ergebnis protokollieren. **Der formale Gesamtfreeze erfolgt erst in G5**
> (Regelwerk, Graphstruktur, Prompts, Parameter, Umgebung, mit Hashes). Erst ab **G5** ist jede
> Änderung eine Nachmessung — nicht schon ab hier.

Stand: K1 8/8 · K2 9/9 · K3 8/8 · K4 7/7 · Integration 19/19.

## AP-G3 — ABSCHLUSSMATRIX

| # | Pilotziel | Status | Beleg |
|---|---|---|---|
| 1 | Einzelfehler | **real belegt** | P01 `c13a6303…` |
| 2 | Referenz-/ID-Fehler | **real belegt** | P02 `…`, P11 `7f447c4e…` (Vorschlag = Ground Truth) |
| 3 | fachlicher Korrekturwert | **real belegt** — und als **Evidenzbefund** umgedeutet | P03 `d0083bed…`, BA-046 |
| 4 | mehrere gleichzeitige Fehler | **real belegt** | P04 `b51c5b1c…` (post-fix, 2 Durchgänge → 0 Fehler) |
| 5 | Folgefehler (Kategorie 4) | **Messinstrument post-fix validiert**; realer Post-Fix-Positivfall **steht aus** | `test_kategorie4_integration.py` 19/19 · Pre-Fix-Beobachtung `7a9a981d…` D2 = **Debugging-Befund**, kein Messbeleg |
| 6 | Kontextsuche ohne Treffer | ✘ **im aktuellen regulären E2E-Workflow nicht erreichbar**; auf Knotenebene implementiert und getestet | `test_kontextsuche_pfade.py` 15/15 · K3/K8 |
| 7 | Fuzzy-/Fallback-Suche | ✘ **im aktuellen regulären E2E-Workflow nicht erreichbar**; auf Knotenebene implementiert und getestet | `test_kontextsuche_pfade.py` 15/15 · K3/K8 |
| 8 | Zusatzkarten | **real belegt** | P08, Kartenauswahl aus Knoten 2 (BA-046) |
| 9a | `stop_uncertain`-**Pfad** | **real belegt** | P10 D5 (BA-045) · R2 · K8-Vertrag |
| 9b | gezielt konstruierter **mehrdeutiger Grenzfall** | ✘ **nicht zuverlässig herstellbar** (3 Entwürfe) | P09 · Kollektiv-Idee · P11 |
| 10 | Rückkante 8→2 | **real belegt und fachlich validiert** | P04/P10 (BA-036), post-fix `b51c5b1c…` |
| — | Iterations-/Proposal-Handoff | **repariert und validiert** | BA-043 … BA-048, R1–R9 |
| — | Messinstrumente (4 Kategorien) | **validiert und fachlich festgelegt** *(formaler Freeze erst in G5)* | BA-047, BA-049 |
| — | Überschneidungsfreiheit (G2) | **erneut belegt** | `ueberschneidungsnachweis.json`, Exit 0, 11 Fälle |

**Legende:** *real belegt* = in einem Pilotlauf beobachtet · *Knotentest* = Fähigkeit
nachgewiesen, aber nicht im E2E-Workflow · *nicht erreichbar* = strukturelle Eigenschaft des
Workflows, kein Fallkonstruktionsproblem.

**Sieben von zehn Pilotzielen sind real belegt.** Die drei übrigen sind **nicht offen
geblieben, sondern beantwortet** — jedes mit einem anderen Ergebnis, und die Unterschiede
sind der Punkt:

* **(6) und (7)** sind im **aktuellen regulären Workflow** nicht erreichbar; die Fähigkeit
  selbst ist auf Knotenebene nachgewiesen. Befund über das Bestandssystem (K3) + Limitation (K8).
* **(9a)** ist **belegt**; nur **(9b)**, der gezielt konstruierte mehrdeutige Fall, liess sich
  nicht herstellen. Das ist eine Grenze der **Fallkonstruktion**, keine Fähigkeitslücke.
* **(5)** hat ein **validiertes Messinstrument**, aber noch keinen realen Post-Fix-Positivfall.

Alle drei gehören in K8 — mit genau dieser Unterscheidung, nicht als eine Kategorie.

- **Verifikation:** Punkt 1 statisch am Prompt und an den drei Suchmodi, ohne LLM-Aufruf;
  Punkt 3 durch Auswertung **aller** Post-Fix-Traces plus Integrationstest mit dem echten
  Knoten 7. Alles in der Wurzel-`.venv` (`require_ba_env()`).
- **Was NICHT funktioniert hat:**
  * **Mein Fixture für den Kategorie-4-Test hat den Guard aus BA-043 ausgelöst.** Ich hatte
    inneren Vorschlag und Hülle getrennt gebaut; `voll_huelle()` ergänzt Pflichtfelder, also
    wichen sie ab und Knoten 7 blockierte zu Recht. Behoben, indem der innere Vorschlag **aus
    der Hülle abgeleitet** wird. Der Guard hat sich damit ein weiteres Mal bewährt — diesmal
    gegen meinen eigenen Testaufbau.
  * **Ich hatte den P06/P07-Befund zunächst zu milde eingeordnet** — als Grenze der
    Fehlerinjektion. Die schärfere Frage zeigt: die Pfade sind **im gesamten E2E-Workflow**
    nicht erreichbar, unabhängig von der Fallkonstruktion. Das ist ein Befund über das
    **Bestandssystem**, nicht über die Pilotphase, und wäre in der Arbeit an der falschen
    Stelle gelandet.
- **Offen / nächstes:** **G4** (Änderungsprotokoll der Pilotphase), **G5a**
  (Lock-Artefakt: `pip freeze` der Wurzel-`.venv` plus `collect_run_metadata()`), dann **G5**
  (Einfrieren). **Während der gesamten Pilotphase wurde keine Regelkarte und kein Prompt
  geändert** — G4 wird das entsprechend kurz ausfallen lassen.

---

### [BA-050] 2026-08-21 — BA-049 methodisch präzisiert · AP-G4 abgeschlossen
- **Status:** done — **G4 abgeschlossen, keine neue Inkonsistenz.** Nächstes: G5a, dann G5
- **Kapitelbezug:** K3, K5, K6, K7, K8 *(Limitationen)*
- **Literatur:** —
- **Changed files:** `docs/BA_G4_PILOTPHASE_ABSCHLUSS.md` *(neu)*, `docs/BA_PROJECT_LOG.md`
  *(BA-049 präzisiert)*, `docs/BA_ARBEITSPAKETE.md`, `app/eval/test_kontextsuche_pfade.py`
  *(Formulierung)*. **Kein Produktcode, kein Prompt, keine Regelkarte. Kein LLM-Lauf.**
- **Status der Läufe:** keine Läufe. Keiner der 17 Messfälle berührt.
  `generate_audit_report()` nicht aufgerufen.

## Vier Präzisierungen an BA-049

Alle vier korrigieren **Überdehnungen meiner eigenen Formulierungen** — der Befund bleibt
jeweils, die Reichweite der Aussage schrumpft.

**1 — „toter Code" war zu pauschal.** Richtig ist: Nulltreffer- und Fuzzy-Pfad sind **unter dem
derzeitigen regulären E2E-Korrekturworkflow, mit der aktuellen Validatormenge und
Suchwertableitung, nicht erreichbar**; auf Knotenebene sind sie implementiert und getestet.
**Ausdrücklich offen bleibt**, dass andere oder künftige Aufrufer, eine geänderte
Validatormenge — oder eine **Fehlklassifikation durch Knoten 2** — sie sehr wohl erreichen
können. Der P10-D5-Fall ist genau dafür der Beleg: der Zustand *kommt vor*, er ist nur nicht
ansteuerbar. Ich hatte ihn als blossen Klassifikationsfehler abgetan, statt zu sehen, dass er
meine eigene Absolutaussage widerlegt.

**2 — Der Pre-Fix-P04-Lauf ist kein regulärer Kategorie-4-Nachweis.** `7a9a981d…` D2 stammt aus
einem Lauf, dessen Artefakte vom K5→K6-Handoffdefekt betroffen waren. Er bleibt
**Debugging-Befund**. Gültig ist ausschliesslich: das **Messinstrument** ist post-fix validiert
(19/19); ein realer Post-Fix-Positivfall **steht aus**. In der Matrix entsprechend geändert —
vorher stand dort „real belegt (pre-fix)", was die eigene Artefakt-Warnung unterlaufen hätte.

**3 — Grenzfall: zwei Aussagen, die nicht dasselbe sind.** (a) Der `stop_uncertain` /
`manual_intervention_required`-**Pfad** ist real belegt (P10 D5). (b) Ein **gezielt
konstruierter fachlich mehrdeutiger Ground-Truth-Grenzfall** liess sich nicht zuverlässig
herstellen. In der Matrix jetzt als **9a** und **9b** getrennt geführt. Wer beides gleichsetzt,
behauptet entweder einen Testfall, den es nicht gibt, oder eine Fähigkeitslücke, die es nicht
gibt. Die Zählung „7 von 10" bleibt dadurch konsistent.

**4 — Kein „Freeze" vor G5.** Die Kategorien sind **fachlich festgelegt** und dürfen nur nach
**dokumentierter Revalidierung** geändert werden. Der **formale Gesamtfreeze erfolgt in G5**;
die Nachmessungspflicht gilt **ab G5**, nicht schon ab BA-049.

## AP-G4 — konsolidierter Pilotphasen-Abschluss

Neu: **`docs/BA_G4_PILOTPHASE_ABSCHLUSS.md`**. Keine Optimierungsrunde — es wurde nichts
geändert, nur zusammengetragen und gegengeprüft.

### Die sieben Feststellungen, jede belegt statt behauptet

| # | Feststellung | Beleg |
|---|---|---|
| 1 | **0 Promptänderungen** | kein Runtime-Modul trägt einen BA-047/048/049-Marker; jüngster Marker in `validate_correction_schema_llm.py` ist **BA-043** |
| 2 | **0 Regelkartenänderungen** | `find app/skills -name "*.md" -newermt "2026-08-20"` → **leer** |
| 3 | **kein Messfall benutzt** | alle Läufe über `run_pilot_suite.py` auf `ba-pilot-snapshots`; G2 Exit 0 |
| 4 | beschädigte Artefakte = **Debugging-Material** | `WARNUNG-BESCHAEDIGTE-ARTEFAKTE.md` |
| 5 | **P06/P07 E2E nicht erreichbar** (im aktuellen Workflow) | `test_kontextsuche_pfade.py` 15/15 |
| 6 | **mehrdeutiger Grenzfall nicht konstruiert** | P09 · Kollektiv-Idee · P11 |
| 7 | **Kategorie 4 post-fix per Integration validiert** | `test_kategorie4_integration.py` 19/19 |

> **Der Runtime-Marker-Test war nötig, weil die Dateizeitstempel irreführend sind.** Drei
> Runtime-Dateien tragen ein `mtime` aus dem Zeitraum der Pilotphase. Erst die Suche nach
> BA-Markern zeigt, dass **keine** davon in dieser Sitzung geändert wurde — die Stempel
> stammen von BA-043 und früher. **Zeitstempel sind kein Änderungsnachweis.**

### Die drei Produktänderungen, mit A/B/C-Wirkung

| | Ursache | Geändert | A/B/C-Wirkung | Regression |
|---|---|---|---|---|
| **BA-043** | Artefakt-Iteration fror auf `1` ein (Zirkelbezug K6) | GraphState, K2/K5/K6/K7, **`run_technical_check`** | **nur C** — die Funktion hat genau **einen** Aufrufer, AST-belegt | R3 12/12 · R4 5/5 · R5 7/7 · R6 15/15 |
| **BA-044** | drei Stellen mit derselben Annahme übersehen; K8 hing an `bool(applied)` | K5/K7/K8, `trace_keys` | **nur C** — alles unter `graph/` | R1 10/10 · R2 22/22 · **Replay 12/12 identisch** |
| **BA-047** | K6 prüfte den inneren Vorschlag gegen das Hüllenschema → C-eigener Zusatz-LLM-Aufruf | GraphState, K5/K6 — **keine Runtime-Änderung nötig** | **nur C**, und sie **beseitigt** eine C-Sonderleistung | R9a 13/13 · R9b 16/16 · A/B/C **0/0/0** |

**Vier Belege für erhaltene Vergleichbarkeit:** (1) alle Graph-Änderungen unter `graph/`,
einziger Importeur ausserhalb ist `sp_agent` hinter dem Modusschalter; (2) die eine berührte
Runtime-Funktion hat genau einen Aufrufer, der CLI-Pfad ruft `validate_with_retry` direkt,
Legacy-Defaults unverändert; (3) empirisch bestätigt über A auf P02 und den A/B/C-Dreiervergleich
auf P04; (4) **die einzige gefundene C-Sonderleistung wurde entfernt, nicht hinzugefügt**.

**Regressionsstand gesamt: 199 Einzelprüfungen** über sieben Dateien, alle grün, alle in der
Wurzel-`.venv`. Jeder Fix zusätzlich mit **Negativkontrolle** abgesichert.

### Limitationen, nach Wirkungsrichtung getrennt

* **K3/K8** — zwei Suchpfade im aktuellen Ablauf nicht erreichbar *(mit dem oben genannten
  Vorbehalt)*
* **K5/K8** — mehrdeutiger Grenzfall nicht konstruiert; der Pfad selbst ist belegt
* **K6/K7** — Kategorie 4: Instrument validiert, realer Post-Fix-Positivfall steht aus
* **K3** — `sorted[len//2]` heisst `median`, ist bei geradem n der **obere** Median.
  **Nicht geändert**: gemeinsame Runtime, eine Änderung verschöbe A, B und C gleichzeitig
* **UF3** — die Kartenauswahl von Knoten 2 ist nichtdeterministisch (P01 vs. P03)
* **AP-H** — alle Pilotläufe sind **Einzelläufe**; Streuungsaussagen sind daraus nicht
  ableitbar

- **Verifikation:** die sieben Feststellungen einzeln am Dateisystem und am Code geprüft, nicht
  aus dem Protokoll übernommen. Regressionszahlen durch einen Gesamtlauf erhoben (199).
- **Was NICHT funktioniert hat:**
  * **Alle vier Präzisierungen betrafen Überdehnungen meiner eigenen Formulierungen** — nicht
    die Befunde. „Toter Code", „real belegt (pre-fix)", die Gleichsetzung von beobachtetem
    Pfad und konstruiertem Fall, „eingefroren": jedes Mal habe ich einen korrekten Befund
    **weiter formuliert, als er trägt**. Für eine Arbeit, die später begutachtet wird, ist das
    die gefährlichere Fehlerklasse — ein falscher Befund fällt auf, eine überdehnte
    Formulierung nicht.
  * **Ich hätte „0 Runtime-Änderungen" um ein Haar über Dateizeitstempel belegt.** Drei
    Runtime-Dateien tragen ein `mtime` aus dem Pilotzeitraum; der Nachweis gelingt nur über
    die BA-Marker im Inhalt. Dieselbe Klasse wie der Exit-Code-Zähler in BA-025: **das
    naheliegende Merkmal war das falsche.**
- **Offen / nächstes:** **G5a** — `pip freeze` der Wurzel-`.venv` plus `collect_run_metadata()`
  nach `data/archive/ba-umgebung-eingefroren-<datum>/`; danach **G5** (Einfrieren von
  Regelwerk, Graphstruktur, Prompts, Parametern, Umgebung mit Hashes). **Ab G5 ist jede
  Änderung eine Nachmessung.**

---

### [BA-051] 2026-08-21 — AP-H4a: BA-Runner gebaut und validiert · Kategorie-4-Messunterschied
- **Status:** partial — Runner validiert; **eine messrelevante Anpassung freigegeben und offen**
- **Kapitelbezug:** K5 *(Kontrollbedingungen)*, K6 *(Messinstrument, Kategorie 4)*, K8
- **Literatur:** —
- **Changed files:** `app/eval/run_ba_abc_suite.py` *(neu)*, `docs/BA_ARBEITSPAKETE.md`
- **Status der Läufe:** `pilot` — **kein Messergebnis**

## Warum ein eigener Runner

Die PT4-Runner sind für diese Messung unbrauchbar und werden **nicht umgebaut** (Befund F4,
BA-025): `run_combined_suite.py:97` und `run_iterative.py:33` erzwingen `RULEBOOK_MODE=cards`
**hart** — das Literal gewinnt gegen die Umgebung — und setzen `MEMORY_MODE` gar nicht, sodass
der Default `on` greift. Ein Lauf für **Bedingung A** wäre dort unbemerkt ein `cards`-Lauf
**mit** Gedächtnis.

`app/eval/run_ba_abc_suite.py` startet die bestehenden Pipelines und schreibt auf, was
passiert — **keine neue Fachlogik**, kein Aufruf von `generate_audit_report()`. Je Bedingung
ein eigener Prozess (Schalter kommen beim Import aus `agent_config`), je Lauf ein frischer
Snapshot, `require_ba_env()` hart vor dem ersten Fall.

## Der Ausfall-Lauf wurde zum False-Green-Test

Beim ersten Validierungsversuch war die Testinstanz nicht erreichbar (interner IdP-Host,
`ConnectionError`). **Das hat unbeabsichtigt die wichtigste Anforderung geprüft:**

```
P01/A, P01/B, P01/C  ->  ergebnis="abgebrochen", fehler_nachher=None
```

**Nicht `0`.** Jeder Lauf trug seinen eigenen `abbruchgrund`, die Suite lief weiter, und die
Schalter waren trotz Abbruch korrekt protokolliert. Rohdaten:
`data/archive/ba-h4a/abc-pilot-20260820T213134Z.json`.

## Der erfolgreiche Lauf

Fall **P01**, alle drei Bedingungen, Testinstanz erreichbar
(`…T213724Z.json`, 3 Läufe, 0 Abbrüche):

| | A (mono+monolith) | B (mono+cards) | C (graph+cards) |
|---|---|---|---|
| `MEMORY_MODE` effektiv | off | off | off |
| Fehler vorher → nachher | 1 → 0 | 1 → 0 | 1 → 0 |
| `applied_ok` / `uploaded` / `revalidation_ok` | True/True/True | True/True/True | True/True/True |
| Vorschlag | `update_field` **1.049** | **1.049** | **1.049** |
| Ergebnis | fehlerfrei | fehlerfrei | fehlerfrei |

Ground Truth ist **1.063** — alle drei daneben, deterministisch aus `similar_items_stats`
(BA-046), **keine Halluzination**. Das Messschema trägt **28 Felder, in allen Zeilen gleich**.

## ⚠ Der Befund: Kategorie 4 wird derzeit ungleich gemessen

```
A: errors_resolved=None  errors_new=None  new_error_types=None
B: errors_resolved=None  errors_new=None  new_error_types=None
C: errors_resolved=1     errors_new=0     new_error_types=[]
```

Diese Werte stammen aus `graph_state.json` — und das schreibt **nur C**. Für A und B stehen
sie bewusst auf `None` statt geraten (Lehre aus BA-033).

> **Das ist eine echte Ungleichbehandlung im Messinstrument, kein UF3-Befund.**
> Kategorie 4 (Folgefehlererzeugung) ist eine **fachliche** Grösse: sie lässt sich für alle drei
> Arme aus den Validierungsmeldungen vor und nach der Re-Validierung berechnen. Sie nur dort zu
> erheben, wo zufällig ein `GraphState` existiert, würde **C bevorzugen** — und ein Unterschied
> in Kategorie 4 wäre dann teilweise ein Artefakt der Messung statt der Architektur.
>
> **Abzugrenzen davon:** Karten, Regel-Hashes und Trace, die nur C strukturiert persistiert,
> bleiben wie sie sind. **Das** ist Untersuchungsgegenstand der Nachvollziehbarkeit (Kap. 16.3)
> und ausdrücklich keine Runner-Lücke.

**Freigegeben und offen:** Kategorie 4 für A, B und C aus **einer gemeinsamen** Messfunktion
über `before_errors` / `after_errors`. Die Logik aus Knoten 7 (Fehleridentität =
Validator-Tag + Meldungs-Hash) darf extrahiert und wiederverwendet werden — **keine drei
Implementierungen**. Für C zusätzlich Konsistenzprüfung gegen die persistierten Werte; der
`GraphState` ist für Kategorie 4 **nicht** die privilegierte Quelle.

- **Was NICHT funktioniert hat:**
  * **Ich hätte die Ungleichbehandlung beim Bau sehen müssen.** Ich habe die Kategorie-4-Werte
    aus dem `GraphState` genommen, weil sie dort fertig lagen — und für A/B ehrlich `None`
    gesetzt. Ehrlich, aber falsch: die Grösse ist berechenbar, ich habe nur die bequemere
    Quelle genommen. **Verfügbarkeit einer Quelle ist kein Argument für ihre Verwendung.**
  * Der Netzausfall war ein Glücksfall — ohne ihn wäre der False-Green-Pfad ungetestet
    geblieben, weil der Erfolgsfall ihn nicht berührt.
- **Offen / nächstes:** gemeinsame Kategorie-4-Auswertung implementieren und auf einem
  Pilotfall A/B/C prüfen (gleiche Funktion für alle drei · C-Berechnung == C-GraphState ·
  keine falschen Nullen bei fehlender Re-Validierung · 28-Feld-Schema unverändert). Danach
  H4a schliessen, dann **G5a** (sechs Punkte) und **G5**.

---

### [BA-052] 2026-08-21 — Kategorie 4 für A/B/C aus einer Funktion · Messschema 28 → 29 · AP-H4a geschlossen
- **Status:** done — **H4a abgeschlossen.** Der in BA-051 gemeldete Messunterschied ist behoben
- **Kapitelbezug:** K5 *(Kontrollbedingungen)*, K6 *(Messinstrument, Kategorie 4)*, K7, K8
- **Literatur:** —
- **Changed files:** `app/eval/kategorie4.py` *(neu)*, `app/eval/run_ba_abc_suite.py`,
  `docs/BA_ARBEITSPAKETE.md`. **Kein Produktcode, kein Prompt, keine Regelkarte geändert.**
- **Lauf-Metadaten:** Bedingungen **A** (`monolith`/`monolith`), **B** (`monolith`/`cards`),
  **C** (`graph`/`cards`) · `MEMORY_MODE=off` · `HUMAN_IN_THE_LOOP=false` · `gpt-4.1`,
  API `2025-01-01-preview`, `temperature=0.3` · **Pilotfall P01**, je eigener Prozess und
  frischer Snapshot · `require_ba_env()` bestanden · **Rohdaten:**
  `data/archive/ba-h4a/abc-pilot-20260820T215517Z.json`
- **Status der Läufe:** `pilot` — **kein Messergebnis.** Keiner der 17 Messfälle ausgeführt
  oder angesehen. `generate_audit_report()` nicht aufgerufen.

## Der Befund aus BA-051, behoben

BA-051 hatte aufgedeckt, dass `errors_resolved` / `errors_new` / `new_error_types` aus
`graph_state.json` gelesen wurden — und **das schreibt nur C**. A und B standen auf `None`.

> **Das war eine Ungleichbehandlung im Messinstrument, kein UF3-Befund.** Kategorie 4 ist eine
> **fachliche** Grösse und aus den Validierungsmeldungen für alle drei Arme berechenbar. Sie
> nur dort zu erheben, wo zufällig ein `GraphState` existiert, hätte C bevorzugt — ein
> Unterschied wäre dann teilweise ein Artefakt der Messung statt der Architektur.

**Behoben durch `app/eval/kategorie4.py`:** eine Funktion `kategorie4(vorher_meldungen,
nachher_meldungen, revalidation_ok)`, die der Runner für **A, B und C identisch** aufruft.

**Abzugrenzen und unverändert:** Karten, Regel-Hashes und Trace, die nur C strukturiert
persistiert, bleiben asymmetrisch. Das ist Untersuchungsgegenstand von UF3 (Kap. 16.3) und
ausdrücklich keine Runner-Lücke.

## Primäre Quelle: die autoritativen Validierungsmeldungen

`basis = "validierungsmeldungen_vorher_nachher"` — in allen drei Armen, im Rohdatensatz je
Zeile mitgeschrieben.

**Die Vorher-Meldungen werden direkt nach der initialen Validierung gesichert.** Das ist kein
Stilfrage, sondern notwendig: `snapshot-validation.json` wird von der **Nach**-Validierung
**überschrieben**. Wer sie später erneut lädt, bekommt den Nachher-Stand und misst die
Differenz gegen sich selbst — Ergebnis wäre `0 behoben, 0 neu` bei jedem Lauf.

**Nachher-Meldungen nur nach nachweislich erfolgreicher Re-Validierung.** Sonst:

```
revalidation_ok is not True  ODER  nachher_meldungen is None
   ->  alle vier Felder = "nicht_bestimmbar", basis = "nicht_bestimmbar"
```

**Niemals `0`.** Eine 0 wäre die Behauptung, es sei *nachweislich* nichts Neues entstanden —
dieselbe Umkehr der Beweislast wie im K8-Entscheidungsvertrag (BA-044).

## Eine Implementierung, nicht drei — ohne Produktcodeänderung

Die Fehleridentität wird **direkt aus Knoten 7 importiert**:
`graph/nodes/apply_revalidate._fehler_identitaeten`. Vorher geprüft, nicht angenommen: reine
Funktion, das Modul importiert auf Modulebene nur `hashlib`, `json`, `datetime` — **keine
Nebenwirkungen**. Damit rechnen Produkt und Auswertung nachweislich mit **derselben
Definition**, und es musste kein Produktcode angefasst werden.

## Die falsche Annahme — und was sie gefangen hat

Mein erster Entwurf nahm an, `_fehler_identitaeten()` liefere Identitäten der Form
`"<tag>|<hash>"`, und leitete `new_error_types` durch Zurückparsen des Präfixes ab.

**Tatsächliches Format** (`apply_revalidate.py:207`, nachgesehen statt erinnert):

```
{ hash16 : validator_tag }      # der SCHLUESSEL ist der Hash, der WERT der Tag
```

Der Entwurf lieferte deshalb **Hashes statt Validator-Tags** in `new_error_types`.

> **Gefangen hat es der C-Cross-Check.** Er verglich die gemeinsame Berechnung mit den im
> `graph_state.json` persistierten Werten und meldete die Abweichung — genau wofür er gebaut
> ist. Die korrekte Ableitung bestimmt den Typ durch **Nachschlagen im Nachher-Dict**
> (`sorted({nach[i] for i in neu})`), nicht durch Parsen der Identität.
>
> **Fünfte Annahme dieser Art in Folge** (BA-025, BA-033, BA-040, BA-042, jetzt diese). Der
> Unterschied: diesmal hat ein gebautes Instrument sie abgefangen, bevor sie in eine Messung
> geriet.

## Der Cross-Check: Gegenprobe, kein Schiedsrichter

Für **C** wird zusätzlich `cross_check_graphstate()` gerechnet. Regeln, bewusst so:

* **Die gemeinsame Berechnung ist die primäre Messung.** Der `GraphState` ist die Gegenprobe.
* Bei Abweichung wird **nichts überschrieben** und **keiner der beiden Werte gewinnt**.
* Der Lauf wird als Messinkonsistenz gekennzeichnet:
  `ergebnis = "messinkonsistenz_kategorie4|<eigentliches Ergebnis>"`.

**Semantik dieses Präfixes, ausdrücklich:** ein **technisch abgeschlossener** Lauf, der
hinsichtlich **dieser einen Messgrösse** nicht regulär auswertbar ist. Es ist **kein**
Pipeline-Abbruch und **kein** fachliches `stop_uncertain`. Das eigentliche Ergebnis bleibt
hinter dem Trennstrich erhalten, damit ein technisch erfolgreicher Korrekturlauf nicht
fälschlich als Fehlschlag in die Auswertung geht.

Kein neues Schemafeld dafür: die Inkonsistenz ist über `provenienz.kategorie4_cross_check`
vollständig dokumentierbar (`durchgefuehrt`, `identisch`, `abweichungen`,
`graph_state_werte`).

## Semantik von `ergebnis = "fehlerfrei"`

```
fehler_nachher is None ODER revalidation_ok is not True  ->  "unsicher"
fehler_nachher == 0                                      ->  "fehlerfrei"
sonst                                                    ->  "verbleibend:<n>"
```

> **`fehlerfrei` bezeichnet ausschliesslich den technischen/validatorischen Abschluss** — der
> Server meldet nach abgeschlossener Re-Validierung null Fehler. Es sagt **nichts** über
> Ground-Truth-Korrektheit. P01 ist das Musterbeispiel: alle drei Arme enden `fehlerfrei` und
> schlagen `1.049` vor, während die Ground Truth `1.063` ist — deterministisch aus
> `similar_items_stats` abgelesen, **keine Halluzination** (BA-046). Wer `fehlerfrei` als
> „richtig korrigiert" liest, misst etwas anderes als er glaubt.

## Schemakorrektur 28 → 29

`errors_remaining` fehlte im `MESSSCHEMA`, obwohl es eines der vier Kategorie-4-Felder ist.

**Das ist kein Zusatzfeld für die Messinkonsistenz** — die hängt an `provenienz` — sondern das
Schliessen einer Lücke im ursprünglichen Schema. Damit **29 Felder**.

> **BA-051 wird NICHT rückwirkend umgeschrieben.** Dort steht „28 Felder", und das war zum
> damaligen Zeitpunkt korrekt. Die Korrektur wird **hier** referenziert; historische Einträge
> behalten ihren damaligen Stand (Regel: Protokoll ist Rohmaterial, kein Reinschriftdokument).
>
> **Gleiches gilt für das Rohartefakt:** `abc-pilot-20260820T215517Z.json` trägt im Kopf
> `messschema` mit **28** Einträgen, während jede Zeile **29** Schlüssel hat — der Lauf fand
> im Moment zwischen Erkennen und Nachziehen statt. **Nicht nachträglich verändert.** Der
> heutige Code schreibt beides konsistent (`"messschema": list(MESSSCHEMA)` → 29).

## A/B/C-Pilotvalidierung — P01

| | **A** mono+monolith | **B** mono+cards | **C** graph+cards |
|---|---|---|---|
| Felder je Zeile | **29** | **29** | **29** |
| `MEMORY_MODE` effektiv | off | off | off |
| Fehler vorher → nachher | 1 → 0 | 1 → 0 | 1 → 0 |
| `applied_ok` / `uploaded` / `revalidation_ok` | True/True/True | True/True/True | True/True/True |
| **`errors_resolved`** | **1** | **1** | **1** |
| **`errors_remaining`** | **0** | **0** | **0** |
| **`errors_new`** | **0** | **0** | **0** |
| **`new_error_types`** | `[]` | `[]` | `[]` |
| `kategorie4_basis` | `validierungsmeldungen_vorher_nachher` | *(identisch)* | *(identisch)* |
| Cross-Check | `durchgefuehrt=false` *(kein GraphState)* | *(dito)* | **`identisch=true`, `abweichungen={}`** |
| `ergebnis` | fehlerfrei | fehlerfrei | fehlerfrei |

**Der Befund aus BA-051 ist damit geschlossen:** A und B tragen jetzt dieselben
Kategorie-4-Werte wie C, aus derselben Funktion, auf derselben Basis. Der C-Cross-Check ist
**exakt grün** — die gemeinsame Berechnung und der `GraphState` stimmen überein.

- **Verifikation:** Rohartefakt `abc-pilot-20260820T215517Z.json` mechanisch ausgewertet
  (Feldzahl je Zeile, Kategorie-4-Werte, `provenienz`); `MESSSCHEMA` per AST gezählt (**29**);
  Testdurchlauf siehe unten. Alles in der Wurzel-`.venv`.
- **Was NICHT funktioniert hat:**
  * **Die „tag|hash"-Annahme** — fünfte ihrer Art. Sie wäre in die Messung gelangt, hätte der
    Cross-Check sie nicht gefangen. **Das ist das Argument für die Gegenprobe**: ein
    Instrument, das sich selbst widersprechen kann, ist mehr wert als eines, das immer
    einstimmig ist.
  * **`errors_remaining` fehlte im Schema**, obwohl es eines der vier definierten Felder ist.
    Aufgefallen erst beim Verdrahten, nicht beim Entwerfen — das Schema war aus dem
    Gedächtnis geschrieben statt aus `kategorie4.FELDER` abgeleitet.
  * **Für die Aussagen „kategorie4 7/7" und „Runner-Negativtests 8/8" existiert keine
    permanente Testdatei.** Beide Zahlen sind im Repository nicht reproduzierbar; die
    Kategorie-4-Logik ist stattdessen über `test_kategorie4_integration.py` (**19/19**) und
    `test_kategorien_instrumente.py` (K4 **7/7**) abgedeckt. **Dieselbe Lücke wie bei den
    verlorenen Scratchpad-Skripten in BA-044** — hier ohne Folgen, weil die Abdeckung
    anderweitig besteht, aber als Befund festgehalten.
- **Offen / nächstes:** **G5a** (Lock-Artefakt, sechs Punkte), dann **G5-Preflight**.
  **AP-H (Hauptmessung) NICHT gestartet.**

---

### [BA-053] 2026-08-21 — H4a formal geschlossen · G5a-Lock erzeugt · READY_FOR_G5
- **Status:** done — **G5a abgeschlossen, G5-Preflight erfüllt. G5 bewusst NICHT gesetzt.**
- **Kapitelbezug:** K5 *(Kontrollbedingungen, Reproduzierbarkeit)*, K6, K8
- **Literatur:** —
- **Changed files:** `docs/BA_G5_PREFLIGHT.md` *(neu)*, `docs/BA_ARBEITSPAKETE.md`
  *(H4a, F4, fünf Statusmarker)*, `docs/BA_PROJECT_LOG.md`;
  `data/archive/ba-umgebung-eingefroren-20260820/{lock.json,requirements-frozen.txt}` *(neu)*.
  **Kein Produktcode, kein Prompt, keine Regelkarte. Kein LLM-Lauf, kein Messfall.**

## H4a formal geschlossen

`AP-H4a` auf `[x]` gesetzt, mit den erfüllten Anforderungen einzeln belegt. Zusätzlich zwei
Stellen nachgezogen, die H4a noch als offenen Auftrag führten: der **Befund-F4-Verweis** und
die **F4-Zeile in der Befundtabelle** (jetzt „erledigt 21.08."). **Historische Logeinträge
blieben unverändert.**

**Preflight 26/26** — statisch am Runner und an den vorhandenen Pilotnachweisen:

| Gruppe | geprüft |
|---|---|
| Bedingungen | A=`monolith`+`monolith`, B=`monolith`+`cards`, C=`graph`+`cards`; `MEMORY_MODE=off` und `HUMAN_IN_THE_LOOP=false` **effektiv gemessen** in allen drei Armen |
| Prozesse | eigener Subprozess je Bedingung; **3 verschiedene Snapshot-IDs** bei 3 Läufen |
| Schema | `MESSSCHEMA` = **29** (AST); alle vier Kategorie-4-Felder enthalten; in allen Zeilen identisch |
| Kategorie 4 | Runner importiert `kategorie4()` als **einzige** Quelle; Basis in allen Armen identisch; **A und B tragen Werte, nicht `None`**; `_fehler_identitaeten` aus Knoten 7 |
| Cross-Check | C: `durchgefuehrt=true`, `identisch=true`, `abweichungen={}`; A/B korrekt als `durchgefuehrt=false`; bei Abweichung **kennzeichnen statt überschreiben** |
| Kette | Apply/Upload/Revalidation in allen Armen erfasst und `True` |
| keine falschen Nullen | Ausfall-Lauf: `fehler_nachher=None`, Kategorie 4 **nicht 0** |
| Hygiene | **kein `generate_audit_report()`-Aufruf und kein Import** (AST); kein Messfall in den Rohdaten; `require_ba_env()` hart |

## Fünf veraltete Statusmarker korrigiert

In `BA_ARBEITSPAKETE.md` standen normative Marker, die dem heutigen Zustand widersprachen.
**Nur Statuszeichen und Verweise geändert — kein Befund gelöscht, keine Begründung entfernt:**

| Marker | vorher | jetzt |
|---|---|---|
| **G3b.2** | `[ ] 🚫 BLOCKER — C macht je Durchgang einen LLM-Retry` | `[x]` **behoben** (BA-047, verifiziert BA-048: A 0 · B 0 · C 0, SHA-Invariante hält) |
| **P11** | `[~]` | `[x]` — Ergebnis dokumentiert |
| **Grenzfall-Pfad** | `[ ] Offene Entscheidung` | `[x]` **entschieden**: kein vierter Versuch; (a) Pfad belegt / (b) Fall nicht konstruierbar getrennt geführt |
| **P05-Zusatzfall** | `[ ]` offen, mit der Aussage „Kategorie 4 ist durch P04 real belegt" | `[x]` **entfällt**; die Pre-Fix-Aussage ist gemäss BA-050 als **Debugging-Befund** präzisiert |
| **G3b.4** | `[ ] ~~durchgestrichen~~` | `[x]` **erledigt** (BA-047, vorgezogen) |

Danach führt AP-G **nur noch G5a und G5** als offen — das entspricht dem Ist-Zustand.

## G5a — die sechs Punkte, nicht mehr

`data/archive/ba-umgebung-eingefroren-20260820/`

| # | Punkt | Wert |
|---|---|---|
| 1 | **Git-Commit** | `3ed63bf10102…` auf `main` |
| 2 | **Working Tree** | **38 Einträge, keiner unbekannt** — 17 Messinstrument/Graph · 14 Produktpfad · 7 Dokumentation |
| 3 | **`pip freeze`** | **77 Pakete** → `requirements-frozen.txt` |
| 4 | **`collect_run_metadata()`** | `ba_env_ok=True`, `sys_prefix=…\agentic-ai-mfg\.venv` |
| 5 | **Modell + Schalter** | `gpt-4.1` / `2025-01-01-preview` / `T=0.3`; A/B/C-Schaltermatrix, `MEMORY_MODE=off`, `HUMAN_IN_THE_LOOP=false` |
| 6 | **SHA-256** | Messkatalog isoliert `635a1e06…`, kombiniert `94ae337e…`, Pilot-Ground-Truth `6c4c3bb4…`, Referenz-Snapshot `b429ba26…`, **14 Regelkarten** einzeln + Gesamt `4d380884…` |

**Kein Datei-für-Datei-Manifest** — wie im Umfang festgelegt. Punkt 6 hasht nur, was **nicht**
unter Versionskontrolle steht (`data/` ist ignoriert).

> **Der Messkatalog wurde ausschliesslich gehasht, nicht gelesen.** Ein SHA-256 über die
> Katalogdatei verrät keinen Fallinhalt; G5a Punkt 6 verlangt ihn ausdrücklich.

## Git-Zustand — nichts angefasst

`git status --porcelain` klassifiziert, **nichts gestaged, verworfen, resettet oder
überschrieben**. Kein `git reset`, kein Stash, kein Cleanup.

**Nicht committet, und zwar bewusst:** der Tree trägt Änderungen aus mehreren Arbeitspaketen
und aus Sitzungen, die nicht diesem Block zuzuordnen sind. Ein „nur die Dateien dieses
Blocks"-Commit wäre nicht sauber abgrenzbar — die Vorgabe verlangt in dem Fall ausdrücklich,
den Zustand zu dokumentieren statt zu committen. Genau das ist in `lock.json` Punkt 2
geschehen.

## Testbericht — 21.08.2026, 00:07

| Datei | Prüfungen | Ergebnis |
|---|---|---|
| `test_graph_handoff_regressions.py` *(R1–R6, R9a/b)* | 100 | PASS |
| `test_kategorien_instrumente.py` | 32 | PASS |
| `test_kategorie4_integration.py` | 19 | PASS |
| `test_kontextsuche_pfade.py` | 15 | PASS |
| `test_k8_replay_ba036.py` | 12 | PASS |
| `test_trace_registry.py` | 11 | PASS |
| `test_ab_cli_isolation.py` | 10 | PASS |
| **Summe** | **199** | **alle grün** |

> **Diese 199 sind Assertions, keine unabhängigen Experimente.** Sie verteilen sich auf
> **7 Testdateien** und decken denselben Gegenstand teils mehrfach ab. Als Fallzahl für eine
> empirische Aussage taugen sie nicht — sie belegen ausschliesslich, dass die Verträge des
> Messinstruments halten.

## READY_FOR_G5 — mit einem benannten Vorbehalt

`docs/BA_G5_PREFLIGHT.md` führt zwölf Kriterien, **alle erfüllt, kein Blocker**. Der einzige
Vorbehalt ist G5a Punkt 2: der Working Tree ist **nicht sauber**. Zwei saubere Wege stehen zur
Wahl — vor G5 committen (dann trägt der Commit-Hash allein) oder ohne Commit einfrieren (dann
ist `lock.json` Punkt 2 das Delta gegenüber `3ed63bf1`). **Das ist eine Abnahmeentscheidung
und wurde nicht vorweggenommen.**

**G5 ist NICHT gesetzt.**

- **Verifikation:** H4a-Preflight 26/26 statisch am Runner (AST) und an zwei archivierten
  Pilotläufen; G5a-Werte aus `lock.json`; Testbericht aus einem Gesamtlauf; Statusmarker durch
  erneuten Sweep gegengeprüft (AP-G führt nur noch G5a/G5 offen).
- **Was NICHT funktioniert hat:**
  * **Mein eigener Preflight meldete einen falschen FAIL:** „kein `generate_audit_report()` im
    Runner" — der Name steht dort im **Docstring** (*„wird nie aufgerufen"*), und ich hatte per
    Textsuche geprüft. AST zeigt null Aufrufe und null Imports. **Dieselbe Lehre wie beim
    Exit-Code-Zähler in BA-025**, und ich bin ihr im selben Projekt erneut aufgesessen. Der
    Prüfer läuft jetzt über den AST.
  * **`git status --porcelain` per `.strip()` ausgewertet** — das frisst das führende
    Leerzeichen der **ersten** Zeile, und `CLAUDE.md` erschien als `LAUDE.md` in der Klasse
    „unbekannt". Ein Parsing-Fehler, der beinahe einen erfundenen Blocker erzeugt hätte.
  * **Die G5a-Katalogpfade waren geraten** und zeigten ins Leere (`isolated-error-snapshots/`
    statt `pt4-manipulated_snapshots/isolated-error-snapshots/`). Erst der `FEHLT`-Vermerk im
    ersten Lauf hat es aufgedeckt — deshalb meldet die Hash-Funktion Fehlen ausdrücklich,
    statt den Eintrag zu überspringen.
  * **Für „kategorie4 7/7" und „Runner-Negativtests 8/8" gibt es keine permanente Testdatei**
    (bereits in BA-052 vermerkt). Die Abdeckung besteht anderweitig, die Zahlen selbst sind im
    Repository nicht reproduzierbar.
- **Offen / nächstes:** **Abnahme durch den Nutzer**, dann Entscheidung zum Working Tree, dann
  **G5 setzen**. **AP-H nicht begonnen** — kein Messfall ausgeführt oder angesehen, keine
  Vorabmessung, kein Audit-Report.

---

### [BA-054] 2026-08-21 — Messstand als Commit fixiert · G5a auf den echten Codestand aktualisiert
- **Status:** done — Reproduzierbarkeitslücke geschlossen. **G5 weiterhin NICHT gesetzt.**
- **Kapitelbezug:** K5 *(Reproduzierbarkeit, Kontrollbedingungen)*, K8
- **Literatur:** —
- **Changed files:** Git-Commit `61a3f51` auf neuem Branch `ba-messstand-g5` (53 Dateien);
  `data/archive/ba-umgebung-eingefroren-20260820/lock.json` *(neu erzeugt)*;
  `docs/BA_G5_PREFLIGHT.md`, `docs/BA_PROJECT_LOG.md`.
  **Kein Produktcode inhaltlich geändert, kein Prompt, keine Regelkarte, kein Testlauf.**

## Der Befund: HEAD beschrieb den Messstand nicht

`3ed63bf1` enthielt **keine einzige** messrelevante Datei:

```
git ls-tree -r HEAD --name-only | grep -c "smart-planning/graph"      -> 0
git ls-tree -r HEAD --name-only | grep -cE "run_ba_abc_suite|kategorie4" -> 0
```

**Die gesamte Bedingung C, der BA-Runner und die Kategorie-4-Auswertung lagen untracked im
Working Tree.** Ein G5a-Lock, das `3ed63bf1` als Messstand führt, hätte auf einen Commit
gezeigt, in dem der Messcode nicht existiert — die Messung wäre aus dem Repository heraus
nicht rekonstruierbar gewesen.

## Klassifikation aller Einträge

39 Einträge auf oberster Ebene, **53 expandiert** (`--untracked-files=all`, zwei
Verzeichnisse aufgelöst).

| Klasse | Anzahl | Inhalt |
|---|---|---|
| **Bestandteil des finalen BA-/Messstands** | **46** | Graph-Variante (15), `app/eval/*` (17), gemeinsame Runtime (7), `app/core/*` (4), `sp_agent.py`, `retrieval.py`, `requirements.txt` |
| **Reine Dokumentation** | **7** | `CLAUDE.md`, `docs/BA_*.md` (6), `docs/abbildungen/graph-korrekturablauf.mmd` |
| **Eindeutig fachfremd/unabhängig** | **0** | — |
| **Unklar** | **0** | — |

**Alle 53 sind im BA-Projektprotokoll dokumentiert.** Damit war die saubere Trennung möglich,
und es gab keinen Grund, den Commit zu verweigern.

## Der Commit

`61a3f51e0b77…` auf **neuem Branch `ba-messstand-g5`** — bewusst nicht auf `main`: der
Messstand ist ein Zustand, auf den zurückgezeigt wird, kein Fortschritt der Hauptlinie.

Vor dem Stagen geprüft: `app/.env` ist per `.gitignore:6` ausgeschlossen und **nicht gestagt**;
kein Klartext-Geheimnis in den Diffs. `data/` ist per `.gitignore:12` ausgeschlossen — das
G5a-Lock ist deshalb **bewusst nicht versioniert**, es hasht ja genau die nicht versionierten
Artefakte.

**Nichts verworfen, resettet oder gestasht.** Working Tree danach: **0 Einträge**.

## Die zwei geprüften Punkte

### 1 — Ground Truth der Messfälle: Lücke gefunden und geschlossen

**Der erste Lockstand reichte nicht.** Er hashte zwei Index-Dateien:

* `isolated-error-snapshots/expected-results.json` — trägt echte Ground Truth ✔
* `kombinierte-fehler-snapshots/ERROR-SNAPSHOTS.md` — **eine Beschreibung**. Eine Prüfung auf
  Feldnamen (`before`, `after`, `jsonPath`) fand **keine**; die Datei besteht aus
  Überschriften. Als maschinenlesbare Ground Truth **ungeeignet**.

**Und die eigentlichen Messeingänge — die manipulierten Snapshots — waren gar nicht erfasst.**
Ohne sie ist die Hauptmessung nicht reproduzierbar: der Ground-Truth-Wert allein sagt nichts,
wenn der Eingang, auf den er sich bezieht, nicht fixiert ist.

**Geschlossen:** Punkt 6 hasht jetzt **jede Datei beider Messkataloge einzeln plus einen
Gesamthash**:

| | Dateien | Gesamt-SHA-256 |
|---|---|---|
| `messfaelle_isoliert` | **14** | `0b0a9aff6100406f…` |
| `messfaelle_kombiniert` | **13** | `5a237594fb9f6f0c…` |

27 Dateien sind kein „riesiges Manifest", sondern genau der Umfang, den G5a Punkt 6 meint —
und es ist die einzige Stelle, an der Einzeldateien gehasht werden.

> **Die Messfälle wurden ausschliesslich gehasht, nicht gelesen.** Geprüft wurde nur, *ob*
> Ground-Truth-Feldnamen vorkommen — keine Werte, keine Fallinhalte.

### 2 — Regelbasis der Bedingung A: doppelt gesichert

`app/tools/smart-planning/runtime/runtime-files/llm-validation-fix-rules.md`

* **versioniert** — `git ls-files` bestätigt: in Git enthalten, unverändert seit `3ed63bf1`
* **gehasht** — `a3c14bd1b66cc1e3…`, 36.165 Byte

Der Hash **stimmt mit BA-016 (B3.1) überein**, wo dasselbe Regelwerk vor dem AP-B-Baselinelauf
archiviert wurde. Die Regelbasis von A ist seit April unverändert.

## Datumsabweichung `20260820` vs. Testbericht 21.08. — reine Zeitzone

Der Ordnername kommt aus `datetime.now(timezone.utc).strftime("%Y%m%d")`, der Testbericht nennt
**Lokalzeit** (`+02:00`):

```
lock erzeugt_utc : 2026-08-20T22:13:07+00:00
Testbericht      : 2026-08-21 00:07:41+02:00   (= 2026-08-20 22:07 UTC)
```

**Dieselbe Stunde, zwei Zeitzonen.** Kein inhaltlicher Versatz. **Nicht umbenannt** — der
Ordnername bleibt UTC-basiert, wie alle Rohdatenstempel des Projekts (`…T215517Z`), und
`lock.json` führt `erzeugt_utc` ausdrücklich mit.

## G5a aktualisiert

| # | Punkt | Wert |
|---|---|---|
| 1 | Git-Commit | **`61a3f51e0b77…`** auf `ba-messstand-g5` *(vorher `3ed63bf1`)* |
| 2 | Working Tree | **sauber** *(vorher 38 Einträge)* |
| 3 | `pip freeze` | 77 Pakete |
| 4 | `collect_run_metadata()` | `ba_env_ok=True` |
| 5 | Modell + Schalter | `gpt-4.1` / `2025-01-01-preview` / `T=0.3` |
| 6 | SHA-256 | **+27 Messfall-Dateien einzeln**, 14 Regelkarten, 4 Katalog-/Referenzdateien, Monolith-Regelwerk |

- **Verifikation:** `git ls-tree` für die HEAD-Lücke; `git status --porcelain
  --untracked-files=all` für die Klassifikation; `git check-ignore` für `.env` und `data/`;
  Diff-Grep auf Geheimnisse; Lock nach dem Commit neu erzeugt.
- **Was NICHT funktioniert hat:**
  * **Die erste Geheimnis-Kontrolle meldete `trace_keys.py` als Treffer** — mein Grep suchte
    nach `key` im Pfadnamen. Dritter Textsuche-Fehlalarm in Folge (BA-053 zweimal). Präzise
    geprüft: `.env` nicht gestagt, keine Klartext-Geheimnisse in den Diffs.
  * **Ich hatte das G5a-Lock für vollständig gehalten, obwohl die Messeingänge fehlten.**
    Erst die gezielte Frage nach der Ground Truth der Messfälle hat es aufgedeckt. Zwei
    gehashte Index-Dateien sahen nach Abdeckung aus — eine davon enthält gar keine Ground
    Truth. **Ein Hash über die falsche Datei ist keine Sicherung.**
  * **Der dokumentierte HEAD war neun Einträge lang falsch.** Seit BA-045 steht in mehreren
    Protokolleinträgen `git 3ed63bf1` als Lauf-Metadatum — technisch richtig als *Commit zum
    Laufzeitpunkt*, aber irreführend, weil der gemessene Code nie darin lag. **Historische
    Einträge bleiben unverändert**; ab hier ist `61a3f51` der Messstand.
- **Offen / nächstes:** **Abnahme und G5 setzen.** AP-H nicht begonnen.

---

### [BA-055] 2026-08-21 — H2/H3/H4 vor dem Freeze geschlossen: 5 Wiederholungen, Randomisierung, Grenzfall als Limitation
- **Status:** done — **AP-H ist bis auf H5 (die Messung selbst) vollständig vorbereitet.**
  **G5 weiterhin NICHT gesetzt.**
- **Kapitelbezug:** K5 *(Forschungsdesign, Messvorschrift)*, K6 *(Robustheit/UF2)*, K8 *(Limitationen)*
- **Literatur:** —
- **Changed files:** `app/eval/run_ba_abc_suite.py`, `app/eval/test_messplan.py` *(neu)*,
  `docs/BA_ARBEITSPAKETE.md`, `docs/BA_PROJECT_LOG.md`.
  **Kein Produktcode, kein Prompt, keine Regelkarte. Kein LLM-Lauf, kein Messfall.**

## Warum das vor G5 gehört

H2 und H4 sind **selbst messrelevant**: Wiederholungszahl und Reihenfolge sind Teil der
Messvorschrift, nicht der Auswertung. Nach dem Freeze festgelegt wären sie Nachjustieren —
und nach dem Sehen der Ergebnisse festgelegt wären sie wertlos (harte Regel 5). Deshalb hier,
vor dem Einfrieren.

## H2 — Wiederholungen: N = 5, verbindlich

**Die Zahl war nicht festgelegt.** Geprüft, bevor irgendetwas implementiert wurde:

| Fundstelle | Wortlaut | verbindlich? |
|---|---|---|
| Masterplan Kap. 13.2 | *„denselben Fall **3–5×**"* | nein — Spanne |
| Masterplan Kap. 15.3 | *„Wiederholungstest, identische Eingabe, **N Läufe**"* | nein — N offen |
| Masterplan Kap. 15.3, Warnkasten | *„**5 Wiederholungen** von 17 Fällen ergeben **nicht** n=85"* | nein — Rechenbeispiel in einer Warnung |
| AP-H H2 | *„derselbe Fall **3–5×**"* | nein — Spanne |

> **Das war die eine methodische Entscheidung, die ich nicht selbst treffen durfte** — sie
> wurde ausdrücklich eingeholt und lautet: **N = 5**. Sie steht jetzt als Konstante
> `WIEDERHOLUNGEN = 5` im Runner, mit Datum und Begründung im Code.

**Nur A und C werden wiederholt. B läuft einmal** — Kontrollarm, nur UF1 (Kap. 7.1, AP-H5).
Das ist Teil des Designs, keine Sparmassnahme: B beantwortet die Frage nach dem Kartensystem,
nicht die nach der Konsistenz.

| Arm | Läufe |
|---|---|
| **A** monolith + monolith | 17 × 5 = **85** |
| **B** monolith + cards *(Kontrollarm)* | 17 × 1 = **17** |
| **C** graph + cards | 17 × 5 = **85** |
| | **187** |

> ⚠ **Wiederholungen sind KEINE zusätzlichen Fälle.** 5 × 17 ergibt **nicht** n = 85. Es
> bleiben **17 Fälle**, ergänzt um eine **Within-Case-Stabilität** je Fall. Der Rohdatensatz
> macht das explizit: identische `fall`-ID, laufende `wiederholung`, und der Kopf trägt den
> Warnhinweis mit. Wer die Wiederholungen als Fallzahl mitzählt, überschätzt die Aussagekraft
> um das Fünffache — ein Fehler, den ein Gutachter mit Statistikhintergrund sofort sieht.

**Das 29-Feld-Schema bleibt unverändert.** Die Wiederholungsnummer steht in `lauf_metadaten`,
einem bestehenden Feld — der Inhalt wird präziser, das Schema nicht breiter. Auch abgebrochene
Läufe tragen Wiederholung und Position, sonst wäre die Reihenfolge hinterher nicht
rekonstruierbar.

## H4 — Randomisierung: Seed 20260821, vorher dokumentiert

`messplan()` erzeugt die Reihenfolge der Tripel **(Fall × Bedingung × Wiederholung)** und
mischt sie mit einem eigenen `random.Random(seed)` — nicht mit dem globalen Modul, damit
nichts anderes im Prozess den Zustand beeinflusst.

**Was randomisiert wird:** ausschliesslich die **Reihenfolge**.
**Was nicht:** die Zuordnung von Schaltern zu Bedingungen, die Fälle, irgendetwas an der
A/B/C-Semantik. Jeder Lauf bleibt ein **eigener Prozess** mit frischem Snapshot,
`MEMORY_MODE=off`, `HUMAN_IN_THE_LOOP=false`.

**Wozu überhaupt:** ohne Mischung liefe erst alles A, dann alles B, dann alles C. Jede Drift
über die Zeit — Serverlast, Netzlatenz, Modellverhalten — fiele dann systematisch mit der
Bedingung zusammen und wäre von einem Architektureffekt **nicht zu trennen** (Kap. 17).

**Seed `20260821`** — das Datum der Festlegung, ohne weitere Bedeutung. Der Wert ist beliebig
und darf es sein; entscheidend ist allein, dass er **vor** der Messung feststeht.

> **Seed und Reihenfolge gehen beide in die Rohdaten** (`randomisierung.seed`,
> `randomisierung.reihenfolge`). Der Seed allein genügt **nicht**: er belegt
> Reproduzierbarkeit nur, solange der Planungscode unverändert bleibt. Die ausgeschriebene
> Reihenfolge belegt, was **wirklich** gelaufen ist.

Neu ausserdem `--trockenlauf`: erzeugt den Plan und gibt ihn aus, **ohne irgendetwas
auszuführen**. So lässt sich die Messreihenfolge vorab ansehen, ohne einen einzigen Lauf zu
starten.

## H3 — geschlossen als Limitation, nicht durch neue Fälle

Der ursprüngliche Auftrag lautete „Grenzfälle ergänzen". **Er wird nicht ausgeführt** — G3 hat
die Frage bereits beantwortet, und der gehashte 17-Fälle-Katalog wird nicht angefasst.

**Zwei Aussagen, die nicht gleichgesetzt werden:**

* **(a)** Der `stop_uncertain` / `manual_intervention_required`-**Pfad** ist **real belegt**
  (P10 D5, BA-045) und über R2 sowie den K8-Entscheidungsvertrag regressionsgesichert.
* **(b)** Ein **gezielt konstruierter, fachlich mehrdeutiger Ground-Truth-Grenzfall** liess
  sich in **drei** Entwürfen nicht zuverlässig herstellen.

Neue Messfälle würden ausserdem den in G5a fixierten Katalog brechen (14 + 13 Dateien einzeln
gehasht). **Geht als Limitation nach K5 und K8.**

## Geprüft — ohne einen einzigen Messfall

`app/eval/test_messplan.py`, **25/25**, ausschliesslich mit **synthetischen** IDs (`S01…S17`)
und echten **Pilot**-IDs. Der Messkatalog wird nicht geladen.

Zwei Eigenschaften tragen den Plan, und **beide** werden geprüft:

* **reproduzierbar** — gleicher Seed + gleiche Eingabe → identische Reihenfolge
* **wirksam** — anderer Seed → andere Reihenfolge

> Die zweite ist die leicht zu vergessende: eine „Randomisierung", die immer dasselbe liefert,
> ist keine — und das fiele nicht auf, solange nur die erste geprüft wird.

Zusätzlich: alle drei Bedingungen kommen bereits in der **ersten Planhälfte** vor, und es gibt
häufige Bedingungswechsel statt Blöcke. Ohne diese Prüfung könnte eine formal „gemischte"
Reihenfolge trotzdem blockweise sein.

**Finaler Runner-Preflight: 35/35** — die 26 Kriterien aus BA-053 plus neun zu H2/H4.
**Regressionsstand: 224 Assertions über 8 Dateien**, alle grün.

- **Verifikation:** Wiederholungszahl vor der Implementierung an vier Fundstellen geprüft;
  Plan per Trockenlauf mit Pilot-IDs erzeugt; Preflight statisch am Runner plus Planvergleich;
  Gesamtlauf aller Tests nach der Änderung.
- **Was NICHT funktioniert hat:**
  * **Ich hätte die Wiederholungszahl beinahe aus dem Warnkasten in Kap. 15.3 abgeleitet.**
    Dort steht *„5 Wiederholungen von 17 Fällen"* — aber als **Rechenbeispiel in einer Warnung
    gegen n=85**, nicht als Festlegung. Eine Zahl aus einem Gegenbeispiel zu übernehmen und
    als verbindlich auszugeben, wäre eine erfundene Messvorschrift gewesen.
  * **Die Testausgabe ist bei langen Listen unlesbar** — `Pruefung.drucken()` schreibt
    187-elementige Reihenfolgen vollständig aus. Kosmetisch, und ich habe es **bewusst nicht
    geändert**: der Harness wird von acht Testdateien geteilt, und kurz vor dem Freeze ist das
    Risiko einer Sammeländerung höher als der Nutzen. Vermerkt für nach der Messung.
- **Offen / nächstes:** **H5, die eigentliche Messung** — 187 Läufe, randomisiert, nach G5.
  **G5 ist nicht gesetzt und AP-H nicht begonnen.**

---

### [BA-056] 2026-08-21 — B wird ebenfalls wiederholt: 255 Läufe, Attribution auch für UF2
- **Status:** done — H2 angepasst. **G5 weiterhin NICHT gesetzt, H5 nicht gestartet.**
- **Kapitelbezug:** K5 *(Forschungsdesign, Dreiarm-Attribution)*, K6 *(UF2/Robustheit)*, K8
- **Literatur:** —
- **Changed files:** `app/eval/run_ba_abc_suite.py`, `app/eval/test_messplan.py`,
  `docs/BA_MASTERPLAN.md` *(Kap. 7.1)*, `docs/BA_ARBEITSPAKETE.md` *(H2, H5)*,
  `docs/BA_G5_PREFLIGHT.md`, `docs/BA_PROJECT_LOG.md`.
  **Kein Produktcode, kein Prompt, keine Regelkarte. Keine Änderung an der A/B/C-Semantik.**

## Die Änderung

`WIEDERHOLUNGSARME` von `("A", "C")` auf `("A", "B", "C")`. Umfang **187 → 255 Läufe**.

| Arm | vorher | jetzt |
|---|---|---|
| **A** monolith + monolith | 85 | **85** |
| **B** monolith + cards | **17** | **85** |
| **C** graph + cards | 85 | **85** |
| | 187 | **255** |

## Warum das nicht bloss „mehr Läufe" ist

Der Masterplan begründet den Kontrollarm B in Kap. 7.1 selbst mit **Attribution**:

> *„Bei A gegen C allein wäre nicht entscheidbar, woher ein Effekt kommt. Mit B ist er
> zerlegbar."*

**Genau das galt bisher nur für UF1.** Zwei Absätze weiter stand: *„für UF2 wäre es zu teuer.
**Ohne Wiederholungsläufe.**"* Damit hätte sich für die Robustheit nur der Gesamteffekt
A → C betrachten lassen:

```
A → B    Effekt der Regelkarten-Modularisierung   (gleiche Pipeline, andere Regelform)
B → C    Effekt der Graph-Orchestrierung          (gleiche Regelform, andere Pipeline)
A → C    Gesamtpaket                              (Hauptvergleich, unverändert)
```

Ein Stabilitätsunterschied zwischen A und C wäre **nicht zuordenbar** gewesen — er könnte aus
der Kartenform stammen oder aus der Orchestrierung. Da die Intervention ausdrücklich ein
**Gesamtpaket** ist (harte Regel 3), ist die Zerlegung für die Interpretation notwendig.

> **Der Hauptvergleich bleibt A gegen C.** Die Zerlegung schwächt ihn nicht, sie macht ihn
> deutbar. Und sie schliesst einen **Selbstwiderspruch im Masterplan**: dort wurde B mit
> Attribution begründet und gleichzeitig von der einzigen Forschungsfrage ausgenommen, bei der
> Wiederholungen überhaupt etwas beitragen.

## Was sich ausdrücklich NICHT ändert

* **Die A/B/C-Semantik.** B bleibt `monolith` + `cards` — der reale, produktiv ausgerollte
  Ist-Zustand. Kein Schalter, keine Zuordnung, keine Pipeline wurde angefasst.
* **Die Randomisierung.** Seed `20260821` unverändert; `messplan()` mischt weiterhin die Tripel
  (Fall × Bedingung × Wiederholung). Die **Reihenfolge ändert sich** natürlich, weil die
  Grundmenge grösser ist — der Seed bleibt derselbe und die Reihenfolge weiterhin
  reproduzierbar.
* **Das 29-Feld-Messschema.**
* **Kategorien, Prompts, Regelkarten, Produktlogik.**
* **Die Fallzahl.** Die Wiederholungen bleiben **Within-Case**-Wiederholungen:
  **n = 17**, nicht n = 255. 255 Läufe ergeben nicht 255 unabhängige Fälle — im
  Rohdatensatzkopf steht der Warnhinweis unverändert mit.

## Geprüft

`app/eval/test_messplan.py`, **27/27** (vorher 25 — zwei Prüfungen kamen dazu):

* `B: jeder Fall genau 5x (seit BA-056, vorher 1x)`
* `alle drei Arme gleich oft — kein Arm bevorzugt`
* Gesamtzahl **255**, je Bedingung `{A: 85, B: 85, C: 85}`
* Reproduzierbarkeit und Wirksamkeit der Mischung unverändert grün

Weiterhin **ausschliesslich synthetische** IDs (`S01…S17`) und Pilot-IDs; kein Messfall
geladen. Trockenlauf mit drei Pilotfällen: 45 Läufe, `{A: 15, B: 15, C: 15}`.

**Runner-Preflight 35/35** · **Regressionen 226 Assertions über 8 Dateien**, alle grün.

## Nachgezogene Dokumente

| Dokument | Stelle |
|---|---|
| `BA_MASTERPLAN.md` | Kap. 7.1 — der Satz *„für UF2 wäre es zu teuer. Ohne Wiederholungsläufe."* ist ersetzt, **mit sichtbarem Änderungskasten** statt stiller Korrektur |
| `BA_ARBEITSPAKETE.md` | H2 (Umfang), H5 (*„Wiederholungen nur für A und C"* → alle drei) |
| `BA_G5_PREFLIGHT.md` | Kriterium H2, Schritt 3 nach der Abnahme |

- **Verifikation:** Trockenlauf mit Pilot-IDs; `test_messplan.py` 27/27; Preflight 35/35;
  Gesamtlauf aller acht Testdateien. Alles in der Wurzel-`.venv`.
- **Was NICHT funktioniert hat:**
  * **`CLAUDE.md` trägt denselben überholten Satz und wurde NICHT von mir geändert.** Zeile 126
    beschreibt B als *„Kontrollarm, nur UF1, ohne Wiederholungen"*. Das ist ab jetzt falsch.
    Ich habe es bewusst liegen gelassen: `CLAUDE.md` sind die Projektinstruktionen, und die
    ändere ich nicht unaufgefordert. **Vor G5 anzupassen** — sonst friert der Einfrierzeitpunkt
    einen Widerspruch zwischen Instruktion und Messvorschrift ein.
  * **Beinahe hätte ich nur den Code geändert.** Der Masterplan ist die verbindliche Referenz;
    eine Codeänderung, die ihm widerspricht, macht ihn wertlos, ohne dass es auffällt. Die
    Prüfung auf betroffene Stellen (`ohne Wiederholungen`, `nur UF1`) fand **vier** Fundstellen
    in drei Dateien — drei habe ich nachgezogen, die vierte ist oben gemeldet.
- **Offen / nächstes:** `CLAUDE.md` Zeile 126, dann **G5**. **H5 nicht gestartet.**

---

### [BA-057] 2026-08-21 — ██ G5: EINGEFROREN ██ — ab hier ist jede Änderung eine Nachmessung
- **Status:** done — **AP-G vollständig abgeschlossen.** Nächstes: **H5**, die Hauptmessung
- **Kapitelbezug:** K5 *(Forschungsdesign, Kontrollbedingungen, Reproduzierbarkeit)*, K6, K7
- **Literatur:** —
- **Changed files:** `docs/BA_ARBEITSPAKETE.md` *(G5, X2)*, `docs/BA_G5_PREFLIGHT.md`,
  `docs/BA_PROJECT_LOG.md`. **Kein Produktcode, kein Prompt, keine Regelkarte, kein Testlauf.**

## Einfrierzeitpunkt

```
2026-08-21  12:39:27 +02:00        (= 2026-08-21T10:39:28Z)
```

**Freigegeben durch den Nutzer** nach dem Preflight in `docs/BA_G5_PREFLIGHT.md`.

## Was eingefroren ist

| | Stand |
|---|---|
| **Codestand** | Commit **`93ad674`** — der letzte, der `app/` berührt hat. Alles danach ist reine Dokumentation. |
| **HEAD beim Einfrieren** | `beae011` auf Branch `ba-messstand-g5`, Working Tree **sauber** |
| **Graphstruktur** | **9 Knoten**, 12 Kanten — am kompilierten Graphen nachgezählt, nicht aus der Doku |
| **Regelkarten** | **14** Stück · Gesamt-SHA `4d380884…f658` |
| **Monolith-Regelwerk (Bedingung A)** | `llm-validation-fix-rules.md`, 36.165 Byte · SHA `a3c14bd1…b4b1` — **identisch mit BA-016 B3.1**, seit April unverändert |
| **Messkatalog isoliert** | **14** Dateien · Gesamt-SHA `0b0a9aff…da76` |
| **Messkatalog kombiniert** | **13** Dateien · Gesamt-SHA `5a237594…cedb` |
| **Referenz-Snapshot** | SHA `b429ba26…57ac` |
| **Pilot-Ground-Truth** | SHA `6c4c3bb4…2767` |
| **Modell** | `gpt-4.1` · API `2025-01-01-preview` · `temperature=0.3` |
| **Umgebung** | Wurzel-`.venv`, **77 Pakete**, `requirements-frozen.txt`; `ba_env_ok=True` |
| **Prompts** | unverändert — **0 Promptänderungen** während der gesamten Pilotphase (BA-050, an BA-Markern im Code belegt, nicht an Zeitstempeln) |

**Vollständiges Lock-Artefakt:**
`data/archive/ba-umgebung-eingefroren-20260821/{lock.json, requirements-frozen.txt}`

## Die Messvorschrift, die ab jetzt gilt

| | |
|---|---|
| **Bedingungen** | **A** `monolith`+`monolith` · **B** `monolith`+`cards` · **C** `graph`+`cards` |
| **Fälle** | **17** |
| **Wiederholungen** | **5 je Fall, in allen drei Armen** (BA-055, BA-056) |
| **Umfang** | **255 Läufe** — A 85 · B 85 · C 85 |
| **Reihenfolge** | randomisiert, Seed **`20260821`**, Seed und erzeugte Reihenfolge gehen in die Rohdaten |
| **Schalter** | `MEMORY_MODE=off`, `HUMAN_IN_THE_LOOP=false`, je Bedingung ein **eigener Prozess** |
| **Messschema** | **29 Felder**, in allen Zeilen identisch |
| **Kategorie 4** | für A, B und C aus **derselben Funktion** (`kategorie4.py`); `GraphState` bei C nur Cross-Check |
| **Audit-Report** | **nicht** Bestandteil der Messung — kein Aufruf, kein Import (AST-belegt) |

> ⚠ **`n` bleibt 17.** Die 255 Läufe sind **Within-Case**-Wiederholungen. 255 ergibt nicht
> n=255, und 5 × 17 nicht n=85. Jede Aussage über Halluzinationsraten hat die Fallzahl **17**.

## Was der Freeze bedeutet

**Ab diesem Zeitpunkt ist jede Änderung an Regelwerk, Graphstruktur, Prompts, Parametern oder
Umgebung eine Nachmessung** — und muss als solche gekennzeichnet werden (harte Regel 5). Das
gilt auch für Änderungen, die offensichtlich Verbesserungen wären: nach dem Sehen der
Ergebnisse nachzujustieren ist genau der Fehler, den der Einfrierzeitpunkt verhindert.

**Nicht eingefroren** sind: die Auswertungsschicht (AP-I), die Expertenmaterialien (AP-X) und
das Protokoll. Sie erzeugen keine Messwerte.

## Belege, auf denen der Freeze steht

* **G3** abgeschlossen (BA-049) — 7 von 10 Pilotzielen real belegt, 3 begründet nicht
* **G4** abgeschlossen (BA-050) — `BA_G4_PILOTPHASE_ABSCHLUSS.md`, keine Inkonsistenz
* **H4a** abgeschlossen (BA-051/052) — Runner-Preflight **35/35**
* **H2/H3/H4** abgeschlossen (BA-055/056) — vor dem Freeze, weil selbst messrelevant
* **G5a** abgeschlossen (BA-053/054) — sechs Punkte, Lock auf `beae011`
* **Regressionen** — **226 Assertions** über 8 Dateien, alle grün
* **0 Promptänderungen · 0 Regelkartenänderungen · kein Messfall verbraucht**

## Nebenkorrektur: X2

Bei der Schlussdurchsicht der Arbeitspakete fiel auf, dass **X2** („Variantenneutrales
Präsentationsformat") auf `[ ]` stand, obwohl `app/core/ergebnis_format.py` vollständig gebaut
und in **F5 für beide Bedingungen erprobt** ist. Auf `[~]` korrigiert, nicht auf `[x]`:
`aus_pipeline_ergebnis()` und `als_text()` werden derzeit **nirgends aufgerufen** — das Format
existiert und ist validiert, die Expertenvorlage entsteht aber erst aus Messergebnissen.

- **Verifikation:** Einfrierzeitpunkt aus der Systemzeit (lokal und UTC); Codestand über
  `git log -1 -- app/`; Knotenzahl am **kompilierten** Graphen; alle Hashes aus dem
  Lock-Artefakt; Working Tree vor dem Freeze-Commit leer.
- **Was NICHT funktioniert hat:**
  * **Meine erste Prüfung der Knotenzahl scheiterte an einem geratenen Funktionsnamen**
    (`baue_graph` statt `build_graph`). Die 9 stammt jetzt aus dem kompilierten Graphen, nicht
    aus der Dokumentation — was bei einer Zahl, die seit BA-023 durch alle Dokumente wandert,
    der einzig sinnvolle Beleg ist.
  * **X2 stand acht Arbeitspakete lang falsch auf offen.** Aufgefallen erst bei der
    ausdrücklichen Frage, ob die Haken stimmen. Ein Statusmarker, den niemand prüft, veraltet
    still — dieselbe Klasse wie die fünf Marker aus BA-053.
- **Offen / nächstes:** **H5 — die Hauptmessung.** 255 Läufe, randomisiert, nach diesem
  Einfrieren. Danach AP-I und AP-X.

---

### [BA-058] 2026-08-21 — Dry-Run findet fehlenden Messumfang: 150 statt 255 · Ground Truth für die 7 kombinierten Fälle rekonstruiert
- **Status:** done — Messkatalog vollständig, **G5 von 12:39 Uhr ist überholt**, neuer G5 steht aus
- **Kapitelbezug:** K5 *(Testfallkatalog, Ground-Truth-Methode)*, K6, K7, K8
- **Literatur:** —
- **Changed files:** `app/eval/run_ba_abc_suite.py` *(KATALOGE, `lade_katalog()`)*,
  `app/eval/test_messkatalog_h5.py` *(neu)*,
  `data/snapshots/pt4-manipulated_snapshots/kombinierte-fehler-snapshots/expected-results.json` *(neu)*,
  `data/archive/ba-h5-messplan/` *(neu)*, Dokumentation.
  **Kein Prompt, keine Regelkarte, keine Produktlogik, keine A/B/C-Semantik geändert.**
- **Status der Läufe:** **kein Messlauf.** Ausschliesslich Trockenläufe und Katalogprüfung —
  keine Pipeline, kein LLM, kein Server.

## Der Befund

Der H5-Trockenlauf mit dem eingefrorenen Stand ergab:

```
Messplan: 150 Laeufe, Seed 20260821, 5x fuer A/B/C
je Bedingung: {'A': 50, 'B': 50, 'C': 50}
```

**150 statt 255.** `KATALOGE["mess"]` zeigte nur auf `isolated-error-snapshots/` — und der hat
**10** Fälle. Die 17 setzen sich laut Masterplan Kap. 13.1 anders zusammen:

> `isolated-error-snapshots/` → 10 · `kombinierte-fehler-snapshots/` → 10, davon sind
> **01–03 Einzelfehler**, die I01–I03 wiederholen. **→ 17 distinkte Fälle, davon 3 redundant.**

Der zweite Katalog fehlte im Runner vollständig — und hatte **keine
`expected-results.json`**, konnte also gar nicht geladen werden.

> **Der Dry-Run hat genau das geleistet, wofür er da ist.** Ohne ihn wäre die Hauptmessung mit
> **41 % zu wenig Fällen** gelaufen — und ausgerechnet ohne die Mehrfehlerfälle, bei denen der
> Masterplan den Effekt **primär** erwartet.

## Freeze-Semantik: der alte G5 ist überholt, es gibt keine Nachmessung

**Unter dem G5 von 12:39 Uhr wurde kein einziger H5-Messlauf durchgeführt.** Es existiert kein
Messwert, der von der Korrektur betroffen wäre. Damit ist dies **keine Nachmessung**, sondern
eine Korrektur **vor Beginn der Datenerhebung**.

**BA-057 bleibt unverändert stehen** — der Einfrierzeitpunkt, die Hashes und der Stand sind
korrekt protokolliert und werden nicht rückwirkend verändert. Er ist ab jetzt als *überholt vor
der ersten Datenerhebung* gekennzeichnet. Ein neuer verbindlicher G5 wird nach Abnahme gesetzt.

## Schritt 1 — Ground-Truth-Herkunft, unabhängig belegt

`generate-error-snapshots.ps1` deklariert je Injektion `Path / Anchor / Before / After`.
Das ist eine **Behauptung** — geprüft wurde sie per **Deep-Diff** zwischen
`ok-snapshot.json` und jedem Fehler-Snapshot:

| Datei | deklariert | im Diff | |
|---|---|---|---|
| `snapshot-error-01…03` | je 1 | je 1 | ✔ |
| `snapshot-error-04…07` | je 2 | je 2 | ✔ |
| `snapshot-error-08, 09` | je 3 | je 3 | ✔ |
| `snapshot-error-10` | 4 | 4 | ✔ |

**Die Menge der abweichenden JSON-Pfade entspricht in allen zehn Fällen exakt der deklarierten
Menge** — nicht mehr, nicht weniger, und alle Werte stimmen. Damit hängt die Ground Truth an
den **Daten**, nicht am Skript und nicht am untersuchten System.

**Nicht verwendet:** `pt4-combined-results.json` (PT4-*Ergebnisse*, kein Ground Truth), keine
Modellantworten, keine erwarteten Systemausgaben.

## Schritt 2 — Mehrfach-Ground-Truth

Neu: `kombinierte-fehler-snapshots/expected-results.json`, **7 Fälle** `K04`–`K10`,
**18 Korrekturen**, im Format des bestehenden isolierten Katalogs.

| Fall | Fehler | Korrekturen | Validatoren |
|---|---|---|---|
| K04 | 2 | 2 | `unique_ids`, `demand_article_ids` |
| K05 | 2 | 2 | `density_values`, `work_plan_ids` |
| K06 | 2 | 2 | `packaging_references`, `unique_ids` |
| K07 | 2 | 2 | `equipment_predecessor_references`, `equipment_worker_qualification_compatibility` |
| K08 | 3 | 3 | `unique_ids`, `demand_article_ids`, `density_values` |
| K09 | 3 | 3 | `work_plan_ids`, `packaging_references`, `packaging_equipment_compatibility_references` |
| **K10** | **3** | **4** | `unique_ids`, `equipment_predecessor_references`, `start_end_operation_existence` |

> **K10 ist der Fall, der still verlorengegangen wäre:** drei Fehler, aber **vier**
> Korrekturen — `E12` verlangt *zwei* Zeitwerte (`rampUpTime` **und** `netTimeFactor`). Wer
> „ein Fehler = eine Korrektur" annimmt, misst hier falsch.

**Braucht es neue Bewertungslogik? Nein — und das ist geprüft, nicht vermutet.** `changes` ist
im bestehenden Format **bereits eine Liste**, und der Runner reicht sie unverändert nach
`artefakte.ground_truth`. Mehr noch: **der isolierte Katalog führt seit jeher selbst einen
Mehrfachfall — I08** (derselbe HE01-Fall, zwei Zeitwerte). Mehrfach-Ground-Truth ist also nicht
neu, sondern war die ganze Zeit da.

Zusätzlich je Fall `expectedErrors[]` mit Validator, Typ, erwarteter Meldung und Korrektur —
die singulären Felder des isolierten Formats (`expectedContext`, `expectedMessageContains`)
können mehrere Validatoren nicht abbilden und hätten den Fall auf einen Fehler reduziert.

## Schritt 3 — der finale Messkatalog

**10 isolierte (`I01`–`I10`) + 7 kombinierte (`K04`–`K10`) = n = 17.**

`snapshot-error-01…03` stehen **gar nicht erst** in der Ground-Truth-Datei — mit Begründung im
Feld `ausgeschlossen`. Sie können damit nicht versehentlich mitgezählt werden.

## Schritt 4 — Runner

`KATALOGE` trägt jetzt je Katalog eine **Liste** von Verzeichnissen; `lade_katalog()` sammelt
die Fälle darüber hinweg und **wirft bei doppelten Fall-Codes** — zwei Kataloge mit derselben
Kennung wären stillschweigend ein Fall zu wenig, also genau die Lücke, die hier aufgefallen ist.

Unverändert: A/B/C-Semantik, N=5, Seed `20260821`, Kategorien, 29-Feld-Schema, `MEMORY_MODE`,
Prompts, Regeln, Produktlogik.

## Schritt 5 — Validierung, ausschliesslich Trockenlauf

`app/eval/test_messkatalog_h5.py`, **31/31**:

* Katalog **17** Fälle, Codes eindeutig, 10 isoliert + 7 kombiniert, keine Fremdcodes
* `snapshot-error-01…03` **nicht** als Messfälle geführt, Ausschluss begründet
* Ground Truth für **alle 17** ladbar, alle Snapshot-Dateien vorhanden, **29 Korrekturen** gesamt
* **8 Mehrfachfälle** (I08 + die sieben kombinierten), K10 mit 4 Korrekturen
* Plan **255** Positionen, A/B/C je **85**, Positionen lückenlos 1..255
* **keine doppelten und keine fehlenden** (Fall, Bedingung, Wiederholung)-Tripel
* jeder Fall je Arm genau **5×**, jeder Fall in allen drei Armen
* Seed **20260821**, Reihenfolge mit 255 Einträgen im Kopf

**Archiviert:** `data/archive/ba-h5-messplan/h5-messplan-trockenlauf-20260821T105431Z.json` —
die vollständige 255er-Reihenfolge. **Gesamtstand: 257 Assertions über 9 Dateien, alle grün.**

- **Verifikation:** Deep-Diff gegen den sauberen Snapshot für alle zehn Dateien; HE01-Index am
  Snapshot nachgesehen (`workItemKey` auf Index 3); Trockenlauf; Katalogtest; Gesamtlauf.
- **Was NICHT funktioniert hat:**
  * **Mein Diff meldete zunächst eine Abweichung bei `snapshot-error-10`** — der Generator
    schreibt `workItemConfigs[HE01]` als *logisches* Label, im JSON ist es eine **Liste** und
    HE01 liegt auf Index 3. Kein Datenproblem, sondern meine Notation. Am Snapshot geprüft:
    Index 3 trägt `workItemKey: "HE01"`, `rampUpTime: 120`, `netTimeFactor: 0.3`.
  * **Meine Testerwartung „28 Korrekturen" war falsch — es sind 29.** `I08` im *isolierten*
    Katalog hat schon immer **zwei** Korrekturen. Ich hatte „10 isolierte = 10 Korrekturen"
    angenommen, statt nachzuzählen. Der Fehler war harmlos, weil der Test ihn sofort meldete —
    aber er zeigt, dass auch der **isolierte** Katalog nie „ein Fehler = eine Korrektur" war.
  * **Die beiden Kataloge benutzen unterschiedliche Pfadnotation** — der isolierte semantisch
    (`articles[articleId=100005].workItemConfigs[HE01]`), der neue indexbasiert
    (`articles[0].workItemConfigs[3]`). **Bewusst nicht vereinheitlicht:** eine nachträgliche
    Umschreibung von Ground-Truth-Pfaden wäre eine Normalisierung ohne unabhängigen Beleg. Im
    Katalog unter `herkunft.pfadnotation` festgehalten — **AP-I muss beide Formen behandeln.**
- **Offen / nächstes:** **neuen G5 setzen** (nach Abnahme), dann **H5**. Kein Messlauf gestartet.

---

### [BA-059] 2026-08-21 — Pfadnotationen: Auflösung statt Normalisierung · Vergleichsregel vor der Messung fixiert
- **Status:** done — letzte Vorbereitungsbaustelle geschlossen. **Neuer G5 steht aus.**
- **Kapitelbezug:** K5 *(Messvorschrift)*, K6 *(Korrektheitsbewertung, Kategorie 1)*, K8
- **Literatur:** —
- **Changed files:** `app/eval/pfadaufloesung.py` *(neu)*, `app/eval/test_pfadaufloesung.py` *(neu)*.
  **Keine Ground-Truth-Datei geändert, kein Pfad umgeschrieben, keine Produktlogik,
  kein Prompt, keine Regel. Kein LLM-Lauf, kein Messlauf.**

## Die Festlegung

> **Zwei Zielpfade gelten fachlich als identisch, wenn sie im zugehörigen Snapshot
> deterministisch auf dasselbe JSON-Element beziehungsweise dasselbe Feld auflösen.**

Sie steht **vor** der Hauptmessung fest und gilt für A, B und C gleichermassen.

## Existiert so etwas schon? — geprüft, nicht angenommen

Beide vorhandenen Parser wurden gegen **alle 29** Ground-Truth-Pfade laufen gelassen:

| Parser | löst auf | scheitert an |
|---|---|---|
| `apply_correction.parse_target_path()` *(Produktcode)* | **18 / 29** | semantischen Selektoren **und** dreistufigen Indexpfaden |
| `routes.review._parse_target_path()` | **20 / 29** | allen semantischen Selektoren |

**Keiner versteht `[articleId=100005]`, `[HE01]` oder `[workItems contains VOAR01]`.** Ein
naiver Stringvergleich hätte eine **richtige** Korrektur als falsch gezählt.

Nebenbefund: der isolierte Katalog benutzt **vier** Notationen, nicht zwei — Index,
`Feld=Wert`, blosses Label, und ein `contains`-Prädikat.

## Was gebaut wurde — und was ausdrücklich nicht

`app/eval/pfadaufloesung.py`: löst beide Notationen gegen den Snapshot in einen **kanonischen
Indexpfad** auf und vergleicht diese.

* **Auswertung, keine Produktlogik.** Liegt unter `app/eval/`, wird von keiner Pipeline
  importiert. `apply_correction.parse_target_path()` bleibt unangetastet.
* **Die Ground-Truth-Dateien wurden NICHT umgeschrieben.** Eine nachträgliche Normalisierung
  von Messmaterial wäre eine Änderung ohne unabhängigen Beleg.
* **Es rät nie.** 0 Treffer oder >1 Treffer → `nicht_bestimmbar`, mit benanntem Grund.

## Die unangenehme Feinheit: gegen welchen Snapshot?

Zwei GT-Pfade lösen im **Fehler**-Snapshot auf **null** Elemente auf — weil ihr Selektor genau
den Wert nennt, den die Injektion zerstört hat:

| Fall | Pfad | before → after |
|---|---|---|
| **I07** | `articles[articleId=100005].workItemConfigs[RF01].workItemKey` | `"RF01"` → `"RF01_REMOVED"` |
| **I09** | `equipment[workItems contains VOAR01].workItems[0]` | `"VOAR01"` → `"WORK_ITEM_NOT_AVAILABLE"` |

Kein Katalogfehler — die Pfade beschreiben die Stelle, **bevor** sie manipuliert wurde.

**Regel, deterministisch und protokolliert:** zuerst gegen den **Fehler-Snapshot** auflösen —
das ist der Zustand, den das System sieht und auf den sich ein Modellvorschlag bezieht.
Gelingt das nicht eindeutig, gegen die **saubere Referenz**. Die verwendete Basis steht im
Ergebnis (`basis`). Gelingt es in **keiner** Basis: `nicht_bestimmbar`.

> **Warum das den Vergleich nicht verschiebt:** Die Injektionen ändern **nur Werte, keine
> Struktur** — in BA-058 per Deep-Diff über alle zehn Dateien belegt, keine Listenlänge weicht
> ab. Ein kanonischer Indexpfad ist deshalb in beiden Snapshots derselbe.

## Geprüft — beide Richtungen

`app/eval/test_pfadaufloesung.py`, **23/23**:

**Positiv** — alle **29** GT-Pfade lösen eindeutig auf; **27** über den Fehler-Snapshot,
**genau I07 und I09** über die Referenz. Semantisch und indexbasiert werden als gleich erkannt:

```
articles[articleId=100005].workItemConfigs[HE01].rampUpTime
articles[0].workItemConfigs[3].rampUpTime
     ->  beide: articles[0].workItemConfigs[3].rampUpTime   ->  gleich
```

**Negativ** — nichts davon geht still als Treffer durch: Selektor trifft nichts · Index
ausserhalb · Feld existiert nicht · Pfad syntaktisch kaputt · unbekannter Selektortyp ·
**Selektor trifft zwei Elemente**. Alle sechs → `nicht_bestimmbar` mit benanntem Grund, und
ein Vergleich mit mehrdeutiger Seite ergibt ebenfalls `nicht_bestimmbar`.

Ausserdem die Gegenproben: verschiedene Stellen werden als **verschieden** erkannt
(`articles[0]` vs. `articles[1]`, `relDensityMin` vs. `relDensityMax`), und ein eindeutiges
Label wird aufgelöst. **Ohne die Negativrichtung wäre der Test wertlos** — ein Vergleicher,
der alles gleich findet, besteht jeden Positivtest.

**Gesamtstand: 280 Assertions über 10 Dateien, alle grün.**

- **Verifikation:** beide vorhandenen Parser gegen alle 29 Pfade; Auflösung aller 29 gegen den
  jeweils eigenen Snapshot; I07/I09-Hypothese durch Gegenprobe gegen die saubere Referenz
  bestätigt; Negativkontrollen mit künstlichen Strukturen.
- **Was NICHT funktioniert hat:**
  * **Mein erster Entwurf löste nur gegen den Fehler-Snapshot auf** und meldete I07 und I09 als
    unauflösbar. Ich hätte das als Katalogfehler abhaken können — tatsächlich lag es daran,
    dass der Selektor den zerstörten Wert nennt. **Erst die Gegenprobe gegen den sauberen
    Snapshot hat es geklärt.** Ein „unauflösbar" ohne zweite Basis wäre eine falsche
    Fehlermeldung gewesen.
  * **Ich hatte zwei Notationen erwartet und vier vorgefunden.** `[workItems contains VOAR01]`
    stand in keiner Dokumentation; es fiel nur auf, weil der Test gegen **alle** 29 Pfade lief
    statt gegen eine Auswahl.
- **Offen / nächstes:** **neuen G5 setzen** (nach Abnahme), dann **H5**. Keine weiteren
  Vorbereitungsbaustellen.

---

### [BA-060] 2026-08-21 — Analysewerkzeuge gesichert · methodische Befunde nach Kapitel sortiert
- **Status:** done — Dokumentation und Werkzeugsicherung. **Neuer G5 steht weiterhin aus.**
- **Kapitelbezug:** K3, K5, K6, K7, K8 *(dieser Eintrag ist selbst ein Einstieg für alle)*
- **Literatur:** —
- **Changed files:** `docs/BA_METHODISCHE_BEFUNDE.md` *(neu)*;
  `app/eval/{verify_ground_truth,preflight_messrunner,g5a_messstand_festhalten}.py` *(neu,
  aus dem Scratchpad übernommen)*.
  **Kein Produktcode, kein Prompt, keine Regel, kein Messlauf.**

## Anlass: drei Beweismittel lagen ungesichert

Die Analyse dieser Arbeitsphase entstand in **38 Scratchpad-Skripten**. Die meisten sind
Einmal-Patches — ihr Ergebnis steht im Repository und im Protokoll, sie werden nicht gebraucht.
**Drei sind es sehr wohl**, und sie lagen in einem sitzungsgebundenen Temp-Verzeichnis:

| Werkzeug | Warum es bleiben muss |
|---|---|
| `verify_ground_truth.py` | **ist selbst das Beweismittel** für BA-058: der Deep-Diff belegt die Ground Truth unabhängig vom Generator. Ohne das Skript ist der zentrale Beleg nicht nachrechenbar. |
| `preflight_messrunner.py` | **wird vor der Messung erneut gebraucht** — 35 Kriterien am Runner |
| `g5a_messstand_festhalten.py` | **wird für den finalen G5 erneut gebraucht** — erzeugt das Lock-Artefakt |

> **Das ist genau die Lücke, die dieses Projekt schon einmal getroffen hat.** In BA-044 gingen
> die Regressionsskripte 1 und 2 im Scratchpad verloren; R1 galt danach als *unbelegt*, bis es
> neu gebaut war. Denselben Fehler ein zweites Mal zu machen — mit dem Skript, das die Ground
> Truth der Hauptmessung belegt — wäre schwer zu erklären.

Übernommen, Pfadkonstanten generalisiert (`Path(__file__)` statt hartkodiert), aus dem Repo
heraus laufen lassen: alle drei laufen.

## Beim Übernehmen einen dauerhaften Fehlalarm gefunden

`verify_ground_truth.py` meldete **`>>> NICHT VOLLSTAENDIG REKONSTRUIERBAR <<<`** für
`snapshot-error-10` — obwohl alles stimmt. Ursache: seine Pfadnormalisierung ersetzte nur die
Klammern, sodass `workItemConfigs[HE01]` als `workItemConfigs.HE01` stehen blieb, während der
Diff `workItemConfigs.3` liefert. Reine Notation, in BA-058 bereits am Snapshot geklärt
(Index 3 trägt `workItemKey='HE01'`).

Behoben durch **Wiederverwendung von `pfadaufloesung.aufloesen()`** — keine neue Logik. Das
Werkzeug meldet jetzt `ALLE SIEBEN REKONSTRUIERBAR`, Exit 0.

> **Ein Werkzeug, das dauerhaft falschen Alarm schlägt, wird ignoriert — und dann übersieht man
> den echten.** Als Wegwerfskript war das egal; als versioniertes Beweismittel nicht.

## `docs/BA_METHODISCHE_BEFUNDE.md`

Das Protokoll ist chronologisch — die richtige Ordnung für ein Protokoll, die falsche für eine
Arbeit. Das neue Dokument sortiert die Befunde aus BA-035 bis BA-059 **nach Kapitel**, jeder
mit Verweis auf den Eintrag, in dem er entstanden ist. Es wiederholt das Protokoll nicht und
ersetzt es nicht.

**Aufbau:**

* **Die drei wertvollsten Befunde** — falscher Wert ≠ Halluzination · zwei von vier Kategorien
  zeigten auf das Instrument · die Fehlerinjektion hat eine benennbare Reichweitengrenze
* **Befunde nach Kapitel** — K3, K5, K6, K7, K8, je als Tabelle mit Beleg
* **Was das Projekt über sein eigenes Arbeiten gelernt hat** — acht wiederkehrende Muster,
  darunter: fehlende Evidenz als Unbedenklichkeit gelesen · ein grüner Nachbarfall belegt den
  Nachbarn nicht · **sechsmal am falschen Merkmal gemessen** · Zeitstempel sind kein
  Änderungsnachweis · eine Attrappe, die alles akzeptiert, prüft nichts · jeder Fix braucht
  eine Negativkontrolle · vier Reissbrett-Entwürfe in Folge daneben · der Dry-Run hat sich
  bezahlt gemacht
* **Werkzeuge**, die den Belegen zugrunde liegen

**Warum dieser Abschnitt der wichtigste ist:** Kapitel 8 und die Limitationen leben von dem,
was **nicht** funktioniert hat — und genau das lässt sich später nicht rekonstruieren. Die
acht Muster stehen verstreut über sechzehn Protokolleinträge; als Muster erkennbar werden sie
erst nebeneinander.

- **Verifikation:** alle drei übernommenen Werkzeuge aus dem Repo heraus ausgeführt;
  `verify_ground_truth.py` nach der Korrektur mit Exit 0; Gesamttestlauf unverändert
  **280 Assertions über 10 Dateien**, alle grün.
- **Was NICHT funktioniert hat:**
  * **Der Fehlalarm im übernommenen Werkzeug wäre beinahe mitversioniert worden.** Ich hatte
    ihn in BA-058 erklärt und abgehakt — als Wegwerfskript zu Recht. Beim Übernehmen ins Repo
    ändert sich die Anforderung: ein Dauerwerkzeug darf nicht dauerhaft falsch melden. Das war
    mir beim Kopieren zunächst nicht präsent.
  * **35 der 38 Scratchpad-Skripte werden nicht übernommen** — bewusst. Einmal-Patches, deren
    Ergebnis im Repository steht; sie zu versionieren erzeugte eine zweite, veraltende
    Beschreibung desselben Zustands. Was sie taten, steht im jeweiligen Protokolleintrag.
- **Offen / nächstes:** **neuen G5 setzen** (nach Abnahme), dann **H5**.

---

### [BA-061] 2026-08-21 — ██ G5 (verbindlich): EINGEFROREN ██ — Messstand für die Hauptmessung
- **Status:** done — **AP-G endgültig abgeschlossen.** Nächstes und einziges Offenes: **H5**
- **Kapitelbezug:** K5 *(Forschungsdesign, Kontrollbedingungen, Reproduzierbarkeit)*, K6, K7
- **Literatur:** —
- **Changed files:** `docs/BA_ARBEITSPAKETE.md`, `docs/BA_G5_PREFLIGHT.md`,
  `docs/BA_PROJECT_LOG.md`. **Kein Produktcode, kein Prompt, keine Regel, kein Messlauf.**

## Einfrierzeitpunkt

```
2026-08-21  13:13:41 +02:00        (= 2026-08-21T11:13:41Z)
```

**Freigegeben durch den Nutzer.** Dies ist der **verbindliche** G5.

## Der vorherige G5 ist überholt — und warum das keine Nachmessung ist

Am **21.08.2026 um 12:39:27 +02:00** wurde ein erster G5 gesetzt (**BA-057**). Der
anschliessende **H5-Trockenlauf** — der erste Schritt nach dem Freeze — ergab **150 statt 255
Läufen**: `KATALOGE["mess"]` lud nur den isolierten Katalog mit 10 Fällen (**BA-058**).

> **Unter dem alten G5 wurde kein einziger H5-Messlauf durchgeführt.** Es existieren keine
> Hauptmessdaten, die von der Korrektur betroffen wären. Damit ist dies **keine Nachmessung**,
> sondern eine Korrektur **vor Beginn der Datenerhebung**.

**BA-057 bleibt unverändert stehen.** Der damalige Einfrierzeitpunkt, die Hashes und der Stand
sind korrekt protokolliert und werden nicht rückwirkend verändert — sie sind als *überholt vor
der ersten Datenerhebung* gekennzeichnet. Nichts gelöscht, nichts verschleiert.

> **Der Trockenlauf hat sich damit bezahlt gemacht.** Ohne ihn wäre die Hauptmessung mit
> **41 % zu wenig Fällen** gelaufen — und ausgerechnet ohne die Mehrfehlerfälle, bei denen der
> Masterplan den Effekt **primär** erwartet.

## Der eingefrorene Stand

| | |
|---|---|
| **Messrelevanter Codestand** | **`15f2a44`** auf Branch `ba-messstand-g5` |
| **HEAD beim Einfrieren** | `a1e018e` — Working Tree **sauber** |
| **Differenz `15f2a44` → HEAD** | **ausschliesslich Hinzufügungen**: drei *lesende* Prüfwerkzeuge (`verify_ground_truth.py`, `preflight_messrunner.py`, `g5a_messstand_festhalten.py`) und zwei Dokumente. **Keine messrelevante Datei geändert** — per `git diff --name-only` über `app/eval/run_ba_abc_suite.py`, `kategorie4.py`, `kategorien.py`, `pfadaufloesung.py`, `app/core/`, `app/agents/`, `app/tools/`, `app/skills/`, `data/` belegt: leer. |

**Messvorschrift:**

| | |
|---|---|
| **Fälle** | **17** — 10 isolierte (`I01`–`I10`) + 7 kombinierte (`K04`–`K10`) |
| **Ground Truth** | **29** erwartete Korrekturen; `snapshot-error-01…03` ausgeschlossen (redundant zu I01–I03) |
| **Bedingungen** | **A** `monolith`+`monolith` · **B** `monolith`+`cards` · **C** `graph`+`cards` |
| **Wiederholungen** | **N = 5 in allen drei Armen** |
| **Umfang** | **255 Läufe** — A 85 · B 85 · C 85 |
| **Reihenfolge** | randomisiert, **Seed `20260821`**; Seed und erzeugte Reihenfolge gehen in die Rohdaten |
| **Messschema** | **29 Felder**, in allen Zeilen identisch |
| **Kategorie 4** | für A, B und C aus **derselben Funktion** (`kategorie4.py`); `GraphState` bei C nur Cross-Check |
| **Pfadvergleich** | `pfadaufloesung.py` — zwei Zielpfade sind identisch, wenn sie **deterministisch auf dasselbe JSON-Element auflösen**; Mehrdeutigkeit → `nicht_bestimmbar` |
| **Schalter** | `MEMORY_MODE=off`, `HUMAN_IN_THE_LOOP=false`, je Bedingung ein **eigener Prozess** |
| **Modell** | `gpt-4.1` · API `2025-01-01-preview` · `temperature=0.3` |
| **Umgebung** | Wurzel-`.venv`, 77 Pakete, `ba_env_ok=True` |

**Hashes** *(vollständig in `data/archive/ba-umgebung-eingefroren-20260821/lock.json`)*:

| Artefakt | SHA-256 |
|---|---|
| Regelkarten (14 Stück, gesamt) | `4d3808849946e2b8dc9453d8…` |
| Monolith-Regelwerk (A), 36.165 Byte | `a3c14bd1b66cc1e391839a01…` |
| Ground Truth isoliert | `635a1e0679f35e75fed2a4bb…` |
| Ground Truth kombiniert | `24f457988225d599a16bf906…` |
| Messfall-Dateien isoliert (14) | `0b0a9aff6100406fadf29607…` |
| Messfall-Dateien kombiniert (14) | `b9313710cfe980fcbd9c5a35…` |
| Referenz-Snapshot | `b429ba2606068bb670180681…` |

> **`n` bleibt 17.** Die 255 Läufe sind **Within-Case**-Wiederholungen. 255 ergibt nicht
> n = 255, und 5 × 17 nicht n = 85. Jede Aussage über Halluzinationsraten hat die Fallzahl 17.

## Was ab jetzt gesperrt ist

**Keine messrelevanten Änderungen mehr an:** Produktcode · Graph · Runner ·
Evaluierungslogik · Pfadauflösung · Kategorien · Prompts · Regeln · Ground Truth ·
Messkatalog · Modellparametern · Umgebung.

**Weiterhin erlaubt:** Dokumentation und spätere **reine AP-I-Auswertungsschritte** — solange
sie die **eingefrorene Bewertungssemantik nicht nachträglich verändern**. Die Grenze ist
scharf: eine Auswertung *anwenden* ist erlaubt, ihre *Definition* ändern nicht. Wer eine
Kategorie, eine Pfadregel oder ein Ground-Truth-Feld anders auslegt als hier festgelegt,
erzeugt eine **Nachmessung** und muss sie als solche kennzeichnen (harte Regel 5).

## Grundlage des Freeze

* **G3** abgeschlossen (BA-049) — 7 von 10 Pilotzielen real belegt, 3 begründet nicht
* **G4** abgeschlossen (BA-050) — `BA_G4_PILOTPHASE_ABSCHLUSS.md`, keine Inkonsistenz
* **H4a** abgeschlossen (BA-051/052) — Runner-Preflight **35/35**
* **H2/H3/H4** abgeschlossen (BA-055/056) — vor dem Freeze, weil selbst messrelevant
* **Messkatalog** vervollständigt (BA-058) — Ground Truth per Deep-Diff unabhängig belegt
* **Pfadvergleich** festgelegt (BA-059) — `test_pfadaufloesung.py` 23/23
* **G5a** aktualisiert (BA-053/054/060) — sechs Punkte, Lock auf dem aktuellen Stand
* **Regressionen** — **280 Assertions** über 10 Dateien, alle grün
* **0 Promptänderungen · 0 Regelkartenänderungen · kein Messfall verbraucht**

- **Verifikation:** Einfrierzeitpunkt aus der Systemzeit (lokal und UTC); die Differenz
  `15f2a44` → HEAD per `git diff --name-status` **und** gezielt über alle messrelevanten Pfade;
  Hashes aus dem Lock-Artefakt; Working Tree vor dem Freeze-Commit leer.
- **Was NICHT funktioniert hat:**
  * **Mein erster Abgleich der beiden Commits war unbrauchbar.** Ich verglich SHA-256 von
    `git show` (LF) gegen den Working Tree (CRLF) und erhielt fünf falsche „ABWEICHUNG" —
    darunter `kategorie4.py` und `sp_agent.py`. Ein Zeilenenden-Artefakt. **Dritter
    Textvergleichs-Fehlalarm dieser Sitzung** (nach `generate_audit_report` im Docstring und
    `trace_keys.py` in der Geheimnisprüfung). Die belastbare Antwort liefert `git diff`, das
    Zeilenenden kennt — nicht ein selbstgebauter Hashvergleich.
  * **Beinahe hätte ich auf `a1e018e` eingefroren, ohne die Differenz zu benennen.** Sie ist
    harmlos, aber „harmlos" muss belegt sein und nicht angenommen: der Freeze ist der eine
    Punkt, an dem eine unbemerkte Änderung die ganze Messung entwertet.
- **Offen / nächstes:** **H5 — die Hauptmessung.** 255 Läufe, randomisiert, nach diesem
  Einfrieren. Danach AP-I und AP-X. **H5 ist nicht gestartet.**

---

### [BA-062] 2026-08-21 — Laufende Sicherung der Messzeilen · ██ G5 neu gesetzt ██
- **Status:** done — **AP-G abgeschlossen. READY_FOR_H5.**
- **Kapitelbezug:** K5 *(Reproduzierbarkeit, Rohdatenpflicht)*, K6, K7
- **Changed files:** `app/eval/run_ba_abc_suite.py` *(nur Schreibzeitpunkt)*,
  `app/eval/test_persistenz.py` *(neu)*, Dokumentation.
  **Keine Änderung an A/B/C, Messplan, Reihenfolge, Seed, 29-Feld-Schema, Kategorie-4-,
  Korrektheits- oder Pfadlogik, Ground Truth, Prompts, Regeln, Produktcode. Kein Messlauf.**

## Der Befund vor dem Start

Der Runner schrieb den Rohdatensatz **erst nach der letzten Zeile**
(`ziel.write_text(...)` hinter der Schleife). Bis dahin lagen die 29-Feld-Zeilen nur im
Arbeitsspeicher. Ein Abbruch bei Lauf 250 von 255 — VPN, Serverneustart, Timeout — hätte den
**kompletten Aggregatdatensatz** gekostet; bei 3–5 Stunden Laufzeit kein theoretisches Risiko.

Die Snapshot-Artefakte je Lauf (`data/snapshots/<sid>/…`) wären erhalten geblieben, aber die
aggregierten Messzeilen mit `schalter_effektiv`, Kategorie-4-Werten, `provenienz` und
Reihenfolgeposition hätten aus 250 Snapshots rekonstruiert werden müssen.

**Nicht eigenmächtig repariert.** Das ist kein Defekt, sondern eine fehlende Eigenschaft — und
der Runner stand unter Freeze. Vorgelegt, entschieden, dann umgesetzt.

## Die Änderung — ausschliesslich der Schreibzeitpunkt

`_schreibe_aggregat(ziel, katalog, kopf, zeilen)` wird **nach jedem Lauf** gerufen, auch nach
einem abgebrochenen.

**Atomar, nicht anhängend:** Die Zieldatei ist **ein** JSON-Dokument. Mitten hineinzuschreiben
erzeugte bei einem Abbruch eine korrupte Datei — also genau den Schaden, den die Sicherung
verhindern soll. Stattdessen: vollständigen Stand in eine `.json.tmp` schreiben, dann
`os.replace()`. Auf demselben Datenträger atomar; es existiert zu keinem Zeitpunkt eine halb
geschriebene Zieldatei. Fällt der Prozess während des Schreibens aus, bleibt die **vorige
vollständige** Fassung stehen.

Zusätzlich wird der Dateiname **vor** der Schleife festgelegt und ein leerer Anfangsstand
geschrieben — sonst gäbe es bis zum ersten Lauf keine Datei.

**Der Inhalt ist identisch zur bisherigen Fassung:** gleiche Schlüssel, gleiches Schema,
gleiche Reihenfolge. Es ändert sich, **wann** geschrieben wird, nicht **was**.

> **Ausdrücklich nicht enthalten:** keine automatische Wiederholung fehlgeschlagener Läufe,
> keine Resume-Entscheidungslogik, keine nachträgliche Änderung bereits persistierter Zeilen.
> `zeilen` wächst nur am Ende.

## Geprüft — deterministisch, ohne LLM und ohne Server

`app/eval/test_persistenz.py`, **22/22**, mit synthetischen Messzeilen:

| Prüfung | Ergebnis |
|---|---|
| Datei existiert **vor** dem ersten Lauf, Schema von Anfang an vollständig | ✔ |
| nach Lauf 1: genau **eine** Zeile, Position 1, Fall/Bedingung wie im Plan (`I05/A`) | ✔ |
| nach Lauf 40: genau 40 Zeilen, Positionen **lückenlos 1…40 in Reihenfolge** | ✔ |
| **Stand ist exakt das Präfix des eingefrorenen Plans** — nicht irgendeine Teilmenge | ✔ |
| keine doppelte Position | ✔ |
| **Abbruch:** Datei byte-identisch unverändert, N Zeilen intakt, valides JSON | ✔ |
| **keine automatische Fortsetzung** — 40 von 255, der Rest bleibt ungeschrieben | ✔ |
| Zeile 1 seit ihrem Lauf inhaltlich unverändert | ✔ |
| jede Zeile trägt **29** Felder, keine `.tmp`-Reste | ✔ |
| Seed und vollständige 255er-Reihenfolge in **jedem** Zwischenstand | ✔ |

**Gesamtstand: 302 Assertions über 11 Dateien, alle grün.**

## Invarianten nach der Änderung

| | |
|---|---|
| Messplan identisch mit dem archivierten | **True** |
| Plan-SHA | `4ed26d0c1baf247c5643e8360d42703e` |
| Seed | `20260821` |
| `MESSSCHEMA` | **29** Felder |
| Einzige geänderte messrelevante Datei | `app/eval/run_ba_abc_suite.py` |

## ██ G5 neu gesetzt — verbindlich ██

```
2026-08-21  13:24:29 +02:00        (= 2026-08-21T11:24:29Z)
```

**Der G5 von 13:13:41 (BA-061) ist überholt** — die Persistenz-Nachrüstung berührt den Runner.
**Unter ihm wurden keine H5-Messdaten erhoben**, also **keine Nachmessung**. BA-061 bleibt
unverändert stehen; damit ist es der **zweite** Freeze, den ein Vorbereitungsschritt vor der
ersten Datenerhebung überholt hat — der erste war BA-057 durch den Trockenlauf (BA-058).

**Eingefroren, unverändert gegenüber BA-061:** 17 Fälle (10 isoliert + 7 kombiniert) ·
29 Ground-Truth-Korrekturen · A/B/C je **N=5** · **255 Läufe** · Seed `20260821` ·
29-Feld-Schema · gemeinsame Kategorie-4-Auswertung · Pfadsemantik aus `pfadaufloesung.py` ·
`MEMORY_MODE=off` · `gpt-4.1` / `2025-01-01-preview` / `T=0.3` · Regelkarten `4d380884…` ·
Regelwerk A `a3c14bd1…` · GT `635a1e06…` / `24f45798…`. **`n` bleibt 17.**

**Neu allein:** der Schreibzeitpunkt des Rohdatensatzes.

- **Verifikation:** Trockenlauf nach der Änderung (255, Seed unverändert); Plan gegen das
  Archiv verglichen; `MESSSCHEMA` per Konstante gezählt; Gesamttestlauf; `git status` vor dem
  Commit.
- **Was NICHT funktioniert hat:**
  * **Ich hätte H5 beinahe gestartet, ohne den Schreibzeitpunkt zu prüfen.** Die Vorgabe
    „Rohdaten laufend sichern" stand im Auftrag; dass der Runner sie nicht erfüllt, fiel erst
    beim gezielten Nachsehen auf. Bei 255 Läufen wäre der Fehler teuer und **erst am Ende**
    sichtbar geworden.
  * **Zweiter Freeze, der vor der ersten Datenerhebung überholt wird.** Beide Male fand es ein
    Vorbereitungsschritt *nach* dem Setzen — Trockenlauf und Startvorbereitung. Das ist kein
    Zufall: **ein Freeze prüft sich erst, wenn man das Eingefrorene benutzen will.** Für die
    Arbeit ist das ein Befund über die Methode, kein Betriebsunfall.
- **Offen / nächstes:** **H5 — die Hauptmessung.** 255 Läufe, randomisiert, laufend gesichert.
  **Nicht gestartet.**

---

### [BA-063] 2026-08-22 — ██ H5: Hauptmessung vollständig erhoben ██ · technische Unterbrechung und Fortsetzung
- **Status:** done — **AP-H abgeschlossen. 255 von 255 Positionen. READY_FOR_AP-I.**
- **Kapitelbezug:** K5 *(Reproduzierbarkeit, Umgang mit technischen Ausfällen)*, K6, K7 *(die
  Messdaten selbst)*, K8 *(zwei Limitationen: Instrumentendefekt, geteilter Runnerstand)*
- **Literatur:** — *(keine der 16 Kernquellen behandelt den Umgang mit Infrastrukturausfällen
  während einer Messreihe. **Fundstelle fehlt** — das ist selbst ein Befund: die Frage, wie
  ein technischer Abbruch von einem fachlichen Nullergebnis zu trennen ist, wird in der von
  uns gesichteten Literatur nicht adressiert.)*
- **Changed files:** `app/eval/run_ba_abc_suite.py` *(rein additiv, +53/−0)*,
  `app/eval/verify_fortsetzung.py` *(neu)*, Dokumentation.
  **Keine Änderung an A/B/C, Messplan, Reihenfolge, Seed, 29-Feld-Schema, Kategorie-4-,
  Korrektheits- oder Pfadlogik, Ground Truth, Prompts, Regeln, Modell, Bewertung oder an der
  Ausführung eines einzelnen Runs.**

## Der Messdatensatz

| | |
|---|---|
| **Rohdaten** | `data/archive/ba-h4a/abc-mess-20260822T141347Z.json` |
| Positionen | **255**, lückenlos 1…255, **keine Duplikate** |
| Bedingungen | **A 85 · B 85 · C 85** |
| Zellen | **51** (17 Fälle × 3 Arme), **jede mit genau 5 Wiederholungen** |
| Reihenfolge | **Position für Position identisch mit dem eingefrorenen Plan**, Seed `20260821` |
| Technische Abbrüche im Enddatensatz | **0** |
| Schema | 29 Felder in **jeder** Zeile · `MEMORY_MODE=off` in **jeder** Zeile |
| Erhebungszeitraum | 2026-08-22 **11:30:46Z** … **16:17:31Z** |

> **`n` bleibt 17.** Die 255 Läufe sind Within-Case-Wiederholungen.

**Keine Auswertung in diesem Eintrag** — die Ergebnisverteilung ist nur als Integritätsbeleg
festgehalten, nicht als Befund: `fehlerfrei` 203 · `messinkonsistenz_kategorie4` 25 ·
`unsicher` 15 · `verbleibend:1` 11 · `verbleibend:2` 1. **Die Deutung gehört in AP-I.**

## Was unterbrochen hat — zwei getrennte Vorgänge

**1. Die Verbindung zur Test-VM brach um 13:47:15Z weg.** Ab Position 134 scheiterte jeder Lauf
an derselben Stelle:

```
ConnectionError: HTTPSConnectionPool(host='vm-t-weu-ccadmm-idp-test02.internal.idp.cca-dev.com',
port=443): /keycloak/realms/Esarom/protocol/openid-connect/token
```

22 Läufe fielen in **32 Sekunden**, weil jeder sofort an der Token-Beschaffung scheitert.
**Alle 22 wurden als `abgebrochen` erfasst**, mit `fehler_vorher = fehler_nachher = None` —
**kein Ausfall wurde als fachliches Ergebnis oder als „0 Fehler" verbucht.** Genau dafür war
die Unterscheidung vorgesehen. Sie hat gehalten.

**2. Danach starb der Runner-Prozess** beim Sichern von Position 155:
`PermissionError: [WinError 5]` in `os.replace(tmp, ziel)`.

**Datenlage nach dem Absturz — nichts verloren, nichts korrupt:** Zieldatei
`abc-mess-20260822T113043Z.json` valide mit 154 Zeilen, die `.tmp` valide mit 155, und die 154
sind **exakt** das Präfix der 155. Das ist der Ausfallmodus, für den die atomare Sicherung aus
**BA-062** gebaut wurde. **Ohne BA-062 wären 2 h 13 min Messung verloren gewesen.**

## Der Absturz ist ein Instrumentendefekt — und er ist reproduzierbar

Beim Gesamttestlauf fiel `test_persistenz.py` sporadisch aus: **2 von 12 Durchläufen** sterben
mit **demselben `WinError 5`** an **derselben Zeile** — im **Temp-Verzeichnis**, ohne
Messbetrieb, ohne lesenden Nebenprozess.

> **Das widerlegt die erste Hypothese.** Ich hatte den Fortschrittsmonitor als Hauptverdächtigen
> benannt, weil er die Zieldatei alle 120 s las. Der Testfall kommt **ohne jeden Leser** aus.
> Es ist ein Windows-Dateisperren-Effekt bei schnell aufeinanderfolgenden Ersetzungen —
> Defender-Echtzeitschutz ist aktiv und der plausibelste Halter des Handles, **nachgewiesen ist
> das nicht** (Ausnahmen sind ohne Adminrechte nicht einsehbar).

Größenordnung: 2 Fehler auf ~490 Ersetzungen im Test, 1 auf 155 im Messlauf — **0,4 bis 0,65 %
je Schreibvorgang**. `_schreibe_aggregat()` hat **keine Toleranz** gegen eine vorübergehende
Sperre.

**Nicht repariert** — der Runner stand unter Freeze, und die Regel lautet: bei Verdacht auf
einen Defekt des Messinstruments stoppen und berichten, nicht reparieren. Für die verbleibenden
122 Läufe lag das Risiko bei rund 40 %; es trat **nicht** ein.

## Die Fortsetzung — Entscheidung des Nutzers, nicht des Runners

Ein vollständiger Neulauf wäre ohne Codeeingriff möglich gewesen (Seed-Determinismus belegt).
**Der Nutzer entschied sich für die Fortsetzung ab Position 134** und gab die Bedingungen vor.
Vorher belegt: **kein bestehender CLI-Pfad kann den eingefrorenen Rest reproduzieren** —
`--only` filtert die Fallliste **vor** `messplan()`, das anschliessend neu mischt; der Rest
beginnt mit `K10/A/W2`, ein `--only`-Lauf mit `I05/A/W4`.

Zwei Schalter, **rein additiv (+53/−0)**, die **nur gemeinsam** wirken:

* `--ab-position N` — schneidet den **unverändert erzeugten** Plan auf Positionen ≥ N.
  **Keine zweite Mischung.**
* `--uebernahme PFAD` — übernimmt die Zeilen 1…N−1.

**Der Runner entscheidet nichts selbst:** kein Abbruch wird erkannt, nichts automatisch
wiederholt. Startposition und Quelle nennt der Mensch. Vier harte Abbrüche mit Exit 2, wenn
Seed oder Reihenfolge der Quelle abweichen, die Übernahme nicht lückenlos ist oder einen
technischen Abbruch enthält.

**Die 22 Abbruchzeilen wurden bewusst nicht übernommen** — sie sind keine Messergebnisse, und
ihre Positionen 134…155 wurden neu gefahren. Hätte man sie mitgenommen, stünden dort Duplikate.

## Verifikation

`app/eval/verify_fortsetzung.py` — **27/27**, führt nichts aus und schreibt nichts. Belegt
**vor** dem Start: Plan deterministisch reproduziert · archivierte Reihenfolge == reproduzierter
Plan (alle 255) · Fortsetzungsplan **exakt** Suffix 134…255 · **keine** Position aus 1…133 ·
Übernahme lückenlos 1…133, ohne Abbruch, 29 Felder, `MEMORY_MODE=off` · Übernahme inhaltlich
identisch mit der Quelle · **Projektion** des Enddatensatzes auf alle Abnahmekriterien.

**Nach dem Lauf** am tatsächlichen Datensatz nachgeprüft: alle Kriterien oben, dazu
**Zeilen 1…133 inhaltsgleich mit der Quelldatei** und **48 eingefrorene Messartefakte
byte-identisch** gegen `lock.json` (Messfälle 28, Regelkarten 14, Regelwerk 3, Kataloge 3).

**Gesamtstand: 307 Assertions über 12 Dateien, alle grün.**

## Ein geteilter Runnerstand — offen benannt

Die Zeilen **1…133** entstanden unter Runner-SHA `064c2271…`, die Zeilen **134…255** unter
`8ef70528…`. Das ist eine **Abweichung vom G5-Prinzip**: der Runner wurde geändert, **nachdem**
die Datenerhebung begonnen hatte — anders als bei BA-057/BA-061, die beide **vor** dem ersten
Messwert überholt wurden.

**Was dafür spricht, dass es die Messsemantik nicht berührt:** die Differenz ist rein additiv
(+53/−0, `git diff --stat`), betrifft ausschliesslich `argparse` und den Codeblock **vor** der
Ausführungsschleife, und lässt `_schreibe_aggregat()`, die Schleife, den Kindprozessaufruf und
jede Bewertungslogik unangetastet. Jeder Lauf ist ein **eigener Prozess** mit identischer
Umgebung und `MEMORY_MODE=off`, trägt also keinen Zustand aus vorherigen Läufen.

**Das ist eine Begründung, kein Beweis** — und gehört als solche in die Limitationen.

- **Verifikation:** Abbruchgründe aus den 22 Zeilen gelesen (alle identisch); Ziel- und
  `.tmp`-Datei elementweise verglichen; Erreichbarkeit der VM vor dem Neustart geprüft
  (DNS → 10.112.19.8, TCP 443 41 ms, Keycloak HTTP 200); `test_persistenz.py` 12× wiederholt,
  Traceback eingefangen; `git diff --stat` für den Umfang der Runner-Änderung;
  `verify_fortsetzung.py` vor **und** die Kriterienprüfung nach dem Lauf; Lock-Abgleich.
  Rohdaten: `abc-mess-20260822T141347Z.json` (Enddatensatz),
  `abc-mess-20260822T113043Z.json` + `.tmp` (Abbruchlauf, unverändert aufbewahrt),
  `abc-mess-20260821T115134Z.json` (erster Abbruchlauf, 10 Zeilen).
- **Was NICHT funktioniert hat:**
  * **Meine erste Ursachenhypothese zum Absturz war falsch.** Ich benannte meinen eigenen
    Fortschrittsmonitor als Hauptkandidaten, weil er die Zieldatei las. Der Testfall
    reproduziert den Fehler **ohne jeden Leser**. Ich hatte aus einer **Korrelation**
    (Monitor lief, Absturz kam) eine Ursache gemacht, ohne den Fall zu konstruieren, der sie
    ausschliesst. **Dass der Befund überhaupt auffiel, war Zufall** — ein sporadischer
    Testfehler im Routinelauf, den ich fast als Flackern abgetan hätte.
  * **Mein Fortschrittsmonitor für die Fortsetzung war blind.** Er suchte `[n/255]`; der
    geschnittene Plan druckt `[n/122]`. Er hätte über zwei Stunden **nichts** gemeldet und wäre
    stumm weitergelaufen. Aufgefallen ist es erst, als der Lauf fertig war. **Ein Monitor, der
    nie meldet, ist von einem stillen Lauf nicht unterscheidbar.**
  * **Ich habe die Assertionssumme falsch gezählt** (193 statt 307): Dateien mit mehreren
    Prüfblöcken wertete ich nur mit dem letzten Block. Der zweite Zählversuch scheiterte still
    an fehlendem `bc`. **Zweimal in Folge eine Kennzahl gemeldet, die ich nicht geprüft hatte.**
  * **Der Plan-SHA `4ed26d0c…` ist nicht nachrechenbar.** 24 Serialisierungen × 4 Hashverfahren,
    kein Treffer — die Berechnungsart entstand im Scratchpad und wurde nie übernommen. Dieselbe
    Lücke wie in BA-060, nur an anderer Stelle. Geprüft wurde stattdessen gegen die vollständige
    archivierte 255er-Reihenfolge, was strenger ist, aber **das Etikett im Protokoll bleibt
    unbelegt**. Gleiches gilt für die Sammelhashes der Messfallverzeichnisse — dort sind
    ersatzweise **alle 45 Einzeldateien** geprüft.
  * **Eine Defender-Ausnahme hätte vermutlich nichts genützt.** Ich hatte sie für
    `data/archive/ba-h4a/` vorgeschlagen; der Fehler tritt auch im Temp-Verzeichnis auf. Der
    Vorschlag war am falschen Ort angesetzt.
- **Offen / nächstes:** **AP-I — die Auswertung** (I1–I5) auf
  `abc-mess-20260822T141347Z.json`, danach AP-X. Der Instrumentendefekt in
  `_schreibe_aggregat()` bleibt **unrepariert und dokumentiert**; er ist für AP-I ohne Belang,
  wäre aber vor jeder Nachmessung zu beheben.

---

### [BA-064] 2026-08-22 — AP-I Integritätsaudit des finalen Datensatzes · die 25 Messinkonsistenzen aufgeklärt
- **Status:** done — **read-only.** Keine Ergebnisinterpretation, kein A/B/C-Vergleich.
- **Kapitelbezug:** K6 *(Messinstrument, Cross-Check als Kontrollmechanismus)*, K7 *(Bestand
  des Datensatzes)*, K8 *(Reichweitengrenze des GraphState als Messquelle)*
- **Literatur:** — *(Fundstelle fehlt: keine der 16 Kernquellen behandelt die Gegenprobe
  zweier Messquellen innerhalb eines Agentensystems.)*
- **Changed files:** `data/archive/ba-i-audit/{MANIFEST.json,snapshot-ids-255.csv}` *(neu,
  reine Auditartefakte)*, Dokumentation.
  **Nichts an `kategorie4.py`, `GraphState`, Runner, Bewertungsdefinition oder am
  Messdatensatz geändert.**

## Der finale Datensatz — festgeschrieben

```
data/archive/ba-h4a/abc-mess-20260822T141347Z.json
sha256  db867a26d1157c4af0d8202437bcd0ba503a40cb034cf2673b0a7c4c345cec79
bytes   1 177 017        Zeilen  255
```

Durch **zwei unabhängige Werkzeuge** bestätigt (`hashlib`, `certutil`). 255 `snapshot_id`,
**alle eindeutig**, **alle Verzeichnisse auf Platte vorhanden** — Liste in
`snapshot-ids-255.csv`. **Ausdrücklich nicht Teil von AP-I** und im Manifest so benannt: die
beiden Abbruchläufe, die `.tmp` und die Pilotläufe.

## Die 25 Messinkonsistenzen — die Hypothese trifft zu, 25 von 25

**Alle 25 liegen in Bedingung C**, betreffen **genau fünf Fälle** (K04, K05, K08, K09, K10) und
dort **jede der fünf Wiederholungen** — 5 × 5, kein Streuverhalten. Abweichend ist in **allen 25
ausschliesslich `errors_resolved`**; `errors_remaining`, `errors_new` und `new_error_types`
stimmen überall überein.

| | gemeinsam | GraphState |
|---|---|---|
| `errors_resolved` | 2 (10 Läufe) bzw. 3 (15 Läufe) | **immer 1** |

**Vier Identitäten, über alle 25 geprüft:** `errors_resolved` (gemeinsam) `== fehler_vorher` ·
`fehler_nachher == 0` · GraphState-Wert `== 1` · **Differenz `== iterationen − 1`**.

**Ursache, am Code belegt — nicht aus dem Muster geschlossen:**

* **Gemeinsamer Evaluator** — der Runner sichert `vorher_meldungen` **einmal, vor**
  `execute_pipeline()` (`run_ba_abc_suite.py:269`, mit dem ausdrücklichen Kommentar, sonst
  liefere das Nachladen den Nach-Zustand). `nachher_meldungen` wird nach der abgeschlossenen
  Re-Validierung geladen. → **Initial → Final des Gesamtlaufs.**
* **GraphState** — Knoten 7 lädt `vorher_meldungen` **zu Beginn jeder Ausführung**
  (`apply_revalidate.py:78`), und die Re-Validierung der vorigen Iteration hat **dieselbe
  Datei** bereits überschrieben. `state["applied"] = {...}` (`:197`) ist eine schlichte
  Zuweisung je Iteration. → Der persistierte Wert ist **Vorher → Nachher der letzten
  Iteration**.

Der Graph behebt **einen** Fehler je Iteration; darum `iterationen == fehler_vorher` und darum
der GraphState-Wert 1.

**Negativkontrolle — die Regel ist schärfer als „Iterationen > 1":** acht C-Läufe mit
Iterationen > 1 sind **kein** Mismatch. K06 (5 Läufe, 5 Iterationen): gemeinsam 0, GraphState 0.
I10 (3 Läufe, 2 Iterationen): gemeinsam 1, GraphState 1. In beiden Gruppen fällt der
Gesamtwert mit dem Beitrag der letzten Iteration zusammen. Die Regel lautet also:

> **Mismatch ⟺ vor der letzten Iteration wurde mindestens ein Fehler behoben.**

**Keine weiteren Ursachen.** 25 von 25 erklärt, restlose Klassifikation, kein Rest.

## Ein zweiter, kleinerer Befund: vier C-Läufe ohne `graph_state.json`

`graph_state` liegt bei A und B erwartungsgemäss nie vor, bei C in **81 von 85** Läufen — es
fehlt bei **K07, Wiederholungen 2–5** (Positionen 82, 85, 98, 140). Für sie ist der Cross-Check
`durchgefuehrt: false`. Der ausgegebene Grund lautet dort **`"kein graph_state.json (A/B)"`** —
der Text ist ein **fest verdrahtetes Literal** (`kategorie4.py`) und behauptet für C-Läufe
fälschlich die Bedingung A/B. Kosmetisch für die Messung, **irreführend für den Leser der
Rohdaten**: wer die Provenienz liest, hält diese vier für A/B-Läufe. **Nicht geändert** —
Bewertungscode ist eingefroren.

## Aufgabe 3: Marker oder Ausschlusskriterium?

**Es ist ausschliesslich ein QC-/Cross-Check-Marker.** Im eingefrorenen Design (BA-051/052,
Protokoll ab Zeile 5417) wörtlich festgelegt:

* „**Die gemeinsame Berechnung ist die primäre Messung.** Der `GraphState` ist die Gegenprobe."
* „Bei Abweichung wird **nichts überschrieben** und **keiner der beiden Werte gewinnt**."
* Das Präfix bedeutet „ein **technisch abgeschlossener** Lauf, der hinsichtlich **dieser einen
  Messgrösse** nicht regulär auswertbar ist" — **kein** Pipeline-Abbruch, **kein**
  `stop_uncertain`.
* Das eigentliche Ergebnis bleibt hinter dem Trennstrich erhalten, „damit ein technisch
  erfolgreicher Korrekturlauf nicht fälschlich als Fehlschlag in die Auswertung geht".

Der Runner setzt es genau so um (`:355`): `ergebnis = f"messinkonsistenz_kategorie4|{ergebnis}"`
— **Präfix, keine Ersetzung**. Alle 25 tragen dahinter `fehlerfrei`.

**Eine Ausschlussregel existiert nicht.** Volltextsuche über `BA_PROJECT_LOG.md` und
`BA_ARBEITSPAKETE.md` nach Ausschluss-/Verwerfungsformulierungen im Zusammenhang mit
Kategorie 4 oder dem Cross-Check: **keine Fundstelle**. Ein Ausschluss wäre daher eine **neue,
nachträgliche Festlegung** und nach harter Regel 5 als **Nachmessung** zu kennzeichnen.

**Verbindliche Primärquelle für Kategorie 4:** die gemeinsame Vorher-/Nachher-Berechnung für
A, B und C aus `kategorie4.py`, in jeder der 255 Zeilen als
`provenienz.kategorie4_basis = "validierungsmeldungen_vorher_nachher"` mitgeführt. Im G5-Stand
(BA-061, Log 6479) so eingefroren: „für A, B und C aus **derselben Funktion**; `GraphState` bei
C nur Cross-Check". **Die Erwartung des Auftrags bestätigt sich.**

- **Verifikation:** SHA-256 doppelt (`hashlib`, `certutil`); `snapshot_id`-Eindeutigkeit und
  Existenz aller 255 Verzeichnisse; Tabelle aller 25 Mismatches aus den Rohdaten; vier
  Identitäten über alle 25; Negativkontrolle über **alle 85** C-Läufe nach Iterationszahl;
  `kategorie4.py` (`kategorie4`, `cross_check_graphstate`), `run_ba_abc_suite.py:269/326-355`,
  `apply_revalidate.py:78/197` gelesen; Volltextsuche nach einer Ausschlussregel.
- **Was NICHT funktioniert hat:**
  * **„Mismatch ⟺ Iterationen > 1" wäre falsch gewesen.** Genau das legte die erste Tabelle
    nahe — bis die Negativkontrolle acht Gegenbeispiele lieferte. Hätte ich nur die 25
    betrachtet und nicht die übrigen 60 C-Läufe, stünde eine überdehnte Regel im Bericht.
    **Dritter Fall dieser Sitzung, in dem ein Muster ohne Gegenprobe zur Ursache erklärt worden
    wäre** (nach der Absturzhypothese in BA-063).
  * **Der Grundtext `"kein graph_state.json (A/B)"` wäre beinahe unbemerkt geblieben.** Er
    steht in vier C-Zeilen und behauptet dort die falsche Bedingung. Aufgefallen ist er nur,
    weil ich die `graph_state`-Verteilung je Bedingung ausgezählt habe, statt sie
    vorauszusetzen.
- **Offen / nächstes:** **I1** — Halluzinationen kategorisieren. Der Datensatz ist auditiert
  und unverändert; die 25 Messinkonsistenzen sind vollständig aufgeklärt und betreffen **nur**
  die Messgrösse `errors_resolved` in C.
