"""
Lernkarten zwischen `app/skills/` und dem Blob Storage abgleichen.

WOZU
----
Im Cloud-Betrieb (`STORAGE_MODE=AZURE`) liest `core.rulebook_loader` die Karten NICHT aus
dem Container-Image, sondern über den `StorageManager` aus dem Blob Storage unter dem
Präfix `skills/`. Der Ordner `app/skills/` im Image ist dort unbeteiligt. Ohne einen
Erstbestand im Blob stirbt die Korrektur-Pipeline mit
`FileNotFoundError: skills/_core.md not found`.

Genau das ist aber auch die Chance: liegt eine Karte erst einmal als Blob, genügt das
Bearbeiten dieser einen Datei, um das Verhalten zu ändern — ohne Deployment, ohne Zugriff
auf das Repository.

DIE GEFAHR, DIE DIESES SKRIPT ABFÄNGT
-------------------------------------
Genau deshalb darf ein Abgleich NICHT einfach alles überschreiben. Wer im Portal eine Karte
korrigiert und danach ein blindes „hochladen" auslöst, verliert seine Arbeit ohne Vorwarnung.
Deshalb:

* `push` lädt nur Karten hoch, die im Blob FEHLEN. Karten, die sich unterscheiden, werden
  gemeldet und übersprungen.
* `--overwrite` ist nötig, um Abweichendes zu überschreiben — eine bewusste Entscheidung.
* `pull` holt den Blob-Stand zurück ins Repository, damit Änderungen aus dem Portal ihren
  Weg in die Versionsverwaltung finden.

Snapshots fasst dieses Skript NICHT an.

AUFRUF
------
    python -m tools.sync_skills status              # nur zeigen, nichts ändern
    python -m tools.sync_skills push                # fehlende Karten hochladen
    python -m tools.sync_skills push --overwrite     # auch abweichende überschreiben
    python -m tools.sync_skills pull                 # Blob-Stand ins Repository holen
    python -m tools.sync_skills pull --overwrite

Die Verbindung kommt aus denselben Variablen wie im Betrieb:
`AZURE_STORAGE_CONNECTION_STRING`; der Container kommt aus `AZURE_SKILLS_CONTAINER`
(Standard `skills`) — bewusst NICHT der Snapshot-Container.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(APP_ROOT / ".env")

from core.rulebook_loader import SKILLS_CONTAINER, SKILLS_PREFIX, _sp  # noqa: E402
from core.storage_manager import StorageManager  # noqa: E402

SKILLS_DIR = APP_ROOT / "skills"


def _digest(text: str) -> str:
    """Vergleichswert. Zeilenenden normalisiert — Windows/Linux sind kein Unterschied."""
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()[:12]


def _storage() -> StorageManager:
    """
    Erzwingt den AZURE-Modus. Ein Abgleich gegen das lokale Dateisystem wäre sinnlos —
    Quelle und Ziel wären dieselbe Datei.
    """
    if (os.getenv("STORAGE_MODE") or "").upper() != "AZURE":
        os.environ["STORAGE_MODE"] = "AZURE"
    if not os.getenv("AZURE_STORAGE_CONNECTION_STRING"):
        sys.exit("AZURE_STORAGE_CONNECTION_STRING ist nicht gesetzt — Abbruch.")
    sm = StorageManager(container=SKILLS_CONTAINER)
    if sm.mode != "AZURE":
        sys.exit("StorageManager ist auf LOCAL zurückgefallen (Verbindung prüfen) — Abbruch.")
    return sm


def _compare(sm: StorageManager) -> tuple[list, list, list, list]:
    """(nur lokal, nur im Blob, unterschiedlich, gleich) — jeweils Dateinamen."""
    local = {p.name: p.read_text(encoding="utf-8") for p in sorted(SKILLS_DIR.glob("*.md"))}

    remote: dict[str, str] = {}
    for blob_path in sm.list_files(_sp()):
        name = Path(blob_path).name
        if not name.endswith(".md"):
            continue
        text = sm.load_text(_sp(name))
        if text is not None:
            remote[name] = text

    only_local = sorted(set(local) - set(remote))
    only_remote = sorted(set(remote) - set(local))
    both = sorted(set(local) & set(remote))
    differing = [n for n in both if _digest(local[n]) != _digest(remote[n])]
    identical = [n for n in both if n not in differing]
    return only_local, only_remote, differing, identical


def cmd_status(sm: StorageManager) -> int:
    only_local, only_remote, differing, identical = _compare(sm)
    print(f"Container: {sm.container_name}   Präfix: {SKILLS_PREFIX or '(keiner)'}")
    print(f"  gleich              : {len(identical)}")
    print(f"  nur lokal           : {len(only_local)}  {only_local or ''}")
    print(f"  nur im Blob         : {len(only_remote)}  {only_remote or ''}")
    print(f"  unterschiedlich     : {len(differing)}  {differing or ''}")
    if differing:
        print("\n  Unterschiedliche Karten wurden vermutlich im Portal bearbeitet.")
        print("  `pull` holt sie ins Repository, `push --overwrite` verwirft sie.")
    return 0


def cmd_push(sm: StorageManager, overwrite: bool) -> int:
    only_local, _, differing, identical = _compare(sm)
    for name in only_local:
        sm.save_text(_sp(name), (SKILLS_DIR / name).read_text(encoding="utf-8"))
        print(f"  hochgeladen  {name}")
    if differing:
        if overwrite:
            for name in differing:
                sm.save_text(_sp(name),
                             (SKILLS_DIR / name).read_text(encoding="utf-8"))
                print(f"  überschrieben {name}")
        else:
            for name in differing:
                print(f"  ÜBERSPRUNGEN {name} — weicht ab (mit --overwrite erzwingen)")
    print(f"\n  {len(only_local)} neu, "
          f"{len(differing) if overwrite else 0} überschrieben, "
          f"{len(identical)} unverändert, "
          f"{0 if overwrite else len(differing)} übersprungen")
    return 1 if (differing and not overwrite) else 0


def cmd_pull(sm: StorageManager, overwrite: bool) -> int:
    _, only_remote, differing, identical = _compare(sm)
    for name in only_remote:
        (SKILLS_DIR / name).write_text(sm.load_text(_sp(name)), encoding="utf-8")
        print(f"  geholt        {name}")
    if differing:
        if overwrite:
            for name in differing:
                (SKILLS_DIR / name).write_text(sm.load_text(_sp(name)),
                                               encoding="utf-8")
                print(f"  überschrieben {name}")
        else:
            for name in differing:
                print(f"  ÜBERSPRUNGEN {name} — weicht ab (mit --overwrite erzwingen)")
    print(f"\n  {len(only_remote)} neu, "
          f"{len(differing) if overwrite else 0} überschrieben, "
          f"{len(identical)} unverändert")
    return 1 if (differing and not overwrite) else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Lernkarten mit dem Blob Storage abgleichen.")
    ap.add_argument("command", choices=["status", "push", "pull"])
    ap.add_argument("--overwrite", action="store_true",
                    help="Abweichende Karten überschreiben (sonst werden sie übersprungen)")
    args = ap.parse_args()

    if not SKILLS_DIR.is_dir():
        sys.exit(f"Kein Kartenordner unter {SKILLS_DIR}")

    sm = _storage()
    if args.command == "status":
        return cmd_status(sm)
    if args.command == "push":
        return cmd_push(sm, args.overwrite)
    return cmd_pull(sm, args.overwrite)


if __name__ == "__main__":
    raise SystemExit(main())
