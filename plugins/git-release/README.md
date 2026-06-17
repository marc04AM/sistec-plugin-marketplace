# git-release

Strumenti di rilascio per le solution **multi-repo** Sistec (la radice della solution non è un repo
git; ogni sottocartella lo è). I due comandi condividono la cache del set di repo in memoria
(`git-repos-<stem>`), così la scoperta del layout della solution avviene una volta sola.

## Comandi

| Comando | Cosa fa | Scrive |
| :------ | :------ | :----- |
| `/gitize -fn "<.sln, project file, o cartella>" [--split]` | aggrega i diff di tutti i sub-repo cambiati in **un** messaggio Conventional-Commits sulla clipboard; con `--split` spezza lo staged in commit raggruppati per impatto e li committa interattivamente | clipboard (o commit in `--split`) |
| `/versionize -new\|-upd\|--zip "<target>" [--out <path>] [--rel <note>] [--skip …]` | release note `ReleaseNote.md` (4 sezioni: Versions, Cell AB, Cell C, Libraries) da DLL già buildate + git; `-upd` antepone un changelog; `--zip` impacchetta sorgente git-clean + build | file `.md` / `.zip` |

## Note

- **`/gitize` default è read-only** (git status/diff + scrittura clipboard, nessun commit). Solo
  `--split` committa, ed è gated da conferme per-commit.
- **`/versionize` non builda mai**: legge le versioni dalle DLL già buildate (la più giovane) e i
  fatti git dai repo. Unica scrittura: il file di output (o lo zip).
- I segreti non sono coinvolti. `git` / `Set-Clipboard` possono chiedere un permesso la prima volta.

## Installazione

```shell
/plugin install git-release@sistec-plugins
```
