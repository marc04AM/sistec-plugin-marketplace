---
name: track-timing
description: Track timing & event-chain consistency of a Fael/HMI application log (+ sibling PLC report JSONs). Catalogs all artifacts first (asks if an unknown one stays unclear), reconstructs per-job event chains (lifecycle → first press program → subsequent RobotFollow programs → handshakes → punch/track cycles), flags every broken/missing/out-of-order link, builds timing + device-health tables, and reports. Usage /log-forensics:track-timing -fn "<log-or-folder>" [-prod] [--baseline "<SystemCoordination.md>"] [--out "<dir>"]
---

The user invoked `/log-forensics:track-timing` to verify the **runtime timing and event-chain consistency**
of the Fael (`5309_FAEL`) HMI/PLC coordination from its own logs. It complements `/log-forensics:analyze-crash`
(crash-capture focused) — this one is **production-timing / chain-consistency** focused.
**Read-only** except the report (under `--out`) and, optionally, project memory. v3.25 builds use
the symbol map (`CellALogic`→`PlcPunchingTeam`/`PressRobotTeam`, …) — recall it from memory if
present.

1. **Resolve the source.** `-fn "<path>"` (strip quotes) — a `.log` file **or** a capture folder.
   `-prod` → newest `SPV_*.log` on `\\192.168.10.10\Condivisa\Sistec\Logs`. If neither resolves, say
   so and stop. `--out` (optional) = output dir, default `./timing-out/`. `--baseline` (optional) =
   path to a `SystemCoordination.md` claims doc to test the live log against (step 3).

2. **Catalog ALL artifacts first — including unknown types (deliverable §1).** Enumerate
   every file in the source folder. For each, give path · type · size · time-coverage ·
   role. For any artifact whose meaning/purpose isn't already known, **read it** (head/
   sample large files) to infer schema and role. **If reading still does not clarify what
   it is or how it relates to the analysis, STOP and ASK the user** — do not guess — then
   record the answer in the catalog. Only proceed once every artifact is catalogued. Known
   companions to fold in:
   - **HMI/app log** `SPV_*.log` — the **primary** timeline (drives the run's window).
   - **PLC reports** `plc_reports_<YYYYMMDD>.json` — array of
     `{ID, DataTime, Type∈{ALM,WRN,CMD,STA}, ZoneSymbol, Text1..3, created_at}`
     (ALM=alarm, WRN=warning, CMD=command, STA=status/log). Same-date file = this shift;
     a prior-date file = baseline/context. Correlate ALM/WRN bursts to chain breaks.

3. **Recall-first; read the baseline.** Recall related memory before reading. If `--baseline` is
   given, read that `SystemCoordination.md` — its claims are the checklist the live log is tested
   against (CONFIRMED / CONTRADICTED / PARTIAL). If no baseline is provided, skip the cross-check and
   report the chains on their own.

4. **Parse the primary log's shape** — never full-read a huge log: `wc -l`, `grep -c`,
   hourly histograms, `head`/`tail`. Capture build/version banner, start/end, restart count,
   any log-flood.

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
   - lifecycle gaps (`Failed` silent, `OnResumeProgramAsync` stub, double `StopProduction`,
     `Scheduled` not clearing).

7. **Timing tables.** Cycle Δ = `T(OnTrackingChanged zone 1 … Status:1) − T(OnNewPart)` per
   sheet → ordering race (negative = race); report avg/σ/race-rate. Also: per-stage press
   send durations, and first-program send latency after `Running`.

8. **Device connectivity & exceptions — all devices.** Per device/link collect count, first/last,
   hourly distribution, affected tags, correlation to gaps:
   - **SistecPLC** (CODESYS OPC-UA): `WriteValueAsync/ReadValueAsync … threw
     ServiceResultException`, `SetValueWriteToBus … FAIL`, `UAClient KeepAlive
     BadSecureChannelClosed`/`Reconnecting`. Classify failed tag: heartbeat (`*_LIVE`,
     `LiveBit_HMI`) vs data (`Main_ID_Shell*`, `Main_Handle*`).
   - **BSPLC / BS_PUNCHING** (OPC-UA), **PressBrake** (Modbus TCP `192.168.10.35`:
     `ModbusClient […] Reconnect`), **Kuka** (`KrcClient … ContinuousListening FAIL`),
     **Gade / PressRobotTeam** (`Disconnected`, `StopRobotFollow`).
   A simultaneous multi-link drop ⇒ likely a site-network event, not an app fault.

9. **Report (deliverable).** Save to `<out>/<log-base-name>.md` (log file name, extension dropped,
   `+ .md`). Sections: (1) artifact catalog; (2) consistency table vs the baseline (if provided);
   (3) per-job chain table + anomaly list; (4) timing table (Δ avg/σ/race-rate); (5) per-device
   health table; (6) headline findings. Cite `log:line` + timestamp for every claim. Then **persist
   notable findings to memory** if project memory is in use.

Notes: global command. Read-only on the source. The Fael event-chain vocabulary above is the domain
value of this command; the baseline checklist is supplied via `--baseline` rather than a hardcoded
project path. If a step triggers a permission prompt, the user approves case-by-case.
