#!/usr/bin/env python3
"""Deterministic parser for track-timing: Fael/HMI SPV_*.log (+ plc_reports_*.json).

Parses every source in full (CPU is cheap; tokens are not), then:
  * writes the data-heavy report sections straight into reports/<base>.md
    (artifact catalog, per-job chains, timing, device health, unified anomaly timeline),
    preserving any narrative the model wrote between <!-- BEGIN:x --> / <!-- END:x --> markers;
  * appends new rows to reports/parts-issued.md (keyed by IdBatch + ID_part);
  * prints a SHORT digest to stdout: shape, counts, and only the anomalies the model has to reason
    about (by default those past the per-file high-water mark from the previous run).

Stdlib only. Usage:
  python scan_timing.py --reports <dir> [--state <dir>] [--full] [--window 5] <log-or-folder> ...
"""
from __future__ import annotations

import argparse
import bisect
import datetime as dt
import hashlib
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

# ----------------------------------------------------------------------------- patterns
# Edit here when a build renames a message. Each pattern: (key, category, regex).
TS_RE = re.compile(r'(?:(\d{4}-\d{2}-\d{2})[ T])?(\d{2}):(\d{2}):(\d{2})[.,](\d{1,3})')
# Real lines: "FrmHMI Job(Job[3108], Order -952: ...)", "Job_3108 OnTrackingChanged ...",
# "Job_ItemStart(...): Job[3113], ...". Job[<n>] first, then Job_<n>.
JOB_RE = re.compile(r'Job\[(\d+)\]|\bJob_(\d+)\b')
DATE_IN_NAME = re.compile(r'(20\d{2})-?(\d{2})-?(\d{2})')

# Validated against production logs SPV_5309AB/5309C 2026-09-22/23 (build v3.32.9761).
P = [
    # lifecycle
    # "OnStatusChanged Running ----------->" announces a state; "OnStatusChanged Start -----------> Running Job[..]"
    # is the transition into it (group 2 = target).
    ('status', 'lifecycle', r'OnStatusChanged\s+(\w+)(?:\s*-+>\s*(\w+))?'),
    ('stop_production', 'lifecycle', r'StopProduction'),
    ('resume_stub', 'lifecycle', r'OnResumeProgramAsync'),
    # press program chain. The bare "... SendPressConfigurationAsync" line (nothing after it)
    # opens a send; "... progress: <stage>" lines are stages of the same send.
    ('backgauge_reminder', 'press', r'ShowPressBackGaugeReminder'),
    ('send_cfg', 'press', r'(LoadProgram|FollowRobot)\s+SendPressConfigurationAsync\s*$'),
    ('send_cfg_ok', 'press', r'SendPressConfigurationAsync\s+SUCCESS\b'),
    ('send_cfg_fail', 'press', r'SendPressConfigurationAsync\s+FAIL\b'),
    ('send_cfg_retry', 'press', r'SendPressConfigurationAsync\s+RETRY\b'),
    ('stage', 'press', r'progress:\s*(SendPressbrakeConfiguration|SetModeEditorSuccess|LoadProgramSuccess|OperationComplete)\b'),
    ('press_cfg_params', 'press', r'SendPressbrakeConfiguration.*?"Mode"\W*(\w+).*?"BendIndex"\W*(\w+)'),
    ('load_program_fail', 'press', r'progress:\s*LoadProgramFail'),   # once per send; popup lines echo it
    ('press_fail_popup', 'press', r'OnPressFail\s+#(\w+)'),
    ('robotfollow_load', 'press', r'RobotFollow\s+Condition met'),
    ('stop_robotfollow', 'press', r'StopRobotFollow'),
    # handshakes
    ('handshake', 'handshake', r'(PressProgramLoaded|PressBrakeReady)\s+Handshake\s+(SUCCESS|FAIL)'),
    ('hs_timeout', 'handshake', r'HandShake\.(\w+)\(([^,)]+)[^)]*\).*?waiting.*?Timeout'),
    ('hs_cancelled', 'handshake', r'HandShake\.(\w+)\(([^,)]+).*TaskCanceledException'),
    ('inconsistency', 'handshake', r'SendPlcPressProgramInconsistency'),
    # punch / track
    ('new_part', 'punch', r'OnNewPart\s+PunchedSheet\[([^\]]+)\]\s*Length:\s*(\d+).*?Count:\s*(\d+)\s*/\s*(\d+)'),
    ('new_part_early', 'punch', r'firing NewPart early'),
    ('inconsistency_fix', 'punch', r'handle inconsistency, correcting to false'),
    ('dup_part', 'punch', r'OnNewPart Aborted: duplicate'),
    ('tracking', 'punch', r'OnTrackingChanged\s+zone\s*(\d+).*?Status:\s*(\d+)'),
    ('bs_roller', 'punch', r'OnPieceOnBsRollerChanged'),
    ('program_name', 'punch', r'OnPressBrakeProgramNameChanged\s+(\S+)'),
    ('item', 'punch', r'Job_(ItemStart|ItemComplete|ItemDiscard)'),
    # devices
    ('dev_sistecplc', 'device', r'OpcUaClient SistecPLC\b.*(?:threw\s+ServiceResultException|\bTIMEOUT\b|\bfail:)|SetValueWriteToBus.*FAIL'),
    ('dev_uaclient', 'device', r'UAClient\s+(?:KeepAlive.*(?:BadSecureChannelClosed|Reconnecting)|Create Session ServiceResultException|Session Disconnected)'),
    ('dev_bsplc', 'device', r'OpcUaClient BSPLC\b.*(?:UNREACHABLE|disconnected|\d+ failed|threw|\bTIMEOUT\b)'),
    ('dev_modbus', 'device', r'Modbus connector\s+(\S+)\s+(?:Connect failed|reconnected)|ModbusClient\s*\[[^\]]*\].*Reconnect'),
    ('dev_kuka', 'device', r'KrcClientLogic_\w+ ConnectAsync Fail|KrcClient ContinuousListening FAIL|TcpClient_\d+ Connection (?:failed|I/O error)|Kuka_\d+ Disconnected'),
    ('dev_gade', 'device', r'(?i)gade_?\d*\b.*disconnection|PressRobotTeam.*Disconnected'),
    ('dev_null_conn', 'device', r'connection\W+Null'),
    # generic
    ('exception', 'exception', r'\b(\w+Exception)\b'),
    # Start banner: ": Sistec.5309AB v3.32.9761.30240 by Sistec AM" (one per application start).
    ('banner', 'banner', r':\s+(Sistec\.\d{4}\w*)\s+v(\d+\.\d+\.\d+\.\d+)'),
]
PATS = [(k, c, re.compile(r)) for k, c, r in P]
# Cheap literal gate: a line that contains none of these can't match any pattern above, so the
# ~35 regexes run only on the few percent of lines that matter. Keep in sync when adding patterns.
PREFILTER = re.compile(
    r'OnStatusChanged|StopProduction|OnResumeProgramAsync|ShowPressBackGauge|SendPress|'
    r'OnPressFail|RobotFollow|Handshake|HandShake|Inconsistency|'
    r'OnNewPart|NewPart early|handle inconsistency|OnTrackingChanged|OnPieceOnBsRoller|'
    r'OnPressBrakeProgramName|Job_Item|OpcUaClient|UAClient|SetValueWriteToBus|Modbus|KrcClient|'
    r'TcpClient_|Kuka_|[Gg]ade|Disconnected|Null|Exception|: Sistec\.')
TAG_RE = re.compile(r'(?:Write|Read)ValueAsync\(\s*(?:NodeId\s+)?"?([^",)]+)')
BATCH_RE = re.compile(r'Batch\[(\d+)\]')
IDBATCH_RE = re.compile(r'idBatch\W*(\w+)', re.I)
ROLLER_RE = re.compile(r'Current Sheet on roller:\s*Batch\[([^\]]+)\]')
DIGITS = re.compile(r'\d+')
HEARTBEAT = re.compile(r'(_LIVE\b|LiveBit)', re.I)
# Core lifecycle ranks. Paused/Resumed/NextRunning/ReadyToRestart are side states: allowed
# anywhere, never judged as out of order. Start/Running repeat legitimately after a resume.
RANK = {'Ready': 0, 'Start': 1, 'Running': 2, 'LoadProgram': 3, 'TrySendPressConfiguration': 4,
        'PunchingCompleted': 5, 'Completed': 6, 'NotCompletable': 6, 'Cancelled': 6, 'Failed': 6}
SIDE_STATES = {'Paused', 'Resumed', 'NextRunning', 'ReadyToRestart', 'Scheduled'}
TERMINAL = {'Completed', 'NotCompletable', 'Failed', 'Cancelled'}
# The punching cell's work ends at PunchingCompleted; Completed follows only when the whole order
# is closed (often much later, or in another log). So PunchingCompleted is a valid end here.
END_OK = TERMINAL | {'PunchingCompleted'}
DEVICE_NAMES = {'dev_sistecplc': 'SistecPLC (OPC-UA)', 'dev_uaclient': 'UAClient session/KeepAlive',
                'dev_bsplc': 'BSPLC/BS_PUNCHING', 'dev_modbus': 'PressBrake/Esa (Modbus)',
                'dev_kuka': 'Kuka KRC', 'dev_gade': 'Gade/PressRobotTeam', 'dev_null_conn': 'connection Null'}

MAX_ANOMALIES_STDOUT = 60
MAX_ROWS_REPORT = 400


# ----------------------------------------------------------------------------- helpers
def file_date(path: Path) -> dt.date:
    m = DATE_IN_NAME.search(path.name)
    if m:
        try:
            return dt.date(int(m[1]), int(m[2]), int(m[3]))
        except ValueError:
            pass
    return dt.date.fromtimestamp(path.stat().st_mtime)


def cell_of(path: Path) -> str:
    m = re.match(r'SPV_\w*?(\d{3,4}(?:AB|C|[A-Z]{1,2}))_', path.name)
    if m:
        return m[1]
    m = re.search(r'(AB|C)(?=[_.\-])', path.stem)
    return m[1] if m else path.stem


def parse_ts(line: str, day: dt.date):
    m = TS_RE.search(line[:60])
    if not m:
        return None
    d = dt.date.fromisoformat(m[1]) if m[1] else day
    ms = int(m[5].ljust(3, '0'))
    return dt.datetime(d.year, d.month, d.day, int(m[2]), int(m[3]), int(m[4]), ms * 1000)


def fmt(t: dt.datetime | None) -> str:
    return t.strftime('%H:%M:%S.%f')[:-3] if t else '?'


def head_hash(path: Path, n: int = 4096) -> str:
    with open(path, 'rb') as f:
        return hashlib.sha1(f.read(n)).hexdigest()[:12]


def stats(values):
    if not values:
        return None
    return {'n': len(values), 'avg': statistics.fmean(values),
            'sd': statistics.pstdev(values) if len(values) > 1 else 0.0,
            'min': min(values), 'max': max(values)}


# ----------------------------------------------------------------------------- per-log parse
class Anomaly:
    __slots__ = ('src', 'line', 't', 'kind', 'job', 'text', 'new', 'corr')

    def __init__(self, src, line, t, kind, job, text):
        self.src, self.line, self.t, self.kind, self.job, self.text = src, line, t, kind, job, text
        self.new = True
        self.corr = []


def parse_log(path: Path, label: str):
    day = file_date(path)
    ev = []            # (line_no, t, key, match, raw)
    shape = {'lines': 0, 'first': None, 'last': None, 'banners': [], 'hourly': Counter(),
             'no_ts': 0, 'exceptions': Counter(), 'backwards': [], 'templates': Counter()}
    last_t = None
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        for i, raw in enumerate(f, 1):
            shape['lines'] = i
            t = parse_ts(raw, day)
            if t is None:
                shape['no_ts'] += 1
                t = last_t
            else:
                if last_t and t < last_t - dt.timedelta(hours=12):   # crossed midnight
                    t += dt.timedelta(days=1)
                elif last_t and t < last_t:
                    # Lines written out of time order (async loggers): worth knowing, since
                    # chain ordering is judged by line order while Δ uses timestamps.
                    shape['backwards'].append(i)
                last_t = t
                shape['first'] = shape['first'] or t
                shape['last'] = t
                shape['hourly'][t.hour] += 1
                # Message template (digits folded) to spot log floods, e.g. 42k identical
                # "UAClient KeepAlive ... Reconnecting" lines drowning a shift.
                shape['templates'][DIGITS.sub('N', raw[19:110]).rstrip()] += 1
            if not PREFILTER.search(raw):
                continue
            for key, cat, rx in PATS:
                m = rx.search(raw)
                if not m:
                    continue
                if key == 'exception':
                    shape['exceptions'][m[1]] += 1
                    continue
                if key == 'banner':
                    shape['banners'].append((i, fmt(t), f'{m[1]} v{m[2]}'))
                    ev.append((i, t, key, m, ''))     # a restart resets the "current job"
                    continue
                ev.append((i, t, key, m, raw.rstrip()))
    return day, shape, ev


def analyze(label: str, path: Path, ev, hwm_line: int):
    jobs = {}           # id -> dict
    order = []
    current = None
    anomalies: list[Anomaly] = []
    parts = []
    newparts, track1 = [], []
    sends = []          # (t, source, job)
    send_dur, first_latency = [], []
    devices = defaultdict(lambda: {'n': 0, 'first': None, 'last': None, 'hours': Counter(),
                                   'tags': Counter(), 'lines': [], 'times': []})
    last_params, pending_retry = {}, {}
    open_send = None
    stop_prod = []

    def job_rec(jid):
        if jid not in jobs:
            jobs[jid] = {'id': jid, 'status': [], 'first': None, 'last': None, 'sends': 0, 'ok': 0,
                         'fail': 0, 'retry': 0, 'hs_ok': 0, 'hs_fail': 0, 'parts': 0, 'issues': 0,
                         'send_start': None, 'running_t': None}
            order.append(jid)
        return jobs[jid]

    def flag(line, t, kind, job, text):
        a = Anomaly(label, line, t, kind, job, text[:220])
        a.new = line > hwm_line
        anomalies.append(a)
        if job and job in jobs:
            jobs[job]['issues'] += 1

    for line, t, key, m, raw in ev:
        if key == 'banner':
            current = open_send = None
            continue
        jm = JOB_RE.search(raw)
        jid = (jm[1] or jm[2]) if jm else None
        if jid:
            rec = job_rec(jid)
            rec['first'] = rec['first'] or t
            rec['last'] = t
        job = jid or current
        if key in ('send_cfg_ok', 'send_cfg_fail', 'send_cfg_retry', 'press_cfg_params') and not jid and open_send:
            job = open_send      # results belong to the job that opened the send
        rec = jobs.get(job) if job else None

        if key == 'status' and jid:
            s = m[2] or m[1]
            if rec['status'] and rec['status'][-1][0] == s:
                continue        # transition line + announcement line for the same state
            rec['status'].append((s, t, line))
            if s.isdigit():
                flag(line, t, 'unknown numeric job status', jid, s)
            if s == 'Running':
                current = jid
                rec['running_t'] = rec['running_t'] or t
        elif key == 'stop_production':
            if stop_prod and t and stop_prod[-1] and (t - stop_prod[-1]).total_seconds() < 5:
                flag(line, t, 'double StopProduction', job, '')
            stop_prod.append(t)
        elif key == 'resume_stub':
            flag(line, t, 'OnResumeProgramAsync stub hit', job, '')
        elif key == 'send_cfg':
            src = m[1]
            sends.append((t, src, job, line))
            open_send = job
            if rec:
                rec['sends'] += 1
                rec['send_start'] = t
                if rec['running_t'] and rec['sends'] == 1 and t:
                    first_latency.append((t - rec['running_t']).total_seconds())
        elif key == 'send_cfg_ok':
            if rec:
                rec['ok'] += 1
                if rec['send_start'] and t:
                    send_dur.append((t - rec['send_start']).total_seconds())
                    rec['send_start'] = None
        elif key == 'send_cfg_fail':
            if rec:
                rec['fail'] += 1
            flag(line, t, 'SendPressConfigurationAsync FAIL', job, '')
        elif key == 'send_cfg_retry':
            if rec:
                rec['retry'] += 1
            pending_retry[job] = True
            flag(line, t, 'SendPressConfiguration RETRY', job, '')
        elif key == 'press_cfg_params':
            # Compare only the attempt right after a RETRY with the attempt that failed; a new
            # program (next bend, RobotFollow) legitimately changes Mode/BendIndex.
            now = (m[1], m[2])
            if pending_retry.get(job) and last_params.get(job) and last_params[job] != now:
                flag(line, t, 'Mode/BendIndex changed between attempts', job, f'{last_params[job]}->{now}')
            pending_retry[job] = False
            last_params[job] = now
        elif key == 'load_program_fail':
            flag(line, t, 'LoadProgramFail', job, '')
        elif key == 'press_fail_popup':
            flag(line, t, 'OnPressFail popup', job, m[1])
        elif key == 'handshake':
            if m[2] == 'SUCCESS':
                if rec:
                    rec['hs_ok'] += 1
            else:
                if rec:
                    rec['hs_fail'] += 1
                flag(line, t, 'Handshake FAIL', job, m[1])
        elif key == 'hs_timeout':
            flag(line, t, 'HandShake timeout', job, f'{m[1]}({m[2]})')
        elif key == 'hs_cancelled':
            flag(line, t, 'HandShake TaskCanceledException', job, f'{m[1]}({m[2]})')
        elif key == 'stop_robotfollow':
            pass
        elif key == 'inconsistency':
            ib = IDBATCH_RE.search(raw)
            rl = ROLLER_RE.search(raw)
            flag(line, t, 'SendPlcPressProgramInconsistency (expect 0)', job,
                 f'idBatch={ib[1] if ib else "?"} roller={rl[1] if rl else "?"}')
        elif key == 'new_part':
            parts.append({'IdBatch': m[1], 'ID_part': m[3], 'IssueTime': t, 'Length': m[2],
                          'src': label, 'line': line})
            newparts.append((t, line, m[1]))
            if rec:
                rec['parts'] += 1
        elif key == 'tracking':
            if m[1] == '1' and m[2] == '1':
                b = BATCH_RE.search(raw)
                track1.append((t, line, b[1] if b else None))
        elif key.startswith('dev_'):
            d = devices[key]
            d['n'] += 1
            d['first'] = d['first'] or t
            d['last'] = t
            if t:
                d['hours'][t.hour] += 1
                d['times'].append(t)
            tg = TAG_RE.search(raw)
            if tg:
                tag = tg[1].strip().split('.')[-1]
                d['tags'][('heartbeat:' if HEARTBEAT.search(tag) else 'data:') + tag] += 1
            if len(d['lines']) < 3:
                d['lines'].append(line)

    # concurrent dual sends (job-boundary race)
    for (t1, s1, j1, l1), (t2, s2, j2, l2) in zip(sends, sends[1:]):
        if t1 and t2 and s1 != s2 and abs((t2 - t1).total_seconds()) <= 1.0:
            flag(l2, t2, 'dual send (job-boundary race)', j2 or j1, f'{s1}+{s2} {abs((t2 - t1).total_seconds()):.3f}s')

    # lifecycle consistency per job. A job without a terminal state is TRUNCATED when nothing
    # started after it (the capture simply ended mid-chain), MISSING-END when later jobs ran.
    starts = {jid: jobs[jid]['status'][0][2] for jid in order if jobs[jid]['status']}
    for jid in order:
        r = jobs[jid]
        seq = [s for s, _, _ in r['status']]
        r['verdict'] = 'CONSISTENT'
        if not seq:
            r['verdict'] = 'NO-STATUS'
            continue
        # Out of order = falling back before PunchingCompleted once it (or a terminal state) was
        # reached, without a ReadyToRestart in between. Start/Running/LoadProgram loop freely
        # before that (one iteration per press program), and side states never count.
        top, back = -1, False
        for st in seq:
            if st == 'ReadyToRestart':
                top = -1
            if st in SIDE_STATES or st not in RANK:
                continue
            if top >= RANK['PunchingCompleted'] and RANK[st] < RANK['PunchingCompleted']:
                back = True
            top = max(top, RANK[st])
        if back:
            r['verdict'] = 'OUT-OF-ORDER'
            s, t, ln = r['status'][-1]
            flag(ln, t, 'lifecycle out of order', jid, '→'.join(seq))
        if not END_OK.intersection(seq) and not seq[-1].isdigit():   # numeric already flagged
            later = any(ln > r['status'][-1][2] for j2, ln in starts.items() if j2 != jid)
            r['verdict'] = 'MISSING-END' if later else 'TRUNCATED'
            if r['verdict'] == 'MISSING-END':
                s, t, ln = r['status'][-1]
                flag(ln, t, 'no terminal state (later jobs ran)', jid, f'last: {s}')
        elif 'Failed' in seq:
            r['verdict'] = 'FAILED'
        if r['verdict'] == 'CONSISTENT' and (r['fail'] or r['hs_fail'] or r['issues']):
            r['verdict'] = 'ANOMALY'   # lifecycle complete, but a link in the chain broke
        if 'Running' in seq and r['sends'] == 0 and 'Cancelled' not in seq:   # cancelled before sending is fine
            r['verdict'] = 'INCONSISTENT'
            s, t, ln = r['status'][-1]
            flag(ln, t, 'Running but no SendPressConfigurationAsync', jid, '')

    # Cycle Δ per sheet: T(zone 1 Status:1) − T(OnNewPart). On the real line the sheet reaches
    # zone 1 minutes after OnNewPart, so pair by order within each batch (n-th OnNewPart of
    # Batch[b] with the n-th zone-1 Status:1 of Batch[b]) instead of by time proximity.
    # Negative Δ = the tracking event came first: an ordering race.
    deltas, races = [], 0
    by_batch = defaultdict(list)
    for tt_, lt, b in track1:
        if tt_ and b:
            by_batch[b].append(tt_)
    seen = Counter()
    for tn, ln, ib in newparts:
        k = seen[ib]
        seen[ib] += 1
        lst = by_batch.get(ib, [])
        if tn and k < len(lst):
            d = (lst[k] - tn).total_seconds()
            deltas.append(d)
            if d < 0:
                races += 1
    timing = {'cycle': stats(deltas), 'race': races, 'send': stats(send_dur), 'first': stats(first_latency)}
    return {'jobs': [jobs[j] for j in order], 'anomalies': anomalies, 'parts': parts,
            'devices': dict(devices), 'timing': timing}


def parse_plc(path: Path, label: str):
    try:
        data = json.loads(path.read_text(encoding='utf-8', errors='replace'))
        rows = data if isinstance(data, list) else data.get('items') or data.get('data') or []
    except Exception as e:           # a corrupt known companion is noted, the run continues
        return None, f'unusable ({type(e).__name__})'
    out = []
    day = file_date(path)
    for r in rows:
        if not isinstance(r, dict):
            continue
        ty = str(r.get('Type', ''))
        # Real files: DataTime = "06:56:00" (time only), created_at = "2026-06-09 06:56:28".
        # Take the date from created_at (else the file name) and the event time from DataTime.
        ts, ca = str(r.get('DataTime') or ''), str(r.get('created_at') or '')
        try:
            if re.fullmatch(r'\d{2}:\d{2}:\d{2}(\.\d+)?', ts):
                d = dt.date.fromisoformat(ca[:10]) if re.match(r'\d{4}-\d{2}-\d{2}', ca) else day
                t = dt.datetime.combine(d, dt.time.fromisoformat(ts[:12]))
            else:
                t = dt.datetime.fromisoformat((ts or ca).replace('Z', '').replace('T', ' ')[:23])
        except ValueError:
            continue
        out.append({'t': t, 'type': ty, 'zone': r.get('ZoneSymbol', ''),
                    'text': ' / '.join(str(r[k]).strip() for k in ('Text1', 'Text2', 'Text3') if str(r.get(k) or '').strip()),
                    'id': r.get('ID')})
    out.sort(key=lambda x: x['t'])
    return out, f'{len(out)} rows ({Counter(x["type"] for x in out)})'


# ----------------------------------------------------------------------------- state / catalog
def load_json(p: Path, default):
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        return default


KNOWN = [
    (re.compile(r'^SPV_.*\.log$', re.I), 'HMI/app log (primary timeline)'),
    (re.compile(r'^plc_reports_\d{8}\.json$', re.I), 'PLC reports (ALM/WRN/CMD/STA)'),
]


def catalog_sources(inputs, catalog):
    logs, plcs, entries, unknown = [], [], [], []
    for inp in inputs:
        p = Path(inp)
        files = sorted(p.iterdir()) if p.is_dir() else [p]
        for f in files:
            if not f.is_file():
                continue
            role = next((r for rx, r in KNOWN if rx.match(f.name)), None) or catalog.get(f.name)
            if role is None:
                for pat, r in catalog.items():
                    if any(ch in pat for ch in '*?') and re.fullmatch(pat.replace('.', r'\.').replace('*', '.*').replace('?', '.'), f.name, re.I):
                        role = r
                        break
            st = f.stat()
            entries.append({'path': str(f), 'size': st.st_size, 'role': role or 'UNKNOWN'})
            if role is None:
                unknown.append(f)
            elif role.startswith('HMI/app log'):
                logs.append(f)
            elif role.startswith('PLC reports'):
                plcs.append(f)
    return logs, plcs, entries, unknown


# ----------------------------------------------------------------------------- report
def floods(sh, share=0.10):
    """Templates that alone make up more than `share` of the timestamped lines."""
    total = sum(sh['templates'].values()) or 1
    return [f'{n:,}× ({100 * n / total:.0f}%) "{tpl[:80]}"' for tpl, n in sh['templates'].most_common(3)
            if n / total > share]


def md_table(headers, rows):
    out = ['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join('---' for _ in headers) + ' |']
    out += ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in rows]
    return '\n'.join(out)


def keep_blocks(old: str):
    return dict(re.findall(r'<!-- BEGIN:(\w+) -->\n(.*?)<!-- END:\1 -->', old, re.S))


def block(name, kept, placeholder):
    body = kept.get(name, placeholder + '\n')
    return f'<!-- BEGIN:{name} -->\n{body}<!-- END:{name} -->'


def fnum(x, nd=3):
    return '—' if x is None else f'{x:.{nd}f}'


def write_report(path: Path, base, entries, results, shapes, plc_info, anomalies, multi):
    kept = keep_blocks(path.read_text(encoding='utf-8')) if path.exists() else {}
    L = [f'# Track timing — {base}', '',
         f'_Generated {dt.datetime.now():%Y-%m-%d %H:%M} by scan_timing.py. Sections between BEGIN/END '
         f'markers are written by the analyst and preserved across runs; everything else is regenerated._', '',
         '## Headline findings', block('findings', kept, '_(to be written)_'), '',
         '## 1. Artifact catalog']
    L.append(md_table(['Path', 'Role', 'Size', 'Coverage'],
                      [(Path(e['path']).name, e['role'], f"{e['size']:,}", e.get('coverage', '')) for e in entries]))
    for lbl, sh in shapes.items():
        L.append(f"\n- **{lbl}**: {sh['lines']:,} lines, {fmt(sh['first'])} → {fmt(sh['last'])}, "
                 f"starts: {', '.join(f'L{l} {t} {v}' for l, t, v in sh['banners'][:5]) or 'none'}"
                 f"{' (restarts: ' + str(len(sh['banners']) - 1) + ')' if len(sh['banners']) > 1 else ''}; "
                 f"timestamps going backwards: {len(sh['backwards'])}"
                 f"{' (e.g. ' + ', '.join(f'L{x}' for x in sh['backwards'][:5]) + ')' if sh['backwards'] else ''}; "
                 f"top exceptions: {', '.join(f'{k}×{v}' for k, v in sh['exceptions'].most_common(5)) or 'none'}")
        fl = floods(sh)
        if fl:
            L.append(f"  - log flood: {'; '.join(fl)}")
    for lbl, info in plc_info.items():
        L.append(f'- **{lbl}**: {info}')

    L += ['', '## 2. Consistency vs SystemCoordination.md', block('consistency', kept, '_(to be written)_'), '',
          '## 3. Per-job chains']
    rows = []
    for lbl, r in results.items():
        for j in r['jobs']:
            rows.append((lbl, j['id'], '→'.join(dict.fromkeys(s for s, _, _ in j['status'])) or '—',
                         f"{j['ok']}/{j['sends']}", j['retry'], j['fail'], f"{j['hs_ok']}/{j['hs_ok'] + j['hs_fail']}",
                         j['parts'], j['issues'], j['verdict']))
    L.append(md_table(['Src', 'Job', 'Lifecycle', 'Send ok/total', 'Retry', 'Fail', 'HS ok/total', 'Parts',
                       'Issues', 'Verdict'], rows[:MAX_ROWS_REPORT]))
    if len(rows) > MAX_ROWS_REPORT:
        L.append(f'\n_{len(rows) - MAX_ROWS_REPORT} more jobs omitted._')

    L += ['', '### Anomalies (unified timeline)']
    arows = [(fmt(a.t), a.src, f'L{a.line}', a.job or '—', a.kind + (f' ({a.text})' if a.text else ''),
              '; '.join(a.corr) or ('isolated' if multi else '—')) for a in anomalies]
    L.append(md_table(['Time', 'Src', 'Line', 'Job', 'Anomaly', 'Correlated (±window)'], arows[:MAX_ROWS_REPORT]))

    L += ['', '## 4. Timing']
    trows = []
    for lbl, r in results.items():
        tm = r['timing']
        c = tm['cycle']
        trows.append((lbl, c['n'] if c else 0, fnum(c and c['avg']), fnum(c and c['sd']),
                      f"{tm['race']}/{c['n']} ({100 * tm['race'] / c['n']:.1f}%)" if c else '—',
                      fnum(tm['send'] and tm['send']['avg']), fnum(tm['send'] and tm['send']['max']),
                      fnum(tm['first'] and tm['first']['avg'])))
    L.append(md_table(['Src', 'Cycles', 'Δ avg s', 'Δ σ s', 'Race (Δ<0)', 'Send avg s', 'Send max s',
                       '1st-send latency s'], trows))

    L += ['', '## 5. Device health']
    drows = []
    for lbl, r in results.items():
        for k, d in sorted(r['devices'].items()):
            hrs = ' '.join(f'{h:02d}h:{n}' for h, n in sorted(d['hours'].items()))
            tags = ', '.join(f'{t}×{n}' for t, n in d['tags'].most_common(4))
            drows.append((lbl, DEVICE_NAMES.get(k, k), d['n'], fmt(d['first']), fmt(d['last']), hrs, tags or '—',
                          ' '.join(f'L{x}' for x in d['lines'])))
    L.append(md_table(['Src', 'Device', 'Events', 'First', 'Last', 'Hourly', 'Tags', 'Sample lines'], drows)
             if drows else '_No device errors matched._')

    if multi:
        L += ['', '## Unified timeline / cross-correlation', block('correlation', kept, '_(to be written)_')]
    path.write_text('\n'.join(L) + '\n', encoding='utf-8')


def update_parts(path: Path, parts):
    header = ['# Parts issued (cumulative)', '', 'Last updated: {}', '',
              '| IdBatch | ID_part | IssueTime | Length |', '| --- | --- | --- | --- |']
    rows, seen = [], set()
    if path.exists():
        for ln in path.read_text(encoding='utf-8').splitlines():
            m = re.match(r'\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|$', ln)
            if m and m[1] not in ('IdBatch', '---'):
                rows.append(m.groups())
                seen.add((m[1], m[2]))
    added = 0
    for p in parts:
        key = (p['IdBatch'], p['ID_part'])
        if key in seen:
            continue
        seen.add(key)
        rows.append((p['IdBatch'], p['ID_part'], p['IssueTime'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] if p['IssueTime'] else '?', p['Length']))
        added += 1
    rows.sort(key=lambda r: r[2])
    header[2] = header[2].format(dt.datetime.now().strftime('%Y-%m-%d %H:%M'))
    path.write_text('\n'.join(header + [f'| {a} | {b} | {c} | {d} |' for a, b, c, d in rows]) + '\n', encoding='utf-8')
    return added, len(rows)


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('inputs', nargs='+')
    ap.add_argument('--reports', required=True, help='active project reports\\ folder')
    ap.add_argument('--state', default='.trackTiming', help='state dir (catalog.json, hwm.json)')
    ap.add_argument('--base', help='report base name (default derived from the sources)')
    ap.add_argument('--full', action='store_true', help='digest every anomaly, ignore the high-water mark')
    ap.add_argument('--window', type=float, default=5.0, help='correlation window, seconds')
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')   # Windows consoles default to cp1252

    state = Path(a.state)
    state.mkdir(parents=True, exist_ok=True)
    reports = Path(a.reports)
    reports.mkdir(parents=True, exist_ok=True)
    catalog = load_json(state / 'catalog.json', {})
    hwm = load_json(state / 'hwm.json', {})

    logs, plcs, entries, unknown = catalog_sources(a.inputs, catalog)
    if not logs:
        print('RESULT: NO-SOURCE — no SPV_*.log among the inputs')
        for u in unknown:
            print(f'UNKNOWN: {u}')
        return 2

    results, shapes, plc_info, plc_events = {}, {}, {}, []
    labels = {}
    for f in logs:
        lbl = cell_of(f)
        while lbl in results:
            lbl += "'"
        labels[str(f)] = lbl
        key = str(f.resolve())
        h = head_hash(f)
        prev = hwm.get(key)
        if a.full or not prev or prev.get('head') != h or f.stat().st_size < prev.get('size', 0):
            hwm_line = 0     # new file, rotated/restarted, or --full
        else:
            hwm_line = prev.get('lines', 0)
        day, shape, ev = parse_log(f, lbl)
        if shape['first'] is None:
            print(f'SKIPPED-EMPTY: {f.name} has no parseable timestamps (not analyzed)')
            continue
        res = analyze(lbl, f, ev, hwm_line)
        res['hwm_line'] = hwm_line
        results[lbl] = res
        shapes[lbl] = shape
        for e in entries:
            if e['path'] == str(f):
                e['coverage'] = f"{fmt(shape['first'])}→{fmt(shape['last'])}"
        hwm[key] = {'head': h, 'size': f.stat().st_size, 'lines': shape['lines'], 'last': fmt(shape['last'])}
    for f in plcs:
        rows, info = parse_plc(f, f.name)
        plc_info[f.name] = info
        if rows:
            # Codes that fire all shift long (maintenance reminders, standing warnings) are
            # background, not a correlate: drop any ALM/WRN code seen more than 30 times.
            plc_events += [dict(r, src=f.name) for r in rows if r['type'] in ('ALM', 'WRN')]
            for e in entries:
                if e['path'] == str(f):
                    e['coverage'] = f"{rows[0]['t']:%H:%M:%S}→{rows[-1]['t']:%H:%M:%S}" if rows else ''

    if not results:
        return 2
    if plc_events:
        # Counted over all PLC files together (a prior-day file shows what is "always on").
        freq = Counter(e['text'].split(' / ')[0] for e in plc_events)
        cap = max(30, len(plc_events) // 100)
        noisy = {c for c, n in freq.items() if n > cap}
        plc_events = [e for e in plc_events if e['text'].split(' / ')[0] not in noisy]
        if noisy:
            plc_info['background'] = (f"{len(noisy)} ALM/WRN codes firing >{cap}× ignored for correlation: "
                                      f"{', '.join(sorted(noisy)[:6])}{'…' if len(noisy) > 6 else ''}")

    # unified timeline + cross-source correlation
    anomalies = sorted((x for r in results.values() for x in r['anomalies']), key=lambda x: x.t or dt.datetime.min)
    dev_events = [(t, lbl, DEVICE_NAMES.get(k, k)) for lbl, r in results.items()
                  for k, d in r['devices'].items() for t in d['times']]
    multi = len(results) > 1 or bool(plc_events)
    win = dt.timedelta(seconds=a.window)
    # Every stream is sorted by time, so each lookup is a bisect into a ±window slice.
    an_t = [x.t for x in anomalies]            # anomalies is sorted; None sorts first as min
    plc_events.sort(key=lambda e: e['t'])
    plc_t = [e['t'] for e in plc_events]
    dev_events.sort(key=lambda e: e[0])
    dev_t = [e[0] for e in dev_events]

    def window(ts, t):
        return bisect.bisect_left(ts, t - win), bisect.bisect_right(ts, t + win)

    first_real = next((i for i, t in enumerate(an_t) if t), len(an_t))
    an_tr = an_t[first_real:]
    for x in anomalies:
        if not x.t:
            continue
        hits = []
        lo, hi = window(an_tr, x.t)
        for y in anomalies[first_real + lo:first_real + hi]:
            if y.src != x.src:
                hits.append(f'{y.src} L{y.line} {y.kind}')
                if len(hits) >= 4:
                    break
        lo, hi = window(plc_t, x.t)
        for e in plc_events[lo:min(hi, lo + 4)]:
            hits.append(f"{e['type']} {e['zone']} {e['text'][:50]}")
        lo, hi = window(dev_t, x.t)
        for t, lbl, name in dev_events[lo:hi]:
            hits.append(f'{lbl} {name}')
        x.corr = list(dict.fromkeys(hits))[:4]

    # windows overlap / skew
    spans = {l: (s['first'], s['last']) for l, s in shapes.items()}
    overlap = None
    if len(spans) > 1:
        lo = max(s[0] for s in spans.values())
        hi = min(s[1] for s in spans.values())
        overlap = (lo, hi) if lo < hi else None

    # report + parts
    if a.base:
        base = a.base
    elif len(logs) == 1:
        base = logs[0].stem
    else:
        # Same-family cell logs (SPV_5309AB_* + SPV_5309C_*) -> SPV_5309AB+C_<date>;
        # anything else -> <first input folder>_merged_<date>.
        cells = sorted(results)
        fam = {re.sub(r'(AB|C)$', '', c) for c in cells}
        d = min(file_date(f) for f in logs).strftime('%Y%m%d')
        if len(fam) == 1:
            pre = fam.pop()
            base = f"SPV_{pre}{'+'.join(c[len(pre):] for c in cells)}_{d}"
        else:
            base = f'{Path(a.inputs[0]).resolve().name}_merged_{d}'
    report = reports / f'{base}.md'
    write_report(report, base, entries, results, shapes, plc_info, anomalies, multi)
    all_parts = [p for r in results.values() for p in r['parts']]
    added, total = update_parts(reports / 'parts-issued.md', all_parts)
    (state / 'hwm.json').write_text(json.dumps(hwm, indent=1), encoding='utf-8')

    # ------------------------------------------------------------------ digest (stdout)
    print(f'REPORT: {report}')
    print(f'PARTS: +{added} new rows (total {total}) -> {reports / "parts-issued.md"}')
    for lbl, sh in shapes.items():
        r = results[lbl]
        print(f"SOURCE {lbl}: {sh['lines']:,} lines {fmt(sh['first'])}→{fmt(sh['last'])} "
              f"restarts={max(0, len(sh['banners']) - 1)} backwards-ts={len(sh['backwards'])} jobs={len(r['jobs'])} parts={len(r['parts'])} "
              f"anomalies={len(r['anomalies'])} (new since L{r['hwm_line']}: {sum(x.new for x in r['anomalies'])})")
        for fl in floods(sh):
            print(f'  flood: {fl}')
        vc = Counter(j['verdict'] for j in r['jobs'])
        print(f"  verdicts: {dict(vc)}")
        tm = r['timing']
        if tm['cycle']:
            c = tm['cycle']
            print(f"  cycle Δ avg={c['avg']:.3f}s σ={c['sd']:.3f}s race={tm['race']}/{c['n']}")
        for k, d in r['devices'].items():
            print(f"  device {DEVICE_NAMES.get(k, k)}: {d['n']} events {fmt(d['first'])}→{fmt(d['last'])}")
    if overlap is not None or len(spans) > 1:
        print(f"OVERLAP: {fmt(overlap[0])}→{fmt(overlap[1])}" if overlap else 'OVERLAP: NONE — windows are disjoint; treat sources separately')
    for n, info in plc_info.items():
        print(f'PLC {n}: {info}')
    for u in unknown:
        print(f'UNKNOWN ARTIFACT: {u} ({u.stat().st_size:,} bytes) — identify from a head sample')

    show = anomalies if a.full else [x for x in anomalies if x.new]
    kinds = Counter(x.kind for x in show)
    print(f'ANOMALIES TO REVIEW: {len(show)} of {len(anomalies)} — by kind: {dict(kinds.most_common(12))}')
    # Show each kind's first occurrences, so a flood of one kind doesn't hide the rest.
    per_kind = defaultdict(int)
    shown = 0
    for x in show:
        if per_kind[x.kind] >= 5 or shown >= MAX_ANOMALIES_STDOUT:
            continue
        per_kind[x.kind] += 1
        shown += 1
        print(f"  {fmt(x.t)} {x.src} L{x.line} job={x.job or '-'} {x.kind}{' [' + x.text + ']' if x.text else ''}"
              f"{' || ' + '; '.join(x.corr) if x.corr else ''}")
    if shown < len(show):
        print(f'  … {len(show) - shown} more in the report table')
    return 0


if __name__ == '__main__':
    sys.exit(main())
