# Der Konfidenz-Score — wie die Zahl zustande kommt

Referenz zu der Prozentzahl, die im Review Board neben jedem Korrekturvorschlag steht.
Code: `app/tools/smart-planning/runtime/generate_correction_llm.py`,
Funktion `compute_confidence_score` (Formelstand `v4`).

> **Wofür diese Zahl da ist.** Sie soll einem Prüfer sagen, wie genau er hinschauen muss —
> nicht, ob er zustimmen soll. Eine hohe Konfidenz ersetzt keine Entscheidung. Der Kern von
> PT4 ist, dass das System vorschlägt und wartet.

---

## Die Formel

```
Konfidenz = 0.5 · llm_confidence     Selbsteinschätzung des Modells   (0…1)
          + 0.3 · value_grounded     Wert aus den Daten belegbar?     (0 oder 1)
          + 0.2 · memory_support     Rückhalt aus früheren Fällen     (0 / 0.5 / 1)

danach:  ist memory_support == 1.0, gilt mindestens 0.9
```

Sonderfall: bei `action == "manual_intervention_required"` ist der Score **0.0** — das System
sagt damit ausdrücklich, dass es diesen Fall nicht selbst lösen kann.

---

## Woher jedes Signal stammt

Die drei Signale kommen aus **drei verschiedenen Quellen**. Das ist der Kern: sie sagen
absichtlich nicht dasselbe, und deshalb stehen sie im Review Board auch als getrennte Kästen
statt als eine Zahl.

| Signal | Quelle | Aussage |
|---|---|---|
| `llm_confidence` | Das Modell selbst (Teil seiner Antwort) | „Wie sicher bin ich mir?" |
| `value_grounded` | **Der Snapshot** — `snapshot-data.json`, also die Produktionsdaten, die gerade korrigiert werden | „Solche Werte kommen in diesen Daten vor" |
| `memory_support` | **Die Datenbank** — Tabelle `memory_items` mit früheren menschlichen Entscheidungen | „Ein Mensch hat genau das hier schon entschieden" |

Nur das erste Signal stammt aus dem Modell. Die anderen beiden sind **deterministisch**: bei
gleichem Snapshot und gleicher Datenbank liefern sie immer dasselbe Ergebnis, ohne dass ein
LLM beteiligt wäre. Genau deshalb dürfen sie die Selbsteinschätzung korrigieren.

---

## Die drei Signale

### 1. `llm_confidence` — die Selbsteinschätzung (Gewicht 0.5)

Was das Modell selbst über seinen Vorschlag sagt. **Bewusst nur die Hälfte**, denn dieses
Signal ist nicht zuverlässig: gemessen hat das Modell eine ID, die es **erfunden** hatte, mit
„Band A / 0.9" bewertet — ausgerechnet in dem Fall, in dem ein Mensch es überstimmen musste.
Eine Selbsteinschätzung kann nicht zwischen „das habe ich in den Daten gelesen" und „das habe
ich mir ausgedacht" unterscheiden.

### 2. `value_grounded` — ist der Wert belegbar? (Gewicht 0.3)

Genau die Unterscheidung, die dem Modell fehlt — deterministisch geprüft, ohne LLM.

> **Woher die Information stammt:** aus dem **Snapshot selbst** (`snapshot-data.json`), also
> aus den Produktionsdaten, die gerade korrigiert werden sollen. NICHT aus der Datenbank und
> NICHT vom Modell. Die Prüfung durchsucht das betroffene Array und vergleicht Werte — sie
> ist reproduzierbar und würde bei gleichem Snapshot immer dasselbe Ergebnis liefern.
> (Zum Vergleich: `memory_support` kommt aus der Tabelle `memory_items`, also aus früheren
> menschlichen Entscheidungen. Zwei verschiedene Quellen, zwei verschiedene Aussagen.)

**Klassenabhängig**, denn die richtige Frage hängt vom Feldtyp ab:

| Feldklasse | Geprüfte Frage |
|---|---|
| Identität (z. B. `demandId`) | Ist der Wert im Array **eindeutig** und folgt er der dort üblichen Form? |
| Referenz (z. B. `articleId`) | Existiert das referenzierte Objekt? |
| Wert (z. B. `relDensityMin`) | Steht derselbe Wert bereits auf demselben Feld eines vergleichbaren Objekts? |
| Neues Objekt | Identitäts- und Referenzprüfung auf das neue Objekt angewandt |

Warum nicht eine Frage für alle? Weil „steht der Wert schon in den Daten?" für ein
**Identitätsfeld genau verkehrt herum** ist: eine neue eindeutige ID darf gerade NICHT
existieren — täte sie es, wäre sie ein Duplikat und damit falsch. Eine Einheitsfrage hätte
also ausgerechnet die richtigen ID-Vorschläge bestraft (siehe „Entwicklung der Formel", v3).

Konservativ: Was nicht überprüfbar ist, zählt als **nicht belegt**. Ein unbelegbarer Wert
kann den Score also nie aufblähen.

#### Am echten Beispiel

Für `articles[0].relDensityMin` (ein WERT-Feld) durchsucht die Prüfung alle 422 Artikel des
Snapshots und fragt: trägt ein anderer Artikel diesen Wert bereits auf demselben Feld?

| Vorschlag | Ergebnis | Begründung der Prüfung |
|---|---|---|
| `1.017` | **0.0** | „Wert nicht in den Daten auffindbar — konstruiert/erfunden (kein `articles[*].relDensityMin` mit diesem Wert)" |
| `1.055` | **1.0** | „Wert existiert bereits in `articles[1].relDensityMin` — aus vergleichbarem Datensatz übernommen" |

#### Was „belegt" NICHT bedeutet

Es heißt: *ein vergleichbarer Datensatz trägt diesen Wert bereits*. Es heißt **nicht**, dass
der Wert für DIESES Objekt richtig ist. Beide Richtungen kommen vor:

- **Belegt und trotzdem falsch:** `1.055` stammt von einem anderen Artikel. Die Prüfung sagt
  „so ein Wert ist in diesen Daten üblich" — nicht „das ist die Dichte dieses Artikels".
- **Nicht belegt und trotzdem richtig:** `1.017` ist genau der Wert, den ein Mensch für
  diesen Artikel bestätigt hat. Er ist einmalig, also findet ihn die Prüfung nirgends.

Deshalb ist `value_grounded` ein **Plausibilitätssignal, kein Korrektheitsnachweis** — und
deshalb wiegt es nur 0.3 und wird von einer menschlichen Bestätigung überstimmt.

### 3. `memory_support` — Rückhalt aus früheren Entscheidungen (Gewicht 0.2)

> **Woher die Information stammt:** aus der Tabelle **`memory_items`** in der Datenbank. Dort
> landet nach jeder menschlichen Entscheidung ein Fall — welcher Wert vorgeschlagen, welcher
> angewendet wurde, für welches Objekt und mit welcher Begründung. Das Gedächtnis wächst also
> ausschliesslich durch geprüfte Entscheidungen, nie durch die KI selbst.

| Stufe | Bedeutung |
|---|---|
| `0.0` | Kein vergleichbarer Fall — **oder** ein negativer Präzedenzfall: genau dieser Wert wurde für dieses Objekt schon einmal verworfen |
| `0.5` | Es gibt Präzedenzfälle für diese **Fehlerart**, aber keinen für dieses Objekt |
| `1.0` | Ein Mensch hat **genau diesen Wert** für **dieses Objekt** bestätigt |

Die Unterscheidung „selbes Objekt" ist tragend. Eine Dichte ist artikelspezifisch — ein
bestätigter Wert von Artikel A sagt über Artikel B nichts aus. Ohne diese Trennung würde das
Gedächtnis Fehler **erzeugen** statt verhindern.

---

## Die Untergrenze bei 0.9 — und warum sie sein muss

```python
if memory_support >= 1.0:
    score = max(score, 0.9)
```

Ohne sie war die Konfidenz für den sichersten Fall **verkehrt herum**.

Bei einem zerstörten Wert — Dichte auf `0` gesetzt — ist `value_grounded` **zwangsläufig 0**:
der richtige Wert steht ja gerade nicht mehr im Snapshot. Ein Wert, den ein Mensch
ausdrücklich bestätigt hat, kam damit auf `0.675` und lag **unter** einer bloß plausiblen
Schätzung mit `0.75`. Die Zahl war also am niedrigsten, wo die Sicherheit am größten war.

Eine ausdrückliche menschliche Bestätigung für dasselbe Objekt ist das stärkste Signal, das
dieses System kennt — stärker als Datenbeleg und stärker als die Selbsteinschätzung.

---

## Durchgerechnetes Beispiel

`articles[0].relDensityMin`, Vorschlag `1.017` (Snapshot `27414fc9-…`):

| Signal | Wert | Beitrag |
|---|---|---|
| `llm_confidence` | 0.9 | 0.45 |
| `value_grounded` | **0.0** | 0.00 |
| `memory_support` | **1.0** | 0.20 |
| | Summe | **0.65** |
| | Untergrenze greift | **0.90** |

**Die angezeigten 90 % stammen vollständig aus der Untergrenze**, nicht aus der Summe. Die
gewichtete Rechnung allein ergäbe 65 %.

### Was dieselbe Selbsteinschätzung sonst ergäbe

| Lage | Konfidenz |
|---|---|
| Kein Präzedenzfall, Wert nicht belegt | 45 % |
| Präzedenz für die Fehlerart, anderes Objekt | 55 % |
| Wert belegt, kein Gedächtnis | 75 % |
| Mensch hat genau diesen Wert bestätigt | **90 %** |
| KI unsicher (0.2), aber Mensch hat bestätigt | **90 %** |

Die letzte Zeile zeigt die Wirkung der Untergrenze am deutlichsten.

---

## Wie ein Prüfer die Zahl lesen sollte

**90 % ist nicht gleich 90 %.** Entscheidend ist, woher der Wert kommt — und genau dafür
stehen die Kästen in der Seitenspalte:

- **90 % mit „Wert ist belegt"** → die Zahl steht so in den Daten, das Risiko ist gering.
- **90 % mit „Wert ist NICHT belegt" + „Ein Mensch hat bestätigt"** → die Zahl stammt aus dem
  Gedächtnis. Vertrauenswürdig, **wenn** die frühere Entscheidung richtig war. Der Blick
  gehört auf die Präzedenzfälle darunter, nicht auf die Prozentzahl.
- **Niedrige Konfidenz** heißt nicht „falsch", sondern „nicht belegbar" — häufig genau die
  Fälle, in denen menschliches Fachwissen gebraucht wird.

Ein zerstörter Wert erzeugt IMMER `value_grounded = 0`. Der gelbe Kasten „Wert ist NICHT
belegt" ist dort bauartbedingt und kein Alarmzeichen.

---

## Entwicklung der Formel

| Stand | Änderung | Grund |
|---|---|---|
| v0 | `0.5·llm + 0.3·schema_valid + 0.2·memory` | Ursprung laut PT4-Plan |
| v1 | `schema_valid` → `value_grounded` | `schema_valid` ist **immer 1** (der Vorschlag wird direkt nach dem Bau gegen das Pydantic-Modell geprüft). Der Term war tautologisch, der Score kollabierte auf ~0.775 in 7 von 8 gemessenen Vorschlägen. |
| v2 | `memory_support` abgestuft 0 / 0.5 / 1.0 | Vorher hart 0 und damit wirkungslos |
| v3 | `value_grounded` klassenabhängig | Die alte Einheitsfrage war für Identitätsfelder **rückwärts**: eine neue eindeutige ID darf gerade NICHT in den Daten existieren. Gemessen: zwei exakt richtige ID-Vorschläge bekamen 0.0, ein falscher Dichtewert 1.0 — das Signal war gegenläufig zur Korrektheit. |
| v4 | Untergrenze 0.9 bei `memory_support == 1.0` | Siehe oben: die Konfidenz war für den sichersten Fall verkehrt herum. |

Jeder Vorschlag speichert seinen Formelstand im Feld `formula_version`. Alte Vorschläge sind
damit erkennbar und werden nicht stillschweigend mit neuen vermischt.

**Was das Dashboard daraus macht (Stand 13.08.2026):** Die Kalibrierungskurve — die einzige
Darstellung, die eine Behauptung über die *Vorhersagekraft* der Konfidenz aufstellt — rechnet
ausschliesslich auf der **aktuellen** Generation. Welche das ist, wird nicht als Textkonstante
hinterlegt, sondern als höchste im Bestand vorkommende Generation ermittelt; eine Kopie von
`CONFIDENCE_FORMULA_VERSION` würde sonst beim nächsten Formelwechsel veralten. Liegt auf der
aktuellen Formel noch keine Entscheidung vor, bleibt die Kurve leer und sagt das auch — eine
Kurve über mehrere Generationen sähe flach aus, ohne dass das etwas bedeutet.

Die Kennzahl **Mittlere Konfidenz** und die **Konfidenz-Verteilung** laufen bewusst weiter
über alle Generationen: sie beschreiben, was tatsächlich erzeugt wurde, und behaupten nichts
über Vorhersagekraft. Wer gezielt in eine ältere Generation sehen will, hängt
`?formula_version=v3` an die Adresse — das grenzt dann ALLE Zahlen der Seite darauf ein.

---

## Wenn das Gedächtnis den Wert ersetzt

Überstimmt ein Gedächtnisfall die Schätzung des Modells, bezieht sich die
**Selbsteinschätzung weiterhin auf den ursprünglichen Vorschlag** — sie wurde ja vor der
Ersetzung geschrieben. Im Beispiel oben begründet sie den Medianwert `1.14`, vorgeschlagen
wird aber `1.017`.

Der Originaltext wird bewusst NICHT verworfen: er ist der Beleg dafür, was das Modell
gedacht hat, und gehört damit zur Nachvollziehbarkeit. Stattdessen wird er eingeordnet —
seit 13.08.2026 an zwei Stellen:

- **Im Vorschlag selbst** (`generate_correction_llm.py`): der Override stellt dem Rationale
  einen Satz voran, der die Ersetzung benennt. Das steht damit auch in der Datenbank und im
  gespeicherten JSON, nicht nur auf dem Bildschirm.
- **In der Oberfläche** (`review.js`): für Vorschläge, die VOR dieser Änderung entstanden
  sind, ergänzt das Review Board die Einordnung beim Anzeigen. Erkannt wird der Fall am
  Präfix `[GEDÄCHTNIS]` in `reasoning` — eine verlässliche Markierung, weil genau ein
  Codepfad sie schreibt.

Ein Prüfer liest also nie eine Begründung, die sich unkommentiert auf einen verworfenen Wert
bezieht.
