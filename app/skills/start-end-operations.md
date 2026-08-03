---
name: start-end-operations
applies_to: [START_END_OPERATION_EXISTENCE]
description: HE01 oder ABF01 fehlt in workItemConfigs oder besitzt keine positive Zeit.
---

# Card: START_END_OPERATION_EXISTENCE

Tag: `[validate_start_end_operation_existence]`.

## Fehlendes HE01 oder ABF01

1. Prüfen, ob der Key nur durch einen Placeholder ersetzt wurde.
2. Exakte Config desselben Artikels aus gültiger Historie bevorzugen.
3. Sonst mehrere Artikel mit gleichem Department und Workplan vergleichen.
4. Element an der belegten Prozessposition einsetzen, ohne andere Keys umzusortieren.

Typische Reihenfolge im vorliegenden Workplan: `... WART01, HE01, ... WART03, ABF01, WART04`.
Der konkrete Workplan und ein Referenzartikel bleiben maßgeblich.

## Keine positive Zeit

Für HE01 und ABF01 muss mindestens eines gelten:

- `rampUpTime > 0`
- `netTimeFactor > 0`

Nicht pauschal `1` einsetzen. Beide Werte aus demselben Artikel in gültiger Historie oder aus
fachlich gleichen Artikeln übernehmen. Nur die fehlerhaften Felder ändern. Ist bereits einer
der beiden Werte positiv, keine unnötige Änderung vornehmen.

Eine Ergänzung kann gleichzeitig einen
`validate_work_item_configs_completeness`-Error beheben; danach alle Errors erneut sammeln.

