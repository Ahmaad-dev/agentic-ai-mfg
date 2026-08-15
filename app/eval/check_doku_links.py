"""Prueft, ob alle Verweise zwischen Dokumenten noch ins Ziel treffen.

Aufruf aus dem Repository-Wurzelverzeichnis:
    app/.venv/Scripts/python.exe -X utf8 app/eval/check_doku_links.py

WOZU. Beim Umsortieren der Dokumentation brechen Querverweise — und zwar LAUTLOS. Eine
Markdown-Datei beschwert sich nicht, wenn ihr Ziel weggezogen wurde; man merkt es erst beim
Lesen, oft Wochen spaeter. Beim Umbau am 15.08.2026 sind auf einen Schlag fuenf Verweise ins
Leere gelaufen, weil drei Dokumente nach `docs/04_PT4/` gewandert sind.

Geprueft werden nur LOKALE Ziele (Dateien und Ordner). Externe URLs werden bewusst nicht
abgerufen: das braucht Netz, ist langsam und schlaegt aus Gruenden fehl, die nichts mit dem
Repository zu tun haben.
"""
import re
import sys
import pathlib

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

WURZEL = pathlib.Path(__file__).resolve().parents[2]

#: Markdown-Link: [Text](Ziel). Anker (#L42) und Titel werden abgeschnitten.
_LINK = re.compile(r'\[[^\]]*\]\(([^)]+)\)')

#: Verweise in Backticks, die wie ein PFAD aussehen — `docs/FOO.md`, `app/eval/bar.py`.
#: Sie sind keine klickbaren Links, veralten aber genauso.
#:
#: Der Schraegstrich ist Pflicht, und das ist der springende Punkt: Ein blosser Dateiname in
#: Backticks (`short_term.py`, `unique-ids.md`) ist eine ERWAEHNUNG im Fliesstext, keine
#: Ortsangabe. Die erste Fassung dieser Pruefung liess ihn zu und meldete 1672 „kaputte"
#: Verweise — fast alle Fehlalarm. Eine Pruefung, die man wegen Laerm ignoriert, ist
#: schlimmer als keine.
_PFAD = re.compile(r'`([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+\.(?:md|py|json|ini|yml|yaml|tf))`')

#: Ordner, die nicht durchsucht werden.
_IGNORIEREN = {'.git', '.venv', 'node_modules', '__pycache__', 'data'}

#: Dateien, in denen Pfadangaben GESCHICHTE sind, keine Ortsangabe fuer heute.
#:
#: Ein fortlaufendes Protokoll haelt fest, was an einem Tag galt. Ein Eintrag vom 08.07., der
#: `demo/agents/...` nennt, war damals richtig — der Ordner heisst erst seit dem 02.08. `app/`.
#: Solche Zeilen nachtraeglich umzuschreiben waere Geschichtsfaelschung; sie hier zu melden
#: waere Laerm (690 der ersten 836 Treffer kamen allein daher).
#: Die klickbaren LINKS dieser Dateien werden weiterhin geprueft — die sollen funktionieren.
_NUR_LINKS = ('PROJECT_LOG.md', 'PROJECT_LOG copy.md', 'BA_PROJECT_LOG.md')


def dateien():
    for p in WURZEL.rglob('*.md'):
        if not any(teil in _IGNORIEREN for teil in p.parts):
            yield p


def ziele(text: str, nur_links: bool = False):
    """(Ziel, Art) je Verweis. Externe URLs und reine Anker fallen raus."""
    for m in _LINK.finditer(text):
        ziel = m.group(1).split()[0].split('#')[0].strip()
        if ziel and not ziel.startswith(('http://', 'https://', 'mailto:', '#', 'data:')):
            yield ziel, 'Link'
    if nur_links:
        return
    for m in _PFAD.finditer(text):
        yield m.group(1), 'Pfadangabe'


def main():
    kaputt, geprueft = [], 0
    for datei in dateien():
        text = datei.read_text(encoding='utf-8', errors='replace')
        for ziel, art in ziele(text, nur_links=datei.name in _NUR_LINKS):
            geprueft += 1
            # Relativ zur Datei zuerst, dann relativ zur Repo-Wurzel: Backtick-Angaben sind
            # meist von der Wurzel aus gedacht ("docs/FOO.md"), Links dateirelativ.
            if (datei.parent / ziel).exists() or (WURZEL / ziel).exists():
                continue
            kaputt.append((datei.relative_to(WURZEL), art, ziel))

    print(f'{geprueft} Verweise in {len(list(dateien()))} Dokumenten geprueft.')
    print()
    if not kaputt:
        print('ERGEBNIS: alle Verweise treffen ins Ziel.')
        return 0

    for datei, art, ziel in sorted(kaputt):
        print(f'  FEHLT  {datei}')
        print(f'         {art}: {ziel}')
    print()
    print(f'ERGEBNIS: {len(kaputt)} Verweis(e) laufen ins Leere.')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
