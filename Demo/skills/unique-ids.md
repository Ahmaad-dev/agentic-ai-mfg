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

**Strategie:** Zuerst alle Objekte mit der gemeldeten ID vergleichen. Nicht pauschal
durchnummerieren und nicht automatisch einen Datensatz löschen.

1. Exakten Datensatz aus einem bestätigten gültigen Snapshot suchen.
2. Prüfen, ob die Objekte echte Dubletten oder verschiedene Business-Objekte mit kollidierter ID sind.
3. Nur die nachweislich falsche ID auf ihren belegten Originalwert korrigieren.
4. Abhängige Referenzen nur dann mitändern, wenn eindeutig feststeht, welchem Objekt sie gehören.
5. Sind beide Objekte verschieden und die richtige Zuordnung ist nicht belegbar: keine ID erfinden.

**Beispiel:**
```json
// Vorher
"articles": [
    {"articleId": "SPE_AR_fil"},
    {"articleId": "SPE_AR_fil"}
]

// Nachher – nur wenn eine autoritative Quelle die zweite ID als SPE_AR_fil_2 belegt
"articles": [
    {"articleId": "SPE_AR_fil"},
    {"articleId": "SPE_AR_fil_2"}
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

**Strategie:** ID aus einer autoritativen Quelle wiederherstellen. Ein Array-Pattern darf nur
verwendet werden, wenn es deterministisch ist und genau eine freie ID ergibt.

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

**Kein Fallback mit Timestamp, Zufall oder `NEW`:** Solche IDs sind nicht fachlich belegt,
nicht reproduzierbar und können externe Referenzen brechen. Wenn kein eindeutiger Wert aus
Historie, Business-Schlüssel oder lückenloser Sequenz ableitbar ist, Korrektur als mehrdeutig melden.
