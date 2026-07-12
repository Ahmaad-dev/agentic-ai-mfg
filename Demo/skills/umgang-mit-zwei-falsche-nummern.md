---
name: negative-dichtewerte
description: Wenn ein Dichtewert (relDensityMin / relDensityMax) NEGATIV ist — dann wurde beim Erfassen das Vorzeichen falsch gesetzt und muss nur umgedreht werden.
---

# Negative Dichtewerte: Vorzeichenfehler

## Wann

Wenn sowas passiert oder entdeckt wird:

    "relDensityMin": -2,
    "relDensityMax": -6,

## Was zu tun ist

Dann ist der Fix einfach: anstatt das "-", einen "+" zu hinterlegen.

    "relDensityMin": -2,   ->   "relDensityMin": 2,
    "relDensityMax": -6,   ->   "relDensityMax": 6,

## Wann NICHT

Gilt nur für NEGATIVE Werte. Ist der Wert 0 oder fehlt er, ist es kein Vorzeichenfehler —
dann muss der Wert aus vergleichbaren Artikeln abgeleitet werden (siehe `density-values.md`).
