---
description: Create and maintain a release note (ReleaseNote.md) for a Sistec solution or project — a 4-section snapshot (Versions, Cell AB, Cell C, Libraries). `-new` builds the first issue from the target's repos; `-upd` prepends a changelog of features/fixes since the last release; `--zip` packages the solution's git-clean source + each executable project's build output (under `Release/<App>/…`) + the release note into a versioned zip (with optional `--skip` to drop named folders, `--include`/`-i` to bundle extra folders); `--deploy`/`-d` appends a `/deploy` leg that pushes the just-built artifact into production (gated, not read-only). Before any note/package/deploy work a **pre-flight cleanliness gate** warns on unwanted conditions (dirty working tree, in-progress merge/rebase, stale build vs source HEAD) and offers to sanitize (`/gitize` / `/gitAlign`) or proceed; when sanitizing was necessary, the note is refreshed and the zip rebuilt AFTER the build so they match the just-deployed binaries. `-r`/`--repeat` replays the last recorded flow (one invocation per line in the state file, in order — e.g. a compound `-upd` then `--zip`). Artifact versions + authors are read from the already-built DLLs (no rebuild); repos + commits come from git. Usage: /versionize -new|-upd|--zip "<.sln, project file, or folder>" [--out <path>] [--rel <release-note>] [--skip "f1","f2",…] [--include "f1","f2",…] [--deploy|-d <deploy flags…>] | -r|--repeat
---

The user invoked `/versionize` to **create and maintain a release note** for a Sistec solution.
The release note (`ReleaseNote.md`) is a **snapshot** of the solution at a point in time with **four
fixed sections, in order: `Versions`, `Cell AB`, `Cell C`, `Libraries`**. Many Sistec solutions are
**multi-repo workspaces** (the solution root is not a git repo; each subfolder is its own) — this
command reuses the `/gitize` repo-set discovery/cache. It is **read-only on git** and reads
**already-built DLLs** for versions; it **never builds, stages, or commits**. Its only write is the
output file — **except** when `--deploy`/`-d` is present, which appends a `/deploy` leg that copies the
built artifact into production (gated by `/deploy`'s own confirmation; see Step 12).

1. **Parse the arguments** (flags order-independent):
   - **`--repeat` / `-r` — replay the last recorded flow (standalone mode, takes no other args).**
     Check for it **first**: read the saved flow from the state file
     `commands\versionize\last-args.txt` (relative to the workspace root
     `C:\Users\Sistec 23\source\repos\Claude\`). The file holds **one invocation per line** — a flow
     of one or more legs; **replay every line in order**, re-dispatching each **exactly as if**
     `/versionize` had been invoked with those arguments (same mode + target + every flag). A compound
     flow such as 5309's `-upd` → `--zip --include …` thus reproduces a **coherent snapshot** — it
     refreshes the note **first**, THEN packages it, so the zip never bundles a stale `ReleaseNote.md`.
     If the file is **missing or empty**, print usage and **stop**. **Echo each leg** before running
     it. The replayed legs **do not re-record** (a flow's own legs are part of the replay, not new
     user calls) and `-r` itself is **never recorded** — so the saved flow is unchanged and a second
     `-r` repeats it identically. See `[[versionize-repeat-last-flow]]`.
   - **Mode** — exactly one of `-new` (create the first issue), `-upd` (prepend a changelog section
     since the last release), or `--zip` (package source + note — Step 11) — or the standalone
     `-r`/`--repeat` replay above. If none/more-than-one (other than a lone `-r`) →
     print usage and **stop**.
   - **`<target>`** (positional, usually quoted; strip quotes) → a `.sln` file, a **project file**
     (`.csproj`/…), or a **folder**.
   - **`--out <path>`** (optional, `-new`/`-upd`) → output file path. If it names a folder, append
     `ReleaseNote.md`. If **missing**, default to **`<solution root>\ReleaseNote.md`**.
   - **`--rel <path>`** (optional, `--zip`) → the release note to bundle into the zip. If **missing**,
     default to **`<solution root>\ReleaseNote.md`**.
   - **`--skip "f1","f2",…`** (optional, `--zip`) → a **list of folder names** to exclude from the zip.
     Collect every token after `--skip` up to the next flag; **strip surrounding quotes and commas**;
     case-insensitive. A name matches a **whole repo** (e.g. `Test`) **or any folder segment** anywhere
     in a file's path (e.g. a nested `Test\` / `Resources\`). Empty by default.
   - **`--include "f1","f2",…`** / **`-i …`** (optional, `--zip`) → a **list of additional folders to
     bundle** into the zip (beyond the solution's own repos). Collect every token after `--include`/`-i`
     up to the next flag; **strip surrounding quotes and commas**. Optional, empty by default. Each
     folder is added under its **leaf name** at the zip root; if it **contains a C# solution** it gets
     the git-clean + `--skip` exclusion rules **and** its built `Release/v<ver>` output (Step 10).
   - **`--deploy` / `-d` `<deploy flags…>`** (optional; pairs with `--zip`) → append a **`/deploy`
     leg** after the package step (Step 12). `--deploy` is a **trigger + boundary**: every token after
     it is handed verbatim to `/deploy` (so `/deploy`'s own `-d`/`--dest`, `-r`/`--release`, `-n`,
     `-l`, `-z` parse there, not here — place `--deploy` **last**). Omitting `/deploy`'s `--zip`/
     `--release` makes the leg default its source to **this run's `--zip` output** (the chained case).
     **Self-versioning in the `-r`/`--repeat` flow:** the **first** call must carry the full deploy flag
     set (recorded verbatim); on **every replay**, `/versionize` **injects `--version <this run's
     artifact major.minor>`** (Step 4) into the deploy leg unless the recorded tokens already carry
     `--version`/`-v`, and sources the rest (`--dest`/`--name`/`--release`/`--link`) from the recorded
     line — so each repeat re-deploys at the **freshly-built** version without re-specifying it (have the
     recorded `--name`/`--release` use the `*`/root forms `/deploy`'s `--version` completion fills; Step 12).
   - **Record the invocation for `-r` (every non-`-r` run).** Once the arguments are parsed and
     validated, write the full resolved parameter set (mode + target + every flag and its values) as
     **one re-runnable line** to `commands\versionize\last-args.txt` **before** executing the mode —
     so a later `/versionize -r` replays it. A lone normal run **overwrites** the file with its single
     line (flow = that one call). A **multi-leg flow** (one invocation per line, replayed in order by
     `-r`) is **seeded / maintained explicitly** — auto-recording does **not** detect flow boundaries,
     so to preserve a known compound flow (e.g. 5309's `-upd` → `--zip --include …`, whose whole point
     is a fresh note *then* a fresh zip) keep **both** legs in the file rather than letting a lone
     `-upd`/`--zip` run overwrite it. This state write is the command's own bookkeeping (not a mode
     side effect); it does not affect the read-only / no-build guarantees.
   - Usage on error: `/versionize -new|-upd|--zip "<.sln, project file, or folder>" [--out <path>]
     [--rel <release-note>] [--skip "f1","f2",…] [--include "f1","f2",…] [--deploy|-d <deploy flags…>]
     | -r|--repeat`.

2. **Resolve the target → root, stem, and repo set** (same shapes as `/gitize`):
   - **`.sln` file** (or a **folder** with exactly one `.sln`) → **solution target**: root = its
     folder, `<stem>` = the `.sln` name. Get the repo set via Step 3.
   - **project file / in-repo path** → **single-repo target**: resolve the one enclosing repo with
     `git -C "<dir>" rev-parse --show-toplevel`; repo set = just that repo; skip Step 3's cache.

3. **Get the git-repo set from memory; discover + persist if absent** *(solution targets only)* —
   recall a memory slugged `git-repos-<stem>` (for `Sistec.5309AB-C` → `git-repos-sistec-5309abc`).
   If absent, discover (root `.git` + immediate subfolders with `.git`) and persist a
   `git-repos-<stem>.md` reference memory + a `MEMORY.md` pointer, exactly like `/gitize` step 1.

4. **Locate the build outputs — follow each app project's output redirection, then trust the
   youngest build.** Do **not** assume a fixed folder name, and do **not** default to the
   solution-root `release\` tree — that is often a **stale *published* copy** (it bit the first run:
   the root `release\` DLLs were ~10 days older than the project build and predated HEAD). For each
   application project (`Sistec.5309AB`, `Sistec.5309C`):
   - **Read the `.csproj` for an output redirection** — `<OutputPath>` (or `<OutDir>` /
     `<BaseOutputPath>`). Sistec apps set `OutputPath = bin\$(Configuration)\$(_ProductFolderName)\`
     where `_ProductFolderName = "HMI v$(_AsmVerMajorMinor)"` (e.g. `bin\Release\HMI v3.25\`).
     **Follow it.** Substitute `$(Configuration)` (Release) and resolve the trailing **computed**
     folder by **discovery** rather than re-evaluating the MSBuild expression: take the resolvable
     base (`<projDir>\bin\Release\`) and enumerate its subfolders.
   - **If no redirection is declared**, default the base to `<projDir>\bin\Release\` (then `bin\Debug\`).
   - **Pick the youngest build:** under the resolved base, choose the subfolder whose DLLs have the
     **most recent `LastWriteTime`** — this handles any folder-name pattern and multiple builds, and
     guarantees the freshest artifacts. Note the build timestamp + that AB and C built in the **same**
     solution build share identical shared-lib versions (different builds → per-cell versions differ).
   - **Do not build.** If a project has no built DLL anywhere, note it and fall back to its `.csproj`
     version (which may be the unexpanded literal `3.25.*`).
   - Pipe-free discovery, e.g.
     `Get-ChildItem -LiteralPath "<projDir>\bin\Release" -Directory` → sort its subfolders by the
     newest `*.dll` `LastWriteTime`. **Scan both apps' `bin\Release` in ONE shell pass and read only
     `LastWriteTime` here** — this step is a *light* scan whose sole job is to pick the youngest
     folder per app; defer all identity reads (version/company/provenance/FileVersion) to Step 5's
     single deep pass over the chosen folder. Do not read each DLL here and again in Steps 5/6.

4.5. **Pre-flight cleanliness gate — warn on any unwanted condition, offer to sanitize, then resume
   (all modes; strongest for `--zip`/`--deploy`).** A note/zip built over a dirty tree or a stale build
   captures work that corresponds to **no commit** — and a `--deploy` then pushes those uncommitted/stale
   binaries to production. So **before** any note/package/deploy work (before the Step 5–9 / Step 10
   body), verify the repo set + build are release-worthy. Detect, across the resolved repo set in **one
   batched read-only shell loop**:
   - **(a) Dirty working tree** — `git -C "<repo>" status --porcelain` non-empty ⇒ uncommitted/untracked
     changes. `--zip` bundles `ls-files --cached --others --exclude-standard` (the **working-tree** state),
     so a dirty repo packages uncommitted work. Report per repo (staged / unstaged / untracked counts).
   - **(b) Git operation in progress** — a `.git/MERGE_HEAD`, a `rebase-merge`/`rebase-apply` dir, or a
     `.git/CHERRY_PICK_HEAD` ⇒ the repo is mid-merge/rebase/cherry-pick (a half-finished state — `/gitAlign`
     territory).
   - **(c) Stale / not-clean build** — compare each app's **built-from SHA** (the `ProductVersion`
     `1.0.0+<sha>`, resolved here if Step 5 hasn't run) and the youngest-build **timestamp** against repo
     HEAD: if HEAD is **ahead** of the built-from commit, or any tracked source file is **newer** than the
     youngest build's DLLs, the built artifacts are **stale vs source** — the packaged/deployed binaries
     don't reflect current code. (This is the "drift" the note already flags, promoted to a gating warning.)
   - **(d) Ahead/behind upstream** *(informational)* — `git -C "<repo>" rev-list --left-right --count
     @{u}...HEAD` where an upstream exists; note unpushed/unpulled commits.

   **If no condition fires → continue silently** to the mode work. **If any fires → present a concise
   per-repo summary** (which repos are dirty / mid-op / stale, with the counts + drift SHAs) and **offer
   to sanitize** via `AskUserQuestion`, then **resume from here**:
   - **Sanitize the git state** — hand off to the matching command **on the same repo set**: `/gitize`
     (`--split` to commit the pending changes group-wise, or `--amend`) for dirty repos; `/gitAlign` to
     finish an in-progress merge/rebase. They own their own gates/commits (and P15 — `/versionize` never
     stages). After they finish, **re-run the 4.5 checks** and continue.
   - **Proceed anyway** — accept the condition and continue; the dirty/stale/drift state is **recorded in
     the note header + the chat report** so the package is honestly labelled.
   - **Cancel** — stop without doing the mode work.

   For a **stale build (c)** specifically, `/versionize` **never builds** — the only real fix is to rebuild
   in the IDE, so its sanitize path is *Cancel → rebuild → re-run* or *Proceed anyway (drift noted)*; there
   is **no auto-rebuild**. The gate is advisory for `-new`/`-upd` (a note over a dirty tree is merely
   imprecise) and **most important for `--zip`/`--deploy`** (packaging/pushing uncommitted or stale
   binaries). It does **not** change the read-only / no-build guarantees — sanitize is always a hand-off to
   another gated command, never an action `/versionize` takes itself.

   **Regenerate the note + zip AFTER the build when sanitizing was necessary.** Whenever the Sanitize
   path committed changes and/or a stale build was rebuilt, the user rebuilds before resuming — and on
   resume the note + package must reflect the **post-build** state, not the pre-sanitize one. So after the
   build, **before any `--deploy` leg**: **(i)** re-run Step 4 to pick up the **fresh youngest build**;
   **(ii)** **refresh the release note** so its Versions pointers + changelog capture the just-committed
   sanitized changes — if the flow already has `-new`/`-upd`, run that; **a bare `--zip` flow with no note
   leg still refreshes the note via an implicit `-upd`** (so the packaged note isn't stale) — skip the
   refresh only if no repo actually advanced (nothing was committed and the build was already current);
   **(iii)** rebuild the `--zip` output from the fresh build; **then** run `--deploy`. Rationale: a
   note/zip computed before the sanitize rebuild would ship binaries + a changelog that disagree — which
   is exactly what catching the stale build is meant to prevent. (If sanitizing was **not** necessary —
   the pre-flight passed clean — proceed straight through with no implicit `-upd`.)

**Steps 5–7 are `-new`/`-upd` only.** `--zip` needs just Step 4's app `major.minor` — **skip Steps
5, 6, and 7 entirely** for `--zip` and go to Step 10.

5. **Read artifact identity from the built DLLs — ONE consolidated PowerShell pass per chosen build
   folder** (read-only; one call per cell, **not** per-property or per-DLL). Enumerate the target
   DLLs in the Step-4 folder once and emit a single table carrying **all four** fields below for
   every DLL — `Version`, `CompanyName`, `ProductVersion`, **and `FileVersion`** (the last is reused
   by Step 6, so it is read here, not in a second pass):
   - **Version (resolved 4-part):** `[System.Reflection.AssemblyName]::GetAssemblyName($dll).Version`
     — note the `.csproj`'s literal `FileVersion` is often unexpanded (`3.25.*`); the **AssemblyName
     version** carries the real build numbers (e.g. `2.10.9652.21350`).
   - **Author / assembly name:** `(Get-Item $dll).VersionInfo.CompanyName` (e.g. `Sistec AM`,
     `Sistec`) and the assembly's `Name` / `AssemblyTitle`.
   - **Build provenance:** `(Get-Item $dll).VersionInfo.ProductVersion` is usually
     `1.0.0+<commit-sha>` — record the SHA the DLL was **built from** (it may predate repo HEAD).
   - Cover the Sistec/Esa/Modbus assemblies that map to the repo set: `Sistec.Core`, `Sistec.Opc.Ua`,
     `Sistec.Controls`, `Sistec.Common`, `Sistec.UI`, `Sistec.KRC.Client` (Kuka.Client repo),
     `Esa.Client`, `EasyModbus` (AssemblyTitle `Sistec.Modbus`), `Sistec.Bus`, and the apps
     `Sistec.5309AB` / `Sistec.5309C` (+ `Sistec.BS`). **Apps AB and C are built separately**, so the
     shared libs can carry **different** build numbers per cell — report per cell when they differ.

6. **Read framework + third-party package versions** (no rebuild):
   - **.NET:** TargetFramework(s) from the `.csproj` set (apps vs libs) + any `global.json` SDK pin.
   - **Packages:** **reuse the FileVersion column from Step 5's single DLL pass** — do **not**
     re-enumerate the release folder. Cross-check those against `Sistec.HMI\Directory.Packages.props`
     (and inline `PackageReference`s). Collect the families the note calls out: **Opc.Ua** (`OPCFoundation.NetStandard.Opc.Ua.*` / `Opc.Ua.*.dll`), **Abc**
     (`Abc.Zebus`, `Abc.Zebus.Contracts`), **Mysql** (`MySqlConnector`, `MySqlBackup.NET`,
     `MySql.Data`), **Dapper** (`Dapper`, `Dapper.Contrib`).

7. **For each repo, read git facts** (read-only): `git -C "<repo>" remote get-url origin`
   (the *repository address*), `git -C "<repo>" rev-parse --abbrev-ref HEAD` (active branch), and
   `git -C "<repo>" log -1 --format="%h|%s|%ci"` (the *last commit at the active branch*). **Run
   these as a single loop over the repo set in one shell invocation** — not three calls per repo.

8. **`-new` — write `ReleaseNote.md` with the 4 sections, in order.** **Recall before reading
   (P0):** pull `[[fael-solution]]` (project list, roles, frameworks, packages, library purposes) +
   the `fael-hmi-feature-catalog` memory (if present) + related HMI anchors ([[alarm-journal-anchor]],
   …) **before** opening any app source. Build the **`Libraries`** section and the **descriptive
   half of `Versions`** *from memory*; read source only to fill genuine gaps. **Live numbers (build
   versions + commit SHAs) are always read fresh** (Steps 4/5/7) — never recalled. For **Cell AB/C**:
   recall the feature-catalog if present, else read the app source **once**; either way **verify-
   delta** — trust recalled descriptions but re-read only the areas changed since the recalled
   memory's snapshot date via `git -C "<Sistec.HMI>" log <mem-date>..HEAD -- AB C Common` (+
   `git -C "<Sistec.UI>" log <mem-date>..HEAD`). The sections:
   1. **`## Versions`**
      - **.NET version** — app vs lib TargetFrameworks; SDK; note if no `global.json`.
      - **Sistec artifacts** — a table; **each artifact described by: repository address · last
        commit at the active branch · assembly name · version · author** (from Steps 5 & 7). Where
        AB and C builds differ, show both (with the built-from SHA when it differs from HEAD).
      - **Opc.Ua versions**, **Abc versions**, **Mysql versions**, **Dapper versions** (Step 6).
   2. **`## Cell AB`** — the supervisor's **purpose** (what line/zones it supervises) and the
      **operator-callable features**: login / user levels, alarm inspection, settings, page
      navigation, each page's purpose + exposed features, device communication (which devices, which
      protocol/client), and database/MES usage. Derive from the app code (`Sistec.HMI\AB`, shared
      `Sistec.HMI\Common`, `Sistec.UI`).
   3. **`## Cell C`** — same shape for the line-C app (`Sistec.HMI\C`), noting what differs from AB.
   4. **`## Libraries`** — each Sistec library the cells depend on + its **purpose** (Core, Controls,
      UI, Common, Opc.Ua, Kuka.Client/KRC, Esa.Client/Modbus, EasyModbus, Bus).
   - Add a short header line with the generation date and the target, and **flag any drift** (e.g.
     release DLLs built from commits older than HEAD).
   - **Persist after writing (P0.4):** refresh the `fael-hmi-feature-catalog` memory (per-cell page
     inventory + operator features + device comms + DB/MES) and bump `[[fael-solution]]` if the
     structure/version line moved — so the next `-new`/`-upd` recalls the descriptive sections
     instead of re-reading the app source.

9. **`-upd` — prepend a changelog section** (don't rewrite the 4 sections):
   - Read the existing `ReleaseNote.md`; parse the **per-repo last-commit** recorded in its
     `Versions` section (that is the previous release baseline). If the file is missing, tell the
     user to run `-new` first and **stop**.
   - For each repo: `git -C "<repo>" log <recorded>..HEAD --format="%h|%s"` (**one shell loop over
     the repo set**, not a call per repo); classify by
     Conventional-Commits type into **Features** (`feat`) and **Fixes** (`fix`) — other types
     (`refactor`/`chore`/…) under a brief **Other** line. Group by repo.
   - Insert a new `## <YYYY-MM-DD> — <version>` section **at the very top** of the file with those
     Features/Fixes, then **refresh** the `Versions` section's commit pointers + DLL versions so the
     next `-upd` diffs from here. Leave Cell AB / Cell C / Libraries intact (regenerate only if their
     code changed and the user asks).
   - **Younger-before-older everywhere (chronology rule).** Every accumulating list in the note is
     ordered **newest-first**: the new dated `##` section goes **above** all prior ones (as above),
     **and** the new `> 🔄 …` header update-note is prepended at the **top of the header `🔄` block**
     (directly under the `-new` origin line), **above** the previous update-notes. Do **not** append
     it after the older notes. If a prior run left the header block oldest-first, **reorder it
     newest-first** while you are there, so the most recent information always reads first.

10. **`--zip` — package the solution's git-clean source + the release note into a versioned zip.**
    This mode does **not** generate the note; it bundles an existing one with the source. Steps:
    - **Release note** = `--rel <path>`; if omitted default `<root>\ReleaseNote.md`. If it doesn't
      exist → tell the user to run `-new` first (or pass `--rel`) and **stop**.
    - **Version** = the HMI **app assembly major.minor** (`Sistec.5309AB` / `Sistec.5309C`, read from
      the youngest build located in Step 4) — e.g. `3.25`.
    - **Output path** = `<parent-of-root>\<root-leaf> v<version>.zip` (i.e. the workspace `repos`
      folder: for `…\repos\5309_FAEL\…` → `…\repos\5309_FAEL v3.25.zip`). Overwrite if present.
    - **Contents — source of every repo in the set, git-ignored files excluded:** for each repo run
      `git -C "<repo>" ls-files --cached --others --exclude-standard` (tracked + untracked-but-not-
      ignored; honours every `.gitignore`, so `bin\`/`obj\`/`.vs\` and the stale root `release\` tree
      are excluded). Add each file under `<repo-folder>/<path>` (ls-files already uses `/`). Plus the
      **target `.sln`** at the zip root (the solution root isn't a git repo) and the **release note**
      at the zip root (its basename).
    - **Plus the build output of every executable project, under a top-level `Release/` folder.** The
      git-clean source excludes `bin\`, so the deployable output is added **explicitly** (it is the
      whole point of a release package). For each **app/executable project** (`OutputType` Exe/WinExe —
      here `Sistec.5309AB` @ `Sistec.HMI\AB`, `Sistec.5309C` @ `Sistec.HMI\C`; `Sistec.BS` is bundled
      inside AB's output by its `CopyBS` target), take the **youngest build folder** resolved in Step 4
      (the csproj `OutputPath` → `<projDir>\bin\Release\<_ProductFolderName>\`, e.g. `…\AB\bin\Release\
      HMI v3.25\`) and add **all** its files (recursive) under
      **`Release/<app-folder-leaf>/<output-subfolder-name>/<rel>`** — i.e. `…\AB\bin\Release\HMI v3.25\`
      → `Release/AB/HMI v3.25/…`, `…\C\bin\Release\HMI v3.25\` → `Release/C/HMI v3.25/…`. (Convert the
      recursive relative path's separators with `.Replace([char]92,[char]47)` — not a literal
      `'\\'`/`'/'`.)
    - **Apply `--skip`:** if a repo's folder name is in the skip set, drop the whole repo (don't even
      `ls-files` it); otherwise drop any file whose path has a **segment** matching the skip set
      (case-insensitive — split each ls-files path on `/` and test each segment). Report which repos +
      how many nested files were skipped.
    - **Apply `--include` / `-i` — bundle each extra folder** (after the main solution, before building
      the zip). For every folder in the include set, add it under its **leaf folder name** at the zip
      root (`<includedLeaf>/<rel>`):
      - **If the folder contains a C# solution** (a `.sln` at its root or within): apply the **same
        exclusion rules** as the main target — resolve its repo set (root `.git` + immediate subfolders
        with `.git`, like Steps 2–3) and add each repo's `git ls-files --cached --others
        --exclude-standard` (git-clean; `bin\`/`obj\`/`.vs\`/the stale `release\` excluded), honouring
        the `--skip` segment filtering. **Plus** add that solution's **executable project build output**
        — located by the **Step-4 youngest-build logic** on its exe project(s) (`OutputType`
        Exe/WinExe), **never built here** — under **`<includedLeaf>/Release/v<ver>/…`**, where `v<ver>`
        = the included **app assembly's `major.minor`** (the artifact version; place each exe project's
        output in its own `<app-leaf>/` subfolder when the solution has more than one). If the folder is
        not git-managed, enumerate its files directly, excluding `bin\`/`obj\`/`.vs\`/`.git\`.
      - **Otherwise** (no `.sln`): add all the folder's files as-is, still honouring the `--skip`
        segment filtering; no `Release/` output.
      Report each included folder + its file count (and the resolved `v<ver>` for solution folders).
    - **Build** with `System.IO.Compression.ZipFile.Open(<out>, Create)` +
      `ZipFileExtensions.CreateEntryFromFile($zip,$full,$entry,Optimal)` — direct entries, no staging
      copy. **Sandbox-safe scripting:** the static guard reads a literal `'/'` / `'\\'` near a delete as
      "remove root" — so (a) **don't** use `-replace '\\','/'` (ls-files is already `/`), (b) split path
      segments with `[char]47` not `'/'`, and (c) clear a pre-existing zip with `[IO.File]::Delete($out)`
      rather than `Remove-Item`.

11. **Report** in chat: for `-new`/`-upd` — the output path, the resolved repo set + per-repo HEAD,
    the artifact version table just written, and any drift/missing-DLL notes (`-upd`: summarize the
    changelog added). For `--zip` — the zip path + size, the repo set + file count, and confirmation
    that git-ignored files and the note are handled.

12. **`--deploy` / `-d` — append a `/deploy` leg (push the artifact into production).** Only when the
    flag is present, and only after the package step has produced the zip (so `--deploy` pairs with
    `--zip`; if used without `--zip`, the chained `/deploy` must carry its own `--release`/`--zip`).
    Invoke **`/deploy`** with the tokens that followed `--deploy` on the command line, verbatim. When
    those tokens omit a binaries source (`--release`/`--zip`), `/deploy` defaults its source to **this
    run's `--zip` output** (`<repos>\<root-leaf> v<ver>.zip`). `/deploy` owns its own **production-write
    confirmation gate** — `/versionize` does not copy anything itself; it just hands off. Report the
    `/deploy` outcome (targets, folders, shortcut) alongside the zip result. In the `-r` flow this is a
    leg like any other (record `--zip … --deploy …` as its own line, or chain after the `--zip` leg).

    **Self-versioning under `-r`/`--repeat`.** When the deploy leg runs as part of a **replay**, first
    resolve **`V` = this run's app assembly `major.minor`** (the same value Step 10 uses for the zip —
    read from the youngest build in Step 4). Hand `/deploy` the **recorded** deploy tokens **plus**
    `--version <V>` (skip the injection if the recorded tokens already include `--version`/`-v`).
    `/deploy` Step 1c then completes the recorded `--name`/`--release` (their `*`/root forms) to `V` and
    coordinates the indicator across sites. The first (recorded) call supplies the deploy params
    explicitly; from the second run on, the leg **assumes `--version`** from the artifact and sources the
    rest from that recorded call — so a repeated build-and-deploy flow advances the deployed version
    automatically.

Notes: global command — operates on the `<target>`, independent of the active project. **No approval
gate for `-new`/`-upd`/`--zip`** in the clean case (read-only git + reads of built DLLs + a single doc
write — or, for `--zip`, one zip written to the `repos` folder, overwriting a prior same-name zip; it
never builds/stages/commits). **Two conditional gates:** the **Step 4.5 pre-flight** interrupts *any*
mode when the tree is dirty / mid-op / the build is stale (offer sanitize / proceed / cancel), and
**`--deploy`** hands off to `/deploy`, which **writes to a production share behind its own explicit
confirmation** (Step 12). Sanitize is always a hand-off to another (gated) command — `/versionize`
itself never stages, commits, or builds.
`git` may prompt for permission the first time — handle case-by-case, don't pre-add allow-rules.
Writing `.claude\commands\*.md` is agent-config self-modification (see `[[cannot-self-edit-permissions]]`).
The repo-set memory (`git-repos-<stem>`) is shared with `/gitize`. Anchor `[[commands-anchor]]`;
detail `[[versionize-command]]`.
