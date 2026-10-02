"""Build the spy dataset: every 'meaningful' alarm/warning the PLC defines (workbook-independent),
with priority/key/area/it/en. Reuses already-authored description/solution/note (from a prior
fill, if any) and emits balanced slices for the not-yet-authored keys.

'Meaningful' = the translation carries descriptive text (beyond the bare code) OR the station bit is
coded in the PLC OR it is a device-FB with a known meaning. Reserved placeholder slots (text = bare
code like 'Main: Alm_07') and untranslated generic device fault-codes are excluded.

Usage: python build_spy.py <alarm_join.json> <translation.json> <out_dir> [prior_authored_dir] [N]
  <out_dir> receives spy_all.json + spy_slices/slice_*.json ; prior_authored_dir holds out_*.json.
"""
import glob
import os
import re
import sys

from common import dump_json, fb_of, load_json

JOIN, TRANSLATION, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
PRIOR = sys.argv[4] if len(sys.argv) > 4 else ''
N = int(sys.argv[5]) if len(sys.argv) > 5 else 4

j = load_json(JOIN)
tr = {s['StringName']: s for s in load_json(TRANSLATION)}
CODE = re.compile(r':\s*(Alm|Wrn|Alarm|Warning)[_ ]?\d+\s*$', re.I)


def is_code(t):
    t = (t or '').strip()
    return not t or bool(CODE.search(t))


def is_real(k, e):
    it, en = tr.get(k, {}).get('Italian', ''), tr.get(k, {}).get('English', '')
    return (not is_code(en)) or (not is_code(it)) or e.get('coded') is True or \
           bool(fb_of(k) and not is_code(e.get('meaning', '')))


def area(k):
    m = re.match(r'(?:Stations_)?(Z0\d|Main|General|Robot(\d))', k)
    if not m:
        return ''
    z = m.group(1)
    return 'MAIN' if z in ('Main', 'General') else ('Z0' + m.group(2) if z.startswith('Robot') else z)


authored = {}
for f in sorted(glob.glob(os.path.join(PRIOR, 'out_*.json'))) if PRIOR else []:
    authored.update(load_json(f))

rows, to_author = {}, []
for k, e in j.items():
    if not is_real(k, e):
        continue
    t = tr.get(k, {})
    rec = {'priority': e['kind'], 'key': k, 'area': area(k),
           'it': t.get('Italian', ''), 'en': t.get('English', ''),
           'name': t.get('English', '') or t.get('Italian', ''), 'meaning': e.get('meaning', ''),
           'condition': e.get('condition', ''), 'coded': e.get('coded'), 'fb': fb_of(k),
           'sheet': e['kind'] + 's'}
    a = authored.get(k)
    if a and (a.get('description') or a.get('solution')):
        rec['description'], rec['solution'], rec['note'] = \
            a.get('description', ''), a.get('solution', ''), a.get('note', '')
    else:
        rec['description'] = rec['solution'] = rec['note'] = None
        to_author.append(rec)
    rows[k] = rec

os.makedirs(OUT, exist_ok=True)
dump_json(rows, os.path.join(OUT, 'spy_all.json'))
SP = os.path.join(OUT, 'spy_slices')
os.makedirs(SP, exist_ok=True)
for old in glob.glob(os.path.join(SP, 'slice_*.json')):   # never the agents' out_*.json
    os.remove(old)
to_author.sort(key=lambda r: (r['sheet'], r['key']))
size = -(-len(to_author) // N) if to_author else 0
for i in range(N):
    chunk = to_author[i * size:(i + 1) * size] if size else []
    if not chunk:
        continue
    slim = [{'key': r['key'], 'sheet': r['sheet'], 'name': r['name'], 'meaning': r['meaning'],
             'italian': r['it'], 'condition': r['condition'], 'coded': r['coded'], 'fb': r['fb']}
            for r in chunk]
    dump_json(slim, os.path.join(SP, f'slice_{i+1}.json'))
    print(f'spy slice_{i+1}: {len(chunk)} rows')
print('meaningful:', len(rows), '| alarms:', sum(1 for r in rows.values() if r['priority'] == 'Alarm'),
      '| warnings:', sum(1 for r in rows.values() if r['priority'] == 'Warning'))
print('reused authored:', len(rows) - len(to_author), '| to author:', len(to_author))
