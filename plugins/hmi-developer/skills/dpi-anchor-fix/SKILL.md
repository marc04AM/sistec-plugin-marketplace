---
name: dpi-anchor-fix
description: Diagnose and fix the .NET 8 WinForms bug where a control anchored Top|Bottom (a TableLayoutPanel or panel filling a region) collapses to Height 0 — showing up blank or missing — when the app is DPI-aware (PerMonitorV2) but the legacy anchor engine (System.Windows.Forms.AnchorLayoutV2) is off. Use whenever WinForms controls vanish, shrink to zero height, or leave a blank region at high DPI or after a .NET 8 migration, or when auditing which WinForms executable projects carry the risky DPI + anchor mix. A bundled deterministic scanner finds the affected projects; this skill interprets the verdict, recommends one of the two safe configurations, and applies it under confirmation.
---

# WinForms DPI / anchor collapse fix

On .NET 8 a control anchored `Top|Bottom` collapses to **Height 0** when the app is
**DPI-aware (PerMonitorV2)** *and* the **legacy anchor engine** is in use
(`System.Windows.Forms.AnchorLayoutV2` off). The DPI rescale runs while the control is still
detached and the V1 anchor engine latches a transient 0 height. The visible symptom: a panel,
`TableLayoutPanel`, or grid that fills a region shows **empty/nothing** on a high-DPI monitor.

Only the **mix** is broken. The two consistent, safe configurations are:

- **HighDpiMode** — DPI-aware (PerMonitorV2) **+** `AnchorLayoutV2 = true` (crisp on high-DPI).
- **OldMode** — DPI-unaware (uniform bitmap scaling).

## How the work is split

A bundled PowerShell scanner does the **deterministic** detection and edits — do **not** re-derive
its logic by hand (grepping projects yourself is slower and less reliable than the script):

```
${CLAUDE_PLUGIN_ROOT}/assets/dpiRepair/resources/Repair-WinFormsDpiAnchor.ps1
```

It scans a folder for WinForms **executable** projects (`WinExe` / `UseWindowsForms`), reads each
one's DPI setting (manifest → `.csproj` `ApplicationHighDpiMode` → `Program.cs` → default) and its
`AnchorLayoutV2` state, counts the anchored `Top|Bottom` controls at risk, and prints a per-project
verdict. With a fix action it edits `app.manifest` / `.csproj`, backing up every edited file to
`<file>.bak`, and writes a Markdown report to the scanned root.

Your job is the part the script can't: **choose the scope, interpret the verdict for the user,
recommend which safe config fits this app, gate the write, and drive the rebuild + verification.**

## Step 1 — Resolve the scan folder

The scanner's `-ProjectPath` is a **folder**. Take it from the user's argument if given; otherwise
default to the current solution/repo root (the folder containing the `.sln`). It scans recursively,
so a solution root covers every WinForms exe project under it. Confirm the folder exists.

## Step 2 — Check (always first, read-only)

Run the scanner in check mode — it changes nothing:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT/assets/dpiRepair/resources/Repair-WinFormsDpiAnchor.ps1" -ProjectPath "<folder>" -Action None
```

Relay the per-project findings and the report path it writes (`<folder>\DpiAnchorReport_<stamp>.md`).
For each project state the verdict plainly:

- **SAFE (old / DPI-unaware mode)** — no issue.
- **SAFE (HighDpiMode + AnchorLayoutV2)** — no issue.
- **ISSUE PRESENT (DPI-aware + AnchorLayoutV2 off)** — the broken mix; this is what to fix.

If no project shows `ISSUE PRESENT`, say so and stop — there is nothing to repair (offer to
standardize a config only if the user explicitly asks).

## Step 3 — Recommend a config and gate the fix

When at least one project is `ISSUE PRESENT`, recommend a config **with reasoning**, then confirm
before writing:

- Prefer **HighDpiMode** when the app should look **crisp on high-DPI monitors** (the usual choice
  for an actively-maintained UI) — it keeps DPI awareness and switches on the modern anchor engine.
- Prefer **OldMode** when the UI is legacy/pixel-tuned and **uniform bitmap scaling is acceptable**,
  or when enabling `AnchorLayoutV2` risks disturbing hand-tuned layouts.

Then **gate**: present the affected projects, the chosen config, that it **edits**
`app.manifest`/`.csproj` (each backed up to `<file>.bak`), and that a **rebuild is required**. Ask
for explicit confirmation (`Proceed` / `Cancel`) before any write. On `Cancel`, stop.

## Step 4 — Apply (after confirmation)

Run the scanner with the chosen action (non-interactive):

```powershell
powershell -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT/assets/dpiRepair/resources/Repair-WinFormsDpiAnchor.ps1" -ProjectPath "<folder>" -Action HighDpiMode
```

Use `-Action OldMode` for the DPI-unaware config. Relay the script's "Changes applied" list and the
report path.

## Step 5 — Rebuild and verify

DPI/anchor settings are baked at build time, so the fix has **no effect until a rebuild**. Rebuild
the affected project(s) (`dotnet build`), then confirm the previously-collapsing control now renders
at its expected height on a high-DPI monitor.

## Notes

- **Read-only until the Step 3 gate.** Check mode writes only the Markdown report.
- The scanner backs up every file it edits to `<file>.bak` — its own safety net.
- Leave the `app.manifest`/`.csproj` edits **unstaged** for the user's review; don't `git add` them.
- The scanner is **deterministic** — don't hand-edit manifests/csproj yourself; run it and interpret.
- `powershell` / file writes may prompt for permission the first time; the user approves case by case.
