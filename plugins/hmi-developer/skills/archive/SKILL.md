---
name: archive
description: Write a concise change summary of the current session's work to .claude/claude-archive/<date>-<slug>.md. Use when the user asks to archive, log, record, or summarize what was done this session, wants a session/change note captured as local history, or is wrapping up a chunk of work and wants it written down before moving on.
disable-model-invocation: false
---

Write a summary of the work done in this session to `.claude/claude-archive/<YYYY-MM-DD>-<slug>.md`
(create the `.claude/claude-archive/` folder if it doesn't exist). If the session produced no
substantive change, say so and skip writing rather than creating an empty note.

## Rules

- `<YYYY-MM-DD>` = today; `<slug>` = short kebab-case title of the change. If that filename already
  exists (another change the same day, same slug), add a numeric suffix (`-2`, `-3`) rather than
  overwriting.
- **One file per change** — never append to a single growing log.
- This folder is local history (gitignored, not synced by `sync.ps1`). Do not write secrets into it
  (passwords, tokens, connection strings) — it's plain local history, not a vault.
- Keep it concise and technical; include only the sections below that actually apply.

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
