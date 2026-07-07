---
description: Manage the CODESYS Virtual Control PLC containers (Docker inside the Debian WSL distro) via the live codesys.sh lifecycle — up/down/restart/recreate/status/logs/list over one/many/all instances. Wraps `codesys\codesys.sh`; gates the destructive actions (down/recreate). 
Usage: /codesys [<action>] [<name1,name2,…|all>]
---

The user invoked **`/codesys`** to manage the CODESYS PLC containers on Docker inside the
**Debian WSL** distro — a thin wrapper over the live manager script `codesys\codesys.sh` (the same
one the `codesys` `~/.bashrc` launcher calls). `restart`/`recreate` reset the runtime's **2-hour
demo** timer (no WSL reboot needed); after a WSL reboot nothing auto-starts (autostart is disabled)
→ `/codesys up all`.

Constants:
- Manager script (Windows path): `C:\Users\Sistec 23\source\repos\Claude\codesys\codesys.sh`
- WSL mount path: `/mnt/c/Users/Sistec 23/source/repos/Claude/codesys/codesys.sh`
- WSL distro: **Debian**
- Managed instances: `vPLC1 vPLC2 vPLC3 v5315 vKuka vLagNx1525 vEdge` (case-sensitive). `portainer`
  is **standalone — not managed here**.

## 1. Parse
Mirror `codesys.sh`'s own arg grammar:
- **`<action> <names>`** — action ∈ `up|down|restart|recreate|status|logs|list`; names = a
  comma-separated list (no spaces) or `all`.
- **`<names>` alone** → action defaults to **`up`**.
- **`list` alone** → no names needed.
- Unknown action / missing names (for a non-`list` action) → print the usage line and **stop**.
- (`-h`/`--help` is the universal P11 help — handled by the directive, not here.)

## 2. Approval gate — destructive actions only
If the action is **`down`** or **`recreate`** (both remove the container(s); bind-mount data under
`/var/opt/codesysvcontrol/instances/<name>/` is **kept**, but the running runtime is torn down):
`AskUserQuestion` (`Proceed`/`Cancel`) listing the resolved target instances. On `Cancel` → stop.
`up`/`restart`/`status`/`logs`/`list` run directly (no gate).

## 3. Run
Invoke the live script in the Debian WSL distro, passing the action + names through verbatim:
```
wsl.exe -d Debian -- bash "/mnt/c/Users/Sistec 23/source/repos/Claude/codesys/codesys.sh" <action> <names>
```
- Do **not** copy the script to `/tmp` or normalize line endings (the files are LF; in this env a
  `\r` substitution corrupts lines). Run it in place.
- The script auto-detects the license-server `HOST_IP` (eth0); override only if asked
  (`HOST_IP=<ip> /codesys …` → prepend `HOST_IP=<ip>` inside the `bash -c`).
- The WSL VM cold-boots on first access — if a PLC "disappears" right after, give Docker a few
  seconds and re-run `up all`.

## 4. Report
Relay the script's per-instance output (project, state, and any error). For `status`/`list`/`logs`
that's the whole result; for `up`/`restart`/`down`/`recreate` confirm the new state. Nothing is
written to the workspace. Log to the active project ledger if one is active (P2).
