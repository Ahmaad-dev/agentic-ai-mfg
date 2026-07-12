---
name: density-values
applies_to: [DENSITY_VALUES]
description: Numerische Werte aus array_context ableiten (Gruppenfilter, Median)
---

# Card: DENSITY_VALUES  (`[validate_density_values]`)

Deriving a numeric field value from array_context — worked examples.
The general principle ("filter to the same group first") lives in `_core.md`; this card carries
the detailed examples.
Source: `llm-validation-fix-rules.md` lines 208–282 (inventory rule R22).

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
