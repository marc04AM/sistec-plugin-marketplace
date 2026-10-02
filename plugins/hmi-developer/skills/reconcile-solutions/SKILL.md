---
name: reconcile-solutions
description: Ports a feature/innovation from a SOURCE solution into a DEST solution, scoped to a single purpose. Uses git merge/cherry-pick where the feature lives in a repo shared by both solutions on different branches; otherwise does a manual cross-repo port by re-applying the *intent* of the change (not a textual diff) to the dest's divergent code. Plans everything, confirms non-trivial decisions, verifies with a build, and leaves the edits unstaged. Use it when you need to align two solutions of the same family (typically checkouts on different milestone branches) by porting a specific feature from one to the other.
disable-model-invocation: true
---

# reconcile-solutions — port a feature from one solution to another

Ports the **innovations** of a SOURCE solution into a DEST solution, scoped to **a single
purpose/feature**. The two solutions are typically checkouts of the **same** repo family on
different milestone branches: where the feature lives in a **shared** repo, reconciliation is a
**git merge/cherry-pick**; where the repo is **distinct** (or the code has diverged), it is a **semantic
manual port**.

Guiding rule: *merge is preferred when the same repo exists on different branches; trivial/dependent
decisions proceed on their own; every non-trivial decision is confirmed.*

## 1. Input (all required)

- **source** — the solution (`.sln`/`.slnx`/folder) whose innovations are ported.
- **dest** — the solution that receives them.
- **purpose** — the **feature/purpose** to reconcile (the specific change, **not** the whole branch).

One of the three missing → ask for it and stop until it is clear.

## 2. Survey both repo sets (read-only) + classify

For each solution resolve root + sub-repos (multi-repo → the root is not a repo; every subfolder with
`.git` is). For each sub-repo on both sides record: current **branch**, the relevant **milestone/feature
refs**, any in-progress **MERGE_HEAD/rebase**, the **dirtiness**. Then classify:

- **SHARED** — same repo on both sides: same origin **or** shared history (a
  `git merge-base` exists) → git-merge candidate.
- **DISTINCT** — counterpart with a different origin **and** no shared history → manual port only.

A **dirty** dest, or one with a **merge in progress** → close/clean it first (see *Closing a merge
safely*); if it cannot be finished safely → report and **stop**.

## 3. Find the feature's commit footprint

On the SOURCE, find the commits that make up the **purpose** beyond the milestone base
(`git log <base>..<feature-branch>`), then `git show --stat` to get the **exact files + which repos**
the feature touches. The purpose — not the whole branch — defines the scope.

## 4. Merge-vs-port decision (for each touched repo)

- **git merge / cherry-pick** *only* when the repo is the **same SHARED** repo on both sides. Whole-branch
  merge only if it **does not over-port**; if the source branch also carries unrelated work →
  **cherry-pick** only the feature's commits. → non-trivial: **confirm** the choice.
- **Manual port** when the repo is **DISTINCT** (different repo → no shared history to merge):
  re-create the change in the dest tree.
- A **SHARED repo the feature does not touch** → nothing to do there.

### Closing a merge safely

When you complete a merge, finalize it as **a single two-parent merge commit**
(`git commit --no-edit`, uses `MERGE_MSG`) — **never** split it into ordinary commits: that would flatten the
merge and **destroy the two-parent link**. If there are **unresolved paths** (conflicts), resolution
belongs to the user → report and stop; do not stage/resolve/commit on their behalf. **Never**
`reset --hard`, `push --force`, or rebase already-pushed commits.

## 5. Map the paths + enumerate the call sites in the dest

Map every touched source path to its equivalent in the dest (same-named project/folder under the dest
root; the application layer often differs — e.g. multi-cell `AB/`+`C/` vs single `HMI/`). **Grep
the dest** for the symbol(s) the feature changes/removes → enumerate the **actual call sites** to migrate.

## 6. Classify each edit — trivial vs non-trivial

- **Trivial/dependent → automatic:** files with shared ancestry that port almost identically; mechanical
  renames; new files whose dependencies already exist in the dest.
- **Non-trivial → confirm (`AskUserQuestion`):** a shared file that has **diverged** in the dest (must be
  re-applied **semantically**, not textually); a dest call site **without** a source
  counterpart; the merge-vs-cherry-pick choice; the **deletion** of a migrated-away type.

## 7. Plan + approval gate (before any edit)

Present the complete plan — per-repo merge/port decision, the file groups (auto vs confirm), and the
verification step — and **gate** (`Proceed` / correct / plan-only). Read-only up to this point.

Minimum plan structure (and of the final report in Step 9):

```
## Reconciliation: <purpose>   (SOURCE → DEST)
### <repo> — [SHARED merge | SHARED cherry-pick | DISTINCT port | no action]
- Auto files: <list>
- Files to confirm: <list + why>
### Verification
- dest build 0 new errors · 0 leftover references · edits left unstaged
```

## 8. Execute (after approval)

- **Dest build baseline** — before editing, build the dest and record pre-existing errors/warnings,
  so at the end you can tell **new** problems from those already there.
- **Build-dependency pre-check** — before adding ported files, verify that the types/extensions
  they require already exist on the dest branch (avoids broken-build surprises).
- **Auto-apply** the trivial group; for every **divergent shared file**, diff the dest version and
  re-apply the **intent** of the change (do not blindly patch a stale diff).
- **Confirm each non-trivial site** as you reach it, then apply.
- **Watch out for old→new factory signatures**: argument order may change in the
  migration → pass **named arguments** to be safe.
- **Defer the deletion** of a migrated-away type until **all** callers (including the gated ones)
  have been migrated.
- Merge/cherry-pick path: finalize as a single gated two-parent commit (see above).

## 9. Verify + report

- **Build the dest** (`dotnet build <dest .sln/.slnx>`), comparing against the Step 8 baseline:
  0 **new** errors expected. If the build fails, report the errors, **leave the edits unstaged**, and
  do not auto-repair beyond the feature's intent (no out-of-scope rework).
- **Zero leftover references** to a removed symbol (a `<c>…</c>` doc note is harmless).
- **Leave all edits unstaged** — report the change set (`git status --porcelain`) for review.
- **Report the divergence** created between the two solutions, to ease the next sync.

## Notes

- Read-only until the Step 7 gate; everything after it is gated and left unstaged for review.
- Multi-repo: a feature can span several repos with different merge/port verdicts — decide per repo.
- If the SOURCE feature is **uncommitted**, a git merge cannot carry it → commit it on the
  source first (ask), or fall back to the manual port.
