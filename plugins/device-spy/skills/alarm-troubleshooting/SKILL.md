---
name: alarm-troubleshooting
description: >-
  Fill a machine's Excel Troubleshooting sheet from its CODESYS PLC: for every Alarm and Warning
  row, write the Description (the problem that raised it, grounded in the PLC trigger condition and
  sensor tags), the Solution (the corrective action) and a Note, resolving each row's key through a
  DB-exported translation JSON. Spy mode instead lists EVERY meaningful alarm/warning the PLC
  defines, workbook-independent, to .xlsx/.csv/.json/.md. Use when the user wants to fill, complete
  or write the troubleshooting / alarm sheet of a machine, describe the PLC alarms and their
  remedies, or dump all the alarms a CODESYS project defines — "compila il troubleshooting",
  "descrizione e soluzione degli allarmi", "elenca tutti gli allarmi del PLC", "fill the
  troubleshooting sheet". Usage: point at the .project, its password, the translation JSON and the
  workbook in conversation, or use flags as shorthand: /device-spy:alarm-troubleshooting
  -s "<.project>" -pw <password> -l "<translation.json>" [-o "<troubleshooting.xlsx>"]
  [--spy ["<output>"]] [--out "<dir>"]
---

Turns a CODESYS PLC + a translation export into a filled **Troubleshooting** workbook. Two modes:

- **fill** (default): the rows come from an existing workbook (`-o`); Description, Solution and
  Note are written for each of them.
- **spy** (`--spy`): the rows come from the PLC itself — every meaningful alarm/warning it defines —
  and go to a new file. No workbook needed.

Deterministic work (join, slicing, writing Excel) is done by the bundled scripts in
`${CLAUDE_SKILL_DIR}/scripts/` (Python 3 + `openpyxl`; do not modify them). The judgement — what
each alarm means and how to fix it — is yours, following
`${CLAUDE_SKILL_DIR}/references/authoring-guideline.md`. **The production workbook is never touched
before the approval gate (step 9).**

## 1. Resolve the inputs — natural language first

From the conversation, or from the flags used as shorthand (order-independent, strip quotes):

- `-s` / `--source` — the CODESYS `.project`, or directly a folder already extracted by
  `codesys-spy` (it contains `Reports.txt` and the per-POU `.txt` files).
- `-pw` / `--password` — the CODESYS password. Only needed if the project has not been extracted
  yet. Ephemeral: never write it to a file, report or trace; call it "the CODESYS password".
- `-l` / `--language` — the DB-exported translation JSON (array of
  `{StringName, Italian, English, …}`). Required.
- `-o` / `--output` — the Troubleshooting workbook. Required in fill mode, ignored in spy mode.
- `--spy [<output>]` — spy mode. The extension of `<output>` picks the format (`.xlsx`, `.csv`,
  `.json`, `.md`); without a path, spy only reports the counts and writes no file.
- `--out` — working folder (default `./alarm-troubleshooting-out/`).

If a required input is missing or a path does not exist, say exactly what is missing and stop.
`<stem>` = the `.project` filename without extension; `<work>` = `<out>/<stem>/`.

**Workbook contract** (fill mode): sheets `Alarms` and `Warnings`; column A = StringName key
(often hidden), D = `Name` (operator-facing text, the meaning's source of truth), E = Description,
F = Solution, G = Note (added if missing). A row with a blank A is resolved by matching D against
the translation. If the workbook does not look like this, show what you found and ask.

## 2. Make sure the PLC is extracted

Reuse an existing extraction when there is one: the folder given in `-s`, or
`./codesySpy-out/<stem>/` with `Reports.txt` inside. Otherwise run the **`codesys-spy`** skill on
the `.project` (export + extraction only, with its own approval gate; its analysis step is not
needed here). From the analysis report if it exists, or from `Main.txt` and the `*_Mgmt.txt`
headers, write a one-paragraph **machine context** (cell type, zones/stations, main devices) for
the guideline.

## 3. Stage local copies

Copy the translation JSON and the workbook into `<work>/` and work only on the copies: the original
may sit on a share or be open in Excel.

## 4. Build the key ↔ PLC join

```
python "${CLAUDE_SKILL_DIR}/scripts/extract_alarms.py" "<extract_dir>" "<work>/<translation>.json" "<work>/alarm_join.json"
```

It parses `Reports.txt` (`GVL.Alarms.<Inst>.AlarmsText/WarningText[r,c] := '<key>'; //<meaning>`)
and the station `Alarms()/Warnings()` actions, and gives each key its `condition`, `meaning`,
`coded` (true = active, false = commented out, null = no station assignment, typically a device
function block) and `fb` (Valve / Inverter / Encoder / AnalogScaling). Spy mode: go to step S.

## 5. Split into slices

```
python "${CLAUDE_SKILL_DIR}/scripts/make_slices.py" "<work>/alarm_join.json" "<work>/<workbook>.xlsx" "<work>/slices" --translation "<work>/<translation>.json" --n 4
```

Rows are ordered by key, so instances of the same device stay in the same slice. Report its
warnings: rows whose key could not be resolved, and keys the PLC does not define.

## 6. Author Description + Solution + Note

Copy the guideline into `<work>/slices/GUIDELINE.md`, replacing its `## Machine` comment with the
machine context from step 2. For more than ~60 rows, fan out up to **4 `general-purpose` subagents**
(model `sonnet`), one per slice, each given only its `slice_<n>.json` + `GUIDELINE.md` and writing
`<work>/slices/out_<n>.json` = `{ "<key>": {"description", "solution", "note"}, … }`. For a small
set, author inline into `out_1.json`.

- Reason **per row**: the per-instance `name` often diverges from the generic PLC comment, so a
  per-index template is not enough.
- Description cites the sensor/signal tags present in `name`/`condition`; never invent numbers.
- Write in English, like the guideline, unless the user asks for another language.

## 7. Fill a copy (with validation)

```
python "${CLAUDE_SKILL_DIR}/scripts/fill_excel.py" "<work>/slices" "<work>/<workbook>.xlsx" "<work>/<workbook>.filled.xlsx" --translation "<work>/<translation>.json"
```

It merges the `out_*.json` files and saves **only if** no key is duplicated, every row is authored,
every entry has description + solution and there are no U+FFFD/control characters. On
`VALIDATION FAILED`, fix the listed keys (re-author them) and run it again.

## 8. Spot-check

Open a few filled rows of each kind (station alarm, device FB, commented-out, warning) and check
that Description matches the condition and Solution is actionable. Fix and re-run step 7 if needed.

## 9. Approval gate — before overwriting the production workbook

`AskUserQuestion` recap: rows filled per sheet, the filled copy, the target `-o`. Options
**Proceed** / **Keep copy only**.
- **Proceed**: if a `~$<name>.xlsx` lock file sits next to `-o`, the workbook is open in Excel —
  stop and ask to close it. Otherwise copy the original to `<name>.bak.xlsx`, then copy the filled
  workbook over `-o`.
- **Keep copy only**: the deliverable stays in `<work>/`.

## 10. Report

The filled workbook (copy, and production + `.bak` if written), `alarm_join.json`, and the
coverage counts per sheet.

---

## S. Spy mode (instead of steps 5–10)

S1. **Enumerate** the meaningful alarms/warnings — descriptive translation, or coded in the PLC, or
a device FB with a known meaning; reserved placeholder slots and untranslated generic device codes
are dropped:

```
python "${CLAUDE_SKILL_DIR}/scripts/build_spy.py" "<work>/alarm_join.json" "<work>/<translation>.json" "<work>/spy" ["<work>/slices"] 4
```

Pass a previous fill's `slices` folder to reuse what was already authored. It writes
`spy/spy_all.json` and, for the rest, `spy/spy_slices/slice_*.json`.

S2. **Author** the spy slices exactly as step 6 (guideline into `spy/spy_slices/GUIDELINE.md`).
Untranslated generic device codes get best-effort generic text + a Note saying so.

S3. **Write** (only if `--spy` has a path; a new file, so no gate — but if it already exists, ask
before overwriting):

```
python "${CLAUDE_SKILL_DIR}/scripts/write_spy.py" "<work>/spy/spy_all.json" "<work>/spy/spy_slices" "<output>"
```

Columns: priority · key · area · it · en · description · solution · note. `.xlsx` gives a single
`Troubleshooting` sheet (bold header, frozen row, auto-filter, wrapped cells); `.csv` is UTF-8
with BOM.

S4. **Report** the counts (meaningful total, alarms/warnings, reused vs newly authored) and the
output path.

## Notes

- If a step triggers a permission prompt (`python`, file writes, CODESYS), the user approves case
  by case — do not add allow-rules.
- If `openpyxl` is missing, ask before running `pip install openpyxl`.
