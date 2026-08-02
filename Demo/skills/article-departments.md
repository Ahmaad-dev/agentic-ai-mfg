---
name: article-departments
applies_to: [ARTICLE_DEPARTMENT_PRESENCE, ARTICLE_EQUIPMENT_DEPARTMENT_CONSISTENCY]
description: Artikel hat keine departmentId oder sein Department ist in keinem Equipment abgedeckt.
---

# Card: Article departments

Tags: `[validate_article_department_presence]`,
`[validate_article_equipment_department_consistency]`.

## Fehlendes Artikel-Department

1. Denselben `articleId` in einem bestätigten gültigen Snapshot suchen.
2. Falls nicht vorhanden, nur eine eindeutig konsistente Zuordnung aus Artikelstamm,
   Produktfamilie, `departmentName` und `workPlanId` verwenden.
3. Prüfen, dass die Ziel-ID in mindestens einem `equipment[].departments` vorkommt.
4. Nur `articles[i].departmentId` korrigieren; `departmentName` nur ändern, wenn dessen
   falscher Wert ebenfalls eindeutig belegt ist.

Die Menge vorhandener Equipment-Departments zeigt nur erlaubte IDs, aber nicht automatisch
das richtige Department für den Artikel. Keine beliebige vorhandene ID wählen.

## Department ohne Equipment-Abdeckung

Zuerst Ursache unterscheiden:

- **Artikelwert ist Tippfehler/veraltet:** Artikel-Department anhand desselben Artikels aus
  gültiger Historie korrigieren.
- **Equipment-Konfiguration fehlt:** Department nur bei den exakt belegten Equipment-Objekten
  ergänzen, wenn eine gültige historische oder autoritative Konfiguration dies zeigt.

Nie das unbekannte Department pauschal an ein beliebiges Equipment anhängen. Equipment muss
zusätzlich fachlich zum Work-Item, Prozess, Batchbereich und zur Qualifikation passen.

`Equipment without departments ...` ist nur eine Warnung und wird nicht korrigiert.

