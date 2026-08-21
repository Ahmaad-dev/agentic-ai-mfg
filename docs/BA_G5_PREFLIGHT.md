# G5-Preflight — Bereitschaft zum Einfrieren

**Status: ✅ `G5 GESETZT` — eingefroren am 21.08.2026, 12:39:27 +02:00 (BA-057).**

> Dieses Dokument hat seinen Zweck erfüllt und bleibt als **Nachweis der Bereitschaft** stehen.
> Der Einfrierzeitpunkt und der vollständige Stand sind in **BA-057** protokolliert.
> **Ab dem Freeze ist jede Änderung an Regelwerk, Graphstruktur, Prompts, Parametern oder
> Umgebung eine Nachmessung.**

> **Aktualisiert 21.08. (BA-054).** Der zuvor benannte Vorbehalt — Working Tree nicht
> sauber — ist **aufgelöst**: der Messstand liegt jetzt als Commit `61a3f51` auf
> Branch `ba-messstand-g5`, der Tree ist leer, und G5a zeigt darauf.
>
> **Zwei Commits, ein Codestand:** `61a3f51` fixiert den **Messcode** (53 Dateien),
> `f0e5f41` legt nur die **Dokumentation** dazu (BA-054, Preflight). Am gemessenen Code
> ändert der zweite Commit nichts; `lock.json` führt den jeweils aktuellen HEAD.

Erstellt 21.08.2026, Grundlage BA-035 bis BA-056.

> **Was dieses Dokument ist und was nicht.** Es prüft, ob alle Voraussetzungen für G5 erfüllt
> *wären* — es setzt den Einfrierzeitpunkt **nicht**. Der Freeze ist eine Abnahmeentscheidung
> und bleibt dem Nutzer vorbehalten. Ab G5 ist jede Änderung an Regelwerk, Graphstruktur,
> Prompts, Parametern oder Umgebung eine **Nachmessung**; dieser Schnitt wird nicht nebenbei
> gezogen.

---

## Preflight-Matrix

| Kriterium | Status | Beleg | Blocker |
|---|---|---|---|
| **G3 geschlossen** | ✅ | BA-049, Abschlussmatrix; AP-G3 auf `[x]`; 7 von 10 Pilotzielen real belegt, 3 begründet nicht | — |
| **G4 geschlossen** | ✅ | BA-050, `docs/BA_G4_PILOTPHASE_ABSCHLUSS.md`; keine Inkonsistenz gefunden | — |
| **H4a geschlossen** | ✅ | BA-051/BA-052; **Preflight 26/26**; AP-H4a auf `[x]`, Befund F4 als erledigt markiert | — |
| **G5a vollständig** | ✅ | `…/ba-umgebung-eingefroren-20260820/{lock.json,requirements-frozen.txt}` — sechs Punkte, **auf `61a3f51` aktualisiert** (BA-054) | — |
| **Runner final** | ✅ | `app/eval/run_ba_abc_suite.py`; A/B/C-Pilotvalidierung P01 grün, Ausfall-Lauf als False-Green-Test | — |
| **Messschema final: 29 Felder** | ✅ | AST-Zählung `MESSSCHEMA` = 29; jede Zeile des Pilotlaufs trägt 29; in allen Zeilen identisch | — |
| **Kategorien fachlich festgelegt** | ✅ | `app/eval/kategorien.py` + `kategorie4.py`; K1 8/8 · K2 9/9 · K3 8/8 · K4 7/7 · Integration 19/19 | — |
| **Modellkonfiguration bekannt** | ✅ | `gpt-4.1`, API `2025-01-01-preview`, `temperature=0.3`; Quellen `generate_correction_llm.py:753`, `identify_error_llm.py:239` | — |
| **Root-Umgebung dokumentiert** | ✅ | `ba_env_ok=True`, `sys_prefix=…\agentic-ai-mfg\.venv`, **77 Pakete** in `requirements-frozen.txt` | — |
| **Ground Truth der MESSfälle gehasht** | ✅ | **BA-054**: 14 + 13 Messfall-Dateien **einzeln** + Gesamthashes (`0b0a9aff…`, `5a237594…`); zuvor nur zwei Index-Dateien, davon eine ohne GT-Felder | — |
| **Regelbasis Bedingung A eingefroren** | ✅ | `llm-validation-fix-rules.md` **in Git** *und* SHA `a3c14bd1…` (36.165 Byte) — deckungsgleich mit BA-016 B3.1 | — |
| **Keine Messfälle verbraucht** | ✅ | alle Läufe auf `ba-pilot-snapshots`; kein `I01…I10` in den Rohdaten; G2 Exit 0 | — |
| **Keine offenen Produkt-/Prompt-/Regeländerungen** | ✅ | 0 Promptänderungen, 0 Regelkartenänderungen (BA-050, an BA-Markern belegt); AP-G ohne offene Punkte ausser G5a/G5 | — |
| **H2 Wiederholungen fixiert** | ✅ | **N=5** verbindlich (BA-055) für **alle drei Arme** (BA-056); **255 Läufe** (85+85+85); Wiederholungsnr. in `lauf_metadaten`, Schema unverändert | — |
| **H3 Grenzfälle entschieden** | ✅ | als **Limitation** geschlossen (BA-055): Pfad belegt, gezielter Fall nicht konstruierbar; 17-Fälle-Katalog unangetastet | — |
| **H4 Randomisierung fixiert** | ✅ | Seed **20260821** vorher dokumentiert; Seed + erzeugte Reihenfolge in den Rohdaten; `test_messplan.py` **25/25** | — |
| **Runner-Preflight** | ✅ | **35/35** (26 aus BA-053 + 9 zu H2/H4) | — |
| **Regressionen grün** | ✅ | **224 Assertions** über **8** Dateien, alle PASS — 21.08.2026 | — |
| **Working Tree sauber** | ✅ | **0 Einträge** nach Commit `61a3f51` (53 Dateien: 46 Messstand, 7 Dokumentation, 0 fachfremd, 0 unklar) | — |

**Blocker: keine.**

---

## Der frühere Vorbehalt ist aufgelöst (BA-054)

`3ed63bf1` enthielt **keine einzige** messrelevante Datei — der gesamte Graph, der Runner und
`kategorie4.py` lagen untracked. Der Messstand ist jetzt als Commit fixiert:

* **`61a3f51e0b77…`** auf Branch `ba-messstand-g5`, 53 Dateien
* Working Tree **leer**; `app/.env` und `data/` per `.gitignore` ausgeschlossen
* nichts verworfen, resettet oder gestasht

**Der Ordnername `…-20260820` ist UTC-basiert** (`erzeugt_utc 2026-08-20T22:13Z`), der
Testbericht nennt Lokalzeit (`2026-08-21 00:07+02:00`). Dieselbe Stunde, zwei Zeitzonen —
nicht umbenannt.

## Was nach der Abnahme zu tun ist

1. ~~Entscheidung zum Working Tree~~ — **erledigt (BA-054)**: Messstand als Commit fixiert,
   Tree sauber.
2. **G5 setzen** — Einfrierzeitpunkt mit Datum und den Hashes aus `lock.json` protokollieren.
3. Ab dann: **H5, die eigentliche Messung** — **255 Läufe** (A 85 + B 85 + C 85),
   randomisiert mit Seed `20260821`. H2, H3, H4 und H4a sind vorbereitet und geschlossen.
   Jede Änderung ab G5 ist eine Nachmessung.

**AP-H wurde nicht begonnen.** Kein Messfall ausgeführt, keiner angesehen, keine Vorabmessung,
kein `generate_audit_report()`.
