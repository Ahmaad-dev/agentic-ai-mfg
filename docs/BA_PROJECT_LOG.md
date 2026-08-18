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

Beim Verfassen eines Kapitels hier beginnen, nicht oben im Protokoll.
**Bei jedem neuen Eintrag mitpflegen.**

| Kapitel der Arbeit | Einträge |
|---|---|
| **K3** Das bestehende System | BA-004 |
| **K4** Konzeption der Graph-Architektur | BA-005, BA-006, **BA-009** |
| **K5** Forschungsdesign und Methodik | BA-004, BA-005, BA-006, BA-007, BA-008, BA-009, BA-010 |
| **K6** Evaluierungsdesign | BA-004, BA-007 |
| **K7** Ergebnisse | *(noch keine — beginnt mit dem Baseline-Lauf)* |
| **K8** Diskussion und Limitationen | BA-004, BA-005, BA-006, BA-007, BA-008, BA-009 |
| **K9** Fazit und Ausblick | BA-006, BA-009 |
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
