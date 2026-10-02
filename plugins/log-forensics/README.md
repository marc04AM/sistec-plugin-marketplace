# log-forensics

**Read-only** forensic analysis of PLC/HMI logs and captures. The commands catalog the artifacts,
reconstruct a time-correlated timeline/event chain from them and produce a report; they never
modify the capture (the only write is the report under `--out`, plus — optionally — the project
memory). For many/large logs they parallelize across up to **5 Explore subagents**.

## Skills

| Skill | What it does | Writes |
| :---- | :----------- | :----- |
| `/log-forensics:analyze-crash -fn "<capture folder>" [--out "<dir>"]` | forensics on a capture folder (HMI/app logs, PLC logs, Windows events, PerfMon `.blg`/`.etl`, network) → correlated timeline + root cause across ≥2 independent sources. Generalized across different PLCs/HMIs (detects the format and applies the right parser) | `--out` (default `./crash-out/`) |
| `/log-forensics:track-timing [-fn "<log-or-folder>" …] [-prod] [--upd\|-u ["<src>" …]] [--full]` | **timing and event-chain** consistency of a Fael/HMI log (+ `plc_reports` JSON): reconstructs the per-job chains, flags broken/missing/out-of-order links, timing + device-health tables, cumulative parts ledger | the active project's `reports\` + state in `./.trackTiming/` |

## Notes

- Both are **read-only** on the source; CSV/XML derived from binaries (`.blg`→`relog`,
  `.etl`→`tracerpt`) go to `$env:TEMP`, never the output folder.
- `/log-forensics:analyze-crash` is crash-capture oriented; `/log-forensics:track-timing` is
  production-timing / chain-consistency oriented and carries the Fael domain's event-chain vocabulary.
- `track-timing` delegates parsing to `scripts/scan_timing.py` (Python stdlib): it analyzes the whole
  log (~9 s for 1.4 M lines), writes the report tables directly and prints only a digest with the
  anomalies that are **new** since the last run (per-file high-water mark in `.trackTiming/hwm.json`;
  `--full` to review them all). `--upd` uses `scripts/sync_logs.py` (appends only the tail, handles
  rotations, skips the backlog). The artifact catalog and the baseline checklist are persisted in
  `.trackTiming/`. It runs with `context: fork` + `model: sonnet`: it can't ask questions, so any
  questions (unknown artifacts, destination folder) end up in the final report.
- The parsers use Windows built-ins; any permission prompt is approved case by case.

## Installation

```shell
/plugin install log-forensics@sistec-plugins
```
