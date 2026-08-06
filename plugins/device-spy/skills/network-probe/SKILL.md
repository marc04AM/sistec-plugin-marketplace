---
name: network-probe
description: Snapshot the local Windows host's network configuration and health into one Markdown report, then diagnose it. Covers adapter/driver inventory, NIC advanced properties (Energy-Efficient Ethernet / flow-control / speed-duplex / power), full IP config, ARP with duplicate-IP/MAC detection, routes/DNS, connectivity tests, and recent NIC (e1rexpress) / Tcpip System events. Use whenever a Windows or industrial PC shows intermittent link drops or link-flapping, IP-address conflicts, slow/dropped connections to a PLC/HMI/server, or suspected stale or misconfigured NIC drivers — or when you need a re-runnable baseline of a host's network state. Runs a bundled read-only scanner (best run elevated for complete data), then interprets the findings into a root-cause diagnosis.
---

# Local host network probe

Snapshot the **local machine's** network configuration + health into one Markdown report, then
**diagnose** it. This runs on **this** PC — it collects the local host's NICs, IP config, ARP,
drivers, and events; it is not a remote scan.

## How the work is split

A bundled PowerShell scanner does the **deterministic** collection — do not re-derive its queries by
hand:

```
${CLAUDE_PLUGIN_ROOT}/assets/networkProbe/resources/network-config-probe.ps1
```

It gathers, in one read-only pass, a raw report: adapter inventory + link status + MAC + driver
version/date; the physical-NIC hardware IDs and driver provenance (with an Intel DEV-id → model
decode); NIC advanced properties (EEE / flow-control / speed-duplex / power) and power management;
full IP config; IP-interface settings incl. `DadTransmits`; the ARP/neighbor table with a
**duplicate IP↔MAC analysis**; routes; DNS; connectivity tests; and recent `e1rexpress` / `Tcpip`
System events with counts.

The report is **raw data with hint-notes, not a verdict.** Your job is the part the script can't:
**run it, then read the report and diagnose the root cause** — that diagnosis is the deliverable.

## Step 1 — Resolve options — natural language first

Take the report location, how far back to look, and any extra hosts to ping from what the user says
in conversation (or default them). `--out`/`--days`/`--targets` also work as an explicit **shorthand**
— they map straight onto the scanner's Step-2 parameters (`--out`→`-OutFile`, `--days`→`-DaysBack`,
`--targets`→`-PingTargets`):

- **Report path** — default `./network-probe-out/network.config.md` (create the dir); `--out "<path>"`
  is the shorthand.
- **Lookback window** for NIC/Tcpip events — default 7 days; `--days <N>` is the shorthand.
- **Extra hosts to ping** — the scanner **already auto-detects and pings the gateway(s)**; if the user
  names production servers / PLCs / suspected-conflicting addresses, add them here (`--targets
  "ip1,ip2,…"` is the shorthand).

## Step 2 — Run the probe (read-only)

Single PowerShell call — it writes only the report; every section is independent and skips on
failure:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT/assets/networkProbe/resources/network-config-probe.ps1" -OutFile "<out>" [-DaysBack <N>] [-PingTargets <ip1>,<ip2>,…]
```

The report header states whether it ran **elevated**. If it did **not**, some data is partial —
surface that and suggest re-running from an elevated shell ("Run as administrator") for complete
results.

## Step 3 — Read the report and surface the headline findings

First confirm the scanner actually wrote `<out>`; if the file is missing or empty (the scan errored
before writing), report the scanner failure and stop — there's nothing to diagnose. Otherwise read
the generated report and lead with the signals that matter:

- **Duplicate IP / duplicate MAC** hits (the conflict source).
- NICs with **Energy-Efficient Ethernet / Green Ethernet** enabled, **Flow Control**, non-forced
  **Speed & Duplex**, or **AllowComputerToTurnOff = Enabled**.
- Any **NO REPLY** connectivity target.
- The `e1rexpress` / `Tcpip` **event counts** and their timing.

## Step 4 — Diagnose the root cause (the deliverable)

Correlate the findings — this is where the skill earns its keep:

- **Link-flaps** (`e1rexpress` Ev27 = link down, 32 = up, 33 = transition). Prime suspects, in order:
  **Energy-Efficient / Green Ethernet enabled** (a top cause of periodic link drops → recommend
  Disabled); **NIC power management** `AllowComputerToTurnOff = Enabled` (→ Disabled); **Speed &
  Duplex = Auto** against a fixed-speed switch port (→ force to match); **Flow Control** mismatch.
  Tie the event timestamps to any config that would explain the cadence.
- **IP-address conflict** (`Tcpip` Ev4199). Read the duplicate analysis: an **IP answered by 2+
  MACs** is the conflict — name the offending MAC/host. `DadTransmits` = 0 disables duplicate-address
  detection, which can mask or worsen it.
- **Stale / wrong drivers.** Compare each NIC's `DriverVersion` / `DriverDate` against the current
  vendor release (Intel I210/I211/I219, etc.); flag an old or fallback/compatible-ID binding.
- **Reachability gaps.** A `NO REPLY` to the gateway vs. a production host narrows the fault to the
  local link, the switch, or the far host.

On a **non-Intel NIC** the `e1rexpress` events and Intel DEV-id decode won't apply — say so and fall
back to the vendor-neutral evidence (link status, duplicate IP/MAC, EEE / power / speed-duplex
properties, `Tcpip` events, reachability). State a clear conclusion (most-likely cause + evidence)
and the concrete config changes to try.

## Step 5 — Report

Give the report path, then the diagnosis in this shape:

```markdown
## Headline findings
<duplicate IP/MAC, EEE / power / speed-duplex flags, NO REPLY targets, event counts>
## Root cause (ranked)
1. <most-likely cause> — evidence: <events / config that tie to it>
## Recommended actions
- <concrete NIC / driver / config change to try>
```

The report is re-runnable — re-probe after a change to confirm the flaps/conflicts stopped.

## Notes

- **Read-only** — the only write is the report file. No approval gate needed.
- Run **elevated** for complete data (driver/event/PnP detail); the report flags when it wasn't.
- This is the **local-host** network probe (NIC / IP / ARP / events). It is **not** a site-topology
  map (node/route/VPN diagram) — that is a separate analytical task, out of scope here.
- `powershell` / `Get-WinEvent` / file writes may prompt for permission the first time; the user
  approves case by case.
