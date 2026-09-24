---
name: versionize
description: >-
  Create and maintain a release note (ReleaseNote.md) for a Sistec solution or project — a
  4-section snapshot (Versions, Cell AB, Cell C, Libraries). `-new` builds the first issue; `-upd`
  prepends a changelog since the last release. A pre-flight gate warns on a dirty tree /
  in-progress merge / stale build and offers to sanitize before writing. Reads versions from the
  built DLLs (no rebuild); read-only on git except the note itself. Use when the user wants to cut
  or update a release, or generate/refresh a ReleaseNote. For packaging a versioned source+build
  zip (and for repeating a past packaging flow), use the sibling skill `package-release` — when the
  flow calls for a fresher note, it calls this skill's `-upd` step first so the packaged note isn't
  stale. Usage: say what you want
  (cut a new release note, update the changelog) and point at the solution/project/folder — or use
  flags as shorthand: /versionize -new|-upd "<.sln, project file, or folder>" [--out <path>]
disable-model-invocation: true
model: sonnet
---

Create or update `ReleaseNote.md`, a snapshot of a Sistec solution with **four fixed sections, in
order: `Versions`, `Cell AB`, `Cell C`, `Libraries`**. Read-only on git, reads already-built DLLs,
never builds / stages / commits. Only the note (and, for `-new`, `FeatureCatalog.md`) is written.
Packaging a zip is `package-release`'s job.

Arguments: `$ARGUMENTS`

Background and edge cases (output-path redirection, version fields, assembly families, what the
Cell sections contain) are in `${CLAUDE_SKILL_DIR}/references/details.md`. Read it when a script
result is surprising or you're writing the Cell sections for `-new`, not on every run.

## 1. Mode, target, output

Infer these from the request, or take the flags as shorthand (order-independent):
- **Mode**: `-new` (first issue) or `-upd` (prepend a changelog). If neither is clear, or both are
  given → print `/versionize -new|-upd "<.sln, project file, or folder>" [--out <path>]` and stop.
- **Target**: a `.sln`/`.slnx`, a project file, or a folder (strip quotes). Defaults to the cwd.
- **`--out`**: output file. If it's a folder, append `ReleaseNote.md`. Defaults to `<root>\ReleaseNote.md`.

For `-upd`, first read the existing note's `Versions` table and take each repo's recorded last
commit. If the note is missing → tell the user to run `-new` first and stop.

## 2. Collect every fact — one script call

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "${CLAUDE_SKILL_DIR}/scripts/collect-release-facts.ps1" -Target "<target>" [-Since "RepoA=sha;RepoB=sha"]
```

(`-Since` only for `-upd`, built from the recorded commits.) It prints one compact JSON with:
`root`, `stem`, `mode`, `repos[]` (remote, branch, head, subject, date, dirty counts, in-progress
op, ahead/behind, and with `-Since` the `log` of `hash|subject` lines), `builds[]` (youngest build
folder per executable project + `dlls[]` with version/file/company/title/built-from sha),
`frameworks[]`, `packages[]` (from `Directory.Packages.props`), `globalJson`, `catalog` (path of
`FeatureCatalog.md` if tracked), and `preflight` (dirty / inProgress / stale / unpushed).

This JSON replaces the old per-step git and DLL probing. Don't re-run git, re-enumerate build
folders, or re-read DLLs by hand. If a field is missing or looks wrong, check `details.md`
first. A non-zero exit returns `{error, usage}`: report it and stop (exit 3 = several solutions → ask
which; exit 4 = an unreadable repo, because a note over a partial repo set would misstate the snapshot).

## 3. Pre-flight gate

If every `preflight` list is empty (`unpushed` is informational only) → continue silently.
Otherwise show a short per-repo summary (dirty counts, in-progress op, stale reasons, drift SHAs)
and ask with `AskUserQuestion`:
- **Sanitize**: for a dirty tree, hand off to `git-split-commits` or `git-amend-commits` on the same
  repo set. They own their own gates and commits. For a mid-merge/rebase/cherry-pick there is no
  automated fix: name the repo and operation, and let the user `--continue`/`--abort` it. For a
  stale build: cancel, rebuild in the IDE, re-run. Afterwards, re-run the script and continue.
- **Proceed anyway**: continue, and record the dirty/stale/drift state in the note header and the
  chat report, so the note is honestly labelled.
- **Cancel**: stop.

## 4a. `-new` — write the four sections

Read the feature catalog **before** any app source. It's a tracked file in the repo (see
`catalog`), so every developer and agent works from the same descriptions. Build `Libraries` and
the descriptive half of `Versions` from it. For Cell AB/C, trust the catalog, and re-read only
what changed since its snapshot date:
`git -C "<Sistec.HMI>" log --since=<snapshot-date> --stat -- AB C Common` (+ the same for `Sistec.UI`).
Open source files only for areas that log touches, or when there is no catalog. Live numbers
(versions, SHAs) always come from the script JSON, never from the catalog.

```markdown
# ReleaseNote — <stem>   (<YYYY-MM-DD>)
> generated <date> from <target>; <drift / dirty notes if any>
## Versions
.NET: <app vs lib TargetFrameworks; SDK from global.json or "no global.json">
| Artifact | Repo address | Last commit | Assembly | Version | Author |
| --- | --- | --- | --- | --- | --- |
<one row per Sistec artifact; show AB and C separately when their versions differ, with the
built-from sha when it differs from HEAD>
Opc.Ua / Abc / Mysql / Dapper: <versions>
## Cell AB
## Cell C
## Libraries
```

After writing, update `FeatureCatalog.md` (page inventory, operator features, device comms,
DB/MES per cell, plus a `snapshot <date>` line) if the structure or version line moved. That way
the next run reads the catalog instead of the source. It's a plain file write: the user commits
it like any other change.

## 4b. `-upd` — prepend a changelog

From each repo's `log`, classify by Conventional-Commits type: **Features** (`feat`), **Fixes**
(`fix`), and a brief **Other** line for the rest. Group them by repo. Insert
`## <YYYY-MM-DD> — <version>` **at the top** of the note, then refresh the `Versions` table's
commit pointers and DLL versions from the JSON, so the next `-upd` diffs from here. Leave Cell
AB / Cell C / Libraries untouched unless the user asks. Don't read app source for `-upd`.

Keep every accumulating list newest-first. The new dated section goes above the older ones, and
the new `> 🔄 …` header note goes at the top of the header `🔄` block, directly under the `-new`
origin line. If an earlier run left that block oldest-first, reorder it now.

## 5. Report

Give the output path, the repo set with each repo's HEAD, the version table you wrote, and any
drift or missing-DLL notes. For `-upd`, also summarize the changelog you added.
