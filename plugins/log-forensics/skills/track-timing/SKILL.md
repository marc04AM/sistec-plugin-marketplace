---
name: track-timing
description: >-
  Track timing & event-chain consistency of a Fael/HMI application log (+ sibling PLC report
  JSONs). Catalogs all artifacts first, reconstructs per-job event chains (lifecycle →
  press/RobotFollow programs → handshakes → punch/track cycles), flags every
  broken/missing/out-of-order link, builds timing + device-health tables, and reports. `-fn`
  accepts MULTIPLE paths (logs and/or folders) merged into ONE unified timeline with cross-source
  correlation. `--upd`/`-u <src…>` first refreshes the local log copies (append-only delta where
  possible) and the cells' DB day-table exports (PLC reports + alarm journal) before analyzing;
  `-b`/`--base` only fetches them. Every run also maintains a cumulative parts-issued table. Use
  when the user wants to verify runtime timing / event-chain consistency of a Fael/HMI log, spot
  broken or out-of-order job chains or device-health issues, refresh and re-analyze those logs, or
  just fetch the latest logs and DB records. Usage:
  /track-timing [-fn "<log-or-folder>" …] [-prod] [--upd|-u ["<src>" …]] [-b|--base ["<src>" …]
  [--dates YYYYMMDD,…]] [--full]
disable-model-invocation: true
context: fork
model: sonnet
---

Verify the **runtime timing and event-chain consistency** of the Fael HMI/PLC coordination from its
own logs, and write a report. This skill focuses on production timing and chain consistency.
Crash captures are `analyze-crash`'s job. Read-only on the sources. It writes only the report, the
parts ledger, the state in `./.trackTiming/`, and (with `--upd`/`-b`) the local log copies and DB
exports. The DB is only read.

Arguments: `$ARGUMENTS`

You run in a forked context: you can't see the invoking conversation or ask the user questions.
Everything comes from the arguments. When you'd normally stop and ask, finish what you can and put
the question in your final report instead.

The two bundled scripts do the heavy lifting deterministically. They parse every line, so you
don't have to, and they print only a short digest. **Don't grep or read the logs wholesale.** That
is the cost this design removes. Open a log only at the specific `L<line>` numbers the digest
cites, a few lines around each (`sed -n '<a>,<b>p'`), when an anomaly needs its context.
Vocabulary for interpreting chains and anomalies: `${CLAUDE_SKILL_DIR}/references/event-chains.md`.
Read it the first time you need to interpret an anomaly, not up front.

## 1. Resolve the sources

- `-fn "<path>" …`: one or more `.log` files or capture folders (strip quotes).
- `-prod`: the newest `SPV_*.log` on `\\192.168.10.10\Condivisa\Sistec\Logs`.
- Nothing given: the newest `SPV_*.log` under the active project's `external resources\`.
- Nothing resolves: say so and stop.

`reports\` is the active project's reports folder. The state dir is `./.trackTiming/`.

## 2. `--upd` / `-u` / `-b` — refresh local copies first (only when asked)

```bash
python "${CLAUDE_SKILL_DIR}/scripts/sync_logs.py" --dest "<project>/external resources" --state .trackTiming ["<src>" …]
```

With no source path, the script reuses the paths from the last `--upd` (`upd-sources.txt`). It
skips the backlog older than each local folder's youngest file and appends only the new tail when
the source is a strict append. It fully replaces a file that rotated or restarted, and creates new
ones. Its `CHANGED:` lines are the analysis targets (plus any `-fn` paths). `RESULT: NOTHING-NEW`
with no `-fn` → report that and stop. A `NEEDS-FOLDER:` line means a file's naming family matches
no local folder, or several. Don't guess. Leave it out and ask in the report where it belongs.
`UNREADABLE:` means a source could not be read this time; its local copy is untouched, so report it.

Then export the DB day tables of the analyzed dates (the distinct `YYYYMMDD` in the `CHANGED:`
names; none → skip):

```bash
python "${CLAUDE_SKILL_DIR}/scripts/export_db_tables.py" --config .trackTiming/db-source.txt --dates <YYYYMMDD,…>
```

Per cell and date it writes `<out_dir>/<date>.json` (table `reports_<date>`) and
`alarms_<date>.json` (that day's `alarm_journal`): append past the file's max ID, rebuild a reset
table, skip an absent one. Report its per-file lines. `ERROR` lines and `RESULT: NO-MYSQL` don't
stop the analysis: note them. Credentials stay in each cell's `DB.ini`: never read, print or copy
them yourself. `.trackTiming/db-source.txt` has one block per cell, plus an optional
`[common] mysql=<path>` when the client isn't on PATH. Relative paths resolve against the project
root:

```ini
[AB]
host=192.168.10.10
db_ini=<that cell's HMI Config\DB.ini>
db_section=DB_0
out_dir=<project>/external resources/db-tables-ab
```

`RESULT: NO-CONFIG` → skip the export and ask in the report for each cell's host, `DB.ini` path +
section and output folder, giving that block as the example (5309 FAEL also has `[C]`: host
`192.168.10.11`, `db-tables-c`). Write the file once the user answers.

**`-b` / `--base`: fetch only.** It implies `--upd` (bare `-b` reuses `upd-sources.txt`). Run the
log sync, then the export for `--dates` if given, else the changed logs' dates, else today: the PLC
writes `reports_<date>`/`alarm_journal` even when the HMI log is silent, so `NOTHING-NEW` doesn't
stop it. Return both scripts' summary lines and stop: no scan, report, baseline or parts ledger.
`-fn`/`-prod` are ignored.

## 3. Scan — one call

```bash
python "${CLAUDE_SKILL_DIR}/scripts/scan_timing.py" --reports "<project>/reports" --state .trackTiming [--full] <log-or-folder> …
```

The script:
- **catalogs** the inputs: known `SPV_*.log` / `plc_reports_*.json` / DB exports `<date>.json` +
  `alarms_<date>.json`, plus any roles recorded in `.trackTiming/catalog.json`. It adds the DB
  exports of the logs' dates from the `out_dir`s in `db-source.txt` by itself. A DB export
  supersedes a `plc_reports_<date>.json` of the same date and cell (the catalog says so). Alarm
  raises and clears join the PLC rows as correlates;
- parses every source in full, **reconstructs per-job chains**, flags broken, missing and
  out-of-order links, computes cycle Δ / race-rate, send durations and first-send latency, and
  **device health**;
- places every anomaly on **one unified timeline** and attaches whatever happened on other sources
  within ±5 s (`--window` to widen it, e.g. 60 for slow handshake chains);
- **writes `reports/<base>.md`**: the catalog, chain, anomaly, timing and device tables. It
  preserves any text between `<!-- BEGIN:x -->`/`<!-- END:x -->` markers from earlier runs;
- **appends new rows to `reports/parts-issued.md`**, keyed by (IdBatch, ID_part);
- tracks a per-file high-water mark. The digest's `ANOMALIES TO REVIEW` lists only anomalies
  **past the previous run's last line**. A rotated or replaced file resets it, and `--full` shows everything.

Digest lines to act on:
- `RESULT: NO-SOURCE`: report and stop. `SKIPPED-EMPTY:` a log with no parseable timestamps. Note it in the catalog and carry on with the rest.
- `OVERLAP: NONE`: the source windows are disjoint. Say so, and treat each source separately in the narrative.
- `UNKNOWN ARTIFACT:` read its first ~20 lines (or a hex head for a binary). If that identifies
  it, add `"<filename or glob>": "<role>"` to `.trackTiming/catalog.json` so no later run asks
  again. If it doesn't, list it as an open question. A companion that is known but fails to parse
  shows up as `unusable` in the catalog: note it and move on.

## 4. Baseline checklist — cached

The claims in `5309_FAEL-Coordination\reports\SystemCoordination.md` are the checklist the log is
tested against. Keep a compact version in `.trackTiming/baseline-checklist.md`: one line per claim
and the baseline's last-modified time on the first line. Re-extract it only when the baseline file
is newer than that time. Otherwise read the cached file only.

## 5. Write the narrative sections (the only prose you write)

Edit `reports/<base>.md` between its markers. Leave the generated tables alone, because the next
run regenerates them.
- `consistency`: each checklist claim → **CONFIRMED / CONTRADICTED / PARTIAL**, with the evidence (`src L<line> time`).
- `findings`: the headline findings, most important first. On a delta run, **add** new findings
  under a dated sub-heading and keep the earlier ones.
- `correlation` (only if >1 source): for each anomaly worth discussing, say whether it is
  **correlated** (with what, and citing both sources' line + time) or **isolated**. Several links
  or sources failing at the same moment points to infrastructure, not an app fault.

Cite `log:line` + timestamp (+ source) for every claim. The digest and the report table give you
these directly.

## 6. Report back (this is what the caller sees)

Return the report path, the digest's per-source summary, the headline findings, and the parts
ledger delta. Also list any open questions (unidentified artifacts, `NEEDS-FOLDER` files) with the
exact re-run the user can do once they answer (e.g. `-fn` again, or which folder to create).
