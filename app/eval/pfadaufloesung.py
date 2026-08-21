"""
Zielpfade auf dasselbe JSON-Element auflösen — für die AP-I-Korrektheitsbewertung (BA-059).

DAS PROBLEM
-----------
Die beiden Ground-Truth-Kataloge benutzen **verschiedene Notationen für dieselbe Stelle**:

    isoliert    articles[articleId=100005].workItemConfigs[HE01].rampUpTime
    kombiniert  articles[0].workItemConfigs[3].rampUpTime

Beide zeigen auf dasselbe Feld. Ein naiver Stringvergleich würde sie als verschieden werten —
und damit eine **richtige** Korrektur als falsch zählen.

**Die Ground-Truth-Dateien werden nicht umgeschrieben.** Sie sind erhobene Rohdaten; eine
nachträgliche Normalisierung wäre eine Änderung an Messmaterial ohne unabhängigen Beleg. Statt
dessen wird hier **aufgelöst**: beide Notationen werden gegen den zugehörigen Snapshot in einen
kanonischen Indexpfad übersetzt.

DIE FESTLEGUNG, DIE HIER GETROFFEN WIRD
----------------------------------------
> **Zwei Zielpfade gelten fachlich als identisch, wenn sie im zugehörigen Snapshot
> deterministisch auf dasselbe JSON-Element beziehungsweise dasselbe Feld auflösen.**

Sie steht **vor** der Hauptmessung fest (harte Regel 5) und gilt für alle drei Bedingungen
gleichermassen.

WAS DIESES MODUL IST — UND WAS NICHT
-------------------------------------
* **Auswertung, keine Produktlogik.** Es liegt unter `app/eval/`, wird von keiner Pipeline
  importiert und verändert nichts am gemessenen Pfad. `apply_correction.parse_target_path()`
  bleibt unangetastet.
* **Deterministisch.** Kein LLM, keine Heuristik über „Ähnlichkeit", kein Raten.
* **Es rät nie.** Löst ein Selektor auf **kein** oder **mehr als ein** Element auf, ist das
  Ergebnis `nicht_bestimmbar` — nicht „ungefähr richtig". Eine stillschweigend akzeptierte
  mehrdeutige Auflösung wäre schlimmer als ein ehrliches Nichtwissen: sie erzeugt eine
  Bewertung, die niemand nachprüfen kann.

WARUM ES NICHT SCHON EXISTIERT — GEPRÜFT, NICHT ANGENOMMEN
-----------------------------------------------------------
Beide vorhandenen Parser wurden gegen alle 29 Ground-Truth-Pfade laufen gelassen:

    apply_correction.parse_target_path()   18 von 29   (nur numerische Indizes, zwei Ebenen)
    routes.review._parse_target_path()     20 von 29   (numerisch, beliebig tief)

Keiner versteht `[articleId=100005]`, `[HE01]` oder `[workItems contains VOAR01]`.

GEGEN WELCHEN SNAPSHOT WIRD AUFGELÖST? — die unangenehme Feinheit
------------------------------------------------------------------
Zwei Ground-Truth-Pfade sind **relativ zum sauberen Snapshot** formuliert, weil ihr Selektor
genau den Wert nennt, den die Injektion zerstört hat:

    I07  articles[articleId=100005].workItemConfigs[RF01].workItemKey
         before "RF01"  ->  after "RF01_REMOVED"      im Fehler-Snapshot gibt es kein RF01 mehr
    I09  equipment[workItems contains VOAR01].workItems[0]
         before "VOAR01" -> after "WORK_ITEM_NOT_AVAILABLE"

Im Fehler-Snapshot lösen sie auf **null** Elemente auf. Gegen die saubere Referenz lösen beide
eindeutig auf. Das ist kein Fehler im Katalog — die Pfade beschreiben die Stelle, *bevor* sie
manipuliert wurde.

**Regel, deterministisch und protokolliert:** zuerst gegen den **Fehler-Snapshot** auflösen —
das ist der Zustand, den das System tatsächlich sieht und auf den sich ein Modellvorschlag
bezieht. Gelingt das nicht eindeutig, gegen die **saubere Referenz**. Welche Basis benutzt
wurde, steht im Ergebnis (`basis`). Gelingt es in **keiner** Basis: `nicht_bestimmbar`.

Das ist zulässig, weil die Injektionen **nur Werte ändern, keine Struktur** — in Schritt 1 von
BA-058 per Deep-Diff über alle zehn Dateien belegt: keine Listenlänge weicht ab. Ein
kanonischer Indexpfad ist deshalb in beiden Snapshots derselbe, und die Wahl der Basis kann
das Vergleichsergebnis nicht verschieben.

UNTERSTÜTZTE SELEKTOREN — genau die, die in den Katalogen vorkommen
--------------------------------------------------------------------
    [3]                          Index
    [articleId=100005]           Feld = Wert   (Vergleich als Text: 100005 == "100005")
    [HE01]                       blosses Label — irgendein Feld des Elements trägt den Wert
    [workItems contains VOAR01]  Listenfeld enthält den Wert

Mehr nicht. Ein unbekannter Selektor führt zu `nicht_bestimmbar`, nicht zu einem Rateversuch.
"""
from __future__ import annotations

import re

JA = "ja"
NEIN = "nein"
UNKLAR = "nicht_bestimmbar"

#: Ein Pfadabschnitt: Name, danach beliebig viele Selektoren in eckigen Klammern.
_ABSCHNITT = re.compile(r"([A-Za-z_]\w*)|\[([^\]]*)\]")


def _zerlege(pfad: str):
    """`a[0].b[x=1].c` -> ['a', '0', 'b', 'x=1', 'c']. Leer, wenn etwas nicht aufgeht."""
    teile, pos = [], 0
    for m in _ABSCHNITT.finditer(pfad or ""):
        if m.start() > pos and pfad[pos:m.start()] != ".":
            return []                       # etwas Unverstandenes dazwischen
        teile.append(m.group(1) if m.group(1) is not None else m.group(2))
        pos = m.end()
    return teile if teile and pos == len(pfad or "") else []


def _passt(element, selektor: str):
    """Trifft der Selektor dieses Listenelement? `None`, wenn der Selektor unbekannt ist."""
    if not isinstance(element, dict):
        return None
    if "=" in selektor:
        feld, _, wert = selektor.partition("=")
        return str(element.get(feld.strip())) == wert.strip()
    if " contains " in selektor:
        feld, _, wert = selektor.partition(" contains ")
        inhalt = element.get(feld.strip())
        return isinstance(inhalt, list) and wert.strip() in [str(x) for x in inhalt]
    # Blosses Label: irgendein Feld des Elements traegt genau diesen Wert.
    return any(str(v) == selektor for v in element.values())


def aufloesen(pfad: str, snapshot: dict) -> dict:
    """
    Löst einen Zielpfad gegen den Snapshot auf.

    Returns `{"status", "kanonisch", "grund"}`:
        status = "eindeutig"          -> `kanonisch` ist der Indexpfad, z. B. `articles[0].x`
        status = "nicht_bestimmbar"   -> `grund` sagt, woran es lag
    """
    teile = _zerlege(pfad)
    if not teile:
        return {"status": UNKLAR, "kanonisch": None,
                "grund": f"Pfad nicht zerlegbar: {pfad!r}"}

    knoten, kanonisch = snapshot, []
    for teil in teile:
        if isinstance(knoten, dict) and teil in knoten:
            knoten = knoten[teil]
            kanonisch.append(teil)
            continue
        if isinstance(knoten, list):
            if teil.isdigit():
                i = int(teil)
                if i >= len(knoten):
                    return {"status": UNKLAR, "kanonisch": None,
                            "grund": f"Index [{i}] ausserhalb der Liste ({len(knoten)})"}
                knoten = knoten[i]
                kanonisch.append(f"[{i}]")
                continue
            treffer = [i for i, e in enumerate(knoten) if _passt(e, teil) is True]
            unbekannt = any(_passt(e, teil) is None for e in knoten)
            if unbekannt and not treffer:
                return {"status": UNKLAR, "kanonisch": None,
                        "grund": f"Selektor [{teil}] auf dieser Liste nicht anwendbar"}
            if len(treffer) != 1:
                # NIE raten: 0 Treffer heisst "gibt es nicht", >1 heisst "mehrdeutig".
                return {"status": UNKLAR, "kanonisch": None,
                        "grund": (f"Selektor [{teil}] trifft {len(treffer)} Elemente - "
                                  f"{'keine Auflösung' if not treffer else 'mehrdeutig'}")}
            knoten = knoten[treffer[0]]
            kanonisch.append(f"[{treffer[0]}]")
            continue
        return {"status": UNKLAR, "kanonisch": None,
                "grund": f"Abschnitt {teil!r} passt nicht auf {type(knoten).__name__}"}

    text = ""
    for k in kanonisch:
        text += k if k.startswith("[") else (("." + k) if text else k)
    return {"status": "eindeutig", "kanonisch": text, "grund": None}


def aufloesen_mit_referenz(pfad: str, snapshot: dict, referenz: dict | None = None) -> dict:
    """
    Wie `aufloesen()`, faellt aber auf die saubere Referenz zurueck, wenn der Selektor im
    Fehler-Snapshot ins Leere laeuft (siehe Modulkopf: I07 und I09).

    Das Ergebnis traegt zusaetzlich `basis` - "snapshot" oder "referenz". Ohne diese Angabe
    waere hinterher nicht nachvollziehbar, WORAUF sich ein kanonischer Pfad bezieht.
    """
    r = aufloesen(pfad, snapshot)
    if r["status"] == "eindeutig":
        return r | {"basis": "snapshot"}
    if referenz is None:
        return r | {"basis": None}
    rr = aufloesen(pfad, referenz)
    if rr["status"] == "eindeutig":
        return rr | {"basis": "referenz",
                     "hinweis": ("Selektor nennt einen Wert, den die Injektion veraendert hat - "
                                 "gegen die saubere Referenz aufgeloest.")}
    return {"status": UNKLAR, "kanonisch": None, "basis": None,
            "grund": f"weder im Snapshot noch in der Referenz eindeutig: {r['grund']}"}


def pfade_gleich(a: str, b: str, snapshot: dict, referenz: dict | None = None) -> dict:
    """
    Zeigen zwei Zielpfade auf dieselbe Stelle?

    Returns `{"befund", "begruendung", "a", "b"}` mit `befund` aus ja / nein /
    nicht_bestimmbar. **Bei Mehrdeutigkeit auf einer der beiden Seiten: nicht_bestimmbar.**
    """
    ra = aufloesen_mit_referenz(a, snapshot, referenz)
    rb = aufloesen_mit_referenz(b, snapshot, referenz)
    if ra["status"] != "eindeutig" or rb["status"] != "eindeutig":
        offen = ra if ra["status"] != "eindeutig" else rb
        return {"befund": UNKLAR, "a": ra["kanonisch"], "b": rb["kanonisch"],
                "begruendung": f"nicht eindeutig auflösbar: {offen['grund']}"}
    gleich = ra["kanonisch"] == rb["kanonisch"]
    return {"befund": JA if gleich else NEIN,
            "a": ra["kanonisch"], "b": rb["kanonisch"],
            "begruendung": ("beide lösen auf " + ra["kanonisch"] + " auf" if gleich
                            else f"verschiedene Stellen: {ra['kanonisch']} vs. {rb['kanonisch']}")}
