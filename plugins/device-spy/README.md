# device-spy

**Read-only** inspectors: an encrypted CODESYS project, a live Ubiquiti router, and the local host's
network — plus `alarm-troubleshooting`, which turns a CODESYS project's alarms into a filled
Troubleshooting workbook. The helpers are scripts bundled in the plugin. Where a secret is needed (CODESYS, Ubiquiti),
it reaches the helper via `os.environ` / STDIN, **never** as a command-line argument and **never** on
disk, and is cleared right after use. Inspectors that connect to or launch a target have an
**approval gate**; `network-probe` is read-only on the local host and doesn't need one.

## Skills

| Skill | What it does | Writes |
| :---- | :----------- | :----- |
| `/device-spy:codesys-spy -pw <password> -fn "<.project>" [--out "<dir>"]` | encrypted CODESYS project → PLCopen XML export (headless) → per-POU source extraction (ST/SFC/LD/FBD decoded) → analysis with Explore subagents | `--out` (default `./codesySpy-out/`) |
| `/device-spy:ubiquity-spy -ip <ip> -user <user> -pw <password> [--out "<dir>"]` | login + read-only GET on a Ubiquiti "System Manager" router → captures the server-rendered dashboard → faithful report of the current config (`field → value` for each pane) | `--out` (default `./ubiquity-out/`) |
| `/device-spy:alarm-troubleshooting -s "<.project>" -pw <password> -l "<translation.json>" [-o "<troubleshooting.xlsx>"] [--spy ["<output>"]] [--out "<dir>"]` | CODESYS PLC alarm/warning definitions + DB translation JSON → Description / Solution / Note authored per row (subagents, guideline in `references/`) → filled **copy** of the Troubleshooting workbook; `--spy` lists every meaningful alarm/warning the PLC defines to `.xlsx`/`.csv`/`.json`/`.md`. Reuses `codesys-spy` for the extraction | `--out` (default `./alarm-troubleshooting-out/`); the production workbook only after the gate, with a `.bak` |
| `/device-spy:network-probe [--out "<dir>"] [--days <N>] [--targets "ip1,ip2,…"]` | read-only snapshot of the local host's network → Markdown report (adapters/drivers, EEE/flow/power, IP, ARP + dup-IP/MAC analysis, routes/DNS, connectivity, e1rexpress/Tcpip events) → **diagnosis** of link-flaps / IP conflicts / stale drivers | `--out` (default `./network-probe-out/`) |

## Bundled resources

The helper scripts are **static** and must not be modified; they are resolved via `$env:CLAUDE_PLUGIN_ROOT`:

```
assets/
  codesySpy/resources/{export_project.py, run_export.bat, extract_pous.py}
  ubiquitySpy/resources/ubiquity_fetch.ps1
  networkProbe/resources/network-config-probe.ps1
```

`alarm-troubleshooting` keeps its scripts next to the skill, in
`skills/alarm-troubleshooting/scripts/` (`extract_alarms.py`, `make_slices.py`, `fill_excel.py`,
`build_spy.py`, `write_spy.py`; Python 3 + `openpyxl`), resolved via `${CLAUDE_SKILL_DIR}`.

## Notes

- `/device-spy:codesys-spy` launches CODESYS headless (heavyweight) → confirm at the approval gate.
  `/device-spy:ubiquity-spy` is login + GET only, **never** a POST that changes the config.
  `/device-spy:network-probe` runs on the local host, read-only (it writes only the report) → no gate;
  best run from an **elevated** shell for complete data.
  `/device-spy:alarm-troubleshooting` writes only into its working folder; the production workbook is
  overwritten only after the approval gate, never while it is open in Excel, and always with a `.bak`.
- **Secret handling** (codesys-spy, ubiquity-spy): the password is ephemeral (env → child process /
  STDIN), cleared after use, never persisted or echoed. `network-probe` uses no secrets.
- Permissions (`cmd /c`, `CODESYS.exe`, `python`, `powershell`, `curl`, file writes) are approved case
  by case — no allow-rule is added unilaterally.

## Installation

```shell
/plugin install device-spy@sistec-plugins
```
