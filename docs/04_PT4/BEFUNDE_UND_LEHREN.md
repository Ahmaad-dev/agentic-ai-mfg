# Befunde und Lehren — 14. bis 15.08.2026

**Was dieses Dokument ist.** `PROJECT_LOG.md` erzählt chronologisch, was wann getan wurde.
`AGENTEN_ARCHITEKTUR.md` beschreibt den Zustand des Systems. Dieses Dokument beantwortet die
dritte Frage: **was haben wir gelernt, und woran erkennt man es beim nächsten Mal?**

In zwei Tagen wurden 16 Fehler gefunden. Nicht alle waren Zufall — die meisten fallen in
sechs wiederkehrende Muster. Die Muster sind der eigentliche Ertrag; die Einzelfälle stehen
darunter als Belege.

---

## Teil I — Die sechs Muster

### 1. Ein Schritt, der sein Ergebnis nicht liefert, meldet trotzdem Erfolg

Am häufigsten. Ein Werkzeug läuft, tut nichts Nützliches, gibt Exit-Code 0 zurück, und der
Fehler zeigt sich Schritte später an einer Stelle, die nichts dafür kann.

| Fall | Was geschah | Wo es auffiel |
|---|---|---|
| `trigger_identify_tool` | Rückgabewert True/False wurde **verworfen** | zwei Schritte später |
| `identify_error_llm` | meldete Erfolg ohne Suchergebnis | in `generate_correction_llm` |
| Download-Runde | „Download erfolgreich" ohne geschriebene Datei | erst beim Korrekturlauf |

**Regel:** Ein Schritt ist erst erfolgreich, wenn sein *Ergebnis* vorliegt — nicht, wenn er
ohne Ausnahme zurückkehrt. Rückgabewerte auswerten, Vorbedingungen vorher prüfen, und im
Fehlerfall benennen, **was** fehlt statt zu raten, **wer** schuld ist.

### 2. Wissen liegt vor, erreicht aber den Empfänger nicht

Kein Fehler in der Berechnung — die Information existiert, wird nur nicht durchgereicht.

- `revalidation_result` stand in der Datenbank (`errors_before=3, errors_after=2`), aber
  `get_decisions_for_snapshot()` gab sie nicht zurück.
- `agent_name` wurde bei jeder Nachricht **geschrieben und nie gelesen**.
- `similar_items` wurde korrekt über `departmentId` gebildet, trug aber nur Dichtewerte —
  bei einer Frage nach Zeitwerten war das richtige Kollektiv stumm.
- Review-Links waren reine Pfade; das Modell kannte den Host nicht und **konnte** keinen
  vollständigen Link liefern.

**Regel:** Wenn ein Agent etwas Falsches sagt, zuerst prüfen, ob er es überhaupt wissen
konnte. Meist ist es ein Datenweg, kein Prompt.

### 3. Eine starre Regel bestraft irgendwann die richtige Antwort

Betraf vor allem die Prüfungen, aber auch die Prompts.

- Verbot der Wörter „fehlerfrei/valide/einsatzbereit" — schlug an, als der Snapshot
  **wirklich** fehlerfrei war.
- Feste Erwartung „2 Fehler, HE01" — nach einer Freigabe schlicht überholt.
- Wortlisten für „nichts geändert" — dreimal an freier Formulierung gescheitert.
- Im Prompt: „DETAILLIERTE Antworten" gegen „2-3 Sätze" — ein unerfüllbarer Widerspruch,
  den das Modell jedes Mal gleich auflöste.

**Regel:** Prüfe die **Aussage**, nicht den Wortlaut, und leite Erwartungen aus den Daten
ab statt sie festzuschreiben. Eine Regel, die auch dann gilt, wenn die Welt anders ist,
ist keine Regel, sondern ein blinder Fleck.

### 4. Eine Abkürzung überspringt eine Quelle, von der niemand wusste

Die teuerste Klasse, weil sie durch eine *Verbesserung* entsteht.

Die Optimierung „Intent aus dem Plan lesen statt ein zweites Mal fragen" nahm die
Snapshot-ID aus der **Historie**. Der ersetzte LLM-Aufruf hatte den Nutzertext im Prompt und
las die ID auch aus der **aktuellen Nachricht** — diese Quelle fiel weg. Folge: der Nutzer
verlangte `9faf89b1`, geladen wurde `a810d470`.

**Regel:** Bevor ein LLM-Aufruf durch Logik ersetzt wird, aufschreiben, **welche Eingaben er
hatte**. Was die Logik nicht liest, geht verloren — und zwar still.

### 5. Sonderzeichen überleben den Weg durch eine Shell nicht

Drei eigene Fehler an einem Tag, alle unsichtbar in der Datei.

- `\25B8` wurde als Oktal-Escape gelesen → Steuerzeichen `0x15` in der CSS-Datei, im
  Browser stand „BE Liste mit 13 Einträgen".
- Backticks in Kommentaren wurden dreimal als Kommandosubstitution verschluckt.
- `\n` in Zeichenketten wurde zum echten Zeilenumbruch → Syntaxfehler.

**Regel:** Sonderzeichen nie als Escape durch eine Shell schicken. Direkt schreiben, aus
`chr()` bauen oder die Datei mit einem Editor-Werkzeug anfassen. Und: `grep` zeigt
Steuerzeichen nicht — bei unerklärlichen Anzeigefehlern `repr()` der Zeile ansehen.

### 6. Ein Flex-Kind ist so breit wie sein längstes unbrechbares Wort

Zweimal derselbe Layout-Fehler an verschiedenen Stellen.

- Dashboard: der aufgeklappte Vorbehalt sprengte die Karte und quetschte die Überschrift.
- Review Board: der grüne „Wert ist belegt"-Kasten lief 57 px über den Rand, weil
  `packagingEquipmentCompatibility[1].predecessors` keine Trennstelle hat.

**Regel:** Text in einem Flex-Kasten braucht `min-width: 0`. Enthält er technische
Bezeichner, zusätzlich `overflow-wrap: anywhere` — `min-width` allein bricht das Wort nicht.

---

## Teil II — Die Einzelbefunde

### A. Der Agent behauptete Erfolge, die es nicht gab (14.08.)

Drei Falschaussagen in einem Lauf: „Alle kritischen Fehler wurden behoben" (es war ein
Vorschlag für **einen von drei**), „Der Snapshot ist jetzt valide und vom Server akzeptiert"
(es wurde **nichts** geschrieben), „vollständig fehlerfrei und einsatzbereit" (die Freigabe
selbst meldete `3 → 2 Fehler`).

**Ursache:** Muster 2. Für `analyze_only` stand nur „Status: success" im Kontext;
`final_validation` wird nur für Pipelines berechnet, die unter HitL gar nicht laufen. Und
`revalidation_result` wurde vom Repository verschluckt.

**Behoben:** `_describe_analysis_scope()` meldet die Reichweite, `get_decisions_for_snapshot()`
liefert die Nachvalidierung, `_facts_block()` rendert Zahlen deterministisch aus dem Code
statt sie einem Modell zu überlassen.

### B. Sechs Stellen, an denen Wissen nicht ankam (15.08.)

Aus einem Audit auf Nachfrage. Der schwerwiegendste: `last_snapshot_metadata` war ein
Attribut am **prozessweiten** Orchestrator — alle Chat-Sitzungen teilten sich den Wert, in
der Cloud auch verschiedene Nutzer. Dazu: nie aufgefrischt, Entscheidungen nur im Chat-Pfad,
200-Zeichen-Kürzung im Mehrschritt, offene Vorschläge nirgends, Snapshot-Erkennung rein
textuell.

**Behoben:** Fokus-Snapshot je Sitzung (nur die ID, Zustand wird jedes Mal frisch gelesen),
Entscheidungen und offene Vorschläge in beide Pfade, Kürzung auf 1200 Zeichen.

### C. „Fehlerstelle im Original" zeigte die falsche Zeile

`re.match(r"^(\w+)\[(\d+)\]\.(\w+)")` prüft nur den **Anfang**;
`articles[0].workItemConfigs[3].rampUpTime` wurde zu `articles[0].workItemConfigs`
verkürzt. Zwei Vorschläge zeigten dieselbe Stelle. Später **dieselbe Fehlerklasse** in
`apply_correction.py`, dort mit härterer Folge: die Korrektur wurde gar nicht angewendet,
nachdem die menschliche Entscheidung bereits gespeichert war.

**Behoben:** vollständige Pfadzerlegung mit beliebiger Tiefe, an beiden Stellen; leer statt
falsch, wenn ein Rest unverstanden bleibt.

### D. Falsches Vergleichskollektiv bei der Wertherleitung

Vom Nutzer gefunden und hier nachgerechnet: Der Vorschlag `rampUpTime=200` berief sich auf
Artikel „aus demselben Department (20100)" — alle drei zitierten lagen in **20200**. Es waren
die **Array-Nachbarn** `articles[1..3]`. Im tatsächlichen Kollektiv (Department 20100) tragen
**326 von 331** Artikeln den Wert 120/0.3; die vorgeschlagenen 200/0.25 kommen dort genau
**einmal** vor.

**Ursache:** Muster 2 — `similar_items` war richtig gebildet, trug aber die falschen Felder.

**Behoben:** Verteilung der Zeitwerte je Arbeitsgang über das Department im Kontext, ein
Hinweis, dass Array-Nachbarschaft keine fachliche Ähnlichkeit ist, und eine Prompt-Regel:
*„Deine Selbsteinschätzung misst die Übereinstimmung mit den DATEN, nicht die Schlüssigkeit
deiner eigenen Begründung."*

### E. Doppelte offene Vorschläge

Die Sperre existierte bereits — aber beim **Anwenden**, also nachdem der Prüfer den Diff
gelesen und entschieden hatte. Jetzt greift sie beim **Erzeugen** (nur unter HitL, siehe
`AGENTEN_ARCHITEKTUR.md` §4), und überholte Vorschläge sind im Review Board sichtbar
gekennzeichnet, mit stillgelegten Freigabe-Knöpfen.

**Folgefehler dabei:** Meine erste Fassung ließ auch „Ablehnen" ins Leere laufen — ein
überholter Vorschlag war weder anwendbar noch löschbar. Behoben.

### F. Zwei Abstürze, die wie Verständnisfehler aussahen

1. **`UnicodeEncodeError` bei `→`.** Ein Pfeil im Begründungstext des Modells, gedruckt auf
   eine cp1252-Konsole, beendete `generate_correction_llm`. Der Nutzer sah „der Agent
   versteht mich nicht" — tatsächlich war der Fehler korrekt erkannt und das Werkzeug
   gestorben. Behoben: alle Werkzeuge laufen unter erzwungenem UTF-8.
2. **429 Rate-Limit.** Ein Lauf kostet ~55.000 Token; das Kontingent lag bei 50.000/Minute.
   Der Schritt konnte strukturell nie zuverlässig laufen. Vom Nutzer durch Erhöhung gelöst.

### G. Formzwang statt Authentizität

Nutzerbefund: die Antworten folgten immer demselben Muster. Nachgezählt: 60 Regelzeilen im
Auswertungs-Prompt, aber nur **3** schrieben eine Form vor. Das Muster kam aus einer
Frageliste am Prompt-Ende (wirkte als Vorlage) und aus dem Widerspruch „ausführlich" gegen
„2-3 Sätze".

**Behoben, getrennt nach Art:** Formregeln raus, Wahrheitsregeln bleiben. Neu ein Abschnitt
*„Deine Stimme"* (kein Pflichtaufbau, Register des Nutzers übernehmen, keine rituellen
Schlussfloskeln). Gemessen an vier identischen Anfragen: 24–45 % kürzer, Floskeln von 3 auf 0.

**Ehrliche Einschränkung:** Die Vielfalt selbst ist damit *nicht* belegt — vier Anfragen sind
zu wenig, und gemessen wurden nur Zeilenanfänge. Belegt sind Länge und Floskeln.

### H. Zwei Meldungen, die auf die falsche Ursache zeigten

- `_suggest_recovery` bildete „`last_search_results.json` fehlt" fest auf „identify wurde
  nicht ausgeführt" ab. Eine **verdrahtete Vermutung**, die dem Nutzer riet, einen Schritt
  nachzuholen, den das System gerade ausgeführt hatte.
- Der Chat-Agent zitierte die Nachvalidierung einer **älteren** Entscheidung („noch 1 Fehler
  offen"), obwohl die jüngste 0 meldete. Die Liste war sortiert — aber das sah man ihr nicht
  an. Jetzt trägt die jüngste `ist_aktueller_stand: true`.

**Regel:** Eine Fehlermeldung nennt Tatsachen. Eine Ursache behaupten darf sie nur, wenn sie
sie geprüft hat.

### I. Zwei Bremsen ohne Bezug zur Fachlichkeit

- **`localhost` kostete 2 Sekunden pro Anfrage.** Löst zuerst nach `::1` auf, der Server
  lauschte nur auf IPv4. Betraf **jede** Route, auch statische Dateien
  (`127.0.0.1` → 17 ms). Bindeadresse ist jetzt über `DEV_SERVER_HOST` einstellbar, die
  Voreinstellung bleibt aus Sicherheitsgründen der reine Loopback.
- **Ein vermisster Zähler war nur langsam**, nicht weg — eine Folge derselben 2 Sekunden.

---

## Teil III — Zwei Fehler in der Arbeitsweise

Beide von mir, beide behoben — sie gehören hierher, weil sie sich sonst wiederholen.

**1. Ein Patch-Skript schrieb Datei 1 und brach bei Datei 2 ab.** Der Wiederholungslauf
fügte den Block in Datei 1 ein **zweites Mal** ein (doppelte Funktionsdefinitionen). Zweimal
passiert. Behoben durch ein Werkzeug: `apply_all()` prüft **alle** Anker über **alle**
Dateien, bevor die erste geschrieben wird, und toleriert abweichende Zeilenend-Leerzeichen
(die häufigste Ursache fehlschlagender Anker).

**2. Eine Browser-Prüfung hat auf „Ablehnen" geklickt.** Das Rückgängig-Fenster lief im
Kopflos-Browser ab, und ein Vorschlag wurde tatsächlich abgelehnt — mit dem Kommentar
„Prüfung – nicht absenden" und einem Gedächtnis-Eintrag als Folge.
**Regel: In einer Messung niemals Knöpfe auslösen, die etwas schreiben.** Verdrahtung prüft
man am Handler, nicht am Klick.

---

## Teil IV — Was daraus dauerhaft bleibt

**Drei Testreihen**, alle gegen das echte System und das echte Modell:

| Datei | Prüft |
|---|---|
| `app/eval/test_agent_truthfulness.py` | keine Erfolgsmeldung ohne Beleg; Reichweite wird genannt |
| `app/eval/test_agent_context_access.py` | Sitzungstrennung, frischer Zustand, Entscheidungen, offene Vorschläge |
| `app/eval/test_agent_architektur.py` | Herkunft, Direktantwort, Intent-Abkürzung, Fakten-Block |

Sie sind bewusst **datengetrieben**: Erwartungen kommen aus dem aktuellen Stand, nicht aus
festen Zahlen. Ein Test, der den alten Stand einfordert, meldet Fehler, wo keine sind — und
verdeckt damit die echten.

**Der Grundsatz, der sich durch alles zieht:** Struktur wird deterministisch gerendert, Prosa
steht drumherum. Zahlen kommen aus dem Code (`_facts_block`), Links aus der Konfiguration
(`APP_BASE_URL`), Entscheidungen aus der Datenbank. Das Modell formuliert — es rechnet nicht,
und es rät nicht.

---

## Offene Punkte

1. **Nach einer Freigabe wird der nächste Fehler nicht automatisch angeboten.** Der nächste
   Lauf muss angestossen werden. Ob das so bleiben soll, ist eine offene Entscheidung.
2. **429 wird nicht als solcher erkannt.** Die Wiederholung wartet 1 Sekunde — gegen ein
   Minutenkontingent wirkungslos — und die Meldung nennt den Grund nicht.
3. **Warum die Download-Runde vom 15.08. „erfolgreich" meldete, ohne etwas zu schreiben**,
   ist geklärt (falsche ID, Muster 4). Ob der Agent zusätzlich beschönigt hat, liesse sich
   nur mit dem Werkzeug-Ausgabetext jener Runde belegen.
4. **Eine reine Formatierungsfrage löste einen erneuten Download aus** („gib mir den
   vollständigen Link"). Das entscheidet der Planer; unnötig, aber harmlos.
5. **34 Dateien sind nicht committet.** Darunter die vier neuen Dokumente und drei
   Testreihen.
