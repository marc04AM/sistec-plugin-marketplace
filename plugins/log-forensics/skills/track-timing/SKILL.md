---
name: track-timing
description: Track timing & event-chain consistency of a Fael/HMI application log (+ sibling PLC report JSONs). Catalogs all artifacts first, reconstructs per-job event chains (lifecycle → press/RobotFollow programs → handshakes → punch/track cycles), flags every broken/missing/out-of-order link, builds timing + device-health tables, and reports. `-fn` accepts MULTIPLE paths (logs and/or folders) merged into ONE unified timeline with cross-source correlation. `--upd`/`-u <src…>` first refreshes the local log copies (append-only delta where possible) before analyzing. Every run also maintains a cumulative parts-issued table. Use when the user wants to verify runtime timing / event-chain consistency of a Fael/HMI log, spot broken or out-of-order job chains or device-health issues, or refresh and re-analyze those logs. Usage: /trackTiming [-fn "<log-or-folder>" …] [-prod] [--upd|-u ["<src>" …]]
disable-model-invocation: true
---

The user invoked `/trackTiming` to verify the **runtime timing and event-chain consistency**
of the Fael HMI/PLC coordination from its own logs (`5309_FAEL`, the paths, and the IPs below are
this deployment's values — swap them for the target project). This distils the standing
"Time analysis" procedure (`5309_FAEL-Diagnostics\reports\Time.analysis.md`, memories
[[time-analysis-job-pattern]], [[time-analysis-device-tracking]], [[time-analysis-doc]],
[[zone1-handoff-timing]]) into a reusable command. It complements [[analyzecrash-command]]
(crash-capture focused) — this one is **production-timing / chain-consistency** focused.
**Read-only** except the report + ledger + memory (no approval gate) — **plus**, in `--upd`/`-u`
mode, the local log copies it refreshes (append/create into the project's log folders; the source
paths are never written). v3.25 builds use the [[sistec-hmi-v325-renames]] symbol map
(`CellALogic`→`PlcPunchingTeam`/`PressRobotTeam`, …).

0. **Update mode — refresh local copies first (`--upd` / `-u ["<src>" …]`).** Only when
   this flag is present. **Sources:** the given **source** path(s) (each a folder or a single
   file; never written to). **If `--upd` is passed with NO path** → reuse the source list from the
   **last `--upd` run**, read from the state file `./.trackTiming/upd-sources.txt`
   (one path per line); if that file is missing/empty, say so and stop. At the end of every
   `--upd` run that received explicit paths, **(over)write** that state file with the paths used.
   Pull fresh log data into the project's **local log folders** — the `external resources\…`
   folders that already hold the logs (e.g. `logs-ab\` / `logs-c\`). For **each** source file,
   match it to an existing local file **by name** (and naming convention — `SPV_5309AB_*` belongs
   with the other `SPV_5309AB_*`, `SPV_5309C_*` with the C folder; `plc_reports_<date>.json`
   likewise).

   **Youngest-floor filter (skip the backlog).** Per matching local folder, find the **youngest**
   (most-recently-modified) local file and consider in the source **only** files at least as young
   as it (source `LastWriteTime` ≥ that floor; equivalently, date-in-name ≥ the newest local
   date). Everything older is already fully captured locally — do not re-stat or re-copy it. The
   floor is **per folder/cell** (`logs-ab\` floor vs `logs-c\` floor computed separately). If a
   local folder is empty, there is no floor → all matching source files are candidates.

   Then update each candidate's local copy by the **cheapest correct** path:
   - **No local match** → it's new: **full-copy** the file into the folder its naming convention
     dictates (if the convention is ambiguous and no sibling folder fits, ASK where it belongs).
   - **Local exists & source is a strict append** (same head/prefix, source ≥ local size) →
     **append only the new tail** to the local copy (the bytes/lines past the local length).
     Then analyze **only** that appended slice — the **delta-only** rule ([[P14]]: only the new
     bytes past the local length, never a full re-read) — and **merge** into the existing report
     (advance the high-water mark).
   - **Source shrank / rotated / restarted** (smaller than local, head differs, or a new
     start-banner / earlier-than-HWM first timestamp) → **full-copy (overwrite)**, treat as a new
     file/restart: **full** analysis, **reset** the HWM, and note the rotation (P14 boundary case).
   - **Identical** (same size + content) → no-op; nothing new to analyze.
   Report per file what was done (created / appended N lines from line M / full-replaced / skipped).
   After the sync, the analysis target = the set of local files that were created or grew; proceed
   through §1+ on those (an append-grown file is analyzed delta-only per P14; a new/replaced file
   in full). If `-fn` is also given, it adds further targets; if no file changed, say so and stop.

1. **Resolve the source(s).** `-fn` accepts **one OR MORE** paths (strip quotes from each);
   each is a `.log` file **or** a capture folder (a folder contributes every `SPV_*.log` in it,
   plus its sibling companions per §2). `-prod` → newest `SPV_*.log` on
   `\\192.168.10.10\Condivisa\Sistec\Logs`. With neither flag → the newest `SPV_*.log` under the
   **active project**'s `external resources\`. If nothing resolves, say so and stop. Build the
   union set of primary logs and label each by its source/**cell** (e.g. AB vs C, by file
   stem `SPV_5309AB_*` / `SPV_5309C_*`), since one merged run commonly spans the two cells of a
   line that hand off to each other.

   **Unified time context (when >1 source resolves).** Treat **all** sources as a single
   timeline keyed on the absolute wall-clock timestamp (`HH:MM:SS.mmm`) — do **not** analyze
   each log in isolation and staple the reports together. Confirm the sources overlap in time
   (note any clock skew between hosts; if a source's window is disjoint, say so and analyze it
   separately). Per-source parsing/chains (§4–§8) still happen per log, but every anomaly is
   then **placed on, and reasoned about within, the one shared timeline** (§6 correlation).

2. **Catalog ALL artifacts first — including unknown types (deliverable §1).** Enumerate
   every file in the source folder. For each, give path · type · size · time-coverage ·
   role. For any artifact whose meaning/purpose isn't already known, **read it** (head/
   sample large files) to infer schema and role. **If reading still does not clarify what
   it is or how it relates to the analysis, STOP and ASK the user** — do not guess — then
   record the answer in the catalog. Only proceed once every artifact is catalogued. (A **known**
   companion that fails to parse — e.g. a corrupt `plc_reports_*.json` — is noted as **unusable** and
   the run continues; the STOP-and-ASK is only for genuinely unidentifiable artifacts.) Known
   companions to fold in:
   - **HMI/app log** `SPV_*.log` — the **primary** timeline (drives the run's window).
   - **PLC reports** `plc_reports_<YYYYMMDD>.json` — array of
     `{ID, DataTime, Type∈{ALM,WRN,CMD,STA}, ZoneSymbol, Text1..3, created_at}`
     (ALM=alarm, WRN=warning, CMD=command, STA=status/log). Same-date file = this shift;
     a prior-date file = baseline/context. Correlate ALM/WRN bursts to chain breaks.

3. **Recall-first; read the baseline.** Recall memory before reading (P0). Read
   `5309_FAEL-Coordination\reports\SystemCoordination.md` — its claims are the checklist
   the live log is tested against (CONFIRMED / CONTRADICTED / PARTIAL).

4. **Parse the primary log's shape** — never full-read a huge log: `wc -l`, `grep -c`,
   hourly histograms, `head`/`tail`. Capture build/version banner, start/end, restart count,
   any log-flood. If the primary log is empty or has no parseable banner/timestamps, say so and
   stop; if it ends mid-chain (partial capture), mark the trailing chains **truncated**, not broken.

5. **Reconstruct per-job event chains** keyed by `Job[id] / Order`:
   - **Lifecycle:** `FrmHMI Job(…) OnStatusChanged Ready → Start → Running → LoadProgram →
     TrySendPressConfiguration → Running → … → PunchingCompleted → Completed|NotCompletable`.
   - **First press program** (one per job): `ShowPressBackGaugeReminder` (user-confirmed
     *or* `skipped: BackGauges already in position`) → `PressRobotTeam LoadProgram
     SendPressConfigurationAsync` → stages `SendPressbrakeConfiguration {Mode,PMS,BendIndex,
     program} → SetModeEditorSuccess → LoadProgramSuccess → OperationComplete → SUCCESS` →
     `TrySendPressProgram PressProgramLoaded Handshake SUCCESS`.
   - **Subsequent programs** (RobotFollow): `RobotFollow Condition met: loading program →
     FollowRobot SendPressConfigurationAsync` → same stages → `SUCCESS` →
     `PressProgramLoaded Handshake SUCCESS` [+ `PressBrakeReady Handshake SUCCESS`].
   - **Punch / transfer / bend cycles:** `OnNewPart PunchedSheet`, `OnIdPartChanged …
     firing NewPart early` [+ `handle inconsistency, correcting to false`], `PezzoInUscita`
     Path-B dedup (`OnNewPart Aborted: duplicate`), `OnTrackingChanged zone <z> … Status:<s>`,
     `OnPieceOnBsRollerChanged`, `OnPressBrakeProgramNameChanged <name> IsInf|IsSup`,
     `Job_ItemStart/ItemComplete/ItemDiscard`.

6. **Per-link consistency (the core check).** For each expected step in every chain, mark
   CONSISTENT / INCONSISTENT / MISSING / OUT-OF-ORDER. Flag specifically:
   - `LoadProgramFail`, `SendPressConfigurationAsync FAIL`, `RETRY` (and any **Mode /
     BendIndex change between attempts**), `OnPressFail.*` popups;
   - `PressProgramLoaded`/`PressBrakeReady` `Handshake FAIL` — trace its root
     (`StopRobotFollow`, `HandShake.HmiToPlc(Z02_PressbrakeProgramLoaded…) … threw
     TaskCanceledException`, connection `Null`);
   - `TrySendPressProgram SendPlcPressProgramInconsistency …` (**expect 0**) — record the
     `idBatch` vs the `Current Sheet on roller: Batch[…]` (cross-job overlap);
   - concurrent dual sends (`FollowRobot` **and** `LoadProgram` `SendPressConfigurationAsync`
     firing together — job-boundary race);
   - lifecycle gaps from [[job_setstatus_call_tree]] (`Failed` silent, `OnResumeProgramAsync`
     stub, double `StopProduction`, `Scheduled` not clearing).

   **Cross-log correlation (mandatory whenever an issue/anomaly is found).** For **every**
   flagged issue, look up any correlated data across **all** sources in the unified timeline —
   not just the log it surfaced in. Take the issue's timestamp and scan a tight window around
   it (default **±5 s**, widen to ±60 s for slow/handshake chains) over every other source for:
   a device drop/reconnect, an alarm/warning burst (ALM/WRN from a `plc_reports_*.json`), a
   cross-cell handoff event (e.g. an AB job/part event vs a C-side tracking/robot event, the
   `JobList` bus, a shared device), a restart/teardown, or the same symptom on the other cell.
   Decide and **state explicitly**: correlated (→ likely common root, e.g. a [[site-network]]
   drop hitting both cells, or an upstream cell starving the downstream one) **or** isolated
   (→ local to that chain). A simultaneous multi-source/multi-link event ⇒ infrastructure, not
   an app fault. Cite the correlated `log:line` + timestamp from each source involved.

7. **Timing tables.** Cycle Δ = `T(OnTrackingChanged zone 1 … Status:1) − T(OnNewPart)` per
   sheet → ordering race (negative = race); report avg/σ/race-rate. Also: per-stage press
   send durations, and first-program send latency after `Running`.

8. **Device connectivity & exceptions — all devices** (Time.analysis §D). Per device/link
   collect count, first/last, hourly distribution, affected tags, correlation to gaps:
   - **SistecPLC** (CODESYS OPC-UA): `WriteValueAsync/ReadValueAsync … threw
     ServiceResultException`, `SetValueWriteToBus … FAIL`, `UAClient KeepAlive
     BadSecureChannelClosed`/`Reconnecting`. Classify failed tag: heartbeat (`*_LIVE`,
     `LiveBit_HMI`) vs data (`Main_ID_Shell*`, `Main_Handle*`).
   - **BSPLC / BS_PUNCHING** (OPC-UA), **PressBrake** (Modbus TCP `192.168.10.35`:
     `ModbusClient […] Reconnect`), **Kuka** (`KrcClient … ContinuousListening FAIL`),
     **Gade / PressRobotTeam** (`Disconnected`, `StopRobotFollow`).
   A simultaneous multi-link drop ⇒ likely a [[site-network]] event, not an app fault.

9. **Report (deliverable).** Save to the **active project**'s `reports\<base-name>.md` —
   `<base-name>` = the single log's name (extension dropped) for one source; for several, a combined
   stem — `SPV_5309AB+C_<date>` when merging same-family cell logs, `<folder>_merged_<date>` when
   merging a whole folder of mixed logs. Sections:
   (1) artifact catalog (all sources); (2) consistency table vs `SystemCoordination.md`;
   (3) per-job chain table + anomaly list (tag each row with its source/cell); (4) timing table
   (Δ avg/σ/race-rate); (5) per-device health table (all sources); (6) headline findings. When
   >1 source was merged, add a **unified-timeline / cross-correlation** section: the merged
   chronological view of the issues across sources and, for each, the §6 correlation verdict
   (correlated-with-what vs isolated). Cite `log:line` + timestamp (and source) for every claim.
   Then **persist notable findings to memory** (a `time-analysis-finding-<date>` per notable
   incident; suffix the cell when per-cell, e.g. `-c`) and append the request/result to the
   active project's `*.log.md` ledger (P2).

10. **Maintain the running parts-issued table (`reports\parts-issued.md`) — on every run** (so the
    cumulative ledger stays complete no matter which slice was analyzed). Extract one
    row per punched part from the analyzed slice — every `OnNewPart PunchedSheet[<IdBatch>] Length:
    <Length>, …, Count: <ID_part>/<n> Sheets` (parts come from the AB punching cell; the C log
    contributes none). Columns exactly **`| IdBatch | ID_part | IssueTime | Length |`** (IssueTime =
    the part's log timestamp, datestamped; Length = the logged PunchedSheet value, 1/10 mm). **Append
    only new rows** keyed by **(IdBatch, ID_part)** — never duplicate an existing pair (delta-only per
    P14 makes this natural); keep rows ordered by IssueTime and refresh the "Last updated" line. Create
    the file from the template header if it does not exist. This table is cumulative across all runs —
    it is **not** reset per day/log.
