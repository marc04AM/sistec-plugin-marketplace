---
description: Register and track a problem as a named "issue" — a description plus an indexed plan of parts, each carrying a verification state (pending/confirmed/completed/rejected). Issue files live inside the target solution folder as <name>.issue.md. --new creates one (from a description, scoped to a solution/projects); --plan prints the indexed plan with each part's state; --pending prints only the not-yet-resolved parts with the result each awaits; --confirm records the awaited result for a part and flips its state; --add appends a new indexed part with the given description; --list lists every issue in the active project's solution (resolved from the project's ledger), grouped by the Claude project that owns each. Usage: /issue --new|-n "<name>" [--scope|-s "<folder-or-.sln>"] [-d|--desc "<text>"] | --plan|-p "<name>" | --pending|-pe "<name>" | --confirm|-c "<name>" <index> "<result>" | --add|-a "<name>" "<description>" | --list|-l [--scope|-s "<folder-or-.sln>"]
---

The user invoked `/issue` to **register a problem as a tracked issue** and follow its parts to
closure. An issue = a **description** (the problem, the involved classes, reference folders) + an
**indexed Plan** of parts, where each part has a **state** and a **result it awaits**. The issue is
a single Markdown file, `<name>.issue.md`, stored **inside the target solution folder** (the code it
concerns) so it travels with the source. This is the file-backed twin of plan-mode tracking: parts
are implemented, then verified, and `--confirm` records the evidence as it arrives. It pairs with
[[gitize-command]] / [[versionize-command]] (shares their repo-set discovery) and the project ledger
([[commands-anchor]], P2).

1. **Parse the arguments** (flags order-independent; strip surrounding quotes). Exactly one **verb**
   is required; every verb except `--list` also needs the issue **name**:
   - `--new` / `-n` `"<name>"` → **create** a new issue (Step 4). Honors `--scope` and `-d`/`--desc`.
   - `--plan` / `-p` `"<name>"` → **print the plan** (Step 5): the full indexed part list with states.
   - `--pending` / `-pe` `"<name>"` → **print pending** (Step 6): only non-terminal parts, **same
     indexes** as `--plan`, each with the result it awaits.
   - `--confirm` / `-c` `"<name>" <index> "<result>"` → **confirm** part #index (Step 7): record the
     awaited result that arrived and flip the part's state.
   - `--add` / `-a` `"<name>" "<description>"` → **add a part** (Step 8): append a new indexed part
     to the issue's Plan with the given description, state `pending`.
   - `--list` / `-l` → **list issues** (Step 9): print every `<name>.issue.md` in the active
     project's solution — the solution **resolved from the active project's ledger** — grouped by the
     **Claude project** that owns each issue. Takes **no name**; honors `--scope` to scope to a
     specific solution instead of the active project's.
   - `--scope` / `-s` `"<folder-or-.sln>"` (also accepts the deprecated `--fn`/`-f`, hidden from `-h` help) → the target solution (folder or `.sln`); scopes the issue and
     locates its file. If the folder has no `.sln`, the contained **project(s)** are the scope.
   - `--desc` / `-d` `"<text>"` → the issue description (problem, involved classes `file:line`,
     reference folders, useful info). Primarily for `--new`; on an existing issue it appends/expands.
   - If no verb, or a name-requiring verb with no name, print the Usage synopsis and **stop** (`--list`
     needs no name). `-h`/`--help` anywhere → P11 prints this command's parameters and does not execute
     (handled by the directive, not here).

2. **Resolve the target solution root** (reuse the [[gitize-command]] Step-2 logic):
   - `.sln` file → root = its containing folder; `<stem>` = the `.sln` name without extension.
   - Folder → if it contains exactly one `.sln`, that's the root (several → ask which); no `.sln` →
     the folder itself is the root and its project(s) are the scope.
   - For `--new`, `--scope` is the source of the root. For the other verbs, if `--scope` is omitted, locate the
     issue by searching for `<name>.issue.md` (Step 3).

3. **Locate the issue file.** `<root>\<name>.issue.md`. If `--scope` was given, look there. If omitted on a
   non-create verb, search the **active project** tree and the last-used target root for
   `<name>.issue.md`; if not found, say so and suggest `/issue -n "<name>" --scope "<folder>"`. On `--new`,
   if the file already exists, do **not** overwrite — report it and switch to `--plan` output instead.

4. **`--new` — create the issue.**
   - Resolve the root (Step 2) and, for a multi-repo solution, the **repo set** via the
     [[gitize-command]] Step-1 cache (`git-repos-<stem>` memory; discover + persist if absent).
   - **Investigate** enough to seed the plan: from `-d` and a light read of the named classes/folders,
     derive the **initial Plan** — one part per distinct task/claim/fix in the description, each with a
     concrete **Result awaited** (the evidence that will confirm it) and state `pending`.
   - Write `<root>\<name>.issue.md` in the **Issue file format** (below). **Approval gate:** present a
     recap (root, scope, the derived parts) via `AskUserQuestion` → `Proceed`/cancel before writing.
   - Append a creation entry to the active project's `*.log.md` ledger (P2).

5. **`--plan` — print the plan.** Read the issue file and print the full **Plan** as an indexed table:
   `# · Part · State · Result awaited · Result`. Lead with the header line (name, scope, repos) and a
   one-line state tally (e.g. `3 confirmed · 2 pending · 1 rejected`).

6. **`--pending` — print pending operations.** Print only parts whose state is **non-terminal**
   (`pending` / `in-progress` / `blocked`), **keeping the `--plan` indexes**. For each, show the
   **Result awaited** — the concrete evidence/result type that will let it be confirmed (e.g. "next
   prod `/trackTiming`: dialog count drops, dup-abort stays 0"). If none are pending, say so.

7. **`--confirm` — confirm a part.** `<index>` selects the part (the `--plan`/`--pending` index);
   `"<result>"` is the awaited result that arrived. Set that part's **Result** = the text + today's
   date, and flip its **State**: → `confirmed` when the result satisfies the awaited evidence (→
   `completed` if it also closes the part with no follow-up; → `rejected` if the result refutes it /
   the part is dropped — infer from the result wording, and say which you chose). Append a dated line
   to the issue's **Log**. Re-print the updated `--plan` table.

8. **`--add` — add a part.** Locate the issue file (Steps 2–3). Append a **new row** to the Plan at
   the **next free index** (never reuse or renumber existing ones, per the stable-index rule): `Part`
   = the given `"<description>"`, `State` = `pending`, `Result` = `—`. Derive a concrete **Result
   awaited** the same way `--new` does (the evidence that will let it be confirmed); if the
   description gives nothing to infer from, leave it `—`. Append a dated line to the issue's **Log**
   (`<YYYY-MM-DD> part <i> added: <description>`) and re-print the updated `--plan` table.

9. **`--list` — list the solution's issues, grouped by Claude project.**
   a. **Resolve the solution root.** If `--scope` is given, use it (Step 2). Otherwise resolve from
      the **active Claude project's ledger** (`<work-dir>\<active-proj>\<active-proj>.log.md`): read it
      to find the solution / subject the project's work targets (the `.sln` + root named in its
      entries) — the **ledger is authoritative** over the prompt's *Subject / solution paths*
      placeholder, which is often left unfilled. Resolve that to root + `.sln` via Step 2 (multi-repo →
      include its sub-repos).
   b. **Find issues.** Recursively find every `*.issue.md` under that root; compute each issue's state
      tally from its Plan table (e.g. `3 confirmed · 2 pending`), normalizing markup (strip `**`) and
      taking the first word of the State cell so legacy labels (`implemented`) still bucket.
   c. **Attribute each issue to a Claude project.** Scan the workspace project ledgers
      (`<work-dir>\*\*.log.md`) for a reference to each issue's **filename**; the project whose ledger
      **created / tracks** it owns it (prefer the ledger that records its creation; ignore the
      `commands` ledger's own command-documentation references). An issue no ledger references → group
      `(unattributed)`.
   d. **Group by Claude project.** One heading per owning Claude project (sorted by name), its issues
      beneath; for each issue print name, state tally, and its path relative to the root.
   e. Lead with a one-line total (`N issues across M projects in <root>`). If the root holds no issue
      files, say so. **Read-only** — `--list` writes nothing (no file, no ledger).

**Issue file format** (`<name>.issue.md`):
```markdown
# Issue: <name>
> Created <YYYY-MM-DD>. Scope: <.sln / project(s)> at <root>. Repos: [[git-repos-<stem>]].

## Description
<the problem; involved classes as file:line; reference folders/reports; useful info>

## Plan
| # | Part | State | Result awaited | Result |
|---|------|-------|----------------|--------|
| 1 | <title> | confirmed | <evidence type> | <recorded result — YYYY-MM-DD> |
| 2 | <title> | pending   | <evidence type> | — |

## Log
- <YYYY-MM-DD> created — N parts
- <YYYY-MM-DD> part <i> confirmed: <result>
```

**State model:** `pending` (implemented/proposed, awaiting evidence) · `in-progress` · `blocked` ·
`confirmed` (evidence received and validates the part) · `completed` (done, no further action) ·
`rejected` (dropped, or evidence refuted it). `pending`/`in-progress`/`blocked` are the **non-terminal**
states printed by `--pending`.

**Notes.** Read-only except the issue file (+ ledger / repo-set memory) — only `--new`, `--confirm`,
and `--add` write; `--plan`, `--pending`, and `--list` are read-only. Indexes are **stable**: never
renumber parts on confirm/add; append new parts at the next index.
Issue files live inside the **target solution folder** (a deliberate S1 single-root deviation chosen
for this command, so the issue travels with the code). Per P13, no Claude co-author trailer on any
commit that includes an issue file.
