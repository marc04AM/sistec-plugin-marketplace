---
description: Diagnose (and optionally fix) the WinForms "anchored control collapses to Height 0" DPI/dpanchor bug across a solution's WinForms exe projects — reports each project's DPI-awareness + AnchorLayoutV2 + at-risk anchored controls, then applies one of the two safe configs. Wraps Repair-WinFormsDpiAnchor.ps1; check is read-only, fixes are gated and left unstaged (P15). 
Usage: /dpiRepair [--scope|-s "<folder or .sln>"] [--mode check|highDpi|oldMode]
---

The user invoked **`/dpiRepair`** to check (and optionally fix) the WinForms anchored-control DPI
collapse — a control anchored `Top|Bottom` collapses to Height 0 when the app is DPI-aware
(PerMonitorV2) **and** the .NET 8 legacy anchor engine is in use (`AnchorLayoutV2` off). Two safe
configs: **DPI-aware + AnchorLayoutV2=true** (`highDpi`) or **DPI-unaware** (`oldMode`). Wraps the
resource script `Repair-WinFormsDpiAnchor.ps1`.

Constants:
- Script: `commands\dpiRepair\resources\Repair-WinFormsDpiAnchor.ps1`
- `--mode` → script `-Action`: `check`→`None` (read-only), `highDpi`→`HighDpiMode`,
  `oldMode`→`OldMode`. Supplying both `-ProjectPath` + `-Action` runs the script non-interactively.

## 1. Parse
- `--scope` / `-s "<path>"` (also accepts the deprecated `-fn`/`--fn`, hidden from `-h` help) — optional: a folder or a `.sln`. Given-but-nonexistent → usage + stop.
- `--mode check|highDpi|oldMode` — default **`check`**.
- (`-h`/`--help` is the universal P11 help — not implemented here.)

## 2. Resolve the scan root (a folder)
The script's `-ProjectPath` is a **folder**:
- `--scope` is a `.sln` → its containing directory; `--scope` is a folder → that folder.
- **No `--scope`** → the active Claude project's solution root (resolve from `<active-proj>\<active-proj>.log.md`,
  like `/gitize` Step 2); take the solution's root folder. If none resolves → usage + stop.

## 3. Check pass (always, read-only)
Run the script in **check** mode and surface its findings:
```
powershell -ExecutionPolicy Bypass -File "<script>" -ProjectPath "<root>" -Action None
```
Relay the per-project table (DPI-aware + source, AnchorLayoutV2 + source, anchored Top|Bottom
count, verdict) and the report path it writes (`<root>\DpiAnchorReport_<stamp>.md`). If
`--mode check` → **stop here** (nothing changed).

## 4. Fix pass (gated) — `highDpi` / `oldMode` only
If a fix mode was requested:
- If **no** project shows `ISSUE PRESENT`, report that and stop (still offer to apply if the user
  wants to standardize a safe config anyway — only on explicit confirmation).
- Otherwise **approval gate** — `AskUserQuestion` (`Proceed`/`Cancel`) recapping: the affected
  projects, the chosen config (`highDpi` = PerMonitorV2 + AnchorLayoutV2=true; `oldMode` =
  DPI-unaware), that it **edits** `app.manifest`/`.csproj` (backing each up to `<file>.bak`), and
  that a **rebuild is required** for the change to take effect. On `Cancel` → stop.
- On `Proceed`, run the script with the fix action:
  ```
  powershell -ExecutionPolicy Bypass -File "<script>" -ProjectPath "<root>" -Action HighDpiMode   # or OldMode
  ```

## 5. Report & leave unstaged
- Relay the "Changes applied" list + the report path; restate the **rebuild** requirement.
- The edits land in the working tree — **do not `git add`/stage** them; leave them for the user's
  review (P15). The `<file>.bak` backups are the script's own safety net.
- Log to the active project ledger if one is active (P2).
