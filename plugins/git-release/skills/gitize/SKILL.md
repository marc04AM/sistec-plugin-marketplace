---
name: gitize
description: >-
  Summarize a solution's pending git changes into one Conventional-Commits message and copy it to
  the clipboard. Multi-repo aware (discovers the repo set fresh each run). Accepts a .sln, a
  project file, or a folder; defaults to the current working directory. Fully read-only on git —
  never stages or commits. Use when the user wants a ready-to-paste commit message for a
  solution's pending (multi-repo) changes. For organizing the STAGED changes into several fresh
  commits, use the sibling skill `git-split-commits`; for folding staged changes into existing
  unpushed commits, use `git-amend-commits`. Usage — just ask (e.g. "give me a commit message for
  this"), or use flags as shorthand: /gitize [--scope|-s "<.sln, project file, or folder>"]
disable-model-invocation: true
---

The user invoked `/gitize` to turn the **pending git changes of a solution** into a single,
ready-to-paste **Conventional-Commits** message on the **clipboard**. Many Sistec solutions are
**multi-repo workspaces** — the solution root is not a git repo; each subfolder is its own. So
gitize aggregates the diffs of **every changed sub-repo** into **one** message. This is read-only
on the repos (git status/diff) plus a clipboard write — **it never commits or stages anything**.
(If the user instead wants staged changes turned into separate commits, or folded into existing
ones, that's `git-split-commits` / `git-amend-commits` — this skill only ever summarizes.)

1. **Resolve the scope — natural language first.** Default to summarizing pending changes for
   whatever the user is pointing at or already discussing (the current working directory, or a
   solution/project/folder they name). `--scope` / `-s "<path>"` (also accepts the deprecated
   `-fn`/`--fn`, hidden from `-h` help) is an accepted **shorthand** for the same intent — handy for
   scripting or when precision matters — but none of this wording is required: path to a `.sln`
   file, a **project file** (`.csproj`/`.vbproj`/`.vcxproj`/`.fsproj`/…), **or** a folder (typically
   quoted; strip quotes). **Optional** — when omitted (or not otherwise implied by context), the
   target defaults to the **current working directory** (Step 2 walks up from it to the nearest
   `.sln`/repo). If a scope is **named but the path does not exist**, print the usage
   (`/gitize [--scope|-s "<.sln, project file, or folder>"]`) and **stop**. If no scope is
   **named**, do **not** stop — resolve the target from the current working directory in Step 2
   (only stop with usage there if no `.sln`/repo can be resolved from it).

2. **Resolve the target → root + stem.** When `--scope` is **omitted**, default the target to the
   **current working directory** — walk up from it to find the nearest `.sln` (solution target) or,
   failing that, the nearest enclosing git repo (single-repo target); if neither resolves, print
   usage and **stop**. Otherwise the explicit `--scope` path is the target. Either way it resolves
   to one of three shapes (this also picks the Step-3 discovery):
   - **`.sln` file** → root = its containing folder; `<stem>` = the `.sln` name without extension.
     **Solution target** → use the multi-repo discovery of Step 3.
   - **Folder** → if it contains exactly one `.sln`, treat as a solution root (`<stem>` from that
     `.sln`; if several, ask which) → **solution target** (Step 3). If it contains no `.sln`, treat
     it as a **single-repo target**: resolve its enclosing repo as below.
   - **Project file or any in-repo path** (no solution to scan) → **single-repo target**: resolve the
     one enclosing git repo with `git -C "<dir>" rev-parse --show-toplevel` and scope the whole run
     to **that single repo** (`<dir>` = the file's folder or the path itself). If the path is **not
     inside any git repo** (`rev-parse` fails), report that and stop with usage. `<stem>` = the project
     filename without extension (or the repo-folder leaf). **Skip Step 3's discovery** — the repo set
     is just this one repo. Note in the report that a single repo was targeted (and, when relevant,
     that the enclosing repo differs from / is nested beneath any parent solution root, e.g. a
     `Tests\<Proj>` repo not in the parent's immediate-subfolder set).

3. **Discover the git-repo set.**
   *(Solution targets only. For a **single-repo target** resolved in Step 2 the repo set is just that
   one enclosing repo — skip discovery here.)*
   - Test the root itself for a `.git`, then scan the **immediate subfolders** for a `.git`
     directory; collect every repo found. A cheap, single-pass scan, so discover fresh every run
     rather than caching it — no stale/out-of-sync state to carry between machines. Use a
     pipe-free discovery command, e.g.
     `Get-ChildItem -LiteralPath "<root>" -Directory | Where-Object { Test-Path (Join-Path $_.FullName '.git') }`.

4. **Collect the pending changes — lean by default.** Run `git -C "<repo>" status --short` for
   **every repo in one shell pass** (a single loop — *not* one call per repo) to find the changed
   ones and read each file's **XY** code. This mode always needs **both staged and unstaged**
   changes — a full picture of everything pending. For every repo with any change:
   - **a. Size first.** Run `git -C "<repo>" diff --stat` and `git -C "<repo>" diff --staged --stat`
     to see the file list + churn before pulling any hunks.
   - **b. Read hunks with zero context and noise excluded.** Pull the actual changes with
     `--unified=0` (no surrounding context lines — pure overhead for a commit summary) and a noise
     pathspec, e.g.
     `git -C "<repo>" diff --unified=0 -- . ':(exclude)**/obj/**' ':(exclude)**/bin/**' ':(exclude)**/*.Designer.cs' ':(exclude)**/*.min.*' ':(exclude)**/*-lock.json' ':(exclude)**/*.lock'`
     (and the same with `--staged`). Generated/lockfile churn never improves the message.
   - **c. Hard budget.** If a repo's total churn (from step a) exceeds **~600 changed lines**, do
     **not** read its hunks — summarize that repo from the `--stat` + name-status lines only. Apply
     the same fallback to any single file that dominates the diff.
   - **Never truncate silently** — whenever you fall back to file-level (step c) or an exclude hides
     real changes, say so in the report.

5. **Nothing changed anywhere** → report "nothing to commit (working trees clean)" and **stop**
   (do not touch the clipboard).

6. **Summarize → ONE Conventional-Commits message** spanning all changed repos:
   - **Subject** `type(scope): <imperative summary>` — pick the dominant `type`
     (`feat`/`fix`/`refactor`/`chore`/`docs`/`test`/…); `scope` = the dominant area, or omit it when
     the change spans many repos. Keep the subject ≤ ~72 chars.
   - **Body** = bullet lines **grouped by repo / area**, each describing what changed and why
     (read the diffs — summarize intent, not just filenames).
   - **Footer** listing the touched repos, e.g. `Repos: Sistec.Controls, Sistec.Core, Sistec.HMI`.

   Shape:
   ```
   type(scope): imperative summary

   - <repo/area>: what changed and why
   - <repo/area>: …

   Repos: <repo1>, <repo2>
   ```

7. **Copy to the clipboard** with a single PowerShell call — `$msg | Set-Clipboard` (build `$msg`
   from the text generated in step 6). Verify with `Get-Clipboard` if useful. If `Set-Clipboard` is
   unavailable (headless / no clipboard), don't fail — the message is still printed in full in Step 8;
   just note it couldn't be copied so the user copies it manually.

8. **Report** the full message in the chat, list which repos contributed, and confirm it is on the
   clipboard (the user pastes it into each changed repo's commit).

Notes: global command — it operates on the `--scope` solution; when `--scope` is **omitted** it
defaults to the **current working directory** (Step 2). This mode has **no approval gate** — it's
read-only git plus a non-destructive clipboard write; it never resets, commits, or amends anything.
`git` / `Set-Clipboard` may prompt for permission the first time — handle case-by-case, don't
pre-add allow-rules. Repo-set discovery is cheap and shared with `/versionize`, `git-split-commits`,
and `git-amend-commits` (all scan fresh, no cache).
