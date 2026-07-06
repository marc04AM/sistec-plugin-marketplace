---
name: gitize
description: Summarize the pending git changes of a solution into one Conventional-Commits message and copy it to the clipboard. Multi-repo aware (caches the repo set in memory). Accepts a .sln, a project file, or a folder. With --split, instead splits the STAGED changes into several impact-grouped commits and interactively stages+commits them. Usage /git-release:gitize -fn "<path to .sln, project file, or folder>" [--split]
---

The user invoked `/git-release:gitize` to turn the **pending git changes of a solution** into a single,
ready-to-paste **Conventional-Commits** message on the **clipboard**. Many Sistec solutions are
**multi-repo workspaces** — the solution root is not a git repo; each subfolder is its own. So
gitize aggregates the diffs of **every changed sub-repo** into **one** message. This is read-only
on the repos (git status/diff) plus a clipboard write — **it never commits or stages anything**
(except in `--split` mode, which is gated per-commit).

1. **Parse the arguments** (flags order-independent):
   - `-fn` (also accept `--fn`) → path to a `.sln` file, a **project file**
     (`.csproj`/`.vbproj`/`.vcxproj`/`.fsproj`/…), **or** a folder (typically quoted; strip quotes).
   - `--split` → opt into **split mode** (Step 9): partition the **staged** changes into several
     impact-grouped commits and interactively stage+commit them. Default (no `--split`) is the
     read-only single-message + clipboard behaviour of steps 6–8.
   - If `-fn` is missing, or the path does not exist, print the usage
     (`/git-release:gitize -fn "<.sln, project file, or folder>" [--split]`) and **stop**.

2. **Resolve the target → root + stem.** Three target shapes (this also picks the Step-3 mode):
   - **`.sln` file** → root = its containing folder; `<stem>` = the `.sln` name without extension.
     **Solution target** → use the multi-repo discovery/cache of Step 3.
   - **Folder** → if it contains exactly one `.sln`, treat as a solution root (`<stem>` from that
     `.sln`; if several, ask which) → **solution target** (Step 3). If it contains no `.sln`, treat
     it as a **single-repo target**: resolve its enclosing repo as below.
   - **Project file or any in-repo path** (no solution to scan) → **single-repo target**: resolve the
     one enclosing git repo with `git -C "<dir>" rev-parse --show-toplevel` and scope the whole run
     to **that single repo** (`<dir>` = the file's folder or the path itself). `<stem>` = the project
     filename without extension (or the repo-folder leaf). **Skip Step 3's recall/discover/persist**
     — the repo set is just this one repo. Note in the report that a single repo was targeted (and,
     when relevant, that the enclosing repo differs from / is nested beneath any parent solution root,
     e.g. a `Tests\<Proj>` repo not in the parent's immediate-subfolder set).

3. **Step 1 — get the git-repo set from memory; discover + persist if absent.**
   *(Solution targets only. For a **single-repo target** resolved in Step 2 the repo set is just that
   one enclosing repo — skip the recall/discover/persist here.)*
   - **Recall** a memory slugged `git-repos-<solution-stem>` (its `description:` names the solution).
     If present, use its repo list as the candidate set.
   - **If absent**, **discover**: test the root itself for a `.git`, then scan the **immediate
     subfolders** for a `.git` directory; collect every repo found. Then **record** the result in
     memory under `git-repos-<solution-stem>` (the solution path + the repo list) so the next run is
     a cache-hit. Use a pipe-free discovery command, e.g.
     `Get-ChildItem -LiteralPath "<root>" -Directory | Where-Object { Test-Path (Join-Path $_.FullName '.git') }`.

4. **Collect the pending changes — lean by default.** For each repo in the set run
   `git -C "<repo>" status --short` to find the **changed** ones. For every changed repo:
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

   **→ If `--split` was given, skip steps 6–8 and go to Step 9 (split mode).** Steps 6–8 below are
   the **default** mode (one message → clipboard, fully read-only).

6. **Summarize → ONE Conventional-Commits message** spanning all changed repos:
   - **Subject** `type(scope): <imperative summary>` — pick the dominant `type`
     (`feat`/`fix`/`refactor`/`chore`/`docs`/`test`/…); `scope` = the dominant area, or omit it when
     the change spans many repos. Keep the subject ≤ ~72 chars.
   - **Body** = bullet lines **grouped by repo / area**, each describing what changed and why
     (read the diffs — summarize intent, not just filenames).
   - **Footer** listing the touched repos, e.g. `Repos: Sistec.Controls, Sistec.Core, Sistec.HMI`.

7. **Copy to the clipboard** with a single PowerShell call — `$msg | Set-Clipboard` (build `$msg`
   from the text generated in step 6). Verify with `Get-Clipboard` if useful.

8. **Report** the full message in the chat, list which repos contributed, and confirm it is on the
   clipboard (the user pastes it into each changed repo's commit).

9. **`--split` mode — split the STAGED changes into several impact-grouped commits, then stage +
   commit them interactively.** Unlike the default mode this **commits** (so it is *not* read-only),
   but every commit is gated behind an explicit confirmation. **Scope = staged changes only:**
   unstaged and untracked changes are excluded and left untouched throughout. No clipboard write.

   9.1. **Collect the staged changes.** For each repo run `git -C "<repo>" diff --staged` (use
   `--stat` / name-status as a fallback for very large diffs — say so). If **nothing is staged
   anywhere**, report "nothing staged to split" and **stop** (no reset, no commit).

   9.2. **Partition into logical commit groups, applying these rules in PRECEDENCE order**
   (higher overrides lower):

   1. **(highest) Self-dependent changes stay in one logical commit — even across repositories.**
      Changes that depend on each other to compile/work (a new API + its callers, a rename + its
      references, an interface + its implementors) are never split apart. This is the **only** rule
      that may group **multiple repos** together. Since git cannot make one commit span repos, a
      cross-repo group becomes **one commit per involved repo sharing the same message**, committed
      back-to-back as a coordinated set.
   2. **Removed-`using` changes are grouped — strictly one commit per repo.** Changes that are (or
      are dominated by) removed `using` directives are kept together but **never merged across repo
      boundaries**. Subordinate to rule 1: a using-removal that is part of a self-dependent set
      follows rule 1 instead.
   3. **(fallback) Topic-related changes go in one commit (per repo).** Remaining changes addressing
      the same topic/feature/area are grouped together.

   Order the resulting commits so prerequisites land first (self-dependent/foundational changes
   before their dependents; within a repo, prerequisite before consumer). Give each group its own
   Conventional-Commits message (subject + body + `Repos:` footer).

   9.3. **Present the plan and confirm (interaction 1).** Show the **ordered list** of proposed
   commits — each with its order index, message, and the repo(s)/files it covers — and **ask the
   user to confirm the list** before touching anything.

   9.4. **On confirmation, commit SEGMENT BY SEGMENT.** The global partition (9.2) runs **once**;
   from here each segment is processed in isolation so only the **current** segment's diff is ever in
   working context. A change request re-plans **only that segment** — never the whole batch — which is
   what keeps a long split run's usage bounded.
   - **a. Snapshot + unstage (once).** Record the current staged state per repo as authoritative
     patches (`git -C "<repo>" diff --staged --binary` → snapshot patches kept for the whole run).
     Then unstage everything (`git -C "<repo>" reset`) so the index starts clean; the working tree
     (including pre-existing unstaged changes) is left untouched.
   - **b. For each segment, in order — and ONLY that segment:**
     - i. **Stage exactly that segment** into the index, isolated from working-tree/unstaged noise, by
       applying the segment's slice of the snapshot patch:
       `git -C "<repo>" apply --cached "<segment.patch>"` (per involved repo for a cross-repo segment).
       Use `apply --cached` from the snapshot — **not** `git add <file>` — so only the originally
       staged hunks are committed even when a file also has unstaged edits or was partially staged.
     - ii. **Show the segment's commit message** and what is staged.
     - iii. **Ask confirmation.** On a change request, first **evaluate its impact on the other
       (uncommitted) segments** — does the edit break a precedence rule (9.2), move a hunk that another
       segment depends on, or change ordering? From that, **define the minimum replanning-perimeter**:
       the smallest set of uncommitted segments the change actually touches (often just THIS one).
       Then **re-plan only within that perimeter** — reword, split into sub-commits, drop hunks, or
       reshuffle hunks among the perimeter's segments — using only those segments' slices of the
       snapshot. Discard the affected segments from the index (`git -C "<repo>" reset` for each) and
       redo i–iii for them in order. Do **not** re-partition or re-read segments outside the perimeter.
       Already-committed segments stand (if a change would require reopening one, say so and stop rather
       than rewriting history).
     - iv. If accepted → **commit**: `git -C "<repo>" commit -m "<message>"` in each involved repo,
       then advance to the next segment.
   - **c. Done.** Report the commits made (per repo, with short hashes + subjects) and confirm the
     working tree's remaining unstaged changes are untouched. Keep the snapshot patches until the run
     completes so the original staged set can be re-staged if the user aborts before further commits.

Notes: global command — it operates on the `-fn` solution, independent of any working folder.
**Default mode** (no `--split`) has no approval gate (read-only git + a non-destructive clipboard
write). **`--split` mode commits** and is therefore gated by the explicit per-commit confirmations in
Step 9 (the user OKs the plan, then each commit); never reset/commit without them. `git` /
`Set-Clipboard` (and `git reset`/`apply`/`commit` in split mode) may prompt for permission the first
time — handle case-by-case, don't pre-add allow-rules. The repo-set memory keeps the solution's
layout discoverable for later runs (and for sibling commands like `/git-release:versionize`).
