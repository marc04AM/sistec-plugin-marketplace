# log-forensics

Analisi forense **read-only** di log e capture PLC/HMI. I comandi catalogano gli artefatti, ne
ricostruiscono una timeline/event-chain correlata nel tempo e producono un report; non modificano
mai la capture (l'unica scrittura è il report sotto `--out`, più — opzionale — la memoria di
progetto). Per molti/grandi log parallelizzano fino a **5 subagent Explore**.

## Comandi

| Comando | Cosa fa | Scrive |
| :------ | :------ | :----- |
| `/analyzeCrash -fn "<cartella capture>" [--out "<dir>"]` | forensics su una cartella di capture (log HMI/app, log PLC, eventi Windows, PerfMon `.blg`/`.etl`, rete) → timeline correlata + root-cause su ≥2 sorgenti indipendenti. Generalizzato su PLC/HMI diversi (rileva il formato e applica il parser giusto) | `--out` (default `./crash-out/`) |
| `/trackTiming -fn "<log-o-cartella>" [-prod] [--baseline "<SystemCoordination.md>"] [--out "<dir>"]` | consistenza **timing ed event-chain** di un log Fael/HMI (+ JSON `plc_reports`): ricostruisce le catene per-job, segnala link rotti/mancanti/fuori ordine, tabelle timing + salute dispositivi | `--out` (default `./timing-out/`) |

## Note

- Entrambi sono **read-only** sulla sorgente; i CSV/XML derivati dai binari (`.blg`→`relog`,
  `.etl`→`tracerpt`) vanno in `$env:TEMP`, mai nella cartella di output.
- `/analyzeCrash` è crash-capture-oriented; `/trackTiming` è production-timing / chain-consistency
  oriented e porta il vocabolario di event-chain del dominio Fael.
- I parser usano built-in Windows; un eventuale permesso viene approvato caso per caso.

## Installazione

```shell
/plugin install log-forensics@sistec-plugins
```
