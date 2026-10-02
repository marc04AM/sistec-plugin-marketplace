"""Shared helpers for the alarm-troubleshooting scripts."""
import json
import re

# Device function-block family + Alm/Wrn index at the end of a StringName key,
# e.g. 'Stations_Z01_V12ValveAlm_01' -> 'Valve'.
FB_RE = re.compile(r'(Valve|Inverter|Encoder|AnalogScaling)(Alm|Wrn)_\d+$')

# Workbook contract (both Alarms and Warnings sheets): A = StringName key, D = Name,
# E = Description, F = Solution, G = Note.
COL_KEY, COL_NAME, COL_DESC, COL_SOL, COL_NOTE = 1, 4, 5, 6, 7


def load_json(path):
    # DB exports often carry a UTF-8 BOM.
    with open(path, encoding='utf-8-sig') as f:
        return json.load(f)


def dump_json(obj, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def fb_of(key):
    m = FB_RE.search(key or '')
    return m.group(1) if m else None


def name_index(translation_path):
    """Map Italian/English text -> StringName, to resolve rows whose key column is blank."""
    if not translation_path:
        return {}
    idx = {}
    for s in load_json(translation_path):
        for lang in ('English', 'Italian'):
            t = (s.get(lang) or '').strip()
            if t:
                idx.setdefault(t, s['StringName'])
    return idx


def row_key(ws, r, by_name):
    """The row's key: column A, else column D resolved through the translation."""
    k = ws.cell(r, COL_KEY).value
    if k:
        return str(k).strip()
    name = ws.cell(r, COL_NAME).value
    return by_name.get(str(name).strip()) if name else None
