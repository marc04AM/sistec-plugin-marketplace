---
description: Merge a source branch into the current branch across EVERY repo of a multi-repo solution at once. By default each merge is left OPEN (--no-ff --no-commit, MERGE_HEAD set) for the user to finalize with /gitAlign; the gate also offers a "Proceed & commit" choice that finalizes each conflict-free repo inline as one two-parent (--no-ff) merge commit — carrying a /gitize-style Conventional-Commits message describing the merged result (not git's parent-branch default) — leaves any conflicted repo OPEN, then re-runs the survey/gate. A repo is merged only if the source produces differences (commits in HEAD..from); repos that are already-merged, missing the source ref, dirty, or mid-merge/rebase are skipped and reported. The initiator half of the /merge → /gitAlign pair. Reuses the /gitize repo-set cache. Usage: /merge --from|-f <branch> [--scope|-s "<.sln, project file, or folder>"]
---

The user invoked **`/merge`** to start a merge of a source branch into the **current** branch across
**every repository of a multi-repo solution at once**, leaving each merge **open** (uncommitted) so
the set is finalized together by **`/gitAlign`**. `/merge` is the *initiator*; `/gitAlign` is the
*finalizer* (it commits each open merge as one two-parent merge commit). A repo is merged **only if
the source produces differences**.

Constants:
- Work dir: `C:\Users\Sistec 23\source\repos\Claude`

## 1. Parse
- `--from` / `-f "<branch>"` — **mandatory**: the source branch to merge **into** each repo's current
  branch. Missing → print usage + **stop** (there is nothing to merge).
- `--scope` / `-s "<path>"` (also accepts the deprecated `-fn`/`--fn`, hidden from `-h` help) — optional: a `.sln`, a project file, or a folder. Given-but-nonexistent →
  usage + stop.
- (`-h`/`--help` is the universal P11 help — handled by the directive, not here.)

## 2. Resolve target & repo set
Reuse the **`/gitize` Step 1–2** resolution:
- **No `--scope`** → the active Claude project's solution from its ledger (`<active-proj>\<active-proj>.log.md`).
  None resolves → usage + stop.
- A `.sln` (or single-`.sln` folder) → recall `git-repos-<stem>` memory, else discover + persist.
- A project file / `.sln`-less path → single enclosing repo (`git -C <dir> rev-parse --show-toplevel`).

## 3. Pre-flight survey (read-only)
One pass per repo. For each, collect:
- **Branch:** `git -C <repo> rev-parse --abbrev-ref HEAD` (note a detached HEAD).
- **Source ref:** resolve `<from>` per repo — prefer the local branch `<from>`, else the
  remote-tracking `origin/<from>` (`git -C <repo> rev-parse --verify -q <ref>`). Neither → `no-source`.
- **Incoming commits:** `git -C <repo> rev-list --count HEAD..<source>` → `0` means the source is
  already contained in HEAD → `already-merged` (no differences → do not merge).
- **Dirty:** `git -C <repo> status --porcelain` → any uncommitted change → `dirty`.
- **In-progress op:** `MERGE_HEAD` / a `rebase-merge`|`rebase-apply` dir / `CHERRY_PICK_HEAD` present
  → `in-progress`.

## 4. Plan table + classification
Print one row per repo: `repo | branch | source ref | incoming (HEAD..from) | action`. Action is:
- **MERGE** — source present, **≥1** incoming commit, clean tree, no in-progress op.
- **skip: already-merged** — 0 incoming commits (source produces no differences).
- **skip: no-source** — neither `<from>` nor `origin/<from>` exists (suggest `/fetch` first).
- **skip: dirty** — uncommitted changes (starting a merge over them is unsafe).
- **skip: in-progress** — a merge/rebase/cherry-pick is already underway (suggest `/gitAlign` first).

## 5. Approval gate
`/merge` mutates working trees → **always gate** (`AskUserQuestion`), recapping the **source branch**,
the repos that **will be merged**, and the **skipped** repos with reasons. If **nothing** is classified
MERGE → report + **stop** (no gate, no changes). Offer three choices:
- **Cancel** — make no changes.
- **Proceed (open)** — open every MERGE repo for `/gitAlign` (step 6a). The default initiator behavior.
- **Proceed & commit** — for **each** MERGE repo, finalize inline when it applies cleanly and leave any
  conflicted repo open (step 6b), then **come back to step 3** (re-survey + re-gate) so the now-committed
  repos read `already-merged` and only the still-open (conflicted) ones remain to act on.

## 6a. Perform the open merges (on "Proceed (open)")
Per MERGE repo, leave the merge **open** for `/gitAlign`:
- `git -C <repo> merge --no-ff --no-commit <source>`
  - `--no-ff` forces a two-parent merge even when a fast-forward is possible (uniform finalize path).
  - `--no-commit` leaves `MERGE_HEAD` set + the result staged — the **open** state `/gitAlign` detects.
- **Conflicts** → leave the unmerged paths in place (the merge stays open); do **not** resolve, stage,
  or commit. Record outcome `conflicts-open`.
- Clean apply → `merged-open`. A failure to even start → `failed` (report the git error).

## 6b. Perform & commit the clean merges (on "Proceed & commit")
Per MERGE repo, finalize the conflict-free ones inline, leave conflicted ones open:
- **Apply, holding the commit:** `git -C <repo> merge --no-ff --no-commit <source>`
  - `--no-ff` forces a two-parent merge (uniform with the `/gitAlign` finalize shape; preserves the
    merge link).
  - `--no-commit` stops before the commit so the message can be **composed**, not defaulted.
- **Conflicts** (unmerged paths after the apply) → **do not** resolve, stage, or commit — the merge
  stays **open**. Record `conflicts-open` (route it to `/gitAlign`).
- **Clean apply** → **compose a descriptive merge message, then commit:**
  - Build the message the **`/gitize`** way — summarize the **incoming commits** (`HEAD..<source>`,
    `git -C <repo> log --no-merges <source> --not HEAD`) into **one Conventional-Commits message**
    (`type(scope): subject`, type ∈ fix / feat / chore / refactor / …) describing the **result the
    merge lands** — *what changed*, never the parent branch names. Rationale: git's default
    `Merge branch '<from>' into '<to>'` is meaningless once a branch is deleted; a result-describing
    subject survives. **No `Co-Authored-By` / Claude trailer** (P13).
  - `git -C <repo> commit -m "<message>"` — `MERGE_HEAD` is still set, so this is a **two-parent
    merge commit** carrying the composed message. Record `committed`.
- A failure to even start the merge → `failed` (report the git error).
- After the pass, **re-run step 3 (survey) and step 5 (gate)**; the committed repos now show
  `already-merged`, conflicted ones show `in-progress` (→ `/gitAlign`).

## 7. Report + hand off
- Table of outcomes per repo: `open-clean` / `open-with-conflicts` (6a), `committed` /
  `open-with-conflicts` (6b), or `skipped (<reason>)`.
- **Any repo left open (conflicts, or all of 6a) → hand off to `/gitAlign`** to finalize as a single
  two-parent commit (resolving conflicts first). **Never** route a `/merge`-opened tree through
  `/gitize --split` (it flattens the merge link — the `5315-git-align` lesson).
- Log to the active project ledger if one is active (P2).

## Guard rails
- **No history rewrite, no force, no auto-resolve.** Writes are limited to the `merge` invocations:
  open merges (6a) and **clean** two-parent merge commits (6b). Conflict resolution and finalizing a
  conflicted merge are always the user's / `/gitAlign`'s.
- **Commit only the clean, automatic merge (6b).** Never commit a repo with unresolved conflicts.
  Commit with a composed `/gitize`-style Conventional-Commits message (`-m`) describing the merged
  **result** — never git's `Merge branch …` parent-branch default, and never a Claude co-author (P13).
- **Skip, don't fight.** Dirty / in-progress / no-source / already-merged repos are reported untouched.
- **6b is the user's explicit commit choice — the P15 exception.** P15 (don't stage/commit the agent's
  own edits) still governs 6a (open merges stage only the merge result, untouched for review). 6b
  commits **only** because the user picked "Proceed & commit" at the gate, and only the clean automatic
  merge — never the agent's own edits.
