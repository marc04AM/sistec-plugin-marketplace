# git-release

Release tools for Sistec **multi-repo** solutions (the solution root is not a git repo; each
subfolder is). The skills share repo-set discovery (a fresh scan on every run, no cache).

## Skills

| Skill | What it does | Writes |
| :---- | :----------- | :----- |
| `/git-release:gitize [--scope\|-s "<target>"]` | aggregates the diffs of every changed sub-repo (staged + unstaged) into **one** Conventional-Commits message on the clipboard | clipboard |
| `/git-release:git-split-commits [--scope\|-s "<target>"]` | splits the **staged** changes into several commits grouped by impact, committed interactively segment by segment | commits |
| `/git-release:git-amend-commits [--scope\|-s "<target>"]` | folds the **staged** changes into the existing unpushed commits (amend/fixup+autosquash); plans a new commit for the rest | commits (amend) |
| `/git-release:versionize -new\|-upd "<target>" [--out <path>]` | `ReleaseNote.md` release note (4 sections: Versions, Cell AB, Cell C, Libraries) from already-built DLLs + git; `-upd` prepends a changelog | `.md` file |
| `/git-release:package-release --zip "<target>" [--rel <note>] [--skip …] [--include\|-i …] \| -r\|--repeat` | packages git-clean source + build + release note into a versioned zip; `-r` repeats the last packaging flow | `.zip` file |

Previously there were only two commands (`gitize` with nested `--split`/`--amend`, `versionize` with
nested `--zip`/`--deploy`/`-r`); they were split out because each mode is git surgery or release
orchestration in its own right, not a variant of the base task. **No skill deploys or publishes
anything to production** — this plugin's scope stops at the zip; `--deploy` was removed on purpose
(the `/deploy` skill it relied on does not exist in this marketplace).

## Notes

- **`gitize` is always read-only** (git status/diff + a clipboard write, no commits).
- **`git-split-commits` and `git-amend-commits` commit** (the latter also rewrites unpushed commits
  via amend/autosquash) — both are gated by confirmations and refuse to start if a repo is
  mid-merge/rebase/cherry-pick (no auto-fix: the user resolves it by hand, then re-runs).
- **`versionize` never builds**: it reads versions from the already-built DLLs (the youngest) and
  git facts from the repos. Its only write is the output file.
- **`package-release` never builds** and does not write the release note's content (it calls
  `versionize -upd` when the note needs refreshing before packaging). It does not deploy or publish
  anything — it only produces the zip.
- **Reduced token usage**: `gitize` and `versionize` collect their data with a bundled PowerShell
  script (`scripts/collect-changes.ps1`, `scripts/collect-release-facts.ps1`) that returns compact
  output in a single call, instead of dozens of git/DLL commands read by the model.
  `gitize` has a diff budget (300 lines per file, 600 per repo, 1500 in total; beyond that, a
  file-level summary only, always declared) and runs in a separate context (`context: fork`) with
  `model: haiku`: it does not see the conversation, so the scope must be passed as an argument
  (default: cwd). `versionize` uses `model: sonnet` and stays inline because the pre-flight gate
  must be able to ask the user; for `-new` it reads `FeatureCatalog.md` + only the git delta, never
  the whole source.
- No secrets are involved. `git` / `Set-Clipboard` may ask for permission the first time.

## Installation

```shell
/plugin install git-release@sistec-plugins
```
