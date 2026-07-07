---
description: Inspect a Ubiquiti "System Manager" router READ-ONLY — log in and save a faithful report of its complete current configuration (interfaces / DHCP / networking / VPN / users). Usage: /ubiquitySpy -ip <ip> -user <user> -pw <password>
---

The user invoked `/ubiquitySpy` to log into a Ubiquiti **"System Manager"** router and **save a
faithful report of its complete current configuration** — every pane (system/identity, interfaces
WAN/LAN, DHCP, networking: internet sharing / NAT / routing, VPN / remote-access settings, users).
The job is **pure configuration extraction**: capture every setting as `field → value` — it does
**not** analyze, conclude, or answer questions about the config. This parameterizes the one-off
inspection first done on `192.168.10.6` in the **network-configuration** project. It is
**READ-ONLY**: it performs a login and HTTP **GET**s only — it never POSTs a configuration change.
**Secret handling: per P9 the password is ephemeral — it rides `$env:UBQ_PW` → the helper's
STDIN, never a command-line argument and never disk; clear it right after and never persist it.**

Resource (do not modify): `commands\ubiquitySpy\resources\ubiquity_fetch.ps1` — env-driven login +
authenticated-dashboard fetch (the dashboard is server-rendered, so all config is inline in its HTML).

1. **Parse the arguments** from the text after `/ubiquitySpy` (flags order-independent):
   - `-ip` → the router IP/host.
   - `-user` → the admin username.
   - `-pw` → the password = everything after `-pw` up to the next ` -<flag>` (may contain `$`,
     spaces if quoted, etc.).
   - Any flag missing → report the exact problem and stop.

2. **Resolve output locations** in the **active project** tree:
   - `<active-project>\external resources\ubiquitySpy\<ip>\dashboard.html` — the captured config.
   - `<active-project>\reports\ubiquitySpy.<ip>.md` — the **configuration report** (main deliverable).
   - If no project is active (chat/none), fall back to `commands\ubiquitySpy\out\<ip>\`.
   - Create the folders as needed.

3. **Approval gate — CONNECT TO NOTHING YET.** Show an `AskUserQuestion` recap: the target `-ip`,
   the `-user`, and the output dir, noting it is a **read-only admin login to a live (possibly
   production) device**. Options **`Proceed`** / **`Cancel`**. On `Cancel`, stop.

4. **On `Proceed`, log in + fetch — set env and run the helper in a SINGLE PowerShell call**
   (env vars don't persist across calls, and the password must ride the environment, never a
   command line or disk):
   ```powershell
   $env:UBQ_IP='<-ip>'
   $env:UBQ_USER='<-user>'
   $env:UBQ_PW='<-pw value>'      # SINGLE quotes — keeps $ and friends literal
   $env:UBQ_OUT='<out_dir>\dashboard.html'
   powershell -NoProfile -ExecutionPolicy Bypass -File 'C:\Users\Sistec 23\source\repos\Claude\commands\ubiquitySpy\resources\ubiquity_fetch.ps1'
   ```
   The helper sends `UBQ_PW` to `curl` over **STDIN** (`--data-binary @-`), so it is never a shell
   argument and never touches disk. Confirm the output shows `DEVICE_TITLE: …`, `LOGIN_OK`, and
   `SAVED_BYTES: …`. If it printed `LOGIN_FAILED` (wrong credentials / unexpected device) or
   `ERROR`/`SAVE_FAILED`, surface it and stop.

5. **Secret hygiene (immediately).** Clear the password from the session:
   `Remove-Item Env:\UBQ_PW` (it was never written to disk; this drops it from the live
   environment). Per P9, do **not** repeat the password value in any later output.

6. **Extract every config field from the saved dashboard HTML** (`<out_dir>\dashboard.html`) — it
   is server-rendered, so all values are inline. The validated extraction method: regex over every
   `<input|select|textarea>` for its `name` (or `aria-labelledby`) + `value`, plus the serialized
   `*Str` / `*ListStr` list fields and any `selected` options. Cover **every pane** (grep the
   anchors, then read the matched regions — don't read the whole 150 KB+ file blindly):
   - **Identity:** `<title>`, `productName`, `hostname`, firmware/os/runtime versions,
     `lanMacAddress` / `wanMacAddress`, NTP, session/password-policy.
   - **Interfaces:** the `pills-interfaces` pane — WAN + LAN IP/mask/MAC, `lanGateway`, DNS,
     **DHCP Server on LAN** (`lanDhcpServer…` mode/pool/lease/reservations), Gateway Priority.
   - **Networking:** the `pills-networking` pane — **Internet Sharing** (`internetSharing…`),
     **NAT Rules** (`dnat…` / `natRulesJsonStr` / external IP pools), **Routing Rules**
     (`routingEntryListStr`, `routingGateway`).
   - **VPN / remote access:** the VPN + `pills-uniqloud` panes — capture the settings as
     `field → value`: `vpnStaticIpPoolListStr`, `vpnStaticIpPoolEnabled`, `*ReachableThroughVPN`,
     the uniqloud "Server connection" fields. (Capture them; do not interpret them.)
   - **Users:** the `pills-users` pane (account list, if shown).

7. **Save the configuration report** — the **primary deliverable**. Write
   `reports\ubiquitySpy.<ip>.md` as a **faithful capture of the router's CURRENT configuration**:
   - a header (IP, device title/product, hostname, LAN/WAN MAC, capture timestamp);
   - **one section per dashboard pane**, listing each setting as `field → value` exactly as read
     (identity, interfaces/WAN/LAN, DHCP server, gateway priority, internet sharing, NAT rules,
     routing rules, VPN/remote-access settings, users) — show empty fields as *(empty)* rather than
     omitting them;
   - a pointer to the captured `dashboard.html`.
   It is a **pure config snapshot** — no analysis, no findings, no conclusions. It must stand alone
   and be re-runnable to diff over time.

8. **Report** every deliverable path (the captured `dashboard.html` + the config report). Note that
   the captured HTML is **device config** (may include sensitive settings) — it lives under
   `external resources\`; the **login password is nowhere on disk**.

Notes: this command is global; outputs follow the active project. **Read-only** — login + GET only,
never a config-changing POST. The password is ephemeral (P9): env → STDIN, cleared after, never
persisted or echoed. Editing `.claude\commands\*.md` is agent-config self-modification
(`[[cannot-self-edit-permissions]]`, P6). If a step triggers a permission prompt (`powershell`,
`curl`, file writes), the user approves case-by-case — no allow-rule is added unilaterally (P6).
