---
name: equipment-work-items
applies_to: [WORK_ITEM_EQUIPMENT_AVAILABILITY]
description: Für einen vom Arbeitsplan benötigten Work-Item-Key existiert kein kompatibles Equipment.
---

# Card: WORK_ITEM_EQUIPMENT_AVAILABILITY

Tag: `[validate_work_item_equipment_availability]`.

## Vorgehen

1. Fehlende Keys aus der Error-Meldung übernehmen.
2. Prüfen, welche von Demands benötigten Workplans diese Keys verlangen.
3. Ursache unterscheiden:
   - Tippfehler/Placeholder in `equipment[].workItems`
   - falscher Work-Item-Key im Workplan
   - tatsächlich fehlende Equipment-Stammdaten
4. Exakte gültige Historie desselben Equipments beziehungsweise Workplans bevorzugen.
5. Bei Equipment zusätzlich Department, Funktion, Kapazität, Qualifikation und
   Vorgängerstruktur prüfen.

Nur einen nachweislich falschen Key ersetzen oder einen historisch belegten Key in das
Equipment-Array zurücksetzen. Dabei keine Duplikate erzeugen und die übrige Reihenfolge erhalten.

Nie einen benötigten Key an irgendein Equipment anhängen, nur um den Validator zu beruhigen.
Wenn kein geeignetes Equipment autoritativ belegt ist, keine automatische Korrektur ausgeben.

Die Keys `QS01`, `QS02` und `WART01` bis `WART04` sind von dieser harten Prüfung ausgenommen.

