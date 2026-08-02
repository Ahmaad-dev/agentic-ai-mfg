---
name: packaging-references
applies_to: [PACKAGING_EQUIPMENT_COMPATIBILITY_REFERENCES, PACKAGING_REFERENCES]
description: Ungültige oder leere Packaging-Referenzen und Packaging-Equipment-Vorgänger.
---

# Card: Packaging references

Tags: `[validate_packaging_equipment_compatibility_references]`,
`[validate_packaging_references]`.

## Ungültiger Equipment-Vorgänger

Korrigiere `packagingEquipmentCompatibility[].predecessors[]` nur auf einen existierenden
`equipmentKey`. Bevorzuge die exakte Vorgängerliste derselben Packaging-ID aus einem gültigen
Snapshot. Bei einem eindeutigen Tippfehler zusätzlich Funktion und Array-Kontext prüfen und
keine Duplikate erzeugen.

## Packaging ohne Vorgänger

Eine leere Liste ausschließlich aus einer autoritativen Zuordnung derselben Packaging-ID
wiederherstellen. Keine Liste anhand numerischer Nähe der Packaging-ID, Nachbarposition oder
größtmöglicher Kettenlänge kopieren.

## Demand referenziert unbekanntes Packaging

1. Denselben `demandId` in gültiger Historie suchen.
2. Danach gleiche Auftrags-/VGNR-Gruppe und denselben Artikel prüfen.
3. `article.standardPackaging` nur als Kandidat, nicht automatisch als Beweis behandeln.
4. Zielwert muss im Packaging-Katalog existieren.

## Artikel referenziert unbekanntes Standard-Packaging

Denselben `articleId` aus gültiger Historie verwenden. Nur bei eindeutiger Produktvariante
auf fachlich gleiche Artikel zurückgreifen. Kein neues Packaging anlegen.

`No packaging equipment compatibility data found` ist eine Warnung und wird nicht korrigiert.

