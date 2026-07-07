---
description: Collect the local host's network configuration & health into one Markdown report — adapter/driver inventory, NIC advanced props (EEE/flow-control/power), full IP config, ARP + duplicate-IP/MAC analysis, routes/DNS, connectivity tests, and recent NIC (e1rexpress) / Tcpip events. Wraps network-config-probe.ps1; read-only except the report (run elevated for complete data). Usage: /networkProbe [--out <path>] [--days <N>] [--targets "ip1,ip2,…"]
---

The user invoked **`/networkProbe`** to snapshot the **local (production) PC's** network
configuration + health into a single Markdown report — the standing diagnostic for the 5309_FAEL
NIC link-flaps (e1rexpress Ev27) and IP conflicts (Tcpip Ev4199). Wraps the resource script
`network-config-probe.ps1`. **Read-only** except the report file; run from an **elevated** shell for
complete data.

Constants:
- Script: `commands\networkProbe\resources\network-config-probe.ps1`
- Script params → flags: `-OutFile`←`--out`, `-DaysBack`←`--days`, `-PingTargets`←`--targets`.

## 1. Parse
- `--out "<path>"` — report path. Optional (default below).
- `--days <N>` — how far back to pull NIC/Tcpip events (default 7).
- `--targets "ip1,ip2,…"` — comma list of hosts to ping (default = the script's gateway +
  production + known-conflict addresses).
- (`-h`/`--help` is the universal P11 help — handled by the directive, not here.)

## 2. Resolve the output path
- `--out` given → use it.
- Else → the **active Claude project's** `reports\network-config-probe.<yyyyMMdd_HHmmss>.md` (resolve
  the active project from the session; if none, fall back to the scratchpad dir). Create `reports\`
  if missing.

## 3. Run the probe
Single PowerShell call (it runs on **this** machine — the probe collects the *local* host's config):
```
powershell -ExecutionPolicy Bypass -File "<script>" -OutFile "<out>" [-DaysBack <N>] [-PingTargets <ip1>,<ip2>,…]
```
- The script is **read-only** (only the report is written); each section is independent and skips on
  failure. It notes whether it ran **elevated** — if not, surface that the data is partial and
  suggest re-running from an elevated shell (`! powershell …` or "Run as administrator").
- Do not normalize line endings or relocate the script; run it from its resource path.

## 4. Report
- Confirm the report path and surface the **headline findings**: any **duplicate-IP/duplicate-MAC**
  hits (the conflict source), NICs with **Energy-Efficient Ethernet / power-save enabled** or
  AllowComputerToTurnOff, any **NO REPLY** connectivity targets, and the e1rexpress/Tcpip **event
  counts**.
- Read-only diagnostic — nothing else is changed. Log to the active project ledger if one is active (P2).

## Notes
This is the **host** network probe (local NIC/IP/ARP/events). It is **not** the site-topology map
(the `network-configuration` project's node/route/VPN diagram) — that is a separate analytical task,
not wrapped here.
