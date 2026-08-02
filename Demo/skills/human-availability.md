---
name: human-availability
applies_to: [HUMAN_AVAILABILITY_EXISTS]
description: Im vollständigen Solverlauf fehlt workerAvailability für den schichtbasierten Planungsstart.
---

# Card: HUMAN_AVAILABILITY_EXISTS

Tag: `[_validate_human_availability_exists]` beziehungsweise
`[validate_human_availability_exists]`.

Diese harte Prüfung gehört zum vollständigen Solverlauf und wird nicht vom Message-Collector
des `/validate-snapshot`-Endpunkts ausgeführt.

## Vorgehen

1. Planungsmodus prüfen.
2. Bei schichtbasiertem Modus `workerAvailability` aus dem zuständigen Schichtsystem oder
   einem für denselben Planungszeitraum bestätigten Snapshot wiederherstellen.
3. Worker-IDs mit `workerQualifications` und Zeitintervalle auf Konsistenz prüfen.
4. Alternativ nur nach ausdrücklicher fachlicher Freigabe auf `demand_driven` umstellen.

Keine Schichten, Worker oder Verfügbarkeitszeiten aus Nachbarwerten erfinden. Historische
Schichten eines anderen Tages nicht ungeprüft kopieren.

Eine reine Warning `No worker availability defined` aus `validate_worker_consistency` bleibt
ohne Mutation, solange der ausgeführte Planungsmodus keine harte Availability-Prüfung auslöst.
