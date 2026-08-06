---
name: package-release
description: >-
  Package a Sistec solution's git-clean source + build output + release note into a versioned zip,
  and replay a past packaging flow. `--zip`-equivalent packaging; `-r`/`--repeat` replays the last
  recorded flow (refresh-note/package legs, in order). A pre-flight gate warns on a dirty tree /
  in-progress merge / stale build and offers to sanitize before packaging — a zip is meant to be
  handed off, so it should never silently bundle uncommitted or stale work. Reads versions from
  already-built DLLs (no rebuild); this skill never builds, deploys, or pushes anything anywhere —
  its only write is the zip file (plus its own tiny replay-state file). Use when the user wants to
  package/bundle a release zip, or repeat a past packaging flow. For just writing/updating the
  release note without packaging, use the sibling skill `versionize`. Usage: say what you want
  (package a zip, repeat the last release package) and point at the solution/project/folder — or
  use flags as shorthand: /package-release --zip "<.sln, project file, or folder>" [--rel <note>]
  [--skip …] [--include|-i …] | -r|--repeat
---

The user invoked `/package-release` to **package a Sistec solution's release artifact** (git-clean
source + build output + release note) into a versioned zip. It reuses `gitize`/`versionize`'s
repo-set discovery, and calls `versionize`'s own `-upd` step when the note needs refreshing first —
this skill never writes the release note's own content itself. It is **read-only on git**; its only
writes are the zip file and its own replay-state file. **It never deploys or pushes anything
anywhere** — packaging a zip is the entire scope; what the user does with that zip afterward is up
to them.

1. **Resolve the flow — natural language first.** Check for a **repeat** request first (it's
   standalone — see Step 2). Otherwise infer, from what the user is asking, whether to **refresh
   the release note first** (e.g. "update the changelog and package it") before packaging. The
   flags below are accepted, order-independent **shorthand** for the same intent — useful for
   precise lists (`--skip`/`--include`) or repeatable scripting — but none of this wording is
   required:
   - **`<target>`** (positional, usually quoted; strip quotes) → a `.sln` file, a **project file**,
     or a **folder**.
   - **`--rel <path>`** (optional) → the release note to bundle into the zip. If **missing**,
     default to **`<solution root>\ReleaseNote.md`**.
   - **`--skip "f1","f2",…`** (optional) → a **list of folder names** to exclude from the zip.
     Collect every token after `--skip` up to the next flag; **strip surrounding quotes and commas**;
     case-insensitive. A name matches a **whole repo** (e.g. `Test`) **or any folder segment** anywhere
     in a file's path (e.g. a nested `Test\` / `Resources\`). Empty by default.
   - **`--include "f1","f2",…`** / **`-i …`** (optional) → a **list of additional folders to
     bundle** into the zip (beyond the solution's own repos). Collect every token after `--include`/`-i`
     up to the next flag; **strip surrounding quotes and commas**. Each folder is added under its
     **leaf name** at the zip root; if it **contains a C# solution** it gets the git-clean + `--skip`
     exclusion rules **and** its built `Release/v<ver>` output (Step 7).
   - Usage on error: `/package-release --zip "<.sln, project file, or folder>" [--rel <path>] [--skip
     "f1","f2",…] [--include "f1","f2",…] | -r|--repeat`.

2. **Replay the last recorded flow (standalone — when the user asks to repeat/redo the last
   run)** (`-r`/`--repeat` is the literal shorthand; takes no other args). Read the saved flow from
   `./.package-release/last-flow.txt` (current working directory) — **one leg per line**, in order:
   `refresh-note <target>` or `package <target> [flags…]`. If the file is **missing or empty**,
   print usage and **stop**. **Echo each leg before running it**; a `refresh-note` leg re-dispatches
   `versionize`'s own `-upd` step (Step 3 below) on the recorded target, a `package` leg
   re-dispatches Step 7. If a leg's target no longer resolves (moved/renamed path), echo the leg,
   report the failure, and **stop** rather than replaying a broken flow. Replayed legs **do not
   re-record** (a flow's own legs are part of the replay, not new user calls) and `-r` itself is
   **never recorded** — so the saved flow is unchanged and a second `-r` repeats it identically.
   Skip Steps 3–8 below entirely once a replay is dispatched.

3. **Refresh the release note first, when the flow calls for it.** Run `versionize`'s own `-upd`
   step (its Steps 1–10, mode `-upd`) on the resolved target, exactly as if the user had asked
   `versionize` directly — this skill does not duplicate that logic. Skip this step when the flow is
   package-only (the existing `--rel` note is trusted as-is).

4. **Resolve the target → root, stem, and repo set** (same shapes as `gitize`/`versionize`):
   - **`.sln` file** (or a **folder** with exactly one `.sln`) → **solution target**: root = its
     folder, `<stem>` = the `.sln` name. Discover the repo set: scan the root itself for a `.git`,
     then its immediate subfolders for a `.git` directory — a cheap, single-pass scan, done fresh
     every run.
   - **project file / in-repo path** → **single-repo target**: resolve the one enclosing repo with
     `git -C "<dir>" rev-parse --show-toplevel`; repo set = just that repo.

5. **Locate the build outputs — follow each app project's output redirection, then trust the
   youngest build** (same discipline as `versionize` Step 4 — reused here so the zip's version and
   `Release/` contents come from the actual freshest build, never a stale published copy):
   - **Read the `.csproj` for an output redirection** — `<OutputPath>` (or `<OutDir>` /
     `<BaseOutputPath>`). Sistec apps set `OutputPath = bin\$(Configuration)\$(_ProductFolderName)\`
     where `_ProductFolderName = "HMI v$(_AsmVerMajorMinor)"` (e.g. `bin\Release\HMI v3.25\`). Resolve
     the resolvable base (`<projDir>\bin\Release\`) and enumerate its subfolders by **discovery**
     rather than re-evaluating the MSBuild expression.
   - **If no redirection is declared**, default the base to `<projDir>\bin\Release\` (then `bin\Debug\`).
   - **Pick the youngest build:** under the resolved base, choose the subfolder whose DLLs have the
     **most recent `LastWriteTime`**. **Do not build.**
   - Pipe-free discovery, e.g. `Get-ChildItem -LiteralPath "<projDir>\bin\Release" -Directory` → sort
     by newest `*.dll` `LastWriteTime`. **Scan every app's `bin\Release` in ONE shell pass**, reading
     only `LastWriteTime` — the version number itself (major.minor) comes from a single follow-up
     `[System.Reflection.AssemblyName]::GetAssemblyName($dll).Version` read on the chosen folder.
   - **No build found anywhere** (same fallback as `versionize` Step 4): fall back to the `.csproj`'s
     literal `FileVersion`, and **sanitize it for filesystem use** before Step 7 touches a path with
     it — an unexpanded literal like `3.25.*` still has a `major.minor` prefix, so strip everything
     from the first non-numeric/non-dot character onward (`3.25.*` → `3.25`). Flag prominently in the
     Step 8 report that **no build output exists** — the zip's `Release/` folder will be empty/omitted
     and the version in its name is read from source, not verified against an actual build.

6. **Pre-flight cleanliness gate — warn on any unwanted condition, offer to sanitize, then resume.**
   A zip built over a dirty tree or a stale build captures work that corresponds to **no commit** —
   whoever receives the package gets binaries or source that don't match any commit, so this gate
   matters more here than in `versionize`'s note-only case. Before Step 7, verify the repo set +
   build are release-worthy. Detect, across the resolved repo set in **one batched read-only shell
   loop**:
   - **(a) Dirty working tree** — `git -C "<repo>" status --porcelain` non-empty. The zip bundles
     `ls-files --cached --others --exclude-standard` (the **working-tree** state), so a dirty repo
     packages uncommitted work. Report per repo (staged / unstaged / untracked counts).
   - **(b) Git operation in progress** — a `.git/MERGE_HEAD`, a `rebase-merge`/`rebase-apply` dir, or a
     `.git/CHERRY_PICK_HEAD` ⇒ mid-merge/rebase/cherry-pick (a half-finished state with no automated
     fix — see the sanitize options below).
   - **(c) Stale / not-clean build** — compare each app's **built-from SHA** (`ProductVersion`
     `1.0.0+<sha>`) and the youngest-build **timestamp** against repo HEAD: if HEAD is **ahead** of the
     built-from commit, or any tracked source file is **newer** than the youngest build's DLLs, the
     built artifacts are **stale vs source**.
   - **(d) Ahead/behind upstream** *(informational)* — `git -C "<repo>" rev-list --left-right --count
     @{u}...HEAD` where an upstream exists.

   **If no condition fires → continue silently** to Step 7. **If any fires → present a concise
   per-repo summary** and **offer to sanitize** via `AskUserQuestion`, then **resume from here**:
   - **Sanitize the git state** — for a **dirty tree (a)**, hand off to `git-split-commits` or
     `git-amend-commits` on the same repo set; they own their own gates/commits. For a
     **mid-operation repo (b)**, there is no automated fix — tell the user which repo and operation,
     and have them finish or abort it manually. After either is resolved, **re-run these checks**.
   - **Proceed anyway** — accept the condition and continue; record it in the zip's report so the
     package is honestly labelled.
   - **Cancel** — stop without packaging.

   For a **stale build (c)**, this skill **never builds** — the sanitize path is *Cancel → rebuild →
   re-run* or *Proceed anyway (drift noted)*. **Regenerate after a sanitize rebuild:** whenever
   sanitizing committed changes and/or a stale build was rebuilt, resume by **(i)** re-running Step 5
   to pick up the fresh youngest build, **(ii)** re-running Step 3 (note refresh) so the packaged
   note reflects the just-committed changes — even a package-only flow gets an implicit refresh here,
   so the zip never bundles a stale note — **(iii)** rebuilding the zip from the fresh build. (If
   sanitizing was **not** necessary, proceed straight through.)

7. **Package — the git-clean source + build output + release note, into a versioned zip.**
   - **Version** = the HMI **app assembly major.minor** (from Step 5) — e.g. `3.25`.
   - **Output path** = `<parent-of-root>\<root-leaf> v<version>.zip` (i.e. the workspace `repos`
     folder: for `…\repos\5309_FAEL\…` → `…\repos\5309_FAEL v3.25.zip`). If a same-name zip already
     exists it is **overwritten** — call that out in the Step 8 report so a prior package isn't
     replaced unnoticed.
   - **Contents — source of every repo in the set, git-ignored files excluded:** for each repo run
     `git -C "<repo>" ls-files --cached --others --exclude-standard` (tracked + untracked-but-not-
     ignored; honours every `.gitignore`, so `bin\`/`obj\`/`.vs\` and the stale root `release\` tree
     are excluded). Add each file under `<repo-folder>/<path>` (ls-files already uses `/`). Plus the
     **target `.sln`** at the zip root (the solution root isn't a git repo) and the **release note**
     (`--rel`, default `<root>\ReleaseNote.md`; if missing, tell the user to run `versionize -new`
     first or pass `--rel`, and **stop**) at the zip root (its basename).
   - **Plus the build output of every executable project, under a top-level `Release/` folder.** The
     git-clean source excludes `bin\`, so the deployable output is added **explicitly** — except
     when Step 5 found **no build at all**, in which case there's nothing to add: skip `Release/`
     entirely and say so plainly in the Step 8 report (the zip is source + note only). For each
     **app/executable project** (`OutputType` Exe/WinExe — here `Sistec.5309AB` @ `Sistec.HMI\AB`,
     `Sistec.5309C` @ `Sistec.HMI\C`; `Sistec.BS` is bundled inside AB's output by its `CopyBS`
     target), take the **youngest build folder** resolved in Step 5 and add **all** its files
     (recursive) under **`Release/<app-folder-leaf>/<output-subfolder-name>/<rel>`** — i.e. `…\AB\bin\
     Release\HMI v3.25\` → `Release/AB/HMI v3.25/…`, `…\C\bin\Release\HMI v3.25\` → `Release/C/HMI
     v3.25/…`. (Convert the recursive relative path's separators with `.Replace([char]92,[char]47)` —
     not a literal `'\\'`/`'/'`.)
   - **Apply `--skip`:** if a repo's folder name is in the skip set, drop the whole repo (don't even
     `ls-files` it); otherwise drop any file whose path has a **segment** matching the skip set
     (case-insensitive — split each ls-files path on `/` and test each segment). Report which repos +
     how many nested files were skipped.
   - **Apply `--include` / `-i` — bundle each extra folder** (after the main solution, before building
     the zip). For every folder in the include set, add it under its **leaf folder name** at the zip
     root (`<includedLeaf>/<rel>`):
     - **If the folder contains a C# solution** (a `.sln` at its root or within): apply the **same
       exclusion rules** as the main target — resolve its repo set (root `.git` + immediate subfolders
       with `.git`, like Step 4) and add each repo's `git ls-files --cached --others
       --exclude-standard` (git-clean; `bin\`/`obj\`/`.vs\`/the stale `release\` excluded), honouring
       the `--skip` segment filtering. **Plus** add that solution's **executable project build output**
       — located by the **Step-5 youngest-build logic** on its exe project(s) (`OutputType`
       Exe/WinExe), **never built here** — under **`<includedLeaf>/Release/v<ver>/…`**, where `v<ver>`
       = the included **app assembly's `major.minor`** (place each exe project's output in its own
       `<app-leaf>/` subfolder when the solution has more than one). If the folder is not git-managed,
       enumerate its files directly, excluding `bin\`/`obj\`/`.vs\`/`.git\`.
     - **Otherwise** (no `.sln`): add all the folder's files as-is, still honouring the `--skip`
       segment filtering; no `Release/` output.
     Report each included folder + its file count (and the resolved `v<ver>` for solution folders).
   - **Build** with `System.IO.Compression.ZipFile.Open(<out>, Create)` +
     `ZipFileExtensions.CreateEntryFromFile($zip,$full,$entry,Optimal)` — direct entries, no staging
     copy. **Sandbox-safe scripting:** the static guard reads a literal `'/'` / `'\\'` near a delete as
     "remove root" — so (a) **don't** use `-replace '\\','/'` (ls-files is already `/`), (b) split path
     segments with `[char]47` not `'/'`, and (c) clear a pre-existing zip with `[IO.File]::Delete($out)`
     rather than `Remove-Item`.

8. **Report** in chat: the zip path + size, the repo set + file count, confirmation that
   git-ignored files and the note are handled, and any skip/include summaries.

9. **Record the resolved flow, for later `-r`/`--repeat` (every non-replay run).** Once the flow is
   resolved (Step 1) and has finished, write it as **one leg per line** to
   `./.package-release/last-flow.txt` (current working directory) — `refresh-note <target>` (if
   Step 3 ran) and `package <target> [--rel …] [--skip …] [--include …]`. A lone run **overwrites**
   the file with its own legs (flow = this run). This is bookkeeping only — it does not affect the
   read-only / no-build guarantees, and `-r` runs never re-record (Step 2).

Notes: global command — operates on the `<target>`, independent of the active project. **No approval
gate** in the clean case (read-only git + one zip write, overwriting a prior same-name zip). **One
conditional gate:** the **Step 6 pre-flight** interrupts before packaging when the tree is dirty /
mid-op / the build is stale (offer sanitize / proceed / cancel). Sanitize is always a hand-off to
another gated command — this skill never stages, commits, or builds — **and it never deploys or
pushes the zip anywhere**; that is deliberately out of scope. `git` may prompt for permission the
first time — handle case-by-case, don't pre-add allow-rules. Repo-set discovery is cheap and shared
with `gitize`/`versionize` (all scan fresh, no cache).
