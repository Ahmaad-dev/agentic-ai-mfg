"""
G5a — Messstand festhalten. Exakt die sechs definierten Punkte, nicht mehr.
Schreibt nach data/archive/ba-umgebung-eingefroren-<datum>/.
"""
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
PY = REPO / ".venv" / "Scripts" / "python.exe"
sys.path.insert(0, str(REPO / "app"))

STEMPEL = datetime.now(timezone.utc).strftime("%Y%m%d")
ZIEL = REPO / "data" / "archive" / f"ba-umgebung-eingefroren-{STEMPEL}"
ZIEL.mkdir(parents=True, exist_ok=True)


def sh(*args):
    return subprocess.run(args, capture_output=True, text=True, cwd=str(REPO)).stdout.strip()


def sha(pfad: Path):
    if not pfad.exists():
        return {"pfad": str(pfad.relative_to(REPO)), "vorhanden": False}
    h = hashlib.sha256(pfad.read_bytes()).hexdigest()
    return {"pfad": str(pfad.relative_to(REPO)).replace("\\", "/"),
            "vorhanden": True, "bytes": pfad.stat().st_size, "sha256": h}


# ---------------------------------------------------------------- 1 + 2
commit = sh("git", "rev-parse", "HEAD")
branch = sh("git", "rev-parse", "--abbrev-ref", "HEAD")
# NICHT strippen: `git status --porcelain` beginnt jede Zeile mit zwei Statuszeichen, und
# bei nicht-gestageten Aenderungen ist das erste ein LEERZEICHEN. Ein `.strip()` auf die
# Gesamtausgabe frisst es in der ERSTEN Zeile - der Pfad verliert sein erstes Zeichen
# ("CLAUDE.md" -> "LAUDE.md") und faellt als "unbekannt" durch. Beim ersten Lauf genau so
# passiert.
status_roh = subprocess.run(["git", "status", "--porcelain"], capture_output=True,
                            text=True, cwd=str(REPO)).stdout
eintraege = [z for z in status_roh.splitlines() if z.strip()]


def klassifiziere(zeile):
    pfad = zeile[3:].strip().strip('"')
    if pfad.startswith(("app/eval/", "app/tools/smart-planning/graph/")):
        return "BA-relevant (Messinstrument/Graph)"
    if pfad.startswith("docs/"):
        return "Dokumentation"
    if pfad.startswith("app/"):
        return "BA-relevant (Produktpfad)"
    if pfad == "CLAUDE.md":
        return "Dokumentation (Projektinstruktionen)"
    return "unbekannt"


working_tree = {"sauber": not eintraege, "anzahl": len(eintraege),
                "eintraege": [{"status": z[:2], "pfad": z[3:].strip().strip('"'),
                               "klasse": klassifiziere(z)} for z in eintraege]}

# ---------------------------------------------------------------- 3
freeze = subprocess.run([str(PY), "-m", "pip", "freeze"],
                        capture_output=True, text=True, cwd=str(REPO)).stdout
(ZIEL / "requirements-frozen.txt").write_text(freeze, encoding="utf-8")

# ---------------------------------------------------------------- 4
meta_roh = subprocess.run(
    [str(PY), "-c",
     "import sys,json;sys.path.insert(0,'app');"
     "from core.run_metadata import collect_run_metadata;"
     "print(json.dumps(collect_run_metadata({'zweck':'G5a Lock-Artefakt'}),"
     "ensure_ascii=False,default=str))"],
    capture_output=True, text=True, cwd=str(REPO)).stdout.strip()
metadaten = json.loads(meta_roh)

# ---------------------------------------------------------------- 5
schalter = {
    "SP_ARCHITECTURE_MODE": {"A": "monolith", "B": "monolith", "C": "graph"},
    "RULEBOOK_MODE": {"A": "monolith", "B": "cards", "C": "cards"},
    "MEMORY_MODE": "off (alle Arme)",
    "HUMAN_IN_THE_LOOP": "false (alle Arme)",
    "hinweis": ("Je Bedingung ein EIGENER PROZESS - die Schalter kommen beim Import aus "
                "agent_config, importlib.reload() schaltet sie nicht um (BA-021)."),
}
modell = metadaten.get("modell", {})

# ---------------------------------------------------------------- 6
D = REPO / "data" / "snapshots"
hashes = {
    "messkatalog_isoliert": sha(D / "pt4-manipulated_snapshots" / "isolated-error-snapshots" / "expected-results.json"),
    # ERROR-SNAPSHOTS.md ist eine BESCHREIBUNG ohne maschinenlesbare GT-Felder (BA-054).
    # Die autoritative Ground Truth der kombinierten Faelle liegt seit BA-058 daneben.
    "messkatalog_kombiniert_beschreibung": sha(D / "pt4-manipulated_snapshots" / "kombinierte-fehler-snapshots" / "ERROR-SNAPSHOTS.md"),
    "messkatalog_kombiniert_ground_truth": sha(D / "pt4-manipulated_snapshots" / "kombinierte-fehler-snapshots" / "expected-results.json"),
    "generator_kombiniert": sha(D / "pt4-manipulated_snapshots" / "kombinierte-fehler-snapshots" / "generate-error-snapshots.ps1"),
    "pilotkatalog_ground_truth": sha(D / "ba-pilot-snapshots" / "expected-results.json"),
    "referenz_snapshot": sha(D / "ok-snapshot.json"),
}
# BA-054: Die beiden Index-/GT-Dateien allein genuegen NICHT. `ERROR-SNAPSHOTS.md` ist eine
# BESCHREIBUNG ohne maschinenlesbare Ground-Truth-Felder, und die manipulierten Snapshots -
# die eigentlichen MESSEINGAENGE - waren gar nicht erfasst. Ohne sie ist die Hauptmessung
# nicht reproduzierbar. Deshalb hier je Datei gehasht; 27 Dateien sind kein "riesiges
# Manifest", sondern genau der Umfang, den G5a Punkt 6 meint.
for name, ordner in (("messfaelle_isoliert", "isolated-error-snapshots"),
                     ("messfaelle_kombiniert", "kombinierte-fehler-snapshots")):
    verz = D / "pt4-manipulated_snapshots" / ordner
    dateien = sorted(x for x in verz.iterdir() if x.is_file())
    ges = hashlib.sha256()
    for x in dateien:
        ges.update(x.read_bytes())
    hashes[name] = {"verzeichnis": str(verz.relative_to(REPO)).replace("\\", "/"),
                    "anzahl": len(dateien), "gesamt_sha256": ges.hexdigest(),
                    "dateien": [sha(x) for x in dateien]}

karten = sorted((REPO / "app" / "skills").glob("*.md"))
hashes["regelkarten"] = {"anzahl": len(karten), "dateien": [sha(k) for k in karten]}
gesamt = hashlib.sha256()
for k in karten:
    gesamt.update(k.read_bytes())
hashes["regelkarten_gesamt_sha256"] = gesamt.hexdigest()
mono = list((REPO / "app" / "tools" / "smart-planning").rglob("*rule*")) + \
       list((REPO / "app" / "tools" / "smart-planning").rglob("*Regelwerk*"))
hashes["monolith_regelwerk"] = [sha(m) for m in mono if m.is_file()][:5]

lock = {
    "zweck": "G5a - Messstand festhalten (AP-G5a). Sechs Punkte, bewusst schlank.",
    "erzeugt_utc": datetime.now(timezone.utc).isoformat(),
    "1_git": {"commit": commit, "branch": branch},
    "2_working_tree": working_tree,
    "3_pip_freeze": "requirements-frozen.txt (neben dieser Datei)",
    "4_run_metadata": metadaten,
    "5_modell_und_schalter": {"modell": modell, "schalter": schalter},
    "6_sha256_nicht_versionierter_messartefakte": hashes,
}
(ZIEL / "lock.json").write_text(json.dumps(lock, indent=2, ensure_ascii=False, default=str),
                                encoding="utf-8")

print(f"Ziel: {ZIEL.relative_to(REPO)}")
print(f"1 Git      : {commit[:12]} auf {branch}")
print(f"2 Tree     : {'sauber' if working_tree['sauber'] else str(working_tree['anzahl']) + ' Eintraege'}")
for kl in sorted({e['klasse'] for e in working_tree['eintraege']}):
    n = sum(1 for e in working_tree['eintraege'] if e['klasse'] == kl)
    print(f"             {kl}: {n}")
print(f"3 pip      : {len(freeze.splitlines())} Pakete")
print(f"4 Metadaten: ba_env_ok={metadaten['umgebung']['ba_env_ok']} "
      f"prefix={metadaten['umgebung']['sys_prefix']}")
print(f"5 Modell   : {modell.get('deployment')} / {modell.get('api_version')} / "
      f"T={modell.get('temperature')}")
print(f"6 Hashes   : {hashes['regelkarten']['anzahl']} Regelkarten, "
      f"Gesamt {hashes['regelkarten_gesamt_sha256'][:16]}")
for k in ("messfaelle_isoliert", "messfaelle_kombiniert"):
    v = hashes[k]
    print(f"             {k:26} {v['anzahl']} Dateien, gesamt {v['gesamt_sha256'][:16]}")
for k in ("messkatalog_isoliert", "messkatalog_kombiniert_ground_truth",
          "generator_kombiniert", "messkatalog_kombiniert_beschreibung",
          "pilotkatalog_ground_truth", "referenz_snapshot"):
    v = hashes[k]
    print(f"             {k:26} {'sha ' + v['sha256'][:16] if v['vorhanden'] else 'FEHLT'}")
