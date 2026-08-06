---
name: git-amend-commits
description: >-
  Fold a solution's STAGED git changes into the existing unpushed commits they belong to
  (amend/fixup+autosquash); plan a fresh commit for anything independent. Multi-repo aware
  (discovers the repo set fresh each run, same as gitize/versionize). Refuses to run (pre-flight
  check) if any repo is mid-merge or mid-rebase. Never touches a pushed commit — a change whose only
  plausible target is already pushed is forced to a new commit instead of rewriting published
  history. Use when the user wants staged changes "folded into", "squashed into", or "added to" an
  existing commit rather than committed separately. For a single summarizing commit message
  instead, use `gitize`; to split staged changes into several FRESH commits instead of amending,
  use `git-split-commits`. Usage: just ask (e.g. "fold this into the existing commit"), or use
  flags as shorthand: /git-amend-commits [--scope|-s "<.sln, project file, or folder>"]
disable-model-invocation: true
---

The user invoked `/git-amend-commits` to fold a solution's **staged** git changes into the
**existing unpushed commits** they're a continuation of, rather than creating a separate commit for
them. Like `git-split-commits` this **commits** (and here also **rewrites** unpushed history via
amend/autosquash), so it is *not* read-only and every action is gated behind explicit confirmation.
**Scope = staged changes only:** unstaged and untracked changes are excluded and left untouched
throughout.

1. **Resolve the scope — natural language first.** Default to the current working directory, or a
   solution/project/folder the user names. `--scope` / `-s "<path>"` is an accepted **shorthand** —
   a `.sln` file, a **project file**, or a folder (strip quotes). If a scope is **named but the path
   does not exist**, print the usage and **stop**. If no scope is named, resolve from the current
   working directory in Step 2 instead of stopping here.

2. **Resolve the target → root + stem** (same shapes as `gitize`):
   - **`.sln` file** (or a **folder** with exactly one `.sln`) → **solution target**: root = its
     folder, `<stem>` = the `.sln` name → repo set via Step 3.
   - **Project file / any in-repo path** → **single-repo target**: resolve the one enclosing repo
     with `git -C "<dir>" rev-parse --show-toplevel`; repo set = just that repo; skip Step 3.
   If neither resolves (no `.sln`/repo found), print usage and **stop**.

3. **Discover the git-repo set** *(solution targets only)* — scan the root itself for a `.git`,
   then its immediate subfolders for a `.git` directory; collect every repo found. A cheap,
   single-pass scan, so discover fresh every run rather than caching it, e.g.
   `Get-ChildItem -LiteralPath "<root>" -Directory | Where-Object { Test-Path (Join-Path $_.FullName '.git') }`.

4. **Collect the STAGED changes — one pass, staged only.** Run `git -C "<repo>" status --short` for
   every repo in **one shell pass**; restrict the repo set to those whose status shows a **staged**
   entry (**X** column ≠ space). For each such repo, collect its staged diff **exactly once**:
   `git -C "<repo>" diff --staged --stat` for size, then
   `git -C "<repo>" diff --staged --unified=0 -- . ':(exclude)**/obj/**' ':(exclude)**/bin/**' ':(exclude)**/*.Designer.cs' ':(exclude)**/*.min.*' ':(exclude)**/*-lock.json' ':(exclude)**/*.lock'`
   for the hunks (zero context, noise excluded). A repo whose staged churn exceeds **~600 changed
   lines** is summarized from `--stat`/name-status only — say so rather than truncating silently. If
   **nothing is staged anywhere**, report "nothing staged to amend" and **stop** (no reset, no
   commit, no amend).

5. **Pre-flight: refuse to amend in any repo that's mid-operation.** Amending/rebasing while a
   repo is mid-merge or mid-rebase would compound an already half-finished operation — so check
   first, across the resolved repo set, for a `.git/MERGE_HEAD`, a `rebase-merge`/`rebase-apply`
   dir, or a `.git/CHERRY_PICK_HEAD`.
   - **None found** → continue to Step 6.
   - **Any found** → **STOP and surface it; do not amend.** Name the repo(s) and the in-progress
     operation, and tell the user to finish or abort it (`git merge --continue`/`--abort`, `git
     rebase --continue`/`--abort`, `git cherry-pick --continue`/`--abort`) before re-running
     `/git-amend-commits`.

6. **Enumerate the amend candidates — the UNPUSHED commits only.** For each repo with staged
   changes, list the local commits not yet on the upstream:
   `git -C "<repo>" log --oneline @{u}..HEAD` (when an upstream is set). If there is **no upstream**,
   fall back to the commits on the current branch since it diverged from its base, and **say so** in
   the plan (the base is a heuristic). **Never offer a pushed commit as an amend target** — amending
   it would rewrite published history; such a change is forced to a **new commit** instead (Step 7),
   and the report notes why.

7. **Assign each staged hunk to a target, applying these rules in PRECEDENCE order** (higher
   overrides lower):

   1. **(highest) Consistent follow-up → amend that commit.** A staged change that is a
      continuation/fix/completion of an existing **unpushed** commit (touches the same symbols,
      files, or topic that commit introduced) is assigned to **amend** that commit.
   2. **Independent or inconsistent → new commit.** A staged change that belongs to no existing
      commit, or that would contradict one (a different topic, a reversal, an unrelated area), is
      **not** folded in — it is planned as a **new commit** (summarized per `gitize`'s
      Conventional-Commits shape). When several such changes are independent of the existing commits
      but related to each other, group them using `git-split-commits`'s three precedence rules
      (self-dependent-across-repos > removed-`using`-per-repo > topic) instead of leaving each as its
      own commit.
   3. **Ambiguous → ask, defaulting to a new commit.** If a change could plausibly belong to more
      than one commit, surface it in the plan and let the user decide; absent a decision, prefer a
      **new commit** (safer than amending the wrong one).

   When multiple staged hunks target the **same** existing commit, they fold into a single amend of
   that commit. Order the work so amends of older commits and their dependents stay consistent.

   **Cross-repo coordination.** When a staged change is part of one logical unit that spans several
   repos (rule 1's cross-repo case), and the matching commit for that unit **already exists and is
   unpushed** in some repos while it's only **staged** in others: don't create a fresh standalone
   commit everywhere. **Amend** the existing commit where it exists; **create** a new commit
   (sharing the same Conventional-Commits message) where it doesn't, committed back-to-back with the
   amends as one coordinated set. If a target repo's matching commit is already **pushed**, it
   cannot join the set — create a new coordinating commit there instead and **note the divergence**
   in the plan.

8. **Present the plan and confirm (interaction 1).** Show, per repo: each **amend** (target
   commit `<short-sha> <subject>` + the staged files/hunks folded into it, and whether its message
   is kept or reworded) and each **new commit** (message + files). Flag any change that was forced
   to a new commit because its only plausible target is already **pushed**. **Ask the user to
   confirm** before touching anything.

9. **On confirmation, execute per repo — snapshot first, then amends, then new commits.**
   - **a. Snapshot + unstage (once).** Capture each repo's staged state as authoritative binary
     patches (`git -C "<repo>" diff --staged --binary`), then `git -C "<repo>" reset` so the index is
     clean and the working tree is untouched. Keep the patches for the whole run (recovery if
     aborted).
   - **b. Amends.** For each target commit (process the **nearest to HEAD last** so earlier rebases
     don't invalidate later shas):
     - i. Stage **only** that target's slice of the snapshot patch with
       `git -C "<repo>" apply --cached "<slice.patch>"` (never `git add <file>` — keeps unstaged
       edits out).
     - ii. **If the target is HEAD** → `git -C "<repo>" commit --amend --no-edit` (or `-m
       "<reworded>"` when Step 8 reworded it). **If the target is an older unpushed commit** →
       create a fixup with `git -C "<repo>" commit --fixup=<sha>` and autosquash it
       non-interactively: `GIT_SEQUENCE_EDITOR=true git -C "<repo>" rebase --autosquash <sha>~1`
       (the `true` sequence editor accepts the generated todo without prompting). On a rebase
       conflict, **stop and report** (do not force-resolve); the snapshot lets the user recover.
   - **c. New commits.** Stage and commit each planned new commit the same way (`apply --cached` the
     slice, show what's staged, `git -C "<repo>" commit -m "<message>"`).
   - **d. Done.** Report per repo: which commits were amended (old → new short-sha + subject) and
     which were newly created, and confirm the remaining unstaged/untracked changes are untouched.

Notes: **commits and rewrites unpushed history** — gated by the Step-8 plan confirmation; never
reset/commit/amend without it. **Always** checks first for a mid-merge/mid-rebase repo (Step 5)
and refuses to amend if it finds one. Only ever
touches **unpushed** commits — a change whose only target is pushed is forced to a new commit,
never a history rewrite. `git` (and `reset`/`apply`/`commit`/`commit --amend`/`rebase --autosquash`
here) may prompt for permission the first time — handle case-by-case, don't pre-add allow-rules.
Repo-set discovery is cheap and shared with `gitize`/`versionize`/`git-split-commits` (all scan
fresh, no cache).
