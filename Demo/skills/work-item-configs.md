---
name: work-item-configs
applies_to: [WORK_ITEM_CONFIGS_COMPLETENESS, START_END_OPERATION_EXISTENCE]
description: Fehlende Elemente in workItemConfigs (Placeholder-Erkennung, Prozessreihenfolge)
---

# Card: WORK_ITEM_CONFIGS_COMPLETENESS  (`[validate_work_item_configs_completeness]`)

Source: `llm-validation-fix-rules.md` lines 599–770 (inventory rules R15–R17).

## Fehlende Array-Elemente

**Problem:** Ein Objekt hat ein fehlendes Pflicht-Element in einem Nested-Array.

**Beispiel:** "Article SPE_AR_fil is missing work_item_configs for: VOAR01"

### 1. KRITISCH: Placeholder-Erkennung ZUERST prüfen!

**Bevor du ein Element hinzufügst, prüfe ob ein PLACEHOLDER/DUMMY-Wert existiert!**

"Missing X" kann zwei Bedeutungen haben:
1. **X existiert gar nicht** → HINZUFÜGEN am Ende
2. **X wurde durch ungültigen Placeholder ersetzt** → ERSETZEN des Placeholders

**Placeholder-Patterns (GENERISCH erkennen - für ALLE Entity-Typen):**

Placeholders sind **ungültige Werte** die als Platzhalter verwendet wurden. Sie können in JEDEM Array-Typ vorkommen (workItemConfigs, predecessors, etc.)

**Erkennungsmerkmale (mindestens eines erfüllt):**
1. **Prefix-basiert:**
   - Beginnt mit: `XXXX`, `DUMMY`, `TEST`, `PLACEHOLDER`, `TMP`, `INVALID`, `TODO`
   - Format: Prefix + Ziffern (z.B. `XXXX99`, `DUMMY01`, `TEST123`)

2. **Pattern-basiert:**
   - Nur Sonderzeichen: `---`, `???`, `...`, `***`
   - Ungültige Zeichen für den Kontext: Sonderzeichen wo normalerweise alphanumerisch
   - Repetitive Ziffern: `999`, `000`, `111` am Ende

3. **Kontext-basiert (wichtigste Prüfung!):**
   - **Vergleiche mit benachbarten Werten im selben Array**
   - **Pattern passt NICHT:** z.B. `XXXX99` zwischen `VO*`, `WA*` Keys
   - **Format-Inkonsistenz:** Alle anderen haben Pattern `[A-Z]{2,4}[0-9]{2}`, dieser nicht

**5-SCHRITT PLACEHOLDER-DETECTION:**

1. **Array inspizieren:**
   - Schaue alle Werte im betroffenen Array an
   - Suche nach Werten die anders aussehen als die anderen

2. **Pattern-Analyse:**
   - Erkenne das Format-Pattern der gültigen Werte
   - Beispiel: `VOAR01`, `VOPU01`, `WART01` → Pattern: `[A-Z]{4}[0-9]{2}`
   - Vergleiche jeden Wert mit diesem Pattern

3. **Placeholder identifizieren:**
   - Werte die NICHT dem Pattern entsprechen → potenzielle Placeholders
   - Prefix-Check (XXXX, DUMMY, etc.)
   - Kontext-Check (passt nicht zum Rest)

4. **Entscheidung:**
   - **Placeholder gefunden:** ACTION = `update_field` (ersetzen)
   - **Kein Placeholder:** ACTION = `add_to_array` (hinzufügen am Ende)

5. **Korrektur ausführen:**
   - Bei ERSETZEN: Nutze gleichen Index wie Placeholder
   - Bei HINZUFÜGEN: Füge am Array-Ende ein

**KONZEPT-BEISPIEL (anwendbar auf ALLE Arrays):**
```json
// Fehlermeldung: "Entity X is missing Y for: REAL_VALUE"

// Aktuelles Array im original_object:
"someArray": [
    {"key": "XXXX99", ...},      // ← Passt nicht zu anderen (kein [A-Z]{4}[0-9]{2})
    {"key": "REAL01", ...},      // ← Valides Pattern
    {"key": "REAL02", ...}       // ← Valides Pattern
]

// Pattern-Erkennung:
// - REAL01, REAL02 folgen Pattern: [A-Z]{4}[0-9]{2}
// - XXXX99 folgt NICHT diesem Pattern
// - XXXX99 beginnt mit "XXXX" → PLACEHOLDER!

// → ENTSCHEIDUNG: ERSETZE Placeholder an Index 0

// RICHTIG (update_field):
{
  "action": "update_field",
  "target_path": "someArray[0].key",
  "current_value": "XXXX99",
  "new_value": "REAL_VALUE"
}

// FALSCH wäre (add_to_array):
// Würde am Ende hinzufügen → 4 Elemente statt 3
```

**WICHTIG - Warum Placeholder-Check KRITISCH ist:**
- OK **Verhindert Duplikate:** Wenn Placeholder ersetzt wird, kein neuer Eintrag nötig
- OK **Erhält Array-Länge:** Original hatte 3 Elemente, Korrektur auch 3
- NOT OK **Ohne Check:** Placeholder bleibt + neuer Eintrag = 4 Elemente (FALSCH!)

**Reasoning Template:**
```
"The error states that VOAR01 is missing. However, analysis of original_object.workItemConfigs 
shows a placeholder value 'XXXX99' at index 0. Comparing with array_context (SPE_EM, SPE_GS_gr), 
all similar articles have 'VOAR01' with rampUpTime=15 at this position. 
SOLUTION: Replace entire workItemConfigs array with corrected version (XXXX99 → VOAR01)."
```

**WICHTIG - Action-Format:**
- Bei Nested Arrays (wie `workItemConfigs` in `articles`): Nutze `update_field` auf das **GESAMTE Parent-Array**
- **NICHT** `articles[0].workItemConfigs[0].workItemKey` (unsupported)
- **SONDERN** `articles[0].workItemConfigs` mit komplettem Array als new_value

```json
{
  "action": "update_field",
  "target_path": "articles[0].workItemConfigs",
  "current_value": [/* altes Array mit XXXX99 */],
  "new_value": [/* gesamtes Array mit VOAR01 statt XXXX99 */],
  "reasoning": "Placeholder XXXX99 replaced with VOAR01 based on array_context analysis..."
}
```

### 2. Standard-Strategie (wenn KEIN Placeholder)

**KRITISCH — REIHENFOLGE NIEMALS ÄNDERN:**
Die Reihenfolge der `workItemConfigs` ist die **Prozessreihenfolge** der Fertigung
(z. B. `VOAR01` Vorbereiten → `HE01` Herstellen → `RF01` Reifen → `QS01` Qualitätssicherung →
`ABF01` Abfüllen). Sie ist **fachliche Information, keine Formatierung**.
- **Übernimm das Array 1:1 vom ähnlichsten Artikel** (gleiche `departmentId`/`workPlanId`,
  gleiches Artikel-Präfix) und setze das fehlende Element an **genau die Position**, an der es
  in diesem Referenz-Artikel steht.
- **NIEMALS alphabetisch sortieren. NIEMALS umsortieren.** Ein umsortiertes Array ist fachlich
  falsch, auch wenn es dieselben Keys enthält — und es ist in den Daten nirgends belegt
  (`value_grounded` = 0), was die Konfidenz zu Recht einbrechen lässt.
- Prüfe zum Schluss: Kommt genau diese Key-Sequenz so in einem vergleichbaren Artikel vor?
  Wenn nein, hast du umsortiert oder erfunden.

**Wenn das Element tatsächlich komplett fehlt:**
1. Suche ähnliche Objekte im gleichen Array (`array_context`)
2. Prüfe `enriched_context` für typische Werte des fehlenden Elements
3. Kopiere Struktur, Reihenfolge und typische Werte vom ähnlichsten Objekt
4. Füge das fehlende Element an seiner Position in dieser Referenz-Sequenz ein

**Wichtig:**
- **Nutze array_context** um Format zu erkennen
- **Nutze similar_items** (falls vorhanden) für domain-spezifische Werte
- **Prüfe enriched_context** für andere Artikel mit dem Element
- Setze sinnvolle Default-Werte wenn keine Beispiele gefunden

**Beispiel:**
```json
// Vorher - SPE_AR_fil fehlt ABF01 in workItemConfigs
"articles": [
    {
        "articleId": "SPE_AR_fil",
        "workItemConfigs": [
            {"workItemKey": "VOAR01", "rampUpTime": 0, "netTimeFactor": 0},
            {"workItemKey": "WART04", "rampUpTime": 1, "netTimeFactor": 0}
            // ABF01 fehlt!
        ]
    }
]

// array_context oder enriched_context zeigt:
// Andere Artikel haben: {"workItemKey": "ABF01", "rampUpTime": 1, "netTimeFactor": 1}

// Nachher - ABF01 hinzugefügt
"articles": [
    {
        "articleId": "SPE_AR_fil",
        "workItemConfigs": [
            {"workItemKey": "VOAR01", "rampUpTime": 0, "netTimeFactor": 0},
            {"workItemKey": "WART04", "rampUpTime": 1, "netTimeFactor": 0},
            {"workItemKey": "ABF01", "rampUpTime": 1, "netTimeFactor": 1}
        ]
    }
]
```

**Action:** `update_field` auf das gesamte Nested-Array (z.B. `articles[0].workItemConfigs`)

**Alternative:** Bei sehr langen Arrays kann auch `add_to_array` verwendet werden, wenn der Pfad zum Nested-Array korrekt ist.

**Reasoning Beispiel:**
```json
{
  "action": "update_field",
  "target_path": "articles[0].workItemConfigs",
  "new_value": [/* existing items + new ABF01 */],
  "reasoning": "Article SPE_AR_fil is missing work_item_config for ABF01. Based on enriched_context, similar articles (SPE_EM, SPE_GS_gr) include ABF01 with rampUpTime=1 and netTimeFactor=1. Added ABF01 to workItemConfigs array to ensure completeness."
}
```
