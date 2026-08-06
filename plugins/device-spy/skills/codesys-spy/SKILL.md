---
name: codesys-spy
description: >-
  Open a password-protected CODESYS .project, export + extract its PLC program to readable source,
  then analyze it. Use when the user points at a CODESYS .project (often
  encrypted/password-protected) and wants its POUs/program extracted, made readable, reviewed, or
  analyzed without opening CODESYS by hand. Usage: point at the .project file and give its
  password in conversation, or use flags as shorthand: /codesySpy -pw <password> -fn "<path to
  .project>" [--out "<dir>"]
---

The user invoked `/codesySpy` to turn an encrypted CODESYS `.project` into readable, analyzed
source, via the static, env-driven helper scripts bundled under
`${CLAUDE_PLUGIN_ROOT}/assets/codesySpy/resources/`. **Do not launch CODESYS or write anything
until the approval gate (step 4).**

Resources (do not modify), under `${CLAUDE_PLUGIN_ROOT}/assets/codesySpy/resources/`:
`export_project.py` (CODESYS IronPython export), `run_export.bat` (headless launcher),
`extract_pous.py` (Python 3 xml.etree extractor).

1. **Resolve the project file + password — natural language first.** Take the `.project` path and
   its password from what the user says or points at in conversation; `-pw`/`-fn` also work as an
   explicit **shorthand** (`-pw`'s value runs to the next ` -<flag>` and may contain `$`/spaces if
   quoted; `-fn`'s path is typically quoted — strip the quotes). `--out` optionally names an output
   directory (strip quotes; default `./codesySpy-out/`). If the password or the `.project` path can't
   be resolved from the message either way, or the file doesn't exist, report the exact problem and
   stop — do not proceed.

2. **Resolve output locations.** Under the output dir (`--out`, default `./codesySpy-out/`):
   - `<out>\<project-stem>\` — for the PLCopen XML, the per-POU `.txt` files, and the consolidated
     source (`<project-stem>` = the `.project` filename without extension).
   - `<out>\<project-stem>\reports\` — for the analysis report.
   - Throughout the steps below, **`<out_dir>` = `<out>\<project-stem>\`** (the XML/txt/source path above).
   - Create the folders as needed.

3. **Auto-detect the newest CODESYS install.** Run the pipe-free, allow-friendly command
   `Get-ChildItem -LiteralPath 'C:\Program Files' -Directory` (or `Get-ChildItem 'C:\Program Files\CODESYS *' -Directory`),
   pick the **newest-versioned** `CODESYS *` folder that contains `CODESYS\Common\CODESYS.exe`, and
   determine its installed **profile name** (the newest `.profile`; profiles live under the install
   and/or `C:\ProgramData\CODESYS\...`). Example mapping only — **detect, don't assume**: install
   `3.5.21.40` → profile `"CODESYS V3.5 SP21 Patch 4"`. If **no** `CODESYS *` install containing
   `CODESYS\Common\CODESYS.exe` is found, report that and stop. If detection is ambiguous (several
   installs/profiles), state what you found and ask.

4. **Approval gate — APPLY/LAUNCH NOTHING YET.** Show an `AskUserQuestion` recap of: the `.project`
   file, the detected `CODESYS.exe` + profile, and the output directory; options **`Proceed`** /
   **`Cancel`**. Launching CODESYS headless is heavyweight, so confirm first. On `Cancel`, stop.

5. **On `Proceed`, export — set env + run in a SINGLE PowerShell call** (env vars do not persist
   across calls, and the password must ride the environment, never a command line or disk):
   ```powershell
   $env:CODESYS_EXE='<detected CODESYS.exe>'
   $env:CODESYS_PROFILE='<detected profile name>'
   $env:CODESYS_SCRIPT="$env:CLAUDE_PLUGIN_ROOT\assets\codesySpy\resources\export_project.py"
   $env:CODESYS_PROJECT='<-fn path>'
   $env:CODESYS_PW='<-pw value>'      # SINGLE quotes — keeps $ and friends literal
   $env:CODESYS_EXPORT_XML='<out_dir>\<project-stem>.xml'
   cmd /c "$env:CLAUDE_PLUGIN_ROOT\assets\codesySpy\resources\run_export.bat"
   ```
   The `cmd` child and CODESYS inherit the env, so `CODESYS_PW` reaches `export_project.py` via
   `os.environ` without ever being a shell argument. Confirm the output contains
   `Export done: …` and the XML file now exists. If it printed `ERROR: …` (e.g. wrong password),
   surface it, drop the secret (`Remove-Item Env:\CODESYS_PW -ErrorAction SilentlyContinue`), and stop.

6. **Extract the program.** Run:
   ```powershell
   python "$env:CLAUDE_PLUGIN_ROOT\assets\codesySpy\resources\extract_pous.py" "<out_dir>\<project-stem>.xml" "<out_dir>" "<out_dir>\program.<project-stem>.txt"
   ```
   Confirm it reports the POU count and wrote the per-POU `.txt` + the consolidated
   `program.<project-stem>.txt`. A POU count of **0** (or a script error) means the export hit the
   wrong file or failed to decode — drop the secret
   (`Remove-Item Env:\CODESYS_PW -ErrorAction SilentlyContinue`), report it, and stop before analysis.

7. **Env hygiene.** Clear the secret from the session:
   `Remove-Item Env:\CODESYS_PW -ErrorAction SilentlyContinue` (the password was never written to
   disk; this just drops it from the live environment). Clear it on **every** exit path — including
   the error stops in steps 5–6 — so it never lingers in the session after the run.

8. **Analyze.** List the per-POU `.txt` files; split them into up to **5 balanced groups** and spawn
   that many **Explore** subagents (use a simpler model / lower reasoning effort for these read-only
   summarizers to save budget), each reading its group and returning a structured summary. Synthesize
   their findings into one Markdown report saved to the `reports\` location from step 2
   (e.g. `<project-stem>.analysis.md`), using this skeleton:
   ```markdown
   # <project-stem> — PLC program analysis
   ## Machine overview
   ## Startup & cycle flow
   ## Zones / structure breakdown
   ## Key global variables
   ```

9. **Report** every deliverable path: the XML, the per-POU folder, the consolidated source, and the
   analysis report.

Notes: outputs go under `--out` (default `./codesySpy-out/`). The bundled resource scripts are
static — do not modify them. If a step triggers a permission prompt (`cmd /c`, `CODESYS.exe`,
`python`, file writes), the user approves case-by-case — do not add allow-rules unilaterally.
