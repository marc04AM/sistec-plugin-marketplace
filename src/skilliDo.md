---
description: Distill an armed /skillify recording into a finished, reusable slash-command. Reads commands\<name>\trace.md, generalizes the session's concrete values into the declared flags, keeps the ordered steps + decision rules (auto vs. ask) + approval gates + reused sub-commands, and writes the runnable .claude\commands\<name>.md + filled commands\<name>\<name>.prompt.md, then syncs the commands docs. Gated before writing. Inline in the recording session (holds the live context). Partner of /skillify (skill-ify records, skilli-Do produces). Usage: /skilliDo [<skill-name>]
---

The user invoked **`/skilliDo`** to **distill an armed `/skillify` recording into a finished
slash-command**. `/skillify` recorded the session into `commands\<name>\trace.md`; `/skilliDo`
**generalizes** that trace — the concrete run becomes a reusable command. It is the **producer**
half of the pair (skill-*ify* records → skilli-*Do* produces) and runs **inline in the recording
session**, which holds the live context (no new window, unlike `/command new`).

Constants:
- Work dir: `C:\Users\Sistec 23\source\repos\Claude`
- Runnable command files: `.claude\commands\<name>.md`  ·  Template: `commands\commands.prompt.md`
- Recording home: `commands\<name>\trace.md`  ·  Doc-sync routine: `.claude\commands\command.md` §3
- Ledger: `commands\commands.log.md`  ·  Memory anchor: `[[commands-anchor]]`

## 1. Resolve the recording
- `/skilliDo <name>` → use `commands\<name>\trace.md`.
- `/skilliDo` (no name) → find the **most-recent armed** trace (status `recording`, not yet
  `distilled`/`aborted`) under `commands\*\trace.md`. Several open → list them and ask which.
- No armed trace found → say so and stop (suggest `/skillify <name> …` to start one).
- `-h` / `--help` anywhere → **P11** prints this command's parameters and does not execute.

## 2. Distill the trace into a generalized procedure
Read the trace (Purpose, **Declared flags**, **Trace** steps, **Generalize-away**) and reconcile it
against what actually happened in the session. Produce the new command's design by **generalizing**:
- **Parameterize** — replace every concrete value (paths, solution/repo names, the specific
  feature) with the **declared flag** it maps to (use the Generalize-away list). The procedure must
  read for *any* inputs, not this one run.
- **Keep the procedure** — the ordered steps, in the order they were done.
- **Encode the interaction model** — turn the recorded branch-points into rules: what ran
  **automatically** (trivial / unambiguous) vs. what required **confirmation** (non-trivial →
  `AskUserQuestion`). Preserve every **approval gate** that guarded a mutation.
- **Reuse, don't reinvent** — if the session leaned on an existing command/cache (e.g. the
  `/gitize` repo-set cache, a doc-sync routine), reference it rather than duplicating it.
- **Fill the Purpose** if the trace left it `TBD`, from what the session accomplished.

## 3. Build the command files
a. **Runnable** `.claude\commands\<name>.md` — frontmatter `description:` = one-line purpose + a
   **Usage** synopsis built from the declared flags (`/<name> [-s …] [-d …] …`), then the
   instruction body: the parse/dispatch step, the generalized numbered steps, the interaction
   model, the approval gate(s), and a Notes/Verification close. Match the house style of the
   existing `.claude\commands\*.md` (see `/issue`, `/gitize`). Honor **P11** (don't implement
   `-h`/`--help`), and any workspace directives the procedure touches (P1/P13/P15/S-series).
b. **Spec** `commands\<name>\<name>.prompt.md` — fill the template at `commands\commands.prompt.md`
   (Name, Purpose, Trigger, Scope, Behavior/steps, Resources, Notes, Verification, Memory).

## 4. Approval gate (before writing the runnable)
`AskUserQuestion` recap: the `<name>`, the **Usage** synopsis, the distilled **steps + interaction
model**, and the **files to write** (`.claude\commands\<name>.md`, `commands\<name>\<name>.prompt.md`,
the doc-sync targets). `Proceed` / cancel. On cancel → write nothing, leave the trace armed.

## 5. Write + sync docs
On `Proceed`, write the two files, then run the **doc-sync routine** (`.claude\commands\command.md`
§3): add the inventory **row** + a `## /<name>` **section** in `commands\commands.log.md`, update
the **`commands-anchor`** memory inventory line, add the command's **`command.catalog.md`** entry
(workspace root — purpose + flag table + examples), and append a ledger entry to the active project's
`*.log.md` (P2). Finally mark the trace **distilled `<YYYY-MM-DD>`** in its header (keep it as
provenance). Report: *"Built `/<name>` — available next session."*

## Notes / constraints
- Writing `.claude\commands\<name>.md` is **agent-config self-modification** → the auto-mode
  classifier needs explicit per-file authorization (`[[cannot-self-edit-permissions]]`); expect a
  permission prompt and handle it per **P6** (don't pre-add an allow-rule).
- The distilled command may **itself** want a permission rule — per P6, hand the user the exact
  line to paste; prefer a design that needs none.
- Per **P13**, no Claude co-author trailer on anything authored here.
