---
name: analyze-crash
description: Analyze a crash/diagnostic capture folder (HMI/app logs, PLC/controller logs, Windows events, PerfMon/ETL, network) — catalog the artifacts, build a time-correlated issue timeline over the main log's lifetime, root-cause, and report. Generalized across PLC and HMI software. Use when the user has a crash/incident capture folder from a machine or controller and wants its mixed logs catalogued, correlated on one timeline, and root-caused into a single report. Usage: /analyzeCrash [-fn "<capture folder>"]
disable-model-invocation: true
---

The user invoked `/analyzeCrash` to analyze a machine/controller crash-or-incident **capture
folder** and produce a correlated root-cause report. This generalizes the procedure proven on the
`5309_FAEL-Diagnostics` captures (**example only** — e.g. `Crash 20260608_1827`, see
`reports\Crash.20260608_1827.analysis.md` and memory [[time-analysis-job-pattern]],
[[time-analysis-device-tracking]]; treat these as illustrative, not required inputs). **Read-only**
except the report + ledger + memory (no approval gate needed). Do **not** hardcode a specific PLC/HMI — detect artifact types by pattern/content and
apply the matching parser; state assumptions when something is unfamiliar.

1. **Resolve the capture folder.** `-fn "<path>"` if given (strip quotes); else the **newest**
   `Crash *` / capture folder under the **active project**'s `external resources\`. Read
   `_manifest.txt` if present (capture time, computer, channels, source dirs). If nothing resolves,
   say so and stop.

2. **Catalog every artifact** (deliverable §1) — one table: path · type · size · **time-coverage** ·
   parser · relevance. Detect and group by kind (a capture may have any subset). If an artifact's
   type stays unclear after sampling and it looks load-bearing, **stop and ask** before relying on
   it — don't guess:
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
   - If a binary is empty/zero-length or the parser (`relog` / `tracerpt` / `Get-WinEvent`) errors,
     note it as **unreadable** and continue with the remaining sources rather than aborting the run.

4. **Establish the primary log's lifetime & shape** — never full-read a huge log: use `wc -l`,
   `grep -c`, `grep -oE '^\[[0-9]{2}'` hourly histograms, `head`/`tail`. Capture: build/version
   banner(s), start/end timestamps, restart count, and any **log-flood** (dominant repeated line +
   lines/hour) — a runaway log is itself an issue.

5. **Mine each source and build ONE time-correlated timeline** (note timezones — e.g. CODESYS
   PlcLog is UTC, HMI log local — and reconcile any **clock skew/drift** between hosts before
   aligning events; note the offset on the timeline):
   - app/HMI: exceptions/`unhandled`, comms error histograms (OPC `BadSecureChannelClosed`/
     `BadRequestInterrupted`/`BadConnectionClosed`, Modbus, etc.), watchdog, reconnect cycles, the flood;
   - controller: crashes/`double free`/heap, comm-cycle/task stalls (`alive=0`, watchdog), device errors;
   - Windows: **reboots** (Kernel-Power `41`, `1074`/`6008`/`6005`/`6006`), **Application Error `1000`**
     — record faulting module + **exception code** and decode it (e.g. `0xC00000FD` = stack overflow,
     `0xE0434352` = .NET, `0xC0000005` = AV), WER buckets;
   - perfmon: CPU/mem/disk/handles in-window (flag if **post-crash**);
   - network: changes / device reachability.

6. **Device tracking** (per [[time-analysis-device-tracking]]) — enumerate every device/peer
   disconnection or exception across the window, with times.

7. **Root cause** — correlate across **≥2 independent sources**; pin the incident to a faulting
   module + exception code + code path when identifiable; separate app vs controller vs OS vs
   network, and **symptom vs cause**. If only **one** source is available, root-cause from it and
   flag the conclusion as **single-source / lower confidence**. Compare with the immediately-preceding
   capture.

8. **Parallelize when it pays:** for many/large logs, split into disjoint groups and spawn up to
   **5 Explore subagents** (use a simpler model / lower reasoning effort for these read-only miners)
   in parallel, then synthesize.

9. **Deliverables** — write `reports\Crash.<capture-id>.analysis.md` (capture-id = folder suffix):
   **§1 catalog**, **§2 timeline**, **root cause**, **device tracking**, **verdicts & actions**,
   cross-refs. Report concrete numbers (counts, counter values), not adjectives. Minimal shapes:
   - timeline row: `time · source · event · severity`
   - device row: `device · disconnects · first/last · affected tags · correlates-with`

10. **Ledger + memory** — append a `*.log.md` P2 entry for the request; update the project anchor +
    relevant theme memories with any new, non-obvious finding.

Notes: global command; outputs follow the **active project**. Read-only on the capture; parsed
CSV/XML go to `$env:TEMP`, never the reports dir. If a parser/permission prompt appears, the user
approves case-by-case (P6). Generalize — the same flow serves other PLCs (Beckhoff/Siemens/…) and
HMIs by detecting their log/trace formats and applying the right parser.
