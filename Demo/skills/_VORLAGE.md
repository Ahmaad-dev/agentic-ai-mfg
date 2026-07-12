---
name: vorlage
description: KURZ und in normaler Sprache — wann soll der Agent diese Karte lesen?
---

# So legst du eine neue Regel an

Kopiere diese Datei, gib ihr einen sprechenden Namen (`umgang-mit-negativen-dichten.md`),
schreib deine Regel rein — fertig. **Kein Code, kein Deploy, kein Entwickler.**

Dateien, die mit `_` beginnen (wie diese hier und `_core.md`), sind KEINE Regelkarten.
`_core.md` wird immer geladen; diese Vorlage wird nie geladen.

---

## Das Einzige, was wirklich zählt: die `description`

```
---
description: Wenn eine Dichte (relDensityMin/Max) negativ ist — dann wurde beim Erfassen
             das Vorzeichen falsch gesetzt und muss umgedreht werden.
---
```

Der Agent bekommt bei JEDEM Fehler ein Inhaltsverzeichnis **aller** Karten zu sehen — nur
Dateiname plus diese Beschreibung. Daraus entscheidet er selbst, welche Karten er zu diesem
konkreten Fehler liest. **Er hat also jederzeit Zugriff auf den gesamten Regelbestand, lädt
aber nur, was er braucht.**

Deshalb: **Beschreibe, WANN die Regel gilt, nicht WAS sie tut.** Der Agent entscheidet anhand
der Beschreibung, ob er weiterlesen soll.

- Gut:      `Wenn ein Dichtewert negativ ist (Vorzeichenfehler bei der Erfassung).`
- Schlecht: `Dichteregeln.` — daraus kann der Agent nicht erkennen, wann sie greift.

Ohne `description` nimmt der Loader notdürftig die erste Zeile deines Textes. Das
funktioniert, ist aber schlechter — schreib die Beschreibung.

---

## Optional: `applies_to` (nur wenn du den Validator kennst)

```
---
applies_to: [DENSITY_VALUES]
---
```

Das ist eine **Abkürzung**, kein Muss. Nennst du hier das Tag des Validators, wird die Karte
bei diesem Fehlertyp **immer garantiert** geladen — ohne dass der Agent entscheiden muss.

Das Tag steht vorne in jeder Fehlermeldung von Smart Planning:

```
[validate_density_values] Article 100005 has invalid rel_density_min: -2
 ^^^^^^^^^^^^^^^^^^^^^^^^  ->  applies_to: [DENSITY_VALUES]
```

Bekannte Tags: `UNIQUE_IDS`, `DEMAND_ARTICLE_IDS`, `DEMAND_UNIQUENESS`, `DENSITY_VALUES`,
`WORK_ITEM_CONFIGS_COMPLETENESS`, `START_END_OPERATION_EXISTENCE`, `WORK_PLAN_IDS`,
`EQUIPMENT_PREDECESSOR_REFERENCES`, `EQUIPMENT_CONNECTIVITY`, `EQUIPMENT_DEPARTMENT_PRESENCE`,
`EQUIPMENT_UNAVAILABILITY_CONSISTENCY`, `EQUIPMENT_WORKER_QUALIFICATION_COMPATIBILITY`,
`WORKER_CONSISTENCY`.

**Wenn du das Tag nicht kennst: lass es einfach weg.** Die Karte wird trotzdem gefunden.

---

## Mehrere Karten für dieselbe Fehlerart sind erlaubt

Du musst eine bestehende Karte nicht anfassen. Leg einfach eine neue daneben — sie wird
zusätzlich geladen. So ergänzt du einen Sonderfall, ohne etwas kaputt zu machen.

---

## Der Regeltext selbst

Schreib ihn so, wie du ihn einem neuen Kollegen erklären würdest. Ein Beispiel mit echten
Daten ist mehr wert als drei Absätze Theorie.

```
## Wann

Wenn relDensityMin oder relDensityMax einen negativen Wert hat.

## Was zu tun ist

Das Vorzeichen wurde bei der Erfassung falsch gesetzt. Dreh es um: aus -2 wird 2.

## Beispiel

    "relDensityMin": -2,   ->   "relDensityMin": 2,
    "relDensityMax": -6,   ->   "relDensityMax": 6,

## Wann NICHT

Wenn der Wert 0 ist — dann fehlt er, und der Wert muss aus vergleichbaren Artikeln
abgeleitet werden (siehe density-values.md).
```

---

## Wo die Dateien liegen

- **Lokal:** `demo/skills/`
- **Cloud:** Blob-Prefix `skills/` im konfigurierten Storage-Container (`STORAGE_MODE=AZURE`).
  Derselbe Code, kein Unterschied — du bearbeitest die Regeln im Storage Account, ohne die
  Anwendung neu zu deployen.
