---
name: git-split-commits
description: >-
  Partition a solution's STAGED git changes into several impact-grouped commits and commit them
  interactively, one confirmed segment at a time. Multi-repo aware (discovers the repo set fresh
  each run, same as gitize/versionize). Refuses to run (pre-flight check) if any repo is mid-merge
  or mid-rebase, rather than splitting on top of a half-finished operation. Use when the user wants
  the currently-staged changes
  organized/broken into separate, logically-grouped commits instead of one commit or one gitize
  message. For a single summarizing commit message instead, use `gitize`; to fold staged changes
  into EXISTING commits instead of creating new ones, use `git-amend-commits`. Usage: just ask
  (e.g. "split the staged changes into commits"), or use flags as shorthand: /git-split-commits
  [--scope|-s "<.sln, project file, or folder>"]
disable-model-invocation: true
---

The user invoked `/git-split-commits` to turn a solution's **staged** git changes into **several
commits, grouped by impact**, instead of one undifferentiated commit. Unlike `gitize`'s default
mode this **commits** (so it is *not* read-only), but every commit is gated behind an explicit
confirmation. **Scope = staged changes only:** unstaged and untracked changes are excluded and left
untouched throughout.

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
   single-pass scan, so discover fresh every run rather than caching it — no stale/out-of-sync
   state to carry between machines, e.g.
   `Get-ChildItem -LiteralPath "<root>" -Directory | Where-Object { Test-Path (Join-Path $_.FullName '.git') }`.

4. **Collect the STAGED changes — one pass, staged only.** Run `git -C "<repo>" status --short` for
   every repo in **one shell pass**; restrict the repo set to those whose status shows a **staged**
   entry (**X** column ≠ space — never run `git diff --staged` on a repo with no staged entry). For
   each such repo, collect its staged diff **exactly once**, reused throughout the run:
   - `git -C "<repo>" diff --staged --stat` for size before pulling hunks.
   - `git -C "<repo>" diff --staged --unified=0 -- . ':(exclude)**/obj/**' ':(exclude)**/bin/**' ':(exclude)**/*.Designer.cs' ':(exclude)**/*.min.*' ':(exclude)**/*-lock.json' ':(exclude)**/*.lock'`
     for the actual hunks (zero context, noise excluded).
   - **Hard budget:** a repo whose staged churn exceeds **~600 changed lines** (or a single file that
     dominates it) is summarized from `--stat`/name-status only, not read hunk-by-hunk — say so
     rather than truncating silently.
   If **nothing is staged anywhere**, report "nothing staged to split" and **stop** (no reset, no
   commit).

5. **Pre-flight: refuse to split any repo that's mid-operation.** Splitting the staged changes
   while a repo is mid-merge flattens the merge into ordinary commits and **destroys the
   two-parent merge link** — so check first, across the resolved repo set, for a `.git/MERGE_HEAD`,
   a `rebase-merge`/`rebase-apply` dir, or a `.git/CHERRY_PICK_HEAD` (mid-merge/rebase/cherry-pick).
   - **None found** → continue to Step 6.
   - **Any found** → **STOP and surface it; do not split.** Name the repo(s) and the in-progress
     operation, and tell the user to finish or abort it (`git merge --continue`/`--abort`, `git
     rebase --continue`/`--abort`, `git cherry-pick --continue`/`--abort`, as appropriate) before
     re-running `/git-split-commits`. This is a plain detect-and-refuse check — there is no
     automated way to safely finish someone else's half-done merge/rebase.

6. **Partition into logical commit groups, applying these rules in PRECEDENCE order**
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
   Conventional-Commits message (subject + body + `Repos:` footer, same shape as `gitize` Step 6).

7. **Present the plan and confirm (interaction 1).** Show the **ordered list** of proposed
   commits — each with its order index, message, and the repo(s)/files it covers — and **ask the
   user to confirm the list** before touching anything.

8. **On confirmation, commit SEGMENT BY SEGMENT.** The global partition (Step 6) runs **once**;
   from here each segment is processed in isolation so only the **current** segment's diff is ever in
   working context. A change request re-plans **only that segment** — never the whole batch — which is
   what keeps a long split run's usage bounded.
   - **a. Snapshot + unstage (once).** Record the current staged state **per file, not per repo** —
     one authoritative patch per staged file (`git -C "<repo>" diff --staged --binary -- "<file>"`
     for each staged file in each repo; keep these for the whole run). Snapshotting at file
     granularity means a segment's "slice" is just the subset of per-file patches for the files it
     covers — nothing to cut out of a combined diff. (The only case that still needs care: two
     segments splitting hunks **within the same file**. There, hand-edit that file's patch to keep
     only the relevant hunk(s) before applying it — everything else already separates cleanly by
     file.) Then unstage everything (`git -C "<repo>" reset`) so the index starts clean; the working
     tree (including pre-existing unstaged changes) is left untouched.
   - **b. For each segment, in order — and ONLY that segment:**
     - i. **Stage exactly that segment** into the index, isolated from working-tree/unstaged noise,
       by applying the per-file snapshot patches for the files this segment covers:
       `git -C "<repo>" apply --cached "<file.patch>"` for each (per involved repo for a cross-repo
       segment). Use `apply --cached` from the snapshot — **not** `git add <file>` — so only the
       originally staged hunks are committed even when a file also has unstaged edits or was
       partially staged.
     - ii. **Show the segment's commit message** and what is staged.
     - iii. **Ask confirmation.** On a change request, first **evaluate its impact on the other
       (uncommitted) segments** — does the edit break a precedence rule (Step 6), move a hunk that another
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
     completes so the original staged set can be recovered if the user aborts before further commits —
     to restore, re-apply each repo's kept snapshot with `git -C "<repo>" apply --cached "<snapshot.patch>"`.

Notes: **commits** (rewrites the index, not history) — gated by the Step-7 plan confirmation and
each Step-8 segment's own confirmation; never reset/commit without them. **Always** checks first
for a mid-merge/mid-rebase repo (Step 5) and refuses to split if it finds one — splitting a
mid-merge tree would flatten the merge and destroy its two-parent link. `git` (and
`reset`/`apply`/`commit` here) may prompt for permission the
first time — handle case-by-case, don't pre-add allow-rules. Repo-set discovery is cheap and shared
with `gitize`/`versionize`/`git-amend-commits` (all scan fresh, no cache).
