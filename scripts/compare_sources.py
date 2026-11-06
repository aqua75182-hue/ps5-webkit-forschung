#!/usr/bin/env python3
"""Vorsichtiger, statischer Vergleich von WebKit-Veröffentlichungsarchiven.

Keine Exploit-Suche, keine Payloads, keine Konsole erforderlich.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

MAX_DIFF_FILES = 12
MAX_DIFF_BYTES = 120_000
MAX_DIFF_LINES = 1000


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


class Source:
    def __init__(self, path: Path):
        self.path = path
        self.archive = None
        self.members = {}
        self.trim_root = False
        if path.is_dir():
            for item in sorted(path.rglob('*')):
                if item.is_file():
                    key = item.relative_to(path).as_posix()
                    self.members[key] = item
        elif zipfile.is_zipfile(path):
            self.archive = zipfile.ZipFile(path)
            entries = [i for i in self.archive.infolist() if not i.is_dir()]
            # Sony archives may use a WebKit-1400/ root on one side but not
            # the other, and they can also contain a root-level changelog.
            # Normalize only the known version-specific WebKit container,
            # regardless of how many extra files are at ZIP root.
            import re
            normalized_roots = set()
            for item in entries:
                parts = PurePosixPath(item.filename).parts
                if not parts or item.filename.startswith('/') or any(part in ('.', '..') for part in parts):
                    continue
                is_version_root = (len(parts) > 1 and
                    re.fullmatch(r'WebKit[-_]\d+(?:\.\d+)?', parts[0], flags=re.I) is not None)
                if is_version_root:
                    normalized_roots.add(parts[0])
                key = '/'.join(parts[1:] if is_version_root else parts)
                if key in self.members:
                    raise ValueError(f'Doppelte Archivpfade nach Normalisierung: {key}')
                self.members[key] = item
            print(f'Pfadnormalisierung für {path.name}: {sorted(normalized_roots) or "bereits flach"}')
        else:
            raise ValueError(f'Quelle muss Ordner oder ZIP-Archiv sein: {path}')

    def stat(self, key: str):
        item = self.members[key]
        if self.archive:
            return item.file_size, item.CRC
        return item.stat().st_size, None

    def checksum(self, key: str):
        item = self.members[key]
        h = hashlib.sha256()
        if self.archive:
            stream = self.archive.open(item)
        else:
            stream = item.open('rb')
        with stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                h.update(chunk)
        return h.hexdigest()

    def small_text(self, key: str):
        size, _ = self.stat(key)
        if size > MAX_DIFF_BYTES:
            return None
        item = self.members[key]
        with (self.archive.open(item) if self.archive else item.open('rb')) as fh:
            raw = fh.read(MAX_DIFF_BYTES + 1)
        if b'\x00' in raw:
            return None
        try:
            return raw.decode('utf-8').splitlines(keepends=True)
        except UnicodeDecodeError:
            return None

    def close(self):
        if self.archive:
            self.archive.close()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--old', type=Path, required=True)
    p.add_argument('--new', type=Path, required=True)
    p.add_argument('--mode', choices=('demo', 'official'), required=True)
    p.add_argument('--out', type=Path, default=Path('reports'))
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    old, new = Source(args.old), Source(args.new)
    try:
        old_keys, new_keys = set(old.members), set(new.members)
        added = sorted(new_keys - old_keys)
        removed = sorted(old_keys - new_keys)
        changed = []
        for key in sorted(old_keys & new_keys):
            # ZIP CRC32 is only a fast indicator, not a cryptographic equality proof.
            if old.stat(key) != new.stat(key):
                changed.append(key)
            elif old.archive is None or new.archive is None:
                if old.checksum(key) != new.checksum(key):
                    changed.append(key)

        md = [
            '# PS5-WebKit: statischer Quellcodevergleich',
            '',
            f'**Modus:** {args.mode.upper()}  ' + ('**NUR DEMODATEN, KEIN SONY-CODE**' if args.mode == 'demo' else '**SONY-QUELLCODEARCHIVE**'),
            '',
            'Dieser Bericht entdeckt **keine** Sicherheitslücken und belegt **keinen** Jailbreak auf PS5 14.22.',
            '',
            f'- Alte Quelle: `{args.old}` ({len(old_keys)} Dateien)',
            f'- Neue Quelle: `{args.new}` ({len(new_keys)} Dateien)',
            f'- Neu: **{len(added)}**',
            f'- Entfernt: **{len(removed)}**',
            f'- Geändert (Dateigröße/CRC oder Hash): **{len(changed)}**',
            '',
            'Hinweis: ZIP-Inhalte werden anhand von Größe und CRC32 vorverglichen; seltene CRC-Kollisionen sind möglich.',
            'Der Bericht vergleicht keine Firmware-Binärdateien und belegt keine exakte Zuordnung zu Firmware 14.22.',
            '',
        ]
        for title, values in [('Neue Dateien', added), ('Entfernte Dateien', removed), ('Geänderte Dateien', changed)]:
            md += [f'## {title}', '']
            md += [f'- `{key}`' for key in values[:150]] or ['(keine)']
            if len(values) > 150:
                md.append(f'... und {len(values) - 150} weitere (alle Pfade in details.json).')
            md.append('')
        md += ['## Text-Diff (kleine geänderte Dateien; maximal 12)', '']
        line_budget = MAX_DIFF_LINES
        shown = 0
        for key in changed:
            if shown >= MAX_DIFF_FILES or line_budget <= 0:
                break
            before, after = old.small_text(key), new.small_text(key)
            if before is None or after is None:
                continue
            lines = list(difflib.unified_diff(before, after, fromfile=f'alt/{key}', tofile=f'neu/{key}', n=2))
            if not lines:
                continue
            lines = lines[:line_budget]
            md += [f'### `{key}`', '', '```diff', *[line.rstrip('\r\n') for line in lines], '```', '']
            shown += 1
            line_budget -= len(lines)
        if shown == 0:
            md += ['Keine kleinen UTF-8-Textdateien mit angezeigtem Diff.', '']
        (args.out / 'bericht.md').write_text('\n'.join(md), encoding='utf-8')
        (args.out / 'details.json').write_text(json.dumps({
            'mode': args.mode, 'old': str(args.old), 'new': str(args.new),
            'counts': {'old': len(old_keys), 'new': len(new_keys), 'added': len(added), 'removed': len(removed), 'changed': len(changed)},
            'paths': {'added': added, 'removed': removed, 'changed': changed},
            'note': 'Kein Nachweis einer Sicherheitslücke oder eines Jailbreaks auf Firmware 14.22.'
        }, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'Fertig: {len(added)} neu, {len(removed)} entfernt, {len(changed)} verändert -> {args.out}')
    finally:
        old.close()
        new.close()


if __name__ == '__main__':
    main()
