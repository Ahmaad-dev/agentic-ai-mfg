# Core Rules (always loaded)

Cross-cutting rules: error identification, array_context usage, and the action catalogue.
Error-type specific rules live in the card loaded alongside this file.
Source: `llm-validation-fix-rules.md` (see `docs/AP7-0_rule_inventory.md`, rules R1–R5, R18–R21).

## 0. Error Identification & Prioritization

Diese Regeln gelten für die **Fehler-Analyse** (identify_error_llm.py) - bevor eine Korrektur generiert wird.

### 0.1 Prioritisierung von Fehlern

**Wenn mehrere Fehler vorhanden sind, wähle den KRITISCHSTEN ZUERST:**

1. **ROOT CAUSE vor Symptomen:**
   - EMPTY/MISSING Felder sind meist die Ursache → diese ZUERST fixen
   - Beispiel: Fehlende demand_id verursacht später Referenzfehler
   - Behebe die Quelle, nicht die Folge-Fehler

2. **Abhängigkeiten analysieren:**
   - Verursacht ein Fehler mehrere andere?
   - Beispiel: DUPLICATE IDs sollten vor invalid references behoben werden
   - Beispiel: Missing demand verursacht "demand not found" Fehler

3. **Severity-Reihenfolge:**
   - Kritische Business-Daten (demands, orders) > Konfigurationsdaten
   - Datenintegrität > Formatierung
   - Strukturelle Fehler > Wert-Validierungen

**Beispiel-Priorisierung:**
```
Fehler vorhanden:
1. "Demand IDs must not be empty" (2 demands) → ROOT CAUSE
2. "Duplicate demand IDs found: D830081_005" → DUPLICATE 
3. "Invalid reference to demand: " (empty ref) → SYMPTOM von #1

Wähle: Fehler #1 - behebt potentiell auch #3
```

### 0.2 Search Mode Auswahl

**Entscheide zwischen "value" und "empty_field" mode basierend auf dem Fehlertyp:**

#### "value" Mode verwenden wenn:
- Fehler erwähnt **spezifische ID oder Name**
  - Beispiel: "Article SPE_ZU_kl" → search_value = "SPE_ZU_kl"
  - Beispiel: "Demand D830081_005" → search_value = "D830081_005"

- Fehler erwähnt **INVALID VALUE** (Wert ist falsch, aber vorhanden)
  - Beispiel: "invalid rel_density_min: 0.0" → search_value = Artikel-Name
  - Beispiel: "negative quantity: -5" → search_value = Entity-ID

- Fehler erwähnt **"missing X for Y"** oder **"entity is missing X"**
  - Beispiel: "Article SPE_AR_fil is missing work_item_configs for: ABF01"
  - → search_value = "SPE_AR_fil" (die Entity, die das Problem hat)
  - → NICHT "ABF01" (das ist das fehlende Element)

#### "empty_field" Mode verwenden wenn:
- Fehler erwähnt **EMPTY, NULL, oder MISSING field** (Feld hat KEINEN Wert)
  - Beispiel: "demandId is empty" → search_value = "demandId"
  - Beispiel: "articleId must not be null" → search_value = "articleId"
  - Beispiel: "workPlanId field missing" → search_value = "workPlanId"

**WICHTIGE Unterscheidung:**
```
Not OK: "invalid rel_density_min: 0.0" 
   → Wert ist VORHANDEN aber FALSCH
   → "value" mode mit Artikel-Name

OK: "Article SPE_AR_fil is missing work_item_configs for: ABF01"
   → Entity fehlt ein ELEMENT in einem Array
   → "value" mode mit "SPE_AR_fil"

OK: "demandId is empty"
   → Feld hat KEINEN Wert
   → "empty_field" mode mit "demandId"
```

**Weitere Beispiele:**
```json
// Fehler: "Duplicate demand IDs found: D830081_005"
{"search_mode": "value", "search_value": "D830081_005"}

// Fehler: "Demand IDs must not be empty"
{"search_mode": "empty_field", "search_value": "demandId"}

// Fehler: "Article SPE_ZU_kl has invalid rel_density_min: 0.0"
{"search_mode": "value", "search_value": "SPE_ZU_kl"}

// Fehler: "Article SPE_AR_fil is missing work_item_configs for: ABF01"
{"search_mode": "value", "search_value": "SPE_AR_fil"}

// Fehler: "Order quantity cannot be negative: -10"
{"search_mode": "value", "search_value": "<order-id>"}
```

### 0.3 Investigation Decision

**should_investigate: true/false**

- **true**: Fehler erfordert Datensuche im Snapshot
  - Fehlende Referenzen (welcher Wert ist korrekt?)
  - Duplikate (wie unterscheiden sich die Einträge?)
  - Invalid values (was ist der typische Wert?)

- **false**: Fehler ist trivial/selbsterklärend
  - Einfache Formatierungsfehler
  - Offensichtliche Fixes (empty string → remove)
  - Keine Kontextsuche nötig

---

## Wichtig: Nutzung von array_context

**Wann ist array_context sinnvoll?**

**JA - Nutze array_context für:**
- **Statistische Analyse**: Median, Durchschnitt, häufigster Wert berechnen
- **Pattern-Erkennung**: Format-Muster aus umliegenden Einträgen ableiten
- **Numerische Werte**: relDensityMin, quantity, priority - Vergleich mit Nachbarn
- **Leere Felder**: Typischen Wert aus umliegenden Einträgen ermitteln
- **Duplikate**: Suffix-Pattern aus existierenden Einträgen erkennen
- **PACKAGING ID-PATTERN**: Ähnliche Packaging-IDs bevorzugen gleiche Equipment-Sequenzen

**NEIN - array_context ist NICHT sinnvoll für:**
- **Typo-Korrektur von Referenz-IDs**: Braucht die referenzierte Liste (z.B. articles), nicht umliegende demands
- **Einzelne Felder außerhalb von Arrays**: Keine Nachbar-Einträge verfügbar
- **Absolute Werte**: Wenn der Wert eindeutig falsch ist, unabhängig vom Kontext

### KRITISCH: Domain-Intelligence bei array_context — Grundprinzip

**Wenn du array_context nutzt, FILTERE die items_before/items_after intelligent!**

Bevor du aus Nachbar-Einträgen einen Wert ableitest (Median, häufigster Wert, Format):

1. **Prüfe ZUERST, ob die Nachbarn zur gleichen Gruppe gehören:**
   - Vergleiche `departmentId` und `workPlanId`
   - Vergleiche das ID-/Artikel-Präfix (z.B. "SPE_ZU" vs "SPE_PU")

2. **NUTZE NUR Einträge aus der gleichen Gruppe für Statistik.**
   Blind den Median ALLER Einträge zu nehmen führt zu falschen Werten:
   verschiedene Departments und Produkttypen haben unterschiedliche Eigenschaften
   (z.B. SPE_ZU_* (Zubereitung) hat andere Dichte als SPE_PU_* (Pulver)).

3. **Begründung explizit im Reasoning erwähnen:**
   - "Used only articles from same department (20300) and workplan (7202)"
   - "Filtered to same product prefix (SPE_ZU_*) for domain accuracy"
   - "Excluded unrelated article types (SPE_PU_*, SPE_AR_*)"

---

# 5. Verfügbare Actions

## Action: `update_field`
**Verwendung:** Ändere den Wert eines existierenden Feldes.

**JSON Format:**
```json
{
  "action": "update_field",
  "target_path": "demands[5].articleId",
  "current_value": "SPE_OLD",
  "new_value": "SPE_NEW",
  "reasoning": "...",
  "additional_updates": []
}
```

**Beispiel:**
```json
// Korrigiere Typo in articleId
{
  "action": "update_field",
  "target_path": "demands[3].articleId",
  "current_value": "SPE_PUasdsda_gr",
  "new_value": "SPE_PU_gr",
  "reasoning": "Typo correction based on fuzzy match with 60% similarity to existing article SPE_PU_gr"
}
```

---

## Action: `add_to_array`
**Verwendung:** Füge ein neues Objekt zu einem Array hinzu.

**JSON Format:**
```json
{
  "action": "add_to_array",
  "target_path": "demands",
  "current_value": null,
  "new_value": {
    "demandId": "DSPE_NEW_001",
    "articleId": "SPE_EM",
    "quantity": 500,
    "packaging": "71164",
    "successor": "01A11305414002000",
    "vgnr-vorschlag": null,
    "dueDate": "2025-11-20T00:00:00Z",
    "dispatcherGroup": "20",
    "priority": 12
  },
  "reasoning": "...",
  "additional_updates": []
}
```

**Wichtig:**
- `target_path` ist nur der Array-Name (z.B. `demands`), NICHT `demands[5]`
- `new_value` muss ein vollständiges Objekt sein
- Nutze `array_context` um Format der bestehenden Einträge zu erkennen

**Beispiel:**
```json
// Fehlender Demand muss hinzugefügt werden
{
  "action": "add_to_array",
  "target_path": "demands",
  "current_value": null,
  "new_value": {
    "demandId": "DSPE_EM_004",
    "articleId": "SPE_EM",
    "quantity": 750,
    "packaging": "71164",
    "successor": "01A11305414002000",
    "vgnr-vorschlag": null,
    "dueDate": "2025-11-25T00:00:00Z",
    "dispatcherGroup": "20",
    "priority": 12
  },
  "reasoning": "Missing demand entry referenced by customer order. Created based on pattern from existing SPE_EM demands using array_context"
}
```

---

## Action: `remove_from_array`
**Verwendung:** Entferne ein Objekt aus einem Array.

**Option 1 - Nach Index:**
```json
{
  "action": "remove_from_array",
  "target_path": "demands[5]",
  "current_value": {
    "demandId": "DSPE_INVALID_001",
    "articleId": "SPE_WRONG"
  },
  "new_value": null,
  "reasoning": "..."
}
```

**Option 2 - Nach Matching (ohne Index):**
```json
{
  "action": "remove_from_array",
  "target_path": "demands",
  "current_value": {
    "demandId": "DSPE_INVALID_001"
  },
  "new_value": null,
  "reasoning": "..."
}
```

**Wichtig:**
- Mit Index (`demands[5]`): Entfernt exakt diesen Index
- Ohne Index (`demands`): Sucht nach Objekt mit matching Feldern in `current_value`
- `current_value` enthält das zu entfernende Objekt oder Match-Kriterien
- `new_value` ist immer `null` bei remove

**Beispiel:**
```json
// Entferne doppelten/invaliden Eintrag
{
  "action": "remove_from_array",
  "target_path": "demands",
  "current_value": {
    "demandId": "DSPE_DUPLICATE_001",
    "articleId": "SPE_INVALID"
  },
  "new_value": null,
  "reasoning": "Duplicate demand entry with invalid article reference. Removing duplicate as correction is applied to other instance"
}
```

---

# 6. Wann welche Action?

**`update_field`:**
- Typo-Korrektur
- Wert-Anpassung (quantity, priority, etc.)
- Referenz-Update
- Format-Korrektur
- **Fehlende Elemente in Nested-Arrays** (z.B. workItemConfigs)

**`add_to_array`:**
- Fehlender referenzierter Eintrag
- Pflicht-Objekt wurde vergessen
- NUR wenn absolut notwendig!
- Prüfe: Kann stattdessen ein Typo korrigiert werden?

**`remove_from_array`:**
- Echter Duplikat (nicht nur ID-Duplikat!)
- Invalider/beschädigter Eintrag
- Test-Daten die nicht in Produktion gehören
- Vorsicht: Könnte Referenzen brechen!

**Generelle Regel:**
1. **Prefer update_field** für die meisten Fälle (inkl. Nested-Arrays!)
2. **Vermeide add_to_array** wenn möglich (suche nach Typos!)
3. **Vermeide remove_from_array** (könnte Daten-Verlust bedeuten)
4. **Bei Unsicherheit**: Nutze update_field
