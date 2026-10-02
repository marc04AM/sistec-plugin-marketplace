# Changelog

Modifiche rilevanti ai plugin del marketplace. Formato ispirato a
[Keep a Changelog](https://keepachangelog.com/it/1.1.0/); le versioni sono quelle dei singoli plugin.

## 2026-10-02 — Nuovo plugin blender-ply

**blender-ply 0.1.0** · branch `feat/blender-ply`

### Aggiunto

Plugin per lavorare in Blender, tramite il bridge MCP, su modelli PLY esportati da CAD (in mm,
colori per vertice, nessun materiale). Le skill vengono da sessioni d'uso reali.

- `/blender-ply:visualizzaply`: dopo l'import rende visibili i colori per vertice, calcola il clip
  dalla diagonale del modello, imposta una vista 3/4 centrata e attiva *Zoom to Mouse Position* +
  *Auto Depth*.
- `/blender-ply:centrablender`: centra il modello sulla sagoma a schermo senza cambiare
  l'inclinazione; lo zoom si allontana solo se il modello non ci sta.
- `/blender-ply:centraply`: porta il vertice selezionato (o il punto medio) su (0,0,0), facendo
  coincidere origine oggetto, cursore 3D e origine mondo. Sposta la mesh, quindi vale anche nel
  PLY esportato.
- `/blender-ply:fotografaply`: salva un PNG su sfondo bianco senza overlay tramite viewport render
  (view transform `Standard`, perché con AgX il bianco esce grigio), poi ripristina la vista.
- `/blender-ply:ply-colors`: ripristina i colori per vertice (Solid → `VERTEX` e materiale per
  Material Preview); `detect_ply_colors.py` è la versione in sola lettura.
- Hook `PostToolUse` `ply-colors-nudge.py`: dopo un import PLY o alla prima chiamata Blender della
  sessione interroga Blender in sola lettura e avvisa solo se un modello è davvero mostrato grigio.
- Regola opzionale `rules/blender-ply-colors.md`, da copiare a mano in `~/.claude/rules/`.

### Rispetto alle skill originali

- Percorsi portabili: gli script si caricano da `${CLAUDE_SKILL_DIR}` con un wrapper `exec`, invece
  che da un percorso utente scritto nel codice. Anche `ply-colors` usa ora il wrapper e non invia
  più lo script intero nella conversazione.
- La matematica del viewport (proiezione, centratura, vertici nel mondo) è in
  `lib/view_projection.py`, invece che duplicata in tre script. L'equivalenza con il vecchio ciclo
  di centratura è stata verificata su 300 casi casuali.
- `blender-ply-colors` rinominata in `ply-colors`, per evitare `/blender-ply:blender-ply-colors`.
- SKILL.md e messaggi degli script in inglese; le frasi d'innesco italiane restano nelle description.

### Corretto

- Hook: il messaggio riportava il `color_type` della prima vista invece di quella sbagliata.
- `centraply`: rileva anche rotazioni in quaternioni o asse-angolo (`matrix_basis` invece di
  `rotation_euler`).

## 2026-09-24 — Riduzione del consumo token di gitize, versionize, track-timing

**git-release 0.2.0 → 0.3.0 · log-forensics 0.1.1 → 0.2.0** · branch `perf/skill-token-reduction`

### Motivazione

Statistiche d'uso 2026-06-20 → 2026-09-17 (costo a listino attribuito, non spesa effettiva):

| Skill | Invocazioni | Costo attribuito | Costo per invocazione |
| --- | ---: | ---: | ---: |
| trackTiming | 115 | $544.65 | ~$4.74 |
| versionize | 78 | $194.63 | ~$2.50 |
| gitize | 222 | $327.65 | ~$1.48 |

Il testo delle skill pesava poco (2–4,5k token). Il costo veniva dal lavoro fatto dal modello:
decine di comandi git/DLL/grep eseguiti uno alla volta, output grezzi letti per intero, tabelle
rigenerate a mano e il contesto della sessione ripagato a ogni turno.

### Modificato

**gitize**
- Frontmatter `context: fork` + `model: haiku`: gira in un subagent isolato su un modello economico.
- Nuovo `scripts/collect-changes.ps1`: una sola chiamata risolve il target, scopre i repo e
  restituisce status + stat + hunk a zero contesto. Budget sui diff: 300 righe per file, 600 per
  repo, 1500 in totale. Oltre il budget il riepilogo è solo a livello file, sempre dichiarato.
  Il rumore bin/obj non tracciato viene ignorato e i workspace `.slnx` vengono rilevati.
- SKILL.md da 8,5 a 3,7 KB.

**versionize**
- Frontmatter `model: sonnet`, senza fork: il gate di pre-flight usa `AskUserQuestion`, che nei
  fork non è disponibile.
- Nuovo `scripts/collect-release-facts.ps1`: un solo JSON compatto con fatti git, pre-flight
  (dirty / operazioni in corso / build obsoleta / unpushed), build più recente per progetto
  eseguibile, identità delle DLL, framework, pacchetti centrali e changelog con `-Since` per `-upd`.
- `-new` parte da `FeatureCatalog.md` e legge solo il delta git (`--since=<snapshot>`); `-upd` non
  legge mai il sorgente.
- Le spiegazioni sono in `references/details.md`. SKILL.md da 17,6 a 6,9 KB.
- Fix: `git log <data>..HEAD` (revisione non valida, già presente nella versione precedente)
  sostituito da `--since=<data>`.

**track-timing**
- Frontmatter `context: fork` + `model: sonnet`.
- Nuovo `scripts/scan_timing.py` (Python, solo stdlib):
  - analizza tutti i log (circa 9 s per 1,4 M righe);
  - ricostruisce le catene per-job e segnala anomalie, cicli, race e salute dei dispositivi;
  - correla le sorgenti entro ±5 s su un'unica timeline;
  - scrive direttamente le tabelle del report e mantiene il testo dell'analista tra i marker
    `BEGIN`/`END`;
  - aggiorna `parts-issued.md`;
  - stampa un digest con le sole anomalie **nuove** dall'ultimo run (high-water mark per file;
    `--full` per rivederle tutte).
- Nuovo `scripts/sync_logs.py` per `--upd`: salta il backlog, accoda solo il tail nuovo, sostituisce
  i file ruotati.
- Catalogo artefatti e checklist del baseline salvati in `.trackTiming/`.
- Il vocabolario delle catene di eventi è in `references/event-chains.md`. SKILL.md da 14,7 a 6,7 KB.

**Altro**
- Aggiornati i riferimenti ai passi in `package-release` e `git-split-commits`.
- Aggiornati i README.

### Benchmark

Sei esecuzioni: ogni skill una volta con la versione nuova e una con la versione originale
(snapshot pre-modifica), su fixture identiche. Stesso modello per entrambe, così il confronto misura
solo il flusso di lavoro. Le impostazioni `model`/`context: fork` del frontmatter non entrano in gioco.

| Skill | Fixture | Token nuova / originale | Durata | Tool call | Controlli nuova / originale |
| --- | --- | --- | --- | --- | --- |
| gitize | 3 repo: modifica piccola, file da 700 righe + 1 riga, solo bin non tracciati | 46.560 / 50.807 (**−8%**) | 29 s / 55 s | 4 / 8 | 4/4 / 3/4 |
| versionize | `-new`, tree sporco, build 1 commit indietro | 56.796 / 64.625 (**−12%**) | 96 s / 128 s | 11 / 15 | 4/4 / 4/4 |
| track-timing | 2 log sintetici (8 job, FAIL/RETRY, handshake FAIL, inconsistency, race, artefatto sconosciuto) | 64.140 / 84.676 (**−24%**) | 116 s / 183 s | 13 / 10 | 6/6 / 6/6 |
| **Totale** | | 167.496 / 200.108 (**−16%**) | 241 s / 366 s (**−34%**) | 28 / 33 | 14/14 / 13/14 |

Controlli automatici:
- **gitize**: subject Conventional-Commits ≤ 72 caratteri; Retry citato; modifica C3 (3 → 33)
  descritta; footer `Repos:` senza Demo.App. La versione originale ha perso la modifica a C3,
  perché scartava l'intero repo oltre le 600 righe.
- **versionize**: 4 sezioni nell'ordine giusto; versioni DLL 3.25.4.0 / 2.10.1.0; drift `5e66b02`
  segnalato; tree sporco registrato.
- **track-timing**: nome del report `SPV_5309AB+C_<data>`; handshake FAIL del job 1005; inconsistency
  batch 1007/1006; race 6/24; 24 righe in `parts-issued.md`; artefatto `notes.bin` segnalato.

Parser di track-timing su un log da 1.392.000 righe: 2 min 33 s nella prima stesura (correlazioni
O(n²)), **8,7 s** dopo l'uso di `bisect` e del prefiltro letterale.

### Come leggere i numeri

- Ogni esecuzione include un costo fisso di circa 40k token (prompt di sistema e strumenti del
  subagent). Al netto di questo, la riduzione del lavoro specifico della skill è molto maggiore
  delle percentuali in tabella.
- Le fixture sono piccole. Con le versioni originali il costo cresce con la dimensione di diff e
  log; con le nuove resta quasi costante, perché il modello legge solo digest compatti.
- In uso reale si aggiungono due effetti che il benchmark non misura:
  - il modello più economico (haiku per gitize, sonnet per track-timing e versionize);
  - il fork, che non si porta dietro la conversazione.
- Per track-timing, i run successivi al primo mostrano solo le anomalie nuove.

### Validazione di `scan_timing.py` su log di produzione

Log reali copiati da `\\192.168.10.10` (AB) e `\\192.168.10.11` (C): `SPV_5309AB/5309C` del
2026-09-22 (giorno con problemi: 50k "Reconnect") e del 2026-09-23 (giorno normale), build
v3.32.9761. In totale 161.565 righe.

**Pattern corretti rispetto alla prima stesura** (scritta sui log sintetici):
- ID dei job: `Job(Job[3108], …)` e `Job_3108`.
- Le righe `… SendPressConfigurationAsync progress: <stage>` venivano contate come nuovi invii.
- Banner di avvio: `: Sistec.5309AB v3.32…`.
- Transizioni di stato `A -----------> B` e stati reali: Cancelled, Resumed, Paused,
  ReadyToRestart, NextRunning, più valori numerici.
- Timeout degli handshake (`HandShake.* waiting … Timeout`).
- Messaggi reali di OpcUaClient SistecPLC/BSPLC, UAClient, Modbus connector, Kuka/TcpClient.
- Esiti dell'invio (SUCCESS/FAIL/RETRY) attribuiti al job che ha aperto l'invio.
- Cambio Mode/BendIndex segnalato solo subito dopo un RETRY.
- **Δ di ciclo**: sulla linea reale il pezzo arriva in zona 1 minuti dopo `OnNewPart`. La prima
  stesura accoppiava entro ±30 s e agganciava 4 pezzi su 47; ora accoppia per ordine all'interno
  del batch e aggancia 46/47 e 60/60.
- Rilevamento dei flood: il 22/09, 42.286 righe KeepAlive, il 44% del log.

**Confronto con `grep` indipendente** (conteggi identici su tutti e 4 i file):

| Evento | AB 22/09 | AB 23/09 | C 22/09 | C 23/09 |
| --- | ---: | ---: | ---: | ---: |
| Handshake FAIL | 1 | 3 | 0 | 0 |
| HandShake timeout | 2 | 8 | 0 | 0 |
| SendPressConfigurationAsync FAIL / RETRY | 0 / 0 | 2 / 1 | — | — |
| Pezzi (OnNewPart) | 60 | 47 | 0 | 0 |
| Avvii applicazione | 4 | 10 | 2 | 5 |
| Eventi Kuka | 1.670 | 255 | 18 | 64 |
| Eventi UAClient | 42.365 | 65 | 2 | 6 |

SistecPLC: il parser conta anche `SetValueWriteToBus … FAIL` (48 = 39 + 9 sul 22/09). Le catene
per-job sono state ricontrollate a mano riga per riga. Prestazioni: 0,65 s per 55k righe. Un secondo
run sullo stesso file dà 0 anomalie nuove e 0 pezzi duplicati. `sync_logs.py` sullo snapshot reale
del 24/09 accoda il solo tail.

**Confronto con il report del vecchio `/trackTiming`** (`SPV_5309AB_20260609.md`, build v3.25),
rilanciando il parser sullo stesso log (13.948 righe) e sugli stessi `plc_reports_20260608/09.json`
presi dal NAS (`5309_FAEL-Coordination`):

| Finding del report vecchio | Parser nuovo |
| --- | --- |
| Job 1698: LoadProgramFail → FAIL → RETRY con Mode 8→1 → Handshake FAIL (TaskCanceledException su `Z02_PressbrakeProgramLoaded`) | ✅ stessa catena, stesse righe (L5008–L5198) |
| `SendPlcPressProgramInconsistency` idBatch 1708 / roller 1704 (L12771) | ✅ |
| Invio doppio FollowRobot + LoadProgram entro 200 ms (L12785) | ✅ 0,200 s |
| Job 1701 e 1704 puliti | ✅ CONSISTENT |
| 23 cicli in zona 1, nessun race | ✅ 0/23 |
| Burst SistecPLC 08:25:48 → 08:26:55, solo tag heartbeat | ✅ 34 eventi, `*_LIVE`/`LiveBit_HMI` |
| `plc_reports`: 1.982 righe (148 ALM / 190 WRN / 36 CMD / 1.608 STA) e 6.107 righe | ✅ conteggi identici |

**Correzioni emerse dal confronto:**
- `plc_reports`: `DataTime` contiene solo l'ora; la data si prende da `created_at`. Prima le righe
  lette erano 0.
- `PunchingCompleted` è la fine valida per la cella di punzonatura, perché `Completed` arriva solo
  alla chiusura dell'ordine. I 5 falsi "MISSING-END" del 09/06 sono spariti, e anche il job 3102
  del 22/09, prima segnalato, è ora CONSISTENT.
- `LoadProgramFail` viene contato una volta per invio, non 6 (le righe dei popup lo ripetono).
- I codici ALM/WRN sempre attivi (oltre 30 occorrenze, per esempio `Stations_GeneralWrn_Main_38`)
  sono esclusi dalla correlazione come rumore di fondo.

Differenze note e accettate:
- Modbus: il vecchio report cita 178 "Reconnect", ma nel log non esiste nessuna riga del genere,
  solo `ModbusClient.WriteMultipleRegisters leave`, che il report stesso giudicava routine.
- Il parser non traccia il popup del back-gauge (confermato o saltato) né la formattazione di
  `OnPressBrakeProgramNameChanged`. Sono dettagli di path che il vecchio report citava come benigni.

Non validati: i report vecchi del 12 e 13/07 (i loro log non sono sul NAS) e la checklist del
baseline (`SystemCoordination.md` trovato e copiato; la checklist viene estratta dal modello e non
dallo script).

### Limiti noti

- Con `context: fork` la skill non vede la conversazione: per gitize e track-timing il target va
  passato come argomento. Se manca, gitize usa la cartella corrente e track-timing il log più
  recente del progetto attivo. track-timing non può fare domande, quindi le mette nel report finale.
- I pattern di `scan_timing.py` sono validati sulla build v3.32.9761 (vedi sopra). Se una build
  futura rinomina un messaggio, va aggiornata la lista `P` in cima allo script, insieme alle
  parole chiave di `PREFILTER`.
- L'attribuzione ai job degli eventi senza ID (invii pressa, handshake) segue il "job corrente",
  cioè l'ultimo andato in Running. Con due job che si sovrappongono al cambio job, qualche evento
  può finire sul job adiacente.
