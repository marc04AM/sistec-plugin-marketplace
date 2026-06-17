---
description: Create and maintain a release note (ReleaseNote.md) for a Sistec solution or project — a 4-section snapshot (Versions, Cell AB, Cell C, Libraries). `-new` builds the first issue from the target's repos; `-upd` prepends a changelog of features/fixes since the last release; `--zip` packages the solution's git-clean source + each executable project's build output (under `Release/<App>/…`) + the release note into a versioned zip (with optional `--skip` to drop named folders). Artifact versions + authors are read from the already-built DLLs (no rebuild); repos + commits come from git. Usage: /versionize -new|-upd|--zip "<.sln, project file, or folder>" [--out <path>] [--rel <release-note>] [--skip "f1","f2",…]
---

The user invoked `/versionize` to **create and maintain a release note** for a Sistec solution.
The release note (`ReleaseNote.md`) is a **snapshot** of the solution at a point in time with **four
fixed sections, in order: `Versions`, `Cell AB`, `Cell C`, `Libraries`**. Many Sistec solutions are
**multi-repo workspaces** (the solution root is not a git repo; each subfolder is its own) — this
command reuses the `/gitize` repo-set discovery/cache. It is **read-only on git** and reads
**already-built DLLs** for versions; it **never builds, stages, or commits**. Its only write is the
output file.

1. **Parse the arguments** (flags order-independent):
   - **Mode** — exactly one of `-new` (create the first issue), `-upd` (prepend a changelog section
     since the last release), or `--zip` (package source + note — Step 11). If none/more-than-one →
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
   - Usage on error: `/versionize -new|-upd|--zip "<.sln, project file, or folder>" [--out <path>]
     [--rel <release-note>] [--skip "f1","f2",…]`.

2. **Resolve the target → root, stem, and repo set** (same shapes as `/gitize`):
   - **`.sln` file** (or a **folder** with exactly one `.sln`) → **solution target**: root = its
     folder, `<stem>` = the `.sln` name. Get the repo set via Step 3.
   - **project file / in-repo path** → **single-repo target**: resolve the one enclosing repo with
     `git -C "<dir>" rev-parse --show-toplevel`; repo set = just that repo; skip Step 3's cache.

3. **Get the git-repo set from memory; discover + persist if absent** *(solution targets only)* —
   recall a memory slugged `git-repos-<stem>` (for `Sistec.5309AB-C` → `git-repos-sistec-5309abc`).
   If absent, discover (root `.git` + immediate subfolders with `.git`) and record it in memory under
   `git-repos-<stem>`, exactly like `/gitize` step 1 (shared cache).

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
     newest `*.dll` `LastWriteTime`.

5. **Read artifact identity from each built DLL** (PowerShell, read-only):
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
   - **Packages:** prefer the built DLLs' FileVersion in the release folder, cross-checked against
     `Sistec.HMI\Directory.Packages.props` (and inline `PackageReference`s). Collect the families the
     note calls out: **Opc.Ua** (`OPCFoundation.NetStandard.Opc.Ua.*` / `Opc.Ua.*.dll`), **Abc**
     (`Abc.Zebus`, `Abc.Zebus.Contracts`), **Mysql** (`MySqlConnector`, `MySqlBackup.NET`,
     `MySql.Data`), **Dapper** (`Dapper`, `Dapper.Contrib`).

7. **For each repo, read git facts** (read-only): `git -C "<repo>" remote get-url origin`
   (the *repository address*), `git -C "<repo>" rev-parse --abbrev-ref HEAD` (active branch), and
   `git -C "<repo>" log -1 --format="%h|%s|%ci"` (the *last commit at the active branch*).

8. **`-new` — write `ReleaseNote.md` with the 4 sections, in order:**
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

9. **`-upd` — prepend a changelog section** (don't rewrite the 4 sections):
   - Read the existing `ReleaseNote.md`; parse the **per-repo last-commit** recorded in its
     `Versions` section (that is the previous release baseline). If the file is missing, tell the
     user to run `-new` first and **stop**.
   - For each repo: `git -C "<repo>" log <recorded>..HEAD --format="%h|%s"`; classify by
     Conventional-Commits type into **Features** (`feat`) and **Fixes** (`fix`) — other types
     (`refactor`/`chore`/…) under a brief **Other** line. Group by repo.
   - Insert a new `## <YYYY-MM-DD> — <version>` section **at the very top** of the file with those
     Features/Fixes, then **refresh** the `Versions` section's commit pointers + DLL versions so the
     next `-upd` diffs from here. Leave Cell AB / Cell C / Libraries intact (regenerate only if their
     code changed and the user asks).

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

Notes: global command — operates on the `<target>`, independent of any working folder. **No approval
gate** (read-only git + reads of built DLLs + a single doc write — or, for `--zip`, one zip written to
the `repos` folder, overwriting a prior same-name zip; it never builds/stages/commits).
`git` may prompt for permission the first time — handle case-by-case, don't pre-add allow-rules.
The repo-set memory (`git-repos-<stem>`) is shared with `/gitize`.
