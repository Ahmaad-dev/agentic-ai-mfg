---
name: references
applies_to: [DEMAND_ARTICLE_IDS, EQUIPMENT_PREDECESSOR_REFERENCES, EQUIPMENT_CONNECTIVITY]
description: Ungültige Referenzen (Typo-Korrektur, Duplikat-Filter, funktionale Kohärenz)
---

# Card: Invalid / broken references

Tags: `[validate_demand_article_ids]`, `[validate_equipment_predecessor_references]`,
`[validate_equipment_connectivity]`.
Source: `llm-validation-fix-rules.md` lines 160–203 and 367–597 (inventory rules R6, R9–R14).

## Ungültige Referenzen

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

5. **FUNKTIONALE KOHÄRENZ PRÜFEN (DOMAIN-KONTEXT):**
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

## KRITISCH: Domain-Intelligence — Packaging Equipment Pattern Analysis

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
