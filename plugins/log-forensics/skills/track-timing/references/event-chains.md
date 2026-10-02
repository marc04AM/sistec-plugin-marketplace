# Fael/HMI event-chain vocabulary

The expected chains that `scripts/scan_timing.py` checks, in words. Read this when an anomaly needs
interpreting, or when a build renamed a message and a pattern in the script's `P` list needs
updating. v3.25 builds use a renamed symbol map (`CellALogic` → `PlcPunchingTeam`/`PressRobotTeam`, …).
`5309_FAEL`, the paths and the IPs are this deployment's values. Swap them for another project.

## Lifecycle (per `Job[id]` / Order)
`FrmHMI Job(…) OnStatusChanged Ready → Start → Running → LoadProgram → TrySendPressConfiguration →
Running → … → PunchingCompleted → Completed | NotCompletable`.
Known gaps to watch for: `Failed` going silent, the `OnResumeProgramAsync` stub, a double
`StopProduction`, and `Scheduled` not clearing.

## First press program (one per job)
`ShowPressBackGaugeReminder` (user-confirmed, *or* `skipped: BackGauges already in position`) →
`PressRobotTeam LoadProgram SendPressConfigurationAsync` → stages
`SendPressbrakeConfiguration {Mode,PMS,BendIndex,program} → SetModeEditorSuccess → LoadProgramSuccess →
OperationComplete → SUCCESS` → `TrySendPressProgram PressProgramLoaded Handshake SUCCESS`.

## Subsequent programs (RobotFollow)
`RobotFollow Condition met: loading program → FollowRobot SendPressConfigurationAsync` → same stages →
`SUCCESS` → `PressProgramLoaded Handshake SUCCESS` [+ `PressBrakeReady Handshake SUCCESS`].

## Punch / transfer / bend cycles
`OnNewPart PunchedSheet`, `OnIdPartChanged … firing NewPart early` [+ `handle inconsistency,
correcting to false`], `PezzoInUscita` Path-B dedup (`OnNewPart Aborted: duplicate`),
`OnTrackingChanged zone <z> … Status:<s>`, `OnPieceOnBsRollerChanged`,
`OnPressBrakeProgramNameChanged <name> IsInf|IsSup`, `Job_ItemStart/ItemComplete/ItemDiscard`.

## What each anomaly usually means
- **SendPressConfigurationAsync FAIL / RETRY**: check whether Mode or BendIndex changed between
  attempts (flagged separately). A changed parameter set means the retry isn't a pure resend.
- **Handshake FAIL**: trace the root. Common ones are `StopRobotFollow`,
  `HandShake.HmiToPlc(Z02_PressbrakeProgramLoaded…) … threw TaskCanceledException`, and a connection `Null`.
- **SendPlcPressProgramInconsistency** (expect 0): compare `idBatch` with
  `Current Sheet on roller: Batch[…]`. They differ when two jobs overlap.
- **dual send (job-boundary race)**: `FollowRobot` and `LoadProgram` both send within 1 s.
- **Cycle Δ** = `T(OnTrackingChanged zone 1 … Status:1) − T(OnNewPart)` per sheet. A negative Δ is
  an ordering race. The report gives avg/σ/race-rate.

## Devices
- **SistecPLC** (CODESYS OPC-UA): `Write/ReadValueAsync … threw ServiceResultException`,
  `SetValueWriteToBus … FAIL`, `UAClient KeepAlive BadSecureChannelClosed/Reconnecting`. Failed tags
  split into heartbeat (`*_LIVE`, `LiveBit_HMI`) and data (`Main_ID_Shell*`, `Main_Handle*`).
- **BSPLC / BS_PUNCHING** (OPC-UA), **PressBrake** (Modbus TCP `192.168.10.35`, `ModbusClient […] Reconnect`),
  **Kuka** (`KrcClient … ContinuousListening FAIL`), **Gade / PressRobotTeam** (`Disconnected`, `StopRobotFollow`).
- If several links drop at the same moment, suspect a site-wide network event before an app fault.

## Real message forms (build v3.32.9761, validated 2026-09-24)

- **Line format**: `[HH:MM:SS.mmm LVL] <msg>`. The date comes from the file name. Settings blocks
  and stack traces are continuation lines with no timestamp.
- **Start banner** (one per application start): `: Sistec.5309AB v3.32.9761.30240 by Sistec AM`,
  preceded by `HMI settings:`. A normal day has 1–10 of them, so restarts are common.
- **Job id**: `FrmHMI Job(Job[3108], Order -952: …) OnStatusChanged <State> ----------->`. A transition
  line `OnStatusChanged Start -----------> Running Job[…]` is followed by the announcement of the
  same state.
- **Real states**: Ready, Start, LoadProgram, TrySendPressConfiguration, Running, PunchingCompleted,
  Completed, NotCompletable, Cancelled, plus the side states Paused, Resumed, NextRunning,
  ReadyToRestart. Numeric values (`513`, `541`) also show up and are flagged.
- **Press send**: the bare `PressRobotTeam LoadProgram|FollowRobot SendPressConfigurationAsync` line
  opens it. Stages follow as `… SendPressConfigurationAsync progress: <Stage>`, with a JSON
  `details: {"Mode": 8, "PMS": true, "BendIndex": 1, "program": "…"}`. The send ends with
  `… SendPressConfigurationAsync SUCCESS|FAIL|RETRY`. Popup: `OnPressFail #<Reason>`.
- **Handshake timeouts**: `HandShake.HmiToEsa(PPMode, PPAckMode) … waiting … Timeout`,
  `HandShake.HmiToPlc(Z02_PressbrakeProgramLoaded, …) waiting ACK true Timeout`.
- **Tracking**: `Job_3113 OnTrackingChanged zone 1 Batch[3113] Status: 1, … (1 / 8) Shells`. A sheet
  reaches zone 1 **minutes** after its `OnNewPart … Count: 1/8 Sheets` (median ~3–4 min), so the
  cycle Δ pairs the n-th OnNewPart of a batch with that batch's n-th zone-1 Status:1.
- **Devices**:
  - OPC-UA: `OpcUaClient SistecPLC … threw ServiceResultException | TIMEOUT | fail:`, and
    `OpcUaClient BSPLC … UNREACHABLE | disconnected | N failed`;
  - UA session: `UAClient KeepAlive status BadSecureChannelClosed … Reconnecting`. It can flood,
    e.g. 42k lines, 44% of a day;
  - Modbus: `Modbus connector <ip:port> Connect failed | reconnected`, and
    `ModbusEsaBend Gade_N disconnection …`;
  - Kuka: `KrcClientLogic_Kuka_N ConnectAsync Fail`, `KrcClient ContinuousListening FAIL`,
    `TcpClient_N Connection failed | I/O error`.
- **End of a job**: the punching cell's chain ends at `PunchingCompleted`. `Completed` arrives
  only when the whole order closes, often much later or in another log.
- **plc_reports rows**: `DataTime` is `HH:MM:SS` (time only) and the date is in `created_at`. Some
  ALM/WRN codes fire all shift long, and the script drops codes seen more than 30 times from the
  correlation.
- **v3.25 (June) extras**: `SendPlcPressProgramInconsistency: idBatch N, … Current Sheet on roller:
  Batch[M]` exists there, along with `progress: LoadProgramFail`.
- **Not present in the September builds**: `ModbusClient […] Reconnect`, `SendPlcPressProgramInconsistency`,
  `firing NewPart early`, `OnNewPart Aborted: duplicate`, `OnPieceOnBsRollerChanged`,
  `StopProduction`, `OnResumeProgramAsync`. The patterns stay in the script in case older or newer
  builds log them.

## Companions
- `plc_reports_<YYYYMMDD>.json`: an array of `{ID, DataTime, Type∈{ALM,WRN,CMD,STA}, ZoneSymbol,
  Text1..3, created_at}`. A same-date file covers this shift, and a prior-date file gives the
  baseline. ALM/WRN rows are used for correlation.
- DB exports (`scripts/export_db_tables.py`): `<date>.json` is table `reports_<date>`, same schema as
  `plc_reports_*`. `alarms_<date>.json` is that day's `alarm_journal`: `{ID, TimeStamp, UID,
  EventTime, Priority, Zone, Name, Extra, Active}`, all strings. One occurrence = one `UID` with a
  raise row (`Active` 1) and a clear row (`Active` 0). `TimeStamp` is when that row was written
  (~2 s late). `EventTime` is the PLC raise time, equal to the report row's `DataTime` and repeated
  on the clear row, so it is not the clear time. It is empty on some rows (4-13%) and stale on old data
  (June). `Priority` 1 = alarm, 2 = warning. Some `reports_<date>` rows on C have `DataTime`
  `00:00`; the scan falls back to `created_at` for them.
- Baseline claims: `5309_FAEL-Coordination\reports\SystemCoordination.md`. Standing procedure:
  `5309_FAEL-Diagnostics\reports\Time.analysis.md`.

## DB companions (5309 FAEL)
- Each cell's `DB.ini` `DB_0.IP` is `127.0.0.1`, the loopback of that cell's own HMI. From the dev
  machine the DB is on the cell's log-share host: AB `192.168.10.10`, C `192.168.10.11`. The tables
  are in database `sistec`.
- The two cells have independent ID sequences (alarm IDs ~426k on AB, ~122k on C in Sep 2026).
  Correlate across cells on timestamp, never on ID.
- AB's `DB_1` (`db_5309c`, "Secondary database, Cell C") points to a database that doesn't exist on
  the AB host (`ERROR 1049 Unknown database`). C's `DB_1` points back to AB's `sistec`. Use `DB_0`
  on both.
- The PLC writes `reports_<date>` and `alarm_journal` even when the HMI log is silent, so a day
  without log changes can still have new DB rows.
