#!/usr/bin/env python3
"""--upd for track-timing: refresh the project's local log copies from source paths.

Never writes to the sources. For each source file (a folder contributes its SPV_*.log and
plc_reports_*.json), it finds the local folder that already holds files of the same naming family
(SPV_5309AB_* with SPV_5309AB_*, plc_reports_* with the cell whose logs sit next to it in the
source), skips everything older than that folder's youngest local file (the backlog is already
captured), then does the cheapest correct update:

  created   no local match: full copy
  appended  source is a strict append of local: copy only the new tail
  replaced  source shrank or its head differs (rotation/restart): full overwrite
  identical same size and content: nothing to do

Prints one line per candidate plus CHANGED: <local path> lines for the scan. Stdlib only.
Usage:  python sync_logs.py --dest <external resources dir> [--state .trackTiming] [src ...]
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

WANTED = re.compile(r'^(SPV_.*\.log|plc_reports_\d{8}\.json)$', re.I)
DATE = re.compile(r'20\d{2}-?\d{2}-?\d{2}')
CHUNK = 1 << 16


def family(name: str) -> str:
    return DATE.sub('<d>', name).lower()


def same_bytes(a: Path, b: Path, offset: int, n: int) -> bool:
    with open(a, 'rb') as fa, open(b, 'rb') as fb:
        fa.seek(offset)
        fb.seek(offset)
        return fa.read(n) == fb.read(n)


def is_prefix(local: Path, src: Path) -> bool:
    """Local is byte-identical to the start of src (checks head and the local tail)."""
    size = local.stat().st_size
    if size == 0:
        return True
    head = min(size, CHUNK)
    if not same_bytes(local, src, 0, head):
        return False
    tail = min(size, 4096)
    return same_bytes(local, src, size - tail, tail)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('sources', nargs='*')
    ap.add_argument('--dest', required=True, help="project's external resources folder (holds logs-ab\\, logs-c\\, …)")
    ap.add_argument('--state', default='.trackTiming')
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    state = Path(a.state)
    state.mkdir(parents=True, exist_ok=True)
    remembered = state / 'upd-sources.txt'
    sources = a.sources
    if not sources:
        if not remembered.exists() or not remembered.read_text(encoding='utf-8').strip():
            print('RESULT: NO-SOURCES — no paths given and no previous --upd run recorded')
            return 2
        sources = [l.strip() for l in remembered.read_text(encoding='utf-8').splitlines() if l.strip()]
        print(f'SOURCES (from last --upd): {"; ".join(sources)}')

    dest = Path(a.dest)
    local_files = [p for p in dest.rglob('*') if p.is_file() and WANTED.match(p.name) and len(p.relative_to(dest).parts) <= 3]
    by_family: dict[str, set[Path]] = {}
    for p in local_files:
        by_family.setdefault(family(p.name), set()).add(p.parent)
    floor = {}
    for p in local_files:
        floor[p.parent] = max(floor.get(p.parent, 0), p.stat().st_mtime)

    cand = []
    for s in sources:
        sp = Path(s)
        if not sp.exists():
            print(f'MISSING-SOURCE: {s}')
            continue
        cand += [f for f in (sorted(sp.iterdir()) if sp.is_dir() else [sp]) if f.is_file() and WANTED.match(f.name)]

    changed, counts = [], Counter()
    for f in cand:
        folders = by_family.get(family(f.name), set())
        if len(folders) > 1:
            # e.g. plc_reports_* live in both cells: pick the folder sharing most families with
            # the source file's own folder (its SPV_* siblings say which cell it belongs to).
            sib = {family(x.name) for x in f.parent.iterdir() if x.is_file() and WANTED.match(x.name)}
            score = {d: len(sib & {family(x.name) for x in d.iterdir() if x.is_file()}) for d in folders}
            best = sorted(score.items(), key=lambda kv: -kv[1])
            folders = {best[0][0]} if best[0][1] > (best[1][1] if len(best) > 1 else -1) else folders
        if len(folders) != 1:
            print(f'NEEDS-FOLDER: {f} — {"no" if not folders else "ambiguous"} local folder for this naming '
                  f'family ({", ".join(str(x) for x in folders) or "none"}); ask the user where it belongs')
            counts['needs-folder'] += 1
            continue
        folder = next(iter(folders))   # not pop(): the set is shared via by_family
        if f.stat().st_mtime < floor.get(folder, 0) - 1:
            counts['backlog'] += 1
            continue
        local = folder / f.name
        ss = f.stat().st_size
        if not local.exists():
            shutil.copy2(f, local)
            print(f'created   {local} ({ss:,} bytes)')
            counts['created'] += 1
            changed.append(local)
            continue
        ls = local.stat().st_size
        if ss == ls and is_prefix(local, f):
            counts['identical'] += 1
            continue
        if ss > ls and is_prefix(local, f):
            with open(local, 'rb') as fl:
                old_lines = sum(chunk.count(b'\n') for chunk in iter(lambda: fl.read(1 << 20), b''))
            with open(f, 'rb') as fs, open(local, 'ab') as fl:
                fs.seek(ls)
                shutil.copyfileobj(fs, fl)
            print(f'appended  {local} (+{ss - ls:,} bytes from line {old_lines + 1})')
            counts['appended'] += 1
            changed.append(local)
            continue
        shutil.copy2(f, local)
        print(f'replaced  {local} (source {"shrank" if ss < ls else "head differs"}: rotation/restart — full analysis)')
        counts['replaced'] += 1
        changed.append(local)

    if a.sources:
        remembered.write_text('\n'.join(a.sources) + '\n', encoding='utf-8')
    print(f'SUMMARY: {dict(counts)}')
    for c in changed:
        print(f'CHANGED: {c}')
    if not changed:
        print('RESULT: NOTHING-NEW')
    return 0


if __name__ == '__main__':
    sys.exit(main())
