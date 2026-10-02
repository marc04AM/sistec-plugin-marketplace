# git-release

Strumenti di rilascio per le solution **multi-repo** Sistec (la radice della solution non è un repo
git; ogni sottocartella lo è). Le skill condividono la scoperta del set di repo (scansione fresca ad
ogni run, nessuna cache).

## Skill

| Skill | Cosa fa | Scrive |
| :---- | :------ | :----- |
| `/git-release:gitize [--scope\|-s "<target>"]` | aggrega i diff di tutti i sub-repo cambiati (staged + unstaged) in **un** messaggio Conventional-Commits sulla clipboard | clipboard |
| `/git-release:git-split-commits [--scope\|-s "<target>"]` | spezza lo **staged** in più commit raggruppati per impatto, committati interattivamente segmento per segmento | commit |
| `/git-release:git-amend-commits [--scope\|-s "<target>"]` | piega lo **staged** nei commit unpushed esistenti (amend/fixup+autosquash); pianifica un nuovo commit per il resto | commit (amend) |
| `/git-release:versionize -new\|-upd "<target>" [--out <path>]` | release note `ReleaseNote.md` (4 sezioni: Versions, Cell AB, Cell C, Libraries) da DLL già buildate + git; `-upd` antepone un changelog | file `.md` |
| `/git-release:package-release --zip "<target>" [--rel <note>] [--skip …] [--include\|-i …] \| -r\|--repeat` | impacchetta sorgente git-clean + build + release note in uno zip versionato; `-r` ripete l'ultimo flow di packaging | file `.zip` |

Prima erano solo due comandi (`gitize` con `--split`/`--amend` annidati, `versionize` con
`--zip`/`--deploy`/`-r` annidati); sono stati separati perché ciascuna modalità è una chirurgia git o
un'orchestrazione di release a sé, non una variante del compito base. **Nessuna skill deploya o
pubblica nulla in produzione** — il perimetro di questo plugin si ferma allo zip; `--deploy` è stato
rimosso intenzionalmente (la skill `/deploy` a cui si appoggiava non esiste in questo marketplace).

## Note

- **`gitize` è sempre read-only** (git status/diff + scrittura clipboard, nessun commit).
- **`git-split-commits` e `git-amend-commits` committano** (il secondo riscrive anche commit
  unpushed via amend/autosquash) — entrambi gated da conferme e si rifiutano di partire se un repo
  è a metà merge/rebase/cherry-pick (nessun auto-fix: l'utente risolve a mano, poi ri-lancia).
- **`versionize` non builda mai**: legge le versioni dalle DLL già buildate (la più giovane) e i
  fatti git dai repo. Unica scrittura: il file di output.
- **`package-release` non builda mai** e non scrive il contenuto della release note (richiama
  `versionize -upd` quando serve rinfrescarla prima di impacchettare). Non deploya e non pubblica
  nulla — produce solo lo zip.
- **Consumo token ridotto**: `gitize` e `versionize` raccolgono i dati con uno script PowerShell
  bundled (`scripts/collect-changes.ps1`, `scripts/collect-release-facts.ps1`) che restituisce un
  output compatto in una sola chiamata, invece di decine di comandi git/DLL letti dal modello.
  `gitize` ha un budget sui diff (300 righe per file, 600 per repo, 1500 in totale; oltre, solo
  riepilogo a livello file, sempre dichiarato) e gira in un contesto separato (`context: fork`) con
  `model: haiku`: non vede la conversazione, quindi lo scope va passato come argomento (default: cwd).
  `versionize` usa `model: sonnet` e resta inline perché il gate di pre-flight deve poter chiedere
  all'utente; per `-new` legge `FeatureCatalog.md` + solo il delta git, mai il sorgente intero.
- I segreti non sono coinvolti. `git` / `Set-Clipboard` possono chiedere un permesso la prima volta.

## Installazione

```shell
/plugin install git-release@sistec-plugins
```
