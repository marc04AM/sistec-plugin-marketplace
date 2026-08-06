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
- I segreti non sono coinvolti. `git` / `Set-Clipboard` possono chiedere un permesso la prima volta.

## Installazione

```shell
/plugin install git-release@sistec-plugins
```
