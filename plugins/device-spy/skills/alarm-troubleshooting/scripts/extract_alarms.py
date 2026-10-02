"""
Extract, for every alarm/warning key the PLC defines, its trigger condition + meaning so
Description/Solution can be authored.

Sources (all under the codesys-spy extraction dir):
  - Reports.txt : master index  GVL.Alarms.<Inst>.AlarmsText[r,c] := '<key>'; //<meaning>
                                 GVL.Alarms.<Inst>.WarningText[r,c] := '<key>'; //<meaning>
  - <Station>_Mgmt.txt / Main.txt : Alarms()/Warnings() actions with
                                 IF <cond> THEN GVL.Alarms.<Inst>.Alm_NN := TRUE; //<comment>
  - translation JSON : key -> Italian/English
Outputs a JSON join keyed by StringName:
  {key, kind, inst, slot, meaning, condition, action_comment, coded, fb, italian, english}.

Usage: python extract_alarms.py <extract_dir> <translation.json> <alarm_join.json>
"""
import os
import re
import sys

from common import dump_json, fb_of, load_json

EXTRACT_DIR, TRANSLATION, OUT = sys.argv[1], sys.argv[2], sys.argv[3]


def read(name):
    with open(os.path.join(EXTRACT_DIR, name), encoding='utf-8', errors='replace') as f:
        return f.read()


if not os.path.isfile(os.path.join(EXTRACT_DIR, 'Reports.txt')):
    sys.exit('ERROR: Reports.txt not found in ' + EXTRACT_DIR)

# ---- 1. Reports.txt : key -> (inst, kind, meaning-comment) ----------------
reports = read('Reports.txt')
idx = {}
pat_txt = re.compile(
    r"GVL\.Alarms\.(?P<inst>[A-Za-z0-9_]+)\.(?P<arr>AlarmsText|WarningText)"
    r"\[(?P<r>\d+),(?P<c>\d+)\][ \t]*:=[ \t]*'(?P<key>[^']+)'[ \t]*;?[ \t]*"
    r"(?://[ \t]*(?P<cmt>[^\n]*))?"
)
for m in pat_txt.finditer(reports):
    idx[m.group('key')] = {
        'inst': m.group('inst'),
        'kind': 'A' if m.group('arr') == 'AlarmsText' else 'W',
        'slot': (int(m.group('r')), int(m.group('c'))),
        'meaning': (m.group('cmt') or '').strip(),
    }

# ---- 2. station actions : (inst, Alm_NN/Wrn_NN) -> (condition, comment, coded) ----
# Scan every *_Mgmt.txt and Main.txt; capture assignment lines (active or commented out).
station_files = [f for f in os.listdir(EXTRACT_DIR)
                 if f.endswith('.txt') and ('Mgmt' in f or f == 'Main.txt')]
assign = {}
# Two assignment styles:
#   alarms   : IF <cond> THEN  GVL.Alarms.<inst>.Alm_NN := TRUE;   //<cmt>   (cond is the IF)
#   warnings : GVL.Alarms.<inst>.Wrn_NN := <bool-expr>;            //<cmt>   (RHS is the cond)
pat_assign = re.compile(
    r"^[ \t]*(?P<cc>//)?[ \t]*GVL\.Alarms\.(?P<inst>[A-Za-z0-9_]+)\.(?P<bit>(?:Alm|Wrn)_\d+)"
    r"[ \t]*:=[ \t]*(?P<rhs>[^;/]*);?[ \t]*(?://[ \t]*(?P<cmt>[^\n]*))?"
)
for sf in station_files:
    lines = read(sf).splitlines()
    for i, ln in enumerate(lines):
        m = pat_assign.match(ln)
        if not m:
            continue
        rhs = re.sub(r'\s+', ' ', (m.group('rhs') or '')).strip()
        cond = rhs
        if rhs.upper() == 'TRUE':  # alarm style: the real condition is the enclosing IF
            for j in range(i - 1, max(i - 6, -1), -1):
                mj = re.search(r'\bIF\b(.*?)\bTHEN\b', lines[j], re.IGNORECASE | re.DOTALL)
                if mj:
                    cond = re.sub(r'\s+', ' ', mj.group(1)).strip()
                    break
                if re.match(r'\s*//?\s*GVL\.Alarms\.', lines[j]):  # previous assignment, stop
                    break
        assign[(m.group('inst'), m.group('bit'))] = {
            'condition': cond,
            'comment': (m.group('cmt') or '').strip(),
            'coded': m.group('cc') is None,
            'file': sf,
        }

# ---- 3. translation ----
tr = {s['StringName']: s for s in load_json(TRANSLATION)}


# ---- 4. join over the keys present in the index ----
def bit_for(entry):
    n = entry['slot'][1] + 1
    return ('Alm_%02d' if entry['kind'] == 'A' else 'Wrn_%02d') % n


out = {}
for key, e in idx.items():
    a = assign.get((e['inst'], bit_for(e)), {})
    out[key] = {
        'key': key,
        'kind': 'Alarm' if e['kind'] == 'A' else 'Warning',
        'inst': e['inst'],
        'slot': e['slot'],
        'meaning': e['meaning'],
        'condition': a.get('condition', ''),
        'action_comment': a.get('comment', ''),
        'coded': a.get('coded', None),  # None = no station assignment (device FB or unused)
        'fb': fb_of(key),
        'italian': tr.get(key, {}).get('Italian', ''),
        'english': tr.get(key, {}).get('English', ''),
    }

dump_json(out, OUT)
print('index keys:', len(idx), '| station assignments:', len(assign), '| joined:', len(out))
dev = sum(1 for v in out.values() if v['coded'] is None)
coded = sum(1 for v in out.values() if v['coded'] is True)
notcoded = sum(1 for v in out.values() if v['coded'] is False)
print('no station assignment:', dev, '| coded station:', coded, '| commented-out station:', notcoded)
print('keys missing from the translation:', sum(1 for k in out if k not in tr))
