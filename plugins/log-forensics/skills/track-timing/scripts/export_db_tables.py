#!/usr/bin/env python3
"""DB day-table exporter for track-timing: per cell and per date, export the HMI database's
PLC report table and that day's alarm journal to JSON files the scan reads as companions.

  <out_dir>/<date>.json         <- table reports_<date>   {ID, DataTime, Type, ZoneSymbol, Text1..3, created_at}
  <out_dir>/alarms_<date>.json  <- alarm_journal rows whose TimeStamp falls on <date>
                                   {ID, TimeStamp, UID, EventTime, Priority, Zone, Name, Extra, Active}

Append-only by ID: an existing file gets only the rows past its max ID, spliced in before the
closing ']'. A source that was reset or shrank (its MAX(ID) is below the file's, its row count up
to the file's max ID differs, or the row at that ID is not the same row) is rebuilt in full. An
absent table is skipped. The DB is only read (SELECT). Optional per-block port=<n> (else the
DB.ini section's Port, else the client default).

Configuration: one block per cell in <state>/db-source.txt (see SKILL.md):

  [AB]
  host=192.168.10.10
  db_ini=<path to that cell's Config\\DB.ini>
  db_section=DB_0
  out_dir=<folder for the JSON files>
  [common]
  mysql=<optional path to mysql(.exe)>

Credentials are never stored or printed: UserName/Password/Database are read from the cell's
DB.ini section at run time, and the password reaches mysql only through the MYSQL_PWD environment
variable of the child process (never on its command line).

Stdlib only. Usage:
  python export_db_tables.py --config .trackTiming/db-source.txt [--cells AB,C]
                             [--dates YYYYMMDD,...] [--mysql <path>] [--overwrite]
--dates defaults to today.
"""
from __future__ import annotations

import argparse
import configparser
import datetime as dt
import glob
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPORT_KEYS = ['ID', 'DataTime', 'Type', 'ZoneSymbol', 'Text1', 'Text2', 'Text3', 'created_at']
ALARM_KEYS = ['ID', 'TimeStamp', 'UID', 'EventTime', 'Priority', 'Zone', 'Name', 'Extra', 'Active']
DATE_RE = re.compile(r'^\d{8}$')
ABSENT = re.compile(r"doesn't exist|Unknown table|ERROR 1146", re.I)


# ----------------------------------------------------------------------------- config
def read_db_source(path: Path) -> tuple[dict, dict]:
    """Return ({cell: block}, common) from db-source.txt. Relative paths in it resolve against the
    project root (the folder that holds the state folder)."""
    cp = configparser.ConfigParser(interpolation=None, comment_prefixes=('#', ';'), inline_comment_prefixes=None)
    cp.optionxform = str.lower
    cp.read(path, encoding='utf-8-sig')
    root = Path(path).resolve().parent.parent
    cells, common = {}, {}
    for sec in cp.sections():
        blk = {k: v.strip() for k, v in cp[sec].items()}
        for k in ('db_ini', 'out_dir', 'mysql'):
            if blk.get(k) and not Path(blk[k]).is_absolute():
                blk[k] = str(root / blk[k])
        if sec.lower() == 'common':
            common = blk
        else:
            cells[sec] = blk
    return cells, common


def read_db_ini(db_ini: str, section: str) -> dict:
    """UserName/Password/Database (+ Port if present) from one section of the HMI's DB.ini.
    Keys are matched case-insensitively. Values are never echoed."""
    sec, found, out, names = section.lower(), False, {}, []
    with open(db_ini, encoding='utf-8-sig', errors='replace') as fh:
        cur = None
        for raw in fh:
            line = raw.strip()
            m = re.match(r'^\[(.+?)\]$', line)
            if m:
                cur = m[1].strip()
                names.append(cur)
                found = found or cur.lower() == sec
                continue
            if cur is not None and cur.lower() == sec and '=' in line and not line.startswith((';', '#')):
                k, v = (p.strip() for p in line.split('=', 1))
                out[k.lower()] = v
    if not found:
        raise ValueError(f'section [{section}] not in {db_ini} (sections: {", ".join(names) or "none"})')
    missing = [k for k in ('username', 'password', 'database') if k not in out]
    if missing:
        raise ValueError(f'[{section}] in {db_ini} lacks {", ".join(missing)}')
    return out


def find_mysql(explicit: str | None, common: dict) -> str | None:
    for cand in (explicit, common.get('mysql')):
        if cand:
            return cand if Path(cand).is_file() else None
    hit = shutil.which('mysql')
    if hit:
        return hit
    if os.name == 'nt':   # the MySQL installer does not put bin\ on PATH
        for pf in {os.environ.get('ProgramFiles', r'C:\Program Files'), os.environ.get('ProgramW6432', '')}:
            found = sorted(glob.glob(os.path.join(pf, 'MySQL', 'MySQL Server*', 'bin', 'mysql.exe'))) if pf else []
            if found:
                return found[-1]
    return None


# ----------------------------------------------------------------------------- mysql
class Db:
    def __init__(self, mysql: str, host: str, creds: dict, port: str | None = None):
        self.mysql, self.host, self.creds = mysql, host, creds
        self.port = port or creds.get('port')

    def query(self, sql: str) -> list[str]:
        env = dict(os.environ, MYSQL_PWD=self.creds['password'])
        cmd = [self.mysql, '-h', self.host, '-u', self.creds['username'], '--database', self.creds['database'],
               '--connect-timeout=8', '--default-character-set=utf8mb4', '-N', '-B', '-r', '-e', sql]
        if self.port:
            cmd[3:3] = ['-P', str(self.port)]
        p = subprocess.run(cmd, capture_output=True, env=env)
        out = p.stdout.decode('utf-8', errors='replace')
        if p.returncode != 0:
            err = p.stderr.decode('utf-8', errors='replace').strip()
            raise RuntimeError(err.replace(self.creds['password'], '***') if self.creds['password'] else err)
        return [ln for ln in out.splitlines() if ln.strip()]


# ----------------------------------------------------------------------------- series files
def obj_str(keys, arr) -> str:
    # Same byte format as the existing series: {"k":v, ...} objects, one per line, in [ ].
    return json.dumps(dict(zip(keys, arr)), separators=(', ', ':'), ensure_ascii=False)


def file_state(path: Path, keys):
    """(exists, row count, max ID, that row re-serialized) of an existing series file."""
    if not path.exists():
        return False, 0, None, None
    txt = path.read_text(encoding='utf-8').strip()
    rows = json.loads(txt) if txt else []
    if not rows:
        return True, 0, None, None
    last = max(rows, key=lambda r: int(r['ID']))
    return True, len(rows), int(last['ID']), obj_str(keys, [last.get(k) for k in keys])


def row_sep(path: Path) -> str:
    """Row separator: the file's own line ending if it exists (the series written so far use the
    platform's, CRLF on Windows), else the platform's."""
    try:
        with open(path, 'rb') as fh:
            head = fh.read(1 << 16)
        if b'},\r\n' in head:
            return ',\r\n '
        if b'},\n' in head:
            return ',\n '
    except OSError:
        pass
    return ',' + os.linesep + ' '


def write_full(path: Path, keys, lines) -> int:
    objs = [obj_str(keys, json.loads(ln)) for ln in lines]
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_bytes(('[' + row_sep(path).join(objs) + ']').encode('utf-8'))
    os.replace(tmp, path)
    return len(objs)


def append_rows(path: Path, keys, lines, had_rows: bool) -> int:
    """Splice rows in before the closing ']' without rewriting the file."""
    objs = [obj_str(keys, json.loads(ln)) for ln in lines]
    if not objs:
        return 0
    sep = row_sep(path)
    with open(path, 'r+b') as fh:
        fh.seek(0, 2)
        pos = fh.tell()
        while pos > 0:                      # find the closing bracket, skipping trailing blanks
            fh.seek(pos - 1)
            ch = fh.read(1)
            if ch == b']':
                pos -= 1
                break
            if not ch.isspace():
                raise ValueError(f'{path.name}: not a JSON array (ends with {ch!r})')
            pos -= 1
        fh.seek(pos)
        fh.write(((sep if had_rows else '') + sep.join(objs) + ']').encode('utf-8'))
        fh.truncate()
    return len(objs)


# ----------------------------------------------------------------------------- export
def export_one(db: Db, path: Path, keys, cols: str, table: str, where: str, label: str, overwrite: bool) -> str:
    """cols = the JSON_ARRAY(...) select list, where = the day condition ('' for a day table)."""
    name = path.name
    select = f'SELECT {cols} FROM {table}'
    w = f' WHERE {where}' if where else ''
    a = ' AND ' if where else ' WHERE '
    try:
        exists, n_file, max_id, last = file_state(path, keys)
        if overwrite or not exists or max_id is None:
            n = write_full(path, keys, db.query(f'{select}{w} ORDER BY ID;'))
            act = 'overwritten' if exists and overwrite else 'refreshed' if exists else 'created'
            return f'{act:<10} {name} ({n} rows) [{label}]'
        # Reset/rotation check before the delta (a query for ID > max alone cannot see one): the
        # source must still hold the file's rows, i.e. its max ID is not lower, it has as many rows
        # up to the file's max ID, and the row at that ID is the same row.
        cnt = db.query(f'SELECT COUNT(*), COALESCE(MAX(ID),0), COALESCE(SUM(ID <= {max_id}),0), '
                       f'(SELECT {cols} FROM {table} WHERE ID = {max_id}) FROM {table}{w};')
        _, src_max, src_le, src_row = cnt[0].split('\t', 3)
        src_max, src_le = int(src_max), int(src_le)
        same_row = src_row != 'NULL' and obj_str(keys, json.loads(src_row)) == last
        if src_max < max_id or src_le != n_file or not same_row:
            n = write_full(path, keys, db.query(f'{select}{w} ORDER BY ID;'))
            why = (f'source max ID {src_max} < file {max_id}' if src_max < max_id else
                   f'source has {src_le} rows up to ID {max_id}, file {n_file}' if src_le != n_file else
                   f'row ID {max_id} differs')
            return f'rebuilt    {name} ({n} rows; source reset/rotated: {why}) [{label}]'
        if src_max == max_id:
            return f'up-to-date {name} ({n_file} rows, max ID {max_id}) [{label}]'
        n = append_rows(path, keys, db.query(f'{select}{w}{a}ID > {max_id} ORDER BY ID;'), n_file > 0)
        return f'appended   {name} (+{n} rows past ID {max_id}, total {n_file + n}) [{label}]'
    except RuntimeError as e:
        if ABSENT.search(str(e)):
            return f'skipped    {name} (table absent) [{label}]'
        return f'ERROR      {name}: {e} [{label}]'


def export_date(db: Db, out_dir: Path, date: str, overwrite: bool) -> list[str]:
    d0 = dt.datetime.strptime(date, '%Y%m%d')
    lo, hi = f'{d0:%Y-%m-%d} 00:00:00', f'{d0 + dt.timedelta(days=1):%Y-%m-%d} 00:00:00'
    # `date` is validated (YYYYMMDD, real calendar day) before it gets here: it is part of a table name.
    rep = ("JSON_ARRAY(ID, DataTime, Type, ZoneSymbol, Text1, Text2, Text3, "
           "DATE_FORMAT(created_at,'%Y-%m-%d %H:%i:%s'))")
    alm = ("JSON_ARRAY(CAST(ID AS CHAR), DATE_FORMAT(TimeStamp,'%Y-%m-%d %H:%i:%s'), UID, "
           "COALESCE(DATE_FORMAT(EventTime,'%Y-%m-%d %H:%i:%s'),''), CAST(Priority AS CHAR), Zone, "
           "Name, COALESCE(Extra,''), CAST(Active AS CHAR))")
    return [export_one(db, out_dir / f'{date}.json', REPORT_KEYS, rep, f'reports_{date}', '',
                       f'reports_{date}', overwrite),
            export_one(db, out_dir / f'alarms_{date}.json', ALARM_KEYS, alm, 'alarm_journal',
                       f"TimeStamp>='{lo}' AND TimeStamp<'{hi}'", f'alarm_journal {date}', overwrite)]


def valid_date(s: str) -> bool:
    if not DATE_RE.match(s):
        return False
    try:
        dt.datetime.strptime(s, '%Y%m%d')
        return True
    except ValueError:
        return False


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', default='.trackTiming/db-source.txt', help='db-source.txt (one block per cell)')
    ap.add_argument('--cells', help='comma list of cell blocks to export (default: all)')
    ap.add_argument('--dates', help='comma list of YYYYMMDD (default: today)')
    ap.add_argument('--mysql', help='mysql client path (default: [common] mysql=, then PATH)')
    ap.add_argument('--overwrite', action='store_true', help='rebuild every file in full')
    a = ap.parse_args(argv)

    dates = [d.strip() for d in (a.dates or dt.date.today().strftime('%Y%m%d')).split(',') if d.strip()]
    bad = [d for d in dates if not valid_date(d)]
    if bad or not dates:
        print(f'RESULT: INVALID-DATE {", ".join(bad) or "(none given)"} — expected YYYYMMDD; nothing exported')
        return 2
    cfg = Path(a.config)
    if not cfg.is_file():
        print(f'RESULT: NO-CONFIG — {cfg} not found; create it (one [cell] block per cell, see SKILL.md)')
        return 2
    cells, common = read_db_source(cfg)
    if a.cells:
        want = [c.strip() for c in a.cells.split(',') if c.strip()]
        unknown = [c for c in want if c not in cells]
        if unknown:
            print(f'RESULT: NO-CELL {", ".join(unknown)} — blocks in {cfg}: {", ".join(cells) or "none"}')
            return 2
        cells = {c: cells[c] for c in want}
    if not cells:
        print(f'RESULT: NO-CELL — {cfg} has no [cell] block')
        return 2
    mysql = find_mysql(a.mysql, common)
    if not mysql:
        print('RESULT: NO-MYSQL — mysql client not found; pass --mysql or set mysql= under [common]')
        return 2

    errors = 0
    for cell, blk in cells.items():
        missing = [k for k in ('host', 'db_ini', 'out_dir') if not blk.get(k)]
        if missing:
            print(f'CELL {cell}: ERROR — block lacks {", ".join(missing)}')
            errors += 1
            continue
        try:
            creds = read_db_ini(blk['db_ini'], blk.get('db_section') or 'DB_0')
        except (OSError, ValueError) as e:
            print(f'CELL {cell}: ERROR — {e}')
            errors += 1
            continue
        out_dir = Path(blk['out_dir'])
        out_dir.mkdir(parents=True, exist_ok=True)
        db = Db(mysql, blk['host'], creds, blk.get('port'))
        print(f"CELL {cell}: host {blk['host']} db {creds['database']} -> {out_dir}")
        for date in dates:
            for line in export_date(db, out_dir, date, a.overwrite):
                errors += line.startswith('ERROR')
                print(f'  {line}')
    print('RESULT: ' + (f'ERRORS {errors}' if errors else 'OK'))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')   # Windows consoles default to cp1252
    sys.exit(main())
