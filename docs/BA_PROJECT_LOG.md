# Bachelorarbeit — Projektprotokoll

Graph-basierte Systemarchitektur vs. monolithische Systemprompt-Struktur.
Ein Eintrag je abgeschlossener Einheit, **neueste unten**.

> Vorgänger: `PROJECT_LOG.md` (PT4, abgeschlossen 2026-08-15). Bewusst getrennt — siehe die
> Begründung dort. PT4 ist Nachweis für das Praxisprojekt, dieses Protokoll für die Arbeit.

---

## Eintragsformat

```
### [DATUM] — [Kapitel/Baustein] [Kurztitel]
- **Status:** done / partial / blocked
- **Changed files:** ...
- **Was getan wurde:** 1–3 Sätze.
- **Verifikation:** wie geprüft (Testlauf, Messung, manuell) — mit dem tatsächlichen Ergebnis.
- **Offen / nächstes:** was bleibt.
```

**Bei Messläufen zusätzlich verpflichtend**, sonst ist die Zahl später wertlos:

```
- **Lauf-Metadaten:** Variante (monolith/graph) · RULEBOOK_MODE · Modell + API-Version ·
  Temperatur und übrige Parameter · Fall-IDs · Wiederholungen · Zeitstempel · Pfad der Rohdaten
```

---

## Was dieses Protokoll leisten muss

Es ist die **Rückverfolgbarkeit** der Arbeit. Jede Zahl, die später in Kapitel 7 steht, muss
sich hier bis zu ihrem Lauf zurückverfolgen lassen: welche Variante, welche Bedingungen,
welche Rohdaten. Ohne diese Kette ist eine Aussage nicht belastbar — und ein Gutachter fragt
genau danach.

Zwei Regeln, die aus PT4 mitgenommen werden, weil sie dort Geld und Zeit gekostet haben:

1. **Was gemessen wurde, wird notiert — auch wenn es nicht gefällt.** Ein Lauf, der gegen die
   Erwartung ausfällt, gehört genauso ins Protokoll wie ein bestätigender. Nachträgliches
   Anpassen nach dem Sehen der Ergebnisse ist ausgeschlossen; fällt doch etwas auf, wird es
   ausdrücklich als **Nachmessung** gekennzeichnet.
2. **Vermutungen werden als solche benannt.** „Vermutlich lag es an X" ist ein zulässiger
   Eintrag. „Es lag an X" ohne Beleg ist es nicht.

---

### 2026-08-15 — Start Bachelorarbeit: Arbeitsumgebung umgestellt
- **Status:** done
- **Changed files:** `CLAUDE.md`, `.github/instructions/instructions.md`, `docs/PT4_PLAN.md`,
  `docs/PROJECT_LOG.md`, `docs/BA_PROJECT_LOG.md` (neu)
- **Was getan wurde:** PT4 abgeschlossen und die Arbeitsumgebung auf die Bachelorarbeit
  umgestellt. Die Agenten-Instruktionen (`CLAUDE.md` und die daraus abgeleitete
  `instructions.md`) verweisen jetzt auf Exposé, Masterplan und Umsetzungsplan statt auf den
  PT4-Plan und tragen die Regeln, die den Vergleich schützen: Koexistenz statt Ersetzen, keine
  Strohmann-Baseline, eingefrorene Kontrollbedingungen, keine erfundenen Messergebnisse, erst
  Protokoll dann messen. `PT4_PLAN.md` und `PROJECT_LOG.md` sind als abgeschlossen
  gekennzeichnet und bleiben als Nachweis erhalten.
- **Verifikation:** Beide Instruktionsdateien enthalten keinen `demo/`-Pfad mehr (die alte
  `instructions.md` verwies noch auf den vor dem 02.08. gültigen Ordnernamen) und sind
  inhaltsgleich, weil die zweite aus der ersten abgeleitet wird — zwei abweichende Fassungen
  wären zwei Wahrheiten.
- **Drei Befunde beim Prüfen des Ist-Stands** (gegen den Code, nicht aus den Plänen
  abgeschrieben):
  * `RULEBOOK_MODE` steht in `app/core/agent_config.py` auf **`"cards"`**, nicht auf
    `"monolith"`. Ein Baseline-Lauf ohne ausdrückliches Setzen misst damit **nicht** den
    Monolithen. Der Masterplan nennt das seinen wichtigsten Einzelpunkt (Kap. 6.1); es steht
    jetzt als Falle in `CLAUDE.md`.
  * **`langgraph` ist nicht installiert**, und es existiert keine Zeile Graph-Code
    (Volltextsuche nach `StateGraph|GraphState|SP_ARCHITECTURE_MODE`: kein Treffer). Die
    Framework-Entscheidung ist getroffen, aber nicht umgesetzt.
  * **Das Modell-Deployment steht auf `gpt-4.1`** und deckt sich damit mit dem Exposé. Der im
    Umsetzungsplan (Kap. 4/12) benannte Konflikt GPT-4.1 gegen `gpt-4o` ist damit
    **aufgelöst** — die Pläne beschreiben hier einen überholten Stand.
- **Offen / nächstes:** Nach Masterplan Kap. 23, in dieser Reihenfolge: `RULEBOOK_MODE`-Historie
  der bestehenden Ergebnisdateien klären, sauberer Monolith-Baseline-Lauf mit
  `RULEBOOK_MODE=monolith`, dann `langgraph` pinnen und den `SP_ARCHITECTURE_MODE`-Schalter
  einbauen.

---

### 2026-08-15 — Link-Prüfer für die Doku-Umstrukturierung
- **Status:** done
- **Changed files:** `app/eval/check_doku_links.py` (neu), `docs/PROJECT_LOG.md`,
  `app/README-PT4.md` (je Verweise nachgezogen)
- **Was getan wurde:** Beim Umsortieren nach `docs/04_PT4/` sind fünf Verweise ins Leere
  gelaufen (drei in `PROJECT_LOG.md`, zwei in `README-PT4.md`) — lautlos, wie immer bei
  Markdown. Die fünf sind gezogen; dazu ein wiederholbarer Prüflauf, der jeden lokalen
  Verweis auflöst.
- **Verifikation:** Lauf über alle Markdown-Dateien des Repositories. Die vier heute
  umgestellten Dateien (`CLAUDE.md`, `instructions.md`, `PT4_PLAN.md`, `BA_PROJECT_LOG.md`)
  sind sauber.
- **Zweimal nachgeschärft, weil eine Prüfung mit Fehlalarmen wertlos ist:**
  1. Erste Fassung: 1672 Treffer, fast alle falsch. Ein blosser Dateiname in Backticks
     (`short_term.py`) ist eine ERWÄHNUNG im Fliesstext, keine Ortsangabe. Jetzt zählt nur,
     was einen Schrägstrich enthält.
  2. Zweite Fassung: 836 Treffer, davon 690 aus den Protokollen. Deren `demo/`-Pfade sind
     GESCHICHTE — sie waren am Eintragsdatum richtig, der Ordner heisst erst seit dem 02.08.
     `app/`. Sie nachträglich umzuschreiben wäre Geschichtsfälschung. In Protokollen werden
     jetzt nur noch die klickbaren Links geprüft.
- **Verbleibend: 149 Verweise**, davon **98 veraltete `demo/`-Pfade** in PT4-Dokumenten, die
  ebenfalls historisch sind, sowie Verweise auf Dateien, die es nie gab oder die mit dem
  Umbau verschwunden sind (`docs/HANDOVER.md`, `docs/Zwischenstand-Abschluss-AP2.md`).
  **Bewusst nicht angefasst** — das sind PT4-Dokumente, und ihre Bereinigung ist eine
  inhaltliche Entscheidung des Nutzers, keine technische.
- **Offen / nächstes:** Nach Abschluss der Doku-Umstrukturierung erneut laufen lassen; er
  meldet dann genau die Verweise, die der Umbau gebrochen hat.
