# log-forensics

Analisi forense **read-only** di log e capture PLC/HMI. I comandi catalogano gli artefatti, ne
ricostruiscono una timeline/event-chain correlata nel tempo e producono un report; non modificano
mai la capture (l'unica scrittura è il report sotto `--out`, più — opzionale — la memoria di
progetto). Per molti/grandi log parallelizzano fino a **5 subagent Explore**.

## Skill

| Skill | Cosa fa | Scrive |
| :---- | :------ | :----- |
| `/log-forensics:analyze-crash -fn "<cartella capture>" [--out "<dir>"]` | forensics su una cartella di capture (log HMI/app, log PLC, eventi Windows, PerfMon `.blg`/`.etl`, rete) → timeline correlata + root-cause su ≥2 sorgenti indipendenti. Generalizzato su PLC/HMI diversi (rileva il formato e applica il parser giusto) | `--out` (default `./crash-out/`) |
| `/log-forensics:track-timing [-fn "<log-o-cartella>" …] [-prod] [--upd\|-u ["<src>" …]] [--full]` | consistenza **timing ed event-chain** di un log Fael/HMI (+ JSON `plc_reports`): ricostruisce le catene per-job, segnala link rotti/mancanti/fuori ordine, tabelle timing + salute dispositivi, ledger cumulativo dei pezzi | `reports\` del progetto attivo + stato in `./.trackTiming/` |

## Note

- Entrambi sono **read-only** sulla sorgente; i CSV/XML derivati dai binari (`.blg`→`relog`,
  `.etl`→`tracerpt`) vanno in `$env:TEMP`, mai nella cartella di output.
- `/log-forensics:analyze-crash` è crash-capture-oriented; `/log-forensics:track-timing` è
  production-timing / chain-consistency oriented e porta il vocabolario di event-chain del dominio Fael.
- `track-timing` delega il parsing a `scripts/scan_timing.py` (Python stdlib): analizza tutto il
  log (~9 s per 1,4 M righe), scrive direttamente le tabelle del report e stampa solo un digest con
  le anomalie **nuove** dall'ultimo run (high-water mark per file in `.trackTiming/hwm.json`;
  `--full` per rivederle tutte). `--upd` usa `scripts/sync_logs.py` (append del solo tail, rotazioni,
  backlog saltato). Il catalogo artefatti e la checklist del baseline sono persistiti in
  `.trackTiming/`. Gira con `context: fork` + `model: sonnet`: non può fare domande, quindi le
  eventuali domande (artefatti sconosciuti, cartella di destinazione) finiscono nel report finale.
- I parser usano built-in Windows; un eventuale permesso viene approvato caso per caso.

## Installazione

```shell
/plugin install log-forensics@sistec-plugins
```
