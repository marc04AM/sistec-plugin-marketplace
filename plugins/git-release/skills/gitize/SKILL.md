---
name: gitize
description: >-
  Summarize a solution's pending git changes into one Conventional-Commits message and copy it to
  the clipboard. Multi-repo aware (discovers the repo set fresh each run). Accepts a .sln/.slnx, a
  project file, or a folder; defaults to the current working directory. Fully read-only on git —
  never stages or commits. Use when the user wants a ready-to-paste commit message for a
  solution's pending (multi-repo) changes. For organizing the STAGED changes into several fresh
  commits, use the sibling skill `git-split-commits`; for folding staged changes into existing
  unpushed commits, use `git-amend-commits`. Usage: /gitize [--scope|-s "<.sln, project file, or folder>"]
disable-model-invocation: true
context: fork
model: haiku
---

Turn the **pending git changes of a solution** into one ready-to-paste **Conventional-Commits**
message and put it on the clipboard. Sistec solutions are often **multi-repo workspaces** (the
solution root is not a repo; each subfolder is), so the message spans every changed sub-repo.
Read-only on git plus one clipboard write — never stage, commit, or amend.

Arguments: `$ARGUMENTS`

You run in a forked context and cannot see the conversation that invoked you, so the scope comes
only from the arguments above: `--scope` / `-s "<path>"` (deprecated alias `-fn`), or a bare path.
Strip quotes. With no path, use the current working directory.

## 1. Collect the changes — one script call

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "${CLAUDE_SKILL_DIR}/scripts/collect-changes.ps1" -Target "<path or cwd>"
```

The script resolves the target to a root + repo set (solution/workspace → every immediate
subfolder with a `.git`; project file or in-repo path → its single enclosing repo), then for each
changed repo prints status, `--stat`, and zero-context hunks with generated/lockfile noise
excluded. It enforces the size budget itself (a file over 300 lines, a repo over 600, or more than
1500 lines in total → file-level only) and lists every such cut under `TRUNCATION:`.
Work from this output alone. Re-running git by hand to read more hunks would undo the budget, and
the budget is the reason this skill is cheap.

Exit handling:
- exit 2 (path not found / nothing resolves) → return the printed usage and stop.
- exit 3 (`AMBIGUOUS:` several solutions) → return the list and ask the caller to re-invoke with
  the chosen `.sln` (you cannot ask the user yourself from a fork).
- `RESULT: CLEAN` → return "nothing to commit (working trees clean)" and stop; leave the clipboard alone.

## 2. Write ONE message

```
type(scope): imperative summary

- <repo/area>: what changed and why
- <repo/area>: …

Repos: <repo1>, <repo2>
```

- **Subject** ≤ ~72 chars. Pick the dominant type (`feat`/`fix`/`refactor`/`chore`/`docs`/`test`/…).
  Use the dominant area as the scope, or omit the scope when the change spans many repos.
- **Body**: bullets grouped by repo/area. Describe intent (what and why) from the hunks, not a
  list of filenames. For a file-level-only repo or file, infer carefully from paths + churn and
  keep that bullet modest.
- **Footer**: `Repos:` listing every repo that contributed.

## 3. Clipboard

Build the message into `$msg` and run `$msg | Set-Clipboard` in one PowerShell call. If the
clipboard is unavailable (headless), don't fail: say so, and the user copies it from the report.

## 4. Report (this is what the caller sees)

Return the full message in a fenced block, the repos that contributed, whether it is on the
clipboard, and every `TRUNCATION:` line from the script, so the user knows which parts were
summarized from file lists only.
