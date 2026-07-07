a cosa serve? meta-tooling per gestire i propri slash-command. il modo nativo CC è creare .claude\commands\<name>.md a mano; per distillare skill c'è già skill-creator. qui invece spawner bespoke (seed-claude.cmd), ledger commands.log.md, commands-anchor, command.catalog.md, work-dir hardcoded/stale (Sistec 23), P4/P6 → non portabile, infra interna, fuori dal marketplace.

---
description: Manage workspace commands — /command new|edit <name> opens a new Claude window to build/edit it; /command delete <name> removes it from the console. Syncs the commands docs after each.
---

The user invoked **`/command <subcommand> <name>`** to manage the workspace's slash-commands
(the `commands` container project). `<subcommand>` is one of **`new`**, **`edit`**, **`delete`**.

Constants:
- Work dir: `C:\Users\Sistec 23\source\repos\Claude`
- Git Bash: `C:\Program Files\Git\git-bash.exe`  ·  Claude CLI: `~/.local/bin/claude.exe`
- Runnable command files: `.claude\commands\<name>.md`
- Per-command project files: `commands\<name>\<name>.prompt.md` (+ `commands\<name>\resources\`)
- Ledger: `commands\commands.log.md`  ·  Template: `commands\commands.prompt.md`
- Spawner (new/edit): `seed-claude.cmd` (work-dir root) → `commands\command\resources\seed-claude.sh`,
  reading the seed from `commands\command\resources\seed.txt`

## 1. Parse & validate
Read the subcommand and `<name>` from the invocation.
- If the subcommand is not `new`/`edit`/`delete`, or `<name>` is empty → print the usage
  (`/command new|edit|delete <name>`) and **stop**. If only `<name>` is missing, also list the
  existing commands (`Get-ChildItem .claude\commands\*.md`) to help, then stop.
- Existence check on `.claude\commands\<name>.md`:
  - `new` → must **not** exist (if it does, tell the user to use `edit`, stop).
  - `edit` / `delete` → must **exist** (if not: `new` suggests `/command new <name>`; `delete`
    says nothing to delete — stop).

## 2. Dispatch

### `new <name>` and `edit <name>` — open a new Claude window (interactive build/edit)
Briefly confirm, then spawn a detached Git Bash + Claude window in **two steps**:

1. **Write the seed** — put the matching seed text below (with `<name>` substituted) into
   `commands\command\resources\seed.txt` (overwrite, UTF-8). The seed is read from this file,
   so it may contain any characters (spaces, parentheses, slashes); it is **not** passed as an
   argument.
2. **Launch the spawner** — run the fixed launcher (PowerShell):
   ```powershell
   & 'C:\Users\Sistec 23\source\repos\Claude\seed-claude.cmd'
   ```
   `seed-claude.cmd` opens Git Bash at the work dir (cmd `start` pattern, pinned via `/D` +
   `--cd`) on `commands\command\resources\seed-claude.sh`, which `cat`s `seed.txt` and runs
   `MSYS_NO_PATHCONV=1 claude "<seed>"`, pausing on exit.
   **Do not** use PowerShell `Start-Process` on git-bash, nor git-bash `-c "..."` — neither opens
   a usable window (the window flashes and closes). Only cmd `start` on a script path works, and
   git-bash forwards no `-c`; the seed therefore travels via the file.

- **`new` seed:** `Work in the commands project (set it active). Create a new command named <name>: copy the template in commands/commands.prompt.md into commands/<name>/<name>.prompt.md, fill its Name and Purpose (ask me the purpose), then create the runnable .claude/commands/<name>.md. When done, sync the docs per the commands conventions (the per-command section plus inventory row in commands.log.md, the commands-anchor memory, and the command.catalog.md entry).`
- **`edit` seed:** `Work in the commands project (set it active). Edit the command named <name>: read commands/<name>/<name>.prompt.md and .claude/commands/<name>.md, ask me what to change, apply it, then sync the docs per the commands conventions.`

After launching, report: *"Opened a new Claude window to build/edit `/<name>` in the commands
project."* The **current** session does no building/editing and does **not** sync docs (the
spawned session syncs when its work completes).

### `delete <name>` — remove from the console (current session, lossless)
1. **Approval gate** — `AskUserQuestion` (`Proceed` / `Cancel`), noting it deletes the runnable
   `.claude\commands\<name>.md` so `/<name>` stops being available in new sessions, while the
   `commands\<name>\` knowledge is **kept**. On `Cancel` → stop.
2. On `Proceed`: delete `.claude\commands\<name>.md` (e.g. `Remove-Item -LiteralPath`). Before
   removing, if `commands\<name>\` holds anything not yet captured, distil it into the kept docs.
3. **Sync docs** (below), marking the command removed. Do **not** delete `commands\<name>\`.

## 3. Doc-sync routine (after delete here; after new/edit in the spawned session)
Update, in `commands\commands.log.md`:
- the **inventory table** in *"What's been done so far"* — add the row (new), or set Status to
  **`removed <YYYY-MM-DD>`** (delete);
- the **`## /<name>` section** — create it (new), append a dated sub-entry (edit), or add a
  `(removed <YYYY-MM-DD>)` note (delete).

Then ensure `commands\<name>\<name>.prompt.md` reflects the change (new/edit), update the
**`commands-anchor`** memory inventory line, and update **`command.catalog.md`** (workspace root) —
add/edit/remove the command's alphabetical entry (purpose + flag table + examples). No `_config\`
changes (project-specific, per P4).

> Note: writing `.claude\commands\*.md` is agent-config self-modification, and spawning the
> window may prompt for permission the first time — handle case by case (P6); don't pre-add an
> allow-rule.
