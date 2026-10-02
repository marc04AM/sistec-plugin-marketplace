# Authoring guideline — fill Description & Solution for PLC alarms/warnings

You are filling the columns of a machine **Troubleshooting** sheet. Each input row is one alarm or
warning raised by a CODESYS PLC.

## Machine
<!-- The skill replaces this comment with one paragraph on the machine (cell type, zones/stations,
main devices), taken from the codesys-spy analysis or the PLC source. -->

## Input (your slice JSON — array of rows)
Each row:
- `key` — StringName the PLC writes into the alarm/warning array (do NOT change).
- `sheet` — "Alarms" or "Warnings".
- `name` — the operator-facing text: column D of the workbook, or in spy mode the English
  translation (Italian if there is none). **This is the source of truth for what the alarm
  means.** It reads like `"<device / area>: <condition>"`.
- `meaning` — a short generic PLC-comment for the device-FB index (may be Italian, may diverge
  from `name`; use only as a hint — `name` wins).
- `italian` — Italian translation (often just a code like "Z1: Alm_11"; ignore if not descriptive).
- `condition` — the raw PLC trigger expression/signal for station alarms/warnings (e.g.
  `NOT GVL.I.iQE_SQ_AirGeneral`, sensor tags like `S44.1`, `SQ516.01`). Empty for device-FB rows.
- `coded` — `true` = active in PLC; `false` = the trigger is **commented-out** in the PLC (alarm
  defined but not currently active); `null` = raised inside a reusable device function block.
- `fb` — device-FB family when applicable: `Valve` | `Inverter` | `Encoder` | `AnalogScaling`.

## Output (write ONE JSON object)
`{ "<key>": {"description": "...", "solution": "...", "note": "..."}, ... }`
- One entry per input row, keyed by `key`. `note` = "" unless a note is warranted (see below).
- English. Concise, technical, operator/maintenance-facing. No fluff.

## Description — describe the PROBLEM that raised the alarm
- State the physical condition/cause, grounded in `name` (+ `condition` signal when present).
- If `condition` names a sensor/signal (e.g. `S44.1`, `SQ516.01`, `80.07`, `iSafe_...`), cite it
  so a technician can find it. Example: name "Insufficient air pressure for air general
  (minimum 6 bar required) signal 80.07", condition `NOT GVL.I.iQE_SQ_AirGeneral` →
  *"Main air pressure is below the required minimum (6 bar). Pressure switch 80.07
  (iQE_SQ_AirGeneral) is not confirming adequate air supply."*
- Do NOT invent signal numbers not present in `name`/`condition`.

## Solution — the action to remove the source
Give the concrete corrective action(s). Use these **device-FB patterns** (keyed by `fb` + index in key):
- **Valve** (double-acting pneumatic, 2 position sensors A/B):
  - `_01` Timeout pos A / `_02` Timeout pos B: valve/cylinder didn't reach the position in time →
    "Check the position-{A/B} sensor and its wiring/alignment; verify pneumatic supply pressure and
    the valve solenoid; check for mechanical jam/obstruction; confirm the cylinder reaches
    position {A/B} within the timeout."
  - `_03` Inconsistent position: both A and B (or neither) read active together → "Check both A and
    B position sensors and wiring; a stuck-on or misaligned sensor gives a false simultaneous
    reading. Re-adjust the sensor(s)."
  - `_04` Position A lost / `_05` Position B lost: confirmed position dropped without a move command →
    "Check the {A/B} sensor mounting/alignment and wiring; verify the cylinder is not drifting and
    that air holding pressure is maintained."
- **Inverter** (motor drive / positioning axis):
  - `_01` Driver/Fault: "Read the fault code on the inverter/drive display, remove the cause
    (over-current, over-temperature, mains, motor), then reset the drive fault (power-cycle if it
    persists)."
  - `_02`/`_03` Hardware limit switch A/B: "Jog the axis off the limit switch; check the limit
    switch and wiring; verify travel range and mechanical end-stops."
  - Software limit / positioning / timeout move / target out of range (see `name`): "Check the
    target position and travel limits vs the mechanics; verify the encoder/feedback; clear the
    fault and re-home/re-reference the axis; re-run the move."
  - interlock (Wrn): "Informational: the move is blocked by an interlock condition — satisfy the
    named precondition (safety, position of the mating device) to allow the movement."
  - Manual/semi-auto/auto command not possible (Wrn): "The requested command is blocked in the
    current state — check mode, enabling conditions and interlocks for that command."
- **Encoder**: `_01` Position error: "Check encoder wiring/coupling and mounting; re-reference the
  axis." `_02` EEPROM error: "Power-cycle; if it persists re-initialize or replace the encoder."
  Speed/adjustment warnings: informational — verify speed setpoint / that adjustment preconditions
  are met.
- **AnalogScaling** (analog sensor, e.g. vacuum PTxxx): parameter/sensor fault → "Check the analog
  sensor and its wiring/scaling parameters (min/max); replace the sensor if faulty." under/over
  range (Wrn) → "Input is outside the scaled range — check the sensor and the process value."
- **Station / safety** categories (use `name` + `condition`):
  - Emergency stop pushbutton: "Release/reset the emergency stop, verify no genuine hazard, then
    acknowledge the alarm and re-arm safety."
  - Light curtain: "Clear the light-curtain area of obstructions/personnel, then reset."
  - Air pressure (general/vacuum): "Restore the air supply to ≥6 bar; check the compressor, FRL,
    and the pressure switch."
  - EDM / safety status (KMxx): "Safety contactor feedback (EDM) mismatch — check the named safety
    relay/contactor and its feedback wiring; reset safety."
  - Handrail/parapet, mode selector, HMI comms, etc.: give the specific, sensible corrective action.

## Note column — set only when warranted
- If `coded == false`: `note` = "Defined in PLC but the trigger is currently commented-out/disabled
  (not active in this version)." Add the PLC-comment reason if `name`/`meaning` implies one (e.g.
  "second sensor not present").
- If a row is a pure information/status warning (not a fault): `note` = "Informational status, not a
  fault."
- Otherwise `note` = "".

Author every row in your slice. Return only the JSON object (no prose).
