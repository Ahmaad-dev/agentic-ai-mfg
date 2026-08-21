# G5-Preflight — Bereitschaft zum Einfrieren

**Status: `READY_FOR_G5`. Der formale Freeze ist NICHT gesetzt.**
Erstellt 21.08.2026, Grundlage BA-035 bis BA-052.

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
| **G5a vollständig** | ✅ | `data/archive/ba-umgebung-eingefroren-20260820/{lock.json,requirements-frozen.txt}` — alle sechs Punkte | — |
| **Runner final** | ✅ | `app/eval/run_ba_abc_suite.py`; A/B/C-Pilotvalidierung P01 grün, Ausfall-Lauf als False-Green-Test | — |
| **Messschema final: 29 Felder** | ✅ | AST-Zählung `MESSSCHEMA` = 29; jede Zeile des Pilotlaufs trägt 29; in allen Zeilen identisch | — |
| **Kategorien fachlich festgelegt** | ✅ | `app/eval/kategorien.py` + `kategorie4.py`; K1 8/8 · K2 9/9 · K3 8/8 · K4 7/7 · Integration 19/19 | — |
| **Modellkonfiguration bekannt** | ✅ | `gpt-4.1`, API `2025-01-01-preview`, `temperature=0.3`; Quellen `generate_correction_llm.py:753`, `identify_error_llm.py:239` | — |
| **Root-Umgebung dokumentiert** | ✅ | `ba_env_ok=True`, `sys_prefix=…\agentic-ai-mfg\.venv`, **77 Pakete** in `requirements-frozen.txt` | — |
| **Messkatalog / Ground Truth / Regelbasis gehasht** | ✅ | SHA-256 in `lock.json` Punkt 6: 2 Messkataloge, Pilot-Ground-Truth, Referenz-Snapshot, **14 Regelkarten** einzeln + Gesamthash | — |
| **Keine Messfälle verbraucht** | ✅ | alle Läufe auf `ba-pilot-snapshots`; kein `I01…I10` in den Rohdaten; G2 Exit 0 | — |
| **Keine offenen Produkt-/Prompt-/Regeländerungen** | ✅ | 0 Promptänderungen, 0 Regelkartenänderungen (BA-050, an BA-Markern belegt); AP-G ohne offene Punkte ausser G5a/G5 | — |
| **Regressionen grün** | ✅ | **199 Einzelprüfungen** über 7 Dateien, alle PASS bzw. PENDING-frei — 21.08.2026, 00:07 | — |
| **Working Tree klassifiziert** | ⚠️ | 38 Einträge, **keiner unbekannt**: 17 Messinstrument/Graph · 14 Produktpfad · 7 Dokumentation | siehe unten |

**Blocker: keine.**

---

## Der eine Vorbehalt: der Working Tree ist nicht sauber

G5a Punkt 2 verlangt „Working Tree sauber zum Messbeginn — verbleibende Änderungen
ausdrücklich benannt". Der Tree trägt **38 Einträge**. Sie sind vollständig klassifiziert und
**keiner ist unbekannt oder fremd**:

| Klasse | Anzahl | Inhalt |
|---|---|---|
| BA-relevant (Messinstrument/Graph) | 17 | `app/eval/*`, `app/tools/smart-planning/graph/*` |
| BA-relevant (Produktpfad) | 14 | Runtime-Änderungen aus AP-A bis AP-F **und BA-043** |
| Dokumentation | 6 | `docs/BA_*.md`, `docs/abbildungen/` |
| Dokumentation (Projektinstruktionen) | 1 | `CLAUDE.md` |

**Das ist kein Blocker, aber es ist zu entscheiden.** Zwei saubere Wege:

1. **Vor G5 committen** — dann identifiziert der Commit-Hash den Messstand vollständig, und
   G5a Punkt 1 trägt allein.
2. **Ohne Commit einfrieren** — dann ist `lock.json` Punkt 2 die vollständige Beschreibung des
   Deltas gegenüber `3ed63bf1`, und die Rekonstruktion braucht Commit **und** Lock-Artefakt.

**Ich habe nicht committet.** Der Tree enthält Änderungen aus mehreren Arbeitspaketen und aus
Sitzungen, die nicht diesem Block zuzuordnen sind; ein „nur die Dateien dieses Blocks"-Commit
wäre nicht sauber abgrenzbar. Nichts wurde gestaged, verworfen, resettet oder überschrieben.

---

## Was nach der Abnahme zu tun ist

1. Entscheidung zum Working Tree (committen oder Lock-Artefakt als Delta akzeptieren).
2. **G5 setzen** — Einfrierzeitpunkt mit Datum und den Hashes aus `lock.json` protokollieren.
3. Ab dann: **AP-H**, und jede Änderung ist eine Nachmessung.

**AP-H wurde nicht begonnen.** Kein Messfall ausgeführt, keiner angesehen, keine Vorabmessung,
kein `generate_audit_report()`.
