---
name: work-plan-ids
applies_to: [WORK_PLAN_IDS]
description: Artikel referenziert eine workPlanId, die im workPlans-Katalog nicht existiert.
---

# Card: WORK_PLAN_IDS (`[validate_work_plan_ids]`)

## Ziel

Eine ungültige `articles[].workPlanId` auf eine bereits existierende, fachlich belegte
`workPlans[].workPlanId` korrigieren. Niemals einen neuen Workplan erfinden.

## Vorgehen

1. Alle in der Fehlermeldung genannten Workplan-IDs und betroffenen Artikel bestimmen.
2. Zuerst denselben `articleId` in einem bestätigten gültigen Snapshot suchen.
3. Danach nur Artikel mit gleichem Department, gleicher Produktfamilie und gleichem
   Prozessprofil als Vergleich verwenden.
4. Kandidat muss exakt in `workPlans[].workPlanId` existieren.
5. Exakten String einschließlich mehrfacher Leerzeichen übernehmen.
6. Nur `articles[i].workPlanId` ändern und erneut validieren.

String-Ähnlichkeit allein ist kein Beweis. Bei mehreren fachlich plausiblen Workplans keine
Mutation erzeugen, sondern die Kandidaten und fehlende Evidenz melden.

```json
{
  "action": "update_field",
  "target_path": "articles[1].workPlanId",
  "current_value": "SP10        SP0a",
  "new_value": "SP10        SP01",
  "reasoning": "The exact workPlanId is used by the same article in the last valid snapshot and exists in workPlans. Spacing is preserved."
}
```

