---
description: Delete all unused (safely-deletable) local git branches across EVERY repo of a multi-repo solution at once — the cleanup pass that prunes stale local branches left after merges/pushes. Per repo it classifies each local branch as SAFE (merged into a local or remote branch, and/or fully pushed with 0 local-only commits → git branch -d), KEEP (the current branch + the default/integration branch, never touched), or RISKY-GONE (unmerged + upstream gone/missing → deleted only with --include-gone via -D). Presents a per-repo deletion plan and gates before deleting. --list/-l lists the unused (merged) branches per repo and stops (read-only). --branch/-b "<b1,b2,…>" deletes only the named branches across all repos, and only where already merged (checks before delete). --dry-run plans and stops. Reuses the /gitize repo-set cache. Usage: /gitWipe [--scope|-s "<.sln, project file, or folder>"] [--list|-l] [--branch|-b "<b1,b2,…>"] [--dry-run] [--include-gone]
---

The user invoked **`/gitWipe`** to delete the **unused (safely-deletable) local branches** across
**every repository of a multi-repo solution at once** — the cleanup pass after merges and pushes leave
stale local branches behind. It deletes **local** refs only: never a remote, never the working tree,
never the current or default branch, and never an unmerged branch without an explicit opt-in.

Constants:
- Work dir: `C:\Users\Sistec 23\source\repos\Claude`

## 1. Parse
- `--scope` / `-s "<path>"` (also accepts the deprecated `-fn`/`--fn`, hidden from `-h` help) — optional: a `.sln`, a project file, or a folder. Given-but-nonexistent → usage + stop.
- `--list` / `-l` — **list only**: per repo, list every unused (safely-deletable) local branch and stop. Read-only.
- `--branch` / `-b "<b1,b2,…>"` — delete **only** the named local branches across all repos, and only where each is **already merged** (checks before delete).
- `--dry-run` — classify + print the plan, delete nothing (the safe preview).
- `--include-gone` — also offer (gated) the unmerged branches whose upstream is gone/missing, via `git branch -D`.
- (`--list` and `--branch` are mutually exclusive modes; either overrides the default wipe. `-h`/`--help` is the universal P11 help — handled by the directive, not here.)

## 2. Resolve target & repo set
Reuse the **`/gitize` Step 1–2** resolution:
- **No `--scope`** → the active Claude project's solution from its ledger (`<active-proj>\<active-proj>.log.md`).
  None resolves → usage + stop.
- A `.sln` (or single-`.sln` folder) → recall `git-repos-<stem>` memory, else discover + persist.
- A project file / `.sln`-less path → single enclosing repo (`git -C <dir> rev-parse --show-toplevel`).

## 3. Per repo, classify every local branch (read-only)
One pass per repo. First resolve the two never-delete branches:
- **Current branch:** `git -C <repo> rev-parse --abbrev-ref HEAD` (detached HEAD → no current name).
- **Default/integration branch:** `git -C <repo> symbolic-ref --quiet refs/remotes/origin/HEAD`
  (strip `refs/remotes/origin/`); if unset, fall back to a local `main`/`master`, else the current branch.

Then for each **other** local branch (`git -C <repo> for-each-ref --format='%(refname:short) %(upstream:short) %(upstream:track)' refs/heads`) decide:
- **KEEP** — the branch IS the current or the default branch.
- **SAFE** — it is **merged somewhere**: contained in a local or remote branch
  (`git -C <repo> branch --merged <default>` ∪ `--merged HEAD` ∪ `git -C <repo> branch -r --merged`),
  **or** it is **fully pushed** — has an upstream with **0** local-only commits
  (`git -C <repo> rev-list --count @{u}..<branch>` == 0).
- **RISKY-GONE** — upstream **gone** (`%(upstream:track)` = `[gone]`) or **no upstream**, **and**
  unmerged (it has local-only commits, contained in nothing). Deletable only with `--include-gone`.

## 4. Mode dispatch
- **`--list`/`-l`** → print, per repo, the SAFE branches (the unused/merged set). Stop here — no gate, no deletion.
- **`--branch`/`-b "<csv>"`** → for each repo, intersect the CSV names with the repo's branches; keep a
  name only where it **exists** and is **already merged** (the SAFE merged-check). Skip + report any
  named branch that is current, the default, absent, or unmerged in that repo. The kept set is the
  deletion set → Step 5.
- **default** → the deletion set = the SAFE branches (plus RISKY-GONE **iff** `--include-gone`) → Step 5.

## 5. Plan table
Print one row per repo: `repo | branch | delete? (yes/keep/skip) | reason (merged / fully-pushed / current / default / unmerged-no-upstream / not-found)`.
- **Headline:** total branches to delete across the set, per repo; call out the RISKY-GONE set
  separately (only acted on with `--include-gone`).
- If `--dry-run` → **stop here** (plan only). If the deletion set is **empty** → report + stop (no gate).

## 6. Approval gate
`/gitWipe` deletes refs → **always gate** (`AskUserQuestion` Proceed/Cancel), recapping exactly which
branches delete in which repos (and the `-D` RISKY-GONE set if `--include-gone`). Cancel → no changes.

## 7. Delete (on Proceed)
Per repo, per branch in the deletion set:
- **SAFE / merged** → `git -C <repo> branch -d <branch>` (lower-case `-d` — git refuses if the branch
  turns out **not** merged; that refusal is the safety net, report it as `skipped: not-merged`).
- **RISKY-GONE** (only when `--include-gone` chosen) → `git -C <repo> branch -D <branch>` (force).
- **Never** delete the current or the default branch; **never** `-D` outside the opted-in RISKY-GONE set.
- Capture each result without aborting the rest of the set.

## 8. Report + hand off
- Table of outcomes per repo: `deleted` / `kept (current|default)` / `skipped (<reason>)` / `error (<git msg>)`.
- **Hand off:** point to `/fetch --prune` to also drop deleted remote-tracking refs, or `/gitAlign` /
  `/gitize` for the actual commit work. `/gitWipe` itself never touches remotes.
- Log to the active project ledger if one is active (P2).

## Guard rails
- **Local refs only — no remote deletes, no force-push, no history rewrite.** The only writes are
  `git branch -d` (and `-D` strictly for the opted-in RISKY-GONE set).
- **Never the current or default branch.** They are classified KEEP and excluded from every mode.
- **`--branch` always checks merged-state first** — a named branch is removed from a repo only where it
  is already merged; never force-deleted just because it was named.
- **No working-tree change** → `/gitWipe` makes no edits, so P15 (don't stage the agent's edits) is moot.
