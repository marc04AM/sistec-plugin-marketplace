# hmi-developer

Plugin del marketplace Sistec per lo sviluppo e la manutenzione della solution
**Sistec.HMI** (.NET 8 / C# 12 / WinForms). Porta la persona da *Senior .NET
Architect*, le regole di Clean Architecture / Clean Code del progetto, il ciclo
TDD e i comandi/hook di progetto.

## Componenti

| Componente | File | Cosa fa |
| :--------- | :--- | :------ |
| Skill | `skills/tdd/SKILL.md` | `/hmi-developer:tdd` — orchestra il ciclo Red→Green→Refactor in C# |
| Skill | `skills/csharp-doc-comments/SKILL.md` | Scrive, corregge e verifica commenti XML doc (`///`) e commenti inline C# secondo le convenzioni Microsoft/StyleCop (SA16xx, CS1591); su un progetto/solution/cartella, sul changed-set (diff vs HEAD), su punti specifici, o in automatico sul codice che modifichi |
| Skill | `skills/archive/SKILL.md` | `/hmi-developer:archive` — summary di change in `.claude/claude-archive/` |
| Skill | `skills/dpi-anchor-fix/SKILL.md` | Diagnosi + fix del bug .NET 8 WinForms "controllo anchored Top\|Bottom collassa a Height 0" (DPI-aware + AnchorLayoutV2 off): scanner deterministico → verdetto → config sicura sotto gate |
| Skill | `skills/translate/SKILL.md` | `/hmi-developer:translate` — da `MissingTranslations.csv` genera l'`INSERT` idempotente per `language_spv`: StringName esatta (incl. `#`), testi IT/EN dedotti dal call-site, placeholder preservati. Solo generazione del `.sql` (nessuna connessione DB). Invocazione esplicita (`disable-model-invocation: true`) |
| Skill | `skills/reconcile-solutions/SKILL.md` | `/hmi-developer:reconcile-solutions` — porta una feature da una solution SOURCE a una DEST (stessa famiglia su branch-milestone diversi): git merge/cherry-pick dove il repo è condiviso, port manuale semantico dove è divergente (ri-applica l'*intento*, non il diff). Pianifica, gate, `dotnet build`, edit unstaged. Invocazione esplicita (`disable-model-invocation: true`) |
| Hook | `hooks/hooks.json` + `*.py` | `build-reminder`, `graphify-nudge`, `archive-recall` |
| Asset | `assets/dpiRepair/resources/Repair-WinFormsDpiAnchor.ps1` | Scanner/fixer deterministico usato da `dpi-anchor-fix` (detect DPI/AnchorLayoutV2, applica la config, backup `.bak`) |

## Come funziona

Il plugin porta solo skill, hook e asset **riusabili tra progetti**. La persona
da *Senior .NET Architect*, il workflow agentico e le **regole C#/HMI** non
vivono più nel plugin: sono specifiche del progetto e vanno nel progetto stesso —
il vecchio *project brain* diventa il `CLAUDE.md` della solution e i file di
regola vanno copiati/adattati in `.claude/rules/` (architettura, async-threading,
business-logic, csharp-idioms, data-communication, ui-controls, tests, ecc.).
Le skill che dipendono dalle regole (`tdd`, `csharp-doc-comments`) le leggono da
`.claude/rules/*` del progetto attivo, non da `${CLAUDE_PLUGIN_ROOT}`.

I tre hook replicano il comportamento del workspace originale:
- **archive-recall** (SessionStart) — richiama la change history recente da `.claude/claude-archive/`.
- **graphify-nudge** (PreToolUse su Bash/Grep/Glob) — se esiste `graphify-out/`, suggerisce `graphify query` al posto del grep.
- **build-reminder** (PostToolUse su Edit/Write) — ricorda `dotnet build` dopo edit di file `.cs`.

> Gli hook richiedono **Python 3** nel PATH come `python`. Leggono `CLAUDE_PROJECT_DIR`,
> quindi operano sulla root del progetto in cui il plugin è attivo.

## Cosa NON è incluso (di proposito)

Gli strumenti di terze parti del workspace originale (caveman, OpenSpec, graphify,
claude-mem, karpathy-guidelines) si installano separatamente — vedi il README del
repository `Sistec.Claude.DeveloperHMI`. Questo plugin contiene solo ciò che è
specifico dello sviluppo Sistec.HMI.

## Test rapido

```bash
claude --plugin-dir ./plugins/hmi-developer
```

Poi in sessione:

```shell
/hmi-developer:tdd
document this
```
