# device-spy

Ispettori **read-only**: un progetto CODESYS cifrato, un router Ubiquiti live, e la rete dell'host
locale. Gli helper sono script bundlati nel plugin. Dove serve un segreto (CODESYS, Ubiquiti) questo
raggiunge l'helper via `os.environ` / STDIN, **mai** come argomento di riga di comando e **mai** su
disco, azzerato subito dopo l'uso. Gli inspector che si connettono o lanciano un target hanno un
**approval gate**; `network-probe` è read-only sull'host locale e non ne ha bisogno.

## Skill

| Skill | Cosa fa | Scrive |
| :---- | :------ | :----- |
| `/device-spy:codesys-spy -pw <password> -fn "<.project>" [--out "<dir>"]` | progetto CODESYS cifrato → export PLCopen XML (headless) → estrazione sorgente per-POU (ST/SFC/LD/FBD decodificati) → analisi con subagent Explore | `--out` (default `./codesySpy-out/`) |
| `/device-spy:ubiquity-spy -ip <ip> -user <user> -pw <password> [--out "<dir>"]` | login + GET read-only su un router Ubiquiti "System Manager" → cattura il dashboard server-rendered → report fedele della config corrente (`field → value` per ogni pannello) | `--out` (default `./ubiquity-out/`) |
| `/device-spy:network-probe [--out "<dir>"] [--days <N>] [--targets "ip1,ip2,…"]` | snapshot read-only della rete dell'host locale → report Markdown (adapter/driver, EEE/flow/power, IP, ARP + analisi dup-IP/MAC, route/DNS, connettività, eventi e1rexpress/Tcpip) → **diagnosi** link-flap / conflitti IP / driver stale | `--out` (default `./network-probe-out/`) |

## Resource bundlate

Gli script helper sono **statici** e non vanno modificati; sono risolti via `$env:CLAUDE_PLUGIN_ROOT`:

```
assets/
  codesySpy/resources/{export_project.py, run_export.bat, extract_pous.py}
  ubiquitySpy/resources/ubiquity_fetch.ps1
  networkProbe/resources/network-config-probe.ps1
```

## Note

- `/device-spy:codesys-spy` lancia CODESYS headless (pesante) → conferma all'approval gate.
  `/device-spy:ubiquity-spy` è login + GET soltanto, **mai** un POST che cambia la config.
  `/device-spy:network-probe` gira sull'host locale, read-only (scrive solo il report) → nessun gate;
  meglio da shell **elevata** per dati completi.
- **Gestione segreti** (codesys-spy, ubiquity-spy): la password è effimera (env → child process /
  STDIN), azzerata dopo l'uso, mai persistita né riecheggiata. `network-probe` non usa segreti.
- Permessi (`cmd /c`, `CODESYS.exe`, `python`, `powershell`, `curl`, scritture file) approvati caso
  per caso — nessuna allow-rule aggiunta unilateralmente.

## Installazione

```shell
/plugin install device-spy@sistec-plugins
```
