# Validation Fix Rules

## Wichtig: Nutzung von array_context

**Wann ist array_context sinnvoll?**

**JA - Nutze array_context für:**
- **Statistische Analyse**: Median, Durchschnitt, häufigster Wert berechnen
- **Pattern-Erkennung**: Format-Muster aus umliegenden Einträgen ableiten
- **Numerische Werte**: relDensityMin, quantity, priority - Vergleich mit Nachbarn
- **Leere Felder**: Typischen Wert aus umliegenden Einträgen ermitteln
- **Duplikate**: Suffix-Pattern aus existierenden Einträgen erkennen

**NEIN - array_context ist NICHT sinnvoll für:**
- **Typo-Korrektur von Referenz-IDs**: Braucht die referenzierte Liste (z.B. articles), nicht umliegende demands
- **Einzelne Felder außerhalb von Arrays**: Keine Nachbar-Einträge verfügbar
- **Absolute Werte**: Wenn der Wert eindeutig falsch ist, unabhängig vom Kontext

**Beispiel - Gute Nutzung von array_context:**
```json
// Fehler: relDensityMin = 0 bei articles[10]
// array_context zeigt:
items_before: [
    {"articleId": "A1", "relDensityMin": 0.01},
    {"articleId": "A2", "relDensityMin": 0.01},
    {"articleId": "A3", "relDensityMin": 0.01}
],
items_after: [
    {"articleId": "A5", "relDensityMin": 0.01},
    {"articleId": "A6", "relDensityMin": 0.01}
]

// Analyse: Median ist 0.01 → korrigiere zu 0.01
// Action: update_field
// Target: articles[10].relDensityMin
// New Value: 0.01
// Reasoning: "Array context analysis shows all neighboring entries have relDensityMin=0.01, the median value is 0.01"
```

**Beispiel - SCHLECHTE Nutzung (nicht machen!):**
```json
// Fehler: articleId "S123PE_xyz" existiert nicht in articles
// array_context zeigt andere demands - NICHT hilfreich!
// items_before: [{"articleId": "SPE_AR_fil"}, ...]
// 
// FALSCH: "Basierend auf array_context nehme ich SPE_AR_fil"
// RICHTIG: Suche in enriched_context.field_examples.articleId nach ähnlichem String
// → Finde SPE_XY_fil durch String-Ähnlichkeit, nicht durch array_context
```

---

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

---

## 3. Ungültige Referenzen (validate_demand_article_ids, validate_references)

**Problem:** Referenz-ID existiert nicht im referenzierten Array - meist durch Typo/Tippfehler.

**WICHTIG:** Erstelle NIEMALS neue Einträge! Analysiere stattdessen die vorhandenen Daten und korrigiere den Typo.

**Strategie - Typo-Korrektur:**
1. Analysiere die fehlerhafte ID und erkenne das Pattern
2. Suche in `last_search_results.json` nach ähnlichen existierenden IDs
3. Verwende String-Ähnlichkeit (Levenshtein Distance, gemeinsame Präfixe)
4. Korrigiere die Referenz auf die korrekte existierende ID

**Beispiel 1 - Einfacher Typo:**
```json
// Vorher - "SPE_PUasdsda_gr" ist Typo (sollte "SPE_PU_gr" sein)
"demands": [
    {"demandId": "DSPE_PU_gr_001", "articleId": "SPE_PUasdsda_gr"}
],
"articles": [
    {"articleId": "SPE_PU_gr", "articleName": "..."}
]

// Nachher - Typo korrigiert
"demands": [
    {"demandId": "DSPE_PU_gr_001", "articleId": "SPE_PU_gr"}
],
"articles": [
    {"articleId": "SPE_PU_gr", "articleName": "..."}
]
```

**Beispiel 2 - Präfix-basiert:**
```json
// Vorher - "SPE_AR" fehlt Suffix
"demands": [{"demandId": "D001", "articleId": "SPE_AR"}],
"articles": [{"articleId": "SPE_AR_fil"}]

// Nachher - Korrigiert zu vollständiger ID
"demands": [{"demandId": "D001", "articleId": "SPE_AR_fil"}],
"articles": [{"articleId": "SPE_AR_fil"}]
```

**Analyse-Kriterien:**
- Gemeinsame Präfixe/Suffixe
- Ähnliche Zeichenketten
- Kontext aus `last_search_results.json` nutzen
- Bei mehreren Kandidaten: Wähle ID mit höchster Ähnlichkeit

**Action:** `update_field` - Ändere die fehlerhafte Referenz zur korrekten ID