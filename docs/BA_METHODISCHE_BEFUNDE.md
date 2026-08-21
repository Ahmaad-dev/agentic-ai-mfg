# Methodische Befunde der Vorbereitungsphase

**Einstieg zum Schreiben von K3, K5, K6 und K8.** Grundlage: BA-035 bis BA-060.

> **Wozu dieses Dokument.** Das Protokoll ist chronologisch — die richtige Ordnung für ein
> Protokoll, die falsche für eine Arbeit. Hier stehen die Befunde **nach Kapitel sortiert**,
> jeder mit seinem Beleg. Es ersetzt das Protokoll nicht und wiederholt es nicht; es zeigt auf
> die Einträge, in denen der Befund entstanden ist.
>
> **Es enthält keine Messergebnisse.** Die Hauptmessung (H5) hat nicht stattgefunden. Alles
> hier stammt aus Pilotläufen, statischer Analyse und Instrumentenprüfung.

---

## Die drei Befunde, die für die Arbeit am meisten wert sind

Wenn aus diesem Dokument nur drei Dinge in die Arbeit wandern, dann diese.

### 1. Ein falscher Wert ist nicht dasselbe wie eine Halluzination

**P01 und P03 schlugen beide `1.049` vor, Ground Truth war `1.063` bzw. `1.1`.** Der
naheliegende Schluss — fachliche Halluzination — ist falsch.

Der Wert wird **deterministisch in Python berechnet**: `identify_snapshot.py:553-560` bildet
über `similar_items` (90 Artikel derselben Abteilung) `sorted(werte)[len//2]` und legt das
Ergebnis als `similar_items_stats.relDensityMin.median` in den Kontext. Das Modell hat ihn
**abgelesen und korrekt zitiert**.

> **Für die Messvorschrift folgt daraus:** Ein Korrekturwert, der gegen die Ground Truth falsch,
> aber durch die **vorgelegte Evidenz gestützt** ist, ist ein Befund über die
> **Evidenzaufbereitung** — nicht über die Wahrhaftigkeit des Modells. Ein Halluzinationsmass,
> das ihn mitzählt, misst einen Defekt des Instruments.

Und: die Ground Truth (`1.063`, `1.1`) liegt **im Kollektiv**. Das Kollektiv ist also nicht zu
breit — ein Median über 90 Artikel kann einen Einzelwert nur zufällig treffen. Das ist eine
Eigenschaft der Domänenheuristik, kein Modellfehler.

**→ K3** (Beschreibung des Bestandssystems), **K6** (Kategorie 1), **K8**.
Beleg: **BA-046**, `app/eval/kategorien.py`, `test_kategorien_instrumente.py`.

### 2. Zwei von vier Messkategorien zeigten zuerst auf das Instrument

Nicht einmal, sondern **zweimal hintereinander**:

* **Kategorie 1** hätte `1.049` als Halluzination gezählt — siehe oben.
* **Kategorie 2** registrierte in *jedem* Graph-Durchgang einen Schemaverstoss. Tatsächlich
  prüfte Knoten 6 den **inneren** Vorschlag gegen das **Hüllen**-Schema; es fehlten fünf
  Pflichtfelder, die das Modell nie hätte liefern sollen.

Das ist die `value_grounded`-Falle aus PT4 in zwei Ausprägungen: gemessen wurde ein Defekt des
Messinstruments, nicht des Systems.

**Konsequenz, umgesetzt:** Die vier Kategorien liegen seither als **prüfbare Klassifikatoren**
vor (`app/eval/kategorien.py`), je mit Definition, Ground Truth, autoritativer Quelle,
Positiv-, Negativ- **und Confounderfall** — und mit **drei** Ausgängen statt zwei:
`ja` / `nein` / **`nicht_bestimmbar`**.

> **`nicht_bestimmbar` ist ein Ergebnis, kein Ausweichen.** Es als „nein" zu zählen wäre
> dasselbe falsche Grün, das dieses Projekt dreimal getroffen hat: fehlende Evidenz als
> Unbedenklichkeit lesen.

**→ K6** (Evaluierungsdesign), **K8**.
Beleg: **BA-046, BA-047, BA-049**; `test_kategorien_instrumente.py` (32), `test_kategorie4_integration.py` (19).

### 3. Die Fehlerinjektion hat eine benennbare Reichweitengrenze

Drei Prozesspfade liessen sich **nicht** als Testfall konstruieren — und die Gründe sind
verschieden, was den Punkt erst interessant macht:

| Pfad | Warum nicht | Status |
|---|---|---|
| **Kontextsuche ohne Treffer** | Eine Injektion schreibt den Wert **in** den Snapshot; Knoten 2 sucht danach und findet ihn zwangsläufig. Null Treffer sind so nicht herstellbar. | im aktuellen Workflow **nicht erreichbar** |
| **Fuzzy-Fallback** | Greift nur bei null exakten Treffern — aus demselben Grund unerreichbar. Die **Fähigkeit existiert** und ist auf Knotenebene nachgewiesen. | dito |
| **Mehrdeutiger Grenzfall** | Drei Entwürfe, drei Ursachen: min/max wird gar nicht validiert · es gibt nur zwei Vergleichskollektive (91 und 331 Artikel) · die Lücke in der ID-Sequenz macht die fehlende ID eindeutig. | Pfad **real belegt**, Fall nicht konstruierbar |

Der zweite Punkt ist schärfer, als er zuerst klang: Knoten 2 **extrahiert** den Suchwert aus
der Validatormeldung, und die beanstandet einen Wert, der im Snapshot steht. Das gilt für alle
drei Suchmodi. **Nulltreffer und Fuzzy sind damit im heutigen regulären Ablauf nicht
erreichbar** — auf Knotenebene aber implementiert und getestet.

> Ausdrücklich offen: andere oder künftige Aufrufer, eine geänderte Validatormenge oder eine
> **Fehlklassifikation** (real beobachtet in P10 D5) können die Pfade erreichen. „Toter Code"
> wäre zu pauschal.

**→ K3** (Bestandssystem), **K8** (Limitationen).
Beleg: **BA-048, BA-049**; `test_kontextsuche_pfade.py` (15).

---

## Befunde nach Kapitel

### K3 — Das bestehende System

| Befund | Beleg |
|---|---|
| `similar_items` + deterministischer Median als Domänenheuristik; der Korrekturwert entsteht **im Code**, nicht im Modell | BA-046 |
| `sorted[len//2]` heisst `median`, ist bei geradem n aber der **obere** Median (1.049 statt 1.0485). **Nicht geändert** — gemeinsame Runtime, eine Änderung verschöbe A, B und C gleichzeitig | BA-046 |
| Fuzzy-Fallback ist implementiert, im Korrekturworkflow aber regulär nicht erreichbar | BA-049 |
| Die Kartenauswahl von Knoten 2 ist **nichtdeterministisch** — P01 erhielt `negative-dichtewerte.md`, P03 bei gleichem Tag nicht | BA-046 |

### K5 — Forschungsdesign und Methodik

| Befund | Beleg |
|---|---|
| **N = 5 Wiederholungen** je Fall — die Zahl war **nirgends verbindlich** festgelegt (Masterplan und AP nannten „3–5×"); die einzige konkrete `5` stand in einem Warnkasten *gegen* n=85 | BA-055 |
| **Alle drei Arme** werden wiederholt. Mit einem einmal laufenden B liesse sich nur A → C betrachten; **B → C** trennt Kartenform von Orchestrierung | BA-056 |
| **255 Läufe**, randomisiert, Seed `20260821` **vor** der Messung dokumentiert; Seed **und** erzeugte Reihenfolge gehen in die Rohdaten | BA-055 |
| `n` bleibt **17**. Die Wiederholungen sind Within-Case-Stabilität | BA-055, BA-056 |
| Zielpfade gelten als identisch, wenn sie **deterministisch auf dasselbe JSON-Element auflösen** — vor der Messung festgelegt | BA-059 |
| Mehrdeutiger Grenzfall nicht konstruierbar; der Pfad selbst ist belegt | BA-049 |

### K6 — Evaluierungsdesign

| Befund | Beleg |
|---|---|
| Vier Kategorien als **prüfbare Klassifikatoren**, drei Ausgänge, je Confounderfall | BA-047, BA-049 |
| Kategorie 2 entscheidet über **Provenienz** (`k5_response_valide`), nicht über die Feldsignatur | BA-048 |
| Kategorie 4 aus **einer** Funktion für A, B und C; `GraphState` bei C nur Cross-Check | BA-052 |
| Kategorie 4: **Messinstrument validiert**, realer Post-Fix-Positivfall steht aus | BA-052, BA-049 |
| Der Messkatalog umfasst **17** Fälle: 10 isolierte + 7 kombinierte. `snapshot-error-01…03` sind redundant zu I01–I03 | BA-058 |
| **29** erwartete Korrekturen — Mehrfach-GT war schon immer da (I08) | BA-058 |

### K7 — Ergebnisse

Noch keine Messwerte. Verwendbar als **Durchstichmaterial**: der A/B/C-Pilotlauf auf P01
(alle drei `fehlerfrei`, alle drei `1.049`, Ground Truth `1.063`) zeigt exemplarisch, dass
`ergebnis="fehlerfrei"` **nur den technischen Abschluss** bezeichnet — nicht
Ground-Truth-Korrektheit. **BA-051, BA-052.**

### K8 — Diskussion und Limitationen

| Limitation | Wirkungsrichtung |
|---|---|
| Zwei Suchpfade im aktuellen Workflow nicht erreichbar | Eigenschaft des Ablaufs, nicht Mangel der Pilotphase |
| Mehrdeutiger Grenzfall nicht konstruiert | Grenze der Fallkonstruktion, keine Fähigkeitslücke |
| Kategorie 4 ohne realen Post-Fix-Positivfall | Instrument validiert, Beobachtung offen |
| Pilotläufe sind **Einzelläufe** | Streuungsaussagen erst aus H5 |
| Zwei Pfadnotationen in den GT-Katalogen | **nicht** normalisiert; aufgelöst statt umgeschrieben |
| Kartenauswahl von Knoten 2 nichtdeterministisch | für UF3 relevant |

---

## Was dieses Projekt über sein eigenes Arbeiten gelernt hat

Diese Muster sind für Kapitel 8 mehr wert als jedes gelungene Zwischenergebnis — sie sind
später nicht rekonstruierbar.

**Fehlende Evidenz wurde wiederholt als Unbedenklichkeit gelesen.** Der K8-Entscheidungsvertrag
hing an `bool(applied)`; fehlte der Nachweis ganz, fielen *alle* Sicherheitszweige aus und der
Lauf endete auf `continue`. Behoben durch **Umkehr der Beweislast**: nur positiv belegte
Verarbeitung führt zu einem positiven Ergebnis (**BA-044**).

**Ein grüner Nachbarfall belegt den Nachbarn nicht.** Regression 1 war grün, weil dort Knoten 7
durchlief. Regression 2 traf den Fall, in dem er gar nichts hinterlässt — und fand drei
Defekte (**BA-044**).

**Sechsmal wurde am falschen Merkmal gemessen.** Exit-Codes über Textvorkommen statt AST
(BA-025) · Pipeline-Rückgabe statt Artefakt (BA-033) · falsche Digest-Ebene (BA-040) · falscher
Schlüsselname (BA-042) · `"tag|hash"` statt `{hash: tag}` (BA-052) · `generate_audit_report` im
Docstring als Aufruf gezählt (BA-053). Gegenmittel: `graph/trace_keys.py` als zentrale Registry,
und **AST statt Textsuche**.

**Zeitstempel sind kein Änderungsnachweis.** „0 Promptänderungen" liess sich über `mtime`
*nicht* belegen — drei Runtime-Dateien tragen Stempel aus dem Pilotzeitraum. Der Nachweis
gelingt nur über **BA-Marker im Inhalt** (**BA-050**).

**Eine Attrappe, die alles akzeptiert, prüft nichts.** Das Test-`voll_huelle()` war monatelang
schema-**ungültig**; gemerkt hat es niemand, weil der Prüfer gestubbt war. Aufgefallen erst, als
eine Regression den **echten** Validator benutzte (**BA-047**).

**Jeder Fix braucht eine Negativkontrolle.** Zu jedem Fix wurde der Defekt zurückgebaut und
geprüft, dass die Regression anschlägt. Beim K8-Fix war die erste Kontrolle **zu schwach** —
sie ersetzte nur eine Variable, und die neuen Vergleiche fingen den Fall unabhängig ab. Erst
der wörtliche Rückbau reproduzierte ihn (**BA-045**).

**Vier Reissbrett-Entwürfe in Folge haben danebengetroffen.** P06, P07, P09, P11 — jedes Mal
war *ein Teil* der Information geprüft und der Rest übersehen: Validatorregeln,
Kollektivgrössen, ID-Sequenz. Mehr Fleiss hilft dagegen nicht; **Prüfung an den echten Daten
vor dem Bau** schon.

**Der Dry-Run hat sich bezahlt gemacht.** Er fand vor der ersten Datenerhebung, dass der
Messkatalog nur 10 statt 17 Fälle lud — **41 % zu wenig**, und ausgerechnet ohne die
Mehrfehlerfälle, bei denen der Effekt primär erwartet wird (**BA-058**).

---

## Werkzeuge, die den Belegen zugrunde liegen

Alle unter `app/eval/`, alle wiederholbar, alle in der Wurzel-`.venv`:

| Werkzeug | Wofür |
|---|---|
| `verify_ground_truth.py` | Deep-Diff: belegt die Ground Truth **unabhängig** vom Generator |
| `preflight_messrunner.py` | 35 Kriterien am Messrunner, statisch und an Pilotnachweisen |
| `g5a_messstand_festhalten.py` | Lock-Artefakt: Commit, Tree, `pip freeze`, Metadaten, Modell, Hashes |
| `pfadaufloesung.py` | löst beide Pfadnotationen auf denselben kanonischen Pfad auf |
| `kategorien.py`, `kategorie4.py` | die vier Messkategorien als Klassifikatoren |
| `trace_keys.py` *(unter `graph/`)* | zentrale Registry der Trace-Schlüssel |
| 10 Testdateien | **280 Assertions**, alle grün |

> **280 Assertions sind keine 280 Experimente.** Sie verteilen sich auf 10 Dateien und decken
> denselben Gegenstand teils mehrfach ab. Als Fallzahl für eine empirische Aussage taugen sie
> nicht — sie belegen, dass die Verträge des Messinstruments halten.
