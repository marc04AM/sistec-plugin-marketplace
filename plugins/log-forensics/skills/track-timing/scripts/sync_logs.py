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

SMB/lock handling (all three were hit on the line's log shares):
  * the HMI keeps today's log open for writing: sources are read with plain open(), whose Windows
    share mode lets the writer keep the file (the FileShare.ReadWrite equivalent);
  * a directory listing, and even a direct stat, over SMB can report a stale size (0 B, or
    hundreds of KB short): sizes are never trusted, every decision reads the bytes, and a copy
    always runs to EOF;
  * the file keeps growing while it is read: after an append the tail is re-read until a pass
    adds nothing.
Each local copy is stamped with its source's mtime, so the youngest-file floor reflects the source
and not the time of our own copy; the floor also admits any file whose date-in-name is not older
than the folder's newest one.

Prints one line per candidate plus CHANGED: <local path> lines for the scan. Stdlib only.
Usage:  python sync_logs.py --dest <external resources dir> [--state .trackTiming] [src ...]
"""
from __future__ import annotations

import argparse
import os
import re
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


def has_bytes_past(src: Path, offset: int) -> bool:
    """True when src really holds data beyond offset (read, not stat: SMB sizes can be stale)."""
    with open(src, 'rb') as f:
        f.seek(offset)
        return bool(f.read(1))


def copy_from(src: Path, dst, offset: int):
    """Copy src[offset:EOF] into the open dst; returns (bytes copied, fstat of the open source)."""
    n = 0
    with open(src, 'rb') as f:
        f.seek(offset)
        for chunk in iter(lambda: f.read(1 << 20), b''):
            dst.write(chunk)
            n += len(chunk)
        st = os.fstat(f.fileno())
    return n, st


def stamp(local: Path, st) -> None:
    os.utime(local, ns=(st.st_atime_ns, st.st_mtime_ns))


def full_copy(src: Path, local: Path) -> int:
    tmp = local.with_name(local.name + '.part')
    with open(tmp, 'wb') as fl:
        n, st = copy_from(src, fl, 0)
    os.replace(tmp, local)
    stamp(local, st)
    return n


def name_date(p: Path):
    m = DATE.search(p.name)
    return m[0].replace('-', '') if m else None


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
    floor, floor_day = {}, {}
    for p in local_files:
        floor[p.parent] = max(floor.get(p.parent, 0), p.stat().st_mtime)
        if name_date(p):
            floor_day[p.parent] = max(floor_day.get(p.parent, ''), name_date(p))

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
        nd = name_date(f)
        recent = nd is not None and nd >= floor_day.get(folder, '')
        if not recent and f.stat().st_mtime < floor.get(folder, 0) - 1:
            counts['backlog'] += 1
            continue
        local = folder / f.name
        try:
            if not local.exists():
                n = full_copy(f, local)
                print(f'created   {local} ({n:,} bytes)')
                counts['created'] += 1
                changed.append(local)
                continue
            ls = local.stat().st_size
            prefix = is_prefix(local, f)
            if prefix and not has_bytes_past(f, ls):
                counts['identical'] += 1
                continue
            if prefix:
                with open(local, 'rb') as fl:
                    old_lines = sum(chunk.count(b'\n') for chunk in iter(lambda: fl.read(1 << 20), b''))
                added = passes = 0
                with open(local, 'ab') as fl:
                    while passes < 5:            # the source grows while we read it
                        n, st = copy_from(f, fl, ls + added)
                        passes += 1
                        added += n
                        if n == 0:
                            break
                stamp(local, st)
                print(f'appended  {local} (+{added:,} bytes from line {old_lines + 1}'
                      f'{f", {passes - 1} passes" if passes > 2 else ""})')
                counts['appended'] += 1
                changed.append(local)
                continue
            n = full_copy(f, local)
            print(f'replaced  {local} (source {"shrank" if n < ls else "head differs"}: rotation/restart — full analysis)')
            counts['replaced'] += 1
            changed.append(local)
        except OSError as e:     # e.g. a sharing violation: the local copy stays as it was
            print(f'UNREADABLE: {f} — {type(e).__name__}: {e}; local copy left unchanged')
            counts['unreadable'] += 1

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
