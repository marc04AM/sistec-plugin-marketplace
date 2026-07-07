---
description: Fetch git/remote updates across a Sistec multi-repo solution in one pass — run `git fetch` over every repo in the solution's repo set, then report a per-repo alignment table (branch, ahead/behind vs upstream, new remote branches/tags, dirtiness). --branch/-b <branch> restricts the fetch to that one branch across all involved repos. Read-only by default (fetch touches only remote-tracking refs); optional --pull fast-forwards the clean, behind-only repos under a gate (never a merge commit, never a force). Reuses the /gitize repo-set cache. Usage: /fetch [--scope|-s "<.sln, project file, or folder>"] [--branch|-b <branch>] [--prune] [--pull]
---

The user invoked **`/fetch`** to bring a multi-repo solution's **remote** state up to date in one
pass — fetch every repo in the solution's repo set, then report what is available upstream. It is
read-only by default (`git fetch` updates only remote-tracking refs); the optional `--pull` fast-
forwards the clean, behind-only repos under an approval gate. Complements `/gitAlign` (local merge
state) — `/fetch` brings remote state in.

Constants:
- Work dir: `C:\Users\Sistec 23\source\repos\Claude`

## 1. Parse
- `--scope` / `-s "<path>"` (also accepts the deprecated `-fn`/`--fn`, hidden from `-h` help) — optional: a `.sln`, a project file, or a folder. Given-but-nonexistent → usage + stop.
- `--branch` / `-b "<branch>"` — optional: restrict the fetch to that single branch across **all**
  involved repos (default: fetch every branch the remote offers). Used as the fetch refspec in Step 3.
- `--prune` — pass `--prune` to `git fetch` (drop remote-tracking refs deleted upstream).
- `--pull` — after fetching, fast-forward-only update each clean, behind-only repo (gated, Step 5).
- (`-h`/`--help` is the universal P11 help — handled by the directive, not here.)

## 2. Resolve target & repo set
Reuse the **`/gitize` Step 1–2** resolution:
- **No `--scope`** → the active Claude project's solution from its ledger (`<active-proj>\<active-proj>.log.md`).
  None resolves → usage + stop.
- A `.sln` (or single-`.sln` folder) → recall `git-repos-<stem>` memory, else discover + persist.
- A project file / `.sln`-less path → single enclosing repo (`git -C <dir> rev-parse --show-toplevel`).

## 3. Fetch every repo (read-only on the working tree)
One pass per repo. `git fetch` only updates remote-tracking refs and tags — it never touches the
working tree or local branches, so this needs no gate. Capture each repo's result
(ok / no-remote / auth-failed / offline / branch-not-on-remote) without aborting the rest of the set.
- **Default (no `--branch`):** `git -C <repo> fetch [--prune] --tags` — fetch everything the remote
  offers.
- **`--branch <branch>`:** fetch only that branch across all repos. Resolve the repo's remote
  (the current branch's `branch.<b>.remote` if set, else `origin`) and run
  `git -C <repo> fetch [--prune] <remote> <branch>`. If `<branch>` doesn't exist on the remote,
  mark the repo `branch-not-on-remote` and continue (don't abort the set).

## 4. Alignment report
Print one row per repo: `repo | branch | ↑ahead ↓behind (vs upstream, post-fetch) | new remote branches/tags | dirty? | fetch result`.
- **Upstream gap (post-fetch):** `git -C <repo> rev-list --left-right --count @{u}...HEAD` → `↓behind ↑ahead`
  (no upstream → mark `no-upstream`).
- **New refs:** note remote branches/tags that appeared in this fetch (from the fetch output).
- **Dirty:** `git -C <repo> status --porcelain` → working-tree changes present?
- **Headline:** how many repos are behind / diverged (ahead AND behind) / up-to-date; flag any
  fetch failures and any `no-upstream` repos.

## 5. `--pull` — fast-forward the clean behind-only repos (gated)
Only if `--pull` was given and at least one repo is **behind-only** (`↑ahead == 0` and `↓behind > 0`)
**and clean**:
- **Approval gate** (`AskUserQuestion` Proceed/Cancel) recapping exactly which repos will fast-forward.
- On Proceed: `git -C <repo> merge --ff-only @{u}` per eligible repo.
- **Skip + report** any repo that is **ahead** (`↑ahead > 0` → would need a real merge — point to
  `/gitAlign` / `/gitize`) or **dirty** (uncommitted changes — fast-forward refused).
- **Never** a merge commit, **never** `--force`, **never** a non-ff merge.

## 6. Guard rails & hand-off
- **No history rewrite, no force, no non-ff merge.** The only write `/fetch` ever performs is a
  gated `merge --ff-only` under `--pull`; default mode writes nothing but remote-tracking refs.
- **Do not stage the agent's own edits** (P15) — `/fetch` makes none.
- **Hand off:** once fetched, point to `/gitAlign` (finish a pending local merge), `/gitize`
  (commit local work), or re-run with `--pull` to integrate behind-only repos.
- Log to the active project ledger if one is active (P2).
