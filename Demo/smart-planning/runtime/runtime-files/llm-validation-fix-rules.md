# Validation Fix Rules

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
## KRITISCH: Domain-Intelligence bei array_context

### PACKAGING EQUIPMENT PATTERN ANALYSIS

**Problem**: Leere predecessors in packagingEquipmentCompatibility

**LÖSUNG**: Nutze ID-Nähe-Analyse für Equipment-Pattern:

**Schritt 1: ID-Clustering**
```json
// Gegeben: packaging "70409" mit predecessors [""] (leer)
// Array_context zeigt:
"items_after": [
  {"packaging": "70702", "predecessors": ["ABD01", "ABB01"]},      // 2-Equipment-Pattern  
  {"packaging": "71105", "predecessors": ["AKA03", "AKA02", "AKA01", "AAR01"]},  // 4-Equipment-Pattern
  {"packaging": "71164", "predecessors": ["ABB01"]},              // 1-Equipment-Pattern
  {"packaging": "71330", "predecessors": ["BPU01", "APU01", "BPU03"]}  // 3-Equipment-Pattern
]
```

**Schritt 2: ID-Pattern-Matching**
- **70409** vs **71105**: Beide 5-stellige IDs, 70xxx/71xxx Pattern → HOHE ÄHNLICHKEIT
- **70409** vs **70702**: Beide 70xxx, aber different length/pattern → MITTLERE ÄHNLICHKEIT  
- **70409** vs **71164**: Different prefix → NIEDRIGE ÄHNLICHKEIT

**Schritt 3: Equipment-Sequence-Priorisierung**
- **Längere Equipment-Sequenzen bevorzugen**: 4er > 3er > 2er > 1er
- **Funktional zusammenhängende Chains**: AKA03→AKA02→AKA01→AAR01 ist eine Abfüll-Sequenz
- **String-Distance ist SEKUNDÄR**: ID-Pattern + Equipment-Sequence-Length ist PRIMARY

**Logik-Template**:
1. **ID-Pattern-Ähnlichkeit** (Länge, Prefix, Format)
2. **Equipment-Sequence-Length** (längere = vollständigere Prozesse)  
3. **Functional Coherence** (Abfüll-Ketten bevorzugen)
4. **String-Distance** als letztes Kriterium

## KRITISCH: Domain-Intelligence bei array_context

### PACKAGING EQUIPMENT PATTERN ANALYSIS

**Problem**: Leere predecessors in packagingEquipmentCompatibility

**LÖSUNG**: Nutze ID-Nähe-Analyse für Equipment-Pattern:

**Schritt 1: ID-Clustering**
```json
// Gegeben: packaging "70409" mit predecessors [""] (leer)
// Array_context zeigt:
"items_after": [
  {"packaging": "70702", "predecessors": ["ABD01", "ABB01"]},      // 2-Equipment-Pattern  
  {"packaging": "71105", "predecessors": ["AKA03", "AKA02", "AKA01", "AAR01"]},  // 4-Equipment-Pattern
  {"packaging": "71164", "predecessors": ["ABB01"]},              // 1-Equipment-Pattern
  {"packaging": "71330", "predecessors": ["BPU01", "APU01", "BPU03"]}  // 3-Equipment-Pattern
]
```

**Schritt 2: ID-Pattern-Matching**
- **70409** vs **71105**: Beide 5-stellige IDs, 70xxx/71xxx Pattern → HOHE ÄHNLICHKEIT
- **70409** vs **70702**: Beide 70xxx, aber different length/pattern → MITTLERE ÄHNLICHKEIT  
- **70409** vs **71164**: Different prefix → NIEDRIGE ÄHNLICHKEIT

**Schritt 3: Equipment-Sequence-Priorisierung**
- **Längere Equipment-Sequenzen bevorzugen**: 4er > 3er > 2er > 1er
- **Funktional zusammenhängende Chains**: AKA03→AKA02→AKA01→AAR01 ist eine Abfüll-Sequenz
- **String-Distance ist SEKUNDÄR**: ID-Pattern + Equipment-Sequence-Length ist PRIMARY

**ERGEBNIS für 70409**:
```json
// RICHTIG (71105-basiert): 4-Equipment Aromen/Kanister-Sequence
"predecessors": ["AKA03", "AKA02", "AKA01", "AAR01"]

// FALSCH (70702-basiert): Nur 2-Equipment, andere Funktion  
"predecessors": ["ABD01", "ABB01"]
```

**Logik-Template**:
1. **ID-Pattern-Ähnlichkeit** (Länge, Prefix, Format)
2. **Equipment-Sequence-Length** (längere = vollständigere Prozesse)  
3. **Functional Coherence** (Abfüll-Ketten bevorzugen)
4. **String-Distance** als letztes Kriterium
- **Absolute Werte**: Wenn der Wert eindeutig falsch ist, unabhängig vom Kontext

---

## KRITISCH: Domain-Intelligence bei array_context

**Wenn du array_context nutzt, FILTERE die items_before/items_after intelligent!**

**Für articles Array:**
1. **Prüfe ZUERST, ob die Artikel zur gleichen Gruppe gehören:**
   - Vergleiche `departmentId` und `workPlanId`
   - Vergleiche Artikel-Präfix (z.B. "SPE_ZU" vs "SPE_PU")
   
2. **NUTZE NUR Artikel aus der gleichen Gruppe für Statistik:**
   ```json
   // FEHLER: articles[7] hat relDensityMin = 0
   // TARGET: {"articleId": "SPE_ZU_kl", "departmentId": "20300", "workPlanId": "7202"}
   
   // items_before enthält:
   [
       {"articleId": "SPE_AR_fil", "departmentId": "10100", "relDensityMin": 0.02},  //IGNORIERE - anderes dept
       {"articleId": "SPE_PU_kl", "departmentId": "30100", "relDensityMin": 0.05},   //IGNORIERE - anderes dept+prefix
       {"articleId": "SPE_ZU_gr", "departmentId": "20300", "workPlanId": "7202", "relDensityMin": 0.01},  //NUTZE - gleiche Gruppe!
   ]
   
   // Richtige Analyse:
   // - Filtere NUR Artikel mit departmentId="20300" UND workPlanId="7202"
   // - Oder zumindest: Artikel mit Präfix "SPE_ZU_*"
   // - Berechne Median NUR aus gefilterten Werten
   // - Reasoning: "Filtered array_context to same product type (SPE_ZU_*, dept 20300). Median relDensityMin is 0.01"
   ```

3. **Begründung explizit erwähnen:**
   - "Used only articles from same department (20300) and workplan (7202)"
   - "Filtered to same product prefix (SPE_ZU_*) for domain accuracy"
   - "Excluded unrelated article types (SPE_PU_*, SPE_AR_*)"

**Warum ist das wichtig?**
- SPE_ZU_* (Zubereitung) hat andere Dichte als SPE_PU_* (Pulver)
- Verschiedene Departments haben unterschiedliche Produkteigenschaften
- Blind den Median ALLER Artikel zu nehmen kann zu falschen Werten führen

**Beispiel - Gute Nutzung von array_context:**
```json
// Fehler: relDensityMin = 0 bei articles[10]
// TARGET: {"articleId": "SPE_ZU_kl", "departmentId": "20300", "workPlanId": "7202"}

// array_context zeigt (ungefiltert):
items_before: [
    {"articleId": "SPE_AR_fil", "departmentId": "10100", "relDensityMin": 0.02},
    {"articleId": "SPE_ZU_gr", "departmentId": "20300", "workPlanId": "7202", "relDensityMin": 0.01},
    {"articleId": "SPE_PU_kl", "departmentId": "30100", "relDensityMin": 0.05}
],
items_after: [
    {"articleId": "SPE_ZU_mi", "departmentId": "20300", "workPlanId": "7202", "relDensityMin": 0.01},
    {"articleId": "SPE_EM", "departmentId": "40100", "relDensityMin": 0.03}
]

// RICHTIGE Analyse:
// 1. Filtere nach departmentId="20300" + workPlanId="7202" → SPE_ZU_gr (0.01), SPE_ZU_mi (0.01)
// 2. Median = 0.01
// 3. Action: update_field, Target: articles[10].relDensityMin, New Value: 0.01
// 4. Reasoning: "Filtered array_context to same department (20300) and workplan (7202). Found 2 similar articles (SPE_ZU_gr, SPE_ZU_mi) with relDensityMin=0.01. Median is 0.01."

// FALSCHE Analyse (NICHT machen!):
// "Array context shows median of all items is 0.02" NOT OK.
// → Das würde SPE_AR (0.02), SPE_PU (0.05), SPE_EM (0.03) einbeziehen - FALSCH!
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

**KRITISCH - PRESERVE EXACT FORMAT:**
- **ÜBERNIMM das EXAKTE Format aus `last_search_results.json`**
- **Inklusive Leerzeichen, Unterstriche, Groß-/Kleinschreibung**
- **Ändere NUR den fehlerhaften Wert, NIEMALS korrekte Referenzen**
- **Beispiel**: Wenn korrekte ID "SP10        SP01" (mit Leerzeichen), dann korrigiere "SP10        SP0a" zu "SP10        SP01" - **NICHT** zu "SP10_SP01"!

**KRITISCH - KEINE DUPLIKATE IN ARRAYS:**

**ALLGEMEINE REGEL FÜR ALLE ARRAY-KORREKTUREN:**
Wenn du einen Wert in **IRGENDEINEM Array** korrigierst (predecessors, successors, workItems, functions, etc.), **VERMEIDE DUPLIKATE** im selben Array!

**5-SCHRITT PROZESS (immer gleich, unabhängig vom Array-Typ):**

1. **Original-Array identifizieren:**
   - Schaue in `last_search_results.json` → `original_object` 
   - Finde das betroffene Array-Feld (z.B. "predecessors", "workItems")
   - Liste ALLE aktuellen Werte im Array

2. **Fehlerhafte ID identifizieren:**
   - Identifiziere welcher Wert im Array ungültig/fehlerhaft ist
   - Notiere die Position (für Korrektur-Path)

3. **Kandidaten finden:**
   - Suche ähnliche gültige Werte in `all_equipment_keys`, `similar_items`, etc.
   - Berechne String-Ähnlichkeit (Levenshtein Distance) zum fehlerhaften Wert
   - Sortiere Kandidaten nach Ähnlichkeit (höchste zuerst)

4. **DUPLIKATE FILTERN (KRITISCH!):**
   - **Vergleiche JEDEN Kandidaten mit ALLEN Werten aus Schritt 1**
   - **Entferne Kandidaten die BEREITS im Array vorkommen**
   - **Auch wenn Kandidat sehr ähnlich ist - wenn Duplikat → AUSSCHLIESSEN!**

5. **FUNKTIONALE KOHÄRENZ PRÜFEN (NEU - DOMAIN-KONTEXT):**
   - **Bei Arrays: Analysiere die ANDEREN Elemente im selben Array**
   - **Erkenne funktionale Pattern:**
     * Gemeinsame Präfixe (z.B. alle starten mit "BPU", "APU")
     * Gemeinsame Equipment-Typen (z.B. alle sind "Pulver", "Abfueller", "Tank")
     * Gemeinsame Funktionen (aus `functions`-Feld oder Equipment-Namen)
   - **Wenn mehrere Kandidaten ähnliche String-Distance haben:**
     * Bevorzuge Kandidaten die zum funktionalen Pattern passen
     * Beispiel: Array ["APU01", "BPU03", "BbU01_typo"]
       - Kandidat "ABB01" (String-Distance=1, Funktion: "Abfueller Bag")
       - Kandidat "BPU01" (String-Distance=2, Funktion: "Pulvermischer")
       - Pattern-Analyse: APU01="Abfuellen Pulver", BPU03="Pulvermischer 1000"
       - **Wähle BPU01** trotz schlechterer Distance, weil funktional kohärent (alle Pulver)

6. **Besten Kandidaten wählen:**
   - Wähle aus den VERBLEIBENDEN (nicht-duplizierten) Kandidaten
   - **Primär-Kriterium: Funktionale Kohärenz mit Array-Kontext**
   - **Sekundär-Kriterium: Höchste String-Ähnlichkeit zum fehlerhaften Wert**
   - Bei gleichwertigen Kandidaten: Dokumentiere Pattern-Match im Reasoning

**KONZEPT-BEISPIEL (generisch anwendbar):**
```
Original-Array:     [VALUE_A_typo, VALUE_B]
Gültige Kandidaten: VALUE_A (sehr ähnlich), VALUE_B (sehr ähnlich), VALUE_C (ähnlich)

Schritt 4 - Duplikat-Filter:
  ✗ VALUE_A ähnlich zu VALUE_A_typo, ABER VALUE_A würde Duplikat erzeugen? Nein, ok
  ✗ VALUE_B ähnlich zu VALUE_A_typo, ABER VALUE_B BEREITS in Array → AUSSCHLIESSEN!
  ✓ VALUE_C verbleibend, keine Duplikate

ABER WENN VALUE_B NICHT im Array wäre:
  ✓ VALUE_A hat höchste Ähnlichkeit, wählen!
```

**WICHTIGE PRINZIPIEN:**
- NOT OK: **Häufigkeit ist IRRELEVANT:** Auch wenn ein Wert 100x vorkommt - wenn er bereits im Array ist → NICHT wählen!
- NOT OK: **Ähnlichkeit allein reicht nicht:** Erst filtern, dann nach Ähnlichkeit sortieren
- OK: **Duplikat-Check ist PFLICHT:** Bei JEDEM Array-Update, in JEDEM Kontext
- OK: **Prozess ist universell:** Gilt für Equipment, Articles, WorkItems, etc.

**Strategie - Typo-Korrektur (universell für alle ID-Typen):**
1. Analysiere die fehlerhafte ID und erkenne das Pattern
2. Suche in `last_search_results.json` nach ähnlichen existierenden IDs (nutze `all_equipment_keys`, `similar_items`, etc.)
3. **WICHTIG**: Berechne String-Ähnlichkeit (Levenshtein Distance) zu ALLEN Kandidaten
4. **WICHTIG**: Filtere Kandidaten die bereits im selben Array existieren (prüfe `original_object` im search_results)
5. **FUNKTIONALE KOHÄRENZ (KRITISCH!):** Analysiere das Array-Pattern:
   - Betrachte alle ANDEREN Werte im selben Array (aus `original_object`)
   - Identifiziere funktionale Gemeinsamkeiten (z.B. alle Equipment haben "Pulver" im Namen, alle starten mit "BP", "AP")
   - Wenn mehrere Kandidaten ähnliche String-Distance haben (Differenz ≤1):
     * Bevorzuge Kandidaten die funktional zum Array passen
     * Nutze Equipment-Namen, Funktionen, Präfixe zur Kategorisierung
   - Beispiel: Array ["APU01", "BPU03", "fehler"] sollte "BPU01" wählen (Pulver-Kontext) statt "ABB01" (Bag-Kontext)
6. **PATTERN-MATCHING (ZUSÄTZLICHER KONTEXT):** Wenn mehrere Kandidaten ähnlich gute String-Distance haben:
   - Prüfe `items_before` und `items_after` auf ähnliche Objekte
   - Suche nach gemeinsamen Array-Patterns (identische Präfix-Sequenzen)
   - Bevorzuge Werte die im Pattern-Kontext vorkommen, auch wenn String-Distance minimal schlechter
7. Wähle den Kandidaten der BESTE Kombination aus:
   - **Primär: Funktionale Kohärenz** (passt zum Domain-Kontext des Arrays)
   - **Sekundär: Pattern-Match** (kommt in ähnlichen Equipment-Konfigurationen vor)
   - **Tertiär: String-Ähnlichkeit** (minimale Levenshtein Distance)
   - **Constraint: Kein Duplikat** im selben Array
8. **Kopiere das EXAKTE Format (inklusive Leerzeichen) der korrekten ID aus search_results**
9. Korrigiere NUR die fehlerhafte Referenz - ändere NIEMALS bereits korrekte Werte

**KONZEPT-BEISPIEL (anwendbar auf alle Entity-Typen):**
```json
// Beispiel 1: Typo mit format preservation (Unterstriche)
// Vorher - "PREFIX_SUFFIXtypo" ist falsch (sollte "PREFIX_SUFFIX" sein)
"entity": [
    {"id": "REF_001", "refId": "PREFIX_SUFFIXtypo"}
],
"references": [
    {"id": "PREFIX_SUFFIX", "name": "..."}
]

// Nachher - Typo korrigiert (EXAKT "PREFIX_SUFFIX" aus references)
"entity": [
    {"id": "REF_001", "refId": "PREFIX_SUFFIX"}
],
"references": [
    {"id": "PREFIX_SUFFIX", "name": "..."}  // UNCHANGED!
]

// Beispiel 2: Typo mit Leerzeichen (CRITICAL FORMAT PRESERVATION)
// search_results zeigen:
// Result #1: validReferences[0].id = "KEY10      KEY01" (mit vielen Leerzeichen!)
// Result #2: entity[0].refId = "KEY10      KEY0a" (Typo: 'a' statt '1')

// Nachher - Typo korrigiert (PRESERVE EXACT SPACING!)
"entity": [
    {"id": "X", "refId": "KEY10      KEY01"}  // Mit exakt gleichen Leerzeichen!
]

// FALSCH wäre: "KEY10_KEY01" (Format geändert!)
// FALSCH wäre: "KEY10 KEY01" (Leerzeichen-Anzahl geändert!)

// Beispiel 3: Präfix-basiert
// Vorher - "PREFIX_AB" fehlt Suffix
"entity": [{"id": "D001", "refId": "PREFIX_AB"}],
"references": [{"id": "PREFIX_AB_full"}]

// Nachher - Korrigiert zu vollständiger ID
"entity": [{"id": "D001", "refId": "PREFIX_AB_full"}]

// Beispiel 4: Pattern-Matching in Arrays (KONTEXT-BASIERT)
// Vorher - "LT033" ist ungültig, zwei Kandidaten: LT03 (Distance=1), LT04 (Distance=2)
// original_object:
{
    "equipmentKey": "ABD01",
    "name": "Abfuellen Bag in Drum 01",
    "predecessors": ["ST06", "ST05", "ST03", "LT033"]
}

// items_before zeigt ähnliches Equipment:
{
    "equipmentKey": "ABB01",
    "name": "Abfuellen Bag in Box 01",  // Ähnlicher Name! ("Bag")
    "predecessors": ["ST06", "ST05", "ST03", "LTBB", "LT04"]  // Identische ersten 3 Werte!
}

// Pattern-Analyse:
// - ABB01 und ABD01 haben IDENTISCHE ersten 3 predecessors: ["ST06", "ST05", "ST03"]
// - Beide haben "Bag" im Namen (ähnlicher Equipment-Typ)
// - Beide haben gleiche Funktion: "Abfueller"
// - ABB01 verwendet LT04 an ähnlicher Position

// ENTSCHEIDUNG mit Pattern-Matching:
// - LT03: String-Distance = 1 (besser), ABER nicht im Pattern
// - LT04: String-Distance = 2 (schlechter), ABER im Pattern von ähnlichem Equipment
// → WÄHLE LT04 wegen Pattern-Match trotz schlechterer String-Distance

// Nachher - Pattern-basierte Korrektur
{
    "equipmentKey": "ABD01",
    "predecessors": ["ST06", "ST05", "ST03", "LT04"]
}

// Reasoning: "Pattern-matching with ABB01 (similar 'Bag' equipment) shows identical 
// predecessor prefix ['ST06', 'ST05', 'ST03'] followed by LT04. Despite LT03 having 
// better string similarity (distance=1 vs 2), LT04 is chosen based on contextual 
// pattern alignment with similar equipment type."

// Beispiel 5: Funktionale Kohärenz in Arrays (DOMAIN-KONTEXT)
// Vorher - "BbU01" ist ungültig in Pulver-Equipment Array
// original_object:
{
    "packaging": "71330",
    "predecessors": ["BbU01", "APU01", "BPU03"]
}

// Analyse der Array-Elemente (aus enriched_context):
// - APU01: "Abfuellen Pulver 01" (Funktion: Abfueller, Typ: PULVER)
// - BPU03: "Bearbeiten Pulvermischer 1000 01" (Funktion: BA-Anlage, Typ: PULVER)
// → Pattern: Beide Equipment sind PULVER-bezogen!

// Kandidaten für "BbU01":
// 1. ABB01: "Abfuellen Bag in Box 01" (Distance=1, Typ: BAG/BOX, Funktion: Abfueller)
// 2. BPU01: "Bearbeiten Pulvermischer 25 01" (Distance=2, Typ: PULVER, Funktion: BA-Anlage)
// 3. BPU02: "Bearbeiten Pulvermischer 300 01" (Distance=2, Typ: PULVER, Funktion: BA-Anlage)

// ENTSCHEIDUNG mit Funktionaler Kohärenz:
// - ABB01: String-Distance = 1 (BESTE), ABER funktional inkohärent (Bag vs Pulver)
// - BPU01: String-Distance = 2 (schlechter), ABER funktional kohärent (Pulver-Kontext!)
// - BPU02: String-Distance = 2 (schlechter), funktional kohärent
// → WÄHLE BPU01 wegen funktionaler Kohärenz trotz schlechterer String-Distance

// Nachher - Funktional kohärente Korrektur
{
    "packaging": "71330",
    "predecessors": ["BPU01", "APU01", "BPU03"]
}

// Reasoning: "Array context analysis shows all other predecessors are PULVER equipment: 
// APU01 (Abfuellen Pulver) and BPU03 (Pulvermischer 1000). Candidates: ABB01 (distance=1, 
// Bag-in-Box equipment) vs BPU01 (distance=2, Pulvermischer 25). Despite worse string 
// similarity, BPU01 is chosen for functional coherence - maintaining consistent PULVER 
// equipment type throughout the array."
```

**Analyse-Kriterien:**
- Gemeinsame Präfixe/Suffixe
- Ähnliche Zeichenketten
- **Funktionale Kohärenz im Array-Kontext (DOMAIN LOGIC)**
- **Pattern-Matching bei ähnlichen Objekten (items_before/after)**
- Kontext aus `last_search_results.json` nutzen
- Bei mehreren Kandidaten: Wähle ID mit bester Kombination aus:
  1. **Funktionale Kohärenz** (passt zum Equipment-Typ der anderen Array-Elemente)
  2. **Pattern-Matching** (kommt in ähnlichen Konfigurationen vor)
  3. **String-Ähnlichkeit** (Levenshtein Distance)

**Action:** `update_field` - Ändere die fehlerhafte Referenz zur korrekten ID

---

## 4. Fehlende Array-Elemente (validate_work_item_configs_completeness)

**Problem:** Ein Objekt hat ein fehlendes Pflicht-Element in einem Nested-Array.

**Beispiel:** "Article SPE_AR_fil is missing work_item_configs for: VOAR01"

### 4.1 KRITISCH: Placeholder-Erkennung ZUERST prüfen!

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

### 4.2 Standard-Strategie (wenn KEIN Placeholder)

**Wenn das Element tatsächlich komplett fehlt:**
1. Suche ähnliche Objekte im gleichen Array (`array_context`)
2. Prüfe `enriched_context` für typische Werte des fehlenden Elements
3. Kopiere Struktur und typische Werte vom ähnlichsten Objekt
4. Füge das fehlende Element zum Array hinzu

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