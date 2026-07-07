
ported in reconcile-solutions in hmi-developer

---
description: Compare two Sistec solutions and port the innovations of a SOURCE into a DEST, scoped to one feature/purpose. Prefers a git merge when the feature lives in a repo SHARED by both solutions on different branches; otherwise manually ports the change across the (distinct) repos. Trivial/dependent decisions proceed automatically; every non-trivial decision is confirmed interactively. Multi-repo aware (reuses the /gitize repo-set cache); plans everything and gates before editing; leaves edits unstaged (P15). Usage: /gitReconcile -s|--source "<source .sln/.slnx/folder>" -d|--dest "<dest .sln/.slnx/folder>" -p|--purpose "<feature / purpose to port>"
---

The user invoked **`/gitReconcile`** to **port the innovations of a SOURCE solution into a DEST
solution**, scoped to one **purpose/feature**. The two solutions are typically checkouts of the
**same** GitHub repo set on different milestone branches, so reconciliation is a **git merge** where
the feature's repo is shared — and a **manual cross-repo port** where it is not. The governing rule:
*git merge is preferred when different branches of the same repository exist; trivial/dependent
decisions proceed automatically; any non-trivial decision follows an interactive confirm.* Distilled
from the 2026-06-26 `Sistec.5309AB-C → Sistec.5315` ObjectInfo→MultiRowMessageDialog port. Reuses the
[[gitize-command]] repo-set cache and the [[gitalign-command]] merge-finish; pairs with
[[5315-lag-v46-reconciliation]].

Constants / reuse:
- Repo-set discovery + cache: [[gitize-command]] Step 1 (`git-repos-<stem>` memory).
- Merge pre-flight / finish-as-one-commit: `/gitAlign` (never split mid-merge).
- Per P13 no Claude co-author on any commit; per **P15** leave the agent's edits **unstaged**.

## 1. Parse the arguments
Flags order-independent; strip surrounding quotes. **All three are required**:
- `--source` / `-s` `"<…>"` → the SOURCE solution (`.sln`/`.slnx`/folder) whose innovations are ported.
- `--dest` / `-d` `"<…>"` → the DEST solution that receives them.
- `--purpose` / `-p` `"<text>"` → the **feature/purpose** to reconcile (the specific change to port,
  not the whole branch).
- Missing any of the three → print the Usage synopsis and **stop**. `-h`/`--help` anywhere → **P11**
  prints this command's parameters and does not execute (handled by the directive, not here).

## 2. Recall first (P0.2) — do not re-derive
Before touching git, recall from memory: both solutions' **repo-set caches** ([[gitize-command]]
Step-1 `git-repos-<stem>`; discover + persist if absent), the **feature's source-side knowledge**
(its anchor / theme memory — what changed, where), and any active **reconciliation** anchor. Start
from what is already known; only read genuinely new/unverified data.

## 3. Survey both repo sets (read-only)
For each solution resolve its root + sub-repo set (multi-repo → root is not a repo; each subfolder
is). For every sub-repo on both sides record: current **branch**, the relevant **milestone/feature
refs**, an in-progress **MERGE_HEAD/rebase**, and **dirtiness**. Then classify each repo:
- **SHARED** — same origin present on both solutions (a git-merge candidate);
- **DISTINct** — the dest's counterpart is a different repo (manual-port only).
A dirty dest or an in-progress merge → resolve via `/gitAlign` first (report + stop if it can't be
finished safely).

## 4. Locate the feature's commit footprint
On the SOURCE, find the commits that make up the **purpose** beyond the source's milestone base
(`git log <base>..<feature-branch>`), then `git show --stat` them to get the **exact files + which
repos** the feature touches. The purpose — not the whole branch — defines the scope.

## 5. Merge-vs-port decision (the core rule)
For each repo the feature touches:
- **git merge** *only when* the feature's repo is the **same SHARED repo** on both sides **and** a
  full branch merge would **not over-port** (if the source branch also carries unrelated line-work,
  prefer **cherry-pick** of just the feature commits). Finish a merge as **one two-parent commit via
  `/gitAlign`** — never split mid-merge. → **non-trivial: confirm** the merge/cherry-pick choice.
- **Manual port** when the feature's repo is **DISTINCT** from the dest's counterpart (different repo
  → no shared history to merge). Re-create the change in the dest tree.
- A **SHARED repo the feature does not touch** → nothing to do there.

## 6. Map paths + enumerate dest call sites
Map each touched source path to its dest equivalent (same-named project/folder under the dest root;
the app layer often differs — e.g. multi-cell `AB/`+`C/` vs a single `HMI/`). **Grep the dest** for
the symbol(s) the feature changes/removes to enumerate the **real call sites** to migrate.

## 7. Classify every edit — trivial vs non-trivial
- **Trivial / dependent → automatic:** files with shared heritage that port near-identically;
  mechanical renames; new files whose dependencies already exist on the dest.
- **Non-trivial → `AskUserQuestion` confirm:** a shared file that has **diverged** on the dest (must
  be re-applied *semantically*, not textually); a dest call site with **no source counterpart**; the
  merge-vs-cherry-pick choice; and **deleting** a migrated-away type.

## 8. Plan + approval gate
Present the full reconciliation plan — per-repo merge/port decision, the file groups (auto vs
confirm), and the verification step — and **gate** with `AskUserQuestion` (`Proceed` / adjust /
plan-only) **before any edit**. This is the standing "plan everything and ask confirmation" mandate.

## 9. Execute (after approval)
- **Build-dependency pre-check** — before adding ported files, verify the types/extensions they need
  already exist on the dest's branch (avoid a build-break surprise).
- **Auto-apply** the trivial group; for each **divergent shared file**, diff the dest version and
  re-apply the change's *intent* (don't blind-patch a stale diff).
- **Confirm each non-trivial site** as you reach it (per Step 7), then apply.
- **Watch old→new factory signatures** — arg order can change across the migration; pass **named
  arguments** to stay safe.
- **Defer deletion** of any migrated-away type until **all** callers (including the gated ones) are
  migrated.
- Merge/cherry-pick path: perform via `/gitAlign` (one commit, gated).

## 10. Verify + report
- **Build the dest solution** (`dotnet build <dest .sln/.slnx>`), expect 0 errors (note any
  pre-existing warning baseline).
- **Zero residual references** to a removed symbol (a `<c>…</c>` doc note is harmless).
- **Leave all edits unstaged** (P15) — report the change set (`git status --porcelain`). Per P13 no
  Claude co-author on any commit. Per **P1** explicitly **report the divergence** created between the
  two solutions to ease later sync.

## Notes / constraints
- Read-only until the Step-8 gate; everything after is gated and left unstaged for review.
- Multi-repo: a feature can span several repos with different merge/port verdicts — decide per repo.
- If the SOURCE feature is **uncommitted**, a git merge cannot carry it — commit it on the source
  first (ask), or fall back to a manual port.
