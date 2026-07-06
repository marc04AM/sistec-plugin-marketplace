---
name: analyze-crash
description: Analyze a crash/diagnostic capture folder (HMI/app logs, PLC/controller logs, Windows events, PerfMon/ETL, network) — catalog the artifacts, build a time-correlated issue timeline over the main log's lifetime, root-cause, and report. Generalized across PLC and HMI software. Usage /log-forensics:analyze-crash -fn "<capture folder>" [--out "<dir>"]
---

The user invoked `/log-forensics:analyze-crash` to analyze a machine/controller crash-or-incident **capture
folder** and produce a correlated root-cause report. **Read-only** on the capture (the only writes
are the report under `--out` plus, optionally, project memory). Do **not** hardcode a specific
PLC/HMI — detect artifact types by pattern/content and apply the matching parser; state assumptions
when something is unfamiliar.

1. **Resolve the capture folder.** `-fn "<path>"` (strip quotes) is required — the capture folder to
   analyze. Read `_manifest.txt` if present (capture time, computer, channels, source dirs). If
   `-fn` is missing or the path does not exist, say so and stop. `--out` (optional) = output
   directory; default `./crash-out/`.

2. **Catalog every artifact** (deliverable §1) — one table: path · type · size · **time-coverage** ·
   parser · relevance. Detect and group by kind (a capture may have any subset):
   - **HMI/app logs** — text `*.log` (e.g. `SPV_*.log`). Pick the **primary** one (largest / matches
     the line numbers of interest) → its lifetime drives the timeline.
   - **PLC/controller logs** — e.g. CODESYS `PlcLog*.csv` (UTC) + config `*.cfg` + audit `.Audit*.log`;
     or other controllers' equivalents. Note rotation (active file = newest).
   - **Windows event logs** — `*.evtx` (System/Application/Security/Setup/Kernel-*).
   - **PerfMon** — `*.blg` (perf counters) and `*.etl` (ETW kernel/WLAN traces). **Check their
     coverage window** — often a short snapshot, possibly *post-crash*.
   - **Network** — `network.config.md` or similar; diff against the prior capture.

3. **Parse binaries (read-only, Windows built-ins):**
   - `.blg` → `relog "<file>.blg" -f CSV -o "$env:TEMP\<x>.csv"` then summarize key counters
     (Processor _Total `% Processor Time`, Memory `Available MBytes` / `% Committed`, PhysicalDisk
     `Disk Write Bytes/sec`, page faults, per-Process if captured).
   - `.etl` → `tracerpt "<file>.etl" -summary "$env:TEMP\sum.txt" -o "$env:TEMP\d.xml" -of XML -y`.
   - `.evtx` → PowerShell `Get-WinEvent -FilterHashtable @{ Path="<f>.evtx"; Id=… }` filtered by time.

4. **Establish the primary log's lifetime & shape** — never full-read a huge log: use `wc -l`,
   `grep -c`, `grep -oE '^\[[0-9]{2}'` hourly histograms, `head`/`tail`. Capture: build/version
   banner(s), start/end timestamps, restart count, and any **log-flood** (dominant repeated line +
   lines/hour) — a runaway log is itself an issue.

5. **Mine each source and build ONE time-correlated timeline** (note timezones — e.g. CODESYS
   PlcLog is UTC, HMI log local):
   - app/HMI: exceptions/`unhandled`, comms error histograms (OPC `BadSecureChannelClosed`/
     `BadRequestInterrupted`/`BadConnectionClosed`, Modbus, etc.), watchdog, reconnect cycles, the flood;
   - controller: crashes/`double free`/heap, comm-cycle/task stalls (`alive=0`, watchdog), device errors;
   - Windows: **reboots** (Kernel-Power `41`, `1074`/`6008`/`6005`/`6006`), **Application Error `1000`**
     — record faulting module + **exception code** and decode it (e.g. `0xC00000FD` = stack overflow,
     `0xE0434352` = .NET, `0xC0000005` = AV), WER buckets;
   - perfmon: CPU/mem/disk/handles in-window (flag if **post-crash**);
   - network: changes / device reachability.

6. **Device tracking** — enumerate every device/peer disconnection or exception across the window,
   with times.

7. **Root cause** — correlate across **≥2 independent sources**; pin the incident to a faulting
   module + exception code + code path when identifiable; separate app vs controller vs OS vs
   network, and **symptom vs cause**. Compare with the immediately-preceding capture if available.

8. **Parallelize when it pays:** for many/large logs, split into disjoint groups and spawn up to
   **5 Explore subagents** (simpler model / lower effort) to mine in parallel, then synthesize.

9. **Deliverables** — write `<out>/Crash.<capture-id>.analysis.md` (capture-id = folder suffix):
   **§1 catalog**, **§2 timeline**, **root cause**, **device tracking**, **verdicts & actions**,
   cross-refs. Report concrete numbers (counts, counter values), not adjectives.

10. **Memory (optional).** If project memory is in use, recall related findings before mining and
    record any new, non-obvious finding (root causes, signal/bit mappings) as you discover it.

Notes: global command. Read-only on the capture; parsed CSV/XML go to `$env:TEMP`, never the output
dir. If a parser/permission prompt appears, the user approves case-by-case. Generalize — the same
flow serves other PLCs (Beckhoff/Siemens/…) and HMIs by detecting their log/trace formats and
applying the right parser.
