# Validation Fix Rules

## 1. Duplizierte IDs (validate_unique_ids-duplicate)

**Problem:** Mehrere Einträge haben dieselbe ID.

**Strategie:** Nummeriere Duplikate mit `_2`, `_3`, etc.

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
    {"articleId": "SPE_AR_fil"}
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

---

## 3. Ungültige Referenzen (validate_references)

**Problem:** Referenz-ID existiert nicht im referenzierten Array.

**Strategie 1 - Referenz korrigieren:** Finde ähnlichste existierende ID.
```json
// Vorher - "SPE_AR" existiert nicht in articles
"demands": [{"demandId": "D001", "articleId": "SPE_AR"}],
"articles": [{"articleId": "SPE_AR_fil"}]

// Nachher
"demands": [{"demandId": "D001", "articleId": "SPE_AR_fil"}],
"articles": [{"articleId": "SPE_AR_fil"}]
```

**Strategie 2 - Eintrag erstellen:** Erstelle fehlenden Eintrag mit Minimal-Daten.
```json
// Vorher - Equipment "EQ_999" fehlt
"workPlans": [{
    "workPlanId": "WP_001",
    "steps": [{"equipmentId": "EQ_999"}]
}],
"equipment": []

// Nachher
"workPlans": [{
    "workPlanId": "WP_001",
    "steps": [{"equipmentId": "EQ_999"}]
}],
"equipment": [{"equipmentId": "EQ_999"}]
```

**Priorisierung:** Strategie 1 (korrigieren) bevorzugen, wenn ähnliche ID existiert. Sonst Strategie 2 (erstellen).