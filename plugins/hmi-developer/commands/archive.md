---
name: archive
description: Write a claude-archive change summary for the current session's work
disable-model-invocations: false
---

Write a summary of the work done in this session to `.claude/claude-archive/<YYYY-MM-DD>-<slug>.md`.

## Rules

- `<YYYY-MM-DD>` = today; `<slug>` = short kebab-case title of the change.
- **One file per change** — never append to a single growing log.
- This folder is local history (gitignored, not synced by `sync.ps1`); do not reference secrets (see Governance).
- Brutally concise per the project persona. Include only the sections that apply.

## Structure (Italian, matching existing entries)

```
# <YYYY-MM-DD> — <title>

## Cosa è stato fatto
<1–3 line summary of intent>

## Modifiche
### `<path>`
- <what changed and why>

## Non toccato (deliberato)
- <relevant things deliberately left alone, with reason>

## Verifiche
- <how it was tested / validated>
```
