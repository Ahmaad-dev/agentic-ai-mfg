---
name: unique-ids
applies_to: [UNIQUE_IDS]
description: Doppelte IDs und leere Pflicht-ID-Felder
---

# Card: UNIQUE_IDS  (`[validate_unique_ids]`)

This validator emits the SAME tag for two different problems. Decide which one applies from the
error message, then follow the matching section.
Source: `llm-validation-fix-rules.md` lines 286–363 (inventory rules R7, R8).

## 1. Duplizierte IDs (validate_unique_ids-duplicate)

**Problem:** Mehrere Einträge haben dieselbe ID.

**Strategie:** Nummeriere Duplikate mit `_1`, `_2`, `_3`, etc.

**Beispiel:**
```json
// Vorher
"articles": [
    {"articleId": "SPE_AR_fil"},
    {"articleId": "SPE_AR_fil"}
]

// Nachher
"articles": [
    {"articleId": "SPE_AR_fil"},
    {"articleId": "SPE_AR_fil_2"}
]
// oder
"articles": [
    {"articleId": "SPE_AR_fil_2"},
    {"articleId": "SPE_AR_fil_1"}
]
```

**Mit Referenzen:** Aktualisiere alle betroffenen Referenzen.
```json
// Vorher
"articles": [{"articleId": "ART_001"}, {"articleId": "ART_001"}],
"demands": [
    {"demandId": "D001", "articleId": "ART_001"},
    {"demandId": "D002", "articleId": "ART_001"}
]

// Nachher
"articles": [{"articleId": "ART_001"}, {"articleId": "ART_001_2"}],
"demands": [
    {"demandId": "D001", "articleId": "ART_001"},
    {"demandId": "D002", "articleId": "ART_001_2"}
]
```

---

## 2. Leere Pflichtfelder (validate_unique_ids-empty)

**Problem:** ID-Feld ist leer (`null`, `""`, oder nur Whitespace).

**Strategie:** Generiere ID basierend auf erkanntem Pattern.

**Pattern-Erkennung:**
1. Analysiere existierende IDs im gleichen Array
2. Erkenne Format (z.B. `PREFIX_{ARTIKEL}_{NUMMER}`)
3. Finde fehlende Sequenznummer
4. Generiere neue ID nach gleichem Pattern

**Beispiel:**
```json
// Vorher - demandId fehlt
"demands": [
    {"demandId": "DSPE_EM_001", "articleId": "SPE_EM"},
    {"demandId": "", "articleId": "SPE_EM"},
    {"demandId": "DSPE_EM_003", "articleId": "SPE_EM"}
]

// Pattern erkannt: DSPE_{articleId}_{sequence}
// Fehlende Nummer: 002

// Nachher
"demands": [
    {"demandId": "DSPE_EM_001", "articleId": "SPE_EM"},
    {"demandId": "DSPE_EM_002", "articleId": "SPE_EM"},
    {"demandId": "DSPE_EM_003", "articleId": "SPE_EM"}
]
```

**Fallback:** Wenn kein Pattern erkennbar, nutze `{PREFIX}_{TIMESTAMP}` oder `{PREFIX}_NEW_{INDEX}`.
