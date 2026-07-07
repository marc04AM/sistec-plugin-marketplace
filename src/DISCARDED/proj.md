a cosa serve? il modo nativo di Claude Code è lanciare `claude` dentro ciascuna repository/cartella (da doc CC) — la cwd È il progetto, non serve un gestore di "progetto attivo". qui poi è tutto cablato sul framework privato (_config\templates, .prompt.md/.log.md, P3/P8, MEMORY.md, anchor [[…]], archiving S1 su D:\) con work-dir hardcoded e pure stale (Sistec 23). infra di sessione, non capacità → fuori dal marketplace.

---
description: Switch active project — /proj <name> switches, /proj -n creates+switches, /proj -d deletes (plan+approval), /proj alone opens the P3 picker
---

Parse the text after `/proj` and **dispatch** before anything else (trim whitespace):

- **Empty** → run **A. Picker** (the P3 startup selection).
- **First token is `-n` or `--new`** → run **B. Create + switch**, with `<name>` = the rest of
  the argument.
- **First token is `-d` or `--delete`** → run **D. Delete**, with `<name>` = the rest of the
  argument.
- **Anything else** → run **C. Switch**, with `<name>` = the whole argument.

An **empty `<name>` after `-n` or `-d`** is invalid — say so and fall back to the picker (A).

---

## A. No argument → P3 picker

Run the **P3 startup project selection** now, exactly as at session start.

The picker is a **single question** (one tab). Its options are the most-recent projects; the
built-in `Other` free-text field carries a mini-syntax for create/chat. There is **no second
tab** and **no separate Create/Chat options**.

1. **Enumerate.** Run this **single, pipe-free** command **exactly** (it matches the
   allow-rule `PowerShell(Get-ChildItem -LiteralPath 'C:\Users\Sistec 23\source\repos\Claude' -Directory*)`
   so it runs with **no permission prompt** — do not add pipes/`Sort-Object`/`Where-Object`,
   which would break the match and re-introduce the prompt):

   ```powershell
   Get-ChildItem -LiteralPath 'C:\Users\Sistec 23\source\repos\Claude' -Directory
   ```

   Then, **in your reasoning** (no extra shell commands): drop `_config`, `.claude`, `chat`;
   rank the remaining folders by `LastWriteTime` (newest first); take the top **4**
   (`AskUserQuestion` caps options at 4). Do **not** print the list — feed those 4 straight
   into the picker.

2. **Render one question `Project`.** Options = those (up to) 4 projects. Tell the user that
   the built-in **`Other`** field accepts:
   - **`/p <name>`** → create a new **project** named `<name>`.
   - **`/c <name>`** → create a new **chat** named `<name>`.
   - **anything else** → treated as `other` (no action; just echoed back).

3. **Parse the answer into a resolved choice (do not act yet).** Trim whitespace from
   `<name>`. Resolve to exactly one evidence line:
   - **A listed project** picked → `project <name> selected`.
   - **`Other` = `/p <name>`** → `new project <name>`.
   - **`Other` = `/c <name>`** → `new chat <name>`.
   - **`Other` = anything else** → `other: <raw text>`.

   For `/p` and `/c`, an **empty name** after the prefix is invalid — say so and re-open
   the picker (step 2); do not proceed.

4. **Recap & approval gate — ALWAYS, even when permission is already granted.** Show the
   resolved evidence line from step 3 and ask the user to approve via `AskUserQuestion`
   (options `Proceed` / `Pick again`). **Wait for the answer.**
   - **Proceed** → continue to step 5.
   - **Pick again** (or rejected) → re-open the picker (step 2); take no other action.

5. **Act on the approved choice:**
   - `project <name> selected` → set it active.
   - `new project <name>` → scaffold the canonical skeleton from `_config\templates\` per
     P3 step 3 (folders + `<project>.prompt.md` + seeded `<project>.log.md`); set active.
   - `new chat <name>` → start the free, non-project session under `chat\<name>\`.
   - `other: <raw text>` → take no action.

6. **Confirm the outcome** (the evidence line) before doing anything else.

---

## B. `/proj -n <name>` → create + switch

Acts **immediately** — the `-n` flag is explicit intent, so there is **no approval gate**.

1. Trim `<name>`. If empty → invalid; say so and fall back to **A. Picker**.
2. Enumerate project folders with the same allow-listed, pipe-free command from A.1. If a
   folder named `<name>` **already exists** → it isn't new: switch to it (run **C** from step 2)
   and note that it already existed.
3. Otherwise **scaffold** the canonical skeleton from `_config\templates\` per P3 step 3
   (folders + `<project>.prompt.md` + seeded `<project>.log.md`); set it active.
4. **Confirm:** `new project <name> created and selected`.

---

## C. `/proj <name>` → switch to existing

Acts **immediately** — naming the project IS the confirmation, so there is **no approval gate**.

1. **Enumerate.** Run the same **single, pipe-free** command from A.1 (so there's **no
   permission prompt**):

   ```powershell
   Get-ChildItem -LiteralPath 'C:\Users\Sistec 23\source\repos\Claude' -Directory
   ```

   Drop `_config`, `.claude`, `chat`. Resolve `<name>` against the remaining folders by
   **case-insensitive exact match** (in your reasoning; do not print the list).
2. **Found** → set it active. **Confirm:** `project <name> selected`.
3. **Not found** → report that no project named `<name>` exists, list the closest folder
   names, and offer **`/proj -n <name>`** to create it or **`/proj`** to open the picker.
   Take no other action.

---

## D. `/proj -d <name>` → delete (plan → options → approval → execute)

A **destructive** path — so unlike B/C it **never** acts on the bare argument. It plans first,
offers the applicable options, and requires a **final yes/no confirmation for EVERY option**
before touching anything.

1. **Validate & resolve.** Trim `<name>`. If empty → invalid; say so and fall back to **A.
   Picker**. Enumerate project folders with the same pipe-free command from A.1, drop
   `_config` / `.claude` / `chat`, resolve `<name>` by **case-insensitive exact match** (in
   your reasoning; do not print the list).
   - **Not found** → report no project named `<name>` exists, list the closest folder names,
     offer **`/proj`** to open the picker. Take no other action.

2. **Inspect & build the plan — no changes yet.** Gather everything the deletion would touch:
   - **Artifacts** — the project folder tree at `<work-dir>\<name>\` (prompt, log, plan,
     `reports\` / `specifications\` / `scripts\` / `external resources\`, `resources\`, …).
   - **Memory footprint** — the project's **anchor** memory file, its **MEMORY.md** index
     entry, and every **theme** memory that links to it via `[[…]]` (cross-cutting memories
     owned by no single project: they must **survive**; only the back-link is affected).
   - **Archive state** — whether the project is already archived (its MEMORY.md entry is
     tagged `[archived → D:\…]`); if so there is nothing left to archive.
   - **Active?** — whether `<name>` is the **active project** this session.

3. **Present the plan — operations + consequences per option.** For each *applicable* option,
   list the exact operations it runs and what is kept / lost:
   - **Delete but keep memory** — remove the project folder (artifacts) from the work dir;
     **keep** the anchor + theme memories + MEMORY.md entry **live** (retag the entry, e.g.
     `[deleted — memory kept]`). *Consequence:* knowledge stays recallable; artifacts gone with
     no D:\ copy.
   - **Archive then delete** *(omit if already archived)* — move the artifacts to `D:\<name>`
     (S1 archiving), retag the MEMORY.md entry `[archived → D:\<name>]`, keep anchor + themes
     live, then remove the now-relocated folder from the work dir. *Consequence:* artifacts
     recoverable from D:\; memory live.
   - **Delete files and memory** — first **distil** any irreplaceable nuggets into memory per
     S1 (lossless deletion); then remove the project folder **and** delete the anchor memory
     file, remove its MEMORY.md entry, and **delink** `[[…]]` from every theme memory (the
     theme memories themselves survive). *Consequence:* full purge — nothing recoverable.

4. **Offer the options** via `AskUserQuestion` — only the **applicable** options from step 3
   (e.g. omit *Archive then delete* when the project is already archived) **plus Cancel**.
   Cancel → take no action.

5. **Final confirmation — ALWAYS, for every option.** After the pick, show a recap of the exact
   operations the chosen option will perform and ask a **second** `AskUserQuestion` (`Proceed` /
   `Cancel`). **Wait for the answer.** Anything but `Proceed` → take no action.

6. **Execute the approved plan** exactly as recapped (artifacts, then memory).

7. **Confirm the outcome** — report what was removed / archived / kept. If `<name>` was the
   **active project**, note that there is now **no active project** set and do **not** auto-open
   the picker (run `/proj` when ready). *(Deliberate divergence from P8, which re-opens the
   picker after archiving the active project — the `-d` path just reports.)*
