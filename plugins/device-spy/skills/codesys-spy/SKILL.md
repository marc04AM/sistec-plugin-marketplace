---
name: codesys-spy
description: Open a password-protected CODESYS .project, export + extract its program, and analyze it. Usage: /codesySpy -pw <password> -fn "<path to .project>"
---

The user invoked `/codesySpy` to turn an encrypted CODESYS `.project` into readable, analyzed
source. This reproduces the procedure first done in `5309_FAEL-Coordination` (see its
`scripts\process.md`), parameterized via the static, env-driven resources under
`commands\codesySpy\resources\`. **Do not launch CODESYS or write anything until the approval
gate (step 4).**

Resources (do not modify): `commands\codesySpy\resources\export_project.py` (CODESYS IronPython
export), `run_export.bat` (headless launcher), `extract_pous.py` (Python 3 xml.etree extractor).

1. **Parse the arguments** from the text after `/codesySpy` (flags are order-independent):
   - `-pw` → the password = the value after `-pw`, up to the next ` -<flag>` (it may contain `$`,
     spaces if quoted, etc.).
   - `-fn` → the `.project` path (typically quoted; strip the quotes).
   - If either flag is missing, or the `.project` file does not exist, report the exact problem and
     stop — do not proceed.

2. **Resolve output locations.** Use the **active project** tree:
   - `<active-project>\external resources\codesySpy\<project-stem>\` — for the PLCopen XML, the
     per-POU `.txt` files, and the consolidated source. (`<project-stem>` = the `.project` filename
     without extension.)
   - `<active-project>\reports\` — for the analysis report.
   - If no project is active (chat / none), fall back to `commands\codesySpy\out\<project-stem>\`
     and `commands\codesySpy\out\<project-stem>\reports\`.
   - Create the folders as needed.

3. **Auto-detect the newest CODESYS install.** Run the pipe-free, allow-friendly command
   `Get-ChildItem -LiteralPath 'C:\Program Files' -Directory` (or `Get-ChildItem 'C:\Program Files\CODESYS *' -Directory`),
   pick the **newest-versioned** `CODESYS *` folder that contains `CODESYS\Common\CODESYS.exe`, and
   determine its installed **profile name** (the newest `.profile`; profiles live under the install
   and/or `C:\ProgramData\CODESYS\...`). Known mapping (from `process.md`): install `3.5.21.40` →
   profile `"CODESYS V3.5 SP21 Patch 4"`. If detection is ambiguous, state what you found and ask.

4. **Approval gate — APPLY/LAUNCH NOTHING YET.** Show an `AskUserQuestion` recap of: the `.project`
   file, the detected `CODESYS.exe` + profile, and the output directory; options **`Proceed`** /
   **`Cancel`**. Launching CODESYS headless is heavyweight, so confirm first. On `Cancel`, stop.

5. **On `Proceed`, export — set env + run in a SINGLE PowerShell call** (env vars do not persist
   across calls, and the password must ride the environment, never a command line or disk):
   ```powershell
   $env:CODESYS_EXE='<detected CODESYS.exe>'
   $env:CODESYS_PROFILE='<detected profile name>'
   $env:CODESYS_SCRIPT='C:\Users\Sistec 23\source\repos\Claude\commands\codesySpy\resources\export_project.py'
   $env:CODESYS_PROJECT='<-fn path>'
   $env:CODESYS_PW='<-pw value>'      # SINGLE quotes — keeps $ and friends literal
   $env:CODESYS_EXPORT_XML='<out_dir>\<project-stem>.xml'
   cmd /c "C:\Users\Sistec 23\source\repos\Claude\commands\codesySpy\resources\run_export.bat"
   ```
   The `cmd` child and CODESYS inherit the env, so `CODESYS_PW` reaches `export_project.py` via
   `os.environ` without ever being a shell argument. Confirm the output contains
   `Export done: …` and the XML file now exists. If it printed `ERROR: …` (e.g. wrong password),
   surface it and stop.

6. **Extract the program.** Run:
   ```powershell
   python "C:\Users\Sistec 23\source\repos\Claude\commands\codesySpy\resources\extract_pous.py" "<out_dir>\<project-stem>.xml" "<out_dir>" "<out_dir>\program.<project-stem>.txt"
   ```
   Confirm it reports the POU count and wrote the per-POU `.txt` + the consolidated
   `program.<project-stem>.txt`.

7. **Env hygiene.** Clear the secret from the session: `Remove-Item Env:\CODESYS_PW` (the password
   was never written to disk; this just drops it from the live environment).

8. **Analyze.** List the per-POU `.txt` files; split them into up to **5 balanced groups** and spawn
   that many **Explore** subagents (simpler model / lower effort, per P0.5), each reading its group
   and returning a structured summary. Synthesize their findings into one Markdown report — machine
   overview, startup/cycle flow, zone/structure breakdown, key globals — and save it to the
   `reports\` location from step 2 (e.g. `<project-stem>.analysis.md`).

9. **Report** every deliverable path: the XML, the per-POU folder, the consolidated source, and the
   analysis report.

Notes: this command is global; outputs follow the active project. It does not modify the canonical
`5309_FAEL-Coordination` scripts. If a step triggers a permission prompt (`cmd /c`, `CODESYS.exe`,
`python`, file writes), the user approves case-by-case — do not add allow-rules unilaterally (P6).
