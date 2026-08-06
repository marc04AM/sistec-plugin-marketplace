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
---

The user invoked `/versionize` to **create and maintain a release note** for a Sistec solution.
The release note (`ReleaseNote.md`) is a **snapshot** of the solution at a point in time with **four
fixed sections, in order: `Versions`, `Cell AB`, `Cell C`, `Libraries`**. Many Sistec solutions are
**multi-repo workspaces** (the solution root is not a git repo; each subfolder is its own) — this
command reuses `gitize`'s repo-set discovery. It is **read-only on git** and reads
**already-built DLLs** for versions; it **never builds, stages, or commits**. Its only write is the
output file. (Packaging a zip is a separate concern — that's `package-release`.)

1. **Resolve the mode, target, and options — natural language first.** Infer the mode from what the
   user is asking (cut/create a new release note → `-new`; refresh/update the changelog → `-upd`),
   the target from the solution/project/folder they're pointing at or the current working directory,
   and the output path from what they describe. Every flag below is an accepted, order-independent
   **shorthand** for the same intent — but none of this wording is required; describing the same
   thing in plain language is enough:
   - **Mode** — exactly one of `-new` (create the first issue) or `-upd` (prepend a changelog
     section since the last release). If none/more than one → print usage and **stop**.
   - **`<target>`** (positional, usually quoted; strip quotes) → a `.sln` file, a **project file**
     (`.csproj`/…), or a **folder**.
   - **`--out <path>`** (optional) → output file path. If it names a folder, append
     `ReleaseNote.md`. If **missing**, default to **`<solution root>\ReleaseNote.md`**.
   - Usage on error: `/versionize -new|-upd "<.sln, project file, or folder>" [--out <path>]`.

2. **Resolve the target → root, stem, and repo set** (same shapes as `gitize`):
   - **`.sln` file** (or a **folder** with exactly one `.sln`) → **solution target**: root = its
     folder, `<stem>` = the `.sln` name. Get the repo set via Step 3.
   - **project file / in-repo path** → **single-repo target**: resolve the one enclosing repo with
     `git -C "<dir>" rev-parse --show-toplevel`; repo set = just that repo; skip Step 3's cache.

3. **Discover the git-repo set** *(solution targets only)* — scan the root itself for a `.git`,
   then its immediate subfolders for a `.git` directory; collect every repo found. A cheap,
   single-pass scan, so discover fresh every run rather than caching it — no stale/out-of-sync
   state to carry between machines. Exactly like `gitize` Step 3.

4. **Locate the build outputs — follow each app project's output redirection, then trust the
   youngest build.** Do **not** assume a fixed folder name, and do **not** default to the
   solution-root `release\` tree — that is often a **stale *published* copy** (it bit the first run:
   the root `release\` DLLs were ~10 days older than the project build and predated HEAD). For each
   application project (here `Sistec.5309AB` / `Sistec.5309C` — this solution's example apps;
   substitute the target's own executable projects):
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

5. **Pre-flight cleanliness gate — warn on any unwanted condition, offer to sanitize, then resume.**
   A note built over a dirty tree or a stale build captures work that corresponds to **no commit** —
   so **before** any note work (before Step 6 onward), verify the repo set + build are
   release-worthy. Detect, across the resolved repo set in **one batched read-only shell loop**:
   - **(a) Dirty working tree** — `git -C "<repo>" status --porcelain` non-empty ⇒ uncommitted/untracked
     changes. Report per repo (staged / unstaged / untracked counts).
   - **(b) Git operation in progress** — a `.git/MERGE_HEAD`, a `rebase-merge`/`rebase-apply` dir, or a
     `.git/CHERRY_PICK_HEAD` ⇒ the repo is mid-merge/rebase/cherry-pick (a half-finished state with no
     automated fix — see the sanitize options below).
   - **(c) Stale / not-clean build** — compare each app's **built-from SHA** (the `ProductVersion`
     `1.0.0+<sha>`, resolved here if Step 6 hasn't run) and the youngest-build **timestamp** against repo
     HEAD: if HEAD is **ahead** of the built-from commit, or any tracked source file is **newer** than the
     youngest build's DLLs, the built artifacts are **stale vs source** — the note would describe binaries
     that don't reflect current code.
   - **(d) Ahead/behind upstream** *(informational)* — `git -C "<repo>" rev-list --left-right --count
     @{u}...HEAD` where an upstream exists; note unpushed/unpulled commits.

   **If no condition fires → continue silently** to the mode work. **If any fires → present a concise
   per-repo summary** (which repos are dirty / mid-op / stale, with the counts + drift SHAs) and **offer
   to sanitize** via `AskUserQuestion`, then **resume from here**:
   - **Sanitize the git state** — for a **dirty tree (a)**, hand off to `git-split-commits` (to
     commit the pending changes group-wise) or `git-amend-commits`, on the same repo set; they own
     their own gates/commits (never stage/commit here). For a **mid-operation repo (b)**, there is
     no automated fix — tell the user which repo and operation, and have them finish or abort it
     manually (`git merge`/`rebase`/`cherry-pick` `--continue`/`--abort`). After either is resolved,
     **re-run these checks** and continue.
   - **Proceed anyway** — accept the condition and continue; the dirty/stale/drift state is **recorded in
     the note header + the chat report** so the note is honestly labelled.
   - **Cancel** — stop without doing the mode work.

   For a **stale build (c)** specifically, `/versionize` **never builds** — the only real fix is to rebuild
   in the IDE, so its sanitize path is *Cancel → rebuild → re-run* or *Proceed anyway (drift noted)*; there
   is **no auto-rebuild**. It does **not** change the read-only / no-build guarantees — sanitize is always a
   hand-off to another gated command, never an action `/versionize` takes itself.

6. **Read artifact identity from the built DLLs — ONE consolidated PowerShell pass per chosen build
   folder** (read-only; one call per cell, **not** per-property or per-DLL). Enumerate the target
   DLLs in the Step-4 folder once and emit a single table carrying **all four** fields below for
   every DLL — `Version`, `CompanyName`, `ProductVersion`, **and `FileVersion`** (the last is reused
   by Step 7, so it is read here, not in a second pass):
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

7. **Read framework + third-party package versions** (no rebuild):
   - **.NET:** TargetFramework(s) from the `.csproj` set (apps vs libs) + any `global.json` SDK pin.
   - **Packages:** **reuse the FileVersion column from Step 6's single DLL pass** — do **not**
     re-enumerate the release folder. Cross-check those against `Sistec.HMI\Directory.Packages.props`
     (and inline `PackageReference`s). Collect the families the note calls out: **Opc.Ua** (`OPCFoundation.NetStandard.Opc.Ua.*` / `Opc.Ua.*.dll`), **Abc**
     (`Abc.Zebus`, `Abc.Zebus.Contracts`), **Mysql** (`MySqlConnector`, `MySqlBackup.NET`,
     `MySql.Data`), **Dapper** (`Dapper`, `Dapper.Contrib`).

8. **For each repo, read git facts** (read-only): `git -C "<repo>" remote get-url origin`
   (the *repository address*), `git -C "<repo>" rev-parse --abbrev-ref HEAD` (active branch), and
   `git -C "<repo>" log -1 --format="%h|%s|%ci"` (the *last commit at the active branch*). **Run
   these as a single loop over the repo set in one shell invocation** — not three calls per repo. If a
   repo in the set can't be read (missing/corrupt `.git`, not a repo), report which one and stop — a
   release note built over a partial repo set would misstate the snapshot.

9. **`-new` — write `ReleaseNote.md` with the 4 sections, in order.** **Read the feature catalog
   before reading app source:** `Sistec.HMI\FeatureCatalog.md` — a **tracked file in the repo**
   (project list, roles, frameworks, packages, library purposes), kept as real project
   documentation rather than personal memory, so every developer/agent sees the same catalog. Build
   the **`Libraries`** section and the **descriptive half of `Versions`** *from the catalog*; read
   source only to fill genuine gaps or when the catalog is absent. **Live numbers (build versions +
   commit SHAs) are always read fresh** (Steps 4/6/8) — never taken from the catalog. For **Cell
   AB/C**: read the catalog if present, else read the app source **once**; either way **verify-
   delta** — trust the catalog's descriptions but re-read only the areas changed since the
   catalog's recorded snapshot date via `git -C "<Sistec.HMI>" log <snapshot-date>..HEAD -- AB C
   Common` (+ `git -C "<Sistec.UI>" log <snapshot-date>..HEAD`). The sections:
   1. **`## Versions`**
      - **.NET version** — app vs lib TargetFrameworks; SDK; note if no `global.json`.
      - **Sistec artifacts** — a table; **each artifact described by: repository address · last
        commit at the active branch · assembly name · version · author** (from Steps 6 & 8). Where
        AB and C builds differ, show both (with the built-from SHA when it differs from HEAD).
      - **Opc.Ua versions**, **Abc versions**, **Mysql versions**, **Dapper versions** (Step 7).
   2. **`## Cell AB`** — the supervisor's **purpose** (what line/zones it supervises) and the
      **operator-callable features**: login / user levels, alarm inspection, settings, page
      navigation, each page's purpose + exposed features, device communication (which devices, which
      protocol/client), and database/MES usage. Derive from the app code (`Sistec.HMI\AB`, shared
      `Sistec.HMI\Common`, `Sistec.UI`).
   3. **`## Cell C`** — same shape for the line-C app (`Sistec.HMI\C`), noting what differs from AB.
   4. **`## Libraries`** — each Sistec library the cells depend on + its **purpose** (Core, Controls,
      UI, Common, Opc.Ua, Kuka.Client/KRC, Esa.Client/Modbus, EasyModbus, Bus).

   Skeleton (keep this fixed section order):
   ```markdown
   # ReleaseNote — <target>   (<date>)
   ## Versions
   | Artifact | Repo address | Last commit | Assembly | Version | Author |
   | --- | --- | --- | --- | --- | --- |
   ## Cell AB
   ## Cell C
   ## Libraries
   ```
   - Add a short header line with the generation date and the target, and **flag any drift** (e.g.
     release DLLs built from commits older than HEAD).
   - **Persist after writing:** update `Sistec.HMI\FeatureCatalog.md` (per-cell page inventory +
     operator features + device comms + DB/MES, plus a snapshot-date line) whenever the
     structure/version line moved — so the next `-new`/`-upd` reads the catalog instead of
     re-reading the app source. Plain file write, same as `ReleaseNote.md` itself — `/versionize`
     still never stages or commits it; the user commits the catalog update like any other change.

10. **`-upd` — prepend a changelog section** (don't rewrite the 4 sections):
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

11. **Report** in chat: the output path, the resolved repo set + per-repo HEAD, the artifact version
    table just written, and any drift/missing-DLL notes (`-upd`: summarize the changelog added).

Notes: global command — operates on the `<target>`, independent of the active project. **No approval
gate** in the clean case (read-only git + reads of built DLLs + a single doc write; it never
builds/stages/commits). **One conditional gate:** the **Step 5 pre-flight** interrupts either mode
when the tree is dirty / mid-op / the build is stale (offer sanitize / proceed / cancel). Sanitize is
always a hand-off to another (gated) command — `/versionize` itself never stages, commits, or builds.
`git` may prompt for permission the first time — handle case-by-case, don't pre-add allow-rules.
Repo-set discovery is cheap and shared with `gitize`, `git-split-commits`, `git-amend-commits`, and
`package-release` (all scan fresh, no cache).
