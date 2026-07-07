---
name: gitize
description: Summarize the pending git changes of a solution into one Conventional-Commits message and copy it to the clipboard. Multi-repo aware (caches the repo set in memory). Accepts a .sln, a project file, or a folder. With --split, instead splits the STAGED changes into several impact-grouped commits and interactively stages+commits them — a /gitAlign pre-flight runs first to clear any in-progress merge/rebase before splitting (splitting mid-merge would destroy the merge link). With --amend (-a), folds the STAGED changes into the existing (unpushed) commits they belong to, planning a new commit for anything independent/inconsistent; --amend --split amends the matching commits and creates coordinating commits in the other repos for a cross-repo set (also gitAlign-pre-flighted). If --scope is omitted, defaults to the active project's solution (resolved from its ledger). Usage: /gitize [--scope|-s "<path to .sln, project file, or folder>"] [--split] [--amend|-a]
---

The user invoked `/gitize` to turn the **pending git changes of a solution** into a single,
ready-to-paste **Conventional-Commits** message on the **clipboard**. Many Sistec solutions are
**multi-repo workspaces** — the solution root is not a git repo; each subfolder is its own. So
gitize aggregates the diffs of **every changed sub-repo** into **one** message. This is read-only
on the repos (git status/diff) plus a clipboard write — **it never commits or stages anything**.

1. **Parse the arguments** (flags order-independent):
   - `--scope` / `-s "<path>"` (also accepts the deprecated `-fn`/`--fn`, hidden from `-h` help) → path to a `.sln` file, a **project file**
     (`.csproj`/`.vbproj`/`.vcxproj`/`.fsproj`/…), **or** a folder (typically quoted; strip quotes).
     **Optional** — when omitted, the target defaults to the **active project's solution** (Step 2
     resolves it from the active project's ledger).
   - `--split` → opt into **split mode** (Step 9): partition the **staged** changes into several
     impact-grouped commits and interactively stage+commit them. Default (no `--split`) is the
     read-only single-message + clipboard behaviour of steps 6–8. **Whenever `--split` is present
     (alone or with `--amend`), a `/gitAlign` pre-flight runs first** (Step 5 mode-routing) to clear
     any in-progress merge/rebase before splitting.
   - `--amend` (also accept `-a`) → opt into **amend mode** (Step 10): fold the **staged** changes
     into the existing **unpushed** commits they belong to (amend), planning a new commit for any
     change that is independent of — or inconsistent with — every existing commit. Combine with
     `--split` for the cross-repo coordinated case (Step 10.6).
   - If `--scope` is **given but the path does not exist**, print the usage
     (`/gitize [--scope|-s "<.sln, project file, or folder>"] [--split] [--amend|-a]`) and **stop**. If `--scope`
     is **omitted**, do **not** stop — resolve the active project's solution in Step 2 (only stop with
     usage there if no active-project solution can be resolved).

2. **Resolve the target → root + stem.** When `--scope` is **omitted**, first resolve the target from the
   **active Claude project's ledger** (`<work-dir>\<active-proj>\<active-proj>.log.md`) — read it to
   find the `.sln` + root the project's work targets (the ledger is authoritative; mirrors `/issue`
   Step 8a). If no active project is set or its ledger names no solution, print usage and **stop**.
   Otherwise the explicit `--scope` path is the target. Either way it resolves to one of three shapes
   (this also picks the Step-3 mode):
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
     subfolders** for a `.git` directory; collect every repo found. Then **persist** the result as
     a new memory file `git-repos-<solution-stem>.md` (`type: reference`, body = the solution path +
     the repo list, linked `[[…]]` to the solution's anchor memory when one exists) **and** add a
     one-line pointer to `MEMORY.md`, so the next run is a cache-hit. Use a pipe-free discovery
     command, e.g.
     `Get-ChildItem -LiteralPath "<root>" -Directory | Where-Object { Test-Path (Join-Path $_.FullName '.git') }`.

4. **Collect the pending changes — lean by default.** Run `git -C "<repo>" status --short` for
   **every repo in one shell pass** (a single loop — *not* one call per repo) to find the changed
   ones and read each file's **XY** code. **Scope by mode now (don't wait for Step 5):** default
   mode needs staged **and** unstaged; **`--split`/`--amend` need STAGED only** — for those modes
   skip every unstaged read below, restrict the repo set to those whose status shows a **staged**
   entry (**X** column ≠ space; never run `git diff --staged` on a repo with no staged entry), and
   collect each such repo's staged diff **exactly once** here (Steps 9.1/10.1 reuse it, never
   re-read). For every repo with in-scope changes:
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

   **Mode routing** — steps 6–8 below are the **default** mode (one message → clipboard, fully
   read-only). Otherwise skip 6–8 and jump:
   - **`--split` present (alone or with `--amend`) → run `/gitAlign` FIRST (pre-flight).** Before any
     partition or commit, execute `/gitAlign` on the resolved repo set (it reuses this same
     `git-repos-<stem>` cache, so no extra discovery). Splitting the staged changes while a repo is
     mid-merge flattens the merge into ordinary commits and **destroys the two-parent merge link** —
     so gitAlign must clear in-progress operations first. Outcomes:
     - gitAlign reports **all repos aligned** (no in-progress op) → continue to the split below.
     - gitAlign (gated) **finalized a pending merge** as a single two-parent commit → note it, then
       continue on the now-clean tree.
     - gitAlign leaves any repo **not aligned** — a merge with unresolved conflicts, or a
       conflict-stopped rebase/cherry-pick it reported-and-stopped on → **STOP and surface it; do not
       split.** The user resolves, then re-runs `/gitize --split`.
   - `--amend` (with or without `--split`) → **Step 10** (amend mode). Step 10 owns the amend logic
     and, when `--split` is also set, the cross-repo coordination (10.6) — the `/gitAlign` pre-flight
     above has already run.
   - `--split` alone → **Step 9** (split mode) — after the `/gitAlign` pre-flight above.

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

   9.1. **Reuse the staged changes already collected in Step 4 — do not re-read git.** Step 4
   (mode-scoped to staged-only for `--split`) has already pulled each staged-bearing repo's staged
   diff exactly once; work from that. Fall back to `git -C "<repo>" diff --staged --stat` /
   name-status only for a diff too large to have been read in full (say so). If **nothing is staged
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

10. **`--amend` mode — fold the STAGED changes into the existing commits they belong to; plan a new
    commit for the rest.** Like split mode this **commits** (rewrites history via amend), so it is
    *not* read-only and every action is gated behind explicit confirmation. **Scope = staged changes
    only:** unstaged and untracked changes are excluded and left untouched throughout. No clipboard
    write. Mechanically it reuses Step 9's snapshot/unstage/restage discipline (9.4.a–b).

    10.1. **Reuse the staged changes already collected in Step 4** exactly as Step 9.1 — Step 4
    (mode-scoped to staged-only for `--amend`) has already read each staged-bearing repo's staged
    diff once; **do not re-read git**. Fall back to `diff --staged --stat`/name-status only for a
    diff too large to have been read in full (say so). If **nothing is staged anywhere**, report
    "nothing staged to amend" and **stop** (no reset, no commit, no amend).

    10.2. **Enumerate the amend candidates — the UNPUSHED commits only.** For each repo with staged
    changes, list the local commits not yet on the upstream:
    `git -C "<repo>" log --oneline @{u}..HEAD` (when an upstream is set). If there is **no upstream**,
    fall back to the commits on the current branch since it diverged from its base, and **say so** in
    the plan (the base is a heuristic). **Never offer a pushed commit as an amend target** — amending
    it would rewrite published history; such a change is forced to a **new commit** instead (10.3),
    and the report notes why.

    10.3. **Assign each staged hunk to a target, applying these rules in PRECEDENCE order** (higher
    overrides lower):

    1. **(highest) Consistent follow-up → amend that commit.** A staged change that is a
       continuation/fix/completion of an existing **unpushed** commit (touches the same symbols,
       files, or topic that commit introduced) is assigned to **amend** that commit.
    2. **Independent or inconsistent → new commit.** A staged change that belongs to no existing
       commit, or that would contradict one (a different topic, a reversal, an unrelated area), is
       **not** folded in — it is planned as a **new commit** (summarized per Step 6's
       Conventional-Commits rules). When several such changes are independent of the commits but
       related to each other, group them as in 9.2.
    3. **Ambiguous → ask, defaulting to a new commit.** If a change could plausibly belong to more
       than one commit, surface it in the plan and let the user decide; absent a decision, prefer a
       **new commit** (safer than amending the wrong one).

    When multiple staged hunks target the **same** existing commit, they fold into a single amend of
    that commit. Order the work so amends of older commits and their dependents stay consistent.

    10.4. **Present the plan and confirm (interaction 1).** Show, per repo: each **amend** (target
    commit `<short-sha> <subject>` + the staged files/hunks folded into it, and whether its message
    is kept or reworded) and each **new commit** (message + files). Flag any change that was forced
    to a new commit because its only plausible target is already **pushed**. **Ask the user to
    confirm** before touching anything.

    10.5. **On confirmation, execute per repo — snapshot first, then amends, then new commits.**
    - **a. Snapshot + unstage (once)** exactly as 9.4.a: capture each repo's staged state as
      authoritative binary patches, then `git -C "<repo>" reset` so the index is clean and the
      working tree is untouched. Keep the patches for the whole run (recovery if aborted).
    - **b. Amends.** For each target commit (process the **nearest to HEAD last** so earlier rebases
      don't invalidate later shas):
      - i. Stage **only** that target's slice of the snapshot patch with
        `git -C "<repo>" apply --cached "<slice.patch>"` (never `git add <file>` — keeps unstaged
        edits out).
      - ii. **If the target is HEAD** → `git -C "<repo>" commit --amend --no-edit` (or `-m "<reworded>"`
        when 10.4 reworded it). **If the target is an older unpushed commit** → create a fixup with
        `git -C "<repo>" commit --fixup=<sha>` and autosquash it non-interactively:
        `GIT_SEQUENCE_EDITOR=true git -C "<repo>" rebase --autosquash <sha>~1` (the `true` sequence
        editor accepts the generated todo without prompting — no interactive editor). On a rebase
        conflict, **stop and report** (do not force-resolve); the snapshot lets the user recover.
    - **c. New commits.** Stage and commit each planned new commit exactly as Step 9.4.b.i+iv
      (`apply --cached` the slice, show what's staged, `git -C "<repo>" commit -m "<message>"`).
    - **d. Done.** Report per repo: which commits were amended (old → new short-sha + subject) and
      which were newly created, and confirm the remaining unstaged/untracked changes are untouched.

    10.6. **`--amend --split` — coordinate a cross-repo commit by amending where it exists and
    creating it where it doesn't.** This is the amend-aware form of 9.2 rule 1 (a self-dependent set
    spanning repos). When a coordinated change has **already landed as a commit in some repos** but
    is only **staged in the others**, do not make a fresh standalone commit everywhere:
    - In the repos where the matching commit **exists and is unpushed**, **amend** it (10.5.b) so the
      staged follow-up joins the original cross-repo commit.
    - In the repos where it **does not yet exist**, **create** a new commit (10.5.c) **sharing the
      same Conventional-Commits message**, committed back-to-back with the amends as one coordinated
      set — exactly the "one commit per involved repo, same message" shape of 9.2 rule 1.
    - If a target repo's matching commit is already **pushed**, it cannot be amended into the set:
      create a new coordinating commit there instead and **note the divergence** (that repo gets a
      separate follow-up commit rather than an amended one). Present the full cross-repo plan
      (amends + new commits, grouped by the shared message) in the 10.4 confirmation before acting.

Notes: global command — it operates on the `--scope` solution; when `--scope` is **omitted** it defaults to the
**active project's solution** (resolved from that project's ledger, Step 2).
**Default mode** (no `--split`/`--amend`) has no approval gate (read-only git + a non-destructive
clipboard write). **`--split` and `--amend` modes commit** (and `--amend` *rewrites* history via
amend/autosquash) and are therefore gated by the explicit confirmations in Step 9 / Step 10 (the
user OKs the plan, then each commit); never reset/commit/amend without them. **Any `--split`
invocation (alone or with `--amend`) first runs a `/gitAlign` pre-flight** (Step 5) — splitting a
mid-merge tree would flatten the merge and destroy its two-parent link, so gitAlign clears
in-progress operations first and `/gitize` stops rather than split a not-aligned repo. `--amend`
only ever touches **unpushed** commits — a change whose only target is pushed is forced to a new
commit, never a history rewrite. `git` / `Set-Clipboard` (and `git reset`/`apply`/`commit`/`commit --amend`/`rebase
--autosquash` in split/amend modes) may prompt for permission the first time — handle case-by-case,
don't pre-add allow-rules. The repo-set memory keeps the solution's layout discoverable for later runs
(and for sibling commands).
