---
description: Pre-flight + safe-reconciliation for a multi-repo solution's git state — survey every repo (branch, ahead/behind, in-progress merge/rebase/cherry-pick, dirtiness), report an alignment table, and safely FINISH a pending merge as a single two-parent merge commit (never split) under a gate. Run BEFORE /gitize --split, which is unsafe mid-merge. Reuses the /gitize repo-set cache. Usage: /gitAlign [--scope|-s "<.sln or folder>"] [--check-only]
---

The user invoked **`/gitAlign`** to align the git state across a multi-repo solution **before**
any commit shaping. It is the pre-flight `/gitize` lacks: it detects in-progress git operations and
branch divergence, and **safely finishes a pending merge** (preserving the two-parent link) — never
splitting it. Rationale: `/gitize --split` during a merge flattens the merge into ordinary commits
and **destroys the merge link** (the lesson from landing the v3.26→v4.6 reconciliation).

Constants:
- Work dir: `C:\Users\Sistec 23\source\repos\Claude`

## 1. Parse
- `--scope` / `-s "<path>"` (also accepts the deprecated `-fn`/`--fn`, hidden from `-h` help) — optional: a `.sln` or a folder. Given-but-nonexistent → usage + stop.
- `--check-only` — scan + report, change nothing (the safe default to run before `/gitize --split`).
- (`-h`/`--help` is the universal P11 help — handled by the directive, not here.)

## 2. Resolve target & repo set
Reuse the **`/gitize` Step 1–2** resolution:
- **No `--scope`** → the active Claude project's solution from its ledger (`<active-proj>\<active-proj>.log.md`).
  None resolves → usage + stop.
- A `.sln` (or single-`.sln` folder) → recall `git-repos-<stem>` memory, else discover + persist.
- A project file / `.sln`-less path → single enclosing repo (`git -C <dir> rev-parse --show-toplevel`).

## 3. Survey every repo (read-only)
Batch one pass per repo. For each, collect:
- **Branch:** `git -C <repo> rev-parse --abbrev-ref HEAD` (note a detached HEAD).
- **Upstream gap:** `git -C <repo> rev-list --left-right --count @{u}...HEAD` → `↓behind ↑ahead`
  (no upstream → mark `no-upstream`).
- **Dirty:** `git -C <repo> status --porcelain` → working-tree changes present? unmerged paths?
- **In-progress op** — test the sentinels (`git -C <repo> rev-parse --verify -q <ref>` / git-dir
  paths): `MERGE_HEAD` → **merging**; a `rebase-merge`/`rebase-apply` dir → **rebasing**;
  `CHERRY_PICK_HEAD` → **cherry-picking**; `REVERT_HEAD` → **reverting**; `BISECT_LOG` → **bisecting**.

## 4. Alignment report
Print one row per repo: `repo | branch | ↑ahead ↓behind | state (clean / merging / rebasing / cherry-picking / …) | dirty? | staged?`.
- **Branch consistency:** if the repos are not all on the same branch, flag the divergence
  explicitly (a cross-repo landing assumes the set moves together) — list the outliers; do not
  enforce a specific name.
- **Headline:** *aligned* (all clean, no in-progress op, branches consistent) or *not aligned*
  (which repos block, and why).
- If `--check-only` → **stop here** (report only).

## 5. Safely finish pending operations (gated)
Only if not `--check-only` and at least one repo has an in-progress op:

**Merging (`MERGE_HEAD`)** — the core safe-complete:
- If the repo still has **unmerged paths** (conflicts) → **report and stop** for that repo; the
  conflict resolution is the user's. Do **not** stage, resolve, or commit.
- If conflicts are already resolved (no unmerged paths) → **approval gate** (`AskUserQuestion`
  Proceed/Cancel) recapping the repo + the merge parents → on Proceed finalize as a **single
  two-parent merge commit**: `git -C <repo> commit --no-edit` (uses `MERGE_MSG`; preserves the
  merge link). **Never** `reset`/unstage and re-commit, and **never** route a pending merge through
  `/gitize --split`.

**Rebasing / cherry-picking / reverting (conflict-stopped)** — **report and stop** (option a): show
the repo, the operation, and the conflicted paths; let the user resolve and `--continue` themselves.
`/gitAlign` does not auto-`continue` a stopped rebase/cherry-pick.

**Bisecting** — report only.

## 6. Guard rails & hand-off
- **No history rewrite, no force.** No `reset --hard`, no `push --force`, no `rebase` of pushed
  commits. The only write `/gitAlign` performs is finalizing an already-resolved merge (Step 5),
  and only after the gate.
- **Do not stage the agent's own edits** (P15). Completing a merge commits the **user's**
  already-resolved merge index — it adds nothing of the agent's.
- **Hand off:** once every repo is clean + consistent, point to `/gitize` (message),
  `/gitize --split` (now safe — no pending merge), or `/gitize --amend` for the actual commit work.
- Log to the active project ledger if one is active (P2).
