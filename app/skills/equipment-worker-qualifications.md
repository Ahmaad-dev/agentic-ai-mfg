---
name: equipment-worker-qualifications
applies_to: [EQUIPMENT_WORKER_QUALIFICATION_COMPATIBILITY]
description: Equipment verlangt eine Qualifikation, die kein Worker in einer zulässigen Kategorie besitzt.
---

# Card: EQUIPMENT_WORKER_QUALIFICATION_COMPATIBILITY

Tag: `[validate_equipment_worker_qualification_compatibility]`.

## Harte Fehler

### Keine Worker-Qualifications vorhanden

Eine vollständige Qualifikationsmatrix nicht aus Namen, Equipment oder Nachbarobjekten
synthetisieren. Nur aus dem zuständigen Personal-/Qualifikationsstamm oder einem bestätigten
gültigen Snapshot wiederherstellen.

### Benötigte Qualifikation fehlt

1. Prüfen, ob `equipment[].qualification` ein Tippfehler gegenüber existierenden
   Qualifikationsnamen ist.
2. Historie desselben Equipments als stärksten Beleg verwenden.
3. Falls die Equipment-Anforderung korrekt ist, eine Worker-Qualifikation nur aus einer
   autoritativen Personalquelle wiederherstellen.
4. Kategorie muss in den konfigurierten erlaubten Kategorien liegen, typischerweise `A` oder `Q`.

Nie einem Worker eine Befähigung allein deshalb erteilen, weil der Validator sie benötigt.
Das wäre sicherheits- und personenbezogen fachlich falsch. Bei fehlender Personal-Evidenz
eskalieren statt mutieren.

`Qualifications with fewer than 3 workers ...` und nicht verwendete Qualifikationen sind
Warnungen; dafür keine Korrektur ausgeben.

