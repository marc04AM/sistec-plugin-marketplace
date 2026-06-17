# device-spy

Ispettori **read-only** di target protetti (un progetto CODESYS cifrato, un router Ubiquiti live).
Entrambi i comandi usano script helper **env-driven** bundlati nel plugin: i segreti raggiungono gli
helper via `os.environ` / STDIN, **mai** come argomento di riga di comando e **mai** su disco, e
vengono azzerati subito dopo l'uso. Entrambi hanno un **approval gate** prima di lanciare/connettersi.

## Comandi

| Comando | Cosa fa | Scrive |
| :------ | :------ | :----- |
| `/codesySpy -pw <password> -fn "<.project>" [--out "<dir>"]` | progetto CODESYS cifrato → export PLCopen XML (headless) → estrazione sorgente per-POU (ST/SFC/LD/FBD decodificati) → analisi con subagent Explore | `--out` (default `./codesySpy-out/`) |
| `/ubiquitySpy -ip <ip> -user <user> -pw <password> [--out "<dir>"]` | login + GET read-only su un router Ubiquiti "System Manager" → cattura il dashboard server-rendered → report fedele della config corrente (`field → value` per ogni pannello) | `--out` (default `./ubiquity-out/`) |

## Resource bundlate

Gli script helper sono **statici** e non vanno modificati; sono risolti via `$env:CLAUDE_PLUGIN_ROOT`:

```
assets/
  codesySpy/resources/{export_project.py, run_export.bat, extract_pous.py}
  ubiquitySpy/resources/ubiquity_fetch.ps1
```

## Note

- `/codesySpy` lancia CODESYS headless (pesante) → conferma all'approval gate. `/ubiquitySpy` è
  login + GET soltanto, **mai** un POST che cambia la config.
- **Gestione segreti:** la password è effimera (env → child process / STDIN), azzerata dopo l'uso,
  mai persistita né riecheggiata.
- Permessi (`cmd /c`, `CODESYS.exe`, `python`, `powershell`, `curl`, scritture file) approvati caso
  per caso — nessuna allow-rule aggiunta unilateralmente.

## Installazione

```shell
/plugin install device-spy@sistec-plugins
```
