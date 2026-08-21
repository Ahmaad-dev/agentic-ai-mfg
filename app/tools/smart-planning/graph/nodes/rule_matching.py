"""
Knoten 4 — Regelzuordnung.

**Was hier neu ist — praezise formuliert (korrigiert 19.08.2026).**
Nicht die Kartenauswahl selbst: **Bedingung B** (bestehende Pipeline + `RULEBOOK_MODE=cards`)
waehlt funktional bereits dieselben Karten aus. Neu ist der **eigenstaendige, explizite
Rule-Matching-SCHRITT mit persistierter Provenienz im gemeinsamen State**.

In A und B steht die Kartenauswahl nur in einem `print()` in `generate_correction_llm.py` und
verschwindet im stdout des Subprozesses (BA_MASTERPLAN Kap. 3.7) — sie ist fluechtig und nicht
maschinell auswertbar. Hier wird sie zu einem gespeicherten, hashbaren Zustand.

Gemeinsam mit Knoten 5 der Beobachtungspunkt fuer **Kategorie 3: Regelhalluzination**
(Kap. 15.1): Hier steht, welche Karten geladen WAREN, dort die Behauptung des Modells darueber.
Erst das Paar macht die Kategorie pruefbar.

ZUSTAENDIGKEIT GEGENUEBER KNOTEN 2 — genau formuliert (Kap. 9.0)
----------------------------------------------------------------
Knoten 2 **schlaegt zusaetzliche Karten vor** (`classified_error["relevant_cards"]`); er laedt
nichts und protokolliert nichts. **Dieser Knoten loest die Vorschlaege zusammen mit der
deterministischen Tag-Zuordnung zum tatsaechlich verwendeten Kartensatz auf, laedt ihn und
protokolliert ihn.** Beide Wege laufen in `select_cards()` zusammen — genau eine
Aufloesungsstelle. Was Knoten 5 zu sehen bekommt, ist ausschliesslich das hier Aufgeloeste.

WICHTIG: Der geladene Regeltext wird als `rule_text` im State weitergereicht, nicht nur sein
Name. Knoten 5 nimmt ihn als Parameter entgegen und laedt NICHT nach — sonst koennte
`matched_rules` etwas anderes ausweisen als das, was das Modell gesehen hat, und die
Regelprovenienz waere wertlos.
"""
import hashlib
from datetime import datetime, timezone


def node_rule_matching(state: dict) -> dict:
    """
    Liest:    state["classified_error"] (Knoten 2) — braucht den [validate_*]-Tag
    Schreibt: state["matched_rules"], haengt einen trace-Eintrag an.

    `matched_rules` enthaelt:
        rulebook_mode  — welcher Modus galt (cards | monolith)
        cards_loaded   — welche Karten der Loader tatsaechlich zusammengesetzt hat
        rule_text      — der VOLLE Text, den Knoten 5 bekommt
        rule_text_hash — sha256 davon, damit spaeter beweisbar ist, was das Modell sah
        chars          — Umfang, fuer den Vergleich der Bedingungen A/B/C
    """
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
    from core.agent_config import RULEBOOK_MODE
    from core.rulebook_loader import load_rulebook

    begonnen = datetime.now(timezone.utc)

    klassifikation = state.get("classified_error") or {}
    tag = klassifikation.get("tag")
    # AP7.5: Karten, die der Agent bei der Identifikation selbst benannt hat.
    extra = klassifikation.get("relevant_cards") or None

    fehler = None
    try:
        regeltext = load_rulebook(tag, extra_cards=extra)
    except Exception as exc:
        regeltext = None
        fehler = f"{type(exc).__name__}: {exc}"

    # Welche Karten es waren: ueber `select_cards()` — DIESELBE Funktion, die `load_rulebook()`
    # zur Auswahl benutzt. Die Auswahlregel hier nachzubauen waere ein Drift-Risiko.
    karten = []
    if regeltext is not None:
        if RULEBOOK_MODE == "cards":
            from core.rulebook_loader import CORE_CARD, select_cards
            gewaehlt, _ = select_cards(tag, extra_cards=extra)
            karten = [CORE_CARD] + [c["file"] for c in gewaehlt]
        else:
            karten = ["(monolith)"]

    state["matched_rules"] = {
        "rulebook_mode": RULEBOOK_MODE,
        "cards_loaded": karten,
        "rule_text": regeltext,
        "rule_text_hash": (hashlib.sha256(regeltext.encode("utf-8")).hexdigest()
                           if regeltext is not None else None),
        "chars": len(regeltext) if regeltext is not None else None,
        "error": fehler,
    }

    dauer_ms = int((datetime.now(timezone.utc) - begonnen).total_seconds() * 1000)
    state.setdefault("trace", []).append({
        "node": "rule_matching",
        "timestamp_utc": begonnen.isoformat(),
        "duration_ms": dauer_ms,
        "input_digest": {"tag": tag, "extra_cards": extra},
        # Der Regeltext selbst gehoert NICHT in den trace — er waere 24.000 bis 35.000 Zeichen
        # und wuerde ihn unlesbar machen (Kap. 12.5). Hash und Umfang genuegen als Beleg.
        "output_digest": {"rulebook_mode": RULEBOOK_MODE, "cards_loaded": karten,
                          "chars": state["matched_rules"]["chars"],
                          "rule_text_hash": state["matched_rules"]["rule_text_hash"],
                          "fehler": fehler},
    })
    return state
